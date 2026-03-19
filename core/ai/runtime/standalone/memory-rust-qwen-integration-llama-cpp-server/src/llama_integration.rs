use crate::{error::Result, models::InferenceRequest};
use async_trait::async_trait;
use reqwest::Client;
use serde_json::{json, Value};
use std::time::Duration;

/// Trait for LLM inference backends
#[async_trait]
pub trait InferenceBackend: Send + Sync {
    async fn generate_completion(&self, request: &InferenceRequest) -> Result<String>;
    async fn generate_completion_stream(
        &self,
        request: &InferenceRequest,
    ) -> Result<tokio::sync::mpsc::UnboundedReceiver<String>>;
    fn is_model_loaded(&self) -> bool;
    fn get_model_info(&self) -> Result<crate::models::ModelInfo>;
}

/// Real llama.cpp inference backend via HTTP API
pub struct LlamaCppBackend {
    client: Client,
    base_url: String,
    model_name: String,
    model_loaded: bool,
}

impl LlamaCppBackend {
    pub fn new(base_url: String, model_name: String) -> Self {
        Self {
            client: Client::new(),
            base_url,
            model_name,
            model_loaded: false,
        }
    }

    pub async fn check_model_status(&mut self) -> Result<()> {
        let url = format!("{}/api/tags", self.base_url);
        
        match self.client.get(&url).timeout(Duration::from_secs(5)).await {
            Ok(response) => {
                if response.status().is_success() {
                    let tags: Value = response.json().await?;
                    if let Some(models) = tags.get("models").and_then(|v| v.as_array()) {
                        self.model_loaded = models.iter().any(|model| {
                            model.get("name")
                                .and_then(|n| n.as_str())
                                .map(|n| n.contains(&self.model_name))
                                .unwrap_or(false)
                        });
                    }
                }
            }
            Err(_) => {
                self.model_loaded = false;
            }
        }
        Ok(())
    }

    async fn call_llamacpp_completion(&self, prompt: &str, max_tokens: Option<usize>, temperature: Option<f32>) -> Result<Value> {
        let url = format!("{}/api/completion", self.base_url);
        
        let request_body = json!({
            "prompt": prompt,
            "model": self.model_name,
            "max_tokens": max_tokens.unwrap_or(2048),
            "temperature": temperature.unwrap_or(0.7),
            "stream": false
        });

        let response = self.client
            .post(&url)
            .json(&request_body)
            .timeout(Duration::from_secs(30))
            .await?;

        if response.status().is_success() {
            let result: Value = response.json().await?;
            Ok(result)
        } else {
            Err(crate::error::Error::Inference(format!(
                "llama.cpp API error: {}",
                response.status()
            )))
        }
    }

    async fn call_llamacpp_chat(&self, messages: &[crate::models::ChatMessage], max_tokens: Option<usize>, temperature: Option<f32>) -> Result<Value> {
        let url = format!("{}/api/chat", self.base_url);
        
        // Convert messages to llama.cpp format
        let llama_messages: Vec<Value> = messages.iter().map(|msg| {
            json!({
                "role": match msg.role {
                    crate::models::MessageRole::User => "user",
                    crate::models::MessageRole::Assistant => "assistant",
                    crate::models::MessageRole::System => "system",
                },
                "content": msg.content
            })
        }).collect();

        let request_body = json!({
            "model": self.model_name,
            "messages": llama_messages,
            "max_tokens": max_tokens.unwrap_or(2048),
            "temperature": temperature.unwrap_or(0.7),
            "stream": false
        });

        let response = self.client
            .post(&url)
            .json(&request_body)
            .timeout(Duration::from_secs(30))
            .await?;

        if response.status().is_success() {
            let result: Value = response.json().await?;
            Ok(result)
        } else {
            Err(crate::error::Error::Inference(format!(
                "llama.cpp chat API error: {}",
                response.status()
            )))
        }
    }
}

#[async_trait]
impl InferenceBackend for LlamaCppBackend {
    async fn generate_completion(&self, request: &InferenceRequest) -> Result<String> {
        if !self.model_loaded {
            return Err(crate::error::Error::ModelNotLoaded);
        }

        // Try chat API first (better for Qwen), fallback to completion
        let result = match self.call_llamacpp_chat(&request.messages, request.max_tokens, request.temperature).await {
            Ok(response) => response,
            Err(_) => {
                // Fallback to completion API
                let prompt = self.format_messages_as_prompt(&request.messages);
                self.call_llamacpp_completion(&prompt, request.max_tokens, request.temperature).await?
            }
        };

        // Extract response content
        if let Some(content) = result.get("message")
            .and_then(|msg| msg.get("content"))
            .and_then(|content| content.as_str()) {
            Ok(content.to_string())
        } else if let Some(content) = result.get("content")
            .and_then(|content| content.as_str()) {
            Ok(content.to_string())
        } else {
            Err(crate::error::Error::Inference(
                "Invalid response format from llama.cpp".to_string()
            ))
        }
    }

    async fn generate_completion_stream(
        &self,
        request: &InferenceRequest,
    ) -> Result<tokio::sync::mpsc::UnboundedReceiver<String>> {
        if !self.model_loaded {
            return Err(crate::error::Error::ModelNotLoaded);
        }

        let (tx, rx) = tokio::sync::mpsc::unbounded_channel();
        let client = self.client.clone();
        let base_url = self.base_url.clone();
        let model_name = self.model_name.clone();
        let messages = request.messages.clone();

        tokio::spawn(async move {
            let url = format!("{}/api/chat", base_url);
            
            let llama_messages: Vec<Value> = messages.iter().map(|msg| {
                json!({
                    "role": match msg.role {
                        crate::models::MessageRole::User => "user",
                        crate::models::MessageRole::Assistant => "assistant", 
                        crate::models::MessageRole::System => "system",
                    },
                    "content": msg.content
                })
            }).collect();

            let request_body = json!({
                "model": model_name,
                "messages": llama_messages,
                "max_tokens": request.max_tokens.unwrap_or(2048),
                "temperature": request.temperature.unwrap_or(0.7),
                "stream": true
            });

            match client.post(&url).json(&request_body).timeout(Duration::from_secs(60)).await {
                Ok(response) => {
                    if response.status().is_success() {
                        let mut lines = response.bytes_stream();
                        use futures_util::StreamExt;
                        
                        while let Some(chunk_result) = lines.next().await {
                            match chunk_result {
                                Ok(chunk) => {
                                    let chunk_str = String::from_utf8_lossy(&chunk);
                                    for line in chunk_str.lines() {
                                        if line.starts_with("data: ") && !line.contains("[DONE]") {
                                            let data = &line[6..];
                                            if let Ok(parsed) = serde_json::from_str::<Value>(data) {
                                                if let Some(content) = parsed
                                                    .get("message")
                                                    .and_then(|msg| msg.get("content"))
                                                    .and_then(|c| c.as_str()) {
                                                    if tx.send(content.to_string()).is_err() {
                                                        break;
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                                Err(_) => break,
                            }
                        }
                    }
                }
                Err(_) => {
                    let _ = tx.send("Streaming error occurred".to_string());
                }
            }
        });

        Ok(rx)
    }

    fn is_model_loaded(&self) -> bool {
        self.model_loaded
    }

    fn get_model_info(&self) -> Result<crate::models::ModelInfo> {
        Ok(crate::models::ModelInfo {
            id: self.model_name.clone(),
            name: format!("Qwen Model ({})", self.model_name),
            description: "Qwen language model via llama.cpp server".to_string(),
            max_tokens: 4096,
            backend: "llama.cpp".to_string(),
        })
    }
}

impl LlamaCppBackend {
    fn format_messages_as_prompt(&self, messages: &[crate::models::ChatMessage]) -> String {
        messages
            .iter()
            .map(|msg| match msg.role {
                crate::models::MessageRole::User => format!("User: {}", msg.content),
                crate::models::MessageRole::Assistant => format!("Assistant: {}", msg.content),
                crate::models::MessageRole::System => format!("System: {}", msg.content),
            })
            .collect::<Vec<_>>()
            .join("\n")
    }
}

/// Ollama inference backend (fallback)
pub struct OllamaBackend {
    base_url: String,
    client: Client,
}

impl OllamaBackend {
    pub fn new(base_url: String) -> Self {
        Self {
            base_url,
            client: Client::new(),
        }
    }
}

#[async_trait]
impl InferenceBackend for OllamaBackend {
    async fn generate_completion(&self, request: &InferenceRequest) -> Result<String> {
        let url = format!("{}/api/generate", self.base_url);
        
        let ollama_request = json!({
            "model": request.model,
            "prompt": self.format_messages(&request.messages),
            "stream": false,
            "options": {
                "temperature": request.temperature.unwrap_or(0.7),
                "num_predict": request.max_tokens.unwrap_or(4096)
            }
        });

        let response = self.client
            .post(&url)
            .json(&ollama_request)
            .timeout(Duration::from_secs(30))
            .await?;

        if response.status().is_success() {
            let result: Value = response.json().await?;
            if let Some(response_text) = result.get("response").and_then(|v| v.as_str()) {
                Ok(response_text.to_string())
            } else {
                Err(crate::error::Error::Inference("Invalid response from Ollama".to_string()))
            }
        } else {
            Err(crate::error::Error::Inference(format!(
                "Ollama API error: {}",
                response.status()
            )))
        }
    }

    async fn generate_completion_stream(
        &self,
        _request: &InferenceRequest,
    ) -> Result<tokio::sync::mpsc::UnboundedReceiver<String>> {
        let (tx, rx) = tokio::sync::mpsc::unbounded_channel();
        tx.send("Ollama streaming not yet implemented".to_string()).ok();
        Ok(rx)
    }

    fn is_model_loaded(&self) -> bool {
        true // Ollama handles model loading automatically
    }

    fn get_model_info(&self) -> Result<crate::models::ModelInfo> {
        Ok(crate::models::ModelInfo {
            id: "qwen2.5:0.5b".to_string(),
            name: "Qwen 2.5 0.5B".to_string(),
            description: "Qwen language model via Ollama".to_string(),
            max_tokens: 4096,
            backend: "ollama".to_string(),
        })
    }
}

impl OllamaBackend {
    fn format_messages(&self, messages: &[crate::models::ChatMessage]) -> String {
        messages
            .iter()
            .map(|msg| match msg.role {
                crate::models::MessageRole::User => format!("User: {}", msg.content),
                crate::models::MessageRole::Assistant => format!("Assistant: {}", msg.content),
                crate::models::MessageRole::System => format!("System: {}", msg.content),
            })
            .collect::<Vec<_>>()
            .join("\n")
    }
}

/// Factory for creating inference backends
pub fn create_backend(backend_type: crate::config::BackendType, config: &crate::config::InferenceConfig) -> Result<Box<dyn InferenceBackend>> {
    match backend_type {
        crate::config::BackendType::LlamaCpp => {
            let url = config.llamacpp_url.clone().unwrap_or_else(|| "http://localhost:8080".to_string());
            let model = config.model.clone();
            let backend = LlamaCppBackend::new(url, model);
            Ok(Box::new(backend))
        }
        crate::config::BackendType::Ollama => {
            let url = config.ollama_url.clone().unwrap_or_else(|| "http://localhost:11434".to_string());
            let backend = OllamaBackend::new(url);
            Ok(Box::new(backend))
        }
    }
}

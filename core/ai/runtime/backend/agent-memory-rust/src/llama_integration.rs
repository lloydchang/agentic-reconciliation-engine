use crate::{error::Result, models::InferenceRequest};
use async_trait::async_trait;

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

/// Llama.cpp inference backend
pub struct LlamaCppBackend {
    model_path: String,
    model_loaded: bool,
    // In a real implementation, this would contain llama.cpp bindings
    // For now, we'll use a placeholder implementation
}

impl LlamaCppBackend {
    pub fn new(model_path: String) -> Self {
        Self {
            model_path,
            model_loaded: false,
        }
    }

    pub async fn load_model(&mut self) -> Result<()> {
        // In a real implementation, this would load the model using llama.cpp
        // For now, we'll simulate loading
        tokio::time::sleep(tokio::time::Duration::from_millis(1000)).await;
        self.model_loaded = true;
        Ok(())
    }
}

#[async_trait]
impl InferenceBackend for LlamaCppBackend {
    async fn generate_completion(&self, request: &InferenceRequest) -> Result<String> {
        if !self.model_loaded {
            return Err(crate::error::Error::ModelNotLoaded);
        }

        // Simulate inference with llama.cpp
        // In a real implementation, this would call into llama.cpp
        tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
        
        // Generate a mock response based on the last user message
        let last_message = request.messages.last()
            .and_then(|msg| if msg.role == crate::models::MessageRole::User {
                Some(msg.content.clone())
            } else {
                None
            });

        let response = last_message
            .map(|content| format!("I understand you said: '{}'. Here's my response based on Qwen analysis.", content))
            .unwrap_or_else(|| "Hello! I'm Qwen, ready to help with your requests.".to_string());

        Ok(response)
    }

    async fn generate_completion_stream(
        &self,
        request: &InferenceRequest,
    ) -> Result<tokio::sync::mpsc::UnboundedReceiver<String>> {
        if !self.model_loaded {
            return Err(crate::error::Error::ModelNotLoaded);
        }

        let (tx, rx) = tokio::sync::mpsc::unbounded_channel();
        let request_clone = request.clone();

        tokio::spawn(async move {
            // Simulate streaming response
            let response = "This is a streaming response from Qwen via llama.cpp. ".to_string();
            let chars: Vec<char> = response.chars().collect();
            
            for chunk in chars.chunks(5) {
                let chunk_str: String = chunk.iter().collect();
                if tx.send(chunk_str).is_err() {
                    break;
                }
                tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;
            }
        });

        Ok(rx)
    }

    fn is_model_loaded(&self) -> bool {
        self.model_loaded
    }

    fn get_model_info(&self) -> Result<crate::models::ModelInfo> {
        Ok(crate::models::ModelInfo {
            id: "qwen2.5-7b-instruct".to_string(),
            name: "Qwen 2.5 7B Instruct".to_string(),
            description: "Qwen language model for instruction following".to_string(),
            max_tokens: 4096,
            backend: "llama.cpp".to_string(),
        })
    }
}

/// Ollama inference backend (fallback)
pub struct OllamaBackend {
    base_url: String,
    client: reqwest::Client,
}

impl OllamaBackend {
    pub fn new(base_url: String) -> Self {
        Self {
            base_url,
            client: reqwest::Client::new(),
        }
    }
}

#[async_trait]
impl InferenceBackend for OllamaBackend {
    async fn generate_completion(&self, request: &InferenceRequest) -> Result<String> {
        let url = format!("{}/api/generate", self.base_url);
        
        let ollama_request = serde_json::json!({
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
            .send()
            .await?;

        let result: serde_json::Value = response.json().await?;
        
        if let Some(response_text) = result.get("response").and_then(|v| v.as_str()) {
            Ok(response_text.to_string())
        } else {
            Err(crate::error::Error::Inference("Invalid response from Ollama".to_string()))
        }
    }

    async fn generate_completion_stream(
        &self,
        _request: &InferenceRequest,
    ) -> Result<tokio::sync::mpsc::UnboundedReceiver<String>> {
        // For simplicity, return non-streaming response as a single chunk
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
            let backend = LlamaCppBackend::new(config.model.clone());
            Ok(Box::new(backend))
        }
        crate::config::BackendType::Ollama => {
            let url = config.ollama_url.clone().unwrap_or_else(|| "http://localhost:11434".to_string());
            let backend = OllamaBackend::new(url);
            Ok(Box::new(backend))
        }
    }
}

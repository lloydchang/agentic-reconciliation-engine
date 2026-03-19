use reqwest::Client;
use serde_json::{json, Value};
use anyhow::{Result, anyhow};
use std::env;

pub struct QwenClient {
    client: Client,
    backend: LlmBackend,
    model: String,
    api_key: String,
}

#[derive(Debug, Clone)]
pub enum LlmBackend {
    OpenAI {
        base_url: String,
    },
    LlamaCpp {
        client: crate::llamacpp::LlamaCppClient,
    },
    Ollama {
        base_url: String,
    },
}

impl QwenClient {
    pub fn new() -> Result<Self> {
        let backend_priority = env::var("BACKEND_PRIORITY")
            .unwrap_or_else(|_| "llamacpp,openai,ollama".to_string());
        
        let backend = Self::select_backend(&backend_priority)?;
        
        let model = env::var("QWEN_MODEL")
            .unwrap_or_else(|_| "qwen2.5:0.5b".to_string());
        let api_key = env::var("QWEN_API_KEY")
            .unwrap_or_else(|_| "agent-memory-api-key".to_string());

        Ok(Self {
            client: Client::new(),
            backend,
            model,
            api_key,
        })
    }

    fn select_backend(priority: &str) -> Result<LlmBackend> {
        let backends: Vec<&str> = priority.split(',').map(|s| s.trim()).collect();
        
        for backend in backends {
            match backend {
                "llamacpp" => {
                    if let Ok(client) = crate::llamacpp::LlamaCppClient::new() {
                        return Ok(LlmBackend::LlamaCpp { client });
                    }
                },
                "openai" => {
                    let base_url = env::var("QWEN_API_URL")
                        .unwrap_or_else(|_| "http://localhost:8000".to_string());
                    return Ok(LlmBackend::OpenAI { base_url });
                },
                "ollama" => {
                    let base_url = env::var("OLLAMA_API_URL")
                        .unwrap_or_else(|_| "http://localhost:11434".to_string());
                    return Ok(LlmBackend::Ollama { base_url });
                },
                _ => continue,
            }
        }
        
        Err(anyhow!("No suitable LLM backend available"))
    }

    pub async fn initialize(&mut self) -> Result<()> {
        // For LLaMA.cpp, just check if server is ready (don't start it automatically)
        match &self.backend {
            LlmBackend::LlamaCpp { client } => {
                if !client.is_server_ready().await {
                    tracing::warn!("LLaMA.cpp server not ready at {}. Please start llama-server manually.", 
                        env::var("LLAMACPP_API_URL").unwrap_or_else(|_| "http://localhost:8080".to_string()));
                }
            },
            _ => {
                // Other backends don't need initialization
            }
        }
        Ok(())
    }

    pub async fn chat_completion(&self, message: &str, context: Option<&str>) -> Result<String> {
        let mut messages = vec![
            json!({
                "role": "system",
                "content": "You are an AI assistant for infrastructure automation. Analyze the given situation and provide actionable insights based on AGENTS.md policies and available skills."
            })
        ];

        if let Some(ctx) = context {
            messages.push(json!({
                "role": "system", 
                "content": format!("Context: {}", ctx)
            }));
        }

        messages.push(json!({
            "role": "user",
            "content": message
        }));

        match &self.backend {
            LlmBackend::OpenAI { base_url } => {
                self.openai_chat_completion(base_url, &messages).await
            },
            LlmBackend::LlamaCpp { client } => {
                client.chat_completion(messages).await
            },
            LlmBackend::Ollama { base_url } => {
                self.ollama_chat_completion(base_url, &messages).await
            },
        }
    }

    async fn openai_chat_completion(&self, base_url: &str, messages: &[Value]) -> Result<String> {
        let request_body = json!({
            "model": self.model,
            "messages": messages,
            "max_tokens": 2048,
            "temperature": 0.7
        });

        let response = self.client
            .post(&format!("{}/v1/chat/completions", base_url))
            .header("Authorization", format!("Bearer {}", self.api_key))
            .header("Content-Type", "application/json")
            .json(&request_body)
            .send()
            .await?;

        if !response.status().is_success() {
            let error_text = response.text().await?;
            return Err(anyhow!("OpenAI API error: {}", error_text));
        }

        let response_json: Value = response.json().await?;
        
        if let Some(choices) = response_json.get("choices").and_then(|c| c.as_array()) {
            if let Some(choice) = choices.first() {
                if let Some(message) = choice.get("message").and_then(|m| m.get("content")) {
                    return Ok(message.as_str().unwrap_or("").to_string());
                }
            }
        }

        Err(anyhow!("Invalid response format from OpenAI API"))
    }

    async fn ollama_chat_completion(&self, base_url: &str, messages: &[Value]) -> Result<String> {
        // Convert messages to Ollama format
        let prompt = self.messages_to_ollama_prompt(messages)?;

        let request_body = json!({
            "model": self.model,
            "prompt": prompt,
            "stream": false,
            "options": {
                "temperature": 0.7,
                "num_predict": 2048
            }
        });

        let response = self.client
            .post(&format!("{}/api/generate", base_url))
            .header("Content-Type", "application/json")
            .json(&request_body)
            .send()
            .await?;

        if !response.status().is_success() {
            let error_text = response.text().await?;
            return Err(anyhow!("Ollama API error: {}", error_text));
        }

        let response_json: Value = response.json().await?;
        
        if let Some(response) = response_json.get("response").and_then(|r| r.as_str()) {
            Ok(response.to_string())
        } else {
            Err(anyhow!("Invalid response format from Ollama API"))
        }
    }

    fn messages_to_ollama_prompt(&self, messages: &[Value]) -> Result<String> {
        let mut prompt = String::new();

        for message in messages {
            if let (Some(role), Some(content)) = (
                message.get("role").and_then(|r| r.as_str()),
                message.get("content").and_then(|c| c.as_str())
            ) {
                match role {
                    "system" => {
                        prompt.push_str(&format!("System: {}\n\n", content));
                    },
                    "user" => {
                        prompt.push_str(&format!("User: {}\n", content));
                    },
                    "assistant" => {
                        prompt.push_str(&format!("Assistant: {}\n", content));
                    },
                    _ => {
                        prompt.push_str(&format!("{}: {}\n", role, content));
                    }
                }
            }
        }

        prompt.push_str("Assistant: ");
        Ok(prompt)
    }

    pub async fn analyze_event(&self, event: &crate::models::EventPayload) -> Result<String> {
        let analysis_prompt = format!(
            "Analyze this infrastructure event:\n\nType: {}\nComponent: {}\nSeverity: {}\nDescription: {}\n\nProvide analysis including:\n1. Root cause assessment\n2. Recommended skill to address this\n3. Risk level (low/medium/high)\n4. Suggested remediation steps",
            event.event_type,
            event.component.as_deref().unwrap_or("unknown"),
            event.severity.as_deref().unwrap_or("unknown"),
            event.description.as_deref().unwrap_or("no description")
        );

        // Get relevant context from memory
        let context = self.get_relevant_context(&event.component).await?;
        
        self.chat_completion(&analysis_prompt, Some(&context)).await
    }

    pub async fn select_skill(&self, problem_description: &str, available_skills: &[String]) -> Result<String> {
        let skill_list = available_skills.join("\n");
        let prompt = format!(
            "Given this problem: {}\n\nAvailable skills:\n{}\n\nSelect the most appropriate skill and explain why.",
            problem_description, skill_list
        );

        self.chat_completion(&prompt, None).await
    }

    async fn get_relevant_context(&self, component: &Option<String>) -> Result<String> {
        // This would query the database for relevant historical context
        // For now, return a placeholder
        if let Some(comp) = component {
            Ok(format!("Historical context for component: {}", comp))
        } else {
            Ok("No specific component context available".to_string())
        }
    }

    pub async fn generate_execution_plan(&self, skill_name: &str, input_data: &Value) -> Result<Vec<String>> {
        let prompt = format!(
            "Generate a step-by-step execution plan for skill '{}' with this input:\n{}\n\nProvide specific, actionable steps.",
            skill_name, input_data
        );

        let response = self.chat_completion(&prompt, None).await?;
        
        // Parse the response into steps
        let steps: Vec<String> = response
            .lines()
            .filter(|line| line.trim().starts_with("-") || line.trim().starts_with("*") || line.trim().matches(char::is_numeric).count() > 0)
            .map(|line| line.trim().trim_start_matches("-").trim_start_matches("*").trim().to_string())
            .filter(|step| !step.is_empty())
            .collect();

        Ok(steps)
    }
}

use crate::{
    error::Result,
    llama_integration::{create_backend, InferenceBackend},
    models::{InferenceRequest, InferenceResponse, ChatMessage, MessageRole, TokenUsage, Choice},
    config::InferenceConfig,
};
use chrono::Utc;
use serde_json::json;
use uuid::Uuid;

/// Inference service for handling LLM requests
pub struct InferenceService {
    backend: Box<dyn InferenceBackend>,
    config: InferenceConfig,
}

impl InferenceService {
    pub fn new(config: InferenceConfig) -> Result<Self> {
        let backend = create_backend(config.backend.clone(), &config)?;
        Ok(Self { backend, config })
    }

    pub async fn initialize(&mut self) -> Result<()> {
        // For llama.cpp backend, we might need to load the model
        if let Some(llama_backend) = self.backend.as_any_mut().downcast_mut::<crate::llama_integration::LlamaCppBackend>() {
            llama_backend.load_model().await?;
        }
        Ok(())
    }

    pub async fn generate_completion(&self, request: &InferenceRequest) -> Result<InferenceResponse> {
        let start_time = Utc::now();
        
        // Validate request
        self.validate_request(request)?;
        
        // Generate completion
        let response_text = self.backend.generate_completion(request).await?;
        
        // Create response
        let response = InferenceResponse {
            id: Uuid::new_v4().to_string(),
            model: request.model.clone(),
            choices: vec![Choice {
                index: 0,
                message: ChatMessage {
                    role: MessageRole::Assistant,
                    content: response_text,
                },
                finish_reason: Some("stop".to_string()),
            }],
            usage: TokenUsage {
                prompt_tokens: self.estimate_tokens(&request.messages),
                completion_tokens: self.estimate_tokens(&[ChatMessage {
                    role: MessageRole::Assistant,
                    content: response_text.clone(),
                }]),
                total_tokens: 0, // Will be calculated below
            },
            created: start_time,
        };

        // Calculate total tokens
        let mut response = response;
        response.usage.total_tokens = response.usage.prompt_tokens + response.usage.completion_tokens;

        Ok(response)
    }

    pub async fn generate_completion_stream(
        &self,
        request: &InferenceRequest,
    ) -> Result<tokio::sync::mpsc::UnboundedReceiver<String>> {
        self.validate_request(request)?;
        self.backend.generate_completion_stream(request).await
    }

    pub fn is_model_loaded(&self) -> bool {
        self.backend.is_model_loaded()
    }

    pub fn get_model_info(&self) -> Result<crate::models::ModelInfo> {
        self.backend.get_model_info()
    }

    pub fn health_check(&self) -> Result<crate::models::HealthResponse> {
        let model_loaded = self.is_model_loaded();
        let model_info = self.get_model_info().ok();

        Ok(crate::models::HealthResponse {
            status: if model_loaded { "healthy" } else { "loading" }.to_string(),
            model_loaded,
            version: "1.0.0".to_string(),
            backend: match self.config.backend {
                crate::config::BackendType::LlamaCpp => "llama.cpp".to_string(),
                crate::config::BackendType::Ollama => "ollama".to_string(),
            },
            uptime_seconds: 0, // Would track actual uptime
        })
    }

    fn validate_request(&self, request: &InferenceRequest) -> Result<()> {
        if request.messages.is_empty() {
            return Err(crate::error::Error::InvalidRequest("No messages provided".to_string()));
        }

        if request.max_tokens.unwrap_or(4096) > 4096 {
            return Err(crate::error::Error::InvalidRequest("Max tokens exceeds limit".to_string()));
        }

        let temp = request.temperature.unwrap_or(0.7);
        if temp < 0.0 || temp > 2.0 {
            return Err(crate::error::Error::InvalidRequest("Temperature must be between 0.0 and 2.0".to_string()));
        }

        Ok(())
    }

    fn estimate_tokens(&self, messages: &[ChatMessage]) -> u32 {
        // Rough estimation: ~4 characters per token
        let total_chars: usize = messages.iter().map(|m| m.content.len()).sum();
        (total_chars / 4) as u32
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::{InferenceConfig, BackendType};

    #[tokio::test]
    async fn test_inference_service_creation() {
        let config = InferenceConfig {
            backend: BackendType::LlamaCpp,
            model: "test-model".to_string(),
            max_tokens: 4096,
            temperature: 0.7,
            ollama_url: None,
        };

        let service = InferenceService::new(config);
        assert!(service.is_ok());
    }

    #[tokio::test]
    async fn test_request_validation() {
        let config = InferenceConfig {
            backend: BackendType::LlamaCpp,
            model: "test-model".to_string(),
            max_tokens: 4096,
            temperature: 0.7,
            ollama_url: None,
        };

        let service = InferenceService::new(config).unwrap();
        
        // Test empty messages
        let request = InferenceRequest {
            model: "test".to_string(),
            messages: vec![],
            max_tokens: None,
            temperature: None,
            stream: None,
        };
        
        let result = service.generate_completion(&request).await;
        assert!(result.is_err());
    }
}

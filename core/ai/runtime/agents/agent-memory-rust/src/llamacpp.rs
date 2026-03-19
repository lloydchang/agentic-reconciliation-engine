use reqwest::Client;
use serde_json::{json, Value};
use anyhow::{Result, anyhow};
use std::env;

pub struct LlamaCppClient {
    client: Client,
    base_url: String,
    model: String,
}

impl LlamaCppClient {
    pub fn new() -> Result<Self> {
        let base_url = env::var("LLAMACPP_API_URL")
            .unwrap_or_else(|_| "http://localhost:8080".to_string());
        let model = env::var("LLAMACPP_MODEL")
            .unwrap_or_else(|_| "qwen2.5:0.5b".to_string());

        Ok(Self {
            client: Client::new(),
            base_url,
            model,
        })
    }

    pub async fn is_server_ready(&self) -> bool {
        let url = format!("{}/health", self.base_url);
        
        match self.client.get(&url).send().await {
            Ok(response) => response.status().is_success(),
            Err(_) => false,
        }
    }

    pub async fn chat_completion(&self, messages: Vec<Value>) -> Result<String> {
        let url = format!("{}/v1/chat/completions", self.base_url);

        let request_body = json!({
            "model": self.model,
            "messages": messages,
            "max_tokens": 2048,
            "temperature": 0.7,
            "stream": false
        });

        let response = self.client
            .post(&url)
            .header("Content-Type", "application/json")
            .header("Authorization", "Bearer no-key")
            .json(&request_body)
            .send()
            .await?;

        if !response.status().is_success() {
            let error_text = response.text().await?;
            return Err(anyhow!("LLaMA.cpp API error: {}", error_text));
        }

        let response_json: Value = response.json().await?;
        
        if let Some(choices) = response_json.get("choices").and_then(|c| c.as_array()) {
            if let Some(choice) = choices.first() {
                if let Some(message) = choice.get("message").and_then(|m| m.get("content")) {
                    return Ok(message.as_str().unwrap_or("").to_string());
                }
            }
        }

        Err(anyhow!("Invalid response format from LLaMA.cpp"))
    }

    pub async fn analyze_event(&self, event: &crate::models::EventPayload) -> Result<String> {
        let analysis_prompt = format!(
            "Analyze this infrastructure event:\n\nType: {}\nComponent: {}\nSeverity: {}\nDescription: {}\n\nProvide analysis including:\n1. Root cause assessment\n2. Recommended skill to address this\n3. Risk level (low/medium/high)\n4. Suggested remediation steps",
            event.event_type,
            event.component.as_deref().unwrap_or("unknown"),
            event.severity.as_deref().unwrap_or("unknown"),
            event.description.as_deref().unwrap_or("no description")
        );

        let messages = vec![
            json!({
                "role": "system",
                "content": "You are an AI assistant for infrastructure automation. Analyze the given situation and provide actionable insights based on AGENTS.md policies and available skills."
            }),
            json!({
                "role": "user",
                "content": analysis_prompt
            })
        ];

        self.chat_completion(messages).await
    }

    pub async fn select_skill(&self, problem_description: &str, available_skills: &[String]) -> Result<String> {
        let skill_list = available_skills.join("\n");
        let prompt = format!(
            "Given this problem: {}\n\nAvailable skills:\n{}\n\nSelect the most appropriate skill and explain why.",
            problem_description, skill_list
        );

        let messages = vec![
            json!({
                "role": "system",
                "content": "You are an AI assistant that selects appropriate skills for infrastructure automation tasks."
            }),
            json!({
                "role": "user", 
                "content": prompt
            })
        ];

        self.chat_completion(messages).await
    }

    pub async fn generate_execution_plan(&self, skill_name: &str, input_data: &Value) -> Result<Vec<String>> {
        let prompt = format!(
            "Generate a step-by-step execution plan for skill '{}' with this input:\n{}\n\nProvide specific, actionable steps.",
            skill_name, input_data
        );

        let messages = vec![
            json!({
                "role": "system",
                "content": "You are an AI assistant that creates execution plans for infrastructure automation skills."
            }),
            json!({
                "role": "user",
                "content": prompt
            })
        ];

        let response = self.chat_completion(messages).await?;
        
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

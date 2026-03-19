use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::env;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub server: ServerConfig,
    pub database: DatabaseConfig,
    pub inference: InferenceConfig,
    pub auth: AuthConfig,
    pub metrics: MetricsConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    pub bind_address: String,
    pub port: u16,
    pub max_connections: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseConfig {
    pub path: String,
    pub max_connections: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InferenceConfig {
    pub backend: BackendType,
    pub model: String,
    pub max_tokens: usize,
    pub temperature: f32,
    pub ollama_url: Option<String>,
    pub llamacpp_url: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum BackendType {
    #[serde(rename = "llama.cpp")]
    LlamaCpp,
    Ollama,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthConfig {
    pub enabled: bool,
    pub jwt_secret: Option<String>,
    pub api_keys: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetricsConfig {
    pub enabled: bool,
    pub bind_address: String,
    pub port: u16,
}

impl Config {
    pub fn from_env() -> Result<Self> {
        let server = ServerConfig {
            bind_address: env::var("BIND_ADDRESS").unwrap_or_else(|_| "0.0.0.0".to_string()),
            port: env::var("PORT")
                .unwrap_or_else(|_| "8080".to_string())
                .parse()?,
            max_connections: env::var("MAX_CONNECTIONS")
                .unwrap_or_else(|_| "1000".to_string())
                .parse()?,
        };

        let database = DatabaseConfig {
            path: env::var("DATABASE_PATH").unwrap_or_else(|_| "/data/memory.db".to_string()),
            max_connections: env::var("DB_MAX_CONNECTIONS")
                .unwrap_or_else(|_| "10".to_string())
                .parse()?,
        };

        let inference = InferenceConfig {
            backend: env::var("BACKEND_TYPE")
                .unwrap_or_else(|_| "llama.cpp".to_string())
                .parse()?,
            model: env::var("MODEL").unwrap_or_else(|_| "qwen2.5:0.5b".to_string()),
            max_tokens: env::var("MAX_TOKENS")
                .unwrap_or_else(|_| "4096".to_string())
                .parse()?,
            temperature: env::var("TEMPERATURE")
                .unwrap_or_else(|_| "0.7".to_string())
                .parse()?,
            ollama_url: env::var("OLLAMA_URL").ok(),
            llamacpp_url: env::var("LLAMACPP_URL").ok(),
        };

        let auth = AuthConfig {
            enabled: env::var("AUTH_ENABLED")
                .unwrap_or_else(|_| "true".to_string())
                .parse()?,
            jwt_secret: env::var("JWT_SECRET").ok(),
            api_keys: env::var("API_KEYS")
                .unwrap_or_else(|_| "".to_string())
                .split(',')
                .map(|s| s.trim().to_string())
                .filter(|s| !s.is_empty())
                .collect(),
        };

        let metrics = MetricsConfig {
            enabled: env::var("METRICS_ENABLED")
                .unwrap_or_else(|_| "true".to_string())
                .parse()?,
            bind_address: env::var("METRICS_BIND_ADDRESS")
                .unwrap_or_else(|_| "0.0.0.0".to_string()),
            port: env::var("METRICS_PORT")
                .unwrap_or_else(|_| "9090".to_string())
                .parse()?,
        };

        Ok(Config {
            server,
            database,
            inference,
            auth,
            metrics,
        })
    }
}

impl std::str::FromStr for BackendType {
    type Err = anyhow::Error;

    fn from_str(s: &str) -> Result<Self> {
        match s.to_lowercase().as_str() {
            "llama.cpp" | "llama-cpp" => Ok(BackendType::LlamaCpp),
            "ollama" => Ok(BackendType::Ollama),
            _ => Err(anyhow::anyhow!("Invalid backend type: {}", s)),
        }
    }
}

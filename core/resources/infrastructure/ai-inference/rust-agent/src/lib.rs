use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Arc;
use std::time::Duration;

use anyhow::{Context, Result};
use axum::{
    extract::{Query, State},
    http::StatusCode,
    response::Json,
    routing::{delete, get, post},
    Router,
};
use chrono::{DateTime, Utc};
use futures::future::join_all;
use notify::{Config, RecommendedWatcher, RecursiveMode, Watcher};
use reqwest::Client;
use rusqlite::{params, Connection, OptionalExtension};
use serde::{Deserialize, Serialize};
use tokio::sync::RwLock;
use tokio::time;
use tower_http::cors::CorsLayer;
use tracing::{error, info, warn};

// Constants
const OLLAMA_BASE_URL: &str = "http://localhost:11434";
const MODEL: &str = "qwen2.5:0.5b";
const MAX_SEARCH_RESULTS: usize = 5;
const SEARCH_TIMEOUT: Duration = Duration::from_secs(10);

// Configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum BackendType {
    LlamaCpp,
    Ollama,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum LanguageType {
    Rust,
    Go,
    Python,
}

#[derive(Debug, Clone)]
pub struct AgentConfig {
    pub backend_priority: Vec<BackendType>,
    pub language_priority: Vec<LanguageType>,
    pub ollama_url: String,
    pub model: String,
    pub llama_cpp_model_path: Option<PathBuf>,
}

// Backend trait for inference
#[async_trait::async_trait]
pub trait InferenceBackend: Send + Sync {
    async fn generate(&self, prompt: &str) -> Result<String>;
    fn name(&self) -> &'static str;
}

// Ollama backend implementation
pub struct OllamaBackend {
    http_client: Client,
    base_url: String,
    model: String,
}

impl OllamaBackend {
    pub fn new(base_url: String, model: String) -> Result<Self> {
        let http_client = Client::builder()
            .timeout(Duration::from_secs(60))
            .build()?;

        Ok(Self {
            http_client,
            base_url,
            model,
        })
    }
}

#[async_trait::async_trait]
impl InferenceBackend for OllamaBackend {
    async fn generate(&self, prompt: &str) -> Result<String> {
        let request_body = serde_json::json!({
            "model": self.model,
            "prompt": prompt,
            "stream": false
        });

        let response = self.http_client
            .post(&format!("{}/api/generate", self.base_url))
            .json(&request_body)
            .send()
            .await?;

        if !response.status().is_success() {
            let error_text = response.text().await?;
            return Err(anyhow::anyhow!("Ollama API error {}: {}", response.status(), error_text));
        }

        let ollama_resp: OllamaResponse = response.json().await?;
        Ok(ollama_resp.response.trim().to_string())
    }

    fn name(&self) -> &'static str {
        "Ollama"
    }
}

// llama.cpp backend implementation
pub struct LlamaCppBackend {
    model: llama_cpp_2::LlamaModel,
    context: llama_cpp_2::LlamaContext,
}

impl LlamaCppBackend {
    pub fn new(model_path: PathBuf) -> Result<Self> {
        // Load the model
        let model_params = llama_cpp_2::LlamaModelParams::default();
        let model = llama_cpp_2::LlamaModel::load_from_file(&model_path, model_params)?;

        // Create context
        let context_params = llama_cpp_2::LlamaContextParams::default();
        let context = model.new_context(context_params)?;

        Ok(Self { model, context })
    }
}

#[async_trait::async_trait]
impl InferenceBackend for LlamaCppBackend {
    async fn generate(&self, prompt: &str) -> Result<String> {
        // Create a sampler for text generation
        let sampler = llama_cpp_2::Sampler::default();

        // Tokenize the prompt
        let tokens = self.context.tokenize(prompt, llama_cpp_2::AddBos::Always, true)?;

        // Evaluate the prompt tokens
        self.context.decode(&tokens)?;

        // Generate response tokens
        let mut generated_tokens = Vec::new();
        let mut max_tokens = 256; // Limit response length

        while generated_tokens.len() < max_tokens {
            // Sample next token
            let token = sampler.sample(&self.context, 0)?;
            generated_tokens.push(token);

            // Check for end of text token
            if token == self.model.token_eos() {
                break;
            }

            // Decode the new token
            self.context.decode(&[token])?;
        }

        // Detokenize to get the response text
        let response = self.context.detokenize(&generated_tokens, true)?;
        Ok(response.trim().to_string())
    }

    fn name(&self) -> &'static str {
        "llama.cpp"
    }
}

#[derive(Debug, Serialize, Deserialize)]
struct OllamaResponse {
    response: String,
}

// Memory agent implementation
pub struct MemoryAgent {
    db: Arc<RwLock<Connection>>,
    backends: Vec<Box<dyn InferenceBackend>>,
    search_client: Client,
    inbox_path: PathBuf,
    config: AgentConfig,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Memory {
    pub id: i64,
    pub source: String,
    pub raw_text: String,
    pub summary: String,
    pub entities: Vec<String>,
    pub topics: Vec<String>,
    pub connections: Vec<Connection>,
    pub importance: f64,
    pub created_at: DateTime<Utc>,
    pub consolidated: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Connection {
    pub from_id: i64,
    pub to_id: i64,
    pub relationship: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Consolidation {
    pub id: i64,
    pub source_ids: Vec<i64>,
    pub summary: String,
    pub insight: String,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResult {
    pub title: String,
    pub body: String,
    pub url: String,
    pub source: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct OllamaResponse {
    response: String,
}

#[derive(Debug, Deserialize)]
pub struct IngestRequest {
    pub text: String,
    pub source: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct QueryRequest {
    pub q: String,
    pub search: Option<bool>,
}

#[derive(Debug, Deserialize)]
pub struct DeleteRequest {
    pub memory_id: i64,
}

#[derive(Debug, Deserialize)]
pub struct SearchRequest {
    pub query: String,
}

// Application state
#[derive(Clone)]
pub struct AppState {
    agent: Arc<MemoryAgent>,
}

// Memory agent implementation
pub struct MemoryAgent {
    db: Arc<RwLock<Connection>>,
    http_client: Client,
    search_client: Client,
    inbox_path: PathBuf,
}

impl MemoryAgent {
    pub async fn new(db_path: &str, inbox_path: &str, config: AgentConfig) -> Result<Self> {
        let conn = Connection::open(db_path)
            .with_context(|| format!("Failed to open database at {}", db_path))?;

        Self::init_db(&conn).await?;

        // Initialize backends based on configuration priority
        let mut backends: Vec<Box<dyn InferenceBackend>> = Vec::new();

        for backend_type in &config.backend_priority {
            match backend_type {
                BackendType::LlamaCpp => {
                    if let Some(model_path) = &config.llama_cpp_model_path {
                        match LlamaCppBackend::new(model_path.clone()) {
                            Ok(backend) => {
                                backends.push(Box::new(backend));
                                info!("✅ Initialized llama.cpp backend");
                            }
                            Err(e) => {
                                warn!("Failed to initialize llama.cpp backend: {}", e);
                            }
                        }
                    }
                }
                BackendType::Ollama => {
                    match OllamaBackend::new(config.ollama_url.clone(), config.model.clone()) {
                        Ok(backend) => {
                            backends.push(Box::new(backend));
                            info!("✅ Initialized Ollama backend");
                        }
                        Err(e) => {
                            warn!("Failed to initialize Ollama backend: {}", e);
                        }
                    }
                }
            }
        }

        // Ensure we have at least one backend
        if backends.is_empty() {
            return Err(anyhow::anyhow!("No inference backends could be initialized"));
        }

        let search_client = Client::builder()
            .timeout(SEARCH_TIMEOUT)
            .user_agent("MemoryAgent/1.0")
            .build()?;

        Ok(Self {
            db: Arc::new(RwLock::new(conn)),
            backends,
            search_client,
            inbox_path: PathBuf::from(inbox_path),
            config,
        })
    }

    async fn init_db(conn: &Connection) -> Result<()> {
        conn.execute(
            "CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL DEFAULT '',
                raw_text TEXT NOT NULL,
                summary TEXT NOT NULL,
                entities TEXT NOT NULL DEFAULT '[]',
                topics TEXT NOT NULL DEFAULT '[]',
                connections TEXT NOT NULL DEFAULT '[]',
                importance REAL NOT NULL DEFAULT 0.5,
                created_at TEXT NOT NULL,
                consolidated INTEGER NOT NULL DEFAULT 0
            )",
            [],
        )?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS consolidations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_ids TEXT NOT NULL,
                summary TEXT NOT NULL,
                insight TEXT NOT NULL,
                created_at TEXT NOT NULL
            )",
            [],
        )?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS processed_files (
                path TEXT PRIMARY KEY,
                processed_at TEXT NOT NULL
            )",
            [],
        )?;

        Ok(())
    }

    pub async fn generate(&self, prompt: &str) -> Result<String> {
        for backend in &self.backends {
            match backend.generate(prompt).await {
                Ok(response) => {
                    info!("✅ Generated response using {}", backend.name());
                    return Ok(response);
                }
                Err(e) => {
                    warn!("❌ {} backend failed: {}", backend.name(), e);
                    continue;
                }
            }
        }
        Err(anyhow::anyhow!("All inference backends failed"))
    }

    pub async fn ingest(&self, content: &str, source: &str) -> Result<Memory> {
        let prompt = format!(
            "You are a Memory Ingest Agent. Process this information into structured memory.

Input: {}

Extract and return ONLY a JSON object with these fields:
{{
    \"summary\": \"1-2 sentence summary\",
    \"entities\": [\"key people/companies/products/concepts\"],
    \"topics\": [\"2-4 topic tags\"],
    \"importance\": 0.0-1.0
}}

Be concise and accurate.",
            text
        );

        let response = self.generate(&prompt).await?;
        let data: serde_json::Value = serde_json::from_str(&response).unwrap_or_else(|_| {
            // Fallback
            serde_json::json!({
                "summary": format!("{}...", &text[..200.min(text.len())]),
                "entities": [],
                "topics": [],
                "importance": 0.5
            })
        });

        let summary = data["summary"].as_str().unwrap_or("Summary unavailable").to_string();
        let entities: Vec<String> = data["entities"]
            .as_array()
            .unwrap_or(&vec![])
            .iter()
            .filter_map(|v| v.as_str().map(|s| s.to_string()))
            .collect();
        let topics: Vec<String> = data["topics"]
            .as_array()
            .unwrap_or(&vec![])
            .iter()
            .filter_map(|v| v.as_str().map(|s| s.to_string()))
            .collect();
        let importance = data["importance"].as_f64().unwrap_or(0.5);

        let db = self.db.read().await;
        let result = db.execute(
            "INSERT INTO memories (source, raw_text, summary, entities, topics, importance, created_at)
             VALUES (?, ?, ?, ?, ?, ?, ?)",
            params![
                source,
                text,
                summary,
                serde_json::to_string(&entities)?,
                serde_json::to_string(&topics)?,
                importance,
                Utc::now().to_rfc3339(),
            ],
        )?;

        let id = db.last_insert_rowid();

        info!("📥 Stored memory #{}: {}...", id, &summary[..60.min(summary.len())]);

        Ok(Memory {
            id,
            source: source.to_string(),
            raw_text: text.to_string(),
            summary,
            entities,
            topics,
            connections: vec![],
            importance,
            created_at: Utc::now(),
            consolidated: false,
        })
    }

    pub async fn consolidate(&self) -> Result<String> {
        let db = self.db.read().await;
        let mut stmt = db.prepare(
            "SELECT id, summary, entities, topics, importance FROM memories
             WHERE consolidated = 0 ORDER BY created_at DESC LIMIT 10"
        )?;

        let memory_rows = stmt.query_map([], |row| {
            Ok((
                row.get::<_, i64>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, String>(2)?,
                row.get::<_, String>(3)?,
                row.get::<_, f64>(4)?,
            ))
        })?;

        let mut memories = Vec::new();
        let mut source_ids = Vec::new();

        for row_result in memory_rows {
            let (id, summary, entities_str, topics_str, importance) = row_result?;
            let entities: Vec<String> = serde_json::from_str(&entities_str).unwrap_or_default();
            let topics: Vec<String> = serde_json::from_str(&topics_str).unwrap_or_default();

            memories.push(format!(
                "Memory {}: {} (Entities: {}) (Topics: {})",
                id,
                summary,
                entities.join(", "),
                topics.join(", ")
            ));
            source_ids.push(id);
        }

        drop(stmt);

        if memories.len() < 2 {
            return Ok("Need at least 2 unconsolidated memories for consolidation".to_string());
        }

        let context = format!("Memories:\n{}", memories.join("\n"));
        let prompt = format!(
            "You are a Memory Consolidation Agent. Analyze these memories and find connections/patterns.

{}

Return ONLY a JSON object with:
{{
    \"source_ids\": {:?},
    \"summary\": \"synthesized summary across memories\",
    \"insight\": \"one key pattern/insight discovered\",
    \"connections\": [{{\"from_id\": id, \"to_id\": id, \"relationship\": \"description\"}}]
}}

Be thorough but concise.",
            context, source_ids
        );

        let response = self.generate(&prompt).await?;
        let data: serde_json::Value = serde_json::from_str(&response).unwrap_or_else(|_| {
            serde_json::json!({
                "source_ids": source_ids,
                "summary": "Consolidation summary unavailable",
                "insight": "No insight generated",
                "connections": []
            })
        });

        if let Some(ids) = data["source_ids"].as_array() {
            let summary = data["summary"].as_str().unwrap_or("Summary unavailable");
            let insight = data["insight"].as_str().unwrap_or("No insight");
            let connections = data["connections"].as_array().unwrap_or(&vec![]);

            // Store consolidation
            db.execute(
                "INSERT INTO consolidations (source_ids, summary, insight, created_at) VALUES (?, ?, ?, ?)",
                params![
                    serde_json::to_string(&ids.iter().filter_map(|v| v.as_i64()).collect::<Vec<_>>())?,
                    summary,
                    insight,
                    Utc::now().to_rfc3339(),
                ],
            )?;

            // Update connections and mark as consolidated
            for conn in connections {
                if let (Some(from_id), Some(to_id), Some(rel)) = (
                    conn["from_id"].as_i64(),
                    conn["to_id"].as_i64(),
                    conn["relationship"].as_str(),
                ) {
                    for &mid in &[from_id, to_id] {
                        let existing: String = db.query_row(
                            "SELECT connections FROM memories WHERE id = ?",
                            [mid],
                            |row| row.get(0),
                        ).unwrap_or_else(|_| "[]".to_string());

                        let mut conns: Vec<serde_json::Value> = serde_json::from_str(&existing).unwrap_or_default();
                        conns.push(serde_json::json!({
                            "from_id": from_id,
                            "to_id": to_id,
                            "relationship": rel
                        }));

                        db.execute(
                            "UPDATE memories SET connections = ? WHERE id = ?",
                            params![serde_json::to_string(&conns)?, mid],
                        )?;
                    }
                }
            }

            // Mark memories as consolidated
            for &id in &source_ids {
                db.execute("UPDATE memories SET consolidated = 1 WHERE id = ?", [id])?;
            }

            info!("🔄 Consolidated {} memories. Insight: {}", source_ids.len(), &insight[..80.min(insight.len())]);
            Ok(format!("Consolidated {} memories. Insight: {}", source_ids.len(), insight))
        } else {
            Ok("No consolidation needed".to_string())
        }
    }

    pub async fn query(&self, question: &str, use_search: bool) -> Result<String> {
        let db = self.db.read().await;

        // Get memories
        let mut stmt = db.prepare("SELECT summary, source FROM memories ORDER BY created_at DESC LIMIT 20")?;
        let memory_rows = stmt.query_map([], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?))
        })?;

        let mut context = "Stored Memories:\n".to_string();
        for row in memory_rows {
            let (summary, source) = row?;
            context.push_str(&format!("[{}] {}\n", source, summary));
        }

        // Get recent consolidations
        let mut stmt = db.prepare("SELECT insight FROM consolidations ORDER BY created_at DESC LIMIT 5")?;
        let consolidation_rows = stmt.query_map([], |row| Ok(row.get::<_, String>(0)?))?;

        let mut has_consolidations = false;
        for row in consolidation_rows {
            let insight = row?;
            if !has_consolidations {
                context.push_str("\nConsolidation Insights:\n");
                has_consolidations = true;
            }
            context.push_str(&format!("- {}\n", insight));
        }

        // Decide if we need to search
        let mut search_needed = false;
        if use_search {
            let search_prompt = format!(
                "Based on this question and available memories, do we need current web information?

Question: {}

Available memories cover: {}

Should we search the internet for additional grounding? Answer only YES or NO.",
                question,
                &context[..200.min(context.len())]
            );

            let search_decision = self.ollama_generate(&search_prompt).await?;
            search_needed = search_decision.to_uppercase().contains("YES");
        }

        let mut search_results = String::new();
        if search_needed {
            info!("🔍 Searching web for: {}", question);
            if let Ok(results) = self.search_web(question).await {
                if !results.is_empty() {
                    search_results = format!(
                        "\n\nWeb Search Results:\n{}",
                        results.iter()
                            .map(|r| format!("- {}: {}... ({})", r.title, &r.body[..200.min(r.body.len())], r.url))
                            .collect::<Vec<_>>()
                            .join("\n")
                    );
                    info!("📊 Found {} search results", results.len());
                }
            }
        }

        let prompt = format!(
            "You are a Memory Query Agent. Answer this question using stored memories and web search results if available.

Question: {}

{}{}

Provide a comprehensive answer. Reference sources when using web search. Be thorough but concise.",
            question, context, search_results
        );

        self.ollama_generate(&prompt).await
    }

    pub async fn search_web(&self, query: &str) -> Result<Vec<SearchResult>> {
        let encoded_query = urlencoding::encode(query);
        let url = format!("https://duckduckgo.com/html/?q={}", encoded_query);

        let response = self.search_client.get(&url).send().await?;
        if !response.status().is_success() {
            return Err(anyhow::anyhow!("Search request failed with status {}", response.status()));
        }

        let html = response.text().await?;
        let mut results = Vec::new();

        // Very basic HTML parsing - extract titles (simplified)
        let title_regex = regex::Regex::new(r#"<a class="result__a"[^>]*>([^<]+)</a>"#)?;
        for capture in title_regex.captures_iter(&html) {
            if let Some(title_match) = capture.get(1) {
                let title = title_match.as_str().to_string();
                results.push(SearchResult {
                    title,
                    body: "Search result snippet".to_string(),
                    url: "#".to_string(),
                    source: "DuckDuckGo".to_string(),
                });

                if results.len() >= MAX_SEARCH_RESULTS {
                    break;
                }
            }
        }

        Ok(results)
    }

    pub async fn get_status(&self) -> Result<serde_json::Value> {
        let db = self.db.read().await;

        let total: i64 = db.query_row("SELECT COUNT(*) FROM memories", [], |row| row.get(0))?;
        let unconsolidated: i64 = db.query_row("SELECT COUNT(*) FROM memories WHERE consolidated = 0", [], |row| row.get(0))?;
        let consolidations: i64 = db.query_row("SELECT COUNT(*) FROM consolidations", [], |row| row.get(0))?;

        Ok(serde_json::json!({
            "total_memories": total,
            "unconsolidated": unconsolidated,
            "consolidations": consolidations,
            "model": MODEL,
            "ollama_url": OLLAMA_BASE_URL
        }))
    }

    pub async fn get_memories(&self) -> Result<Vec<Memory>> {
        let db = self.db.read().await;
        let mut stmt = db.prepare(
            "SELECT id, source, summary, entities, topics, connections, importance, created_at, consolidated
             FROM memories ORDER BY created_at DESC LIMIT 50"
        )?;

        let rows = stmt.query_map([], |row| {
            let entities: Vec<String> = serde_json::from_str(&row.get::<_, String>(3)?).unwrap_or_default();
            let topics: Vec<String> = serde_json::from_str(&row.get::<_, String>(4)?).unwrap_or_default();
            let connections: Vec<Connection> = serde_json::from_str(&row.get::<_, String>(5)?).unwrap_or_default();
            let created_at: DateTime<Utc> = row.get::<_, String>(7)?.parse().unwrap_or(Utc::now());

            Ok(Memory {
                id: row.get(0)?,
                source: row.get(1)?,
                summary: row.get(2)?,
                entities,
                topics,
                connections,
                importance: row.get(6)?,
                created_at,
                consolidated: row.get::<_, i64>(8)? != 0,
            })
        })?;

        let mut memories = Vec::new();
        for row in rows {
            memories.push(row?);
        }

        Ok(memories)
    }

    pub async fn delete_memory(&self, memory_id: i64) -> Result<bool> {
        let db = self.db.read().await;
        let rows_affected = db.execute("DELETE FROM memories WHERE id = ?", [memory_id])?;
        Ok(rows_affected > 0)
    }
}

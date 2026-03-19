use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize)]
pub struct EventPayload {
    pub event_type: String,
    pub namespace: Option<String>,
    pub component: Option<String>,
    pub severity: Option<String>,
    pub description: Option<String>,
    pub timestamp: Option<DateTime<Utc>>,
    pub analysis_context: Option<String>,
    pub correlation_id: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ChatRequest {
    pub message: String,
    pub max_tokens: Option<u32>,
    pub temperature: Option<f32>,
    pub context: Option<String>,
    pub session_id: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ChatResponse {
    pub response: String,
    pub session_id: String,
    pub context_used: Vec<String>,
    pub confidence: f32,
    pub tokens_used: u32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HealthResponse {
    pub status: String,
    pub version: String,
    pub uptime_seconds: u64,
    pub database_connected: bool,
    pub llm_backend: String,
    pub memory_stats: MemoryStats,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MemoryStats {
    pub episodes_count: u64,
    pub semantic_concepts_count: u64,
    pub procedural_patterns_count: u64,
    pub active_sessions_count: u64,
    pub pending_events_count: u64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SkillExecutionRequest {
    pub skill_name: String,
    pub input_data: serde_json::Value,
    pub context: Option<String>,
    pub dry_run: Option<bool>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SkillExecutionResponse {
    pub workflow_id: String,
    pub status: String,
    pub result: Option<serde_json::Value>,
    pub execution_plan: Option<Vec<String>>,
    pub risk_level: Option<String>,
    pub human_gate_required: Option<bool>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EventIngestionResponse {
    pub event_id: String,
    pub status: String,
    pub correlation_id: String,
    pub workflow_triggered: bool,
    pub message: String,
}

// Database models
#[derive(Debug, Serialize, Deserialize, sqlx::FromRow)]
pub struct Event {
    pub id: String,
    pub event_type: String,
    pub source: String,
    pub namespace: Option<String>,
    pub component: Option<String>,
    pub severity: Option<String>,
    pub description: Option<String>,
    pub payload: Option<String>,
    pub correlation_id: Option<String>,
    pub status: String,
    pub created_at: DateTime<Utc>,
    pub processed_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Serialize, Deserialize, sqlx::FromRow)]
pub struct Workflow {
    pub id: String,
    pub workflow_type: String,
    pub skill_name: Option<String>,
    pub status: String,
    pub input_data: Option<String>,
    pub output_data: Option<String>,
    pub error_message: Option<String>,
    pub execution_time_ms: Option<i64>,
    pub created_at: DateTime<Utc>,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Serialize, Deserialize, sqlx::FromRow)]
pub struct Incident {
    pub id: String,
    pub title: String,
    pub description: Option<String>,
    pub severity: Option<String>,
    pub status: String,
    pub component: Option<String>,
    pub namespace: Option<String>,
    pub resolution: Option<String>,
    pub rollback_actions: Option<String>,
    pub lessons_learned: Option<String>,
    pub created_at: DateTime<Utc>,
    pub resolved_at: Option<DateTime<Utc>>,
}

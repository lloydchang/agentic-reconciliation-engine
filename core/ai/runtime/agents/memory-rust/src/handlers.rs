use axum::{
    extract::{Path, State, Query},
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use sqlx::SqlitePool;
use std::collections::HashMap;
use std::env;
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;
use uuid::Uuid;
use chrono::Utc;

use crate::models::*;
use crate::qwen::QwenClient;
use crate::database::initialize_database;

#[derive(Clone)]
pub struct AppState {
    pub pool: SqlitePool,
    pub qwen_client: QwenClient,
    pub start_time: std::time::Instant,
}

#[derive(Deserialize)]
pub struct EventQuery {
    pub correlation_id: Option<String>,
    pub status: Option<String>,
    pub limit: Option<u32>,
}

pub async fn create_app() -> Result<Router, Box<dyn std::error::Error>> {
    // Initialize database
    let database_url = env::var("DATABASE_PATH")
        .unwrap_or_else(|_| "sqlite:/data/memory.db".to_string());
    
    let pool = initialize_database(&database_url).await?;
    
    // Initialize Qwen client
    let qwen_client = QwenClient::new()?;
    
    let state = AppState {
        pool,
        qwen_client,
        start_time: std::time::Instant::now(),
    };

    let app = Router::new()
        .route("/api/health", get(health_check))
        .route("/api/events", post(ingest_event))
        .route("/api/events", get(list_events))
        .route("/api/events/:id", get(get_event))
        .route("/api/chat", post(chat_completion))
        .route("/api/skills/execute", post(execute_skill))
        .route("/api/skills/list", get(list_skills))
        .route("/api/workflows", get(list_workflows))
        .route("/api/incidents", get(list_incidents))
        .route("/metrics", get(prometheus_metrics))
        .layer(TraceLayer::new_for_http())
        .layer(CorsLayer::permissive())
        .with_state(state);

    Ok(app)
}

pub async fn health_check(State(state): State<AppState>) -> Json<HealthResponse> {
    let database_connected = state.pool.acquire().await.is_ok();
    
    let memory_stats = get_memory_stats(&state.pool).await.unwrap_or_default();
    
    Json(HealthResponse {
        status: if database_connected { "healthy" } else { "unhealthy" }.to_string(),
        version: "0.1.0".to_string(),
        uptime_seconds: state.start_time.elapsed().as_secs(),
        database_connected,
        llm_backend: "qwen".to_string(),
        memory_stats,
    })
}

pub async fn ingest_event(
    State(state): State<AppState>,
    Json(payload): Json<EventPayload>,
) -> Result<Json<EventIngestionResponse>, StatusCode> {
    let event_id = Uuid::new_v4().to_string();
    let correlation_id = payload.correlation_id.clone()
        .unwrap_or_else(|| Uuid::new_v4().to_string());
    
    // Store event in database
    let event = crate::models::Event {
        id: event_id.clone(),
        event_type: payload.event_type.clone(),
        source: "argo-events".to_string(),
        namespace: payload.namespace.clone(),
        component: payload.component.clone(),
        severity: payload.severity.clone(),
        description: payload.description.clone(),
        payload: Some(serde_json::to_string(&payload).unwrap_or_default()),
        correlation_id: Some(correlation_id.clone()),
        status: "pending".to_string(),
        created_at: Utc::now(),
        processed_at: None,
    };
    
    if let Err(_) = store_event(&state.pool, &event).await {
        return Err(StatusCode::INTERNAL_SERVER_ERROR);
    }
    
    // Analyze event with Qwen
    let analysis = state.qwen_client.analyze_event(&payload).await;
    let workflow_triggered = analysis.is_ok();
    
    // Update event status
    update_event_status(&state.pool, &event_id, if workflow_triggered { "analyzed" } else { "failed" }).await;
    
    Ok(Json(EventIngestionResponse {
        event_id,
        status: "processed".to_string(),
        correlation_id,
        workflow_triggered,
        message: "Event ingested successfully".to_string(),
    }))
}

pub async fn chat_completion(
    State(state): State<AppState>,
    Json(request): Json<ChatRequest>,
) -> Result<Json<ChatResponse>, StatusCode> {
    let session_id = request.session_id.clone()
        .unwrap_or_else(|| Uuid::new_v4().to_string());
    
    // Get context from memory if available
    let context = get_session_context(&state.pool, &session_id).await.unwrap_or_default();
    
    // Call Qwen
    let response = state.qwen_client.chat_completion(&request.message, Some(&context))
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    // Store conversation in episodes
    store_episode(&state.pool, &session_id, &request.message, &response).await;
    
    Ok(Json(ChatResponse {
        response,
        session_id,
        context_used: vec!["historical_context".to_string()],
        confidence: 0.8,
        tokens_used: 150, // This would come from the actual API response
    }))
}

pub async fn execute_skill(
    State(state): State<AppState>,
    Json(request): Json<SkillExecutionRequest>,
) -> Result<Json<SkillExecutionResponse>, StatusCode> {
    let workflow_id = Uuid::new_v4().to_string();
    
    // Create workflow record
    let workflow = crate::models::Workflow {
        id: workflow_id.clone(),
        workflow_type: "skill_execution".to_string(),
        skill_name: Some(request.skill_name.clone()),
        status: "pending".to_string(),
        input_data: Some(serde_json::to_string(&request.input_data).unwrap_or_default()),
        output_data: None,
        error_message: None,
        execution_time_ms: None,
        created_at: Utc::now(),
        started_at: None,
        completed_at: None,
    };
    
    if let Err(_) = store_workflow(&state.pool, &workflow).await {
        return Err(StatusCode::INTERNAL_SERVER_ERROR);
    }
    
    // Generate execution plan using Qwen
    let execution_plan = state.qwen_client.generate_execution_plan(&request.skill_name, &request.input_data)
        .await
        .unwrap_or_default();
    
    // Determine risk level (simplified)
    let risk_level = determine_risk_level(&request.skill_name);
    
    Ok(Json(SkillExecutionResponse {
        workflow_id,
        status: "planned".to_string(),
        result: None,
        execution_plan: Some(execution_plan),
        risk_level,
        human_gate_required: Some(risk_level == "high"),
    }))
}

pub async fn list_events(
    State(state): State<AppState>,
    Query(query): Query<EventQuery>,
) -> Result<Json<Vec<Event>>, StatusCode> {
    let events = query_events(&state.pool, query.correlation_id, query.status, query.limit.unwrap_or(50))
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    Ok(Json(events))
}

pub async fn get_event(
    State(state): State<AppState>,
    Path(event_id): Path<String>,
) -> Result<Json<Event>, StatusCode> {
    let event = get_event_by_id(&state.pool, &event_id)
        .await
        .map_err(|_| StatusCode::NOT_FOUND)?;
    
    Ok(Json(event))
}

pub async fn list_skills(
    State(state): State<AppState>,
) -> Result<Json<Vec<String>>, StatusCode> {
    // This would scan the skills directory
    let skills = vec![
        "optimize-costs".to_string(),
        "analyze-security".to_string(),
        "troubleshoot-kubernetes".to_string(),
        "manage-certificates".to_string(),
        "scale-resources".to_string(),
    ];
    
    Ok(Json(skills))
}

pub async fn list_workflows(
    State(state): State<AppState>,
) -> Result<Json<Vec<Workflow>>, StatusCode> {
    let workflows = get_recent_workflows(&state.pool, 50)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    Ok(Json(workflows))
}

pub async fn list_incidents(
    State(state): State<AppState>,
) -> Result<Json<Vec<Incident>>, StatusCode> {
    let incidents = get_recent_incidents(&state.pool, 50)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    Ok(Json(incidents))
}

pub async fn prometheus_metrics(State(state): State<AppState>) -> String {
    let stats = get_memory_stats(&state.pool).await.unwrap_or_default();
    
    format!(
        "# HELP agent_memory_episodes_total Total number of episodes in memory\n\
         # TYPE agent_memory_episodes_total counter\n\
         agent_memory_episodes_total {}\n\
         # HELP agent_memory_events_pending_total Number of pending events\n\
         # TYPE agent_memory_events_pending_total gauge\n\
         agent_memory_events_pending_total {}\n\
         # HELP agent_memory_workflows_total Total number of workflows\n\
         # TYPE agent_memory_workflows_total counter\n\
         agent_memory_workflows_total {}\n\
         # HELP agent_memory_uptime_seconds Service uptime in seconds\n\
         # TYPE agent_memory_uptime_seconds gauge\n\
         agent_memory_uptime_seconds {}\n",
        stats.episodes_count,
        stats.pending_events_count,
        stats.procedural_patterns_count,
        state.start_time.elapsed().as_secs()
    )
}

// Database helper functions
async fn store_event(pool: &SqlitePool, event: &Event) -> Result<(), sqlx::Error> {
    sqlx::query(
        r#"
        INSERT INTO events (id, event_type, source, namespace, component, severity, description, payload, correlation_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        "#,
    )
    .bind(&event.id)
    .bind(&event.event_type)
    .bind(&event.source)
    .bind(&event.namespace)
    .bind(&event.component)
    .bind(&event.severity)
    .bind(&event.description)
    .bind(&event.payload)
    .bind(&event.correlation_id)
    .bind(&event.status)
    .bind(&event.created_at)
    .execute(pool)
    .await?;
    
    Ok(())
}

async fn update_event_status(pool: &SqlitePool, event_id: &str, status: &str) -> Result<(), sqlx::Error> {
    sqlx::query("UPDATE events SET status = ?, processed_at = CURRENT_TIMESTAMP WHERE id = ?")
        .bind(status)
        .bind(event_id)
        .execute(pool)
        .await?;
    
    Ok(())
}

async fn store_episode(pool: &SqlitePool, session_id: &str, message: &str, response: &str) -> Result<(), sqlx::Error> {
    let episode_id = Uuid::new_v4().to_string();
    
    sqlx::query(
        "INSERT INTO episodes (id, session_id, content, metadata) VALUES (?, ?, ?, ?)"
    )
    .bind(&episode_id)
    .bind(session_id)
    .bind(&format!("User: {}\nAssistant: {}", message, response))
    .bind(serde_json::json!({"type": "chat"}).to_string())
    .execute(pool)
    .await?;
    
    Ok(())
}

async fn store_workflow(pool: &SqlitePool, workflow: &Workflow) -> Result<(), sqlx::Error> {
    sqlx::query(
        r#"
        INSERT INTO workflows (id, workflow_type, skill_name, status, input_data, output_data, error_message, execution_time_ms, created_at, started_at, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        "#,
    )
    .bind(&workflow.id)
    .bind(&workflow.workflow_type)
    .bind(&workflow.skill_name)
    .bind(&workflow.status)
    .bind(&workflow.input_data)
    .bind(&workflow.output_data)
    .bind(&workflow.error_message)
    .bind(&workflow.execution_time_ms)
    .bind(&workflow.created_at)
    .bind(&workflow.started_at)
    .bind(&workflow.completed_at)
    .execute(pool)
    .await?;
    
    Ok(())
}

async fn query_events(pool: &SqlitePool, correlation_id: Option<String>, status: Option<String>, limit: u32) -> Result<Vec<Event>, sqlx::Error> {
    let mut query = "SELECT * FROM events".to_string();
    let mut conditions = Vec::new();
    
    if correlation_id.is_some() {
        conditions.push("correlation_id = ?".to_string());
    }
    if status.is_some() {
        conditions.push("status = ?".to_string());
    }
    
    if !conditions.is_empty() {
        query.push_str(" WHERE ");
        query.push_str(&conditions.join(" AND "));
    }
    
    query.push_str(" ORDER BY created_at DESC LIMIT ?");
    
    let mut q = sqlx::query_as::<_, Event>(&query).bind(limit as i64);
    
    if let Some(ref cid) = correlation_id {
        q = q.bind(cid);
    }
    if let Some(ref s) = status {
        q = q.bind(s);
    }
    
    let events = q.fetch_all(pool).await?;
    Ok(events)
}

async fn get_event_by_id(pool: &SqlitePool, event_id: &str) -> Result<Event, sqlx::Error> {
    let event = sqlx::query_as::<_, Event>("SELECT * FROM events WHERE id = ?")
        .bind(event_id)
        .fetch_one(pool)
        .await?;
    
    Ok(event)
}

async fn get_session_context(pool: &SqlitePool, session_id: &str) -> Result<String, sqlx::Error> {
    let episodes: Vec<String> = sqlx::query_as(
        "SELECT content FROM episodes WHERE session_id = ? ORDER BY created_at DESC LIMIT 5"
    )
    .bind(session_id)
    .fetch_all(pool)
    .await?;
    
    Ok(episodes.join("\n"))
}

async fn get_memory_stats(pool: &SqlitePool) -> Result<MemoryStats, sqlx::Error> {
    let episodes_count: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM episodes")
        .fetch_one(pool)
        .await?;
    
    let semantic_count: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM semantic_memory")
        .fetch_one(pool)
        .await?;
    
    let procedural_count: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM procedural_memory")
        .fetch_one(pool)
        .await?;
    
    let pending_events: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM events WHERE status = 'pending'")
        .fetch_one(pool)
        .await?;
    
    Ok(MemoryStats {
        episodes_count: episodes_count as u64,
        semantic_concepts_count: semantic_count as u64,
        procedural_patterns_count: procedural_count as u64,
        active_sessions_count: 0, // Would need to track this separately
        pending_events_count: pending_events as u64,
    })
}

async fn get_recent_workflows(pool: &SqlitePool, limit: u32) -> Result<Vec<Workflow>, sqlx::Error> {
    let workflows = sqlx::query_as::<_, Workflow>("SELECT * FROM workflows ORDER BY created_at DESC LIMIT ?")
        .bind(limit as i64)
        .fetch_all(pool)
        .await?;
    
    Ok(workflows)
}

async fn get_recent_incidents(pool: &SqlitePool, limit: u32) -> Result<Vec<Incident>, sqlx::Error> {
    let incidents = sqlx::query_as::<_, Incident>("SELECT * FROM incidents ORDER BY created_at DESC LIMIT ?")
        .bind(limit as i64)
        .fetch_all(pool)
        .await?;
    
    Ok(incidents)
}

fn determine_risk_level(skill_name: &str) -> &str {
    match skill_name {
        "optimize-costs" => "medium",
        "analyze-security" => "high",
        "manage-certificates" => "high",
        "scale-resources" => "medium",
        "troubleshoot-kubernetes" => "low",
        _ => "medium",
    }
}

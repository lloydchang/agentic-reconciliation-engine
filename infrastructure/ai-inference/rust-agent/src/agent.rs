use std::env;
use std::path::Path;
use std::sync::Arc;
use std::time::Duration;

use axum::{
    extract::{Query, State},
    http::StatusCode,
    response::Json,
    routing::{delete, get, post},
    Router,
};
use tokio::signal;
use tokio::sync::RwLock;
use tower_http::cors::CorsLayer;
use tracing::{info, Level};
use tracing_subscriber::FmtSubscriber;

use memory_agent::{
    AgentConfig, AppState, BackendType, Consolidation, DeleteRequest, IngestRequest, LanguageType,
    Memory, MemoryAgent, QueryRequest, SearchRequest,
};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing
    let subscriber = FmtSubscriber::builder()
        .with_max_level(Level::INFO)
        .finish();
    tracing::subscriber::set_global_default(subscriber)?;

    // Configuration
    let db_path = env::var("MEMORY_DB").unwrap_or_else(|_| "memory.db".to_string());
    let inbox_path = env::var("INBOX_PATH").unwrap_or_else(|_| "./inbox".to_string());
    let port = env::var("PORT")
        .unwrap_or_else(|_| "8888".to_string())
        .parse::<u16>()?;
    let consolidate_interval_minutes = env::var("CONSOLIDATE_INTERVAL_MINUTES")
        .unwrap_or_else(|_| "30".to_string())
        .parse::<u64>()?;

    info!("🧠 Enhanced Always-On Memory Agent starting");
    info!("   Model: {}", memory_agent::MODEL);
    info!("   Ollama URL: {}", memory_agent::OLLAMA_BASE_URL);
    info!("   Database: {}", db_path);
    info!("   Watch: {}", inbox_path);
    info!("   Consolidate: every {}m", consolidate_interval_minutes);
    info!("   Internet Search: Enabled via DuckDuckGo");
    info!("   API: http://localhost:{}", port);
    info!("");

    // Create inbox directory if it doesn't exist
    std::fs::create_dir_all(&inbox_path)?;

    // Initialize memory agent
    let agent = Arc::new(MemoryAgent::new(&db_path, &inbox_path, config).await?);

    // Setup file watcher
    let agent_clone = Arc::clone(&agent);
    let inbox_path_clone = inbox_path.clone();
    tokio::spawn(async move {
        if let Err(e) = watch_files(agent_clone, &inbox_path_clone).await {
            tracing::error!("File watcher error: {}", e);
        }
    });

    // Setup consolidation timer
    let agent_clone = Arc::clone(&agent);
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_secs(consolidate_interval_minutes * 60));
        loop {
            interval.tick().await;
            if let Err(e) = run_consolidation(&agent_clone).await {
                tracing::error!("Consolidation error: {}", e);
            }
        }
    });

    // Build application
    let app_state = AppState { agent: Arc::clone(&agent) };

    let app = Router::new()
        .route("/query", get(handle_query))
        .route("/ingest", post(handle_ingest))
        .route("/consolidate", post(handle_consolidate))
        .route("/status", get(handle_status))
        .route("/memories", get(handle_memories))
        .route("/delete", delete(handle_delete))
        .route("/search", post(handle_search))
        .layer(CorsLayer::permissive())
        .with_state(app_state);

    // Start server
    let addr = format!("0.0.0.0:{}", port).parse()?;
    info!("✅ Agent running. Drop files in {}/ or POST to http://localhost:{}/ingest", inbox_path, port);
    info!("   Internet search available for enhanced responses");
    info!("");

    let listener = tokio::net::TcpListener::bind(&addr).await?;
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    info!("🧠 Agent stopped.");
    Ok(())
}

async fn shutdown_signal() {
    let ctrl_c = async {
        signal::ctrl_c()
            .await
            .expect("failed to install Ctrl+C handler");
    };

    #[cfg(unix)]
    let terminate = async {
        signal::unix::signal(signal::unix::SignalKind::terminate())
            .expect("failed to install signal handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {},
        _ = terminate => {},
    }

    info!("👋 Shutting down gracefully...");
}

async fn watch_files(agent: Arc<MemoryAgent>, inbox_path: &str) -> anyhow::Result<()> {
    use notify::{Config, Event, EventKind, RecommendedWatcher, RecursiveMode, Watcher};
    use std::sync::mpsc;

    info!("👁️  Watching: {}/", inbox_path);

    let (tx, rx) = mpsc::channel();
    let mut watcher = RecommendedWatcher::new(tx, Config::default())?;
    watcher.watch(Path::new(inbox_path), RecursiveMode::Recursive)?;

    loop {
        match rx.recv() {
            Ok(event) => {
                if let Event { kind: EventKind::Create(_), paths, .. } = event {
                    for path in paths {
                        if let Some(file_name) = path.file_name() {
                            if file_name.to_string_lossy().starts_with('.') {
                                continue;
                            }

                            // Check if it's a text file or supported media
                            let extension = path.extension()
                                .and_then(|ext| ext.to_str())
                                .unwrap_or("")
                                .to_lowercase();

                            let supported_extensions = [
                                "txt", "md", "json", "csv", "log", "xml", "yaml", "yml",
                            ];

                            if supported_extensions.contains(&extension.as_str()) {
                                info!("📄 New text file: {:?}", file_name);

                                match tokio::fs::read_to_string(&path).await {
                                    Ok(content) if !content.trim().is_empty() => {
                                        if let Err(e) = agent.ingest(&content, &file_name.to_string_lossy()).await {
                                            error!("Failed to ingest file {:?}: {}", file_name, e);
                                        }
                                    }
                                    Ok(_) => {
                                        warn!("Empty file: {:?}", file_name);
                                    }
                                    Err(e) => {
                                        error!("Failed to read file {:?}: {}", file_name, e);
                                    }
                                }
                            } else {
                                warn!("⚠️  Skipping unsupported file: {:?}", file_name);
                            }
                        }
                    }
                }
            }
            Err(e) => {
                error!("Watch error: {}", e);
                break;
            }
        }
    }

    Ok(())
}

async fn run_consolidation(agent: &MemoryAgent) -> anyhow::Result<()> {
    let db = agent.db.read().await;
    let unconsolidated: i64 = db.query_row(
        "SELECT COUNT(*) FROM memories WHERE consolidated = 0",
        [],
        |row| row.get(0)
    )?;

    if unconsolidated >= 2 {
        info!("🔄 Running consolidation ({} unconsolidated memories)...", unconsolidated);
        let result = agent.consolidate().await?;
        info!("🔄 {}", result);
    } else {
        info!("🔄 Skipping consolidation ({} unconsolidated memories)", unconsolidated);
    }

    Ok(())
}

// HTTP handlers
async fn handle_query(
    State(state): State<AppState>,
    Query(params): Query<QueryRequest>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    let use_search = params.search.unwrap_or(true);

    match state.agent.query(&params.q, use_search).await {
        Ok(answer) => Ok(Json(serde_json::json!({
            "question": params.q,
            "answer": answer,
            "search_used": use_search
        }))),
        Err(e) => {
            error!("Query error: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn handle_ingest(
    State(state): State<AppState>,
    Json(req): Json<IngestRequest>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    let source = req.source.unwrap_or_else(|| "api".to_string());

    match state.agent.ingest(&req.text, &source).await {
        Ok(memory) => Ok(Json(serde_json::json!({
            "status": "ingested",
            "memory": memory
        }))),
        Err(e) => {
            error!("Ingest error: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn handle_consolidate(
    State(state): State<AppState>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    match state.agent.consolidate().await {
        Ok(result) => Ok(Json(serde_json::json!({
            "status": "done",
            "response": result
        }))),
        Err(e) => {
            error!("Consolidate error: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn handle_status(
    State(state): State<AppState>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    match state.agent.get_status().await {
        Ok(status) => Ok(Json(status)),
        Err(e) => {
            error!("Status error: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn handle_memories(
    State(state): State<AppState>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    match state.agent.get_memories().await {
        Ok(memories) => Ok(Json(serde_json::json!({
            "memories": memories,
            "count": memories.len()
        }))),
        Err(e) => {
            error!("Memories error: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn handle_delete(
    State(state): State<AppState>,
    Json(req): Json<DeleteRequest>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    match state.agent.delete_memory(req.memory_id).await {
        Ok(deleted) => {
            if deleted {
                Ok(Json(serde_json::json!({
                    "status": "deleted",
                    "memory_id": req.memory_id
                })))
            } else {
                Err(StatusCode::NOT_FOUND)
            }
        }
        Err(e) => {
            error!("Delete error: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn handle_search(
    State(state): State<AppState>,
    Json(req): Json<SearchRequest>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    // Direct search without LLM decision
    match state.agent.search_web(&req.query).await {
        Ok(results) => Ok(Json(serde_json::json!({
            "query": req.query,
            "results": results
        }))),
        Err(e) => {
            error!("Search error: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

use axum::Router;
use std::env;
use std::net::SocketAddr;
use tower::ServiceBuilder;
use tower_http::trace::TraceLayer;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

mod database;
mod models;
mod qwen;
mod handlers;
mod skills;
mod workflows;
mod events;
mod integration;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load environment variables
    dotenv::dotenv().ok();
    
    // Initialize tracing
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            env::var("RUST_LOG").unwrap_or_else(|_| "agent_memory=debug,tower_http=debug".into()),
        ))
        .with(tracing_subscriber::fmt::layer())
        .init();

    // Initialize skill engine
    let skills_directory = env::var("SKILLS_DIRECTORY")
        .unwrap_or_else(|_| "/opt/skills".to_string());
    let mut skill_engine = skills::SkillEngine::new(skills_directory);
    skill_engine.load_skills().await?;

    // Initialize Qwen client and LLM backend
    let mut qwen_client = qwen::QwenClient::new()?;
    qwen_client.initialize().await?;

    // Initialize workflow engine
    let mut workflow_engine = workflows::WorkflowEngine::new(skill_engine);
    workflow_engine.initialize_workflows().await?;

    // Initialize event processor
    let event_processor = events::EventProcessor::new();

    // Create integration state
    let integration_state = integration::IntegrationState {
        event_processor,
        workflow_engine,
        skill_engine: skills::SkillEngine::new(
            env::var("SKILLS_DIRECTORY")
                .unwrap_or_else(|_| "/opt/skills".to_string())
        ),
    };

    // Create application
    let app = handlers::create_app().await?;
    let integration_routes = integration::create_integration_routes(integration_state);
    let app = app.merge(integration_routes);
    
    // Configure server
    let bind_address = env::var("BIND_ADDRESS")
        .unwrap_or_else(|_| "0.0.0.0".to_string());
    let port: u16 = env::var("PORT")
        .unwrap_or_else(|_| "8080".to_string())
        .parse()
        .unwrap_or(8080);
    
    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    
    tracing::info!("Agent Memory Service starting on {}", addr);
    tracing::info!("Available endpoints:");
    tracing::info!("  - GET  /api/health");
    tracing::info!("  - POST /api/events");
    tracing::info!("  - POST /api/chat");
    tracing::info!("  - POST /api/skills/execute");
    tracing::info!("  - GET  /api/integration/alerts");
    tracing::info!("  - POST /api/integration/workflows/trigger");
    tracing::info!("  - GET  /metrics");
    
    // Run server
    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;
    
    Ok(())
}

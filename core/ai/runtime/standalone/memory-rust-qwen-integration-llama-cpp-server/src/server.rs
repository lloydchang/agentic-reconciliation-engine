use crate::{
    config::Config,
    database::Database,
    error::Result,
    inference::InferenceService,
    models::{ChatRequest, ChatResponse, MessageRole, TokenUsage, Conversation, Message},
    auth::AuthService,
    metrics::{Metrics, RequestTimer},
};
use axum::{
    extract::{Path, Query, State},
    http::{StatusCode, HeaderMap},
    response::Json,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use std::{collections::HashMap, sync::Arc, time::Instant};
use tower::ServiceBuilder;
use tower_http::{
    cors::{Any, CorsLayer},
    trace::TraceLayer,
};
use tracing::{info, warn, error};

/// HTTP server for the agent memory service
pub struct Server {
    config: Config,
    database: Arc<Database>,
    inference_service: Arc<InferenceService>,
    auth: AuthService,
    metrics: Metrics,
}

#[derive(Debug, Deserialize)]
pub struct ChatQuery {
    pub conversation_id: Option<String>,
    pub context: Option<String>,
    pub max_tokens: Option<usize>,
    pub temperature: Option<f32>,
    pub stream: Option<bool>,
}

#[derive(Debug, Deserialize)]
pub struct ConversationQuery {
    pub limit: Option<u32>,
}

#[derive(Debug, Deserialize)]
pub struct SearchQuery {
    pub q: String,
    pub limit: Option<u32>,
}

#[derive(Debug, Serialize)]
pub struct ApiResponse<T> {
    pub success: bool,
    pub data: Option<T>,
    pub error: Option<String>,
}

impl<T> ApiResponse<T> {
    pub fn success(data: T) -> Self {
        Self {
            success: true,
            data: Some(data),
            error: None,
        }
    }

    pub fn error(message: String) -> Self {
        Self {
            success: false,
            data: None,
            error: Some(message),
        }
    }
}

impl Server {
    pub fn new(config: Config) -> Result<Self> {
        let database = Arc::new(Database::new(&config.database.path)?);
        let mut inference_service = InferenceService::new(config.inference.clone())?;
        
        // Initialize inference service (load model if needed)
        tokio::spawn({
            let mut service = inference_service.clone();
            async move {
                if let Err(e) = service.initialize().await {
                    error!("Failed to initialize inference service: {}", e);
                }
            }
        });

        let auth = AuthService::new(
            config.auth.jwt_secret.clone(),
            config.auth.api_keys.clone(),
            config.auth.enabled,
        );

        let metrics = Metrics::new()?;

        Ok(Self {
            config,
            database,
            inference_service: Arc::new(inference_service),
            auth,
            metrics,
        })
    }

    pub async fn run(self) -> Result<()> {
        let app = self.create_router();

        let bind_address = self.config.server.bind_address.clone();
        let port = self.config.server.port;

        info!("Starting server on {}:{}", bind_address, port);

        let listener = tokio::net::TcpListener::bind(format!("{}:{}", bind_address, port)).await?;
        axum::serve(listener, app).await?;

        Ok(())
    }

    fn create_router(self) -> Router {
        let app_state = Arc::new(self);

        Router::new()
            // Health endpoints
            .route("/api/health", get(health_check))
            .route("/api/health/backend", get(backend_health))
            
            // Chat endpoints
            .route("/api/v1/chat", post(chat_completion))
            .route("/api/v1/chat/stream", post(chat_completion_stream))
            
            // Conversation endpoints
            .route("/api/conversations", get(list_conversations))
            .route("/api/conversations/:id", get(get_conversation))
            .route("/api/conversations/:id/messages", get(get_messages))
            
            // Knowledge endpoints
            .route("/api/knowledge", post(create_knowledge))
            .route("/api/search", get(search_knowledge))
            
            // Model endpoints
            .route("/api/v1/models", get(list_models))
            .route("/api/v1/models/:model", get(get_model_info))
            
            // Metrics endpoint
            .route("/metrics", get(prometheus_metrics))
            
            // Add middleware
            .layer(
                ServiceBuilder::new()
                    .layer(TraceLayer::new_for_http())
                    .layer(CorsLayer::new().allow_origin(Any).allow_methods(Any).allow_headers(Any))
            )
            
            .with_state(app_state)
    }

    async fn authenticate_request(&self, headers: &HeaderMap) -> Result<String> {
        if !self.auth.enabled {
            return Ok("anonymous".to_string());
        }

        if let Some(api_key) = headers.get("x-api-key") {
            let key_str = api_key.to_str().map_err(|_| {
                crate::error::Error::Authentication("Invalid API key header".to_string())
            })?;
            
            if self.auth.validate_api_key(key_str)? {
                return Ok("api_key".to_string());
            }
        }

        if let Some(auth_header) = headers.get("authorization") {
            let auth_str = auth_header.to_str().map_err(|_| {
                crate::error::Error::Authentication("Invalid authorization header".to_string())
            })?;
            
            let token = self.auth.extract_token_from_header(auth_str)?;
            let claims = self.auth.validate_token(&token)?;
            
            if self.auth.is_token_expired(&claims) {
                return Err(crate::error::Error::Authentication("Token expired".to_string()));
            }
            
            return Ok(claims.sub);
        }

        Err(crate::error::Error::Authentication("Authentication required".to_string()))
    }
}

// Handler functions
async fn health_check(State(app_state): State<Arc<Server>>) -> Json<ApiResponse<crate::models::HealthResponse>> {
    let health = app_state.inference_service.health_check().unwrap_or_else(|_| {
        crate::models::HealthResponse {
            status: "unhealthy".to_string(),
            model_loaded: false,
            version: "1.0.0".to_string(),
            backend: "unknown".to_string(),
            uptime_seconds: 0,
        }
    });

    Json(ApiResponse::success(health))
}

async fn backend_health(State(app_state): State<Arc<Server>>) -> Json<ApiResponse<crate::models::ModelInfo>> {
    match app_state.inference_service.get_model_info() {
        Ok(info) => Json(ApiResponse::success(info)),
        Err(e) => Json(ApiResponse::error(e.to_string())),
    }
}

async fn chat_completion(
    State(app_state): State<Arc<Server>>,
    headers: HeaderMap,
    Query(query): Query<ChatQuery>,
    Json(request): Json<ChatRequest>,
) -> Result<Json<ApiResponse<ChatResponse>>, StatusCode> {
    let timer = RequestTimer::with_metrics(&app_state.metrics)
        .with_labels("POST", "/api/v1/chat", "success");

    // Authenticate request
    let _user_id = match app_state.authenticate_request(&headers) {
        Ok(id) => id,
        Err(e) => {
            timer.with_labels("POST", "/api/v1/chat", "unauthorized").record();
            return Err(StatusCode::UNAUTHORIZED);
        }
    };

    // Get or create conversation
    let conversation_id = if let Some(id) = query.conversation_id.as_ref().or(request.conversation_id.as_ref()) {
        id.clone()
    } else {
        let conv = Conversation::new(None);
        app_state.database.create_conversation(&conv).map_err(|e| {
            error!("Failed to create conversation: {}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })?;
        conv.id
    };

    // Store user message
    let user_message = Message::new(conversation_id.clone(), MessageRole::User, request.message.clone());
    if let Err(e) = app_state.database.create_message(&user_message) {
        error!("Failed to store user message: {}", e);
    }

    // Build inference request
    let messages = if let Some(context) = query.context.as_ref().or(request.context.as_ref()) {
        vec![
            crate::models::ChatMessage { role: MessageRole::System, content: context.clone() },
            crate::models::ChatMessage { role: MessageRole::User, content: request.message.clone() },
        ]
    } else {
        vec![crate::models::ChatMessage { role: MessageRole::User, content: request.message }]
    };

    let inference_request = crate::models::InferenceRequest {
        model: app_state.config.inference.model.clone(),
        messages,
        max_tokens: query.max_tokens.or(request.max_tokens),
        temperature: query.temperature.or(request.temperature),
        stream: Some(false),
    };

    // Generate completion
    match app_state.inference_service.generate_completion(&inference_request).await {
        Ok(inference_response) => {
            // Store assistant message
            let assistant_message = Message::new(
                conversation_id.clone(),
                MessageRole::Assistant,
                inference_response.choices[0].message.content.clone(),
            );
            if let Err(e) = app_state.database.create_message(&assistant_message) {
                error!("Failed to store assistant message: {}", e);
            }

            let response = ChatResponse {
                id: inference_response.id,
                conversation_id,
                message: inference_response.choices[0].message.content,
                role: inference_response.choices[0].message.role,
                timestamp: chrono::Utc::now(),
                usage: Some(inference_response.usage),
                metadata: None,
            };

            timer.record();
            Ok(Json(ApiResponse::success(response)))
        }
        Err(e) => {
            error!("Inference failed: {}", e);
            timer.with_labels("POST", "/api/v1/chat", "error").record();
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn chat_completion_stream(
    State(app_state): State<Arc<Server>>,
    headers: HeaderMap,
    Query(query): Query<ChatQuery>,
    Json(request): Json<ChatRequest>,
) -> Result<Json<ApiResponse<String>>, StatusCode> {
    // Similar to chat_completion but with streaming
    // For brevity, returning a placeholder response
    Ok(Json(ApiResponse::success("Streaming not yet implemented".to_string())))
}

async fn list_conversations(
    State(app_state): State<Arc<Server>>,
    headers: HeaderMap,
    Query(query): Query<ConversationQuery>,
) -> Result<Json<ApiResponse<Vec<Conversation>>>, StatusCode> {
    let _user_id = app_state.authenticate_request(&headers).map_err(|_| StatusCode::UNAUTHORIZED)?;

    match app_state.database.list_conversations(query.limit) {
        Ok(conversations) => Ok(Json(ApiResponse::success(conversations))),
        Err(e) => {
            error!("Failed to list conversations: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn get_conversation(
    State(app_state): State<Arc<Server>>,
    headers: HeaderMap,
    Path(id): Path<String>,
) -> Result<Json<ApiResponse<Option<Conversation>>>, StatusCode> {
    let _user_id = app_state.authenticate_request(&headers).map_err(|_| StatusCode::UNAUTHORIZED)?;

    match app_state.database.get_conversation(&id) {
        Ok(conversation) => Ok(Json(ApiResponse::success(conversation))),
        Err(e) => {
            error!("Failed to get conversation: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn get_messages(
    State(app_state): State<Arc<Server>>,
    headers: HeaderMap,
    Path(conversation_id): Path<String>,
    Query(query): Query<ConversationQuery>,
) -> Result<Json<ApiResponse<Vec<Message>>>, StatusCode> {
    let _user_id = app_state.authenticate_request(&headers).map_err(|_| StatusCode::UNAUTHORIZED)?;

    match app_state.database.get_messages(&conversation_id, query.limit) {
        Ok(messages) => Ok(Json(ApiResponse::success(messages))),
        Err(e) => {
            error!("Failed to get messages: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn create_knowledge(
    State(app_state): State<Arc<Server>>,
    headers: HeaderMap,
    Json(knowledge): Json<crate::models::KnowledgeBase>,
) -> Result<Json<ApiResponse<String>>, StatusCode> {
    let _user_id = app_state.authenticate_request(&headers).map_err(|_| StatusCode::UNAUTHORIZED)?;

    match app_state.database.create_knowledge(&knowledge) {
        Ok(_) => Ok(Json(ApiResponse::success("Knowledge created".to_string()))),
        Err(e) => {
            error!("Failed to create knowledge: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn search_knowledge(
    State(app_state): State<Arc<Server>>,
    headers: HeaderMap,
    Query(query): Query<SearchQuery>,
) -> Result<Json<ApiResponse<Vec<crate::models::KnowledgeBase>>>, StatusCode> {
    let _user_id = app_state.authenticate_request(&headers).map_err(|_| StatusCode::UNAUTHORIZED)?;

    match app_state.database.search_knowledge(&query.q, query.limit.unwrap_or(10)) {
        Ok(results) => Ok(Json(ApiResponse::success(results))),
        Err(e) => {
            error!("Failed to search knowledge: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn list_models(
    State(app_state): State<Arc<Server>>,
    headers: HeaderMap,
) -> Result<Json<ApiResponse<Vec<crate::models::ModelInfo>>>, StatusCode> {
    let _user_id = app_state.authenticate_request(&headers).map_err(|_| StatusCode::UNAUTHORIZED)?;

    match app_state.inference_service.get_model_info() {
        Ok(info) => Ok(Json(ApiResponse::success(vec![info]))),
        Err(e) => {
            error!("Failed to get model info: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn get_model_info(
    State(app_state): State<Arc<Server>>,
    headers: HeaderMap,
    Path(_model): Path<String>,
) -> Result<Json<ApiResponse<crate::models::ModelInfo>>, StatusCode> {
    let _user_id = app_state.authenticate_request(&headers).map_err(|_| StatusCode::UNAUTHORIZED)?;

    match app_state.inference_service.get_model_info() {
        Ok(info) => Ok(Json(ApiResponse::success(info))),
        Err(e) => {
            error!("Failed to get model info: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn prometheus_metrics(State(app_state): State<Arc<Server>>) -> Result<String, StatusCode> {
    use prometheus::Encoder;
    
    let encoder = prometheus::TextEncoder::new();
    let metric_families = prometheus::gather();
    let mut buffer = Vec::new();
    
    encoder.encode(&metric_families, &mut buffer).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    
    Ok(String::from_utf8(buffer).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?)
}

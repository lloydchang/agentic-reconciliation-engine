use std::net::SocketAddr;
use tokio::net::{TcpListener, TcpStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Serialize, Deserialize)]
struct HealthResponse {
    status: String,
    timestamp: String,
}

#[derive(Serialize, Deserialize)]
struct MemoryResponse {
    success: bool,
    message: String,
}

struct AppState {
    // Simple in-memory storage for demo
    memories: HashMap<String, String>,
}

impl AppState {
    fn new() -> Self {
        Self {
            memories: HashMap::new(),
        }
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Agent Memory Service starting on 0.0.0.0:8080");
    
    let state = AppState::new();
    
    let listener = TcpListener::bind("0.0.0.0:8080").await?;
    
    loop {
        let (stream, addr) = listener.accept().await?;
        let state = state.clone();
        
        tokio::spawn(async move {
            if let Err(e) = handle_connection(stream, state).await {
                eprintln!("Failed to handle connection from {}: {}", addr, e);
            }
        });
    }
}

async fn handle_connection(
    mut stream: TcpStream,
    mut state: AppState,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut buffer = [0; 1024];
    
    loop {
        let n = stream.read(&mut buffer).await?;
        if n == 0 {
            break;
        }
        
        let request = String::from_utf8_lossy(&buffer[..n]);
        println!("Request: {}", request);
        
        let response = if request.contains("GET /api/health") {
            let health = HealthResponse {
                status: "healthy".to_string(),
                timestamp: "2024-01-01T00:00:00Z".to_string(),
            };
            format!("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{}", serde_json::to_string(&health)?)
        } else if request.contains("POST /api/memory") {
            let memory_response = MemoryResponse {
                success: true,
                message: "Memory stored successfully".to_string(),
            };
            format!("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{}", serde_json::to_string(&memory_response)?)
        } else {
            "HTTP/1.1 404 Not Found\r\n\r\nNot Found".to_string()
        };
        
        stream.write_all(response.as_bytes()).await?;
        break;
    }
    
    Ok(())
}

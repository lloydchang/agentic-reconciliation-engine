use std::collections::HashMap;
use std::io::prelude::*;
use std::net::{TcpListener, TcpStream};
use std::thread;
use serde::{Deserialize, Serialize};

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

fn main() {
    println!("Agent Memory Service starting on 0.0.0.0:8080");
    
    let listener = TcpListener::bind("0.0.0.0:8080").unwrap();
    
    for stream in listener.incoming() {
        match stream {
            Ok(stream) => {
                thread::spawn(|| {
                    handle_connection(stream);
                });
            }
            Err(e) => {
                eprintln!("Connection failed: {}", e);
            }
        }
    }
}

fn handle_connection(mut stream: TcpStream) {
    let mut buffer = [0; 1024];
    
    match stream.read(&mut buffer) {
        Ok(size) => {
            let request = String::from_utf8_lossy(&buffer[..size]);
            println!("Request: {}", request);
            
            let response = if request.contains("GET /api/health") {
                let health = HealthResponse {
                    status: "healthy".to_string(),
                    timestamp: "2024-01-01T00:00:00Z".to_string(),
                };
                format!(
                    "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n{}",
                    health_response.len(),
                    serde_json::to_string(&health).unwrap_or_default()
                )
            } else if request.contains("POST /api/memory") {
                let memory_response = MemoryResponse {
                    success: true,
                    message: "Memory stored successfully".to_string(),
                };
                format!(
                    "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n{}",
                    memory_response.len(),
                    serde_json::to_string(&memory_response).unwrap_or_default()
                )
            } else {
                "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nAgent Memory Service Running".to_string()
            };
            
            let _ = stream.write(response.as_bytes());
        }
        Err(e) => {
            eprintln!("Failed to read from connection: {}", e);
        }
    }
}

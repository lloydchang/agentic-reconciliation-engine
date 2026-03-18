use std::collections::HashMap;
use std::io::prelude::*;
use std::net::{TcpListener, TcpStream};
use std::thread;

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
                let health_response = r#"{"status":"healthy","timestamp":"2024-01-01T00:00:00Z"}"#;
                format!(
                    "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n{}",
                    health_response.len(),
                    health_response
                )
            } else if request.contains("POST /api/memory") {
                let memory_response = r#"{"success":true,"message":"Memory stored successfully"}"#;
                format!(
                    "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n{}",
                    memory_response.len(),
                    memory_response
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

use std::env;
use reqwest::{Client, Response};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use tokio;
use warp::{Filter, Reply};

#[derive(Debug, Clone, Serialize, Deserialize)]
struct CostOptimizationRequest {
    cloud_provider: String,
    region: String,
    services: Vec<String>,
    time_range: String,
}

#[derive(Debug, Clone, Serialize)]
struct CostOptimizationResponse {
    recommendations: String,
    potential_savings: f64,
    implementation_steps: Vec<String>,
}

#[derive(Debug, Clone, Serialize)]
struct HealthResponse {
    status: String,
    version: String,
}

// Main agent function
#[tokio::main]
async fn main() {
    println!("🚀 Cost Optimizer Agent Starting...");
    
    // Set up HTTP routes
    let health = warp::path("health")
        .and(warp::get())
        .map(|| {
            let response = HealthResponse {
                status: "healthy".to_string(),
                version: "1.0.0".to_string(),
            };
            warp::reply::json(&response)
        });
    
    let optimize = warp::path("optimize")
        .and(warp::post())
        .and(warp::body::json())
        .and_then(optimize_costs);
    
    let routes = health.or(optimize);
    
    // Start server
    println!("✅ Cost Optimizer Agent ready on http://0.0.0.0:8080");
    warp::serve(routes).run(([0, 0, 0, 0], 8080)).await;
}

// Cost optimization endpoint
async fn optimize_costs(req: CostOptimizationRequest) -> Result<impl warp::Reply, warp::Rejection> {
    println!("🔍 Analyzing costs for {} in {}", req.cloud_provider, req.region);
    
    // Simulate cost analysis
    let recommendations = format!(
        "Cost optimization recommendations for {} in {}:\n\
        1. Right-size underutilized instances\n\
        2. Use reserved instances for predictable workloads\n\
        3. Implement auto-scaling policies\n\
        4. Use spot instances for non-critical workloads\n\
        5. Optimize storage tier and cleanup unused resources",
        req.cloud_provider, req.region
    );

    let response = CostOptimizationResponse {
        recommendations,
        potential_savings: 1250.50,
        implementation_steps: vec![
            "Analyze current usage patterns".to_string(),
            "Identify optimization opportunities".to_string(),
            "Generate cost-saving recommendations".to_string(),
            "Create implementation plan".to_string(),
        ],
    };

    println!("💡 Generated {} recommendations", response.implementation_steps.len());
    
    Ok(warp::reply::json(&response))
}

// Health check endpoint
async fn health_check() -> Result<impl warp::Reply, warp::Rejection> {
    let response = HealthResponse {
        status: "healthy".to_string(),
        version: "1.0.0".to_string(),
    };
    
    Ok(warp::reply::json(&response))
}

// Ready check endpoint
async fn ready_check() -> Result<impl warp::Reply, warp::Rejection> {
    let response = HealthResponse {
        status: "ready".to_string(),
        version: "1.0.0".to_string(),
    };
    
    Ok(warp::reply::json(&response))
}

// Integration with memory agent
async fn call_memory_agent(prompt: &str) -> Result<String, Box<dyn std::error::Error>> {
    let memory_agent_url = std::env::var("MEMORY_AGENT_URL").unwrap_or_else(|_| "http://agent-memory-rust:8080".to_string());
    
    let client = Client::new();
    let request_body = serde_json::json!({
        "prompt": prompt,
        "context": "cost-optimization",
        "max_tokens": 1000
    });
    
    match client.post(&format!("{}/api/query", memory_agent_url))
        .header("Content-Type", "application/json")
        .json(&request_body)
        .send()
        .await {
            Ok(response) => {
                match response.text().await {
                    Ok(text) => Ok(text),
                    Err(e) => Err(format!("Failed to read response: {}", e).into()),
                }
            }
            Err(e) => Err(format!("Failed to call memory agent: {}", e).into()),
        }
}

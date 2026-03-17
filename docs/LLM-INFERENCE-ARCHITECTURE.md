# LLM Inference Architecture: Llama.cpp vs Ollama

## Overview

This document explains the two LLM inference backends used in the AI Agents system and their architectural differences.

## Quick Comparison

| Feature | Llama.cpp | Ollama |
|---------|-----------|--------|
| **Type** | In-process library | HTTP service |
| **Local Support** | ✅ True local (no HTTP) | ✅ Local but via HTTP |
| **Performance** | 🚀 Faster (no network) | 🐢 Slower (HTTP overhead) |
| **Setup** | 🔧 Model files required | 🚀 Auto-manages models |
| **API** | Direct function calls | REST API |
| **Multi-language** | Rust/Go/Python bindings | Any HTTP client |
| **Resource Usage** | Lower (shared process) | Higher (separate service) |

---

## Architecture Diagrams

### Llama.cpp Architecture
```
┌─────────────────────────────────────┐
│        Agent Container              │
│  ┌─────────────────────────────┐    │
│  │     Rust Agent Process      │    │
│  │  ┌─────────────────────┐    │    │
│  │  │   Llama.cpp Lib    │    │    │
│  │  │  ┌─────────────┐    │    │    │
│  │  │  │ Model File  │    │    │    │
│  │  │  │ (.gguf)     │    │    │    │
│  │  │  └─────────────┘    │    │    │
│  │  └─────────────────────┘    │    │
│  └─────────────────────────────┘    │
│                                     │
│  Direct in-process inference       │
│  No HTTP calls needed              │
└─────────────────────────────────────┘
```

### Ollama Architecture
```
┌─────────────────┐    HTTP     ┌─────────────────┐
│   Agent Pod     │ ◄─────────► │  Ollama Service │
│                 │    :11434   │                 │
│  ┌─────────────┐│             │  ┌─────────────┐ │
│  │ Rust Agent  ││             │  │   Ollama     │ │
│  │             ││             │  │   Server     │ │
│  │ HTTP Client ││             │  │             │ │
│  └─────────────┘│             │  │ ┌─────────┐ │ │
│                 │             │  │ │ Models  │ │ │
│                 │             │  │ │ Storage │ │ │
│                 │             │  │ └─────────┘ │ │
│                 │             │  └─────────────┘ │
└─────────────────┘             └─────────────────┘
```

---

## Configuration Examples

### Llama.cpp Configuration
```yaml
# Environment Variables
env:
- name: BACKEND_PRIORITY
  value: "llama.cpp,ollama"  # Try llama.cpp first
- name: LLAMA_CPP_MODEL_PATH
  value: "/models/qwen2.5-0.5b.gguf"  # Local model file
- name: MODEL
  value: "qwen2.5:0.5b"

# Volume Mounts
volumeMounts:
- name: model-storage
  mountPath: /models
  readOnly: true

# Storage
volumes:
- name: model-storage
  persistentVolumeClaim:
    claimName: agent-models-pvc
```

### Ollama Configuration
```yaml
# Environment Variables
env:
- name: BACKEND_PRIORITY
  value: "ollama,llama.cpp"  # Try ollama first
- name: OLLAMA_URL
  value: "http://ollama-service:11434"
- name: MODEL
  value: "qwen2.5:0.5b"

# No special volumes needed
# Ollama manages its own model storage
```

---

## Code Examples

### Llama.cpp Inference (Rust)
```rust
use llama_cpp::{Llama, LlamaParams};

// Direct in-process inference
let model_path = "/models/qwen2.5-0.5b.gguf";
let llama = Llama::new(LlamaParams {
    model_path: model_path.to_string(),
    ..Default::default()
})?;

let response = llama.inference("Hello, how are you?")?;
println!("Response: {}", response);
```

### Ollama Inference (Rust)
```rust
use reqwest::Client;
use serde_json::json;

// HTTP API call to Ollama
let client = Client::new();
let response = client
    .post("http://ollama-service:11434/api/generate")
    .json(&json!({
        "model": "qwen2.5:0.5b",
        "prompt": "Hello, how are you?",
        "stream": false
    }))
    .send()
    .await?;

let result: serde_json::Value = response.json().await?;
println!("Response: {}", result["response"]);
```

---

## Backend Priority Logic

### Configuration
```rust
// From rust-agent/src/lib.rs
pub struct AgentConfig {
    pub backend_priority: Vec<BackendType>,
    pub ollama_url: String,
    pub llama_cpp_model_path: Option<PathBuf>,
    pub model: String,
}
```

### Fallback Logic
```rust
impl InferenceBackend for MemoryAgent {
    async fn initialize(&mut self) -> Result<()> {
        for backend_type in &self.config.backend_priority {
            match backend_type {
                BackendType::LlamaCpp => {
                    if let Some(model_path) = &self.config.llama_cpp_model_path {
                        match LlamaBackend::new(model_path.clone()).await {
                            Ok(backend) => {
                                self.backends.push(Box::new(backend));
                                info!("✅ Initialized Llama.cpp backend");
                                break;
                            }
                            Err(e) => {
                                warn!("❌ Llama.cpp failed: {}, trying next backend", e);
                            }
                        }
                    }
                }
                BackendType::Ollama => {
                    match OllamaBackend::new(
                        self.config.ollama_url.clone(),
                        self.config.model.clone()
                    ).await {
                        Ok(backend) => {
                            self.backends.push(Box::new(backend));
                            info!("✅ Initialized Ollama backend");
                            break;
                        }
                        Err(e) => {
                            warn!("❌ Ollama failed: {}, trying next backend", e);
                        }
                    }
                }
            }
        }
        
        if self.backends.is_empty() {
            return Err(anyhow!("No inference backends available"));
        }
        
        Ok(())
    }
}
```

---

## Performance Comparison

### Llama.cpp Performance
```
✅ Advantages:
- Zero network latency
- Direct memory access
- Lower CPU overhead
- Faster inference times
- Better resource utilization

❌ Disadvantages:
- Requires model files
- More complex setup
- Language-specific bindings
- Manual model management
```

### Ollama Performance
```
✅ Advantages:
- Easy setup
- Automatic model management
- Language agnostic
- REST API interface
- Built-in model serving

❌ Disadvantages:
- HTTP overhead
- Higher latency
- More resource usage
- Separate service to manage
- Network dependency
```

---

## Use Cases

### Choose Llama.cpp when:
- ✅ Performance is critical
- ✅ Running in resource-constrained environments
- ✅ Need maximum inference speed
- ✅ Have control over model files
- ✅ Running single-language applications

### Choose Ollama when:
- ✅ Ease of setup is priority
- ✅ Need multi-language support
- ✅ Want automatic model management
- ✅ Building web applications
- ✅ Need REST API interface

### Hybrid Approach (Recommended):
- ✅ Use Llama.cpp as primary (fast, local)
- ✅ Use Ollama as fallback (reliable, easy)
- ✅ Get best of both worlds
- ✅ Automatic failover capability

---

## Deployment Examples

### Llama.cpp-First Deployment
```yaml
# Prioritize local inference
env:
- name: BACKEND_PRIORITY
  value: "llama.cpp,ollama"
- name: LLAMA_CPP_MODEL_PATH
  value: "/models/qwen2.5-0.5b.gguf"
- name: OLLAMA_URL
  value: "http://ollama-service:11434"
- name: MODEL
  value: "qwen2.5:0.5b"
```

### Ollama-First Deployment
```yaml
# Prioritize easy setup
env:
- name: BACKEND_PRIORITY
  value: "ollama,llama.cpp"
- name: OLLAMA_URL
  value: "http://ollama-service:11434"
- name: MODEL
  value: "qwen2.5:0.5b"
- name: LLAMA_CPP_MODEL_PATH
  value: "/models/qwen2.5-0.5b.gguf"
```

---

## Troubleshooting

### Llama.cpp Issues
```bash
# Check model file exists
kubectl exec agent-pod -- ls -la /models/qwen2.5-0.5b.gguf

# Check permissions
kubectl exec agent-pod -- file /models/qwen2.5-0.5b.gguf

# Check agent logs for loading errors
kubectl logs agent-pod | grep -i llama
```

### Ollama Issues
```bash
# Check Ollama service
kubectl get svc ollama-service

# Check Ollama pod
kubectl get pods -l app=ollama

# Test Ollama API
kubectl exec agent-pod -- curl http://ollama-service:11434/api/tags

# Check Ollama logs
kubectl logs ollama-pod | grep -i error
```

---

## Best Practices

### Model Management
```bash
# For Llama.cpp: Store model files in PVC
kubectl create pvc agent-models-pvc --storage-class=standard --access-mode=ReadWriteOnce --size=10Gi

# For Ollama: Let Ollama manage models
# Ollama downloads and stores models automatically
```

### Monitoring
```yaml
# Add health checks for both backends
livenessProbe:
  httpGet:
    path: /status
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Resource Limits
```yaml
# Llama.cpp: Lower resources (shared process)
resources:
  requests:
    memory: "512Mi"
    cpu: "200m"
  limits:
    memory: "1Gi"
    cpu: "500m"

# Ollama: Higher resources (separate service)
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

---

## Conclusion

Both Llama.cpp and Ollama support local inference, but they serve different purposes:

- **Llama.cpp**: Maximum performance, direct control, in-process
- **Ollama**: Easy setup, automatic management, HTTP interface

The hybrid approach (Llama.cpp primary, Ollama fallback) provides the best balance of performance and reliability for production AI agent deployments.

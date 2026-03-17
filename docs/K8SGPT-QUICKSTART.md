# K8sGPT with Qwen LLM - Quick Start Guide

## 🚀 5-Minute Quick Start

Get K8sGPT running with Qwen LLM in minutes!

### Prerequisites
- Kubernetes cluster (v1.20+)
- kubectl configured
- Python 3.8+
- 8GB+ RAM (for Qwen 7B model)

### Step 1: Install K8sGPT

```bash
# macOS/Linux
brew install k8sgpt

# Verify installation
k8sgpt version
```

### Step 2: Setup Qwen LLM

**Option A: Quick Local Setup (Recommended)**

```bash
# Install dependencies
pip install torch transformers accelerate fastapi uvicorn

# Start Qwen server (7B model)
python3 -c "
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import json
from fastapi import FastAPI
import uvicorn

app = FastAPI()

# Load model (this will download the model)
tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-7B-Instruct', trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained('Qwen/Qwen2.5-7B-Instruct', trust_remote_code=True, device_map='auto')
pipe = pipeline('text-generation', model=model, tokenizer=tokenizer)

@app.post('/v1/chat/completions')
async def chat_completions(request: dict):
    messages = request['messages']
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    outputs = pipe(prompt, max_new_tokens=1000, temperature=0.7, do_sample=True)
    response_text = outputs[0]['generated_text'][len(prompt):]
    
    return {
        'id': 'chatcmpl-test',
        'object': 'chat.completion',
        'created': 1234567890,
        'model': request['model'],
        'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': response_text}, 'finish_reason': 'stop'}],
        'usage': {'prompt_tokens': 100, 'completion_tokens': len(response_text), 'total_tokens': 100 + len(response_text)}
    }

@app.get('/v1/models')
async def list_models():
    return {'object': 'list', 'data': [{'id': 'qwen2.5-7b-instruct', 'object': 'model', 'created': 1234567890, 'owned_by': 'local'}]}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
" &
```

**Option B: Use Existing Qwen API**

```bash
# Set environment variables
export QWEN_API_KEY="your-api-key"
export QWEN_BASE_URL="https://your-qwen-api.com"
```

### Step 3: Configure K8sGPT

```bash
# Add Qwen backend to K8sGPT
k8sgpt auth add \
  --backend localai \
  --model qwen2.5-7b-instruct \
  --baseurl http://localhost:8000/v1

# Verify configuration
k8sgpt auth list
```

### Step 4: Run Your First Analysis

```bash
# Analyze your cluster
k8sgpt analyze --explain

# Analyze specific namespace
k8sgpt analyze --namespace default --explain

# Get JSON output
k8sgpt analyze --explain --output json
```

🎉 **You're done!** K8sGPT is now analyzing your cluster with Qwen LLM.

---

## 📋 Complete Setup Guide

### 1. System Requirements

| Component | Minimum | Recommended |
|-----------|----------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 8GB | 16GB |
| Storage | 50GB | 100GB |
| Network | 100Mbps | 1Gbps |

### 2. Installation Options

#### Option A: Binary Installation

```bash
# Download latest release
curl -LO https://github.com/k8sgpt-ai/k8sgpt/releases/latest/download/k8sgpt_linux_amd64.tar.gz
tar xvf k8sgpt_linux_amd64.tar.gz
sudo mv k8sgpt /usr/local/bin/

# Make executable
chmod +x /usr/local/bin/k8sgpt
```

#### Option B: Package Manager

```bash
# macOS
brew install k8sgpt

# Linux (Ubuntu/Debian)
wget https://github.com/k8sgpt-ai/k8sgpt/releases/latest/download/k8sgpt_amd64.deb
sudo dpkg -i k8sgpt_amd64.deb

# Linux (CentOS/RHEL)
wget https://github.com/k8sgpt-ai/k8sgpt/releases/latest/download/k8sgpt_amd64.rpm
sudo rpm -i k8sgpt_amd64.rpm
```

#### Option C: Docker

```bash
# Pull K8sGPT image
docker pull k8sgpt/k8sgpt:latest

# Run with mounted config
docker run -v ~/.kube:/root/.kube -v ~/.k8sgpt:/root/.k8sgpt k8sgpt/k8sgpt:latest analyze --explain
```

### 3. Qwen LLM Setup

#### Local Qwen Server

```bash
# Create local server script
cat > qwen_server.py << 'EOF'
#!/usr/bin/env python3
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Qwen LLM Server")

# Load model
model_name = "Qwen/Qwen2.5-7B-Instruct"
print(f"Loading {model_name}...")
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name, 
    trust_remote_code=True,
    torch_dtype=torch.float16,
    device_map="auto"
)
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)
print("Model loaded successfully!")

@app.post("/v1/chat/completions")
async def chat_completions(request: dict):
    try:
        messages = request["messages"]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        
        outputs = pipe(
            prompt,
            max_new_tokens=request.get("max_tokens", 1000),
            temperature=request.get("temperature", 0.7),
            do_sample=True,
            top_p=0.95,
        )
        
        response_text = outputs[0]["generated_text"][len(prompt):]
        
        return {
            "id": f"chatcmpl-{hash(str(messages))}",
            "object": "chat.completion",
            "created": 1234567890,
            "model": request["model"],
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(prompt),
                "completion_tokens": len(response_text),
                "total_tokens": len(prompt) + len(response_text)
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [{
            "id": "qwen2.5-7b-instruct",
            "object": "model",
            "created": 1234567890,
            "owned_by": "local"
        }]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Install dependencies
pip install torch transformers accelerate fastapi uvicorn

# Start server
python3 qwen_server.py
```

#### Cloud Qwen API

```bash
# Configure for cloud API
export QWEN_API_KEY="your-cloud-api-key"
export QWEN_BASE_URL="https://your-qwen-provider.com"

# Test connection
curl -X POST "$QWEN_BASE_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $QWEN_API_KEY" \
  -d '{"model":"qwen2.5-7b-instruct","messages":[{"role":"user","content":"Hello"}]}'
```

### 4. K8sGPT Configuration

#### Create Configuration File

```bash
# Create config directory
mkdir -p ~/.k8sgpt

# Create configuration
cat > ~/.k8sgpt/config.yaml << 'EOF'
backend: localai
model: qwen2.5-7b-instruct
baseurl: http://localhost:8000/v1
api_key: ""
max_tokens: 4096
temperature: 0.7
namespace: default
output_format: json
timeout: 300
retry_attempts: 3
EOF
```

#### Configure Authentication

```bash
# Add Qwen backend
k8sgpt auth add \
  --backend localai \
  --model qwen2.5-7b-instruct \
  --baseurl http://localhost:8000/v1

# List configured backends
k8sgpt auth list

# Test configuration
k8sgpt analyze --filter "pod/*" --explain
```

### 5. First Analysis

#### Basic Cluster Analysis

```bash
# Full cluster analysis
k8sgpt analyze --explain

# Specific namespace
k8sgpt analyze --namespace kube-system --explain

# Resource-specific analysis
k8sgpt analyze --filter "deployment/*" --explain

# Problem-focused analysis
k8sgpt analyze --filter "problems" --explain
```

#### Output Formats

```bash
# JSON output (default)
k8sgpt analyze --explain --output json

# YAML output
k8sgpt analyze --explain --output yaml

# Table format
k8sgpt analyze --explain --output table

# Summary only
k8sgpt analyze --explain --output summary
```

### 6. Automation Setup

#### Cron Job for Regular Analysis

```bash
# Add to crontab for every 6 hours
crontab -e

# Add this line:
0 */6 * * * /usr/local/bin/k8sgpt analyze --explain --output json >> /var/log/k8sgpt-analysis.log 2>&1
```

#### Script for Alerting

```bash
cat > k8sgpt-alert.sh << 'EOF'
#!/bin/bash
# K8sGPT Alert Script

ANALYSIS_OUTPUT=$(k8sgpt analyze --explain --output json)
ISSUES_COUNT=$(echo "$ANALYSIS_OUTPUT" | jq '.problems | length')

if [ "$ISSUES_COUNT" -gt 0 ]; then
    echo "🚨 K8sGPT found $ISSUES_COUNT issues:"
    echo "$ANALYSIS_OUTPUT" | jq -r '.problems[].message'
    
    # Send to Slack (if configured)
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-type: application/json' \
            --data "{\"text\":\"🚨 K8sGPT Alert: $ISSUES_COUNT issues found in cluster\"}"
    fi
else
    echo "✅ No issues found by K8sGPT"
fi
EOF

chmod +x k8sgpt-alert.sh
```

---

## 🎯 Common Use Cases

### 1. Daily Health Check

```bash
# Quick daily check
k8sgpt analyze --explain --output summary

# Detailed analysis
k8sgpt analyze --explain --output json > daily-analysis-$(date +%Y%m%d).json
```

### 2. Troubleshooting

```bash
# When pods are failing
k8sgpt analyze --filter "pod/failing-pod-*" --explain

# When deployments are stuck
k8sgpt analyze --filter "deployment/stuck-*" --explain

# When services are not working
k8sgpt analyze --filter "service/broken-*" --explain
```

### 3. Resource Optimization

```bash
# Find resource waste
k8sgpt analyze --filter "resources" --explain

# Optimize deployments
k8sgpt analyze --filter "deployment/*" --explain

# Check for unused resources
k8sgpt analyze --filter "unused" --explain
```

### 4. Security Analysis

```bash
# Security scan
k8sgpt analyze --filter "security" --explain

# RBAC issues
k8sgpt analyze --filter "rbac" --explain

# Network policies
k8sgpt analyze --filter "networkpolicy" --explain
```

---

## 🔧 Advanced Configuration

### Custom Filters

```bash
# Multiple filters
k8sgpt analyze --filter "pod/app-*" --filter "service/frontend*" --explain

# Label-based filtering
k8sgpt analyze --filter "label=app=nginx" --explain

# Annotation-based filtering
k8sgpt analyze --filter "annotation=monitoring=true" --explain
```

### Batch Operations

```bash
# Analyze multiple namespaces
for ns in default production staging; do
    echo "Analyzing namespace: $ns"
    k8sgpt analyze --namespace "$ns" --explain --output json > "analysis-$ns-$(date +%Y%m%d).json"
done

# Compare results
python3 -c "
import json
import sys

def compare_analysis(file1, file2):
    with open(file1) as f1, open(file2) as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)
    
    issues1 = len(data1.get('problems', []))
    issues2 = len(data2.get('problems', []))
    
    print(f'Issues in {file1}: {issues1}')
    print(f'Issues in {file2}: {issues2}')
    print(f'Difference: {issues2 - issues1}')

if len(sys.argv) == 3:
    compare_analysis(sys.argv[1], sys.argv[2])
"
```

### Integration with Monitoring

```bash
# Create monitoring script
cat > monitor-cluster.sh << 'EOF'
#!/bin/bash
# Cluster monitoring with K8sGPT

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT_DIR="/var/log/k8sgpt"
mkdir -p "$OUTPUT_DIR"

# Run analysis
k8sgpt analyze --explain --output json > "$OUTPUT_DIR/analysis-$TIMESTAMP.json"

# Extract metrics
ISSUES_COUNT=$(jq '.problems | length' "$OUTPUT_DIR/analysis-$TIMESTAMP.json")
NAMESPACE_COUNT=$(jq '.resources.namespaces | length' "$OUTPUT_DIR/analysis-$TIMESTAMP.json")
POD_COUNT=$(jq '.resources.pods | length' "$OUTPUT_DIR/analysis-$TIMESTAMP.json")

# Log metrics
echo "$TIMESTAMP,$ISSUES_COUNT,$NAMESPACE_COUNT,$POD_COUNT" >> "$OUTPUT_DIR/metrics.csv"

# Alert if issues exceed threshold
if [ "$ISSUES_COUNT" -gt 5 ]; then
    echo "🚨 High issue count: $ISSUES_COUNT" | logger -t k8sgpt
fi
EOF

chmod +x monitor-cluster.sh
```

---

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. K8sGPT Cannot Connect to Qwen

```bash
# Check if Qwen server is running
curl http://localhost:8000/v1/models

# Check K8sGPT configuration
k8sgpt auth list

# Test connection manually
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-7b-instruct","messages":[{"role":"user","content":"test"}]}'
```

#### 2. Permission Denied Errors

```bash
# Check kubectl access
kubectl get pods

# Check RBAC permissions
kubectl auth can-i get pods

# Fix permissions (if using service account)
kubectl create clusterrolebinding k8sgpt-admin \
  --clusterrole=cluster-admin \
  --serviceaccount=default:default
```

#### 3. Memory Issues with Qwen

```bash
# Check system memory
free -h

# Use smaller model if needed
k8sgpt auth remove --backend localai
k8sgpt auth add --backend localai --model qwen2.5-1.5b-instruct --baseurl http://localhost:8000/v1

# Or use cloud API instead
export QWEN_API_KEY="your-api-key"
export QWEN_BASE_URL="https://your-qwen-provider.com"
```

#### 4. Slow Analysis

```bash
# Enable caching
export K8SGPT_CACHE_ENABLED=true

# Reduce analysis scope
k8sgpt analyze --namespace default --explain

# Use smaller model
k8sgpt auth add --backend localai --model qwen2.5-1.5b-instruct --baseurl http://localhost:8000/v1
```

### Debug Mode

```bash
# Enable verbose logging
export K8SGPT_LOG_LEVEL=debug

# Run with debug output
k8sgpt analyze --explain --verbose

# Check configuration
k8sgpt config show
```

---

## 📚 Next Steps

### 1. Explore Advanced Features

- **Multi-cluster analysis**: Analyze multiple Kubernetes clusters
- **Custom analyzers**: Create custom analysis rules
- **Integration with monitoring**: Connect to Prometheus/Grafana
- **Automated remediation**: Set up automatic issue resolution

### 2. Production Deployment

- **Kubernetes deployment**: Deploy K8sGPT as a service
- **High availability**: Set up redundant instances
- **Security hardening**: Implement proper RBAC and network policies
- **Monitoring and alerting**: Set up comprehensive monitoring

### 3. Customization

- **Custom prompts**: Create custom analysis prompts
- **Integration with CI/CD**: Add to deployment pipelines
- **Custom reporting**: Create custom report formats
- **API integration**: Build custom applications

### 4. Community and Support

- **Documentation**: Read the full integration guide
- **GitHub**: Contribute to the project
- **Community**: Join the K8sGPT community
- **Support**: Get help with complex issues

---

## 🎉 Success!

You now have K8sGPT running with Qwen LLM! Here's what you can do next:

1. **Run your first analysis**: `k8sgpt analyze --explain`
2. **Explore different filters**: Try `--filter "deployment/*"`
3. **Set up automation**: Create a cron job for regular analysis
4. **Read the full guide**: Check `docs/K8SGPT-INTEGRATION-GUIDE.md`
5. **Join the community**: Get help and share your experience

Happy Kubernetes troubleshooting! 🚀

---

**Need help?**
- Check the full integration guide
- Review the troubleshooting section
- Join the K8sGPT community
- Create an issue on GitHub

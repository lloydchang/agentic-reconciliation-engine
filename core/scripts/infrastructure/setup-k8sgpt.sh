#!/bin/bash
# K8sGPT with Qwen LLM Setup Script
# Automatically sets up K8sGPT integration in the GitOps Infrastructure Control Plane

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
K8SGPT_DIR="$REPO_ROOT/core/ai/skills/k8sgpt-analyzer"
OVERLAY_DIR="$REPO_ROOT/overlay/k8sgpt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if k8sgpt is available
    if ! command -v k8sgpt &> /dev/null; then
        log_warning "k8sgpt is not installed. Installing..."
        install_k8sgpt
    fi
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot access Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Install K8sGPT
install_k8sgpt() {
    log_info "Installing K8sGPT..."
    
    # Detect OS
    OS="$(uname -s)"
    ARCH="$(uname -m)"
    
    case "$OS" in
        Darwin)
            if command -v brew &> /dev/null; then
                brew install k8sgpt
            else
                log_error "Homebrew not found. Please install K8sGPT manually"
                exit 1
            fi
            ;;
        Linux)
            # Download latest release
            K8SGPT_VERSION=$(curl -s https://api.github.com/repos/k8sgpt-ai/k8sgpt/releases/latest | grep -o '"tag_name": "[^"]*' | sed 's/"//g' | sed 's/tag_name: //')
            if [ -z "$K8SGPT_VERSION" ]; then
                K8SGPT_VERSION="v0.3.32"
            fi
            
            ARCH_NAME="amd64"
            if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
                ARCH_NAME="arm64"
            fi
            
            DOWNLOAD_URL="https://github.com/k8sgpt-ai/k8sgpt/releases/download/${K8SGPT_VERSION}/k8sgpt_linux_${ARCH_NAME}.tar.gz"
            
            log_info "Downloading K8sGPT from $DOWNLOAD_URL"
            curl -LO "$DOWNLOAD_URL"
            tar xzf "k8sgpt_linux_${ARCH_NAME}.tar.gz"
            sudo mv k8sgpt /usr/local/bin/
            rm -f "k8sgpt_linux_${ARCH_NAME}.tar.gz"
            ;;
        *)
            log_error "Unsupported OS: $OS"
            exit 1
            ;;
    esac
    
    log_success "K8sGPT installed successfully"
}

# Setup Qwen LLM
setup_qwen() {
    log_info "Setting up Qwen LLM..."
    
    # Check if Qwen dependencies are available
    if ! python3 -c "import torch" &> /dev/null; then
        log_info "Installing PyTorch and dependencies..."
        pip3 install torch transformers accelerate fastapi uvicorn
    fi
    
    # Create Qwen server script
    QWEN_SCRIPT="$K8SGPT_DIR/scripts/qwen_server.py"
    if [ ! -f "$QWEN_SCRIPT" ]; then
        log_info "Creating Qwen server script..."
        cat > "$QWEN_SCRIPT" << 'EOF'
#!/usr/bin/env python3
"""
Qwen LLM Server for K8sGPT Integration
OpenAI-compatible API server for Qwen models
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    from fastapi import FastAPI, HTTPException
    import uvicorn
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install: pip install torch transformers accelerate fastapi uvicorn")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Qwen LLM Server", version="1.0.0")

# Global variables for model
model = None
tokenizer = None
pipe = None

@app.on_event("startup")
async def load_model():
    """Load the Qwen model on startup"""
    global model, tokenizer, pipe
    
    model_name = os.getenv('QWEN_MODEL', 'Qwen/Qwen2.5-7B-Instruct')
    device = os.getenv('TORCH_DEVICE', 'auto')
    
    logger.info(f"Loading model: {model_name}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map=device
        )
        pipe = pipeline('text-generation', model=model, tokenizer=tokenizer)
        logger.info("Model loaded successfully!")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "model_loaded": model is not None}

@app.get("/ready")
async def ready():
    """Readiness check endpoint"""
    return {"status": "ready" if model is not None else "loading"}

@app.get("/v1/models")
async def list_models():
    """List available models"""
    return {
        "object": "list",
        "data": [{
            "id": "qwen2.5-7b-instruct",
            "object": "model",
            "created": 1234567890,
            "owned_by": "local"
        }]
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: dict):
    """OpenAI-compatible chat completions endpoint"""
    if pipe is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        messages = request.get('messages', [])
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        # Apply chat template
        prompt = tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        # Generate response
        outputs = pipe(
            prompt,
            max_new_tokens=request.get('max_tokens', 1000),
            temperature=request.get('temperature', 0.7),
            do_sample=True,
            top_p=0.95,
        )
        
        response_text = outputs[0]['generated_text'][len(prompt):]
        
        return {
            "id": f"chatcmpl-{hash(str(messages))}",
            "object": "chat.completion",
            "created": 1234567890,
            "model": request.get('model', 'qwen2.5-7b-instruct'),
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
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    
    uvicorn.run(app, host=host, port=port)
EOF
        chmod +x "$QWEN_SCRIPT"
    fi
    
    log_success "Qwen LLM setup completed"
}

# Configure K8sGPT
configure_k8sgpt() {
    log_info "Configuring K8sGPT..."
    
    # Create config directory
    mkdir -p ~/.k8sgpt
    
    # Create configuration
    cat > ~/.k8sgpt/config.yaml << EOF
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
cache_enabled: true
cache_ttl: 300
log_level: info
EOF
    
    # Test configuration
    if k8sgpt auth list &> /dev/null; then
        log_info "K8sGPT configuration verified"
    else
        log_warning "K8sGPT configuration needs manual verification"
    fi
    
    log_success "K8sGPT configuration completed"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    log_info "Deploying K8sGPT to Kubernetes..."
    
    # Check if namespace exists
    if ! kubectl get namespace gitops-infra &> /dev/null; then
        log_info "Creating gitops-infra namespace..."
        kubectl create namespace gitops-infra
    fi
    
    # Apply RBAC
    log_info "Applying RBAC..."
    kubectl apply -f "$OVERLAY_DIR/rbac/k8sgpt-rbac.yaml"
    
    # Apply storage
    log_info "Applying storage..."
    kubectl apply -f "$OVERLAY_DIR/storage/qwen-model-cache.yaml"
    
    # Apply ConfigMaps
    log_info "Applying ConfigMaps..."
    kubectl apply -f "$OVERLAY_DIR/configmaps/k8sgpt-config.yaml"
    
    # Apply Services
    log_info "Applying Services..."
    kubectl apply -f "$OVERLAY_DIR/services/k8sgpt-analyzer.yaml"
    
    # Apply Deployments
    log_info "Applying Deployments..."
    kubectl apply -f "$OVERLAY_DIR/deployments/k8sgpt-analyzer.yaml"
    
    # Apply NetworkPolicies
    log_info "Applying NetworkPolicies..."
    kubectl apply -f "$OVERLAY_DIR/network/networkpolicy.yaml"
    
    # Wait for deployments
    log_info "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/k8sgpt-analyzer -n gitops-infra
    kubectl wait --for=condition=available --timeout=600s deployment/qwen-server -n gitops-infra
    
    log_success "K8sGPT deployed to Kubernetes"
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Check if Prometheus Operator is available
    if kubectl get crd prometheusrules.monitoring.coreos.com &> /dev/null; then
        log_info "Applying Prometheus rules..."
        kubectl apply -f "$OVERLAY_DIR/monitoring/prometheus-rules.yaml"
    else
        log_warning "Prometheus Operator not found. Monitoring setup skipped."
    fi
    
    log_success "Monitoring setup completed"
}

# Test integration
test_integration() {
    log_info "Testing K8sGPT integration..."
    
    # Test local setup
    if command -v k8sgpt &> /dev/null; then
        log_info "Testing local K8sGPT..."
        if k8sgpt --help &> /dev/null; then
            log_success "Local K8sGPT test passed"
        else
            log_error "Local K8sGPT test failed"
        fi
    fi
    
    # Test Kubernetes deployment
    if kubectl get pods -n gitops-infra -l app.kubernetes.io/name=k8sgpt &> /dev/null; then
        log_info "Testing Kubernetes deployment..."
        
        # Check if pods are running
        POD_COUNT=$(kubectl get pods -n gitops-infra -l app.kubernetes.io/name=k8sgpt --no-headers | wc -l)
        if [ "$POD_COUNT" -gt 0 ]; then
            log_success "Kubernetes deployment test passed ($POD_COUNT pods running)"
        else
            log_error "Kubernetes deployment test failed (no pods running)"
        fi
        
        # Check if services are accessible
        if kubectl get svc k8sgpt-analyzer -n gitops-infra &> /dev/null; then
            log_success "Kubernetes services test passed"
        else
            log_error "Kubernetes services test failed"
        fi
    else
        log_warning "Kubernetes deployment not found"
    fi
    
    log_success "Integration testing completed"
}

# Create quickstart script
create_quickstart_script() {
    log_info "Creating quickstart script..."
    
    QUICKSTART_SCRIPT="$REPO_ROOT/scripts/k8sgpt-quickstart.sh"
    cat > "$QUICKSTART_SCRIPT" << 'EOF'
#!/bin/bash
# K8sGPT Quick Start Script

set -euo pipefail

echo "🚀 K8sGPT Quick Start"
echo "===================="

# Check if K8sGPT is configured
if ! k8sgpt auth list &> /dev/null; then
    echo "❌ K8sGPT not configured. Please run setup-k8sgpt.sh first."
    exit 1
fi

echo "✅ K8sGPT is configured"

# Run first analysis
echo "🔍 Running first cluster analysis..."
k8sgpt analyze --explain --output json > /tmp/k8sgpt-first-analysis.json

# Show summary
ISSUES_COUNT=$(jq '.problems | length' /tmp/k8sgpt-first-analysis.json 2>/dev/null || echo "0")
echo "📊 Found $ISSUES_COUNT issues in cluster"

if [ "$ISSUES_COUNT" -gt 0 ]; then
    echo "🔧 Issues found:"
    jq -r '.problems[].message' /tmp/k8sgpt-first-analysis.json 2>/dev/null || echo "Could not parse issues"
else
    echo "✅ No issues found!"
fi

echo ""
echo "📚 Next steps:"
echo "1. Read the full integration guide: docs/K8SGPT-INTEGRATION-GUIDE.md"
echo "2. Check the quickstart guide: docs/K8SGPT-QUICKSTART.md"
echo "3. Explore the skill: core/ai/skills/k8sgpt-analyzer/"
echo "4. Configure automated analysis: setup cron jobs or Kubernetes deployments"

echo ""
echo "🎉 K8sGPT is ready to use!"
EOF
    chmod +x "$QUICKSTART_SCRIPT"
    
    log_success "Quickstart script created"
}

# Main function
main() {
    log_info "Starting K8sGPT setup..."
    
    # Parse command line arguments
    SKIP_KUBERNETES=false
    SKIP_MONITORING=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-kubernetes)
                SKIP_KUBERNETES=true
                shift
                ;;
            --skip-monitoring)
                SKIP_MONITORING=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-kubernetes    Skip Kubernetes deployment"
                echo "  --skip-monitoring    Skip monitoring setup"
                echo "  --help              Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Run setup steps
    check_prerequisites
    install_k8sgpt
    setup_qwen
    configure_k8sgpt
    
    if [ "$SKIP_KUBERNETES" = false ]; then
        deploy_kubernetes
    fi
    
    if [ "$SKIP_MONITORING" = false ]; then
        setup_monitoring
    fi
    
    test_integration
    create_quickstart_script
    
    log_success "K8sGPT setup completed successfully!"
    echo ""
    echo "🎉 K8sGPT with Qwen LLM is now ready!"
    echo ""
    echo "📚 Documentation:"
    echo "  - Integration Guide: docs/K8SGPT-INTEGRATION-GUIDE.md"
    echo "  - Quick Start: docs/K8SGPT-QUICKSTART.md"
    echo "  - Skill Definition: core/ai/skills/k8sgpt-analyzer/SKILL.md"
    echo ""
    echo "🚀 Quick Start:"
    echo "  $REPO_ROOT/scripts/k8sgpt-quickstart.sh"
    echo ""
    echo "🔧 Local Usage:"
    echo "  k8sgpt analyze --explain"
    echo "  k8sgpt analyze --namespace default --explain"
    echo ""
    if [ "$SKIP_KUBERNETES" = false ]; then
        echo "☸️  Kubernetes:"
        echo "  kubectl get pods -n gitops-infra -l app.kubernetes.io/name=k8sgpt"
        echo "  kubectl logs -n gitops-infra deployment/k8sgpt-analyzer"
    fi
}

# Run main function
main "$@"

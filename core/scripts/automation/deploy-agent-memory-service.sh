#!/bin/bash
# Deploy Agent Memory Service - Integrated with Quickstart
# This script builds, containerizes, and deploys the Agent Memory Service

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script information
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel)"
MEMORY_SERVICE_DIR="$REPO_ROOT/core/ai/runtime/agents/memory-rust"

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Agent Memory Service Prerequisites"
    
    local missing_tools=()
    
    # Check for required tools
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    if ! command -v cargo &> /dev/null; then
        missing_tools+=("rust/cargo")
    fi
    
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        print_info "Install missing tools and retry"
        return 1
    fi
    
    # Check if memory service directory exists
    if [[ ! -d "$MEMORY_SERVICE_DIR" ]]; then
        print_error "Agent Memory Service directory not found: $MEMORY_SERVICE_DIR"
        return 1
    fi
    
    print_success "Prerequisites check passed"
    return 0
}

# Build Rust binary
build_rust_binary() {
    print_header "Building Agent Memory Service (Rust)"
    
    cd "$MEMORY_SERVICE_DIR"
    
    # Check if Cargo.toml exists
    if [[ ! -f "Cargo.toml" ]]; then
        print_error "Cargo.toml not found in $MEMORY_SERVICE_DIR"
        return 1
    fi
    
    # Build the Rust application
    print_info "Running cargo build --release..."
    if cargo build --release; then
        print_success "Rust binary built successfully"
    else
        print_error "Failed to build Rust binary"
        return 1
    fi
    
    # Verify binary was created
    if [[ -f "target/release/agent-memory-rust" ]]; then
        print_success "Binary verified: target/release/agent-memory-rust"
    else
        print_error "Binary not found after build"
        return 1
    fi
}

# Build Docker image
build_docker_image() {
    print_header "Building Agent Memory Service Docker Image"
    
    cd "$MEMORY_SERVICE_DIR"
    
    # Check if Dockerfile exists
    if [[ ! -f "Dockerfile" ]]; then
        print_error "Dockerfile not found in $MEMORY_SERVICE_DIR"
        return 1
    fi
    
    # Build Docker image
    print_info "Building Docker image: agent-memory-rust:latest..."
    if docker build -t agent-memory-rust:latest .; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        return 1
    fi
    
    # Verify image exists
    if docker images | grep -q "agent-memory-rust.*latest"; then
        print_success "Docker image verified: agent-memory-rust:latest"
    else
        print_error "Docker image not found after build"
        return 1
    fi
}

# Deploy to Kubernetes
deploy_to_kubernetes() {
    print_header "Deploying Agent Memory Service to Kubernetes"
    
    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Kubernetes cluster not accessible"
        return 1
    fi
    
    # Create namespace if it doesn't exist
    print_info "Creating ai-infrastructure namespace..."
    kubectl create namespace ai-infrastructure --dry-run=client -o yaml | kubectl apply -f -
    
    # Create secrets
    print_info "Creating secrets..."
    kubectl create secret generic agent-memory-secrets \
        --from-literal=jwt-secret=qwen-jwt-secret-for-agent-memory \
        --from-literal=qwen-api-key=agent-memory-api-key \
        --namespace=ai-infrastructure \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Create PVC for database storage
    print_info "Creating PVC for database storage..."
    kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: agent-memory-pvc
  namespace: ai-infrastructure
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
EOF
    
    # Deploy the service
    print_info "Deploying Agent Memory Service..."
    if kubectl apply -f "$MEMORY_SERVICE_DIR/k8s/deployment.yaml"; then
        print_success "Deployment applied successfully"
    else
        print_error "Failed to apply deployment"
        return 1
    fi
    
    # Wait for deployment to be ready
    print_info "Waiting for deployment to be ready..."
    if kubectl wait --for=condition=available deployment/agent-memory-rust \
        --namespace=ai-infrastructure \
        --timeout=300s; then
        print_success "Deployment is ready"
    else
        print_error "Deployment failed to become ready"
        return 1
    fi
    
    # Show LLaMA.cpp setup instructions
    print_info "LLaMA.cpp setup required for AI functionality:"
    echo ""
    echo "🔧 To enable AI capabilities, you need to:"
    echo "1. Setup LLaMA.cpp server:"
    echo "   cd $MEMORY_SERVICE_DIR"
    echo "   ./setup-llamacpp.sh"
    echo ""
    echo "2. Start LLaMA.cpp server:"
    echo "   ./start-llamacpp-server.sh /models/qwen2.5-0.5b-instruct.gguf"
    echo ""
    echo "3. The service will automatically connect to LLaMA.cpp at http://localhost:8080"
    echo ""
}

# Validate deployment
validate_deployment() {
    print_header "Validating Agent Memory Service Deployment"
    
    # Check pod status
    print_info "Checking pod status..."
    local pod_status=$(kubectl get pods -l app=agent-memory-rust -n ai-infrastructure -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "NotFound")
    
    if [[ "$pod_status" == "Running" ]]; then
        print_success "Pod is running"
    else
        print_error "Pod status: $pod_status"
        return 1
    fi
    
    # Check service status
    print_info "Checking service status..."
    if kubectl get svc agent-memory-service -n ai-infrastructure &> /dev/null; then
        print_success "Service is available"
    else
        print_error "Service not found"
        return 1
    fi
    
    # Test health endpoint
    print_info "Testing health endpoint..."
    local pod_name=$(kubectl get pods -l app=agent-memory-rust -n ai-infrastructure -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -n "$pod_name" ]]; then
        if kubectl exec -n ai-infrastructure "$pod_name" -- curl -f http://localhost:8080/api/health &> /dev/null; then
            print_success "Health endpoint responding"
        else
            print_warning "Health endpoint not responding (service may still be starting)"
        fi
    fi
    
    # Show service details
    print_info "Service details:"
    kubectl get svc agent-memory-service -n ai-infrastructure
    
    print_success "Deployment validation completed"
}

# Setup port-forward
setup_port_forward() {
    print_header "Setting up Port Forward"
    
    # Check if port-forward is already running
    if pgrep -f "port-forward.*agent-memory-service.*8081" > /dev/null; then
        print_info "Port-forward already running on localhost:8081"
        return 0
    fi
    
    # Start port-forward in background
    print_info "Starting port-forward for Agent Memory Service..."
    nohup kubectl port-forward -n ai-infrastructure svc/agent-memory-service 8081:8080 > /tmp/agent-memory-port-forward.log 2>&1 &
    
    # Wait a moment and check if it started
    sleep 3
    if pgrep -f "port-forward.*agent-memory-service.*8081" > /dev/null; then
        print_success "Port-forward started: http://localhost:8081"
        print_info "Logs: tail -f /tmp/agent-memory-port-forward.log"
    else
        print_error "Failed to start port-forward"
        return 1
    fi
}

# Show access information
show_access_info() {
    print_header "Agent Memory Service Access Information"
    
    echo ""
    echo -e "${GREEN}🎉 Agent Memory Service is now running!${NC}"
    echo ""
    echo -e "${YELLOW}🧠 Service endpoints:${NC}"
    echo -e "  🌐 Local access: http://localhost:8081"
    echo -e "  🔗 Cluster access: http://agent-memory-service.ai-infrastructure.svc.cluster.local:8080"
    echo -e "  📊 Metrics: http://localhost:8081/metrics"
    echo ""
    echo -e "${YELLOW}🔍 API endpoints:${NC}"
    echo -e "  ❤️  Health: GET http://localhost:8081/api/health"
    echo -e "  📨 Events: POST http://localhost:8081/api/events"
    echo -e "  💬 Chat: POST http://localhost:8081/api/chat"
    echo -e "  🔧 Skills: GET http://localhost:8081/api/skills/list"
    echo -e "  ⚙️  Execute: POST http://localhost:8081/api/skills/execute"
    echo ""
    echo -e "${YELLOW}🧪 Test commands:${NC}"
    echo "  # Health check"
    echo "  curl http://localhost:8081/api/health"
    echo ""
    echo "  # List skills"
    echo "  curl http://localhost:8081/api/skills/list"
    echo ""
    echo "  # Send event"
    echo "  curl -X POST http://localhost:8081/api/events \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"event_type\":\"test\",\"component\":\"test\",\"severity\":\"info\"}'"
    echo ""
    echo -e "${YELLOW}📝 Logs:${NC}"
    echo "  # Service logs"
    echo "  kubectl logs -f -n ai-infrastructure -l app=agent-memory-rust"
    echo ""
    echo "  # Port-forward logs"
    echo "  tail -f /tmp/agent-memory-port-forward.log"
    echo ""
}

# Main deployment function
deploy_agent_memory_service() {
    print_header "Deploying Agent Memory Service"
    
    # Check prerequisites
    if ! check_prerequisites; then
        print_error "Prerequisites check failed"
        return 1
    fi
    
    # Build Rust binary
    if ! build_rust_binary; then
        print_error "Rust build failed"
        return 1
    fi
    
    # Build Docker image
    if ! build_docker_image; then
        print_error "Docker build failed"
        return 1
    fi
    
    # Deploy to Kubernetes
    if ! deploy_to_kubernetes; then
        print_error "Kubernetes deployment failed"
        return 1
    fi
    
    # Validate deployment
    if ! validate_deployment; then
        print_error "Deployment validation failed"
        return 1
    fi
    
    # Setup port-forward
    setup_port_forward
    
    # Show access information
    show_access_info
    
    print_success "Agent Memory Service deployment completed successfully!"
}

# Cleanup function
cleanup() {
    print_header "Cleaning up Agent Memory Service"
    
    # Stop port-forward
    if pgrep -f "port-forward.*agent-memory-service.*8081" > /dev/null; then
        pkill -f "port-forward.*agent-memory-service.*8081"
        print_success "Stopped port-forward"
    fi
    
    # Clean up log file
    if [[ -f "/tmp/agent-memory-port-forward.log" ]]; then
        rm -f /tmp/agent-memory-port-forward.log
        print_info "Cleaned up port-forward log"
    fi
    
    print_success "Cleanup completed"
}

# Command line argument handling
case "${1:-deploy}" in
    "deploy")
        deploy_agent_memory_service
        ;;
    "validate")
        validate_deployment
        ;;
    "cleanup")
        cleanup
        ;;
    "port-forward")
        setup_port_forward
        ;;
    *)
        echo "Usage: $0 {deploy|validate|cleanup|port-forward}"
        echo ""
        echo "Commands:"
        echo "  deploy       - Build, containerize, and deploy the service"
        echo "  validate     - Validate existing deployment"
        echo "  cleanup      - Clean up port-forwards and logs"
        echo "  port-forward - Setup port-forward only"
        exit 1
        ;;
esac

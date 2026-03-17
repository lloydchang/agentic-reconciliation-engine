#!/bin/bash
# AI Agent Evaluation Framework Deployment Script
# Deploys all three background evaluation options

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-localhost:5000}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
NAMESPACE="${NAMESPACE:-ai-agents}"

# Logging functions
print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is required but not installed"
        exit 1
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is required but not installed"
        exit 1
    fi
    
    # Check cluster access
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot access Kubernetes cluster"
        exit 1
    fi
    
    print_success "Prerequisites satisfied"
}

# Build Docker images
build_images() {
    print_header "Building Docker Images"
    
    cd "$PROJECT_ROOT"
    
    # Build base image
    print_info "Building base evaluator image..."
    docker build -f deployments/ai-agent-evaluator-Dockerfile -t "${DOCKER_REGISTRY}/ai-agent-evaluator:${IMAGE_TAG}" --target base .
    
    # Build API server image
    print_info "Building API server image..."
    docker build -f deployments/ai-agent-evaluator-Dockerfile -t "${DOCKER_REGISTRY}/ai-agent-evaluator-api:${IMAGE_TAG}" --target production .
    
    # Build Temporal worker image
    print_info "Building Temporal worker image..."
    docker build -f deployments/ai-agent-evaluator-Dockerfile -t "${DOCKER_REGISTRY}/ai-agent-evaluator:${IMAGE_TAG}" --target temporal-worker .
    
    # Push images if registry is remote
    if [[ "$DOCKER_REGISTRY" != "localhost:5000" ]]; then
        print_info "Pushing images to registry..."
        docker push "${DOCKER_REGISTRY}/ai-agent-evaluator:${IMAGE_TAG}"
        docker push "${DOCKER_REGISTRY}/ai-agent-evaluator-api:${IMAGE_TAG}"
    fi
    
    print_success "Docker images built and pushed"
}

# Deploy Kubernetes resources
deploy_kubernetes_resources() {
    print_header "Deploying Kubernetes Resources"
    
    cd "$PROJECT_ROOT"
    
    # Create namespace
    print_info "Creating namespace: $NAMESPACE"
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply all manifests
    print_info "Applying Kubernetes manifests..."
    kubectl apply -f deployments/ai-agent-evaluator-complete.yaml -n "$NAMESPACE"
    
    # Wait for deployments to be ready
    print_info "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available deployment/temporal-evaluation-worker -n "$NAMESPACE" --timeout=300s
    
    print_success "Kubernetes resources deployed"
}

# Deploy Option 1: Scheduled Jobs
deploy_scheduled_jobs() {
    print_header "Deploying Option 1: Scheduled Kubernetes Jobs"
    
    cd "$PROJECT_ROOT"
    
    # Update image references in CronJob
    sed -i.bak "s|image: ai-agent-evaluator:latest|image: ${DOCKER_REGISTRY}/ai-agent-evaluator:${IMAGE_TAG}|g" deployments/ai-agent-evaluation-cronjob.yaml
    
    # Apply CronJob
    kubectl apply -f deployments/ai-agent-evaluation-cronjob.yaml -n "$NAMESPACE"
    
    # Restore original file
    mv deployments/ai-agent-evaluation-cronjob.yaml.bak deployments/ai-agent-evaluation-cronjob.yaml
    
    print_success "Scheduled jobs deployed"
}

# Deploy Option 2: API Server
deploy_api_server() {
    print_header "Deploying Option 2: API Server"
    
    cd "$PROJECT_ROOT"
    
    # Update image references in deployment
    sed -i.bak "s|image: ai-agent-evaluator:latest|image: ${DOCKER_REGISTRY}/ai-agent-evaluator-api:${IMAGE_TAG}|g" deployments/ai-agent-evaluator-deployment.yaml
    
    # Apply deployment
    kubectl apply -f deployments/ai-agent-evaluator-deployment.yaml -n "$NAMESPACE"
    
    # Wait for API server to be ready
    print_info "Waiting for API server to be ready..."
    kubectl wait --for=condition=available deployment/ai-agent-evaluator-api -n "$NAMESPACE" --timeout=300s
    
    # Restore original file
    mv deployments/ai-agent-evaluator-deployment.yaml.bak deployments/ai-agent-evaluator-deployment.yaml
    
    print_success "API server deployed"
}

# Deploy Option 3: Temporal Integration
deploy_temporal_integration() {
    print_header "Deploying Option 3: Temporal Integration"
    
    cd "$PROJECT_ROOT"
    
    # Check if Temporal is running
    if ! kubectl get pods -n temporal -l app=temporal &> /dev/null; then
        print_warning "Temporal is not running. Temporal integration will not work until Temporal is deployed."
        print_info "Deploying Temporal worker anyway (will be ready when Temporal is available)..."
    else
        print_info "Temporal detected. Deploying Temporal worker..."
    fi
    
    # Temporal worker is already deployed in the main manifest
    print_success "Temporal integration deployed"
}

# Test deployments
test_deployments() {
    print_header "Testing Deployments"
    
    # Test API server
    print_info "Testing API server health endpoint..."
    if kubectl get service ai-agent-evaluator-service -n "$NAMESPACE" &> /dev/null; then
        # Port forward to test
        kubectl port-forward service/ai-agent-evaluator-service 8080:80 -n "$NAMESPACE" &
        PF_PID=$!
        sleep 5
        
        if curl -s http://localhost:8080/health | grep -q "healthy"; then
            print_success "API server health check passed"
        else
            print_error "API server health check failed"
        fi
        
        kill $PF_PID 2>/dev/null || true
    fi
    
    # Test scheduled jobs
    print_info "Testing scheduled jobs..."
    if kubectl get cronjob ai-agent-evaluation-cronjob -n "$NAMESPACE" &> /dev/null; then
        print_success "Scheduled jobs deployed successfully"
    else
        print_error "Scheduled jobs not found"
    fi
    
    # Test Temporal worker
    print_info "Testing Temporal worker..."
    if kubectl get pods -n "$NAMESPACE" -l component=temporal-worker &> /dev/null; then
        print_success "Temporal worker deployed successfully"
    else
        print_error "Temporal worker not found"
    fi
}

# Show deployment status
show_status() {
    print_header "Deployment Status"
    
    echo "Namespace: $NAMESPACE"
    echo "Docker Registry: $DOCKER_REGISTRY"
    echo "Image Tag: $IMAGE_TAG"
    echo ""
    
    # Show pods
    print_info "Pods in $NAMESPACE namespace:"
    kubectl get pods -n "$NAMESPACE" -l app=ai-agent-evaluation
    
    echo ""
    
    # Show services
    print_info "Services in $NAMESPACE namespace:"
    kubectl get services -n "$NAMESPACE" -l app=ai-agent-evaluation
    
    echo ""
    
    # Show cronjobs
    print_info "CronJobs in $NAMESPACE namespace:"
    kubectl get cronjobs -n "$NAMESPACE"
    
    echo ""
    
    # Show access information
    print_info "Access Information:"
    echo "API Server: kubectl port-forward service/ai-agent-evaluator-service 8080:80 -n $NAMESPACE"
    echo "Then access: http://localhost:8080"
    echo ""
    echo "View logs: kubectl logs -f deployment/ai-agent-evaluator-api -n $NAMESPACE"
    echo "View worker logs: kubectl logs -f deployment/temporal-evaluation-worker -n $NAMESPACE"
}

# Cleanup function
cleanup() {
    print_header "Cleaning Up"
    
    read -p "Are you sure you want to delete all AI Agent Evaluation resources? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl delete namespace "$NAMESPACE" --ignore-not-found=true
        print_success "Cleanup completed"
    else
        print_info "Cleanup cancelled"
    fi
}

# Main function
main() {
    print_header "AI Agent Evaluation Framework Deployment"
    print_info "Deploying all three background evaluation options"
    print_info "Namespace: $NAMESPACE"
    print_info "Docker Registry: $DOCKER_REGISTRY"
    print_info "Image Tag: $IMAGE_TAG"
    
    case "${1:-deploy}" in
        deploy)
            check_prerequisites
            build_images
            deploy_kubernetes_resources
            deploy_scheduled_jobs
            deploy_api_server
            deploy_temporal_integration
            test_deployments
            show_status
            ;;
        build)
            build_images
            ;;
        k8s)
            deploy_kubernetes_resources
            ;;
        scheduled)
            deploy_scheduled_jobs
            ;;
        api)
            deploy_api_server
            ;;
        temporal)
            deploy_temporal_integration
            ;;
        test)
            test_deployments
            ;;
        status)
            show_status
            ;;
        cleanup)
            cleanup
            ;;
        *)
            echo "Usage: $0 {deploy|build|k8s|scheduled|api|temporal|test|status|cleanup}"
            echo ""
            echo "Commands:"
            echo "  deploy    - Full deployment (default)"
            echo "  build     - Build Docker images only"
            echo "  k8s       - Deploy Kubernetes resources only"
            echo "  scheduled - Deploy scheduled jobs only"
            echo "  api       - Deploy API server only"
            echo "  temporal  - Deploy Temporal integration only"
            echo "  test      - Test deployments"
            echo "  status    - Show deployment status"
            echo "  cleanup   - Delete all resources"
            exit 1
            ;;
    esac
}

# Help function
show_help() {
    echo "AI Agent Evaluation Framework Deployment Script"
    echo ""
    echo "USAGE: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "COMMANDS:"
    echo "  deploy    Full deployment (default)"
    echo "  build     Build Docker images only"
    echo "  k8s       Deploy Kubernetes resources only"
    echo "  scheduled Deploy scheduled jobs only"
    echo "  api       Deploy API server only"
    echo "  temporal  Deploy Temporal integration only"
    echo "  test      Test deployments"
    echo "  status    Show deployment status"
    echo "  cleanup   Delete all resources"
    echo ""
    echo "ENVIRONMENT VARIABLES:"
    echo "  DOCKER_REGISTRY    Docker registry (default: localhost:5000)"
    echo "  IMAGE_TAG          Image tag (default: latest)"
    echo "  NAMESPACE          Kubernetes namespace (default: ai-agents)"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                                    # Full deployment with defaults"
    echo "  DOCKER_REGISTRY=myregistry.com $0     # Use custom registry"
    echo "  IMAGE_TAG=v1.0.0 $0                   # Use specific tag"
    echo "  $0 api                                # Deploy API server only"
    echo ""
    echo "DEPLOYMENT OPTIONS:"
    echo "  Option 1: Scheduled Kubernetes Jobs - Runs every 4 hours"
    echo "  Option 2: API Server - REST API for on-demand evaluation"
    echo "  Option 3: Temporal Integration - Event-driven evaluation"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    "")
        main
        ;;
    *)
        main "$1"
        ;;
esac

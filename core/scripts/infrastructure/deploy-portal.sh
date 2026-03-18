#!/bin/bash

# AI Infrastructure Portal Deployment Script
# Deploys a central portal with links to all AI services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="ai-infrastructure"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi
    
    # Check cluster access
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot access Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    log_success "Prerequisites satisfied"
}

# Create namespace if it doesn't exist
create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    if kubectl get namespace $NAMESPACE &> /dev/null; then
        log_info "Namespace $NAMESPACE already exists"
    else
        kubectl create namespace $NAMESPACE
        log_success "Created namespace: $NAMESPACE"
    fi
}

# Deploy portal
deploy_portal() {
    log_info "Deploying AI Infrastructure Portal..."
    
    # Deploy ConfigMap
    log_info "Deploying portal ConfigMap..."
    kubectl apply -f "$SCRIPT_DIR/../../ai/runtime/dashboard/deployment/kubernetes/portal-configmap.yaml"
    
    # Deploy Service and Deployment
    log_info "Deploying portal Service and Deployment..."
    kubectl apply -f "$SCRIPT_DIR/../../ai/runtime/dashboard/deployment/kubernetes/portal-deployment.yaml"
    
    log_success "Portal deployed successfully!"
}

# Wait for portal to be ready
wait_for_portal() {
    log_info "Waiting for portal to be ready..."
    
    # Wait for deployment to be ready
    kubectl wait --for=condition=available --timeout=60s \
        deployment/ai-infrastructure-portal -n $NAMESPACE
    
    log_success "Portal is ready!"
}

# Start port-forward
start_port_forward() {
    log_info "Starting portal port-forward..."
    
    # Check if port-forward is already running
    if pgrep -f "port-forward.*ai-infrastructure-portal.*8888" > /dev/null; then
        log_info "Portal port-forward already running"
    else
        # Start port-forward in background
        nohup kubectl port-forward -n $NAMESPACE svc/ai-infrastructure-portal 8888:80 > /tmp/portal-port-forward.log 2>&1 &
        sleep 2
        
        # Verify it started successfully
        if pgrep -f "port-forward.*ai-infrastructure-portal.*8888" > /dev/null; then
            log_success "Portal port-forward started successfully!"
            echo -e "${GREEN}🌐 Portal accessible at: http://localhost:8888${NC}"
            echo -e "${YELLOW}📝 Logs: tail -f /tmp/portal-port-forward.log${NC}"
        else
            log_warning "Portal port-forward failed to start"
            echo "Manual access: kubectl port-forward -n $NAMESPACE svc/ai-infrastructure-portal 8888:80"
        fi
    fi
}

# Main function
main() {
    echo -e "${BLUE}=== AI Infrastructure Portal Deployment ===${NC}"
    echo ""
    
    check_prerequisites
    create_namespace
    deploy_portal
    wait_for_portal
    start_port_forward
    
    echo ""
    echo -e "${GREEN}🎉 AI Infrastructure Portal Deployment Complete!${NC}"
    echo ""
    echo -e "${BLUE}🚪 Portal Access:${NC}"
    echo "  🌐 Portal: http://localhost:8888"
    echo ""
    echo -e "${YELLOW}🔧 Manual Port Forward (if needed):${NC}"
    echo "  kubectl port-forward -n $NAMESPACE svc/ai-infrastructure-portal 8888:80"
    echo ""
    echo -e "${BLUE}📋 Portal Features:${NC}"
    echo "  ✅ Central access to all AI services"
    echo "  ✅ Real-time service status checking"
    echo "  ✅ One-click access to dashboards"
    echo "  ✅ Responsive design for all devices"
    echo "  ✅ Automatic refresh every 30 seconds"
    echo ""
    echo -e "${GREEN}🌐 Access your portal at: http://localhost:8888${NC}"
}

# Help function
show_help() {
    echo "AI Infrastructure Portal Deployment"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "DESCRIPTION:"
    echo "  Deploys a central portal that provides easy access to all AI services"
    echo "  including dashboards, APIs, and monitoring tools."
    echo ""
    echo "SERVICES ACCESSIBLE VIA PORTAL:"
    echo "  🚪 Portal:           http://localhost:8888"
    echo "  🤖 AI Dashboard:     http://localhost:8080"
    echo "  📊 Dashboard API:     http://localhost:5000"
    echo "  ⏰ Temporal UI:       http://localhost:7233"
    echo "  🔍 Langfuse:          http://localhost:3000"
    echo "  📈 Comprehensive API: http://localhost:5001"
    echo "  🖥️  Comprehensive Frontend: http://localhost:8082"
    echo "  🧠 Memory Service:    http://localhost:8081"
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
        echo "Unknown option: $1"
        show_help
        exit 1
        ;;
esac

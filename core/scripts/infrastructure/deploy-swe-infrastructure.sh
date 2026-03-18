#!/bin/bash

# SWE Infrastructure Deployment Script
# Deploys Open-SWE components, SWE-agent, and related infrastructure

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="swe-infrastructure"
OVERLAY_DIR="$SCRIPT_DIR/../../../overlay"
KUBECTL_CMD="kubectl"

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

    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please ensure cluster is running and kubectl is configured."
        exit 1
    fi

    # Check overlay directory
    if [ ! -d "$OVERLAY_DIR/swe-infrastructure" ]; then
        log_error "SWE infrastructure manifests not found in $OVERLAY_DIR/swe-infrastructure"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Create namespace
create_namespace() {
    log_info "Creating namespace $NAMESPACE..."
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    log_success "Namespace $NAMESPACE created/verified"
}

# Deploy SWE components
deploy_swe_components() {
    log_info "Deploying SWE infrastructure components..."

    # Apply all SWE manifests
    find "$OVERLAY_DIR/swe-infrastructure" -name "*.yaml" -o -name "*.yml" | while read -r manifest; do
        log_info "Applying $manifest"
        kubectl apply -f "$manifest" -n $NAMESPACE
    done

    log_success "SWE components deployed"
}

# Wait for deployments to be ready
wait_for_deployments() {
    log_info "Waiting for deployments to be ready..."

    # Wait for SWE agent
    kubectl wait --for=condition=available --timeout=300s deployment/swe-agent -n $NAMESPACE

    # Wait for Open-SWE framework
    kubectl wait --for=condition=available --timeout=300s deployment/open-swe-framework -n $NAMESPACE

    # Wait for sandbox manager
    kubectl wait --for=condition=available --timeout=300s deployment/cloud-sandbox-manager -n $NAMESPACE

    log_success "All deployments are ready"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."

    # Check pod status
    kubectl get pods -n $NAMESPACE

    # Check services
    kubectl get svc -n $NAMESPACE

    log_success "Deployment verification complete"
}

# Display access information
display_access_info() {
    log_info "SWE Infrastructure Access Information:"
    echo ""
    echo "Services deployed:"
    echo "- SWE Agent: http://localhost:8085"
    echo "- Open-SWE Framework: http://localhost:8086"
    echo "- Cloud Sandbox Manager: Internal service"
    echo ""
    echo "To access services locally, run port-forwarding:"
    echo "kubectl port-forward -n $NAMESPACE svc/swe-agent-service 8085:80"
    echo "kubectl port-forward -n $NAMESPACE svc/open-swe-service 8086:80"
    echo ""
    echo "Portal integration: Services will be available at http://localhost:9000"
}

# Cleanup function
cleanup() {
    log_warning "Script interrupted. Cleaning up..."
    # Add cleanup logic if needed
    exit 1
}

# Set trap for cleanup on error
trap cleanup ERR

# Main execution
main() {
    log_info "Starting SWE Infrastructure Deployment"

    check_prerequisites
    create_namespace
    deploy_swe_components
    wait_for_deployments
    verify_deployment
    display_access_info

    log_success "SWE Infrastructure deployment completed successfully!"
}

# Run main function
main "$@"

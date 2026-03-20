#!/bin/bash

# Open SWE Gateway Deployment Script
# This script deploys the Open SWE Gateway service to Kubernetes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
OPEN_SWE_DIR="${PROJECT_ROOT}/core/ai/runtime/open-swe-gateway"

NAMESPACE="ai-infrastructure"
DEPLOYMENT_NAME="open-swe-gateway"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    # Check if namespace exists
    if ! kubectl get namespace "${NAMESPACE}" &> /dev/null; then
        log_info "Creating namespace ${NAMESPACE}..."
        kubectl create namespace "${NAMESPACE}"
    fi

    log_success "Prerequisites check passed"
}

# Function to validate configuration
validate_config() {
    log_info "Validating configuration..."

    # Check if config files exist
    if [[ ! -f "${OPEN_SWE_DIR}/k8s/deployment.yaml" ]]; then
        log_error "Deployment manifest not found: ${OPEN_SWE_DIR}/k8s/deployment.yaml"
        exit 1
    fi

    if [[ ! -f "${OPEN_SWE_DIR}/k8s/service.yaml" ]]; then
        log_error "Service manifest not found: ${OPEN_SWE_DIR}/k8s/service.yaml"
        exit 1
    fi

    if [[ ! -f "${OPEN_SWE_DIR}/k8s/config.yaml" ]]; then
        log_error "Config manifest not found: ${OPEN_SWE_DIR}/k8s/config.yaml"
        exit 1
    fi

    if [[ ! -f "${OPEN_SWE_DIR}/k8s/rbac.yaml" ]]; then
        log_error "RBAC manifest not found: ${OPEN_SWE_DIR}/k8s/rbac.yaml"
        exit 1
    fi

    if [[ ! -f "${OPEN_SWE_DIR}/k8s/security.yaml" ]]; then
        log_error "Security manifest not found: ${OPEN_SWE_DIR}/k8s/security.yaml"
        exit 1
    fi

    log_success "Configuration validation passed"
}

# Function to deploy manifests
deploy_manifests() {
    log_info "Deploying Open SWE Gateway manifests..."

    # Deploy RBAC first
    log_info "Deploying RBAC..."
    kubectl apply -f "${OPEN_SWE_DIR}/k8s/rbac.yaml" -n "${NAMESPACE}"

    # Deploy security policies
    log_info "Deploying security policies..."
    kubectl apply -f "${OPEN_SWE_DIR}/k8s/security.yaml" -n "${NAMESPACE}"

    # Deploy config
    log_info "Deploying configuration..."
    kubectl apply -f "${OPEN_SWE_DIR}/k8s/config.yaml" -n "${NAMESPACE}"

    # Deploy service
    log_info "Deploying service..."
    kubectl apply -f "${OPEN_SWE_DIR}/k8s/service.yaml" -n "${NAMESPACE}"

    # Deploy deployment
    log_info "Deploying application..."
    kubectl apply -f "${OPEN_SWE_DIR}/k8s/deployment.yaml" -n "${NAMESPACE}"

    log_success "All manifests deployed successfully"
}

# Function to wait for deployment to be ready
wait_for_deployment() {
    log_info "Waiting for deployment to be ready..."

    # Wait for deployment to be available
    kubectl wait --for=condition=available --timeout=300s deployment/"${DEPLOYMENT_NAME}" -n "${NAMESPACE}"

    # Wait for pods to be ready
    kubectl wait --for=condition=ready pod -l app="${DEPLOYMENT_NAME}" --timeout=300s -n "${NAMESPACE}"

    log_success "Deployment is ready"
}

# Function to verify deployment
verify_deployment() {
    log_info "Verifying deployment..."

    # Check pod status
    POD_STATUS=$(kubectl get pods -l app="${DEPLOYMENT_NAME}" -n "${NAMESPACE}" -o jsonpath='{.items[0].status.phase}')
    if [[ "${POD_STATUS}" != "Running" ]]; then
        log_error "Pod is not running. Status: ${POD_STATUS}"
        kubectl describe pod -l app="${DEPLOYMENT_NAME}" -n "${NAMESPACE}"
        exit 1
    fi

    # Check service endpoints
    SERVICE_IP=$(kubectl get service "${DEPLOYMENT_NAME}" -n "${NAMESPACE}" -o jsonpath='{.spec.clusterIP}')
    if [[ -z "${SERVICE_IP}" ]]; then
        log_error "Service cluster IP is not assigned"
        exit 1
    fi

    # Test health endpoint
    HEALTH_URL="http://${DEPLOYMENT_NAME}.${NAMESPACE}.svc.cluster.local:8080/health"
    if kubectl run test-health --image=curlimages/curl --rm -i --restart=Never -- curl -f "${HEALTH_URL}" &> /dev/null; then
        log_success "Health check passed"
    else
        log_warning "Health check failed - service may still be starting"
    fi

    log_success "Deployment verification completed"
}

# Function to display deployment info
display_info() {
    log_info "Open SWE Gateway Deployment Information:"
    echo ""
    echo "Service URL: http://${DEPLOYMENT_NAME}.${NAMESPACE}.svc.cluster.local:8080"
    echo "Metrics URL: http://${DEPLOYMENT_NAME}.${NAMESPACE}.svc.cluster.local:9090/metrics"
    echo "Load Balancer: $(kubectl get service ${DEPLOYMENT_NAME}-lb -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo 'Not assigned yet')"
    echo ""
    echo "Webhook endpoints:"
    echo "  Slack: POST /webhooks/slack"
    echo "  Linear: POST /webhooks/linear"
    echo "  GitHub: POST /webhooks/github"
    echo ""
    echo "To check logs: kubectl logs -l app=${DEPLOYMENT_NAME} -n ${NAMESPACE} -f"
}

# Main deployment function
main() {
    log_info "Starting Open SWE Gateway deployment..."

    check_prerequisites
    validate_config
    deploy_manifests
    wait_for_deployment
    verify_deployment
    display_info

    log_success "Open SWE Gateway deployment completed successfully!"
    log_info "The integration is now ready for webhook configuration and testing."
}

# Run main function
main "$@"

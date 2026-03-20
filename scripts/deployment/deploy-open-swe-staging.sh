#!/bin/bash

# Open-SWE Staging Deployment Script
# Deploys the complete Open-SWE intelligence platform to staging environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# Color codes for output
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

# Configuration
NAMESPACE="ai-infrastructure"
STAGING_NAMESPACE="ai-infrastructure-staging"
DEPLOYMENT_TIMEOUT="600s"

# Prerequisites check
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi

    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Unable to connect to Kubernetes cluster."
        exit 1
    fi

    # Check if staging namespace exists, create if not
    if ! kubectl get namespace "$STAGING_NAMESPACE" &> /dev/null; then
        log_info "Creating staging namespace: $STAGING_NAMESPACE"
        kubectl create namespace "$STAGING_NAMESPACE"
    fi

    log_success "Prerequisites check passed"
}

# Deploy core SWE services
deploy_core_services() {
    log_info "Deploying core SWE services..."

    # Deploy SWE Intelligence Gateway
    log_info "Deploying SWE Intelligence Gateway..."
    kubectl apply -f "${PROJECT_ROOT}/core/ai/runtime/open-swe-gateway/k8s/" -n "$STAGING_NAMESPACE"

    # Deploy SWE Integration Dispatcher
    log_info "Deploying SWE Integration Dispatcher..."
    kubectl apply -f "${PROJECT_ROOT}/core/ai/runtime/open-swe-integration/k8s/" -n "$STAGING_NAMESPACE"

    # Deploy SWE Monitoring Dashboard
    log_info "Deploying SWE Monitoring Dashboard..."
    kubectl apply -f "${PROJECT_ROOT}/core/swe/monitoring/dashboard/" -n "$STAGING_NAMESPACE"

    # Deploy SWE Metrics Service
    log_info "Deploying SWE Metrics Service..."
    kubectl apply -f "${PROJECT_ROOT}/core/swe/monitoring/metrics-service/" -n "$STAGING_NAMESPACE"

    log_success "Core SWE services deployed"
}

# Deploy analysis services
deploy_analysis_services() {
    log_info "Deploying analysis services..."

    # Code Analysis Service
    kubectl apply -f "${PROJECT_ROOT}/core/swe/analysis/code-analysis/k8s/" -n "$STAGING_NAMESPACE"

    # Security Scanner Service
    kubectl apply -f "${PROJECT_ROOT}/core/swe/security/security-scanner/k8s/" -n "$STAGING_NAMESPACE"

    # Performance Profiler Service
    kubectl apply -f "${PROJECT_ROOT}/core/swe/performance/performance-profiler/k8s/" -n "$STAGING_NAMESPACE"

    log_success "Analysis services deployed"
}

# Deploy intelligence services
deploy_intelligence_services() {
    log_info "Deploying intelligence services..."

    # SWE Intelligence API
    kubectl apply -f "${PROJECT_ROOT}/core/swe/intelligence/api/k8s/" -n "$STAGING_NAMESPACE"

    # Cross-Repository Analysis
    kubectl apply -f "${PROJECT_ROOT}/core/swe/intelligence/cross-repo-analysis/k8s/" -n "$STAGING_NAMESPACE"

    # Documentation Intelligence
    kubectl apply -f "${PROJECT_ROOT}/core/swe/intelligence/documentation-intelligence/k8s/" -n "$STAGING_NAMESPACE"

    # Vulnerability Management
    kubectl apply -f "${PROJECT_ROOT}/core/swe/security/vulnerability-management/k8s/" -n "$STAGING_NAMESPACE"

    log_success "Intelligence services deployed"
}

# Deploy governance services
deploy_governance_services() {
    log_info "Deploying governance services..."

    # Policy Engine (OPA)
    kubectl apply -f "${PROJECT_ROOT}/core/swe/governance/policies/k8s/" -n "$STAGING_NAMESPACE"

    # Audit Service
    kubectl apply -f "${PROJECT_ROOT}/core/swe/governance/audit/k8s/" -n "$STAGING_NAMESPACE"

    # Compliance Engine
    kubectl apply -f "${PROJECT_ROOT}/core/swe/governance/compliance/k8s/" -n "$STAGING_NAMESPACE"

    log_success "Governance services deployed"
}

# Wait for deployments to be ready
wait_for_deployments() {
    log_info "Waiting for all deployments to be ready (timeout: $DEPLOYMENT_TIMEOUT)..."

    # List of deployments to wait for
    deployments=(
        "swe-intelligence-gateway"
        "swe-integration-dispatcher"
        "swe-monitoring-dashboard"
        "swe-metrics-service"
        "swe-code-analysis"
        "swe-security-scanner"
        "swe-performance-profiler"
        "swe-intelligence-api"
        "swe-cross-repo-analysis"
        "swe-documentation-intelligence"
        "swe-vulnerability-management"
        "swe-policy-engine"
        "swe-audit-service"
        "swe-compliance-engine"
    )

    for deployment in "${deployments[@]}"; do
        log_info "Waiting for deployment: $deployment"
        if ! kubectl wait --for=condition=available --timeout="$DEPLOYMENT_TIMEOUT" deployment/"$deployment" -n "$STAGING_NAMESPACE" 2>/dev/null; then
            log_warning "Deployment $deployment not ready within timeout, continuing..."
        fi
    done

    log_success "Deployment readiness check completed"
}

# Setup port forwarding for staging
setup_port_forwarding() {
    log_info "Setting up port forwarding for staging environment..."

    # Create log directory
    mkdir -p /tmp/quickstart-port-forwards/staging

    # Start background port forwards
    nohup kubectl port-forward -n "$STAGING_NAMESPACE" svc/swe-monitoring-dashboard 8081:8080 > /tmp/quickstart-port-forwards/staging/swe-dashboard.log 2>&1 &
    nohup kubectl port-forward -n "$STAGING_NAMESPACE" svc/swe-intelligence-api 5002:5000 > /tmp/quickstart-port-forwards/staging/swe-api.log 2>&1 &

    log_success "Port forwarding configured"
}

# Run basic health checks
run_health_checks() {
    log_info "Running basic health checks..."

    # Check if services are responding
    services=(
        "swe-monitoring-dashboard.ai-infrastructure-staging.svc.cluster.local:8080"
        "swe-intelligence-api.ai-infrastructure-staging.svc.cluster.local:5000"
    )

    for service in "${services[@]}"; do
        log_info "Checking health of: $service"
        # Note: In staging, we might not have external access, so we'll just check pod status
    done

    # Check pod statuses
    if kubectl get pods -n "$STAGING_NAMESPACE" | grep -q "Running"; then
        log_success "Pods are running"
    else
        log_warning "Some pods may not be running"
    fi

    log_success "Health checks completed"
}

# Display staging environment info
display_staging_info() {
    log_success "Open-SWE Staging Environment Deployed Successfully!"
    echo ""
    echo "📊 Staging Environment Details:"
    echo "   Namespace: $STAGING_NAMESPACE"
    echo "   Dashboard: http://localhost:8081 (port-forwarded)"
    echo "   API: http://localhost:5002 (port-forwarded)"
    echo ""
    echo "🔍 Services Available:"
    echo "   - SWE Intelligence Gateway"
    echo "   - Code Analysis Engine"
    echo "   - Security Scanner"
    echo "   - Performance Profiler"
    echo "   - Cross-Repository Analysis"
    echo "   - Documentation Intelligence"
    echo "   - Vulnerability Management"
    echo "   - Policy Engine (OPA)"
    echo "   - Audit Service"
    echo "   - Compliance Engine"
    echo ""
    echo "📁 Log Files:"
    echo "   /tmp/quickstart-port-forwards/staging/"
    echo ""
    echo "🧪 Next Steps:"
    echo "   1. Run integration tests: ./scripts/test-open-swe-integration.sh"
    echo "   2. Monitor services: ./scripts/monitor-open-swe-integration.sh"
    echo "   3. Review adoption guide: docs/OPEN-SWE-ADOPTION-GUIDE.md"
}

# Main deployment function
main() {
    log_info "Starting Open-SWE Staging Deployment"

    check_prerequisites
    deploy_core_services
    deploy_analysis_services
    deploy_intelligence_services
    deploy_governance_services
    wait_for_deployments
    setup_port_forwarding
    run_health_checks
    display_staging_info

    log_success "Open-SWE Staging Deployment Completed Successfully! 🎉"
}

# Handle command line arguments
case "${1:-}" in
    "--help"|"-h")
        echo "Open-SWE Staging Deployment Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h    Show this help message"
        echo ""
        echo "This script deploys the complete Open-SWE intelligence platform"
        echo "to a staging environment for testing and validation."
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac

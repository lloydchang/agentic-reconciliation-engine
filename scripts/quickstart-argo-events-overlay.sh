#!/bin/bash

# Argo Events Overlay Quickstart Script
# Quick deployment using Kustomize overlays for different environments

set -euo pipefail

# Configuration
ENVIRONMENT="${1:-development}"
OVERLAY_DIR="overlay/argo-events"
TIMEOUT=300

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ✓ $1"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ⚠ $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ✗ $1"
}

highlight() {
    echo -e "${MAGENTA}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} 🌟 $1"
}

# Show banner
show_banner() {
    echo -e "${MAGENTA}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              Argo Events Overlay Quickstart                ║"
    echo "║                                                              ║"
    echo "║  🚀 Environment-Specific Deployment                          ║"
    echo "║  🔧 Kustomize-Based Configuration                           ║"
    echo "║  📦 Overlay Management                                      ║"
    echo "║  🎯 Quick & Easy Setup                                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
    log "Starting Argo Events overlay deployment..."
    log "Environment: ${ENVIRONMENT}"
    log "Overlay Directory: ${OVERLAY_DIR}"
    echo
}

# Check environment
check_environment() {
    log "Checking environment configuration..."
    
    # Validate environment
    local valid_environments=("development" "staging" "production")
    local is_valid=false
    
    for env in "${valid_environments[@]}"; do
        if [[ "${ENVIRONMENT}" == "${env}" ]]; then
            is_valid=true
            break
        fi
    done
    
    if [[ "${is_valid}" != "true" ]]; then
        error "Invalid environment: ${ENVIRONMENT}"
        echo "Valid environments: ${valid_environments[*]}"
        exit 1
    fi
    
    # Check overlay directory exists
    if [[ ! -d "${OVERLAY_DIR}/${ENVIRONMENT}" ]]; then
        error "Overlay directory not found: ${OVERLAY_DIR}/${ENVIRONMENT}"
        exit 1
    fi
    
    success "Environment validation passed"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed"
        exit 1
    fi
    
    # Check kustomize
    if ! command -v kustomize &> /dev/null && ! kubectl kustomize version &> /dev/null; then
        error "kustomize is not installed or kubectl doesn't support kustomize"
        exit 1
    fi
    
    # Check cluster access
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot access Kubernetes cluster"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Show overlay configuration
show_overlay_config() {
    log "Showing overlay configuration for ${ENVIRONMENT}..."
    
    echo "=== Kustomization Configuration ==="
    if command -v kustomize &> /dev/null; then
        kustomize build "${OVERLAY_DIR}/${ENVIRONMENT}" | grep -E "(kind:|metadata:|name:)" | head -20
    else
        kubectl kustomize "${OVERLAY_DIR}/${ENVIRONMENT}" | grep -E "(kind:|metadata:|name:)" | head -20
    fi
    echo
    
    echo "=== Resources to be Applied ==="
    if command -v kustomize &> /dev/null; then
        kustomize build "${OVERLAY_DIR}/${ENVIRONMENT}" | grep -E "^kind:" | sort | uniq -c
    else
        kubectl kustomize "${OVERLAY_DIR}/${ENVIRONMENT}" | grep -E "^kind:" | sort | uniq -c
    fi
    echo
}

# Deploy overlay
deploy_overlay() {
    log "Deploying ${ENVIRONMENT} overlay..."
    
    # Build and apply overlay
    if command -v kustomize &> /dev/null; then
        if kustomize build "${OVERLAY_DIR}/${ENVIRONMENT}" | kubectl apply -f -; then
            success "Overlay deployment initiated"
        else
            error "Failed to deploy overlay"
            exit 1
        fi
    else
        if kubectl apply -k "${OVERLAY_DIR}/${ENVIRONMENT}"; then
            success "Overlay deployment initiated"
        else
            error "Failed to deploy overlay"
            exit 1
        fi
    fi
}

# Wait for deployment
wait_for_deployment() {
    log "Waiting for deployment to be ready..."
    
    # Determine namespace based on environment
    local namespace="argo-events-${ENVIRONMENT}"
    
    # Wait for controller
    log "Waiting for Argo Events controller..."
    if kubectl wait --for condition=available --timeout="${TIMEOUT}s" deployment/"${ENVIRONMENT}"-argo-events-controller -n "${namespace}"; then
        success "Argo Events controller is ready"
    else
        error "Argo Events controller readiness timeout"
        exit 1
    fi
    
    # Wait for event sources
    log "Waiting for event sources..."
    local event_sources
    event_sources=$(kubectl get eventsources -n "${namespace}" --no-headers | awk '{print $1}' || echo "")
    
    for es in ${event_sources}; do
        if kubectl wait --for condition=ready --timeout=120s eventsources/"${es}" -n "${namespace}"; then
            success "Event source ${es} is ready"
        else
            warning "Event source ${es} readiness timeout"
        fi
    done
    
    # Wait for sensors
    log "Waiting for sensors..."
    local sensors
    sensors=$(kubectl get sensors -n "${namespace}" --no-headers | awk '{print $1}' || echo "")
    
    for sensor in ${sensors}; do
        if kubectl wait --for condition=ready --timeout=120s sensors/"${sensor}" -n "${namespace}"; then
            success "Sensor ${sensor} is ready"
        else
            warning "Sensor ${sensor} readiness timeout"
        fi
    done
}

# Show deployment status
show_deployment_status() {
    local namespace="argo-events-${ENVIRONMENT}"
    
    log "Deployment Status for ${ENVIRONMENT}:"
    echo
    
    echo "=== Namespace ==="
    kubectl get namespace "${namespace}" -o wide || echo "Namespace not found"
    echo
    
    echo "=== Pods ==="
    kubectl get pods -n "${namespace}" -o wide || echo "No pods found"
    echo
    
    echo "=== Services ==="
    kubectl get svc -n "${namespace}" -o wide || echo "No services found"
    echo
    
    echo "=== Event Sources ==="
    kubectl get eventsources -n "${namespace}" -o wide || echo "No event sources found"
    echo
    
    echo "=== Sensors ==="
    kubectl get sensors -n "${namespace}" -o wide || echo "No sensors found"
    echo
    
    echo "=== Recent Events ==="
    kubectl get events -n "${namespace}" --sort-by='.lastTimestamp' | tail -5 || echo "No events found"
    echo
}

# Show access information
show_access_info() {
    local namespace="argo-events-${ENVIRONMENT}"
    
    highlight "Access Information for ${ENVIRONMENT}:"
    echo
    
    echo "=== Webhook Endpoints ==="
    local webhook_services
    webhook_services=$(kubectl get svc -n "${namespace}" -l app.kubernetes.io/name=argo-events --no-headers | awk '{print $1}' || echo "")
    
    for service in ${webhook_services}; do
        local port
        port=$(kubectl get svc "${service}" -n "${namespace}" -o jsonpath='{.spec.ports[0].port}' 2>/dev/null || echo "unknown")
        echo "${service}: http://$(kubectl get svc "${service}" -n "${namespace}" -o jsonpath='{.status.clusterIP}' 2>/dev/null || echo "pending"):${port}"
    done
    echo
    
    echo "=== Port Forward Commands ==="
    echo "# Port forward webhook for testing:"
    echo "kubectl port-forward -n ${namespace} svc/${ENVIRONMENT}-comprehensive-webhook-api-events 12001:12001"
    echo
    echo "# Port forward controller metrics:"
    echo "kubectl port-forward -n ${namespace} svc/${ENVIRONMENT}-argo-events-controller 8080:8080"
    echo
    
    echo "=== Test Commands ==="
    echo "# Test webhook:"
    echo "curl -X POST http://localhost:12001/api -H 'Content-Type: application/json' -d '{\"type\": \"test\", \"message\": \"Hello ${ENVIRONMENT}\"}'"
    echo
    echo "# Check logs:"
    echo "kubectl logs -n ${namespace} deployment/${ENVIRONMENT}-argo-events-controller -f"
    echo
    
    if [[ "${ENVIRONMENT}" == "development" ]]; then
        echo "=== Development Specific ==="
        echo "# Debug event sources:"
        echo "kubectl get eventsources -n ${namespace} -o yaml"
        echo
        echo "# Debug sensors:"
        echo "kubectl get sensors -n ${namespace} -o yaml"
        echo
    fi
    
    if [[ "${ENVIRONMENT}" == "production" ]]; then
        echo "=== Production Specific ==="
        echo "# Check HPA status:"
        echo "kubectl get hpa -n ${NAMESPACE}"
        echo
        echo "# Check PDB status:"
        echo "kubectl get pdb -n ${NAMESPACE}"
        echo
    fi
}

# Show next steps
show_next_steps() {
    highlight "Next Steps for ${ENVIRONMENT}:"
    echo
    echo "1. 🚀 Test event sources and sensors:"
    echo "   Use the port forward commands above to test webhooks"
    echo
    echo "2. 📊 Monitor deployment:"
    echo "   kubectl get all -n argo-events-${ENVIRONMENT}"
    echo
    echo "3. 📋 Check event processing:"
    echo "   kubectl logs -n argo-events-${ENVIRONMENT} deployment/${ENVIRONMENT}-argo-events-controller -f"
    echo
    echo "4. 🔧 Customize configuration:"
    echo "   Edit files in ${OVERLAY_DIR}/${ENVIRONMENT}/"
    echo "   Then run: $0 ${ENVIRONMENT}"
    echo
    echo "5. 📈 Scale as needed:"
    echo "   kubectl scale deployment/${ENVIRONMENT}-argo-events-controller --replicas=3 -n argo-events-${ENVIRONMENT}"
    echo
    echo "6. 🧪 Run tests:"
    echo "   kubectl apply -f tests/argo-events/test-suite.yaml"
    echo "   bash tests/argo-events/test-runner.sh"
    echo
}

# Cleanup function
cleanup() {
    local namespace="argo-events-${ENVIRONMENT}"
    
    log "Cleaning up ${ENVIRONMENT} deployment..."
    
    if command -v kustomize &> /dev/null; then
        kustomize build "${OVERLAY_DIR}/${ENVIRONMENT}" | kubectl delete -f --ignore-not-found=true --timeout=60s || true
    else
        kubectl delete -k "${OVERLAY_DIR}/${ENVIRONMENT}" --ignore-not-found=true --timeout=60s || true
    fi
    
    # Delete namespace if empty
    if kubectl get namespace "${namespace}" &>/dev/null; then
        kubectl delete namespace "${namespace}" --ignore-not-found=true --timeout=60s || true
    fi
    
    success "Cleanup completed"
}

# Main execution
main() {
    local command="${1:-${ENVIRONMENT}}"
    
    case "${command}" in
        development|staging|production)
            ENVIRONMENT="${command}"
            show_banner
            check_environment
            check_prerequisites
            show_overlay_config
            deploy_overlay
            wait_for_deployment
            show_deployment_status
            show_access_info
            show_next_steps
            success "🎉 ${ENVIRONMENT} overlay deployment completed!"
            ;;
        status)
            if [[ -z "${2:-}" ]]; then
                error "Please specify environment: $0 status [development|staging|production]"
                exit 1
            fi
            ENVIRONMENT="${2}"
            check_environment
            show_deployment_status
            show_access_info
            ;;
        cleanup)
            if [[ -z "${2:-}" ]]; then
                error "Please specify environment: $0 cleanup [development|staging|production]"
                exit 1
            fi
            ENVIRONMENT="${2}"
            check_environment
            cleanup
            ;;
        *)
            echo "Usage: $0 [development|staging|production|status|cleanup]"
            echo
            echo "Commands:"
            echo "  development  - Deploy development environment"
            echo "  staging      - Deploy staging environment"
            echo "  production   - Deploy production environment"
            echo "  status ENV   - Show status for specific environment"
            echo "  cleanup ENV  - Clean up specific environment"
            echo
            echo "Examples:"
            echo "  $0 development    # Deploy dev environment"
            echo "  $0 status dev      # Show dev status"
            echo "  $0 cleanup prod    # Clean up prod environment"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

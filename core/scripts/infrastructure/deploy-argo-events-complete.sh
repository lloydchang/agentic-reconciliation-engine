#!/bin/bash

# Complete Argo Events Deployment Script
# Automated deployment with Qwen LLM integration, monitoring, and comprehensive setup

set -euo pipefail

# Configuration
NAMESPACE="argo-events"
ARGO_EVENTS_VERSION="v1.9.0"
QWEN_MODEL="qwen2.5:7b"
ENVIRONMENT="${ENVIRONMENT:-development}"
ENABLE_MONITORING="${ENABLE_MONITORING:-true}"
ENABLE_QWEN="${ENABLE_QWEN:-true}"
ENABLE_TESTING="${ENABLE_TESTING:-false}"
TIMEOUT=600

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Logging functions
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

info() {
    echo -e "${CYAN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ℹ $1"
}

highlight() {
    echo -e "${MAGENTA}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} 🌟 $1"
}

# Show banner
show_banner() {
    echo -e "${MAGENTA}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                Argo Events Complete Deployment              ║"
    echo "║                      with Qwen LLM Integration                ║"
    echo "║                                                              ║"
    echo "║  🚀 Event-Driven Automation                                    ║"
    echo "║  🤖 Qwen LLM Intelligence                                     ║"
    echo "║  📊 Comprehensive Monitoring                                   ║"
    echo "║  🧪 Automated Testing                                          ║"
    echo "║  🔒 Production Ready Security                                  ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
    log "Starting complete Argo Events deployment..."
    log "Environment: ${ENVIRONMENT}"
    log "Namespace: ${NAMESPACE}"
    log "Qwen Model: ${QWEN_MODEL}"
    echo
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed"
        exit 1
    fi
    
    # Check cluster access
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot access Kubernetes cluster"
        exit 1
    fi
    
    # Check cluster health
    if ! kubectl get nodes &> /dev/null; then
        error "Cannot get cluster nodes"
        exit 1
    fi
    
    # Check for required storage classes
    local storage_classes
    storage_classes=$(kubectl get storageclass --no-headers | wc -l)
    if [[ "${storage_classes}" -eq 0 ]]; then
        warning "No storage classes found - PVC creation may fail"
    fi
    
    # Check available resources
    local available_memory
    available_memory=$(kubectl top nodes --no-headers | awk '{sum+=$3} END {print sum}' | sed 's/Mi//' || echo "0")
    if [[ "${available_memory}" -lt 4096 ]]; then
        warning "Low memory available (${available_memory}Mi) - Qwen model may require more memory"
    fi
    
    success "Prerequisites check completed"
}

# Create namespace and labels
create_namespace() {
    log "Creating namespace with labels..."
    
    kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | \
    kubectl apply -f - -l \
        app.kubernetes.io/name=argo-events \
        app.kubernetes.io/component=events \
        environment="${ENVIRONMENT}" \
        managed-by=automated-script
    
    success "Namespace created with labels"
}

# Install Argo Events core
install_argo_events() {
    log "Installing Argo Events core components..."
    
    # Apply core Argo Events manifest
    if kubectl apply -n "${NAMESPACE}" -f "https://raw.githubusercontent.com/argoproj/argo-events/${ARGO_EVENTS_VERSION}/manifests/install.yaml"; then
        success "Argo Events installation initiated"
    else
        error "Failed to install Argo Events"
        exit 1
    fi
    
    # Wait for controller to be ready
    log "Waiting for Argo Events controller to be ready..."
    if kubectl wait --for condition=available --timeout=300s deployment/argo-events-controller -n "${NAMESPACE}"; then
        success "Argo Events controller is ready"
    else
        error "Argo Events controller readiness timeout"
        exit 1
    fi
}

# Deploy Qwen LLM infrastructure
deploy_qwen_infrastructure() {
    if [[ "${ENABLE_QWEN}" != "true" ]]; then
        log "Qwen LLM integration disabled - skipping"
        return
    fi
    
    log "Deploying Qwen LLM infrastructure..."
    
    # Deploy Ollama with Qwen
    if kubectl apply -n "${NAMESPACE}" -f core/resources/infrastructure/tenants/3-workloads/argo-events/ollama-qwen-deployment.yaml; then
        success "Ollama deployment started"
    else
        error "Failed to deploy Ollama"
        exit 1
    fi
    
    # Wait for Ollama to be ready
    log "Waiting for Ollama to be ready..."
    if kubectl wait --for condition=ready --timeout=300s pod -l app=ollama -n "${NAMESPACE}"; then
        success "Ollama is ready"
    else
        error "Ollama readiness timeout"
        exit 1
    fi
    
    # Deploy K8sGPT with Qwen configuration
    if kubectl apply -n "${NAMESPACE}" -f core/resources/infrastructure/tenants/3-workloads/argo-events/k8sgpt-qwen-config.yaml; then
        success "K8sGPT with Qwen configuration deployed"
    else
        error "Failed to deploy K8sGPT"
        exit 1
    fi
    
    # Wait for K8sGPT to be ready
    log "Waiting for K8sGPT to be ready..."
    if kubectl wait --for condition=ready --timeout=300s pod -l app=k8sgpt -n "${NAMESPACE}"; then
        success "K8sGPT is ready"
    else
        error "K8sGPT readiness timeout"
        exit 1
    fi
}

# Deploy Argo Events resources
deploy_argo_events_resources() {
    log "Deploying Argo Events resources and examples..."
    
    # Deploy core resources
    if kubectl apply -n "${NAMESPACE}" -f core/resources/infrastructure/tenants/3-workloads/argo-events/argo-events-resources.yaml; then
        success "Core Argo Events resources deployed"
    else
        error "Failed to deploy core resources"
        exit 1
    fi
    
    # Deploy event sources
    if kubectl apply -n "${NAMESPACE}" -f core/resources/infrastructure/tenants/3-workloads/argo-events/event-sources.yaml; then
        success "Event sources deployed"
    else
        error "Failed to deploy event sources"
        exit 1
    fi
    
    # Deploy sensors
    if kubectl apply -n "${NAMESPACE}" -f core/resources/infrastructure/tenants/3-workloads/argo-events/sensors.yaml; then
        success "Sensors deployed"
    else
        error "Failed to deploy sensors"
        exit 1
    fi
    
    # Deploy Qwen-integrated sensors if enabled
    if [[ "${ENABLE_QWEN}" == "true" ]]; then
        if kubectl apply -n "${NAMESPACE}" -f core/resources/infrastructure/tenants/3-workloads/argo-events/argo-events-qwen-sensor.yaml; then
            success "Qwen-integrated sensors deployed"
        else
            error "Failed to deploy Qwen sensors"
            exit 1
        fi
    fi
}

# Setup monitoring
setup_monitoring() {
    if [[ "${ENABLE_MONITORING}" != "true" ]]; then
        log "Monitoring disabled - skipping"
        return
    fi
    
    log "Setting up monitoring and observability..."
    
    # Create ServiceMonitor for Argo Events
    cat <<EOF | kubectl apply -n "${NAMESPACE}" -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: argo-events-controller
  labels:
    app.kubernetes.io/name: argo-events
    app.kubernetes.io/component: monitoring
    environment: ${ENVIRONMENT}
spec:
  selector:
    matchLabels:
      app: argo-events-controller
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
EOF
    
    # Create ServiceMonitor for Ollama if enabled
    if [[ "${ENABLE_QWEN}" == "true" ]]; then
        cat <<EOF | kubectl apply -n "${NAMESPACE}" -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ollama
  labels:
    app.kubernetes.io/name: ollama
    app.kubernetes.io/component: monitoring
    environment: ${ENVIRONMENT}
spec:
  selector:
    matchLabels:
      app: ollama
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
EOF
    fi
    
    # Create PrometheusRule for alerts
    cat <<EOF | kubectl apply -n "${NAMESPACE}" -f -
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: argo-events-alerts
  labels:
    app.kubernetes.io/name: argo-events
    app.kubernetes.io/component: monitoring
    environment: ${ENVIRONMENT}
spec:
  groups:
  - name: argo-events.rules
    rules:
    - alert: ArgoEventsDown
      expr: up{job="argo-events-controller"} == 0
      for: 1m
      labels:
        severity: critical
        environment: ${ENVIRONMENT}
      annotations:
        summary: "Argo Events controller is down"
        description: "Argo Events controller has been down for more than 1 minute in ${ENVIRONMENT}."
    
    - alert: ArgoEventsHighErrorRate
      expr: rate(argo_events_errors_total[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
        environment: ${ENVIRONMENT}
      annotations:
        summary: "Argo Events high error rate"
        description: "Argo Events error rate is {{ \$value }} errors per second in ${ENVIRONMENT}."
    
    - alert: QwenModelUnavailable
      expr: up{job="ollama"} == 0
      for: 2m
      labels:
        severity: warning
        environment: ${ENVIRONMENT}
      annotations:
        summary: "Qwen model (Ollama) is unavailable"
        description: "Qwen model service is down in ${ENVIRONMENT}."
EOF
    
    success "Monitoring setup completed"
}

# Run tests if enabled
run_tests() {
    if [[ "${ENABLE_TESTING}" != "true" ]]; then
        log "Testing disabled - skipping"
        return
    fi
    
    log "Running comprehensive tests..."
    
    # Deploy test suite
    if kubectl apply -f tests/argo-events/test-suite.yaml; then
        success "Test suite deployed"
    else
        error "Failed to deploy test suite"
        return 1
    fi
    
    # Run test runner
    if bash tests/argo-events/test-runner.sh; then
        success "Tests completed successfully"
    else
        warning "Tests completed with issues"
    fi
}

# Verify deployment
verify_deployment() {
    log "Verifying complete deployment..."
    
    local verification_passed=true
    
    # Check core components
    local components=(
        "deployment/argo-events-controller"
        "eventsources.argoproj.io"
        "sensors.argoproj.io"
    )
    
    for component in "${components[@]}"; do
        if kubectl get "${component}" -n "${NAMESPACE}" &>/dev/null; then
            success "✓ ${component} is available"
        else
            error "✗ ${component} is not available"
            verification_passed=false
        fi
    done
    
    # Check Qwen components if enabled
    if [[ "${ENABLE_QWEN}" == "true" ]]; then
        local qwen_components=(
            "deployment/ollama"
            "deployment/k8sgpt-qwen"
        )
        
        for component in "${qwen_components[@]}"; do
            if kubectl get "${component}" -n "${NAMESPACE}" &>/dev/null; then
                success "✓ ${component} is available"
            else
                error "✗ ${component} is not available"
                verification_passed=false
            fi
        done
    fi
    
    # Check monitoring if enabled
    if [[ "${ENABLE_MONITORING}" == "true" ]]; then
        if kubectl get servicemonitor -n "${NAMESPACE}" argo-events-controller &>/dev/null; then
            success "✓ ServiceMonitor is configured"
        else
            warning "⚠ ServiceMonitor not found"
        fi
    fi
    
    if [[ "${verification_passed}" == "true" ]]; then
        success "✓ All components verified successfully"
    else
        warning "⚠ Some components failed verification"
    fi
}

# Show deployment status
show_deployment_status() {
    log "Deployment Status Summary:"
    echo
    
    echo "=== Namespace ==="
    kubectl get namespace "${NAMESPACE}" -o wide
    echo
    
    echo "=== Pods ==="
    kubectl get pods -n "${NAMESPACE}" -o wide
    echo
    
    echo "=== Services ==="
    kubectl get svc -n "${NAMESPACE}" -o wide
    echo
    
    echo "=== Event Sources ==="
    kubectl get eventsources -n "${NAMESPACE}" -o wide
    echo
    
    echo "=== Sensors ==="
    kubectl get sensors -n "${NAMESPACE}" -o wide
    echo
    
    if [[ "${ENABLE_QWEN}" == "true" ]]; then
        echo "=== Qwen Components ==="
        echo "Ollama Status:"
        kubectl get pods -n "${NAMESPACE}" -l app=ollama -o wide
        echo "K8sGPT Status:"
        kubectl get pods -n "${NAMESPACE}" -l app=k8sgpt -o wide
        echo
    fi
    
    echo "=== Recent Events ==="
    kubectl get events -n "${NAMESPACE}" --sort-by='.lastTimestamp' | tail -10
    echo
}

# Show access information
show_access_info() {
    highlight "Access Information:"
    echo
    
    echo "=== Argo Events ==="
    echo "Controller Metrics: http://$(kubectl get svc argo-events-controller -n "${NAMESPACE}" -o jsonpath='{.status.clusterIP}' 2>/dev/null || echo "pending"):8080/metrics"
    echo "Health Endpoint: http://$(kubectl get svc argo-events-controller -n "${NAMESPACE}" -o jsonpath='{.status.clusterIP}' 2>/dev/null || echo "pending"):8081/healthz"
    echo
    
    if [[ "${ENABLE_QWEN}" == "true" ]]; then
        echo "=== Qwen LLM ==="
        echo "Ollama API: http://$(kubectl get svc ollama -n "${NAMESPACE}" -o jsonpath='{.status.clusterIP}' 2>/dev/null || echo "pending"):11434"
        echo "K8sGPT Service: http://$(kubectl get svc k8sgpt-qwen -n "${NAMESPACE}" -o jsonpath='{.status.clusterIP}' 2>/dev/null || echo "pending"):8080"
        echo
        
        echo "=== Qwen Model Test ==="
        echo "Test Qwen model:"
        echo "curl -X POST http://\$(kubectl get svc ollama -n ${NAMESPACE} -o jsonpath='{.status.clusterIP}'):11434/api/generate \\"
        echo "  -H 'Content-Type: application/json' \\"
        echo "  -d '{\"model\": \"${QWEN_MODEL}\", \"prompt\": \"Analyze this Argo Events configuration for issues\", \"stream\": false}'"
        echo
    fi
    
    echo "=== Monitoring ==="
    echo "Prometheus: http://prometheus-server.monitoring.svc.cluster.local:9090"
    echo "Grafana: http://grafana.monitoring.svc.cluster.local:3000"
    echo
    
    echo "=== Webhook Endpoints ==="
    kubectl get eventsources -n "${NAMESPACE}" -o jsonpath='{range .items[*]}{.metadata.name}: {.spec.webhook[*].port}{": "}{.spec.webhook[*].endpoint}{"\n"}{end}' | head -5 || echo "No webhook endpoints found"
    echo
    
    echo "=== Management Commands ==="
    echo "View logs: kubectl logs -n ${NAMESPACE} deployment/argo-events-controller -f"
    echo "Check status: kubectl get all -n ${NAMESPACE}"
    echo "Test webhook: kubectl port-forward -n ${NAMESPACE} svc/webhook-source-example 12000:12000"
    if [[ "${ENABLE_QWEN}" == "true" ]]; then
        echo "Qwen analysis: kubectl logs -n ${NAMESPACE} deployment/k8sgpt-qwen -f"
    fi
    echo
}

# Show next steps
show_next_steps() {
    highlight "Next Steps:"
    echo
    echo "1. 🚀 Test webhook endpoints:"
    echo "   kubectl port-forward -n ${NAMESPACE} svc/webhook-source-example 12000:12000"
    echo "   curl -X POST http://localhost:12000/example -H 'Content-Type: application/json' -d '{\"message\": \"test\"}'"
    echo
    echo "2. 📊 Monitor event processing:"
    echo "   kubectl logs -n ${NAMESPACE} deployment/argo-events-controller -f"
    echo
    if [[ "${ENABLE_QWEN}" == "true" ]]; then
        echo "3. 🤖 Test Qwen LLM analysis:"
        echo "   curl -X POST http://\$(kubectl get svc ollama -n ${NAMESPACE} -o jsonpath='{.status.clusterIP}'):11434/api/generate \\"
        echo "     -H 'Content-Type: application/json' \\"
        echo "     -d '{\"model\": \"${QWEN_MODEL}\", \"prompt\": \"Analyze Argo Events configuration\", \"stream\": false}'"
        echo
        echo "4. 🧠 Trigger intelligent analysis:"
        echo "   curl -X POST http://localhost:12020/k8sgpt \\"
        echo "     -H 'Content-Type: application/json' \\"
        echo "     -H 'Authorization: Bearer qwen-kwisgpt-webhook-secret-12345' \\"
        echo "     -d '{\"type\": \"analysis\", \"component\": \"eventsource\", \"severity\": \"info\"}'"
        echo
    fi
    echo "5. 📈 Check monitoring dashboards:"
    echo "   Access Grafana: http://grafana.monitoring.svc.cluster.local:3000"
    echo "   View Argo Events dashboards and alerts"
    echo
    echo "6. 🧪 Run comprehensive tests (if not already run):"
    echo "   ENABLE_TESTING=true $0"
    echo
    echo "7. 📚 Review documentation:"
    echo "   docs/argo-events/README.md"
    echo "   docs/argo-events/QUICKSTART.md"
    echo
}

# Cleanup function
cleanup() {
    if [[ "${1:-}" == "on_error" ]]; then
        error "Deployment failed - cleaning up partial installation..."
        kubectl delete namespace "${NAMESPACE}" --ignore-not-found=true --timeout=60s || true
    fi
}

# Main execution
main() {
    local command="${1:-deploy}"
    
    case "${command}" in
        deploy)
            show_banner
            check_prerequisites
            create_namespace
            install_argo_events
            deploy_qwen_infrastructure
            deploy_argo_events_resources
            setup_monitoring
            run_tests
            verify_deployment
            show_deployment_status
            show_access_info
            show_next_steps
            success "🎉 Argo Events deployment completed successfully!"
            ;;
        status)
            show_deployment_status
            show_access_info
            ;;
        test)
            ENABLE_TESTING=true
            run_tests
            ;;
        cleanup)
            log "Cleaning up Argo Events deployment..."
            kubectl delete namespace "${NAMESPACE}" --ignore-not-found=true --timeout=120s
            success "Cleanup completed"
            ;;
        *)
            echo "Usage: $0 [deploy|status|test|cleanup]"
            echo "  deploy  - Complete deployment with all components"
            echo "  status  - Show current deployment status"
            echo "  test    - Run comprehensive tests"
            echo "  cleanup - Remove all deployed resources"
            exit 1
            ;;
    esac
}

# Trap for cleanup on errors
trap 'cleanup on_error' ERR

# Run main function
main "$@"

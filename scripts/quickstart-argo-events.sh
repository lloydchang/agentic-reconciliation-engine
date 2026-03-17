#!/bin/bash

# Argo Events Quickstart Script
# This script automatically sets up Argo Events with examples

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="argo-events"
ARGO_EVENTS_VERSION="v1.9.0"
TIMEOUT=300

# Helper functions
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
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check cluster access
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot access Kubernetes cluster"
        exit 1
    fi
    
    # Check if cluster is healthy
    if ! kubectl get nodes &> /dev/null; then
        log_error "Cannot get cluster nodes"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Install Argo Events
install_argo_events() {
    log_info "Installing Argo Events..."
    
    # Create namespace
    kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -
    
    # Install Argo Events
    if kubectl apply -n "${NAMESPACE}" -f "https://raw.githubusercontent.com/argoproj/argo-events/${ARGO_EVENTS_VERSION}/manifests/install.yaml"; then
        log_success "Argo Events installation started"
    else
        log_error "Failed to install Argo Events"
        exit 1
    fi
    
    # Wait for installation
    log_info "Waiting for Argo Events to be ready..."
    if kubectl wait --for condition=available --timeout="${TIMEOUT}s" deployment/argo-events-controller -n "${NAMESPACE}"; then
        log_success "Argo Events is ready"
    else
        log_error "Argo Events installation timed out"
        exit 1
    fi
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    # Check pods
    if kubectl get pods -n "${NAMESPACE}" | grep -q "argo-events-controller"; then
        log_success "Controller pod is running"
    else
        log_error "Controller pod not found"
        exit 1
    fi
    
    # Check CRDs
    if kubectl get crd | grep -q "eventsources.argoproj.io" && kubectl get crd | grep -q "sensors.argoproj.io"; then
        log_success "CRDs are installed"
    else
        log_error "CRDs not found"
        exit 1
    fi
    
    # Check services
    if kubectl get svc -n "${NAMESPACE}" | grep -q "argo-events-controller"; then
        log_success "Services are running"
    else
        log_error "Services not found"
        exit 1
    fi
}

# Create example event sources and sensors
create_examples() {
    log_info "Creating example event sources and sensors..."
    
    # Create webhook event source
    cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: EventSource
metadata:
  name: quickstart-webhook
  namespace: ${NAMESPACE}
spec:
  webhook:
    example:
      port: "12000"
      endpoint: /webhook
      method: POST
EOF
    
    # Create calendar event source
    cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: EventSource
metadata:
  name: quickstart-calendar
  namespace: ${NAMESPACE}
spec:
  calendar:
    every-minute:
      schedule: "* * * * *"
EOF
    
    # Create sensor for webhook
    cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Sensor
metadata:
  name: quickstart-webhook-sensor
  namespace: ${NAMESPACE}
spec:
  dependencies:
    - name: webhook-dep
      eventSourceName: quickstart-webhook
      eventName: example
  triggers:
    - template:
        name: log-trigger
        log:
          level: info
          message: "Webhook received: {{webhook-dep.body}}"
EOF
    
    # Create sensor for calendar
    cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Sensor
metadata:
  name: quickstart-calendar-sensor
  namespace: ${NAMESPACE}
spec:
  dependencies:
    - name: calendar-dep
      eventSourceName: quickstart-calendar
      eventName: every-minute
  triggers:
    - template:
        name: log-trigger
        log:
          level: info
          message: "Calendar triggered at {{calendar-dep.time}}"
EOF
    
    log_success "Example event sources and sensors created"
}

# Test webhook
test_webhook() {
    log_info "Testing webhook..."
    
    # Port forward
    log_info "Setting up port forward (this will run in background)..."
    kubectl port-forward -n "${NAMESPACE}" svc/quickstart-webhook-example 12000:12000 &
    PF_PID=$!
    
    # Wait for port forward to be ready
    sleep 5
    
    # Send test webhook
    if curl -s -X POST http://localhost:12000/webhook \
        -H "Content-Type: application/json" \
        -d '{"message": "Hello Argo Events!", "timestamp": "'$(date -Iseconds)'"}' > /dev/null; then
        log_success "Webhook test sent successfully"
    else
        log_error "Webhook test failed"
    fi
    
    # Clean up port forward
    kill $PF_PID 2>/dev/null || true
}

# Show status
show_status() {
    log_info "Current status:"
    echo
    echo "=== Event Sources ==="
    kubectl get eventsources -n "${NAMESPACE}"
    echo
    echo "=== Sensors ==="
    kubectl get sensors -n "${NAMESPACE}"
    echo
    echo "=== Pods ==="
    kubectl get pods -n "${NAMESPACE}"
    echo
    echo "=== Services ==="
    kubectl get svc -n "${NAMESPACE}"
}

# Show logs
show_logs() {
    log_info "Showing recent logs..."
    kubectl logs -n "${NAMESPACE}" deployment/argo-events-controller --tail=20
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    
    # Delete examples
    kubectl delete eventsource quickstart-webhook quickstart-calendar -n "${NAMESPACE}" --ignore-not-found=true
    kubectl delete sensor quickstart-webhook-sensor quickstart-calendar-sensor -n "${NAMESPACE}" --ignore-not-found=true
    
    # Delete Argo Events
    if [[ "${CLEANUP_ALL:-}" == "true" ]]; then
        log_warning "Deleting entire Argo Events installation..."
        kubectl delete -n "${NAMESPACE}" -f "https://raw.githubusercontent.com/argoproj/argo-events/${ARGO_EVENTS_VERSION}/manifests/install.yaml" --ignore-not-found=true
        kubectl delete namespace "${NAMESPACE}" --ignore-not-found=true
    fi
    
    log_success "Cleanup completed"
}

# Show usage
usage() {
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  install     Install Argo Events and create examples"
    echo "  test        Test the webhook event source"
    echo "  status      Show current status"
    echo "  logs        Show recent logs"
    echo "  cleanup     Remove examples (set CLEANUP_ALL=true to remove everything)"
    echo "  help        Show this help message"
    echo
    echo "Examples:"
    echo "  $0 install              # Install and setup"
    echo "  $0 test                 # Test webhook"
    echo "  $0 status               # Show status"
    echo "  CLEANUP_ALL=true $0 cleanup  # Remove everything"
}

# Main script
main() {
    case "${1:-install}" in
        install)
            check_prerequisites
            install_argo_events
            verify_installation
            create_examples
            show_status
            log_success "Argo Events quickstart completed!"
            echo
            echo "Next steps:"
            echo "1. Run '$0 test' to test the webhook"
            echo "2. Run '$0 status' to check status"
            echo "3. Run '$0 logs' to see logs"
            echo "4. Check the documentation for more examples"
            ;;
        test)
            test_webhook
            log_success "Webhook test completed. Check logs with '$0 logs'"
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        cleanup)
            cleanup
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            log_error "Unknown command: $1"
            usage
            exit 1
            ;;
    esac
}

# Trap for cleanup
trap cleanup EXIT

# Run main function
main "$@"

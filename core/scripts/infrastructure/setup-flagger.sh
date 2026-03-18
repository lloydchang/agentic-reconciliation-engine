#!/bin/bash

# Flagger Progressive Delivery Setup Script
# Automated setup for Flagger with AI-powered progressive delivery capabilities

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FLAGGER_NAMESPACE="flagger-system"
FLAGGER_VERSION="v1.34.0"

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
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check helm
    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed or not in PATH"
        exit 1
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Setup provider (Istio, NGINX, etc.)
setup_provider() {
    local provider="${1:-istio}"
    
    log_info "Setting up provider: ${provider}"
    
    case "${provider}" in
        "istio")
            setup_istio
            ;;
        "nginx")
            setup_nginx
            ;;
        "linkerd")
            setup_linkerd
            ;;
        *)
            log_error "Unsupported provider: ${provider}"
            exit 1
            ;;
    esac
}

# Setup Istio
setup_istio() {
    log_info "Setting up Istio service mesh..."
    
    # Check if Istio is already installed
    if kubectl get namespace istio-system &> /dev/null; then
        log_warning "Istio namespace already exists, skipping installation"
        return
    fi
    
    # Add Istio Helm repository
    helm repo add istio https://istio-release.storage.googleapis.com/charts
    helm repo update
    
    # Install Istio base
    log_info "Installing Istio base..."
    helm upgrade --install istio-base istio/base \
        --namespace istio-system \
        --create-namespace \
        --wait
    
    # Install Istiod
    log_info "Installing Istiod..."
    helm upgrade --install istiod istio/istiod \
        --namespace istio-system \
        --wait
    
    # Install Istio ingress gateway
    log_info "Installing Istio ingress gateway..."
    helm upgrade --install istio-ingressgateway istio/gateway \
        --namespace istio-system \
        --wait
    
    log_success "Istio setup completed"
}

# Setup NGINX Ingress
setup_nginx() {
    log_info "Setting up NGINX Ingress Controller..."
    
    # Check if NGINX Ingress is already installed
    if kubectl get namespace ingress-nginx &> /dev/null; then
        log_warning "NGINX Ingress namespace already exists, skipping installation"
        return
    fi
    
    # Add NGINX Ingress Helm repository
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm repo update
    
    # Install NGINX Ingress Controller
    log_info "Installing NGINX Ingress Controller..."
    helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
        --namespace ingress-nginx \
        --create-namespace \
        --wait
    
    log_success "NGINX Ingress setup completed"
}

# Setup Linkerd
setup_linkerd() {
    log_info "Setting up Linkerd service mesh..."
    
    # Check if linkerd CLI is available
    if ! command -v linkerd &> /dev/null; then
        log_error "linkerd CLI is not installed"
        exit 1
    fi
    
    # Check if Linkerd is already installed
    if kubectl get namespace linkerd &> /dev/null; then
        log_warning "Linkerd namespace already exists, skipping installation"
        return
    fi
    
    # Install Linkerd
    log_info "Installing Linkerd..."
    linkerd install | kubectl apply -f -
    
    # Verify installation
    log_info "Verifying Linkerd installation..."
    linkerd check
    
    log_success "Linkerd setup completed"
}

# Install Flagger
install_flagger() {
    local provider="${1:-istio}"
    
    log_info "Installing Flagger with ${provider} provider..."
    
    # Add Flagger Helm repository
    helm repo add flagger https://flagger.app
    helm repo update
    
    # Install Flagger
    log_info "Installing Flagger operator..."
    helm upgrade --install flagger flagger/flagger \
        --namespace "${FLAGGER_NAMESPACE}" \
        --create-namespace \
        --set meshProvider="${provider}" \
        --set crds.install=true \
        --set logLevel=info \
        --set metrics.enabled=true \
        --set webhook.enabled=true \
        --wait
    
    log_success "Flagger installation completed"
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring for Flagger..."
    
    # Create monitoring namespace if it doesn't exist
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
    
    # Install Prometheus (simplified - in production use proper monitoring setup)
    if ! kubectl get deployment prometheus-server -n monitoring &> /dev/null; then
        log_info "Installing Prometheus..."
        # This is a simplified Prometheus setup
        # In production, use kube-prometheus-stack or similar
        kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus-server
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        args:
        - '--config.file=/etc/prometheus/prometheus.yml'
        - '--storage.tsdb.path=/prometheus/'
        - '--web.console.libraries=/etc/prometheus/console_libraries'
        - '--web.console.templates=/etc/prometheus/consoles'
        - '--storage.tsdb.retention.time=200h'
        - '--web.enable-lifecycle'
        volumeMounts:
        - name: prometheus-config-volume
          mountPath: /etc/prometheus/
      volumes:
      - name: prometheus-config-volume
        configMap:
          name: prometheus-config
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus-service
  namespace: monitoring
spec:
  selector:
    app: prometheus
  ports:
    - port: 9090
      targetPort: 9090
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'flagger'
      static_configs:
      - targets: ['flagger.fagger-system:8080']
EOF
    fi
    
    log_success "Monitoring setup completed"
}

# Setup Qwen LLM integration
setup_qwen_integration() {
    log_info "Setting up Qwen LLM integration..."
    
    # Create Qwen configuration
    kubectl create configmap qwen-config \
        --from-literal=model=qwen2.5-7b-instruct \
        --from-literal=base_url=http://localhost:8000/v1 \
        --from-literal=max_tokens=4096 \
        --from-literal=temperature=0.7 \
        --namespace "${FLAGGER_NAMESPACE}" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Create K8sGPT configuration
    kubectl create configmap k8sgpt-config \
        --from-literal=backend=localai \
        --from-literal=model=qwen2.5-7b-instruct \
        --from-literal=namespace=default \
        --from-literal=output_format=json \
        --from-literal=analysis=true \
        --from-literal=explain=true \
        --namespace "${FLAGGER_NAMESPACE}" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    log_success "Qwen LLM integration setup completed"
}

# Deploy example applications
deploy_examples() {
    log_info "Deploying example applications..."
    
    # Create examples namespace
    kubectl create namespace examples --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy frontend example
    log_info "Deploying frontend example..."
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: examples
  labels:
    app: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
        version: v1
    spec:
      containers:
      - name: frontend
        image: ghcr.io/fluxcd/flagger-loadtester:0.26.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: 10m
            memory: 64Mi
          limits:
            cpu: 100m
            memory: 128Mi
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: examples
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
  selector:
    app: frontend
EOF
    
    # Deploy canary configuration for frontend
    log_info "Creating canary configuration for frontend..."
    kubectl apply -f - <<EOF
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: frontend
  namespace: examples
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: frontend
  service:
    port: 80
    targetPort: 8080
  analysis:
    interval: 10s
    threshold: 99
    iterations: 10
    metrics:
    - name: request-success-rate
      threshold: 99
      interval: 1m
    webhooks:
    - name: load-test
      url: http://flagger-loadtester.fagger-system/
      timeout: 30s
      metadata:
        cmd: "hey -z 1m -q 10 -c 2 http://frontend.examples/"
        expected_status: "200"
  canarySteps:
  - setWeight: 10
  - pause:
      duration: 1m
  - setWeight: 20
  - pause:
      duration: 1m
  - setWeight: 30
  - pause:
      duration: 1m
  - setWeight: 50
  - pause:
      duration: 1m
  - setWeight: 100
EOF
    
    log_success "Example applications deployed"
}

# Verify installation
verify_installation() {
    log_info "Verifying Flagger installation..."
    
    # Check Flagger pods
    if kubectl get pods -n "${FLAGGER_NAMESPACE}" -l app=flagger | grep -q "Running"; then
        log_success "Flagger pods are running"
    else
        log_error "Flagger pods are not running"
        return 1
    fi
    
    # Check Flagger CRDs
    if kubectl get crd | grep -q "flagger.app"; then
        log_success "Flagger CRDs are installed"
    else
        log_error "Flagger CRDs are not installed"
        return 1
    fi
    
    # Check example canary
    if kubectl get canary frontend -n examples &> /dev/null; then
        log_success "Example canary is created"
    else
        log_error "Example canary is not created"
        return 1
    fi
    
    log_success "Installation verification completed"
}

# Show status and next steps
show_status() {
    log_info "Flagger installation status:"
    echo
    
    echo "Namespace: ${FLAGGER_NAMESPACE}"
    echo "Flagger version: ${FLAGGER_VERSION}"
    echo
    
    # Show Flagger pods
    echo "Flagger pods:"
    kubectl get pods -n "${FLAGGER_NAMESPACE}" -l app=flagger
    echo
    
    # Show canaries
    echo "Canaries:"
    kubectl get canaries -A
    echo
    
    # Show next steps
    echo "Next steps:"
    echo "1. Monitor Flagger logs: kubectl logs -n ${FLAGGER_NAMESPACE} deployment/flagger -f"
    echo "2. Check canary status: kubectl get canary frontend -n examples"
    echo "3. Trigger canary deployment: kubectl set image deployment/frontend frontend=new-image -n examples"
    echo "4. View documentation: ${REPO_ROOT}/docs/flagger-quickstart.md"
    echo
}

# Cleanup function
cleanup() {
    local provider="${1:-istio}"
    
    log_warning "Cleaning up Flagger installation..."
    
    # Delete examples
    kubectl delete namespace examples --ignore-not-found=true
    
    # Delete Flagger
    helm uninstall flagger -n "${FLAGGER_NAMESPACE}" --ignore-not-found=true
    kubectl delete namespace "${FLAGGER_NAMESPACE}" --ignore-not-found=true
    
    # Delete monitoring
    kubectl delete namespace monitoring --ignore-not-found=true
    
    # Delete provider (optional)
    if [[ "${CLEANUP_PROVIDER:-false}" == "true" ]]; then
        case "${provider}" in
            "istio")
                helm uninstall istio-ingressgateway -n istio-system --ignore-not-found=true
                helm uninstall istiod -n istio-system --ignore-not-found=true
                helm uninstall istio-base -n istio-system --ignore-not-found=true
                kubectl delete namespace istio-system --ignore-not-found=true
                ;;
            "nginx")
                helm uninstall ingress-nginx -n ingress-nginx --ignore-not-found=true
                kubectl delete namespace ingress-nginx --ignore-not-found=true
                ;;
            "linkerd")
                linkerd uninstall | kubectl delete -f - || true
                ;;
        esac
    fi
    
    log_success "Cleanup completed"
}

# Main function
main() {
    local action="${1:-install}"
    local provider="${2:-istio}"
    
    case "${action}" in
        "install")
            log_info "Starting Flagger installation with ${provider} provider..."
            check_prerequisites
            setup_provider "${provider}"
            install_flagger "${provider}"
            setup_monitoring
            setup_qwen_integration
            deploy_examples
            verify_installation
            show_status
            log_success "Flagger installation completed successfully!"
            ;;
        "cleanup")
            cleanup "${provider}"
            ;;
        "verify")
            verify_installation
            show_status
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [install|cleanup|verify|help] [provider]"
            echo
            echo "Actions:"
            echo "  install  - Install Flagger with specified provider (default)"
            echo "  cleanup  - Remove Flagger installation"
            echo "  verify   - Verify Flagger installation"
            echo "  help     - Show this help message"
            echo
            echo "Providers:"
            echo "  istio    - Istio service mesh (default)"
            echo "  nginx    - NGINX Ingress Controller"
            echo "  linkerd  - Linkerd service mesh"
            echo
            echo "Examples:"
            echo "  $0 install istio     # Install Flagger with Istio"
            echo "  $0 install nginx     # Install Flagger with NGINX"
            echo "  $0 cleanup istio     # Clean up Flagger with Istio"
            echo "  $0 verify             # Verify installation"
            ;;
        *)
            log_error "Unknown action: ${action}"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Trap for cleanup
trap 'log_error "Script failed"' ERR

# Run main function with all arguments
main "$@"

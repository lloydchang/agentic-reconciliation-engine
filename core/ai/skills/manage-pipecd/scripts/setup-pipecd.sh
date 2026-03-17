#!/bin/bash

# PipeCD Setup Script
# This script automates the installation and configuration of PipeCD with Qwen LLM integration

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${PIPECD_NAMESPACE:-pipecd}"
PROJECT_NAME="${PIPECD_PROJECT:-quickstart}"
QWEN_ENABLED="${QWEN_ENABLED:-true}"
QWEN_MODEL="${QWEN_MODEL:-qwen2.5-72b-instruct}"
QWEN_ENDPOINT="${QWEN_ENDPOINT:-http://qwen-llm-service.ai.svc.cluster.local:8080}"

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
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    # Check if helm is available (for Qwen integration)
    if [[ "$QWEN_ENABLED" == "true" ]] && ! command -v helm &> /dev/null; then
        log_warning "helm is not installed. Qwen integration requires helm."
        QWEN_ENABLED="false"
    fi
    
    log_success "Prerequisites check completed"
}

# Install PipeCD control plane
install_control_plane() {
    log_info "Installing PipeCD control plane in namespace: $NAMESPACE"
    
    # Create namespace
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Install control plane
    if kubectl apply -n "$NAMESPACE" -f https://raw.githubusercontent.com/pipe-cd/pipecd/master/quickstart/manifests/control-plane.yaml; then
        log_success "PipeCD control plane installed successfully"
    else
        log_error "Failed to install PipeCD control plane"
        exit 1
    fi
    
    # Wait for components to be ready
    log_info "Waiting for PipeCD components to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=pipecd -n "$NAMESPACE" --timeout=300s
    
    log_success "PipeCD control plane is ready"
}

# Setup port forwarding
setup_port_forward() {
    log_info "Setting up port forwarding for PipeCD console..."
    
    # Check if port is already in use
    if lsof -i :8080 &> /dev/null; then
        log_warning "Port 8080 is already in use. Please stop the existing process or use a different port."
        return 1
    fi
    
    # Start port forwarding in background
    kubectl port-forward -n "$NAMESPACE" svc/pipecd 8080 &
    PORT_FORWARD_PID=$!
    
    # Wait a moment for port forwarding to establish
    sleep 5
    
    if kill -0 $PORT_FORWARD_PID 2>/dev/null; then
        log_success "Port forwarding established (PID: $PORT_FORWARD_PID)"
        echo $PORT_FORWARD_PID > /tmp/pipecd-port-forward.pid
        log_info "PipeCD console is available at: http://localhost:8080?project=$PROJECT_NAME"
        log_info "Login credentials: hello-pipecd / hello-pipecd"
    else
        log_error "Failed to establish port forwarding"
        return 1
    fi
}

# Install Qwen LLM integration
install_qwen_integration() {
    if [[ "$QWEN_ENABLED" != "true" ]]; then
        log_info "Qwen integration is disabled"
        return 0
    fi
    
    log_info "Installing Qwen LLM integration..."
    
    # Add Qwen helm repository
    helm repo add qwen https://qwen-ai.github.io/helm-charts 2>/dev/null || helm repo add qwen https://kubernetes-charts.banzaicloud.com/charts
    helm repo update
    
    # Install Qwen LLM service
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: qwen-ai
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qwen-llm-service
  namespace: qwen-ai
spec:
  replicas: 1
  selector:
    matchLabels:
      app: qwen-llm-service
  template:
    metadata:
      labels:
        app: qwen-llm-service
    spec:
      containers:
      - name: qwen-llm
        image: qwen/qwen2.5-72b-instruct:latest
        ports:
        - containerPort: 8080
        env:
        - name: MODEL_NAME
          value: "$QWEN_MODEL"
        - name: ENDPOINT
          value: "$QWEN_ENDPOINT"
        resources:
          requests:
            memory: "16Gi"
            cpu: "4"
          limits:
            memory: "32Gi"
            cpu: "8"
---
apiVersion: v1
kind: Service
metadata:
  name: qwen-llm-service
  namespace: qwen-ai
spec:
  selector:
    app: qwen-llm-service
  ports:
  - port: 8080
    targetPort: 8080
EOF
    
    # Wait for Qwen service to be ready
    log_info "Waiting for Qwen LLM service to be ready..."
    kubectl wait --for=condition=ready pod -l app=qwen-llm-service -n qwen-ai --timeout=600s
    
    log_success "Qwen LLM integration installed"
}

# Configure K8sGPT with Qwen
configure_k8sgpt() {
    if [[ "$QWEN_ENABLED" != "true" ]]; then
        log_info "Skipping K8sGPT configuration (Qwen disabled)"
        return 0
    fi
    
    log_info "Configuring K8sGPT with Qwen integration..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: k8sgpt-config
  namespace: $NAMESPACE
data:
  config.yaml: |
    ai:
      provider: qwen
      model: $QWEN_MODEL
      endpoint: $QWEN_ENDPOINT
      apikey: "\${QWEN_API_KEY}"
      max_tokens: 4096
      temperature: 0.7
    analysis:
      enable_deployment_analysis: true
      enable_performance_monitoring: true
      enable_security_analysis: true
      enable_cost_optimization: true
    filters:
      exclude_namespaces:
        - kube-system
        - kube-public
        - kube-node-lease
      include_resources:
        - deployments
        - services
        - configmaps
        - secrets
    sinks:
      prometheus:
        enabled: true
        address: http://prometheus.monitoring.svc.cluster.local:9090
      grafana:
        enabled: true
        address: http://grafana.monitoring.svc.cluster.local:3000
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: k8sgpt-analyzer
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: k8sgpt-analyzer
  template:
    metadata:
      labels:
        app: k8sgpt-analyzer
    spec:
      containers:
      - name: k8sgpt
        image: ghcr.io/k8sgpt-ai/k8sgpt:latest
        command: ["/bin/sh"]
        args: ["-c", "while true; do k8sgpt analyze --output json --provider=qwen --model=$QWEN_MODEL --endpoint=$QWEN_ENDPOINT; sleep 300; done"]
        env:
        - name: QWEN_API_KEY
          valueFrom:
            secretKeyRef:
              name: qwen-api-key
              key: api-key
        volumeMounts:
        - name: config
          mountPath: /etc/k8sgpt
          readOnly: true
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: config
        configMap:
          name: k8sgpt-config
EOF
    
    log_success "K8sGPT configured with Qwen integration"
}

# Create example application
create_example_app() {
    log_info "Creating example application..."
    
    cat <<EOF > /tmp/pipecd-example-app.yaml
apiVersion: pipecd.dev/v1beta1
kind: Application
metadata:
  name: web-app
spec:
  pipeline:
    stages:
      - name: K8S_CANARY_ROLLOUT
        with:
          replicas: 10%
      - name: K8S_TRAFFIC_ROUTING
        with:
          weight: 10%
      - name: K8S_PRIMARY_ROLLOUT
        with:
          replicas: 100%
      - name: K8S_TRAFFIC_ROUTING
        with:
          weight: 100%
      - name: ANALYSIS
        with:
          duration: 5m
          metrics:
            - name: success_rate
              query: "rate(http_requests_total{status=~'2..'}[5m])"
            - name: error_rate
              query: "rate(http_requests_total{status=~'5..'}[5m])"
EOF
    
    log_info "Example application configuration saved to /tmp/pipecd-example-app.yaml"
    log_info "You can apply this configuration through the PipeCD console"
}

# Display next steps
show_next_steps() {
    log_success "PipeCD setup completed successfully!"
    echo
    log_info "Next steps:"
    echo "1. Access PipeCD console: http://localhost:8080?project=$PROJECT_NAME"
    echo "2. Login with: hello-pipecd / hello-pipecd"
    echo "3. Register a piped agent in the console"
    echo "4. Configure your Git repository"
    echo "5. Deploy your first application"
    echo
    log_info "Useful commands:"
    echo "- Check PipeCD status: kubectl get pods -n $NAMESPACE"
    echo "- View logs: kubectl logs -n $NAMESPACE deployment/pipecd-server"
    echo "- Stop port forwarding: kill \$(cat /tmp/pipecd-port-forward.pid)"
    echo
    if [[ "$QWEN_ENABLED" == "true" ]]; then
        log_info "Qwen LLM integration:"
        echo "- Check Qwen status: kubectl get pods -n qwen-ai"
        echo "- Configure QWEN_API_KEY: kubectl create secret generic qwen-api-key -n $NAMESPACE --from-literal=api-key=your-api-key"
    fi
}

# Cleanup function
cleanup() {
    if [[ -f /tmp/pipecd-port-forward.pid ]]; then
        PID=$(cat /tmp/pipecd-port-forward.pid)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            log_info "Stopped port forwarding (PID: $PID)"
        fi
        rm -f /tmp/pipecd-port-forward.pid
    fi
}

# Main execution
main() {
    log_info "Starting PipeCD setup..."
    
    # Set up cleanup trap
    trap cleanup EXIT
    
    # Execute setup steps
    check_prerequisites
    install_control_plane
    setup_port_forward
    install_qwen_integration
    configure_k8sgpt
    create_example_app
    show_next_steps
    
    log_success "Setup completed. Press Ctrl+C to stop port forwarding."
    
    # Keep script running to maintain port forwarding
    wait
}

# Handle script arguments
case "${1:-}" in
    "cleanup")
        cleanup
        exit 0
        ;;
    "status")
        echo "PipeCD components:"
        kubectl get pods -n "$NAMESPACE"
        if [[ "$QWEN_ENABLED" == "true" ]]; then
            echo
            echo "Qwen components:"
            kubectl get pods -n qwen-ai
        fi
        exit 0
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [cleanup|status|help]"
        echo "  cleanup - Stop port forwarding and cleanup"
        echo "  status  - Show component status"
        echo "  help    - Show this help message"
        echo
        echo "Environment variables:"
        echo "  PIPECD_NAMESPACE - Kubernetes namespace for PipeCD (default: pipecd)"
        echo "  PIPECD_PROJECT    - PipeCD project name (default: quickstart)"
        echo "  QWEN_ENABLED      - Enable Qwen LLM integration (default: true)"
        echo "  QWEN_MODEL        - Qwen model to use (default: qwen2.5-72b-instruct)"
        echo "  QWEN_ENDPOINT     - Qwen service endpoint"
        exit 0
        ;;
    "")
        main
        ;;
    *)
        log_error "Unknown argument: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac

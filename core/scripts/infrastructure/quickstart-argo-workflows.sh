#!/bin/bash

# Argo Workflows Quickstart Script with Qwen LLM Integration
# This script automatically sets up Argo Workflows with comprehensive testing and Qwen integration

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
ARGO_WORKFLOWS_VERSION="v3.5.0"
NAMESPACE="argo-workflows"
QWEN_MODEL="qwen"
CLUSTER_TYPE="auto"
INSTALL_MONITORING=true
INSTALL_MINIO=true
ENABLE_QWEN=true
AUTO_APPROVE=false

# Functions
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

show_help() {
    cat << EOF
Argo Workflows Quickstart with Qwen LLM Integration

Usage: $0 [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -n, --namespace NAME    Set namespace (default: argo-workflows)
    -v, --version VERSION  Set Argo Workflows version (default: v3.5.0)
    -c, --cluster TYPE     Cluster type: kind, k3s, eks, gke, aks, auto (default: auto)
    --no-monitoring         Skip monitoring installation
    --no-minio             Skip MinIO installation
    --no-qwen              Skip Qwen LLM integration
    --auto-approve         Auto-approve all prompts
    --dry-run              Show what would be installed without installing

EXAMPLES:
    $0                      # Install with default settings
    $0 --namespace my-wf   # Install to custom namespace
    $0 --cluster kind      # Install on kind cluster
    $0 --no-monitoring     # Install without monitoring
    $0 --dry-run           # Preview installation

EOF
}

detect_cluster_type() {
    log_info "Detecting cluster type..."
    
    # Check for kind
    if kubectl get nodes | grep -q "kind-control-plane\|kind-worker"; then
        CLUSTER_TYPE="kind"
        log_success "Detected kind cluster"
        return
    fi
    
    # Check for k3s
    if kubectl get nodes | grep -q "k3s"; then
        CLUSTER_TYPE="k3s"
        log_success "Detected k3s cluster"
        return
    fi
    
    # Check for EKS
    if kubectl get nodes | grep -q "eks"; then
        CLUSTER_TYPE="eks"
        log_success "Detected EKS cluster"
        return
    fi
    
    # Check for GKE
    if kubectl get nodes | grep -q "gke"; then
        CLUSTER_TYPE="gke"
        log_success "Detected GKE cluster"
        return
    fi
    
    # Check for AKS
    if kubectl get nodes | grep -q "aks"; then
        CLUSTER_TYPE="aks"
        log_success "Detected AKS cluster"
        return
    fi
    
    # Default to generic
    CLUSTER_TYPE="generic"
    log_warning "Could not detect specific cluster type, using generic configuration"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check kustomize
    if ! command -v kustomize &> /dev/null; then
        log_warning "kustomize not found, installing..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install kustomize
        else
            curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
            sudo mv kustomize /usr/local/bin/
        fi
    fi
    
    # Check helm (optional)
    if ! command -v helm &> /dev/null; then
        log_warning "helm not found, some features may not work"
    fi
    
    log_success "Prerequisites check completed"
}

create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE already exists"
    else
        kubectl create namespace "$NAMESPACE"
        kubectl label namespace "$NAMESPACE" \
            app.kubernetes.io/name=argo-workflows \
            app.kubernetes.io/component=workflows \
            app.kubernetes.io/part-of=agentic-reconciliation-engine
        log_success "Namespace $NAMESPACE created"
    fi
}

install_argo_workflows() {
    log_info "Installing Argo Workflows $ARGO_WORKFLOWS_VERSION..."
    
    # Apply the overlay
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would apply Argo Workflows overlay"
        kustomize build overlay/argo-workflows | kubectl apply --dry-run=client -f -
    else
        kustomize build overlay/argo-workflows | kubectl apply -f -
        log_success "Argo Workflows installed"
    fi
}

install_qwen_integration() {
    if [[ "$ENABLE_QWEN" != "true" ]]; then
        log_info "Skipping Qwen LLM integration"
        return
    fi
    
    log_info "Installing Qwen LLM integration..."
    
    # Create Qwen LocalAI deployment
    cat << EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qwen-localai
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: argo-workflows
    app.kubernetes.io/component: qwen-localai
    app.kubernetes.io/llm: qwen
spec:
  replicas: 1
  selector:
    matchLabels:
      app: qwen-localai
  template:
    metadata:
      labels:
        app: qwen-localai
        app.kubernetes.io/name: argo-workflows
        app.kubernetes.io/component: qwen-localai
        app.kubernetes.io/llm: qwen
    spec:
      containers:
      - name: qwen-localai
        image: quay.io/go-skynet/local-ai:v2.5.0
        ports:
        - name: http
          containerPort: 8080
        env:
        - name: MODELS_PATH
          value: /models
        - name: DEBUG
          value: "true"
        resources:
          requests:
            cpu: "1000m"
            memory: "2Gi"
          limits:
            cpu: "4000m"
            memory: "8Gi"
        volumeMounts:
        - name: models
          mountPath: /models
      volumes:
      - name: models
        emptyDir:
          sizeLimit: 4Gi
EOF

    # Wait for Qwen LocalAI to be ready
    if [[ "$DRY_RUN" != "true" ]]; then
        log_info "Waiting for Qwen LocalAI to be ready..."
        kubectl wait --for=condition=available --timeout=300s deployment/qwen-localai -n "$NAMESPACE"
        
        # Download Qwen model
        log_info "Downloading Qwen model..."
        kubectl exec -n "$NAMESPACE" deployment/qwen-localai -- \
            curl -L https://huggingface.co/Qwen/Qwen-7B-Chat-GGUF/resolve/main/qwen-7b-chat.q4_0.gguf -o /models/qwen-7b-chat.gguf
        
        log_success "Qwen LLM integration completed"
    fi
}

install_monitoring() {
    if [[ "$INSTALL_MONITORING" != "true" ]]; then
        log_info "Skipping monitoring installation"
        return
    fi
    
    log_info "Installing monitoring stack..."
    
    # Install Prometheus Operator
    if helm repo list | grep -q "prometheus-community"; then
        helm repo update prometheus-community
    else
        helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
        helm repo update
    fi
    
    # Install kube-prometheus-stack
    if [[ "$DRY_RUN" != "true" ]]; then
        helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
            --namespace monitoring \
            --create-namespace \
            --set prometheus.prometheusSpec.retention=7d \
            --set grafana.adminPassword=admin123 \
            --wait \
            --timeout=10m
        
        log_success "Monitoring stack installed"
    else
        log_info "DRY RUN: Would install monitoring stack"
    fi
}

install_minio() {
    if [[ "$INSTALL_MINIO" != "true" ]]; then
        log_info "Skipping MinIO installation"
        return
    fi
    
    log_info "Installing MinIO for artifact storage..."
    
    cat << EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
  namespace: $NAMESPACE
  labels:
    app: minio
spec:
  replicas: 1
  selector:
    matchLabels:
      app: minio
  template:
    metadata:
      labels:
        app: minio
    spec:
      containers:
      - name: minio
        image: minio/minio:latest
        args:
        - server
        - /data
        - --console-address
        - ":9001"
        ports:
        - name: api
          containerPort: 9000
        - name: console
          containerPort: 9001
        env:
        - name: MINIO_ROOT_USER
          value: "admin"
        - name: MINIO_ROOT_PASSWORD
          value: "admin123"
        resources:
          requests:
            cpu: "100m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "1Gi"
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: minio
  namespace: $NAMESPACE
spec:
  selector:
    app: minio
  ports:
  - name: api
    port: 9000
    targetPort: 9000
  - name: console
    port: 9001
    targetPort: 9001
---
apiVersion: v1
kind: Secret
metadata:
  name: argo-workflows-minio
  namespace: $NAMESPACE
type: Opaque
data:
  accesskey: YWRtaW4=  # admin
  secretkey: YWRtaW4xMjM=  # admin123
EOF

    if [[ "$DRY_RUN" != "true" ]]; then
        log_info "Waiting for MinIO to be ready..."
        kubectl wait --for=condition=available --timeout=300s deployment/minio -n "$NAMESPACE"
        
        # Create bucket
        log_info "Creating MinIO bucket..."
        kubectl run minio-client --rm -i --restart=Never --image=minio/mc:latest \
            --namespace="$NAMESPACE" -- \
            mc alias set minio http://minio:9000 admin admin123 && \
            mc mb minio/argo-workflows --ignore-existing
        
        log_success "MinIO installed and configured"
    fi
}

wait_for_readiness() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Skipping readiness checks"
        return
    fi
    
    log_info "Waiting for Argo Workflows components to be ready..."
    
    # Wait for controller
    kubectl wait --for=condition=available --timeout=300s deployment/argo-workflows-controller -n "$NAMESPACE"
    
    # Wait for server
    kubectl wait --for=condition=available --timeout=300s deployment/argo-workflows-server -n "$NAMESPACE"
    
    if [[ "$ENABLE_QWEN" == "true" ]]; then
        kubectl wait --for=condition=available --timeout=300s deployment/qwen-k8sgpt -n "$NAMESPACE"
    fi
    
    log_success "All components are ready"
}

run_tests() {
    log_info "Running automated tests..."
    
    # Test basic workflow
    cat << EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: quickstart-test
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: argo-workflows
    app.kubernetes.io/component: test
spec:
  entrypoint: test
  templates:
  - name: test
    container:
      image: alpine:latest
      command: [echo]
      args: ["Quickstart test successful!"]
EOF

    if [[ "$DRY_RUN" != "true" ]]; then
        log_info "Waiting for test workflow to complete..."
        kubectl wait --for=condition=Succeeded --timeout=300s workflow/quickstart-test -n "$NAMESPACE"
        
        # Get workflow logs
        log_info "Test workflow logs:"
        kubectl logs -n "$NAMESPACE" -l workflow=quickstart-test -c main
        
        # Clean up test workflow
        kubectl delete workflow quickstart-test -n "$NAMESPACE"
        
        log_success "Automated tests completed successfully"
    fi
}

setup_port_forwarding() {
    log_info "Setting up port forwarding..."
    
    # Argo Workflows UI
    log_info "Argo Workflows UI: http://localhost:2746"
    kubectl port-forward -n "$NAMESPACE" svc/argo-workflows-server 2746:2746 &
    ARGO_PORT_FORWARD_PID=$!
    
    # Qwen K8sGPT API
    if [[ "$ENABLE_QWEN" == "true" ]]; then
        log_info "Qwen K8sGPT API: http://localhost:8080"
        kubectl port-forward -n "$NAMESPACE" svc/qwen-k8sgpt 8080:8080 &
        QWEN_PORT_FORWARD_PID=$!
    fi
    
    # MinIO Console
    if [[ "$INSTALL_MINIO" == "true" ]]; then
        log_info "MinIO Console: http://localhost:9001"
        kubectl port-forward -n "$NAMESPACE" svc/minio 9001:9001 &
        MINIO_PORT_FORWARD_PID=$!
    fi
    
    # Store PIDs for cleanup
    echo "$ARGO_PORT_FORWARD_PID" > /tmp/argo-port-forward.pid
    [[ -n "${QWEN_PORT_FORWARD_PID:-}" ]] && echo "$QWEN_PORT_FORWARD_PID" >> /tmp/argo-port-forward.pid
    [[ -n "${MINIO_PORT_FORWARD_PID:-}" ]] && echo "$MINIO_PORT_FORWARD_PID" >> /tmp/argo-port-forward.pid
}

show_access_info() {
    log_success "Argo Workflows with Qwen LLM integration is ready!"
    echo
    echo "=== Access Information ==="
    echo "Argo Workflows UI: http://localhost:2746"
    echo "Namespace: $NAMESPACE"
    echo "Version: $ARGO_WORKFLOWS_VERSION"
    echo
    
    if [[ "$ENABLE_QWEN" == "true" ]]; then
        echo "=== Qwen LLM Integration ==="
        echo "Qwen K8sGPT API: http://localhost:8080"
        echo "Health Check: curl http://localhost:8080/health"
        echo "Example Analysis: curl -X POST http://localhost:8080/analyze -H 'Content-Type: application/json' -d '{\"event_type\":\"test\",\"namespace\":\"$NAMESPACE\"}'"
        echo
    fi
    
    if [[ "$INSTALL_MINIO" == "true" ]]; then
        echo "=== MinIO Storage ==="
        echo "MinIO Console: http://localhost:9001"
        echo "Username: admin"
        echo "Password: admin123"
        echo "Bucket: argo-workflows"
        echo
    fi
    
    if [[ "$INSTALL_MONITORING" == "true" ]]; then
        echo "=== Monitoring ==="
        echo "Prometheus: kubectl port-forward -n monitoring svc/prometheus-server 9090:80"
        echo "Grafana: kubectl port-forward -n monitoring svc/grafana 3000:3000"
        echo "Grafana Password: admin123"
        echo
    fi
    
    echo "=== Next Steps ==="
    echo "1. Open the Argo Workflows UI at http://localhost:2746"
    echo "2. Try the example workflows in the overlay/argo-workflows/examples/ directory"
    echo "3. Test Qwen integration with the analysis workflows"
    echo "4. Configure your own workflows using the templates"
    echo
    echo "=== Cleanup ==="
    echo "To stop port forwarding: kill \$(cat /tmp/argo-port-forward.pid)"
    echo "To uninstall: ./scripts/uninstall-argo-workflows.sh --namespace $NAMESPACE"
    echo
}

cleanup() {
    log_info "Cleaning up..."
    
    if [[ -f /tmp/argo-port-forward.pid ]]; then
        while read -r pid; do
            kill "$pid" 2>/dev/null || true
        done < /tmp/argo-port-forward.pid
        rm -f /tmp/argo-port-forward.pid
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -v|--version)
            ARGO_WORKFLOWS_VERSION="$2"
            shift 2
            ;;
        -c|--cluster)
            CLUSTER_TYPE="$2"
            shift 2
            ;;
        --no-monitoring)
            INSTALL_MONITORING=false
            shift
            ;;
        --no-minio)
            INSTALL_MINIO=false
            shift
            ;;
        --no-qwen)
            ENABLE_QWEN=false
            shift
            ;;
        --auto-approve)
            AUTO_APPROVE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
main() {
    trap cleanup EXIT
    
    log_info "Starting Argo Workflows quickstart with Qwen LLM integration..."
    
    check_prerequisites
    
    if [[ "$CLUSTER_TYPE" == "auto" ]]; then
        detect_cluster_type
    fi
    
    create_namespace
    install_argo_workflows
    install_qwen_integration
    install_monitoring
    install_minio
    wait_for_readiness
    run_tests
    setup_port_forwarding
    show_access_info
    
    log_success "Quickstart completed successfully!"
}

# Run main function
main "$@"

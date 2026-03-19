#!/bin/bash

# Argo Rollouts Quickstart Script
# This script automatically sets up Argo Rollouts with K8sGPT Qwen integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="argo-rollouts"
K8SGPT_NAMESPACE="$TOPDIR"
ARGO_ROLLOUTS_VERSION="v1.7.0"
QWEN_MODEL="qwen2.5-7b-instruct"

# Functions
print_header() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    print_success "kubectl found: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"
    
    # Check cluster access
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot access Kubernetes cluster"
        exit 1
    fi
    print_success "Kubernetes cluster accessible"
    
    # Check helm
    if ! command -v helm &> /dev/null; then
        print_error "Helm is not installed or not in PATH"
        exit 1
    fi
    print_success "Helm found: $(helm version --short 2>/dev/null || helm version)"
    
    # Check cluster version
    k8s_version=$(kubectl version -o json | jq -r '.serverVersion.minor' | sed 's/[^0-9]//g')
    if [ "$k8s_version" -lt 20 ]; then
        print_error "Kubernetes version must be 1.20 or higher (found: $k8s_version)"
        exit 1
    fi
    print_success "Kubernetes version compatible: 1.$k8s_version"
    
    # Check if cluster has sufficient resources
    nodes_count=$(kubectl get nodes --no-headers | wc -l)
    if [ "$nodes_count" -lt 1 ]; then
        print_error "Cluster must have at least 1 node"
        exit 1
    fi
    print_success "Cluster has $nodes_count node(s)"
}

install_argo_rollouts() {
    print_header "Installing Argo Rollouts"
    
    # Create namespace
    print_info "Creating namespace: $NAMESPACE"
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Add Argo Rollouts Helm repository
    print_info "Adding Argo Rollouts Helm repository"
    helm repo add argo-rollouts https://argoproj.github.io/argo-helm
    helm repo update
    
    # Install Argo Rollouts
    print_info "Installing Argo Rollouts version: $ARGO_ROLLOUTS_VERSION"
    helm upgrade --install argo-rollouts argo-rollouts/argo-rollouts \
        --namespace "$NAMESPACE" \
        --version "$ARGO_ROLLOUTS_VERSION" \
        --set controller.image.tag="$ARGO_ROLLOUTS_VERSION" \
        --set controller.metrics.enabled=true \
        --set controller.serviceMonitor.enabled=true \
        --wait \
        --timeout=300s
    
    # Verify installation
    print_info "Verifying Argo Rollouts installation"
    kubectl wait --for=condition=available deployment/argo-rollouts -n "$NAMESPACE" --timeout=300s
    
    # Check CRDs
    if kubectl get crd rollouts.argoproj.io &> /dev/null; then
        print_success "Argo Rollouts CRDs installed"
    else
        print_error "Argo Rollouts CRDs not found"
        exit 1
    fi
    
    print_success "Argo Rollouts installed successfully"
}

install_kubectl_plugin() {
    print_header "Installing kubectl Argo Rollouts plugin"
    
    # Check if plugin is already installed
    if kubectl argo rollouts version &> /dev/null; then
        print_success "kubectl plugin already installed"
        return
    fi
    
    # Determine OS and architecture
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    case $ARCH in
        x86_64)
            ARCH="amd64"
            ;;
        aarch64|arm64)
            ARCH="arm64"
            ;;
        *)
            print_error "Unsupported architecture: $ARCH"
            exit 1
            ;;
    esac
    
    # Download and install plugin
    print_info "Downloading kubectl plugin for $OS-$ARCH"
    curl -LO "https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-$OS-$ARCH"
    
    # Make executable
    chmod +x "kubectl-argo-rollouts-$OS-$ARCH"
    
    # Move to PATH
    sudo mv "kubectl-argo-rollouts-$OS-$ARCH" "/usr/local/bin/kubectl-argo-rollouts"
    
    # Verify installation
    if kubectl argo rollouts version &> /dev/null; then
        print_success "kubectl plugin installed successfully"
        kubectl argo rollouts version
    else
        print_error "kubectl plugin installation failed"
        exit 1
    fi
}

setup_k8sgpt_qwen() {
    print_header "Setting up K8sGPT with Qwen"
    
    # Create namespace for K8sGPT
    print_info "Creating namespace: $K8SGPT_NAMESPACE"
    kubectl create namespace "$K8SGPT_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Check if Qwen server is available
    if ! kubectl get service qwen-server -n "$K8SGPT_NAMESPACE" &> /dev/null; then
        print_warning "Qwen server not found. Setting up basic Qwen configuration..."
        
        # Create basic Qwen configuration
        cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: qwen-config
  namespace: $K8SGPT_NAMESPACE
data:
  model: "$QWEN_MODEL"
  base_url: "http://qwen-server:8000"
  temperature: "0.7"
  max_tokens: "4096"
EOF
        
        print_info "Qwen configuration created. Please ensure Qwen server is running."
    else
        print_success "Qwen server found"
    fi
    
    # Create Qwen API secret (placeholder - user should update)
    if ! kubectl get secret qwen-secret -n "$K8SGPT_NAMESPACE" &> /dev/null; then
        print_info "Creating Qwen API secret (please update with actual API key)"
        kubectl create secret generic qwen-secret \
            --from-literal=api-key="your-qwen-api-key-here" \
            --namespace="$K8SGPT_NAMESPACE" \
            --dry-run=client -o yaml | kubectl apply -f -
    fi
    
    # Deploy K8sGPT analyzer
    print_info "Deploying K8sGPT analyzer"
    kubectl apply -f overlay/k8sgpt/ -n "$K8SGPT_NAMESPACE"
    
    # Wait for K8sGPT to be ready
    print_info "Waiting for K8sGPT analyzer to be ready"
    kubectl wait --for=condition=available deployment/k8sgpt-analyzer -n "$K8SGPT_NAMESPACE" --timeout=300s
    
    print_success "K8sGPT analyzer deployed"
}

create_examples() {
    print_header "Creating Example Rollouts"
    
    # Create example namespace
    kubectl create namespace examples --dry-run=client -o yaml | kubectl apply -f -
    
    # Create basic rollout example
    print_info "Creating basic rollout example"
    cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: example-rollout
  namespace: examples
  labels:
    app: example-rollout
spec:
  replicas: 3
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 5m}
      - setWeight: 40
      - pause: {duration: 5m}
      - setWeight: 60
      - pause: {duration: 5m}
      - setWeight: 80
      - pause: {duration: 5m}
      canaryService: example-rollout-canary
      stableService: example-rollout-stable
  selector:
    matchLabels:
      app: example-rollout
  template:
    metadata:
      labels:
        app: example-rollout
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 100m
            memory: 128Mi
---
apiVersion: v1
kind: Service
metadata:
  name: example-rollout-stable
  namespace: examples
spec:
  selector:
    app: example-rollout
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: example-rollout-canary
  namespace: examples
spec:
  selector:
    app: example-rollout
  ports:
  - port: 80
    targetPort: 80
EOF
    
    # Create analysis template example
    print_info "Creating analysis template example"
    cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
  namespace: examples
spec:
  args:
  - name: service-name
  metrics:
  - name: success-rate
    interval: 30s
    count: 5
    successCondition: result[0] >= 0.95
    failureLimit: 3
    provider:
      job:
        spec:
          template:
            spec:
              containers:
              - name: success-rate-checker
                image: alpine:3.18
                command:
                - /bin/sh
                - -c
                - |
                  echo "0.98"  # Mock success rate for demo
                resources:
                  requests:
                    cpu: 10m
                    memory: 32Mi
                  limits:
                    cpu: 50m
                    memory: 64Mi
              restartPolicy: Never
EOF
    
    # Create K8sGPT analysis template
    print_info "Creating K8sGPT analysis template"
    cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: k8sgpt-health-check
  namespace: examples
spec:
  args:
  - name: namespace
    value: examples
  metrics:
  - name: k8sgpt-health-score
    interval: 60s
    count: 3
    successCondition: result[0] >= 0.8
    failureLimit: 1
    provider:
      job:
        spec:
          template:
            spec:
              containers:
              - name: k8sgpt-analyzer
                image: k8sgpt/k8sgpt:latest
                command:
                - /bin/sh
                - -c
                - |
                  k8sgpt analyze --namespace {{args.namespace}} --output json > /tmp/analysis.json
                  python3 /scripts/calculate-health-score.py /tmp/analysis.json
                env:
                - name: QWEN_API_KEY
                  valueFrom:
                    secretKeyRef:
                      name: qwen-secret
                      key: api-key
                volumeMounts:
                - name: analysis-scripts
                  mountPath: /scripts
              volumes:
              - name: analysis-scripts
                configMap:
                  name: k8sgpt-analysis-scripts
              restartPolicy: Never
EOF
    
    # Create analysis scripts configmap
    print_info "Creating K8sGPT analysis scripts"
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: k8sgpt-analysis-scripts
  namespace: examples
data:
  calculate-health-score.py: |
    #!/usr/bin/env python3
    import sys
    import json
    
    def calculate_health_score(analysis_file):
        try:
            with open(analysis_file, 'r') as f:
                analysis = json.load(f)
            
            # Calculate health score based on K8sGPT analysis
            problems = analysis.get('problems', [])
            total_resources = analysis.get('total_resources', 1)
            
            # Base score starts at 1.0
            score = 1.0
            
            # Deduct points for problems
            for problem in problems:
                severity = problem.get('severity', 'medium')
                if severity == 'critical':
                    score -= 0.3
                elif severity == 'high':
                    score -= 0.2
                elif severity == 'medium':
                    score -= 0.1
                elif severity == 'low':
                    score -= 0.05
            
            # Ensure score doesn't go below 0
            score = max(0.0, score)
            
            print(score)
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    if __name__ == "__main__":
        sys.exit(calculate_health_score(sys.argv[1]))
EOF
    
    print_success "Example rollouts created"
}

setup_monitoring() {
    print_header "Setting up Monitoring"
    
    # Create monitoring namespace if it doesn't exist
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
    
    # Create ServiceMonitor for Argo Rollouts
    print_info "Creating ServiceMonitor for Argo Rollouts"
    cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: argo-rollouts-metrics
  namespace: $NAMESPACE
  labels:
    app: argo-rollouts
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: argo-rollouts
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
EOF
    
    # Create PrometheusRule for alerting
    print_info "Creating alerting rules"
    cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: argo-rollouts-alerts
  namespace: $NAMESPACE
spec:
  groups:
  - name: argo-rollouts
    rules:
    - alert: RolloutProgressDeadlineExceeded
      expr: argo_rollouts_rollout_phase{phase="Progressing"} > 0
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "Rollout {{ \$labels.rollout }} is progressing too long"
        description: "Rollout {{ \$labels.rollout }} in namespace {{ \$labels.namespace }} has been progressing for more than 10 minutes."
    
    - alert: RolloutAnalysisFailed
      expr: argo_rollouts_analysis_result{result="failed"} > 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Rollout analysis failed for {{ \$labels.rollout }}"
        description: "Analysis template {{ \$labels.template }} failed for rollout {{ \$labels.rollout }}."
EOF
    
    print_success "Monitoring setup completed"
}

verify_installation() {
    print_header "Verifying Installation"
    
    # Check Argo Rollouts controller
    print_info "Checking Argo Rollouts controller"
    if kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=argo-rollouts | grep -q "Running"; then
        print_success "Argo Rollouts controller is running"
    else
        print_error "Argo Rollouts controller is not running"
        return 1
    fi
    
    # Check kubectl plugin
    print_info "Checking kubectl plugin"
    if kubectl argo rollouts version &> /dev/null; then
        print_success "kubectl plugin is working"
        kubectl argo rollouts version
    else
        print_error "kubectl plugin is not working"
        return 1
    fi
    
    # Check K8sGPT
    print_info "Checking K8sGPT analyzer"
    if kubectl get pods -n "$K8SGPT_NAMESPACE" -l app=k8sgpt-analyzer | grep -q "Running"; then
        print_success "K8sGPT analyzer is running"
    else
        print_warning "K8sGPT analyzer is not running (this is optional)"
    fi
    
    # Check example rollout
    print_info "Checking example rollout"
    if kubectl get rollout example-rollout -n examples &> /dev/null; then
        print_success "Example rollout created"
        kubectl argo rollouts get rollout example-rollout -n examples
    else
        print_error "Example rollout not found"
        return 1
    fi
    
    print_success "Installation verification completed"
}

show_next_steps() {
    print_header "Next Steps"
    
    echo -e "${BLUE}Congratulations! Argo Rollouts with K8sGPT Qwen integration is now installed.${NC}"
    echo
    echo -e "${YELLOW}Quick Commands:${NC}"
    echo -e "  ${BLUE}# List rollouts${NC}"
    echo -e "  kubectl argo rollouts list -n examples"
    echo
    echo -e "  ${BLUE}# Get rollout status${NC}"
    echo -e "  kubectl argo rollouts get rollout example-rollout -n examples"
    echo
    echo -e "  ${BLUE}# Trigger a new rollout${NC}"
    echo -e "  kubectl set image rollout/example-rollout nginx=nginx:1.21 -n examples"
    echo
    echo -e "  ${BLUE}# Watch rollout progress${NC}"
    echo -e "  kubectl argo rollouts get rollout example-rollout -n examples --watch"
    echo
    echo -e "  ${BLUE}# Promote a paused rollout${NC}"
    echo -e "  kubectl argo rollouts promote example-rollout -n examples"
    echo
    echo -e "  ${BLUE}# Rollback to previous version${NC}"
    echo -e "  kubectl argo rollouts undo example-rollout -n examples"
    echo
    echo -e "  ${BLUE}# Test K8sGPT analysis${NC}"
    echo -e "  kubectl exec -n $K8SGPT_NAMESPACE deployment/k8sgpt-analyzer -- k8sgpt analyze --namespace examples --explain"
    echo
    echo -e "${YELLOW}Documentation:${NC}"
    echo -e "  ${BLUE}• Comprehensive Guide:${NC} docs/ARGO-ROLLOUTS-COMPREHENSIVE-GUIDE.md"
    echo -e "  ${BLUE}• K8sGPT Integration:${NC} docs/K8SGPT-INTEGRATION-GUIDE.md"
    echo -e "  ${BLUE}• Examples:${NC} examples/argo-rollouts/"
    echo
    echo -e "${YELLOW}Configuration:${NC}"
    echo -e "  ${BLUE}• Update Qwen API key:${NC} kubectl edit secret qwen-secret -n $K8SGPT_NAMESPACE"
    echo -e "  ${BLUE}• Configure Qwen server:${NC} kubectl edit configmap qwen-config -n $K8SGPT_NAMESPACE"
    echo
    echo -e "${YELLOW}Monitoring:${NC}"
    echo -e "  ${BLUE}• Check metrics:${NC} kubectl port-forward -n $NAMESPACE svc/argo-rollouts-metrics 8090:8090"
    echo -e "  ${BLUE}• View alerts:${NC} kubectl get prometheusrules -n $NAMESPACE"
    echo
    echo -e "${GREEN}Happy rolling! 🚀${NC}"
}

# Main execution
main() {
    print_header "Argo Rollouts with K8sGPT Qwen Integration - Quickstart"
    
    check_prerequisites
    install_argo_rollouts
    install_kubectl_plugin
    setup_k8sgpt_qwen
    create_examples
    setup_monitoring
    verify_installation
    show_next_steps
}

# Handle script interruption
trap 'print_error "Script interrupted"; exit 1' INT TERM

# Run main function
main "$@"

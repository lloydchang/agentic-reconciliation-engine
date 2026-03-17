#!/bin/bash

# Qwen LLM Setup Script
# Dedicated setup script for Qwen LLM integration with Flux and K8sGPT

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default configuration
DEFAULT_MODEL="qwen2.5:7b"
DEFAULT_NAMESPACE="qwen-system"
DEFAULT_STORAGE_SIZE="10Gi"
DEFAULT_STORAGE_CLASS="standard"
DEFAULT_REPLICAS=1
DEFAULT_CPU_REQUEST="1000m"
DEFAULT_MEMORY_REQUEST="4Gi"
DEFAULT_CPU_LIMIT="2000m"
DEFAULT_MEMORY_LIMIT="8Gi"

# Script configuration
MODEL="${MODEL:-$DEFAULT_MODEL}"
NAMESPACE="${NAMESPACE:-$DEFAULT_NAMESPACE}"
STORAGE_SIZE="${STORAGE_SIZE:-$DEFAULT_STORAGE_SIZE}"
STORAGE_CLASS="${STORAGE_CLASS:-$DEFAULT_STORAGE_CLASS}"
REPLICAS="${REPLICAS:-$DEFAULT_REPLICAS}"
CPU_REQUEST="${CPU_REQUEST:-$DEFAULT_CPU_REQUEST}"
MEMORY_REQUEST="${MEMORY_REQUEST:-$DEFAULT_MEMORY_REQUEST}"
CPU_LIMIT="${CPU_LIMIT:-$DEFAULT_CPU_LIMIT}"
MEMORY_LIMIT="${MEMORY_LIMIT:-$DEFAULT_MEMORY_LIMIT}"
DRY_RUN="${DRY_RUN:-false}"
AUTO_APPROVE="${AUTO_APPROVE:-false}"

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

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Show banner
show_banner() {
    echo -e "${CYAN}"
    echo "=================================================="
    echo "      Qwen LLM Setup for Flux Integration"
    echo "=================================================="
    echo -e "${NC}"
    echo "This script will set up Qwen LLM for intelligent"
    echo "Kubernetes operations with K8sGPT and Flux."
    echo ""
}

# Show help
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

OPTIONS:
    --model MODEL              Qwen model to use [default: qwen2.5:7b]
    --namespace NAMESPACE      Kubernetes namespace [default: qwen-system]
    --storage-size SIZE        Storage size for model [default: 10Gi]
    --storage-class CLASS     Storage class [default: standard]
    --replicas COUNT          Number of replicas [default: 1]
    --cpu-request CPU         CPU request [default: 1000m]
    --memory-request MEMORY   Memory request [default: 4Gi]
    --cpu-limit CPU           CPU limit [default: 2000m]
    --memory-limit MEMORY     Memory limit [default: 8Gi]
    --dry-run                 Show what would be done without executing
    --auto-approve            Auto-approve all prompts
    --help                    Show this help message

EXAMPLES:
    $0 --model qwen2.5:7b --replicas 2 --storage-size 20Gi
    $0 --namespace qwen-prod --cpu-limit 4000m --memory-limit 16Gi
    $0 --dry-run --auto-approve

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --model)
                MODEL="$2"
                shift 2
                ;;
            --namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            --storage-size)
                STORAGE_SIZE="$2"
                shift 2
                ;;
            --storage-class)
                STORAGE_CLASS="$2"
                shift 2
                ;;
            --replicas)
                REPLICAS="$2"
                shift 2
                ;;
            --cpu-request)
                CPU_REQUEST="$2"
                shift 2
                ;;
            --memory-request)
                MEMORY_REQUEST="$2"
                shift 2
                ;;
            --cpu-limit)
                CPU_LIMIT="$2"
                shift 2
                ;;
            --memory-limit)
                MEMORY_LIMIT="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN="$2"
                shift 2
                ;;
            --auto-approve)
                AUTO_APPROVE="$2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check for required tools
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    if ! command -v curl &> /dev/null; then
        missing_tools+=("curl")
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install the missing tools and try again."
        exit 1
    fi
    
    # Check Kubernetes connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check cluster permissions
    if ! kubectl auth can-i create namespaces &> /dev/null; then
        log_error "Insufficient permissions to create namespaces"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create namespace
create_namespace() {
    log_step "Creating Qwen namespace..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create namespace: $NAMESPACE"
        return
    fi
    
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: $NAMESPACE
  labels:
    app.kubernetes.io/name: qwen-system
    app.kubernetes.io/component: ai-llm
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
EOF
    
    log_success "Namespace $NAMESPACE created"
}

# Create storage
create_storage() {
    log_step "Creating storage for Qwen model..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create PVC: qwen-model-pvc ($STORAGE_SIZE)"
        return
    fi
    
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: qwen-model-pvc
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: qwen-llm
    app.kubernetes.io/component: storage
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: $STORAGE_SIZE
  storageClassName: $STORAGE_CLASS
EOF
    
    log_success "Storage created: $STORAGE_SIZE"
}

# Create Qwen configuration
create_qwen_config() {
    log_step "Creating Qwen configuration..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create Qwen configmap"
        return
    fi
    
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: qwen-config
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: qwen-llm
    app.kubernetes.io/component: config
data:
  config.yaml: |
    model:
      name: "$MODEL"
      path: "/models/qwen2.5-7b-instruct.gguf"
      context_size: 8192
      gpu_layers: 0
      temperature: 0.7
      top_p: 0.9
      max_tokens: 2048
      batch_size: 512
    
    server:
      host: "0.0.0.0"
      port: 8000
      workers: 1
      timeout: 30
      max_connections: 100
    
    logging:
      level: "info"
      format: "json"
    
    monitoring:
      enabled: true
      port: 9090
      path: "/metrics"
    
    cache:
      enabled: true
      size: "1GB"
      ttl: "1h"
EOF
    
    log_success "Qwen configuration created"
}

# Create Qwen deployment
create_qwen_deployment() {
    log_step "Creating Qwen deployment..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create Qwen deployment with $REPLICAS replicas"
        return
    fi
    
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qwen-llm
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: qwen-llm
    app.kubernetes.io/component: ai-llm
    app.kubernetes.io/version: v1.0.0
spec:
  replicas: $REPLICAS
  selector:
    matchLabels:
      app.kubernetes.io/name: qwen-llm
      app.kubernetes.io/component: ai-llm
  template:
    metadata:
      labels:
        app.kubernetes.io/name: qwen-llm
        app.kubernetes.io/component: ai-llm
        app.kubernetes.io/version: v1.0.0
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: qwen
        image: ghcr.io/your-org/qwen-llm:v2.5-7b
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP
        - name: metrics
          containerPort: 9090
          protocol: TCP
        env:
        - name: MODEL_PATH
          value: "/models/qwen2.5-7b-instruct.gguf"
        - name: HOST
          value: "0.0.0.0"
        - name: PORT
          value: "8000"
        - name: METRICS_PORT
          value: "9090"
        - name: TEMPERATURE
          value: "0.7"
        - name: MAX_TOKENS
          value: "2048"
        - name: LOG_LEVEL
          value: "info"
        resources:
          requests:
            cpu: $CPU_REQUEST
            memory: $MEMORY_REQUEST
          limits:
            cpu: $CPU_LIMIT
            memory: $MEMORY_LIMIT
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        startupProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 30
        volumeMounts:
        - name: model-volume
          mountPath: /models
          readOnly: true
        - name: tmp-volume
          mountPath: /tmp
        - name: config-volume
          mountPath: /app/config
          readOnly: true
      volumes:
      - name: model-volume
        persistentVolumeClaim:
          claimName: qwen-model-pvc
      - name: tmp-volume
        emptyDir: {}
      - name: config-volume
        configMap:
          name: qwen-config
      terminationGracePeriodSeconds: 60
EOF
    
    log_success "Qwen deployment created"
}

# Create Qwen service
create_qwen_service() {
    log_step "Creating Qwen service..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create Qwen service"
        return
    fi
    
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: qwen-llm
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: qwen-llm
    app.kubernetes.io/component: ai-llm
spec:
  type: ClusterIP
  ports:
  - name: http
    port: 8000
    targetPort: 8000
    protocol: TCP
  - name: metrics
    port: 9090
    targetPort: 9090
    protocol: TCP
  selector:
    app.kubernetes.io/name: qwen-llm
    app.kubernetes.io/component: ai-llm
---
apiVersion: v1
kind: Service
metadata:
  name: qwen-llm-metrics
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: qwen-llm
    app.kubernetes.io/component: metrics
spec:
  type: ClusterIP
  ports:
  - name: metrics
    port: 9090
    targetPort: 9090
    protocol: TCP
  selector:
    app.kubernetes.io/name: qwen-llm
    app.kubernetes.io/component: ai-llm
EOF
    
    log_success "Qwen service created"
}

# Download Qwen model
download_qwen_model() {
    log_step "Downloading Qwen model..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would download Qwen model"
        return
    fi
    
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: qwen-model-downloader
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: qwen-llm
    app.kubernetes.io/component: setup
spec:
  template:
    spec:
      restartPolicy: OnFailure
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
      containers:
      - name: downloader
        image: curlimages/curl:latest
        command:
        - /bin/sh
        - -c
        - |
          echo "Downloading Qwen 2.5 7B model..."
          curl -L -o /models/qwen2.5-7b-instruct.gguf \\
            "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct.q4_0.gguf"
          echo "Model download completed"
          ls -la /models/
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: model-volume
          mountPath: /models
        - name: tmp-volume
          mountPath: /tmp
      volumes:
      - name: model-volume
        persistentVolumeClaim:
          claimName: qwen-model-pvc
      - name: tmp-volume
        emptyDir: {}
EOF
    
    log_success "Model download job created"
}

# Create network policies
create_network_policies() {
    log_step "Creating network policies..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create network policies"
        return
    fi
    
    cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: qwen-system-netpol
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: qwen-system
    app.kubernetes.io/component: security
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  # Allow Flux system to access Qwen
  - from:
    - namespaceSelector:
        matchLabels:
          name: flux-system
    ports:
    - protocol: TCP
      port: 8000
  # Allow monitoring from monitoring namespace
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 9090
  # Allow intra-namespace communication
  - from:
    - podSelector: {}
  egress:
  # Allow DNS
  - to: []
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
  # Allow HTTPS for model downloads
  - to: []
    ports:
    - protocol: TCP
      port: 443
  # Allow intra-namespace communication
  - to:
    - podSelector: {}
EOF
    
    log_success "Network policies created"
}

# Create monitoring
create_monitoring() {
    log_step "Creating monitoring for Qwen..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create monitoring"
        return
    fi
    
    cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: qwen-llm
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: qwen-llm
    app.kubernetes.io/component: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: qwen-llm
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: qwen-llm
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/name: qwen-llm
    app.kubernetes.io/component: monitoring
spec:
  groups:
  - name: qwen-llm
    rules:
    - alert: QwenHighMemoryUsage
      expr: container_memory_usage_bytes{pod=~"qwen-llm-.*"} / container_spec_memory_limit_bytes > 0.9
      for: 5m
      labels:
        severity: warning
        service: qwen-llm
      annotations:
        summary: "Qwen LLM high memory usage"
        description: "Qwen LLM pod {{ \$labels.pod }} is using more than 90% of its memory limit"
    - alert: QwenDown
      expr: up{job="qwen-llm"} == 0
      for: 2m
      labels:
        severity: critical
        service: qwen-llm
      annotations:
        summary: "Qwen LLM service is down"
        description: "Qwen LLM service has been down for more than 2 minutes"
EOF
    
    log_success "Monitoring created"
}

# Wait for deployment
wait_for_deployment() {
    log_step "Waiting for Qwen deployment to be ready..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would wait for deployment"
        return
    fi
    
    if kubectl wait --for=condition=available deployment/qwen-llm -n "$NAMESPACE" --timeout=600s; then
        log_success "Qwen deployment is ready"
    else
        log_error "Qwen deployment failed to become ready"
        return 1
    fi
}

# Test Qwen API
test_qwen_api() {
    log_step "Testing Qwen API..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would test Qwen API"
        return
    fi
    
    # Setup port-forward
    if kubectl port-forward -n "$NAMESPACE" svc/qwen-llm 8000:8000 &> /dev/null & then
        sleep 5
        
        # Test health endpoint
        if curl -s --max-time 10 http://localhost:8000/health | grep -q "healthy\|ok\|ready"; then
            log_success "Qwen API health check passed"
        else
            log_warning "Qwen API health check failed"
        fi
        
        # Test chat endpoint
        local response=$(curl -s --max-time 30 -X POST \
            -H "Content-Type: application/json" \
            -d '{"prompt": "Hello, respond with just OK"}' \
            http://localhost:8000/chat || echo "")
        
        if echo "$response" | grep -q "OK\|ok"; then
            log_success "Qwen API chat test passed"
        else
            log_warning "Qwen API chat test failed"
        fi
        
        pkill -f "kubectl port-forward" || true
    else
        log_error "Cannot establish port-forward to test API"
    fi
}

# Setup K8sGPT integration
setup_k8sgpt_integration() {
    log_step "Setting up K8sGPT integration..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would setup K8sGPT integration"
        return
    fi
    
    # Create secret for K8sGPT connection
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: qwen-connection-secret
  namespace: flux-system
  labels:
    app.kubernetes.io/name: qwen-integration
    app.kubernetes.io/component: ai-llm
type: Opaque
stringData:
  model: "$MODEL"
  apiUrl: "http://qwen-llm.$NAMESPACE.svc.cluster.local:8000"
  apiKey: ""
  temperature: "0.7"
  maxTokens: "2048"
  systemPrompt: |
    You are an expert Kubernetes engineer. Analyze the provided Kubernetes resources
    and identify potential issues, security vulnerabilities, or optimization opportunities.
    Provide specific, actionable recommendations with YAML examples when applicable.
    Focus on production readiness and best practices.
EOF
    
    log_success "K8sGPT integration secret created"
}

# Show usage instructions
show_usage() {
    log_step "Usage Instructions"
    echo ""
    echo "Qwen LLM has been successfully set up!"
    echo ""
    echo "To test the Qwen API:"
    echo "kubectl port-forward svc/qwen-llm 8000:8000 -n $NAMESPACE"
    echo "curl -X POST -H 'Content-Type: application/json' \\"
    echo "  -d '{\"prompt\": \"Hello!\"}' \\"
    echo "  http://localhost:8000/chat"
    echo ""
    echo "To check logs:"
    echo "kubectl logs -n $NAMESPACE deployment/qwen-llm"
    echo ""
    echo "To check metrics:"
    echo "kubectl port-forward svc/qwen-llm-metrics 9090:9090 -n $NAMESPACE"
    echo "curl http://localhost:9090/metrics"
    echo ""
    echo "To scale the deployment:"
    echo "kubectl scale deployment qwen-llm -n $NAMESPACE --replicas=3"
    echo ""
    echo "Configuration:"
    echo "• Model: $MODEL"
    echo "• Namespace: $NAMESPACE"
    echo "• Replicas: $REPLICAS"
    echo "• CPU: $CPU_REQUEST/$CPU_LIMIT"
    echo "• Memory: $MEMORY_REQUEST/$MEMORY_LIMIT"
    echo "• Storage: $STORAGE_SIZE"
    echo ""
}

# Main execution
main() {
    show_banner
    
    # Parse arguments
    parse_args "$@"
    
    # Show configuration
    log_info "Configuration:"
    log_info "  Model: $MODEL"
    log_info "  Namespace: $NAMESPACE"
    log_info "  Storage: $STORAGE_SIZE ($STORAGE_CLASS)"
    log_info "  Replicas: $REPLICAS"
    log_info "  CPU: $CPU_REQUEST/$CPU_LIMIT"
    log_info "  Memory: $MEMORY_REQUEST/$MEMORY_LIMIT"
    log_info "  Dry Run: $DRY_RUN"
    echo ""
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "Running in dry-run mode - no changes will be made"
        echo ""
    fi
    
    # Confirmation prompt
    if [[ "$AUTO_APPROVE" != "true" && "$DRY_RUN" != "true" ]]; then
        echo -e "${YELLOW}This will set up Qwen LLM with the above configuration.${NC}"
        read -p "Do you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Setup cancelled by user"
            exit 0
        fi
    fi
    
    # Execute setup steps
    check_prerequisites
    create_namespace
    create_storage
    create_qwen_config
    create_qwen_deployment
    create_qwen_service
    download_qwen_model
    create_network_policies
    create_monitoring
    wait_for_deployment
    test_qwen_api
    setup_k8sgpt_integration
    show_usage
    
    log_success "Qwen LLM setup completed! 🎉"
}

# Run main function
main "$@"

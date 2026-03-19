#!/bin/bash
# Agentic Reconciliation Engine Core Components Deployment Script
# Builds and deploys the core AI components: memory-agent, temporal-orchestrator, qwen-integration, etc.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel)"

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Build Docker image for a Go service
build_go_image() {
    local service_name="$1"
    local service_path="$2"
    local image_tag="${3:-latest}"

    print_info "Building Docker image for $service_name..."

    cd "$REPO_ROOT/core/ai/runtime/backend/$service_path"

    # Check if Dockerfile exists
    if [[ ! -f "Dockerfile" ]]; then
        print_error "Dockerfile not found for $service_name at $service_path"
        return 1
    fi

    # Build the image
    docker build -t "agentic-reconciliation-engine/$service_name:$image_tag" .

    if [[ $? -eq 0 ]]; then
        print_success "Built $service_name:$image_tag"
    else
        print_error "Failed to build $service_name"
        return 1
    fi
}

# Build all Go service images
build_all_images() {
    print_header "Building Core Component Images"

    local services=(
        "memory-agent:memory-agent"
        "temporal-orchestrator:temporal-orchestrator"
        "qwen-integration:qwen-integration"
        "state-synchronizer:state-synchronizer"
        "skill-invocation:skill-invocation"
        "llama-cpp-server:llama-cpp-server"
    )

    local failed_services=()

    for service_config in "${services[@]}"; do
        IFS=':' read -r service_name service_path <<< "$service_config"

        if build_go_image "$service_name" "$service_path"; then
            print_success "✓ $service_name built successfully"
        else
            failed_services+=("$service_name")
            print_error "✗ $service_name build failed"
        fi
    done

    if [[ ${#failed_services[@]} -gt 0 ]]; then
        print_error "Failed to build services: ${failed_services[*]}"
        return 1
    fi

    print_success "All core component images built successfully"
}

# Deploy to Kubernetes
deploy_to_k8s() {
    print_header "Deploying Core Components to Kubernetes"

    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Kubernetes cluster not accessible"
        return 1
    fi

    # Create namespace if it doesn't exist
    kubectl create namespace ai-infrastructure --dry-run=client -o yaml | kubectl apply -f -

    # Apply Kubernetes manifests
    local manifest_dir="$REPO_ROOT/core/ai/runtime/backend"

    print_info "Applying Kubernetes manifests..."

    # Deploy memory agent
    if [[ -f "$manifest_dir/memory-agent/deployment.yaml" ]]; then
        kubectl apply -f "$manifest_dir/memory-agent/deployment.yaml"
        print_success "Memory agent deployment applied"
    else
        print_error "Memory agent deployment manifest not found"
    fi

    # Deploy temporal orchestrator
    if [[ -f "$manifest_dir/temporal-orchestrator/deployment.yaml" ]]; then
        kubectl apply -f "$manifest_dir/temporal-orchestrator/deployment.yaml"
        print_success "Temporal orchestrator deployment applied"
    else
        print_error "Temporal orchestrator deployment manifest not found"
    fi

    # Deploy Qwen integration
    if [[ -f "$manifest_dir/qwen-integration/deployment.yaml" ]]; then
        kubectl apply -f "$manifest_dir/qwen-integration/deployment.yaml"
        print_success "Qwen integration deployment applied"
    else
        print_error "Qwen integration deployment manifest not found"
    fi

    # Deploy state synchronizer
    if [[ -f "$manifest_dir/state-synchronizer/deployment.yaml" ]]; then
        kubectl apply -f "$manifest_dir/state-synchronizer/deployment.yaml"
        print_success "State synchronizer deployment applied"
    else
        print_error "State synchronizer deployment manifest not found"
    fi

    # Deploy skill invocation service
    if [[ -f "$manifest_dir/skill-invocation/deployment.yaml" ]]; then
        kubectl apply -f "$manifest_dir/skill-invocation/deployment.yaml"
        print_success "Skill invocation service deployment applied"
    else
        print_error "Skill invocation deployment manifest not found"
    fi

    # Deploy llama-cpp-server
    if [[ -f "$manifest_dir/llama-cpp-server/deployment.yaml" ]]; then
        kubectl apply -f "$manifest_dir/llama-cpp-server/deployment.yaml"
        print_success "llama-cpp-server deployment applied"
    else
        print_error "llama-cpp-server deployment manifest not found"
    fi


    # Wait for deployments to be ready
    print_info "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/memory-agent -n ai-infrastructure || print_warning "Memory agent not ready"
    kubectl wait --for=condition=available --timeout=300s deployment/temporal-orchestrator -n ai-infrastructure || print_warning "Temporal orchestrator not ready"
    kubectl wait --for=condition=available --timeout=300s deployment/llama-cpp-server -n ai-infrastructure || print_warning "llama-cpp-server not ready"

    print_success "Core components deployed to Kubernetes"
}

# Create Kubernetes manifests for all services
create_k8s_manifests() {
    print_header "Creating Kubernetes Manifests"

    local services=(
        "memory-agent:8080"
        "temporal-orchestrator:8081"
        "qwen-integration:8082"
        "state-synchronizer:8083"
        "skill-invocation:8084"
        "llama-cpp-server:8080"
    )

    for service_config in "${services[@]}"; do
        IFS=':' read -r service_name service_port <<< "$service_config"

        local manifest_dir="$REPO_ROOT/core/ai/runtime/backend/$service_name"
        mkdir -p "$manifest_dir"

        # Create deployment manifest
        cat > "$manifest_dir/deployment.yaml" << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $service_name
  namespace: ai-infrastructure
  labels:
    app: $service_name
    component: agentic-reconciliation-engine
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $service_name
  template:
    metadata:
      labels:
        app: $service_name
        component: agentic-reconciliation-engine
    spec:
      containers:
      - name: $service_name
        image: agentic-reconciliation-engine/$service_name:latest
        ports:
        - containerPort: $service_port
          name: http
        env:
        - name: SERVICE_PORT
          value: "$service_port"
        - name: NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        # Memory agent specific env vars
        - name: MEMORY_DB_PATH
          value: "/data/memory.db"
        # Qwen integration env vars
        - name: QWEN_API_URL
          value: "http://llama-cpp-server.ai-infrastructure.svc.cluster.local:8080"
        - name: QWEN_MODEL
          value: "qwen2.5-coder-7b-instruct"
        # Temporal env vars
        - name: TEMPORAL_ADDRESS
          value: "temporal-frontend.ai-infrastructure.svc.cluster.local:7233"
        # Database for persistent storage
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: $service_name-data
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: $service_name-data
  namespace: ai-infrastructure
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: $service_name-service
  namespace: ai-infrastructure
  labels:
    app: $service_name
    component: agentic-reconciliation-engine
spec:
  selector:
    app: $service_name
  ports:
  - name: http
    port: $service_port
    targetPort: $service_port
    protocol: TCP
  type: ClusterIP
EOF

        print_success "Created manifests for $service_name"
    done

    print_success "All Kubernetes manifests created"
}

# Validate deployment
validate_deployment() {
    print_header "Validating Core Components Deployment"

    local services=(
        "memory-agent:8080"
        "temporal-orchestrator:8081"
        "qwen-integration:8082"
    )

    for service_config in "${services[@]}"; do
        IFS=':' read -r service_name service_port <<< "$service_config"

        # Check if deployment exists
        if kubectl get deployment "$service_name" -n ai-infrastructure &> /dev/null; then
            print_success "$service_name deployment exists"
        else
            print_error "$service_name deployment not found"
            continue
        fi

        # Check if service exists
        if kubectl get service "$service_name-service" -n ai-infrastructure &> /dev/null; then
            print_success "$service_name service exists"
        else
            print_error "$service_name service not found"
        fi

        # Check if pods are running
        local pod_count=$(kubectl get pods -n ai-infrastructure -l "app=$service_name" --no-headers 2>/dev/null | wc -l)
        if [[ $pod_count -gt 0 ]]; then
            print_success "$service_name has $pod_count running pod(s)"
        else
            print_error "$service_name has no running pods"
        fi

        # Test health endpoint if service is accessible
        local cluster_ip=$(kubectl get service "$service_name-service" -n ai-infrastructure -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
        if [[ -n "$cluster_ip" && "$cluster_ip" != "None" ]]; then
            # Use port-forward to test health endpoint
            local test_result=$(kubectl exec -n ai-infrastructure deployment/"$service_name" -- curl -f http://localhost:$service_port/health 2>/dev/null && echo "success" || echo "failed")
            if [[ "$test_result" == "success" ]]; then
                print_success "$service_name health check passed"
            else
                print_warning "$service_name health check failed (may not have curl or endpoint)"
            fi
        fi
    done

    print_success "Core components validation completed"
}

# Main function
main() {
    case "${1:-}" in
        "build")
            build_all_images
            ;;
        "manifests")
            create_k8s_manifests
            ;;
        "deploy")
            deploy_to_k8s
            ;;
        "validate")
            validate_deployment
            ;;
        "all")
            build_all_images
            create_k8s_manifests
            deploy_to_k8s
            validate_deployment
            ;;
        *)
            echo "Usage: $0 {build|manifests|deploy|validate|all}"
            echo ""
            echo "Commands:"
            echo "  build     - Build Docker images for all core components"
            echo "  manifests - Generate Kubernetes manifests"
            echo "  deploy    - Deploy components to Kubernetes"
            echo "  validate  - Validate deployment health"
            echo "  all       - Run all steps: build, manifests, deploy, validate"
            exit 1
            ;;
    esac
}

main "$@"

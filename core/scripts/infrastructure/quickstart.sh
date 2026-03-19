#!/bin/bash

# Quickstart Script for Agentic Reconciliation Engine
# Sets up the complete development environment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
SKIP_DEPS=false
SKIP_BUILD=false
SKIP_CLUSTER=false
BOOTSTRAP_CLUSTER_NAME="gitops-bootstrap"
KIND_CONFIG_FILE=""
VERBOSE=false

# Help function
show_help() {
    cat << EOF
Agentic Reconciliation Engine Quickstart

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --skip-deps           Skip dependency installation
    --skip-build          Skip Docker image building
    --skip-cluster        Skip Kind cluster creation
    --bootstrap-name <name>  Bootstrap cluster name (default: gitops-bootstrap)
    --kind-config <file>  Kind cluster configuration file
    -v, --verbose         Enable verbose output
    -h, --help           Show this help message

EXAMPLES:
    $0                                    # Full setup
    $0 --skip-deps --skip-build          # Skip dependencies and build
    $0 --bootstrap-name my-cluster       # Custom cluster name
    $0 --kind-config custom-config.yaml  # Custom Kind config

DESCRIPTION:
    This script sets up the complete Agentic Reconciliation Engine
    including dependencies, Docker images, and Kind clusters.

EOF
}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

log_debug() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${CYAN}[DEBUG]${NC} $1"
    fi
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-deps)
                SKIP_DEPS=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-cluster)
                SKIP_CLUSTER=true
                shift
                ;;
            --bootstrap-name)
                BOOTSTRAP_CLUSTER_NAME="$2"
                shift 2
                ;;
            --kind-config)
                KIND_CONFIG_FILE="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
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

# Check if running on supported platform
check_platform() {
    local os=$(uname -s)
    local arch=$(uname -m)
    
    case "$os" in
        Darwin|Linux)
            log_debug "Supported OS: $os"
            ;;
        *)
            log_error "Unsupported OS: $os"
            exit 1
            ;;
    esac
    
    case "$arch" in
        x86_64|arm64)
            log_debug "Supported architecture: $arch"
            ;;
        *)
            log_error "Unsupported architecture: $arch"
            exit 1
            ;;
    esac
}

# Install dependencies
install_dependencies() {
    if [[ "$SKIP_DEPS" == "true" ]]; then
        log_info "Skipping dependency installation"
        return 0
    fi
    
    log_step "Installing dependencies..."
    
    # Check for Homebrew on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if ! command -v brew &> /dev/null; then
            log_info "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        # Install required tools
        local tools=("kubectl" "kind" "docker" "git" "make" "jq" "yq")
        for tool in "${tools[@]}"; do
            if ! command -v "$tool" &> /dev/null; then
                log_info "Installing $tool..."
                brew install "$tool"
            else
                log_debug "$tool already installed"
            fi
        done
    else
        # Linux installation
        log_info "Installing dependencies for Linux..."
        
        # Install kubectl
        if ! command -v kubectl &> /dev/null; then
            log_info "Installing kubectl..."
            curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
            sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
            rm kubectl
        fi
        
        # Install kind
        if ! command -v kind &> /dev/null; then
            log_info "Installing kind..."
            curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
            chmod +x ./kind
            sudo mv ./kind /usr/local/bin/kind
        fi
        
        # Install other tools
        local tools=("docker.io" "git" "make" "jq" "yq")
        for tool in "${tools[@]}"; do
            if ! command -v "$tool" &> /dev/null; then
                log_info "Installing $tool..."
                sudo apt-get update && sudo apt-get install -y "$tool"
            fi
        done
    fi
    
    log_success "Dependencies installed"
}

# Check Docker daemon
check_docker() {
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "Docker daemon is running"
}

# Create Kind cluster
create_kind_cluster() {
    if [[ "$SKIP_CLUSTER" == "true" ]]; then
        log_info "Skipping Kind cluster creation"
        return 0
    fi
    
    log_step "Creating Kind cluster: $BOOTSTRAP_CLUSTER_NAME"
    
    # Check if cluster already exists
    if kind get clusters | grep -q "^$BOOTSTRAP_CLUSTER_NAME$"; then
        log_warn "Cluster $BOOTSTRAP_CLUSTER_NAME already exists"
        read -p "Do you want to delete and recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Deleting existing cluster..."
            kind delete cluster --name "$BOOTSTRAP_CLUSTER_NAME"
        else
            log_info "Using existing cluster"
            return 0
        fi
    fi
    
    # Create Kind config if not provided
    local config_file="$KIND_CONFIG_FILE"
    if [[ -z "$config_file" ]]; then
        config_file="/tmp/${BOOTSTRAP_CLUSTER_NAME}-kind-config.yaml"
        cat > "$config_file" << EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: $BOOTSTRAP_CLUSTER_NAME
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
- role: worker
EOF
    fi
    
    log_debug "Using Kind config: $config_file"
    
    # Create cluster
    kind create cluster --config "$config_file" --name "$BOOTSTRAP_CLUSTER_NAME" --wait 300s
    
    # Verify cluster
    if kubectl cluster-info --context "kind-$BOOTSTRAP_CLUSTER_NAME" &> /dev/null; then
        log_success "Kind cluster created successfully"
    else
        log_error "Failed to create Kind cluster"
        exit 1
    fi
}

# Build Docker images
build_docker_images() {
    if [[ "$SKIP_BUILD" == "true" ]]; then
        log_info "Skipping Docker image building"
        return 0
    fi
    
    log_step "Building Docker images..."
    
    # Load images into Kind cluster
    local images=(
        "ai-agent-evaluator"
        "temporal-worker"
        "ai-dashboard"
    )
    
    for image in "${images[@]}"; do
        log_info "Building image: $image"
        
        # Build the image (assuming Dockerfile exists)
        if [[ -f "Dockerfile" ]] || [[ -f "core/deployment/${image}-Dockerfile" ]]; then
            local dockerfile="Dockerfile"
            if [[ ! -f "$dockerfile" ]]; then
                dockerfile="core/deployment/${image}-Dockerfile"
            fi
            
            docker build -f "$dockerfile" -t "$image:latest" . || {
                log_warn "Failed to build $image, continuing..."
                continue
            }
            
            # Load into Kind cluster
            kind load docker-image "$image:latest" --name "$BOOTSTRAP_CLUSTER_NAME"
            log_success "Built and loaded $image:latest"
        else
            log_warn "Dockerfile not found for $image, skipping..."
        fi
    done
}

# Deploy GitOps components
deploy_gitops() {
    log_step "Deploying GitOps components..."
    
    # Apply CRDs
    if [[ -d "core/gitops/crds" ]]; then
        log_info "Applying CRDs..."
        kubectl apply -f core/gitops/crds/ --context "kind-$BOOTSTRAP_CLUSTER_NAME"
    fi
    
    # Deploy Flux or ArgoCD (choose based on available manifests)
    if [[ -d "core/gitops/flux" ]]; then
        log_info "Deploying Flux..."
        kubectl apply -f core/gitops/flux/ --context "kind-$BOOTSTRAP_CLUSTER_NAME"
    elif [[ -d "core/gitops/argocd" ]]; then
        log_info "Deploying ArgoCD..."
        kubectl apply -f core/gitops/argocd/ --context "kind-$BOOTSTRAP_CLUSTER_NAME"
    fi
    
    # Wait for deployments
    log_info "Waiting for GitOps components to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment --all -n flux-system --context "kind-$BOOTSTRAP_CLUSTER_NAME" 2>/dev/null || \
    kubectl wait --for=condition=available --timeout=300s deployment --all -n argocd --context "kind-$BOOTSTRAP_CLUSTER_NAME" 2>/dev/null || \
    log_warn "GitOps components may still be starting"
}

# Setup AI agents
setup_ai_agents() {
    log_step "Setting up AI agents..."
    
    # Deploy AI agent runtime
    if [[ -f "core/deployment/ai-agent-evaluation-cronjob.yaml" ]]; then
        log_info "Deploying AI agent evaluation..."
        kubectl apply -f core/deployment/ai-agent-evaluation-cronjob.yaml --context "kind-$BOOTSTRAP_CLUSTER_NAME"
    fi
    
    # Deploy Temporal if available
    if [[ -d "core/gitops/temporal" ]]; then
        log_info "Deploying Temporal..."
        kubectl apply -f core/gitops/temporal/ --context "kind-$BOOTSTRAP_CLUSTER_NAME"
    fi
}

# Verify setup
verify_setup() {
    log_step "Verifying setup..."
    
    # Check cluster status
    log_info "Cluster status:"
    kubectl get nodes --context "kind-$BOOTSTRAP_CLUSTER_NAME"
    
    # Check pod status
    log_info "Pod status:"
    kubectl get pods --all-namespaces --context "kind-$BOOTSTRAP_CLUSTER_NAME"
    
    # Check services
    log_info "Services:"
    kubectl get svc --all-namespaces --context "kind-$BOOTSTRAP_CLUSTER_NAME"
    
    # Test connectivity
    log_info "Testing cluster connectivity..."
    if kubectl get pods --context "kind-$BOOTSTRAP_CLUSTER_NAME" &> /dev/null; then
        log_success "Cluster connectivity verified"
    else
        log_error "Cluster connectivity failed"
        exit 1
    fi
}

# Show next steps
show_next_steps() {
    log_step "Setup completed successfully!"
    
    cat << EOF

${GREEN}🎉 Agentic Reconciliation Engine is ready!${NC}

Next steps:
1. Set your kubeconfig:
   export KUBECONFIG="\$HOME/.kube/config"

2. Access the dashboard (if deployed):
   kubectl port-forward svc/ai-dashboard 8080:8080 -n default

3. Check GitOps status:
   kubectl get gitrepositories -n flux-system
   # or
   kubectl get applications -n argocd

4. Run debug tools:
   ./core/automation/scripts/debug/quick_debug.sh agents errors

5. Explore skills:
   ls core/ai/skills/

Useful commands:
- kubectl get nodes
- kubectl get pods --all-namespaces
- kind delete cluster --name $BOOTSTRAP_CLUSTER_NAME

Documentation:
- README.md
- docs/developer-guide/
- core/ai/skills/*/SKILL.md

EOF
}

# Cleanup function
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Setup failed with exit code $exit_code"
        log_info "Check the logs above for error details"
    fi
}

# Set up cleanup trap
trap cleanup EXIT

# Main function
main() {
    log_info "Starting Agentic Reconciliation Engine quickstart..."
    
    parse_args "$@"
    check_platform
    
    log_info "Configuration:"
    log_info "  Skip dependencies: $SKIP_DEPS"
    log_info "  Skip build: $SKIP_BUILD"
    log_info "  Skip cluster: $SKIP_CLUSTER"
    log_info "  Bootstrap cluster: $BOOTSTRAP_CLUSTER_NAME"
    log_info "  Kind config: ${KIND_CONFIG_FILE:-"auto-generated"}"
    
    install_dependencies
    check_docker
    create_kind_cluster
    build_docker_images
    deploy_gitops
    setup_ai_agents
    verify_setup
    show_next_steps
    
    log_success "Quickstart completed successfully!"
}

# Run main function with all arguments
main "$@"

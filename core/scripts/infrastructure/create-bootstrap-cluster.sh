#!/bin/bash

# Bootstrap Cluster Creation Script
# Creates a Kind cluster for GitOps bootstrap

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BOOTSTRAP_CLUSTER_NAME="gitops-bootstrap"
KUBERNETES_VERSION="v1.28.0"
CONFIG_FILE=""
DELETE_CLUSTER=false
DRY_RUN=false
VERBOSE=false

# Help function
show_help() {
    cat << EOF
Bootstrap Cluster Creation Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -n, --name <name>         Cluster name (default: gitops-bootstrap)
    -k, --k8s-version <ver>   Kubernetes version (default: v1.28.0)
    -c, --config <file>       Kind configuration file
    -d, --delete              Delete existing cluster
    --dry-run                 Show commands without executing
    -v, --verbose             Enable verbose output
    -h, --help                Show this help message

EXAMPLES:
    $0                                    # Create default bootstrap cluster
    $0 -n my-cluster -k v1.27.3          # Custom name and version
    $0 -c custom-config.yaml             # Custom configuration
    $0 --delete                          # Delete existing cluster

DESCRIPTION:
    This script creates a Kind cluster suitable for GitOps bootstrap
    with proper port mappings and node configurations.

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

log_debug() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--name)
                BOOTSTRAP_CLUSTER_NAME="$2"
                shift 2
                ;;
            -k|--k8s-version)
                KUBERNETES_VERSION="$2"
                shift 2
                ;;
            -c|--config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            -d|--delete)
                DELETE_CLUSTER=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
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

# Check dependencies
check_dependencies() {
    local deps=("kind" "kubectl" "docker")
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "Required dependency not found: $dep"
            exit 1
        fi
    done
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_debug "All dependencies verified"
}

# Create Kind configuration
create_kind_config() {
    local config_file="/tmp/${BOOTSTRAP_CLUSTER_NAME}-kind-config.yaml"
    
    log_debug "Creating Kind configuration: $config_file"
    
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
  - containerPort: 30000
    hostPort: 30000
    protocol: TCP
  extraMounts:
  - containerPath: /var/log/containers
    hostPath: /tmp/$BOOTSTRAP_CLUSTER_NAME-logs
    readOnly: false
- role: worker
  extraMounts:
  - containerPath: /var/log/containers
    hostPath: /tmp/$BOOTSTRAP_CLUSTER_NAME-logs
    readOnly: false
- role: worker
  extraMounts:
  - containerPath: /var/log/containers
    hostPath: /tmp/$BOOTSTRAP_CLUSTER_NAME-logs
    readOnly: false
networking:
  apiServerAddress: "127.0.0.1"
  apiServerPort: 6443
  podSubnet: "10.244.0.0/16"
  serviceSubnet: "10.96.0.0/12"
EOF

    echo "$config_file"
}

# Delete existing cluster
delete_cluster() {
    log_info "Checking for existing cluster: $BOOTSTRAP_CLUSTER_NAME"
    
    if kind get clusters | grep -q "^$BOOTSTRAP_CLUSTER_NAME$"; then
        log_info "Deleting existing cluster: $BOOTSTRAP_CLUSTER_NAME"
        
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY-RUN] kind delete cluster --name $BOOTSTRAP_CLUSTER_NAME"
        else
            kind delete cluster --name "$BOOTSTRAP_CLUSTER_NAME"
            log_success "Cluster deleted successfully"
        fi
    else
        log_info "No existing cluster found"
    fi
}

# Create cluster
create_cluster() {
    log_info "Creating Kind cluster: $BOOTSTRAP_CLUSTER_NAME"
    
    # Determine config file
    local kind_config="$CONFIG_FILE"
    if [[ -z "$kind_config" ]]; then
        kind_config=$(create_kind_config)
    fi
    
    log_debug "Using configuration: $kind_config"
    
    # Create log directory
    local log_dir="/tmp/$BOOTSTRAP_CLUSTER_NAME-logs"
    mkdir -p "$log_dir"
    
    # Build kind command
    local cmd="kind create cluster"
    cmd="$cmd --config $kind_config"
    cmd="$cmd --name $BOOTSTRAP_CLUSTER_NAME"
    cmd="$cmd --image kindest/node:$KUBERNETES_VERSION"
    cmd="$cmd --wait 300s"
    
    log_debug "Command: $cmd"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] $cmd"
        return 0
    fi
    
    # Execute command
    if eval "$cmd"; then
        log_success "Cluster created successfully"
    else
        log_error "Failed to create cluster"
        exit 1
    fi
}

# Verify cluster
verify_cluster() {
    log_info "Verifying cluster setup..."
    
    # Check cluster context
    local context="kind-$BOOTSTRAP_CLUSTER_NAME"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] kubectl cluster-info --context $context"
        log_info "[DRY-RUN] kubectl get nodes --context $context"
        return 0
    fi
    
    # Check cluster info
    if kubectl cluster-info --context "$context" &> /dev/null; then
        log_success "Cluster is accessible"
    else
        log_error "Cluster is not accessible"
        exit 1
    fi
    
    # Check nodes
    log_info "Node status:"
    kubectl get nodes --context "$context"
    
    # Check cluster health
    local ready_nodes
    ready_nodes=$(kubectl get nodes --context "$context" --no-headers | awk '{print $2}' | grep -c "Ready" || true)
    local total_nodes
    total_nodes=$(kubectl get nodes --context "$context" --no-headers | wc -l)
    
    if [[ "$ready_nodes" -eq "$total_nodes" ]]; then
        log_success "All $total_nodes nodes are ready"
    else
        log_warn "Only $ready_nodes of $total_nodes nodes are ready"
    fi
    
    # Check system pods
    log_info "System pod status:"
    kubectl get pods -n kube-system --context "$context"
}

# Setup cluster for GitOps
setup_gitops() {
    log_info "Setting up cluster for GitOps..."
    
    local context="kind-$BOOTSTRAP_CLUSTER_NAME"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Setting up GitOps prerequisites"
        return 0
    fi
    
    # Create namespaces
    local namespaces=("flux-system" "argocd" "temporal" "ai-agents")
    for ns in "${namespaces[@]}"; do
        if ! kubectl get namespace "$ns" --context "$context" &> /dev/null; then
            log_info "Creating namespace: $ns"
            kubectl create namespace "$ns" --context "$context"
        else
            log_debug "Namespace $ns already exists"
        fi
    done
    
    # Label nodes for GitOps
    log_info "Labeling nodes for GitOps..."
    kubectl label nodes --all gitops=enabled --context "$context" --overwrite
    
    # Create service accounts
    log_info "Creating service accounts..."
    kubectl apply -f - --context "$context" << EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: gitops-service-account
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: gitops-cluster-admin
subjects:
- kind: ServiceAccount
  name: gitops-service-account
  namespace: default
roleRef:
  kind: ClusterRole
  name: cluster-admin
EOF
    
    log_success "GitOps setup completed"
}

# Show cluster information
show_cluster_info() {
    log_info "Cluster Information:"
    
    local context="kind-$BOOTSTRAP_CLUSTER_NAME"
    
    echo
    echo "Cluster Name: $BOOTSTRAP_CLUSTER_NAME"
    echo "Kubernetes Version: $KUBERNETES_VERSION"
    echo "Context: $context"
    echo
    
    echo "To use this cluster:"
    echo "  export KUBECONFIG=\"\$HOME/.kube/config\""
    echo "  kubectl config use-context $context"
    echo
    
    echo "Access services:"
    echo "  kubectl get svc --all-namespaces --context $context"
    echo
    
    echo "Delete cluster:"
    echo "  kind delete cluster --name $BOOTSTRAP_CLUSTER_NAME"
    echo
    
    if [[ -f "/tmp/${BOOTSTRAP_CLUSTER_NAME}-kind-config.yaml" ]]; then
        echo "Configuration file:"
        echo "  /tmp/${BOOTSTRAP_CLUSTER_NAME}-kind-config.yaml"
        echo
    fi
}

# Main function
main() {
    log_info "Bootstrap Cluster Creation Script"
    
    parse_args "$@"
    check_dependencies
    
    log_info "Configuration:"
    log_info "  Cluster name: $BOOTSTRAP_CLUSTER_NAME"
    log_info "  Kubernetes version: $KUBERNETES_VERSION"
    log_info "  Config file: ${CONFIG_FILE:-"auto-generated"}"
    log_info "  Delete cluster: $DELETE_CLUSTER"
    log_info "  Dry run: $DRY_RUN"
    
    if [[ "$DELETE_CLUSTER" == "true" ]]; then
        delete_cluster
        exit 0
    fi
    
    create_cluster
    verify_cluster
    setup_gitops
    show_cluster_info
    
    log_success "Bootstrap cluster setup completed!"
}

# Run main function with all arguments
main "$@"

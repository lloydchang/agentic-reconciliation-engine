#!/usr/bin/env bash
# =============================================================================
# Create Bootstrap Cluster - Lightweight recovery anchor for hub cluster
# =============================================================================
set -euo pipefail

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

pass() { echo -e "  ${GREEN}✓${RESET} $*"; }
fail() { echo -e "  ${RED}✗${RESET} $*"; exit 1; }
warn() { echo -e "  ${YELLOW}!${RESET} $*"; }
info() { echo -e "  ${CYAN}→${RESET} $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/helpers/wsl-detect.sh"
ensure_wsl_sanity "create-bootstrap-cluster.sh" warn info

# Default configuration
BOOTSTRAP_CLUSTER_NAME="gitops-bootstrap"
BOOTSTRAP_KUBECONFIG="${SCRIPT_DIR}/../bootstrap-kubeconfig"
CLUSTER_TYPE="kind"  # kind, k3s, or local

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)
      BOOTSTRAP_CLUSTER_NAME="$2"
      shift 2
      ;;
    --type)
      CLUSTER_TYPE="$2"
      shift 2
      ;;
    --kubeconfig)
      BOOTSTRAP_KUBECONFIG="$2"
      shift 2
      ;;
    --help)
      cat <<EOF
Usage: $0 [options]

Create a lightweight bootstrap cluster for GitOps infrastructure recovery.

Options:
  --name <name>        Cluster name (default: gitops-bootstrap)
  --type <type>        Cluster type: kind, k3s, local (default: kind)
  --kubeconfig <path>  Kubeconfig path (default: ./bootstrap-kubeconfig)
  --help               Show this help

Examples:
  $0                           # Create kind cluster with defaults
  $0 --type k3s               # Create k3s cluster
  $0 --name my-bootstrap      # Custom cluster name
EOF
      exit 0
      ;;
    *)
      fail "Unknown option: $1. Use --help for usage."
      ;;
  esac
done

info "Creating bootstrap cluster: ${BOOTSTRAP_CLUSTER_NAME}"
info "Cluster type: ${CLUSTER_TYPE}"
info "Kubeconfig: ${BOOTSTRAP_KUBECONFIG}"

# Validate prerequisites
validate_prerequisites() {
  info "Validating prerequisites..."
  
  case "$CLUSTER_TYPE" in
    kind)
      if ! command -v kind >/dev/null 2>&1; then
        fail "kind not found. Install from https://kind.sigs.k8s.io/"
      fi
      ;;
    k3s)
      if ! command -v k3s >/dev/null 2>&1; then
        fail "k3s not found. Install from https://k3s.io/"
      fi
      ;;
    local)
      if ! command -v kubectl >/dev/null 2>&1; then
        fail "kubectl not found. Install from https://kubernetes.io/docs/tasks/tools/"
      fi
      ;;
    *)
      fail "Unsupported cluster type: $CLUSTER_TYPE. Use: kind, k3s, local"
      ;;
  esac
  
  pass "Prerequisites validated"
}

# Create cluster based on type
create_cluster() {
  info "Creating ${CLUSTER_TYPE} cluster..."
  
  case "$CLUSTER_TYPE" in
    kind)
      create_kind_cluster
      ;;
    k3s)
      create_k3s_cluster
      ;;
    local)
      use_local_cluster
      ;;
  esac
}

# Create kind cluster
create_kind_cluster() {
  info "Creating kind cluster..."
  
  # Kind config for lightweight bootstrap
  cat > /tmp/kind-config.yaml <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
    - |
      kind: InitConfiguration
      nodeRegistration:
        kubeletExtraArgs:
          node-labels: "gitops-role=bootstrap"
    extraPortMappings:
    - containerPort: 80
      hostPort: 8080
    - containerPort: 443
      hostPort: 8443
EOF

  if kind get clusters | grep -q "^${BOOTSTRAP_CLUSTER_NAME}$"; then
    warn "Cluster ${BOOTSTRAP_CLUSTER_NAME} already exists. Deleting..."
    kind delete cluster --name "${BOOTSTRAP_CLUSTER_NAME}"
  fi

  kind create cluster --name "${BOOTSTRAP_CLUSTER_NAME}" --config /tmp/kind-config.yaml
  kind get kubeconfig --name "${BOOTSTRAP_CLUSTER_NAME}" > "${BOOTSTRAP_KUBECONFIG}"
  export KUBECONFIG="${BOOTSTRAP_KUBECONFIG}"
  
  pass "Kind cluster created"
}

# Create k3s cluster
create_k3s_cluster() {
  info "Creating k3s cluster..."
  
  if k3s cluster-exists 2>/dev/null; then
    warn "k3s cluster already exists. Resetting..."
    sudo k3s server --cluster-reset || true
  fi

  # Install k3s with minimal configuration
  curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644 --disable traefik --disable servicelb --node-label gitops-role=bootstrap
  
  # Copy kubeconfig
  mkdir -p "$(dirname "${BOOTSTRAP_KUBECONFIG}")"
  cp /etc/rancher/k3s/k3s.yaml "${BOOTSTRAP_KUBECONFIG}"
  sed -i "s/127.0.0.1/$(hostname -I | awk '{print $1}')/g" "${BOOTSTRAP_KUBECONFIG}"
  export KUBECONFIG="${BOOTSTRAP_KUBECONFIG}"
  
  pass "k3s cluster created"
}

# Use existing local cluster
use_local_cluster() {
  info "Using existing local cluster..."
  
  if ! kubectl cluster-info >/dev/null 2>&1; then
    fail "No accessible local cluster found. Ensure kubectl is configured."
  fi
  
  mkdir -p "$(dirname "${BOOTSTRAP_KUBECONFIG}")"
  cp "${KUBECONFIG:-$HOME/.kube/config}" "${BOOTSTRAP_KUBECONFIG}"
  export KUBECONFIG="${BOOTSTRAP_KUBECONFIG}"
  
  # Add bootstrap label to nodes
  kubectl label nodes --all gitops-role=bootstrap --overwrite
  
  pass "Using local cluster"
}

# Install required components
install_components() {
  info "Installing bootstrap components..."
  
  # Wait for cluster to be ready
  info "Waiting for cluster to be ready..."
  kubectl wait --for=condition=Ready nodes --all --timeout=300s
  
  # Create namespace
  kubectl create namespace gitops-system --dry-run=client -o yaml | kubectl apply -f -
  
  # Install basic tools
  info "Installing kubectl tools in cluster..."
  kubectl create configmap bootstrap-scripts \
    --from-file="${SCRIPT_DIR}/../scripts/" \
    --namespace gitops-system \
    --dry-run=client -o yaml | kubectl apply -f - || true
  
  pass "Bootstrap components installed"
}

# Store bootstrap configuration
store_bootstrap_config() {
  info "Storing bootstrap configuration..."
  
  # Create bootstrap config map
  cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: bootstrap-config
  namespace: gitops-system
  labels:
    gitops-role: bootstrap
data:
  cluster-name: "${BOOTSTRAP_CLUSTER_NAME}"
  cluster-type: "${CLUSTER_TYPE}"
  created-at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  purpose: "GitOps bootstrap and recovery anchor"
EOF

  pass "Bootstrap configuration stored"
}

# Verify cluster
verify_cluster() {
  info "Verifying bootstrap cluster..."
  
  # Check node status
  if ! kubectl get nodes | grep -q "Ready"; then
    fail "Bootstrap cluster nodes are not ready"
  fi
  
  # Check namespace
  if ! kubectl get namespace gitops-system >/dev/null 2>&1; then
    fail "gitops-system namespace not found"
  fi
  
  # Check bootstrap config
  if ! kubectl get configmap bootstrap-config -n gitops-system >/dev/null 2>&1; then
    fail "Bootstrap configuration not found"
  fi
  
  pass "Bootstrap cluster verified"
}

# Show cluster info
show_cluster_info() {
  echo
  echo -e "${BOLD}Bootstrap Cluster Information${RESET}"
  echo "================================"
  echo "Cluster Name: ${BOOTSTRAP_CLUSTER_NAME}"
  echo "Cluster Type: ${CLUSTER_TYPE}"
  echo "Kubeconfig: ${BOOTSTRAP_KUBECONFIG}"
  echo "Namespace: gitops-system"
  echo
  echo "To use this cluster:"
  echo "  export KUBECONFIG=${BOOTSTRAP_KUBECONFIG}"
  echo "  kubectl get nodes -n gitops-system"
  echo
  echo "Next steps:"
  echo "  1. Run: scripts/create-hub-cluster.sh"
  echo "  2. The hub cluster will use this bootstrap for recovery"
  echo
}

# Main execution
main() {
  echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${RESET}"
  echo -e "${BOLD}║   GitOps Infra Control Plane — Bootstrap Cluster Setup      ║${RESET}"
  echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${RESET}"
  echo
  
  validate_prerequisites
  create_cluster
  install_components
  store_bootstrap_config
  verify_cluster
  show_cluster_info
  
  echo -e "${GREEN}${BOLD}Bootstrap cluster created successfully!${RESET}"
}

# Run main function
main "$@"

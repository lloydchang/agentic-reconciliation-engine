#!/usr/bin/env bash
# =============================================================================
# Create Hub Cluster - HA GitOps control plane cluster
# =============================================================================
set -euo pipefail
cd $(dirname $0)

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

pass() { echo -e "  ${GREEN}✓${RESET} $*"; }
fail() { echo -e "  ${RED}✗${RESET} $*"; exit 1; }
warn() { echo -e "  ${YELLOW}!${RESET} $*"; }
info() { echo -e "  ${CYAN}→${RESET} $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/helpers/wsl-detect.sh"
ensure_wsl_sanity "create-hub-cluster.sh" warn info

# Default configuration
HUB_CLUSTER_NAME="gitops-hub"
HUB_KUBECONFIG="${SCRIPT_DIR}/../hub-kubeconfig"
CLOUD_PROVIDER="azure"
NODE_COUNT=3
REGION="eastus"
BOOTSTRAP_KUBECONFIG="${SCRIPT_DIR}/../bootstrap-kubeconfig"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)
      HUB_CLUSTER_NAME="$2"
      shift 2
      ;;
    --provider)
      CLOUD_PROVIDER="$2"
      shift 2
      ;;
    --nodes)
      NODE_COUNT="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --kubeconfig)
      HUB_KUBECONFIG="$2"
      shift 2
      ;;
    --bootstrap-kubeconfig)
      BOOTSTRAP_KUBECONFIG="$2"
      shift 2
      ;;
    --help)
      cat <<EOF
Usage: $0 [options]

Create a high-availability GitOps hub cluster.

Options:
  --name <name>              Cluster name (default: gitops-hub)
  --provider <provider>      Cloud provider: azure, aws, gcp (default: azure)
  --nodes <count>            Number of control plane nodes (default: 3)
  --region <region>          Cloud region (default: eastus)
  --kubeconfig <path>        Kubeconfig path (default: ./hub-kubeconfig)
  --bootstrap-kubeconfig <path> Bootstrap cluster kubeconfig
  --help                     Show this help

Examples:
  $0                                    # Azure cluster with defaults
  $0 --provider aws --region us-west-2  # AWS cluster in Oregon
  $0 --nodes 5 --provider gcp          # GCP cluster with 5 nodes
EOF
      exit 0
      ;;
    *)
      fail "Unknown option: $1. Use --help for usage."
      ;;
  esac
done

info "Creating hub cluster: ${HUB_CLUSTER_NAME}"
info "Cloud provider: ${CLOUD_PROVIDER}"
info "Region: ${REGION}"
info "Node count: ${NODE_COUNT}"

# Validate prerequisites
validate_prerequisites() {
  info "Validating prerequisites..."
  
  # Check cloud CLI tools
  case "$CLOUD_PROVIDER" in
    azure)
      if ! command -v az >/dev/null 2>&1; then
        fail "Azure CLI not found. Install from https://docs.microsoft.com/en-us/cli/azure/"
      fi
      
      # Check Azure login
      if ! az account show >/dev/null 2>&1; then
        fail "Not logged into Azure. Run 'az login'"
      fi
      ;;
    aws)
      if ! command -v aws >/dev/null 2>&1; then
        fail "AWS CLI not found. Install from https://aws.amazon.com/cli/"
      fi
      
      # Check AWS credentials
      if ! aws sts get-caller-identity >/dev/null 2>&1; then
        fail "AWS credentials not configured. Run 'aws configure'"
      fi
      ;;
    gcp)
      if ! command -v gcloud >/dev/null 2>&1; then
        fail "Google Cloud CLI not found. Install from https://cloud.google.com/sdk"
      fi
      
      # Check GCP login
      if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 >/dev/null; then
        fail "Not logged into Google Cloud. Run 'gcloud auth login'"
      fi
      ;;
    *)
      fail "Unsupported cloud provider: $CLOUD_PROVIDER. Use: azure, aws, gcp"
      ;;
  esac
  
  # Check kubectl
  if ! command -v kubectl >/dev/null 2>&1; then
    fail "kubectl not found. Install from https://kubernetes.io/docs/tasks/tools/"
  fi
  
  # Check bootstrap cluster
  if [[ ! -f "${BOOTSTRAP_KUBECONFIG}" ]]; then
    warn "Bootstrap kubeconfig not found at ${BOOTSTRAP_KUBECONFIG}"
    info "Run 'scripts/create-bootstrap-cluster.sh' first"
  fi
  
  pass "Prerequisites validated"
}

# Create hub cluster based on provider
create_hub_cluster() {
  info "Creating ${CLOUD_PROVIDER} hub cluster..."
  
  case "$CLOUD_PROVIDER" in
    azure)
      create_aks_cluster
      ;;
    aws)
      create_eks_cluster
      ;;
    gcp)
      create_gke_cluster
      ;;
  esac
}

# Create AKS cluster
create_aks_cluster() {
  info "Creating AKS cluster..."
  
  local resource_group="gitops-rg-${HUB_CLUSTER_NAME}"
  local cluster_name="${HUB_CLUSTER_NAME}"
  
  # Create resource group if it doesn't exist
  if ! az group show --name "$resource_group" >/dev/null 2>&1; then
    info "Creating resource group: $resource_group"
    az group create --name "$resource_group" --location "$REGION" --output none
  fi
  
  # Check if cluster exists
  if az aks show --resource-group "$resource_group" --name "$cluster_name" >/dev/null 2>&1; then
    warn "AKS cluster $cluster_name already exists"
    info "Using existing cluster"
  else
    info "Creating AKS cluster with $NODE_COUNT nodes..."
    
    # Create AKS cluster
    az aks create \
      --resource-group "$resource_group" \
      --name "$cluster_name" \
      --node-count "$NODE_COUNT" \
      --generate-ssh-keys \
      --enable-cluster-autoscaler \
      --min-count 1 \
      --max-count 5 \
      --network-plugin azure \
      --network-policy azure \
      --enable-managed-identity \
      --output none
    
    pass "AKS cluster created"
  fi
  
  # Get credentials
  info "Getting AKS credentials..."
  az aks get-credentials \
    --resource-group "$resource_group" \
    --name "$cluster_name" \
    --file "${HUB_KUBECONFIG}" \
    --overwrite-existing
  
  export KUBECONFIG="${HUB_KUBECONFIG}"
  pass "AKS credentials configured"
}

# Create EKS cluster
create_eks_cluster() {
  info "Creating EKS cluster..."
  
  local cluster_name="${HUB_CLUSTER_NAME}"
  local node_group_name="${cluster_name}-ng"
  
  # Check if cluster exists
  if aws eks describe-cluster --name "$cluster_name" --region "$REGION" >/dev/null 2>&1; then
    warn "EKS cluster $cluster_name already exists"
    info "Using existing cluster"
  else
    info "Creating EKS cluster..."
    
    # Create EKS cluster
    aws eks create-cluster \
      --region "$REGION" \
      --name "$cluster_name" \
      --kubernetes-version "1.29" \
      --role-arn "$(aws iam create-role --role-name "${cluster_name}-role" --assume-role-policy-document '{"Version": "2012-10-17","Statement": [{"Effect": "Allow","Principal": {"Service": "eks.amazonaws.com"},"Action": "sts:AssumeRole"}]}' --query 'Role.Arn' --output text)" \
      --resources-vpc-config subnetIds="$(aws ec2 describe-subnets --region "$REGION" --filters "Name=default-for-az,Values=true" --query 'Subnets[0:2].SubnetId' --output text)" \
      --output none
    
    # Wait for cluster to become active
    info "Waiting for EKS cluster to become active..."
    aws eks wait cluster-active --name "$cluster_name" --region "$REGION"
    
    pass "EKS cluster created"
  fi
  
  # Create node group if needed
  if ! aws eks describe-nodegroup --cluster-name "$cluster_name" --nodegroup-name "$node_group_name" --region "$REGION" >/dev/null 2>&1; then
    info "Creating EKS node group..."
    
    aws eks create-nodegroup \
      --cluster-name "$cluster_name" \
      --nodegroup-name "$node_group_name" \
      --scaling-config minSize=1,maxSize=5,desiredSize="$NODE_COUNT" \
      --subnets "$(aws ec2 describe-subnets --region "$REGION" --filters "Name=default-for-az,Values=true" --query 'Subnets[0:2].SubnetId' --output text)" \
      --instance-types "t3.medium" \
      --ami-type "AL2_x86_64" \
      --capacity-type "ON_DEMAND" \
      --region "$REGION" \
      --output none
    
    # Wait for node group to become active
    info "Waiting for node group to become active..."
    aws eks wait nodegroup-active --cluster-name "$cluster_name" --nodegroup-name "$node_group_name" --region "$REGION"
    
    pass "EKS node group created"
  fi
  
  # Update kubeconfig
  info "Updating kubeconfig..."
  aws eks update-kubeconfig --region "$REGION" --name "$cluster_name" --kubeconfig "${HUB_KUBECONFIG}"
  export KUBECONFIG="${HUB_KUBECONFIG}"
  
  pass "EKS credentials configured"
}

# Create GKE cluster
create_gke_cluster() {
  info "Creating GKE cluster..."
  
  local cluster_name="${HUB_CLUSTER_NAME}"
  
  # Set project if not set
  local project_id
  project_id=$(gcloud config get-value project 2>/dev/null || echo "")
  if [[ -z "$project_id" ]]; then
    fail "Google Cloud project not set. Run 'gcloud config set project PROJECT_ID'"
  fi
  
  # Check if cluster exists
  if gcloud container clusters describe "$cluster_name" --region "$REGION" >/dev/null 2>&1; then
    warn "GKE cluster $cluster_name already exists"
    info "Using existing cluster"
  else
    info "Creating GKE cluster..."
    
    # Create GKE cluster
    gcloud container clusters create "$cluster_name" \
      --region "$REGION" \
      --num-nodes "$NODE_COUNT" \
      --enable-autoscaling \
      --min-nodes 1 \
      --max-nodes 5 \
      --enable-autorepair \
      --enable-autoupgrade \
      --enable-ip-alias \
      --enable-network-policy \
      --enable-master-authorized-networks \
      --enable-private-nodes \
      --enable-master-global-access \
      --release-channel "stable"
    
    pass "GKE cluster created"
  fi
  
  # Get credentials
  info "Getting GKE credentials..."
  gcloud container clusters get-credentials "$cluster_name" --region "$REGION" --kubeconfig "${HUB_KUBECONFIG}"
  export KUBECONFIG="${HUB_KUBECONFIG}"
  
  pass "GKE credentials configured"
}

# Install GitOps components
install_gitops_components() {
  info "Installing GitOps components on hub cluster..."
  
  # Wait for cluster to be ready
  info "Waiting for cluster to be ready..."
  kubectl wait --for=condition=Ready nodes --all --timeout=600s
  
  # Create namespaces
  kubectl create namespace flux-system --dry-run=client -o yaml | kubectl apply -f -
  kubectl create namespace crossplane-system --dry-run=client -o yaml | kubectl apply -f -
  kubectl create namespace gitops-system --dry-run=client -o yaml | kubectl apply -f -
  
  # Install Flux
  info "Installing Flux..."
  if ! command -v flux >/dev/null 2>&1; then
    warn "Flux CLI not found. Installing Flux components manually..."
    # Apply Flux manifests directly
    kubectl apply -f https://github.com/fluxcd/flux2/releases/latest/download/install.yaml
  else
    flux install --namespace flux-system
  fi
  
  pass "GitOps components installed"
}

# Configure hub recovery
configure_hub_recovery() {
  info "Configuring hub recovery using bootstrap cluster..."
  
  if [[ -f "${BOOTSTRAP_KUBECONFIG}" ]]; then
    # Store bootstrap cluster info in hub
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: bootstrap-cluster-kubeconfig
  namespace gitops-system
type: Opaque
data:
  kubeconfig: $(base64 -i "${BOOTSTRAP_KUBECONFIG}")
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: hub-recovery-config
  namespace gitops-system
data:
  bootstrap-cluster: "${BOOTSTRAP_KUBECONFIG}"
  hub-cluster: "${HUB_KUBECONFIG}"
  recovery-enabled: "true"
  created-at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
EOF
    pass "Hub recovery configured"
  else
    warn "Bootstrap kubeconfig not found - recovery not configured"
  fi
}

# Verify hub cluster
verify_hub_cluster() {
  info "Verifying hub cluster..."
  
  # Check node status
  local ready_nodes
  ready_nodes=$(kubectl get nodes --no-headers | grep -c "Ready" || echo "0")
  if [[ "$ready_nodes" -lt "$NODE_COUNT" ]]; then
    fail "Expected $NODE_COUNT ready nodes, found $ready_nodes"
  fi
  
  # Check namespaces
  for ns in flux-system crossplane-system gitops-system; do
    if ! kubectl get namespace "$ns" >/dev/null 2>&1; then
      fail "Namespace $ns not found"
    fi
  done
  
  # Check Flux pods
  if ! kubectl get pods -n flux-system --no-headers | grep -q "Running"; then
    fail "Flux pods are not running"
  fi
  
  pass "Hub cluster verified"
}

# Show cluster info
show_cluster_info() {
  echo
  echo -e "${BOLD}Hub Cluster Information${RESET}"
  echo "============================="
  echo "Cluster Name: ${HUB_CLUSTER_NAME}"
  echo "Cloud Provider: ${CLOUD_PROVIDER}"
  echo "Region: ${REGION}"
  echo "Node Count: ${NODE_COUNT}"
  echo "Kubeconfig: ${HUB_KUBECONFIG}"
  echo
  echo "To use this cluster:"
  echo "  export KUBECONFIG=${HUB_KUBECONFIG}"
  echo "  kubectl get nodes"
  echo
  echo "Next steps:"
  echo "  1. Run: scripts/install-crossplane.sh"
  echo "  2. Run: scripts/provision-spoke-clusters.sh"
  echo "  3. Apply GitOps manifests"
  echo
}

# Main execution
main() {
  echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${RESET}"
  echo -e "${BOLD}║   GitOps Infra Control Plane — Hub Cluster Setup         ║${RESET}"
  echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${RESET}"
  echo
  
  validate_prerequisites
  create_hub_cluster
  install_gitops_components
  configure_hub_recovery
  verify_hub_cluster
  show_cluster_info
  
  echo -e "${GREEN}${BOLD}Hub cluster created successfully!${RESET}"
}

# Run main function
main "$@"

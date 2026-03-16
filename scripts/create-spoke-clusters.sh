#!/usr/bin/env bash
# =============================================================================
# Provision Spoke Clusters - Create and configure spoke clusters via Cluster API
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
ensure_wsl_sanity "provision-spoke-clusters.sh" warn info

# Default configuration
HUB_KUBECONFIG="${SCRIPT_DIR}/../hub-kubeconfig"
SPOKE_CONFIG="${SCRIPT_DIR}/../spoke-clusters.yaml"
CLOUD_PROVIDERS="azure,aws,gcp"  # Multi-cloud by design
SPOKE_COUNT=3  # One per cloud provider
SPOKE_PREFIX="gitops-spoke"
FLUX_ENABLED=true
ESO_ENABLED=true

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --hub-kubeconfig)
      HUB_KUBECONFIG="$2"
      shift 2
      ;;
    --config)
      SPOKE_CONFIG="$2"
      shift 2
      ;;
    --provider)
      CLOUD_PROVIDER="$2"
      shift 2
      ;;
    --count)
      SPOKE_COUNT="$2"
      shift 2
      ;;
    --prefix)
      SPOKE_PREFIX="$2"
      shift 2
      ;;
    --no-flux)
      FLUX_ENABLED=false
      shift
      ;;
    --no-eso)
      ESO_ENABLED=false
      shift
      ;;
    --help)
      cat <<EOF
Usage: $0 [options]

Provision spoke clusters using Cluster API on the hub cluster.

Options:
  --hub-kubeconfig <path>   Hub cluster kubeconfig (default: ./hub-kubeconfig)
  --config <path>          Spoke clusters configuration file (default: ./spoke-clusters.yaml)
  --providers <list>       Cloud providers: azure,aws,gcp (default: azure,aws,gcp)
  --count <number>         Number of spoke clusters (default: 3 - one per provider)
  --prefix <prefix>        Spoke cluster name prefix (default: gitops-spoke)
  --no-flux               Disable Flux installation on spokes
  --no-eso                Disable External Secrets Operator on spokes
  --help                  Show this help

Examples:
  $0                                    # Create 3 spokes (Azure, AWS, GCP) - multi-cloud by design
  $0 --providers azure,aws              # Create 2 spokes (Azure, AWS)
  $0 --count 2 --providers azure,gcp    # Create 2 spokes (Azure, GCP)
  $0 --config custom-spokes.yaml       # Use custom configuration
EOF
      exit 0
      ;;
    *)
      fail "Unknown option: $1. Use --help for usage."
      ;;
  esac
done

info "Provisioning spoke clusters"
info "Cloud providers: ${CLOUD_PROVIDERS}"
info "Spoke count: ${SPOKE_COUNT}"
info "Prefix: ${SPOKE_PREFIX}"

# Validate prerequisites
validate_prerequisites() {
  info "Validating prerequisites..."
  
  # Check hub kubeconfig
  if [[ ! -f "${HUB_KUBECONFIG}" ]]; then
    fail "Hub kubeconfig not found at ${HUB_KUBECONFIG}"
    fail "Run 'scripts/create-hub-cluster.sh' first"
  fi
  
  export KUBECONFIG="${HUB_KUBECONFIG}"
  
  # Check cluster access
  if ! kubectl cluster-info >/dev/null 2>&1; then
    fail "Cannot access hub cluster"
  fi
  
  # Check Crossplane
  if ! kubectl get providers.pkg.crossplane.io -n crossplane-system --no-headers | grep -q "Running"; then
    fail "Crossplane not running on hub cluster"
    fail "Run 'scripts/install-crossplane.sh' first"
  fi
  
  # Check cloud CLI tools for all providers
  IFS=',' read -ra PROVIDERS <<< "$CLOUD_PROVIDERS"
  for provider in "${PROVIDERS[@]}"; do
    provider=$(echo "$provider" | xargs)  # trim whitespace
    
    case "$provider" in
      azure)
        if ! command -v az >/dev/null 2>&1; then
          fail "Azure CLI not found"
        fi
        ;;
      aws)
        if ! command -v aws >/dev/null 2>&1; then
          fail "AWS CLI not found"
        fi
        ;;
      gcp)
        if ! command -v gcloud >/dev/null 2>&1; then
          fail "Google Cloud CLI not found"
        fi
        ;;
      *)
        warn "Unknown provider: $provider. Skipping..."
        ;;
    esac
  done
  
  pass "Prerequisites validated"
}

# Create spoke clusters configuration
create_spoke_config() {
  info "Creating spoke clusters configuration..."
  
  cat > "$SPOKE_CONFIG" <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: spoke-clusters-config
  namespace: gitops-system
data:
  config.yaml: |
    spoke_clusters:
EOF

  # Add spoke cluster configurations - one per provider
  local provider_index=0
  IFS=',' read -ra PROVIDERS <<< "$CLOUD_PROVIDERS"
  for provider in "${PROVIDERS[@]}"; do
    provider=$(echo "$provider" | xargs)  # trim whitespace
    provider_index=$((provider_index + 1))
    
    if [[ $provider_index -gt $SPOKE_COUNT ]]; then
      break
    fi
    
    local spoke_name="${SPOKE_PREFIX}-${provider}"
    local spoke_region
    
    case "$provider" in
      azure)
        spoke_region="eastus"
        ;;
      aws)
        spoke_region="us-east-1"
        ;;
      gcp)
        spoke_region="us-central1"
        ;;
      *)
        warn "Skipping unknown provider: $provider"
        continue
        ;;
    esac
    
    cat >> "$SPOKE_CONFIG" <<EOF
      - name: ${spoke_name}
        provider: ${provider}
        region: ${spoke_region}
        node_count: 2
        flux_enabled: ${FLUX_ENABLED}
        eso_enabled: ${ESO_ENABLED}
EOF
  done
  
  kubectl apply -f "$SPOKE_CONFIG"
  pass "Spoke configuration created"
}

# Install Cluster API providers
install_cluster_api() {
  info "Installing Cluster API providers..."
  
  # Create cluster-api namespace
  kubectl create namespace cluster-api-system --dry-run=client -o yaml | kubectl apply -f -
  
  # Install Cluster API core
  if ! kubectl get pods -n cluster-api-system --no-headers | grep -q "capi-controller-manager"; then
    info "Installing Cluster API core..."
    kubectl apply -f https://github.com/kubernetes-sigs/cluster-api/releases/latest/download/cluster-api-core.yaml
    kubectl wait --for=condition=Available deployment/capi-controller-manager -n cluster-api-system --timeout=300s
  fi
  
  # Install all required Cluster API providers
  IFS=',' read -ra PROVIDERS <<< "$CLOUD_PROVIDERS"
  for provider in "${PROVIDERS[@]}"; do
    provider=$(echo "$provider" | xargs)  # trim whitespace
    
    case "$provider" in
      azure)
        install_capi_azure
        ;;
      aws)
        install_capi_aws
        ;;
      gcp)
        install_capi_gcp
        ;;
      *)
        warn "Unknown provider: $provider. Skipping..."
        ;;
    esac
  done
  
  pass "Cluster API providers installed"
}

# Install CAPZ (Cluster API Provider Azure)
install_capi_azure() {
  info "Installing Cluster API Provider Azure..."
  
  if ! kubectl get pods -n cluster-api-system --no-headers | grep -q "capz-controller-manager"; then
    kubectl apply -f https://github.com/kubernetes-sigs/cluster-api-provider-azure/releases/latest/download/infrastructure-azure.yaml
    kubectl wait --for=condition=Available deployment/capz-controller-manager -n cluster-api-system --timeout=300s
  fi
  
  pass "CAPZ installed"
}

# Install CAPA (Cluster API Provider AWS)
install_capi_aws() {
  info "Installing Cluster API Provider AWS..."
  
  if ! kubectl get pods -n cluster-api-system --no-headers | grep -q "capa-controller-manager"; then
    kubectl apply -f https://github.com/kubernetes-sigs/cluster-api-provider-aws/releases/latest/download/infrastructure-aws.yaml
    kubectl wait --for=condition=Available deployment/capa-controller-manager -n cluster-api-system --timeout=300s
  fi
  
  pass "CAPA installed"
}

# Install CAPG (Cluster API Provider GCP)
install_capi_gcp() {
  info "Installing Cluster API Provider GCP..."
  
  if ! kubectl get pods -n cluster-api-system --no-headers | grep -q "capg-controller-manager"; then
    kubectl apply -f https://github.com/kubernetes-sigs/cluster-api-provider-gcp/releases/latest/download/infrastructure-gcp.yaml
    kubectl wait --for=condition=Available deployment/capg-controller-manager -n cluster-api-system --timeout=300s
  fi
  
  pass "CAPG installed"
}

# Create spoke clusters
create_spoke_clusters() {
  info "Create spoke clusters - one per cloud provider"
  local provider_index=0
  IFS=',' read -ra PROVIDERS <<< "$CLOUD_PROVIDERS"
  for provider in "${PROVIDERS[@]}"; do
    provider=$(echo "$provider" | xargs)  # trim whitespace
    provider_index=$((provider_index + 1))
    
    if [[ $provider_index -gt $SPOKE_COUNT ]]; then
      break
    fi
    
    local spoke_name="${SPOKE_PREFIX}-${provider}"
    create_single_spoke "$spoke_name" "$provider"
  done
  
  pass "Spoke clusters creation initiated"
}

# Create individual spoke cluster
create_single_spoke() {
  local spoke_name="$1"
  local provider="$2"
  
  info "Creating spoke cluster: $spoke_name (provider: $provider)"
  
  case "$provider" in
    azure)
      create_azure_spoke "$spoke_name"
      ;;
    aws)
      create_aws_spoke "$spoke_name"
      ;;
    gcp)
      create_gcp_spoke "$spoke_name"
      ;;
    *)
      warn "Unknown provider: $provider. Skipping..."
      ;;
  esac
}

# Create Azure spoke cluster
create_azure_spoke() {
  local spoke_name="$1"
  
  local resource_group="gitops-spokes-rg"
  local location="eastus"
  
  # Create resource group if needed
  if ! az group show --name "$resource_group" >/dev/null 2>&1; then
    az group create --name "$resource_group" --location "$location" --output none
  fi
  
  # Create AzureCluster manifest
  cat <<EOF | kubectl apply -f -
apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
kind: AzureCluster
metadata:
  name: ${spoke_name}
  namespace: gitops-system
spec:
  resourceGroup: ${resource_group}
  location: ${location}
  networkSpec:
    vnet:
      name: ${spoke_name}-vnet
      cidrBlocks:
      - 10.0.0.0/16
    subnets:
    - name: ${spoke_name}-node-subnet
      cidrBlocks:
      - 10.0.1.0/24
    - name: ${spoke_name}-lb-subnet
      cidrBlocks:
      - 10.0.2.0/24
  controlPlaneEndpoint:
    host: ""
    port: 6443
---
apiVersion: cluster.x-k8s.io/v1beta1
kind: Cluster
metadata:
  name: ${spoke_name}
  namespace: gitops-system
spec:
  clusterNetwork:
    pods:
      cidrBlocks:
      - 192.168.1.0/16
    services:
      cidrBlocks:
      - 10.96.1.0/12
    serviceDomain: service.${spoke_name}.local
  infrastructureRef:
    apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
    kind: AzureCluster
    name: ${spoke_name}
  controlPlaneRef:
    apiVersion: controlplane.cluster.x-k8s.io/v1beta1
    kind: KubeadmControlPlane
    name: ${spoke_name}-control-plane
---
apiVersion: controlplane.cluster.x-k8s.io/v1beta1
kind: KubeadmControlPlane
metadata:
  name: ${spoke_name}-control-plane
  namespace: gitops-system
spec:
  replicas: 1
  version: v1.29.0
  infrastructureTemplate:
    apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
    kind: AzureMachineTemplate
    name: ${spoke_name}-control-plane
  kubeadmConfigSpec:
    initConfiguration:
      nodeRegistration:
        name: \${local_hostname}
        criSocket: /var/run/containerd/containerd.sock
    joinConfiguration:
      nodeRegistration:
        name: \${local_hostname}
        criSocket: /var/run/containerd/containerd.sock
    postKubeadmCommands:
    - kubectl apply -f https://github.com/kubernetes-sigs/cluster-api/releases/latest/download/cluster-api.yaml
---
apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
kind: AzureMachineTemplate
metadata:
  name: ${spoke_name}-control-plane
  namespace: gitops-system
spec:
  template:
    spec:
      vmSize: Standard_D2s_v3
      image:
        marketplace:
          publisher: cncf-upstream
          offer: capi
          sku: k8s-1dot29dot0-ubuntu-2204
          version: latest
      osDisk:
        diskSizeGB: 30
        osType: Linux
EOF
}

# Create AWS spoke cluster
create_aws_spoke() {
  local spoke_name="$1"
  
  local region="us-east-1"
  
  # Create AWSCluster manifest
  cat <<EOF | kubectl apply -f -
apiVersion: infrastructure.cluster.x-k8s.io/v1beta2
kind: AWSCluster
metadata:
  name: ${spoke_name}
  namespace: gitops-system
spec:
  region: ${region}
  network:
    vpc:
      cidrBlock: 10.1.0.0/16
  controlPlaneLoadBalancer:
    loadBalancerType: "public"
  sshKeyName: gitops-spoke-${spoke_name}
---
apiVersion: cluster.x-k8s.io/v1beta1
kind: Cluster
metadata:
  name: ${spoke_name}
  namespace: gitops-system
spec:
  clusterNetwork:
    pods:
      cidrBlocks:
      - 192.168.2.0/16
    services:
      cidrBlocks:
      - 10.96.2.0/12
  infrastructureRef:
    apiVersion: infrastructure.cluster.x-k8s.io/v1beta2
    kind: AWSCluster
    name: ${spoke_name}
  controlPlaneRef:
    apiVersion: controlplane.cluster.x-k8s.io/v1beta1
    kind: KubeadmControlPlane
    name: ${spoke_name}-control-plane
---
apiVersion: controlplane.cluster.x-k8s.io/v1beta1
kind: KubeadmControlPlane
metadata:
  name: ${spoke_name}-control-plane
  namespace: gitops-system
spec:
  replicas: 1
  version: v1.29.0
  infrastructureTemplate:
    apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
    kind: AWSMachineTemplate
    name: ${spoke_name}-control-plane
  kubeadmConfigSpec:
    initConfiguration:
      nodeRegistration:
        name: \${local_hostname}
        criSocket: /var/run/containerd/containerd.sock
    joinConfiguration:
      nodeRegistration:
        name: \${local_hostname}
        criSocket: /var/run/containerd/containerd.sock
---
apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
kind: AWSMachineTemplate
metadata:
  name: ${spoke_name}-control-plane
  namespace: gitops-system
spec:
  template:
    spec:
      instanceType: t3.medium
      ami:
        id: ami-0c02fb55956c7d316
      sshKeyName: gitops-spoke-${spoke_name}
      rootVolume:
        size: 30
        type: gp3
EOF
}

# Create GCP spoke cluster
create_gcp_spoke() {
  local spoke_name="$1"
  
  local region="us-central1"
  
  # Create GCPCluster manifest
  cat <<EOF | kubectl apply -f -
apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
kind: GCPCluster
metadata:
  name: ${spoke_name}
  namespace: gitops-system
spec:
  project: $(gcloud config get-value project)
  region: ${region}
  network:
    name: ${spoke_name}-network
    autoCreateSubnetworks: false
---
apiVersion: cluster.x-k8s.io/v1beta1
kind: Cluster
metadata:
  name: ${spoke_name}
  namespace: gitops-system
spec:
  clusterNetwork:
    pods:
      cidrBlocks:
      - 192.168.3.0/16
    services:
      cidrBlocks:
      - 10.96.3.0/12
  infrastructureRef:
    apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
    kind: GCPCluster
    name: ${spoke_name}
  controlPlaneRef:
    apiVersion: controlplane.cluster.x-k8s.io/v1beta1
    kind: KubeadmControlPlane
    name: ${spoke_name}-control-plane
---
apiVersion: controlplane.cluster.x-k8s.io/v1beta1
kind: KubeadmControlPlane
metadata:
  name: ${spoke_name}-control-plane
  namespace: gitops-system
spec:
  replicas: 1
  version: v1.29.0
  infrastructureTemplate:
    apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
    kind: GCPMachineTemplate
    name: ${spoke_name}-control-plane
  kubeadmConfigSpec:
    initConfiguration:
      nodeRegistration:
        name: \${local_hostname}
        criSocket: /var/run/containerd/containerd.sock
    joinConfiguration:
      nodeRegistration:
        name: \${local_hostname}
        criSocket: /var/run/containerd/containerd.sock
---
apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
kind: GCPMachineTemplate
metadata:
  name: ${spoke_name}-control-plane
  namespace: gitops-system
spec:
  template:
    spec:
      machineType: e2-medium
      image: ubuntu-os-cloud/ubuntu-2204-jammy-v20240101
      diskSizeGb: 30
      diskType: pd-balanced
EOF
}

# Install Flux on spokes
install_flux_on_spokes() {
  if [[ "$FLUX_ENABLED" != "true" ]]; then
    warn "Flux installation on spokes disabled"
    return
  fi
  
  info "Configuring Flux installation on spoke clusters..."
  
  # Create Flux GitRepository for spokes
  cat <<EOF | kubectl apply -f -
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: flux-system
  namespace: flux-system
spec:
  interval: 1m0s
  ref:
    branch: main
  url: ssh://git@github.com/your-org/your-repo.git
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: flux-system
  namespace: flux-system
spec:
  interval: 10m0s
  path: ./control-plane/spokes
  prune: true
  sourceRef:
    kind: GitRepository
    name: flux-system
EOF
  
  pass "Flux configuration for spokes created"
}

# Install External Secrets Operator on spokes
install_eso_on_spokes() {
  if [[ "$ESO_ENABLED" != "true" ]]; then
    warn "External Secrets Operator installation on spokes disabled"
    return
  fi
  
  info "Configuring External Secrets Operator on spoke clusters..."
  
  # Create ESO configuration
  cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: external-secrets
---
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: external-secrets
  namespace: external-secrets
spec:
  interval: 1m0s
  ref:
    branch: main
  url: https://github.com/external-secrets/external-secrets
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: external-secrets
  namespace: external-secrets
spec:
  interval: 10m0s
  path: ./deploy/charts/external-secrets
  prune: true
  sourceRef:
    kind: GitRepository
    name: external-secrets
EOF
  
  pass "ESO configuration for spokes created"
}

# Monitor spoke cluster creation
monitor_spoke_creation() {
  info "Monitoring spoke cluster creation..."
  
  local total_wait=0
  local max_wait=1800  # 30 minutes
  
  while [[ $total_wait -lt $max_wait ]]; do
    local ready_count=0
    local provider_index=0
    IFS=',' read -ra PROVIDERS <<< "$CLOUD_PROVIDERS"
    
    for provider in "${PROVIDERS[@]}"; do
      provider=$(echo "$provider" | xargs)  # trim whitespace
      provider_index=$((provider_index + 1))
      
      if [[ $provider_index -gt $SPOKE_COUNT ]]; then
        break
      fi
      
      local spoke_name="${SPOKE_PREFIX}-${provider}"
      
      if kubectl get cluster "$spoke_name" -n gitops-system -o jsonpath='{.status.phase}' 2>/dev/null | grep -q "Provisioned"; then
        ready_count=$((ready_count + 1))
      fi
    done
    
    if [[ $ready_count -eq $SPOKE_COUNT ]]; then
      pass "All spoke clusters are provisioned"
      return
    fi
    
    info "Spoke clusters ready: $ready_count/$SPOKE_COUNT (waiting...)"
    sleep 60
    total_wait=$((total_wait + 60))
  done
  
  warn "Spoke cluster creation timed out. Check cluster status manually."
}

# Verify spoke clusters
verify_spoke_clusters() {
  info "Verifying spoke clusters..."
  
  local provider_index=0
  IFS=',' read -ra PROVIDERS <<< "$CLOUD_PROVIDERS"
  
  for provider in "${PROVIDERS[@]}"; do
    provider=$(echo "$provider" | xargs)  # trim whitespace
    provider_index=$((provider_index + 1))
    
    if [[ $provider_index -gt $SPOKE_COUNT ]]; then
      break
    fi
    
    local spoke_name="${SPOKE_PREFIX}-${provider}"
    
    if ! kubectl get cluster "$spoke_name" -n gitops-system >/dev/null 2>&1; then
      fail "Spoke cluster $spoke_name not found"
    fi
    
    local phase
    phase=$(kubectl get cluster "$spoke_name" -n gitops-system -o jsonpath='{.status.phase}' 2>/dev/null || echo "Unknown")
    info "Spoke $spoke_name ($provider) status: $phase"
  done
  
  pass "Spoke clusters verified"
}

# Show provisioning info
show_provisioning_info() {
  echo
  echo -e "${BOLD}Spoke Clusters Provisioning Information${RESET}"
  echo "=========================================="
  echo "Cloud Providers: $CLOUD_PROVIDERS"
  echo "Spoke Count: $SPOKE_COUNT"
  echo "Prefix: $SPOKE_PREFIX"
  echo "Hub Kubeconfig: $HUB_KUBECONFIG"
  echo "Config File: $SPOKE_CONFIG"
  echo "Flux Enabled: $FLUX_ENABLED"
  echo "ESO Enabled: $ESO_ENABLED"
  echo
  echo "Multi-cloud spoke clusters:"
  local provider_index=0
  IFS=',' read -ra PROVIDERS <<< "$CLOUD_PROVIDERS"
  for provider in "${PROVIDERS[@]}"; do
    provider=$(echo "$provider" | xargs)  # trim whitespace
    provider_index=$((provider_index + 1))
    
    if [[ $provider_index -gt $SPOKE_COUNT ]]; then
      break
    fi
    
    local spoke_name="${SPOKE_PREFIX}-${provider}"
    echo "  - $spoke_name ($provider)"
  done
  echo
  echo "To check spoke cluster status:"
  echo "  export KUBECONFIG=$HUB_KUBECONFIG"
  echo "  kubectl get clusters -n gitops-system"
  echo "  kubectl describe cluster <spoke-name> -n gitops-system"
  echo
  echo "Next steps:"
  echo "  1. Wait for clusters to be provisioned (can take 15-30 minutes)"
  echo "  2. Apply GitOps manifests to clusters"
  echo "  3. Configure spoke-specific applications"
  echo
}

# Main execution
main() {
  echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${RESET}"
  echo -e "${BOLD}║   GitOps Infra Control Plane — Spoke Clusters Setup     ║${RESET}"
  echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${RESET}"
  echo
  
  validate_prerequisites
  create_spoke_config
  install_cluster_api
  create_spoke_clusters
  install_flux_on_spokes
  install_eso_on_spokes
  monitor_spoke_creation
  verify_spoke_clusters
  show_provisioning_info
  
  echo -e "${GREEN}${BOLD}Spoke clusters provisioning initiated!${RESET}"
}

# Run main function
main "$@"

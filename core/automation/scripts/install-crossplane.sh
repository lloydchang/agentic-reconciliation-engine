#!/usr/bin/env bash
# =============================================================================
# Install Crossplane - Universal Control Plane for Cloud Infrastructure
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
ensure_wsl_sanity "install-crossplane.sh" warn info

# Default configuration
HUB_KUBECONFIG="${SCRIPT_DIR}/../hub-kubeconfig"
CLOUD_PROVIDERS="azure,aws,gcp,local"
CROSSPLANE_VERSION="latest"
NAMESPACE="crossplane-system"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --kubeconfig)
      HUB_KUBECONFIG="$2"
      shift 2
      ;;
    --providers)
      CLOUD_PROVIDERS="$2"
      shift 2
      ;;
    --version)
      CROSSPLANE_VERSION="$2"
      shift 2
      ;;
    --namespace)
      NAMESPACE="$2"
      shift 2
      ;;
    --help)
      cat <<EOF
Usage: $0 [options]

Install Crossplane and cloud providers on the hub cluster.

Options:
  --kubeconfig <path>     Hub cluster kubeconfig (default: ./hub-kubeconfig)
  --providers <list>      Cloud providers: azure,aws,gcp,local (default: azure,aws,gcp)
  --version <version>     Crossplane version (default: latest)
  --namespace <namespace> Installation namespace (default: crossplane-system)
  --help                  Show this help

Examples:
  $0                                    # Install all cloud providers
  $0 --providers azure,aws             # Install only Azure and AWS
  $0 --providers local                 # Install Kubernetes provider for local development
  $0 --kubeconfig /path/to/kubeconfig  # Custom kubeconfig
EOF
      exit 0
      ;;
    *)
      fail "Unknown option: $1. Use --help for usage."
      ;;
  esac
done

info "Installing Crossplane on hub cluster"
info "Providers: ${CLOUD_PROVIDERS}"
info "Version: ${CROSSPLANE_VERSION}"

# Validate prerequisites
validate_prerequisites() {
  info "Validating prerequisites..."
  
  # Check kubeconfig
  if [[ ! -f "${HUB_KUBECONFIG}" ]]; then
    fail "Hub kubeconfig not found at ${HUB_KUBECONFIG}"
    fail "Run 'core/core/automation/ci-cd/scripts/create-hub-cluster.sh' first"
  fi
  
  export KUBECONFIG="${HUB_KUBECONFIG}"
  
  # Check cluster access
  if ! kubectl cluster-info >/dev/null 2>&1; then
    fail "Cannot access hub cluster"
  fi
  
  # Check kubectl
  if ! command -v kubectl >/dev/null 2>&1; then
    fail "kubectl not found"
  fi
  
  pass "Prerequisites validated"
}

# Install Crossplane core
install_crossplane() {
  info "Installing Crossplane core..."
  
  # Add Crossplane repository
  if ! helm repo add crossplane https://charts.crossplane.io/stable; then
    diagnose_installation_failure "helm repo add" $?
    return 1
  fi
  
  if ! helm repo update; then
    diagnose_installation_failure "helm repo update" $?
    return 1
  fi
  
  # Install Crossplane
  if ! helm upgrade --install crossplane crossplane/crossplane \
    --namespace "$NAMESPACE" \
    --create-namespace \
    --set version="$CROSSPLANE_VERSION" \
    --set args[0]="--enable-environment-configs=true" \
    --wait; then
    diagnose_installation_failure "helm install crossplane" $?
    return 1
  fi
  
  # Wait for Crossplane to be ready
  info "Waiting for Crossplane to be ready..."
  if ! kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=crossplane -n "$NAMESPACE" --timeout=300s; then
    diagnose_installation_failure "kubectl wait crossplane pods" $?
    return 1
  fi
  
  pass "Crossplane installed"
}

# Install cloud providers
install_providers() {
  info "Installing cloud providers..."
  
  # Parse providers list
  IFS=',' read -ra PROVIDERS <<< "$CLOUD_PROVIDERS"
  
  for provider in "${PROVIDERS[@]}"; do
    provider=$(echo "$provider" | xargs)  # trim whitespace
    
    case "$provider" in
      azure)
        install_azure_provider
        ;;
      aws)
        install_aws_provider
        ;;
      gcp)
        install_gcp_provider
        ;;
      local)
        install_kubernetes_provider
        ;;
      *)
        warn "Unknown provider: $provider. Skipping..."
        ;;
    esac
  done
  
  pass "Cloud providers installed"
}

# Install Kubernetes provider for local development
install_kubernetes_provider() {
  info "Installing Kubernetes provider for local development..."
  
  # Install Kubernetes provider
  cat <<EOF | kubectl apply -f -
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-kubernetes
spec:
  package: "crossplane-contrib/provider-kubernetes:v0.6.0"
EOF
  
  # Wait for provider to be installed
  info "Waiting for Kubernetes provider to be ready..."
  kubectl wait --for=condition=Healthy provider/provider-kubernetes -n "$NAMESPACE" --timeout=300s
  
  # Create provider config for local cluster access
  cat <<EOF | kubectl apply -f -
apiVersion: kubernetes.crossplane.io/v1alpha1
kind: ProviderConfig
metadata:
  name: local-cluster
  namespace: "$NAMESPACE"
spec:
  credentials:
    source: InjectedIdentity
EOF
  
  pass "Kubernetes provider installed for local development"
}

# Install Azure provider
install_azure_provider() {
  info "Installing Azure provider..."
  
  # Create Azure provider secret (if credentials available)
  if az account show >/dev/null 2>&1; then
    local subscription_id tenant_id client_id client_secret
    
    subscription_id=$(az account show --query id -o tsv)
    tenant_id=$(az account show --query tenantId -o tsv)
    
    # Try to get service principal credentials
    if az ad sp show --id "http://gitops-crossplane" >/dev/null 2>&1; then
      client_id=$(az ad sp show --id "http://gitops-crossplane" --query appId -o tsv)
      client_secret=$(az ad sp credential list --id "http://gitops-crossplane" --query '[0].password' -o tsv 2>/dev/null || echo "")
    fi
    
    if [[ -n "$client_id" && -n "$client_secret" ]]; then
      kubectl create secret generic azure-creds \
        --namespace "$NAMESPACE" \
        --from-literal=client-id="$client_id" \
        --from-literal=client-secret="$client_secret" \
        --from-literal=subscription-id="$subscription_id" \
        --from-literal=tenant-id="$tenant_id" \
        --dry-run=client -o yaml | kubectl apply -f -
      
      pass "Azure provider credentials configured"
    else
      warn "Azure service principal not found. Manual credential setup required."
      info "Run: az ad sp create-for-rbac -n gitops-crossplane"
    fi
  fi
  
  # Install Azure provider
  cat <<EOF | kubectl apply -f -
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-azure
spec:
  package: "crossplane/provider-azure:${CROSSPLANE_VERSION}"
EOF
  
  pass "Azure provider installed"
}

# Install AWS provider
install_aws_provider() {
  info "Installing AWS provider..."
  
  # Create AWS provider secret (if credentials available)
  if aws sts get-caller-identity >/dev/null 2>&1; then
    local access_key_id secret_access_key session_token
    
    # Try to get credentials from environment
    access_key_id="${AWS_ACCESS_KEY_ID:-}"
    secret_access_key="${AWS_SECRET_ACCESS_KEY:-}"
    session_token="${AWS_SESSION_TOKEN:-}"
    
    if [[ -n "$access_key_id" && -n "$secret_access_key" ]]; then
      kubectl create secret generic aws-creds \
        --namespace "$NAMESPACE" \
        --from-literal=access-key-id="$access_key_id" \
        --from-literal=secret-access-key="$secret_access_key" \
        --from-literal=session-token="$session_token" \
        --dry-run=client -o yaml | kubectl apply -f -
      
      pass "AWS provider credentials configured"
    else
      warn "AWS credentials not found in environment. Manual credential setup required."
      info "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables"
    fi
  fi
  
  # Install AWS provider
  cat <<EOF | kubectl apply -f -
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-aws
spec:
  package: "crossplane/provider-aws:${CROSSPLANE_VERSION}"
EOF
  
  pass "AWS provider installed"
}

# Install GCP provider
install_gcp_provider() {
  info "Installing GCP provider..."
  
  # Create GCP provider secret (if credentials available)
  if gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 >/dev/null; then
    local service_account_key
    
    # Try to get service account key
    service_account_key="${GOOGLE_APPLICATION_CREDENTIALS:-}"
    
    if [[ -n "$service_account_key" && -f "$service_account_key" ]]; then
      kubectl create secret generic gcp-creds \
        --namespace "$NAMESPACE" \
        --from-file=service-account.json="$service_account_key" \
        --dry-run=client -o yaml | kubectl apply -f -
      
      pass "GCP provider credentials configured"
    else
      warn "GCP service account key not found. Manual credential setup required."
      info "Set GOOGLE_APPLICATION_CREDENTIALS environment variable to service account key file"
    fi
  fi
  
  # Install GCP provider
  cat <<EOF | kubectl apply -f -
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-gcp
spec:
  package: "crossplane/provider-gcp:${CROSSPLANE_VERSION}"
EOF
  
  pass "GCP provider installed"
}

# Install sample Composite Resource Definitions
install_compositions() {
  info "Installing sample Composite Resource Definitions..."
  
  # Create XDatabase composition
  cat <<EOF | kubectl apply -f -
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xdatabases.database.gitops.example
spec:
  group: database.gitops.example
  names:
    plural: xdatabases
    singular: xdatabase
    kind: XDatabase
  claimNames:
    plural: xdatabases
    singular: xdatabase
  connectionSecretKeys:
    - username
    - password
    - endpoint
    - port
  versions:
  - name: v1alpha1
    served: true
    referenceable: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              parameters:
                type: object
                properties:
                  storageGB:
                    type: integer
                    default: 20
                  engine:
                    type: string
                    enum: [postgresql, mysql]
                    default: postgresql
                  region:
                    type: string
                    default: us-east-1
                required:
                - storageGB
                - engine
            required:
            - parameters
EOF
  
  # Create XNetwork composition
  cat <<EOF | kubectl apply -f -
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xnetworks.network.gitops.example
spec:
  group: network.gitops.example
  names:
    plural: xnetworks
    singular: xnetwork
    kind: XNetwork
  claimNames:
    plural: xnetworks
    singular: xnetwork
  versions:
  - name: v1alpha1
    served: true
    referenceable: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              parameters:
                type: object
                properties:
                  cidrBlock:
                    type: string
                    default: "10.0.0.0/16"
                  region:
                    type: string
                    default: us-east-1
                required:
                - cidrBlock
            required:
            - parameters
EOF
  
  pass "Sample compositions installed"
}

# Diagnose installation failure
diagnose_installation_failure() {
  local operation="$1"
  local exit_code="$2"
  
  echo
  echo -e "${RED}❌ Installation failed during: ${operation}${RESET}"
  echo -e "${YELLOW}Exit code: ${exit_code}${RESET}"
  echo
  
  # Run network connectivity diagnostic
  if [[ -f "${SCRIPT_DIR}/network-connectivity-diagnostic.sh" ]]; then
    echo -e "${CYAN}Running network connectivity diagnostic...${RESET}"
    "${SCRIPT_DIR}/network-connectivity-diagnostic.sh"
    echo
  fi
  
  # Analyze specific failure patterns
  case "$exit_code" in
    1)
      echo -e "${YELLOW}Possible causes:${RESET}"
      echo "  • Command execution failure"
      echo "  • Permission issues"
      echo "  • Resource not found"
      ;;
    2)
      echo -e "${YELLOW}Possible causes:${RESET}"
      echo "  • Invalid arguments or options"
      echo "  • Misconfiguration"
      ;;
    125)
      echo -e "${YELLOW}Possible causes:${RESET}"
      echo "  • Command timeout (network connectivity issue)"
      echo "  • Resource exhaustion"
      echo "  • Network latency"
      ;;
    130)
      echo -e "${YELLOW}Possible causes:${RESET}"
      echo "  • Script interrupted (Ctrl+C)"
      echo "  • Process termination"
      ;;
    255)
      echo -e "${YELLOW}Possible causes:${RESET}"
      echo "  • Exit status out of range"
      echo "  • Signal termination"
      ;;
    *)
      echo -e "${YELLOW}Possible causes:${RESET}"
      echo "  • Network connectivity issues"
      echo "  • Service unavailable"
      echo "  • Authentication/authorization problems"
      echo "  • Resource constraints"
      ;;
  esac
  
  # Operation-specific diagnostics
  echo
  echo -e "${CYAN}Operation-specific diagnostics:${RESET}"
  case "$operation" in
    "helm repo add")
      echo "  • Check internet connectivity"
      echo "  • Verify proxy settings: HTTP_PROXY, HTTPS_PROXY"
      echo "  • Test DNS resolution: nslookup charts.crossplane.io"
      echo "  • Check firewall rules for HTTPS (port 443)"
      ;;
    "helm repo update")
      echo "  • Repository availability issues"
      echo "  • Network latency or packet loss"
      echo "  • Helm cache corruption: Try 'helm repo rm crossplane' and retry"
      ;;
    "helm install crossplane")
      echo "  • Cluster connectivity problems"
      echo "  • Insufficient cluster resources"
      echo "  • Namespace creation issues"
      echo "  • Image pull failures"
      echo "  • Check: kubectl get nodes, kubectl top nodes"
      ;;
    "kubectl wait crossplane pods")
      echo "  • Pod startup failures"
      echo "  • Resource constraints (CPU/memory)"
      echo "  • Image pull issues"
      echo "  • Configuration errors"
      echo "  • Check: kubectl get pods -n $NAMESPACE, kubectl describe pods -n $NAMESPACE"
      ;;
  esac
  
  # Additional debugging commands
  echo
  echo -e "${CYAN}Additional debugging commands:${RESET}"
  echo "  # Check cluster connectivity"
  echo "  kubectl cluster-info"
  echo "  kubectl get nodes"
  echo
  echo "  # Check Crossplane namespace"
  echo "  kubectl get namespace $NAMESPACE -o yaml"
  echo "  kubectl get events -n $NAMESPACE --sort-by=.metadata.creationTimestamp"
  echo
  echo "  # Check Helm status"
  echo "  helm list -n $NAMESPACE"
  echo "  helm history crossplane -n $NAMESPACE"
  echo
  echo "  # Check system resources"
  echo "  kubectl top nodes"
  echo "  kubectl top pods --all-namespaces"
  echo
  echo "  # Test network connectivity"
  echo "  curl -I https://charts.crossplane.io/stable"
  echo "  ping -c 3 charts.crossplane.io"
  
  # Recommendations based on common issues
  echo
  echo -e "${CYAN}Common solutions:${RESET}"
  echo "  1. Network issues: Set proxy variables and retry"
  echo "     export HTTP_PROXY=http://proxy.company.com:8080"
  echo "     export HTTPS_PROXY=http://proxy.company.com:8080"
  echo
  echo "  2. Resource issues: Check cluster capacity"
  echo "     kubectl describe nodes"
  echo
  echo "  3. DNS issues: Restart CoreDNS"
  echo "     kubectl rollout restart deployment/coredns -n kube-system"
  echo
  echo "  4. Helm issues: Clear cache and retry"
  echo "     helm repo rm crossplane"
  echo "     helm repo add crossplane https://charts.crossplane.io/stable"
  echo
  echo "  5. Permission issues: Check RBAC"
  echo "     kubectl auth can-i create namespace"
  echo "     kubectl auth can-i create deployment --namespace=$NAMESPACE"
  
  echo
  echo -e "${RED}Installation failed. Run the diagnostic commands above to identify the root cause.${RESET}"
  exit "$exit_code"
}
# Verify Crossplane installation
verify_installation() {
  info "Verifying Crossplane installation..."
  
  # Check Crossplane pods
  if ! kubectl get pods -n "$NAMESPACE" --no-headers | grep -q "Running"; then
    diagnose_installation_failure "verification - pod check" $?
    return 1
  fi
  
  # Check providers
  local provider_count
  provider_count=$(kubectl get providers.pkg.crossplane.io -n "$NAMESPACE" --no-headers | wc -l)
  if [[ "$provider_count" -eq 0 ]]; then
    diagnose_installation_failure "verification - provider check" $?
    return 1
  fi
  
  # Check XRDs
  local xrd_count
  xrd_count=$(kubectl get compositeresourcedefinitions.apiextensions.crossplane.io --no-headers | wc -l)
  if [[ "$xrd_count" -eq 0 ]]; then
    warn "No Composite Resource Definitions found"
  fi
  
  pass "Crossplane installation verified"
}

# Show installation info
show_installation_info() {
  echo
  echo -e "${BOLD}Crossplane Installation Information${RESET}"
  echo "======================================"
  echo "Namespace: $NAMESPACE"
  echo "Version: $CROSSPLANE_VERSION"
  echo "Providers: $CLOUD_PROVIDERS"
  echo "Kubeconfig: $HUB_KUBECONFIG"
  echo
  echo "To check Crossplane status:"
  echo "  export KUBECONFIG=$HUB_KUBECONFIG"
  echo "  kubectl get providers -n $NAMESPACE"
  echo "  kubectl get xrd"
  echo
  echo "Next steps:"
  echo "  1. Configure cloud provider credentials"
  echo "  2. Run: core/core/automation/ci-cd/scripts/provision-spoke-clusters.sh"
  echo "  3. Create Composite Resources"
  echo
}

# Main execution
main() {
  echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${RESET}"
  echo -e "${BOLD}║   GitOps Infra Control Plane — Crossplane Setup         ║${RESET}"
  echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${RESET}"
  echo
  
  # Set error handling to use diagnostic function
  set -Eeo pipefail
  trap 'diagnose_installation_failure "unknown operation" $?' ERR
  
  validate_prerequisites
  install_crossplane
  install_providers
  install_compositions
  verify_installation
  show_installation_info
  
  echo -e "${GREEN}${BOLD}Crossplane installed successfully!${RESET}"
}

# Run main function
main "$@"

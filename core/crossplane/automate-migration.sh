#!/usr/bin/env bash
#
# Crossplane Migration Automation Script
# This script automates the complete migration from Terraform to Crossplane
#
# Usage:
#   ./automate-migration.sh [--dry-run] [--skip-providers] [--skip-gitops] [--only-rbac]
#
# Examples:
#   ./automate-migration.sh --dry-run    # Show what would be done
#   ./automate-migration.sh              # Full automated setup
#   ./automate-migration.sh --skip-providers  # Skip provider installation (already done)
#
# Prerequisites:
# - kubectl configured with cluster-admin access
# - helm 3+
# - jq for JSON processing
# - AWS CLI, Azure CLI, GCP CLI (for credential validation)
# - Crossplane repository added to helm

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CROSSPLANE_NAMESPACE="crossplane-system"
CROSSPLANE_VERSION="1.12.0"  # Adjust as needed
PROVIDERS_VERSION="v0.35.0"  # AWS provider version (others similar)
TEAM_NAMESPACES=("team-a" "team-b" "team-c")
ENVIRONMENTS=("dev" "staging" "prod")
DRY_RUN=false
SKIP_PROVIDERS=false
SKIP_GITOPS=false
ONLY_RBAC=false

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi

    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed"
        exit 1
    fi

    if ! command -v jq &> /dev/null; then
        log_warn "jq is not installed (optional but recommended)"
    fi

    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    # Check cluster version
    K8S_VERSION=$(kubectl version --short --client 2>/dev/null | grep -oP 'v\d+\.\d+' | head -1)
    log_info "Kubernetes client version: $K8S_VERSION"

    # Verify cluster-admin access
    if ! kubectl auth can-i create namespaces --all-namespaces &> /dev/null; then
        log_error "Insufficient permissions. Need cluster-admin access."
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Step 1: Install Crossplane
install_crossplane() {
    if $DRY_RUN; then
        log_info "[DRY RUN] Would install Crossplane $CROSSPLANE_VERSION"
        return 0
    fi

    log_info "Installing Crossplane..."

    # Add Crossplane Helm repository
    if ! helm repo list | grep -q crossplane-stable; then
        helm repo add crossplane-stable https://charts.crossplane.io/stable
    fi
    helm repo update

    # Create namespace if not exists
    kubectl create namespace "$CROSSPLANE_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

    # Install Crossplane
    if helm list -n "$CROSSPLANE_NAMESPACE" | grep -q crossplane; then
        log_warn "Crossplane already installed, upgrading..."
        helm upgrade crossplane crossplane-stable/crossplane \
            --namespace "$CROSSPLANE_NAMESPACE" \
            --set rbac.manager=true \
            --wait \
            --timeout 5m
    else
        helm install crossplane crossplane-stable/crossplane \
            --namespace "$CROSSPLANE_NAMESPACE" \
            --set rbac.manager=true \
            --wait \
            --timeout 5m
    fi

    # Wait for Crossplane pod to be ready
    log_info "Waiting for Crossplane pod to be ready..."
    kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=crossplane -n "$CROSSPLANE_NAMESPACE" --timeout=300s

    log_success "Crossplane installed successfully"
}

# Step 2: Install Provider Packages
install_providers() {
    if $SKIP_PROVIDERS; then
        log_info "Skipping provider installation (--skip-providers flag)"
        return 0
    fi

    if $DRY_RUN; then
        log_info "[DRY RUN] Would install cloud provider packages"
        return 0
    fi

    log_info "Installing cloud provider packages..."

    # Install AWS provider
    log_info "Installing AWS provider..."
    kubectl install provider-aws "$PROVIDERS_VERSION" --namespace "$CROSSPLANE_NAMESPACE" || true
    kubectl wait --for=condition=Healthy provider.pkg.crossplane.io/provider-aws -n "$CROSSPLANE_NAMESPACE" --timeout=300s || log_warn "AWS provider health check timed out, continuing..."

    # Install Azure provider (slightly different version)
    log_info "Installing Azure provider..."
    AZURE_VERSION="${PROVIDERS_VERSION/v/}"  # Remove 'v' prefix if present
    kubectl install provider-azure "v0.44.0" --namespace "$CROSSPLANE_NAMESPACE" || true
    kubectl wait --for=condition=Healthy provider.pkg.crossplane.io/provider-azure -n "$CROSSPLANE_NAMESPACE" --timeout=300s || log_warn "Azure provider health check timed out, continuing..."

    # Install GCP provider
    log_info "Installing GCP provider..."
    kubectl install provider-gcp "v0.38.0" --namespace "$CROSSPLANE_NAMESPACE" || true
    kubectl wait --for=condition=Healthy provider.pkg.crossplane.io/provider-gcp -n "$CROSSPLANE_NAMESPACE" --timeout=300s || log_warn "GCP provider health check timed out, continuing..."

    # Verify all providers are healthy
    log_info "Checking provider health status..."
    kubectl get providers.pkg.crossplane.io -n "$CROSSPLANE_NAMESPACE"

    log_success "Provider packages installed"
}

# Step 3: Configure Provider Credentials
configure_providers() {
    if $DRY_RUN; then
        log_info "[DRY RUN] Would configure provider credentials"
        return 0
    fi

    log_info "Configuring provider credentials..."

    # Check for credential files
    local aws_creds_file="secrets/aws-credentials"
    local azure_creds_file="secrets/azure-service-principal.json"
    local gcp_creds_file="secrets/gcp-service-account-key.json"

    # AWS
    if [[ -f "$aws_creds_file" ]]; then
        log_info "Creating AWS credentials secret..."
        kubectl create secret generic aws-creds \
            --namespace "$CROSSPLANE_NAMESPACE" \
            --from-file=key="$aws_creds_file" \
            --dry-run=client -o yaml | kubectl apply -f -
        log_success "AWS credentials configured"
    else
        log_warn "AWS credentials file not found: $aws_creds_file"
        log_warn "Create it with: kubectl create secret generic aws-creds -n $CROSSPLANE_NAMESPACE --from-file=key=./secrets/aws-credentials"
    fi

    # Azure
    if [[ -f "$azure_creds_file" ]]; then
        log_info "Creating Azure credentials secret..."
        kubectl create secret generic azure-creds \
            --namespace "$CROSSPLANE_NAMESPACE" \
            --from-file=key="$azure_creds_file" \
            --dry-run=client -o yaml | kubectl apply -f -
        log_success "Azure credentials configured"
    else
        log_warn "Azure credentials file not found: $azure_creds_file"
        log_warn "Create it with: kubectl create secret generic azure-creds -n $CROSSPLANE_NAMESPACE --from-file=key=./secrets/azure-service-principal.json"
    fi

    # GCP
    if [[ -f "$gcp_creds_file" ]]; then
        log_info "Creating GCP credentials secret..."
        kubectl create secret generic gcp-creds \
            --namespace "$CROSSPLANE_NAMESPACE" \
            --from-file=key="$gcp_creds_file" \
            --dry-run=client -o yaml | kubectl apply -f -
        log_success "GCP credentials configured"
    else
        log_warn "GCP credentials file not found: $gcp_creds_file"
        log_warn "Create it with: kubectl create secret generic gcp-creds -n $CROSSPLANE_NAMESPACE --from-file=key=./secrets/gcp-service-account-key.json"
    fi

    # Apply ProviderConfigs
    log_info "Applying ProviderConfig resources..."
    kubectl apply -f core/crossplane/providers/

    # Wait for ProviderConfigs to be ready
    log_info "Waiting for ProviderConfigs to be ready..."
    kubectl wait --for=condition=Ready providerconfig.aws.crossplane.io/aws-provider --timeout=300s || log_warn "AWS ProviderConfig not ready"
    kubectl wait --for=condition=Ready providerconfig.azure.crossplane.io/azure-provider --timeout=300s || log_warn "Azure ProviderConfig not ready"
    kubectl wait --for=condition=Ready providerconfig.gcp.crossplane.io/gcp-provider --timeout=300s || log_warn "GCP ProviderConfig not ready"

    log_success "Provider configuration complete"
}

# Step 4: Setup RBAC and Team Namespaces
setup_rbac() {
    if $DRY_RUN; then
        log_info "[DRY RUN] Would setup RBAC and team namespaces"
        return 0
    fi

    log_info "Setting up RBAC and team namespaces..."

    # Create team namespaces
    for ns in "${TEAM_NAMESPACES[@]}"; do
        log_info "Creating namespace: $ns"
        kubectl create namespace "$ns" --dry-run=client -o yaml | kubectl apply -f -
    done

    # Apply RBAC configurations
    log_info "Applying ServiceAccounts..."
    kubectl apply -f core/crossplane/rbac/teams-sa.yaml

    log_info "Applying team Roles and RoleBindings..."
    kubectl apply -f core/crossplane/rbac/team-a-role.yaml
    kubectl apply -f core/crossplane/rbac/team-b-role.yaml
    kubectl apply -f core/crossplane/rbac/team-c-role.yaml

    log_info "Applying cluster admin roles..."
    kubectl apply -f core/crossplane/rbac/cluster-admin-roles.yaml

    log_info "Applying NetworkPolicies..."
    kubectl apply -f core/crossplane/rbac/network-policies.yaml

    # Verify RBAC
    log_info "Verifying RBAC permissions..."
    kubectl auth can-i list eksclusters.eks.aws.crossplane.io --as=system:serviceaccount:team-a:team-a-sa --namespace=team-a
    kubectl auth can-i list kubernetesclusters.platform.azure --as=system:serviceaccount:team-b:team-b-sa --namespace=team-b

    log_success "RBAC and team namespaces configured"
}

# Step 5: Deploy XRDs and Compositions
deploy_compositions() {
    if $DRY_RUN; then
        log_info "[DRY RUN] Would deploy XRDs and Compositions"
        return 0
    fi

    if $ONLY_RBAC; then
        log_info "Skipping compositions (--only-rbac flag)"
        return 0
    fi

    log_info "Deploying XRDs and Compositions..."

    # Deploy in order: providers should be healthy before compositions

    # AWS compositions
    log_info "Deploying AWS EKS composition..."
    kubectl apply -f core/crossplane/compositions/aws-eks-cluster/

    log_info "Deploying AWS RDS composition..."
    kubectl apply -f core/crossplane/compositions/aws-rds-postgresql/

    log_info "Deploying AWS S3 composition..."
    kubectl apply -f core/crossplane/compositions/shared-storage/

    # Azure compositions
    log_info "Deploying Azure AKS composition..."
    kubectl apply -f core/crossplane/compositions/azure-aks-cluster/

    log_info "Deploying Azure PostgreSQL composition..."
    kubectl apply -f core/crossplane/compositions/azure-postgresql/

    # GCP compositions
    log_info "Deploying GCP GKE composition..."
    kubectl apply -f core/crossplane/compositions/gcp-gke-cluster/

    log_info "Deploying GCP Cloud SQL composition..."
    kubectl apply -f core/crossplane/compositions/gcp-cloudsql-postgresql/

    log_info "Deploying GCP Redis composition..."
    kubectl apply -f core/crossplane/compositions/gcp-memorystore/

    # Wait for XRDs to be established
    log_info "Waiting for XRDs to be established..."
    kubectl wait --for=condition=Established xrd --all --timeout=300s || log_warn "Some XRDs may not be established yet"

    # Check composition status
    log_info "Checking composition status..."
    kubectl get compositions.apiextensions.crossplane.io

    log_success "XRDs and Compositions deployed"
}

# Step 6: Setup GitOps Sync
setup_gitops() {
    if $SKIP_GITOPS; then
        log_info "Skipping GitOps setup (--skip-gitops flag)"
        return 0
    fi

    if $DRY_RUN; then
        log_info "[DRY RUN] Would setup GitOps sync (Flux/ArgoCD)"
        return 0
    fi

    log_info "Setting up GitOps sync..."

    # Check if Flux is installed
    if kubectl get namespace flux-system &> /dev/null; then
        log_info "Flux detected, creating Flux resources..."

        # Create GitRepository source
        log_info "Creating Flux GitRepository..."
        cat <<EOF | kubectl apply -f -
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: crossplane-config
  namespace: flux-system
spec:
  interval: 5m
  url: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^.]*\).*/\1/')/agentic-reconciliation-engine.git
  ref:
    branch: main
  secretRef:
    name: flux-git-deploy-key
  ignore: |
    # exclude all
    /*
    # include only crossplane directory
    !/core/crossplane/
EOF

        # Create Kustomization
        log_info "Creating Flux Kustomization..."
        cat <<EOF | kubectl apply -f -
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: crossplane-resources
  namespace: flux-system
spec:
  interval: 5m
  path: ./core/crossplane
  prune: true
  sourceRef:
    kind: GitRepository
    name: crossplane-config
  targetNamespace: crossplane-system
  dependsOn:
    - name: crossplane-namespace
      namespace: flux-system
EOF

    # Check if ArgoCD is installed
    elif kubectl get namespace argocd &> /dev/null; then
        log_info "ArgoCD detected, creating Application..."
        kubectl apply -f core/crossplane/gitops-sync.yaml
    else
        log_warn "Neither Flux nor ArgoCD detected. Skipping GitOps setup."
        log_warn "Install Flux or ArgoCD first, then manually apply core/crossplane/gitops-sync.yaml"
        return 1
    fi

    log_success "GitOps sync configured"
}

# Step 7: Validate Installation
validate_installation() {
    if $DRY_RUN; then
        log_info "[DRY RUN] Would validate installation"
        return 0
    fi

    log_info "Validating installation..."

    local errors=0

    # Check Crossplane pod
    if ! kubectl get pod -n "$CROSSPLANE_NAMESPACE" -l app.kubernetes.io/name=crossplane | grep -q Running; then
        log_error "Crossplane pod is not running"
        ((errors++))
    fi

    # Check providers
    for provider in aws azure gcp; do
        if ! kubectl get providerpkg -n "$CROSSPLANE_NAMESPACE" | grep -q "provider-$provider.*HEALTHY"; then
            log_warn "Provider $provider is not healthy"
        fi
    done

    # Check ProviderConfigs
    for provider in aws azure gcp; do
        if ! kubectl get providerconfig."${provider}".crossplane.io -n "$CROSSPLANE_NAMESPACE" 2>/dev/null | grep -q Ready; then
            log_warn "ProviderConfig for $provider is not ready (credentials may be missing)"
        fi
    done

    # Check team namespaces
    for ns in "${TEAM_NAMESPACES[@]}"; do
        if ! kubectl get namespace "$ns" &> /dev/null; then
            log_error "Team namespace $ns not found"
            ((errors++))
        fi
    done

    # Check XRDs
    local xrd_count=$(kubectl get xrd --ignore-not-found=true | wc -l)
    if [[ $xrd_count -lt 8 ]]; then
        log_warn "Expected at least 8 XRDs, found $xrd_count"
    fi

    # Check Compositions
    local comp_count=$(kubectl get compositions --ignore-not-found=true | wc -l)
    if [[ $comp_count -lt 8 ]]; then
        log_warn "Expected at least 8 Compositions, found $comp_count"
    fi

    if [[ $errors -gt 0 ]]; then
        log_error "Validation failed with $errors errors"
        return 1
    else
        log_success "Installation validated successfully"
    fi
}

# Step 8: Print Next Steps
print_next_steps() {
    log_info "=========================================="
    log_info "Crossplane installation complete!"
    log_info "=========================================="
    echo
    log_info "Next steps:"
    echo "  1. Verify all providers show READY: True"
    echo "     kubectl get providerconfigs.aws.crossplane.io"
    echo
    echo "  2. Test with a sample claim:"
    echo "     kubectl apply -f core/crossplane/compositions/example-claims.yaml"
    echo
    echo "  3. Watch resources being created:"
    echo "     kubectl get managed -A -w"
    echo
    echo "  4. View team claims:"
    echo "     kubectl get eksclusterclaims.platform.aws.ecs.azure -n team-a"
    echo
    echo "  5. Check connection secrets:"
    echo "     kubectl get secret -n team-a"
    echo
    echo "  6. Review Crossplane logs if needed:"
    echo "     kubectl logs -n crossplane-system deployment/crossplane -c crossplane"
    echo
    log_info "Migration plan: See docs/CROSSPLANE-IMPLEMENTATION-PLAN.md"
    log_info "Phase 1 (Storage) → Phase 2 (Databases) → Phase 3 (Clusters)"
    echo
    log_warn "IMPORTANT: Before migrating production resources:"
    echo "  - Ensure provider credentials are correct"
    echo "  - Test with non-production workloads first"
    echo "  - Keep Terraform state files (for rollback)"
    echo "  - Follow the phased migration plan"
}

# Main execution
main() {
    log_info "Starting Crossplane migration automation..."
    echo

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --skip-providers)
                SKIP_PROVIDERS=true
                shift
                ;;
            --skip-gitops)
                SKIP_GITOPS=true
                shift
                ;;
            --only-rbac)
                ONLY_RBAC=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Usage: $0 [--dry-run] [--skip-providers] [--skip-gitops] [--only-rbac]"
                exit 1
                ;;
        esac
    done

    if $DRY_RUN; then
        log_warn "RUNNING IN DRY-RUN MODE - No changes will be made"
        echo
    fi

    check_prerequisites

    if ! $ONLY_RBAC; then
        install_crossplane
        install_providers
        configure_providers
    fi

    setup_rbac
    deploy_compositions
    setup_gitops
    validate_installation
    print_next_steps

    log_success "Migration automation completed!"
}

# Run main function
main "$@"

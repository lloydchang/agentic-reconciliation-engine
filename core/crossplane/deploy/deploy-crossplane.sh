#!/bin/bash
# Deploy Simplified Crossplane Single Control Plane
# This script deploys the unified Crossplane instance with multi-cloud support

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="crossplane-system"
TEAM_NAMESPACES=("team-a" "team-b")
CLOUD_PROVIDERS=("aws" "azure" "gcp")

# Functions
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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check helm
    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed"
        exit 1
    fi
    
    # Check cluster access
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot access Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create namespaces
create_namespaces() {
    log_info "Creating namespaces..."
    
    # Create Crossplane namespace
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Create team namespaces
    for team in "${TEAM_NAMESPACES[@]}"; do
        kubectl create namespace $team --dry-run=client -o yaml | kubectl apply -f -
        log_success "Created namespace: $team"
    done
    
    log_success "All namespaces created"
}

# Deploy Crossplane
deploy_crossplane() {
    log_info "Deploying Crossplane..."
    
    # Add Crossplane Helm repository
    helm repo add crossplane-stable https://charts.crossplane.io/stable
    helm repo update
    
    # Install Crossplane
    helm upgrade --install crossplane crossplane-stable/crossplane \
        --namespace $NAMESPACE \
        --create-namespace \
        --set rbac.create=true \
        --set securityContext.runAsUser=2000 \
        --set securityContext.runAsGroup=2000 \
        --set resourcesCrossplane.limits.cpu=1000m \
        --set resourcesCrossplane.limits.memory=1Gi \
        --set resourcesCrossplane.requests.cpu=100m \
        --set resourcesCrossplane.requests.memory=128Mi \
        --set resourcesRBACManager.limits.cpu=500m \
        --set resourcesRBACManager.limits.memory=512Mi \
        --set resourcesRBACManager.requests.cpu=100m \
        --set resourcesRBACManager.requests.memory=128Mi \
        --wait \
        --timeout=10m
    
    log_success "Crossplane deployed successfully"
}

# Deploy providers
deploy_providers() {
    log_info "Deploying Crossplane providers..."
    
    # Apply unified provider configurations
    kubectl apply -f core/crossplane/providers/unified-providers.yaml
    
    log_success "Providers deployed"
}

# Deploy RBAC and team isolation
deploy_rbac() {
    log_info "Deploying RBAC and team isolation..."
    
    kubectl apply -f core/crossplane/rbac/team-isolation.yaml
    
    log_success "RBAC and team isolation deployed"
}

# Deploy compositions
deploy_compositions() {
    log_info "Deploying multi-cloud compositions..."
    
    kubectl apply -f core/crossplane/compositions/multi-cloud-network-complete.yaml
    kubectl apply -f core/crossplane/compositions/multi-cloud-compute-complete.yaml
    kubectl apply -f core/crossplane/compositions/multi-cloud-storage-complete.yaml
    
    log_success "Multi-cloud compositions deployed"
}

# Deploy XRDs
deploy_xrds() {
    log_info "Deploying Composite Resource Definitions..."
    
    kubectl apply -f core/crossplane/xrds/xnetwork.yaml
    kubectl apply -f core/crossplane/xrds/xcompute.yaml
    kubectl apply -f core/crossplane/xrds/xstorage.yaml
    
    log_success "XRDs deployed"
}

# Setup team credentials (placeholder - actual secrets should be created separately)
setup_team_credentials() {
    log_info "Setting up team credential placeholders..."
    
    for team in "${TEAM_NAMESPACES[@]}"; do
        for provider in "${CLOUD_PROVIDERS[@]}"; do
            # Create placeholder secrets (these should be replaced with actual credentials)
            cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: ${provider}-credentials
  namespace: ${team}
  labels:
    app.kubernetes.io/name: crossplane
    app.kubernetes.io/team: ${team}
    app.kubernetes.io/provider: ${provider}
type: Opaque
stringData:
  credentials: |
    # Placeholder - replace with actual ${provider} credentials
    # For AWS: access_key_id and secret_access_key
    # For Azure: client_id, client_secret, subscription_id, tenant_id
    # For GCP: project_id and service account key
EOF
        done
    done
    
    log_warning "Team credential placeholders created - please replace with actual credentials"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Wait for Crossplane to be ready
    kubectl wait --for=condition=available deployment/crossplane -n $NAMESPACE --timeout=300s
    
    # Check providers
    log_info "Checking provider status..."
    kubectl get providers -n $NAMESPACE
    
    # Check XRDs
    log_info "Checking XRDs..."
    kubectl get compositeresourcedefinitions
    
    # Check compositions
    log_info "Checking compositions..."
    kubectl get compositions
    
    # Check team namespaces
    log_info "Checking team namespaces..."
    for team in "${TEAM_NAMESPACES[@]}"; do
        kubectl get namespace $team
    done
    
    log_success "Deployment verification completed"
}

# Create sample resources
create_sample_resources() {
    log_info "Creating sample resources for testing..."
    
    # Create sample network for team-a
    cat <<EOF | kubectl apply -f -
apiVersion: platform.example.com/v1alpha1
kind: Network
metadata:
  name: sample-network
  namespace: team-a
  labels:
    app.kubernetes.io/team: team-a
    app.kubernetes.io/managed-by: crossplane
spec:
  provider: aws
  region: us-west-2
  cidrBlock: 10.0.0.0/16
  subnetCount: 3
  enableDnsHostnames: true
  enableDnsSupport: true
  tags:
    Environment: test
    Team: team-a
    Purpose: sample
EOF

    # Create sample compute for team-a
    cat <<EOF | kubectl apply -f -
apiVersion: platform.example.com/v1alpha1
kind: Compute
metadata:
  name: sample-compute
  namespace: team-a
  labels:
    app.kubernetes.io/team: team-a
    app.kubernetes.io/managed-by: crossplane
spec:
  provider: aws
  region: us-west-2
  instanceType: t3.micro
  minCount: 1
  maxCount: 1
  monitoring: true
  tags:
    Environment: test
    Team: team-a
    Purpose: sample
EOF

    # Create sample storage for team-a
    cat <<EOF | kubectl apply -f -
apiVersion: platform.example.com/v1alpha1
kind: Storage
metadata:
  name: sample-storage
  namespace: team-a
  labels:
    app.kubernetes.io/team: team-a
    app.kubernetes.io/managed-by: crossplane
spec:
  provider: aws
  region: us-west-2
  bucketName: team-a-sample-storage
  storageClass: standard
  versioning: false
  encryption: true
  accessControl: private
  tags:
    Environment: test
    Team: team-a
    Purpose: sample
EOF

    log_success "Sample resources created in team-a namespace"
}

# Main deployment function
main() {
    log_info "Starting simplified Crossplane deployment..."
    
    check_prerequisites
    create_namespaces
    deploy_crossplane
    deploy_providers
    deploy_rbac
    deploy_xrds
    deploy_compositions
    setup_team_credentials
    verify_deployment
    
    # Optional: Create sample resources for testing
    if [[ "${CREATE_SAMPLES:-false}" == "true" ]]; then
        create_sample_resources
    fi
    
    log_success "Simplified Crossplane deployment completed successfully!"
    log_info "Next steps:"
    log_info "1. Replace placeholder team credentials with actual cloud credentials"
    log_info "2. Test resource creation using the simplified orchestrator"
    log_info "3. Monitor resource status with: kubectl get networks,computes,storages -A"
    log_info "4. Check Crossplane status with: kubectl get providers -n crossplane-system"
}

# Help function
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  --create-samples        Create sample resources for testing"
    echo "  --skip-prerequisites    Skip prerequisite checks"
    echo ""
    echo "Environment Variables:"
    echo "  CREATE_SAMPLES=true     Create sample resources"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --create-samples)
            CREATE_SAMPLES=true
            shift
            ;;
        --skip-prerequisites)
            SKIP_PREREQUISITES=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run main function
main

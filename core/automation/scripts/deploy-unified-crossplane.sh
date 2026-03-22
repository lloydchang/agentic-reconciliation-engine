#!/bin/bash

# Unified Crossplane Deployment Script
# Deploys single Crossplane instance with smart provider selection and team isolation

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="crossplane-system"
TEAM_A_NAMESPACE="team-a"
TEAM_B_NAMESPACE="team-b"
TIMEOUT=300s

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check helm (optional)
    if command -v helm &> /dev/null; then
        log_info "Helm is available"
    else
        log_warning "Helm not found, will use kubectl manifests only"
    fi
    
    log_success "Prerequisites check completed"
}

# Create namespaces
create_namespaces() {
    log_info "Creating namespaces..."
    
    kubectl apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: ${NAMESPACE}
  labels:
    name: ${NAMESPACE}
    control-plane: unified
    component: crossplane
---
apiVersion: v1
kind: Namespace
metadata:
  name: ${TEAM_A_NAMESPACE}
  labels:
    name: ${TEAM_A_NAMESPACE}
    isolation: namespace
    managed-by: crossplane
---
apiVersion: v1
kind: Namespace
metadata:
  name: ${TEAM_B_NAMESPACE}
  labels:
    name: ${TEAM_B_NAMESPACE}
    isolation: namespace
    managed-by: crossplane
EOF
    
    log_success "Namespaces created"
}

# Deploy Crossplane
deploy_crossplane() {
    log_info "Deploying Crossplane..."
    
    # Install Crossplane using helm if available, otherwise use manifests
    if command -v helm &> /dev/null; then
        # Add Crossplane helm repository
        helm repo add crossplane https://charts.crossplane.io/stable 2>/dev/null || true
        helm repo update
        
        # Install Crossplane
        helm upgrade --install crossplane crossplane/crossplane \
            --namespace ${NAMESPACE} \
            --create-namespace \
            --wait \
            --timeout ${TIMEOUT}
    else
        # Fallback to kubectl manifests (would need to be pre-downloaded)
        log_warning "Helm not available, please install Crossplane manually"
        return 1
    fi
    
    log_success "Crossplane deployed"
}

# Install Crossplane providers
install_providers() {
    log_info "Installing Crossplane providers..."

    kubectl apply -f overlay/crossplane/unified/crossplane-install.yaml

    # Wait for providers to be installed (non-blocking, 30s timeout for dev)
    log_info "Waiting for providers to be ready (short timeout for development)..."
    if kubectl wait --for=condition=healthy provider --all --namespace ${NAMESPACE} --timeout=30s 2>/dev/null; then
        log_success "All providers healthy"
    else
        log_warning "Provider health check timed out or failed - continuing anyway (providers need credentials for full health)"
    fi

    log_success "Crossplane providers installed (proceeding with deployment)"
}

# Create provider configurations with team isolation
create_provider_configs() {
    log_info "Creating provider configurations with team isolation..."
    
    # Create secrets for team credentials (in real implementation, these would be properly secured)
    kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: aws-team-a-credentials
  namespace: ${TEAM_A_NAMESPACE}
type: Opaque
stringData:
  credentials: |
    [default]
    aws_access_key_id = \${AWS_ACCESS_KEY_ID}
    aws_secret_access_key = \${AWS_SECRET_ACCESS_KEY}
---
apiVersion: v1
kind: Secret
metadata:
  name: aws-team-b-credentials
  namespace: ${TEAM_B_NAMESPACE}
type: Opaque
stringData:
  credentials: |
    [default]
    aws_access_key_id = \${AWS_ACCESS_KEY_ID}
    aws_secret_access_key = \${AWS_SECRET_ACCESS_KEY}
---
apiVersion: v1
kind: Secret
metadata:
  name: azure-team-a-credentials
  namespace: ${TEAM_A_NAMESPACE}
type: Opaque
stringData:
  credentials: |
    {
      "tenantId": "\${AZURE_TENANT_ID}",
      "subscriptionId": "\${AZURE_SUBSCRIPTION_ID}",
      "clientId": "\${AZURE_CLIENT_ID}",
      "clientSecret": "\${AZURE_CLIENT_SECRET}"
    }
---
apiVersion: v1
kind: Secret
metadata:
  name: azure-team-b-credentials
  namespace: ${TEAM_B_NAMESPACE}
type: Opaque
stringData:
  credentials: |
    {
      "tenantId": "\${AZURE_TENANT_ID}",
      "subscriptionId": "\${AZURE_SUBSCRIPTION_ID}",
      "clientId": "\${AZURE_CLIENT_ID}",
      "clientSecret": "\${AZURE_CLIENT_SECRET}"
    }
---
apiVersion: v1
kind: Secret
metadata:
  name: gcp-team-a-credentials
  namespace: ${TEAM_A_NAMESPACE}
type: Opaque
stringData:
  credentials: |
    \${GCP_SERVICE_ACCOUNT_KEY}
---
apiVersion: v1
kind: Secret
metadata:
  name: gcp-team-b-credentials
  namespace: ${TEAM_B_NAMESPACE}
type: Opaque
stringData:
  credentials: |
    \${GCP_SERVICE_ACCOUNT_KEY}
EOF
    
    # Apply provider configurations
    kubectl apply -f overlay/crossplane/unified/provider-configs-isolated.yaml
    
    log_success "Provider configurations created"
}

# Setup RBAC
setup_rbac() {
    log_info "Setting up RBAC for team isolation..."
    
    kubectl apply -f overlay/crossplane/unified/rbac.yaml
    
    log_success "RBAC setup completed"
}

# Deploy composite resources and compositions
deploy_composite_resources() {
    log_info "Deploying composite resources and compositions..."
    
    # Deploy XRDs
    kubectl apply -f overlay/crossplane/unified/composite-resources-unified.yaml
    
    # Deploy compositions
    kubectl apply -f overlay/crossplane/unified/compositions/smart-multi-cloud-compute.yaml
    kubectl apply -f overlay/crossplane/unified/compositions/cross-cloud-failover.yaml
    kubectl apply -f overlay/crossplane/unified/compositions/cost-optimized-storage.yaml
    
    log_success "Composite resources and compositions deployed"
}

# Deploy sample resources
deploy_sample_resources() {
    log_info "Deploying sample resources..."
    
    kubectl apply -f overlay/crossplane/unified/examples/unified-sample-resources.yaml
    
    log_success "Sample resources deployed"
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Check if monitoring namespace exists
    if ! kubectl get namespace monitoring &> /dev/null; then
        log_info "Creating monitoring namespace..."
        kubectl create namespace monitoring
    fi
    
    # Apply monitoring configuration
    kubectl apply -f overlay/crossplane/unified/monitoring/unified-monitoring.yaml
    
    log_success "Monitoring setup completed"
}

# Setup GitOps (optional)
setup_gitops() {
    log_info "Setting up GitOps configuration..."
    
    # Check if Flux is installed
    if ! kubectl get namespace flux-system &> /dev/null; then
        log_warning "Flux not found, skipping GitOps setup"
        return 0
    fi
    
    kubectl apply -f overlay/crossplane/unified/gitops/unified-gitops.yaml
    
    log_success "GitOps configuration applied"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check Crossplane pods
    log_info "Checking Crossplane pods..."
    kubectl get pods -n ${NAMESPACE}
    
    # Check providers
    log_info "Checking providers..."
    kubectl get providers -n ${NAMESPACE}
    
    # Check provider configs
    log_info "Checking provider configs..."
    kubectl get providerconfigs --all-namespaces
    
    # Check composite resources
    log_info "Checking composite resources..."
    kubectl get xnetworks,xcomputes,xstorages --all-namespaces
    
    # Check sample resources
    log_info "Checking sample resources..."
    kubectl get xnetworks,xcomputes,xstorages -n ${TEAM_A_NAMESPACE}
    kubectl get xnetworks,xcomputes,xstorages -n ${TEAM_B_NAMESPACE}
    
    log_success "Deployment verification completed"
}

# Test unified orchestrator
test_orchestrator() {
    log_info "Testing unified orchestrator..."
    
    # Test basic functionality
    python3 core/scripts/automation/unified_crossplane_orchestrator.py --action status
    
    log_success "Orchestrator test completed"
}

# Cleanup function
cleanup() {
    log_warning "Cleaning up deployment..."
    
    # Delete sample resources
    kubectl delete -f overlay/crossplane/unified/examples/unified-sample-resources.yaml --ignore-not-found=true
    
    # Delete compositions
    kubectl delete -f overlay/crossplane/unified/compositions/ --ignore-not-found=true
    
    # Delete XRDs
    kubectl delete -f overlay/crossplane/unified/composite-resources-unified.yaml --ignore-not-found=true
    
    # Delete provider configs
    kubectl delete -f overlay/crossplane/unified/provider-configs-isolated.yaml --ignore-not-found=true
    
    # Delete RBAC
    kubectl delete -f overlay/crossplane/unified/rbac.yaml --ignore-not-found=true
    
    # Delete Crossplane
    if command -v helm &> /dev/null; then
        helm uninstall crossplane -n ${NAMESPACE} --ignore-not-found=true
    fi
    
    # Delete namespaces
    kubectl delete namespace ${TEAM_B_NAMESPACE} --ignore-not-found=true
    kubectl delete namespace ${TEAM_A_NAMESPACE} --ignore-not-found=true
    kubectl delete namespace ${NAMESPACE} --ignore-not-found=true
    
    log_success "Cleanup completed"
}

# Show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  deploy     - Deploy unified Crossplane architecture"
    echo "  cleanup    - Remove deployment"
    echo "  verify     - Verify deployment status"
    echo "  test       - Test orchestrator functionality"
    echo "  help       - Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
    echo "  AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET"
    echo "  GCP_SERVICE_ACCOUNT_KEY"
}

# Main function
main() {
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            create_namespaces
            deploy_crossplane
            install_providers
            create_provider_configs
            setup_rbac
            deploy_composite_resources
            deploy_sample_resources
            setup_monitoring
            setup_gitops
            verify_deployment
            test_orchestrator
            log_success "Unified Crossplane deployment completed successfully!"
            ;;
        "cleanup")
            cleanup
            ;;
        "verify")
            verify_deployment
            ;;
        "test")
            test_orchestrator
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            log_error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Trap cleanup on script exit
trap cleanup EXIT

# Run main function
main "$@"

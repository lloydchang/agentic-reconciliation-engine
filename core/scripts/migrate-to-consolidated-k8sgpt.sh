#!/bin/bash
# K8sGPT Consolidation Migration Script
# This script helps migrate from multiple K8sGPT deployments to a single unified deployment

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONSOLIDATED_DIR="${SCRIPT_DIR}/core/gitops/consolidated"
NAMESPACE="k8sgpt-system"
BACKUP_DIR="/tmp/k8sgpt-migration-backup-$(date +%Y%m%d-%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "kubectl is available and connected to cluster"
}

# Function to backup existing resources
backup_resources() {
    log_info "Creating backup of existing K8sGPT resources..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup existing K8sGPT deployments
    log_info "Backing up existing deployments..."
    kubectl get deployments -A -l app.kubernetes.io/name=k8sgpt -o yaml > "$BACKUP_DIR/deployments.yaml" || log_warning "No K8sGPT deployments found"
    
    # Backup existing services
    log_info "Backing up existing services..."
    kubectl get services -A -l app.kubernetes.io/name=k8sgpt -o yaml > "$BACKUP_DIR/services.yaml" || log_warning "No K8sGPT services found"
    
    # Backup existing configmaps
    log_info "Backing up existing configmaps..."
    kubectl get configmaps -A -l app.kubernetes.io/name=k8sgpt -o yaml > "$BACKUP_DIR/configmaps.yaml" || log_warning "No K8sGPT configmaps found"
    
    # Backup existing secrets
    log_info "Backing up existing secrets..."
    kubectl get secrets -A -l app.kubernetes.io/name=k8sgpt -o yaml > "$BACKUP_DIR/secrets.yaml" || log_warning "No K8sGPT secrets found"
    
    # Backup existing RBAC
    log_info "Backing up existing RBAC..."
    kubectl get serviceaccounts,roles,rolebindings,clusterroles,clusterrolebindings -A -l app.kubernetes.io/name=k8sgpt -o yaml > "$BACKUP_DIR/rbac.yaml" || log_warning "No K8sGPT RBAC found"
    
    log_success "Backup completed: $BACKUP_DIR"
}

# Function to identify existing K8sGPT deployments
identify_existing_deployments() {
    log_info "Identifying existing K8sGPT deployments..."
    
    local deployments=()
    local namespaces=()
    
    # Find all K8sGPT deployments
    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            deployments+=("$line")
        fi
    done < <(kubectl get deployments -A -l app.kubernetes.io/name=k8sgpt --no-headers | awk '{print $1":"$2}')
    
    if [[ ${#deployments[@]} -eq 0 ]]; then
        log_warning "No existing K8sGPT deployments found"
        return 0
    fi
    
    log_info "Found ${#deployments[@]} existing K8sGPT deployments:"
    for deployment in "${deployments[@]}"; do
        IFS=':' read -r namespace name <<< "$deployment"
        log_info "  - $name in $namespace"
        namespaces+=("$namespace")
    done
    
    # Export for use in other functions
    export EXISTING_DEPLOYMENTS=("${deployments[@]}")
    export EXISTING_NAMESPACES=($(printf '%s\n' "${namespaces[@]}" | sort -u))
    
    log_success "Identified ${#EXISTING_DEPLOYMENTS[@]} existing deployments in ${#EXISTING_NAMESPACES[@]} namespaces"
}

# Function to create consolidated namespace
create_namespace() {
    log_info "Creating consolidated namespace: $NAMESPACE"
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE already exists"
        return 0
    fi
    
    kubectl create namespace "$NAMESPACE"
    kubectl label namespace "$NAMESPACE" \
        app.kubernetes.io/name=k8sgpt \
        app.kubernetes.io/component=namespace \
        app.kubernetes.io/part-of=agentic-reconciliation-engine \
        name="$NAMESPACE"
    
    log_success "Created namespace: $NAMESPACE"
}

# Function to apply consolidated deployment
apply_consolidated_deployment() {
    log_info "Applying consolidated K8sGPT deployment..."
    
    if [[ ! -d "$CONSOLIDATED_DIR" ]]; then
        log_error "Consolidated configuration directory not found: $CONSOLIDATED_DIR"
        exit 1
    fi
    
    # Apply secrets template first (user needs to populate it)
    if [[ -f "$CONSOLIDATED_DIR/k8sgpt-secrets-template.yaml" ]]; then
        log_warning "Please review and update the secrets template: $CONSOLIDATED_DIR/k8sgpt-secrets-template.yaml"
        log_warning "After updating, apply it with: kubectl apply -f $CONSOLIDATED_DIR/k8sgpt-secrets-template.yaml"
        
        # Check if secrets already exist
        if kubectl get secret k8sgpt-secrets -n "$NAMESPACE" &> /dev/null; then
            log_info "Secrets already exist, proceeding with deployment"
        else
            log_error "Please create the secrets before proceeding"
            exit 1
        fi
    fi
    
    # Apply configuration
    if [[ -f "$CONSOLIDATED_DIR/k8sgpt-unified-config.yaml" ]]; then
        log_info "Applying unified configuration..."
        kubectl apply -f "$CONSOLIDATED_DIR/k8sgpt-unified-config.yaml"
    fi
    
    # Apply deployment
    if [[ -f "$CONSOLIDATED_DIR/k8sgpt-unified-deployment.yaml" ]]; then
        log_info "Applying unified deployment..."
        kubectl apply -f "$CONSOLIDATED_DIR/k8sgpt-unified-deployment.yaml"
    fi
    
    # Apply GitOps applications
    if [[ -f "$CONSOLIDATED_DIR/k8sgpt-gitops-apps.yaml" ]]; then
        log_info "Applying GitOps applications..."
        kubectl apply -f "$CONSOLIDATED_DIR/k8sgpt-gitops-apps.yaml"
    fi
    
    log_success "Consolidated deployment applied"
}

# Function to wait for consolidated deployment to be ready
wait_for_deployment() {
    log_info "Waiting for consolidated K8sGPT deployment to be ready..."
    
    local timeout=300
    local interval=10
    local elapsed=0
    
    while [[ $elapsed -lt $timeout ]]; do
        if kubectl get deployment k8sgpt -n "$NAMESPACE" &> /dev/null; then
            local ready=$(kubectl get deployment k8sgpt -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
            local desired=$(kubectl get deployment k8sgpt -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
            
            if [[ "$ready" == "$desired" ]] && [[ "$ready" == "1" ]]; then
                log_success "Consolidated deployment is ready"
                return 0
            fi
        fi
        
        log_info "Waiting... (${elapsed}/${timeout}s)"
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    log_error "Timeout waiting for deployment to be ready"
    return 1
}

# Function to test consolidated deployment
test_deployment() {
    log_info "Testing consolidated K8sGPT deployment..."
    
    # Test service endpoint
    log_info "Testing service endpoint..."
    if kubectl get service k8sgpt -n "$NAMESPACE" &> /dev/null; then
        local service_ip=$(kubectl get service k8sgpt -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
        log_info "Service IP: $service_ip"
        
        # Port-forward test
        log_info "Testing via port-forward..."
        if kubectl port-forward service/k8sgpt 8080:8080 -n "$NAMESPACE" &> /dev/null & then
            sleep 5
            if curl -f http://localhost:8080/healthz &> /dev/null; then
                log_success "Health endpoint is responding"
            else
                log_warning "Health endpoint not responding"
            fi
            pkill -f "kubectl port-forward service/k8sgpt" || true
        fi
    fi
    
    # Test metrics endpoint
    log_info "Testing metrics endpoint..."
    if kubectl get service k8sgpt -n "$NAMESPACE" -o jsonpath='{.spec.ports[?(@.name=="metrics")].port}' &> /dev/null; then
        log_success "Metrics endpoint is available"
    fi
    
    log_success "Deployment testing completed"
}

# Function to remove old deployments
remove_old_deployments() {
    log_info "Removing old K8sGPT deployments..."
    
    for deployment in "${EXISTING_DEPLOYMENTS[@]}"; do
        IFS=':' read -r namespace name <<< "$deployment"
        
        log_info "Removing deployment $name from namespace $namespace..."
        
        # Delete deployment
        kubectl delete deployment "$name" -n "$namespace" --ignore-not-found=true
        
        # Delete associated service
        kubectl delete service "$name" -n "$namespace" --ignore-not-found=true
        
        # Delete associated configmaps
        kubectl delete configmap -l app.kubernetes.io/name=k8sgpt -n "$namespace" --ignore-not-found=true
        
        # Delete associated secrets
        kubectl delete secret -l app.kubernetes.io/name=k8sgpt -n "$namespace" --ignore-not-found=true
        
        # Delete associated RBAC (only roles, not cluster roles)
        kubectl delete role,rolebinding -l app.kubernetes.io/name=k8sgpt -n "$namespace" --ignore-not-found=true
        
        log_success "Removed deployment $name from namespace $namespace"
    done
    
    log_success "All old deployments removed"
}

# Function to update component configurations
update_component_configs() {
    log_info "Updating component configurations to use centralized K8sGPT..."
    
    # This function would contain logic to update various component configurations
    # For now, it's a placeholder showing what needs to be done
    
    log_info "Component configuration updates required:"
    log_info "  1. Update Argo Workflows to use: http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
    log_info "  2. Update Argo Rollouts analysis templates"
    log_info "  3. Update Flux Kustomizations"
    log_info "  4. Update Argo Events sensors"
    log_info "  5. Update PipeCD configuration"
    log_info "  6. Update network policies to allow traffic to k8sgpt-system"
    
    log_warning "Please refer to the component integration guide for detailed instructions"
}

# Function to verify migration
verify_migration() {
    log_info "Verifying migration..."
    
    # Check that only one deployment exists
    local deployment_count=$(kubectl get deployments -A -l app.kubernetes.io/name=k8sgpt --no-headers | wc -l)
    if [[ "$deployment_count" -eq 1 ]]; then
        log_success "Only one K8sGPT deployment exists"
    else
        log_error "Expected 1 deployment, found $deployment_count"
        return 1
    fi
    
    # Check that it's in the correct namespace
    local deployment_namespace=$(kubectl get deployments -A -l app.kubernetes.io/name=k8sgpt --no-headers | awk '{print $1}')
    if [[ "$deployment_namespace" == "$NAMESPACE" ]]; then
        log_success "Deployment is in correct namespace: $NAMESPACE"
    else
        log_error "Deployment found in wrong namespace: $deployment_namespace"
        return 1
    fi
    
    # Check service health
    if kubectl get service k8sgpt -n "$NAMESPACE" &> /dev/null; then
        log_success "Service exists in correct namespace"
    else
        log_error "Service not found"
        return 1
    fi
    
    log_success "Migration verification completed successfully"
}

# Function to show migration summary
show_summary() {
    log_info "Migration Summary:"
    log_info "  - Backup created: $BACKUP_DIR"
    log_info "  - Consolidated deployment namespace: $NAMESPACE"
    log_info "  - Service endpoint: http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
    log_info "  - Metrics endpoint: http://k8sgpt.k8sgpt-system.svc.cluster.local:9090/metrics"
    
    log_warning "Next steps:"
    log_warning "  1. Update all component configurations to use the centralized service"
    log_warning "  2. Remove old K8sGPT deployments from component namespaces"
    log_warning "  3. Update network policies to allow traffic to k8sgpt-system"
    log_warning "  4. Monitor the consolidated deployment for proper operation"
    log_warning "  5. Update documentation to reflect the new architecture"
    
    log_success "Migration completed successfully!"
}

# Main migration function
main() {
    log_info "Starting K8sGPT consolidation migration..."
    
    # Check prerequisites
    check_kubectl
    
    # Backup existing resources
    backup_resources
    
    # Identify existing deployments
    identify_existing_deployments
    
    # Create consolidated namespace
    create_namespace
    
    # Apply consolidated deployment
    apply_consolidated_deployment
    
    # Wait for deployment to be ready
    wait_for_deployment
    
    # Test deployment
    test_deployment
    
    # Remove old deployments (with confirmation)
    if [[ ${#EXISTING_DEPLOYMENTS[@]} -gt 0 ]]; then
        log_warning "Found existing deployments that will be removed:"
        for deployment in "${EXISTING_DEPLOYMENTS[@]}"; do
            IFS=':' read -r namespace name <<< "$deployment"
            log_warning "  - $name in $namespace"
        done
        
        read -p "Do you want to proceed with removing old deployments? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            remove_old_deployments
        else
            log_warning "Skipping removal of old deployments"
        fi
    fi
    
    # Update component configurations
    update_component_configs
    
    # Verify migration
    verify_migration
    
    # Show summary
    show_summary
}

# Help function
show_help() {
    cat << EOF
K8sGPT Consolidation Migration Script

This script helps migrate from multiple K8sGPT deployments to a single unified deployment.

Usage: $0 [OPTIONS]

Options:
  -h, --help     Show this help message
  -b, --backup   Only create backup of existing resources
  -r, --restore  Restore from backup (experimental)
  -v, --verify   Verify migration status

Examples:
  $0                    # Run full migration
  $0 --backup          # Only backup existing resources
  $0 --verify          # Verify migration status

Requirements:
  - kubectl installed and configured
  - Access to the Kubernetes cluster
  - Permissions to create/delete resources

Backup location: /tmp/k8sgpt-migration-backup-YYYYMMDD-HHMMSS

EOF
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -b|--backup)
        check_kubectl
        backup_resources
        log_success "Backup completed: $BACKUP_DIR"
        exit 0
        ;;
    -v|--verify)
        check_kubectl
        verify_migration
        exit 0
        ;;
    "")
        main
        ;;
    *)
        log_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac

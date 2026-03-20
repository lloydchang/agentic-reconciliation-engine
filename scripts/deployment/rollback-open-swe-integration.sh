# Open SWE Integration Rollback Script
# Safely removes Open SWE integration components

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

NAMESPACE="ai-infrastructure"
BACKUP_DIR="/tmp/open-swe-backup-$(date +%Y%m%d-%H%M%S)"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Function to create backup
create_backup() {
    log_info "Creating backup before rollback..."

    mkdir -p "$BACKUP_DIR"

    # Backup current manifests
    kubectl get all -n "$NAMESPACE" -l component=open-swe-integration -o yaml > "$BACKUP_DIR/resources.yaml"
    kubectl get secrets -n "$NAMESPACE" -l component=open-swe-integration -o yaml > "$BACKUP_DIR/secrets.yaml"
    kubectl get configmaps -n "$NAMESPACE" -l component=open-swe-integration -o yaml > "$BACKUP_DIR/configmaps.yaml"

    log_success "Backup created at: $BACKUP_DIR"
}

# Function to scale down deployments
scale_down_deployments() {
    log_info "Scaling down Open SWE deployments..."

    # Scale gateway to 0
    kubectl scale deployment open-swe-gateway --replicas=0 -n "$NAMESPACE"

    # Wait for pods to terminate
    kubectl wait --for=delete pod -l app=open-swe-gateway -n "$NAMESPACE" --timeout=300s

    log_success "Deployments scaled down"
}

# Function to remove integration components
remove_components() {
    log_info "Removing Open SWE integration components..."

    # Remove deployment
    kubectl delete deployment open-swe-gateway -n "$NAMESPACE" --ignore-not-found=true

    # Remove services
    kubectl delete service open-swe-gateway -n "$NAMESPACE" --ignore-not-found=true
    kubectl delete service open-swe-gateway-lb -n "$NAMESPACE" --ignore-not-found=true

    # Remove RBAC
    kubectl delete rolebinding open-swe-gateway-rolebinding -n "$NAMESPACE" --ignore-not-found=true
    kubectl delete role open-swe-gateway-role -n "$NAMESPACE" --ignore-not-found=true
    kubectl delete serviceaccount open-swe-gateway-sa -n "$NAMESPACE" --ignore-not-found=true

    # Remove security policies
    kubectl delete networkpolicy open-swe-gateway-network-policy -n "$NAMESPACE" --ignore-not-found=true
    kubectl delete podsecuritypolicy open-swe-gateway-psp --ignore-not-found=true

    # Remove config
    kubectl delete configmap open-swe-gateway-config -n "$NAMESPACE" --ignore-not-found=true
    kubectl delete secret open-swe-secrets -n "$NAMESPACE" --ignore-not-found=true

    log_success "Open SWE components removed"
}

# Function to clean up GitOps configuration
cleanup_gitops() {
    log_info "Cleaning up GitOps configuration..."

    local gitops_dir="${PROJECT_ROOT}/core/gitops/open-swe-gateway"

    if [[ -d "$gitops_dir" ]]; then
        # Remove from GitOps (this will trigger reconciliation)
        rm -rf "$gitops_dir"
        log_info "Removed Open SWE manifests from GitOps directory"
    fi

    log_success "GitOps configuration cleaned up"
}

# Function to verify rollback
verify_rollback() {
    log_info "Verifying rollback..."

    # Check that pods are gone
    local remaining_pods
    remaining_pods=$(kubectl get pods -n "$NAMESPACE" -l component=open-swe-integration --no-headers | wc -l)

    if [[ "$remaining_pods" -eq 0 ]]; then
        log_success "All Open SWE pods removed"
    else
        log_warning "$remaining_pods Open SWE pods still remain"
    fi

    # Check that services are gone
    local remaining_services
    remaining_services=$(kubectl get svc -n "$NAMESPACE" -l component=open-swe-integration --no-headers | wc -l)

    if [[ "$remaining_services" -eq 0 ]]; then
        log_success "All Open SWE services removed"
    else
        log_warning "$remaining_services Open SWE services still remain"
    fi
}

# Function to display rollback summary
display_summary() {
    log_info "Open SWE Integration Rollback Summary"
    echo ""
    echo "✅ Gateway Deployment: Removed"
    echo "✅ Services: Removed"
    echo "✅ RBAC: Cleaned up"
    echo "✅ Security Policies: Removed"
    echo "✅ Config/Secrets: Removed"
    echo "✅ GitOps Config: Cleaned up"
    echo ""
    echo "📁 Backup Location: $BACKUP_DIR"
    echo ""
    echo "🔄 To restore from backup:"
    echo "  kubectl apply -f $BACKUP_DIR/resources.yaml"
    echo "  kubectl apply -f $BACKUP_DIR/secrets.yaml"
    echo "  kubectl apply -f $BACKUP_DIR/configmaps.yaml"
    echo ""
    echo "⚠️  Note: External webhook configurations in Slack/Linear/GitHub"
    echo "    will need to be manually updated or removed."
}

# Main rollback function
main() {
    log_warning "This will remove the Open SWE integration. Are you sure? (y/N)"
    read -r -p "" response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        log_info "Rollback cancelled"
        exit 0
    fi

    log_info "Starting Open SWE Integration rollback..."

    create_backup
    scale_down_deployments
    remove_components
    cleanup_gitops
    verify_rollback
    display_summary

    log_success "Open SWE Integration rollback completed successfully!"
    log_info "The integration has been safely removed. Use the backup to restore if needed."
}

# Run main function
main "$@"

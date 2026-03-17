#!/bin/bash

# Migration script to transition from separate Qwen deployments to centralized agent-memory-rust

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
NAMESPACE="${NAMESPACE:-ai-infrastructure}"
BACKUP_DIR="${BACKUP_DIR:-/tmp/qwen-migration-$(date +%s)}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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
    
    # Create backup directory
    mkdir -p "${BACKUP_DIR}"
    
    log_success "Prerequisites check passed"
}

# Backup existing configurations
backup_existing_configs() {
    log_info "Backing up existing Qwen configurations..."
    
    # Backup existing deployments
    kubectl get deployments -n "${NAMESPACE}" -l app=qwen -o yaml > "${BACKUP_DIR}/qwen-deployments.yaml" 2>/dev/null || true
    kubectl get deployments -n "${NAMESPACE}" -l component=qwen -o yaml > "${BACKUP_DIR}/qwen-component-deployments.yaml" 2>/dev/null || true
    
    # Backup existing services
    kubectl get services -n "${NAMESPACE}" -l app=qwen -o yaml > "${BACKUP_DIR}/qwen-services.yaml" 2>/dev/null || true
    kubectl get services -n "${NAMESPACE}" -l component=qwen -o yaml > "${BACKUP_DIR}/qwen-component-services.yaml" 2>/dev/null || true
    
    # Backup existing configmaps
    kubectl get configmaps -n "${NAMESPACE}" -l app=qwen -o yaml > "${BACKUP_DIR}/qwen-configmaps.yaml" 2>/dev/null || true
    kubectl get configmaps -n "${NAMESPACE}" -l component=qwen -o yaml > "${BACKUP_DIR}/qwen-component-configmaps.yaml" 2>/dev/null || true
    
    # Backup existing secrets
    kubectl get secrets -n "${NAMESPACE}" -l app=qwen -o yaml > "${BACKUP_DIR}/qwen-secrets.yaml" 2>/dev/null || true
    kubectl get secrets -n "${NAMESPACE}" -l component=qwen -o yaml > "${BACKUP_DIR}/qwen-component-secrets.yaml" 2>/dev/null || true
    
    log_success "Configurations backed up to ${BACKUP_DIR}"
}

# Scale down existing Qwen deployments
scale_down_existing() {
    log_info "Scaling down existing Qwen deployments..."
    
    # Scale down qwen deployments
    kubectl scale deployment -n "${NAMESPACE}" --replicas=0 -l app=qwen 2>/dev/null || true
    kubectl scale deployment -n "${NAMESPACE}" --replicas=0 -l component=qwen 2>/dev/null || true
    
    # Wait for pods to terminate
    kubectl wait --for=delete pod -n "${NAMESPACE}" -l app=qwen --timeout=300s 2>/dev/null || true
    kubectl wait --for=delete pod -n "${NAMESPACE}" -l component=qwen --timeout=300s 2>/dev/null || true
    
    log_success "Existing Qwen deployments scaled down"
}

# Deploy centralized agent-memory-rust
deploy_centralized_service() {
    log_info "Deploying centralized agent-memory-rust service..."
    
    # Apply the updated deployment
    kubectl apply -f "${REPO_ROOT}/core/resources/infrastructure/ai-inference/shared/agent-memory-deployment.yaml"
    
    # Wait for the service to be ready
    kubectl wait --for=condition=available deployment/agent-memory-rust -n "${NAMESPACE}" --timeout=600s
    
    # Verify the service is responding
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if kubectl get pods -n "${NAMESPACE}" -l component=agent-memory | grep -q "Running"; then
            log_success "agent-memory-rust pods are running"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            log_error "agent-memory-rust pods failed to start"
            kubectl logs -n "${NAMESPACE}" deployment/agent-memory-rust --tail=50
            exit 1
        fi
        
        log_info "Waiting for agent-memory-rust pods to start... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    # Test the health endpoint
    local health_attempts=20
    local health_attempt=1
    
    while [[ $health_attempt -le $health_attempts ]]; do
        if kubectl port-forward -n "${NAMESPACE}" svc/agent-memory-service 8080:8080 &>/dev/null & then
            sleep 2
            if curl -f http://localhost:8080/api/health &>/dev/null; then
                log_success "agent-memory-rust health check passed"
                pkill -f "kubectl port-forward.*8080:8080" || true
                break
            fi
            pkill -f "kubectl port-forward.*8080:8080" || true
        fi
        
        if [[ $health_attempt -eq $health_attempts ]]; then
            log_warning "Health check failed, but deployment may still be working"
            break
        fi
        
        log_info "Waiting for health endpoint... (attempt $health_attempt/$health_attempts)"
        sleep 5
        ((health_attempt++))
    done
}

# Update K8sGPT configuration
update_k8sgpt_config() {
    log_info "Updating K8sGPT configuration to use centralized Qwen..."
    
    # Check if K8sGPT is deployed
    if kubectl get deployment k8sgpt -n "${NAMESPACE}" &>/dev/null; then
        # Create or update K8sGPT config
        cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: k8sgpt-config
  namespace: ${NAMESPACE}
data:
  config.yaml: |
    backend: agent-memory
    model: qwen2.5-7b-instruct
    baseurl: http://agent-memory-service.${NAMESPACE}.svc.cluster.local:8080
    maxtokens: 4096
    temperature: 0.7
    timeout: 30
    headers:
      X-API-Key: k8sgpt-api-key
EOF
        
        # Restart K8sGPT to pick up new configuration
        kubectl rollout restart deployment/k8sgpt -n "${NAMESPACE}"
        kubectl rollout status deployment/k8sgpt -n "${NAMESPACE}"
        
        log_success "K8sGPT configuration updated"
    else
        log_warning "K8sGPT deployment not found in namespace ${NAMESPACE}"
    fi
}

# Update Flagger configuration
update_flagger_config() {
    log_info "Updating Flagger configuration to use centralized Qwen..."
    
    # Check if Flagger is deployed
    if kubectl get deployment flagger -n flagger-system &>/dev/null; then
        # Create Flagger Qwen config
        cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: flagger-qwen-config
  namespace: flagger-system
data:
  qwen-config.yaml: |
    model: qwen2.5-7b-instruct
    base_url: http://agent-memory-service.ai-infrastructure.svc.cluster.local:8080
    api_key: flagger-api-key
    max_tokens: 4096
    temperature: 0.7
    timeout: 30
EOF
        
        # Restart Flagger to pick up new configuration
        kubectl rollout restart deployment/flagger -n flagger-system
        kubectl rollout status deployment/flagger -n flagger-system
        
        log_success "Flagger configuration updated"
    else
        log_warning "Flagger deployment not found in namespace flagger-system"
    fi
}

# Verify migration
verify_migration() {
    log_info "Verifying migration..."
    
    # Check agent-memory-rust is running
    if kubectl get pods -n "${NAMESPACE}" -l component=agent-memory | grep -q "Running"; then
        log_success "✓ agent-memory-rust is running"
    else
        log_error "✗ agent-memory-rust is not running"
        return 1
    fi
    
    # Check service is accessible
    if kubectl get svc agent-memory-service -n "${NAMESPACE}" &>/dev/null; then
        log_success "✓ agent-memory-service is available"
    else
        log_error "✗ agent-memory-service is not available"
        return 1
    end
    
    # Check metrics endpoint
    if kubectl get svc agent-memory-service -n "${NAMESPACE}" -o yaml | grep -q "9090"; then
        log_success "✓ metrics endpoint is configured"
    else
        log_warning "⚠ metrics endpoint may not be configured"
    fi
    
    # Check ServiceMonitor
    if kubectl get servicemonitor agent-memory-metrics -n "${NAMESPACE}" &>/dev/null; then
        log_success "✓ ServiceMonitor is configured"
    else
        log_warning "⚠ ServiceMonitor may not be configured"
    fi
    
    log_success "Migration verification completed"
}

# Cleanup old resources (optional)
cleanup_old_resources() {
    if [[ "${CLEANUP_OLD:-false}" == "true" ]]; then
        log_info "Cleaning up old Qwen resources..."
        
        # Delete old deployments
        kubectl delete deployment -n "${NAMESPACE}" -l app=qwen --ignore-not-found=true 2>/dev/null || true
        kubectl delete deployment -n "${NAMESPACE}" -l component=qwen --ignore-not-found=true 2>/dev/null || true
        
        # Delete old services
        kubectl delete service -n "${NAMESPACE}" -l app=qwen --ignore-not-found=true 2>/dev/null || true
        kubectl delete service -n "${NAMESPACE}" -l component=qwen --ignore-not-found=true 2>/dev/null || true
        
        # Delete old configmaps
        kubectl delete configmap -n "${NAMESPACE}" -l app=qwen --ignore-not-found=true 2>/dev/null || true
        kubectl delete configmap -n "${NAMESPACE}" -l component=qwen --ignore-not-found=true 2>/dev/null || true
        
        log_success "Old Qwen resources cleaned up"
    fi
}

# Show migration summary
show_migration_summary() {
    log_info "Migration Summary:"
    echo
    echo "🎯 Centralized Qwen Service:"
    echo "  - Namespace: ${NAMESPACE}"
    echo "  - Service: agent-memory-service"
    echo "  - HTTP Port: 8080"
    echo "  - Metrics Port: 9090"
    echo
    echo "🔗 Integration Points:"
    echo "  - K8sGPT: Updated to use agent-memory backend"
    echo "  - Flagger: Updated to use centralized Qwen"
    echo
    echo "📊 Monitoring:"
    echo "  - Metrics: http://agent-memory-service.${NAMESPACE}.svc.cluster.local:9090/metrics"
    echo "  - Health: http://agent-memory-service.${NAMESPACE}.svc.cluster.local:8080/api/health"
    echo
    echo "💾 Backup Location: ${BACKUP_DIR}"
    echo
    echo "🔄 Rollback:"
    echo "  kubectl apply -f ${BACKUP_DIR}/"
    echo
    echo "📚 Documentation:"
    echo "  - ${REPO_ROOT}/docs/qwen-consolidation-plan.md"
    echo
}

# Main function
main() {
    local action="${1:-migrate}"
    
    case "${action}" in
        "migrate")
            log_info "Starting Qwen consolidation migration..."
            check_prerequisites
            backup_existing_configs
            scale_down_existing
            deploy_centralized_service
            update_k8sgpt_config
            update_flagger_config
            verify_migration
            cleanup_old_resources
            show_migration_summary
            log_success "Qwen consolidation migration completed successfully!"
            ;;
        "verify")
            verify_migration
            ;;
        "cleanup")
            cleanup_old_resources
            ;;
        "rollback")
            log_warning "Rolling back to previous configuration..."
            if [[ -d "${BACKUP_DIR}" ]]; then
                kubectl apply -f "${BACKUP_DIR}/"
                log_success "Rollback completed"
            else
                log_error "No backup directory found at ${BACKUP_DIR}"
                exit 1
            fi
            ;;
        "help"|"-h"|"--help")
            echo "Qwen Consolidation Migration Script"
            echo
            echo "Usage: $0 [migrate|verify|cleanup|rollback|help]"
            echo
            echo "Actions:"
            echo "  migrate   - Full migration to centralized Qwen (default)"
            echo "  verify    - Verify migration status"
            echo "  cleanup   - Clean up old Qwen resources"
            echo "  rollback  - Rollback to previous configuration"
            echo "  help      - Show this help message"
            echo
            echo "Environment Variables:"
            echo "  NAMESPACE        - Kubernetes namespace (default: ai-infrastructure)"
            echo "  BACKUP_DIR       - Backup directory (auto-generated)"
            echo "  CLEANUP_OLD      - Clean up old resources (default: false)"
            echo
            echo "Examples:"
            echo "  $0                           # Full migration"
            echo "  NAMESPACE=prod $0            # Migrate in prod namespace"
            echo "  CLEANUP_OLD=true $0           # Migrate and cleanup old resources"
            echo "  $0 verify                    # Verify migration"
            echo "  $0 rollback                  # Rollback changes"
            ;;
        *)
            echo "Unknown action: ${action}"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"

#!/bin/bash
# K8sGPT Consolidation Quick Deployment Script
# Automates deployment and validation of consolidated K8sGPT

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONSOLIDATED_DIR="${SCRIPT_DIR}/../core/gitops/consolidated"
NAMESPACE="k8sgpt-system"
SERVICE_URL="http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"

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

# Help function
show_help() {
    cat << EOF
K8sGPT Consolidation Quick Deployment Script

USAGE:
    $0 [OPTIONS] <COMMAND>

COMMANDS:
    deploy          Deploy consolidated K8sGPT
    validate        Validate deployment and integration
    test            Run connectivity tests
    cleanup          Clean up old deployments
    report          Generate deployment report
    full            Run complete deployment and validation

OPTIONS:
    -h, --help     Show this help message
    -n, --namespace  Override namespace (default: k8sgpt-system)
    -q, --quiet     Suppress non-error output
    -v, --verbose    Enable verbose output
    --dry-run        Show commands without executing

EXAMPLES:
    $0 deploy                    # Deploy K8sGPT
    $0 validate                  # Validate deployment
    $0 full                      # Full deployment and validation
    $0 --namespace test-k8sgpt deploy  # Deploy to custom namespace

EOF
}

# Parse command line arguments
NAMESPACE="k8sgpt-system"
QUIET=false
VERBOSE=false
DRY_RUN=false
COMMAND=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        deploy|validate|test|cleanup|report|full)
            COMMAND="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Verbose logging
verbose_log() {
    if [[ "$VERBOSE" == "true" ]]; then
        log_info "$1"
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check cluster access
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check consolidated files
    if [[ ! -d "$CONSOLIDATED_DIR" ]]; then
        log_error "Consolidated configuration directory not found: $CONSOLIDATED_DIR"
        exit 1
    fi
    
    # Check required files
    local required_files=(
        "k8sgpt-unified-deployment.yaml"
        "k8sgpt-unified-config.yaml"
        "k8sgpt-secrets-template.yaml"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$CONSOLIDATED_DIR/$file" ]]; then
            log_error "Required file not found: $file"
            exit 1
        fi
    done
    
    log_success "Prerequisites check passed"
}

# Create namespace
create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "kubectl create namespace $NAMESPACE \\"
        echo "  --label=app.kubernetes.io/name=k8sgpt \\"
        echo "  --label=app.kubernetes.io/component=namespace \\"
        echo "  --label=app.kubernetes.io/part-of=agentic-reconciliation-engine \\"
        echo "  --label=name=$NAMESPACE"
        return
    fi
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE already exists"
        return
    fi
    
    kubectl create namespace "$NAMESPACE" \
        --label=app.kubernetes.io/name=k8sgpt \
        --label=app.kubernetes.io/component=namespace \
        --label=app.kubernetes.io/part-of=agentic-reconciliation-engine \
        --label=name="$NAMESPACE"
    
    log_success "Namespace $NAMESPACE created"
}

# Deploy K8sGPT
deploy_k8sgpt() {
    log_info "Deploying consolidated K8sGPT..."
    
    # Check if secrets file exists
    local secrets_file="$CONSOLIDATED_DIR/k8sgpt-secrets.yaml"
    if [[ ! -f "$secrets_file" ]]; then
        log_warning "Secrets file not found. Creating template..."
        cp "$CONSOLIDATED_DIR/k8sgpt-secrets-template.yaml" "$secrets_file"
        log_warning "Please edit $secrets_file with your actual values before proceeding"
        return 1
    fi
    
    # Apply configurations
    local files=(
        "k8sgpt-unified-config.yaml"
        "k8sgpt-secrets.yaml"
        "k8sgpt-unified-deployment.yaml"
    )
    
    for file in "${files[@]}"; do
        local file_path="$CONSOLIDATED_DIR/$file"
        verbose_log "Applying $file"
        
        if [[ "$DRY_RUN" == "true" ]]; then
            echo "kubectl apply -f $file_path"
        else
            kubectl apply -f "$file_path"
        fi
    done
    
    log_success "K8sGPT deployment applied"
}

# Wait for deployment to be ready
wait_for_deployment() {
    log_info "Waiting for deployment to be ready..."
    
    local timeout=300
    local interval=10
    local elapsed=0
    
    while [[ $elapsed -lt $timeout ]]; do
        local ready=$(kubectl get deployment k8sgpt -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        local desired=$(kubectl get deployment k8sgpt -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "1")
        
        if [[ "$ready" == "$desired" ]] && [[ "$ready" == "1" ]]; then
            log_success "Deployment is ready"
            return 0
        fi
        
        if [[ "$QUIET" != "true" ]]; then
            echo "Waiting... (${elapsed}/${timeout}s)"
        fi
        
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    log_error "Timeout waiting for deployment to be ready"
    return 1
}

# Test service connectivity
test_connectivity() {
    log_info "Testing service connectivity..."
    
    # Port-forward for testing
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "kubectl port-forward service/k8sgpt 8080:8080 -n $NAMESPACE &"
        return
    fi
    
    kubectl port-forward service/k8sgpt 8080:8080 -n "$NAMESPACE" &
    local pf_pid=$!
    
    # Wait for port-forward to be ready
    sleep 5
    
    # Test health endpoint
    local health_test=false
    for i in {1..5}; do
        if curl -f --connect-timeout 5 http://localhost:8080/healthz &>/dev/null; then
            health_test=true
            break
        fi
        sleep 2
    done
    
    # Clean up port-forward
    kill $pf_pid 2>/dev/null
    
    if [[ "$health_test" == "true" ]]; then
        log_success "Service connectivity test passed"
    else
        log_error "Service connectivity test failed"
        return 1
    fi
}

# Validate integration with components
validate_integration() {
    log_info "Validating component integration..."
    
    local components=("argo-workflows" "argo-rollouts" "flux-system" "argo-events" "argocd" "pipecd")
    local success_count=0
    
    for component in "${components[@]}"; do
        verbose_log "Testing integration from $component namespace"
        
        if [[ "$DRY_RUN" == "true" ]]; then
            echo "kubectl run test-$component --image=curlimages/curl --rm -i --restart=Never -- curl -f $SERVICE_URL/healthz -n $component"
            continue
        fi
        
        # Check if namespace exists
        if ! kubectl get namespace "$component" &> /dev/null; then
            verbose_log "Namespace $component not found, skipping"
            continue
        fi
        
        # Test connectivity
        if kubectl run test-$component --image=curlimages/curl --rm -i --restart=Never \
            -- curl -f --connect-timeout 10 "$SERVICE_URL/healthz" -n "$component" &>/dev/null; then
            log_success "Integration working for $component"
            success_count=$((success_count + 1))
        else
            log_warning "Integration failed for $component"
        fi
    done
    
    if [[ $success_count -eq ${#components[@]} ]]; then
        log_success "All component integrations validated"
    else
        log_warning "Some component integrations failed"
    fi
}

# Clean up old deployments
cleanup_old_deployments() {
    log_info "Cleaning up old K8sGPT deployments..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "# Would clean up old deployments from other namespaces"
        return
    fi
    
    # Find old deployments
    local old_deployments=$(kubectl get deployments -A -l app.kubernetes.io/name=k8sgpt --no-headers | awk -v ns="$NAMESPACE" '$1 != ns {print $1":"$2}')
    
    if [[ -z "$old_deployments" ]]; then
        log_info "No old deployments found"
        return
    fi
    
    while IFS=':' read -r namespace name <<< "$old_deployments"; do
        log_info "Removing old deployment: $name from $namespace"
        kubectl delete deployment "$name" -n "$namespace" --ignore-not-found=true
        kubectl delete service "$name" -n "$namespace" --ignore-not-found=true
        kubectl delete configmap -l app.kubernetes.io/name=k8sgpt -n "$namespace" --ignore-not-found=true
        kubectl delete secret -l app.kubernetes.io/name=k8sgpt -n "$namespace" --ignore-not-found=true
    done
    
    log_success "Old deployments cleaned up"
}

# Generate deployment report
generate_report() {
    log_info "Generating deployment report..."
    
    local report_file="k8sgpt-deployment-report-$(date +%Y%m%d-%H%M%S).md"
    
    cat > "$report_file" << EOF
# K8sGPT Consolidation Deployment Report

## Deployment Summary
- **Date**: $(date)
- **Cluster**: $(kubectl config current-context)
- **Namespace**: $NAMESPACE
- **Service URL**: $SERVICE_URL

## Deployment Status
$(kubectl get deployment k8sgpt -n "$NAMESPACE" -o yaml)

## Service Status
$(kubectl get service k8sgpt -n "$NAMESPACE" -o yaml)

## Resource Usage
$(kubectl top pod -n "$NAMESPACE" -l app.kubernetes.io/name=k8sgpt)

## Component Integration Test
$(validate_integration 2>&1)

## Validation Commands
- Health check: curl -f $SERVICE_URL/healthz
- Metrics: curl -f $SERVICE_URL/metrics
- Analysis: curl -X POST $SERVICE_URL/analyze -H "Content-Type: application/json" -d '{"namespace":"default","resources":["deployments"]}'

Generated by: $0 on $(date)
EOF
    
    log_success "Deployment report generated: $report_file"
}

# Full deployment and validation
full_deployment() {
    log_info "Starting full deployment and validation..."
    
    check_prerequisites
    create_namespace
    deploy_k8sgpt
    
    if wait_for_deployment; then
        test_connectivity
        validate_integration
        generate_report
        log_success "Full deployment and validation completed successfully!"
    else
        log_error "Deployment failed"
        exit 1
    fi
}

# Main execution logic
main() {
    case "$COMMAND" in
        deploy)
            check_prerequisites
            create_namespace
            deploy_k8sgpt
            wait_for_deployment
            ;;
        validate)
            test_connectivity
            validate_integration
            ;;
        test)
            test_connectivity
            ;;
        cleanup)
            cleanup_old_deployments
            ;;
        report)
            generate_report
            ;;
        full)
            full_deployment
            ;;
        "")
            log_error "No command specified"
            show_help
            exit 1
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# Execute main function
main

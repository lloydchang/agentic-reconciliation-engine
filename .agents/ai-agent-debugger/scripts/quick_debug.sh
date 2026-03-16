#!/bin/bash

# Quick Debug Script for AI Systems
# Fast debugging commands for common issues

set -euo pipefail

# Configuration
NAMESPACE="${NAMESPACE:-temporal}"
TIME_RANGE="${TIME_RANGE:-1h}"
VERBOSE="${VERBOSE:-false}"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed or not in PATH"
        exit 1
    fi
    
    # Check kubernetes connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Agent debugging functions
debug_agents() {
    log_info "Debugging AI agents in namespace: $NAMESPACE"
    
    echo "=== Agent Pod Status ==="
    kubectl get pods -n "$NAMESPACE" -l app=temporal-worker -o wide
    
    echo -e "\n=== Agent Pod Restarts ==="
    kubectl get pods -n "$NAMESPACE" -l app=temporal-worker --no-headers | awk '{print $1, $4}' | column -t
    
    echo -e "\n=== Recent Agent Errors (Last Hour) ==="
    kubectl logs -n "$NAMESPACE" deployment/temporal-worker --since=1h | grep -i error | tail -10 || log_info "No errors found"
    
    echo -e "\n=== Agent Resource Usage ==="
    kubectl top pods -n "$NAMESPACE" -l app=temporal-worker --no-headers 2>/dev/null | head -5 || log_warn "Metrics server not available"
    
    echo -e "\n=== Agent Health Endpoint ==="
    if kubectl get svc temporal-worker -n "$NAMESPACE" &> /dev/null; then
        kubectl port-forward -n "$NAMESPACE" svc/temporal-worker 8080:8080 &
        PF_PID=$!
        sleep 2
        if curl -s http://localhost:8080/health &> /dev/null; then
            log_success "Agent health endpoint is responding"
        else
            log_error "Agent health endpoint is not responding"
        fi
        kill $PF_PID 2>/dev/null || true
    else
        log_warn "Agent service not found"
    fi
}

# Workflow debugging functions
debug_workflows() {
    log_info "Debugging Temporal workflows in namespace: $NAMESPACE"
    
    echo "=== Temporal Server Status ==="
    kubectl get pods -n "$NAMESPACE" -l app=temporal-server -o wide
    
    echo -e "\n=== Temporal Frontend Status ==="
    kubectl get pods -n "$NAMESPACE" -l app=temporal-frontend -o wide
    
    echo -e "\n=== Temporal Services ==="
    kubectl get svc -n "$NAMESPACE" -l app=temporal-*
    
    echo -e "\n=== Recent Workflow Errors ==="
    kubectl logs -n "$NAMESPACE" deployment/temporal-server --since=1h | grep -i error | tail -10 || log_info "No errors found"
    
    echo -e "\n=== Workflow Queue Status ==="
    if kubectl get svc temporal-server -n "$NAMESPACE" &> /dev/null; then
        kubectl port-forward -n "$NAMESPACE" svc/temporal-server 7233:7233 &
        PF_PID=$!
        sleep 2
        # This would require temporal CLI to be installed
        if command -v temporal &> /dev/null; then
            temporal task queue describe --address localhost:7233 || log_warn "Could not fetch task queue info"
        else
            log_warn "Temporal CLI not installed"
        fi
        kill $PF_PID 2>/dev/null || true
    fi
}

# Infrastructure debugging functions
debug_infrastructure() {
    log_info "Debugging Kubernetes infrastructure"
    
    echo "=== Node Status ==="
    kubectl get nodes -o wide
    
    echo -e "\n=== Resource Usage ==="
    kubectl top nodes --no-headers 2>/dev/null || log_warn "Metrics server not available"
    
    echo -e "\n=== Namespace Events ==="
    kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | tail -10
    
    echo -e "\n=== Storage Status ==="
    kubectl get pv,pvc -n "$NAMESPACE" --no-headers | head -10
    
    echo -e "\n=== Network Policies ==="
    kubectl get networkpolicies -n "$NAMESPACE" -o wide || log_info "No network policies found"
}

# Performance debugging functions
debug_performance() {
    log_info "Debugging performance issues"
    
    echo "=== High CPU Pods ==="
    kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | awk '$2 ~ /m$/ && ($2+0) > 1000 {print $0}' || log_warn "Metrics server not available"
    
    echo -e "\n=== High Memory Pods ==="
    kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | awk '$3 ~ /Mi$/ && ($3+0) > 1000 {print $0}' || log_warn "Metrics server not available"
    
    echo -e "\n=== Pod Resource Limits ==="
    kubectl get pods -n "$NAMESPACE" -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].resources.requests.cpu}{"\t"}{.spec.containers[*].resources.limits.cpu}{"\n"}{end}' | column -t
    
    echo -e "\n=== Slow Queries/Operations ==="
    kubectl logs -n "$NAMESPACE" deployment/temporal-worker --since=1h | grep -i -E "(slow|timeout|latency)" | tail -5 || log_info "No performance issues found"
}

# Connectivity debugging functions
debug_connectivity() {
    log_info "Debugging connectivity issues"
    
    echo "=== Service Connectivity ==="
    kubectl get svc -n "$NAMESPACE" -o wide
    
    echo -e "\n=== Endpoints ==="
    kubectl get endpoints -n "$NAMESPACE" -o wide
    
    echo -e "\n=== Ingress Status ==="
    kubectl get ingress -n "$NAMESPACE" -o wide || log_info "No ingress resources found"
    
    echo -e "\n=== Network Policies ==="
    kubectl get networkpolicies -n "$NAMESPACE" -o yaml | head -20 || log_info "No network policies found"
    
    echo -e "\n=== DNS Resolution Test ==="
    kubectl run -n "$NAMESPACE" dns-test --image=busybox --rm -it --restart=Never -- nslookup temporal-server.$NAMESPACE.svc.cluster.local || log_warn "DNS resolution failed"
}

# Auto-fix functions
apply_auto_fixes() {
    log_info "Applying automatic fixes..."
    
    # Restart failing pods
    local failed_pods
    failed_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Failed -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || true)
    
    if [[ -n "$failed_pods" ]]; then
        log_warn "Found failed pods: $failed_pods"
        for pod in $failed_pods; do
            log_info "Deleting failed pod: $pod"
            kubectl delete pod "$pod" -n "$NAMESPACE" || log_error "Failed to delete pod: $pod"
        done
    fi
    
    # Clear evicted pods
    local evicted_pods
    evicted_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Failed -o jsonpath='{.items[?(@.status.reason=="Evicted")].metadata.name}' 2>/dev/null || true)
    
    if [[ -n "$evicted_pods" ]]; then
        log_warn "Found evicted pods: $evicted_pods"
        for pod in $evicted_pods; do
            log_info "Deleting evicted pod: $pod"
            kubectl delete pod "$pod" -n "$NAMESPACE" || log_error "Failed to delete evicted pod: $pod"
        done
    fi
    
    # Restart stuck deployments
    local stuck_deployments
    stuck_deployments=$(kubectl get deployments -n "$NAMESPACE" -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.status.readyReplicas}{" "}{.spec.replicas}{"\n"}{end}' | awk '$2 != $3 {print $1}' || true)
    
    if [[ -n "$stuck_deployments" ]]; then
        log_warn "Found stuck deployments: $stuck_deployments"
        for deployment in $stuck_deployments; do
            log_info "Restarting deployment: $deployment"
            kubectl rollout restart deployment/"$deployment" -n "$NAMESPACE" || log_error "Failed to restart deployment: $deployment"
        done
    fi
    
    log_success "Auto-fixes applied"
}

# Generate summary report
generate_report() {
    local report_file="/tmp/ai-debug-report-$(date +%Y%m%d-%H%M%S).json"
    
    log_info "Generating debug report: $report_file"
    
    # Collect system information
    local timestamp
    timestamp=$(date -Iseconds)
    
    # Create JSON report
    jq -n \
        --arg timestamp "$timestamp" \
        --arg namespace "$NAMESPACE" \
        --arg time_range "$TIME_RANGE" \
        '{
            timestamp: $timestamp,
            namespace: $namespace,
            time_range: $time_range,
            cluster_info: {},
            pod_status: {},
            recent_errors: [],
            recommendations: []
        }' > "$report_file"
    
    # Add pod status
    kubectl get pods -n "$NAMESPACE" -o json | jq '.items | map({name: .metadata.name, status: .status.phase, restarts: [.status.containerStatuses[].restartCount] | add})' > /tmp/pods.json
    jq -s '.[0].pod_status = .[1] | .[0]' "$report_file" /tmp/pods.json > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    # Add recent errors
    kubectl logs -n "$NAMESPACE" deployment/temporal-worker --since=1h 2>/dev/null | grep -i error | head -20 > /tmp/errors.txt || true
    if [[ -s /tmp/errors.txt ]]; then
        jq -R -s '{"recent_errors": split("\n") | map(select(length > 0))}' /tmp/errors.txt > /tmp/errors.json
        jq -s '.[0] + .[1]' "$report_file" /tmp/errors.json > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    fi
    
    # Add recommendations
    local recommendations=()
    
    # Check for failed pods
    local failed_count
    failed_count=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Failed --no-headers | wc -l)
    if [[ $failed_count -gt 0 ]]; then
        recommendations+=("Investigate $failed_count failed pods")
    fi
    
    # Check for high restarts
    local high_restart_pods
    high_restart_pods=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.status.containerStatuses[].restartCount}{"\n"}{end}' | awk '$2 > 5 {print $1}' || true)
    if [[ -n "$high_restart_pods" ]]; then
        recommendations+=("Check pods with high restart counts: $high_restart_pods")
    fi
    
    # Add recommendations to report
    if [[ ${#recommendations[@]} -gt 0 ]]; then
        printf '%s\n' "${recommendations[@]}" | jq -R . | jq -s '{"recommendations": .}' > /tmp/recs.json
        jq -s '.[0] + .[1]' "$report_file" /tmp/recs.json > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    fi
    
    # Cleanup temp files
    rm -f /tmp/pods.json /tmp/errors.json /tmp/recs.json /tmp/errors.txt
    
    log_success "Debug report saved to: $report_file"
    
    # Display summary
    echo -e "\n=== Debug Summary ==="
    jq -r '.timestamp, .namespace, (.pod_status | length), (.recent_errors | length), (.recommendations | length)' "$report_file" | {
        read -r timestamp
        read -r namespace
        read -r pod_count
        read -r error_count
        read -r rec_count
        
        echo "Timestamp: $timestamp"
        echo "Namespace: $namespace"
        echo "Pods analyzed: $pod_count"
        echo "Recent errors: $error_count"
        echo "Recommendations: $rec_count"
    }
}

# Main function
main() {
    local component="${1:-all}"
    local issue_type="${2:-general}"
    local auto_fix="${3:-false}"
    
    log_info "Starting AI System Debugger"
    log_info "Component: $component, Issue Type: $issue_type, Auto-fix: $auto_fix"
    
    check_prerequisites
    
    case "$component" in
        "agents")
            debug_agents
            ;;
        "workflows")
            debug_workflows
            ;;
        "infrastructure")
            debug_infrastructure
            ;;
        "performance")
            debug_performance
            ;;
        "connectivity")
            debug_connectivity
            ;;
        "all")
            debug_agents
            debug_workflows
            debug_infrastructure
            ;;
        *)
            log_error "Unknown component: $component"
            echo "Usage: $0 [agents|workflows|infrastructure|performance|connectivity|all] [issue_type] [auto_fix]"
            exit 1
            ;;
    esac
    
    if [[ "$auto_fix" == "true" ]]; then
        apply_auto_fixes
    fi
    
    generate_report
    
    log_success "Debug session completed"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

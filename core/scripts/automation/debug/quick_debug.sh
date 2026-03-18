#!/bin/bash

# Quick Debug Script for Distributed Systems
# Provides fast debugging commands for common issues

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
NAMESPACE="default"
TIME_RANGE="30m"
VERBOSE=false
AUTO_FIX=false

# Help function
show_help() {
    cat << EOF
Quick Debug Script for Distributed Systems

USAGE:
    $0 [OPTIONS] <TARGET> <ISSUE_TYPE>

TARGETS:
    agents          Debug AI agents and temporal workflows
    workflows       Debug temporal workflow execution
    infrastructure  Debug Kubernetes infrastructure
    all             Debug all components

ISSUE_TYPES:
    errors          Debug error patterns and failures
    performance     Debug performance and latency issues
    timeouts        Debug timeout and hanging issues
    connectivity    Debug network and service connectivity
    resource        Debug resource utilization issues

OPTIONS:
    -n, --namespace <name>     Kubernetes namespace (default: default)
    -t, --time-range <range>    Time range for analysis (default: 30m)
    -v, --verbose              Enable verbose output
    -f, --auto-fix             Attempt automatic fixes
    -h, --help                 Show this help message

EXAMPLES:
    $0 agents errors --namespace temporal --time-range 1h
    $0 infrastructure performance --verbose --auto-fix
    $0 all connectivity --namespace production

EOF
}

# Logging functions
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

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -t|--time-range)
                TIME_RANGE="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -f|--auto-fix)
                AUTO_FIX=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -*)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                if [[ -z "${TARGET:-}" ]]; then
                    TARGET="$1"
                elif [[ -z "${ISSUE_TYPE:-}" ]]; then
                    ISSUE_TYPE="$1"
                else
                    log_error "Too many arguments"
                    show_help
                    exit 1
                fi
                shift
                ;;
        esac
    done

    # Validate required arguments
    if [[ -z "${TARGET:-}" || -z "${ISSUE_TYPE:-}" ]]; then
        log_error "Target and issue type are required"
        show_help
        exit 1
    fi
}

# Check dependencies
check_dependencies() {
    local deps=("kubectl" "jq" "curl")
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "Required dependency not found: $dep"
            exit 1
        fi
    done
    
    # Check kubectl connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "All dependencies verified"
}

# Debug agents
debug_agents() {
    local issue_type="$1"
    
    log_info "Debugging agents for issue type: $issue_type"
    
    case "$issue_type" in
        errors)
            debug_agent_errors
            ;;
        performance)
            debug_agent_performance
            ;;
        timeouts)
            debug_agent_timeouts
            ;;
        *)
            log_error "Unsupported issue type for agents: $issue_type"
            return 1
            ;;
    esac
}

# Debug agent errors
debug_agent_errors() {
    log_info "Analyzing agent errors..."
    
    # Get agent pods
    local agent_pods
    agent_pods=$(kubectl get pods -n "$NAMESPACE" -l app=temporal-worker -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -z "$agent_pods" ]]; then
        log_warn "No agent pods found in namespace: $NAMESPACE"
        return 0
    fi
    
    for pod in $agent_pods; do
        log_info "Checking pod: $pod"
        
        # Check pod status
        local status
        status=$(kubectl get pod "$pod" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
        
        if [[ "$status" != "Running" ]]; then
            log_error "Pod $pod is not running (status: $status)"
            
            if [[ "$AUTO_FIX" == "true" ]]; then
                log_info "Attempting to restart pod: $pod"
                kubectl delete pod "$pod" -n "$NAMESPACE" --wait=false
                log_success "Initiated restart for pod: $pod"
            fi
        fi
        
        # Check recent errors in logs
        if [[ "$VERBOSE" == "true" ]]; then
            log_info "Recent errors for pod $pod:"
            kubectl logs "$pod" -n "$NAMESPACE" --since="$TIME_RANGE" | grep -i error | tail -5 || true
        fi
        
        # Check restart count
        local restart_count
        restart_count=$(kubectl get pod "$pod" -n "$NAMESPACE" -o jsonpath='{.status.containerStatuses[0].restartCount}')
        
        if [[ "$restart_count" -gt 0 ]]; then
            log_warn "Pod $pod has restarted $restart_count times"
        fi
    done
}

# Debug agent performance
debug_agent_performance() {
    log_info "Analyzing agent performance..."
    
    # Get resource usage
    log_info "Resource usage for agent pods:"
    kubectl top pods -n "$NAMESPACE" -l app=temporal-worker --use-protocol-buffers 2>/dev/null || {
        log_warn "Metrics server not available or no metrics found"
    }
    
    # Check pod resource requests vs limits
    log_info "Resource requests and limits:"
    kubectl get pods -n "$NAMESPACE" -l app=temporal-worker -o custom-columns=NAME:.metadata.name,CPU_REQUEST:.spec.containers[0].resources.requests.cpu,MEMORY_REQUEST:.spec.containers[0].resources.requests.memory,CPU_LIMIT:.spec.containers[0].resources.limits.cpu,MEMORY_LIMIT:.spec.containers[0].resources.limits.memory
}

# Debug agent timeouts
debug_agent_timeouts() {
    log_info "Analyzing agent timeouts..."
    
    # Check temporal workflow status
    log_info "Temporal workflow status:"
    
    # Look for stuck workflows (this would require temporal CLI in a real implementation)
    log_warn "Temporal workflow analysis requires temporal CLI"
    
    # Check network connectivity
    log_info "Checking network connectivity..."
    kubectl get pods -n "$NAMESPACE" -l app=temporal-worker -o wide
}

# Debug workflows
debug_workflows() {
    local issue_type="$1"
    
    log_info "Debugging workflows for issue type: $issue_type"
    
    case "$issue_type" in
        errors)
            debug_workflow_errors
            ;;
        performance)
            debug_workflow_performance
            ;;
        timeouts)
            debug_workflow_timeouts
            ;;
        *)
            log_error "Unsupported issue type for workflows: $issue_type"
            return 1
            ;;
    esac
}

# Debug workflow errors
debug_workflow_errors() {
    log_info "Analyzing workflow errors..."
    
    # Check temporal service pods
    local temporal_pods
    temporal_pods=$(kubectl get pods -n "$NAMESPACE" -l app=temporal -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -z "$temporal_pods" ]]; then
        log_warn "No temporal service pods found in namespace: $NAMESPACE"
        return 0
    fi
    
    for pod in $temporal_pods; do
        log_info "Checking temporal pod: $pod"
        
        # Check pod status
        local status
        status=$(kubectl get pod "$pod" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
        
        if [[ "$status" != "Running" ]]; then
            log_error "Temporal pod $pod is not running (status: $status)"
        fi
        
        # Check for errors in logs
        if [[ "$VERBOSE" == "true" ]]; then
            log_info "Recent errors for temporal pod $pod:"
            kubectl logs "$pod" -n "$NAMESPACE" --since="$TIME_RANGE" | grep -i error | tail -5 || true
        fi
    done
}

# Debug workflow performance
debug_workflow_performance() {
    log_info "Analyzing workflow performance..."
    
    # Check temporal service resource usage
    log_info "Temporal service resource usage:"
    kubectl top pods -n "$NAMESPACE" -l app=temporal --use-protocol-buffers 2>/dev/null || {
        log_warn "Metrics server not available or no metrics found"
    }
}

# Debug workflow timeouts
debug_workflow_timeouts() {
    log_info "Analyzing workflow timeouts..."
    
    log_warn "Workflow timeout analysis requires temporal CLI access"
    log_info "Checking temporal service health..."
    
    # Check temporal service endpoints
    kubectl get svc -n "$NAMESPACE" -l app=temporal
}

# Debug infrastructure
debug_infrastructure() {
    local issue_type="$1"
    
    log_info "Debugging infrastructure for issue type: $issue_type"
    
    case "$issue_type" in
        errors)
            debug_infrastructure_errors
            ;;
        performance)
            debug_infrastructure_performance
            ;;
        connectivity)
            debug_infrastructure_connectivity
            ;;
        resource)
            debug_infrastructure_resources
            ;;
        *)
            log_error "Unsupported issue type for infrastructure: $issue_type"
            return 1
            ;;
    esac
}

# Debug infrastructure errors
debug_infrastructure_errors() {
    log_info "Analyzing infrastructure errors..."
    
    # Check node status
    log_info "Node status:"
    kubectl get nodes --no-headers | awk '{print $1, $2}' | while read -r node status; do
        if [[ "$status" != "Ready" ]]; then
            log_error "Node $node has status: $status"
        fi
    done
    
    # Check for failing pods
    log_info "Checking for failing pods in namespace: $NAMESPACE"
    kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running --no-headers | while read -r name ready status restarts age; do
        if [[ "$status" != "Running" && "$status" != "Succeeded" ]]; then
            log_error "Pod $name has status: $status (ready: $ready, restarts: $restarts)"
        fi
    done
}

# Debug infrastructure performance
debug_infrastructure_performance() {
    log_info "Analyzing infrastructure performance..."
    
    # Check node resource usage
    log_info "Node resource usage:"
    kubectl top nodes --use-protocol-buffers 2>/dev/null || {
        log_warn "Metrics server not available or no metrics found"
    }
    
    # Check pod resource usage
    log_info "Pod resource usage in namespace: $NAMESPACE"
    kubectl top pods -n "$NAMESPACE" --use-protocol-buffers 2>/dev/null || {
        log_warn "Metrics server not available or no metrics found"
    }
}

# Debug infrastructure connectivity
debug_infrastructure_connectivity() {
    log_info "Analyzing infrastructure connectivity..."
    
    # Check services
    log_info "Services in namespace: $NAMESPACE"
    kubectl get svc -n "$NAMESPACE"
    
    # Check endpoints
    log_info "Service endpoints in namespace: $NAMESPACE"
    kubectl get endpoints -n "$NAMESPACE"
    
    # Check network policies
    log_info "Network policies in namespace: $NAMESPACE"
    kubectl get networkpolicies -n "$NAMESPACE" || log_info "No network policies found"
}

# Debug infrastructure resources
debug_infrastructure_resources() {
    log_info "Analyzing infrastructure resources..."
    
    # Check resource quotas
    log_info "Resource quotas in namespace: $NAMESPACE"
    kubectl get resourcequota -n "$NAMESPACE" || log_info "No resource quotas found"
    
    # Check limit ranges
    log_info "Limit ranges in namespace: $NAMESPACE"
    kubectl get limitrange -n "$NAMESPACE" || log_info "No limit ranges found"
    
    # Check persistent volumes
    log_info "Persistent volume claims in namespace: $NAMESPACE"
    kubectl get pvc -n "$NAMESPACE"
}

# Debug all components
debug_all() {
    local issue_type="$1"
    
    log_info "Debugging all components for issue type: $issue_type"
    
    debug_agents "$issue_type"
    debug_workflows "$issue_type"
    debug_infrastructure "$issue_type"
}

# Main function
main() {
    parse_args "$@"
    
    log_info "Starting quick debug session..."
    log_info "Target: $TARGET"
    log_info "Issue Type: $ISSUE_TYPE"
    log_info "Namespace: $NAMESPACE"
    log_info "Time Range: $TIME_RANGE"
    
    check_dependencies
    
    case "$TARGET" in
        agents)
            debug_agents "$ISSUE_TYPE"
            ;;
        workflows)
            debug_workflows "$ISSUE_TYPE"
            ;;
        infrastructure)
            debug_infrastructure "$ISSUE_TYPE"
            ;;
        all)
            debug_all "$ISSUE_TYPE"
            ;;
        *)
            log_error "Unknown target: $TARGET"
            show_help
            exit 1
            ;;
    esac
    
    log_success "Debug session completed"
}

# Run main function with all arguments
main "$@"

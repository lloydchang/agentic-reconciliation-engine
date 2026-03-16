#!/bin/bash

# Automated Debugging Script for Distributed Reconciliation Tracking
# Provides comprehensive debugging for GitOps infrastructure dependency chains

set -euo pipefail
cd $(dirname $0)

# Configuration
NAMESPACE="${NAMESPACE:-flux-system}"
RESOURCE_NAME="${1:-}"
RESOURCE_TYPE="${2:-kustomization}"
VERBOSE="${VERBOSE:-false}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-table}" # table, json, yaml
CORRELATION_ID="${CORRELATION_ID:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_debug() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${PURPLE}[DEBUG]${NC} $1"
    fi
}

# Header function
print_header() {
    echo -e "${CYAN}================================================================${NC}"
    echo -e "${CYAN} GitOps Infrastructure Dependency Chain Debugging${NC}"
    echo -e "${CYAN}================================================================${NC}"
    echo "Namespace: $NAMESPACE"
    echo "Resource: $RESOURCE_NAME"
    echo "Type: $RESOURCE_TYPE"
    echo "Timestamp: $(date)"
    echo ""
}

# Check dependencies
check_dependencies() {
    log_info "Checking required dependencies..."
    
    local missing=()
    
    if ! command -v kubectl &> /dev/null; then
        missing+=("kubectl")
    fi
    
    if ! command -v jq &> /dev/null; then
        missing+=("jq")
    fi
    
    if ! command -v curl &> /dev/null; then
        missing+=("curl")
    fi
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing[*]}"
        log_info "Please install missing dependencies and try again"
        exit 1
    fi
    
    log_success "All dependencies found"
}

# Get Flux reconciliation status
get_flux_status() {
    log_info "Getting Flux reconciliation status..."
    
    local flux_status
    flux_status=$(kubectl get kustomizations -n "$NAMESPACE" -o json 2>/dev/null || echo '{"items": []}')
    
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        echo "$flux_status" | jq '.'
        return
    fi
    
    if [[ "$OUTPUT_FORMAT" == "yaml" ]]; then
        echo "$flux_status" | jq -r '.'
        return
    fi
    
    # Table format
    echo -e "${CYAN}Flux Kustomizations Status:${NC}"
    printf "%-30s %-15s %-20s %-30s\n" "NAME" "READY" "LAST APPLIED" "MESSAGE"
    printf "%-30s %-15s %-20s %-30s\n" "----" "-----" "------------" "-------"
    
    echo "$flux_status" | jq -r '.items[] | 
        "\(.metadata.name)\t\(
            .status.conditions[]? | select(.type=="Ready") | .status // "Unknown"
        )\t\(
            .status.lastAppliedRevision // "Unknown"
        )\t\(
            .status.conditions[]? | select(.type=="Ready") | .message // "No message"
        )"' | while IFS=$'\t' read -r name ready last_applied message; do
        local color="$NC"
        if [[ "$ready" == "True" ]]; then
            color="$GREEN"
        elif [[ "$ready" == "False" ]]; then
            color="$RED"
        else
            color="$YELLOW"
        fi
        
        printf "%-30s ${color}%-15s${NC} %-20s %-30s\n" "$name" "$ready" "$last_applied" "${message:0:30}"
    done
    echo ""
}

# Check controller logs
check_controller_logs() {
    log_info "Checking controller logs..."
    
    local controllers
    controllers=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/part-of=gitops-infra-control-plane -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -z "$controllers" ]]; then
        log_warning "No GitOps controllers found in namespace $NAMESPACE"
        return
    fi
    
    for controller in $controllers; do
        log_debug "Checking logs for controller: $controller"
        
        echo -e "${CYAN}Controller: $controller${NC}"
        
        # Get recent logs with correlation ID if provided
        local log_args=("--tail=50")
        if [[ -n "$CORRELATION_ID" ]]; then
            log_args+=("--since=1h")
        fi
        
        local logs
        logs=$(kubectl logs -n "$NAMESPACE" "$controller" "${log_args[@]}" 2>/dev/null || echo "No logs available")
        
        if [[ -n "$CORRELATION_ID" ]]; then
            echo "$logs" | grep -i "$CORRELATION_ID" || log_warning "No logs found for correlation ID: $CORRELATION_ID"
        else
            echo "$logs" | tail -20
        fi
        
        echo ""
    done
}

# Check resource dependencies
check_dependencies() {
    log_info "Checking resource dependencies..."
    
    if [[ -z "$RESOURCE_NAME" ]]; then
        log_warning "No resource name specified, skipping dependency check"
        return
    fi
    
    local resource
    resource=$(kubectl get "$RESOURCE_TYPE" -n "$NAMESPACE" "$RESOURCE_NAME" -o json 2>/dev/null || echo "{}")
    
    if [[ "$resource" == "{}" ]]; then
        log_error "Resource $RESOURCE_NAME of type $RESOURCE_TYPE not found"
        return
    fi
    
    echo -e "${CYAN}Dependency Analysis for: $RESOURCE_NAME${NC}"
    
    # Extract dependencies
    local deps
    deps=$(echo "$resource" | jq -r '.spec.dependsOn[]?.name // empty' 2>/dev/null || echo "")
    
    if [[ -z "$deps" ]]; then
        log_info "No dependencies found for $RESOURCE_NAME"
        return
    fi
    
    echo "Dependencies:"
    for dep in $deps; do
        local dep_status
        dep_status=$(kubectl get kustomization -n "$NAMESPACE" "$dep" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "Unknown")
        
        local color="$NC"
        if [[ "$dep_status" == "True" ]]; then
            color="$GREEN"
        elif [[ "$dep_status" == "False" ]]; then
            color="$RED"
        else
            color="$YELLOW"
        fi
        
        echo "  - $dep: ${color}$dep_status${NC}"
    done
    echo ""
}

# Check resource status
check_resource_status() {
    log_info "Checking resource status..."
    
    if [[ -z "$RESOURCE_NAME" ]]; then
        log_warning "No resource name specified, skipping status check"
        return
    fi
    
    local resource
    resource=$(kubectl get "$RESOURCE_TYPE" -n "$NAMESPACE" "$RESOURCE_NAME" -o json 2>/dev/null || echo "{}")
    
    if [[ "$resource" == "{}" ]]; then
        log_error "Resource $RESOURCE_NAME of type $RESOURCE_TYPE not found"
        return
    fi
    
    echo -e "${CYAN}Resource Status: $RESOURCE_NAME${NC}"
    
    # Get conditions
    local conditions
    conditions=$(echo "$resource" | jq -r '.status.conditions[]? | "\(.type): \(.status) - \(.message // "No message")"' 2>/dev/null || echo "No conditions found")
    
    echo "Conditions:"
    echo "$conditions" | while IFS= read -r condition; do
        local status=$(echo "$condition" | cut -d':' -f2 | cut -d' ' -f2)
        local color="$NC"
        
        if [[ "$status" == "True" ]]; then
            color="$GREEN"
        elif [[ "$status" == "False" ]]; then
            color="$RED"
        else
            color="$YELLOW"
        fi
        
        echo "  $condition" | sed "s/$status/${color}$status${NC}/"
    done
    
    # Get last applied revision
    local last_applied
    last_applied=$(echo "$resource" | jq -r '.status.lastAppliedRevision // "Unknown"' 2>/dev/null)
    echo "Last Applied Revision: $last_applied"
    
    # Get last handled reconcile
    local last_reconcile
    last_reconcile=$(echo "$resource" | jq -r '.status.lastHandledReconcileAt // "Unknown"' 2>/dev/null)
    echo "Last Handled Reconcile: $last_reconcile"
    echo ""
}

# Check cloud provider status
check_cloud_status() {
    log_info "Checking cloud provider resources..."
    
    local cloud_resources
    cloud_resources=$(kubectl get cloudresources -n "$NAMESPACE" -o json 2>/dev/null || echo '{"items": []}')
    
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        echo "$cloud_resources" | jq '.'
        return
    fi
    
    if [[ "$OUTPUT_FORMAT" == "yaml" ]]; then
        echo "$cloud_resources" | jq -r '.'
        return
    fi
    
    # Table format
    echo -e "${CYAN}Cloud Resources Status:${NC}"
    printf "%-25s %-15s %-20s %-30s\n" "NAME" "TYPE" "PROVIDER" "STATUS"
    printf "%-25s %-15s %-20s %-30s\n" "----" "----" "--------" "------"
    
    echo "$cloud_resources" | jq -r '.items[] | 
        "\(.metadata.name)\t\(.spec.kind)\t\(.metadata.labels.cloud // "Unknown")\t\(
            .status.conditions[]? | select(.type=="Ready") | .status // "Unknown"
        )"' 2>/dev/null | while IFS=$'\t' read -r name type provider status; do
        local color="$NC"
        if [[ "$status" == "True" ]]; then
            color="$GREEN"
        elif [[ "$status" == "False" ]]; then
            color="$RED"
        else
            color="$YELLOW"
        fi
        
        printf "%-25s %-15s %-20s ${color}%-30s${NC}\n" "$name" "$type" "$provider" "$status"
    done
    echo ""
}

# Check metrics from Prometheus
check_metrics() {
    log_info "Checking reconciliation metrics..."
    
    local prometheus_url="http://prometheus-operated.$NAMESPACE.svc.cluster.local:9090"
    
    # Check if Prometheus is accessible
    if ! curl -s --connect-timeout 5 "$prometheus_url/-/healthy" > /dev/null 2>&1; then
        log_warning "Prometheus is not accessible at $prometheus_url"
        return
    fi
    
    echo -e "${CYAN}Reconciliation Metrics (last 5 minutes):${NC}"
    
    # Success rate
    local success_rate
    success_rate=$(curl -s "$prometheus_url/api/v1/query?query=rate(flux_reconcile_success_total[5m])" | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
    echo "Success Rate: $success_rate/sec"
    
    # Failure rate
    local failure_rate
    failure_rate=$(curl -s "$prometheus_url/api/v1/query?query=rate(flux_reconcile_failure_total[5m])" | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
    echo "Failure Rate: $failure_rate/sec"
    
    # Duration P95
    local duration_p95
    duration_p95=$(curl -s "$prometheus_url/api/v1/query?query=histogram_quantile(0.95,rate(flux_reconcile_duration_seconds_bucket[5m]))" | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")
    echo "Duration P95: ${duration_p95}s"
    echo ""
}

# Generate debugging report
generate_report() {
    log_info "Generating debugging report..."
    
    local report_file="gitops-debug-report-$(date +%Y%m%d_%H%M%S).json"
    
    local report
    report=$(jq -n \
        --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --arg namespace "$NAMESPACE" \
        --arg resource_name "$RESOURCE_NAME" \
        --arg resource_type "$RESOURCE_TYPE" \
        --arg correlation_id "$CORRELATION_ID" \
        '{
            timestamp: $timestamp,
            namespace: $namespace,
            resource_name: $resource_name,
            resource_type: $resource_type,
            correlation_id: $correlation_id,
            flux_status: null,
            controller_logs: null,
            dependencies: null,
            resource_status: null,
            cloud_resources: null,
            metrics: null
        }')
    
    # Add Flux status
    local flux_status
    flux_status=$(kubectl get kustomizations -n "$NAMESPACE" -o json 2>/dev/null || echo '{"items": []}')
    report=$(echo "$report" | jq --argjson flux_status "$flux_status" '.flux_status = $flux_status')
    
    # Add controller logs (truncated)
    local controllers
    controllers=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/part-of=gitops-infra-control-plane -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    
    local logs_obj="{}"
    for controller in $controllers; do
        local logs
        logs=$(kubectl logs -n "$NAMESPACE" "$controller" --tail=10 2>/dev/null || echo "No logs")
        logs_obj=$(echo "$logs_obj" | jq --arg controller "$controller" --arg logs "$logs" '. + {($controller): $logs}')
    done
    
    report=$(echo "$report" | jq --argjson logs_obj "$logs_obj" '.controller_logs = $logs_obj')
    
    # Save report
    echo "$report" > "$report_file"
    log_success "Debugging report saved to: $report_file"
}

# Main execution
main() {
    print_header
    check_dependencies
    
    # Run debugging steps
    get_flux_status
    check_controller_logs
    check_dependencies
    check_resource_status
    check_cloud_status
    check_metrics
    
    # Generate report
    generate_report
    
    log_success "Debugging completed successfully"
    
    # Show summary
    echo -e "${CYAN}Summary:${NC}"
    echo "- Namespace: $NAMESPACE"
    echo "- Resource: $RESOURCE_NAME"
    echo "- Correlation ID: ${CORRELATION_ID:-'Not specified'}"
    echo "- Report generated: gitops-debug-report-$(date +%Y%m%d_%H%M%S).json"
    echo ""
    
    # Show next steps
    echo -e "${CYAN}Next Steps:${NC}"
    echo "1. Review the generated report for detailed analysis"
    echo "2. Check the dependency status dashboard at http://dependency-status.local"
    echo "3. Use correlation ID to trace specific reconciliation flows"
    echo "4. Check logs for any error messages or warnings"
}

# Help function
show_help() {
    echo "GitOps Infrastructure Dependency Chain Debugging Script"
    echo ""
    echo "Usage: $0 [RESOURCE_NAME] [RESOURCE_TYPE] [OPTIONS]"
    echo ""
    echo "Arguments:"
    echo "  RESOURCE_NAME    Name of the resource to debug (optional)"
    echo "  RESOURCE_TYPE     Type of resource (kustomization, helmrelease, etc.)"
    echo ""
    echo "Environment Variables:"
    echo "  NAMESPACE         Kubernetes namespace (default: flux-system)"
    echo "  VERBOSE           Enable verbose logging (true/false, default: false)"
    echo "  OUTPUT_FORMAT     Output format (table, json, yaml, default: table)"
    echo "  CORRELATION_ID    Correlation ID for tracing (optional)"
    echo ""
    echo "Examples:"
    echo "  $0 network-infrastructure kustomization"
    echo "  $0 app-helmrelease helmrelease NAMESPACE=gitops VERBOSE=true"
    echo "  $0 CORRELATION_ID=abc123-def456 OUTPUT_FORMAT=json"
    echo ""
}

# Parse command line arguments
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    show_help
    exit 0
fi

# Run main function
main "$@"

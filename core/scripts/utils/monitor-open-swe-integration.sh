#!/bin/bash

# Open SWE Integration Monitoring Script
# Monitors health, performance, and logs of Open SWE components

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

NAMESPACE="ai-infrastructure"
GATEWAY_NAME="open-swe-gateway"
MONITORING_INTERVAL=30

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_metric() {
    echo -e "${CYAN}[METRIC]${NC} $1"
}

# Function to check pod status
check_pod_status() {
    local component="$1"
    local expected_replicas="$2"

    local ready_pods
    ready_pods=$(kubectl get pods -n "$NAMESPACE" -l "component=$component" -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' | grep -o "True" | wc -l)

    if [[ "$ready_pods" -eq "$expected_replicas" ]]; then
        log_success "$component: $ready_pods/$expected_replicas pods ready"
        return 0
    else
        log_error "$component: $ready_pods/$expected_replicas pods ready (EXPECTED: $expected_replicas)"
        return 1
    fi
}

# Function to check service endpoints
check_service_endpoints() {
    local service_name="$1"
    local expected_ports="$2"

    for port in $expected_ports; do
        if kubectl get endpoints -n "$NAMESPACE" "$service_name" -o jsonpath="{.subsets[*].ports[?(@.port==$port)].port}" | grep -q "$port"; then
            log_success "$service_name:$port endpoint is healthy"
        else
            log_error "$service_name:$port endpoint is not healthy"
            return 1
        fi
    done
}

# Function to check gateway health
check_gateway_health() {
    local gateway_url="http://$GATEWAY_NAME.$NAMESPACE.svc.cluster.local:8080"

    # Check health endpoint
    if kubectl run health-check --image=curlimages/curl --rm -i --restart=Never --quiet -- \
        curl -f --max-time 10 "$gateway_url/health" &> /dev/null; then
        log_success "Gateway health check: PASSED"
        return 0
    else
        log_error "Gateway health check: FAILED"
        return 1
    fi
}

# Function to collect metrics
collect_metrics() {
    local gateway_url="http://$GATEWAY_NAME.$NAMESPACE.svc.cluster.local:8080"

    # Get basic metrics
    local metrics
    metrics=$(kubectl run metrics-check --image=curlimages/curl --rm -i --restart=Never --quiet -- \
        curl -f --max-time 10 "$gateway_url/metrics" 2>/dev/null || echo "")

    if [[ -n "$metrics" ]]; then
        # Parse key metrics
        local request_count
        request_count=$(echo "$metrics" | grep "http_requests_total" | head -1 | awk '{print $2}' || echo "0")
        log_metric "Total HTTP requests processed: $request_count"

        local webhook_count
        webhook_count=$(echo "$metrics" | grep "webhook_requests_total" | awk '{sum += $2} END {print sum}' || echo "0")
        log_metric "Total webhook requests processed: $webhook_count"

        local error_count
        error_count=$(echo "$metrics" | grep "http_requests_total.*status.*5[0-9][0-9]" | awk '{sum += $2} END {print sum}' || echo "0")
        log_metric "Total 5xx errors: $error_count"

        local active_workflows
        active_workflows=$(kubectl get workflows.temporal.io -n temporal --no-headers | wc -l 2>/dev/null || echo "0")
        log_metric "Active Temporal workflows: $active_workflows"
    else
        log_warning "Unable to collect metrics from gateway"
    fi
}

# Function to check resource usage
check_resource_usage() {
    log_info "Checking resource usage..."

    # Get pod resource usage
    kubectl top pods -n "$NAMESPACE" -l component=open-swe-integration --no-headers | while read -r line; do
        local pod_name cpu mem
        pod_name=$(echo "$line" | awk '{print $1}')
        cpu=$(echo "$line" | awk '{print $2}')
        mem=$(echo "$line" | awk '{print $3}')

        log_metric "Pod $pod_name - CPU: $cpu, Memory: $mem"
    done
}

# Function to check recent logs for errors
check_recent_logs() {
    local since="${1:-5m}"

    log_info "Checking recent logs for errors (last $since)..."

    # Check gateway logs for errors
    local error_count
    error_count=$(kubectl logs -n "$NAMESPACE" -l app=open-swe-gateway --since="$since" --tail=1000 2>/dev/null | grep -i error | wc -l)

    if [[ "$error_count" -gt 0 ]]; then
        log_warning "Found $error_count error(s) in gateway logs"
        kubectl logs -n "$NAMESPACE" -l app=open-swe-gateway --since="$since" --tail=1000 2>/dev/null | grep -i error | head -5
    else
        log_success "No errors found in recent gateway logs"
    fi
}

# Function to check webhook activity
check_webhook_activity() {
    log_info "Checking webhook activity..."

    # Check for recent webhook processing
    local recent_webhooks
    recent_webhooks=$(kubectl logs -n "$NAMESPACE" -l app=open-swe-gateway --since=1h --tail=1000 2>/dev/null | grep -c "webhook.*processed" || echo "0")

    if [[ "$recent_webhooks" -gt 0 ]]; then
        log_success "Processed $recent_webhooks webhooks in the last hour"
    else
        log_info "No webhooks processed in the last hour"
    fi

    # Check webhook sources
    local slack_webhooks
    slack_webhooks=$(kubectl logs -n "$NAMESPACE" -l app=open-swe-gateway --since=1h --tail=1000 2>/dev/null | grep -c "Slack webhook" || echo "0")
    local linear_webhooks
    linear_webhooks=$(kubectl logs -n "$NAMESPACE" -l app=open-swe-gateway --since=1h --tail=1000 2>/dev/null | grep -c "Linear webhook" || echo "0")
    local github_webhooks
    github_webhooks=$(kubectl logs -n "$NAMESPACE" -l app=open-swe-gateway --since=1h --tail=1000 2>/dev/null | grep -c "GitHub webhook" || echo "0")

    log_metric "Slack webhooks: $slack_webhooks"
    log_metric "Linear webhooks: $linear_webhooks"
    log_metric "GitHub webhooks: $github_webhooks"
}

# Function to check Temporal integration
check_temporal_integration() {
    log_info "Checking Temporal integration..."

    # Check Temporal frontend connectivity
    if kubectl get svc temporal-frontend -n temporal &> /dev/null; then
        log_success "Temporal frontend service is available"
    else
        log_error "Temporal frontend service not found"
        return 1
    fi

    # Check for workflow executions
    local workflow_count
    workflow_count=$(kubectl get workflows.temporal.io -n temporal --no-headers 2>/dev/null | wc -l || echo "0")

    if [[ "$workflow_count" -gt 0 ]]; then
        log_success "Found $workflow_count active workflows"
    else
        log_info "No active workflows found"
    fi
}

# Function to generate health report
generate_health_report() {
    local report_file="/tmp/open-swe-health-report-$(date +%Y%m%d-%H%M%S).txt"

    {
        echo "Open SWE Integration Health Report"
        echo "Generated: $(date)"
        echo "==================================="
        echo ""

        echo "Component Status:"
        echo "================="

        # Gateway pods
        if check_pod_status "open-swe-integration" 3 2>/dev/null; then
            echo "✅ Gateway Pods: HEALTHY"
        else
            echo "❌ Gateway Pods: UNHEALTHY"
        fi

        # Gateway service
        if check_service_endpoints "$GATEWAY_NAME" "8080 9090" 2>/dev/null; then
            echo "✅ Gateway Service: HEALTHY"
        else
            echo "❌ Gateway Service: UNHEALTHY"
        fi

        # Gateway health
        if check_gateway_health 2>/dev/null; then
            echo "✅ Gateway Health: HEALTHY"
        else
            echo "❌ Gateway Health: UNHEALTHY"
        fi

        # Temporal integration
        if check_temporal_integration 2>/dev/null; then
            echo "✅ Temporal Integration: HEALTHY"
        else
            echo "❌ Temporal Integration: UNHEALTHY"
        fi

        echo ""
        echo "Metrics Summary:"
        echo "================"
        collect_metrics

        echo ""
        echo "Recent Activity:"
        echo "================"
        check_webhook_activity

        echo ""
        echo "System Resources:"
        echo "================="
        kubectl top pods -n "$NAMESPACE" -l component=open-swe-integration --no-headers 2>/dev/null || echo "Resource metrics unavailable"

        echo ""
        echo "Recent Errors:"
        echo "=============="
        check_recent_logs "10m"

    } > "$report_file"

    log_success "Health report generated: $report_file"
    echo ""
    cat "$report_file"
}

# Function to start continuous monitoring
start_continuous_monitoring() {
    log_info "Starting continuous monitoring (interval: ${MONITORING_INTERVAL}s)..."
    log_info "Press Ctrl+C to stop monitoring"

    while true; do
        echo ""
        log_info "=== Health Check $(date +'%H:%M:%S') ==="

        # Quick health checks
        check_pod_status "open-swe-integration" 3 > /dev/null 2>&1 && echo "✅ Pods" || echo "❌ Pods"
        check_gateway_health > /dev/null 2>&1 && echo "✅ Health" || echo "❌ Health"

        # Show key metrics
        collect_metrics

        # Check for errors
        error_count=$(kubectl logs -n "$NAMESPACE" -l app=open-swe-gateway --since=30s --tail=100 2>/dev/null | grep -i error | wc -l)
        if [[ "$error_count" -gt 0 ]]; then
            log_warning "Found $error_count new errors in last 30 seconds"
        fi

        sleep "$MONITORING_INTERVAL"
    done
}

# Function to show dashboard
show_dashboard() {
    echo ""
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}                  Open SWE Integration Dashboard               ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Current status
    echo -e "${CYAN}Current Status:${NC}"
    check_pod_status "open-swe-integration" 3 2>/dev/null || true
    check_gateway_health 2>/dev/null || true
    echo ""

    # Key metrics
    echo -e "${CYAN}Key Metrics:${NC}"
    collect_metrics
    echo ""

    # Recent activity
    echo -e "${CYAN}Recent Activity (last hour):${NC}"
    check_webhook_activity
    echo ""

    # Resource usage
    echo -e "${CYAN}Resource Usage:${NC}"
    check_resource_usage
    echo ""

    # System info
    echo -e "${CYAN}System Information:${NC}"
    echo "Gateway URL: http://$GATEWAY_NAME.$NAMESPACE.svc.cluster.local:8080"
    echo "Metrics URL: http://$GATEWAY_NAME.$NAMESPACE.svc.cluster.local:9090/metrics"
    echo "Namespace: $NAMESPACE"
    echo ""
    echo -e "${CYAN}Active Components:${NC}"
    kubectl get pods -n "$NAMESPACE" -l component=open-swe-integration --no-headers -o custom-columns="NAME:.metadata.name,STATUS:.status.phase,AGE:.metadata.creationTimestamp" 2>/dev/null || echo "No components found"
}

# Main monitoring function
main() {
    local command="${1:-status}"

    case "$command" in
        "status")
            log_info "Checking Open SWE integration status..."
            check_pod_status "open-swe-integration" 3
            check_service_endpoints "$GATEWAY_NAME" "8080 9090"
            check_gateway_health
            check_temporal_integration
            collect_metrics
            check_recent_logs "5m"
            ;;
        "metrics")
            log_info "Collecting detailed metrics..."
            collect_metrics
            check_resource_usage
            ;;
        "logs")
            local since="${2:-1h}"
            log_info "Showing logs from last $since..."
            kubectl logs -n "$NAMESPACE" -l app=open-swe-gateway --since="$since" -f
            ;;
        "errors")
            log_info "Checking for errors..."
            check_recent_logs "1h"
            ;;
        "activity")
            log_info "Checking recent activity..."
            check_webhook_activity
            ;;
        "continuous")
            start_continuous_monitoring
            ;;
        "dashboard")
            show_dashboard
            ;;
        "report")
            generate_health_report
            ;;
        *)
            echo "Usage: $0 {status|metrics|logs|errors|activity|continuous|dashboard|report} [options]"
            echo ""
            echo "Commands:"
            echo "  status          Show current health status"
            echo "  metrics         Show detailed metrics"
            echo "  logs [duration] Show container logs (default: 1h)"
            echo "  errors          Check for recent errors"
            echo "  activity        Show recent webhook activity"
            echo "  continuous      Start continuous monitoring"
            echo "  dashboard       Show interactive dashboard"
            echo "  report          Generate comprehensive health report"
            echo ""
            echo "Examples:"
            echo "  $0 status"
            echo "  $0 logs 30m"
            echo "  $0 continuous"
            echo "  $0 dashboard"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

#!/bin/bash

# Argo Events Test Runner
# Comprehensive automated testing for Argo Events

set -euo pipefail

# Configuration
TEST_NAMESPACE="argo-events-test"
TIMEOUT=300
TEST_RESULTS_DIR="/tmp/argo-events-test-results"
WEBHOOK_PORT=12010

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ✓ $1"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ⚠ $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ✗ $1"
}

# Create results directory
setup_results() {
    mkdir -p "${TEST_RESULTS_DIR}"
    log "Test results will be saved to: ${TEST_RESULTS_DIR}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot access Kubernetes cluster"
        exit 1
    fi
    
    if ! kubectl get crd eventsources.argoproj.io &> /dev/null; then
        error "Argo Events CRDs not found"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Deploy test suite
deploy_test_suite() {
    log "Deploying test suite..."
    
    # Apply test suite
    if kubectl apply -f tests/argo-events/test-suite.yaml; then
        success "Test suite deployed"
    else
        error "Failed to deploy test suite"
        exit 1
    fi
    
    # Wait for Redis to be ready
    log "Waiting for Redis to be ready..."
    kubectl wait --for condition=available --timeout=60s deployment/redis-test -n "${TEST_NAMESPACE}"
    
    # Wait for event sources to be ready
    log "Waiting for event sources to be ready..."
    for es in test-webhook-source test-calendar-source test-redis-source; do
        kubectl wait --for condition=ready --timeout=120s eventsources/"${es}" -n "${TEST_NAMESPACE}" || {
            error "Event source ${es} not ready"
            exit 1
        }
    done
    
    # Wait for sensors to be ready
    log "Waiting for sensors to be ready..."
    for sensor in test-webhook-sensor test-calendar-sensor test-redis-sensor test-multi-dep-sensor test-filter-sensor test-transform-sensor; do
        kubectl wait --for condition=ready --timeout=120s sensors/"${sensor}" -n "${TEST_NAMESPACE}" || {
            error "Sensor ${sensor} not ready"
            exit 1
        }
    done
    
    success "All test components are ready"
}

# Test webhook functionality
test_webhook() {
    log "Testing webhook event source..."
    
    # Port forward webhook
    kubectl port-forward -n "${TEST_NAMESPACE}" svc/test-webhook-source-test-endpoint "${WEBHOOK_PORT}":12010 &
    PF_PID=$!
    
    # Wait for port forward
    sleep 5
    
    # Test cases
    local test_cases=(
        '{"type": "test", "message": "Basic test", "timestamp": "'$(date -Iseconds)'"}'
        '{"type": "validation", "priority": "high", "message": "High priority test", "timestamp": "'$(date -Iseconds)'"}'
        '{"type": "other", "message": "Should be filtered out", "timestamp": "'$(date -Iseconds)'"}'
        '{"type": "test", "priority": "critical", "message": "Critical test", "timestamp": "'$(date -Iseconds)'"}'
    )
    
    local webhook_results=0
    
    for test_case in "${test_cases[@]}"; do
        log "Sending webhook: ${test_case}"
        
        if curl -s -X POST "http://localhost:${WEBHOOK_PORT}/test" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer test-token-12345" \
            -d "${test_case}" > "${TEST_RESULTS_DIR}/webhook-response-$(date +%s).json"; then
            success "Webhook sent successfully"
            ((webhook_results++))
        else
            error "Webhook failed"
        fi
        
        sleep 2
    done
    
    # Clean up port forward
    kill $PF_PID 2>/dev/null || true
    
    log "Webhook test results: ${webhook_results}/${#test_cases[@]} successful"
    echo "${webhook_results}" > "${TEST_RESULTS_DIR}/webhook-score"
}

# Test Redis functionality
test_redis() {
    log "Testing Redis event source..."
    
    # Get Redis pod
    local redis_pod
    redis_pod=$(kubectl get pods -n "${TEST_NAMESPACE}" -l app=redis -o jsonpath='{.items[0].metadata.name}')
    
    if [[ -z "${redis_pod}" ]]; then
        error "Redis pod not found"
        return 1
    fi
    
    # Test cases
    local redis_messages=(
        'test-events:{"type": "redis-test", "message": "Redis test message"}'
        'test-notifications:{"type": "notification", "message": "Test notification"}'
        'test-events:{"type": "another-test", "message": "Another Redis test"}'
    )
    
    local redis_results=0
    
    for message in "${redis_messages[@]}"; do
        log "Publishing Redis message: ${message}"
        
        if kubectl exec -n "${TEST_NAMESPACE}" "${redis_pod}" -- redis-cli PUBLISH "${message}" > /dev/null; then
            success "Redis message published successfully"
            ((redis_results++))
        else
            error "Redis message failed"
        fi
        
        sleep 2
    done
    
    log "Redis test results: ${redis_results}/${#redis_messages[@]} successful"
    echo "${redis_results}" > "${TEST_RESULTS_DIR}/redis-score"
}

# Test calendar events (wait for scheduled events)
test_calendar() {
    log "Testing calendar event source (waiting for scheduled events)..."
    
    # Wait for 2 minutes to get calendar events
    local calendar_wait=120
    local calendar_results=0
    
    log "Waiting ${calendar_wait} seconds for calendar events..."
    
    for i in $(seq 1 $((calendar_wait / 10))); do
        sleep 10
        log "Waiting for calendar events... ($((i * 10))s elapsed)"
        
        # Check if calendar events were triggered
        local calendar_events
        calendar_events=$(kubectl logs -n "${TEST_NAMESPACE}" deployment/argo-events-controller --since=1m | grep -c "TEST: Calendar triggered" || echo "0")
        
        if [[ "${calendar_events}" -gt 0 ]]; then
            success "Calendar events detected: ${calendar_events}"
            calendar_results=1
            break
        fi
    done
    
    log "Calendar test results: ${calendar_results} events detected"
    echo "${calendar_results}" > "${TEST_RESULTS_DIR}/calendar-score"
}

# Test event filtering
test_filtering() {
    log "Testing event filtering..."
    
    # Send events that should be filtered
    local filter_tests=(
        '{"type": "test", "priority": "high", "message": "Should pass filter"}'
        '{"type": "validation", "priority": "critical", "message": "Should pass filter"}'
        '{"type": "other", "priority": "high", "message": "Should be filtered (wrong type)"}'
        '{"type": "test", "priority": "low", "message": "Should be filtered (wrong priority)"}'
    )
    
    local filter_results=0
    
    for test_case in "${filter_tests[@]}"; do
        log "Testing filter with: ${test_case}"
        
        # Port forward for webhook
        kubectl port-forward -n "${TEST_NAMESPACE}" svc/test-webhook-source-test-endpoint "${WEBHOOK_PORT}":12010 &
        local pf_pid=$!
        sleep 3
        
        if curl -s -X POST "http://localhost:${WEBHOOK_PORT}/test" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer test-token-12345" \
            -d "${test_case}" > /dev/null; then
            ((filter_results++))
        fi
        
        kill $pf_pid 2>/dev/null || true
        sleep 2
    done
    
    log "Filter test results: ${filter_results}/${#filter_tests[@]} events sent"
    echo "${filter_results}" > "${TEST_RESULTS_DIR}/filter-score"
}

# Test data transformation
test_transformation() {
    log "Testing data transformation..."
    
    # Send event with transformation data
    local transform_data='{"type": "test", "message": "transform me", "timestamp": "'$(date -Iseconds)'"}'
    
    # Port forward for webhook
    kubectl port-forward -n "${TEST_NAMESPACE}" svc/test-webhook-source-test-endpoint "${WEBHOOK_PORT}":12010 &
    local pf_pid=$!
    sleep 3
    
    local transform_result=0
    
    if curl -s -X POST "http://localhost:${WEBHOOK_PORT}/test" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer test-token-12345" \
        -d "${transform_data}" > /dev/null; then
        transform_result=1
        success "Transformation test event sent"
    else
        error "Transformation test failed"
    fi
    
    kill $pf_pid 2>/dev/null || true
    
    log "Transformation test result: ${transform_result}"
    echo "${transform_result}" > "${TEST_RESULTS_DIR}/transform-score"
}

# Check logs for test results
check_logs() {
    log "Checking logs for test results..."
    
    # Get controller logs
    kubectl logs -n "${TEST_NAMESPACE}" deployment/argo-events-controller --since=5m > "${TEST_RESULTS_DIR}/controller-logs.txt"
    
    # Count test events in logs
    local test_events
    test_events=$(grep -c "TEST:" "${TEST_RESULTS_DIR}/controller-logs.txt" || echo "0")
    
    log "Found ${test_events} test events in logs"
    echo "${test_events}" > "${TEST_RESULTS_DIR}/total-events"
    
    # Extract specific test results
    grep "TEST: Webhook received" "${TEST_RESULTS_DIR}/controller-logs.txt" > "${TEST_RESULTS_DIR}/webhook-events.txt" || true
    grep "TEST: Calendar triggered" "${TEST_RESULTS_DIR}/controller-logs.txt" > "${TEST_RESULTS_DIR}/calendar-events.txt" || true
    grep "TEST: Redis event from" "${TEST_RESULTS_DIR}/controller-logs.txt" > "${TEST_RESULTS_DIR}/redis-events.txt" || true
    grep "TEST: Filtered event" "${TEST_RESULTS_DIR}/controller-logs.txt" > "${TEST_RESULTS_DIR}/filter-events.txt" || true
    grep "TEST: Transformed data" "${TEST_RESULTS_DIR}/controller-logs.txt" > "${TEST_RESULTS_DIR}/transform-events.txt" || true
    grep "TEST: Multi-dependency triggered" "${TEST_RESULTS_DIR}/controller-logs.txt" > "${TEST_RESULTS_DIR}/multi-events.txt" || true
}

# Generate test report
generate_report() {
    log "Generating test report..."
    
    local report_file="${TEST_RESULTS_DIR}/test-report-$(date +%Y%m%d-%H%M%S).html"
    
    cat > "${report_file}" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Argo Events Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .success { color: green; font-weight: bold; }
        .warning { color: orange; font-weight: bold; }
        .error { color: red; font-weight: bold; }
        .score { font-size: 1.2em; font-weight: bold; }
        pre { background: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Argo Events Test Report</h1>
        <p>Generated: $(date)</p>
        <p>Test Namespace: ${TEST_NAMESPACE}</p>
    </div>
    
    <div class="section">
        <h2>Test Summary</h2>
        <div class="score">Total Events Processed: $(cat "${TEST_RESULTS_DIR}/total-events" 2>/dev/null || echo "0")</div>
    </div>
    
    <div class="section">
        <h2>Test Results</h2>
        <p><strong>Webhook Tests:</strong> $(cat "${TEST_RESULTS_DIR}/webhook-score" 2>/dev/null || echo "0") successful</p>
        <p><strong>Redis Tests:</strong> $(cat "${TEST_RESULTS_DIR}/redis-score" 2>/dev/null || echo "0") successful</p>
        <p><strong>Calendar Tests:</strong> $(cat "${TEST_RESULTS_DIR}/calendar-score" 2>/dev/null || echo "0") events detected</p>
        <p><strong>Filter Tests:</strong> $(cat "${TEST_RESULTS_DIR}/filter-score" 2>/dev/null || echo "0") events sent</p>
        <p><strong>Transform Tests:</strong> $(cat "${TEST_RESULTS_DIR}/transform-score" 2>/dev/null || echo "0") successful</p>
    </div>
    
    <div class="section">
        <h2>Event Details</h2>
        <h3>Webhook Events</h3>
        <pre>$(cat "${TEST_RESULTS_DIR}/webhook-events.txt" 2>/dev/null || echo "No webhook events found")</pre>
        
        <h3>Redis Events</h3>
        <pre>$(cat "${TEST_RESULTS_DIR}/redis-events.txt" 2>/dev/null || echo "No Redis events found")</pre>
        
        <h3>Calendar Events</h3>
        <pre>$(cat "${TEST_RESULTS_DIR}/calendar-events.txt" 2>/dev/null || echo "No calendar events found")</pre>
        
        <h3>Filter Events</h3>
        <pre>$(cat "${TEST_RESULTS_DIR}/filter-events.txt" 2>/dev/null || echo "No filter events found")</pre>
        
        <h3>Transform Events</h3>
        <pre>$(cat "${TEST_RESULTS_DIR}/transform-events.txt" 2>/dev/null || echo "No transform events found")</pre>
    </div>
    
    <div class="section">
        <h2>Component Status</h2>
        <h3>Event Sources</h3>
        <pre>$(kubectl get eventsources -n "${TEST_NAMESPACE}" -o wide)</pre>
        
        <h3>Sensors</h3>
        <pre>$(kubectl get sensors -n "${TEST_NAMESPACE}" -o wide)</pre>
        
        <h3>Pods</h3>
        <pre>$(kubectl get pods -n "${TEST_NAMESPACE}")</pre>
    </div>
    
    <div class="section">
        <h2>Full Logs</h3>
        <pre>$(tail -100 "${TEST_RESULTS_DIR}/controller-logs.txt" 2>/dev/null || echo "No logs available")</pre>
    </div>
</body>
</html>
EOF
    
    success "Test report generated: ${report_file}"
    echo "${report_file}" > "${TEST_RESULTS_DIR}/latest-report"
}

# Cleanup test environment
cleanup() {
    log "Cleaning up test environment..."
    
    # Delete test namespace
    if kubectl get namespace "${TEST_NAMESPACE}" &>/dev/null; then
        kubectl delete namespace "${TEST_NAMESPACE}" --ignore-not-found=true --timeout=60s
        success "Test namespace deleted"
    fi
    
    # Clean up any port forwards
    pkill -f "port-forward.*${TEST_NAMESPACE}" || true
    
    success "Cleanup completed"
}

# Show test summary
show_summary() {
    log "Test Summary:"
    echo
    
    local total_events
    total_events=$(cat "${TEST_RESULTS_DIR}/total-events" 2>/dev/null || echo "0")
    
    echo "=== Overall Results ==="
    echo "Total Events Processed: ${total_events}"
    echo
    
    echo "=== Component Status ==="
    echo "Event Sources: $(kubectl get eventsources -n "${TEST_NAMESPACE}" --no-headers | wc -l)"
    echo "Sensors: $(kubectl get sensors -n "${TEST_NAMESPACE}" --no-headers | wc -l)"
    echo "Pods: $(kubectl get pods -n "${TEST_NAMESPACE}" --no-headers | wc -l)"
    echo
    
    echo "=== Test Scores ==="
    echo "Webhook: $(cat "${TEST_RESULTS_DIR}/webhook-score" 2>/dev/null || echo "0")"
    echo "Redis: $(cat "${TEST_RESULTS_DIR}/redis-score" 2>/dev/null || echo "0")"
    echo "Calendar: $(cat "${TEST_RESULTS_DIR}/calendar-score" 2>/dev/null || echo "0")"
    echo "Filter: $(cat "${TEST_RESULTS_DIR}/filter-score" 2>/dev/null || echo "0")"
    echo "Transform: $(cat "${TEST_RESULTS_DIR}/transform-score" 2>/dev/null || echo "0")"
    echo
    
    if [[ -f "${TEST_RESULTS_DIR}/latest-report" ]]; then
        echo "=== Test Report ==="
        echo "Report: $(cat "${TEST_RESULTS_DIR}/latest-report")"
        echo
    fi
    
    if [[ "${total_events}" -gt 0 ]]; then
        success "✓ Tests completed successfully with ${total_events} events processed"
    else
        warning "⚠ Tests completed but no events were processed"
    fi
}

# Main execution
main() {
    local command="${1:-run}"
    
    case "${command}" in
        run)
            log "Starting Argo Events comprehensive test suite..."
            setup_results
            check_prerequisites
            deploy_test_suite
            test_webhook
            test_redis
            test_calendar
            test_filtering
            test_transformation
            check_logs
            generate_report
            show_summary
            ;;
        cleanup)
            cleanup
            ;;
        report)
            if [[ -f "${TEST_RESULTS_DIR}/latest-report" ]]; then
                log "Opening latest test report..."
                open "$(cat "${TEST_RESULTS_DIR}/latest-report")"
            else
                error "No test report found"
            fi
            ;;
        *)
            echo "Usage: $0 [run|cleanup|report]"
            echo "  run     - Run the complete test suite"
            echo "  cleanup - Clean up test environment"
            echo "  report  - Open the latest test report"
            exit 1
            ;;
    esac
}

# Trap for cleanup
trap cleanup EXIT

# Run main function
main "$@"

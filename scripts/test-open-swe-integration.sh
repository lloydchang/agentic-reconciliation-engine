#!/bin/bash

# Open SWE Integration Test Script
# Comprehensive testing of webhook integration and end-to-end functionality

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

NAMESPACE="ai-infrastructure"
GATEWAY_NAME="open-swe-gateway"
TEST_RESULTS_DIR="/tmp/open-swe-tests-$(date +%Y%m%d-%H%M%S)"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

log_info() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[$(date +'%H:%M:%S')]${NC} $1"
    ((TESTS_FAILED++))
}

log_test() {
    echo -e "${CYAN}[TEST]${NC} $1"
    ((TESTS_RUN++))
}

# Function to initialize test results
init_test_results() {
    mkdir -p "$TEST_RESULTS_DIR"
    echo "Open SWE Integration Test Results" > "${TEST_RESULTS_DIR}/summary.txt"
    echo "Started: $(date)" >> "${TEST_RESULTS_DIR}/summary.txt"
    echo "=================================" >> "${TEST_RESULTS_DIR}/summary.txt"
}

# Function to record test result
record_test_result() {
    local test_name="$1"
    local result="$2"
    local details="$3"

    echo "$test_name: $result" >> "${TEST_RESULTS_DIR}/summary.txt"
    if [[ -n "$details" ]]; then
        echo "  $details" >> "${TEST_RESULTS_DIR}/summary.txt"
    fi
}

# Function to test basic connectivity
test_basic_connectivity() {
    log_test "Basic Connectivity Test"

    local gateway_url="http://$GATEWAY_NAME.$NAMESPACE.svc.cluster.local:8080"

    log_info "Testing gateway accessibility..."

    # Test health endpoint
    if kubectl run connectivity-test --image=curlimages/curl --rm -i --restart=Never --quiet -- \
        timeout 30 curl -f "$gateway_url/health" &> /dev/null; then
        log_success "Gateway is accessible"
        record_test_result "Basic Connectivity" "PASSED" "Gateway health endpoint responded"
        return 0
    else
        log_error "Gateway is not accessible"
        record_test_result "Basic Connectivity" "FAILED" "Gateway health endpoint did not respond"
        return 1
    fi
}

# Function to test Slack webhook
test_slack_webhook() {
    log_test "Slack Webhook Test"

    local gateway_url="http://$GATEWAY_NAME.$NAMESPACE.svc.cluster.local:8080"

    log_info "Testing Slack webhook endpoint..."

    # Create test Slack payload
    local slack_payload='{
        "token": "test-token",
        "team_id": "T123456",
        "api_app_id": "A123456",
        "event": {
            "type": "app_mention",
            "user": "U123456",
            "text": "<@U789012> @openswe deploy infrastructure",
            "ts": "1234567890.123456",
            "channel": "C123456",
            "event_ts": "1234567890.123456"
        },
        "type": "event_callback",
        "event_id": "Ev123456",
        "event_time": 1234567890
    }'

    # Test webhook endpoint (should return 401/403 for invalid signature)
    local response
    response=$(kubectl run slack-test --image=curlimages/curl --rm -i --restart=Never --quiet -- \
        timeout 30 curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$gateway_url/webhooks/slack" \
        -H "Content-Type: application/json" \
        -d "$slack_payload" 2>/dev/null || echo "000")

    if [[ "$response" =~ ^(401|403)$ ]]; then
        log_success "Slack webhook endpoint is responding correctly (authentication required)"
        record_test_result "Slack Webhook" "PASSED" "Endpoint properly validates authentication"
        return 0
    elif [[ "$response" == "200" ]]; then
        log_warning "Slack webhook endpoint accepted request without authentication"
        record_test_result "Slack Webhook" "WARNING" "Endpoint should require authentication"
        return 0
    else
        log_error "Slack webhook endpoint not responding correctly (HTTP $response)"
        record_test_result "Slack Webhook" "FAILED" "Unexpected HTTP response: $response"
        return 1
    fi
}

# Function to test Linear webhook
test_linear_webhook() {
    log_test "Linear Webhook Test"

    local gateway_url="http://$GATEWAY_NAME.$NAMESPACE.svc.cluster.local:8080"

    log_info "Testing Linear webhook endpoint..."

    # Create test Linear payload
    local linear_payload='{
        "action": "update",
        "type": "Issue",
        "data": {
            "id": "issue-123",
            "title": "@openswe optimize costs",
            "description": "Please optimize cloud costs for production",
            "team": {
                "id": "team-123",
                "name": "Platform Team"
            },
            "creator": {
                "id": "user-123",
                "name": "Test User"
            }
        },
        "url": "https://linear.app/company/issue/ISSUE-123",
        "createdAt": "2024-01-01T00:00:00.000Z"
    }'

    # Test webhook endpoint
    local response
    response=$(kubectl run linear-test --image=curlimages/curl --rm -i --restart=Never --quiet -- \
        timeout 30 curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$gateway_url/webhooks/linear" \
        -H "Content-Type: application/json" \
        -H "X-Linear-Signature: test-signature" \
        -d "$linear_payload" 2>/dev/null || echo "000")

    if [[ "$response" =~ ^(401|403)$ ]]; then
        log_success "Linear webhook endpoint is responding correctly (authentication required)"
        record_test_result "Linear Webhook" "PASSED" "Endpoint properly validates authentication"
        return 0
    elif [[ "$response" == "200" ]]; then
        log_warning "Linear webhook endpoint accepted request without authentication"
        record_test_result "Linear Webhook" "WARNING" "Endpoint should require authentication"
        return 0
    else
        log_error "Linear webhook endpoint not responding correctly (HTTP $response)"
        record_test_result "Linear Webhook" "FAILED" "Unexpected HTTP response: $response"
        return 1
    fi
}

# Function to test GitHub webhook
test_github_webhook() {
    log_test "GitHub Webhook Test"

    local gateway_url="http://$GATEWAY_NAME.$NAMESPACE.svc.cluster.local:8080"

    log_info "Testing GitHub webhook endpoint..."

    # Create test GitHub payload
    local github_payload='{
        "action": "opened",
        "issue": {
            "number": 1,
            "title": "Infrastructure deployment request",
            "body": "@openswe deploy new environment",
            "user": {
                "login": "testuser",
                "id": 12345
            }
        },
        "repository": {
            "name": "test-repo",
            "full_name": "org/test-repo",
            "owner": {
                "login": "testorg"
            }
        },
        "sender": {
            "login": "testuser",
            "id": 12345
        }
    }'

    # Test webhook endpoint
    local response
    response=$(kubectl run github-test --image=curlimages/curl --rm -i --restart=Never --quiet -- \
        timeout 30 curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$gateway_url/webhooks/github" \
        -H "Content-Type: application/json" \
        -H "X-Hub-Signature-256: sha256=test-signature" \
        -H "X-GitHub-Event: issues" \
        -d "$github_payload" 2>/dev/null || echo "000")

    if [[ "$response" =~ ^(401|403)$ ]]; then
        log_success "GitHub webhook endpoint is responding correctly (authentication required)"
        record_test_result "GitHub Webhook" "PASSED" "Endpoint properly validates authentication"
        return 0
    elif [[ "$response" == "200" ]]; then
        log_warning "GitHub webhook endpoint accepted request without authentication"
        record_test_result "GitHub Webhook" "WARNING" "Endpoint should require authentication"
        return 0
    else
        log_error "GitHub webhook endpoint not responding correctly (HTTP $response)"
        record_test_result "GitHub Webhook" "FAILED" "Unexpected HTTP response: $response"
        return 1
    fi
}

# Function to test metrics endpoint
test_metrics_endpoint() {
    log_test "Metrics Endpoint Test"

    local metrics_url="http://$GATEWAY_NAME.$NAMESPACE.svc.cluster.local:9090/metrics"

    log_info "Testing metrics endpoint..."

    # Test metrics endpoint
    if kubectl run metrics-test --image=curlimages/curl --rm -i --restart=Never --quiet -- \
        timeout 30 curl -f "$metrics_url" &> /dev/null; then
        log_success "Metrics endpoint is accessible"
        record_test_result "Metrics Endpoint" "PASSED" "Prometheus metrics are available"
        return 0
    else
        log_error "Metrics endpoint is not accessible"
        record_test_result "Metrics Endpoint" "FAILED" "Prometheus metrics not available"
        return 1
    fi
}

# Function to test Temporal integration
test_temporal_integration() {
    log_test "Temporal Integration Test"

    log_info "Testing Temporal workflow integration..."

    # Check if Temporal service is accessible
    if kubectl get svc temporal-frontend -n temporal &> /dev/null; then
        log_success "Temporal frontend service is available"
        record_test_result "Temporal Integration" "PASSED" "Temporal service accessible"
        return 0
    else
        log_error "Temporal frontend service not found"
        record_test_result "Temporal Integration" "FAILED" "Temporal service not accessible"
        return 1
    fi
}

# Function to test concurrent requests
test_concurrent_requests() {
    log_test "Concurrent Requests Test"

    local gateway_url="http://$GATEWAY_NAME.$NAMESPACE.svc.cluster.local:8080"
    local concurrent_requests=5

    log_info "Testing $concurrent_requests concurrent requests..."

    # Launch concurrent health checks
    local pids=()
    local results=()

    for i in $(seq 1 "$concurrent_requests"); do
        (
            if kubectl run concurrent-test-$i --image=curlimages/curl --rm -i --restart=Never --quiet -- \
                timeout 30 curl -f "$gateway_url/health" &> /dev/null; then
                echo "success"
            else
                echo "failure"
            fi
        ) &
        pids+=($!)
    done

    # Wait for all requests to complete
    local success_count=0
    for pid in "${pids[@]}"; do
        wait "$pid"
        local result=$?
        if [[ $result -eq 0 ]]; then
            ((success_count++))
        fi
    done

    if [[ $success_count -eq $concurrent_requests ]]; then
        log_success "All concurrent requests succeeded"
        record_test_result "Concurrent Requests" "PASSED" "All $concurrent_requests requests successful"
        return 0
    else
        log_error "$success_count/$concurrent_requests concurrent requests succeeded"
        record_test_result "Concurrent Requests" "FAILED" "$success_count/$concurrent_requests requests successful"
        return 1
    fi
}

# Function to test resource limits
test_resource_limits() {
    log_test "Resource Limits Test"

    log_info "Testing resource usage and limits..."

    # Check pod resource usage
    local high_cpu_pods
    high_cpu_pods=$(kubectl top pods -n "$NAMESPACE" -l app="$GATEWAY_NAME" --no-headers 2>/dev/null | awk '$2 > 80 {print $1}' | wc -l)

    if [[ $high_cpu_pods -eq 0 ]]; then
        log_success "Resource usage is within limits"
        record_test_result "Resource Limits" "PASSED" "CPU usage within acceptable limits"
        return 0
    else
        log_warning "$high_cpu_pods pods have high CPU usage"
        record_test_result "Resource Limits" "WARNING" "$high_cpu_pods pods exceeding CPU limits"
        return 0
    fi
}

# Function to run load test
run_load_test() {
    log_test "Load Test"

    local gateway_url="http://$GATEWAY_NAME.$NAMESPACE.svc.cluster.local:8080"
    local duration=30  # seconds
    local concurrency=10

    log_info "Running load test (${concurrency} concurrent requests for ${duration}s)..."

    local start_time=$(date +%s)
    local end_time=$((start_time + duration))
    local success_count=0
    local total_count=0

    while [[ $(date +%s) -lt $end_time ]]; do
        # Launch batch of concurrent requests
        local pids=()
        for i in $(seq 1 "$concurrency"); do
            (
                if kubectl run load-test-$i-$RANDOM --image=curlimages/curl --rm -i --restart=Never --quiet -- \
                    timeout 10 curl -f "$gateway_url/health" &> /dev/null; then
                    echo "success"
                else
                    echo "failure"
                fi
            ) &
            pids+=($!)
            ((total_count++))
        done

        # Wait for batch to complete
        for pid in "${pids[@]}"; do
            if wait "$pid" 2>/dev/null; then
                ((success_count++))
            fi
        done

        # Small delay between batches
        sleep 0.1
    done

    local success_rate=$((success_count * 100 / total_count))

    if [[ $success_rate -ge 95 ]]; then
        log_success "Load test passed (${success_rate}% success rate)"
        record_test_result "Load Test" "PASSED" "${success_rate}% success rate over $total_count requests"
        return 0
    else
        log_error "Load test failed (${success_rate}% success rate)"
        record_test_result "Load Test" "FAILED" "${success_rate}% success rate over $total_count requests"
        return 1
    fi
}

# Function to generate test report
generate_test_report() {
    log_info "Generating comprehensive test report..."

    {
        echo "Open SWE Integration Test Results"
        echo "Generated: $(date)"
        echo "================================="
        echo ""
        echo "Test Summary:"
        echo "============="
        echo "Total Tests Run: $TESTS_RUN"
        echo "Tests Passed: $TESTS_PASSED"
        echo "Tests Failed: $TESTS_FAILED"
        echo "Success Rate: $((TESTS_PASSED * 100 / TESTS_RUN))%"
        echo ""

        if [[ -f "${TEST_RESULTS_DIR}/summary.txt" ]]; then
            echo "Detailed Results:"
            echo "================="
            cat "${TEST_RESULTS_DIR}/summary.txt"
        fi

        echo ""
        echo "System Information:"
        echo "==================="
        echo "Test Directory: $TEST_RESULTS_DIR"
        echo "Namespace: $NAMESPACE"
        echo "Gateway: $GATEWAY_NAME"
        echo ""
        echo "Pod Status:"
        kubectl get pods -n "$NAMESPACE" -l app="$GATEWAY_NAME" --no-headers -o custom-columns="NAME:.metadata.name,STATUS:.status.phase,READY:.status.conditions[?(@.type=='Ready')].status" 2>/dev/null || echo "Unable to get pod status"
        echo ""
        echo "Service Status:"
        kubectl get svc -n "$NAMESPACE" -l app="$GATEWAY_NAME" --no-headers 2>/dev/null || echo "Unable to get service status"

    } > "${TEST_RESULTS_DIR}/full-report.txt"

    log_success "Test report saved to: ${TEST_RESULTS_DIR}/full-report.txt"
    echo ""
    cat "${TEST_RESULTS_DIR}/full-report.txt"
}

# Function to cleanup test resources
cleanup_test_resources() {
    log_info "Cleaning up test resources..."

    # Remove any test pods that might still be running
    kubectl delete pods -n "$NAMESPACE" -l "job-name=*-test-*" --ignore-not-found=true >/dev/null 2>&1 || true

    log_success "Test cleanup completed"
}

# Main test function
main() {
    local test_type="${1:-basic}"

    init_test_results

    log_info "Starting Open SWE Integration Tests..."
    log_info "Test Results Directory: $TEST_RESULTS_DIR"

    # Set up cleanup on exit
    trap cleanup_test_resources EXIT

    case "$test_type" in
        "basic")
            log_info "Running basic connectivity tests..."
            test_basic_connectivity
            test_metrics_endpoint
            ;;
        "webhooks")
            log_info "Running webhook integration tests..."
            test_slack_webhook
            test_linear_webhook
            test_github_webhook
            ;;
        "integration")
            log_info "Running integration tests..."
            test_temporal_integration
            test_concurrent_requests
            test_resource_limits
            ;;
        "load")
            log_info "Running load tests..."
            run_load_test
            ;;
        "performance")
            log_info "Running performance tests..."
            test_concurrent_requests
            run_load_test
            ;;
        "all")
            log_info "Running all tests..."
            test_basic_connectivity
            test_slack_webhook
            test_linear_webhook
            test_github_webhook
            test_metrics_endpoint
            test_temporal_integration
            test_concurrent_requests
            test_resource_limits
            run_load_test
            ;;
        "report")
            generate_test_report
            ;;
        *)
            echo "Usage: $0 {basic|webhooks|integration|load|performance|all|report}"
            echo ""
            echo "Test Types:"
            echo "  basic        - Basic connectivity and health checks"
            echo "  webhooks     - Webhook endpoint validation"
            echo "  integration  - Temporal and concurrent request tests"
            echo "  load         - High-load performance testing"
            echo "  performance  - Combined performance tests"
            echo "  all          - Complete test suite"
            echo "  report       - Generate test report from previous run"
            echo ""
            echo "Examples:"
            echo "  $0 basic"
            echo "  $0 webhooks"
            echo "  $0 all"
            exit 1
            ;;
    esac

    # Generate final report
    generate_test_report

    # Summary
    echo ""
    log_info "Test Summary: $TESTS_PASSED passed, $TESTS_FAILED failed out of $TESTS_RUN tests"

    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_success "🎉 All tests passed!"
        exit 0
    else
        log_error "❌ Some tests failed. Check the report for details."
        exit 1
    fi
}

# Run main function
main "$@"

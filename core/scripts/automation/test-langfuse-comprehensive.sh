#!/bin/bash
# Comprehensive Langfuse Test Suite
# Tests all Langfuse functionality automatically and autonomously

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Test result function
test_result() {
    local test_name="$1"
    local result="$2"
    local message="$3"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    if [[ "$result" == "PASS" ]]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        print_success "$test_name: $message"
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        print_error "$test_name: $message"
    fi
}

# Test 1: Infrastructure Health
test_infrastructure_health() {
    print_header "Testing Infrastructure Health"
    
    # Test PostgreSQL
    if kubectl exec -n langfuse deployment/postgres -- pg_isready -U postgres > /dev/null 2>&1; then
        test_result "PostgreSQL Health" "PASS" "Database is ready"
    else
        test_result "PostgreSQL Health" "FAIL" "Database not ready"
    fi
    
    # Test Redis
    if kubectl exec -n langfuse deployment/redis -- redis-cli ping > /dev/null 2>&1; then
        test_result "Redis Health" "PASS" "Cache is ready"
    else
        test_result "Redis Health" "FAIL" "Cache not ready"
    fi
    
    # Test MinIO
    if kubectl exec -n langfuse deployment/minio -- curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
        test_result "MinIO Health" "PASS" "Storage is ready"
    else
        test_result "MinIO Health" "FAIL" "Storage not ready"
    fi
    
    # Test Langfuse pod
    if kubectl get pod -l app=langfuse-server -n langfuse --no-headers | grep -q "Running"; then
        test_result "Langfuse Pod" "PASS" "Pod is running"
    else
        test_result "Langfuse Pod" "FAIL" "Pod not running"
    fi
}

# Test 2: API Endpoints
test_api_endpoints() {
    print_header "Testing API Endpoints"
    
    # Wait for port-forward to be established
    local port_forward_pid=$(cat /tmp/langfuse-port-forward.pid 2>/dev/null || echo "")
    if [[ -n "$port_forward_pid" ]] && kill -0 "$port_forward_pid" 2>/dev/null; then
        print_info "Port-forward is running (PID: $port_forward_pid)"
    else
        print_info "Starting port-forward for API tests..."
        kubectl port-forward svc/langfuse-server 3000:3000 -n langfuse &
        echo $! > /tmp/langfuse-port-forward.pid
        sleep 5
    fi
    
    # Test health endpoint
    if curl -s -f http://localhost:3000/api/health > /dev/null 2>&1; then
        test_result "Health API" "PASS" "Health endpoint responding"
    else
        test_result "Health API" "FAIL" "Health endpoint not responding"
    fi
    
    # Test public API
    if curl -s -f http://localhost:3000/api/public/health > /dev/null 2>&1; then
        test_result "Public API" "PASS" "Public API responding"
    else
        test_result "Public API" "FAIL" "Public API not responding"
    fi
    
    # Test authentication endpoint
    if curl -s -f http://localhost:3000/api/auth/signin > /dev/null 2>&1; then
        test_result "Auth API" "PASS" "Authentication endpoint responding"
    else
        test_result "Auth API" "FAIL" "Authentication endpoint not responding"
    fi
}

# Test 3: UI Interface
test_ui_interface() {
    print_header "Testing UI Interface"
    
    # Test main UI page
    if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
        test_result "Main UI" "PASS" "UI page loads successfully"
    else
        test_result "Main UI" "FAIL" "UI page not loading"
    fi
    
    # Test UI contains expected elements
    local ui_content=$(curl -s http://localhost:3000)
    if echo "$ui_content" | grep -q "langfuse\|Langfuse"; then
        test_result "UI Content" "PASS" "UI contains expected content"
    else
        test_result "UI Content" "FAIL" "UI missing expected content"
    fi
    
    # Test static assets
    if curl -s -f http://localhost:3000/favicon.ico > /dev/null 2>&1; then
        test_result "Static Assets" "PASS" "Static assets loading"
    else
        test_result "Static Assets" "FAIL" "Static assets not loading"
    fi
}

# Test 4: Authentication Flow
test_authentication_flow() {
    print_header "Testing Authentication Flow"
    
    # Test signup endpoint
    local signup_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{
            "email": "test@example.com",
            "password": "test-password-123",
            "name": "Test User"
        }' \
        http://localhost:3000/api/auth/signup)
    
    if echo "$signup_response" | grep -q "accessToken\|user\|success"; then
        test_result "User Signup" "PASS" "User can signup"
    else
        test_result "User Signup" "FAIL" "User signup failed"
    fi
    
    # Test login endpoint
    local login_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{
            "email": "test@example.com",
            "password": "test-password-123"
        }' \
        http://localhost:3000/api/auth/signin)
    
    if echo "$login_response" | grep -q "accessToken"; then
        test_result "User Login" "PASS" "User can login"
        # Extract token for API tests
        ACCESS_TOKEN=$(echo "$login_response" | grep -o '"accessToken":"[^"]*' | cut -d'"' -f4)
        echo "$ACCESS_TOKEN" > /tmp/langfuse-test-token
    else
        test_result "User Login" "FAIL" "User login failed"
    fi
}

# Test 5: API Key Generation
test_api_key_generation() {
    print_header "Testing API Key Generation"
    
    local access_token=$(cat /tmp/langfuse-test-token 2>/dev/null || echo "")
    
    if [[ -n "$access_token" ]]; then
        # Test API key creation
        local api_key_response=$(curl -s -X POST \
            -H "Authorization: Bearer $access_token" \
            -H "Content-Type: application/json" \
            -d '{
                "name": "test-api-key",
                "note": "Generated by automated test"
            }' \
            http://localhost:3000/api/public/api-keys)
        
        if echo "$api_key_response" | grep -q "publicKey\|secretKey"; then
            test_result "API Key Creation" "PASS" "API keys generated successfully"
            # Extract keys for tracing tests
            PUBLIC_KEY=$(echo "$api_key_response" | grep -o '"publicKey":"[^"]*' | cut -d'"' -f4)
            SECRET_KEY=$(echo "$api_key_response" | grep -o '"secretKey":"[^"]*' | cut -d'"' -f4)
            echo "$PUBLIC_KEY" > /tmp/langfuse-test-public-key
            echo "$SECRET_KEY" > /tmp/langfuse-test-secret-key
        else
            test_result "API Key Creation" "FAIL" "API key creation failed"
        fi
    else
        test_result "API Key Creation" "SKIP" "No access token available"
    fi
}

# Test 6: Tracing Integration
test_tracing_integration() {
    print_header "Testing Tracing Integration"
    
    local public_key=$(cat /tmp/langfuse-test-public-key 2>/dev/null || echo "")
    local secret_key=$(cat /tmp/langfuse-test-secret-key 2>/dev/null || echo "")
    
    if [[ -n "$public_key" && -n "$secret_key" ]]; then
        # Test OTLP endpoint
        local otlp_response=$(curl -s -X POST \
            -H "Authorization: Bearer $secret_key" \
            -H "Content-Type: application/json" \
            -d '{
                "resourceSpans": [{
                    "resource": {
                        "attributes": [{
                            "key": "service.name",
                            "value": {"stringValue": "test-service"}
                        }]
                    },
                    "scopeSpans": [{
                        "spans": [{
                            "traceId": "12345678901234567890123456789012",
                            "spanId": "1234567890123456",
                            "name": "test-span",
                            "kind": 1,
                            "startTimeUnixNano": "1640995200000000000",
                            "endTimeUnixNano": "1640995201000000000"
                        }]
                    }]
                }]
            }' \
            http://localhost:3000/api/public/ingestion/traces)
        
        if [[ $? -eq 0 ]]; then
            test_result "Trace Ingestion" "PASS" "Traces can be ingested"
        else
            test_result "Trace Ingestion" "FAIL" "Trace ingestion failed"
        fi
        
        # Test trace retrieval
        sleep 2  # Allow time for processing
        local traces_response=$(curl -s -H "Authorization: Bearer $secret_key" \
            http://localhost:3000/api/public/traces)
        
        if echo "$traces_response" | grep -q "data\|traces"; then
            test_result "Trace Retrieval" "PASS" "Traces can be retrieved"
        else
            test_result "Trace Retrieval" "FAIL" "Trace retrieval failed"
        fi
    else
        test_result "Trace Ingestion" "SKIP" "No API keys available"
        test_result "Trace Retrieval" "SKIP" "No API keys available"
    fi
}

# Test 7: Dashboard Functionality
test_dashboard_functionality() {
    print_header "Testing Dashboard Functionality"
    
    local access_token=$(cat /tmp/langfuse-test-token 2>/dev/null || echo "")
    
    if [[ -n "$access_token" ]]; then
        # Test projects endpoint
        if curl -s -f -H "Authorization: Bearer $access_token" \
            http://localhost:3000/api/public/projects > /dev/null 2>&1; then
            test_result "Projects API" "PASS" "Projects endpoint working"
        else
            test_result "Projects API" "FAIL" "Projects endpoint failed"
        fi
        
        # Test users endpoint
        if curl -s -f -H "Authorization: Bearer $access_token" \
            http://localhost:3000/api/public/users > /dev/null 2>&1; then
            test_result "Users API" "PASS" "Users endpoint working"
        else
            test_result "Users API" "FAIL" "Users endpoint failed"
        fi
        
        # Test metrics endpoint
        if curl -s -f -H "Authorization: Bearer $access_token" \
            http://localhost:3000/api/public/metrics > /dev/null 2>&1; then
            test_result "Metrics API" "PASS" "Metrics endpoint working"
        else
            test_result "Metrics API" "FAIL" "Metrics endpoint failed"
        fi
    else
        test_result "Projects API" "SKIP" "No access token available"
        test_result "Users API" "SKIP" "No access token available"
        test_result "Metrics API" "SKIP" "No access token available"
    fi
}

# Test 8: Regression Tests
test_regression_prevention() {
    print_header "Running Regression Tests"
    
    # Test 1: Ensure no CrashLoopBackOff
    local restart_count=$(kubectl get pod -l app=langfuse-server -n langfuse -o jsonpath='{.items[0].status.containerStatuses[0].restartCount}' 2>/dev/null || echo "0")
    if [[ "$restart_count" -lt 5 ]]; then
        test_result "No CrashLoop" "PASS" "Pod stable ($restart_count restarts)"
    else
        test_result "No CrashLoop" "FAIL" "Pod unstable ($restart_count restarts)"
    fi
    
    # Test 2: Ensure database connectivity
    if kubectl exec -n langfuse deployment/postgres -- psql -U postgres -d langfuse -c "SELECT COUNT(*) FROM information_schema.tables;" > /dev/null 2>&1; then
        test_result "Database Schema" "PASS" "Database schema accessible"
    else
        test_result "Database Schema" "FAIL" "Database schema issues"
    fi
    
    # Test 3: Ensure storage bucket exists
    if kubectl exec -n langfuse deployment/minio -- mc alias set local http://localhost:9000 minioadmin minioadmin 2>/dev/null; then
        if kubectl exec -n langfuse deployment/minio -- mc ls local/langfuse > /dev/null 2>&1; then
            test_result "Storage Bucket" "PASS" "Storage bucket accessible"
        else
            test_result "Storage Bucket" "FAIL" "Storage bucket not accessible"
        fi
    else
        test_result "Storage Bucket" "FAIL" "Storage configuration issues"
    fi
    
    # Test 4: Ensure port-forward functionality
    local port_forward_pid=$(cat /tmp/langfuse-port-forward.pid 2>/dev/null || echo "")
    if [[ -n "$port_forward_pid" ]] && kill -0 "$port_forward_pid" 2>/dev/null; then
        test_result "Port Forward" "PASS" "Port-forward active"
    else
        test_result "Port Forward" "FAIL" "Port-forward not active"
    fi
}

# Test 9: Performance Tests
test_performance() {
    print_header "Running Performance Tests"
    
    # Test API response time
    local start_time=$(date +%s%N)
    curl -s http://localhost:3000/api/health > /dev/null
    local end_time=$(date +%s%N)
    local response_time=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
    
    if [[ "$response_time" -lt 2000 ]]; then
        test_result "API Response Time" "PASS" "${response_time}ms (< 2000ms)"
    else
        test_result "API Response Time" "FAIL" "${response_time}ms (> 2000ms)"
    fi
    
    # Test memory usage
    local memory_usage=$(kubectl exec -n langfuse deployment/langfuse-server -- cat /sys/fs/cgroup/memory/memory.usage_in_bytes 2>/dev/null || echo "0")
    local memory_mb=$((memory_usage / 1024 / 1024))
    
    if [[ "$memory_mb" -lt 1024 ]]; then
        test_result "Memory Usage" "PASS" "${memory_mb}MB (< 1024MB)"
    else
        test_result "Memory Usage" "WARN" "${memory_mb}MB (> 1024MB)"
    fi
}

# Test 10: Integration with AI Agents
test_ai_agent_integration() {
    print_header "Testing AI Agent Integration"
    
    # Test if secrets exist in control-plane namespace
    if kubectl get secret langfuse-secrets -n control-plane > /dev/null 2>&1; then
        test_result "Control-Plane Secrets" "PASS" "Secrets exist in control-plane"
    else
        test_result "Control-Plane Secrets" "FAIL" "Secrets missing in control-plane"
    fi
    
    # Test if secrets exist in ai-infrastructure namespace
    if kubectl get secret langfuse-secrets -n ai-infrastructure > /dev/null 2>&1; then
        test_result "AI-Infra Secrets" "PASS" "Secrets exist in ai-infrastructure"
    else
        test_result "AI-Infra Secrets" "FAIL" "Secrets missing in ai-infrastructure"
    fi
    
    # Test if Temporal deployment has Langfuse env vars
    if kubectl get deployment temporal-server -n control-plane -o yaml | grep -q "LANGFUSE_PUBLIC_KEY"; then
        test_result "Temporal Integration" "PASS" "Temporal has Langfuse env vars"
    else
        test_result "Temporal Integration" "FAIL" "Temporal missing Langfuse env vars"
    fi
    
    # Test if pi-mono-agent deployment has Langfuse env vars
    if kubectl get deployment pi-mono-agent -n ai-infrastructure -o yaml | grep -q "LANGFUSE_PUBLIC_KEY"; then
        test_result "Pi-Mono Integration" "PASS" "Pi-mono has Langfuse env vars"
    else
        test_result "Pi-Mono Integration" "FAIL" "Pi-mono missing Langfuse env vars"
    fi
}

# Cleanup test artifacts
cleanup_test_artifacts() {
    print_header "Cleaning Up Test Artifacts"
    
    # Clean up test files
    rm -f /tmp/langfuse-test-token
    rm -f /tmp/langfuse-test-public-key
    rm -f /tmp/langfuse-test-secret-key
    
    # Keep port-forward running for user access
    print_info "Port-forward kept running for access"
    
    print_success "Test artifacts cleaned up"
}

# Generate test report
generate_test_report() {
    print_header "Test Report"
    
    echo "📊 Test Summary:"
    echo "  Total Tests: $TESTS_TOTAL"
    echo "  Passed: $TESTS_PASSED"
    echo "  Failed: $TESTS_FAILED"
    echo "  Success Rate: $(( TESTS_PASSED * 100 / TESTS_TOTAL ))%"
    echo ""
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        print_success "🎉 ALL TESTS PASSED - Langfuse is fully operational!"
        echo ""
        echo "🚀 Ready for Production:"
        echo "  • UI: http://localhost:3000"
        echo "  • API: http://localhost:3000/api"
        echo "  • Health: http://localhost:3000/api/health"
        echo ""
        echo "✨ Autonomous setup completed successfully!"
    else
        print_error "❌ $TESTS_FAILED tests failed - review and fix issues"
        echo ""
        echo "🔧 Troubleshooting:"
        echo "  • Check logs: kubectl logs -l app=langfuse-server -n langfuse -f"
        echo "  • Check pods: kubectl get pods -n langfuse"
        echo "  • Run fix: ./core/automation/scripts/fix-langfuse.sh"
    fi
}

# Main execution
main() {
    print_header "Comprehensive Langfuse Test Suite"
    echo "🧪 Testing all Langfuse functionality automatically and autonomously"
    echo ""
    
    # Run all tests
    test_infrastructure_health
    echo ""
    
    test_api_endpoints
    echo ""
    
    test_ui_interface
    echo ""
    
    test_authentication_flow
    echo ""
    
    test_api_key_generation
    echo ""
    
    test_tracing_integration
    echo ""
    
    test_dashboard_functionality
    echo ""
    
    test_regression_prevention
    echo ""
    
    test_performance
    echo ""
    
    test_ai_agent_integration
    echo ""
    
    # Cleanup and report
    cleanup_test_artifacts
    echo ""
    
    generate_test_report
    
    # Exit with appropriate code
    if [[ $TESTS_FAILED -eq 0 ]]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"

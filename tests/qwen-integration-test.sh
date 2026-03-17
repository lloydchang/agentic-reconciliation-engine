#!/bin/bash

# Qwen LLM Integration Test Suite
# Tests Qwen LLM integration with K8sGPT and Flux

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TEST_NAMESPACE="qwen-test"
QWEN_NAMESPACE="qwen-system"
FLUX_NAMESPACE="flux-system"
TEST_TIMEOUT=300

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

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

# Test reporting
report_test() {
    local test_name="$1"
    local result="$2"
    local details="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [[ "$result" == "PASS" ]]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        log_success "✓ $test_name - $details"
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        log_error "✗ $test_name - $details"
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up test resources..."
    kubectl delete namespace "$TEST_NAMESPACE" --ignore-not-found=true || true
    kubectl delete test-resources --all --ignore-not-found=true || true
}

# Setup test environment
setup_test_environment() {
    log_info "Setting up Qwen test environment..."
    
    # Create test namespace
    kubectl create namespace "$TEST_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Wait for namespace to be ready
    kubectl wait --for=condition=Active namespace "$TEST_NAMESPACE" --timeout=60s
    
    log_success "Qwen test environment setup completed"
}

# Test 1: Qwen Namespace Check
test_qwen_namespace() {
    log_info "Testing Qwen namespace..."
    
    if kubectl get namespace "$QWEN_NAMESPACE" &> /dev/null; then
        local labels=$(kubectl get namespace "$QWEN_NAMESPACE" -o jsonpath='{.metadata.labels}')
        report_test "Qwen Namespace" "PASS" "Namespace exists with labels: $labels"
    else
        report_test "Qwen Namespace" "FAIL" "Qwen namespace not found"
    fi
}

# Test 2: Qwen Deployment Health
test_qwen_deployment_health() {
    log_info "Testing Qwen deployment health..."
    
    if kubectl get deployment qwen-llm -n "$QWEN_NAMESPACE" &> /dev/null; then
        # Check deployment status
        local replicas=$(kubectl get deployment qwen-llm -n "$QWEN_NAMESPACE" -o jsonpath='{.spec.replicas}')
        local ready_replicas=$(kubectl get deployment qwen-llm -n "$QWEN_NAMESPACE" -o jsonpath='{.status.readyReplicas}')
        
        if [[ "$ready_replicas" == "$replicas" ]]; then
            report_test "Qwen Deployment Health" "PASS" "All $replicas replicas are ready"
        else
            report_test "Qwen Deployment Health" "FAIL" "$ready_replicas/$replicas replicas ready"
        fi
    else
        report_test "Qwen Deployment Health" "FAIL" "Qwen deployment not found"
    fi
}

# Test 3: Qwen Service Connectivity
test_qwen_service_connectivity() {
    log_info "Testing Qwen service connectivity..."
    
    if kubectl get svc qwen-llm -n "$QWEN_NAMESPACE" &> /dev/null; then
        # Test service connectivity
        if kubectl port-forward -n "$QWEN_NAMESPACE" svc/qwen-llm 8000:8000 &> /dev/null & then
            sleep 5
            
            # Test health endpoint
            if curl -s --max-time 10 http://localhost:8000/health | grep -q "healthy\|ok\|ready"; then
                report_test "Qwen Service Connectivity" "PASS" "Service is accessible and healthy"
            else
                report_test "Qwen Service Connectivity" "FAIL" "Service health check failed"
            fi
            
            pkill -f "kubectl port-forward" || true
        else
            report_test "Qwen Service Connectivity" "FAIL" "Cannot establish port-forward"
        fi
    else
        report_test "Qwen Service Connectivity" "FAIL" "Qwen service not found"
    fi
}

# Test 4: Qwen Model Loading
test_qwen_model_loading() {
    log_info "Testing Qwen model loading..."
    
    if kubectl get pods -n "$QWEN_NAMESPACE" -l app.kubernetes.io/name=qwen-llm --no-headers | grep -q "Running"; then
        # Check model logs
        local pod_name=$(kubectl get pods -n "$QWEN_NAMESPACE" -l app.kubernetes.io/name=qwen-llm -o jsonpath='{.items[0].metadata.name}')
        local model_logs=$(kubectl logs "$pod_name" -n "$QWEN_NAMESPACE" --tail=50)
        
        if echo "$model_logs" | grep -q "model loaded\|Model loaded\|ready to serve"; then
            report_test "Qwen Model Loading" "PASS" "Model is loaded and ready"
        else
            report_test "Qwen Model Loading" "FAIL" "Model loading not confirmed in logs"
        fi
    else
        report_test "Qwen Model Loading" "FAIL" "No running Qwen pods found"
    fi
}

# Test 5: Qwen API Functionality
test_qwen_api_functionality() {
    log_info "Testing Qwen API functionality..."
    
    # Setup port-forward
    if kubectl port-forward -n "$QWEN_NAMESPACE" svc/qwen-llm 8000:8000 &> /dev/null & then
        sleep 5
        
        # Test chat endpoint
        local response=$(curl -s --max-time 30 -X POST \
            -H "Content-Type: application/json" \
            -d '{"prompt": "Hello, can you respond with just the word OK?"}' \
            http://localhost:8000/chat || echo "")
        
        if echo "$response" | grep -q "OK\|ok"; then
            report_test "Qwen API Functionality" "PASS" "API responds correctly to prompts"
        else
            report_test "Qwen API Functionality" "FAIL" "API response unexpected: $response"
        fi
        
        pkill -f "kubectl port-forward" || true
    else
        report_test "Qwen API Functionality" "FAIL" "Cannot connect to API"
    fi
}

# Test 6: Qwen Performance Metrics
test_qwen_performance_metrics() {
    log_info "Testing Qwen performance metrics..."
    
    if kubectl get svc qwen-llm-metrics -n "$QWEN_NAMESPACE" &> /dev/null; then
        # Setup port-forward for metrics
        if kubectl port-forward -n "$QWEN_NAMESPACE" svc/qwen-llm-metrics 9090:9090 &> /dev/null & then
            sleep 5
            
            # Test metrics endpoint
            if curl -s --max-time 10 http://localhost:9090/metrics | grep -q "qwen_\|model_\|response_"; then
                report_test "Qwen Performance Metrics" "PASS" "Metrics are available"
            else
                report_test "Qwen Performance Metrics" "FAIL" "No metrics found"
            fi
            
            pkill -f "kubectl port-forward" || true
        else
            report_test "Qwen Performance Metrics" "FAIL" "Cannot connect to metrics endpoint"
        fi
    else
        report_test "Qwen Performance Metrics" "SKIP" "Metrics service not found"
    fi
}

# Test 7: Qwen Resource Usage
test_qwen_resource_usage() {
    log_info "Testing Qwen resource usage..."
    
    if kubectl get pods -n "$QWEN_NAMESPACE" -l app.kubernetes.io/name=qwen-llm --no-headers | grep -q "Running"; then
        local pod_name=$(kubectl get pods -n "$QWEN_NAMESPACE" -l app.kubernetes.io/name=qwen-llm -o jsonpath='{.items[0].metadata.name}')
        
        # Check resource requests and limits
        local cpu_request=$(kubectl get pod "$pod_name" -n "$QWEN_NAMESPACE" -o jsonpath='{.spec.containers[0].resources.requests.cpu}')
        local memory_request=$(kubectl get pod "$pod_name" -n "$QWEN_NAMESPACE" -o jsonpath='{.spec.containers[0].resources.requests.memory}')
        local cpu_limit=$(kubectl get pod "$pod_name" -n "$QWEN_NAMESPACE" -o jsonpath='{.spec.containers[0].resources.limits.cpu}')
        local memory_limit=$(kubectl get pod "$pod_name" -n "$QWEN_NAMESPACE" -o jsonpath='{.spec.containers[0].resources.limits.memory}')
        
        if [[ -n "$cpu_request" && -n "$memory_request" && -n "$cpu_limit" && -n "$memory_limit" ]]; then
            report_test "Qwen Resource Usage" "PASS" "Resources configured: CPU($cpu_request/$cpu_limit) Memory($memory_request/$memory_limit)"
        else
            report_test "Qwen Resource Usage" "FAIL" "Incomplete resource configuration"
        fi
    else
        report_test "Qwen Resource Usage" "FAIL" "No running Qwen pods found"
    fi
}

# Test 8: K8sGPT Qwen Integration
test_k8sgpt_qwen_integration() {
    log_info "Testing K8sGPT Qwen integration..."
    
    if kubectl get deployment k8sgpt -n "$FLUX_NAMESPACE" &> /dev/null; then
        # Check K8sGPT configuration
        local qwen_url=$(kubectl get secret qwen-connection-secret -n "$FLUX_NAMESPACE" -o jsonpath='{.data.apiUrl}' | base64 --decode || echo "")
        
        if [[ "$qwen_url" == *"qwen-llm"* ]]; then
            report_test "K8sGPT Qwen Integration" "PASS" "K8sGPT configured to use Qwen at $qwen_url"
        else
            report_test "K8sGPT Qwen Integration" "FAIL" "K8sGPT not properly configured for Qwen"
        fi
    else
        report_test "K8sGPT Qwen Integration" "SKIP" "K8sGPT deployment not found"
    fi
}

# Test 9: K8sGPT Analysis with Qwen
test_k8sgpt_analysis_with_qwen() {
    log_info "Testing K8sGPT analysis with Qwen..."
    
    if kubectl get deployment k8sgpt -n "$FLUX_NAMESPACE" &> /dev/null; then
        # Create test resources for analysis
        cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: test-pod-for-analysis
  namespace: $TEST_NAMESPACE
spec:
  containers:
  - name: test-container
    image: nginx:latest
    securityContext:
      runAsRoot: true
      allowPrivilegeEscalation: true
EOF
        
        # Wait for analysis
        sleep 30
        
        # Check K8sGPT logs for Qwen analysis
        local analysis_logs=$(kubectl logs -n "$FLUX_NAMESPACE" deployment/k8sgpt --since=2m || echo "")
        
        if echo "$analysis_logs" | grep -q "analysis\|qwen\|llm"; then
            report_test "K8sGPT Analysis with Qwen" "PASS" "K8sGPT performed analysis with Qwen"
        else
            report_test "K8sGPT Analysis with Qwen" "FAIL" "No Qwen analysis found in logs"
        fi
        
        # Cleanup
        kubectl delete pod test-pod-for-analysis -n "$TEST_NAMESPACE" --ignore-not-found=true
    else
        report_test "K8sGPT Analysis with Qwen" "SKIP" "K8sGPT deployment not found"
    fi
}

# Test 10: Qwen Model Persistence
test_qwen_model_persistence() {
    log_info "Testing Qwen model persistence..."
    
    if kubectl get pvc qwen-model-pvc -n "$QWEN_NAMESPACE" &> /dev/null; then
        local storage_size=$(kubectl get pvc qwen-model-pvc -n "$QWEN_NAMESPACE" -o jsonpath='{.spec.resources.requests.storage}')
        local storage_class=$(kubectl get pvc qwen-model-pvc -n "$QWEN_NAMESPACE" -o jsonpath='{.spec.storageClassName}')
        local status=$(kubectl get pvc qwen-model-pvc -n "$QWEN_NAMESPACE" -o jsonpath='{.status.phase}')
        
        if [[ "$status" == "Bound" ]]; then
            report_test "Qwen Model Persistence" "PASS" "PVC is Bound: $storage_size ($storage_class)"
        else
            report_test "Qwen Model Persistence" "FAIL" "PVC status: $status"
        fi
    else
        report_test "Qwen Model Persistence" "FAIL" "Model PVC not found"
    fi
}

# Test 11: Qwen Configuration
test_qwen_configuration() {
    log_info "Testing Qwen configuration..."
    
    if kubectl get configmap qwen-config -n "$QWEN_NAMESPACE" &> /dev/null; then
        local config_data=$(kubectl get configmap qwen-config -n "$QWEN_NAMESPACE" -o jsonpath='{.data.config\.yaml}')
        
        if echo "$config_data" | grep -q "model\|server\|logging\|monitoring"; then
            report_test "Qwen Configuration" "PASS" "Configuration contains required sections"
        else
            report_test "Qwen Configuration" "FAIL" "Configuration missing required sections"
        fi
    else
        report_test "Qwen Configuration" "FAIL" "Qwen configmap not found"
    fi
}

# Test 12: Qwen Security Context
test_qwen_security_context() {
    log_info "Testing Qwen security context..."
    
    if kubectl get deployment qwen-llm -n "$QWEN_NAMESPACE" &> /dev/null; then
        local run_as_non_root=$(kubectl get deployment qwen-llm -n "$QWEN_NAMESPACE" -o jsonpath='{.spec.template.spec.securityContext.runAsNonRoot}')
        local read_only_fs=$(kubectl get deployment qwen-llm -n "$QWEN_NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].securityContext.readOnlyRootFilesystem}')
        
        if [[ "$run_as_non_root" == "true" && "$read_only_fs" == "true" ]]; then
            report_test "Qwen Security Context" "PASS" "Security context properly configured"
        else
            report_test "Qwen Security Context" "FAIL" "Security context not properly configured"
        fi
    else
        report_test "Qwen Security Context" "FAIL" "Qwen deployment not found"
    fi
}

# Test 13: Qwen Network Policies
test_qwen_network_policies() {
    log_info "Testing Qwen network policies..."
    
    local netpols=$(kubectl get networkpolicy -n "$QWEN_NAMESPACE" --no-headers | wc -l)
    
    if [[ $netpols -gt 0 ]]; then
        report_test "Qwen Network Policies" "PASS" "Found $netpols network policies"
    else
        report_test "Qwen Network Policies" "FAIL" "No network policies found"
    fi
}

# Test 14: Qwen Scaling
test_qwen_scaling() {
    log_info "Testing Qwen scaling..."
    
    if kubectl get deployment qwen-llm -n "$QWEN_NAMESPACE" &> /dev/null; then
        local current_replicas=$(kubectl get deployment qwen-llm -n "$QWEN_NAMESPACE" -o jsonpath='{.spec.replicas}')
        
        # Test scaling up
        kubectl scale deployment qwen-llm -n "$QWEN_NAMESPACE" --replicas=2
        
        # Wait for scaling
        if kubectl wait --for=condition=available deployment/qwen-llm -n "$QWEN_NAMESPACE" --timeout=120s; then
            report_test "Qwen Scaling" "PASS" "Successfully scaled from $current_replicas to 2 replicas"
            
            # Scale back to original
            kubectl scale deployment qwen-llm -n "$QWEN_NAMESPACE" --replicas="$current_replicas"
        else
            report_test "Qwen Scaling" "FAIL" "Scaling failed"
        fi
    else
        report_test "Qwen Scaling" "FAIL" "Qwen deployment not found"
    fi
}

# Test 15: Qwen Error Handling
test_qwen_error_handling() {
    log_info "Testing Qwen error handling..."
    
    if kubectl port-forward -n "$QWEN_NAMESPACE" svc/qwen-llm 8000:8000 &> /dev/null & then
        sleep 5
        
        # Test with invalid request
        local response=$(curl -s --max-time 10 -X POST \
            -H "Content-Type: application/json" \
            -d '{}' \
            http://localhost:8000/chat || echo "")
        
        if echo "$response" | grep -q "error\|invalid\|missing"; then
            report_test "Qwen Error Handling" "PASS" "Properly handles invalid requests"
        else
            report_test "Qwen Error Handling" "FAIL" "Does not handle invalid requests properly"
        fi
        
        pkill -f "kubectl port-forward" || true
    else
        report_test "Qwen Error Handling" "FAIL" "Cannot connect to Qwen service"
    fi
}

# Test 16: Qwen Load Testing
test_qwen_load_testing() {
    log_info "Testing Qwen load handling..."
    
    if kubectl port-forward -n "$QWEN_NAMESPACE" svc/qwen-llm 8000:8000 &> /dev/null & then
        sleep 5
        
        # Send multiple concurrent requests
        local success_count=0
        local total_requests=5
        
        for i in $(seq 1 $total_requests); do
            if curl -s --max-time 15 -X POST \
                -H "Content-Type: application/json" \
                -d '{"prompt": "Test request '$i'"}' \
                http://localhost:8000/chat | grep -q "Test\|response" & then
                success_count=$((success_count + 1))
            fi &
        done
        
        wait
        
        if [[ $success_count -eq $total_requests ]]; then
            report_test "Qwen Load Testing" "PASS" "Handled all $total_requests concurrent requests"
        else
            report_test "Qwen Load Testing" "FAIL" "Only handled $success_count/$total_requests requests"
        fi
        
        pkill -f "kubectl port-forward" || true
    else
        report_test "Qwen Load Testing" "FAIL" "Cannot connect to Qwen service"
    fi
}

# Test 17: Qwen Model Version
test_qwen_model_version() {
    log_info "Testing Qwen model version..."
    
    if kubectl get pods -n "$QWEN_NAMESPACE" -l app.kubernetes.io/name=qwen-llm --no-headers | grep -q "Running"; then
        local pod_name=$(kubectl get pods -n "$QWEN_NAMESPACE" -l app.kubernetes.io/name=qwen-llm -o jsonpath='{.items[0].metadata.name}')
        local pod_logs=$(kubectl logs "$pod_name" -n "$QWEN_NAMESPACE" --tail=20)
        
        if echo "$pod_logs" | grep -q "qwen2.5\|Qwen2.5\|7b"; then
            report_test "Qwen Model Version" "PASS" "Correct Qwen model version detected"
        else
            report_test "Qwen Model Version" "FAIL" "Unexpected or missing model version"
        fi
    else
        report_test "Qwen Model Version" "FAIL" "No running Qwen pods found"
    fi
}

# Test 18: Qwen Integration with Flux
test_qwen_flux_integration() {
    log_info "Testing Qwen integration with Flux..."
    
    # Check if Flux recognizes Qwen resources
    local qwen_kustomizations=$(kubectl get kustomization -n "$FLUX_NAMESPACE" -o jsonpath='{.items[*].metadata.name}' | tr ' ' '\n' | grep -c "qwen\|ai" || echo "0")
    
    if [[ $qwen_kustomizations -gt 0 ]]; then
        report_test "Qwen Flux Integration" "PASS" "Found $qwen_kustomizations Qwen-related kustomizations"
    else
        report_test "Qwen Flux Integration" "FAIL" "No Qwen-related kustomizations found"
    fi
}

# Test 19: Qwen Auto-fix Integration
test_qwen_autofix_integration() {
    log_info "Testing Qwen auto-fix integration..."
    
    if kubectl get deployment flux-webhook -n "$FLUX_NAMESPACE" &> /dev/null; then
        # Check webhook configuration for Qwen integration
        local webhook_config=$(kubectl get deployment flux-webhook -n "$FLUX_NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].env[*].value}' | tr ' ' '\n')
        
        if echo "$webhook_config" | grep -q "qwen\|Qwen"; then
            report_test "Qwen Auto-fix Integration" "PASS" "Webhook configured for Qwen integration"
        else
            report_test "Qwen Auto-fix Integration" "FAIL" "Webhook not configured for Qwen"
        fi
    else
        report_test "Qwen Auto-fix Integration" "SKIP" "Flux webhook not found"
    fi
}

# Test 20: Qwen End-to-End Workflow
test_qwen_end_to_end_workflow() {
    log_info "Testing Qwen end-to-end workflow..."
    
    # Create problematic resource
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: problematic-pod
  namespace: $TEST_NAMESPACE
  labels:
    app: test
spec:
  containers:
  - name: container-with-issues
    image: nginx:latest
    securityContext:
      runAsRoot: true
      allowPrivilegeEscalation: true
    resources: {}
EOF
    
    # Wait for analysis and potential auto-fix
    sleep 60
    
    # Check if K8sGPT analyzed and provided suggestions
    local k8sgpt_logs=$(kubectl logs -n "$FLUX_NAMESPACE" deployment/k8sgpt --since=2m || echo "")
    
    if echo "$k8sgpt_logs" | grep -q "analysis\|security\|recommendation"; then
        report_test "Qwen End-to-End Workflow" "PASS" "End-to-end workflow completed successfully"
    else
        report_test "Qwen End-to-End Workflow" "FAIL" "End-to-end workflow did not complete"
    fi
    
    # Cleanup
    kubectl delete pod problematic-pod -n "$TEST_NAMESPACE" --ignore-not-found=true
}

# Main test execution
main() {
    log_info "Starting Qwen LLM Integration Test Suite"
    echo ""
    
    # Setup
    setup_test_environment
    
    # Run all tests
    test_qwen_namespace
    test_qwen_deployment_health
    test_qwen_service_connectivity
    test_qwen_model_loading
    test_qwen_api_functionality
    test_qwen_performance_metrics
    test_qwen_resource_usage
    test_k8sgpt_qwen_integration
    test_k8sgpt_analysis_with_qwen
    test_qwen_model_persistence
    test_qwen_configuration
    test_qwen_security_context
    test_qwen_network_policies
    test_qwen_scaling
    test_qwen_error_handling
    test_qwen_load_testing
    test_qwen_model_version
    test_qwen_flux_integration
    test_qwen_autofix_integration
    test_qwen_end_to_end_workflow
    
    # Cleanup
    cleanup
    
    # Print results
    echo ""
    log_info "Qwen Integration Test Results:"
    echo "==============================="
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $TESTS_PASSED"
    echo "Failed: $TESTS_FAILED"
    echo "Success Rate: $(( TESTS_PASSED * 100 / TOTAL_TESTS ))%"
    echo ""
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_success "All Qwen integration tests passed! 🎉"
        exit 0
    else
        log_error "Some Qwen integration tests failed. Please review the output above."
        exit 1
    fi
}

# Run main function
main "$@"

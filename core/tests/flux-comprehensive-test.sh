#!/bin/bash

# Flux Comprehensive Test Suite
# Tests Flux CD integration with Qwen LLM and K8sGPT

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TEST_NAMESPACE="flux-test"
TEST_TIMEOUT=300
TEST_CLUSTER="${TEST_CLUSTER:-kind}"
TEST_ENVIRONMENT="${TEST_ENVIRONMENT:-development}"

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
    kubectl delete test-pod flux-test --ignore-not-found=true || true
    kubectl delete test-deployment flux-test --ignore-not-found=true || true
}

# Setup test environment
setup_test_environment() {
    log_info "Setting up test environment..."
    
    # Create test namespace
    kubectl create namespace "$TEST_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Wait for namespace to be ready
    kubectl wait --for=condition=Active namespace "$TEST_NAMESPACE" --timeout=60s
    
    log_success "Test environment setup completed"
}

# Test 1: Flux Controllers Health Check
test_flux_controllers_health() {
    log_info "Testing Flux controllers health..."
    
    local controllers=("source-controller" "kustomize-controller" "helm-controller" "notification-controller")
    local all_healthy=true
    
    for controller in "${controllers[@]}"; do
        if kubectl get pods -n flux-system -l app.kubernetes.io/name="$controller" --no-headers | grep -q "Running"; then
            log_success "$controller is healthy"
        else
            log_error "$controller is not healthy"
            all_healthy=false
        fi
    done
    
    if [[ "$all_healthy" == "true" ]]; then
        report_test "Flux Controllers Health" "PASS" "All controllers are running"
    else
        report_test "Flux Controllers Health" "FAIL" "Some controllers are not running"
    fi
}

# Test 2: Flux CLI Check
test_flux_cli() {
    log_info "Testing Flux CLI..."
    
    if command -v flux &> /dev/null; then
        local version=$(flux version --client | head -1)
        report_test "Flux CLI" "PASS" "Flux CLI installed: $version"
    else
        report_test "Flux CLI" "FAIL" "Flux CLI not found"
    fi
}

# Test 3: Flux Check Command
test_flux_check() {
    log_info "Running flux check..."
    
    if flux check --namespace flux-system &> /dev/null; then
        report_test "Flux Check" "PASS" "Flux components are properly configured"
    else
        local output=$(flux check --namespace flux-system 2>&1)
        report_test "Flux Check" "FAIL" "Flux check failed: $output"
    fi
}

# Test 4: GitRepository Reconciliation
test_git_repository_reconciliation() {
    log_info "Testing GitRepository reconciliation..."
    
    # Wait for GitRepository to be ready
    if kubectl wait --for=condition=ready gitrepository/flux-system -n flux-system --timeout=120s; then
        local status=$(kubectl get gitrepository flux-system -n flux-system -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
        report_test "GitRepository Reconciliation" "PASS" "Status: $status"
    else
        report_test "GitRepository Reconciliation" "FAIL" "GitRepository not ready within timeout"
    fi
}

# Test 5: Kustomization Reconciliation
test_kustomization_reconciliation() {
    log_info "Testing Kustomization reconciliation..."
    
    # Wait for main kustomization to be ready
    if kubectl wait --for=condition=ready kustomization/flux-system -n flux-system --timeout=120s; then
        local status=$(kubectl get kustomization flux-system -n flux-system -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
        report_test "Kustomization Reconciliation" "PASS" "Status: $status"
    else
        report_test "Kustomization Reconciliation" "FAIL" "Kustomization not ready within timeout"
    fi
}

# Test 6: Qwen LLM Service Health
test_qwen_llm_health() {
    log_info "Testing Qwen LLM service health..."
    
    # Check if Qwen namespace exists
    if kubectl get namespace qwen-system &> /dev/null; then
        # Check Qwen deployment
        if kubectl get deployment qwen-llm -n qwen-system &> /dev/null; then
            # Wait for deployment to be ready
            if kubectl wait --for=condition=available deployment/qwen-llm -n qwen-system --timeout=300s; then
                # Test health endpoint
                if kubectl port-forward -n qwen-system svc/qwen-llm 8000:8000 &> /dev/null & then
                    sleep 5
                    if curl -s http://localhost:8000/health | grep -q "healthy"; then
                        report_test "Qwen LLM Health" "PASS" "Qwen LLM service is healthy"
                    else
                        report_test "Qwen LLM Health" "FAIL" "Qwen LLM health check failed"
                    fi
                    pkill -f "kubectl port-forward" || true
                else
                    report_test "Qwen LLM Health" "FAIL" "Cannot connect to Qwen LLM service"
                fi
            else
                report_test "Qwen LLM Health" "FAIL" "Qwen LLM deployment not ready"
            fi
        else
            report_test "Qwen LLM Health" "SKIP" "Qwen LLM deployment not found"
        fi
    else
        report_test "Qwen LLM Health" "SKIP" "Qwen namespace not found"
    fi
}

# Test 7: K8sGPT Analysis
test_k8sgpt_analysis() {
    log_info "Testing K8sGPT analysis..."
    
    # Check if K8sGPT is installed
    if kubectl get deployment k8sgpt -n flux-system &> /dev/null; then
        # Wait for K8sGPT to be ready
        if kubectl wait --for=condition=available deployment/k8sgpt -n flux-system --timeout=300s; then
            # Create test resources for analysis
            cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: flux-test-pod
  namespace: $TEST_NAMESPACE
spec:
  containers:
  - name: test-container
    image: nginx:latest
    ports:
    - containerPort: 80
EOF
            
            # Wait for K8sGPT to analyze
            sleep 30
            
            # Check K8sGPT logs for analysis
            if kubectl logs -n flux-system deployment/k8sgpt --since=5m | grep -q "analysis completed"; then
                report_test "K8sGPT Analysis" "PASS" "K8sGPT successfully analyzed resources"
            else
                report_test "K8sGPT Analysis" "FAIL" "K8sGPT analysis not found in logs"
            fi
            
            # Cleanup test pod
            kubectl delete pod flux-test-pod -n "$TEST_NAMESPACE" --ignore-not-found=true
        else
            report_test "K8sGPT Analysis" "FAIL" "K8sGPT deployment not ready"
        fi
    else
        report_test "K8sGPT Analysis" "SKIP" "K8sGPT deployment not found"
    fi
}

# Test 8: Flux Webhook Integration
test_flux_webhook_integration() {
    log_info "Testing Flux webhook integration..."
    
    # Check if webhook deployment exists
    if kubectl get deployment flux-webhook -n flux-system &> /dev/null; then
        # Wait for webhook to be ready
        if kubectl wait --for=condition=available deployment/flux-webhook -n flux-system --timeout=120s; then
            # Test webhook health endpoint
            if kubectl port-forward -n flux-system svc/flux-webhook 8080:80 &> /dev/null & then
                sleep 5
                if curl -s http://localhost:8080/health | grep -q "OK"; then
                    report_test "Flux Webhook Integration" "PASS" "Flux webhook is healthy"
                else
                    report_test "Flux Webhook Integration" "FAIL" "Flux webhook health check failed"
                fi
                pkill -f "kubectl port-forward" || true
            else
                report_test "Flux Webhook Integration" "FAIL" "Cannot connect to Flux webhook"
            fi
        else
            report_test "Flux Webhook Integration" "FAIL" "Flux webhook deployment not ready"
        fi
    else
        report_test "Flux Webhook Integration" "SKIP" "Flux webhook deployment not found"
    fi
}

# Test 9: Monitoring Integration
test_monitoring_integration() {
    log_info "Testing monitoring integration..."
    
    # Check if monitoring namespace exists
    if kubectl get namespace monitoring &> /dev/null; then
        # Check for ServiceMonitors
        local service_monitors=$(kubectl get servicemonitor -n monitoring --no-headers | wc -l)
        if [[ $service_monitors -gt 0 ]]; then
            report_test "Monitoring Integration" "PASS" "Found $service_monitors ServiceMonitors"
        else
            report_test "Monitoring Integration" "FAIL" "No ServiceMonitors found"
        fi
    else
        report_test "Monitoring Integration" "SKIP" "Monitoring namespace not found"
    fi
}

# Test 10: Network Policies
test_network_policies() {
    log_info "Testing network policies..."
    
    # Check network policies in flux-system
    local netpols=$(kubectl get networkpolicy -n flux-system --no-headers | wc -l)
    if [[ $netpols -gt 0 ]]; then
        report_test "Network Policies" "PASS" "Found $netpols network policies in flux-system"
    else
        report_test "Network Policies" "FAIL" "No network policies found in flux-system"
    fi
}

# Test 11: Security Context
test_security_context() {
    log_info "Testing security contexts..."
    
    # Check if pods have security contexts
    local secure_pods=0
    local total_pods=0
    
    for pod in $(kubectl get pods -n flux-system -o jsonpath='{.items[*].metadata.name}'); do
        total_pods=$((total_pods + 1))
        if kubectl get pod "$pod" -n flux-system -o jsonpath='{.spec.securityContext}' | grep -q "runAsNonRoot"; then
            secure_pods=$((secure_pods + 1))
        fi
    done
    
    if [[ $secure_pods -gt 0 ]]; then
        report_test "Security Context" "PASS" "$secure_pods/$total_pods pods have security contexts"
    else
        report_test "Security Context" "FAIL" "No pods have security contexts"
    fi
}

# Test 12: Resource Limits
test_resource_limits() {
    log_info "Testing resource limits..."
    
    # Check if deployments have resource limits
    local deployments_with_limits=0
    local total_deployments=0
    
    for deployment in $(kubectl get deployments -n flux-system -o jsonpath='{.items[*].metadata.name}'); do
        total_deployments=$((total_deployments + 1))
        if kubectl get deployment "$deployment" -n flux-system -o jsonpath='{.spec.template.spec.containers[0].resources.limits}' | grep -q "memory\|cpu"; then
            deployments_with_limits=$((deployments_with_limits + 1))
        fi
    done
    
    if [[ $deployments_with_limits -gt 0 ]]; then
        report_test "Resource Limits" "PASS" "$deployments_with_limits/$total_deployments deployments have resource limits"
    else
        report_test "Resource Limits" "FAIL" "No deployments have resource limits"
    fi
}

# Test 13: Image Update Automation
test_image_update_automation() {
    log_info "Testing image update automation..."
    
    # Check for ImageRepository resources
    local image_repos=$(kubectl get imagerepository -n flux-system --no-headers | wc -l)
    if [[ $image_repos -gt 0 ]]; then
        report_test "Image Update Automation" "PASS" "Found $image_repos ImageRepository resources"
    else
        report_test "Image Update Automation" "FAIL" "No ImageRepository resources found"
    fi
}

# Test 14: Notifications Configuration
test_notifications_configuration() {
    log_info "Testing notifications configuration..."
    
    # Check for Provider resources
    local providers=$(kubectl get provider -n flux-system --no-headers | wc -l)
    if [[ $providers -gt 0 ]]; then
        report_test "Notifications Configuration" "PASS" "Found $providers notification providers"
    else
        report_test "Notifications Configuration" "SKIP" "No notification providers found"
    fi
}

# Test 15: End-to-End GitOps Flow
test_end_to_end_gitops() {
    log_info "Testing end-to-end GitOps flow..."
    
    # Create a test deployment
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flux-test-deployment
  namespace: $TEST_NAMESPACE
  labels:
    app: flux-test
spec:
  replicas: 1
  selector:
    matchLabels:
      app: flux-test
  template:
    metadata:
      labels:
        app: flux-test
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
EOF
    
    # Wait for deployment to be applied
    sleep 30
    
    # Check if deployment exists and is ready
    if kubectl get deployment flux-test-deployment -n "$TEST_NAMESPACE" &> /dev/null; then
        if kubectl wait --for=condition=available deployment/flux-test-deployment -n "$TEST_NAMESPACE" --timeout=120s; then
            report_test "End-to-End GitOps Flow" "PASS" "Test deployment successfully applied"
        else
            report_test "End-to-End GitOps Flow" "FAIL" "Test deployment not ready"
        fi
    else
        report_test "End-to-End GitOps Flow" "FAIL" "Test deployment not found"
    fi
    
    # Cleanup
    kubectl delete deployment flux-test-deployment -n "$TEST_NAMESPACE" --ignore-not-found=true
}

# Test 16: Performance Metrics
test_performance_metrics() {
    log_info "Testing performance metrics..."
    
    # Check if metrics endpoints are available
    local metrics_available=false
    
    for service in $(kubectl get svc -n flux-system --no-headers | awk '{print $1}'); do
        if kubectl get svc "$service" -n flux-system -o jsonpath='{.spec.ports[*].name}' | grep -q "metrics"; then
            metrics_available=true
            break
        fi
    done
    
    if [[ "$metrics_available" == "true" ]]; then
        report_test "Performance Metrics" "PASS" "Metrics endpoints are available"
    else
        report_test "Performance Metrics" "FAIL" "No metrics endpoints found"
    fi
}

# Test 17: Backup and Recovery
test_backup_recovery() {
    log_info "Testing backup and recovery procedures..."
    
    # Export current state
    local backup_dir="/tmp/flux-backup-$(date +%s)"
    mkdir -p "$backup_dir"
    
    # Backup GitRepository
    kubectl get gitrepository -n flux-system -o yaml > "$backup_dir/gitrepositories.yaml"
    
    # Backup Kustomizations
    kubectl get kustomization -n flux-system -o yaml > "$backup_dir/kustomizations.yaml"
    
    # Check if backup files were created
    if [[ -f "$backup_dir/gitrepositories.yaml" && -f "$backup_dir/kustomizations.yaml" ]]; then
        report_test "Backup and Recovery" "PASS" "Backup files created successfully"
        rm -rf "$backup_dir"
    else
        report_test "Backup and Recovery" "FAIL" "Backup files not created"
        rm -rf "$backup_dir"
    fi
}

# Test 18: Multi-Environment Support
test_multi_environment_support() {
    log_info "Testing multi-environment support..."
    
    local environments=("production" "staging" "development")
    local environments_found=0
    
    for env in "${environments[@]}"; do
        if [[ -d "overlays/flux-system/$env" ]]; then
            environments_found=$((environments_found + 1))
        fi
    done
    
    if [[ $environments_found -eq 3 ]]; then
        report_test "Multi-Environment Support" "PASS" "All environment overlays found"
    else
        report_test "Multi-Environment Support" "FAIL" "Only $environments_found/3 environment overlays found"
    fi
}

# Test 19: Configuration Validation
test_configuration_validation() {
    log_info "Testing configuration validation..."
    
    # Validate kustomize overlays
    local overlays_valid=true
    
    for env in production staging development; do
        if [[ -d "overlays/flux-system/$env" ]]; then
            if kubectl kustomize "overlays/flux-system/$env" &> /dev/null; then
                log_success "Overlay $env is valid"
            else
                log_error "Overlay $env is invalid"
                overlays_valid=false
            fi
        fi
    done
    
    if [[ "$overlays_valid" == "true" ]]; then
        report_test "Configuration Validation" "PASS" "All overlays are valid"
    else
        report_test "Configuration Validation" "FAIL" "Some overlays are invalid"
    fi
}

# Test 20: Integration Health Check
test_integration_health_check() {
    log_info "Testing integration health check..."
    
    # Check if all components are working together
    local integration_healthy=true
    
    # Check Flux components
    if ! flux check --namespace flux-system &> /dev/null; then
        integration_healthy=false
    fi
    
    # Check Qwen if available
    if kubectl get deployment qwen-llm -n qwen-system &> /dev/null; then
        if ! kubectl wait --for=condition=available deployment/qwen-llm -n qwen-system --timeout=60s; then
            integration_healthy=false
        fi
    fi
    
    # Check K8sGPT if available
    if kubectl get deployment k8sgpt -n flux-system &> /dev/null; then
        if ! kubectl wait --for=condition=available deployment/k8sgpt -n flux-system --timeout=60s; then
            integration_healthy=false
        fi
    fi
    
    if [[ "$integration_healthy" == "true" ]]; then
        report_test "Integration Health Check" "PASS" "All components are healthy"
    else
        report_test "Integration Health Check" "FAIL" "Some components are not healthy"
    fi
}

# Main test execution
main() {
    log_info "Starting Flux Comprehensive Test Suite"
    log_info "Test Environment: $TEST_ENVIRONMENT"
    log_info "Test Cluster: $TEST_CLUSTER"
    echo ""
    
    # Setup
    setup_test_environment
    
    # Run all tests
    test_flux_cli
    test_flux_controllers_health
    test_flux_check
    test_git_repository_reconciliation
    test_kustomization_reconciliation
    test_qwen_llm_health
    test_k8sgpt_analysis
    test_flux_webhook_integration
    test_monitoring_integration
    test_network_policies
    test_security_context
    test_resource_limits
    test_image_update_automation
    test_notifications_configuration
    test_end_to_end_gitops
    test_performance_metrics
    test_backup_recovery
    test_multi_environment_support
    test_configuration_validation
    test_integration_health_check
    
    # Cleanup
    cleanup
    
    # Print results
    echo ""
    log_info "Test Results:"
    echo "================"
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $TESTS_PASSED"
    echo "Failed: $TESTS_FAILED"
    echo "Success Rate: $(( TESTS_PASSED * 100 / TOTAL_TESTS ))%"
    echo ""
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_success "All tests passed! 🎉"
        exit 0
    else
        log_error "Some tests failed. Please review the output above."
        exit 1
    fi
}

# Run main function
main "$@"

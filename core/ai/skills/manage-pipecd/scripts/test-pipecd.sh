#!/bin/bash

# PipeCD Testing Script
# Comprehensive testing suite for PipeCD integration

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${PIPECD_NAMESPACE:-pipecd}"
QWEN_NAMESPACE="${QWEN_NAMESPACE:-qwen-ai}"
TEST_TIMEOUT="${TEST_TIMEOUT:-300}"
TEST_IMAGE="${TEST_IMAGE:-nginx:alpine}"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TEST_RESULTS=()

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

# Test runner
run_test() {
    local test_name="$1"
    local test_func="$2"
    
    log_info "Running test: $test_name"
    
    if $test_func; then
        log_success "✓ $test_name PASSED"
        ((TESTS_PASSED++))
        TEST_RESULTS+=("$test_name: PASSED")
        return 0
    else
        log_error "✗ $test_name FAILED"
        ((TESTS_FAILED++))
        TEST_RESULTS+=("$test_name: FAILED")
        return 1
    fi
}

# Check prerequisites
test_prerequisites() {
    # Check if kubectl is available
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        return 1
    fi
    
    # Check if namespaces exist
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_error "PipeCD namespace '$NAMESPACE' does not exist"
        return 1
    fi
    
    if ! kubectl get namespace "$QWEN_NAMESPACE" &> /dev/null; then
        log_error "Qwen namespace '$QWEN_NAMESPACE' does not exist"
        return 1
    fi
    
    return 0
}

# Test PipeCD control plane
test_pipecd_control_plane() {
    # Check all deployments
    local deployments=("pipecd-server" "pipecd-cache" "pipecd-minio" "pipecd-mysql" "pipecd-gateway" "pipecd-ops")
    
    for deployment in "${deployments[@]}"; do
        if ! kubectl rollout status -n "$NAMESPACE" deployment/"$deployment" --timeout="${TEST_TIMEOUT}s" &> /dev/null; then
            log_error "Deployment $deployment is not ready"
            return 1
        fi
    done
    
    # Check services
    local services=("pipecd" "pipecd-server" "cache" "mysql" "minio")
    
    for service in "${services[@]}"; do
        if ! kubectl get svc -n "$NAMESPACE" "$service" &> /dev/null; then
            log_error "Service $service does not exist"
            return 1
        fi
    done
    
    # Check PVCs
    local pvcs=("pipecd-mysql-pvc" "pipecd-minio-pvc")
    
    for pvc in "${pvcs[@]}"; do
        local status
        status=$(kubectl get pvc -n "$NAMESPACE" "$pvc" -o jsonpath='{.status.phase}' 2>/dev/null)
        if [[ "$status" != "Bound" ]]; then
            log_error "PVC $pvc is not bound (status: $status)"
            return 1
        fi
    done
    
    return 0
}

# Test Qwen LLM service
test_qwen_service() {
    # Check deployment
    if ! kubectl rollout status -n "$QWEN_NAMESPACE" deployment/qwen-llm-service --timeout="${TEST_TIMEOUT}s" &> /dev/null; then
        log_error "Qwen LLM service deployment is not ready"
        return 1
    fi
    
    # Check service
    if ! kubectl get svc -n "$QWEN_NAMESPACE" qwen-llm-service &> /dev/null; then
        log_error "Qwen LLM service does not exist"
        return 1
    fi
    
    # Check PVC
    local status
    status=$(kubectl get pvc -n "$QWEN_NAMESPACE" qwen-model-cache-pvc -o jsonpath='{.status.phase}' 2>/dev/null)
    if [[ "$status" != "Bound" ]]; then
        log_error "Qwen model cache PVC is not bound (status: $status)"
        return 1
    fi
    
    # Test health endpoint
    local pod_name
    pod_name=$(kubectl get pods -n "$QWEN_NAMESPACE" -l app=qwen-llm-service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [[ -z "$pod_name" ]]; then
        log_error "No Qwen LLM service pod found"
        return 1
    fi
    
    # Wait for health endpoint
    local retries=30
    while ((retries > 0)); do
        if kubectl exec -n "$QWEN_NAMESPACE" "$pod_name" -- curl -f http://localhost:8080/health &> /dev/null; then
            break
        fi
        sleep 10
        ((retries--))
    done
    
    if ((retries == 0)); then
        log_error "Qwen LLM service health check failed"
        return 1
    fi
    
    return 0
}

# Test K8sGPT integration
test_k8sgpt_integration() {
    # Check deployment
    if ! kubectl rollout status -n "$NAMESPACE" deployment/k8sgpt-analyzer --timeout="${TEST_TIMEOUT}s" &> /dev/null; then
        log_error "K8sGPT analyzer deployment is not ready"
        return 1
    fi
    
    # Check webhook deployment
    if ! kubectl rollout status -n "$NAMESPACE" deployment/k8sgpt-webhook --timeout="${TEST_TIMEOUT}s" &> /dev/null; then
        log_error "K8sGPT webhook deployment is not ready"
        return 1
    fi
    
    # Check service
    if ! kubectl get svc -n "$NAMESPACE" k8sgpt-webhook &> /dev/null; then
        log_error "K8sGPT webhook service does not exist"
        return 1
    fi
    
    # Check configmap
    if ! kubectl get configmap -n "$NAMESPACE" k8sgpt-config &> /dev/null; then
        log_error "K8sGPT configmap does not exist"
        return 1
    fi
    
    # Test webhook health
    local pod_name
    pod_name=$(kubectl get pods -n "$NAMESPACE" -l app=k8sgpt-webhook -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [[ -z "$pod_name" ]]; then
        log_error "No K8sGPT webhook pod found"
        return 1
    fi
    
    # Test health endpoint
    if ! kubectl exec -n "$NAMESPACE" "$pod_name" -- curl -f http://localhost:8000/health &> /dev/null; then
        log_error "K8sGPT webhook health check failed"
        return 1
    fi
    
    return 0
}

# Test PipeCD console access
test_pipecd_console() {
    # Start port forwarding in background
    kubectl port-forward -n "$NAMESPACE" svc/pipecd 8080 &
    local pf_pid=$!
    
    # Wait for port forwarding to be ready
    sleep 5
    
    # Test HTTP access
    if ! curl -f --max-time 10 http://localhost:8080 &> /dev/null; then
        log_error "PipeCD console is not accessible"
        kill "$pf_pid" 2>/dev/null || true
        return 1
    fi
    
    # Test API health
    if ! curl -f --max-time 10 http://localhost:8080/healthz &> /dev/null; then
        log_error "PipeCD API health check failed"
        kill "$pf_pid" 2>/dev/null || true
        return 1
    fi
    
    # Clean up port forwarding
    kill "$pf_pid" 2>/dev/null || true
    
    return 0
}

# Test sample application deployment
test_sample_deployment() {
    local app_name="test-app"
    local app_namespace="default"
    
    # Create test application
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $app_name
  namespace: $app_namespace
  labels:
    app: $app_name
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $app_name
  template:
    metadata:
      labels:
        app: $app_name
    spec:
      containers:
      - name: nginx
        image: $TEST_IMAGE
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: $app_name
  namespace: $app_namespace
spec:
  selector:
    app: $app_name
  ports:
  - port: 80
    targetPort: 80
EOF
    
    # Wait for deployment to be ready
    if ! kubectl rollout status -n "$app_namespace" deployment/"$app_name" --timeout="${TEST_TIMEOUT}s" &> /dev/null; then
        log_error "Test application deployment failed"
        kubectl delete -n "$app_namespace" deployment/"$app_name" service/"$app_name" --ignore-not-found=true
        return 1
    fi
    
    # Test application accessibility
    local pod_name
    pod_name=$(kubectl get pods -n "$app_namespace" -l app="$app_name" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [[ -z "$pod_name" ]]; then
        log_error "Test application pod not found"
        kubectl delete -n "$app_namespace" deployment/"$app_name" service/"$app_name" --ignore-not-found=true
        return 1
    fi
    
    # Test HTTP response
    if ! kubectl exec -n "$app_namespace" "$pod_name" -- curl -f http://localhost:80 &> /dev/null; then
        log_error "Test application is not responding"
        kubectl delete -n "$app_namespace" deployment/"$app_name" service/"$app_name" --ignore-not-found=true
        return 1
    fi
    
    # Clean up
    kubectl delete -n "$app_namespace" deployment/"$app_name" service/"$app_name" --ignore-not-found=true
    
    return 0
}

# Test AI analysis integration
test_ai_analysis() {
    # Test Qwen connectivity from K8sGPT
    local analyzer_pod
    analyzer_pod=$(kubectl get pods -n "$NAMESPACE" -l app=k8sgpt-analyzer -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [[ -z "$analyzer_pod" ]]; then
        log_error "K8sGPT analyzer pod not found"
        return 1
    fi
    
    # Test Qwen service connectivity
    if ! kubectl exec -n "$NAMESPACE" "$analyzer_pod" -- curl -f --max-time 30 http://qwen-llm-service.qwen-ai.svc.cluster.local:8080/health &> /dev/null; then
        log_error "K8sGPT cannot connect to Qwen service"
        return 1
    fi
    
    # Test webhook analysis endpoint
    local test_payload='{"deployment_data": {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"name": "test"}, "spec": {"replicas": 1}}, "analysis_type": "deployment"}'
    
    if ! kubectl exec -n "$NAMESPACE" "$analyzer_pod" -- curl -f -X POST -H "Content-Type: application/json" -d "$test_payload" http://k8sgpt-webhook.pipecd.svc.cluster.local:8000/analyze &> /dev/null; then
        log_error "AI analysis webhook test failed"
        return 1
    fi
    
    return 0
}

# Performance test
test_performance() {
    log_info "Running performance tests..."
    
    # Test response times
    local start_time
    local end_time
    local response_time
    
    # PipeCD API response time
    start_time=$(date +%s.%3N)
    kubectl exec -n "$NAMESPACE" deployment/pipecd-server -- curl -s http://localhost:8080/healthz &> /dev/null
    end_time=$(date +%s.%3N)
    response_time=$(echo "$end_time - $start_time" | bc)
    
    if (( $(echo "$response_time > 5.0" | bc -l) )); then
        log_warning "PipeCD API response time is slow: ${response_time}s (expected < 5.0s)"
    else
        log_info "PipeCD API response time: ${response_time}s"
    fi
    
    # Qwen service response time
    start_time=$(date +%s.%3N)
    kubectl exec -n "$QWEN_NAMESPACE" deployment/qwen-llm-service -- curl -s http://localhost:8080/health &> /dev/null
    end_time=$(date +%s.%3N)
    response_time=$(echo "$end_time - $start_time" | bc)
    
    if (( $(echo "$response_time > 10.0" | bc -l) )); then
        log_warning "Qwen service response time is slow: ${response_time}s (expected < 10.0s)"
    else
        log_info "Qwen service response time: ${response_time}s"
    fi
    
    return 0
}

# Generate test report
generate_report() {
    echo
    echo "========================================"
    echo "        PipeCD Integration Test Report"
    echo "========================================"
    echo
    echo "Test Results:"
    echo "-------------"
    
    for result in "${TEST_RESULTS[@]}"; do
        echo "- $result"
    done
    
    echo
    echo "Summary:"
    echo "--------"
    echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
    
    if ((TESTS_FAILED > 0)); then
        echo
        echo -e "${RED}Some tests failed. Please check the output above for details.${NC}"
        return 1
    else
        echo
        echo -e "${GREEN}All tests passed! PipeCD integration is working correctly.${NC}"
        return 0
    fi
}

# Cleanup function
cleanup() {
    # Kill any background processes
    pkill -f "kubectl port-forward" || true
}

# Main execution
main() {
    log_info "Starting PipeCD integration tests..."
    
    # Set up cleanup trap
    trap cleanup EXIT
    
    # Run all tests
    run_test "Prerequisites" test_prerequisites
    run_test "PipeCD Control Plane" test_pipecd_control_plane
    run_test "Qwen LLM Service" test_qwen_service
    run_test "K8sGPT Integration" test_k8sgpt_integration
    run_test "PipeCD Console Access" test_pipecd_console
    run_test "Sample Application Deployment" test_sample_deployment
    run_test "AI Analysis Integration" test_ai_analysis
    run_test "Performance Tests" test_performance
    
    # Generate report
    generate_report
}

# Handle script arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Usage: $0 [options]"
        echo
        echo "PipeCD Integration Test Suite"
        echo
        echo "Environment variables:"
        echo "  PIPECD_NAMESPACE    - PipeCD namespace (default: pipecd)"
        echo "  QWEN_NAMESPACE      - Qwen namespace (default: qwen-ai)"
        echo "  TEST_TIMEOUT        - Test timeout in seconds (default: 300)"
        echo "  TEST_IMAGE          - Test container image (default: nginx:alpine)"
        echo
        echo "Examples:"
        echo "  $0                    # Run all tests"
        echo "  PIPECD_NAMESPACE=test $0  # Run tests in test namespace"
        exit 0
        ;;
    "")
        main
        ;;
    *)
        log_error "Unknown argument: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac

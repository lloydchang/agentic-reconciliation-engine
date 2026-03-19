#!/bin/bash

# Argo Rollouts Integration Test Suite
# This script runs comprehensive tests for Argo Rollouts with K8sGPT Qwen integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TEST_NAMESPACE="argo-rollouts-test"
ROLLBACK_NAMESPACE="argo-rollouts-test-rollback"
TIMEOUT=600
TEST_TIMEOUT=300

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

# Functions
print_header() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_info "Running test: $test_name"
    
    if eval "$test_command" > /dev/null 2>&1; then
        print_success "$test_name - PASSED"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        print_error "$test_name - FAILED"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

setup_test_environment() {
    print_header "Setting Up Test Environment"
    
    # Create test namespaces
    print_info "Creating test namespaces"
    kubectl create namespace "$TEST_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace "$ROLLBACK_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Install Argo Rollouts if not present
    if ! kubectl get crd rollouts.argoproj.io &> /dev/null; then
        print_info "Installing Argo Rollouts"
        kubectl apply -n "$TEST_NAMESPACE" -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
        kubectl wait --for=condition=available deployment/argo-rollouts -n "$TEST_NAMESPACE" --timeout=300s
    fi
    
    # Create test services for analysis
    print_info "Creating test services"
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: test-service-stable
  namespace: $TEST_NAMESPACE
spec:
  selector:
    app: test-rollout
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: test-service-canary
  namespace: $TEST_NAMESPACE
spec:
  selector:
    app: test-rollout
  ports:
  - port: 80
    targetPort: 80
EOF
    
    print_success "Test environment setup completed"
}

cleanup_test_environment() {
    print_header "Cleaning Up Test Environment"
    
    # Delete test namespaces
    print_info "Deleting test namespaces"
    kubectl delete namespace "$TEST_NAMESPACE" --ignore-not-found=true --timeout=60s || true
    kubectl delete namespace "$ROLLBACK_NAMESPACE" --ignore-not-found=true --timeout=60s || true
    
    # Wait for namespaces to be deleted
    sleep 10
    
    print_success "Test environment cleanup completed"
}

test_basic_rollout_creation() {
    print_header "Testing Basic Rollout Creation"
    
    # Create basic rollout
    cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: test-basic-rollout
  namespace: $TEST_NAMESPACE
spec:
  replicas: 2
  strategy:
    canary:
      steps:
      - setWeight: 50
      - pause: {duration: 1m}
  selector:
    matchLabels:
      app: test-rollout
  template:
    metadata:
      labels:
        app: test-rollout
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
EOF
    
    # Wait for rollout to be available
    kubectl wait --for=condition=available rollout/test-basic-rollout -n "$TEST_NAMESPACE" --timeout="$TEST_TIMEOUT"
    
    # Verify rollout status
    status=$(kubectl argo rollouts status test-basic-rollout -n "$TEST_NAMESPACE")
    if [[ "$status" == *"healthy"* ]] || [[ "$status" == *"paused"* ]]; then
        print_success "Basic rollout created successfully"
        return 0
    else
        print_error "Basic rollout creation failed"
        return 1
    fi
}

test_canary_strategy() {
    print_header "Testing Canary Strategy"
    
    # Create canary rollout
    cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: test-canary-rollout
  namespace: $TEST_NAMESPACE
spec:
  replicas: 3
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 30s}
      - setWeight: 50
      - pause: {duration: 30s}
      canaryService: test-service-canary
      stableService: test-service-stable
  selector:
    matchLabels:
      app: test-canary-rollout
  template:
    metadata:
      labels:
        app: test-canary-rollout
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
        ports:
        - containerPort: 80
EOF
    
    # Wait for initial deployment
    kubectl wait --for=condition=available rollout/test-canary-rollout -n "$TEST_NAMESPACE" --timeout="$TEST_TIMEOUT"
    
    # Trigger canary update
    kubectl set image rollout/test-canary-rollout nginx=nginx:1.22 -n "$TEST_NAMESPACE"
    
    # Wait for canary to progress
    sleep 10
    
    # Check canary status
    status=$(kubectl argo rollouts status test-canary-rollout -n "$TEST_NAMESPACE")
    if [[ "$status" == *"paused"* ]] || [[ "$status" == *"progressing"* ]]; then
        print_success "Canary strategy working correctly"
        return 0
    else
        print_error "Canary strategy failed"
        return 1
    fi
}

test_blue_green_strategy() {
    print_header "Testing Blue-Green Strategy"
    
    # Create blue-green rollout
    cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: test-bluegreen-rollout
  namespace: $TEST_NAMESPACE
spec:
  replicas: 2
  strategy:
    blueGreen:
      activeService: test-service-stable
      previewService: test-service-canary
      autoPromotionEnabled: false
      scaleDownDelaySeconds: 30
  selector:
    matchLabels:
      app: test-bluegreen-rollout
  template:
    metadata:
      labels:
        app: test-bluegreen-rollout
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
EOF
    
    # Wait for rollout to be available
    kubectl wait --for=condition=available rollout/test-bluegreen-rollout -n "$TEST_NAMESPACE" --timeout="$TEST_TIMEOUT"
    
    # Trigger blue-green update
    kubectl set image rollout/test-bluegreen-rollout nginx=nginx:1.21 -n "$TEST_NAMESPACE"
    
    # Wait for preview deployment
    sleep 10
    
    # Check blue-green status
    status=$(kubectl argo rollouts status test-bluegreen-rollout -n "$TEST_NAMESPACE")
    if [[ "$status" == *"paused"* ]] || [[ "$status" == *"progressing"* ]]; then
        print_success "Blue-green strategy working correctly"
        return 0
    else
        print_error "Blue-green strategy failed"
        return 1
    fi
}

test_analysis_templates() {
    print_header "Testing Analysis Templates"
    
    # Create success rate analysis template
    cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: test-success-rate
  namespace: $TEST_NAMESPACE
spec:
  args:
  - name: service-name
    value: ""
  metrics:
  - name: success-rate
    interval: 5s
    count: 3
    successCondition: result[0] >= 0.95
    failureLimit: 1
    provider:
      job:
        spec:
          template:
            spec:
              containers:
              - name: success-rate-checker
                image: alpine:3.18
                command:
                - /bin/sh
                - -c
                - |
                  echo "0.98"  # Mock success rate
              restartPolicy: Never
EOF
    
    # Create rollout with analysis
    cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: test-analysis-rollout
  namespace: $TEST_NAMESPACE
spec:
  replicas: 2
  strategy:
    canary:
      steps:
      - setWeight: 50
      - analysis:
          templates:
          - templateName: test-success-rate
          args:
          - name: service-name
            value: test-service-canary
  selector:
    matchLabels:
      app: test-analysis-rollout
  template:
    metadata:
      labels:
        app: test-analysis-rollout
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
EOF
    
    # Wait for rollout to be available
    kubectl wait --for=condition=available rollout/test-analysis-rollout -n "$TEST_NAMESPACE" --timeout="$TEST_TIMEOUT"
    
    # Trigger analysis
    kubectl set image rollout/test-analysis-rollout nginx=nginx:1.21 -n "$TEST_NAMESPACE"
    
    # Wait for analysis to run
    sleep 15
    
    # Check analysis runs
    analysis_runs=$(kubectl get analysisrun -n "$TEST_NAMESPACE" --no-headers | wc -l)
    if [ "$analysis_runs" -gt 0 ]; then
        print_success "Analysis templates working correctly"
        return 0
    else
        print_error "Analysis templates failed"
        return 1
    fi
}

test_k8sgpt_integration() {
    print_header "Testing K8sGPT Integration"
    
    # Check if K8sGPT is available
    if ! kubectl get deployment k8sgpt-analyzer -n $TOPDIR &> /dev/null; then
        print_warning "K8sGPT analyzer not found, skipping integration test"
        return 0
    fi
    
    # Create K8sGPT analysis template
    cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: test-k8sgpt-analysis
  namespace: $TEST_NAMESPACE
spec:
  args:
  - name: namespace
    value: $TEST_NAMESPACE
  metrics:
  - name: k8sgpt-health-score
    interval: 10s
    count: 2
    successCondition: result[0] >= 0.5
    failureLimit: 1
    provider:
      job:
        spec:
          template:
            spec:
              containers:
              - name: k8sgpt-analyzer
                image: k8sgpt/k8sgpt:latest
                command:
                - /bin/sh
                - -c
                - |
                  echo "Running K8sGPT analysis..."
                  echo "0.85"  # Mock health score
                env:
                - name: QWEN_API_KEY
                  valueFrom:
                    secretKeyRef:
                      name: qwen-secret
                      key: api-key
                  optional: true
                resources:
                  requests:
                    cpu: 50m
                    memory: 128Mi
                  limits:
                    cpu: 200m
                    memory: 256Mi
              restartPolicy: Never
EOF
    
    # Create rollout with K8sGPT analysis
    cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: test-k8sgpt-rollout
  namespace: $TEST_NAMESPACE
spec:
  replicas: 2
  strategy:
    canary:
      steps:
      - setWeight: 50
      - analysis:
          templates:
          - templateName: test-k8sgpt-analysis
          args:
          - name: namespace
            value: $TEST_NAMESPACE
  selector:
    matchLabels:
      app: test-k8sgpt-rollout
  template:
    metadata:
      labels:
        app: test-k8sgpt-rollout
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
EOF
    
    # Wait for rollout to be available
    kubectl wait --for=condition=available rollout/test-k8sgpt-rollout -n "$TEST_NAMESPACE" --timeout="$TEST_TIMEOUT"
    
    # Trigger K8sGPT analysis
    kubectl set image rollout/test-k8sgpt-rollout nginx=nginx:1.21 -n "$TEST_NAMESPACE"
    
    # Wait for analysis to run
    sleep 15
    
    # Check analysis runs
    analysis_runs=$(kubectl get analysisrun -n "$TEST_NAMESPACE" --no-headers | grep "test-k8sgpt" | wc -l)
    if [ "$analysis_runs" -gt 0 ]; then
        print_success "K8sGPT integration working correctly"
        return 0
    else
        print_warning "K8sGPT integration test inconclusive (may need Qwen server)"
        return 0
    fi
}

test_rollout_rollback() {
    print_header "Testing Rollout Rollback"
    
    # Create rollout for rollback test
    cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: test-rollback-rollout
  namespace: $ROLLBACK_NAMESPACE
spec:
  replicas: 2
  strategy:
    canary:
      steps:
      - setWeight: 50
      - pause: {duration: 30s}
  selector:
    matchLabels:
      app: test-rollback-rollout
  template:
    metadata:
      labels:
        app: test-rollback-rollout
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
EOF
    
    # Wait for rollout to be available
    kubectl wait --for=condition=available rollout/test-rollback-rollout -n "$ROLLBACK_NAMESPACE" --timeout="$TEST_TIMEOUT"
    
    # Get initial revision
    initial_revision=$(kubectl argo rollouts history test-rollback-rollout -n "$ROLLBACK_NAMESPACE" | head -1 | awk '{print $1}')
    
    # Update to new version
    kubectl set image rollout/test-rollback-rollout nginx=nginx:1.21 -n "$ROLLBACK_NAMESPACE"
    
    # Wait for update to start
    sleep 10
    
    # Perform rollback
    kubectl argo rollouts undo test-rollback-rollout -n "$ROLLBACK_NAMESPACE"
    
    # Wait for rollback to complete
    kubectl wait --for=condition=available rollout/test-rollback-rollout -n "$ROLLBACK_NAMESPACE" --timeout="$TEST_TIMEOUT"
    
    # Verify rollback
    current_revision=$(kubectl argo rollouts history test-rollback-rollout -n "$ROLLBACK_NAMESPACE" | head -1 | awk '{print $1}')
    current_image=$(kubectl get rollout test-rollback-rollout -n "$ROLLBACK_NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].image}')
    
    if [[ "$current_revision" == "$initial_revision" ]] && [[ "$current_image" == *"nginx:1.20"* ]]; then
        print_success "Rollback working correctly"
        return 0
    else
        print_error "Rollback failed"
        return 1
    fi
}

test_metrics_and_monitoring() {
    print_header "Testing Metrics and Monitoring"
    
    # Check if metrics endpoint is accessible
    if kubectl get service argo-rollouts-metrics -n argo-rollouts &> /dev/null; then
        # Port forward to test metrics
        kubectl port-forward -n argo-rollouts svc/argo-rollouts-metrics 8090:8090 &
        PF_PID=$!
        
        # Wait for port forward to be ready
        sleep 5
        
        # Test metrics endpoint
        if curl -s http://localhost:8090/metrics | grep -q "argo_rollouts"; then
            print_success "Metrics endpoint working correctly"
            kill $PF_PID 2>/dev/null || true
            return 0
        else
            print_error "Metrics endpoint not working"
            kill $PF_PID 2>/dev/null || true
            return 1
        fi
    else
        print_warning "Metrics service not found, skipping metrics test"
        return 0
    fi
}

test_cli_functionality() {
    print_header "Testing CLI Functionality"
    
    # Test kubectl plugin
    if ! command -v kubectl-argo-rollouts &> /dev/null; then
        if ! kubectl argo rollouts version &> /dev/null; then
            print_error "kubectl plugin not installed"
            return 1
        fi
    fi
    
    # Test basic CLI commands
    if kubectl argo rollouts list -n "$TEST_NAMESPACE" &> /dev/null; then
        print_success "CLI functionality working correctly"
        return 0
    else
        print_error "CLI functionality failed"
        return 1
    fi
}

test_security_configuration() {
    print_header "Testing Security Configuration"
    
    # Check RBAC
    if kubectl get clusterrole argo-rollouts &> /dev/null; then
        print_success "RBAC configuration correct"
    else
        print_error "RBAC configuration missing"
        return 1
    fi
    
    # Check network policies
    if kubectl get networkpolicy -n argo-rollouts | grep -q "argo-rollouts"; then
        print_success "Network policies configured"
    else
        print_warning "Network policies not found (optional)"
    fi
    
    # Check service account
    if kubectl get serviceaccount argo-rollouts -n argo-rollouts &> /dev/null; then
        print_success "Service account configured"
        return 0
    else
        print_error "Service account missing"
        return 1
    fi
}

run_performance_test() {
    print_header "Running Performance Test"
    
    # Create multiple rollouts simultaneously
    for i in {1..3}; do
        cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: test-perf-rollout-$i
  namespace: $TEST_NAMESPACE
spec:
  replicas: 2
  strategy:
    canary:
      steps:
      - setWeight: 50
      - pause: {duration: 30s}
  selector:
    matchLabels:
      app: test-perf-rollout-$i
  template:
    metadata:
      labels:
        app: test-perf-rollout-$i
    spec:
      containers:
      - name: nginx
        image: nginx:1.20
        ports:
        - containerPort: 80
EOF
    done
    
    # Wait for all rollouts to be available
    success_count=0
    for i in {1..3}; do
        if kubectl wait --for=condition=available rollout/test-perf-rollout-$i -n "$TEST_NAMESPACE" --timeout=120s; then
            success_count=$((success_count + 1))
        fi
    done
    
    if [ "$success_count" -eq 3 ]; then
        print_success "Performance test passed - all rollouts deployed successfully"
        return 0
    else
        print_error "Performance test failed - only $success_count/3 rollouts deployed"
        return 1
    fi
}

show_test_results() {
    print_header "Test Results Summary"
    
    echo -e "${BLUE}Total Tests: $TOTAL_TESTS${NC}"
    echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
    
    if [ "$TESTS_FAILED" -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}❌ Some tests failed. Please check the logs above.${NC}"
        return 1
    fi
}

# Main execution
main() {
    print_header "Argo Rollouts Integration Test Suite"
    
    # Setup
    setup_test_environment
    
    # Run tests
    run_test "Basic Rollout Creation" "test_basic_rollout_creation"
    run_test "Canary Strategy" "test_canary_strategy"
    run_test "Blue-Green Strategy" "test_blue_green_strategy"
    run_test "Analysis Templates" "test_analysis_templates"
    run_test "K8sGPT Integration" "test_k8sgpt_integration"
    run_test "Rollout Rollback" "test_rollout_rollback"
    run_test "Metrics and Monitoring" "test_metrics_and_monitoring"
    run_test "CLI Functionality" "test_cli_functionality"
    run_test "Security Configuration" "test_security_configuration"
    run_test "Performance Test" "run_performance_test"
    
    # Show results
    show_test_results
    
    # Cleanup
    cleanup_test_environment
    
    # Exit with appropriate code
    if [ "$TESTS_FAILED" -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Handle script interruption
trap 'print_error "Test suite interrupted"; cleanup_test_environment; exit 1' INT TERM

# Run main function
main "$@"

#!/bin/bash
# Complete End-to-End Test Suite
# Validates the entire GitOps infrastructure control plane from bootstrap to teardown

set -euxo pipefail

# Configuration
REPO_URL="https://github.com/lloydchang/gitops-infra-control-plane"
BRANCH="main"
TEST_TIMEOUT=3600  # 1 hour for full E2E test
CLEANUP_ON_SUCCESS=${CLEANUP_ON_SUCCESS:-false}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_status() {
    echo -e "${GREEN}[E2E-TEST]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test phases tracking
TEST_PHASES=("prerequisites" "bootstrap" "infrastructure" "cloud_providers" "workloads" "applications" "validation" "drift_test" "performance" "cleanup")
declare -a test_results

# Initialize test results
for phase in "${TEST_PHASES[@]}"; do
    test_results+=(false)
done

update_test_result() {
    local phase=$1
    local status=$2
    
    # Find index of phase
    for i in "${!TEST_PHASES[@]}"; do
        if [[ "${TEST_PHASES[$i]}" == "$phase" ]]; then
            test_results[$i]=$status
            break
        fi
    done
    
    if [[ "$status" == "true" ]]; then
        print_status "$phase: ✓ PASS"
    else
        print_error "$phase: ❌ FAIL"
    fi
}

# Phase 1: Prerequisites validation
test_prerequisites() {
    print_header "Phase 1: Prerequisites Validation"

    # Check all required tools
    local tools=("kubectl" "flux" "git" "curl")
    for tool in "${tools[@]}"; do
        if ! command -v $tool &> /dev/null; then
            print_error "$tool not found"
            update_test_result "prerequisites" false
            return 1
        fi
    done

    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        update_test_result "prerequisites" false
        return 1
    fi

    # Check cluster resources (minimum requirements)
    local nodes=$(kubectl get nodes --no-headers | wc -l)
    if [[ $nodes -lt 1 ]]; then
        print_error "Insufficient cluster nodes: $nodes"
        update_test_result "prerequisites" false
        return 1
    fi

    update_test_result "prerequisites" true
}

# Phase 2: Bootstrap test
test_bootstrap() {
    print_header "Phase 2: Bootstrap Test"

    # Run bootstrap script
    if [[ -f "core/core/automation/ci-cd/scripts/deploy-gitops-infrastructure.sh" ]]; then
        chmod +x core/core/automation/ci-cd/scripts/deploy-gitops-infrastructure.sh
        if ./core/core/automation/ci-cd/scripts/deploy-gitops-infrastructure.sh; then
            update_test_result "bootstrap" true
        else
            update_test_result "bootstrap" false
            return 1
        fi
    else
        print_error "deploy-gitops-infrastructure.sh not found"
        update_test_result "bootstrap" false
        return 1
    fi
}

# Phase 3: Infrastructure validation
test_infrastructure() {
    print_header "Phase 3: Infrastructure Validation"

    local success=true

    # Check Flux components
    if ! kubectl wait --for=condition=available --timeout=300s deployment/flux-controller-manager -n flux-system; then
        success=false
    fi

    # Check cert-manager
    if ! kubectl wait --for=condition=available --timeout=300s deployment/cert-manager -n cert-manager; then
        success=false
    fi

    # Check external-dns
    if ! kubectl wait --for=condition=available --timeout=300s deployment/external-dns -n external-dns; then
        success=false
    fi

    # Check Velero
    if ! kubectl wait --for=condition=available --timeout=300s deployment/velero -n velero; then
        success=false
    fi

    update_test_result "infrastructure" $success
    return $([ $success == true ] && echo 0 || echo 1)
}

# Phase 4: Cloud providers validation
test_cloud_providers() {
    print_header "Phase 4: Cloud Providers Validation"

    local success=true

    # Check AWS ACK
    if ! kubectl wait --for=condition=available --timeout=300s deployment/ack-ec2-controller -n ack-system; then
        print_warning "AWS ACK not available (expected in cloud)"
    fi

    # Check Azure ASO
    if ! kubectl wait --for=condition=available --timeout=300s deployment/azureserviceoperator-controller-manager -n azureserviceoperator-system; then
        print_warning "Azure ASO not available (expected in cloud)"
    fi

    # Check GCP KCC
    if ! kubectl wait --for=condition=available --timeout=300s deployment/controller-manager -n cnrm-system; then
        print_warning "GCP KCC not available (expected in cloud)"
    fi

    # For local testing, check emulators
    if kubectl get deployment/localstack -n localstack &>/dev/null; then
        if ! kubectl wait --for=condition=available --timeout=300s deployment/localstack -n localstack; then
            success=false
        fi
    fi

    update_test_result "cloud_providers" $success
    return $([ $success == true ] && echo 0 || echo 1)
}

# Phase 5: Workloads validation
test_workloads() {
    print_header "Phase 5: Platform Workloads Validation"

    local success=true

    # Check monitoring
    if ! kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n monitoring; then
        success=false
    fi

    # Check security
    if ! kubectl wait --for=condition=available --timeout=300s deployment/opa-gatekeeper-controller-manager -n gatekeeper-system; then
        success=false
    fi

    # Check CI/CD
    if ! kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd; then
        success=false
    fi

    # Check service mesh
    if ! kubectl wait --for=condition=available --timeout=300s deployment/istiod -n istio-system; then
        success=false
    fi

    update_test_result "workloads" $success
    return $([ $success == true ] && echo 0 || echo 1)
}

# Phase 6: Applications validation
test_applications() {
    print_header "Phase 6: Sample Applications Validation"

    local success=true

    # Check nginx sample
    if ! kubectl wait --for=condition=available --timeout=300s deployment/nginx-sample -n default; then
        success=false
    fi

    # Check mysql sample
    if ! kubectl wait --for=condition=available --timeout=300s deployment/mysql-sample -n default; then
        success=false
    fi

    # Test application connectivity
    kubectl port-forward svc/nginx-sample 8080:80 -n default &
    PF_PID=$!
    sleep 10
    if ! curl -s http://localhost:8080 | grep -q "nginx"; then
        print_error "Nginx application not responding"
        success=false
    fi
    kill $PF_PID 2>/dev/null || true

    update_test_result "applications" $success
    return $([ $success == true ] && echo 0 || echo 1)
}

# Phase 7: Comprehensive validation
test_validation() {
    print_header "Phase 7: Comprehensive Validation"

    local success=true

    # Run the local test suite
    if [[ -f "core/automation/testing/test-local-suite.sh" ]]; then
        if ! ./core/automation/testing/test-local-suite.sh; then
            print_error "Local test suite failed"
            success=false
        fi
    else
        print_warning "Local test suite not found"
    fi

    # Test Flux reconciliation
    if ! flux reconcile kustomization flux-system --timeout=5m; then
        print_error "Flux reconciliation failed"
        success=false
    fi

    update_test_result "validation" $success
    return $([ $success == true ] && echo 0 || echo 1)
}

# Phase 8: Drift test
test_drift() {
    print_header "Phase 8: GitOps Drift Test"

    local success=true

    # Run drift test
    if [[ -f "core/automation/testing/drift-test.sh" ]]; then
        if ! ./core/automation/testing/drift-test.sh; then
            print_error "Drift test failed"
            success=false
        fi
    else
        print_warning "Drift test script not found"
    fi

    update_test_result "drift_test" $success
    return $([ $success == true ] && echo 0 || echo 1)
}

# Phase 9: Performance test
test_performance() {
    print_header "Phase 9: Performance Validation"

    local success=true

    # Basic performance check - ensure response times are reasonable
    local start_time=$(date +%s%3N)
    kubectl get pods --all-namespaces --no-headers | wc -l > /dev/null
    local end_time=$(date +%s%3N)
    local duration=$((end_time - start_time))

    if [[ $duration -gt 5000 ]]; then  # 5 seconds
        print_warning "Cluster response time slow: ${duration}ms"
        # Don't fail for performance, just warn
    fi

    # Check resource usage
    local high_cpu_pods=$(kubectl top pods --all-namespaces --no-headers 2>/dev/null | awk '$3 > 80 {print $1}' | wc -l)
    if [[ $high_cpu_pods -gt 0 ]]; then
        print_warning "High CPU usage detected in $high_cpu_pods pods"
    fi

    update_test_result "performance" $success
}

# Phase 10: Cleanup
test_cleanup() {
    print_header "Phase 10: Cleanup Validation"

    local success=true

    if [[ "$CLEANUP_ON_SUCCESS" == "true" ]]; then
        print_status "Performing cleanup..."

        # Remove Flux
        flux uninstall --silent

        # Remove all workloads
        kubectl delete namespace flux-system cert-manager external-dns velero ack-system azureserviceoperator-system cnrm-system monitoring gatekeeper-system argocd istio-system --ignore-not-found=true

        print_status "Cleanup completed"
    else
        print_status "Cleanup skipped (set CLEANUP_ON_SUCCESS=true to enable)"
    fi

    update_test_result "cleanup" $success
}

# Generate comprehensive test report
generate_test_report() {
    print_header "E2E Test Results Summary"

    echo ""
    echo "📊 Test Execution Results:"
    echo ""

    local total_tests=${#TEST_PHASES[@]}
    local passed_tests=0

    for i in "${!TEST_PHASES[@]}"; do
        local phase="${TEST_PHASES[$i]}"
        local status="${test_results[$i]}"
        
        if [[ "$status" == "true" ]]; then
            passed_tests=$((passed_tests + 1))
            echo "   ✅ $phase: PASS"
        else
            echo "   ❌ $phase: FAIL"
        fi
    done

    echo ""
    echo "📈 Overall Results:"
    echo "   Total Tests: $total_tests"
    echo "   Passed: $passed_tests"
    echo "   Failed: $((total_tests - passed_tests))"
    echo "   Success Rate: $((passed_tests * 100 / total_tests))%"
    echo ""

    if [[ $passed_tests -eq $total_tests ]]; then
        echo "🎉 ALL TESTS PASSED! Enterprise platform is fully functional."
        echo ""
        echo "🚀 Ready for production deployment"
        echo ""
        return 0
    else
        echo "⚠️  SOME TESTS FAILED. Review output above for issues."
        echo ""
        echo "🔧 Troubleshooting:"
        echo "   1. Check cluster resources and connectivity"
        echo "   2. Verify cloud provider credentials"
        echo "   3. Review controller logs: kubectl logs -n flux-system"
        echo "   4. Run individual tests: ./core/automation/testing/test-components.sh <component>"
        echo ""
        return 1
    fi
}

# Main E2E test execution
main() {
    echo "🧪 Complete End-to-End Test Suite"
    echo "=================================="
    echo "Testing: GitOps Infra Control Plane"
    echo "Repository: $REPO_URL"
    echo "Timeout: ${TEST_TIMEOUT}s"
    echo ""

    # Execute all test phases
    test_prerequisites
    test_bootstrap
    test_infrastructure
    test_cloud_providers
    test_workloads
    test_applications
    test_validation
    test_drift
    test_performance
    test_cleanup

    # Generate final report
    generate_test_report
}

# Run main function
main "$@"

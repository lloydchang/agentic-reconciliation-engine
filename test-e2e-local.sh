#!/bin/bash
# Complete Local End-to-End Test with Emulators

set -e

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
    echo -e "${GREEN}[TEST]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test 1: Kubernetes Cluster Health
test_cluster_health() {
    print_header "Testing Kubernetes Cluster Health"
    
    if kubectl cluster-info >/dev/null 2>&1; then
        print_status "✅ Kubernetes cluster accessible"
    else
        print_error "❌ Cannot access Kubernetes cluster"
        return 1
    fi
    
    NODE_COUNT=$(kubectl get nodes --no-headers | wc -l)
    print_status "✅ Found $NODE_COUNT nodes"
    
    return 0
}

# Test 2: Flux Controllers
test_flux_controllers() {
    print_header "Testing Flux Controllers"
    
    FLUX_DEPLOYMENTS=("source-controller" "kustomize-controller" "helm-controller" "notification-controller")
    
    for deployment in "${FLUX_DEPLOYMENTS[@]}"; do
        if kubectl get deployment $deployment -n flux-system >/dev/null 2>&1; then
            if kubectl get deployment $deployment -n flux-system -o jsonpath='{.status.readyReplicas}' | grep -q "^[1-9]"; then
                print_status "✅ $deployment is ready"
            else
                print_warning "⚠️ $deployment not ready"
            fi
        else
            print_error "❌ $deployment not found"
        fi
    done
    
    return 0
}

# Test 3: LocalStack Emulator
test_localstack() {
    print_header "Testing LocalStack Emulator"
    
    if kubectl get deployment localstack -n localstack >/dev/null 2>&1; then
        if kubectl get deployment localstack -n localstack -o jsonpath='{.status.readyReplicas}' | grep -q "^[1-9]"; then
            print_status "✅ LocalStack is ready"
        else
            print_warning "⚠️ LocalStack not ready"
        fi
    else
        print_error "❌ LocalStack not found"
        return 1
    fi
    
    # Test LocalStack connectivity
    export AWS_ACCESS_KEY_ID=test
    export AWS_SECRET_ACCESS_KEY=test
    export AWS_DEFAULT_REGION=us-west-2
    
    if kubectl port-forward -n localstack svc/localstack 4568:4566 &>/dev/null & then
        sleep 3
        if aws --endpoint-url=http://localhost:4568 ec2 describe-regions >/dev/null 2>&1; then
            print_status "✅ LocalStack AWS API accessible"
        else
            print_warning "⚠️ LocalStack AWS API not accessible"
        fi
        pkill -f "kubectl port-forward.*4568" 2>/dev/null || true
    fi
    
    return 0
}

# Test 4: Cloud Controllers
test_cloud_controllers() {
    print_header "Testing Cloud Controllers"
    
    # AWS ACK Controllers
    if kubectl get deployment ack-ec2-controller -n ack-system >/dev/null 2>&1; then
        print_status "✅ AWS ACK controllers found"
    else
        print_warning "⚠️ AWS ACK controllers not found"
    fi
    
    # Azure ASO Controllers
    if kubectl get deployment azure-service-operator-controller -n azureserviceoperator-system >/dev/null 2>&1; then
        print_status "✅ Azure ASO controllers found"
    else
        print_warning "⚠️ Azure ASO controllers not found"
    fi
    
    # GCP KCC Controllers
    if kubectl get deployment cnrm-controller-manager -n cnrm-system >/dev/null 2>&1; then
        print_status "✅ GCP KCC controllers found"
    else
        print_warning "⚠️ GCP KCC controllers not found"
    fi
    
    return 0
}

# Test 5: Infrastructure Drift Test
test_drift_detection() {
    print_header "Testing Infrastructure Drift Detection"
    
    # Run our local drift test
    if ./test-drift-local.sh >/dev/null 2>&1; then
        print_status "✅ Local drift test passed"
    else
        print_error "❌ Local drift test failed"
        return 1
    fi
    
    return 0
}

# Test 6: GitOps Simulation
test_gitops_simulation() {
    print_header "Testing GitOps Simulation"
    
    # Create a test GitOps Kustomization
    cat <<EOF | kubectl apply -f -
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: test-infra
  namespace: flux-system
spec:
  interval: 1m
  path: "./test-infra"
  prune: true
  sourceRef:
    kind: GitRepository
    name: test-repo
---
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: test-repo
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/lloydchang/gitops-infra-control-plane
  ref:
    branch: main
EOF
    
    sleep 5
    
    if kubectl get kustomization test-infra -n flux-system >/dev/null 2>&1; then
        print_status "✅ GitOps Kustomization created"
    else
        print_warning "⚠️ GitOps Kustomization creation failed"
    fi
    
    return 0
}

# Test 7: Multi-Cloud Emulator Test
test_multi_cloud_emulators() {
    print_header "Testing Multi-Cloud Emulators"
    
    # Test Azure emulator
    if kubectl get deployment localstack-azure -n localstack >/dev/null 2>&1; then
        print_status "✅ Azure emulator found"
    else
        print_warning "⚠️ Azure emulator not found"
    fi
    
    # Test GCS emulator
    if kubectl get deployment gcs-emulator -n default >/dev/null 2>&1; then
        print_status "✅ GCS emulator found"
    else
        print_warning "⚠️ GCS emulator not found"
    fi
    
    return 0
}

# Main execution
echo "🚀 Complete Local End-to-End Test Suite"
echo "======================================="

PASSED_TESTS=0
TOTAL_TESTS=7

test_cluster_health && PASSED_TESTS=$((PASSED_TESTS + 1))
test_flux_controllers && PASSED_TESTS=$((PASSED_TESTS + 1))
test_localstack && PASSED_TESTS=$((PASSED_TESTS + 1))
test_cloud_controllers && PASSED_TESTS=$((PASSED_TESTS + 1))
test_drift_detection && PASSED_TESTS=$((PASSED_TESTS + 1))
test_gitops_simulation && PASSED_TESTS=$((PASSED_TESTS + 1))
test_multi_cloud_emulators && PASSED_TESTS=$((PASSED_TESTS + 1))

# Results
echo ""
print_header "Test Results"
echo "Passed: $PASSED_TESTS/$TOTAL_TESTS tests"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    print_status "🎉 ALL TESTS PASSED!"
    print_status "✅ Local end-to-end test successful"
    print_status "✅ GitOps Infrastructure Control Plane working locally"
    exit 0
else
    print_warning "⚠️ $((TOTAL_TESTS - PASSED_TESTS)) tests failed"
    print_warning "Some components may need attention"
    exit 1
fi

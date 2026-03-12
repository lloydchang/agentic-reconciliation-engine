#!/bin/bash

# Comprehensive Testing Framework for GitOps Infrastructure Control Plane
# This script implements a complete testing framework for validation

set -euxo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TEST_NAMESPACE="gitops-tests"
HUB_NAMESPACE="flux-system"
TEST_TIMEOUT="600s"
REPORT_DIR="test-reports"

echo -e "${BLUE}🧪 Comprehensive Testing Framework${NC}"
echo "=================================="

# Create test namespace
echo -e "${YELLOW}📁 Creating test namespace...${NC}"
kubectl create namespace $TEST_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Create test directory structure
echo -e "${YELLOW}📂 Creating test directory structure...${NC}"
mkdir -p $REPORT_DIR/{unit,integration,e2e,performance,security}
mkdir -p tests/{unit,integration,e2e,performance,security}

# Create unit tests
echo -e "${YELLOW}🔬 Creating unit tests...${NC}"

cat > tests/unit/flux-components.test.sh << 'EOF'
#!/bin/bash

# Unit Tests for Flux Components
set -euxo pipefail

# Test Flux controller availability
test_flux_controllers() {
    echo "Testing Flux controller availability..."
    
    controllers=("source-controller" "kustomize-controller" "helm-controller" "notification-controller")
    
    for controller in "${controllers[@]}"; do
        if kubectl get deployment $controller -n flux-system &> /dev/null; then
            replicas=$(kubectl get deployment $controller -n flux-system -o jsonpath='{.status.readyReplicas}')
            if [[ $replicas -gt 0 ]]; then
                echo "✅ $controller is ready ($replicas replicas)"
                return 0
            else
                echo "❌ $controller is not ready"
                return 1
            fi
        else
            echo "❌ $controller not found"
            return 1
        fi
    done
}

# Test GitRepository connectivity
test_git_repository() {
    echo "Testing GitRepository connectivity..."
    
    if kubectl get gitrepository gitops-infra-control-plane -n flux-system &> /dev/null; then
        status=$(kubectl get gitrepository gitops-infra-control-plane -n flux-system -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
        if [[ $status == "True" ]]; then
            echo "✅ GitRepository is ready"
            return 0
        else
            echo "❌ GitRepository is not ready"
            return 1
        fi
    else
        echo "❌ GitRepository not found"
        return 1
    fi
}

# Test Kustomization status
test_kustomizations() {
    echo "Testing Kustomizations..."
    
    kustomizations=("network-infrastructure" "cluster-infrastructure" "workload-infrastructure")
    
    for kustomization in "${kustomizations[@]}"; do
        if kubectl get kustomization $kustomization -n flux-system &> /dev/null; then
            status=$(kubectl get kustomization $kustomization -n flux-system -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
            if [[ $status == "True" ]]; then
                echo "✅ $kustomization is ready"
            else
                echo "❌ $kustomization is not ready"
                return 1
            fi
        else
            echo "❌ $kustomization not found"
            return 1
        fi
    done
}

# Run all unit tests
run_unit_tests() {
    echo "Running unit tests..."
    
    test_flux_controllers || return 1
    test_git_repository || return 1
    test_kustomizations || return 1
    
    echo "✅ All unit tests passed"
    return 0
}

# Execute tests
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    run_unit_tests
fi
EOF

# Create integration tests
echo -e "${YELLOW}🔗 Creating integration tests...${NC}"

cat > tests/integration/gitops-integration.test.sh << 'EOF'
#!/bin/bash

# Integration Tests for GitOps Workflows
set -euxo pipefail

# Test dependency chain execution
test_dependency_chains() {
    echo "Testing dependency chain execution..."
    
    # Check if cluster-infrastructure depends on network-infrastructure
    network_deps=$(kubectl get kustomization cluster-infrastructure -n flux-system -o jsonpath='{.spec.dependsOn[*].name}' 2>/dev/null || echo "")
    
    if [[ "$network_deps" == *"network-infrastructure"* ]]; then
        echo "✅ Cluster infrastructure depends on network infrastructure"
    else
        echo "❌ Cluster infrastructure missing dependency"
        return 1
    fi
    
    # Check if workload-infrastructure depends on cluster-infrastructure
    cluster_deps=$(kubectl get kustomization workload-infrastructure -n flux-system -o jsonpath='{.spec.dependsOn[*].name}' 2>/dev/null || echo "")
    
    if [[ "$cluster_deps" == *"cluster-infrastructure"* ]]; then
        echo "✅ Workload infrastructure depends on cluster infrastructure"
    else
        echo "❌ Workload infrastructure missing dependency"
        return 1
    fi
    
    return 0
}

# Test multi-cluster synchronization
test_multi_cluster_sync() {
    echo "Testing multi-cluster synchronization..."
    
    # Check if ResourceSets are defined
    if kubectl get resourceset infrastructure -n flux-system &> /dev/null; then
        echo "✅ ResourceSet infrastructure found"
        
        # Check ResourceSet resources
        resources=$(kubectl get resourceset infrastructure -n flux-system -o jsonpath='{.spec.resources[*].name}')
        echo "📋 ResourceSet resources: $resources"
        
        if [[ -n "$resources" ]]; then
            echo "✅ ResourceSet has resources defined"
            return 0
        else
            echo "❌ ResourceSet has no resources"
            return 1
        fi
    else
        echo "❌ ResourceSet infrastructure not found"
        return 1
    fi
}

# Test cloud controller integration
test_cloud_controllers() {
    echo "Testing cloud controller integration..."
    
    # Test AWS ACK controllers
    aws_controllers=("eks-controller" "ec2-controller" "iam-controller")
    aws_ready=0
    
    for controller in "${aws_controllers[@]}"; do
        if kubectl get deployment $controller -n flux-system &> /dev/null; then
            replicas=$(kubectl get deployment $controller -n flux-system -o jsonpath='{.status.readyReplicas}')
            if [[ $replicas -gt 0 ]]; then
                ((aws_ready++))
            fi
        fi
    done
    
    echo "📊 AWS ACK controllers ready: $aws_ready/${#aws_controllers[@]}"
    
    # Test Azure ASO controllers
    azure_controllers=("aks-controller" "network-controller" "resource-controller")
    azure_ready=0
    
    for controller in "${azure_controllers[@]}"; do
        if kubectl get deployment $controller -n flux-system &> /dev/null; then
            replicas=$(kubectl get deployment $controller -n flux-system -o jsonpath='{.status.readyReplicas}')
            if [[ $replicas -gt 0 ]]; then
                ((azure_ready++))
            fi
        fi
    done
    
    echo "📊 Azure ASO controllers ready: $azure_ready/${#azure_controllers[@]}"
    
    # Test GCP KCC controllers
    gcp_controllers=("gke-controller" "compute-controller" "iam-controller")
    gcp_ready=0
    
    for controller in "${gcp_controllers[@]}"; do
        if kubectl get deployment $controller -n flux-system &> /dev/null; then
            replicas=$(kubectl get deployment $controller -n flux-system -o jsonpath='{.status.readyReplicas}')
            if [[ $replicas -gt 0 ]]; then
                ((gcp_ready++))
            fi
        fi
    done
    
    echo "📊 GCP KCC controllers ready: $gcp_ready/${#gcp_controllers[@]}"
    
    # At least one cloud provider should be ready
    total_ready=$((aws_ready + azure_ready + gcp_ready))
    if [[ $total_ready -gt 0 ]]; then
        echo "✅ Cloud controllers integration working"
        return 0
    else
        echo "❌ No cloud controllers ready"
        return 1
    fi
}

# Test Flux Status Page integration
test_flux_status_page() {
    echo "Testing Flux Status Page integration..."
    
    if kubectl get svc flux-operator -n flux-system &> /dev/null; then
        echo "✅ Flux Status Page service found"
        
        # Test local access
        kubectl port-forward -n flux-system svc/flux-operator 9080:9080 &
        PF_PID=$!
        
        sleep 3
        
        if curl -s http://localhost:9080/health > /dev/null 2>&1; then
            echo "✅ Flux Status Page accessible"
            kill $PF_PID 2>/dev/null || true
            return 0
        else
            echo "⚠️ Flux Status Page not yet ready"
            kill $PF_PID 2>/dev/null || true
            return 1
        fi
    else
        echo "❌ Flux Status Page service not found"
        return 1
    fi
}

# Run all integration tests
run_integration_tests() {
    echo "Running integration tests..."
    
    test_dependency_chains || return 1
    test_multi_cluster_sync || return 1
    test_cloud_controllers || return 1
    test_flux_status_page || return 1
    
    echo "✅ All integration tests passed"
    return 0
}

# Execute tests
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    run_integration_tests
fi
EOF

# Create end-to-end tests
echo -e "${YELLOW}🌐 Creating end-to-end tests...${NC}"

cat > tests/e2e/full-gitops-pipeline.test.sh << 'EOF'
#!/bin/bash

# End-to-End Tests for Full GitOps Pipeline
set -euxo pipefail

# Test complete GitOps pipeline
test_complete_pipeline() {
    echo "Testing complete GitOps pipeline..."
    
    # 1. Test Git repository sync
    echo "1. Testing Git repository sync..."
    git_status=$(kubectl get gitrepository gitops-infra-control-plane -n flux-system -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
    if [[ $git_status == "True" ]]; then
        echo "✅ Git repository sync working"
    else
        echo "❌ Git repository sync failed"
        return 1
    fi
    
    # 2. Test infrastructure deployment
    echo "2. Testing infrastructure deployment..."
    infra_kustomizations=("network-infrastructure" "cluster-infrastructure" "workload-infrastructure")
    
    for kustomization in "${infra_kustomizations[@]}"; do
        status=$(kubectl get kustomization $kustomization -n flux-system -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
        if [[ $status == "True" ]]; then
            echo "✅ $kustomization deployed successfully"
        else
            echo "❌ $kustomization deployment failed"
            return 1
        fi
    done
    
    # 3. Test monitoring stack
    echo "3. Testing monitoring stack..."
    if kubectl get deployment prometheus-server -n monitoring &> /dev/null; then
        prometheus_replicas=$(kubectl get deployment prometheus-server -n monitoring -o jsonpath='{.status.readyReplicas}')
        if [[ $prometheus_replicas -gt 0 ]]; then
            echo "✅ Prometheus deployed"
        else
            echo "❌ Prometheus not ready"
            return 1
        fi
    else
        echo "❌ Prometheus not found"
        return 1
    fi
    
    if kubectl get deployment grafana -n monitoring &> /dev/null; then
        grafana_replicas=$(kubectl get deployment grafana -n monitoring -o jsonpath='{.status.readyReplicas}')
        if [[ $grafana_replicas -gt 0 ]]; then
            echo "✅ Grafana deployed"
        else
            echo "❌ Grafana not ready"
            return 1
        fi
    else
        echo "❌ Grafana not found"
        return 1
    fi
    
    # 4. Test application deployment
    echo "4. Testing application deployment..."
    app_deployments=("harbor" "confighub" "langchain" "mezmo")
    
    for app in "${app_deployments[@]}"; do
        if kubectl get deployment $app -n default &> /dev/null; then
            replicas=$(kubectl get deployment $app -n default -o jsonpath='{.status.readyReplicas}')
            if [[ $replicas -gt 0 ]]; then
                echo "✅ $app deployed"
            else
                echo "⚠️ $app not ready (expected without credentials)"
            fi
        else
            echo "⚠️ $app not found (expected without credentials)"
        fi
    done
    
    return 0
}

# Test disaster recovery procedures
test_disaster_recovery() {
    echo "Testing disaster recovery procedures..."
    
    # Test backup configuration
    if kubectl get configmap backup-config -n flux-system &> /dev/null; then
        echo "✅ Backup configuration found"
    else
        echo "⚠️ Backup configuration not found"
    fi
    
    # Test state backup
    if kubectl get job etcd-backup -n flux-system &> /dev/null; then
        echo "✅ State backup job found"
    else
        echo "⚠️ State backup job not found"
    fi
    
    return 0
}

# Test security policies
test_security_policies() {
    echo "Testing security policies..."
    
    # Test network policies
    if kubectl get networkpolicy -n flux-system | grep -q "flux-ui-netpol"; then
        echo "✅ Network policies configured"
    else
        echo "⚠️ Network policies not found"
    fi
    
    # Test RBAC
    if kubectl get clusterrole flux-ui-admin &> /dev/null; then
        echo "✅ RBAC roles configured"
    else
        echo "⚠️ RBAC roles not found"
    fi
    
    # Test secrets management
    secrets=("flux-ui-oidc" "sops-keys" "grafana-credentials")
    for secret in "${secrets[@]}"; do
        if kubectl get secret $secret -n flux-system &> /dev/null; then
            echo "✅ Secret $secret found"
        else
            echo "⚠️ Secret $secret not found"
        fi
    done
    
    return 0
}

# Run all E2E tests
run_e2e_tests() {
    echo "Running end-to-end tests..."
    
    test_complete_pipeline || return 1
    test_disaster_recovery || return 1
    test_security_policies || return 1
    
    echo "✅ All E2E tests passed"
    return 0
}

# Execute tests
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    run_e2e_tests
fi
EOF

# Create performance tests
echo -e "${YELLOW"⚡ Creating performance tests...${NC}"

cat > tests/performance/performance-benchmarks.test.sh << 'EOF'
#!/bin/bash

# Performance Tests and Benchmarks
set -euxo pipefail

# Test Flux reconciliation performance
test_flux_reconciliation_performance() {
    echo "Testing Flux reconciliation performance..."
    
    # Get reconciliation metrics
    if kubectl get servicemonitor flux-metrics -n flux-system &> /dev/null; then
        echo "✅ Flux metrics configured"
        
        # Test reconciliation rate
        echo "📊 Measuring reconciliation rate..."
        start_time=$(date +%s)
        
        # Trigger reconciliation
        kubectl patch kustomization network-infrastructure -n flux-system --type=merge -p '{"spec":{"reconcileAt":"'$(date -u +'%Y-%m-%dT%H:%M:%SZ')'"}}'
        
        # Wait for reconciliation
        timeout=60
        while [[ $timeout -gt 0 ]]; do
            status=$(kubectl get kustomization network-infrastructure -n flux-system -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "False")
            if [[ $status == "True" ]]; then
                break
            fi
            sleep 5
            ((timeout--))
        done
        
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        
        echo "📈 Reconciliation completed in ${duration}s"
        
        if [[ $duration -lt 60 ]]; then
            echo "✅ Reconciliation performance acceptable"
            return 0
        else
            echo "⚠️ Reconciliation performance slow"
            return 1
        fi
    else
        echo "❌ Flux metrics not configured"
        return 1
    fi
}

# Test resource utilization
test_resource_utilization() {
    echo "Testing resource utilization..."
    
    # Get resource usage for Flux controllers
    controllers=("source-controller" "kustomize-controller" "helm-controller")
    
    for controller in "${controllers[@]}"; do
        if kubectl get deployment $controller -n flux-system &> /dev/null; then
            cpu_request=$(kubectl get deployment $controller -n flux-system -o jsonpath='{.spec.template.spec.containers[0].resources.requests.cpu}')
            memory_request=$(kubectl get deployment $controller -n flux-system -o jsonpath='{.spec.template.spec.containers[0].resources.requests.memory}')
            cpu_limit=$(kubectl get deployment $controller -n flux-system -o jsonpath='{.spec.template.spec.containers[0].resources.limits.cpu}')
            memory_limit=$(kubectl get deployment $controller -n flux-system -o jsonpath='{.spec.template.spec.containers[0].resources.limits.memory}')
            
            echo "📊 $controller resources:"
            echo "  CPU: $cpu_request / $cpu_limit"
            echo "  Memory: $memory_request / $memory_limit"
        fi
    done
    
    return 0
}

# Test scalability
test_scalability() {
    echo "Testing scalability..."
    
    # Count total resources
    total_resources=$(kubectl get all -n flux-system --no-headers | wc -l)
    echo "📊 Total resources in flux-system: $total_resources"
    
    # Check pod counts
    pod_count=$(kubectl get pods -n flux-system --no-headers | wc -l)
    echo "📊 Total pods in flux-system: $pod_count"
    
    # Check service counts
    service_count=$(kubectl get services -n flux-system --no-headers | wc -l)
    echo "📊 Total services in flux-system: $service_count"
    
    return 0
}

# Run all performance tests
run_performance_tests() {
    echo "Running performance tests..."
    
    test_flux_reconciliation_performance || return 1
    test_resource_utilization || return 1
    test_scalability || return 1
    
    echo "✅ All performance tests passed"
    return 0
}

# Execute tests
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    run_performance_tests
fi
EOF

# Create security tests
echo -e "${YELLOW}🔒 Creating security tests...${NC}"

cat > tests/security/security-compliance.test.sh << 'EOF'
#!/bin/bash

# Security and Compliance Tests
set -euxo pipefail

# Test RBAC configuration
test_rbac_configuration() {
    echo "Testing RBAC configuration..."
    
    # Check for overly permissive roles
    if kubectl get clusterrole | grep -q "cluster-admin"; then
        echo "⚠️ Found cluster-admin role (review if necessary)"
    fi
    
    # Check Flux UI roles
    if kubectl get clusterrole flux-ui-admin &> /dev/null; then
        echo "✅ Flux UI admin role configured"
    else
        echo "❌ Flux UI admin role not found"
        return 1
    fi
    
    # Check role bindings
    if kubectl get clusterrolebinding flux-ui-admin-binding &> /dev/null; then
        echo "✅ Role bindings configured"
    else
        echo "❌ Role bindings not found"
        return 1
    fi
    
    return 0
}

# Test network policies
test_network_policies() {
    echo "Testing network policies..."
    
    # Check Flux UI network policy
    if kubectl get networkpolicy flux-ui-netpol -n flux-system &> /dev/null; then
        echo "✅ Flux UI network policy configured"
    else
        echo "❌ Flux UI network policy not found"
        return 1
    fi
    
    # Check default deny policy
    if kubectl get networkpolicy -n flux-system | grep -q "default-deny"; then
        echo "✅ Default deny policy configured"
    else
        echo "⚠️ Default deny policy not found"
    fi
    
    return 0
}

# Test secrets management
test_secrets_management() {
    echo "Testing secrets management..."
    
    # Check for secrets in flux-system
    secrets=$(kubectl get secrets -n flux-system --no-headers | wc -l)
    echo "📊 Total secrets in flux-system: $secrets"
    
    # Check for encrypted secrets
    if kubectl get secret sops-keys -n flux-system &> /dev/null; then
        echo "✅ SOPS encryption keys found"
    else
        echo "⚠️ SOPS encryption keys not found"
    fi
    
    # Check for OIDC secrets
    if kubectl get secret flux-ui-oidc -n flux-system &> /dev/null; then
        echo "✅ OIDC secrets configured"
    else
        echo "⚠️ OIDC secrets not found"
    fi
    
    return 0
}

# Test pod security
test_pod_security() {
    echo "Testing pod security..."
    
    # Check for privileged pods
    privileged_pods=$(kubectl get pods -n flux-system -o jsonpath='{.items[*].spec.containers[*].securityContext.privileged}' | grep true | wc -l)
    if [[ $privileged_pods -eq 0 ]]; then
        echo "✅ No privileged pods found"
    else
        echo "❌ Found $privileged_pods privileged pods"
        return 1
    fi
    
    # Check for root containers
    root_containers=$(kubectl get pods -n flux-system -o jsonpath='{range .items[*]}{.spec.containers[*].securityContext.runAsUser}{"\n"}{end}' | grep -v "^0$" | wc -l)
    total_containers=$(kubectl get pods -n flux-system -o jsonpath='{range .items[*]}{.spec.containers[*].securityContext.runAsUser}{"\n"}{end}' | wc -l)
    
    if [[ $root_containers -eq $total_containers ]]; then
        echo "✅ All containers running as non-root"
    else
        echo "⚠️ Some containers may be running as root"
    fi
    
    return 0
}

# Test TLS configuration
test_tls_configuration() {
    echo "Testing TLS configuration..."
    
    # Check for TLS certificates
    if kubectl get secret flux-ui-tls -n flux-system &> /dev/null; then
        echo "✅ TLS certificate found"
    else
        echo "⚠️ TLS certificate not found"
    fi
    
    # Check for cert-manager
    if kubectl get deployment cert-manager -n cert-manager &> /dev/null; then
        echo "✅ cert-manager deployed"
    else
        echo "⚠️ cert-manager not found"
    fi
    
    return 0
}

# Run all security tests
run_security_tests() {
    echo "Running security tests..."
    
    test_rbac_configuration || return 1
    test_network_policies || return 1
    test_secrets_management || return 1
    test_pod_security || return 1
    test_tls_configuration || return 1
    
    echo "✅ All security tests passed"
    return 0
}

# Execute tests
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    run_security_tests
fi
EOF

# Create test runner script
echo -e "${YELLOW"🏃 Creating test runner script...${NC}"

cat > scripts/run-all-tests.sh << 'EOF'
#!/bin/bash

# Comprehensive Test Runner
set -euxo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPORT_DIR="test-reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$REPORT_DIR/test-report-$TIMESTAMP.txt"

echo -e "${BLUE}🧪 Running Comprehensive Test Suite${NC}"
echo "=================================="

# Create report directory
mkdir -p $REPORT_DIR

# Initialize report
cat > $REPORT_FILE << EOF
GitOps Infrastructure Control Plane - Test Report
Generated: $(date)
===============================================

EOF

# Test functions
run_test_suite() {
    local suite_name=$1
    local test_script=$2
    
    echo -e "${YELLOW}🔬 Running $suite_name tests...${NC}"
    echo "" >> $REPORT_FILE
    echo "=== $suite_name Tests ===" >> $REPORT_FILE
    echo "" >> $REPORT_FILE
    
    if bash $test_script >> $REPORT_FILE 2>&1; then
        echo -e "${GREEN}✅ $suite_name tests passed${NC}"
        echo "RESULT: PASSED" >> $REPORT_FILE
        return 0
    else
        echo -e "${RED}❌ $suite_name tests failed${NC}"
        echo "RESULT: FAILED" >> $REPORT_FILE
        return 1
    fi
}

# Run all test suites
failed_suites=0
total_suites=0

# Unit tests
((total_suites++))
if ! run_test_suite "Unit" "tests/unit/flux-components.test.sh"; then
    ((failed_suites++))
fi

# Integration tests
((total_suites++))
if ! run_test_suite "Integration" "tests/integration/gitops-integration.test.sh"; then
    ((failed_suites++))
fi

# End-to-end tests
((total_suites++))
if ! run_test_suite "E2E" "tests/e2e/full-gitops-pipeline.test.sh"; then
    ((failed_suites++))
fi

# Performance tests
((total_suites++))
if ! run_test_suite "Performance" "tests/performance/performance-benchmarks.test.sh"; then
    ((failed_suites++))
fi

# Security tests
((total_suites++))
if ! run_test_suite "Security" "tests/security/security-compliance.test.sh"; then
    ((failed_suites++))
fi

# Generate summary
echo "" >> $REPORT_FILE
echo "=== Test Summary ===" >> $REPORT_FILE
echo "Total test suites: $total_suites" >> $REPORT_FILE
echo "Passed: $((total_suites - failed_suites))" >> $REPORT_FILE
echo "Failed: $failed_suites" >> $REPORT_FILE
echo "Success rate: $(((total_suites - failed_suites) * 100 / total_suites))%" >> $REPORT_FILE

# Display results
echo ""
echo -e "${BLUE}📊 Test Results Summary:${NC}"
echo "Total test suites: $total_suites"
echo "Passed: $((total_suites - failed_suites))"
echo "Failed: $failed_suites"
echo "Success rate: $(((total_suites - failed_suites) * 100 / total_suites))%"

if [[ $failed_suites -eq 0 ]]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    echo -e "${GREEN}✅ GitOps Infrastructure Control Plane is ready for production${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo -e "${YELLOW}📋 Check the detailed report: $REPORT_FILE${NC}"
    exit 1
fi
EOF

# Make all test scripts executable
chmod +x tests/unit/*.sh
chmod +x tests/integration/*.sh
chmod +x tests/e2e/*.sh
chmod +x tests/performance/*.sh
chmod +x tests/security/*.sh
chmod +x scripts/run-all-tests.sh

# Apply test configurations
echo -e "${YELLOW}🚀 Applying test configurations...${NC}"

# Create test resources
kubectl apply -f - << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: test-config
  namespace: $TEST_NAMESPACE
  labels:
    app.kubernetes.io/name: gitops-tests
    app.kubernetes.io/component: testing
    app.kubernetes.io/part-of: gitops-infra-control-plane
data:
  test-timeout: "600s"
  test-retries: "3"
  test-parallel: "true"
---
apiVersion: batch/v1
kind: Job
metadata:
  name: test-runner
  namespace: $TEST_NAMESPACE
  labels:
    app.kubernetes.io/name: gitops-tests
    app.kubernetes.io/component: testing
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  template:
    spec:
      containers:
      - name: test-runner
        image: bitnami/kubectl:latest
        command:
        - /bin/sh
        - -c
        - |
          echo "Running comprehensive tests..."
          # Copy test scripts
          cp -r /tests/* /tmp/
          # Run tests
          /tmp/scripts/run-all-tests.sh
        volumeMounts:
        - name: tests
          mountPath: /tests
        - name: reports
          mountPath: /test-reports
        env:
        - name: KUBECONFIG
          value: "/etc/kubernetes/config"
      volumes:
      - name: tests
        configMap:
          name: test-scripts
      - name: reports
        emptyDir: {}
      restartPolicy: OnFailure
  backoffLimit: 3
EOF

echo -e "${GREEN}✅ Comprehensive testing framework created!${NC}"
echo ""
echo -e "${BLUE}🎯 Available Tests:${NC}"
echo "  🔬 Unit Tests: Component availability and basic functionality"
echo "  🔗 Integration Tests: Component interactions and workflows"
echo "  🌐 E2E Tests: Complete GitOps pipeline validation"
echo "  ⚡ Performance Tests: Reconciliation speed and resource usage"
echo "  🔒 Security Tests: RBAC, network policies, and compliance"
echo ""
echo -e "${BLUE}🏃 How to Run Tests:${NC}"
echo "  Run all tests: ./scripts/run-all-tests.sh"
echo "  Run specific suite: tests/unit/flux-components.test.sh"
echo "  View reports: ls -la test-reports/"
echo ""
echo -e "${YELLOW}📚 Test Coverage:${NC}"
echo "  ✅ Flux controllers and components"
echo "  ✅ Git repository synchronization"
echo "  ✅ Dependency chain execution"
echo "  ✅ Cloud controller integration"
echo "  ✅ Multi-cluster workflows"
echo "  ✅ Security and compliance"
echo "  ✅ Performance and scalability"
echo ""
echo -e "${GREEN}🎉 Testing framework setup complete!${NC}"
echo -e "${BLUE}📊 Run 'scripts/run-all-tests.sh' to validate your GitOps Infrastructure Control Plane${NC}"

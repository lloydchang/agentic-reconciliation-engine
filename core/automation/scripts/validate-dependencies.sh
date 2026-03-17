#!/bin/bash

# Dependency Validation Script
# Validates and tests the practical implementation of all mitigation strategies

set -euo pipefail

# Configuration
NAMESPACE="${NAMESPACE:-flux-system}"
TEST_TIMEOUT="${TEST_TIMEOUT:-300}" # 5 minutes
VERBOSE="${VERBOSE:-false}"
DRY_RUN="${DRY_RUN:-false}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

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

log_test() {
    echo -e "${PURPLE}[TEST]${NC} $1"
}

log_result() {
    local status=$1
    local message=$2
    
    if [[ "$status" == "PASS" ]]; then
        echo -e "  ${GREEN}✓ PASS${NC} $message"
        ((TESTS_PASSED++))
    elif [[ "$status" == "FAIL" ]]; then
        echo -e "  ${RED}✗ FAIL${NC} $message"
        ((TESTS_FAILED++))
    elif [[ "$status" == "SKIP" ]]; then
        echo -e "  ${YELLOW}- SKIP${NC} $message"
    fi
    
    ((TESTS_TOTAL++))
}

# Test helper functions
wait_for_resource() {
    local resource_type=$1
    local resource_name=$2
    local namespace=$3
    local timeout=$4
    local condition=${5:-"Ready"}
    
    log_debug "Waiting for $resource_type/$resource_name to be $condition (timeout: ${timeout}s)..."
    
    local start_time=$(date +%s)
    local end_time=$((start_time + timeout))
    
    while [[ $(date +%s) -lt $end_time ]]; do
        local status
        case $resource_type in
            "deployment"|"pod"|"service")
                status=$(kubectl get $resource_type -n $namespace $resource_name -o jsonpath='{.status.conditions[?(@.type=="'$condition'")].status}' 2>/dev/null || echo "Unknown")
                ;;
            "kustomization"|"helmrelease")
                status=$(kubectl get $resource_type -n $namespace $resource_name -o jsonpath='{.status.conditions[?(@.type=="'$condition'")].status}' 2>/dev/null || echo "Unknown")
                ;;
            *)
                status="Unknown"
                ;;
        esac
        
        if [[ "$status" == "True" ]]; then
            return 0
        fi
        
        sleep 5
    done
    
    return 1
}

check_resource_exists() {
    local resource_type=$1
    local resource_name=$2
    local namespace=$3
    
    kubectl get $resource_type -n $namespace $resource_name &>/dev/null
}

# Test 1: Multi-Hub Architecture Validation
test_multi_hub_architecture() {
    log_test "Testing Multi-Hub Architecture Implementation"
    
    # Check if Karmada is installed
    if check_resource_exists "customresourcedefinition" "clusters.cluster.karmada.io" ""; then
        log_result "PASS" "Karmada CRDs are installed"
    else
        log_result "FAIL" "Karmada CRDs are not installed"
        return
    fi
    
    # Check if multi-hub configuration exists
    if kubectl get configmap -n $NAMESPACE hub-failover-config &>/dev/null; then
        log_result "PASS" "Hub failover configuration exists"
    else
        log_result "FAIL" "Hub failover configuration not found"
    fi
    
    # Check if propagation policies exist
    if kubectl get propagationpolicy -n $NAMESPACE &>/dev/null; then
        local policy_count=$(kubectl get propagationpolicy -n $NAMESPACE --no-headers | wc -l)
        if [[ $policy_count -gt 0 ]]; then
            log_result "PASS" "Found $policy_count propagation policies"
        else
            log_result "FAIL" "No propagation policies found"
        fi
    else
        log_result "FAIL" "Propagation policies not available"
    fi
    
    # Check if override policies exist
    if kubectl get overridepolicy -n $NAMESPACE &>/dev/null; then
        local override_count=$(kubectl get overridepolicy -n $NAMESPACE --no-headers | wc -l)
        if [[ $override_count -gt 0 ]]; then
            log_result "PASS" "Found $override_count override policies"
        else
            log_result "SKIP" "No override policies found (optional)"
        fi
    else
        log_result "SKIP" "Override policies not available (optional)"
    fi
}

# Test 2: Unified Controller Installer Validation
test_unified_controller_installer() {
    log_test "Testing Unified Controller Installer"
    
    # Check if unified installer HelmRelease exists
    if kubectl get helmrelease -n $NAMESPACE cloud-controllers &>/dev/null; then
        log_result "PASS" "Unified controller HelmRelease exists"
    else
        log_result "FAIL" "Unified controller HelmRelease not found"
    fi
    
    # Check if controller configuration templates exist
    if kubectl get configmap -n $NAMESPACE controller-config-templates &>/dev/null; then
        log_result "PASS" "Controller configuration templates exist"
    else
        log_result "FAIL" "Controller configuration templates not found"
    fi
    
    # Check if AWS controllers are deployed
    local aws_controllers=("aws-ec2-controller" "aws-eks-controller" "aws-vpc-controller" "aws-iam-controller")
    local aws_deployed=0
    
    for controller in "${aws_controllers[@]}"; do
        if check_resource_exists "deployment" "$controller" "$NAMESPACE"; then
            ((aws_deployed++))
        fi
    done
    
    if [[ $aws_deployed -gt 0 ]]; then
        log_result "PASS" "$aws_deployed AWS controllers deployed"
    else
        log_result "FAIL" "No AWS controllers deployed"
    fi
    
    # Check if Azure controllers are deployed
    local azure_controllers=("azure-aks-controller" "azure-network-controller")
    local azure_deployed=0
    
    for controller in "${azure_controllers[@]}"; do
        if check_resource_exists "deployment" "$controller" "$NAMESPACE"; then
            ((azure_deployed++))
        fi
    done
    
    if [[ $azure_deployed -gt 0 ]]; then
        log_result "PASS" "$azure_deployed Azure controllers deployed"
    else
        log_result "SKIP" "No Azure controllers deployed (optional)"
    fi
    
    # Check if GCP controllers are deployed
    local gcp_controllers=("gcp-gke-controller" "gcp-compute-controller")
    local gcp_deployed=0
    
    for controller in "${gcp_controllers[@]}"; do
        if check_resource_exists "deployment" "$controller" "$NAMESPACE"; then
            ((gcp_deployed++))
        fi
    done
    
    if [[ $gcp_deployed -gt 0 ]]; then
        log_result "PASS" "$gcp_deployed GCP controllers deployed"
    else
        log_result "SKIP" "No GCP controllers deployed (optional)"
    fi
}

# Test 3: Dependency Graph Visualization Validation
test_dependency_graph_visualization() {
    log_test "Testing Dependency Graph Visualization System"
    
    # Check if dependency graph visualizer is deployed
    if check_resource_exists "deployment" "dependency-graph-visualizer" "$NAMESPACE"; then
        log_result "PASS" "Dependency graph visualizer deployment exists"
    else
        log_result "FAIL" "Dependency graph visualizer deployment not found"
    fi
    
    # Check if service exists
    if check_resource_exists "service" "dependency-graph-visualizer" "$NAMESPACE"; then
        log_result "PASS" "Dependency graph visualizer service exists"
    else
        log_result "FAIL" "Dependency graph visualizer service not found"
    fi
    
    # Check if ingress exists
    if kubectl get ingress -n $NAMESPACE dependency-graph-visualizer &>/dev/null; then
        log_result "PASS" "Dependency graph visualizer ingress exists"
    else
        log_result "SKIP" "Dependency graph visualizer ingress not found (optional)"
    fi
    
    # Check if pods are running
    local pod_count=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=dependency-graph-visualizer --no-headers | wc -l)
    if [[ $pod_count -gt 0 ]]; then
        log_result "PASS" "$pod_count dependency graph pods are running"
    else
        log_result "FAIL" "No dependency graph pods are running"
    fi
    
    # Test accessibility (if not dry run)
    if [[ "$DRY_RUN" != "true" ]]; then
        local service_ip=$(kubectl get svc -n $NAMESPACE dependency-graph-visualizer -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "")
        if [[ -n "$service_ip" ]]; then
            if curl -s --connect-timeout 5 "http://$service_ip" > /dev/null 2>&1; then
                log_result "PASS" "Dependency graph service is accessible"
            else
                log_result "FAIL" "Dependency graph service is not accessible"
            fi
        else
            log_result "SKIP" "Cannot test service accessibility (no cluster IP)"
        fi
    fi
}

# Test 4: Centralized Observability Validation
test_centralized_observability() {
    log_test "Testing Centralized Observability Stack"
    
    # Check if Prometheus is deployed
    if check_resource_exists "deployment" "prometheus-k8s" "$NAMESPACE"; then
        log_result "PASS" "Prometheus deployment exists"
    else
        log_result "FAIL" "Prometheus deployment not found"
    fi
    
    # Check if Grafana is deployed
    if check_resource_exists "deployment" "grafana" "$NAMESPACE"; then
        log_result "PASS" "Grafana deployment exists"
    else
        log_result "FAIL" "Grafana deployment not found"
    fi
    
    # Check if Loki is deployed
    if check_resource_exists "deployment" "loki" "$NAMESPACE"; then
        log_result "PASS" "Loki deployment exists"
    else
        log_result "FAIL" "Loki deployment not found"
    fi
    
    # Check if Promtail is deployed
    if check_resource_exists "daemonset" "promtail" "$NAMESPACE"; then
        log_result "PASS" "Promtail daemonset exists"
    else
        log_result "FAIL" "Promtail daemonset not found"
    fi
    
    # Check if Jaeger is deployed
    if check_resource_exists "deployment" "jaeger" "$NAMESPACE"; then
        log_result "PASS" "Jaeger deployment exists"
    else
        log_result "SKIP" "Jaeger deployment not found (optional)"
    fi
    
    # Check if correlation ID injector is deployed
    if check_resource_exists "deployment" "correlation-id-injector" "$NAMESPACE"; then
        log_result "PASS" "Correlation ID injector deployment exists"
    else
        log_result "FAIL" "Correlation ID injector deployment not found"
    fi
    
    # Check if ServiceMonitors exist
    local sm_count=$(kubectl get servicemonitor -n $NAMESPACE --no-headers 2>/dev/null | wc -l)
    if [[ $sm_count -gt 0 ]]; then
        log_result "PASS" "Found $sm_count ServiceMonitors"
    else
        log_result "FAIL" "No ServiceMonitors found"
    fi
}

# Test 5: Dependency Status Dashboard Validation
test_dependency_status_dashboard() {
    log_test "Testing Dependency Status Dashboard"
    
    # Check if dashboard deployment exists
    if check_resource_exists "deployment" "dependency-status-dashboard" "$NAMESPACE"; then
        log_result "PASS" "Dependency status dashboard deployment exists"
    else
        log_result "FAIL" "Dependency status dashboard deployment not found"
    fi
    
    # Check if dashboard service exists
    if check_resource_exists "service" "dependency-status-dashboard" "$NAMESPACE"; then
        log_result "PASS" "Dependency status dashboard service exists"
    else
        log_result "FAIL" "Dependency status dashboard service not found"
    fi
    
    # Check if dashboard ingress exists
    if kubectl get ingress -n $NAMESPACE dependency-status-dashboard &>/dev/null; then
        log_result "PASS" "Dependency status dashboard ingress exists"
    else
        log_result "SKIP" "Dependency status dashboard ingress not found (optional)"
    fi
    
    # Test API endpoints (if not dry run)
    if [[ "$DRY_RUN" != "true" ]]; then
        local service_ip=$(kubectl get svc -n $NAMESPACE dependency-status-dashboard -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "")
        if [[ -n "$service_ip" ]]; then
            if curl -s --connect-timeout 5 "http://$service_ip/api/health" > /dev/null 2>&1; then
                log_result "PASS" "Dashboard API is accessible"
            else
                log_result "FAIL" "Dashboard API is not accessible"
            fi
        else
            log_result "SKIP" "Cannot test API accessibility (no cluster IP)"
        fi
    fi
}

# Test 6: Automated Debugging Scripts Validation
test_automated_debugging_scripts() {
    log_test "Testing Automated Debugging Scripts"
    
    # Check if debug script exists and is executable
    if [[ -f "./core/automation/scripts/debug-dependency-chain.sh" && -x "./core/automation/scripts/debug-dependency-chain.sh" ]]; then
        log_result "PASS" "Debug dependency chain script exists and is executable"
    else
        log_result "FAIL" "Debug dependency chain script not found or not executable"
    fi
    
    # Check if validation script exists and is executable
    if [[ -f "./core/automation/scripts/validate-dependencies.sh" && -x "./core/automation/scripts/validate-dependencies.sh" ]]; then
        log_result "PASS" "Validation script exists and is executable"
    else
        log_result "FAIL" "Validation script not found or not executable"
    fi
    
    # Check if controller config generator exists and is executable
    if [[ -f "./core/automation/scripts/generate-controller-config.sh" && -x "./core/automation/scripts/generate-controller-config.sh" ]]; then
        log_result "PASS" "Controller config generator script exists and is executable"
    else
        log_result "FAIL" "Controller config generator script not found or not executable"
    fi
    
    # Check if multi-hub setup script exists and is executable
    if [[ -f "./core/automation/scripts/setup-multi-hub.sh" && -x "./core/automation/scripts/setup-multi-hub.sh" ]]; then
        log_result "PASS" "Multi-hub setup script exists and is executable"
    else
        log_result "FAIL" "Multi-hub setup script not found or not executable"
    fi
    
    # Test debug script functionality (dry run)
    if [[ "$DRY_RUN" != "true" ]]; then
        if ./core/automation/scripts/debug-dependency-chain.sh --help > /dev/null 2>&1; then
            log_result "PASS" "Debug script help functionality works"
        else
            log_result "FAIL" "Debug script help functionality failed"
        fi
    fi
}

# Test 7: Flux dependsOn Integration Validation
test_flux_depends_on_integration() {
    log_test "Testing Flux dependsOn Integration"
    
    # Check if kustomizations exist
    local kustomizations=$(kubectl get kustomizations -n $NAMESPACE --no-headers 2>/dev/null | wc -l)
    if [[ $kustomizations -gt 0 ]]; then
        log_result "PASS" "Found $kustomizations kustomizations"
    else
        log_result "FAIL" "No kustomizations found"
    fi
    
    # Check if any kustomizations have dependencies
    local with_deps=$(kubectl get kustomizations -n $NAMESPACE -o json 2>/dev/null | jq -r '.items[] | select(.spec.dependsOn) | .metadata.name' | wc -l)
    if [[ $with_deps -gt 0 ]]; then
        log_result "PASS" "Found $with_deps kustomizations with dependencies"
    else
        log_result "SKIP" "No kustomizations with dependencies found"
    fi
    
    # Check dependency chain integrity
    local invalid_deps=0
    kubectl get kustomizations -n $NAMESPACE -o json 2>/dev/null | jq -r '.items[] | 
        select(.spec.dependsOn) | 
        "\(.metadata.name):\(.spec.dependsOn[]?.name // empty)"' 2>/dev/null | while IFS=: read -r name dep; do
        if [[ -n "$dep" ]]; then
            if ! kubectl get kustomization -n $NAMESPACE "$dep" &>/dev/null; then
                ((invalid_deps++))
                log_warning "Invalid dependency: $name depends on $dep (not found)"
            fi
        fi
    done
    
    if [[ $invalid_deps -eq 0 ]]; then
        log_result "PASS" "All dependencies are valid"
    else
        log_result "FAIL" "Found $invalid_deps invalid dependencies"
    fi
}

# Generate validation report
generate_validation_report() {
    log_info "Generating validation report..."
    
    local report_file="gitops-validation-report-$(date +%Y%m%d_%H%M%S).json"
    
    local report
    report=$(jq -n \
        --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --arg namespace "$NAMESPACE" \
        --arg tests_passed "$TESTS_PASSED" \
        --arg tests_failed "$TESTS_FAILED" \
        --arg tests_total "$TESTS_TOTAL" \
        --arg dry_run "$DRY_RUN" \
        '{
            timestamp: $timestamp,
            namespace: $namespace,
            summary: {
                tests_passed: ($tests_passed | tonumber),
                tests_failed: ($tests_failed | tonumber),
                tests_total: ($tests_total | tonumber),
                success_rate: ((($tests_passed | tonumber) / ($tests_total | tonumber)) * 100 | floor)
            },
            dry_run: ($dry_run == "true"),
            validation_results: {
                multi_hub_architecture: null,
                unified_controller_installer: null,
                dependency_graph_visualization: null,
                centralized_observability: null,
                dependency_status_dashboard: null,
                automated_debugging_scripts: null,
                flux_depends_on_integration: null
            }
        }')
    
    echo "$report" > "$report_file"
    log_success "Validation report saved to: $report_file"
    
    # Display summary
    echo ""
    echo -e "${CYAN}Validation Summary:${NC}"
    echo "=================="
    echo "Total Tests: $TESTS_TOTAL"
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
    
    local success_rate=$(( (TESTS_PASSED * 100) / TESTS_TOTAL ))
    echo "Success Rate: $success_rate%"
    
    if [[ $success_rate -ge 80 ]]; then
        echo -e "Overall Status: ${GREEN}EXCELLENT${NC}"
    elif [[ $success_rate -ge 60 ]]; then
        echo -e "Overall Status: ${YELLOW}GOOD${NC}"
    else
        echo -e "Overall Status: ${RED}NEEDS IMPROVEMENT${NC}"
    fi
}

# Main execution
main() {
    echo -e "${CYAN}================================================================${NC}"
    echo -e "${CYAN} GitOps Infrastructure Mitigation Strategies Validation${NC}"
    echo -e "${CYAN}================================================================${NC}"
    echo "Namespace: $NAMESPACE"
    echo "Dry Run: $DRY_RUN"
    echo "Timeout: ${TEST_TIMEOUT}s"
    echo "Timestamp: $(date)"
    echo ""
    
    # Run all tests
    test_multi_hub_architecture
    test_unified_controller_installer
    test_dependency_graph_visualization
    test_centralized_observability
    test_dependency_status_dashboard
    test_automated_debugging_scripts
    test_flux_depends_on_integration
    
    # Generate report
    generate_validation_report
    
    # Exit with appropriate code
    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_success "All validation tests passed!"
        exit 0
    else
        log_error "$TESTS_FAILED validation tests failed"
        exit 1
    fi
}

# Help function
show_help() {
    echo "GitOps Infrastructure Mitigation Strategies Validation Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Environment Variables:"
    echo "  NAMESPACE         Kubernetes namespace (default: flux-system)"
    echo "  TEST_TIMEOUT      Test timeout in seconds (default: 300)"
    echo "  VERBOSE           Enable verbose logging (true/false, default: false)"
    echo "  DRY_RUN          Run tests without actual connectivity checks (true/false, default: false)"
    echo ""
    echo "Examples:"
    echo "  $0                           # Run all validation tests"
    echo "  $0 NAMESPACE=gitops VERBOSE=true"
    echo "  $0 DRY_RUN=true TEST_TIMEOUT=600"
    echo ""
}

# Parse command line arguments
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    show_help
    exit 0
fi

# Run main function
main "$@"

#!/bin/bash

# AI Infrastructure Testing Script
# Comprehensive testing for agentic AI components

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="${SCRIPT_DIR}/tests"
LOG_FILE="${TEST_DIR}/test-run-$(date +%Y%m%d-%H%M%S).log"
REPO_DIR="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

# Test configuration
NAMESPACE="ai-infrastructure"
TIMEOUT="300"
RETRIES="3"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$LOG_FILE"
}

# Setup test environment
setup_test_environment() {
    log "Setting up test environment..."
    
    # Create test directory
    mkdir -p "$TEST_DIR"
    
    # Check prerequisites
    check_prerequisites
    
    # Setup test namespace if needed
    if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        log_warning "Namespace $NAMESPACE does not exist. Creating for testing..."
        kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    fi
    
    log_success "Test environment setup complete"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check kubectl
    if ! command -v kubectl >/dev/null; then
        missing_tools+=("kubectl")
    fi
    
    # Check helm
    if ! command -v helm >/dev/null; then
        missing_tools+=("helm")
    fi
    
    # Check docker
    if ! command -v docker >/dev/null; then
        missing_tools+=("docker")
    fi
    
    # Check jq
    if ! command -v jq >/dev/null; then
        missing_tools+=("jq")
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi
    
    log_success "All prerequisites satisfied"
}

# Test namespace and RBAC
test_namespace_and_rbac() {
    log_info "Testing namespace and RBAC configuration..."
    
    # Test namespace exists
    if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        log_error "Namespace $NAMESPACE does not exist"
        return 1
    fi
    log_success "Namespace $NAMESPACE exists"
    
    # Test service account
    if ! kubectl get serviceaccount ai-agent-service-account -n "$NAMESPACE" >/dev/null 2>&1; then
        log_error "Service account ai-agent-service-account not found"
        return 1
    fi
    log_success "Service account exists"
    
    # Test cluster role
    if ! kubectl get clusterrole ai-agent-cluster-role >/dev/null 2>&1; then
        log_error "Cluster role ai-agent-cluster-role not found"
        return 1
    fi
    log_success "Cluster role exists"
    
    # Test cluster role binding
    if ! kubectl get clusterrolebinding ai-agent-cluster-role-binding >/dev/null 2>&1; then
        log_error "Cluster role binding ai-agent-cluster-role-binding not found"
        return 1
    fi
    log_success "Cluster role binding exists"
    
    return 0
}

# Test MCP Gateway deployment
test_mcp_gateway() {
    log_info "Testing MCP Gateway deployment..."
    
    local deployment="mcp-gateway"
    local timeout=0
    
    # Wait for deployment to be ready
    while [[ $timeout -lt $TIMEOUT ]]; do
        if kubectl get deployment "$deployment" -n "$NAMESPACE" >/dev/null 2>&1; then
            local ready=$(kubectl get deployment "$deployment" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
            local desired=$(kubectl get deployment "$deployment" -n "$NAMESPACE" -o jsonpath='{.status.replicas}')
            
            if [[ "$ready" == "$desired" && "$ready" -gt 0 ]]; then
                log_success "MCP Gateway deployment ready ($ready/$desired replicas)"
                
                # Test service
                if kubectl get service "$deployment" -n "$NAMESPACE" >/dev/null 2>&1; then
                    log_success "MCP Gateway service exists"
                    
                    # Test health endpoint
                    local service_ip=$(kubectl get service "$deployment" -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
                    if curl -f -s "http://$service_ip/api/v1/health" >/dev/null 2>&1; then
                        log_success "MCP Gateway health check passed"
                        return 0
                    else
                        log_warning "MCP Gateway health check failed, will retry..."
                    fi
                else
                    log_error "MCP Gateway service not found"
                    return 1
                fi
            fi
        fi
        
        sleep 10
        timeout=$((timeout + 10))
    done
    
    log_error "MCP Gateway deployment failed to become ready within $TIMEOUT seconds"
    return 1
}

# Test skill validation
test_skill_validation() {
    log_info "Testing skill validation..."
    
    local skills_dir="$REPO_DIR/core/ai/skills"
    local invalid_skills=()
    
    # Check if skills directory exists
    if [[ ! -d "$skills_dir" ]]; then
        log_error "Skills directory not found: $skills_dir"
        return 1
    fi
    
    # Validate each skill
    for skill_dir in "$skills_dir"/*/; do
        if [[ -d "$skill_dir" ]]; then
            local skill_name=$(basename "$skill_dir")
            local skill_file="$skill_dir/SKILL.md"
            
            if [[ ! -f "$skill_file" ]]; then
                invalid_skills+=("$skill_name: SKILL.md not found")
                continue
            fi
            
            # Validate SKILL.md format
            if ! grep -q "^name: " "$skill_file"; then
                invalid_skills+=("$skill_name: missing name field")
            fi
            
            if ! grep -q "^description: " "$skill_file"; then
                invalid_skills+=("$skill_name: missing description field")
            fi
            
            if ! grep -q "^metadata:" "$skill_file"; then
                invalid_skills+=("$skill_name: missing metadata")
            fi
        fi
    done
    
    if [[ ${#invalid_skills[@]} -gt 0 ]]; then
        log_error "Invalid skills found:"
        for invalid in "${invalid_skills[@]}"; do
            log_error "  - $invalid"
        done
        return 1
    fi
    
    log_success "All skills validated successfully"
    return 0
}

# Test configuration validation
test_configuration() {
    log_info "Testing configuration validation..."
    
    local config_file="$REPO_DIR/core/gitops/ai-agent-config.yaml"
    
    if [[ ! -f "$config_file" ]]; then
        log_error "Configuration file not found: $config_file"
        return 1
    fi
    
    # Validate required configuration keys
    local required_keys=(
        "MCP_GATEWAY_PORT"
        "COST_TRACKER_PORT"
        "TASK_QUEUE_REDIS_ADDR"
        "TEMPORAL_ADDR"
        "LOG_LEVEL"
    )
    
    local missing_keys=()
    
    for key in "${required_keys[@]}"; do
        if ! grep -q "^  $key:" "$config_file"; then
            missing_keys+=("$key")
        fi
    done
    
    if [[ ${#missing_keys[@]} -gt 0 ]]; then
        log_error "Missing configuration keys: ${missing_keys[*]}"
        return 1
    fi
    
    log_success "Configuration validation passed"
    return 0
}

# Test workflow templates
test_workflow_templates() {
    log_info "Testing workflow templates..."
    
    local templates_dir="$REPO_DIR/core/ai/runtime/backend/workflows"
    
    if [[ ! -d "$templates_dir" ]]; then
        log_error "Workflow templates directory not found: $templates_dir"
        return 1
    fi
    
    # Check for required templates
    local required_templates=(
        "toil-automation-v1"
        "cost-optimization-v1"
        "security-audit-v1"
    )
    
    for template in "${required_templates[@]}"; do
        if [[ ! -f "$templates_dir/templates.go" ]] || ! grep -q "$template" "$templates_dir/templates.go"; then
            log_error "Workflow template not found: $template"
            return 1
        fi
    done
    
    log_success "Workflow templates validation passed"
    return 0
}

# Performance testing
test_performance() {
    log_info "Running performance tests..."
    
    # Test API response times
    local gateway_service="mcp-gateway"
    
    if kubectl get service "$gateway_service" -n "$NAMESPACE" >/dev/null 2>&1; then
        local service_ip=$(kubectl get service "$gateway_service" -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
        
        # Test health endpoint performance
        local start_time=$(date +%s%N)
        if curl -f -s "http://$service_ip/api/v1/health" >/dev/null 2>&1; then
            local end_time=$(date +%s%N)
            local response_time=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
            
            if [[ $response_time -gt 1000 ]]; then
                log_warning "Health endpoint response time: ${response_time}ms (should be < 1000ms)"
            else
                log_success "Health endpoint response time: ${response_time}ms"
            fi
        else
            log_error "Health endpoint test failed"
            return 1
        fi
    else
        log_warning "MCP Gateway service not available for performance testing"
    fi
    
    return 0
}

# Generate test report
generate_test_report() {
    log_info "Generating test report..."
    
    local report_file="$TEST_DIR/test-report-$(date +%Y%m%d-%H%M%S).json"
    
    cat > "$report_file" << EOF
{
  "test_run": {
    "timestamp": "$(date -Iseconds)",
    "duration": "$(($(date +%s) - $(stat -c %Y "$LOG_FILE" 2>/dev/null || date +%s)))",
    "namespace": "$NAMESPACE"
  },
  "results": {
    "namespace_and_rbac": $(test_namespace_and_rbac && echo "true" || echo "false"),
    "mcp_gateway": $(test_mcp_gateway && echo "true" || echo "false"),
    "skill_validation": $(test_skill_validation && echo "true" || echo "false"),
    "configuration": $(test_configuration && echo "true" || echo "false"),
    "workflow_templates": $(test_workflow_templates && echo "true" || echo "false"),
    "performance": $(test_performance && echo "true" || echo "false")
  },
  "log_file": "$LOG_FILE"
}
EOF
    
    log_success "Test report generated: $report_file"
    
    # Print summary
    echo
    echo "=== TEST SUMMARY ==="
    echo "Report: $report_file"
    echo "Log: $LOG_FILE"
    echo
    
    # Check if all tests passed
    local passed_tests=$(jq '.results | to_entries | map(select(.value == true)) | length' "$report_file")
    local total_tests=$(jq '.results | length' "$report_file")
    
    echo "Tests passed: $passed_tests/$total_tests"
    
    if [[ $passed_tests -eq $total_tests ]]; then
        log_success "ALL TESTS PASSED! 🎉"
        return 0
    else
        log_error "SOME TESTS FAILED"
        return 1
    fi
}

# Cleanup test environment
cleanup_test_environment() {
    log_info "Cleaning up test environment..."
    
    # Remove test files older than 7 days
    find "$TEST_DIR" -name "test-run-*.log" -mtime +7 -delete 2>/dev/null || true
    find "$TEST_DIR" -name "test-report-*.json" -mtime +7 -delete 2>/dev/null || true
    
    log_success "Cleanup complete"
}

# Main execution
main() {
    log "Starting AI Infrastructure Testing Suite"
    log "Repository: $REPO_DIR"
    log "Namespace: $NAMESPACE"
    
    local start_time=$(date +%s)
    
    # Setup
    setup_test_environment
    
    # Run tests
    local test_results=()
    
    # Test infrastructure
    if test_namespace_and_rbac; then
        test_results+=("namespace_and_rbac:passed")
    else
        test_results+=("namespace_and_rbac:failed")
    fi
    
    # Test deployments
    if test_mcp_gateway; then
        test_results+=("mcp_gateway:passed")
    else
        test_results+=("mcp_gateway:failed")
    fi
    
    # Test configurations
    if test_skill_validation; then
        test_results+=("skill_validation:passed")
    else
        test_results+=("skill_validation:failed")
    fi
    
    if test_configuration; then
        test_results+=("configuration:passed")
    else
        test_results+=("configuration:failed")
    fi
    
    if test_workflow_templates; then
        test_results+=("workflow_templates:passed")
    else
        test_results+=("workflow_templates:failed")
    fi
    
    if test_performance; then
        test_results+=("performance:passed")
    else
        test_results+=("performance:failed")
    fi
    
    # Generate report
    generate_test_report
    
    # Cleanup
    cleanup_test_environment
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log "Testing completed in ${duration} seconds"
    log "Results: ${test_results[*]}"
    
    # Exit with appropriate code
    local failed_tests=$(echo "${test_results[*]}" | grep -c "failed" || true)
    if [[ $failed_tests -gt 0 ]]; then
        log_error "Testing failed with $failed_tests test failures"
        exit 1
    else
        log_success "All tests passed successfully!"
        exit 0
    fi
}

# Execute main function
main "$@"

#!/bin/bash

# Skill Validation Test Script
# Tests all deployed agentic AI skills for basic functionality

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Configuration
NAMESPACE="staging"
TOTAL_SKILLS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test skill accessibility
test_skill_access() {
    local skill_name=$1
    local deployment_name=$2
    
    log_info "Testing $skill_name..."
    
    if kubectl exec deployment/$deployment_name -n $NAMESPACE -- python -c "print('✅ $skill_name accessible')" > /dev/null 2>&1; then
        log_success "$skill_name - POD ACCESSIBLE"
        ((PASSED_TESTS++))
        
        # Test basic Python environment
        if kubectl exec deployment/$deployment_name -n $NAMESPACE -- python --version > /dev/null 2>&1; then
            local python_version=$(kubectl exec deployment/$deployment_name -n $NAMESPACE -- python --version 2>&1)
            log_info "$skill_name - Python: $python_version"
        fi
        
    else
        log_error "$skill_name - POD NOT ACCESSIBLE"
        ((FAILED_TESTS++))
    fi
    
    ((TOTAL_SKILLS++))
}

# Test skill resource allocation
test_skill_resources() {
    local skill_name=$1
    local deployment_name=$2
    
    log_info "Checking $skill_name resource allocation..."
    
    local cpu_request=$(kubectl get deployment $deployment_name -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].resources.requests.cpu}' 2>/dev/null || echo "not-set")
    local memory_request=$(kubectl get deployment $deployment_name -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].resources.requests.memory}' 2>/dev/null || echo "not-set")
    
    log_info "$skill_name - CPU Request: $cpu_request, Memory Request: $memory_request"
}

# Test skill labels
test_skill_labels() {
    local skill_name=$1
    local deployment_name=$2
    
    log_info "Checking $skill_name labels..."
    
    local component_label=$(kubectl get deployment $deployment_name -n $NAMESPACE -o jsonpath='{.metadata.labels.component}' 2>/dev/null || echo "not-set")
    local app_label=$(kubectl get deployment $deployment_name -n $NAMESPACE -o jsonpath='{.metadata.labels.app}' 2>/dev/null || echo "not-set")
    
    log_info "$skill_name - Component: $component_label, App: $app_label"
}

# Main test execution
main() {
    log_info "Starting Agentic AI Skill Validation Tests..."
    echo
    
    # Test Toil Automation Skills
    log_info "=== Testing Toil Automation Skills ==="
    
    test_skill_access "Certificate Rotation" "certificate-rotation-skill"
    test_skill_resources "Certificate Rotation" "certificate-rotation-skill"
    test_skill_labels "Certificate Rotation" "certificate-rotation-skill"
    echo
    
    test_skill_access "Dependency Updates" "dependency-updates-skill"
    test_skill_resources "Dependency Updates" "dependency-updates-skill"
    test_skill_labels "Dependency Updates" "dependency-updates-skill"
    echo
    
    test_skill_access "Resource Cleanup" "resource-cleanup-skill"
    test_skill_resources "Resource Cleanup" "resource-cleanup-skill"
    test_skill_labels "Resource Cleanup" "resource-cleanup-skill"
    echo
    
    test_skill_access "Security Patching" "security-patching-skill"
    test_skill_resources "Security Patching" "security-patching-skill"
    test_skill_labels "Security Patching" "security-patching-skill"
    echo
    
    test_skill_access "Backup Verification" "backup-verification-skill"
    test_skill_resources "Backup Verification" "backup-verification-skill"
    test_skill_labels "Backup Verification" "backup-verification-skill"
    echo
    
    test_skill_access "Log Retention" "log-retention-skill"
    test_skill_resources "Log Retention" "log-retention-skill"
    test_skill_labels "Log Retention" "log-retention-skill"
    echo
    
    test_skill_access "Performance Tuning" "performance-tuning-skill"
    test_skill_resources "Performance Tuning" "performance-tuning-skill"
    test_skill_labels "Performance Tuning" "performance-tuning-skill"
    echo
    
    # Test Code Review Automation Skills
    log_info "=== Testing Code Review Automation Skills ==="
    
    test_skill_access "PR Risk Assessment" "pr-risk-assessment-skill"
    test_skill_resources "PR Risk Assessment" "pr-risk-assessment-skill"
    test_skill_labels "PR Risk Assessment" "pr-risk-assessment-skill"
    echo
    
    test_skill_access "Automated Testing" "automated-testing-skill"
    test_skill_resources "Automated Testing" "automated-testing-skill"
    test_skill_labels "Automated Testing" "automated-testing-skill"
    echo
    
    test_skill_access "Compliance Validation" "compliance-validation-skill"
    test_skill_resources "Compliance Validation" "compliance-validation-skill"
    test_skill_labels "Compliance Validation" "compliance-validation-skill"
    echo
    
    test_skill_access "Performance Impact" "performance-impact-skill"
    test_skill_resources "Performance Impact" "performance-impact-skill"
    test_skill_labels "Performance Impact" "performance-impact-skill"
    echo
    
    test_skill_access "Security Analysis" "security-analysis-skill"
    test_skill_resources "Security Analysis" "security-analysis-skill"
    test_skill_labels "Security Analysis" "security-analysis-skill"
    echo
    
    # Test Core Services
    log_info "=== Testing Core Services ==="
    
    test_skill_access "MCP Gateway" "mcp-gateway"
    test_skill_resources "MCP Gateway" "mcp-gateway"
    test_skill_labels "MCP Gateway" "mcp-gateway"
    echo
    
    test_skill_access "Parallel Workflow Executor" "parallel-workflow-executor"
    test_skill_resources "Parallel Workflow Executor" "parallel-workflow-executor"
    test_skill_labels "Parallel Workflow Executor" "parallel-workflow-executor"
    echo
    
    test_skill_access "Cost Tracker" "cost-tracker"
    test_skill_resources "Cost Tracker" "cost-tracker"
    test_skill_labels "Cost Tracker" "cost-tracker"
    echo
    
    test_skill_access "Enhanced Pi-Mono RPC" "pi-mono-rpc-enhanced"
    test_skill_resources "Enhanced Pi-Mono RPC" "pi-mono-rpc-enhanced"
    test_skill_labels "Enhanced Pi-Mono RPC" "pi-mono-rpc-enhanced"
    echo
    
    # Summary
    log_info "=== Test Summary ==="
    echo "Total Skills Tested: $TOTAL_SKILLS"
    echo "Passed Tests: $PASSED_TESTS"
    echo "Failed Tests: $FAILED_TESTS"
    
    local success_rate=$((PASSED_TESTS * 100 / TOTAL_SKILLS))
    echo "Success Rate: $success_rate%"
    
    if [[ $FAILED_TESTS -eq 0 ]]; then
        log_success "🎉 All skill validation tests passed!"
        exit 0
    else
        log_warning "⚠️  Some tests failed. Check the logs above for details."
        exit 1
    fi
}

# Run main function
main "$@"

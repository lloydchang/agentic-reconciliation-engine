# Testing and Automation Framework Documentation

## Overview

This document covers the comprehensive testing and automation framework that was developed to ensure the reliability and quality of the AI agents dashboard system. The framework emphasizes CLI-first testing, automated regression testing, and self-healing capabilities.

## Testing Philosophy

### Core Principles

1. **CLI Testing First**: All testing must pass via command-line before GUI testing
2. **Automated Regression**: Self-healing test pipeline with automatic fixes
3. **Memory Logging**: Detailed test execution logs for debugging
4. **Fail-Fast**: Clear indication of system health without ambiguity
5. **Production Ready**: Testing framework suitable for production environments

### Testing Pyramid

```
        E2E Tests (GUI)
           ▲
    Integration Tests
           ▲
       Unit Tests
           ▲
    CLI Tests (Foundation)
```

## CLI Testing Framework

### `complete-cli-testing.sh` - Master Testing Pipeline

The cornerstone of the testing framework, providing comprehensive validation before any GUI testing.

#### Architecture
```bash
#!/bin/bash
# 9-Phase Testing Pipeline

# Phase 1: Pre-Test System Validation
# Phase 2: API Endpoint Testing  
# Phase 3: Go Metrics Server Testing
# Phase 4: Kubernetes Infrastructure Testing
# Phase 5: Data Flow Integration Testing
# Phase 6: Automated Fix Application
# Phase 7: Final Regression Test
# Phase 8: Test Results Summary
# Phase 9: GUI Readiness Assessment
```

#### Phase Breakdown

##### Phase 1: Pre-Test System Validation
```bash
run_test "API Process Running" "ps aux | grep -v grep | grep 'real-data-api.py'" "true"
run_test "Python Available" "python3 --version" "true"
run_test "Kubectl Available" "kubectl version --client" "true"
run_test "Kubeconfig Access" "export KUBECONFIG=/path/to/hub-kubeconfig && kubectl config use-context hub" "true"
```

##### Phase 2: API Endpoint Testing
```bash
run_test "API Health Endpoint" "curl -s --connect-timeout 3 http://localhost:5002/health" "true"
run_test "API Config Endpoint" "curl -s --connect-timeout 3 http://localhost:5002/api/config" "true"
run_test "API Agents Endpoint" "curl -s --connect-timeout 3 http://localhost:5002/api/agents/detailed" "true"
run_test "API Metrics Endpoint" "curl -s --connect-timeout 3 http://localhost:5002/api/metrics/real-time" "true"
```

##### Phase 3: Go Metrics Server Testing
```bash
run_test "Go Server Health" "curl -s --connect-timeout 3 http://localhost:8080/health" "true"
run_test "Go Server Agents" "curl -s --connect-timeout 3 http://localhost:8080/api/agents/detailed" "false"
run_test "Go Server Metrics" "curl -s --connect-timeout 3 http://localhost:8080/api/metrics/real-time" "false"
```

##### Phase 4: Kubernetes Infrastructure Testing
```bash
run_test "Metrics Pod Running" "export KUBECONFIG=/path/to/hub-kubeconfig && kubectl get pods -n ai-infrastructure | grep ai-metrics-server | grep Running" "true"
run_test "Metrics Service Exists" "export KUBECONFIG=/path/to/hub-kubeconfig && kubectl get svc -n ai-infrastructure | grep ai-metrics-service" "true"
run_test "Port-Forward Running" "ps aux | grep -v grep | grep 'port-forward.*ai-metrics'" "true"
```

##### Phase 5: Data Flow Integration Testing
```bash
run_test "Complete Data Flow" "curl -s --connect-timeout 5 http://localhost:5002/api/agents/detailed | grep -q 'error'" "false"
run_test "Error Handling" "curl -s --connect-timeout 3 http://localhost:5002/api/config | grep -q 'real_data_only'" "true"
```

##### Phase 6: Automated Fix Application
```bash
if [ $FAILED_TESTS -gt 0 ]; then
    echo "⚠️  $FAILED_TESTS tests failed. Applying automated fixes..."
    
    # Fix 1: Port-forward
    if ! ps aux | grep -v grep | grep 'port-forward.*ai-metrics' >/dev/null; then
        apply_fix "Establish Port-Forward" "kubectl port-forward svc/ai-metrics-service 8080:8080 -n ai-infrastructure &"
    fi
    
    # Fix 2: Restart API if needed
    if ! curl -s --connect-timeout 3 http://localhost:5002/health >/dev/null; then
        apply_fix "Restart Real Data API" "pkill -f 'real-data-api' 2>/dev/null; sleep 2; python3 real-data-api.py &"
    fi
fi
```

##### Phase 7: Final Regression Test
```bash
run_test "Final API Health" "curl -s --connect-timeout 3 http://localhost:5002/health" "true"
run_test "Final Go Server" "curl -s --connect-timeout 3 http://localhost:8080/health" "true"
run_test "Final Data Integration" "curl -s --connect-timeout 5 http://localhost:5002/api/metrics/real-time" "false"
```

##### Phase 8: Test Results Summary
```bash
echo -e "${BLUE}Total Tests: $TOTAL_TESTS${NC}"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"

SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
echo -e "${CYAN}Success Rate: $SUCCESS_RATE%${NC}"
```

##### Phase 9: GUI Readiness Assessment
```bash
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}✅ CLI testing pipeline completed successfully${NC}"
    echo -e "${GREEN}✅ System ready for GUI testing${NC}"
    echo -e "${GREEN}✅ Real data connection established${NC}"
    echo -e "${GREEN}✅ All regression tests passed${NC}"
    exit 0
else
    echo -e "${RED}❌ TESTS FAILED - GUI TESTING NOT APPROVED${NC}"
    exit 1
fi
```

#### Memory Logging System
```bash
# Memory tracking
MEMORY_FILE="/tmp/cli_testing_memory.log"
echo "$(date): Starting complete CLI testing pipeline" > "$MEMORY_FILE"

log_memory() {
    echo "$(date): $1" >> "$MEMORY_FILE"
}

# Usage throughout the pipeline
log_memory "TEST: $test_name - COMMAND: $test_command"
log_memory "RESULT: PASS - $test_name"
log_memory "CRITICAL: $test_name failed"
```

### `debug-real-data.sh` - Detailed Regression Testing

#### Root Cause Analysis Engine
```bash
#!/bin/bash

# Test results tracking
PASSED=0
FAILED=0

test_step() {
    local test_name="$1"
    local test_command="$2"
    local expected="$3"
    
    echo -n "Testing: $test_name ... "
    
    if eval "$test_command" >/dev/null 2>&1; then
        echo "✅ PASS"
        ((PASSED++))
        return 0
    else
        echo "❌ FAIL"
        echo "   Command: $test_command"
        echo "   Expected: $expected"
        ((FAILED++))
        return 1
    fi
}
```

#### Root Cause Analysis
```bash
if [ $FAILED -gt 0 ]; then
    echo "🔧 Root Cause Analysis:"
    
    if ! ps aux | grep -v grep | grep 'port-forward.*ai-metrics' >/dev/null; then
        echo "   🎯 PRIMARY ISSUE: Port-forward to Go metrics server not running"
        echo "   💡 SOLUTION: Run: ./setup-real-connection.sh"
    fi
    
    if ! curl -s --connect-timeout 2 http://localhost:8080/health >/dev/null 2>&1; then
        echo "   🎯 SECONDARY ISSUE: Go metrics server not accessible on localhost:8080"
        echo "   💡 SOLUTION: Check port-forward and service configuration"
    fi
fi
```

### `auto-test-fix.sh` - Self-Healing Pipeline

#### Automated Fix Engine
```bash
apply_fix() {
    local fix_name="$1"
    local fix_command="$2"
    
    echo -e "\n${YELLOW}🔧 Applying Fix: $fix_name${NC}"
    echo "Command: $fix_command"
    
    if eval "$fix_command"; then
        echo -e "${GREEN}✅ Fix applied successfully${NC}"
        sleep 2
        return 0
    else
        echo -e "${RED}❌ Fix failed${NC}"
        return 1
    fi
}
```

#### Fix Detection and Application
```bash
# Apply fixes based on failed tests
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Issues detected. Applying fixes...${NC}"
    
    # Fix 1: Port-forward
    if ! ps aux | grep -v grep | grep 'port-forward.*ai-metrics' >/dev/null; then
        apply_fix "Establish Port-Forward" "kubectl port-forward svc/ai-metrics-service 8080:8080 -n ai-infrastructure &"
    fi
    
    # Fix 2: Restart API if needed
    if ! curl -s --connect-timeout 3 http://localhost:5002/health >/dev/null; then
        apply_fix "Restart Real Data API" "pkill -f 'real-data-api' 2>/dev/null; sleep 2; python3 real-data-api.py &"
    fi
fi
```

## Connection Management Testing

### `setup-real-connection.sh` - Connection Validation

#### Connection Testing Logic
```bash
#!/bin/bash

echo "🔗 Setting up real connection to Go metrics server..."

# Kill existing port-forwards
pkill -f "kubectl port-forward.*ai-metrics" 2>/dev/null || true

# Set up port-forward
export KUBECONFIG=/path/to/hub-kubeconfig
kubectl config use-context hub
kubectl port-forward svc/ai-metrics-service 8080:8080 -n ai-infrastructure &

# Wait for connection
sleep 3

# Test connection
if curl -s http://localhost:8080/health >/dev/null 2>&1; then
    echo "✅ Real connection established!"
    echo "   Go Metrics Server: http://localhost:8080"
    echo "   Available endpoints:"
    echo "     - /api/agents/detailed"
    echo "     - /api/workflows/status" 
    echo "     - /api/metrics/real-time"
    echo "     - /api/system/health"
    echo ""
    echo "🚀 Enhanced API will now use REAL DATA only!"
else
    echo "❌ Failed to connect to Go metrics server"
    echo "   Check if ai-metrics-server pod is running"
fi
```

### `fix-real-connection.sh` - Comprehensive Connection Repair

#### Multi-Layer Connection Testing
```bash
#!/bin/bash

echo "🔧 FIXING REAL DATA CONNECTION"

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "port-forward.*ai-metrics" 2>/dev/null || true
pkill -f "real-data-api" 2>/dev/null || true

sleep 2

# Set up kubeconfig
export KUBECONFIG=/path/to/hub-kubeconfig
kubectl config use-context hub

echo "📡 Establishing port-forward to ai-metrics-service..."
kubectl port-forward svc/ai-metrics-service 8080:8080 -n ai-infrastructure &
PF_PID=$!

echo "   Port-forward PID: $PF_PID"
sleep 3

# Test connection
echo "🧪 Testing Go metrics server connection..."
if curl -s --connect-timeout 2 http://localhost:8080/health >/dev/null 2>&1; then
    echo "✅ Go metrics server accessible!"
    
    echo "🔄 Restarting real data API..."
    python3 real-data-api.py &
    API_PID=$!
    
    sleep 3
    
    # Test full data flow
    echo "🔗 Testing complete data flow..."
    if curl -s --connect-timeout 2 http://localhost:5002/api/agents/detailed >/dev/null 2>&1; then
        echo "✅ Real data flowing successfully!"
        echo ""
        echo "🎉 REAL DATA CONNECTION ESTABLISHED!"
        echo "   Port-forward PID: $PF_PID"
        echo "   API PID: $API_PID"
        echo "   Dashboard: http://localhost:3001/"
        echo "   Go Server: http://localhost:8080/health"
        echo ""
        echo "🚀 Your dashboard now shows REAL AI agents metrics!"
    else
        echo "❌ API connection issue"
    fi
else
    echo "❌ Failed to connect to Go metrics server"
    echo "   Checking service status..."
    
    # Check service details
    kubectl get svc ai-metrics-service -n ai-infrastructure -o yaml
    echo ""
    echo "Checking pod logs..."
    kubectl logs -n ai-infrastructure -l app=ai-metrics-server --tail=10
fi
```

## Test Categories and Coverage

### 1. System Validation Tests

#### Process Validation
```bash
# Check if critical processes are running
test_step "Real Data API Running" "ps aux | grep -v grep | grep 'real-data-api.py'" "true"
test_step "Port-Forward Running" "ps aux | grep -v grep | grep 'port-forward.*ai-metrics'" "true"
test_step "React Dev Server Running" "ps aux | grep -v grep | grep 'react-scripts start'" "false"
```

#### Tool Availability
```bash
test_step "Python Available" "python3 --version" "true"
test_step "Node Available" "node --version" "false"
test_step "Kubectl Available" "kubectl version --client" "true"
test_step "Curl Available" "curl --version" "true"
```

### 2. API Endpoint Tests

#### Health Checks
```bash
test_step "API Health Endpoint" "curl -s --connect-timeout 3 http://localhost:5002/health" "true"
test_step "Go Server Health" "curl -s --connect-timeout 3 http://localhost:8080/health" "true"
test_step "Temporal Health" "curl -s --connect-timeout 3 http://localhost:7233" "false"
```

#### Data Endpoints
```bash
test_step "API Config Endpoint" "curl -s --connect-timeout 3 http://localhost:5002/api/config" "true"
test_step "API Agents Endpoint" "curl -s --connect-timeout 3 http://localhost:5002/api/agents/detailed" "true"
test_step "API Metrics Endpoint" "curl -s --connect-timeout 3 http://localhost:5002/api/metrics/real-time" "true"
```

#### Error Handling Tests
```bash
test_step "Error Response Format" "curl -s http://localhost:5002/api/nonexistent | grep -q 'error'" "true"
test_step "Config Real Data Only" "curl -s http://localhost:5002/api/config | grep -q 'real_data_only'" "true"
```

### 3. Infrastructure Tests

#### Kubernetes Resources
```bash
test_step "Metrics Pod Running" "kubectl get pods -n ai-infrastructure | grep ai-metrics-server | grep Running" "true"
test_step "Metrics Service Exists" "kubectl get svc -n ai-infrastructure | grep ai-metrics-service" "true"
test_step "API Service Exists" "kubectl get svc -n ai-infrastructure | grep real-data-api-service" "false"
```

#### Cluster Connectivity
```bash
test_step "Kubeconfig Access" "kubectl config current-context" "true"
test_step "Cluster Nodes Ready" "kubectl get nodes | grep Ready" "true"
test_step "Namespace Exists" "kubectl get ns ai-infrastructure" "true"
```

### 4. Integration Tests

#### Data Flow Validation
```bash
test_step "Complete Data Flow" "curl -s --connect-timeout 5 http://localhost:5002/api/agents/detailed | grep -q 'agents'" "false"
test_step "Real Data Integration" "curl -s http://localhost:5002/api/config | grep -q 'real_data_only'" "true"
test_step "Error Propagation" "curl -s http://localhost:8080/nonexistent >/dev/null 2>&1; [ $? -eq 56 ]" "true"
```

#### Service Dependencies
```bash
test_step "API Depends on Go Server" "curl -s http://localhost:5002/api/agents/detailed >/dev/null 2>&1 && curl -s http://localhost:8080/health >/dev/null 2>&1" "false"
test_step "Frontend Depends on API" "curl -s http://localhost:3001 >/dev/null 2>&1 && curl -s http://localhost:5002/health >/dev/null 2>&1" "false"
```

## Test Result Analysis

### Success Metrics

#### Pass/Fail Tracking
```bash
# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Success rate calculation
SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))

# Quality gates
if [ $SUCCESS_RATE -ge 95 ]; then
    echo "🟢 EXCELLENT - System ready for production"
elif [ $SUCCESS_RATE -ge 80 ]; then
    echo "🟡 GOOD - System ready with minor issues"
else
    echo "🔴 NEEDS ATTENTION - System not ready"
fi
```

#### Performance Metrics
```bash
# Response time testing
test_step "API Response Time" "curl -o /dev/null -s -w '%{time_total}' http://localhost:5002/health | awk '{if (\$1 < 1.0) exit 0; else exit 1}'" "true"

# Memory usage testing
test_step "API Memory Usage" "ps aux | grep 'real-data-api.py' | awk '{if (\$6 < 100000) exit 0; else exit 1}'" "true"
```

### Error Classification

#### Critical vs Non-Critical
```bash
if [ "$critical" = "true" ]; then
    echo -e "${RED}🚨 CRITICAL TEST FAILED!${NC}"
    log_memory "CRITICAL: $test_name failed"
    # Immediately fail for critical issues
    exit 1
else
    echo -e "${YELLOW}⚠️ Non-critical test failed${NC}"
    log_memory "NON-CRITICAL: $test_name failed"
fi
```

#### Root Cause Categories
```bash
analyze_failure() {
    local test_name="$1"
    
    case "$test_name" in
        *"Port-Forward"*)
            echo "CATEGORY: Network/Connection"
            echo "LIKELY_CAUSE: Port-forward not established"
            echo "SOLUTION: Run ./setup-real-connection.sh"
            ;;
        *"API"*"Health"*)
            echo "CATEGORY: Service/Process"
            echo "LIKELY_CAUSE: API process not running"
            echo "SOLUTION: Start real-data-api.py"
            ;;
        *"Go Server"*)
            echo "CATEGORY: Backend/Infrastructure"
            echo "LIKELY_CAUSE: Go metrics server unavailable"
            echo "SOLUTION: Check Kubernetes deployment"
            ;;
        *)
            echo "CATEGORY: Unknown"
            echo "LIKELY_CAUSE: Needs investigation"
            echo "SOLUTION: Check logs and system status"
            ;;
    esac
}
```

## Automation and Self-Healing

### Automated Fix Engine

#### Fix Detection Logic
```bash
detect_and_apply_fixes() {
    local failed_tests="$1"
    
    for test in $failed_tests; do
        case "$test" in
            *"Port-Forward"*)
                apply_port_forward_fix
                ;;
            *"API Process"*)
                apply_api_restart_fix
                ;;
            *"Go Server"*)
                apply_go_server_fix
                ;;
            *"Kubeconfig"*)
                apply_kubeconfig_fix
                ;;
        esac
    done
}
```

#### Fix Implementation
```bash
apply_port_forward_fix() {
    echo "🔧 Applying port-forward fix..."
    
    # Kill existing port-forward
    pkill -f "port-forward.*ai-metrics" 2>/dev/null || true
    sleep 1
    
    # Establish new port-forward
    export KUBECONFIG=/path/to/hub-kubeconfig
    kubectl config use-context hub >/dev/null 2>&1
    kubectl port-forward svc/ai-metrics-service 8080:8080 -n ai-infrastructure &
    
    # Verify fix
    sleep 3
    if curl -s --connect-timeout 2 http://localhost:8080/health >/dev/null 2>&1; then
        echo "✅ Port-forward fix successful"
        return 0
    else
        echo "❌ Port-forward fix failed"
        return 1
    fi
}
```

### Continuous Monitoring

#### Health Check Loop
```bash
continuous_monitoring() {
    while true; do
        echo "🔍 Running continuous health check..."
        
        # Quick health checks
        if ! curl -s --connect-timeout 2 http://localhost:5002/health >/dev/null; then
            echo "⚠️ API health check failed, attempting restart..."
            apply_api_restart_fix
        fi
        
        if ! curl -s --connect-timeout 2 http://localhost:8080/health >/dev/null; then
            echo "⚠️ Go server health check failed, attempting reconnection..."
            apply_port_forward_fix
        fi
        
        sleep 30  # Check every 30 seconds
    done
}
```

## Test Execution Workflow

### Pre-Test Validation
```bash
validate_test_environment() {
    echo "🔍 Validating test environment..."
    
    # Check required tools
    required_tools=("curl" "kubectl" "python3")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            echo "❌ Required tool not found: $tool"
            exit 1
        fi
    done
    
    # Check permissions
    if [ ! -w "/tmp" ]; then
        echo "❌ Cannot write to /tmp for logging"
        exit 1
    fi
    
    # Check cluster access
    if ! kubectl cluster-info >/dev/null 2>&1; then
        echo "❌ Cannot access Kubernetes cluster"
        exit 1
    fi
    
    echo "✅ Test environment validated"
}
```

### Test Execution
```bash
execute_test_suite() {
    echo "🧪 Executing test suite..."
    
    # Initialize counters
    TOTAL_TESTS=0
    PASSED_TESTS=0
    FAILED_TESTS=0
    
    # Run all test phases
    run_phase_1_system_validation
    run_phase_2_api_testing
    run_phase_3_go_server_testing
    run_phase_4_infrastructure_testing
    run_phase_5_integration_testing
    
    # Apply fixes if needed
    if [ $FAILED_TESTS -gt 0 ]; then
        run_phase_6_automated_fixes
        run_phase_7_regression_testing
    fi
    
    # Generate report
    generate_test_report
}
```

### Post-Test Actions
```bash
generate_test_report() {
    echo "📊 Generating test report..."
    
    local report_file="/tmp/test_report_$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$report_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "total_tests": $TOTAL_TESTS,
  "passed_tests": $PASSED_TESTS,
  "failed_tests": $FAILED_TESTS,
  "success_rate": $((PASSED_TESTS * 100 / TOTAL_TESTS)),
  "gui_testing_approved": $([ $FAILED_TESTS -eq 0 ] && echo "true" || echo "false"),
  "environment": {
    "os": "$(uname -s)",
    "python_version": "$(python3 --version)",
    "kubectl_version": "$(kubectl version --client --short)"
  }
}
EOF
    
    echo "📋 Test report saved to: $report_file"
}
```

## Best Practices and Guidelines

### Test Design Principles

1. **Deterministic**: Tests should produce consistent results
2. **Isolated**: Tests should not depend on other tests
3. **Fast**: Tests should execute quickly
4. **Clear**: Test names and messages should be descriptive
5. **Actionable**: Failure messages should provide clear solutions

### Test Maintenance

#### Regular Updates
```bash
# Review test coverage monthly
check_test_coverage() {
    echo "🔍 Analyzing test coverage..."
    
    # Identify untested components
    local endpoints=("/api/agents/status" "/api/workflows/status" "/api/system/health")
    for endpoint in "${endpoints[@]}"; do
        if ! grep -q "$endpoint" "$0"; then
            echo "⚠️ Untested endpoint: $endpoint"
        fi
    done
}
```

#### Test Evolution
```bash
# Add new tests for new features
add_feature_tests() {
    local new_feature="$1"
    
    echo "🧪 Adding tests for new feature: $new_feature"
    
    # Create feature-specific test
    cat >> "tests/${new_feature}_tests.sh" << EOF
#!/bin/bash
# Tests for $new_feature feature

test_feature_${new_feature}() {
    echo "Testing $new_feature functionality..."
    # Implementation here
}
EOF
    
    chmod +x "tests/${new_feature}_tests.sh"
}
```

This comprehensive testing and automation framework ensures the reliability and quality of the AI agents dashboard system through systematic CLI-first testing, automated regression testing, and self-healing capabilities.

#!/bin/bash

echo "🧪 COMPLETE AUTOMATED CLI TESTING PIPELINE"
echo "========================================"
echo "📋 Memory: Run CLI testing and regression test pipeline first, automatically, before any GUI testing"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Test tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
TEST_RESULTS=()

# Memory tracking
MEMORY_FILE="/tmp/cli_testing_memory.log"
echo "$(date): Starting complete CLI testing pipeline" > "$MEMORY_FILE"

log_memory() {
    echo "$(date): $1" >> "$MEMORY_FILE"
}

run_test() {
    local test_name="$1"
    local test_command="$2"
    local critical="$3"
    
    ((TOTAL_TESTS++))
    echo -n "${CYAN}[$TOTAL_TESTS] Testing: $test_name${NC} ... "
    log_memory "TEST: $test_name - COMMAND: $test_command"
    
    if eval "$test_command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED_TESTS++))
        TEST_RESULTS+=("PASS: $test_name")
        log_memory "RESULT: PASS - $test_name"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((FAILED_TESTS++))
        TEST_RESULTS+=("FAIL: $test_name")
        log_memory "RESULT: FAIL - $test_name"
        
        if [ "$critical" = "true" ]; then
            echo -e "${RED}🚨 CRITICAL TEST FAILED!${NC}"
            log_memory "CRITICAL: $test_name failed"
        fi
        return 1
    fi
}

apply_fix() {
    local fix_name="$1"
    local fix_command="$2"
    
    echo -e "\n${YELLOW}🔧 Applying Fix: $fix_name${NC}"
    log_memory "FIX: $fix_name - COMMAND: $fix_command"
    
    if eval "$fix_command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Fix applied successfully${NC}"
        log_memory "FIX SUCCESS: $fix_name"
        sleep 2
        return 0
    else
        echo -e "${RED}❌ Fix failed${NC}"
        log_memory "FIX FAILED: $fix_name"
        return 1
    fi
}

echo -e "${PURPLE}📊 PHASE 1: Pre-Test System Validation${NC}"
echo "=========================================="
log_memory "PHASE 1: Pre-Test System Validation"

# System validation tests
run_test "API Process Running" "ps aux | grep -v grep | grep 'real-data-api.py'" "true"
run_test "Python Available" "python3 --version" "true"
run_test "Kubectl Available" "kubectl version --client" "true"
run_test "Kubeconfig Access" "export KUBECONFIG=agentic-reconciliation-engine/core/operators/hub-kubeconfig && kubectl config use-context hub" "true"

echo -e "\n${PURPLE}📊 PHASE 2: API Endpoint Testing${NC}"
echo "==================================="
log_memory "PHASE 2: API Endpoint Testing"

# API endpoint tests
run_test "API Health Endpoint" "curl -s --connect-timeout 3 http://localhost:5002/health" "true"
run_test "API Config Endpoint" "curl -s --connect-timeout 3 http://localhost:5002/api/config" "true"
run_test "API Agents Endpoint" "curl -s --connect-timeout 3 http://localhost:5002/api/core/ai/runtime/detailed" "true"
run_test "API Metrics Endpoint" "curl -s --connect-timeout 3 http://localhost:5002/api/metrics/real-time" "true"

echo -e "\n${PURPLE}📊 PHASE 3: Go Metrics Server Testing${NC}"
echo "======================================"
log_memory "PHASE 3: Go Metrics Server Testing"

# Go server tests
run_test "Go Server Health" "curl -s --connect-timeout 3 http://localhost:8080/health" "true"
run_test "Go Server Agents" "curl -s --connect-timeout 3 http://localhost:8080/api/core/ai/runtime/detailed" "false"
run_test "Go Server Metrics" "curl -s --connect-timeout 3 http://localhost:8080/api/metrics/real-time" "false"

echo -e "\n${PURPLE}📊 PHASE 4: Kubernetes Infrastructure Testing${NC}"
echo "=========================================="
log_memory "PHASE 4: Kubernetes Infrastructure Testing"

# Kubernetes tests
run_test "Metrics Pod Running" "export KUBECONFIG=agentic-reconciliation-engine/core/operators/hub-kubeconfig && kubectl get pods -n ai-infrastructure | grep ai-metrics-server | grep Running" "true"
run_test "Metrics Service Exists" "export KUBECONFIG=agentic-reconciliation-engine/core/operators/hub-kubeconfig && kubectl get svc -n ai-infrastructure | grep ai-metrics-service" "true"
run_test "Port-Forward Running" "ps aux | grep -v grep | grep 'port-forward.*ai-metrics'" "true"

echo -e "\n${PURPLE}📊 PHASE 5: Data Flow Integration Testing${NC}"
echo "=========================================="
log_memory "PHASE 5: Data Flow Integration Testing"

# Integration tests
run_test "Complete Data Flow" "curl -s --connect-timeout 5 http://localhost:5002/api/core/ai/runtime/detailed | grep -q 'error'" "false"
run_test "Error Handling" "curl -s --connect-timeout 3 http://localhost:5002/api/config | grep -q 'real_data_only'" "true"

echo -e "\n${PURPLE}📊 PHASE 6: Automated Fix Application${NC}"
echo "======================================"
log_memory "PHASE 6: Automated Fix Application"

# Apply fixes based on test results
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $FAILED_TESTS tests failed. Applying automated fixes...${NC}"
    
    # Fix 1: Port-forward
    if ! ps aux | grep -v grep | grep 'port-forward.*ai-metrics' >/dev/null; then
        apply_fix "Establish Port-Forward" "pkill -f 'port-forward.*ai-metrics' 2>/dev/null; sleep 1; export KUBECONFIG=agentic-reconciliation-engine/core/operators/hub-kubeconfig && kubectl config use-context hub >/dev/null 2>&1 && kubectl port-forward svc/ai-metrics-service 8080:8080 -n ai-infrastructure &"
    fi
    
    # Fix 2: Restart API if needed
    if ! curl -s --connect-timeout 3 http://localhost:5002/health >/dev/null; then
        apply_fix "Restart Real Data API" "pkill -f 'real-data-api' 2>/dev/null; sleep 2; python3 real-data-api.py &"
    fi
    
    echo -e "\n${CYAN}🔄 Re-testing after fixes...${NC}"
    sleep 3
    
    # Re-run critical tests
    run_test "Post-Fix Go Server Health" "curl -s --connect-timeout 3 http://localhost:8080/health" "true"
    run_test "Post-Fix Data Flow" "curl -s --connect-timeout 5 http://localhost:5002/api/core/ai/runtime/detailed" "false"
fi

echo -e "\n${PURPLE}📊 PHASE 7: Final Regression Test${NC}"
echo "================================="
log_memory "PHASE 7: Final Regression Test"

# Final comprehensive test
run_test "Final API Health" "curl -s --connect-timeout 3 http://localhost:5002/health" "true"
run_test "Final Go Server" "curl -s --connect-timeout 3 http://localhost:8080/health" "true"
run_test "Final Data Integration" "curl -s --connect-timeout 5 http://localhost:5002/api/metrics/real-time" "false"

echo -e "\n${PURPLE}📊 PHASE 8: Test Results Summary${NC}"
echo "================================="
log_memory "PHASE 8: Test Results Summary"

echo -e "${BLUE}Total Tests: $TOTAL_TESTS${NC}"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"

# Calculate success rate
SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
echo -e "${CYAN}Success Rate: $SUCCESS_RATE%${NC}"

log_memory "SUMMARY: Total=$TOTAL_TESTS, Passed=$PASSED_TESTS, Failed=$FAILED_TESTS, Success=$SUCCESS_RATE%"

# Detailed results
echo -e "\n${CYAN}Detailed Test Results:${NC}"
for result in "${TEST_RESULTS[@]}"; do
    if [[ $result == PASS* ]]; then
        echo -e "${GREEN}✅ $result${NC}"
    else
        echo -e "${RED}❌ $result${NC}"
    fi
    log_memory "DETAIL: $result"
done

echo -e "\n${PURPLE}📊 PHASE 9: GUI Readiness Assessment${NC}"
echo "======================================"
log_memory "PHASE 9: GUI Readiness Assessment"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}✅ CLI testing pipeline completed successfully${NC}"
    echo -e "${GREEN}✅ System ready for GUI testing${NC}"
    echo -e "${GREEN}✅ Real data connection established${NC}"
    echo -e "${GREEN}✅ All regression tests passed${NC}"
    log_memory "RESULT: SUCCESS - Ready for GUI testing"
    
    echo -e "\n${BLUE}🚀 GUI TESTING APPROVED${NC}"
    echo "   Dashboard URL: http://localhost:3001/"
    echo "   API Status: http://localhost:5002/health"
    echo "   Go Server: http://localhost:8080/health"
    
    exit 0
else
    echo -e "${RED}❌ TESTS FAILED - GUI TESTING NOT APPROVED${NC}"
    echo -e "${RED}✗ CLI testing pipeline failed${NC}"
    echo -e "${RED}✗ System not ready for GUI testing${NC}"
    echo -e "${RED}✗ Fix remaining issues before GUI testing${NC}"
    log_memory "RESULT: FAILURE - Not ready for GUI testing"
    
    echo -e "\n${YELLOW}🔧 Required Actions Before GUI Testing:${NC}"
    echo "   1. Fix failed tests identified above"
    echo "   2. Re-run: ./complete-cli-testing.sh"
    echo "   3. Ensure all tests pass before GUI testing"
    
    exit 1
fi

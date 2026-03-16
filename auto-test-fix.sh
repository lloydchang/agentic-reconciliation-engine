#!/bin/bash

echo "🤖 AUTOMATED TESTING & FIXING PIPELINE"
echo "====================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
PASSED=0
FAILED=0

run_test() {
    local name="$1"
    local cmd="$2"
    
    echo -n "${BLUE}Testing: $name${NC} ... "
    
    if eval "$cmd" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

apply_fix() {
    local fix_name="$1"
    local fix_cmd="$2"
    
    echo -e "\n${YELLOW}🔧 Applying Fix: $fix_name${NC}"
    echo "Command: $fix_cmd"
    
    if eval "$fix_cmd"; then
        echo -e "${GREEN}✅ Fix applied successfully${NC}"
        sleep 2
        return 0
    else
        echo -e "${RED}❌ Fix failed${NC}"
        return 1
    fi
}

echo -e "${BLUE}📊 STEP 1: Initial Regression Test${NC}"
echo "=================================="

# Initial tests
run_test "API Health" "curl -s --connect-timeout 2 http://localhost:5002/health"
run_test "API Config" "curl -s --connect-timeout 2 http://localhost:5002/api/config"
run_test "Go Server Health" "curl -s --connect-timeout 2 http://localhost:8080/health"
run_test "Port-Forward Running" "ps aux | grep -v grep | grep 'port-forward.*ai-metrics'"

echo -e "\n${BLUE}📈 STEP 2: Analyze Results${NC}"
echo "==========================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED - System Working!${NC}"
    exit 0
fi

echo -e "${YELLOW}⚠️  Issues detected. Applying fixes...${NC}"

# Apply fixes based on failed tests
if ! ps aux | grep -v grep | grep 'port-forward.*ai-metrics' >/dev/null; then
    echo -e "\n${YELLOW}🔧 FIX 1: Establish Port-Forward${NC}"
    
    # Kill existing processes
    pkill -f "port-forward.*ai-metrics" 2>/dev/null || true
    sleep 1
    
    # Set up port-forward
    export KUBECONFIG=/Users/lloyd/github/antigravity/gitops-infra-control-plane/hub-kubeconfig
    kubectl config use-context hub >/dev/null 2>&1
    
    echo "Starting port-forward..."
    kubectl port-forward svc/ai-metrics-service 8080:8080 -n ai-infrastructure &
    PF_PID=$!
    
    echo "Port-forward started with PID: $PF_PID"
    sleep 3
    
    # Test the fix
    if curl -s --connect-timeout 2 http://localhost:8080/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Port-forward fix successful${NC}"
        ((PASSED++))
        ((FAILED--))
    else
        echo -e "${RED}❌ Port-forward fix failed${NC}"
    fi
fi

echo -e "\n${BLUE}📊 STEP 3: Post-Fix Regression Test${NC}"
echo "===================================="

# Re-run tests after fixes
run_test "API Health (Post-Fix)" "curl -s --connect-timeout 2 http://localhost:5002/health"
run_test "Go Server Health (Post-Fix)" "curl -s --connect-timeout 2 http://localhost:8080/health"
run_test "Real Data Flow" "curl -s --connect-timeout 2 http://localhost:5002/api/agents/detailed"

echo -e "\n${BLUE}📋 STEP 4: Final Report${NC}"
echo "====================="

echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 SUCCESS: All tests passed!${NC}"
    echo -e "${GREEN}✅ Real data connection established${NC}"
    echo -e "${GREEN}✅ Dashboard ready with real metrics${NC}"
    echo -e "${GREEN}✅ GUI testing can now proceed${NC}"
    exit 0
else
    echo -e "\n${RED}❌ FAILURE: $FAILED tests still failing${NC}"
    echo -e "${YELLOW}🔍 Manual investigation required${NC}"
    exit 1
fi

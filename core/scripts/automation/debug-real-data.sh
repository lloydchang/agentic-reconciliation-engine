#!/bin/bash

echo "🔍 COMPREHENSIVE REAL DATA DEBUGGING & REGRESSION TEST"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
PASSED=0
FAILED=0

test_step() {
    local test_name="$1"
    local test_command="$2"
    local expected="$3"
    
    echo -n "Testing: $test_name ... "
    
    if eval "$test_command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "   Command: $test_command"
        echo "   Expected: $expected"
        ((FAILED++))
        return 1
    fi
}

echo "📊 Step 1: Check API Processes"
echo "================================"

# Check if real data API is running
if ps aux | grep -v grep | grep "real-data-api.py" >/dev/null; then
    API_PID=$(ps aux | grep -v grep | grep "real-data-api.py" | awk '{print $2}')
    echo -e "${GREEN}✅ Real Data API Running (PID: $API_PID)${NC}"
else
    echo -e "${RED}❌ Real Data API Not Running${NC}"
fi

# Check if port-forward is running
if ps aux | grep -v grep | grep "port-forward.*ai-metrics" >/dev/null; then
    echo -e "${GREEN}✅ Port-Forward Running${NC}"
else
    echo -e "${RED}❌ Port-Forward Not Running${NC}"
fi

echo ""
echo "🔗 Step 2: Test API Endpoints"
echo "=============================="

test_step "API Health Endpoint" "curl -s --connect-timeout 2 http://localhost:5002/health" "API should respond"
test_step "API Config Endpoint" "curl -s --connect-timeout 2 http://localhost:5002/api/config" "API config should show real_data_only"
test_step "API Agents Endpoint" "curl -s --connect-timeout 2 http://localhost:5002/api/core/ai/runtime/detailed" "Should return 504 or real data"
test_step "API Metrics Endpoint" "curl -s --connect-timeout 2 http://localhost:5002/api/metrics/real-time" "Should return 504 or real data"

echo ""
echo "🚀 Step 3: Test Go Metrics Server"
echo "=================================="

test_step "Go Server Health" "curl -s --connect-timeout 2 http://localhost:8080/health" "Go server should respond"
test_step "Go Server Agents" "curl -s --connect-timeout 2 http://localhost:8080/api/core/ai/runtime/detailed" "Go server should have agent data"
test_step "Go Server Metrics" "curl -s --connect-timeout 2 http://localhost:8080/api/metrics/real-time" "Go server should have metrics"

echo ""
echo "☸️  Step 4: Kubernetes Infrastructure"
echo "===================================="

test_step "Kubeconfig Access" "export KUBECONFIG=/Users/lloyd/github/antigravity/gitops-infra-core/operators/hub-kubeconfig && kubectl config use-context hub" "Should access cluster"
test_step "Metrics Pod Running" "export KUBECONFIG=/Users/lloyd/github/antigravity/gitops-infra-core/operators/hub-kubeconfig && kubectl get pods -n ai-infrastructure | grep ai-metrics-server | grep Running" "Pod should be running"
test_step "Metrics Service Exists" "export KUBECONFIG=/Users/lloyd/github/antigravity/gitops-infra-core/operators/hub-kubeconfig && kubectl get svc -n ai-infrastructure | grep ai-metrics-service" "Service should exist"

echo ""
echo "🧪 Step 5: Data Flow Analysis"
echo "============================"

# Test API response when Go server is unavailable
echo "Testing API response without Go server..."
API_RESPONSE=$(curl -s --connect-timeout 2 http://localhost:5002/api/core/ai/runtime/detailed 2>/dev/null || echo "TIMEOUT")

if echo "$API_RESPONSE" | grep -q "real metrics server unavailable"; then
    echo -e "${GREEN}✅ API correctly reports Go server unavailable${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ API not responding correctly to Go server unavailability${NC}"
    echo "   Response: $API_RESPONSE"
    ((FAILED++))
fi

echo ""
echo "📋 Step 6: Regression Test Summary"
echo "================================="

echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED - System Working Correctly${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILED TESTS FAILED - Issues Detected${NC}"
    echo ""
    echo "🔧 Root Cause Analysis:"
    
    if ! ps aux | grep -v grep | grep "port-forward.*ai-metrics" >/dev/null; then
        echo "   🎯 PRIMARY ISSUE: Port-forward to Go metrics server not running"
        echo "   💡 SOLUTION: Run: ./setup-real-connection.sh"
    fi
    
    if ! curl -s --connect-timeout 2 http://localhost:8080/health >/dev/null 2>&1; then
        echo "   🎯 SECONDARY ISSUE: Go metrics server not accessible on localhost:8080"
        echo "   💡 SOLUTION: Check port-forward and service configuration"
    fi
    
    exit 1
fi

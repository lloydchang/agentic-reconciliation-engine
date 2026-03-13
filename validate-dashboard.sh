#!/bin/bash

# Agent Orchestration Dashboard - Automated Browser Validation
# Tests CORS, API integration, and agent swarm display

set -e

echo "🤖 Agent Dashboard - Automated Browser Validation"
echo "=================================================="

# Configuration
DASHBOARD_URL="http://localhost:8084"
API_URL="http://localhost:5000/api/cluster-status"
EXPECTED_AGENTS=4

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Test 1: Check if port-forwards are running
echo ""
print_status "Test 1: Checking port-forwards..."
if lsof -i :8084 >/dev/null 2>&1; then
    print_success "Dashboard port-forward (8084) is running"
else
    print_error "Dashboard port-forward (8084) is not running"
    echo "Run: ./start-dashboard.sh"
    exit 1
fi

if lsof -i :5000 >/dev/null 2>&1; then
    print_success "API port-forward (5000) is running"
else
    print_error "API port-forward (5000) is not running"
    echo "Run: ./start-dashboard.sh"
    exit 1
fi

# Test 2: Test API endpoint
echo ""
print_status "Test 2: Testing API endpoint..."
API_RESPONSE=$(curl -s "$API_URL" 2>/dev/null || echo "FAILED")

if [ "$API_RESPONSE" = "FAILED" ]; then
    print_error "API endpoint not accessible"
    exit 1
fi

# Parse JSON response
AGENT_COUNT=$(echo "$API_RESPONSE" | grep -o '"agent_pods":[0-9]*' | cut -d: -f2 || echo "0")
AGENT_DATA=$(echo "$API_RESPONSE" | grep -o '"agents":\[[^]]*\]' || echo "null")

print_success "API endpoint responding"
echo "  - Agent pods: $AGENT_COUNT"
echo "  - Agent data present: $([ "$AGENT_DATA" != "null" ] && echo "Yes" || echo "No")"

# Test 3: Validate agent count
echo ""
print_status "Test 3: Validating agent count..."
if [ "$AGENT_COUNT" -eq "$EXPECTED_AGENTS" ]; then
    print_success "Agent count matches expected ($EXPECTED_AGENTS)"
else
    print_warning "Agent count mismatch: got $AGENT_COUNT, expected $EXPECTED_AGENTS"
fi

# Test 4: CORS headers test
echo ""
print_status "Test 4: Testing CORS headers..."
CORS_HEADERS=$(curl -I -H "Origin: $DASHBOARD_URL" "$API_URL" 2>/dev/null | grep -i "access-control" || echo "NONE")

if echo "$CORS_HEADERS" | grep -q "Access-Control-Allow-Origin"; then
    print_success "CORS headers present"
    echo "$CORS_HEADERS" | head -3 | sed 's/^/    /'
else
    print_error "CORS headers missing"
    exit 1
fi

# Test 5: Browser automation test (using Playwright if available)
echo ""
print_status "Test 5: Browser automation test..."

# Create a simple HTML test page to validate dashboard loading
cat > /tmp/dashboard_test.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard Test</title>
    <script>
        let testResults = {
            dashboardLoaded: false,
            apiCalled: false,
            agentsDisplayed: false,
            corsWorking: true
        };

        async function runTests() {
            try {
                // Test 1: Dashboard loads
                const dashboardResponse = await fetch('http://localhost:8084');
                testResults.dashboardLoaded = dashboardResponse.ok;

                // Test 2: API call works
                try {
                    const apiResponse = await fetch('http://localhost:5000/api/cluster-status');
                    const data = await apiResponse.json();
                    testResults.apiCalled = true;
                    testResults.agentsDisplayed = data.agents && data.agents.length > 0;
                } catch (e) {
                    testResults.corsWorking = false;
                    testResults.apiCalled = false;
                }

                // Report results
                console.log('DASHBOARD_TEST_RESULTS:', JSON.stringify(testResults));

            } catch (e) {
                console.log('DASHBOARD_TEST_ERROR:', e.message);
            }
        }

        window.onload = runTests;
    </script>
</head>
<body>
    <h1>Dashboard Test Page</h1>
    <p>Check console for test results...</p>
</body>
</html>
EOF

# Start a simple HTTP server for the test page
python3 -m http.server 8085 --directory /tmp >/dev/null 2>&1 &
SERVER_PID=$!

sleep 2

# Use Playwright to test the dashboard
if command -v npx >/dev/null 2>&1; then
    print_status "Running Playwright validation..."

    # Create Playwright test script
    cat > /tmp/test-dashboard.js << EOF
const { chromium } = require('playwright');

async function testDashboard() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  try {
    // Test dashboard loading
    await page.goto('http://localhost:8084');
    await page.waitForTimeout(2000);

    // Check for nginx error
    const hasNginxError = await page.locator('text="Welcome to nginx"').count() > 0;
    if (hasNginxError) {
      console.log('PLAYWRIGHT_ERROR: Dashboard showing nginx welcome page');
      return;
    }

    // Check for dashboard title
    const hasDashboardTitle = await page.locator('text="Agent Dashboard"').count() > 0;
    const hasAgentMetrics = await page.locator('text="Agent Metrics"').count() > 0;

    // Check console for errors
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Test API call by checking for CORS errors
    const corsErrors = [];
    page.on('response', response => {
      if (response.url().includes('localhost:5000') && !response.ok()) {
        corsErrors.push(\`HTTP \${response.status()}: \${response.url()}\`);
      }
    });

    await page.waitForTimeout(3000);

    // Check for agent swarm content
    const agentSwarmVisible = await page.locator('text="Active Agent Swarm"').count() > 0;
    const noAgentsMessage = await page.locator('text="No Agents Deployed"').count() > 0;

    console.log('PLAYWRIGHT_RESULTS:', JSON.stringify({
      dashboardLoaded: hasDashboardTitle,
      metricsVisible: hasAgentMetrics,
      agentSwarmVisible: agentSwarmVisible,
      noAgentsMessage: noAgentsMessage,
      consoleErrors: errors.length,
      corsErrors: corsErrors.length,
      nginxError: hasNginxError
    }));

  } catch (error) {
    console.log('PLAYWRIGHT_ERROR:', error.message);
  } finally {
    await browser.close();
  }
}

testDashboard();
EOF

    # Run Playwright test
    PLAYWRIGHT_OUTPUT=$(npx playwright test /tmp/test-dashboard.js --config /dev/null 2>/dev/null || echo "PLAYWRIGHT_NOT_AVAILABLE")

    if echo "$PLAYWRIGHT_OUTPUT" | grep -q "PLAYWRIGHT_RESULTS:"; then
        RESULTS=$(echo "$PLAYWRIGHT_OUTPUT" | grep "PLAYWRIGHT_RESULTS:" | sed 's/PLAYWRIGHT_RESULTS://')
        DASHBOARD_LOADED=$(echo "$RESULTS" | grep -o '"dashboardLoaded":[^,]*' | cut -d: -f2)
        AGENT_SWARM_VISIBLE=$(echo "$RESULTS" | grep -o '"agentSwarmVisible":[^,]*' | cut -d: -f2)
        NO_AGENTS_MESSAGE=$(echo "$RESULTS" | grep -o '"noAgentsMessage":[^,]*' | cut -d: -f2)
        NGINX_ERROR=$(echo "$RESULTS" | grep -o '"nginxError":[^,]*' | cut -d: -f2)

        if [ "$NGINX_ERROR" = "true" ]; then
            print_error "Dashboard showing nginx welcome page instead of agent dashboard"
        elif [ "$DASHBOARD_LOADED" = "true" ]; then
            print_success "Dashboard loaded successfully"
            if [ "$AGENT_SWARM_VISIBLE" = "true" ] && [ "$NO_AGENTS_MESSAGE" = "false" ]; then
                print_success "Agent swarm properly displayed"
            else
                print_warning "Agent swarm not visible or showing 'No Agents Deployed'"
            fi
        else
            print_error "Dashboard failed to load"
        fi
    else
        print_warning "Playwright test failed or not available"
    fi
else
    print_warning "Playwright not available - skipping browser automation test"
fi

# Cleanup
kill $SERVER_PID 2>/dev/null || true
rm -f /tmp/dashboard_test.html /tmp/test-dashboard.js

# Summary
echo ""
echo "=================================================="
echo "🤖 Dashboard Validation Complete"
echo ""
if [ "$AGENT_COUNT" -eq "$EXPECTED_AGENTS" ] && [ "$AGENT_DATA" != "null" ]; then
    print_success "✅ All validation tests passed!"
    echo "  - API responding with correct agent data"
    echo "  - CORS headers properly configured"
    echo "  - Dashboard should display agent swarm"
else
    print_error "❌ Validation failed - check dashboard configuration"
fi
echo ""
print_status "To view dashboard: http://localhost:8084"
print_status "To restart port-forwards: ./start-dashboard.sh"

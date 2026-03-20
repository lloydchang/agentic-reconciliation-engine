#!/bin/bash
# Open SWE Load Testing Script
# Performs comprehensive load testing for all Open SWE components

set -e

# Configuration
NAMESPACE=${NAMESPACE:-"open-swe-staging"}
DURATION=${DURATION:-"300"}  # 5 minutes
CONCURRENT_USERS=${CONCURRENT_USERS:-"100"}
RAMP_UP_TIME=${RAMP_UP_TIME:-"60"}  # 1 minute
RESULTS_DIR="./load-test-results/$(date +%Y%m%d_%H%M%S)"

# Create results directory
mkdir -p "$RESULTS_DIR"

echo "🚀 Starting Open SWE Load Testing"
echo "Namespace: $NAMESPACE"
echo "Duration: ${DURATION}s"
echo "Concurrent Users: $CONCURRENT_USERS"
echo "Results Directory: $RESULTS_DIR"

# Function to wait for deployment readiness
wait_for_deployment() {
    local deployment=$1
    local namespace=$2
    echo "Waiting for $deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/"$deployment" -n "$namespace"
}

# Function to run load test on a service
run_load_test() {
    local service_name=$1
    local endpoint=$2
    local test_name=$3

    echo "Running load test for $service_name..."

    # Get service URL
    local service_url
    service_url=$(kubectl get svc "$service_name" -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}:{.spec.ports[0].port}')

    if [ -z "$service_url" ]; then
        echo "❌ Failed to get service URL for $service_name"
        return 1
    fi

    # Create JMeter test plan
    cat > "$RESULTS_DIR/${test_name}.jmx" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.5">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Open SWE Load Test" enabled="true">
      <stringProp name="TestPlan.comments"></stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.tearDown_on_shutdown">true</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
      <stringProp name="TestPlan.user_define_classpath"></stringProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Load Test Thread Group" enabled="true">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlGui" testclass="LoopController" testname="Loop Controller" enabled="true">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <stringProp name="LoopController.loops">-1</stringProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">$CONCURRENT_USERS</stringProp>
        <stringProp name="ThreadGroup.ramp_time">$RAMP_UP_TIME</stringProp>
        <longProp name="ThreadGroup.start_time">1</longProp>
        <longProp name="ThreadGroup.end_time">1</longProp>
        <boolProp name="ThreadGroup.scheduler">true</boolProp>
        <stringProp name="ThreadGroup.duration">$DURATION</stringProp>
        <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="HTTP Request" enabled="true">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
            <collectionProp name="Arguments.arguments"/>
          </elementProp>
          <stringProp name="HTTPSampler.domain">$service_url</stringProp>
          <stringProp name="HTTPSampler.port">80</stringProp>
          <stringProp name="HTTPSampler.protocol">http</stringProp>
          <stringProp name="HTTPSampler.contentEncoding"></stringProp>
          <stringProp name="HTTPSampler.path">$endpoint</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
          <boolProp name="HTTPSampler.DO_MULTIPART_POST">false</boolProp>
          <stringProp name="HTTPSampler.embedded_url_re"></stringProp>
          <stringProp name="HTTPSampler.connect_timeout"></stringProp>
          <stringProp name="HTTPSampler.response_timeout"></stringProp>
        </HTTPSamplerProxy>
        <hashTree/>
        <ResultCollector guiclass="ViewResultsFullVisualizer" testclass="ResultCollector" testname="View Results Tree" enabled="true">
          <boolProp name="ResultCollector.error_logging">false</boolProp>
          <objProp>
            <name>saveConfig</name>
            <value class="SampleSaveConfiguration">
              <time>true</time>
              <latency>true</latency>
              <timestamp>true</timestamp>
              <success>true</success>
              <label>true</label>
              <code>true</code>
              <message>true</message>
              <threadName>true</threadName>
              <dataType>true</dataType>
              <encoding>false</encoding>
              <assertions>true</assertions>
              <subresults>true</subresults>
              <responseData>false</responseData>
              <samplerData>false</samplerData>
              <xml>false</xml>
              <fieldNames>true</fieldNames>
              <responseHeaders>false</responseHeaders>
              <requestHeaders>false</requestHeaders>
              <responseDataOnError>false</responseDataOnError>
              <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
              <assertionsResultsToSave>0</assertionsResultsToSave>
              <bytes>true</bytes>
              <sentBytes>true</sentBytes>
              <url>true</url>
              <threadCounts>true</threadCounts>
              <idleTime>true</idleTime>
              <connectTime>true</connectTime>
            </value>
          </objProp>
          <stringProp name="filename">$RESULTS_DIR/${test_name}-results.jtl</stringProp>
        </ResultCollector>
        <hashTree/>
        <ResultCollector guiclass="SummaryReport" testclass="ResultCollector" testname="Summary Report" enabled="true">
          <boolProp name="ResultCollector.error_logging">false</boolProp>
          <objProp>
            <name>saveConfig</name>
            <value class="SampleSaveConfiguration">
              <time>true</time>
              <latency>true</latency>
              <timestamp>true</timestamp>
              <success>true</success>
              <label>true</label>
              <code>true</code>
              <message>true</message>
              <threadName>true</threadName>
              <dataType>true</dataType>
              <encoding>false</encoding>
              <assertions>true</assertions>
              <subresults>true</subresults>
              <responseData>false</responseData>
              <samplerData>false</samplerData>
              <xml>false</xml>
              <fieldNames>true</fieldNames>
              <responseHeaders>false</responseHeaders>
              <requestHeaders>false</requestHeaders>
              <responseDataOnError>false</responseDataOnError>
              <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
              <assertionsResultsToSave>0</assertionsResultsToSave>
              <bytes>true</bytes>
              <sentBytes>true</sentBytes>
              <url>true</url>
              <threadCounts>true</threadCounts>
              <idleTime>true</idleTime>
              <connectTime>true</connectTime>
            </value>
          </objProp>
          <stringProp name="filename">$RESULTS_DIR/${test_name}-summary.csv</stringProp>
        </ResultCollector>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
EOF

    # Run JMeter test
    docker run --rm -v "$PWD:/test" -v "$RESULTS_DIR:/results" \
        justb4/jmeter:latest \
        -n -t "/test/$RESULTS_DIR/${test_name}.jmx" \
        -l "/results/${test_name}-results.jtl" \
        -j "/results/${test_name}.log"

    echo "✅ Load test completed for $service_name"
}

# Function to run AI-specific load tests
run_ai_load_test() {
    local service_name=$1
    local test_name=$2

    echo "Running AI-specific load test for $service_name..."

    # Create AI workload simulation
    cat > "$RESULTS_DIR/${test_name}-ai-test.py" << 'EOF'
import requests
import time
import concurrent.futures
import statistics
from datetime import datetime

def simulate_ai_request(service_url, endpoint, payload=None):
    """Simulate an AI service request"""
    start_time = time.time()
    try:
        if payload:
            response = requests.post(f"http://{service_url}{endpoint}", json=payload, timeout=30)
        else:
            response = requests.get(f"http://{service_url}{endpoint}", timeout=30)

        end_time = time.time()
        return {
            'success': response.status_code == 200,
            'response_time': end_time - start_time,
            'status_code': response.status_code,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        end_time = time.time()
        return {
            'success': False,
            'response_time': end_time - start_time,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def run_ai_load_test(service_url, test_name, num_requests=1000, concurrent_workers=10):
    """Run AI-specific load test"""
    print(f"Starting AI load test for {test_name}...")

    # Different AI workloads
    workloads = [
        ('/health', None, 0.4),  # Health checks (40%)
        ('/reasoning/analyze', {'task': 'test task', 'options': ['opt1', 'opt2']}, 0.3),  # Reasoning (30%)
        ('/workflow/execute', {'definition_id': 'test-workflow', 'input': {}}, 0.2),  # Workflow (20%)
        ('/analytics/metrics', None, 0.1),  # Analytics (10%)
    ]

    results = []

    def worker():
        nonlocal results
        worker_results = []

        for _ in range(num_requests // concurrent_workers):
            workload = random.choices(workloads, weights=[w[2] for w in workloads])[0]
            endpoint, payload, _ = workload

            result = simulate_ai_request(service_url, endpoint, payload)
            worker_results.append(result)

        results.extend(worker_results)

    # Run concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
        futures = [executor.submit(worker) for _ in range(concurrent_workers)]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    # Analyze results
    successful_requests = [r for r in results if r['success']]
    failed_requests = [r for r in results if not r['success']]

    response_times = [r['response_time'] for r in results]

    analysis = {
        'total_requests': len(results),
        'successful_requests': len(successful_requests),
        'failed_requests': len(failed_requests),
        'success_rate': len(successful_requests) / len(results) * 100,
        'avg_response_time': statistics.mean(response_times),
        'median_response_time': statistics.median(response_times),
        '95p_response_time': statistics.quantiles(response_times, n=20)[18],  # 95th percentile
        'min_response_time': min(response_times),
        'max_response_time': max(response_times),
        'requests_per_second': len(results) / sum(response_times)
    }

    return results, analysis

if __name__ == "__main__":
    import sys
    import random

    if len(sys.argv) != 3:
        print("Usage: python ai-load-test.py <service_url> <test_name>")
        sys.exit(1)

    service_url = sys.argv[1]
    test_name = sys.argv[2]

    results, analysis = run_ai_load_test(service_url, test_name)

    # Save results
    with open(f'{test_name}-results.json', 'w') as f:
        json.dump({'results': results, 'analysis': analysis}, f, indent=2)

    print("AI Load Test Results:")
    print(f"Total Requests: {analysis['total_requests']}")
    print(f"Success Rate: {analysis['success_rate']:.2f}%")
    print(f"Avg Response Time: {analysis['avg_response_time']:.3f}s")
    print(f"95th Percentile: {analysis['95p_response_time']:.3f}s")
    print(f"Requests/Second: {analysis['requests_per_second']:.2f}")
EOF

    # Get service URL
    local service_url
    service_url=$(kubectl get svc "$service_name" -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}:{.spec.ports[0].port}')

    if [ -z "$service_url" ]; then
        echo "❌ Failed to get service URL for $service_name"
        return 1
    fi

    # Run AI load test
    cd "$RESULTS_DIR"
    python3 "${test_name}-ai-test.py" "$service_url" "$test_name"

    echo "✅ AI load test completed for $service_name"
}

# Main execution
echo "Waiting for all deployments to be ready..."
wait_for_deployment "open-swe-gateway" "$NAMESPACE"
wait_for_deployment "open-swe-sandbox-operator" "$NAMESPACE"
wait_for_deployment "open-swe-reasoning-engine" "$NAMESPACE"
wait_for_deployment "open-swe-orchestrator" "$NAMESPACE"
wait_for_deployment "open-swe-workflow-engine" "$NAMESPACE"
wait_for_deployment "open-swe-analytics-engine" "$NAMESPACE"

echo "Running standard load tests..."
run_load_test "open-swe-gateway" "/health" "gateway-health"
run_load_test "open-swe-sandbox-operator" "/healthz" "sandbox-operator-health"
run_load_test "open-swe-analytics-engine" "/health" "analytics-health"

echo "Running AI-specific load tests..."
run_ai_load_test "open-swe-reasoning-engine" "reasoning-engine"
run_ai_load_test "open-swe-orchestrator" "orchestrator"
run_ai_load_test "open-swe-workflow-engine" "workflow-engine"

echo "Generating performance report..."
cat > "$RESULTS_DIR/performance-report.md" << EOF
# Open SWE Load Testing Report
Generated: $(date)

## Test Configuration
- Namespace: $NAMESPACE
- Duration: ${DURATION}s
- Concurrent Users: $CONCURRENT_USERS
- Ramp Up Time: ${RAMP_UP_TIME}s

## Summary

### Gateway Service
- Health endpoint load test completed
- Results: $RESULTS_DIR/gateway-health-summary.csv

### Sandbox Operator
- Health endpoint load test completed
- Results: $RESULTS_DIR/sandbox-operator-health-summary.csv

### Analytics Engine
- Health endpoint load test completed
- Results: $RESULTS_DIR/analytics-health-summary.csv

### AI Services Load Tests
- Reasoning Engine: $RESULTS_DIR/reasoning-engine-results.json
- Orchestrator: $RESULTS_DIR/orchestrator-results.json
- Workflow Engine: $RESULTS_DIR/workflow-engine-results.json

## Recommendations

Based on the test results, review the following:
1. Check response times for AI services - ensure they meet SLA requirements
2. Monitor resource usage during peak load
3. Review error rates and failure patterns
4. Consider horizontal scaling for high-throughput services
5. Optimize caching strategies for repeated requests

## Next Steps

1. Analyze detailed JMeter results for bottlenecks
2. Review AI service performance metrics
3. Implement performance optimizations
4. Run additional stress tests if needed
5. Update resource limits based on findings
EOF

echo "📊 Load testing completed! Results available in: $RESULTS_DIR"
echo "📈 Performance report: $RESULTS_DIR/performance-report.md"

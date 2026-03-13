---
name: chaos-load-testing
description: >
  Use this skill to run chaos engineering experiments and load tests to
  validate platform resilience, measure breaking points, and verify auto-
  healing behaviour. Triggers: any request to run a chaos experiment, inject
  a fault, load test an endpoint or system, measure platform performance under
  stress, validate autoscaler response, simulate a zone failure, test circuit
  breakers, or produce a resilience test report.
tools:
  - bash
  - computer
---

# Chaos & Load Testing Skill

Proactively test platform resilience using chaos engineering (Chaos Mesh,
LitmusChaos) and load testing (k6, Locust) to find weaknesses before they
cause production incidents.

---

## Chaos Engineering Framework

### Principles
1. Define steady state (baseline metrics)
2. Hypothesize: "If X fails, Y should happen"
3. Run experiment in non-prod first, then prod
4. Observe blast radius — automated abort if SLOs breach
5. Learn and fix gaps

### Tools

| Tool         | Scope                    | Config format  |
|--------------|--------------------------|----------------|
| Chaos Mesh   | Kubernetes-native faults  | CRD YAML       |
| LitmusChaos  | K8s + cloud faults        | ChaosEngine    |
| Azure Chaos  | Azure resource faults     | ARM / CLI      |
| k6           | HTTP load testing         | JS scripts     |
| Locust       | Python-based load         | Python         |

---

## Chaos Mesh Installation

```bash
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm upgrade --install chaos-mesh chaos-mesh/chaos-mesh \
  --namespace chaos-testing --create-namespace \
  --set chaosDaemon.runtime=containerd \
  --set chaosDaemon.socketPath=/run/containerd/containerd.sock
```

---

## Experiment Library

### 1. Pod Kill (single pod failure)
```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: pod-kill-${APP}
  namespace: chaos-testing
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - ${TENANT_NAMESPACE}
    labelSelectors:
      app: ${APP}
  scheduler:
    cron: "@every 10m"
```

### 2. Network Latency Injection
```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: network-delay-${APP}
  namespace: chaos-testing
spec:
  action: delay
  mode: all
  selector:
    namespaces: [${TENANT_NAMESPACE}]
    labelSelectors:
      app: ${APP}
  delay:
    latency: "200ms"
    correlation: "25"
    jitter: "50ms"
  direction: to
  target:
    selector:
      namespaces: [${TENANT_NAMESPACE}]
      labelSelectors:
        app: database-proxy
    mode: all
  duration: "5m"
```

### 3. CPU / Memory Stress
```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: cpu-stress-${APP}
  namespace: chaos-testing
spec:
  mode: all
  selector:
    namespaces: [${TENANT_NAMESPACE}]
    labelSelectors:
      app: ${APP}
  stressors:
    cpu:
      workers: 4
      load: 80
    memory:
      workers: 2
      size: "512MB"
  duration: "10m"
```

### 4. Zone Failure (Azure Chaos)
```bash
# Stop all VMs in a specific AZ using Azure Chaos Studio
az rest --method PUT \
  --url "https://management.azure.com/subscriptions/${SUB}/resourceGroups/${RG}/providers/Microsoft.Chaos/experiments/zone-failure/start?api-version=2023-04-15-preview" \
  --body "{
    \"targets\": [{
      \"type\": \"ChaosTarget\",
      \"id\": \"${AKS_ID}\",
      \"roles\": [\"Reader\"]
    }],
    \"steps\": [{
      \"name\": \"Zone1 failure\",
      \"branches\": [{
        \"name\": \"zone-1\",
        \"actions\": [{
          \"type\": \"continuous\",
          \"name\": \"urn:csci:microsoft:virtualMachineScaleSet:shutdown/1.0\",
          \"parameters\": [{\"key\":\"abruptShutdown\",\"value\":\"true\"}],
          \"duration\": \"PT10M\"
        }]
      }]
    }]
  }"
```

### 5. Database Connection Exhaustion
```bash
# Simulate connection pool exhaustion
for i in $(seq 1 200); do
  psql -h "$DB_HOST" -U "$DB_USER" \
    -c "SELECT pg_sleep(300);" &
done
# Monitor: alert should fire at 80% connection threshold
```

---

## Automated Abort Guard

```bash
run_chaos_with_guard() {
  local experiment=$1
  local slo_check_interval=30  # seconds
  local max_duration=600        # 10 min max

  # Baseline: snapshot current error rate
  BASELINE_ERROR_RATE=$(query_prometheus \
    "sum(rate(http_requests_total{status=~'5..'}[5m])) / sum(rate(http_requests_total[5m]))")

  # Start experiment
  kubectl apply -f "chaos/${experiment}.yaml" -n chaos-testing
  EXPERIMENT_START=$(date +%s)

  # Guard loop
  while true; do
    sleep $slo_check_interval

    CURRENT_ERROR_RATE=$(query_prometheus \
      "sum(rate(http_requests_total{status=~'5..'}[2m])) / sum(rate(http_requests_total[2m]))")

    # Abort if error rate > 5× baseline or > 10% absolute
    RATIO=$(echo "$CURRENT_ERROR_RATE / $BASELINE_ERROR_RATE" | bc -l)
    if (( $(echo "$RATIO > 5" | bc -l) || $(echo "$CURRENT_ERROR_RATE > 0.10" | bc -l) )); then
      echo "ABORT: Error rate ${CURRENT_ERROR_RATE} exceeds threshold"
      kubectl delete -f "chaos/${experiment}.yaml" -n chaos-testing
      create_incident "chaos-abort" "Experiment $experiment aborted due to SLO breach"
      return 1
    fi

    # Auto-complete after max duration
    ELAPSED=$(( $(date +%s) - EXPERIMENT_START ))
    [[ $ELAPSED -ge $max_duration ]] && break
  done

  kubectl delete -f "chaos/${experiment}.yaml" -n chaos-testing
  echo "Experiment complete: $experiment"
}
```

---

## Load Testing with k6

### Basic Ramp-Up Load Test
```javascript
// k6/load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

export const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 10 },    // warm up
    { duration: '5m', target: 100 },   // ramp to normal load
    { duration: '5m', target: 100 },   // hold
    { duration: '2m', target: 500 },   // stress
    { duration: '2m', target: 1000 },  // spike
    { duration: '2m', target: 0 },     // cool down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1500'],
    errors: ['rate<0.01'],
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL;

export default function () {
  const res = http.get(`${BASE_URL}/api/health`);
  check(res, {
    'status 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  errorRate.add(res.status !== 200);
  sleep(1);
}
```

```bash
# Run load test
k6 run \
  --env BASE_URL="https://${TENANT_ID}.app.example.com" \
  --out influxdb=http://localhost:8086/k6 \
  k6/load-test.js
```

---

## Resilience Test Plan (Quarterly)

| Experiment                      | Hypothesis                                | Pass criterion             |
|---------------------------------|-------------------------------------------|----------------------------|
| Kill 1 pod (HPA workload)       | New pod starts within 60s                 | 0 user-visible errors      |
| Kill all pods in 1 replica set  | Service recovers within 2 min             | Error rate returns to baseline |
| Network latency 500ms to DB     | Timeouts trigger retries, no data loss    | P99 < 2s, 0 errors         |
| Zone failure (AZ1 down)         | Traffic shifts to AZ2/3 within 2 min      | < 30s service disruption   |
| CPU stress 80% for 10 min       | Autoscaler triggers, latency bounded      | Latency < 2× baseline      |
| DB connection exhaustion        | Alert fires, pool rejects gracefully      | Alert in < 5 min           |
| Inject DNS failure              | Service degrades gracefully, cached DNS   | Error rate < 5%            |

---

## Resilience Report

```
Chaos & Load Testing Report — Q[N] [Year]
──────────────────────────────────────────

Experiments Run: 14
  Passed: 12 ✅
  Failed (SLO breached): 2 ❌
    - Zone failure: recovery took 4.2 min (target < 2 min) → ticket: T-1092
    - DB exhaustion: alert fired at 7.3 min (target < 5 min) → ticket: T-1098

Load Test Highlights (peak: 1,000 req/s)
  P95 latency:   312ms  ✅  (target < 500ms)
  P99 latency:   847ms  ✅  (target < 1500ms)
  Error rate:    0.4%   ✅  (target < 1%)
  Autoscaler:    Triggered at 68% CPU, scaled to 12 nodes in 3.2 min ✅

Blast Radius Control: 14/14 experiments stayed within tenant boundaries ✅
Abort triggered:      1 time (CPU stress experiment in prod — auto-aborted)
```

---

## Examples

- "Run the pod-kill chaos experiment on the payments-api in staging"
- "Load test the tenant-42 environment to find the breaking point"
- "Simulate a zone failure on AZ1 in East US and measure recovery time"
- "Has the circuit breaker for the inventory service been tested recently?"
- "Generate the Q2 chaos and resilience test report"

---

## Output Format

```json
{
  "experiment_id": "string",
  "type": "pod-kill|network-latency|cpu-stress|zone-failure|load-test",
  "target": "string",
  "hypothesis": "string",
  "status": "passed|failed|aborted",
  "abort_reason": null,
  "slo_breached": false,
  "metrics": {
    "error_rate_pct": 0.0,
    "p99_latency_ms": 0,
    "recovery_time_seconds": 0
  },
  "rto_achieved_seconds": 0
}
```

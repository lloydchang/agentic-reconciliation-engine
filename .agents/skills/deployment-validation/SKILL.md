---
name: deployment-validation
description: >
  Use this skill to validate deployments before and after they go live, and
  to execute automated rollbacks when issues are detected. Triggers: any
  request to validate a deployment, run smoke tests, check rollout health,
  perform a canary or blue-green promotion decision, trigger or assess a
  rollback, or review deployment reliability metrics.
tools:
  - bash
  - computer
---

# Deployment Validation & Rollback Skill

Automate the full deployment quality gate lifecycle: pre-flight checks →
progressive rollout → real-time validation → automated rollback when
failure signals are detected.

---

## Deployment Strategy Support

| Strategy      | Description                              | Rollback method         |
|---------------|------------------------------------------|-------------------------|
| Rolling       | Gradual pod replacement in-place         | `kubectl rollout undo`  |
| Blue/Green    | Full swap at load balancer level         | Switch traffic back      |
| Canary        | % traffic shift with metric gates        | Reduce weight to 0%     |
| Recreate      | Kill all → deploy new (dev only)         | Re-deploy previous tag  |

---

## Pre-Deployment Checks (Gate 0)

Run before any deployment is initiated:

```bash
# 1. Image exists and is scanned clean
trivy image $IMAGE_REF --exit-code 1 --severity CRITICAL

# 2. IaC / manifest validation
kubeval k8s/${ENV}/*.yaml
conftest test k8s/${ENV}/ -p policy/

# 3. Required secrets exist
kubectl get secret ${APP_SECRET} -n $NAMESPACE

# 4. Resource quota headroom
kubectl describe quota -n $NAMESPACE

# 5. Dependency services healthy
for SVC in $DEPENDENCIES; do
  curl -sf "https://${SVC}/health" || exit 1
done

# 6. Change freeze / maintenance window check
[[ "$CHANGE_FREEZE" == "true" ]] && echo "BLOCKED: change freeze active" && exit 1
```

All gates must pass before deployment proceeds.

---

## Deployment Execution

### Kubernetes Rolling Deploy
```bash
kubectl set image deployment/$APP $CONTAINER=$IMAGE_REF -n $NAMESPACE
kubectl rollout status deployment/$APP -n $NAMESPACE --timeout=10m
```

### Canary (Argo Rollouts)
```bash
kubectl argo rollouts set image $APP $CONTAINER=$IMAGE_REF
kubectl argo rollouts status $APP --watch --timeout 15m
```
The canary progresses automatically if analysis passes at each step.

### Blue/Green (via Ingress weight)
```bash
# Shift 10% to green
kubectl patch ingress $APP -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary-weight":"10"}}}'
# After validation, shift 100%
kubectl patch ingress $APP -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary-weight":"100"}}}'
```

---

## Post-Deployment Validation Gates

### Gate 1 — Smoke Tests (0–2 min post-deploy)
```bash
# Run the smoke test suite
pytest tests/smoke/ -v --timeout=60 \
  --base-url="https://${TENANT_ID}.app.example.com"
```
Must pass within 2 minutes or trigger rollback.

### Gate 2 — Health Check Polling (2–5 min)
```bash
for i in {1..30}; do
  STATUS=$(curl -sf "https://${APP_URL}/health" | jq -r '.status')
  [[ "$STATUS" == "healthy" ]] && break
  sleep 10
done
[[ "$STATUS" != "healthy" ]] && trigger_rollback "health_check_failed"
```

### Gate 3 — Golden Signals (5–15 min)
Query Prometheus for the four golden signals vs baseline:

```promql
# Error rate (must be < 1%)
sum(rate(http_requests_total{status=~"5..",app="$APP"}[5m])) /
sum(rate(http_requests_total{app="$APP"}[5m])) < 0.01

# Latency p99 (must be < 1.5× baseline)
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{app="$APP"}[5m]))
  < ($BASELINE_P99 * 1.5)

# Saturation (CPU must be < 80%)
rate(container_cpu_usage_seconds_total{container="$APP"}[5m]) < 0.8
```

Fail any gate → auto-rollback.

### Gate 4 — Business Metric Validation (15–30 min)
Custom checks per application (define in `validation/${APP}.yaml`):
- API success rate above threshold
- Queue depth not growing
- Database connection pool healthy
- Downstream error rates unchanged

---

## Automated Rollback

### Trigger Conditions
| Signal                              | Auto-rollback |
|-------------------------------------|---------------|
| Smoke tests fail                    | ✅ Immediate  |
| Health check fails for 5 min        | ✅ Immediate  |
| Error rate > 2× baseline for 5 min  | ✅ Immediate  |
| Latency p99 > 3× baseline for 5 min | ✅ Immediate  |
| Manual trigger                      | ✅ Immediate  |
| Slow degradation (soft signal)      | ⚠️ Alert only |

### Rollback Execution
```bash
trigger_rollback() {
  local reason=$1
  echo "ROLLBACK triggered: $reason"

  # Kubernetes rolling rollback
  kubectl rollout undo deployment/$APP -n $NAMESPACE
  kubectl rollout status deployment/$APP -n $NAMESPACE --timeout=5m

  # Canary — abort and reset
  kubectl argo rollouts abort $APP
  kubectl argo rollouts undo $APP

  # Post-rollback validation
  sleep 30
  curl -sf "https://${APP_URL}/health" || echo "WARNING: still unhealthy post-rollback"

  # Notify
  post_slack_alert "🔴 Rollback executed for $APP — reason: $reason"
  create_incident "Automatic rollback: $APP" "$reason" "P2"
}
```

---

## Deployment History & Audit

Maintain a deployment ledger:
```json
{
  "deployment_id": "DEPLOY-20250601-042",
  "app": "payments-api",
  "image": "registry/payments-api:v2.3.1",
  "environment": "prod",
  "strategy": "canary",
  "started_at": "ISO8601",
  "completed_at": "ISO8601",
  "status": "success|rolled_back|failed",
  "rollback_reason": null,
  "gates_passed": ["smoke", "health", "golden_signals"],
  "gates_failed": [],
  "deployer": "cicd-pipeline"
}
```

---

## Examples

- "Validate the current deployment of payments-api in prod"
- "The canary for order-service is at 20% — check metrics and decide whether to promote"
- "Roll back the last deployment to tenant-42's AKS cluster"
- "Show me all rollbacks in the last 30 days and their root causes"
- "Run pre-deployment checks for the new identity-service image"

---

## Output Format

```json
{
  "service": "string",
  "deployment_id": "string",
  "go_nogo": "GO|NO-GO",
  "gate_results": {},
  "status": "success|rolled_back|gates_failed",
  "gates": {
    "smoke": "pass|fail|skip",
    "health": "pass|fail|skip",
    "golden_signals": "pass|fail|skip",
    "business_metrics": "pass|fail|skip"
  },
  "rollback_triggered": false,
  "rollback_reason": null,
  "duration_seconds": 0
}
```

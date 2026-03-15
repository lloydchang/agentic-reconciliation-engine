---
name: autoscaler-advisor
description: |
  Evaluate horizontal/vertical autoscaler settings, spot misconfigurations, and recommend safe adjustments with AI risk scoring so every scaling decision keeps headroom, latency, and cost in balance.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Autoscaler Advisor — World-class Scaling Intelligence Playbook

Keeps workloads responsive with AI-backed autoscaler validation, recommendation, and remediation while emitting dispatcher-ready signals for confidence and gating.

## When to invoke
- After autoscaler configuration changes (HPA, VPA, KEDA, Cluster Autoscaler).
- When pods experience oscillation, throttling, or saturation events.
- Ahead of planned launches/spikes to validate headroom and safety limits.
- Dispatcher/memory agents flag `capacity-risk`, `cost-spike`, or `panic-scaling` events needing tuning.

## Capabilities
- **Autoscaler validation** checks min/max targets, metrics, custom metrics, and respects policy guardrails.
- **AI tuning recommendations** propose new thresholds, concurrency, or target metrics with risk/confidence.
- **Scale event forecasting** predicts when current settings will hit limits and suggests pre-emptive adjustments.
- **Automation hooks** can adjust `kubectl scale`, modify HPA/VPA manifests, or surface gating events.
- **Shared context** records every observation at `shared-context://memory-store/autoscaler-advisor/{operationId}` for reuse.

## Invocation patterns
```bash
/autoscaler-advisor validate --resource=hpa-payments-api --namespace=tenant-42
/autoscaler-advisor recommend --resource=hpa-payments-api --namespace=tenant-42 --objective=latency
/autoscaler-advisor forecast --resource=cluster-autoscaler --window=72h
/autoscaler-advisor apply --resource=hpa-payments-api --namespace=tenant-42 --min=3 --max=12
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `resource` | HPA/VPA/ClusterAutoscaler resource name. | `hpa-payments-api` |
| `namespace` | Kubernetes namespace or tenant. | `tenant-42` |
| `objective` | Target metric (`latency`, `cpu`, `requests`). | `latency` |
| `window` | Forecast horizon (e.g., `72h`). | `72h` |
| `min` | Minimum replicas. | `3` |
| `max` | Maximum replicas. | `12` |

## Output contract
```json
{
  "operationId": "ASA-2026-0315-01",
  "status": "validated",
  "resource": "hpa-payments-api",
  "namespace": "tenant-42",
  "recommendation": "increase max to 12, target latency 50ms",
  "riskScore": 0.31,
  "confidence": 0.87,
  "forecast": {
    "metric": "cpu",
    "timeToLimit": "2026-03-17T04:00:00Z",
    "confidenceInterval": ["2026-03-17T03:30:00Z", "2026-03-17T04:30:00Z"]
  },
  "logs": "shared-context://memory-store/autoscaler-advisor/ASA-2026-0315-01",
  "decisionContext": "redis://memory-store/autoscaler-advisor/ASA-2026-0315-01",
  "events": [ { "name": "autoscaler-validated", "timestamp": "2026-03-15T08:12:00Z" } ]
}
```

## World-class workflow templates

### Autoscaler validation & risk scoring
1. Inspect HPA/VPA/ClusterAutoscaler settings (min/max, target metrics, cooldowns) and annotations.
2. Compare current load to policy guardrails, predicted headroom, and historic scaling events.
3. Emit `autoscaler-validated` with `riskScore` and share context.
4. Command stub: `/autoscaler-advisor validate --resource=hpa-payments-api --namespace=tenant-42`

### Scaling recommendations
1. Analyze telemetry (CPU, memory, custom metrics, request latency) plus cost/capacity signals.
2. Propose new targets, horizontal ranges, or vertical adjustments with confidence and ROI estimation.
3. Route low-risk actions to automation; require human gate when changes affect production-critical services.
4. Command stub: `/autoscaler-advisor recommend --resource=hpa-payments-api --namespace=tenant-42 --objective=latency`

### Forecasting & preemptive actions
1. Predict when current autoscaler settings will exhaust limits using ensemble forecasting models.
2. Alert dispatchers with time-to-event, affected services, and mitigations.
3. Trigger `capacity-planning` or `incident-triage` downstream if headroom drops below thresholds.
4. Command stub: `/autoscaler-advisor forecast --resource=cluster-autoscaler --window=72h`

### Automated tuning & rollback safety
1. Apply recommended settings via `kubectl apply` or manifest patches.
2. Monitor the change with rollback safeguards (pre/post checks, human gate if necessary).
3. Emit `autoscaler-tuned` or `autoscaler-rollback` events for observability.
4. Command stub: `/autoscaler-advisor apply --resource=hpa-payments-api --namespace=tenant-42 --min=3 --max=12`

## AI intelligence highlights
- **AI risk scoring** blends change impact, service criticality, and historic scaling success to label recommendations with confidence.
- **Intelligent forecasting** uses ensembles to predict threshold exhaustion and propose preemptive moves.
- **Automated tuning** weighs cost vs latency to choose the safest action, with human gates when needed.

## Memory agent & dispatcher integration
- Persist decisions under `shared-context://memory-store/autoscaler-advisor/{operationId}`.
- Emit events: `autoscaler-validated`, `autoscaler-recommendation`, `autoscaler-forecast`, `autoscaler-tuned`, `autoscaler-rollback`.
- Subscribe to `capacity-alert`, `policy-risk`, `incident-ready`, and `deployment-risk` events to adapt guidance.
- Tag telemetry with `decisionId`, `resource`, `namespace`, `riskScore`, `confidence`, and `viewerUrl`.

## Observability & telemetry
- Metrics: validation success rate, recommendation acceptance %, forecast error, tuning latency.
- Logs: structured `log.event="autoscaler.advisor"` with `resource`, `namespace`, `riskScore`.
- Dashboards: expose `/autoscaler-advisor metrics --format=prometheus` for SRE/cost views.
- Alerts: repeated tuning failures, forecast error >10%, manual gates held >15m.

## Failure handling & retries
- Retry API calls when fetching metrics/configs up to 3× with exponential backoff.
- On tuning failures, emit `autoscaler-rollback`, notify `incident-triage-runbook`, and store artifacts for audit.
- Keep shared context until downstream skills acknowledge; never delete before telemetry ack.

## Human gates
- Required when:
  1. RiskScore ≥ 0.85 and the target is production-critical.
  2. Proposed changes adjust autoscalers for >20 tenants/services at once.
  3. Dispatcher requests manual approval after automation loops.
- Template matches orchestrator standard (`⚠️ HUMAN GATE: …`).

## Testing & validation
- Dry-run: `/autoscaler-advisor recommend --resource=hpa-test --namespace=staging --objective=latency --dry-run`
- Unit tests: `backend/autoscaler/` ensures scoring/forecasting align with regression data.
- Integration: `scripts/validate-autoscaler-advisor.sh` applies recommendations in emulator clusters.
- Regression: nightly `scripts/nightly-autoscaler-smoke.sh` verifies telemetry, recommendations, and gates.

## References
- Scripts: `scripts/autoscaler-advisor/`.
- Dashboards: `monitoring/autorun/autoscaler/`.
- Templates: `templates/autoscaler/`.

## Related skills
- `/capacity-planning`: aligns headroom forecasts with upcoming demand.
- `/incident-triage-runbook`: invoked if tuning fails or autoscaler alarms fire.
- `/workflow-management`: schedules batch tuning workflows across namespaces.

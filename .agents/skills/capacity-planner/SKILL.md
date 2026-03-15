---
name: capacity-planner
description: |
  Forecast capacity needs, simulate headroom scenarios, and validate scalability playbooks with AI modeling so platform teams can proactively provision or rebalance resources.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Capacity Planner — World-class Growth Modeling Playbook

Analyzes telemetry, forecast signals, and event plans to produce scenario-based capacity guidance, autoscaler recommendations, and dispatcher-grade alerts.

## When to invoke
- Preparing for launches, spikes, or marketing campaigns that stress capacity.
- After capacity incidents to review headroom, autoscaler settings, or quota limits.
- When cost/capacity automation requests new buffering or throttling policies.
- Dispatcher/memory agents emit `capacity-alert`, `autoscaler-risk`, or `cost-spike` events.

## Capabilities
- **Scenario modeling** uses historical peak/forecast data plus business events (campaigns, releases) for headroom projections.
- **Capacity validation** checks deployments, nodes, quotas, and autoscalers to ensure coverage meets forecasts.
- **Autoscaler collaboration** adjusts `capacity-planning` recommendations against `autoscaler-advisor` outputs for safe scaling.
- **Alerting** publishes predictive capacity alerts when headroom risk crosses thresholds.
- **Shared context** writes forecasts to `shared-context://memory-store/capacity-planner/{operationId}` for downstream reference.

## Invocation patterns
```bash
/capacity-planner simulate --scenario=launch --resource=prod-cluster --growthRate=0.25 --months=6
/capacity-planner validate --resource=aks-nodepool --threshold=0.8
/capacity-planner alert --event=marketing-spike --riskScore=0.75
/capacity-planner recommend --action=add-nodepool --confidence=0.88
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `scenario` | Growth scenario (`launch`,`steady`,`spike`). | `launch` |
| `resource` | Cluster/nodepool/service scope. | `prod-cluster` |
| `growthRate` | Expected monthly growth (decimal). | `0.25` |
| `months` | Forecast horizon (months). | `6` |
| `threshold` | Warning threshold as ratio. | `0.8` |
| `action` | Recommended mitigation. | `add-nodepool` |

## Output contract
```json
{
  "operationId": "CP-2026-0315-01",
  "scenario": "launch",
  "status": "ok|at_risk",
  "riskScore": 0.65,
  "forecast": {
    "resource": "prod-cluster",
    "nodesNeeded": 42,
    "timeToExhaust": "2026-05-12T00:00:00Z",
    "confidenceInterval": ["2026-05-10T00:00:00Z","2026-05-14T00:00:00Z"]
  },
  "recommendations": [
    { "type": "nodepool", "detail": "Add 2 x n8s standard in us-east-1", "impact": "+5% headroom" }
  ],
  "logs": "shared-context://memory-store/capacity-planner/CP-2026-0315-01",
  "decisionContext": "redis://memory-store/capacity-planner/CP-2026-0315-01"
}
```

## World-class workflow templates

### Scenario forecasting
1. Collect historical metrics, campaigns, and release timelines.
2. Build ensemble forecasts (ARIMA, Prophet, gradient boosting) per resource/service.
3. Emit `capacity-forecast` events with headroom, riskScore, and action items.
4. Command stub: `/capacity-planner simulate --scenario=launch --resource=prod-cluster --growthRate=0.25 --months=6`

### Capacity validation
1. Examine cluster capacity, quotas, autoscaler settings, and cost thresholds.
2. Identify misalignments (nodes full, autoscalers not tuned, quotas nearing limits).
3. Emit `capacity-validation` events linking to `autoscaler-advisor` and `deployment-validation`.
4. Command stub: `/capacity-planner validate --resource=aks-nodepool --threshold=0.8`

### Alerting & automation
1. When forecasts risk breaching headroom, generate predictive alerts for dispatchers.
2. Attach runbooks or automation instructions to extend capacity or throttle traffic.
3. Emit `capacity-alert` events for orchestrator or incident skills.
4. Command stub: `/capacity-planner alert --event=marketing-spike --riskScore=0.75`

### Recommendation & follow-up
1. Provide actionable plans (add nodes, enable autoscalers, re-balance workloads).
2. Attach confidence/risk metadata, request human approval for production-impact actions.
3. Emit `capacity-recommendation` and hand to `workflow-management` for execution.
4. Command stub: `/capacity-planner recommend --action=add-nodepool --confidence=0.88`

## AI intelligence highlights
- **Scenario modeling** fuses telemetry, forecasts, and events to produce precise headroom guidance.
- **Validation intelligence** ensures autoscalers, quotas, and costs keep pace with predicted demand.
- **Predictive alerts** warn before thresholds hit so ops can act ahead of incidents.

## Memory agent & dispatcher integration
- Store forecasts and alerts in `shared-context://memory-store/capacity-planner/{operationId}`.
- Emit events: `capacity-forecast`, `capacity-validation`, `capacity-alert`, `capacity-recommendation`.
- Subscribe to dispatchers (`incident-ready`, `cost-anomaly`, `deployment-risk`) to adjust scenarios.
- Tag entries with `decisionId`, `scenario`, `riskScore`, `confidence`, `resource`, and `tenant`.

## Observability & telemetry
- Metrics: forecast accuracy, validation pass rate, alert lead time, recommendation acceptance.
- Logs: structured `log.event="capacity.forecast"` with `operationId` and `confidence`.
- Dashboards: integrate `/capacity-planner metrics --format=prometheus` for SRE insights.
- Alerts: missing forecasts, >3 validation failures, recommendations held >15m.

## Failure handling & retries
- Retry telemetry retrieval up to 3× on transient API throttles.
- On forecast drift, update models, emit `capacity-forecast-revised`, and inform watchers.
- Keep forecasts for 90 days for post-mortem analysis; retain logs until downstream ack.

## Human gates
- Required when:
  1. Recommendations affect production clusters or >20 tenants.
  2. RiskScore ≥ 0.85 indicates insufficient headroom.
  3. Dispatcher requests manual review after automation throttles.

## Testing & validation
- Dry-run: `/capacity-planner simulate --scenario=steady --resource=test-cluster --months=3 --dry-run`
- Unit tests: `backend/capacity-planner/` ensures forecasting models behave consistently.
- Integration: `scripts/validate-capacity-planner.sh` runs end-to-end forecasts and alerts.
- Regression: nightly `scripts/nightly-capacity-planner-smoke.sh` monitors alerts and recommendations.

## References
- Scripts: `scripts/capacity-planner/`.
- Templates: `templates/capacity/`.
- Monitoring: `monitoring/capacity-ops/`.

## Related skills
- `/capacity-planning`: broad strategic headroom analysis.
- `/autoscaler-advisor`: detailed autoscaler tuning.
- `/workflow-management`: coordinates capacity automation playbooks.

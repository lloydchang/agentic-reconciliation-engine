---
name: capacity-planning
description: >
  Forecast capacity needs, model scenarios, validate autoscalers, and alert before exhaustion using AI-powered predictions and risk-aware guidance.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Capacity Planning — World-class Predictive Scaling Playbook

Predicts demand, models growth trajectories, validates autoscaler health, and issues predictive alerts so teams can preempt capacity exhaustion.

## When to invoke
- Quarterly/weekly forecasting cycles that set budgets and headroom targets.
- Ahead of tenant launches, marketing campaigns, or expected spikes.
- After autoscaler configuration changes or scaling incidents.
- Dispatcher/memory agent events (`capacity_risk`, `autoscaler_issue`, `resource_saturation`).

## Capabilities
- **AI Resource Forecasting**: predicts CPU, memory, storage, database, and network demand with high accuracy and confidence bands.
- **Intelligent Scenario Modeling**: evaluates conservative, target, and spike growth models, highlighting chokepoints and tipping points.
- **Smart Autoscaler Validation**: detects misconfigured HPAs/Cluster Autoscaler combos through anomaly detection on metrics/events.
- **Predictive Capacity Alerts**: warns of exhaustion before it happens and recommends provisioning, throttling, or autoscaler tuning.
- **Cross-skill propagation**: shares headroom risks with cost, deployment, and incident skills so downstream decision-making stays aligned.

## Invocation patterns

```bash
/capacity-planning forecast --horizon=90d --granularity=daily --target=aks-hub
/capacity-planning scenario --scenario=launch --growthRate=0.2 --months=6
/capacity-planning autoscaler --namespace=payments --validate=true
/capacity-planning alert --threshold=0.85 --resource=cpu
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `target` | Cluster, node pool, namespace, or tenant scope. | `aks-hub` |
| `horizon` | Forecast horizon (days). | `90d` |
| `granularity` | Resolution for predictions. | `daily` |
| `scenario` | Scenario descriptor (launch, steady, spike). | `launch` |
| `growthRate` | Monthly growth expectation. | `0.15` |
| `threshold` | Warning threshold (0–1). | `0.85` |

## Output contract

```json
{
  "snapshotDate": "2026-03-15T07:00:00Z",
  "horizonDays": 90,
  "forecast": [
    { "metric": "cpu_pct", "value": 47, "lower": 42, "upper": 52 },
    { "metric": "memory_pct", "value": 62, "lower": 58, "upper": 66 }
  ],
  "scenarios": [
    {
      "name": "launch",
      "tenantGrowth": 20,
      "nodesNeeded": 40,
      "riskScore": 0.78,
      "alert": "buffer_needed"
    }
  ],
  "autoscalerIssues": [
    {
      "name": "payments-hpa",
      "reason": "target CPU > 90% for 10 min",
      "recommendation": "lower target to 70%"
    }
  ],
  "predictiveAlerts": [
    {
      "resource": "storage",
      "threshold": 0.85,
      "expectedDate": "2026-04-15T00:00:00Z"
    }
  ],
  "decisionContext": "redis://memory-store/capacity/forecast-2026-03-15",
  "metrics": {
    "forecastAccuracy": 0.92,
    "scenarioConfidence": 0.88
  }
}
```

## World-class workflow templates

### AI resource forecasting
1. Gather telemetry from Prometheus/Cloud Monitor/DB stats and clean-slate baselines.
2. Train ensembles per metric (Prophet, ARIMA, gradient boosting) and surface confidence bands.
3. Emit predictions with headroom guidance and `capacity-forecast` events tagged by tenant/region.
4. Share context with memory agents for downstream orchestration.
5. Command stub: `/capacity-planning forecast --horizon=90d --granularity=daily --target=aks-hub`.

### Intelligent scenario modeling
1. Build base, target, and spike scenarios using tenant growth, campaign assumptions, and scaling multipliers.
2. Surface choke points (node limits, quotas, autoscaler ceilings) and recommended buffers.
3. Recommend execution steps (provision node pools, reserve RI, throttle tenants).
4. Publish `scenario-report` artifacts for stakeholders and dispatch further automations.

### Smart autoscaler validation
1. Validate HPAs against observed metrics, ranges, and custom metrics.
2. Monitor Cluster Autoscaler event stream for scale failures or stalls.
3. Flag misconfigurations (min=max, absent metrics) and provide fix-it guidance.
4. Emit `autoscaler-issue` events with remediation actions.
5. Command stub: `/capacity-planning autoscaler --namespace=payments --validate=true`.

### Predictive capacity alerts
1. Monitor forecast vs actual usage; when projected usage crosses `threshold`, fire `capacity-warning`.
2. Recommend provisioning, autoscaler tuning, or tenant throttling before exhaustion.
3. Escalate to `incident-triage-runbook` if exhaustion is predicted within 72h.
4. Command stub: `/capacity-planning alert --threshold=0.85 --resource=cpu`.

## AI intelligence highlights
- **AI Resource Forecasting** captures seasonality, campaigns, and tenancy growth with ensemble models and confidence intervals.
- **Intelligent Scenario Modeling** simulates multiple futures, surfaces tipping points, and recommends mitigation steps.
- **Smart Autoscaler Validation** detects config drift and missing metrics via anomaly detection.
- **Predictive Capacity Alerts** warn teams early with actionable next steps before thresholds trigger outages.

## Memory agent & dispatcher integration
- Store normalized forecasts and alerts under `shared-context://memory-store/capacity/{snapshotDate}` for reuse.
- Emit/consume `capacity-forecast`, `autoscaler-issue`, and `capacity-alert` events with tags (`riskScore`, `impact`, `tenant`).
- Coordinate with dispatchers so cost, deployment, and incident skills adjust plans based on headroom.
- Fall back to `artifact-store://capacity/{snapshotDate}.json` when the event bus is unavailable.

## Observability & telemetry
- Metrics: forecast accuracy, scenario confidence, autoscaler violation count, alert lead time.
- Logs: structured `log.event="capacity.forecast"` entries that include `decisionId` and `alertId`.
- Dashboards: surface `/capacity-planning metrics --format=prometheus` for headroom and alert visibility.
- Alerts: forecasting error >10%, >3 imminent alerts, or autoscaler misconfigurations >5/week.

## Failure handling & retries
- Retry Prometheus/monitoring queries up to 3 times with exponential backoff (30s → 2m).
- When telemetry is missing, use the last known snapshot, flag the gap, and notify humans.
- Persist artifacts (`reports/capacity/{snapshotDate}`) until downstream acknowledgments ensure consumption.
- Escalate to humans if forecasts are stale for >1 hour or if predictive alerts fail to publish.

## Human gates
- Required when:
  1. Predictive alert indicates exhaustion within 48h or riskScore ≥ 0.85.
  2. Autoscaler recommendations touch production workloads, quotas, or throttling policies.
  3. Scenario projections suggest >20% oversubscription requiring infrastructure changes.
- Confirmation template matches the orchestrator standard:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/capacity-planning forecast --target=test-cluster --horizon=30d --dry-run`.
- Unit tests: `backend/capacity/models` validates forecasting and scenario calculations.
- Integration: `scripts/validate-capacity-flow.sh` simulates forecasts, autoscaler checks, and dispatcher handoffs.
- Regression: nightly `scripts/nightly-capacity-smoke.sh` monitors accuracy, alarms, and dispatcher consumption.

## References
- Forecast models: `backend/capacity/forecasts`.
- Autoscaler validation: `monitoring/autoscaler`.
- Reporting: `reports/capacity/`.

## Related skills
- `/ai-agent-orchestration`: orchestrates capacity-triggered adjustments.
- `/deployment-validation`: ensures rollouts align with forecasted headroom.
- `/incident-triage-runbook`: receives alerts when exhaustion threatens availability.

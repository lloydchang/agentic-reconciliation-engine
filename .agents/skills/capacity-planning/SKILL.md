---
name: capacity-planning
description: >
  Forecast capacity needs, model scenarios, validate autoscalers, and alert before exhaustion using AI-powered analysis.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Capacity Planning — World-class Predictive Scaling Playbook

Predicts resource demand, models growth scenarios, validates autoscaler configurations, and raises predictive alerts. Use when onboarding tenants, planning launches, or guarding against capacity exhaustion.

## When to invoke
- During quarterly/weekly forecasting cycles.
- Before onboarding new products/tenants or during marketing campaigns.
- After autoscaler configuration changes.
- When dispatcher events flag `capacity_risk`, `autoscaler_issue`, or `resource_saturation`.

## Capabilities
- **AI Resource Forecasting**: resolves CPU, memory, storage, database, and network demand with high accuracy.
- **Intelligent Scenario Modeling**: evaluates conservative, target, and spike growth scenarios, flagging constraints and tipping points.
- **Smart Autoscaler Validation**: uncovers misconfigured HPAs/CA combos with anomaly detection on metrics.
- **Predictive Capacity Alerts**: early warning alerts before exhaustion occurs using ensemble predictions.
- Integrates with cost/incident skills so capacity impacts propagate across workflows.

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
| `target` | Cluster, node pool, or namespace scope. | `aks-hub` |
| `horizon` | Forecast horizon. | `90d` |
| `granularity` | Forecast resolution. | `daily` |
| `scenario` | Scenario name (launch, steady, spike). | `launch` |
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
1. Ingest telemetry from Prometheus/CloudMonitor/DB stats.
2. Train ensembles per metric (prophet, arima, gradient boosting).
3. Output predictions with confidence bounds and headroom percentages.
4. Emit `capacity-forecast` event tagged by tenant/region.

### Intelligent scenario modeling
1. Generate base, target, spike scenarios with tenant growth, campaign assumptions, and resource multipliers.
2. Highlight choke points (node limits, quotas, autoscaler ceilings).
3. Provide recommended buffer capacity and execution steps (provision new node pools, reserve RI).
4. Summarize into `scenario-report` artifact for leadership.

### Smart autoscaler validation
1. Validate HPA settings against observed metrics, range, and custom metrics.
2. Check Cluster Autoscaler event stream for scale failures.
3. Detect misconfigurations (min=max, absent metrics) and recommended fixes.
4. Create action items for platform teams to adjust scaling policies.

### Predictive capacity alerts
1. Monitor forecast vs actual; when projected usage crosses `threshold`, send `capacity-warning`.
2. Pre-emptively recommend provisioning, autoscaler tuning, or tenant throttling.
3. Escalate to `incident-triage-runbook` if exhaustion imminent within 72h.

## AI intelligence highlights
- **AI Resource Forecasting**: high-fidelity predictions with ensembles capturing seasonality, campaigns, and tenancy growth.
- **Intelligent Scenario Modeling**: simulates multiple growth scenarios, surfaces tipping points, and suggests mitigation.
- **Smart Autoscaler Validation**: flags config drift and missing custom metrics using anomaly detection.
- **Predictive Capacity Alerts**: warns teams before thresholds hit, giving time for mitigation.

## Memory agent & dispatcher integration
- Store forecasts/alerts under `shared-context://memory-store/capacity/{snapshotDate}`.
- Emit/consume `capacity-forecast`, `autoscaler-issue`, `capacity-alert` events.
- Update dispatcher tags (`riskScore`, `impact`, `tenant`) so downstream skills understand headroom risks.

## Communication protocol
- Primary: CLI for invocation; event bus for `capacity-forecast`/`alert`.
- Secondary: Email/Slack notifications via `SLACK_WEBHOOK` for predictive alerts.
- Fallback: Artifact store entries when event bus offline.

## Observability & telemetry
- Metrics: forecast accuracy, scenario confidence, autoscaler violation count, alert lead time.
- Logs: structured `log.event=capacity.forecast`, include `decisionId`, `alertId`.
- Dashboard: include `/capacity-planning metrics --format=prometheus` panels for headroom and alerts.
- Alerts: forecasting error > 10%, >3 imminent alerts, autoscaler misconfig > 5/week.

## Failure handling & retries
- Retry Prometheus/monitoring queries thrice with backoff (30s → 2m).
- Missing telemetry: use last-known snapshot and flag for manual review.
- Persist artifacts (`reports/capacity/{snapshotDate}`) until dispatcher acknowledges consumption.

## Human gates
- Required when:
 1. Predictive alert indicates exhaustion within 48h or riskScore ≥ 0.85.
 2. Autoscaler recommendations adjust production workloads or quotas.
 3. Scenario projections suggest >20% oversubscription requiring infrastructure changes.
- Use standard confirmation template.

## Testing & validation
- Dry-run: `/capacity-planning forecast --target=test-cluster --horizon=30d --dry-run`.
- Unit tests: `backend/capacity/models` ensures forecasting/regression logic.
- Integration: `scripts/validate-capacity-flow.sh` ensures alerts emit, autoscaler issues detected, and dispatcher flows.
- Regression: nightly `scripts/nightly-capacity-smoke.sh` monitors accuracy and alert thresholds.

## References
- Forecast models: `backend/capacity/forecasts`.
- Autoscaler validation: `monitoring/autoscaler`.
- Reporting: `reports/capacity/`.

## Related skills
- `/ai-agent-orchestration`: orchestrates capacity-triggered adjustments.
- `/deployment-validation`: ensures deployments align with forecasted headroom.
- `/incident-triage-runbook`: receives alerts when exhaustion threatens availability.

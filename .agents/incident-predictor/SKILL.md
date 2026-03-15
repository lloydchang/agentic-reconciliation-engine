---
name: incident-predictor
description: |
  Forecast incidents, detect precursors, and surface risk signals so operations teams can staff, remediate, or prevent outages before they spike.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Incident Predictor — World-class Resilience Forecast Playbook

Sweeps telemetry, change data, and historical incidents to compute risk, send alerts, and trigger remediations ahead of problems.

## When to invoke
- Running predictive analytics nightly/weekly to see upcoming incident clusters.
- After deployments/changes to measure risk uplift.
- Observing correlated telemetry patterns (error rate spikes, queue depth) that often precede incidents.
- Dispatcher events `incident-risk`, `trend-alert`, `anomaly-warning`.

## Capabilities
- **Predictive modeling** blends change rate, telemetry drift, queue/backlog, and incident history.
- **Risk scoring** outputs `riskScore` per service/tenant/time window.
- **Automation hooks** trigger runbooks, adjust strategies, or raise tickets before incidents occur.
- **Shared context** `shared-context://memory-store/incident-predictor/{operationId}` for visibility.

## Invocation patterns
```bash
/incident-predictor forecast --service=payments-api --window=72h
/incident-predictor eyebrow --metric=error_rate --threshold=3s
/incident-predictor trend --tenant=tenant-42 --period=30d
/incident-predictor escalate --riskScore=0.92 --action=page-oncall
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `service` | Service/component name. | `payments-api` |
| `window` | Forecast horizon. | `72h` |
| `metric` | Leading metric. | `error_rate` |
| `threshold` | Threshold for alerts. | `3s` |
| `tenant` | Tenant/cluster. | `tenant-42` |
| `action` | Automation action. | `page-oncall` |

## Output contract
```json
{
  "operationId": "IP-2026-0315-01",
  "service": "payments-api",
  "riskScore": 0.84,
  "trend": "increasing",
  "recommendation": "trigger incident runbook",
  "logs": "shared-context://memory-store/incident-predictor/IP-2026-0315-01"
}
```

## World-class workflow templates

### Forecast & detection
1. Feed telemetry, error budgets, change velocity into ensemble models.
2. Emit `incident-forecast` with riskScore and impacted tenants.
3. Command stub: `/incident-predictor forecast --service=payments-api --window=72h`

### Precursors & eyebrow raises
1. Watch golden signals for leading indicators.
2. Emit `incident-eye` events when thresholds near tolerance.
3. Command stub: `/incident-predictor eyebrow --metric=error_rate --threshold=3s`

### Trend analysis
1. Group incidents by tenant/service over windows.
2. Emit `incident-trend` and highlight recurring patterns.
3. Command stub: `/incident-predictor trend --tenant=tenant-42 --period=30d`

### Escalation & automation
1. When riskScore high, trigger automation (incident runbook, alerting adjustments).
2. Emit `incident-escalation` with context and human gate if needed.
3. Command stub: `/incident-predictor escalate --riskScore=0.92 --action=page-oncall`

## AI intelligence highlights
- **Predictive scoring** uses telemetry, queue/backlog, and historical faults for preview.
- **Adaptive thresholds** adjust sensitivity based on business impact.
- **Explainability** surfaces root causes for each forecast.

## Memory agent & dispatcher integration
- Persist forecasts under `shared-context://memory-store/incident-predictor/{operationId}`.
- Emit `incident-forecast`, `incident-eye`, `incident-trend`, `incident-escalation`.
- Listen to dispatcher events and feed back to incident workflows.

## Observability & telemetry
- Metrics: forecast accuracy, automation rate, escalations.
- Logs: `log.event="incident.predict"` with `service`, `riskScore`.
- Dashboards: `/incident-predictor metrics --format=prometheus`.

## Failure handling & retries
- Retry telemetry retrieval; fallback to last-known forecast if data missing.
- On repeated forecast failures, escalate to human gates.

## Human gates
- Required when riskScore ≥ 0.9 or automation touches exec/service control.

## Testing & validation
- Dry-run: `/incident-predictor forecast --service=test --window=24h --dry-run`

## References
- Scripts: `scripts/incident-predictor/`.
- Templates: `templates/incidents/`.
- Monitoring: `monitoring/incident-trends/`.

## Related skills
- `/incident-triage-runbook`, `/workflow-management`, `/alert-prioritizer`

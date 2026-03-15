---
name: sla-monitoring-alerting
description: >
  Monitor SLAs/SLOs, detect breaches, automate burn-rate responses, and feed predictive reliability intelligence into dispatcher workflows.
allowed-tools:
  - Bash
  - Read
  - Write
---

# SLA Monitoring & Alerting — World-class Reliability Playbook

Controls uptime, deployment success, incident response, and performance SLOs end-to-end so every reliability decision is backed by AI risk scoring and dispatcher-ready context.

## When to invoke
- Before (and during) every release to validate deployment success SLOs and alerting readiness.
- On telemetry spikes to calculate error-budget burn rate prior to a breach.
- When dispatcher/memory agents flag `incident-ready`, `capacity-risk`, or other reliability impacts.
- During quarterly reliability reviews or executive SLA reporting.

## Capabilities
- **AI SLA Risk Assessment** contextualizes uptime/performance metrics with historical behavior, change velocity, and business impact to score breach risk.
- **Error Budget Forecasting** projects burn-rate trajectories and predicts exhaustion windows with confidence intervals.
- **Smart Remediation Suggestions** recommend traffic shifts, circuit breaking, or throttles before SLA breaches occur.
- **Predictive Alerts & Automation** provide early warnings plus automation pathways (page, throttle, shift) through dispatchers.
- **Shared-context propagation** stores SLA insight under `shared-context://memory-store/sla/{tier}` for other skills.

## Invocation patterns

```bash
/sla-monitoring-alerting define --tier=enterprise --targets=payments-api,identity-service
/sla-monitoring-alerting monitor --tier=business --window=30d
/sla-monitoring-alerting burn-rate --tier=enterprise --threshold=14x --action=page-oncall
/sla-monitoring-alerting report --tier=starter --format=json --destination=reports/sla-starter.json
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `tier` | SLA/SLO tier (`starter`, `business`, `enterprise`). | `enterprise` |
| `targets` | Services or tenants tracked. | `payments-api,identity-service` |
| `window` | Lookback window for rolling calculations. | `30d` |
| `threshold` | Burn-rate multiplier before action (e.g., `14x`). | `14x` |
| `action` | Automated response (`page`, `throttle`, `escalate`). | `page-oncall` |
| `format` | Output format (json/yaml). | `json` |

## Output contract

```json
{
  "tier": "enterprise",
  "window": "30d",
  "status": "ok|at_risk|breached",
  "errorBudgetRemainingPct": 34.5,
  "burnRate": 12.1,
  "riskScore": 0.78,
  "forecast": {
    "timeToExhaust": "2026-03-19T02:00:00Z",
    "confidenceInterval": ["2026-03-19T01:30:00Z", "2026-03-19T02:30:00Z"]
  },
  "recommendations": [
    {
      "name": "traffic-shift",
      "description": "Shift 20% traffic to blue deployment",
      "action": "throttle",
      "impact": "Reduces load on payments-api"
    }
  ],
  "alert": {
    "name": "HighErrorBudgetBurnRate",
    "severity": "critical",
    "triggeredAt": "2026-03-15T07:40:00Z"
  },
  "logs": "shared-context://memory-store/sla/enterprise/2026-03-15"
}
```

## World-class workflow templates

### Real-time SLA dashboard
1. Query Prometheus/Datadog/Azure Monitor for uptime, latency, error rate, and deployment success.
2. Post metrics to Grafana dashboards and time-series stores for trend analysis.
3. Emit `sla-status` events with tier health, burn rate, and risk scoring for dispatcher consumption.
4. Command stub: `/sla-monitoring-alerting monitor --tier=enterprise --window=30d`.

### Error budget burn-rate automation
1. Calculate burn-rate multiplier (`window-error / budget`) and compare to thresholds (14× for critical, 6× for warning).
2. Fire `sla-burn-rate` events with `severity` and automation action (`page`, `throttle`, `escalate`).
3. Route dispatchers to trigger `incident-triage-runbook` or `deployment-validation` if burn-rate persists beyond 15 minutes.
4. Command stub: `/sla-monitoring-alerting burn-rate --tier=enterprise --threshold=14x --action=page-oncall`.

### Predictive breach alerts
1. Use AI forecasting (Prophet/ensemble) to predict when error budgets exhaust.
2. Publish `sla-forecast` with `timeToExhaust`, `confidenceInterval`, and `riskScore`.
3. Recommend remediation (throttle, circuit-break, deploy mitigations) or request a human gate when `riskScore ≥ 0.9`.
4. Command stub: `/sla-monitoring-alerting report --tier=enterprise --format=json --destination=reports/sla-enterprise.json`.

## AI intelligence highlights
- **AI SLA Risk Assessment** blends current metrics, change volume, and historical breach patterns to classify tier status.
- **Error Budget Forecasting** predicts exhaustion with confidence intervals, enabling proactive mitigation.
- **Smart Remediation Suggestions** propose traffic shifts, emergency throttles, or circuit breakers with business impact context.
- **Predictive Capacity Alerts** collaborate with `capacity-planning` to align forecasts with broader capacity risk.

## Memory agent & dispatcher integration
- Store insights at `shared-context://memory-store/sla/{tier}/{window}` for downstream skills (incident, deployment, cost).
- Emit/consume `sla-status`, `sla-burn-rate`, `sla-forecast`, `sla-breach`, and `sla-action` events.
- Tag context with `decisionId`, `riskScore`, `tier`, `tenant`, `recommendation`, and `timeWindow`.
- Subscribe to `agent-completed`, `incident-ready`, `deployment-risk` events so reliability posture informs automation chains.

## Observability & telemetry
- Metrics: burn-rate, risk score, forecast error, alert volume per tier.
- Logs: structured `log.event="sla.alert"` entries with `decisionId`, `correlationId`, and `bundle` for traceability.
- Dashboards: feed `/sla-monitoring-alerting metrics --format=prometheus` into Grafana for error budget tracking.
- Alerts: fire when >3 burn-rate alerts appear within 1h, forecast error exceeds 12%, or dispatcher rerouting occurs due to `sla-risk`.

## Failure handling & retries
- Retry telemetry/API queries up to 3× with exponential backoff (30s → 2m); fall back to cached metrics if sources fail.
- If burn-rate automation (traffic shift/throttle) fails, escalate to `incident-triage-runbook` and log audit context.
- Keep artifacts (alerts, forecasts) for 90 days for post-incident analysis; do not delete until retention requirements are met.
- Notify on-call channels when automation loops are blocked or human gates remain pending >15 minutes.

## Human gates
- Required when:
  1. SLA status transitions to `breached` for enterprise tier or `riskScore ≥ 0.9`.
  2. Recommended remediation impacts production systems (traffic shifts, throttles, circuit breaks).
  3. Dispatcher requests oversight after >2 burn-rate alerts.
- Confirmation template matches the orchestrator standard:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/sla-monitoring-alerting monitor --tier=enterprise --window=7d --dry-run`.
- Unit tests: `backend/sla/` ensures burn-rate, forecast, and remediation logic produce expected outputs.
- Integration: `scripts/validate-sla-pipeline.sh` passes alerts through dispatcher and human gate automation.
- Regression: nightly `scripts/nightly-sla-smoke.sh` validates thresholds, AI scoring, and `ai-agent-orchestration` triggers.

## References
- Data sources: `docs/SLI-SLO-DEFINITIONS.md`, `docs/EXECUTION-CHECKLIST.md`.
- Alerting rules: `monitoring/alert-rules/sla-burn-rate.yaml`.
- Dashboards: `monitoring/grafana/sla`.

## Related skills
- `/incident-triage-runbook`: remediates when SLA risk escalates.
- `/deployment-validation`: gates canaries/deployments when SLA status tightens.
- `/capacity-planning`: aligns capacity headroom with SLA forecasts.
- `/ai-agent-orchestration`: coordinates dispatcher responses to SLA events.

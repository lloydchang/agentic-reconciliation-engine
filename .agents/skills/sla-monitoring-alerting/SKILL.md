---
name: sla-monitoring-alerting
description: >
  Monitor SLAs/SLOs, detect breaches, alert on burn rate, and feed predictive reliability intelligence into the dispatcher.
allowed-tools:
  - Bash
  - Read
  - Write
---

# SLA Monitoring & Alerting — World-class Reliability Playbook

Controls uptime, deployment success, incident response, and performance SLOs end-to-end. Use this skill when defining error budgets, running breach detection, automating burn-rate responses, or informing dispatcher decisions (e.g., when `riskScore` spikes due to SLA risk).

## When to invoke
- At every release: validate deployment success SLOs and pre-confirm alerting.
- On telemetry spikes: calculate error-budget burn rate before a breach occurs.
- When dispatcher marks `incident-ready` or `capacity-risk`: link reliability impacts to other workflows.
- During quarterly reliability reviews or executive SLA reporting.

## Capabilities
- **AI SLA Risk Assessment**: contextualizes uptime/performance metrics with historical behavior, change velocity, and business impact to score breach risk.
- **Error Budget Forecasting**: projects burn-rate trajectories and predicts exhaustion timings with confidence intervals.
- **Smart Remediation Suggestions**: recommends actions (traffic shifting, circuit-breaking, throttling) before SLA breaches.
- **Predictive Alerts & Automation**: early warnings plus automated escalation pathways.
- Integrates with shared context and dispatcher events for multi-skill collaboration (`shared-context://memory-store/sla/{tier}`).

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
| `tier` | SLA/SLO tier (starter/business/enterprise). | `enterprise` |
| `targets` | Services/tenants under observation. | `payments-api,identity-service` |
| `window` | Lookback window for rolling calculations. | `30d` |
| `threshold` | Burn-rate multiplier before action. | `14x` |
| `action` | Automated response (`page`, `throttle`, `escalate`). | `page-oncall` |
| `format` | Output format (json|yaml). | `json` |

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
1. Query Prometheus/Datadog/Azure Monitor for uptime, error rate, latency, deployment success.
2. Publish metrics to dashboards and store in time-series for trend analysis.
3. Provide `sla-status` event with tier status and burn-rate.

### Error budget burn-rate automation
1. Calculate burn-rate multiplier (`window-error / budget`) and compare to thresholds (14× for critical, 6× for warning).
2. If threshold crossed, emit `sla-burn-rate` event with `severity` and `action` (page, throttle).
3. Auto-trigger dispatchers to run `incident-triage-runbook` or `deployment-validation` if burn-rate persists > 15 minutes.

### Predictive breach alerts
1. Use AI forecasting (Prophet/ensemble) to predict when error budget exhausts.
2. Send `sla-forecast` with `timeToExhaust`, `confidenceInterval`, `riskScore`.
3. Recommend remediation (throttle, scale, circuit break) or request human gate when riskScore ≥ 0.9.

## AI intelligence highlights
- **AI SLA Risk Assessment**: blends current metrics, change volume, and historical breach patterns to classify `status`.
- **Error Budget Forecasting**: predicts exhaustion with `confidenceInterval`, enabling proactive mitigation.
- **Smart Remediation Suggestions**: suggests actions (traffic shift, circuit break, autoscaler tweak) with justification and business impact.
- **Predictive Capacity Alerts**: collab with `capacity-planning` to correlate predicted KPI shortfalls with broader capacity risk.

## Memory agent & dispatcher integration
- Store insights under `shared-context://memory-store/sla/{tier}/{window}` for other skills (incident, deployment, cost).
- Emit/consume events: `sla-status`, `sla-burn-rate`, `sla-forecast`, `sla-breach`, `sla-action`.
- Tag memory records with `decisionId`, `riskScore`, `tier`, `tenant`, `recommendation`.

## Communication protocols
- Primary: Prometheus/Alertmanager, Azure Monitor alerts stream and CLI for manual commands.
- Secondary: NATS/Kafka event bus for `sla-*` events consumed by dispatchers.
- Fallback: Write artifacts to `artifact-store://sla/{tier}/{window}.json` and signal dispatcher pollers.

## Observability & telemetry
- Metrics: burn-rate, risk score, forecast error, alert volume per tier.
- Logs: structured `log.event="sla.alert"` with `decisionId`, `correlationId`, `bundle`.
- Dashboards: integrate `/sla-monitoring-alerting metrics --format=prometheus` into Grafana (error budget, tracking).
- Alerts: >3 burn-rate alerts in 1h, forecast error > 12%, dispatchers rerouted due to `sla-risk`.

## Failure handling & retries
- Retry telemetry/API queries up to 3× with exponential backoff (30s→2m); fallback to cached metrics.
- If burn-rate action fails (e.g., can't throttle), escalate to `incident-triage-runbook` and log for audit.
- Keep artifacts (alerts, forecasts) for 90 days to support post-incident analysis; do not delete until retention satisfied.

## Human gates
- Required when:
 1. SLA status transitions to `breached` for enterprise tier or riskScore ≥ 0.9.
 2. Recommended remediation impacts production systems (traffic shifts, throttles).
 3. Dispatcher requests escalation after >2 burn-rate alerts.
- Use standard human gate confirmation template.

## Testing & validation
- Dry-run: `/sla-monitoring-alerting monitor --tier=enterprise --window=7d --dry-run`.
- Unit tests: `backend/sla/` ensures burn-rate, forecast, and remediation logic produce expected outputs.
- Integration: `scripts/validate-sla-pipeline.sh` runs alerts through dispatcher and human gate automation.
- Regression: nightly `scripts/nightly-sla-smoke.sh` keeps thresholds aligned and verifies `ai-agent-orchestration` triggers.

## References
- Data sources: `docs/SLI-SLO-DEFINITIONS.md`, `docs/EXECUTION-CHECKLIST.md`.
- Alerting rules: `monitoring/alert-rules/sla-burn-rate.yaml`.
- Dashboards: `monitoring/grafana/sla`.

## Related skills
- `/incident-triage-runbook`: executes remediation when SLA risk escalates.
- `/deployment-validation`: gates canaries/deployments in response to SLA status.
- `/capacity-planning`: aligns capacity signals with SLA forecasts.
- `/ai-agent-orchestration`: coordinates dispatcher responses to SLA events.

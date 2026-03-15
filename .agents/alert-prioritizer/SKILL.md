---
name: alert-prioritizer
description: |
  Prioritize incoming alerts, incidents, and telemetry failures by scoring risk, blast radius, and business impact so dispatchers can focus on the most critical work with AI guidance.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Alert Prioritizer — World-class Signal Triage Playbook

Rapidly scores, correlates, and escalates alerts across clouds, Kubernetes, and applications so downstream skills act on the highest-impact signals first while logging an audit trail.

## When to invoke
- A flood of alerts (Prometheus, Sentinel, Datadog, Azure Monitor) arrives and you need AI-assisted triage.
- Security or compliance tooling surfaces suspicious activity (identity changes, secrets access, policy failures).
- Memory agents flag churn (cost anomalies, regression events, incident spikes) that need prioritized response.
- You want to gate dispatchers on normalized `riskScore` before routing incidents to responders, deployments, or communications.

## Capabilities
- **Multi-source ingestion**: normalizes Prometheus, Azure Monitor, Defender, Datadog, and Splunk alerts.
- **Intelligent scoring**: weights severity, user context, operational impact, and historical outcomes into a unified `riskScore`.
- **Correlation & deduplication**: groups related alerts into composite incidents and surfaces escalation candidates.
- **Automation hooks**: emits dispatcher events, assigns owners, or triggers runbooks when thresholds are met.
- **Transparent telemetry**: stores every decision in `shared-context://memory-store/alert-prioritizer/{operationId}` for auditing.

## Invocation patterns
```bash
/alert-prioritizer score --alert-source=prometheus --metric=error_rate --tenant=tenant-42
/alert-prioritizer correlate --group=backend-errors --window=15m
/alert-prioritizer escalate --riskScore=0.92 --response=pagerduty
/alert-prioritizer human-gate --alert=policy-violation --audience=security
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `alert-source` | Monitoring system emitting the signal. | `prometheus` |
| `metric` | Metric, log, or event name. | `error_rate` |
| `riskScore` | Normalized risk (0–1). | `0.92` |
| `tenant` | Tenant/cluster/service. | `tenant-42` |
| `response` | Automation channel (`pagerduty`, `slack`, `human`). | `pagerduty` |
| `window` | Grouping window for correlation (e.g., `15m`). | `15m` |

## Output contract
```json
{
  "operationId": "ALT-2026-0315-01",
  "status": "prioritized",
  "alerts": [
    { "name": "PaymentsErrorRate", "severity": "critical", "riskScore": 0.92, "tenant": "tenant-42" }
  ],
  "riskScore": 0.88,
  "response": "pagerduty",
  "recommendation": "Page on-call, throttle traffic",
  "logs": "shared-context://memory-store/alert-prioritizer/ALT-2026-0315-01",
  "decisionContext": "redis://memory-store/alert-prioritizer/ALT-2026-0315-01"
}
```

## World-class workflow templates

### Alert scoring & normalization
1. Ingest alerts from Prometheus/Sentinel/Defender with metadata (tenant, service, severity, tags).
2. Normalize naming, dedupe duplicates, and calculate blast radius using topology and dependency data.
3. Score every alert with AI risk (severity × impact × confidence) and record `riskScore` in shared context.
4. Command stub: `/alert-prioritizer score --alert-source=prometheus --metric=error_rate --tenant=tenant-42`

### Correlation & incident creation
1. Group alerts with the same root cause (same service, timeframe, or dependency) using heuristics or embedding similarity.
2. Create composite incidents, attach timelines, and persist them under `shared-context://memory-store/alert-prioritizer/incidents/{id}`.
3. Emit `alert-incident` events so `incident-triage-runbook` or `stakeholder-comms-drafter` can operate with that context.
4. Command stub: `/alert-prioritizer correlate --group=backend-errors --window=15m`

### Automated escalation & gating
1. For alerts with `riskScore ≥ threshold` or unusual combinations (policy breach + cost spike), trigger automations (PagerDuty, Slack, throttles) or request human approval.
2. Log the decision, include rationale, and emit `alert-escalated` or `alert-human-gate` events.
3. Update downstream AutoOps (deployment rollback, policy enforcement, communications) with the chosen path.
4. Command stub: `/alert-prioritizer escalate --riskScore=0.92 --response=pagerduty`

### Human gate refresh & review
1. When `riskScore` is high but automation is not safe (new control plane change, sensitive tenant), present the context for human review.
2. Store the gate request under `shared-context://memory-store/alert-prioritizer/human-gates/{id}`.
3. Emit `alert-human-gate` and `alert-human-clear` once a reviewer decides.
4. Command stub: `/alert-prioritizer human-gate --alert=policy-violation --audience=security`

## AI intelligence highlights
- **AI risk scoring** blends severity, topology, historical outcomes, and compliance exposure so every alert has a numerical priority.
- **Intelligent correlation** clusters alerts using semantic similarity plus dependency graphs to reduce noise.
- **Predictive escalation** reasons over cost, performance, and security telemetry before issuing automated responses.

## Memory agent & dispatcher integration
- Persist normalized alerts and incidents under `shared-context://memory-store/alert-prioritizer/{operationId}`.
- Emit events: `alert-prioritized`, `alert-incident`, `alert-escalated`, `alert-human-gate`, `alert-human-clear`.
- Subscribe to dispatcher signals (`incident-ready`, `policy-risk`, `cost-anomaly`, `deployment-risk`) to adjust alerts or escalate hit.
- Tag telemetry with `decisionId`, `tenant`, `service`, `riskScore`, `confidence`, `summary`.

## Observability & telemetry
- Metrics: alerts/incident ratio, average `riskScore`, automation vs human gate count, correlation accuracy.
- Logs: structured `log.event="alert.prioritized"` containing `alertId`, `service`, `decisionId`.
- Dashboards: integrate `/alert-prioritizer metrics --format=prometheus` into SOC/ops panels.
- Alerts: escalating the same alert >3 times, correlation failure rate >5%, automation loops hitting human gates.

## Failure handling & retries
- Retry data pulls from alert sources up to 3× with exponential backoff when APIs throttle.
- On correlation failures emit `alert-correlation-failed`, log context, and fallback to manual grouping.
- When automation responses fail, escalate to `incident-triage-runbook` and keep logs until human ack.

## Human gates
- Required when:
  1. `riskScore ≥ 0.9` and alert touches executive or customer-facing services.
  2. Automation would modify security controls (firewall, policy, key vault) or broadcast exec comms.
  3. Dispatcher requests manual review after repeated automation loops.
- Template matches the orchestrator standard: `⚠️ HUMAN GATE: ...`

## Testing & validation
- Dry-run: `/alert-prioritizer score --alert-source=prometheus --metric=error_rate --tenant=tenant-42 --dry-run`
- Unit tests: `backend/alerting/` ensures scoring and correlation logic generates repeatable priorities.
- Integration: `scripts/validate-alert-prioritizer.sh` simulates alerts across sources and verifies events.
- Regression: nightly `scripts/nightly-alert-smoke.sh` ensures automation, gating, and telemetry stay stable.

## References
- Templates: `templates/alerting/`.
- Scripts: `scripts/alert-prioritizer/`.
- Monitoring: `monitoring/alerting/`.

## Related skills
- `/incident-triage-runbook`: responds to high-priority alerts created here.
- `/stakeholder-comms-drafter`: drafts alerts-based communications.
- `/workflow-management`: reroutes workflows based on alert incidents.

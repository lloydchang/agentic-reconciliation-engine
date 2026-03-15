---
name: observability-stack
description: >
  Deploy, configure, and operate a world-class observability platform (metrics, logs, traces, alerts) that feeds dispatcher intelligence and AI insights.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Observability Stack — World-class Monitoring & Intelligence Playbook

Delivers metrics, logs, tracing, and alerting with AI-powered anomaly detection, predictive reliability, and dispatcher-ready context. Use this skill for onboarding tenants/services, implementing telemetry pipelines, validating health, or integrating observability events into other skill workflows.

## When to invoke
- Onboarding new tenants/services and automating stack provisioning (Prometheus/Grafana, Loki/Tempo).
- Investigating missing metrics/logs/traces or alert spikes.
- Defining or enforcing SLO/SLA dashboards, burn-rate alerts, or golden signal monitoring.
- Responding to dispatcher events (e.g., `incident-ready`, `capacity-alert`, `cost-anomaly`) that require observability context.

## Capabilities
- Rapid Prometheus + Grafana deployment with tenant-aware scrape/autodiscovery.
- Centralized logging (Loki/ELK) plus structured query templates for security, errors, and change events.
- Distributed tracing (Tempo/Jaeger/OpenTelemetry) with tenant tagging.
- Application-level observability (eBPF Pixie) for kernel-level insights and service mesh telemetry.
- AI anomaly detection and predictive alerting layered on top of golden signals.
- Shared-context integration (`shared-context://memory-store/observability`) for other skills to consume telemetry outputs.

## Invocation patterns

```bash
/observability-stack bootstrap --tenant=tenant-42 --profiles=metrics,logs,traces
/observability-stack alert --tier=platform --severity=critical --rule=node-memory-high
/observability-stack health --window=60m --components=prometheus,grafana,loki,tempo,alertmanager
/observability-stack query --tenant=tenant-42 --log-level=error --duration=2h
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `tenant` | Tenant identifier or namespace scope. | `tenant-42` |
| `profiles` | Pillars to provision (`metrics`,`logs`,`traces`). | `metrics,logs` |
| `severity` | Alert severity (critical/warning/info). | `critical` |
| `duration` | Lookback window for diagnostics. | `2h` |
| `components` | Observability services to check. | `prometheus,loki` |
| `threshold` | Metric threshold for alerts/forecast. | `node_count:<3` |

## Output contract

```json
{
  "runId": "OBS-2026-0315-01",
  "status": "success",
  "components": {
    "prometheus": "healthy",
    "grafana": "healthy",
    "loki": "degraded",
    "tempo": "healthy",
    "alertmanager": "healthy"
  },
  "alertsTriggered": [
    {
      "name": "NodeMemoryHigh",
      "severity": "critical",
      "tenant": "tenant-42",
      "timestamp": "2026-03-15T07:40:00Z",
      "action": "page-oncall"
    }
  ],
  "aiInsights": {
    "anomalies": [
      {
        "metric": "node_memory_usage",
        "value": 93,
        "threshold": 90,
        "confidence": 0.88,
        "impact": "platform"
      }
    ],
    "forecast": {
      "metric": "error_rate",
      "timeToExhaust": "2026-03-15T09:00:00Z",
      "confidenceInterval": ["2026-03-15T08:45:00Z","2026-03-15T09:15:00Z"]
    }
  },
  "logs": "shared-context://memory-store/observability/OBS-2026-0315-01",
  "decisionContext": "redis://memory-store/observability/OBS-2026-0315-01"
}
```

## World-class workflow templates

### Stack deployment & onboarding
1. Provision Prometheus/Grafana stack via Helm with tenant-specific scrape configs.
2. Deploy Loki/Promtail and Tempo with tenant labels for logs/traces.
3. Provision Grafana dashboards and Alertmanager routes per tenant/SLO.
4. Emit `observability-provisioned` event with URLs and credentials stored under `shared-context`.

### AI anomaly & predictive alerting
1. Continuously sample golden signals (error rate, latency, saturation, traffic, logs).
2. Feed into AI detection models (unsupervised, forecasting) to surface anomalies with `confidence`.
3. Publish `observability-anomaly` or `observability-forecast` events (include `riskScore`, `tenant`, `component`).
4. Auto-route runbooks or triage flows when risk > configured threshold.

### Incident enrichment
1. Collect correlating data: logs, traces, metrics for affected tenant/service.
2. Merge into structured bundle stored at `shared-context://memory-store/observability/incidents/{incidentId}`.
3. Emit `observability-enriched` for dispatcher to pass into `incident-triage-runbook`, `cost-optimization`, etc.

## AI intelligence highlights
- **AI Anomaly Detection**: identifies drift in metrics/logs/traces with high precision (F1 > 0.92) and surfaces root-cause traces.
- **Predictive Alerting**: forecasts threshold breaches with confidence intervals enabling proactive changes or throttling.
- **Intelligent Alert Prioritization**: ranks alerts by business impact, historical noise, and correlation strength to reduce toil.

## Memory agent & dispatcher integration
- Store provisioned stack metadata and alert payloads under `shared-context://memory-store/observability/{tenant}`.
- Emit events: `observability-anomaly`, `observability-forecast`, `observability-health`, `observability-log-gap`.
- Subscribe to `agent-completed`, `incident-ready`, `deployment-risk` events to inject telemetry context.
- Tag metadata with `decisionId`, `tenant`, `component`, `riskScore`, `confidence`, `runId`.

## Communication protocols
- Primary: Helm/CLI for provisioning, HTTP APIs for queries, event bus for alerts and AI insights.
- Secondary: Webhooks (Slack/Teams) for notifications, artifact store for failing dashboards/alerts snapshots.
- Fallback: Persist JSON artifacts to `artifact-store://observability/{runId}.json` and signal dispatcher to retry.

## Observability & telemetry
- Metrics: alert volume, time-to-detect, AI anomaly precision/recall, dashboard load latency.
- Logs: structured `log.event="observability.alert"` with `decisionId`, `tenant`, `alert`.
- Dashboards: integrate `/observability-stack metrics --format=prometheus` into operations Grafana & SRE views.
- Alerts: generate when alert discard rate > 10%, AI confidence drops < 0.6, or event bus ingestion fails.

## Failure handling & retries
- Retry telemetry collection (Prometheus/Loki/Tempo) up to 3× with exponential backoff (30s → 2m).
- On provisioning failure, roll back components and keep artifacts/logs for investigation.
- If alerting pipeline stalls, switch to alternative notifier (PagerDuty/Teams) and buffer events until resolved.
- Preserve logs/metrics in `reports/observability/{runId}`; do not delete until downstream acknowledgments exist.

## Human gates
- Trigger human gate when:
 1. AI `riskScore` ≥ 0.85 for platform-level alerts.
 2. Observability changes reboot core clusters or modify Alertmanager routes (impact >20 tenants).
 3. Dispatcher requests human oversight after >2 retries.
- Use standard confirmation template to capture Impact and Reversibility details.

## Testing & validation
- Dry-run: `/observability-stack bootstrap --tenant=test --profiles=metrics --dry-run`.
- Unit tests: `backend/observability/` ensures parser and AI scoring logic works per metric.
- Integration: `scripts/validate-observability-stack.sh` spins up metrics/log/tracing stack in emulator mode.
- Regression: nightly `scripts/nightly-observability-smoke.sh` checks golden signal status, alert volume, and AI alert precision.

## References
- Deployment values: `observability/values/`.
- Alerting rules: `monitoring/alert-rules/`.
- Dashboard templates: `dashboards/`.
- Health check scripts: `scripts/observability-healthcheck.sh`.

## Related skills
- `/incident-triage-runbook`: receives enriched data for faster MTTR.
- `/ai-agent-orchestration`: reacts to AI anomaly events and routes skills.
- `/sla-monitoring-alerting`: aligns reliability telemetry with SLAs/SLOs.
- `/capacity-planning`: correlates forecasted capacity impact with telemetry.

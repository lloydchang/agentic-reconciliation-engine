---
name: log-classifier
description: >
  Classify application and system logs into structured categories with AI-driven severity, remediation hints, and shared-context outputs.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Log Classifier — World-class Observability Playbook

Parses raw logs, classifies issues (errors, warnings, info), assigns AI risk scores, and streams structured outputs to dispatcher or remediation skills.

## When to invoke
- Analyze incident logs, alerts, or monitoring spikes.
- Categorize logs (database, network, security, application) and tag severity.
- Supply structured context to `incident-triage-runbook`, `audit-siem`, or automation workflows.
- Feed derived insights into dashboards, quality gates, or AI orchestrations.

## Capabilities
- **Raw log parsing** with regex/ML heuristics for timestamps, components, stack traces.
- **AI severity scoring** (low/medium/high) with remediation hints.
- **Streaming/classification pipelines** for batch or real-time logs.
- **Shared-context propagation** at `shared-context://memory-store/logs/{operationId}`.
- **Human gating** when remediation impacts production.

## Invocation patterns

```bash
/log-classifier classify --input=logs/app.log --format=json --context=shared-context://memory-store/incident/INC-2026-0315
/log-classifier summarize --input=logs/latest-incident.log --severity=high --output=report
/log-classifier stream --source=syslog --category=network --priority=critical
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `input` | Log file or input stream. | `logs/app.log` |
| `format` | Output format (`json|table`). | `json` |
| `context` | Shared context for correlation. | `shared-context://memory-store/incident/INC-2026-0315` |
| `category` | Category filter (`database|network|security|app`). | `database` |
| `priority` | Severity threshold. | `critical` |

## Output contract

```json
{
  "operationId": "LOG-2026-0315-01",
  "status": "success",
  "logsClassified": 120,
  "categories": { "database": 45, "network": 30, "application": 25, "security": 20 },
  "findings": [
    {
      "log": "ERROR Failed to connect to database",
      "category": "database",
      "severity": "high",
      "riskScore": 0.82,
      "suggestedAction": "Check DB service and restart connection pools"
    }
  ],
  "decisionContext": "redis://memory-store/logs/LOG-2026-0315-01",
  "logs": "shared-context://memory-store/logs/LOG-2026-0315-01"
}
```

## World-class workflow templates

### Batch classification
1. Parse log lines, extract metadata (timestamp, service, severity).
2. Match patterns (regex/ML) to assign categories and use AI to compute severity.
3. Score findings, record suggested actions, emit `log-classified` events for incident automation.

### Streaming classification
1. Ingest logs via watchers (syslog, aggregator) with filters.
2. Classify entries in real time and stream results to dashboards or orchestrations.
3. Trigger alerts when severity/volume crosses thresholds.

### Incident enrichment
1. Correlate logs with shared incident context.
2. Provide structured evidence to `incident-triage-runbook` for root-cause analysis.
3. Emit `log-context-ready` for downstream teams.

## AI intelligence highlights
- **AI severity scoring** uses anomalies and historical context to rate logs from info to critical.
- **Intelligent action suggestions** propose fix steps (restart, check credentials) drawn from past incidents.
- **Predictive alert filtering** reduces noise by grouping similar logs and surfacing aggregated impact.

## Memory agent & dispatcher integration
- Persist classifications under `shared-context://memory-store/logs/{operationId}`.
- Emit events: `log-classified`, `log-alert`, `log-context-ready`.
- React to dispatcher signals (`incident-ready`, `policy-risk`) to enrich follow-up automations.
- Tag context with `decisionId`, `tenant`, `riskScore`, `category`.

## Observability & telemetry
- Metrics: logs processed/minute, severity distribution, categories, accepted action suggestions.
- Logs: structured `log.event="log.classified"` with `operationId`, `category`, `severity`.
- Dashboards: include `/log-classifier metrics --format=prometheus` for observability.
- Alerts: classification failure rate > 5%, high severity logs without escalation.

## Failure handling & retries
- Retry parsing/ingestion up to 2× on IO/parsing errors.
- On repeated failures escalate to `incident-triage-runbook` and provide fallback summaries.
- Preserve artifacts until downstream acknowledges for audit purposes.

## Human gates
- Required when:
  1. Suggested action would restart production services.
  2. Severity critical/impact scope wide requiring policy oversight.
  3. Dispatcher requests manual review after repeated noise or automation failure.
- Use the orchestrator-standard confirmation template (impact, reversibility).

## Testing & validation
- Dry-run: `/log-classifier classify --input=logs/sample.log --dry-run`.
- Unit tests: `backend/logs/` ensures models and scoring logic behave as expected.
- Integration: `scripts/validate-log-classifier.sh` converts sample logs and verifies structured output.
- Regression: nightly `scripts/nightly-log-smoke.sh` monitors accuracy and telemetry thresholds.

## References
- Scripts: `scripts/log-classifier/`.
- Templates: `templates/log-classification-report.md`.

## Related skills
- `/incident-triage-runbook`: uses logs for incident context.
- `/audit-siem`: stores classified logs for compliance evidence.
- `/ai-agent-orchestration`: orchestrates follow-up workflows triggered by log events.

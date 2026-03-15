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

Parses raw logs, classifies issues (errors, warnings, info), assigns AI risk scores, and feeds structured outputs into dispatchers or remediation workflows. Use when ingesting incident logs, summarizing alerts, or augmenting incidents with log context.

## When to invoke
- Analyze logs from incidents, alerts, or monitoring spikes.
- Classify logs into categories (database, network, security, application) and assign severity.
- Provide recommendations/actions for engineering teams or automation scripts.
- Supply structured context to `incident-triage-runbook`, `audit-siem`, or `workflow-management`.

## Capabilities
- Raw log parsing + pattern extraction using regex/ML heuristics.
- AI severity scoring (low/medium/high) with suggested actions.
- Support for structured outputs used by downstream skills through shared context.
- Human gates when remediation could touch production systems.

## Invocation patterns

```bash
/log-classifier classify --input=logs/app.log --format=json --context=shared-context://memory-store/incident/INC-2026-0315
/log-classifier summarize --input=logs/latest-incident.log --severity=high --output=report
/log-classifier stream --source=syslog --category=network --priority=critical
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `input` | Log file or string to classify. | `logs/app.log` |
| `format` | Output format (`json|table`). | `json` |
| `context` | Shared context for incident correlation. | `shared-context://memory-store/incident/INC-2026-0315` |
| `category` | Target category filter. | `database` |
| `priority` | Severity threshold. | `critical` |

## Output contract

```json
{
  "operationId": "LOG-2026-0315-01",
  "status": "success",
  "logsClassified": 120,
  "categories": {
    "database": 45,
    "network": 30,
    "application": 25,
    "security": 20
  },
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
1. Parse log lines, extract timestamp/service/severity.
2. Match patterns (regex/ML) to assign categories and severity.
3. Score findings via AI risk heuristics and record suggested actions.
4. Emit `log-classified` events with structured data for incidents.

### Streaming classification
1. Ingest logs via watcher (syslog, log aggregator) with filters.
2. Stream classification results per log entry.
3. Trigger alert or incident skill when severity high.

### Incident enrichment
1. Correlate logs to incident IDs (shared context).
2. Provide structured context to `incident-triage-runbook` for root cause.
3. Emit `log-context-ready` event.

## AI intelligence highlights
- **AI severity scoring**: uses anomaly detection to rate logs from low (info) to critical (security incidents).
- **Intelligent action suggestions**: recommends fix steps (restart service, check credentials) based on past incidents.
- **Predictive alert filtering**: reduces noise by grouping similar logs and scoring aggregated impact.

## Memory agent & dispatcher integration
- Store classified logs at `shared-context://memory-store/logs/<operationId>`.
- Emit events: `log-classified`, `log-alert`, `log-context-ready`.
- Subscribe to dispatcher signals (`incident-ready`, `policy-risk`) to add log context to follow-up workflows.
- Tag records with `decisionId`, `tenant`, `riskScore`.

## Communication protocols
- Primary: CLI scripts reading log files or streaming watchers.
- Secondary: Event bus for `log-*` signals consumed by incident/policy skills.
- Fallback: Persist JSON to `artifact-store://logs/<operationId>.json`.

## Observability & telemetry
- Metrics: logs processed per minute, severity distribution, categories, action suggestions accepted.
- Logs: structured `log.event="log.classified"` with `operationId`, `category`, `severity`.
- Dashboards: integrate `/log-classifier metrics --format=prometheus`.
- Alerts: classification failure rate > 5%, high severity logs > threshold, shared context missing.

## Failure handling & retries
- Retry parsing/ingestion up to 2× on transient errors (IO, parsing).
- On repeated failures, escalate to `incident-triage-runbook` and log context.
- Retain shared-context artifacts until downstream ack.

## Human gates
- Required when:
 1. Action suggestion would restart production services.
 2. Severity critical/impact scope wide.
 3. Dispatcher requests manual review after repeated noise.
- Use standard human gate template.

## Testing & validation
- Dry-run: `/log-classifier classify --input=logs/sample.log --dry-run`.
- Unit tests: `backend/logs/` ensures classification models and scoring behave as expected.
- Integration: `scripts/validate-log-classifier.sh` converts sample logs and verifies structured output.
- Regression: nightly `scripts/nightly-log-smoke.sh` ensures classification accuracy and telemetry.

## References
- Scripts: `scripts/log-classifier/`.
- Templates: `templates/log-classification-report.md`.

## Related skills
- `/incident-triage-runbook`: uses logs to contextualize incidents.
- `/audit-siem`: stores classified logs for compliance evidence.
- `/ai-agent-orchestration`: orchestrates follow-up workflows when log alerts fire.

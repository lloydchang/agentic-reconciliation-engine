---
name: audit-siem
description: >
  Collect, enrich, and forward audit logs/security events into SIEMs with AI risk scoring and dispatcher integration.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Audit & SIEM — World-class Observability Playbook

Centralizes audit logs (Azure Activity, Kubernetes auditable, application events, Defender findings) with connectors, KQL queries, automated responses, and shared context so security/compliance teams always have evidence.

## When to invoke
- Configure Log Analytics/Sentinel/Splunk/Elastic ingestion across Azure, Kubernetes, and application layers.
- Answer “who touched this secret/account?” or respond to suspicious activity.
- Generate compliance evidence (SOC2, ISO27001, PCI) or detection packages for auditors.
- React to dispatcher/memory agent alerts (`policy-risk`, `incident-ready`, `security-anomaly`) that need log-based context.

## Capabilities
- **Multi-source ingestion** (Azure Activity, Kubernetes audit, Defender, network flow, application telemetry).
- **AI-assisted detection** with risk scoring, enrichment, alert prioritization, and automated remediation playbooks.
- **Shared-context propagation** via `shared-context://memory-store/audit/{operationId}` for downstream skills.
- **Response orchestration** (PagerDuty, Slack, automation runbooks) for high-risk alerts.
- **Human gating** before sensitive access changes or policy enforcement steps.

## Invocation patterns

```bash
/audit-siem configure --workspace=law-platform-eastus --connectors=azureactivity,defender,kubernetes
/audit-siem query --period=24h --query="AzureDiagnostics | where ResourceType=='VAULTS'" --format=json
/audit-siem alert --rule=bruteforce --severity=high --action=notify
/audit-siem evidence --period-start=2026-01-01 --period-end=2026-03-01 --output=reports/soc2
/audit-siem respond --incident=INC-2026-041 --playbook=logic-app
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `workspace` | Log Analytics/SIEM workspace. | `law-platform-eastus` |
| `query` | KQL/elastic query. | `AzureDiagnostics | where ResourceType=='VAULTS'` |
| `period` | Lookback window. | `24h` |
| `rule` | Alert rule name. | `bruteforce` |
| `severity` | Alert severity (`info|warning|critical`). | `high` |
| `incident` | Incident reference. | `INC-2026-041` |

## Output contract

```json
{
  "operationId": "AUD-2026-0315-01",
  "status": "success|failure",
  "operation": "configure|query|alert|evidence|respond",
  "workspace": "law-platform-eastus",
  "resultsCount": 42,
  "riskScore": 0.78,
  "alertsTriggered": [
    {
      "name": "BruteForceDetection",
      "severity": "high",
      "timestamp": "2026-03-15T08:12:00Z"
    }
  ],
  "evidenceFiles": ["reports/soc2/admin-actions.json"],
  "logs": "shared-context://memory-store/audit/AUD-2026-0315-01",
  "decisionContext": "redis://memory-store/audit/AUD-2026-0315-01"
}
```

## World-class workflow templates

### SIEM configuration & enrichment
1. Provision workspaces/connectors, enable diagnostic settings for Azure Activity, Kubernetes, Key Vault, Defender, NSGs.
2. Normalize ingested logs and annotate with entity/context information.
3. Emit `audit-configured` events with workspace metadata for dispatcher tracking.

### Detection & alerting
1. Create scheduled/streaming analytics rules for brute force, RBAC changes, secret access, and suspicious deployments.
2. Tag alerts with AI riskScore (user role, event context, policy impact) and recommend playbooks.
3. Emit `audit-alert` events enriched with evidence for `incident-triage-runbook` or `policy-as-code`.

### Compliance evidence generation
1. Run compliance queries (admin actions, secret access, policy violations) over defined periods.
2. Export artifacts (JSON/CSV) with narrative context for auditors.
3. Emit `evidence-ready` events linking to artifact URIs for downstream skills.

## AI intelligence highlights
- **AI risk scoring** blends severity, user role, history, and compliance context to assign `riskScore`.
- **Smart detection prioritization** reduces noise by ranking alerts with impact/urgency.
- **Intelligent evidence assembly** picks relevant logs/events, formats them, and surfaces actionable summaries.

## Memory agent & dispatcher integration
- Store queries/reports under `shared-context://memory-store/audit/{operationId}`.
- Emit `audit-alert`, `playbook-run`, `evidence-ready`, `audit-configured` events.
- Subscribe to dispatcher signals (`incident-ready`, `policy-risk`, `cost-anomaly`) to start targeted investigations.
- Tag metadata with `decisionId`, `workspace`, `riskScore`, `policy`, and `confidence`.

## Observability & telemetry
- Metrics: alert volumes, detection accuracy, evidence exports, riskScore trends.
- Logs: structured `log.event="audit.alert"` with workspace, rule, decisionId.
- Dashboards: integrate `/audit-siem metrics --format=prometheus` for SOC/SRE teams.
- Alerts: alert volume spikes, riskScore ≥ 0.9, failures to generate evidence.

## Failure handling & retries
- Retry diagnostic/API calls up to 2× with exponential backoff on transient errors.
- On alerting failure emit `audit-alert-failed`, store context, escalate to `incident-triage-runbook`.
- Retain artifacts until downstream acknowledges, preserving audit records.

## Human gates
- Required when:
  1. Automated response disables accounts/modifies access.
  2. Evidence packages expose sensitive gaps needing exec review.
  3. Dispatcher requests manual review after repeated high-risk alerts.
- Confirmation template matches orchestrator standards.

## Testing & validation
- Dry-run: `/audit-siem query --query="AzureActivity | take 1" --dry-run`.
- Unit tests: `backend/audit/` ensures parser/alert logic functions correctly.
- Integration: `scripts/validate-audit-siem.sh` spins up workspaces, emits sample logs, verifies alerts.
- Regression: nightly `scripts/nightly-audit-smoke.sh` ensures connectors, alerts, evidence flows stay stable.

## References
- Logging guidelines: `docs/SECURITY-OPERATIONS.md`.
- Alert rules: `monitoring/alert-rules/audit`.
- Evidence scripts: `scripts/audit/`.

## Related skills
- `/incident-triage-runbook`: receives critical alerts to execute.
- `/policy-as-code`: shares policy violations for detection tuning.
- `/ai-agent-orchestration`: coordinates follow-up workflows based on audit data.

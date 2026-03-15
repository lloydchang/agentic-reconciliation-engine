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

Centralizes audit logs (Azure Activity Log, Kubernetes audits, application events, Defender findings) with KQL queries, Sentinel/Splunk/Elastic connectors, automated response playbooks, and shared-context outputs. Trigger when configuring logging, investigating suspicious access, or generating compliance evidence.

## When to invoke
- Configure Log Analytics/SIEM ingestion across Azure/Kubernetes/application layers.
- Query who accessed secrets or performed privileged operations.
- Generate compliance evidence (SOC2, ISO27001, PCI) or detection packages.
- Respond to incidents by searching logs, triaging alerts, and forwarding relevant events to the dispatcher.
- React to `policy-risk`, `incident-ready`, or `security-anomaly` events from memory agents.

## Capabilities
- Multi-source log collection (Azure Activity, Kubernetes audit, application telemetry, network events).
- AI-assisted detection rules, risk scoring, event enrichment, and alert prioritization.
- Automated response playbooks (PagerDuty, Slack, disable accounts) for high-severity alerts.
- Shared context integration `shared-context://memory-store/audit/<operationId>` for other skills.
- Human gate guidance for sensitive responses (suspending accounts, closing access).

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
| `query` | KQL query portion. | `AzureDiagnostics | where ResourceType=='VAULTS'` |
| `period` | Lookback window. | `24h` |
| `rule` | Sentinel/alert rule name. | `bruteforce` |
| `severity` | Alert severity (info/warning/critical). | `high` |
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
1. Create Log Analytics workspace + Sentinel/Splunk connector with required data sources.
2. Enable diagnostic settings for Azure Activity, Key Vault, Kubernetes, Defender.
3. Emit `audit-configured` events with workspace/connector metadata.

### Detection & alerting
1. Create scheduled/streaming analytics rules for brute force, RBAC changes, secret access.
2. AI risk scoring tags alerts (riskScore based on user, event type, policy) and triggers playbook.
3. Emit `audit-alert` event containing enriched data for dispatcher/incident skill consumption.

### Compliance evidence generation
1. Run queries across admin actions, secret access, failed logins, policy compliance.
2. Export JSON/CSV artifacts for auditors and store in versioned directory.
3. Emit `evidence-ready` events linking to artifact URIs.

## AI intelligence highlights
- **AI Risk Assessment**: blends event severity, user role, historical behavior, and policy impact to produce `riskScore`.
- **Smart Detection Prioritization**: ranks alerts by downstream impact (policy, incident) and reduces noise.
- **Intelligent Evidence Assembly**: automatically selects relevant logs for compliance periods and formats them.

## Memory agent & dispatcher integration
- Persist queries/reports under `shared-context://memory-store/audit/<operationId>`.
- Emit events: `audit-alert`, `evidence-ready`, `playbook-run`, `audit-configured`.
- Subscribe to dispatcher signals (`incident-ready`, `policy-risk`) to begin targeted investigations.
- Tag entries with `decisionId`, `workspace`, `riskScore`.

## Communication protocols
- Primary: CLI (az monitor, az sentinel) and KQL queries triggered via script.
- Secondary: Event bus for `audit-*` events consumed by dispatcher.
- Fallback: Artifact files at `artifact-store://audit/<operationId>.json`.

## Observability & telemetry
- Metrics: alerts by severity, audit queries executed, evidence packages generated, riskScore trends.
- Logs: structured `log.event="audit.alert"` with workspace, rule, decisionId.
- Dashboards: integrate `/audit-siem metrics --format=prometheus`.
- Alerts: alert-volume > baseline, riskScore ≥ 0.9, evidence generation failure.

## Failure handling & retries
- Retry diagnostic/API calls up to 2× on failures with exponential backoff.
- On alerting failure, log context, emit `audit-alert-failed`, escalate to `incident-triage-runbook`.
- Preserve artifacts until downstream consumers acknowledge.

## Human gates
- Required when:
 1. Automated response disables accounts, modifies access, or blocks resources.
 2. Evidence packages reveal sensitive compliance gaps needing executive review.
 3. Dispatcher requests manual review after repeated high-risk alerts.
- Use standard human gate template (impact/reversibility).

## Testing & validation
- Dry-run: `/audit-siem query --query="AzureActivity | take 1" --dry-run`.
- Unit tests: `backend/audit/` ensures parser/alert logic functions per expectation.
- Integration: `scripts/validate-audit-siem.sh` spins up workspace, emits sample logs, and verifies alerts.
- Regression: nightly `scripts/nightly-audit-smoke.sh` ensures connectors, alerts, and evidence workflows stay stable.

## References
- Loging guidelines: `docs/SECURITY-OPERATIONS.md`.
- Alert rules: `monitoring/alert-rules/audit`.
- Evidence scripts: `scripts/audit/`.

## Related skills
- `/incident-triage-runbook`: receives critical alerts to execute.
- `/policy-as-code`: monitors policy violations leading to audit trails.
- `/ai-agent-orchestration`: coordinates responses based on audit evidence.

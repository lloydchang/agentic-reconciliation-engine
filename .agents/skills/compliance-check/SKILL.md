---
name: compliance-check
description: >
  Start, monitor, and report on compliance checks (SOC2, GDPR, HIPAA) with AI scoring, gating, and dispatcher context.
argument-hint: "[targetResource] [complianceType] [priority]"
disable-model-invocation: false
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
---

# Compliance Check — World-class Regulator Playbook

Launches Temporal compliance workflows, tracks progress, and generates evidence packages while integrating AI risk scoring and shared context for downstream skills. Use when verifying SOC2/GDPR/HIPAA, preparing audits, or responding to compliance incidents.

## When to invoke
- Start compliance scans per resource/environment.
- Monitor scan progress and produce reports/postmortems.
- Enforce policy frameworks, follow up on failed controls.
- Provide dispatcher alerts when compliance risk high.

## Capabilities
- Start Temporal compliance workflows.
- Monitor execution/states.
- Generate compliance reports, evidence packages, remediation plans.
- AI risk scoring, gating for high-severity violations.
- Shared context `shared-context://memory-store/compliance/<operationId>`.

## Invocation patterns

```bash
/compliance-check scan --targetResource=production-cluster --complianceType=SOC2 --priority=high
/compliance-check scan --targetResource=database-cluster --complianceType=HIPAA --priority=critical
/compliance-check report --operationId=COMPLIANCE-2026-0315-01 --format=json
/compliance-check monitor --workflowId=WF-12345
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `targetResource` | Target object (cluster, tenant, all). | `prod-cluster` |
| `complianceType` | Standard (SOC2, GDPR, HIPAA, CIS). | `SOC2` |
| `priority` | workflow priority (low/normal/high/critical). | `high` |
| `operationId` | Compliance workflow ID. | `COMPLIANCE-2026-0315-01` |
| `workflowId` | Temporal workflow ID to monitor. | `WF-12345` |

## Output contract

```json
{
  "operationId": "COMPLIANCE-2026-0315-01",
  "status": "started|running|completed|failed",
  "targetResource": "prod-cluster",
  "complianceType": "SOC2",
  "priority": "high",
  "reportUrl": "https://reports/compliance/COMPLIANCE-2026-0315-01",
  "riskScore": 0.62,
  "findings": [
    {
      "id": "FIND-0001",
      "severity": "high",
      "description": "K8s audit logging not enabled"
    }
  ],
  "decisionContext": "redis://memory-store/compliance/COMPLIANCE-2026-0315-01",
  "logs": "shared-context://memory-store/compliance/COMPLIANCE-2026-0315-01"
}
```

## World-class workflow templates

### Compliance scan execution
1. Launch Temporal workflow with target/resource.
2. Collect scans across frameworks (SOC2, GDPR, HIPAA).
3. Track progress, emit events (`compliance-progress`, `compliance-complete`).
4. Summarize findings, riskScore, and remediation steps for stakeholders.

### Evidence package generation
1. Query activity logs, audit trails, policy state for time window.
2. Compile JSON/CSV artifacts and generate compliance PDF.
3. Emit `compliance-evidence-ready`.

### Monitoring & human review
1. Monitor workflow states; re-run or escalate on failure.
2. Trigger `request_human_review` when riskScore high or partial compliance.

## AI intelligence highlights
- **AI Risk Scoring**: severity-aware scoring of findings to prioritize gating.
- **Smart Remediation Plan**: sequences actions by impact and assurance effort.
- **Intelligent Evidence Assembly**: selects key logs/events for auditors.

## Memory agent & dispatcher integration
- Store compliance outputs under `shared-context://memory-store/compliance/<operationId>`.
- Emit events: `compliance-progress`, `compliance-alert`, `compliance-complete`.
- Subscribe to dispatcher alerts (policy-risk) to run focused scans.
- Tag entries with `decisionId`, `targetResource`, `complianceType`, `riskScore`.

## Communication protocols
- Primary: Temporal API calls to start/monitor workflows.
- Secondary: Event bus for `compliance-*` events.
- Fallback: JSON artifacts `artifact-store://compliance/<operationId>.json`.

## Observability & telemetry
- Metrics: compliance runs by type/status, finding count, riskScore.
- Logs: structured `log.event="compliance.run"` with `operationId`.
- Dashboards: integrate `/compliance-check metrics --format=prometheus`.
- Alerts: repeated failures, high-risk findings, missing evidence.

## Failure handling & retries
- Retry workflow start/monitor API up to 2×; on failure escalate to `incident-triage-runbook`.
- If scan halts due to missing permissions, fallback to local compliance heuristics.
- Retain artifacts/logs for audit; never auto-delete.

## Human gates
- Required when:
 1. RiskScore ≥ 0.8 or critical compliance findings.
 2. Compliance egress/impact touches customer data or sensitive fields.
 3. Dispatcher requests manual review after repeated auto-runs.
- Use standard human gate template capturing impact/reversibility.

## Testing & validation
- Dry-run: `/compliance-check scan --targetResource=canary --complianceType=SOC2 --dry-run`.
- Unit tests: `backend/compliance/` ensures scoring/guidance logic.
- Integration: `scripts/validate-compliance-check.sh` triggers workflows and extracts evidence.
- Regression: nightly `scripts/nightly-compliance-smoke.sh` ensures workflows and alerts remain stable.

## References
- Templates: `templates/compliance-report.md`.
- Scripts: `scripts/compliance-validator.sh`.
- Assets: `assets/compliance-checklist.json`.

## Related skills
- `/policy-as-code`: ensures policy compliance before scanning.
- `/incident-triage-runbook`: triggered by compliance blockers.
- `/ai-agent-orchestration`: coordinates compliance sequences.

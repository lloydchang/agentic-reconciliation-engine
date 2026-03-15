---
name: compliance-reporter
description: |
  Generate compliance evidence, audit summaries, and executive posture reports by correlating policy, scanning, and telemetry data.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Compliance Reporter — World-class Evidence Playbook

Automates SOC2, ISO, HIPAA, and PCI evidence collection by packaging findings, remediations, and telemetry into structured reports for auditors and leadership.

## When to invoke
- After compliance scans, policy evaluations, or audit requests for evidence.
- When new drifts, incidents, or policy changes occur that impact compliance controls.
- To produce executive summaries showing posture trends and outstanding risks.
- Dispatcher/memory agents signal `compliance-request`, `audit-ready`, or `policy-risk` events.

## Capabilities
- **Evidence aggregation** collects policy scans, SIEM findings, and configuration data.
- **Narrative generation** frames context, mitigation steps, and owners in structured templates.
- **Confidence scoring** highlights risky controls and predicted remediation impact.
- **Distribution hooks** publish PDFs, Markdown, or CSV artifacts to auditors, exec dashboards, or knowledge stores.
- **Shared context** writes evidence to `shared-context://memory-store/compliance-reporter/{operationId}`.

## Invocation patterns
```bash
/compliance-reporter snapshot --framework=SOC2 --period=Q1-2026
/compliance-reporter audit --control=CC6.1 --result=pass
/compliance-reporter summary --tenant=tenant-42 --audience=exec
/compliance-reporter drift --policy=tagging --change=CR-2026-041
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `framework` | Compliance standard (`SOC2`, `ISO27001`, `PCI`). | `SOC2` |
| `period` | Reporting period. | `Q1-2026` |
| `control` | Control identifier. | `CC6.1` |
| `result` | Control outcome (`pass`, `fail`, `warning`). | `pass` |
| `tenant` | Tenant scope. | `tenant-42` |
| `audience` | Recipient (auditor, executive, compliance). | `exec` |
| `policy` | Policy name causing drift. | `tagging` |

## Output contract
```json
{
  "operationId": "CR-2026-0315-01",
  "status": "ready|pending|error",
  "framework": "SOC2",
  "control": "CC6.1",
  "result": "pass",
  "evidence": ["scans/CC6.1-check.pdf", "logs/guardrails/CC6.1.json"],
  "riskScore": 0.21,
  "summary": "Kubernetes audit completed with zero findings",
  "logs": "shared-context://memory-store/compliance-reporter/CR-2026-0315-01",
  "decisionContext": "redis://memory-store/compliance-reporter/CR-2026-0315-01"
}
```

## World-class workflow templates

### Evidence snapshotting
1. Gather scan outputs (tfsec, checkov, CIS, SIEM) relevant to controls.
2. Normalize findings, attach citations, and emit `compliance-evidence` events.
3. Command stub: `/compliance-reporter snapshot --framework=SOC2 --period=Q1-2026`

### Control verification
1. Assess control (e.g., CC6.1) with telemetry, config, and policy outputs.
2. Document outcome and required mitigation.
3. Command stub: `/compliance-reporter audit --control=CC6.1 --result=pass`

### Executive posture summary
1. Synthesize top risks, remediation KPIs, and trending posture metrics.
2. Format for exec dashboards, attach recommendations.
3. Command stub: `/compliance-reporter summary --tenant=tenant-42 --audience=exec`

### Drift & policy change logs
1. Detect policy drifts (e.g., tagging changes) and log them for auditors.
2. Emit `compliance-drift` events and link to commit/CR context.
3. Command stub: `/compliance-reporter drift --policy=tagging --change=CR-2026-041`

## AI intelligence highlights
- **AI context fusion** blends scan results, policy metadata, and telemetry for crisp evidence.
- **Intelligent recommendations** prioritize remediation tasks by control impact.
- **Predictive posture** forecasts compliance over the next quarters.

## Memory agent & dispatcher integration
- Store evidence under `shared-context://memory-store/compliance-reporter/{operationId}`.
- Emit events: `compliance-evidence`, `compliance-summary`, `compliance-drifts`, `compliance-human-gate`.
- Subscribe to dispatcher signals (`policy-risk`, `incident-ready`, `audit-request`).
- Tag entries with `decisionId`, `framework`, `control`, `tenant`, `riskScore`.

## Observability & telemetry
- Metrics: documents created, evidence completeness %, summary latencies.
- Logs: structured `log.event="compliance.report"` with `framework`, `control`, `status`.
- Dashboards: include `/compliance-reporter metrics --format=prometheus`.
- Alerts: pending human gate >10m, drift warnings, missing evidence.

## Failure handling & retries
- Retry scan fetches or API calls up to 3× when endpoints throttle.
- If evidence generation fails, capture partial output and flag `compliance-human-gate`.
- Retain artifacts for 365 days for audit compliance.

## Human gates
- Required when:
  1. Reports touch exec/stakeholder communications.
  2. Control failure indicates major risk.
  3. Dispatcher requests manual review after repeated automation loops.

## Testing & validation
- Dry-run: `/compliance-reporter summary --tenant=test --audience=exec --dry-run`
- Unit tests: `backend/compliance-reporter/` ensures templates compile.
- Integration: `scripts/validate-compliance-reporter.sh` builds evidence packages.
- Regression: nightly `scripts/nightly-compliance-smoke.sh` confirms outputs & citations.

## References
- Scripts: `scripts/compliance-reporter/`.
- Templates: `templates/compliance/`.
- Monitoring: `monitoring/compliance/`.

## Related skills
- `/compliance-security-scanner`: supplies findings.
- `/policy-as-code`: correlates policy changes with compliance.
- `/doc-generator`: produces narrative artifacts from this evidence.

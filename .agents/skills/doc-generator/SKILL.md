---
name: doc-generator
description: |
  Automate operational documentation, runbooks, and playbooks by transforming telemetry, incidents, and compliance data into narrative artifacts with AI assistance and structured outputs.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Doc Generator — World-class Knowledge Playbook

Produces runbooks, postmortems, change documentation, and compliance artifacts that cite evidence, reference shared context, and feed back into the agent memory system.

## When to invoke
- After incidents, changes, or policy updates when runbooks or postmortems must be refreshed.
- When new automation or workflows are created and documentation needs to stay current.
- For compliance evidence (SOC2, ISO) requiring structured context and traceability.
- Dispatcher/memory agents emit `doc-request`, `incident-complete`, `policy-report` events.

## Capabilities
- **Narrative templates** for incident runbooks, change summaries, compliance briefs, and executive updates.
- **Evidence bundling** pulls telemetry, alerts, and skill outputs via `shared-context://memory-store/doc-generator/{operationId}`.
- **AI writers** synthesize context, highlight impact, and propose next actions with citations.
- **Version control hooks** create drafts, open PRs, or update wiki pages with metadata.
- **Human gates** ensure drafts receive approvals before publishing sensitive material.

## Invocation patterns
```bash
/doc-generator runbook --incident=INC-2026-0315-01 --format=markdown
/doc-generator change --changeId=CR-2026-0315-10 --audience=operations
/doc-generator compliance --framework=SOC2 --period=Q1-2026
/doc-generator summary --topic=deployment-health --audience=exec
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `incident` | Incident ID for runbook/postmortem context. | `INC-2026-0315-01` |
| `changeId` | Change request identifier. | `CR-2026-0315-10` |
| `framework` | Compliance standard (SOC2, ISO27001). | `SOC2` |
| `period` | Reporting period (Q1-2026). | `Q1-2026` |
| `topic` | Topic/narrative focus. | `deployment-health` |
| `audience` | Recipient (operations, executive, security). | `exec` |

## Output contract
```json
{
  "operationId": "DOC-2026-0315-01",
  "status": "draft|reviewed|published",
  "documentType": "runbook|change|compliance|summary",
  "title": "Production incident INC-2026-0315-01 runbook",
  "body": "...",
  "audience": "operations",
  "citations": [ "shared-context://memory-store/incident/INC-2026-0315-01" ],
  "logs": "shared-context://memory-store/doc-generator/DOC-2026-0315-01",
  "decisionContext": "redis://memory-store/doc-generator/DOC-2026-0315-01"
}
```

## World-class workflow templates

### Runbook & postmortem generation
1. Collect incident timeline, telemetry, remediations from `shared-context://memory-store/incident/{incident}`.
2. Populate structured narrative with impact, resolution, and action items.
3. Emit `doc-runbook` event and open PR or update wiki drafts.
4. Command stub: `/doc-generator runbook --incident=INC-2026-0315-01 --format=markdown`

### Change & release documentation
1. Summarize deployments, config changes, and approvals.
2. Include rollback plans, impact analysis, and verification steps.
3. Emit `doc-change` events and push to docs repository.
4. Command stub: `/doc-generator change --changeId=CR-2026-0315-10 --audience=operations`

### Compliance & audit briefs
1. Aggregate evidence (alerts, audits, policy scans) for frameworks.
2. Produce executive-ready summaries with citations.
3. Emit `doc-compliance` and store artifacts.
4. Command stub: `/doc-generator compliance --framework=SOC2 --period=Q1-2026`

### Executive/summary communications
1. Craft concise narratives for execs (KPI, health, risk) referencing major events.
2. Attach data, links, and recommendations.
3. Emit `doc-summary` and notify stakeholders.
4. Command stub: `/doc-generator summary --topic=deployment-health --audience=exec`

## AI intelligence highlights
- **AI narrative** transforms structured telemetry into clear explanations with bounded detail.
- **Citation tracking** ensures every document links back to shared context for traceability.
- **Adaptive tone** matches the audience (ops, execs, auditors) using persona templates.

## Memory agent & dispatcher integration
- Save drafts under `shared-context://memory-store/doc-generator/{operationId}` with `decisionId`, `audience`, `documentType`, `framework`.
- Emit events: `doc-runbook`, `doc-change`, `doc-compliance`, `doc-summary`, `doc-human-gate`.
- Subscribe to dispatcher signals (`incident-ready`, `policy-risk`, `capacity-alert`) to auto-generate updates.

## Observability & telemetry
- Metrics: documents created per type, review cycles, publication lag, human gate hits.
- Logs: structured `log.event="doc.generator"` with `documentType`, `status`, `audience`.
- Dashboards: integrate `/doc-generator metrics --format=prometheus` for knowledge ops.
- Alerts: docs stuck waiting for review >1h, human gates pending, citation missing.

## Failure handling & retries
- Retry telemetry/context pulls up to 3× when stores time out; log partial drafts if data unavailable.
- If automation fails to push docs, emit `doc-publish-failed` and wait for manual intervention.
- Preserve drafts until downstream skills ack; do not delete evidence artifacts prematurely.

## Human gates
- Required when:
  1. Communications go to execs/security.
  2. Compliance documents include sensitive data.
  3. Dispatcher requests manual approve after multiple revisions.

## Testing & validation
- Dry-run: `/doc-generator summary --topic=test --audience=ops --dry-run`
- Unit tests: `backend/doc-generator/` ensures templates and citations render correctly.
- Integration: `scripts/validate-doc-generator.sh` produces docs from sample incidents.
- Regression: nightly `scripts/nightly-doc-generator-smoke.sh` verifies output formatting and events.

## References
- Templates: `templates/docs/`.
- Scripts: `scripts/doc-generator/`.
- Monitoring: `monitoring/docs/`.

## Related skills
- `/runbook-documentation-gen`: complementary runbook automation.
- `/incident-triage-runbook`: supplies incident context.
- `/stakeholder-comms-drafter`: crafts message distribution after docs publish.

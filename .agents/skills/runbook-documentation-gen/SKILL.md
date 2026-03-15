---
name: runbook-documentation-gen
description: >
  Generate, maintain, and sync runbooks, ADRs, postmortems, and documentation with AI-assisted context and dispatcher integration.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Runbook & Documentation Generator — World-class Knowledge Playbook

Automates creation and upkeep of operational runbooks, ADRs, postmortems, API docs, and onboarding guides with AI narratives and shared context for downstream automation.

## When to invoke
- Draft or update runbooks for incidents, alerts, or operational playbooks.
- Generate ADRs or decision records from proposals or architecture changes.
- Compile documentation from OpenAPI specs, Terraform manifests, observability outputs, or policy references.
- Sync documentation to Backstage, Confluence, Notion, or internal portals.
- Feed `incident-triage`, `stakeholder-comms-drafter`, or dispatcher follow-ups with narrative context.

## Capabilities
- **Runbook scripting** that extracts timelines, diagnostics, and remediation steps from incidents.
- **ADR & decision capture** using MADR templates with options, decisions, and consequences.
- **Reference doc generation** from OpenAPI/Terraform with diagram links and quality checks.
- **Sync pipelines** that push docs to Backstage/Confluence/Notion plus metadata tracking.
- **Shared-context propagation** at `shared-context://memory-store/docs/{operationId}` for other skills.

## Invocation patterns

```bash
/runbook-documentation-gen runbook --incident=INC-2026-0315-01 --format=markdown
/runbook-documentation-gen adr --title="Adopt Istio" --status=proposed
/runbook-documentation-gen postmortem --incident=INC-2026-0314-22 --publish=confluence
/runbook-documentation-gen api-docs --spec=apis/user.yaml --output=docs/user.md
/runbook-documentation-gen sync --target=notion --path=docs/runbooks/
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `incident` | Incident ID for runbook/postmortem. | `INC-2026-0315-01` |
| `title` | Document title. | `Adopt Istio` |
| `status` | ADR status (`proposed|accepted|deprecated`). | `proposed` |
| `spec` | OpenAPI/Terraform spec path. | `apis/user.yaml` |
| `format` | Output format (`markdown|html`). | `markdown` |
| `target` | Sync destination (backstage, notion, confluence). | `confluence` |

## Output contract

```json
{
  "operationId": "DOC-2026-0315-01",
  "status": "success|failure",
  "docType": "runbook|adr|postmortem|api_ref|infra_doc|onboarding",
  "title": "PodCrashLoopBackOff Runbook",
  "filePath": "runbooks/podcrash.md",
  "wordCount": 1200,
  "qualityGatesPassed": true,
  "wikiSynced": true,
  "wikiUrl": "https://docs/platform/runbooks/podcrash",
  "aiInsights": {
    "riskScore": 0.28,
    "summary": "Runbook covers incident steps, escalation, and action items."
  },
  "decisionContext": "redis://memory-store/docs/DOC-2026-0315-01",
  "logs": "shared-context://memory-store/docs/DOC-2026-0315-01"
}
```

## World-class workflow templates

### Runbook generation
1. Extract timelines, commands, diagnostics, and escalations from incident logs or telemetry.
2. Structure content into the runbook template (symptoms, impact, diagnostics, remediation, rollback, owners).
3. Persist metadata, emit `runbook-created`, and store context for reruns.

### ADR creation
1. Capture context, drivers, options, decision, and consequences using MADR.
2. Notify stakeholders, publish to documentation stores, and annotate related tickets.
3. Emit `adr-created` and track follow-up action items.

### Reference doc & sync pipeline
1. Ingest OpenAPI/Terraform/observability specs plus diagrams.
2. Generate docs, validate quality gates (links, spell-check, policy alignment), and publish to Backstage/Confluence/Notion.
3. Emit `docs-synced` with diff metadata so orchestrators can audit updates.

### Postmortem delivery
1. Aggregate timeline, validation steps, impacted SLAs, and human actions from incidents.
2. Format a postmortem (markdown/HTML), include action items, owners, due dates, and preventive measures.
3. Emit `postmortem-ready` and notify follow-up systems (stakeholder comms, QA).

## AI intelligence highlights
- **AI Narrative** crafts coherent summaries and recommended actions aligned to severity and audience.
- **Intelligent Quality Control** checks templates for completeness, policy compliance, and readability, emitting alerts if thresholds fail.
- **Predictive Documentation Alerts** warn when docs drift from infrastructure manifests or incidents spike.

## Memory agent & dispatcher integration
- Persist metadata under `shared-context://memory-store/docs/{operationId}` with tags (`decisionId`, `docType`, `riskScore`).
- Emit events: `runbook-created`, `adr-created`, `postmortem-ready`, `docs-synced`, `policy-doc-gate`.
- React to dispatcher signals (`incident-ready`, `policy-risk`, `cost-anomaly`) to refresh documentation automatically.
- Tag entries with `decisionId`, `docType`, `riskScore`, `confidence`, `source`.

## Observability & telemetry
- Metrics: docs generated per interval, quality gate pass rate, summary sentiment drift.
- Logs: structured `log.event="docs.operation"` capturing `docType`, `operationId`, `status`.
- Dashboards: integrate `/runbook-documentation-gen metrics --format=prometheus` into SRE/OPS views.
- Alerts: quality gate failures, staleness beyond defined windows, LLM errors, sync failures.

## Failure handling & retries
- Retry generation pipelines up to 2× on transient errors (LLM timeouts, API rate limits) before handing off to humans.
- On repeated failure, emit `docs-failed`, escalate to `incident-triage-runbook`, and keep artifacts for the audit trail.
- Preserve generated outputs until downstream acknowledgments confirm consumption.

## Human gates
- Required when:
  1. Documentation publishes sensitive or strategic decisions (ADRs with enterprise impact).
  2. Runbooks propose destructive actions (e.g., mass restarts) or critical incident escalations.
  3. Dispatcher requests manual review after automation failures.
- Confirmation template matches the orchestrator standard:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/runbook-documentation-gen runbook --incident=INC-DRY --dry-run`.
- Unit tests: `backend/docs/` ensures templates render correctly and data joins function.
- Integration: `scripts/validate-docs-gen.sh` ingests data, generates docs, and syncs to Backstage.
- Regression: nightly `scripts/nightly-docs-smoke.sh` confirms generation, quality gates, and event emission.

## References
- Templates: `templates/runbook`, `templates/adr`.
- Scripts: `scripts/runbooks/`, `scripts/docs-sync/`.
- Diagrams: `assets/diagrams/`.

## Related skills
- `/incident-triage-runbook`: leverages runbooks/postmortems to shorten MTTR.
- `/stakeholder-comms-drafter`: consumes exec summaries and documentation.
- `/ai-agent-orchestration`: triggers documentation updates as part of composite workflows.

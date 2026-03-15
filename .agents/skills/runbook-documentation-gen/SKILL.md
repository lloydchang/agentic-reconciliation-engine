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

Automates creation and upkeep of operational runbooks, ADRs, postmortems, API docs, and onboarding guides using logs, incidents, infra state, and policies. Provides structured outputs, AI narratives, and shared-context for downstream automation.

## When to invoke
- Create or update runbooks for incidents or alerts.
- Generate ADRs from decisions or proposals.
- Compile documentation from OpenAPI/terraform/observability data.
- Sync docs to Backstage, Confluence, or Notion.
- Feed `incident-triage`, `stakeholder-comms`, or dispatcher follow-ups with narrative context.

## Capabilities
- Parse logs/incidents to build repeatable runbooks.
- Draft ADRs (MADR) and postmortems with timelines and action items.
- Pull OpenAPI/terraform metadata for reference docs.
- Publish to documentation stores (Backstage docs, Notion, Confluence).
- Shared context `shared-context://memory-store/docs/<operationId>`.

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
| `status` | ADR status. | `proposed` |
| `spec` | OpenAPI/terraform spec path. | `apis/user.yaml` |
| `format` | Output format (markdown/html). | `markdown` |
| `target` | Sync destination (backstage, notion). | `confluence` |

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
    "summary": "Runbook covers incident steps, escalation, and postmortem action items."
  },
  "decisionContext": "redis://memory-store/docs/DOC-2026-0315-01",
  "logs": "shared-context://memory-store/docs/DOC-2026-0315-01"
}
```

## World-class workflow templates

### Runbook generation from incidents
1. Extract timeline, commands, diagnostics from incident logs.
2. Format into runbook template (symptoms, impact, diagnostics, remediation, escalation).
3. Store runbook with metadata and emit `runbook-created`.

### ADR creation
1. Capture context, drivers, options, decision, consequences in MADR.
2. Publish to documentation store, notify stakeholders.
3. Emit `adr-created`.

### Documentation sync
1. Generate docs from OpenAPI, terraform state, diagrams.
2. Validate quality gates (links, spell-check).
3. Sync to Backstage/Confluence/Notion with update logs.
4. Emit `docs-synced`.

### Postmortem automation
1. Populate timeline from incident steps, metrics, SLO impact.
2. Gather action items, owners, due dates.
3. Produce postmortem report in Markdown/Notion and emit `postmortem-ready`.

## AI intelligence highlights
- **AI Narrative**: crafts coherent summaries and action recommendations.
- **Intelligent Quality Control**: checks templates for completeness, policy compliance, and readability.
- **Predictive Documentation Alerts**: notifies when docs stale vs infrastructure manifest.

## Memory agent & dispatcher integration
- Store doc metadata in `shared-context://memory-store/docs/<operationId>`.
- Emit events: `runbook-created`, `adr-created`, `postmortem-ready`, `docs-synced`.
- React to dispatcher signals (`incident-ready`, `policy-risk`) to update relevant documentation automatically.
- Tag entries with `decisionId`, `docType`, `riskScore`.

## Communication protocols
- Primary: CLI/LLM integration to parse logs/specs and generate Markdown/HTML.
- Secondary: Event bus for `docs-*` events.
- Fallback: JSON artifacts `artifact-store://docs/<operationId>.json`.

## Observability & telemetry
- Metrics: docs generated per period, quality gate pass rate, summary distributions.
- Logs: structured `log.event="docs.operation"` with `docType`, `operationId`.
- Dashboards: integrate `/runbook-documentation-gen metrics --format=prometheus`.
- Alerts: quality gate failures, outdated docs, LLM errors.

## Failure handling & retries
- Retry generation pipelines up to 2× on transient errors (LLM timeouts, API).
- On repeated failure escalate to `incident-triage-runbook` and log user context.
- Preserve generated artifacts until downstream ack.

## Human gates
- Required when:
 1. Documentation publishes sensitive strategic decisions (ADR with impact).
 2. Runbooks propose destructive actions or escalate critical incidents.
 3. Dispatcher requests manual review after automation failure.
- Use standard human gate template capturing impact/reversibility.

## Testing & validation
- Dry-run: `/runbook-documentation-gen runbook --incident=INC-DRY --dry-run`.
- Unit tests: `backend/docs/` ensures template rendering works.
- Integration: `scripts/validate-docs-gen.sh` pulls data, generates documents, syncs to Backstage.
- Regression: nightly `scripts/nightly-docs-smoke.sh` ensures generation + sync pipelines stay healthy.

## References
- Templates: `templates/runbook`, `templates/adr`.
- Scripts: `scripts/runbooks/`, `scripts/docs-sync/`.
- Diagrams: `assets/diagrams/`.

## Related skills
- `/incident-triage-runbook`: uses runbooks/postmortems.
- `/stakeholder-comms-drafter`: consumes exec summaries + docs.
- `/orchestrator`: triggers documentation updates as part of workflows.

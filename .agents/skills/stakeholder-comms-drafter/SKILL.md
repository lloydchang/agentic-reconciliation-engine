---
name: stakeholder-comms-drafter
description: >
  Draft tactical/executive incident, change, and risk communications with AI-guided narratives, structured outputs, and dispatcher context.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Stakeholder Communications Drafter — World-class Narrative Playbook

Creates incident alerts, resolution notes, change announcements, SLA breach reports, and executive summaries with audience-aware tone, AI insights, and dispatcher-wired context.

## When to invoke
- Incident notifications (Slack/Teams/email) for P1–P4 events.
- Resolution summaries, executive status updates, change announcements, or SLA breach notices.
- QBR/KPI reporting or risk escalations needing leadership attention.
- Dispatcher/memory agent events supplying KPI/incident metrics or risk signals.

## Capabilities
- **Audience-specific templates** for execs, engineering, operations, customers, and security.
- **AI risk scoring** to tailor tone, urgency, and call-to-action content.
- **Structured narrative composition** pulling from incidents, compliance, capacity, or telemetry data.
- **Shared-context propagation** via `shared-context://memory-store/comms/{operationId}` for downstream skills.
- **Human review gating**—messages are drafted but never auto-sent without approval.

## Invocation patterns

```bash
/stakeholder-comms-drafter incident --severity=P2 --audience=engineering --context=shared-context://memory-store/incident/INC-2026-0315-01
/stakeholder-comms-drafter resolution --incident=INC-2026-0315-01 --format=markdown
/stakeholder-comms-drafter exec --report=KPI-2026-0315-01 --audience=executive
/stakeholder-comms-drafter change --changeId=CR-2026-0315-01 --audience=ops
/stakeholder-comms-drafter sla-breach --tenant=tenant-42 --audience=customer
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `severity` | Incident severity (P1–P4). | `P2` |
| `audience` | Audience (`executive`, `engineering`, `ops`, `customer`, `security`). | `executive` |
| `incident` | Incident identifier for context. | `INC-2026-0315-01` |
| `report` | KPI/QBR identifier. | `KPI-2026-0315-01` |
| `changeId` | Change request ID. | `CR-2026-0315-01` |
| `tenant` | Tenant name for SLA breaches. | `tenant-42` |

## Output contract

```json
{
  "operationId": "COMM-2026-0315-01",
  "commType": "incident_update|resolution|executive_status|change_announcement|sla_breach|risk_escalation",
  "audience": "executive",
  "channel": "email",
  "subject": "string",
  "body": "string",
  "reviewRequired": true,
  "sent": false,
  "aiInsights": {
    "riskScore": 0.4,
    "summary": "Focus on uptime, deployments, and mitigation"
  },
  "decisionContext": "redis://memory-store/comms/COMM-2026-0315-01",
  "logs": "shared-context://memory-store/comms/COMM-2026-0315-01"
}
```

## World-class workflow templates

### Incident updates
1. Gather timeline, severity, impacted services, and remediation steps from incident context.
2. Compose Slack/Teams/email updates using templates keyed by severity/audience, including actions and expectations.
3. Emit `comm-drafted`, require human approval, then mark `sent` once confirmed.

### Resolution summaries
1. Summarize root cause, resolution steps, SLAs affected, and postmortem links.
2. Provide action items, owners, and next steps for follow-up.
3. Emit `comm-resolution` and link to postmortem artifacts.

### Executive status & risk notes
1. Combine KPI metrics, risk insights, and cost/incident context into succinct executive language.
2. Highlight recommended decisions, approvals, or escalations.
3. Emit `comm-exec` for dashboards or review cycles.

### Change announcements & SLA breach reports
1. Draft communications describing change scope, rollback strategy, or SLA impact.
2. Tailor technical detail level for operations vs external customers.
3. Emit `comm-change` or `comm-sla` events and await human gate before distribution.

## AI intelligence highlights
- **AI Risk Scoring** adjusts message urgency and tone using incident data, KPIs, and policy context.
- **Intelligent Narrative** distills technical metrics into concise bullet points (3–4 lines) per audience.
- **Predictive Channel Guidance** recommends Slack, email, or HTML summary based on severity and stakeholder preference.

## Memory agent & dispatcher integration
- Persist drafts at `shared-context://memory-store/comms/{operationId}` with tags (`decisionId`, `audience`, `riskScore`).
- Emit events: `comm-drafted`, `comm-ready`, `comm-escalation`, `comm-sent`.
- Subscribe to dispatcher signals (`incident-ready`, `policy-risk`, `cost-anomaly`) to trigger or update comms.
- Provide fallback artifacts via `artifact-store://comms/{operationId}.json` when systems are offline.

## Observability & telemetry
- Metrics: messages drafted per type, review time, send latency, manual overrides.
- Logs: structured `log.event="comm.operation"` with `commType`, `audience`, `decisionId`.
- Dashboards: include `/stakeholder-comms-drafter metrics --format=prometheus` for comm health.
- Alerts: communications delayed > threshold, riskScore > 0.85 without manual review.

## Failure handling & retries
- Retry data fetches up to 2× on incident/context fetching errors before surfacing issue.
- If template generation fails, fall back to simplified summary and notify on-call.
- Never auto-send; log `reviewRequired` and require human confirmation before marking `sent`.
- Preserve audit artifacts until follow-ups acknowledge consumption.

## Human gates
- Required when:
  1. Severity is critical or the update influences executive decisions.
  2. Communications mention strategic or sensitive data.
  3. Dispatcher requests manual review after repeated generation failures.
- Confirmation template aligns with the orchestrator standard:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/stakeholder-comms-drafter incident --severity=P3 --dry-run`.
- Unit tests: `backend/comms/` validates template rendering and AI narrative functions.
- Integration: `scripts/validate-stakeholder-comms.sh` simulates incidents, changes, and SLA breaches to verify outputs.
- Regression: nightly `scripts/nightly-comms-smoke.sh` ensures message generation, AI scoring, and logs stay stable.

## References
- Templates: `templates/communications/`.
- Scripts: `scripts/comms/`.
- Guidelines: `docs/COMMUNICATION_GUIDELINES.md`.

## Related skills
- `/incident-triage-runbook`: uses drafted updates for incidents and escalations.
- `/orchestrator`: composes communications into multi-skill workflows.
- `/policy-as-code`: feeds compliance or policy breach narratives into comm drafts.

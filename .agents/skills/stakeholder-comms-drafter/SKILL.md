---
name: stakeholder-comms-drafter
description: >
  Draft tactical and executive communications with AI-assisted narratives and formal structured output for incidents, reports, and notifications.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Stakeholder Communications Drafter — World-class Narrative Playbook

Creates incident updates, resolution summaries, change announcements, SLA notifications, risk escalations, and executive reports. Combines audience-specific tones, data pulls, AI-assisted summaries, and dispatcher integration.

## When to invoke
- Incident notifications (Slack/Teams/email) for P1–P4 events.
- Resolution notices, exec status updates, change announcements, or SLA breach communications.
- QBR reports or risk escalations requiring leadership attention.
- Incorporate KPI data/incident metrics from dispatcher events.

## Capabilities
- Audience-specific templates (exec, engineering, customers, security).
- AI risk scoring to tailor tone and highlight key facts.
- Compose structured communications from triggers.
- Shared context `shared-context://memory-store/comms/<operationId>`.
- Human review factor (must not auto-send).

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
| `audience` | Audience type (executive, engineering, ops, customer, security). | `executive` |
| `incident` | Incident identifier. | `INC-2026-0315-01` |
| `report` | KPI or QBR report linking. | `KPI-2026-0315-01` |
| `changeId` | Change request ID. | `CR-2026-0315-01` |
| `tenant` | Tenant name for SLA breach. | `tenant-42` |

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
1. Pull data from incident runbook/context (severity, impacted services, timeline).
2. Format Slack/Teams message with tone per severity/audience.
3. Emit `comm-drafted` event; human reviews before sending.

### Resolution summary
1. Summarize root cause, resolution steps, and SLAs.
2. Attach postmortem link, action items, next steps.
3. Emit `comm-resolution`.

### Executive status & risk notes
1. Combine KPI metrics, risk insights, cost items into high-level summary.
2. Provide decisions/recommendations for execs.
3. Emit `comm-exec`.

## AI intelligence highlights
- **AI Risk Scoring**: tailors message urgency/ tone via riskScore from incident data.
- **Intelligent Narrative**: distills complex metrics into readable bullet points with 3–4 lines.
- **Predictive Channel Suggestion**: determines best delivery medium (Slack vs email).

## Memory agent & dispatcher integration
- Persist communications under `shared-context://memory-store/comms/<operationId>`.
- Emit events: `comm-drafted`, `comm-ready`, `comm-escalation`.
- Subscribe to dispatcher alerts to auto-generate updates or risk escalations.
- Tag with `decisionId`, `audience`, `riskScore`.

## Communication protocols
- Primary: CLI/templating referencing incident DB/observability.
- Secondary: Event bus for `comm-*` events.
- Fallback: JSON artifact in `artifact-store://comms/<operationId>.json`.

## Observability & telemetry
- Metrics: comms drafted per type, review-to-send time, manual overrides.
- Logs: structured `log.event="comm.operation"`.
- Dashboards: integrate `/stakeholder-comms-drafter metrics --format=prometheus`.
- Alerts: comms delayed > threshold, unmanaged riskScore > 0.85.

## Failure handling & retries
- Retry data fetches up to 2×; log errors and escalate on persistent issues.
- If template generation fails, fallback to simplified message and notify on-call.
 - Do not auto-send until human confirms; log `reviewRequired`.

## Human gates
- Required when:
 1. Severity critical or impacts exec-level decisions.
 2. Communications mention sensitive data or strategic moves.
 3. Dispatcher requests manual approval after repeated generation failures.
- Use standard human gate confirmation template.

## Testing & validation
- Dry-run: `/stakeholder-comms-drafter incident --severity=P3 --dry-run`.
- Unit tests: `backend/comms/` ensures templates and AI narrative logic.
- Integration: `scripts/validate-stakeholder-comms.sh` simulates incidents, change events, and verifies outputs.
- Regression: nightly `scripts/nightly-comms-smoke.sh` ensures message generation, AI scoring, and logs stay stable.

## References
- Templates: `templates/communications/`.
- Scripts: `scripts/comms/`.
- Documentation: `docs/COMMUNICATION_GUIDELINES.md`.

## Related skills
- `/incident-triage-runbook`: needs messages for incidents.
- `/stakeholder-comms-drafter`: uses runbook outputs for clarity.
- `/workflow-management`: includes comm steps in workflows.

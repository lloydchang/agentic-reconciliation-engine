---
name: incident-summary
description: |
  Summarize incident contexts, status updates, and action items for stakeholders using AI to distill the essentials from runbooks and alerts.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Incident Summary — World-class Update Playbook

Produces concise incident updates with timelines, mitigations, impact statements, and next steps tailored to audiences.

## When to invoke
- To inform execs, customers, or downstream teams about ongoing incidents.
- When incidents have cleared and a summary of learnings is needed.
- Before stakeholder review meetings or postmortem sessions.
- Dispatcher events `incident-status`, `lesson-ready`.

## Capabilities
- **Audience-aware narratives** (exec, ops, customer) with tone adjustments.
- **Timeline generation** including alerts, runbook steps, and automation actions.
- **Human gate enforcement** ensures sensitive summaries reviewed.
- **Shared context** `shared-context://memory-store/incident-summary/{operationId}`.

## Invocation patterns
```bash
/incident-summary draft --incident=INC-2026-0315 --audience=exec
/incident-summary update --incident=INC-2026-0315 --status=resolved
/incident-summary follow-up --incident=INC-2026-0315 --action=monitor
/incident-summary controller --incident=INC-2026-0315 --format=markdown
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `incident` | Incident ID. | `INC-2026-0315` |
| `audience` | Exec/ops/customer. | `exec` |
| `status` | Current status. | `resolved` |
| `action` | Next step. | `monitor` |
| `format` | Output format. | `markdown` |

## Workflow templates
### Drafting updates
1. Pull telemetry, runbook actions, and automation steps.
2. Format summary with impact, mitigations, and time-series.
3. Command stub: `/incident-summary draft --incident=INC-2026-0315 --audience=exec`

### Status changes
1. Reflect new statuses, updates, human gate results.
2. Emit `incident-update` events.
3. Command stub: `/incident-summary update --incident=INC-2026-0315 --status=resolved`

### Follow-ups
1. List action items, owners, timelines.
2. Send notifications.
3. Command stub: `/incident-summary follow-up --incident=INC-2026-0315 --action=monitor`

### Controller exports
1. Provide markdown/HTML for dashboards.
2. Command stub: `/incident-summary controller --incident=INC-2026-0315 --format=markdown`

## AI intelligence
- **Summarization** condenses complex data.
- **Tone tuning** adapts for execs vs ops.

## Memory & dispatcher
- Events: `incident-summary`, `incident-update`.
- Store in shared context with `decisionId`, `audience`, `status`.

## Observability
- Metrics: summaries generated, review time.
- Logs: `log.event="incident.summary"`.

## Failure handling
- Retry data fetches.
- Save drafts until ack.

## Human gates
- Required for exec/customer audiences.

## Testing
- `/incident-summary draft --incident=test --audience=exec --dry-run`

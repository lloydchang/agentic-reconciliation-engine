---
name: incident-history
description: |
  Collect and summarize incident timelines, remediation steps, and outcomes so teams can learn, improve runbooks, and track recurring issues with AI analytics.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Incident History — World-class Learnings Playbook

Stores incidents, resolutions, and lessons learned, then surfaces patterns, trends, and action items for SRE/ops teams.

## When to invoke
- After incidents resolve and postmortems need updates.
- When root cause analysis is requested across recurring alerts.
- During reviews of MTTR, repeat issues, or compliance reporting.
- Dispatcher signals `incident-resolved`, `postmortem-ready`, or `incident-trend`.

## Capabilities
- **Timeline aggregation** merges alerts, runbook steps, and tool output.
- **Pattern detection** surfaces recurring services, dependencies, and action owners.
- **Lesson extraction** suggests follow-through actions and runbook updates.
- **Shared artifacts** stored at `shared-context://memory-store/incident-history/{operationId}`.
- **Evidence tagging** ensures auditors can see incident context and actions.

## Invocation patterns
```bash
/incident-history record --incident=INC-2026-0315 --status=resolved
/incident-history trend --window=30d --service=payments
/incident-history summarize --owner=team-sre --format=markdown
/incident-history review --incident=INC-2026-0302
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `incident` | Incident identifier. | `INC-2026-0315` |
| `status` | Incident status. | `resolved` |
| `window` | Lookback window. | `30d` |
| `service` | Service/tenant name. | `payments` |
| `owner` | Action owner/team. | `team-sre` |
| `format` | Output format. | `markdown` |

## Output contract
```json
{
  "operationId": "IH-2026-0315-01",
  "incident": "INC-2026-0315",
  "status": "recorded",
  "timeline": [...],
  "trends": [...],
  "lessons": [...],
  "logs": "shared-context://memory-store/incident-history/IH-2026-0315-01"
}
```

## World-class workflow templates

### Incident recording
1. Collect alerts, runbook actions, and operator notes.
2. Emit `incident-recorded` and store timeline.
3. Command stub: `/incident-history record --incident=INC-2026-0315 --status=resolved`

### Trend & recurrence analysis
1. Scan incidents over the window, group by service/dependency.
2. Emit `incident-trends` and tag repeat offenders.
3. Command stub: `/incident-history trend --window=30d --service=payments`

### Summary & lessons
1. Generate summaries with action items, owner assignments, and timeline.
2. Share drafts for communication or documentation.
3. Command stub: `/incident-history summarize --owner=team-sre --format=markdown`

### Review & feedback
1. Allow SREs to review and add context before closing arcs.
2. Emit `incident-reviewed` with approval metadata.
3. Command stub: `/incident-history review --incident=INC-2026-0302`

## AI intelligence highlights
- **Pattern detection** spots recurring nodes, services, or policies.
- **Lessons mined** highlight actions that reduce MTTR.
- **Confidence scoring** helps prioritize follow-up operations.

## Memory agent & dispatcher integration
- Persist artifacts under `shared-context://memory-store/incident-history/{operationId}`.
- Emit events: `incident-recorded`, `incident-trends`, `incident-reviewed`.
- Subscribe to `incident-resolved`, `postmortem-ready`, `policy-risk`.

## Observability & telemetry
- Metrics: incident recurrence rate, lesson uptake, review lag.
- Logs: `log.event="incident.history"` with `incident`, `status`, `timeline`.
- Alerts: incidents lacking lessons >3 days.

## Failure handling & retries
- Retry fetches, log partial data, escalate if data missing.
- Keep histories for 365 days for compliance.

## Human gates
- Required when:
  1. Reviews touch executive/compliance-sensitive incidents.
  2. Lessons propose major changes without approvals.

## Testing & validation
- Dry-run: `/incident-history record --incident=INC-DRY-01 --status=resolved --dry-run`

## Related skills
- `/incident-triage-runbook`, `/doc-generator`, `/runbook-documentation-gen`

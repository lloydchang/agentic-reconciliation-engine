---
name: change-management
description: >
  Automate change governance, CAB coordination, freeze enforcement, and risk scoring with dispatcher-grade outputs.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Change Management — World-class Governance Playbook

Manages change requests end-to-end (risk scoring, freeze checks, approvals, execution, reporting) with AI insights and dispatcher integration.

## When to invoke
- Raise or review change requests for deployments, infrastructure updates, or emergency fixes.
- Enforce change freeze windows and exception gating.
- Coordinate CAB approvals, human gates, and execution playbooks.
- Produce calendars, success reports, or audits for compliance.
- React to dispatcher signals (`policy-risk`, `incident-ready`, `capacity-alert`) requiring governance adjustments.

## Capabilities
- **AI risk assessment** evaluating env impact, tenants, rollback complexity, and past failures.
- **Freeze enforcement** with exception handling for emergencies.
- **CAB automation** (standard, normal, major, emergency) plus human gate orchestration.
- **Shared-context propagation** via `shared-context://memory-store/change/{operationId}` for downstream skills.
- **Structured reporting** for calendars, success rates, and compliance evidence.

## Invocation patterns

```bash
/change-management request --title="DB schema update" --environments=prod --category=database
/change-management score --changeId=CR-2026-0315-01 --change=payload.json
/change-management calendar --window=7d --format=json
/change-management freeze-check --datetime=2026-03-20T22:00:00Z --environment=prod
/change-management report --window=90d --format=md
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `changeId` | Change request identifier. | `CR-2026-0315-01` |
| `title` | Short summary of change. | `DB schema update` |
| `environments` | Target envs (`prod|staging`). | `prod` |
| `category` | Change category (`database|infra`). | `database` |
| `datetime` | Proposed start time (RFC3339). | `2026-03-20T22:00:00Z` |
| `window` | Reporting or calendar window. | `7d` |

## Output contract

```json
{
  "operationId": "CM-2026-0315-01",
  "status": "draft|approved|implemented|failed",
  "changeId": "CR-2026-0315-01",
  "changeType": "standard|normal|major|emergency",
  "riskScore": 64,
  "reasons": ["Production change +30", "No rollback plan +20", "Category: database +25"],
  "freeze": { "frozen": false, "freezeName": null },
  "approvals": [ { "role": "CAB", "status": "pending" } ],
  "decisionContext": "redis://memory-store/change/CM-2026-0315-01",
  "logs": "shared-context://memory-store/change/CM-2026-0315-01"
}
```

## World-class workflow templates

### AI risk scoring & automation
1. Evaluate inputs (envs, tenants, rollback plan, change window).
2. Compute riskScore using weighted heuristics and determine change type.
3. Emit `change-scored` with gating recommendations and required approvals.

### Freeze enforcement
1. Check proposed datetime against freeze calendar; block if frozen unless emergency.
2. Notify requester/human gate about freeze impact or exception approvals.
3. Log freeze status for audit and dispatcher review.

### CAB coordination & execution
1. Post change request into ServiceNow/CAB feed and notify channels.
2. Track approvals, escalate high-risk changes (riskScore ≥ 70) to additional reviewers.
3. Upon approval trigger execution workflows, monitor success/failure, and emit `change-executed`/`change-failed` events.

### Reporting & audit
1. Generate change calendars (weekly/monthly) with statuses, success rates, and risk trends.
2. Produce compliance-ready reports for auditors and execs.
3. Emit `change-calendar-ready` and store artifacts for downstream consumption.

## AI intelligence highlights
- **AI risk assessment** balances environment, category, tenant impact, and rollback plans to produce riskScore.
- **Intelligent recommendations** propose approval paths, freeze exceptions, and pre-change actions (backups, alerts).
- **Predictive freeze alerts** warn when changes approach frozen windows or accumulate high risk.

## Memory agent & dispatcher integration
- Write context to `shared-context://memory-store/change/{operationId}` possibly consumed by incident, cost, or policy skills.
- Emit events: `change-scored`, `change-approved`, `change-executed`, `change-failed`, `change-calendar-ready`.
- Respond to dispatcher signals (`policy-risk`, `incident-ready`) by prioritizing approvals or invoking emergency procedures.
- Tag telemetry with `decisionId`, `changeId`, `tier`, `riskScore`, `approvals`.

## Communication protocols
- Primary: CLI/scripts interfacing with ServiceNow, Slack, email, or GitHub triggers.
- Secondary: Event bus for `change-*` events consumed by orchestrator, incident, or policy skills.
- Fallback: JSON artifacts stored at `artifact-store://change/{operationId}.json` for pull-based review.

## Observability & telemetry
- Metrics: change volume, riskScore distribution, freeze violations, change success/failure rates.
- Logs: structured `log.event="change.lifecycle"` capturing status, reason, decisionId.
- Dashboards: integrate `/change-management metrics --format=prometheus` for governance views.
- Alerts: riskScore ≥ 85, freeze violations, emergency changes > threshold.

## Failure handling & retries
- Retry automation steps (ticket creation, notifications) up to 2× on transient failures.
- On persistent failure route to manual incident runbook and log `change-failed`.
- Preserve artifacts/logs until downstream acknowledgments confirm completion.

## Human gates
- Required when:
  1. RiskScore ≥ 70 or change impacts production-critical tenants.
  2. Emergency changes alter policies or controls.
  3. Dispatcher requests manual review after retries/failures.
- Confirmation template matches orchestrator standard:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/change-management request --dry-run`.
- Unit tests: `backend/change/` verifies scoring and freeze detection logic.
- Integration: `scripts/validate-change-management.sh` exercises lifecycle (score → approval → execution → reporting).
- Regression: nightly `scripts/nightly-change-smoke.sh` ensures calendars, approvals, and alerts remain healthy.

## References
- Freeze definitions: `docs/CHANGE_FREEZE.md`.
- Templates: `templates/change-request.md`.
- Scripts: `scripts/change-management/`.

## Related skills
- `/ai-agent-orchestration`: composes change-rich workflows.
- `/incident-triage-runbook`: handles emergency change incidents.
- `/workflow-management`: monitors change execution pipelines.

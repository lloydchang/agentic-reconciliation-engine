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

Manages change requests from risk scoring through CAB approvals, freeze checks, execution, and post-change auditing. Integrates AI risk signals, structured outputs, and dispatcher events to automate approvals while keeping humans in control for high-impact changes.

## When to invoke
- Raise or evaluate change requests for deployments, infra updates, configuration changes, or emergencies.
- Score risk, enforce change freeze windows, coordinate CAB/approvals, or respond to rollback/retry need.
- Generate weekly change calendars, success rate reports, or CAB briefings.
- React to dispatcher events (policy-risk, incident-ready, capacity alerts) requiring governance updates.

## Capabilities
- AI risk scoring (production impact, tenant blast radius, rollback complexity).
- Change freeze enforcement with exceptions.
- CAB automation + playbooks (standard/normal/major/emergency).
- Human gate guidance for high-risk changes.
- Shared context at `shared-context://memory-store/change/<operationId>` for downstream workflows.

## Invocation patterns

```bash
/change-management request --title="DB schema update" --environments=prod --category=database
/change-management score --changeId=CR-2026-0315-01 --change=change-payload.json
/change-management calendar --window=7d --format=json
/change-management freeze-check --datetime=2026-03-20T22:00:00Z --environment=prod
/change-management report --window=90d --format=md
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `changeId` | Change request identifier. | `CR-2026-0315-01` |
| `title` | Short description. | `DB schema update` |
| `environments` | Target envs (prod/staging). | `prod` |
| `category` | Change category (database, infra). | `database` |
| `datetime` | Proposed change start. | `2026-03-20T22:00:00Z` |
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
  "freeze": {
    "frozen": false,
    "freezeName": null
  },
  "approvals": [
    { "role": "CAB", "status": "pending" }
  ],
  "decisionContext": "redis://memory-store/change/CM-2026-0315-01",
  "logs": "shared-context://memory-store/change/CM-2026-0315-01"
}
```

## World-class workflow templates

### AI risk scoring & automation
1. Evaluate inputs (environment, tenants, category, rollback plan, change window).
2. Compute riskScore via weighted heuristics (prod impact, tenant count, category severity).
3. Determine change type (standard/normal/major/emergency) and approval needs.
4. Emit `change-scored` event with context.

### Freeze enforcement
1. Check proposed datetime against freeze calendar.
2. Block changes if freeze active unless emergency with approvals.
3. Notify requester/human gate about freeze status.

### CAB coordination & execution
1. Post change request into ServiceNow/Change Calendar and notify channels.
2. Track approvals, escalate when riskScore high.
3. On approval, execute change workflow; monitor for success/failure.
4. Emit `change-executed` or `change-failed` events.

### Reporting & audit
1. Build weekly calendars with status, sweeps, success rates.
2. Provide change success rate reports (deployments vs failures).
3. Store artifacts for compliance and emit `change-calendar-ready`.

## AI intelligence highlights
- **AI Risk Assessment**: weighs environment, category, rollback, and past failures to produce riskScore.
- **Intelligent Recommendations**: suggests approval path and pre-change actions (backups, alerts).
- **Predictive Freeze Alerts**: warns when changes scheduled near frozen periods or high risk.

## Memory agent & dispatcher integration
- Write context to `shared-context://memory-store/change/<operationId>`.
- Emit events: `change-scored`, `change-approved`, `change-executed`, `change-failed`.
- Respond to dispatcher signals (`policy-risk`, `incident-ready`) by adjusting approvals or invoking emergency processes.
- Tag records with `decisionId`, `changeId`, `tier`, `riskScore`.

## Communication protocols
- Primary: CLI/HTTP scripts interacting with ServiceNow, Slack, git/CI triggers.
- Secondary: Event bus for `change-*` events.
- Fallback: JSON artifacts at `artifact-store://change/<operationId>.json`.

## Observability & telemetry
- Metrics: change count, risk score distribution, freeze violations, change success rate.
- Logs: structured `log.event="change.lifecycle"` capturing status, reason, decisionId.
- Dashboards: integrate `/change-management metrics --format=prometheus`.
- Alerts: riskScore ≥ 85, freeze violations, emergency changes > threshold.

## Failure handling & retries
- Retry automation steps (posting to CAS, notifying CAB) up to 2× on transient failures.
- On repeated fail, fall back to manual process via incident-runbook and log the failure.
- Keep artifacts/logs until downstream ack for audits.

## Human gates
- Required when:
 1. RiskScore ≥ 70 or change impacts production-critical tenants.
 2. Emergency changes altering policies or controls.
 3. Dispatcher requests manual review after retries/failures.
- Use the standard confirmation template capturing impact and reversibility.

## Testing & validation
- Dry-run: `/change-management request --dry-run`.
- Unit tests: `backend/change/` ensures scoring logic and freeze detection.
- Integration: `scripts/validate-change-management.sh` runs lifecycle (score → approval → execution).
- Regression: nightly `scripts/nightly-change-smoke.sh` ensures calendars, approval statuses, and alerts stay healthy.

## References
- Freeze definitions: `docs/CHANGE_FREEZE.md`.
- Templates: `templates/change-request.md`.
- Scripts: `scripts/change-management/`.

## Related skills
- `/ai-agent-orchestration`: orchestrates change-related workflows.
- `/incident-triage-runbook`: handles emergency change incidents.
- `/workflow-management`: monitors change execution pipelines.

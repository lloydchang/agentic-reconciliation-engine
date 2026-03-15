---
name: release-manager
description: |
  Coordinate releases across clusters, tenants, and services by validating readiness gates, preparing stakeholders, and tracking execution state.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Release Manager — World-class Coordination Playbook

Aligns release plans, safety checks, human approvals, and stakeholder communications to execute reliable launches.

## When to invoke
- Rolling out major releases across tenants or regions.
- Post-deployment to gather status, incidents, and feedback.
- When timelines change and coordination updates are needed.
- Dispatcher/memory agents emit `release-plan`, `release-check`, or `post-release`.

## Capabilities
- **Readiness orchestration** landing coordination, approvals, and telemetry checks.
- **Gate enforcement** verifying smoke tests, policy compliance, and incident readiness.
- **Stakeholder alerts** prepping execs, customers, and SREs with status.
- **Post-release reviews** summarizing outcomes and action items.
- **Shared context** at `shared-context://memory-store/release-manager/{operationId}`.

## Invocation patterns
```bash
/release-manager plan --release=Q2-2026 --region=multi
/release-manager approve --stage=canary --owner=team-sre
/release-manager status --release=Q2-2026
/release-manager wrapup --release=Q2-2026 --summary=json
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `release` | Release identifier. | `Q2-2026` |
| `region` | Region scope. | `multi` |
| `stage` | Release stage. | `canary` |
| `owner` | Approver/team. | `team-sre` |
| `summary` | Summary format. | `json` |

## Output contract
```json
{
  "operationId": "RL-2026-0315-01",
  "release": "Q2-2026",
  "status": "planned|executing|completed",
  "gates": ["canary", "prod"],
  "stakeholders": ["exec", "ops"],
  "logs": "shared-context://memory-store/release-manager/RL-2026-0315-01"
}
```

## World-class workflow templates

### Release planning
1. Collect scope, stakeholders, dependencies, and risk.
2. Emit `release-planned` with details.
3. Command stub: `/release-manager plan --release=Q2-2026 --region=multi`

### Gate approval
1. Aggregate telemetry before promoting to next stage.
2. Require approvals via `human gate` for high-risk moves.
3. Command stub: `/release-manager approve --stage=canary --owner=team-sre`

### Status tracking
1. Monitor pipelines, deployments, incidents, metrics.
2. Emit `release-status` and notify STAKE holders.
3. Command stub: `/release-manager status --release=Q2-2026`

### Wrap-up & review
1. Summarize outcomes, issues, and follow-ups.
2. Emit `release-wrapup` and archive documents.
3. Command stub: `/release-manager wrapup --release=Q2-2026 --summary=json`

## AI intelligence highlights
- **Risk-aware coordination** balances incident history, policies, and schedule.
- **Stakeholder-aware summaries** align tone for exec vs ops.

## Memory/dispatcher
- Events: `release-planned`, `release-status`, `release-wrapup`

## Observability & telemetry
- Metrics: release progress, gate durations, stakeholder responses.

## Human gates
- Required for production launch or exec summaries.

## Testing
- Dry-run statuses and wrap-ups.

## References
- Scripts: `scripts/release-manager/`.

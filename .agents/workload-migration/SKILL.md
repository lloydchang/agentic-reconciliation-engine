---
name: workload-migration
description: >
  Plan and execute workload migrations (cloud-to-cloud, region, tenant, database) with AI risk scoring and dispatcher-aware orchestration.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Workload Migration — World-class Migration Playbook

Manages assessment, planning, execution, validation, cutover, and decommissioning of workload migrations (blue-green, parallel run, tenant, DB) with rollback safety and compliance tracking.

## When to invoke
- Move workloads across clusters, clouds, or regions.
- Upgrade clusters or databases requiring data migration.
- Clone tenants into new environments for scale or compliance.
- Respond to incidents or policies demanding migrations.

## Capabilities
- **Assessment & dependency mapping** for source resources.
- **Migration planning** with rollback, cutover, and validation steps.
- **Execution orchestration** (data copy, failover, DNS, autoscalers).
- **Validation & reporting** (data parity, performance, health) plus decommission.
- **Shared-context propagation** via `shared-context://memory-store/migration/{operationId}`.

## Invocation patterns

```bash
/workload-migration plan --tenant=t-acme-prod --source=aks-old --target=aks-new
/workload-migration execute --migrationId=MIG-2026-0315-01 --phase=execute
/workload-migration validate --migrationId=MIG-2026-0315-01 --type=dataparity
/workload-migration cutover --migrationId=MIG-2026-0315-01 --strategy=blue-green
/workload-migration report --migrationId=MIG-2026-0315-01
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `tenant` | Tenant/workload identifier. | `t-acme-prod` |
| `source` | Source cluster/region. | `eastus` |
| `target` | Target cluster/region. | `westeurope` |
| `migrationId` | Migration tracking ID. | `MIG-2026-0315-01` |
| `phase` | `assess|plan|execute|validate|cutover|decommission`. | `execute` |
| `strategy` | Pattern (`blue-green|parallel|rolling`). | `blue-green` |

## Output contract

```json
{
  "migrationId": "MIG-2026-0315-01",
  "tenant": "t-acme-prod",
  "source": { "region": "eastus", "cluster": "aks-old" },
  "target": { "region": "westeurope", "cluster": "aks-new" },
  "phase": "execute",
  "status": "success|in_progress|blocked|rolled_back",
  "strategy": "blue-green",
  "riskScore": 0.48,
  "events": [ { "name": "migration-plan-approved", "timestamp": "2026-03-15T08:12:00Z" } ],
  "decisionContext": "redis://memory-store/migration/MIG-2026-0315-01",
  "logs": "shared-context://memory-store/migration/MIG-2026-0315-01"
}
```

## World-class workflow templates

### Assessment & planning
1. Inventory source resources, data sizes, dependencies, and compliance knobs.
2. Generate plan with backups, cutover steps, verification, and rollback.
3. Score risk, schedule gating, and emit `migration-plan-created`.

### Execution & validation
1. Provision target environment, import data (CDC/snapshots), and configure workloads.
2. Run smoke tests, monitor autoscalers, and validate data parity/performance.
3. Emit `migration-executed` and `migration-validated` events.

### Cutover & decommission
1. Shift traffic progressively (10→50→100%) with guard loops tied to metrics.
2. Auto-rollback when thresholds (error rate, latency) breach.
3. Decommission source infrastructure after exit checks, emit `migration-completed`.

## AI intelligence highlights
- **Risk scoring** fuses blast radius, data volume, tenant criticality to gauge hazard.
- **Predictive validation** foresees parity/performance gaps from telemetry.
- **Intelligent rollback gating** advises when to pause or revert.

## Memory agent & dispatcher integration
- Persist metadata under `shared-context://memory-store/migration/{operationId}`.
- Emit events: `migration-plan`, `migration-executed`, `migration-validated`, `migration-cutover`, `migration-complete`.
- Dispatcher triggers (`incident-ready`, `policy-risk`) automatically extend support or rollback.
- Tag context with `decisionId`, `tenant`, `strategy`, `riskScore`.

## Observability & telemetry
- Metrics: migrations run, success/fail rates, rollback counts, riskScore.
- Logs: structured `log.event="migration.phase"` with `phase`, `migrationId`.
- Dashboards: integrate `/workload-migration metrics --format=prometheus`.
- Alerts: cutover delays, rollback frequency, parity failures.

## Failure handling & retries
- Retry operations up to 2× for transient cloud API glitches; escalate after.
- Auto abort when SLO thresholds breach; emit `migration-rollback`.
- Retain artifacts/logs until downstream ack ensures compliance.

## Human gates
- Required when:
  1. Production tenants or mission-critical services are involved.
  2. RiskScore ≥ 0.8 or cross-cloud migrations.
  3. Dispatcher requests manual review after anomalies.
- Use standard confirmation template capturing impact/reversibility.

## Testing & validation
- Dry-run: `/workload-migration plan --tenant=TL-DRY --dry-run`.
- Unit tests: `backend/migration/` ensures planning/validation logic.
- Integration: `scripts/validate-migration.sh` runs plan → execute → validate flows.
- Regression: nightly `scripts/nightly-migration-smoke.sh` ensures metrics and alerts stay stable.

## References
- Scripts: `scripts/migration/`.
- Templates: `templates/migration-plan.md`.
- Docs: `docs/MIGRATION_GUIDE.md`.

## Related skills
- `/tenant-lifecycle-manager`: orchestrates tenant moves.
- `/incident-triage-runbook`: handles migration failures.
- `/ai-agent-orchestration`: sequences migrations within broader workflows.

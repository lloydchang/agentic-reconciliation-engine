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

Manages assessment, planning, execution, validation, cutover, and decommission of workload migrations. Supports blue-green, parallel run, cross-cloud, database, and tenant migrations with rollback safety and compliance tracking.

## When to invoke
- Move workloads across clusters/regions/clouds.
- Upgrade clusters or databases with data migration.
- Clone or scale tenants to new environments.
- Respond to incidents or policies requiring migrations.

## Capabilities
- Resource/tenant assessment and dependency mapping.
- Migration plan generation with rollbacks and checks.
- Execution orchestration (data copy, cutover, DNS shifts).
- Validation (data parity, health, performance) and decommission flows.
- Shared context `shared-context://memory-store/migration/<operationId>`.

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
| `tenant` | Tenant/ workload identifier. | `t-acme-prod` |
| `source` | Source cluster/region. | `eastus` |
| `target` | Target cluster/region. | `westeurope` |
| `migrationId` | Migration tracking ID. | `MIG-2026-0315-01` |
| `phase` | Migration phase. | `assess|plan|execute|validate|cutover|decommission` |
| `strategy` | Pattern (blue-green, parallel, rolling). | `blue-green` |

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
  "events": [
    { "name": "migration-plan-approved", "timestamp": "2026-03-15T08:12:00Z" }
  ],
  "decisionContext": "redis://memory-store/migration/MIG-2026-0315-01",
  "logs": "shared-context://memory-store/migration/MIG-2026-0315-01"
}
```

## World-class workflow templates

### Assessment & planning
1. Inventory source resources, DB sizes, dependencies.
2. Generate plan (steps, backups, DNS, monitoring) with rollback.
3. Score risk and schedule gating (human gates on production).
4. Emit `migration-plan-created`.

### Execution & validation
1. Provision target environment and import data (CDC, snapshots).
2. Apply workloads, run smoke tests, monitor autoscalers.
3. Validate data parity, performance, health.
4. Emit `migration-executed`, `data-validated`.

### Cutover & decommission
1. Shift traffic progressively (10→50→100) with guard loops.
2. Monitor error budgets; auto-rollback if thresholds exceeded.
3. Decommission source after monitoring; emit `migration-completed`.

## AI intelligence highlights
- **Risk scoring**: uses blast radius, data volume, tenant criticality to compute riskScore.
- **Predictive validation**: forecasts parity and performance issues from baseline metrics.
- **Intelligent rollback gating**: suggestions for when to pause or revert.

## Memory agent & dispatcher integration
- Save migration metadata at `shared-context://memory-store/migration/<operationId>`.
- Emit events: `migration-plan`, `migration-executed`, `migration-validated`, `migration-cutover`.
- Dispatcher can trigger follow-up workflows (incident, compliance, comms).
- Tag entries with `decisionId`, `tenant`, `strategy`, `riskScore`.

## Communication protocols
- Primary: CLI/scripts for terraform/az/gcloud/kubectl operations.
- Secondary: Event bus for `migration-*` events.
- Fallback: JSON artifacts at `artifact-store://migration/<operationId>.json`.

## Observability & telemetry
- Metrics: migrations executed, success rate, rollback counts, riskScore.
- Logs: structured `log.event="migration.phase"` with `phase`, `migrationId`.
- Dashboards: integrate `/workload-migration metrics --format=prometheus`.
- Alerts: cutover delays, rollback frequency, parity failures.

## Failure handling & retries
- Retry operations up to 2× for transient cloud errors; escalate on persistent failure.
- Auto abort if SLO thresholds (error rate, latency) breached during cutover.
- Keep artifacts/logs for audit until downstream ack.

## Human gates
- Required when:
 1. Production tenants impacted or downtime > 0.
 2. RiskScore ≥ 0.8 or cross-cloud migration.
 3. Dispatcher requests review after anomalies.
- Use standard template capturing impact/reversibility.

## Testing & validation
- Dry-run: `/workload-migration plan --tenant=TL-DRY --dry-run`.
- Unit tests: `backend/migration/` ensures planner/scorch logic.
- Integration: `scripts/validate-migration.sh` executes plan → execution → validation flows.
- Regression: nightly `scripts/nightly-migration-smoke.sh` ensures metrics/alerts remain stable.

## References
- Scripts: `scripts/migration/`.
- Templates: `templates/migration-plan.md`.
- Documentation: `docs/MIGRATION_GUIDE.md`.

## Related skills
- `/tenant-lifecycle-manager`: uses migration steps for tenant moves.
- `/incident-triage-runbook`: handles migration failures.
- `/ai-agent-orchestration`: sequences migration workflows across other skills.

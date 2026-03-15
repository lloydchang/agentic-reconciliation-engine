---
name: database-operations
description: >
  Provide AI-assisted database lifecycle operations (provision, backup, scale, failover, tune, upgrade) across managed cloud databases with telemetry and dispatcher signals.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Database Operations — World-class Data Platform Playbook

Manages provisioning, high availability, backups, scaling, failovers, tuning, and upgrades for managed databases (Azure PostgreSQL/SQL, MongoDB, Redis) with AI-driven risk scoring, telemetry, and shared-context outputs. Use this skill for any lifecycle operation or when dispatchers signal incidents/policy risk requiring database action.

## When to invoke
- Provision or decommission managed databases per tenant.
- Scale compute/storage or adjust connection parameters.
- Execute backups, restores, failover, upgrade, or HA validation.
- Perform diagnostics, slow query analysis, or replication checks.
- Respond to dispatcher events (`incident-ready`, `policy-risk`, `capacity-alert`) that implicate databases.

## Capabilities
- Multi-cloud database provisioning and scaling with tiered sizing guidelines.
- AI risk scoring for destructive operations (failover, restore, upgrade).
- Automated backup/restore management and failover drills.
- Performance diagnostics (slow queries, bloat, replication lag) with remediation hints.
- Shared context at `shared-context://memory-store/db/<operationId>` for other skills.

## Invocation patterns

```bash
/database-operations provision --engine=postgres --tenant=tenant-42 --tier=enterprise --region=eastus
/database-operations backup --tenant=tenant-42 --type=manual --retention=35
/database-operations failover --tenant=tenant-42 --humanGate=true
/database-operations scale --tenant=tenant-42 --cpu=8 --storage=512
/database-operations diagnose --tenant=tenant-42 --target=slow_queries
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `engine` | Database engine (`postgres|sql|mongodb|redis`). | `postgres` |
| `tenant` | Tenant identifier. | `tenant-42` |
| `tier` | SLA tier (starter/business/enterprise). | `enterprise` |
| `region` | Cloud region. | `eastus` |
| `operation` | Lifecycle step (provision, backup, failover, upgrade). | `failover` |
| `humanGate` | Whether human approval needed for operation. | `true` |

## Output contract

```json
{
  "operationId": "DB-2026-0315-01",
  "status": "success|failure|in_progress",
  "operation": "provision|backup|restore|scale|failover|diagnose|upgrade",
  "tenant": "tenant-42",
  "engine": "postgres",
  "riskScore": 0.33,
  "haState": "Healthy",
  "metrics": {
    "storageUsedPct": 63,
    "cpuUsedPct": 54,
    "replicationLagSeconds": 2
  },
  "issues": [],
  "events": [
    {
      "name": "backup-completed",
      "timestamp": "2026-03-15T08:12:00Z"
    }
  ],
  "logs": "shared-context://memory-store/db/DB-2026-0315-01",
  "decisionContext": "redis://memory-store/db/DB-2026-0315-01"
}
```

## World-class workflow templates

### Provision & HA hardening
1. Provision server (Azure PostgreSQL Flexible, Azure SQL, MongoDB, Redis) with specified tier and HA settings.
2. Configure geo-redundant backups, private endpoints, and tags.
3. Emit `db-provisioned` event with connection info stored in shared context.

### Backup/restore/failover automation
1. Trigger manual/automated backups and retention plan.
2. Restore to point-in-time, measure RPO, log results.
3. Perform failovers for DR or testing with human gate when impacting production.
4. Emit `db-backup`, `db-restore`, `db-failover` events for dispatchers.

### Scaling & tuning
1. Adjust compute/storage (SKU, memory, storage size) per demand.
2. Tune connection parameters, apply recommended performance configurations.
3. Log scaling actions and emit `db-scaled`.

### Diagnostics & upgrades
1. Run slow query analysis, log bloat, high replication lag checks.
2. Upgrade engine version with risk scoring and pre/post validation.
3. Emit `db-upgrade` event and update shared context for downstream skills.

## AI intelligence highlights
- **AI Risk Scoring**: assesses failover/restore/upgrade risk based on change size, tenant impact, historical reliability.
- **Intelligent Scheduling**: prioritizes operations based on capacity alerts and policy context.
- **Predictive Diagnostics**: flags slow queries, replication lags, storage pressure before thresholds breach.
- **Automated Remediation Suggestions**: recommends index tuning, scaling actions, or configuration changes.

## Memory agent & dispatcher integration
- Persist operations under `shared-context://memory-store/db/<operationId>` for other skills (incident, policy, capacity).
- Emit dispatcher events: `db-backup`, `db-restore`, `db-failover`, `db-diagnostics`, `db-risk`.
- Listen for dispatcher signals (`capacity-alert`, `incident-ready`) to initiate scaling or failovers.
- Attach metadata (`decisionId`, `tenant`, `riskScore`, `engine`, `operation`).

## Communication protocols
- Primary: cloud CLIs (az postgres/sql/cosmos, gcloud, aws) and `kubectl` for connectivity; outputs parseable JSON.
- Secondary: Event bus for `db-*` events consumed by dispatcher & skills.
- Fallback: Persist JSON artifacts to `artifact-store://db/<operationId>.json`.

## Observability & telemetry
- Metrics: provisioning count, failover duration, backup success rate, diagnostics frequency, riskScore distribution.
- Logs: structured `log.event="db.operation"` with `operation`, `tenant`, `decisionId`.
- Dashboards: integrate `/database-operations metrics --format=prometheus` onto platform dashboards.
- Alerts: riskScore ≥ 0.85, HA state degraded, replication lag > threshold, backup failure rate > 5%.

## Failure handling & retries
- Retry destructive operations (scale, failover, restore) up to 2× with exponential backoff on transient API errors.
- On failure, log context, emit `db-operation-failed`, escalate to `incident-triage-runbook`.
- Preserve artifacts/logs for audit; do not delete shared-context until ack.

## Human gates
- Required when:
 1. RiskScore ≥ 0.9, or operations impact production-critical data.
 2. Failover/restore involves >20 tenants or cross-region DNS changes.
 3. Dispatcher requests intervention after retries/failures.
- Use standard confirmation template capturing impact/reversibility.

## Testing & validation
- Dry-run: `/database-operations diagnose --tenant=tenant-42 --target=slow_queries --dry-run`.
- Unit tests: `backend/database/` ensures risk scoring and diagnostics logic works correctly.
- Integration: `scripts/validate-database-operations.sh` runs provisioning → backup → failover sequence in emulator.
- Regression: nightly `scripts/nightly-db-smoke.sh` checks backup success, replication lag, and alerting thresholds.

## References
- Provisioning scripts: `scripts/database/`.
- Monitoring queries: `monitoring/queries/postgres`.
- Templates: `templates/results/database-report.md`.

## Related skills
- `/disaster-recovery`: orchestrates DR failovers for databases.
- `/incident-triage-runbook`: responds to database incidents.
- `/capacity-planning`: aligns scaling actions with demand.

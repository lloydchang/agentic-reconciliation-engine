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

Manages provisioning, HA hardening, backups/restores, scaling, diagnostics, and upgrades for managed databases while sharing AI risk context with orchestrators.

## When to invoke
- Provision or decommission managed databases (Azure PostgreSQL/SQL, MongoDB, Redis, Cloud SQL) per tenant.
- Scale compute/storage or adjust connection/performance parameters.
- Trigger backups, restores, failovers, HA drills, or version upgrades.
- Diagnose slow queries, replication lag, or telemetry anomalies.
- React to dispatcher events (`incident-ready`, `policy-risk`, `capacity-alert`, `db-risk`) implicating databases.

## Capabilities
- **AI risk scoring** for destructive operations (failover, restore, upgrade) that balances tenant blast radius and historical reliability.
- **Intelligent provisioning & HA hardening** with geo-redundant backups, private endpoints, and tagging best practices.
- **Smart diagnostics** that surface slow queries, bloat, replication lag, and emit remediation suggestions.
- **Predictive scaling & tuning** recommending compute/storage adjustments before thresholds hit.
- **Shared-context propagation** at `shared-context://memory-store/db/{operationId}` for downstream skills.

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
| `tier` | SLA tier (`starter|business|enterprise`). | `enterprise` |
| `region` | Cloud region. | `eastus` |
| `operation` | Lifecycle step (provision, backup, failover, upgrade). | `failover` |
| `humanGate` | Human approval flag for risky operations. | `true` |

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
1. Provision engine (Azure PostgreSQL Flexible, Azure SQL, MongoDB Atlas, Redis Enterprise) with HA tiers, geo-redundant backups, and private endpoints.
2. Apply tags, RBAC restrictions, and attach to monitoring/logging stacks.
3. Emit `db-provisioned` event with connection info stored in shared context.
4. Command stub: `/database-operations provision --engine=postgres --tenant=tenant-42 --tier=enterprise --region=eastus`.

### Backup, restore, failover automation
1. Schedule manual/automated backups with defined retention policies.
2. Perform restores/point-in-time recovery, capture RPO, and log results.
3. Execute failover drills or DR responses with human gates as needed and emit `db-failover` events.
4. Update downstream skills with `db-backup`, `db-restore`, `db-failover` events and shared context.
5. Command stub: `/database-operations failover --tenant=tenant-42 --humanGate=true`.

### Scaling & performance tuning
1. Adjust compute/storage SKU based on telemetry and cost/capacity signals.
2. Tune connection/settings (max connections, indices) through AI remediation hints.
3. Emit `db-scaled` and maintain event trail for audit.
4. Command stub: `/database-operations scale --tenant=tenant-42 --cpu=8 --storage=512`.

### Diagnostics & upgrades
1. Run slow query analysis, bloat/replication lag detection, and maintenance checks.
2. Upgrade engine version with risk scoring, pre-checks, and post-validation.
3. Emit `db-upgrade` event and store state for `incident`, `deployment`, or `policy` follow-up.
4. Command stub: `/database-operations diagnose --tenant=tenant-42 --target=slow_queries`.

## AI intelligence highlights
- **AI Risk Scoring** balances tenant impact, change size, and historical reliability before destructive actions.
- **Intelligent Scheduling** aligns operations with capacity, incident, and policy contexts.
- **Predictive Diagnostics** spot slow queries, replication lag, or storage pressure before thresholds are breached.
- **Automated Remediation Suggestions** propose index tuning, scaling, or configuration fixes with rationale.

## Memory agent & dispatcher integration
- Persist operations under `shared-context://memory-store/db/{operationId}` and tag with `decisionId`, `tenant`, `engine`, `operation`, `riskScore`.
- Emit events: `db-provisioned`, `db-backup`, `db-restore`, `db-failover`, `db-diagnostics`, `db-upgrade`, `db-risk`.
- Listen for dispatcher signals (`capacity-alert`, `incident-ready`, `policy-risk`) to trigger scaling, failover, or diagnostics.
- Provide fallback artifacts via `artifact-store://db/{operationId}.json` when the bus is offline.

## Observability & telemetry
- Metrics: provisioning count, backup success rate, failover duration, diagnostics frequency, riskScore distribution.
- Logs: structured `log.event="db.operation"` with `operation`, `tenant`, `decisionId`.
- Dashboards: integrate `/database-operations metrics --format=prometheus` into platform views.
- Alerts: riskScore ≥ 0.85, HA degradation, replication lag spikes, backup failure rate > 5%.

## Failure handling & retries
- Retry destructive operations (scale, failover, restore) up to 2× with exponential backoff on transient API errors.
- On failure, emit `db-operation-failed`, log artifacts, and escalate to `incident-triage-runbook`.
- Preserve artifacts/logs for audit; do not delete shared-context entries until downstream acknowledgment.

## Human gates
- Required when:
  1. RiskScore ≥ 0.9 or operations touch production-critical data.
  2. Failover/restore spans >20 tenants or requires cross-region DNS.
  3. Dispatcher requests intervention after retries/failures.
- Confirmation template matches the orchestrator standard:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/database-operations diagnose --tenant=tenant-42 --target=slow_queries --dry-run`.
- Unit tests: `backend/database/` ensures risk scoring and diagnostics logic align with expectations.
- Integration: `scripts/validate-database-operations.sh` runs provisioning → backup → failover sequences in emulator mode.
- Regression: nightly `scripts/nightly-db-smoke.sh` checks backup success, replication lag, and alert thresholds.

## References
- Provisioning scripts: `scripts/database/`.
- Monitoring queries: `monitoring/queries/postgres`.
- Templates: `templates/results/database-report.md`.

## Related skills
- `/disaster-recovery`: orchestrates DR failovers for databases.
- `/incident-triage-runbook`: responds to database incidents.
- `/capacity-planning`: aligns scaling with demand.

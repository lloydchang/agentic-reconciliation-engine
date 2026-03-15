---
name: backup-validator
description: |
  Validate backup/restore pipelines, retention policies, and data integrity with AI-assisted checks so recovery paths remain reliable and auditable.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Backup Validator — World-class Recovery Assurance Playbook

Continuously tests backup repository health, policy compliance, and restore readiness while surfacing risks to dispatchers and incident responders.

## When to invoke
- After backup runs (Azure Backup, AWS Backup, Velero, storage snapshots) to verify success and integrity.
- Before/after DR drills to ensure policies are current and restores succeed within RPO/RTO.
- When storage changes occur (retention, tiering) or incidents threaten backup media.
- Dispatcher/memory agents flag `backup-missed`, `retention-risk`, or `data-loss` events.

## Capabilities
- **Backup health checks** verify run completion, consistency, retention, and encryption.
- **Restore validation** spins up restores in isolation, checks data integrity, and measures RTO.
- **Policy automation** ensures retention/replication rules match compliance frameworks (SOC2, HIPAA).
- **AI risk scoring** rates how close backups are to breaching requirements and alerts dispatchers.
- **Shared context** logs every validation under `shared-context://memory-store/backup-validator/{operationId}`.

## Invocation patterns
```bash
/backup-validator health --vault=kv-backups --tenant=tenant-42
/backup-validator restore --backupId=BU-2026-0315-01 --target=restore-sandbox
/backup-validator policy --framework=soc2 --retention=90d --encrypted=true
/backup-validator drill --region=eastus --type=restore --duration=4h
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `vault` | Backup vault or storage account. | `kv-backups` |
| `backupId` | Backup identifier or snapshot. | `BU-2026-0315-01` |
| `target` | Restore target namespace or account. | `restore-sandbox` |
| `framework` | Compliance framework (`soc2`, `hipaa`, `pci`). | `soc2` |
| `retention` | Role retention target. | `90d` |
| `type` | Check type (`restore`, `consistency`, `policy`). | `restore` |

## Output contract
```json
{
  "operationId": "BV-2026-0315-01",
  "status": "healthy|degraded|failed",
  "vault": "kv-backups",
  "tenant": "tenant-42",
  "riskScore": 0.28,
  "checks": [
    { "name": "lastBackup", "status": "pass", "timestamp": "2026-03-15T03:00:00Z" },
    { "name": "restore-test", "status": "pass", "duration": "5m" }
  ],
  "recommendation": "increase retention to 120 days",
  "logs": "shared-context://memory-store/backup-validator/BV-2026-0315-01",
  "decisionContext": "redis://memory-store/backup-validator/BV-2026-0315-01"
}
```

## World-class workflow templates

### Backup health validation
1. Query backup vaults for completion status, size deltas, encryption status, and policy adherence.
2. Normalize results, compute riskScore, and emit `backup-health` events.
3. Command stub: `/backup-validator health --vault=kv-backups --tenant=tenant-42`

### Restore & DR drill
1. Launch restores (isolated namespaces/VMs), verify integrity, and measure RTO.
2. Emit `backup-restore` and `drill-complete` events with logs/metrics for auditor review.
3. Command stub: `/backup-validator restore --backupId=BU-2026-0315-01 --target=restore-sandbox`

### Policy validation & compliance
1. Compare retention, replication, and encryption policies against frameworks (SOC2, HIPAA).
2. Emit `backup-policy` alerts for deviations or manual approvals.
3. Command stub: `/backup-validator policy --framework=soc2 --retention=90d --encrypted=true`

### Automation & human gate
1. When checks fail or riskScore ≥ 0.8, require human gate and optionally trigger incident skills.
2. Emit `backup-human-gate` events and store context for approvals.
3. Command stub: `/backup-validator drill --region=eastus --type=restore --duration=4h`

## AI intelligence highlights
- **AI risk scoring** balances backup age, size, encryption, and policy drift for each tenant.
- **Predictive policy checks** forecast when retention/restore windows expire.
- **Narrative summaries** capture compliance evidence for SOC2/HIPAA auditors.

## Memory agent & dispatcher integration
- Persist validation status at `shared-context://memory-store/backup-validator/{operationId}`.
- Emit events: `backup-health`, `backup-restore`, `backup-policy`, `backup-human-gate`, `backup-drill`.
- Subscribe to `incident-ready`, `policy-risk`, `capacity-alert` for correlated responses.
- Tag entries with `decisionId`, `vault`, `tenant`, `riskScore`, `framework`.

## Observability & telemetry
- Metrics: health check success rate, restore duration, policy compliance ratio.
- Logs: structured `log.event="backup.validation"` with `checkName`, `status`, `vault`.
- Dashboards: integrate `/backup-validator metrics --format=prometheus` into backup ops.
- Alerts: missing backups, failed restores, policy violations.

## Failure handling & retries
- Retry vault queries/restores up to 3× with exponential backoff; notify on repeated failures.
- On restore failure, escalate to `incident-triage-runbook` with logs/artifacts.
- Preserve reports for 90 days for compliance.

## Human gates
- Required when:
  1. Restore tests touch production datasets or risk data loss.
  2. Policy violations happen for customer vaults.
  3. Dispatcher requests manual oversight after repeated failures.

## Testing & validation
- Dry-run: `/backup-validator health --vault=test-vault --tenant=test --dry-run`
- Unit tests: `backend/backup/` ensures validators and policies behave as expected.
- Integration: `scripts/validate-backup-validator.sh` runs real restores and policy checks.
- Regression: nightly `scripts/nightly-backup-smoke.sh` verifies all pipelines stay healthy.

## References
- Scripts: `scripts/backup-validator/`.
- Templates: `templates/backup/`.
- Monitoring: `monitoring/backup-health/`.

## Related skills
- `/disaster-recovery`: orchestrates restores when backups fail.
- `/incident-triage-runbook`: handles backup incidents.
- `/policy-as-code`: correlates policy gaps with violations.

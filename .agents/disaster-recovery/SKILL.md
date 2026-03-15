---
name: disaster-recovery
description: >
  Design, test, and execute disaster recovery plans with AI-guided RTO/RPO scoring, automated drills, and adaptive failover orchestration.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Disaster Recovery — World-class Resilience Playbook

Ensures workloads recover within SLA-defined RTO/RPO using AI-augmented planning, automated drills, telemetry-driven failover, and shared context for downstream skills.

## When to invoke
- Draft or revise DR plans for Starter/Business/Enterprise/Critical tiers.
- Execute failover or failback runbooks after outages or during scheduled drills.
- Validate backups, replication integrity, and RPO adherence.
- Respond to dispatcher alerts (`incident-ready`, `capacity-alert`, `policy-risk`) requiring cross-region mitigation.

## Capabilities
- **AI RTO/RPO risk scoring** that blends telemetry, tier, and incident history to quantify readiness.
- **Automated DR planning & drills** with guided runbooks for failover/failback scenarios.
- **Intelligent runbook selection** mapping telemetry signatures to procedure templates.
- **Predictive RPO/RTO monitoring** that warns before breaches and integrates with capacity/incident workflows.
- **Shared-context propagation** (`shared-context://memory-store/dr/{operationId}`) for orchestration.

## Invocation patterns

```bash
/disaster-recovery plan --tenant=tenant-42 --tier=enterprise --region=eastus
/disaster-recovery drill --drillId=DRILL-2026-0315-01 --type=rto-measurement --tenant=tenant-42
/disaster-recovery failover --tenant=tenant-42 --reason=region-outage --humanGate=true
/disaster-recovery failback --tenant=tenant-42 --primaryRegion=eastus --secondaryRegion=westeurope
/disaster-recovery rpo-check --tenant=tenant-42 --targetMinutes=5
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `tenant` | Tenant identifier or cluster owner. | `tenant-42` |
| `tier` | DR tier (`starter|business|enterprise|critical`). | `enterprise` |
| `region` | Primary region for plan/drill. | `eastus` |
| `drillId` | Scheduled drill identifier. | `DRILL-2026-0315-01` |
| `targetMinutes` | RTO/RPO target (minutes). | `15` |
| `humanGate` | Flag for approvals on impactful operations. | `true` |

## Output contract

```json
{
  "operationId": "DR-2026-0315-01",
  "operation": "plan|drill|failover|failback|rpo_check",
  "tenant": "tenant-42",
  "status": "success|failure|in_progress",
  "tier": "enterprise",
  "rtoTarget": 15,
  "rpoTarget": 5,
  "rtoAchieved": 12,
  "rpoLag": 3,
  "riskScore": 0.18,
  "events": [
    { "name": "failover-initiated", "timestamp": "2026-03-15T08:00:00Z" }
  ],
  "humanGate": {
    "required": true,
    "impact": "Production failover",
    "reversible": "Yes"
  },
  "logs": "shared-context://memory-store/dr/DR-2026-0315-01",
  "decisionContext": "redis://memory-store/dr/DR-2026-0315-01"
}
```

## World-class workflow templates

### AI-assisted DR planning
1. Map tiers to RTO/RPO targets (Starter 4h/24h, Business 1h/1h, Enterprise 15m/5m, Critical 5m/1m).
2. Use AI risk scoring (tier, tenant impact, telemetry trends) to surface gaps and dependencies.
3. Generate failover/failback runbooks with architecture diagrams and emit `dr-plan-ready` events.
4. Store plan metadata in shared context for dispatcher consumption.

### Automated drills & validation
1. Schedule drills (weekly backup restore, monthly RTO measurement, quarterly failover simulation).
2. Execute steps: restore backups, scale DR clusters, promote replicas, update DNS/traffic managers.
3. Measure actual RTO/RPO, capture metrics, emit `dr-drill`, and notify stakeholders.
4. Update dashboards and log results for reporting/compliance.

### Failover & failback execution
1. Confirm primary outage via health checks and telemetry.
2. Promote geo-replicated databases, scale DR clusters, refresh configs/secrets, and reroute traffic.
3. Validate health, log RTO/RPO, emit `dr-failover`, and document decision context.
4. If failover fails, trigger rollback actions, emit `dr-failover-failed`, and escalate to incident skill.

### Predictive RPO/RTO monitoring
1. Monitor replication lag, backup freshness, capacity, and storage headroom.
2. Forecast breaches and fire `dr-warning` events when risk exceeds thresholds.
3. Correlate with `capacity-planning` and `incident-triage-runbook` when riskScore > gate.

## AI intelligence highlights
- **AI RTO/RPO Risk Scoring** blends telemetry, tier definitions, and incident history to quantify readiness.
- **Intelligent Runbook Selection** matches telemetry fingerprints to failover/failback scripts.
- **Predictive Drill Recommendations** surface tenants and tiers needing drills prior to saturation.
- **Remediation Prioritization** balances failover vs mitigation actions (scaling, routing) using cost/impact heuristics.

## Memory agent & dispatcher integration
- Store drill/failover state under `shared-context://memory-store/dr/{operationId}` tagged with `decisionId`, `tenant`, `riskScore`, `tier`.
- Emit events: `dr-plan-ready`, `dr-drill`, `dr-failover`, `dr-warning`, `dr-failback`.
- Subscribe to dispatcher signals (`incident-ready`, `capacity-alert`, `policy-risk`) to trigger failover actions automatically.
- Provide fallback artifacts via `artifact-store://dr/{operationId}.json` when the event bus is down.

## Observability & telemetry
- Metrics: drill frequency, RTO/RPO compliance rates, backup validation success, failover duration, riskScore trends.
- Logs: structured `log.event="dr.operation"` with `operation`, `tenant`, `tier`, `decisionId`.
- Dashboards: expose `/disaster-recovery metrics --format=prometheus` showing posture, drill history, and alerts.
- Alerts: riskScore > 0.85, RPO lag > target, drill failures exceed threshold.

## Failure handling & retries
- Retry orchestrator steps (scaling, DNS updates, traffic shifts) up to 2× before human escalation.
- On failover failure, roll back partial changes, emit `dr-failover-failed`, and escalate to `incident-triage-runbook`.
- Retain artifacts/logs until downstream acknowledgments confirm consumption.

## Human gates
- Required when:
  1. Tier is Enterprise/Critical or >20 tenants impacted.
  2. Failover touches production traffic or global networking.
  3. Drills disrupt primary systems outside scheduled windows.
- Confirmation template matches the orchestrator standard:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/disaster-recovery drill --drillId=DRILL-DRY-RUN --type=backup_restore --dry-run`.
- Unit tests: `backend/disaster-recovery` ensures scoring and runbook logic behave as expected.
- Integration: `scripts/validate-dr-cycle.sh` runs drill → failover → failback sequences in emulator mode.
- Regression: nightly `scripts/nightly-dr-smoke.sh` keeps telemetry, RTO/RPO reporting, and alerting aligned.

## References
- Failover scripts: `scripts/disaster-recovery/`.
- Runbooks: `runbooks/disaster-recovery/`.
- Dashboards: `monitoring/grafana/dr`.

## Related skills
- `/incident-triage-runbook`: handles failover incidents and escalations.
- `/capacity-planning`: aligns capacity signals with failover needs.
- `/ai-agent-orchestration`: orchestrates multi-step failover/drill workflows.

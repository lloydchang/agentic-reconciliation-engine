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

Ensures workloads recover within their SLA-defined RTO/RPO using AI-augmented planning, automated drills, telemetry-driven failover, and shared-context signals for downstream skills. Trigger when defining recovery architecture, running drills, failing over, or reacting to capacity/incident alerts.

## When to invoke
- Draft or revise DR plans for Starter/Business/Enterprise/Critical tiers.
- Execute failover or failback runbooks after an outage or during drills.
- Validate backups, replication, and RPO compliance.
- Respond to dispatcher alerts (`incident-ready`, `capacity-alert`, `policy-risk`) requiring cross-region mitigation.

## Capabilities
- Multi-tier failover strategies (cold/warm/hot/active-active) with AI RTO/RPO scoring.
- Automated DR drills, backup integrity checks, and posture reporting.
- Intelligent runbook selection and guided failover/failback steps.
- Shared context integration (`shared-context://memory-store/dr/<operationId>`) for other skills.
- Human gate guidance for impactful failovers or production drills.

## Invocation patterns

```bash
/disaster-recovery plan --tenant=tenant-42 --tier=enterprise --region=eastus
/disaster-recovery drill --drillId=DRILL-2026-0315-01 --type=rto_measurement --tenant=tenant-42
/disaster-recovery failover --tenant=tenant-42 --reason=region-outage --humanGate=true
/disaster-recovery failback --tenant=tenant-42 --primaryRegion=eastus --secondaryRegion=westeurope
/disaster-recovery rpo-check --tenant=tenant-42 --targetMinutes=5
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `tenant` | Tenant identifier. | `tenant-42` |
| `tier` | DR SLA tier (starter/business/enterprise/critical). | `enterprise` |
| `region` | Primary region for plan/drill. | `eastus` |
| `drillId` | Identifier for scheduled drill. | `DRILL-2026-0315-01` |
| `targetMinutes` | RTO/RPO target (minutes). | `15` |
| `humanGate` | Whether gate approval is required. | `true` |

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
1. Determine tier (Starter 4h/24h, Business 1h/1h, Enterprise 15min/5min, Critical 5min/1min).
2. Use AI risk scoring (tier, tenant impact, telemetry) to surface gaps.
3. Generate failover/failback runbooks and Azure/AWS/GCP architecture diagrams.
4. Store plan metadata in shared-context for dispatcher consumption.

### Automated DR drills & validation
1. Schedule drills (weekly backup restore, monthly RTO measurement, quarterly failover simulation).
2. Run steps (restore backup, promote geo-replicated DB, scale DR AKS, update DNS/front-door).
3. Measure actual RTO/RPO, log metrics, emit `drill-completed`.
4. Update `dr-loop` dashboards and notify stakeholders.

### Failover & failback execution
1. Confirm primary outage via health checks; gather telemetry.
2. Promote geo-replicated databases, scale DR clusters, update secrets/config.
3. Restore traffic weighting via Front Door/Traffic Manager/VPN.
4. Validate health, log RTO, emit `failover-complete`; if failover fails, trigger incident skill.

### Predictive RPO/RTO monitoring
1. Monitor replication lag, backup freshness, capacity headroom.
2. Forecast RPO breaches; send proactive `dr-warning` events.
3. Align with `capacity-planning` and `incident-triage-runbook` when risk > threshold.

## AI intelligence highlights
- **AI RTO/RPO Risk Scoring**: blends telemetry, tier definitions, incident history to determine readiness.
- **Intelligent Runbook Selection**: matches telemetry signatures to prescribed failover/failback scripts.
- **Predictive Drill Recommendations**: selects tenants/tiers needing drills before saturations occur.
- **Remediation Prioritization**: balances failover versus mitigations (scaling, routing) using cost/impact heuristics.

## Memory agent & dispatcher integration
- Store drill/failover state under `shared-context://memory-store/dr/<operationId>`.
- Emit events: `dr-plan-ready`, `dr-drill`, `dr-failover`, `dr-warning`.
- Subscribe to dispatcher signals (`incident-ready`, `capacity-alert`) to trigger failover sequences automatically.
- Tag metadata with `decisionId`, `tenant`, `riskScore`, `confidence`.

## Communication protocols
- Primary: Bash/CLI runbooks calling cloud CLIs or kubectl/az commands, streaming progress logs.
- Secondary: Event bus for `dr-*` events; watchers (prometheus/alertmanager) monitor telemetry.
- Fallback: Persist JSON artifacts to `artifact-store://dr/<operationId>.json`.

## Observability & telemetry
- Metrics: drills executed, RTO/RPO compliance rates, backup validation success, failover duration, riskScore.
- Logs: structured `log.event="dr.operation"` with `operation`, `tenant`, `tier`, `decisionId`.
- Dashboards: integrate `/disaster-recovery metrics --format=prometheus` showing posture, drill history, alert status.
- Alerts: riskScore > 0.85, RPO lag > target, drill failures > 1 per quarter.

## Failure handling & retries
- Retry orchestrator steps (scaling, DNS updates) up to 2× before human escalation.
- On failover failure, roll back partial changes, emit `dr-failover-failed`, and escalate to `incident-triage-runbook`.
- Keep artifacts/logs until downstream acknowledgement.

## Human gates
- Required when:
 1. Tier is Enterprise/Critical or >20 tenants affected.
 2. Failover impacts production traffic or modifies global networking.
 3. Drill execution may disrupt primary systems beyond scheduled windows.
- Use the standard gate template capturing Impact/Reversibility.

## Testing & validation
- Dry-run: `/disaster-recovery drill --drillId=DRILL-DRY-RUN --type=backup_restore --dry-run`.
- Unit tests: `backend/disaster-recovery` verifying scoring and runbook logic.
- Integration: `scripts/validate-dr-cycle.sh` runs drill → failover → failback in emulator mode.
- Regression: nightly `scripts/nightly-dr-smoke.sh` keeps telemetry, RTO/RPO reporting, and alerting aligned.

## References
- Failover scripts: `scripts/disaster-recovery/`.
- Runbooks: `runbooks/disaster-recovery/`.
- Dashboards: `monitoring/grafana/dr`.

## Related skills
- `/incident-triage-runbook`: handles failover incidents.
- `/capacity-planning`: aligns capacity signals and triggers failovers.
- `/ai-agent-orchestration`: sequences multi-step failover/drill workflows.

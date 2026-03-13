---
name: disaster-recovery
description: >
  Use this skill to design, implement, test, and execute disaster recovery
  procedures for workloads. Triggers: any request to create a DR plan,
  execute a region failover, test RTO/RPO objectives, run a DR drill,
  validate backup integrity, restore a failed environment, or assess and
  improve the current disaster recovery posture.
tools:
  - bash
  - computer
---

# Disaster Recovery Skill

Automate the full DR lifecycle: design DR architecture, codify recovery
runbooks, schedule and execute DR drills, measure RTO/RPO actuals vs targets,
and maintain an always-ready failover capability.

---

## DR Tiers (by SLA)

| Tier       | RTO    | RPO    | Strategy                         |
|------------|--------|--------|----------------------------------|
| Starter    | 4 hr   | 24 hr  | Backup + restore (cold)          |
| Business   | 1 hr   | 1 hr   | Pilot light (warm standby)       |
| Enterprise | 15 min | 5 min  | Active-passive (hot standby)     |
| Critical   | 5 min  | 1 min  | Active-active (multi-region)     |

---

## Architecture Patterns

### Active-Passive (Enterprise default)
```
Primary Region (East US)         Secondary Region (West Europe)
  AKS Cluster (active)    ──────► AKS Cluster (scaled to 0)
  PostgreSQL (primary)    ──────► PostgreSQL (geo-replica, read)
  Blob Storage            ──────► Blob Storage (GRS replicated)
  Key Vault               ──────► Key Vault (replicated)
  Azure Front Door ─── health probes ─── auto-failover at DNS level
```

### Traffic Manager / Front Door Failover
```bash
# Azure Front Door health probe config
az afd origin update \
  --resource-group "$FRONTDOOR_RG" \
  --profile-name "$AFD_PROFILE" \
  --origin-group-name "og-${TENANT_ID}" \
  --origin-name "primary-${REGION}" \
  --priority 1 --weight 1000 \
  --enabled-state Enabled

az afd origin update \
  --resource-group "$FRONTDOOR_RG" \
  --profile-name "$AFD_PROFILE" \
  --origin-group-name "og-${TENANT_ID}" \
  --origin-name "secondary-${DR_REGION}" \
  --priority 2 --weight 1000 \
  --enabled-state Enabled
```

---

## Failover Execution

### Region Failover Runbook (Enterprise Tier)
```bash
execute_failover() {
  local tenant_id=$1
  local reason=$2

  echo "[$(date -u +%H:%M:%SZ)] FAILOVER INITIATED: $tenant_id — $reason"
  FAILOVER_START=$(date +%s)

  # Step 1: Confirm primary is unreachable (don't fail over on false alarm)
  PRIMARY_HEALTHY=$(curl -sf --max-time 10 \
    "https://${tenant_id}.app.example.com/health" && echo "true" || echo "false")
  [[ "$PRIMARY_HEALTHY" == "true" ]] && {
    echo "Primary is healthy — aborting failover"
    return 1
  }

  # Step 2: Promote geo-replica to standalone
  az postgres flexible-server replica stop-replication \
    --resource-group "rg-${tenant_id}-dr" \
    --name "pg-${tenant_id}-replica"
  echo "[$(date -u +%H:%M:%SZ)] DB promoted to standalone"

  # Step 3: Scale up DR AKS node pool
  az aks nodepool scale \
    --cluster-name "aks-${tenant_id}-dr" \
    --resource-group "rg-${tenant_id}-dr" \
    --name workload --node-count "$PROD_NODE_COUNT"
  echo "[$(date -u +%H:%M:%SZ)] DR AKS scaled up"

  # Step 4: Update secrets/config to point at DR database
  kubectl create secret generic db-connection \
    --from-literal=host="pg-${tenant_id}-replica.postgres.database.azure.com" \
    --namespace "$tenant_id" --dry-run=client -o yaml | kubectl apply -f -

  # Step 5: Trigger rolling restart to pick up new DB endpoint
  kubectl rollout restart deployment -n "$tenant_id"
  kubectl rollout status deployment -n "$tenant_id" --timeout=5m

  # Step 6: Update Front Door weights (DR becomes primary)
  az afd origin update \
    --profile-name "$AFD_PROFILE" -g "$FRONTDOOR_RG" \
    --origin-group-name "og-${tenant_id}" \
    --origin-name "secondary-${DR_REGION}" --priority 1

  az afd origin update \
    --profile-name "$AFD_PROFILE" -g "$FRONTDOOR_RG" \
    --origin-group-name "og-${tenant_id}" \
    --origin-name "primary-${REGION}" --priority 99

  # Step 7: Validate
  sleep 30
  DR_HEALTHY=$(curl -sf "https://${tenant_id}.app.example.com/health" \
    && echo "true" || echo "false")

  FAILOVER_END=$(date +%s)
  RTO_ACHIEVED=$(( (FAILOVER_END - FAILOVER_START) / 60 ))

  echo "[$(date -u +%H:%M:%SZ)] FAILOVER COMPLETE"
  echo "RTO achieved: ${RTO_ACHIEVED} minutes | DR healthy: $DR_HEALTHY"
  record_failover_event "$tenant_id" "$reason" "$RTO_ACHIEVED" "$DR_HEALTHY"
}
```

### Failback Runbook (return to primary region)
```bash
execute_failback() {
  local tenant_id=$1

  # 1. Restore primary region infrastructure (if needed via Terraform)
  # 2. Set up replication: DR → primary (reverse)
  # 3. Wait for data sync (monitor replication lag → 0)
  # 4. Maintenance window: freeze writes, final sync
  # 5. Promote primary, demote DR
  # 6. Update Front Door weights back to primary
  # 7. Validate, then scale down DR
}
```

---

## DR Drills

### Automated DR Drill Schedule
```yaml
dr_drills:
  - type: backup_restore_validation
    frequency: weekly
    scope: all_tenants
    action: restore_to_test_env_and_verify_row_counts

  - type: rto_measurement
    frequency: monthly
    scope: enterprise_tenants
    action: execute_full_failover_to_dr_region_and_measure_time
    human_gate: required

  - type: failover_simulation
    frequency: quarterly
    scope: all_tiers
    action: simulate_primary_outage_validate_auto_detection
```

### Drill Execution
```bash
run_dr_drill() {
  local drill_type=$1
  local tenant_id=$2
  local DRILL_ID="DRILL-$(date +%Y%m%d-%H%M%S)"

  echo "Starting DR drill: $drill_type for $tenant_id"

  case $drill_type in
    backup_restore)
      # Restore latest backup to isolated test environment
      az postgres flexible-server restore \
        --resource-group "rg-dr-test" \
        --name "pg-drill-${tenant_id}" \
        --source-server "pg-${tenant_id}" \
        --restore-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

      # Validate row counts
      PROD_COUNT=$(psql -h "pg-${tenant_id}.postgres.database.azure.com" \
        -t -c "SELECT COUNT(*) FROM events;")
      TEST_COUNT=$(psql -h "pg-drill-${tenant_id}.postgres.database.azure.com" \
        -t -c "SELECT COUNT(*) FROM events;")

      RPO_OK=$( [[ "$PROD_COUNT" == "$TEST_COUNT" ]] && echo "PASS" || echo "FAIL" )
      echo "RPO drill result: $RPO_OK (prod: $PROD_COUNT, restore: $TEST_COUNT)"

      # Clean up test server
      az postgres flexible-server delete \
        --resource-group "rg-dr-test" \
        --name "pg-drill-${tenant_id}" --yes
      ;;
  esac

  record_drill_result "$DRILL_ID" "$drill_type" "$tenant_id"
}
```

---

## RPO Validation

```bash
# Confirm geo-replication lag is within RPO target
check_rpo() {
  local tenant_id=$1 rpo_target_minutes=$2

  REPLICA_LAG=$(psql -h "pg-${tenant_id}-replica.postgres.database.azure.com" \
    -t -c "SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) / 60;" \
    | tr -d ' ')

  if (( $(echo "$REPLICA_LAG > $rpo_target_minutes" | bc -l) )); then
    echo "RPO BREACH: lag=${REPLICA_LAG}min, target=${rpo_target_minutes}min"
    create_alert "RPO_BREACH" "$tenant_id" "$REPLICA_LAG"
  else
    echo "RPO OK: lag=${REPLICA_LAG}min (target=${rpo_target_minutes}min)"
  fi
}
```

---

## DR Posture Dashboard

```
DR Posture Report — [Date]
──────────────────────────────

RTO/RPO Coverage
  Enterprise tenants (15/5 min targets):  18/18 ✅
  Business tenants (1hr/1hr targets):     24/24 ✅
  Starter tenants (4hr/24hr targets):     41/41 ✅

Last Drill Results
  Backup restore drill:  PASS (2025-05-01) — avg restore time 8.4 min
  RTO measurement drill: PASS (2025-04-15) — avg RTO 11.2 min (target 15 min)
  Failback drill:        PASS (2025-03-01)

Replication Health
  Replicas in sync (lag < 5 min): 18/18 ✅
  Worst replication lag:          2.3 min (tenant-42)

Backup Integrity
  Backups verified this week:     83/83 ✅
  Last integrity failure:         None (30 days)
```

---

## Examples

- "Execute a region failover for tenant-42 — the East US cluster is down"
- "Run a DR drill for all enterprise tenants this weekend"
- "What is our current RPO compliance across all tenants?"
- "Generate the quarterly DR posture report"
- "Walk me through what happens when we failover tenant-7 to West Europe"
- "Test the backup integrity for all business-tier tenants"

---

## Output Format

```json
{
  "operation": "failover|failback|drill|rpo_check|posture_report",
  "tenant_id": "string",
  "status": "success|failure|in_progress",
  "rto_achieved_minutes": 0,
  "rpo_lag_minutes": 0,
  "rto_target_minutes": 0,
  "rpo_target_minutes": 0,
  "rto_met": true,
  "rpo_met": true,
  "drill_result": "PASS|FAIL|SKIPPED",
  "failover_region": "string"
}
```

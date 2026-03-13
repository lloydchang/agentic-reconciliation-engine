---
name: workload-migration
description: >
  Use this skill to plan and execute migrations of cloud workloads: cloud-to-
  cloud (Azure to AWS, etc.), region migrations, subscription moves, Kubernetes
  cluster upgrades with data migration, database migrations, and SaaS tenant
  migrations to a new platform tier or cloud environment. Triggers: any request
  to migrate a workload, move a tenant to a new cluster or region, consolidate
  environments, perform a blue-green environment switch, or validate a migration
  plan before execution.
tools:
  - bash
  - computer
---

# Workload Migration Skill

Orchestrate complex cloud workload migrations end-to-end: assess → plan →
execute → validate → cutover → decommission. Supports zero-downtime patterns
with rollback at every stage.

# Workload Migration Skill

Orchestrate complex cloud workload migrations end-to-end: assess → plan →
execute → validate → cutover → decommission. Supports zero-downtime patterns
with rollback at every stage.

## Enhanced Workload Migration Orchestrator

### Plan and Automate Migration Between Clusters
Plan and automate migration of workloads between clusters safely across environments.

**Purpose:** Migrate workloads safely across environments with minimal downtime.

**Workflow:**
1. Identify workload dependencies and relationships
2. Build comprehensive migration plan with rollback steps
3. Validate compatibility between source and target environments
4. Execute migration with automated monitoring
5. Verify health checks and functionality in target environment
6. Generate migration completion report with metrics

**Output:** Migration completion report with success metrics, issues encountered, and rollback procedures.

---

## Migration Types

| Type                         | Pattern          | Downtime      |
|------------------------------|------------------|---------------|
| Region migration (same cloud)| Blue-green clone | Zero          |
| Cross-cloud migration        | Parallel run     | Minimal       |
| Subscription / org move      | Clone + cutover  | Hours         |
| K8s cluster upgrade (in-situ)| Rolling          | Zero          |
| K8s cluster migration (new)  | Blue-green       | Zero          |
| Database migration           | CDC replication  | Minutes       |
| Tenant tier upgrade          | In-place scale   | Zero          |
| Legacy → containerised       | Lift-and-shift   | Scheduled     |

---

## Phase 1 — Assessment

```bash
# Inventory all resources in source environment
az resource list \
  --resource-group "rg-${SOURCE_TENANT}" \
  --output json > migration/source-inventory.json

# Kubernetes workload manifest export
kubectl get all,pvc,configmap,secret,ingress \
  -n "$SOURCE_NAMESPACE" -o yaml > migration/k8s-manifests.yaml

# Database size and dependency map
az postgres flexible-server show \
  --name "pg-${SOURCE_TENANT}" \
  --resource-group "rg-${SOURCE_TENANT}" \
  --query "{SKU:sku.name, StorageGB:storage.storageSizeGb, Version:version}" \
  --output json

# Network dependency scan (what does this tenant call?)
kubectl exec -n "$SOURCE_NAMESPACE" deploy/$APP -- \
  ss -tnp | awk '{print $5}' | sort -u
```

### Assessment Report Fields
- Estimated data volume (GB)
- Estimated migration duration
- Downtime risk: Zero / Minutes / Hours
- Dependencies on other tenants/services
- Blockers (unsupported features, regional gaps)
- Recommended pattern

---

## Phase 2 — Migration Plan

Generate a step-by-step plan document:

```markdown
# Migration Plan: ${TENANT_ID} → ${TARGET_ENV}

## Summary
- Source: ${SOURCE_REGION} / ${SOURCE_CLUSTER}
- Target: ${TARGET_REGION} / ${TARGET_CLUSTER}
- Pattern: Blue-Green with parallel run
- Estimated duration: X hours
- Planned downtime: 0 minutes

## Pre-Migration Checklist
- [ ] Snapshot all databases
- [ ] Export and validate Terraform state
- [ ] Confirm target quota available
- [ ] Notify tenant of maintenance window
- [ ] Enable enhanced monitoring

## Migration Steps
1. Provision target environment (terraform apply)
2. Restore database snapshot to target
3. Configure CDC replication: source → target
4. Validate data parity (row count + checksum)
5. Deploy application to target cluster
6. Run smoke tests on target (via internal URL)
7. Switch DNS: 10% → 50% → 100% (blue-green)
8. Monitor for 30 minutes at each traffic split
9. Decommission source environment

## Rollback Plan
- DNS rollback: revert weights in < 5 minutes
- DB rollback: source remains primary until decommission
- Cutover decision point: step 7 (go/no-go gate)

## Success Criteria
- All smoke tests pass on target
- Error rate < 1% at 100% traffic
- Latency p99 within 10% of source baseline
- Data row-count parity confirmed
```

---

## Phase 3 — Execute: Data Migration

### Database (PostgreSQL → PostgreSQL CDC)
```bash
# Use pglogical for logical replication
# On source:
psql -h $SOURCE_DB -c "CREATE EXTENSION pglogical;"
psql -h $SOURCE_DB -c "
  SELECT pglogical.create_node(node_name := 'source', dsn := '$SOURCE_DSN');
  SELECT pglogical.create_replication_set('migration_set');
  SELECT pglogical.replication_set_add_all_tables('migration_set', ARRAY['public']);
"

# On target:
psql -h $TARGET_DB -c "CREATE EXTENSION pglogical;"
psql -h $TARGET_DB -c "
  SELECT pglogical.create_node(node_name := 'target', dsn := '$TARGET_DSN');
  SELECT pglogical.create_subscription(
    subscription_name := 'migration_sub',
    provider_dsn := '$SOURCE_DSN',
    replication_sets := ARRAY['migration_set']
  );
"

# Monitor replication lag
psql -h $SOURCE_DB -c "SELECT * FROM pglogical.show_subscription_status();"
```

### Kubernetes Workloads
```bash
# Export from source namespace
kubectl get all,pvc,cm,secret,ingress \
  -n "$SOURCE_NAMESPACE" -o yaml | \
  grep -v "resourceVersion\|uid\|creationTimestamp\|generation\|selfLink" \
  > migration/k8s-cleaned.yaml

# Apply to target namespace (dry-run first)
kubectl apply --dry-run=server \
  -f migration/k8s-cleaned.yaml \
  -n "$TARGET_NAMESPACE"

# Apply for real
kubectl apply -f migration/k8s-cleaned.yaml -n "$TARGET_NAMESPACE"

# Validate
kubectl get pods -n "$TARGET_NAMESPACE" | grep -v Running
```

### PVC Data Migration (using `pv-migrate`)
```bash
pv-migrate migrate \
  --source-namespace "$SOURCE_NAMESPACE" \
  --source "$SOURCE_PVC_NAME" \
  --dest-namespace "$TARGET_NAMESPACE" \
  --dest "$TARGET_PVC_NAME" \
  --strategy svc
```

---

## Phase 4 — Validation

```bash
# Data parity check
SOURCE_COUNT=$(psql -h $SOURCE_DB -t -c "SELECT COUNT(*) FROM $KEY_TABLE;")
TARGET_COUNT=$(psql -h $TARGET_DB -t -c "SELECT COUNT(*) FROM $KEY_TABLE;")
[[ "$SOURCE_COUNT" == "$TARGET_COUNT" ]] || echo "PARITY MISMATCH: $SOURCE_COUNT vs $TARGET_COUNT"

# Checksum comparison
psql -h $SOURCE_DB -t -c "SELECT MD5(CAST(COUNT(*) AS TEXT)) FROM $KEY_TABLE;" > source.md5
psql -h $TARGET_DB -t -c "SELECT MD5(CAST(COUNT(*) AS TEXT)) FROM $KEY_TABLE;" > target.md5
diff source.md5 target.md5 && echo "Checksums match" || echo "CHECKSUM MISMATCH"

# Application smoke tests
pytest tests/smoke/ --base-url="https://${TARGET_URL}" -v

# Performance baseline comparison
ab -n 1000 -c 10 "https://${TARGET_URL}/api/health" > target-perf.txt
diff baseline-perf.txt target-perf.txt
```

---

## Phase 5 — Cutover (DNS Traffic Shift)

```bash
cutover_traffic() {
  local weight=$1  # 0, 10, 50, 100
  echo "Shifting $weight% traffic to target..."

  # Azure Front Door / Traffic Manager weight update
  az network traffic-manager endpoint update \
    --resource-group "$FRONTDOOR_RG" \
    --profile-name "$TM_PROFILE" \
    --name "target-endpoint" \
    --type externalEndpoints \
    --weight "$weight"

  az network traffic-manager endpoint update \
    --resource-group "$FRONTDOOR_RG" \
    --profile-name "$TM_PROFILE" \
    --name "source-endpoint" \
    --type externalEndpoints \
    --weight "$((100 - weight))"

  echo "Monitoring for 5 minutes at $weight% traffic..."
  sleep 300
  check_error_rate || { rollback_traffic; exit 1; }
}

# Progressive cutover
cutover_traffic 10
cutover_traffic 50
cutover_traffic 100
```

---

## Phase 6 — Decommission Source

Only after 24h monitoring at 100% target traffic with zero issues:

```bash
# 1. Final snapshot of source for archival
az postgres flexible-server backup create \
  --name "pg-${SOURCE_TENANT}" \
  --resource-group "rg-${SOURCE_TENANT}" \
  --backup-name "pre-decommission-final"

# 2. Terraform destroy source
terraform destroy \
  -var-file="env/${SOURCE_TENANT}.tfvars" \
  -auto-approve  # Only after human approval

# 3. Archive DNS record
# 4. Update tenant registry: source → ARCHIVED
# 5. Close migration ticket
```

---

## Examples

- "Migrate tenant-42 from East US to West Europe with zero downtime"
- "Plan a migration of our AKS 1.27 cluster to a new 1.30 cluster"
- "Assess what it would take to move our top 5 tenants from Azure to AWS"
- "Execute the database migration for tenant-91 from PostgreSQL 13 to 16"
- "Generate a migration plan for consolidating dev tenants into a shared cluster"

---

## Output Format

```json
{
  "migration_id": "MIG-2025-001",
  "tenant_id": "string",
  "source": { "region": "string", "cluster": "string", "cloud": "string" },
  "target": { "region": "string", "cluster": "string", "cloud": "string" },
  "pattern": "blue-green|rolling|parallel-run",
  "phase": "assess|plan|execute|validate|cutover|decommission",
  "status": "success|in_progress|blocked|rolled_back",
  "downtime_minutes": 0,
  "data_parity_confirmed": true,
  "rollback_available": true
}
```

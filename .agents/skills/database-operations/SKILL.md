---
name: database-operations
description: >
  Use this skill to manage cloud database lifecycle operations including
  provisioning, scaling, backup/restore, failover, high-availability
  configuration, performance tuning, and version upgrades for Azure Database
  for PostgreSQL, Azure SQL, and MongoDB. Triggers: any request to provision
  a database, restore from backup, trigger or test a failover, scale compute
  or storage, tune query performance, investigate slow queries, set up
  read replicas, rotate credentials, or generate a database health report.
tools:
  - bash
  - computer
---

# Database Operations Skill

Full database lifecycle automation: provision → configure HA → backup →
monitor → tune → scale → failover → restore → upgrade.

---

## Supported Engines

| Engine              | Azure service                     | CLI               |
|---------------------|-----------------------------------|-------------------|
| PostgreSQL          | Azure Database for PostgreSQL Flexible | `az postgres flexible-server` |
| SQL Server          | Azure SQL Database / Managed Instance | `az sql`      |
| MongoDB             | Azure Cosmos DB (Mongo API)       | `az cosmosdb`     |
| Redis               | Azure Cache for Redis             | `az redis`        |

---

## Provisioning

### PostgreSQL Flexible Server (per-tenant)
```bash
az postgres flexible-server create \
  --resource-group "rg-${TENANT_ID}" \
  --name "pg-${TENANT_ID}" \
  --location "$REGION" \
  --sku-name "$DB_SKU" \
  --tier "$DB_TIER" \
  --storage-size "$STORAGE_GB" \
  --version "16" \
  --admin-user "$DB_ADMIN" \
  --admin-password "$DB_PASSWORD" \
  --high-availability ZoneRedundant \
  --standby-zone 2 \
  --zone 1 \
  --backup-retention "$BACKUP_DAYS" \
  --geo-redundant-backup Enabled \
  --private-dns-zone "pg-${TENANT_ID}.private.postgres.database.azure.com" \
  --vnet "vnet-spoke-${TENANT_ID}" \
  --subnet "snet-data" \
  --tags "tenant=${TENANT_ID}" "managed_by=db-operations"
```

### Tier Sizing Guide
| Tier        | SKU                | vCores | Memory | Max Connections | Use case        |
|-------------|-------------------|--------|--------|-----------------|-----------------|
| Starter     | Standard_B2ms     | 2      | 8 GB   | 150             | Dev / small SaaS|
| Business    | Standard_D4s_v3   | 4      | 16 GB  | 400             | Mid-size tenant |
| Enterprise  | Standard_D8s_v3   | 8      | 32 GB  | 860             | High-volume     |
| Enterprise+ | Standard_D16s_v3  | 16     | 64 GB  | 1740            | Supermajors     |

---

## Backup & Restore

### On-Demand Backup
```bash
az postgres flexible-server backup create \
  --resource-group "rg-${TENANT_ID}" \
  --name "pg-${TENANT_ID}" \
  --backup-name "manual-$(date +%Y%m%d-%H%M%S)"
```

### Point-in-Time Restore
```bash
# Restore to a new server at a specific timestamp
az postgres flexible-server restore \
  --resource-group "rg-${TENANT_ID}" \
  --name "pg-${TENANT_ID}-restored" \
  --source-server "pg-${TENANT_ID}" \
  --restore-time "$(date -d '-2 hours' +%Y-%m-%dT%H:%M:%SZ)"

# Validate restored server
psql -h "pg-${TENANT_ID}-restored.postgres.database.azure.com" \
  -U "$DB_ADMIN" -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"
```

### Backup Retention Policy
| Tier        | Local retention | Geo-redundant backup | Point-in-time window |
|-------------|----------------|----------------------|----------------------|
| Starter     | 7 days         | No                   | 7 days               |
| Business    | 30 days        | Yes                  | 30 days              |
| Enterprise  | 35 days        | Yes                  | 35 days              |

---

## High Availability & Failover

### Check HA Status
```bash
az postgres flexible-server show \
  --resource-group "rg-${TENANT_ID}" \
  --name "pg-${TENANT_ID}" \
  --query "{
    state: state,
    ha: highAvailability.mode,
    primaryZone: availabilityZone,
    standbyZone: highAvailability.standbyAvailabilityZone,
    haState: highAvailability.state
  }" --output json
```

### Trigger Forced Failover (for DR testing)
```bash
# REQUIRES APPROVAL — causes brief interruption
az postgres flexible-server restart \
  --resource-group "rg-${TENANT_ID}" \
  --name "pg-${TENANT_ID}" \
  --failover Forced
```

### Read Replica (for read-heavy tenants)
```bash
az postgres flexible-server replica create \
  --resource-group "rg-${TENANT_ID}" \
  --name "pg-${TENANT_ID}-replica" \
  --source-server "pg-${TENANT_ID}" \
  --location "${REPLICA_REGION}"
```

---

## Scaling

```bash
# Scale up compute (live — minimal interruption)
az postgres flexible-server update \
  --resource-group "rg-${TENANT_ID}" \
  --name "pg-${TENANT_ID}" \
  --sku-name "Standard_D8s_v3" \
  --tier GeneralPurpose

# Expand storage (online, non-reversible)
az postgres flexible-server update \
  --resource-group "rg-${TENANT_ID}" \
  --name "pg-${TENANT_ID}" \
  --storage-size 512

# Adjust connection pool (PgBouncer)
az postgres flexible-server parameter set \
  --resource-group "rg-${TENANT_ID}" \
  --server-name "pg-${TENANT_ID}" \
  --name "max_connections" \
  --value "400"
```

---

## Performance Diagnostics

```sql
-- Top 10 slow queries (pg_stat_statements)
SELECT query, calls, mean_exec_time, total_exec_time, rows
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Table bloat check
SELECT relname AS table,
  pg_size_pretty(pg_total_relation_size(oid)) AS total_size,
  pg_size_pretty(pg_relation_size(oid)) AS table_size,
  pg_size_pretty(pg_total_relation_size(oid) - pg_relation_size(oid)) AS index_size
FROM pg_class WHERE relkind = 'r'
ORDER BY pg_total_relation_size(oid) DESC
LIMIT 20;

-- Lock waits
SELECT pid, usename, pg_blocking_pids(pid) AS blocked_by, query
FROM pg_stat_activity
WHERE cardinality(pg_blocking_pids(pid)) > 0;

-- Index usage
SELECT relname, indexrelname,
  idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC
LIMIT 20;
```

### Automated Tuning Recommendations
```bash
# Generate recommendations using Azure Intelligent Performance
az postgres flexible-server show-recommendation \
  --resource-group "rg-${TENANT_ID}" \
  --server-name "pg-${TENANT_ID}" \
  --output json | jq '.[] | {type: .type, detail: .details, impact: .impactedField}'
```

---

## Database Health Monitor

```bash
check_db_health() {
  local tenant_id=$1

  echo "=== Connection Pool ===" && \
    psql -h "pg-${tenant_id}.postgres.database.azure.com" \
      -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

  echo "=== Replication Lag ===" && \
    psql -c "SELECT now() - pg_last_xact_replay_timestamp() AS lag;" 2>/dev/null

  echo "=== Database Sizes ===" && \
    psql -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database ORDER BY pg_database_size(datname) DESC;"

  echo "=== Long Running Queries ===" && \
    psql -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query
    FROM pg_stat_activity WHERE state = 'active' AND now() - query_start > interval '5 minutes';"
}
```

### Alert Thresholds
| Metric                        | Warning  | Critical |
|-------------------------------|----------|----------|
| Storage utilisation           | 75%      | 90%      |
| CPU average (5-min)           | 80%      | 95%      |
| Active connections / max      | 80%      | 95%      |
| Replication lag               | 30s      | 5 min    |
| Failed connections (per min)  | 10       | 50       |

---

## Version Upgrades

```bash
# Major version upgrade (e.g., PG 15 → 16)
# Step 1: Take backup
az postgres flexible-server backup create \
  --name "pg-${TENANT_ID}" -g "rg-${TENANT_ID}" \
  --backup-name "pre-upgrade-$(date +%Y%m%d)"

# Step 2: Run upgrade
az postgres flexible-server upgrade \
  --resource-group "rg-${TENANT_ID}" \
  --name "pg-${TENANT_ID}" \
  --version 16

# Step 3: Validate
psql -h "pg-${TENANT_ID}.postgres.database.azure.com" \
  -c "SELECT version();"
```

---

## Examples

- "Provision a Business-tier PostgreSQL database for tenant-53 in East US"
- "Restore tenant-42's database to 3 hours ago — they had a bad data migration"
- "Scale up the enterprise database for tenant-91 to D8s_v3"
- "Show me all slow queries on the payments service database"
- "Test the failover for tenant-7's HA database and confirm recovery time"
- "Which databases are using more than 80% of their storage?"

---

## Output Format

```json
{
  "operation": "provision|backup|restore|scale|failover|health-check|upgrade",
  "tenant_id": "string",
  "server_name": "string",
  "status": "success|failure|in_progress",
  "ha_state": "Healthy|FailingOver|NotEnabled",
  "storage_used_pct": 0,
  "connection_used_pct": 0,
  "slow_queries_count": 0,
  "backup_name": "string",
  "restore_point": "ISO8601"
}
```

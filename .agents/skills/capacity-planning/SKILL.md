---
name: capacity-planning
description: >
  Use this skill to forecast resource capacity needs, identify headroom risks,
  recommend scaling actions, and produce capacity plans for cloud infrastructure.
  Triggers: any request to forecast compute or storage needs, check whether
  current resources can handle projected growth, plan for a product launch or
  traffic spike, assess autoscaler configuration, model different scaling
  scenarios, or produce a quarterly capacity report.
tools:
  - bash
  - computer
---

# Capacity Planning Skill

Automate resource forecasting, headroom analysis, autoscaler validation, and
scenario modelling to ensure the platform scales ahead of demand — not in
reaction to it.

---

## Data Sources

| Resource         | Source                           | Metric                             |
|------------------|----------------------------------|------------------------------------|
| AKS CPU/Memory   | Prometheus / Azure Monitor       | `container_cpu_usage_seconds_total` |
| AKS node count   | Kubernetes API                   | `kubectl get nodes`                 |
| Storage          | Azure Monitor                    | Disk utilisation %                  |
| Database         | Azure Monitor / pg_stat          | Connections, storage, IOPS          |
| Tenant growth    | Tenant registry                  | New tenant rate, tier distribution  |
| Historical spend | Azure Cost Management            | Resource usage trends               |

---

## Core Workflows

### 1. Current Headroom Check

```bash
# Cluster-level CPU and memory headroom
kubectl top nodes --use-protocol-buffers | \
  awk 'NR>1 {
    printf "Node: %-40s CPU: %s  Memory: %s\n", $1, $3, $5
  }'

# Allocatable vs requested per namespace
kubectl get pods -A -o json | jq -r '
  [.items[] | .spec.containers[].resources.requests // {}] |
  group_by(.namespace)? |
  .[] | {
    namespace: .[0].namespace,
    cpu_requested: ([.[].cpu // "0"] | map(gsub("m"; "") | tonumber) | add),
    memory_requested_mi: ([.[].memory // "0"] | map(gsub("Mi"; "") | tonumber) | add)
  }'

# Node autoscaler status
kubectl get configmap cluster-autoscaler-status \
  -n kube-system -o yaml | grep -A 30 "status:"
```

### 2. Time-Series Forecasting

Use historical Prometheus data to project future consumption:

```python
import requests
import pandas as pd
from prophet import Prophet

def forecast_resource(metric_query, horizon_days=90):
    # Pull 6 months of hourly data from Prometheus
    response = requests.get(f"{PROMETHEUS_URL}/api/v1/query_range", params={
        "query": metric_query,
        "start": (datetime.now() - timedelta(days=180)).isoformat(),
        "end": datetime.now().isoformat(),
        "step": "3600"  # hourly
    })

    data = response.json()["data"]["result"][0]["values"]
    df = pd.DataFrame(data, columns=["ds", "y"])
    df["ds"] = pd.to_datetime(df["ds"], unit="s")
    df["y"] = df["y"].astype(float)

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        changepoint_prior_scale=0.05
    )
    model.fit(df)

    future = model.make_future_dataframe(periods=horizon_days, freq="D")
    forecast = model.predict(future)
    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(horizon_days)

# Forecast cluster CPU utilisation
cpu_forecast = forecast_resource(
    'avg(rate(container_cpu_usage_seconds_total{container!=""}[1h]))'
)
```

### 3. Tenant Growth Modelling

```python
# Project new tenant count from historical growth rate
def project_tenant_growth(current_count, growth_rate_monthly, months=6):
    projections = []
    count = current_count
    for month in range(1, months + 1):
        count = count * (1 + growth_rate_monthly)
        projections.append({
            "month": month,
            "tenant_count": round(count),
            "estimated_nodes_needed": round(count * AVG_NODES_PER_TENANT),
            "estimated_cost_usd": round(count * AVG_COST_PER_TENANT_USD)
        })
    return projections
```

---

## Autoscaler Configuration Validation

```bash
# Check Horizontal Pod Autoscaler settings
kubectl get hpa -A -o json | jq -r '
  .items[] | {
    namespace: .metadata.namespace,
    name: .metadata.name,
    min_replicas: .spec.minReplicas,
    max_replicas: .spec.maxReplicas,
    current_replicas: .status.currentReplicas,
    current_cpu_pct: .status.currentMetrics[0]?.resource?.current?.averageUtilization,
    target_cpu_pct: .spec.metrics[0]?.resource?.target?.averageUtilization
  }'

# Validate Cluster Autoscaler is not bottlenecked
kubectl get events -n kube-system | grep -i "cluster-autoscaler" | tail -20
```

### HPA Best Practices Checklist
- `minReplicas` ≥ 2 for all production workloads (HA)
- `maxReplicas` set to handle 3× current peak
- CPU target: 60–70% (leave headroom for bursts)
- Memory-based HPA where CPU is not the bottleneck metric
- Custom metrics (queue depth, request rate) for async workloads

---

## Capacity Scenarios

Model three scenarios for the next 6 months:

```
Scenario A: Conservative (current growth rate)
  New tenants/month:       +8
  Node count in 6 months:  42 → 58
  Additional monthly cost: +$12,400

Scenario B: Target (planned sales pipeline)
  New tenants/month:       +15
  Node count in 6 months:  42 → 84
  Additional monthly cost: +$29,700
  ⚠️  Hits AKS cluster limit at month 4 → scale-out required

Scenario C: Spike (product launch event)
  Peak traffic multiplier: 5×  for 72h
  Burst nodes required:    +40 (handled by autoscaler)
  Pre-scale recommendation: provision buffer pool 24h before
```

---

## Database Capacity

```bash
# PostgreSQL storage trend
psql -h $DB_HOST -c "
  SELECT
    pg_size_pretty(pg_database_size(current_database())) AS db_size,
    pg_size_pretty(pg_total_relation_size('public.events')) AS events_table,
    (SELECT count(*) FROM pg_stat_activity) AS active_connections,
    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') AS max_connections;
"

# Project storage growth
# If growing at X GB/month, time to threshold =
# (threshold_gb - current_gb) / monthly_growth_gb
```

Alert thresholds:
- Storage > 75% → Warning → plan expansion
- Storage > 90% → Critical → immediate expansion
- Connections > 80% of max → Warning → tune pool or upgrade
- IOPS > 80% of limit → Warning → consider Premium storage tier

---

## Capacity Report Structure

```
Capacity Planning Report — Q[N] [Year]
────────────────────────────────────────

Executive Summary
  Cluster headroom (CPU):   32% available — HEALTHY
  Cluster headroom (Mem):   18% available — AT RISK (< 20% threshold)
  Storage headroom:         61% available — HEALTHY
  DB connection headroom:   44% available — HEALTHY

6-Month Forecast (Base Case)
  Tenant growth:   42 → 68 tenants (+62%)
  Node requirement: 58 nodes (current: 36)
  Action needed:   Provision 2 additional node pools by Week 8

Autoscaler Coverage
  Workloads with HPA:        28/34 deployments ✅
  Workloads without HPA:     6 (list attached)
  Cluster autoscaler status: Active, no scale-out failures

Recommended Actions (Priority)
  1. [HIGH] Add Standard_D8s_v3 node pool — 6 nodes by Week 8
  2. [HIGH] Enable HPA on 6 uncovered deployments
  3. [MED]  Upgrade Azure SQL SKU for tenant-42 before Week 6
  4. [LOW]  Review reserved capacity for base load nodes

Cost Forecast
  Current MRC:        $38,400
  Forecasted (Q3 end): $52,100 (+35.7%)
  RI opportunity:      $6,200/month savings available
```

---

## Examples

- "What is our current cluster headroom and when will we run out of capacity?"
- "Model how many nodes we need if we onboard 20 new enterprise tenants in Q3"
- "Check our autoscaler config — is everything properly set for production?"
- "Generate the quarterly capacity planning report for leadership"
- "Will our database handle a 5× traffic spike during the product launch?"

---

## Output Format

```json
{
  "snapshot_date": "ISO8601",
  "current_headroom": {
    "cpu_pct": 32,
    "memory_pct": 18,
    "storage_pct": 61,
    "db_connections_pct": 44
  },
  "forecast_horizon_days": 90,
  "scenarios": [],
  "recommended_actions": [],
  "autoscaler_issues": [],
  "estimated_cost_6m_usd": 0.0
}
```

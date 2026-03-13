---
name: cost-optimisation
description: >
  Use this skill to analyse, track, and reduce cloud infrastructure spend
  across Azure, AWS, and GCP. Triggers: any request to review cloud costs,
  identify waste or idle resources, right-size over-provisioned workloads,
  generate a cost report, set up budget alerts, optimise Reserved Instance
  or Savings Plan coverage, analyse cost per tenant, or produce recommendations
  for reducing monthly cloud spend.
tools:
  - bash
  - computer
---

# Cloud Cost Optimisation Skill

Automate cloud spend analysis, anomaly detection, waste elimination, and
right-sizing recommendations. Produce actionable cost reports by tenant,
environment, and service — with one-click remediation where safe to do so.

---

## Data Sources

| Platform | Tool / API                              | Auth env var                    |
|----------|-----------------------------------------|---------------------------------|
| Azure    | Azure Cost Management + Advisor API     | `AZURE_SUBSCRIPTION_ID`         |
| AWS      | Cost Explorer + Trusted Advisor         | `AWS_PROFILE`                   |
| GCP      | Cloud Billing API + Recommender API     | `GOOGLE_APPLICATION_CREDENTIALS`|
| Multi    | `infracost` (IaC cost estimation)       | `INFRACOST_API_KEY`             |
| Multi    | Kubecost (Kubernetes cost allocation)   | `KUBECOST_URL`                  |

---

## Core Workflows

### 1. Monthly Spend Summary

```bash
# Azure — total spend by resource group (last 30 days)
az consumption usage list \
  --start-date "$(date -d '-30 days' +%Y-%m-%d)" \
  --end-date "$(date +%Y-%m-%d)" \
  --query "sort_by([].{RG:resourceGroup, Cost:pretaxCost, Currency:currency}, &Cost)" \
  --output table

# AWS — top services by cost
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '-30 days' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE \
  --output json | jq '.ResultsByTime[0].Groups | sort_by(.Metrics.UnblendedCost.Amount | tonumber) | reverse'
```

### 2. Cost Per Tenant

```bash
# Kubecost — cost allocation by namespace (each namespace = one tenant)
curl -s "$KUBECOST_URL/model/allocation?window=30d&aggregate=namespace" | \
  jq '.data[0] | to_entries | sort_by(.value.totalCost) | reverse |
    .[] | {tenant: .key, cost_usd: .value.totalCost, cpu_cost: .value.cpuCost, memory_cost: .value.memoryCost}'
```

### 3. Idle & Orphaned Resource Detection

```bash
# Azure — unattached managed disks
az disk list --query "[?diskState=='Unattached'].{Name:name, SizeGB:diskSizeGb, SKU:sku.name}" \
  --output table

# Azure — unused public IPs
az network public-ip list \
  --query "[?ipConfiguration==null].{Name:name, RG:resourceGroup}" \
  --output table

# Azure — stopped (deallocated) VMs older than 30 days
az vm list --show-details \
  --query "[?powerState=='VM deallocated'].{Name:name, RG:resourceGroup, Size:hardwareProfile.vmSize}" \
  --output table

# Azure — unused load balancers (no backend pools)
az network lb list --query "[?backendAddressPools[0]==null].name" --output tsv

# Kubernetes — pods with no CPU/memory requests set
kubectl get pods -A -o json | \
  jq -r '.items[] | select(.spec.containers[].resources.requests == null) |
    "\(.metadata.namespace)/\(.metadata.name)"'
```

### 4. Right-Sizing Recommendations

```bash
# Azure Advisor — cost recommendations
az advisor recommendation list \
  --category Cost \
  --query "[].{Impact:impact, Resource:resourceMetadata.resourceId, Recommendation:shortDescription.solution}" \
  --output table

# AWS Compute Optimizer
aws compute-optimizer get-ec2-instance-recommendations \
  --query 'instanceRecommendations[?findingReasonCodes[0]==`CPUUnderprovisioned` ||
            findingReasonCodes[0]==`Overprovisioned`]' \
  --output json
```

### 5. Reserved Instance / Savings Plan Coverage

```bash
# AWS — RI coverage report
aws ce get-reservation-coverage \
  --time-period Start=$(date -d '-30 days' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --output json | jq '.CoveragesByTime[0].Total.CoverageHours.CoverageHoursPercentage'

# Target: ≥ 70% coverage for predictable workloads (dev/staging excluded)
```

---

## Auto-Remediation Actions

Actions that can run automatically (with tagging/logging):

| Action                          | Auto-safe | Estimated saving    |
|---------------------------------|-----------|---------------------|
| Delete unattached disks (>14d)  | ✅        | $5–50/disk/month    |
| Release unused public IPs       | ✅        | $3–7/IP/month       |
| Scale down over-provisioned pods | ✅       | Varies              |
| Delete orphaned snapshots (>90d)| ✅        | $0.05/GB/month      |
| Stop idle dev VMs (after hours) | ✅        | 65% of compute cost |
| Downsize right-size candidates  | ⚠️ Needs approval | 20–40% per resource |
| Purchase Reserved Instances     | ⚠️ Needs approval | 30–60% vs on-demand |
| Delete stopped VMs (>30d)       | ⚠️ Needs approval | 100% of disk cost   |

---

## Budget Alerting

```bash
# Azure — create budget with alert
az consumption budget create \
  --budget-name "monthly-budget-${ENV}" \
  --amount $BUDGET_AMOUNT \
  --category Cost \
  --time-grain Monthly \
  --start-date "$(date +%Y-%m-01)" \
  --end-date "$(date -d '+12 months' +%Y-%m-01)" \
  --threshold 80 \
  --contact-emails "$ALERT_EMAIL" \
  --contact-groups "$ACTION_GROUP_ID"
```

Alert thresholds:
- 80% of monthly budget → email warning
- 100% of monthly budget → email + Slack page
- 120% of monthly budget → P2 incident, escalate to leadership

---

## FinOps Report Structure

```
Cloud Cost Report — [Month Year]
──────────────────────────────────

Total Spend:        $XX,XXX  (+/-X% vs last month)
Budget:             $XX,XXX  (XX% consumed)
Forecast (EOM):     $XX,XXX  (XX% of budget)

Top 5 Cost Drivers
  1. AKS Compute (prod)          $X,XXX  (XX%)
  2. Azure SQL (enterprise tier) $X,XXX  (XX%)
  ...

Cost by Tenant (Top 10)
  tenant-42 (enterprise):  $XXX/month  ($X.XX/user)
  ...

Waste Identified & Remediated
  Unattached disks deleted:    12  → saved $XXX/month
  Idle public IPs released:    8   → saved $XXX/month
  Dev VMs auto-stopped:        22  → saved $XXX/month

Recommendations (pending approval)
  Right-size 4 over-provisioned AKS node pools → save ~$X,XXX/month
  Purchase 12-month RIs for stable workloads   → save ~$X,XXX/month

RI/Savings Plan Coverage:  68%  (target 70%)

Cost Trend (6-month)
  [chart data]
```

---

## IaC Cost Estimation (Pre-Deploy)

```bash
# Estimate cost of a Terraform plan before applying
infracost breakdown --path ./terraform \
  --var-file env/prod.tfvars \
  --format json > cost-estimate.json

infracost diff --path ./terraform \
  --compare-to cost-estimate-baseline.json
```

Surface cost delta in every PR that modifies infrastructure.

---

## Examples

- "Show me our total cloud spend by tenant for the last 30 days"
- "Find all idle and orphaned resources across our Azure subscriptions"
- "Generate the monthly FinOps report with recommendations"
- "What is the cost difference if we right-size the AKS node pools?"
- "Set up budget alerts at 80% and 100% for the prod subscription"
- "What's our Reserved Instance coverage and where should we buy more?"

---

## Output Format

```json
{
  "period": { "start": "string", "end": "string" },
  "total_spend_usd": 0.0,
  "budget_usd": 0.0,
  "budget_consumed_pct": 0.0,
  "waste_identified_usd": 0.0,
  "waste_remediated_usd": 0.0,
  "top_tenants": [],
  "recommendations": [],
  "ri_coverage_pct": 0.0,
  "report_url": "string"
}
```

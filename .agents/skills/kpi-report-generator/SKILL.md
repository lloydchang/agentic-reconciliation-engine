---
name: kpi-report-generator
description: >
  Use this skill to automatically collect, aggregate, and generate KPI and
  quarterly progress reports for teams. Triggers:
  any request to generate a platform report, build a quarterly review,
  calculate DORA metrics, summarise operational health, produce an executive
  dashboard, or track progress against OKRs and roadmap milestones.
tools:
  - bash
  - computer
---

# KPI Report Generator Skill

Automate the collection and presentation of Cloud AI platform KPIs: pull
data from observability, CI/CD, incident, and deployment systems → aggregate
→ trend → present as a structured report in Markdown, HTML, or PPTX.

# KPI Report Generator Skill

Automate the collection and presentation of Cloud AI platform KPIs: pull
data from observability, CI/CD, incident, and deployment systems → aggregate
→ trend → present as a structured report in Markdown, HTML, or PPTX.

## Enhanced Executive Status Reporting

### Generate Executive Progress Reports Summarizing Health and Project Milestones
Generate executive progress reports summarizing health and project milestones for leadership communication.

**Purpose:** Communicate operational progress and business outcomes to leadership.

**Workflow:**
1. Aggregate comprehensive operational metrics across all systems
2. Summarize incident impact and resolution trends
3. Evaluate roadmap progress against milestones and timelines
4. Identify key risks and mitigation strategies
5. Generate executive-ready report with actionable insights

**Output:** Quarterly executive report including KPI summary, major milestones achieved, current risks, and strategic recommendations.

---

## Data Sources

| KPI category            | Source system                      | Query method         |
|-------------------------|------------------------------------|----------------------|
| Uptime / availability   | Prometheus, Azure Monitor          | PromQL / REST API    |
| Deployment metrics      | ArgoCD, GitHub Actions, ADO        | API / webhooks       |
| Incident metrics        | PagerDuty, ServiceNow              | REST API             |
| Change fail rate        | Deployment ledger                  | DB query             |
| Platform adoption       | Usage telemetry, feature flags     | REST API / SQL       |
| Security / compliance   | Scanner results, audit logs        | File / API           |
| Cost                    | Azure Cost Management, AWS CE      | REST API             |

---

## Standard KPI Set

### DORA Metrics (Engineering Throughput)
```
Deployment Frequency:   deployments per day/week (elite ≥ 1/day)
Lead Time for Change:   commit → production (elite < 1 hour)
Change Failure Rate:    failed deployments / total (elite < 5%)
MTTR:                   time to restore service (elite < 1 hour)
```

### Reliability Metrics
```
Platform uptime %       (vs SLA target)
Error budget remaining  (% remaining for current month)
P1/P2 incident count    (count, trend)
Mean MTTR by severity   (minutes)
Incidents auto-resolved by runbook (%)
```

### Platform Adoption Metrics
```
Teams onboarded to platform / total target (%)
Deployments via standard pipelines vs manual (%)
IaC coverage: resources managed by Terraform (%)
Tenant onboarding time: median days
Runbook coverage: % incidents with runbook
```

### Security & Compliance
```
Critical/High CVEs open            (count, SLA adherence %)
Secret scan violations (30d)       (count)
CIS benchmark score                (% passing)
Compliance report status           (SOC2 / ISO / CIS)
```

### Cost & Efficiency
```
Cloud spend (month-over-month %)
Cost per tenant                    (avg, by tier)
Resource utilisation: AKS CPU/Mem  (avg %)
Idle / orphaned resource cost      ($)
```

---

## Report Types

### 1. Weekly Ops Snapshot (Markdown → Slack)
```
🟢 Platform Health — Week of [DATE]

Uptime:          99.96% (target 99.9%) ✅
Deployments:     47 total, 46 success (97.9%) ✅
Incidents:       3 (P2×1, P3×2) — MTTR avg 22min ✅
Error budget:    73% remaining (enterprise tier)
Open CVEs (High+): 2 (both in remediation)

Top action this week: Canary failure on payments-api v2.3.1 → rolled back,
root cause identified, fix in review.
```

### 2. Monthly Executive Report (PPTX/PDF)
Structure:
- Slide 1: Executive summary scorecard (Red/Amber/Green per KPI)
- Slide 2: DORA metrics with trend (90-day)
- Slide 3: Reliability & SLA status
- Slide 4: Platform adoption progress
- Slide 5: Security posture
- Slide 6: Cost summary
- Slide 7: Roadmap milestone status (30/60/90 day plan)
- Slide 8: Top risks & mitigations
- Slide 9: Next 30 days priorities

### 3. Quarterly Business Review (QBR)
Extends monthly report with:
- OKR scoring (0.0–1.0 per objective)
- Year-to-date trends
- Comparison vs industry benchmarks (DORA State of DevOps data)
- Budget vs actuals
- Headcount and team capacity

---

## Data Collection Script

```bash
#!/usr/bin/env bash
# Collect all KPI data for the reporting period
PERIOD_START="${1:-$(date -d '-30 days' +%Y-%m-%d)}"
PERIOD_END="${2:-$(date +%Y-%m-%d)}"

# DORA — deployment frequency
DEPLOYS=$(curl -s "$ARGOCD_URL/api/v1/applications" \
  | jq "[.items[].status.history[] | select(.deployedAt >= \"$PERIOD_START\")] | length")

# DORA — change fail rate
FAILED=$(sqlite3 deployment.db \
  "SELECT COUNT(*) FROM deployments WHERE status='rolled_back' AND date >= '$PERIOD_START'")
TOTAL=$(sqlite3 deployment.db \
  "SELECT COUNT(*) FROM deployments WHERE date >= '$PERIOD_START'")
CFR=$(echo "scale=2; $FAILED / $TOTAL * 100" | bc)

# Uptime — from Prometheus
UPTIME=$(curl -s "$PROMETHEUS_URL/api/v1/query" \
  --data-urlencode "query=avg_over_time(up{job='platform'}[30d])*100" \
  | jq '.data.result[0].value[1]')

echo "{\"period_start\":\"$PERIOD_START\",\"period_end\":\"$PERIOD_END\",
      \"deployments\":$DEPLOYS,\"change_fail_rate\":$CFR,\"uptime\":$UPTIME}"
```

---

## Trend Calculation

For each metric, compute:
- Current period value
- Previous period value
- % change (positive/negative)
- 90-day rolling average
- RAG status (Red/Amber/Green) vs target

```python
def rag_status(value, target, higher_is_better=True):
    ratio = value / target
    if higher_is_better:
        if ratio >= 1.0: return "GREEN"
        if ratio >= 0.9: return "AMBER"
        return "RED"
    else:  # lower is better (e.g. incident count)
        if ratio <= 1.0: return "GREEN"
        if ratio <= 1.2: return "AMBER"
        return "RED"
```

---

## Examples

- "Generate the weekly platform health snapshot for Slack"
- "Build the monthly executive report for June as a PowerPoint"
- "What are our DORA metrics for Q2 vs Q1?"
- "Show me platform adoption progress — what % of teams are on the standard pipeline?"
- "Create the QBR deck for the team"

---

## Output Format

```json
{
  "report_type": "weekly|monthly|quarterly",
  "status": "success|failure",
  "period": { "start": "ISO8601", "end": "ISO8601" },
  "metrics": {
    "uptime_pct": 0.0,
    "deployment_frequency": 0.0,
    "change_fail_rate_pct": 0.0,
    "mttr_minutes": 0.0,
    "platform_adoption_pct": 0.0,
    "open_high_cves": 0,
    "cost_delta_pct": 0.0
  },
  "rag_statuses": {},
  "report_url": "string"
}
```

---
name: sla-monitoring-alerting
description: >
  Use this skill to define, monitor, and report on platform SLAs and SLOs for
  uptime, deployment success, incident response, and performance. Triggers:
  requests to check SLA status, calculate SLO error budgets, set up alerting
  thresholds, generate SLA compliance reports, detect SLA breaches, or review
  operational reliability metrics across tenants and environments.
tools:
  - bash
  - computer
---

# SLA Monitoring & Alerting Skill

Implement and operate a full SLO/SLA measurement stack: define objectives,
calculate error budgets, alert on burn-rate, and produce executive-ready
compliance reports.

# SLA Monitoring & Alerting Skill

Implement and operate a full SLO/SLA measurement stack: define objectives,
calculate error budgets, alert on burn-rate, and produce executive-ready
compliance reports.

## Enhanced SLA Monitoring

### Monitor Uptime, Deployment Success, and Incident Response SLAs
Monitor uptime, deployment success, and incident response SLAs to ensure reliability.

**Purpose:** Ensure operational reliability and SLA compliance.

**Key Metrics:**
- Uptime percentage across services and infrastructure
- Deployment success rate and failure patterns
- Mean time to recovery (MTTR) for incidents
- Error rates and availability targets

**Workflow:**
1. Collect comprehensive metrics from monitoring systems
2. Compare current performance against defined SLA thresholds
3. Calculate error budgets and burn rates
4. Trigger alerts when SLA violations are imminent
5. Generate SLA dashboard with real-time status

**Output:** SLA dashboard with uptime metrics, deployment success rates, incident response times, error budgets, and compliance status.

---

## SLA / SLO Definitions

### Platform SLAs (defaults — override per tier)

| SLA                         | Starter | Business | Enterprise |
|-----------------------------|---------|----------|------------|
| Monthly uptime              | 99.5%   | 99.9%    | 99.99%     |
| Deployment success rate     | 95%     | 98%      | 99.5%      |
| P1 incident response        | 1 hr    | 30 min   | 15 min     |
| P2 incident response        | 4 hr    | 2 hr     | 30 min     |
| RTO (recovery time)         | 4 hr    | 2 hr     | 30 min     |
| RPO (data loss window)      | 24 hr   | 4 hr     | 1 hr       |
| Change fail rate            | <20%    | <10%     | <5%        |

### SLO → Error Budget Calculation

```
Error budget (monthly) = (1 - SLO_target) × total_minutes_in_month

Example (99.9% uptime, 30-day month):
  total_minutes = 43,200
  error_budget   = 0.001 × 43,200 = 43.2 minutes
```

---

## Data Sources

Configure via environment variables:

| Source               | Env var                    | Metric types                  |
|----------------------|----------------------------|-------------------------------|
| Prometheus           | `PROMETHEUS_URL`           | Uptime, latency, error rate   |
| Azure Monitor        | `AZURE_MONITOR_WORKSPACE`  | Resource health, platform     |
| DataDog              | `DD_API_KEY`               | APM, synthetics, logs         |
| PagerDuty            | `PD_API_KEY`               | Incident response times       |
| ArgoCD               | `ARGOCD_TOKEN`             | Deployment success rate       |
| Custom webhook       | `SLA_WEBHOOK_URL`          | Any metric via POST           |

---

## Core Workflows

### Real-Time SLO Dashboard Query
```bash
# Uptime — availability over 30 days
curl -s "$PROMETHEUS_URL/api/v1/query" \
  --data-urlencode 'query=avg_over_time(up{job="api"}[30d]) * 100'

# Error rate
curl -s "$PROMETHEUS_URL/api/v1/query" \
  --data-urlencode 'query=sum(rate(http_requests_total{status=~"5.."}[5m])) /
    sum(rate(http_requests_total[5m])) * 100'

# Deployment success rate (ArgoCD)
argocd app list --output json | jq '[.[] | .status.sync.status] |
  (map(select(. == "Synced")) | length) / length * 100'
```

### Error Budget Burn Rate Alerting

```yaml
# Prometheus alerting rules
groups:
  - name: slo_alerts
    rules:
      - alert: HighErrorBudgetBurnRate
        expr: |
          (
            sum(rate(http_requests_total{status=~"5.."}[1h])) /
            sum(rate(http_requests_total[1h]))
          ) > 14.4 * (1 - 0.999)
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error budget burning at 14.4x normal rate — P1 action required"

      - alert: MediumErrorBudgetBurnRate
        expr: |
          (
            sum(rate(http_requests_total{status=~"5.."}[6h])) /
            sum(rate(http_requests_total[6h]))
          ) > 6 * (1 - 0.999)
        for: 15m
        labels:
          severity: warning
```

### SLA Breach Detection
```python
def check_sla_breach(tenant_id, slo_target, current_availability):
    error_budget_remaining = calculate_remaining_budget(tenant_id, slo_target)
    if error_budget_remaining <= 0:
        return "BREACHED"
    elif error_budget_remaining < 0.1 * total_budget:
        return "AT_RISK"
    else:
        return "OK"
```

On breach: page on-call, notify tenant account manager, log to SLA ledger.

---

## Alerting Channels

Route alerts based on severity and team:

```yaml
routes:
  - match:
      severity: critical
    receiver: pagerduty-p1
  - match:
      severity: warning
      team: warning-team
    receiver: slack-warning-team
  - match:
      severity: info
    receiver: slack-alerts-general

receivers:
  - name: pagerduty-p1
    pagerduty_configs:
      - routing_key: $PD_ROUTING_KEY
        severity: critical
  - name: slack-warning-team
    slack_configs:
      - api_url: $SLACK_WEBHOOK
        channel: '#warning-alerts'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

---

## SLA Compliance Report

Weekly/monthly report structure:
```
SLA Compliance Report — [Month Year]
─────────────────────────────────────
Platform Uptime
  Target:  99.9%
  Actual:  99.94% ✅
  Budget used: 18.7 min of 43.2 min available

Deployment Success Rate
  Target:  98%
  Actual:  97.1% ⚠️  (2 failed deployments in window)

Incident Response Compliance
  P1 — 4 incidents: 4/4 within SLA ✅
  P2 — 11 incidents: 10/11 within SLA (1 breach logged) ⚠️

Top Incidents by Downtime
  1. AKS node pool exhaustion — 12 min — tenant-42
  2. DB failover — 6 min — tenant-91

Error Budget Trend (90 days)
  [chart data]
```

---

## Examples

- "What is our current error budget status for the enterprise tier?"
- "Set up burn-rate alerting for 99.9% uptime SLO on the payments API"
- "Generate the monthly SLA compliance report for June"
- "Which tenants are closest to an SLA breach this month?"
- "Show me MTTR trends for P1 incidents over the last quarter"

---

## Output Format

```json
{
  "tier": "string",
  "budget_remaining_pct": 0.0,
  "report_period": "string",
  "slo_name": "string",
  "target_pct": 99.9,
  "actual_pct": 99.94,
  "status": "ok|at_risk|breached",
  "error_budget_minutes_total": 43.2,
  "error_budget_minutes_used": 18.7,
  "error_budget_pct_remaining": 56.7,
  "incidents": [],
  "trend_90d": []
}
```

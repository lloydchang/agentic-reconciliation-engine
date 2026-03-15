---
name: cost-optimisation
description: >
  Analyze cloud spend, detect waste, and drive optimization recommendations with AI risk scoring and dispatcher telemetry.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Cost Optimisation — World-class FinOps Playbook

Analyzes cloud billing/usage, scans for waste, enforces budgets, and recommends optimisations (right-sizing, RI/SP purchases). Provides AI risk signals, structured reports, and shared-context outputs for other skills.

## When to invoke
- Produce monthly FinOps reports or ad-hoc cost summaries.
- Identify idle/orphaned resources and actionable savings.
- Enforce budget alerts and right-size underutilised workloads.
- Collaborate with dispatchers (`capacity-alert`, `policy-risk`, `incident-ready`) to align cost changes with incidents or compliance.

## Capabilities
- Multi-cloud cost data ingestion (Azure, AWS, GCP, Kubecost, Infracost).
- AI risk scoring for cost anomalies and high-impact recommendations.
- Budget alert configuration and automated remediation actions.
- Shared context `shared-context://memory-store/cost-optimisation/<operationId>`.

## Invocation patterns

```bash
/cost-optimisation report --period=30d --format=json
/cost-optimisation analyze --target=prod --framework=optimization
/cost-optimisation detect --threshold=critical --silent=false
/cost-optimisation budget --env=prod --threshold=80 --notify=slack
/cost-optimisation recommend --target=eks-cluster --type=right-size
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `period` | Reporting window. | `30d` |
| `target` | Scope (tenant, cluster, subscription). | `prod` |
| `threshold` | Severity threshold (critical/high/medium). | `critical` |
| `env` | Environment tag. | `prod` |
| `type` | Recommendation type (right-size, ri, purge). | `right-size` |
| `framework` | Analysis mode (usage, optimisation, forecast). | `optimisation` |

## Output contract

```json
{
  "operationId": "CO-2026-0315-01",
  "status": "success|failure",
  "reportType": "usage|optimisation",
  "period": { "start": "2026-02-15", "end": "2026-03-15" },
  "totalSpendUsd": 123456,
  "budgetUsd": 130000,
  "budgetConsumedPct": 95,
  "wasteIdentifiedUsd": 5400,
  "wasteRemediatedUsd": 3200,
  "topTenants": [
    { "tenant": "tenant-42", "spend": 18000 }
  ],
  "recommendations": [
    {
      "id": "RECO-2026-01",
      "type": "right-size",
      "resource": "aks-tenant-42-prod",
      "monthlySavingsUsd": 260,
      "riskScore": 0.28,
      "status": "pending-approval"
    }
  ],
  "aiInsights": {
    "riskScore": 0.35,
    "trend": "costs stable vs last month"
  },
  "reportUrl": "https://reports/cost/CO-2026-0315-01",
  "decisionContext": "redis://memory-store/cost-optimisation/CO-2026-0315-01",
  "logs": "shared-context://memory-store/cost-optimisation/CO-2026-0315-01"
}
```

## World-class workflow templates

### Spend analysis & reporting
1. Gather spend data (Azure consumption, AWS CE, GCP billing, Kubecost/K8s).
2. Compute budgets/ratios, DORA correlation, and adoption metrics.
3. Generate reports (monthly FinOps, ad-hoc) with RAG statuses.
4. Emit `cost-report` event with structured data.

### Waste detection & remediation
1. Identify idle disks/IPs, orphaned snapshots, oversized VMs.
2. Apply auto-remediation (delete, downscale) where safe; flag for manual review per policy.
3. Emit `cost-remediation` events and link to `incident-triage` when risk high.

### Budget enforcement
1. Configure budgets (Azure, AWS, GCP) with 80/100/120% thresholds.
2. Trigger alerts and escalate when budgets breached.
3. Provide recommendations to reduce spend or pause resources.

## AI intelligence highlights
- **AI Risk Scoring**: ranks recommendations by savings, risk, effort, and tenant impact.
- **Predictive Forecasting**: anticipates spend using trend models and confidence intervals.
- **Intelligent ROI Validation**: compares savings vs implementation cost/time.

## Memory agent & dispatcher integration
- Persist context to `shared-context://memory-store/cost-optimisation/<operationId>`.
- Emit events: `cost-report`, `cost-anomaly`, `cost-recommendation`, `budget-alarm`.
- Respond to dispatcher signals (`capacity-alert`, `policy-risk`) for quick cost gating.
- Tag metadata with `decisionId`, `tenant`, `riskScore`.

## Communication protocols
- Primary: CLI/Azure/AWS/GCP APIs, Infracost, Kubecost.
- Secondary: Event bus for `cost-*` events.
- Fallback: JSON artifacts at `artifact-store://cost-optimisation/<operationId>.json`.

## Observability & telemetry
- Metrics: spend per window, budget hits, remediation success, riskScore trends.
- Logs: structured `log.event="cost.operation"` with `operationId`.
- Dashboards: integrate `/cost-optimisation metrics --format=prometheus`.
- Alerts: budget >100%, multiple remediation failures, riskScore ≥ 0.85.

## Failure handling & retries
- Retry API calls (budget, scan) up to 2× on transient errors.
- On failure, log context, emit `cost-operation-failed`, escalate to `incident-triage-runbook`.
- Retain artifacts/logs until downstream ack.

## Human gates
- Required when:
 1. Recommendations impact production-critical workloads or budgets >$100k.
 2. Auto-remediation touches reserved resources.
 3. Dispatcher demands manual review after repeated alerts.
- Use standard human gate template capturing impact/reversibility.

## Testing & validation
- Dry-run: `/cost-optimisation report --period=30d --dry-run`.
- Unit tests: `backend/cost/` ensures forecasting & scoring logic accuracy.
- Integration: `scripts/validate-cost-optimisation.sh` runs report → remediation flows.
- Regression: nightly `scripts/nightly-cost-smoke.sh` keeps thresholds and alerts stable.

## References
- Scripts: `scripts/cost/`.
- Templates: `templates/cost-report.md`.
- Dashboards: `monitoring/grafana/cost`.

## Related skills
- `/finops`: not existing, but aggregator.
- `/incident-triage-runbook`: triggered by cost anomalies.
- `/ai-agent-orchestration`: orchestrates cost workflows with others.

---
name: cost-optimization
description: Optimize cloud spend with AI-driven insights, forecasting, ROI validation, and risk-balanced recommendations.
argument-hint: "[targetResource] [analysisType] [timeframe]"
context: fork
agent: Plan
disable-model-invocation: false
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
---

# Cost Optimization — World-class AI Cost Control Playbook

Uses specialized AI subagents to understand cost patterns, forecast spend, validate ROI, and balance risk/benefit for every recommendation. Trigger this skill anytime you need spend visibility, automated savings, or approval-ready optimization plans.

## When to invoke
- Detect anomalies in cost telemetry (budget burn, unexpected spikes, forecast drifting).
- Pre-change reviews for sizing, autoscaling, tier moves, or new service rollouts.
- Scheduled optimization cycles (daily anomaly scan, monthly forecast, quarterly roadmap).
- Dispatcher events from memory agents tagging `cost_spike`, `waste_opportunity`, `riskScore`.

## Capabilities
- **AI Cost Pattern Recognition**: identifies seasonality, waste, unused resources, and trends per tenant or service.
- **Intelligent Forecasting**: predicts spending with ensembles (linear, random forest, LSTM) and confidence intervals.
- **ROI Validation**: compares savings vs implementation cost over 6-12 month horizon.
- **Risk-Benefit Analysis**: weights savings against business impact, compliance, and performance risks.
- Toolchain: `bill-export`, Prometheus metrics, cloud cost APIs, and resource tagging metadata.
- Integration with dispatcher and shared context so downstream skills (deployment, incident) understand cost implications.

## Invocation patterns

```bash
/cost-optimization analyze --target=production-cluster --analysisType=full --timeframe=30d
/cost-optimization anomalies --target=tenant-42 --riskThreshold=high
/cost-optimization forecast --target=all-resources --horizon=90d --confidence=95
/cost-optimization roi --target=eks-cluster --recommendation=autoscaler-optimization
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `target` | Tenant, cluster, or account scope. | `production-cluster` |
| `analysisType` | `usage|optimization|forecast|full`. | `full` |
| `timeframe` | Lookback window for analysis. | `90d` |
| `horizon` | Forecast horizon (days). | `90` |
| `confidence` | Forecast confidence level (percent). | `95` |
| `riskThreshold` | Filter for high/medium/low risk recommendations. | `high` |

## Output contract

```json
{
  "workflowId": "COST-2026-0412",
  "status": "completed",
  "analysisType": "full",
  "timeframe": "30d",
  "forecasts": [
    {
      "model": "lstm",
      "horizonDays": 90,
      "mean": 123456.78,
      "confidenceInterval": [118000, 129000]
    }
  ],
  "recommendations": [
    {
      "id": "RECO-001",
      "type": "right-size",
      "resource": "vm-prod-3",
      "monthlySavings": 260,
      "riskScore": 22,
      "implementationCost": 0,
      "roiMonths": 0.2,
      "status": "pending-approval"
    }
  ],
  "executiveSummary": {
    "currentSpend": 385000,
    "projectedSavings12m": 54000,
    "roi": 4.2,
    "riskLevel": "Medium"
  },
  "metrics": {
    "costPatternConfidence": 0.92,
    "forecastError": 0.04
  },
  "logs": "shared-context://memory-store/cost/COST-2026-0412"
}
```

## World-class workflow templates

### AI cost pattern recognition & anomaly detection
1. Collect billing, metric, and tagging data.
2. Analyze seasonality, growth, and drift using classification trees and time-series ensembles.
3. Tag anomalies with `riskScore`, `impact`, `tenant`, `region`.
4. Emit `cost-anomaly` event for dispatcher to trigger remediation/clamp.

### Intelligent forecasting & ROI validation
1. Generate forecasts using ensemble models (linear, random forest, LSTM) with `confidenceInterval`.
2. Validate ROI for each recommendation (savings、implementation cost、risk).
3. Prioritize recommendations by ROI × risk-adjusted impact.
4. Surface to stakeholders with predicted savings, confidence, and acceptance criteria.

### Risk-benefit planning
1. Apply business-impact heuristics (performance, compliance, availability) to each plan.
2. If risk > threshold, route to human gate via `/stakeholder-comms-drafter`.
3. Otherwise, mark as `auto-approved` and forward to `/deployment-validation` or orchestration for execution.

## AI intelligence highlights
- **AI Cost Pattern Recognition** uses historical/predictive models to spot waste, underutilized resources, and misconfigurations at tenant/service granularity.
- **Intelligent Forecasting** ensembles deliver predicted spend with confidence intervals, error metrics, and explainability signals for trust.
- **ROI Validation** compares savings vs implementation/effort cost to produce `roiMonths`, `monthlySavings`, and risk-adjusted impact so stakeholders can prioritize.
- **Risk-Benefit Analysis** weights business impact, compliance exposure, and latency penalties before recommending auto-approved actions or human gates.

## Memory agent & dispatcher integration
- Store normalized cost summaries under `shared-context://memory-store/cost/{workflowId}` for reuse across skills.
- Emit `cost-recommendation-ready`, `cost-anomaly`, and `cost-forecast` events; subscribe to `agent-completed` and `human-gate-cleared` events for enrichment.
- Tag telemetry with `decisionId`, `orchestrationId`, `tenant`, `riskScore`, `confidence`, and `modelVersion` so downstream listeners can reconstruct the rationale.

## Observability & telemetry
- Export metrics: savings identified, forecast accuracy (MAPE), recommendations accepted, risk score distribution, forecast deviation alerts.
- Logs: structured `log.event="cost.analysis"` with `decisionId`, `model`, `confidence`, `tenant`, and `workflowId`.
- Dashboards: hook `/cost-optimization metrics --format=prometheus` into Grafana panels and expose confidence/risk heatmaps.
- Alerts: >5% daily forecast deviation, >3 consecutive rejected recommendations, missing billing exports, or dependency access failures.

## Failure handling & retries
- Retry data collection/API failures with exponential backoff (1m → 5m) up to 3 attempts before flagging for manual review.
- On persistent missing data, fall back to the last confirmed baseline, annotate the forecast with `dataIntegrity=false`, and notify stakeholders.
- Preserve intermediate datasets for audits (`reports/cost/{workflowId}`) and avoid deletion until downstream workflows acknowledge completion.

## Human gates
- Required when:
 1. `riskScore ≥ 70` or >20 tenants affected.
 2. ROI period exceeds 12 months or business impact is production-critical.
 3. Recommendation touches sensitive controls (security, compliance, SLA).
- Confirmation template matches the orchestrator human gate pattern and is stored in `shared-context://memory-store/human-gates/{workflowId}`.

## Testing & validation
- Dry-run: `/cost-optimization analyze --target=test-cluster --analysisType=usage --dry-run=true`.
- Unit tests: `backend/cost/models` ensures forecasting accuracy, ROI logic, and risk thresholds.
- Integration: `scripts/validate-cost-workflow.sh` verifies dispatch events, shared context updates, and human gate triggers.
- Regression: nightly `scripts/nightly-cost-smoke.sh` ensures forecasts stay within tolerance and recommendations trigger downstream skills.

## References
- Forecast models: `backend/cost/models/`.
- Reports: `reports/cost/`.
- Orchestrator integration: `backend/orchestration/dispatcher/cost-recommendations`.

## Related skills
- `/ai-agent-orchestration`: receives `cost-anomaly` events and routes skills.
- `/deployment-validation`: receives `go/no-go` insights for new optimizations.
- `/workflow-management`: monitors approval workflows and actualization.

---
name: kpi-report-generator
description: >
  Collect, aggregate, and deliver KPI/exec reports with AI trending, RAG scoring, and dispatcher telemetry.
allowed-tools:
  - Bash
  - Read
  - Write
---

# KPI Report Generator — World-class Insight Playbook

Aggregates telemetry from observability, CI/CD, incidents, governance, and cost into weekly/monthly/quarterly executive reports (Markdown/PPTX/HTML) with AI risk insights, RAG indicators, and shared-context metadata. Use when summarizing health, DORA metrics, adoption, security posture, or cost/OKR progress.

## When to invoke
- Generate weekly ops snapshots, monthly exec reports, QBR decks, or ad-hoc KPI summaries.
- Calculate DORA metrics, reliability, adoption, compliance, and cost indicators.
- Combine high-risk insights from dispatchers (`incident-ready`, `policy-risk`, `capacity-alert`).
- Feed structured reports into leadership, auditing, or automation channels.

## Capabilities
- Pull data from Prometheus, Azure Monitor, CI/CD platforms, incident DB, compliance sources, and billing.
- AI RAG scoring using historical trends and target baselines.
- Export results to Markdown/HTML/PPTX with narrative, charts, and embedded links.
- Shared context `shared-context://memory-store/kpi/<operationId>` for downstream workflows.
- Human gates for sensitive executive distributions or strategic decisions.

## Invocation patterns

```bash
/kpi-report-generator report --type=weekly --window=7d --format=markdown
/kpi-report-generator report --type=monthly --format=pptx --output=reports/monthly.pptx
/kpi-report-generator metrics --include=dora,uptime,cost --period=30d
/kpi-report-generator trends --window=90d --focus=incident-metrics
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `type` | Report type (weekly/monthly/quarterly). | `monthly` |
| `window` | Lookback window (days). | `30d` |
| `format` | Output format (`markdown|html|pptx`). | `pptx` |
| `include` | Metric subsets (dora, uptime, security). | `dora,security` |
| `period` | Time span for KPIs. | `90d` |
| `focus` | Specific area (incident, cost, adoption). | `incident-metrics` |

## Output contract

```json
{
  "operationId": "KPI-2026-0315-01",
  "status": "success|failure",
  "reportType": "weekly",
  "period": { "start": "2026-02-15", "end": "2026-03-15" },
  "metrics": {
    "uptimePct": 99.96,
    "deploymentFrequency": 12,
    "changeFailRatePct": 4,
    "mttrMinutes": 15,
    "platformAdoptionPct": 82,
    "openHighCves": 2,
    "costDeltaPct": -3
  },
  "ragStatuses": {
    "uptime": "GREEN",
    "changeFailRate": "AMBER",
    "cost": "GREEN"
  },
  "aiInsights": {
    "riskScore": 0.41,
    "trend": "lead time improving vs last month"
  },
  "reportUrl": "https://reports/kpi/KPI-2026-0315-01",
  "decisionContext": "redis://memory-store/kpi/KPI-2026-0315-01",
  "logs": "shared-context://memory-store/kpi/KPI-2026-0315-01"
}
```

## World-class workflow templates

### Weekly ops snapshot (Markdown/Slack)
1. Pull DORA, reliability, incident, adoption, security, cost metrics.
2. Compute RAG statuses vs targets and include narrative on top trends.
3. Export summary and push to Slack or email stakeholders.
4. Emit `kpi-report-ready` event with links for dispatcher to react.

### Monthly executive report (PPTX/HTML)
1. Compose slides covering executive summary, DORA, reliability, adoption, security, cost, roadmap.
2. Include AI insights (riskScore, trend direction, anomalies).
3. Attach supporting dashboards and evidence (KQL queries, cost exports).
4. Emit structured JSON for automation and store context for follow-ups.

### Quarterly business review (QBR)
1. Extend monthly content with OKR scoring, YTD trends, benchmarks, risk mitigation.
2. Highlight top risks, incidents, capacity/cost callouts, and roadmap commitments.
3. Notify leadership and update scoreboard documentation.

## AI intelligence highlights
- **AI Trend Detection**: spot deviations from expectations early and surface trend explanations.
- **Risk Impact Scoring**: prioritize metric changes with business impact (e.g., uptime vs cost).
- **Narrative Assistance**: suggest phrasing about key risks/resolutions for exec readability.

## Memory agent & dispatcher integration
- Store report summaries under `shared-context://memory-store/kpi/<operationId>`.
- Emit events: `kpi-report-ready`, `kpi-metrics`, `kpi-anomaly`.
- Subscribe to dispatcher signals (`incident-ready`, `policy-risk`) to include relevant metrics or escalate urgencies.
- Tag context with `decisionId`, `reportType`, `riskScore`, `tenants`.

## Communication protocols
- Primary: Bash/python scripts hitting Prometheus/K8s/CI/CD/incident/observer APIs.
- Secondary: Event bus for `kpi-*` signals.
- Fallback: JSON exports to `artifact-store://kpi/<operationId>.json`.

## Observability & telemetry
- Metrics: report count, DORA metrics, trend direction, riskScore distribution.
- Logs: structured `log.event="kpi.report"` containing `reportType`, `period`, `distance`.
- Dashboards: integrate `/kpi-report-generator metrics --format=prometheus`.
- Alerts: repeated report generation failures, rink ratio dropout, riskScore ≥ 0.8.

## Failure handling & retries
- Retry data collection up to 3× on API/timeout errors; if still failing escalate to `incident-triage-runbook`.
- Keep raw metric snapshots/logs until dispatcher/human acknowledges.
- On repeated failures, trigger alert to platform ops for manual intervention.

## Human gates
- Required when:
 1. Reports include sensitive strategic data (M&A, cost war room).
 2. RiskScore ≥ 0.9 and change fail rate indicates major disruption.
 3. Dispatcher demands manual review after generated anomalies.
- Use standard sentence template capturing impact and reversibility.

## Testing & validation
- Dry-run: `/kpi-report-generator report --type=weekly --format=json --dry-run`.
- Unit tests: `backend/kpi/` ensures metric calculations and trend detection satisfy expectations.
- Integration: `scripts/validate-kpi-report.sh` collects data from all sources and generates report exports.
- Regression: nightly `scripts/nightly-kpi-smoke.sh` ensures report plumbing, metrics, and alerts are stable.

## References
- Script templates: `scripts/kpi/`.
- Dashboard examples: `monitoring/grafana/kpi`.
- Evidence docs: `docs/EXECUTION-CHECKLIST.md`.

## Related skills
- `/workflow-management`: orchestrates report generation pipelines.
- `/stakeholder-comms-drafter`: uses KPI output to craft narratives.
- `/ai-agent-orchestration`: coordinates multi-skill report prep + follow-ups.

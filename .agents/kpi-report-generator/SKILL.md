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

Aggregates telemetry from observability, CI/CD, incidents, governance, and cost into executive reports (weekly/monthly/quarterly) with AI insights, RAG scoring, and structured context for downstream automation.

## When to invoke
- Generate weekly ops snapshots, monthly exec reports, QBR decks, or ad-hoc KPI summaries.
- Calculate DORA metrics, reliability, adoption, security posture, and cost/OKR indicators.
- Respond to dispatcher events (`incident-ready`, `policy-risk`, `capacity-alert`) by highlighting relevant metrics.
- Feed structured reports into leadership, audit, or automation channels for evidence and follow-up.

## Capabilities
- **Cross-domain data aggregation** (Prometheus, Azure Monitor, CI/CD, incidents, compliance, billing).
- **AI RAG scoring** against historical trends and objective baselines.
- **Multi-format exports** (Markdown, HTML, PPTX) with narratives, charts, and citations.
- **Shared-context propagation** via `shared-context://memory-store/kpi/{operationId}` for reuse.
- **Human-gated distribution** for sensitive or strategic reports.

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
| `type` | Report cadence (`weekly|monthly|quarterly`). | `monthly` |
| `window` | Lookback window (days). | `30d` |
| `format` | Output format (`markdown|html|pptx`). | `pptx` |
| `include` | Metric subsets (`dora,uptime,security`). | `dora,security` |
| `period` | Time span for KPIs. | `90d` |
| `focus` | Specific area to highlight. | `incident-metrics` |

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

### Weekly ops snapshot
1. Pull DORA, reliability, incident, adoption, security, and cost metrics.
2. Compute RAG statuses vs targets, draft narrative on top trends, and include action items.
3. Export summary to Markdown/Slack/email and emit `kpi-report-ready` for follow-up.

### Monthly executive report
1. Compose slides covering exec summary, DORA, reliability, adoption, security, cost, and roadmap.
2. Embed AI insights (riskScore, anomalies, trend direction) and cite supporting dashboards.
3. Emit structured metadata for automation and store context for leadership review cycles.

### Quarterly business review (QBR)
1. Extend monthly content with OKR scoring, YTD trends, benchmarks, and risk mitigation updates.
2. Highlight top incidents, capacity/cost impacts, and roadmap commitments.
3. Notify leadership, update scoreboard docs, and link to `stakeholder-comms` templates.

## AI intelligence highlights
- **AI trend detection** surfaces deviations early and explains what changed.
- **Risk impact scoring** weighs metric shifts by business impact (e.g., uptime vs cost).
- **Narrative assistance** suggests phrasing for exec clarity, referencing key insights.

## Memory agent & dispatcher integration
- Store report summaries under `shared-context://memory-store/kpi/{operationId}`.
- Emit events: `kpi-report-ready`, `kpi-metrics`, `kpi-anomaly`, `kpi-followup`.
- React to dispatcher alerts (`incident-ready`, `policy-risk`, `cost-anomaly`) by injecting relevant sections or escalation prompts.
- Tag context with `decisionId`, `reportType`, `riskScore`, `tenants`, and `confidence`.

## Observability & telemetry
- Metrics: report throughput, DORA metrics, trend directions, riskScore distribution.
- Logs: structured `log.event="kpi.report"` capturing `reportType`, `period`, `operationId`.
- Dashboards: expose `/kpi-report-generator metrics --format=prometheus` to leadership and ops.
- Alerts: repeated report failures, riskScore ≥ 0.8 without review, or data gaps in inputs.

## Failure handling & retries
- Retry data collection up to 3× on API/timeouts before escalating to `incident-triage-runbook`.
- Keep raw metric snapshots/logs until automation or humans acknowledge consumption.
- Alert ops when repeated failures persist and escalate to manual reporting support.

## Human gates
- Required when:
  1. Reports include sensitive strategic data (M&A, cost war rooms).
  2. RiskScore ≥ 0.9 and metrics indicate major disruption.
  3. Dispatcher requests manual review after anomaly detection.
- Use the standard confirmation template capturing impact/reversibility:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/kpi-report-generator report --type=weekly --format=json --dry-run`.
- Unit tests: `backend/kpi/` ensures metric calculations and trend detection behave as expected.
- Integration: `scripts/validate-kpi-report.sh` collects data from all sources and builds exports.
- Regression: nightly `scripts/nightly-kpi-smoke.sh` validates plumbing, metrics, and alerts.

## References
- Automation scripts: `scripts/kpi/`.
- Dashboards: `monitoring/grafana/kpi`.
- Execution checklist: `docs/EXECUTION-CHECKLIST.md`.

## Related skills
- `/workflow-management`: orchestrates report generation pipelines.
- `/stakeholder-comms-drafter`: turns KPI outputs into narratives.
- `/ai-agent-orchestration`: coordinates report prep plus follow-ups across skills.

---
name: cicd-pipeline-monitor
description: >
  Monitor, diagnose, and safeguard CI/CD pipelines with AI-assisted alerts, remediation, DORA telemetry, and dispatcher-ready context.
allowed-tools:
  - Bash
  - Read
  - Write
---

# CI/CD Pipeline Monitor — World-class Delivery Gatekeeper

Provides cross-platform visibility (GitHub Actions, Azure DevOps, Jenkins, ArgoCD) plus intelligent diagnostics, safe reruns, DORA reporting, and shared-context signals for orchestrators.

## When to invoke
- Query pipeline status, logs, DORA metrics, or pipeline health.
- Diagnose flaky/infra/config failures and trigger safe reruns.
- Enforce pipeline standards, secrets scans, or compliance policies.
- Generate deployment reports for leadership, compliance, or retrospectives.
- Respond to dispatcher events (`incident-ready`, `policy-risk`, `capacity-alert`) to assess delivery impact.

## Capabilities
- **Multi-platform monitoring** across GitHub Actions, Azure DevOps, Jenkins, and ArgoCD.
- **AI risk scoring** for pipeline runs (failure type, impact, criticality, owner).
- **Intelligent remediation** that auto-retries flake/infra failures or escalates config issues.
- **DORA/leadership telemetry** around deployment frequency, MTTR, change failure rate, and lead time.
- **Shared context** outputs (`shared-context://memory-store/cicd/{operationId}`) consumed by downstream skills.

## Invocation patterns

```bash
/cicd-pipeline-monitor status --tool=github-actions --workflow=deploy-prod --format=json
/cicd-pipeline-monitor diagnose --runId=gh123456 --priority=high
/cicd-pipeline-monitor rerun --runId=gh123456 --reason=flaky-step
/cicd-pipeline-monitor orchestrate --type=security-audit --target=production --parallel=3
/cicd-pipeline-monitor report --window=30d --format=json
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `tool` | Pipeline platform. | `github-actions` |
| `workflow` | Pipeline/workflow name. | `deploy-prod` |
| `runId` | Pipeline run identifier. | `gh123456` |
| `priority` | Run priority (`normal|high|critical`). | `high` |
| `window` | Reporting window (days). | `30d` |
| `format` | Output format (`json|table`). | `json` |

## Output contract

```json
{
  "operationId": "CI-2026-0315-01",
  "tool": "github-actions",
  "workflow": "deploy-prod",
  "runId": "gh123456",
  "status": "running|completed|failed",
  "diagnosis": {
    "failureType": "flaky|infra|config",
    "step": "integration-tests",
    "summary": "Timeout waiting for database"
  },
  "actionTaken": "none|retried|escalated",
  "aiInsights": {
    "riskScore": 0.42,
    "recommendation": "retry step with same config"
  },
  "metrics": {
    "leadTimeMin": 18,
    "failRatePct": 4
  },
  "dora": {
    "deploymentFrequency": 12,
    "leadTime": 20,
    "mttr": 15,
    "changeFailRate": 0.04
  },
  "decisionContext": "redis://memory-store/cicd/CI-2026-0315-01",
  "logs": "shared-context://memory-store/cicd/CI-2026-0315-01"
}
```

## World-class workflow templates

### Monitoring & alerting
1. Collect run metadata (status, duration, logs) across platforms.
2. Compare to thresholds (consecutive failures, duration spikes, queue depth).
3. Emit `pipeline-alert` events for dispatchers to trigger incident or policy workflows.

### Diagnosis & safe remediation
1. Classify failure logs as flaky, infra, or config.
2. Auto-rerun flaky/infra failures (limited retries with exponential backoff).
3. For config/code failures, craft remediation summary, alert stakeholders, and optionally open tickets.

### Orchestration & DORA reporting
1. Coordinate multi-stage orchestrations (security audits, compliance sweeps, or multi-service releases).
2. Compute DORA metrics (deployment frequency, lead time, MTTR, change failure rate) for requested windows.
3. Emit `deployment-report` events with metric summaries for stakeholders.

## AI intelligence highlights
- **AI Risk Assessment** evaluates failure severity, impact scope, and automation readiness.
- **Intelligent Retry Decisions** differentiate flake vs config failures to decide rerun actions.
- **Predictive Load Handling** forecasts queue saturation and scales watchers accordingly.
- **Deployment Impact Forecasting** correlates pipeline failures with incidents/policy compliance.

## Memory agent & dispatcher integration
- Persist monitoring data to `shared-context://memory-store/cicd/{operationId}` tagged with `decisionId`, `tool`, `tenant`, `workflow`, `riskScore`.
- Emit events: `pipeline-started`, `pipeline-failed`, `pipeline-fixed`, `deployment-report`.
- Listen to dispatcher signals (`incident-ready`, `policy-risk`, `capacity-alert`) to pause/resume or escalate pipelines.
- Provide fallback artifacts via `artifact-store://cicd/{operationId}.json` when event bus is unavailable.

## Observability & telemetry
- Metrics: run success/failure counts, consecutive failure streaks, queue depth, DORA metrics.
- Logs: structured `log.event="pipeline.status"` with `runId`, `workflow`, `decisionId` for traceability.
- Dashboards: feed `/cicd-pipeline-monitor metrics --format=prometheus` into Grafana for SRE visibility.
- Alerts: change failure rate >10%, MTTR spikes, repeated manual restarts, or automation gating.

## Failure handling & retries
- Automatically retry runs up to 2× for flaky or infra failures with exponential backoff.
- On repeated failures or manual gates, escalate to `incident-triage-runbook` and pause the pipeline.
- Retain logs/traces until downstream acknowledgments, avoiding deletion until auditing allows.
- Notify on-call channels when remediation automation loops or human gates remain blocked.

## Human gates
- Required when:
  1. `riskScore ≥ 0.85` or a critical production pipeline is involved.
  2. Manual deploys triggered by the skill affect prod services.
  3. Dispatcher requests manual intervention after retries/failures.
- Confirmation template matches the orchestrator format:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/cicd-pipeline-monitor rerun --runId=gh-dry-run --dry-run`.
- Unit tests: `backend/cicd/` ensures classification, telemetry, and metrics calculations stay accurate.
- Integration: `scripts/validate-cicd-pipeline-monitor.sh` hits multiple pipelines, triggers alerts, and verifies remediation actions.
- Regression: nightly `scripts/nightly-cicd-smoke.sh` ensures DORA metrics and alert thresholds remain stable.

## References
- Pipeline scripts: `scripts/cicd/`.
- Monitoring dashboards: `monitoring/grafana/cicd`.
- Templates: `templates/workflow-report.md`.

## Related skills
- `/incident-triage-runbook`: remediates when pipeline errors become incidents.
- `/policy-as-code`: enforces policies before pipelines run.
- `/workflow-management`: orchestrates multi-pipeline operations.
- `/deployment-validation`: gates deployments after pipeline completion.

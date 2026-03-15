---
name: cicd-pipeline-monitor
description: >
  Monitor, diagnose, and safeguard CI/CD pipelines with AI-assisted alerts, remediation, and dispatcher telemetry.
allowed-tools:
  - Bash
  - Read
  - Write
---

# CI/CD Pipeline Monitor — World-class Delivery Gatekeeper

Provides cross-platform CI/CD visibility (GitHub Actions, Azure DevOps, Jenkins, ArgoCD) plus intelligent diagnostics, safe re-runs, DORA reporting, and shared-context signals for orchestrators. Trigger when examining failures, rerunning builds, enforcing standards, or responding to dispatcher alerts tied to deployments, incidents, or policies.

## When to invoke
- Query pipeline status, logs, DORA/KPI metrics.
- Diagnose flake/infra/config errors and trigger safe re-runs.
- Enforce pipeline standards, scans, secrets policies.
- Generate deployment reports for leadership or compliance.
- Respond to dispatcher events (`incident-ready`, `policy-risk`, `capacity-alert`) to evaluate delivery impact.

## Capabilities
- Unified CI/CD monitoring across GitHub Actions, Azure DevOps, Jenkins, ArgoCD.
- AI risk scoring for pipeline runs (failure type, impact, criticality, change owner).
- Automatic remediation for flaky/infra failures, human-gated escalation for config/code failures.
- Telemetry for DORA metrics, change failure rate, MTTR, queue depth.
- Shared context output `shared-context://memory-store/cicd/<operationId>` for downstream skills.

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
| `workflow` | Workflow/pipeline name. | `deploy-prod` |
| `runId` | Run identifier. | `gh123456` |
| `priority` | Run priority (normal/high/critical). | `high` |
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
2. Compare against thresholds (consecutive failures, duration spikes, queue depth).
3. Emit `pipeline-alert` events for dispatcher to trigger incident response or policy review.

### Diagnosis & safe remediation
1. Analyze failure logs, classify as flaky/infra/config.
2. Automatically re-run flaky/infra runs (limit retries).
3. For config/code failures, produce structured remediation summary, alert stakeholders, and optionally open ticket.

### Orchestration & DORA reporting
1. Coordinate multi-stage orchestrations (security audit, compliance check) with dependencies.
2. Calculate DORA metrics, change failure rate, MTTR, deployment frequency for specified window.
3. Emit `deployment-report` event with metric summary.

## AI intelligence highlights
- **AI Risk Assessment**: determines severity/risk of failures and whether auto-remediation is safe.
- **Intelligent Retry Decisions**: distinguishes flake vs config failures to decide re-run actions.
- **Predictive Load Handling**: forecasts queue saturation and scales watchers accordingly.
- **Deployment Impact Forecasting**: correlates pipeline failures with incident metrics (policy/compliance/ops).

## Memory agent & dispatcher integration
- Persist monitoring data to `shared-context://memory-store/cicd/<operationId>`.
- Emit events: `pipeline-started`, `pipeline-failed`, `pipeline-fixed`, `deployment-report`.
- Respond to dispatcher signals (`incident-ready`, `policy-risk`) to escalate or pause pipelines.
- Tag entries with `decisionId`, `tool`, `tenant`, `workflow`, `riskScore`.

## Communication protocols
- Primary: platform CLI/APIs (gh, az pipelines, azdo, jenkins, argocd) returning JSON.
- Secondary: Event bus for `pipeline-*` events.
- Fallback: Artifact store entries `artifact-store://cicd/<operationId>.json`.

## Observability & telemetry
- Metrics: run success/failure counts, consecutive failure alerts, queue depth, DORA metrics.
- Logs: structured `log.event="pipeline.status"` with `runId`, `workflow`, `decisionId`.
- Dashboards: integrate `/cicd-pipeline-monitor metrics --format=prometheus`.
- Alerts: change fail rate > 10%, MTTR spike, manual restart frequency > baseline.

## Failure handling & retries
- Automatically retry underlaying runs up to 2× for flaky/infra failures with exponential backoff.
- On repeated failures/human gate, escalate to `incident-triage-runbook` and pause pipeline.
- Keep logs/traces until downstream ack; do not delete critical evidence for audits.

## Human gates
- Required when:
 1. RiskScore ≥ 0.85 or critical production pipeline.
 2. Manual deploys triggered by the skill affecting prod services.
 3. Dispatcher requests manual intervention after retries/failures.
- Use standard human gate confirmation template describing impact and reversibility.

## Testing & validation
- Dry-run: `/cicd-pipeline-monitor rerun --runId=gh-dry-run --dry-run`.
- Unit tests: `backend/cicd/` ensures classification and metrics calculations align with expectations.
- Integration: `scripts/validate-cicd-pipeline-monitor.sh` hits multiple pipelines, triggers alerts, checks remediation.
- Regression: nightly `scripts/nightly-cicd-smoke.sh` ensures DORA metrics and alert levels remain stable.

## References
- Pipeline scripts: `scripts/cicd/`.
- Monitoring dashboards: `monitoring/grafana/cicd`.
- Templates: `templates/workflow-report.md`.

## Related skills
- `/incident-triage-runbook`: triggered when pipeline errors escalate to incidents.
- `/policy-as-code`: ensures pipeline configs comply with policies.
- `/workflow-management`: orchestrates multi-pipeline operations.

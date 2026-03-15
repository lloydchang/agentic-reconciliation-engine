---
name: ci-cd-integrator
description: |
  Correlate CI/CD systems, trigger pipelines, and ensure downstream deployments stay synchronized by blending pipeline telemetry, artifacts, and approvals into dispatcher workflows.
allowed-tools:
  - Bash
  - Read
  - Write
---

# CI/CD Integrator — World-class Pipeline Orchestration Playbook

Monitors, triggers, and remediates CI/CD pipelines (GitHub Actions, Azure DevOps, Jenkins, ArgoCD) from a single surface with risk-aware automation and human gates.

## When to invoke
- Pipelines fail, flake, or produce suspicious artifacts that might impact production.
- A release needs to be triggered across multiple systems with dependency attention.
- Diagnostics require correlating build logs, artifacts, and deployment status.
- Dispatcher events (`pipeline-failure`, `deploy-ready`, `artifact-signed`) demand remediation.

## Capabilities
- **Multi-pipeline orchestration**: schedule/resume/cancel pipelines across GitHub Actions, Azure DevOps, Jenkins, ArgoCD.
- **Artifact validation**: verify signatures, SBOMs, and compliance before promoting artifacts.
- **Contextual routing**: push telemetry/logs to shared context so other skills understand pipeline health.
- **Risk-aware automation**: apply human gates for high-risk stages, throttle promotions, or require approvals.
- **Response playbooks**: run rollback or artifact reprovision flows when failures appear.

## Invocation patterns
```bash
/ci-cd-integrator monitor --pipeline=deploy-platform --system=github-actions
/ci-cd-integrator trigger --pipeline=release-v3 --systems=github-actions,argo
/ci-cd-integrator diagnose --run=run-2026-041 --system=azure-devops
/ci-cd-integrator remediate --pipeline=deploy-platform --action=rerun-failed
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `pipeline` | Pipeline or workflow name. | `deploy-platform` |
| `system` | CI/CD system (`github-actions`,`azure-devops`,`jenkins`,`argocd`). | `github-actions` |
| `run` | Pipeline execution ID. | `run-2026-041` |
| `action` | Automated remediation action (`rerun`,`cancel`,`promote`). | `rerun-failed` |
| `systems` | Comma list of platforms to trigger. | `github-actions,argo` |
| `artifact` | Artifact identifier for validation. | `artifact-2026-105`

## Output contract
```json
{
  "operationId": "CI-2026-0315-01",
  "status": "running|failed|remediated",
  "pipeline": "deploy-platform",
  "system": "github-actions",
  "riskScore": 0.42,
  "remediation": "rerun failed jobs",
  "logs": "shared-context://memory-store/ci-cd-integrator/CI-2026-0315-01",
  "decisionContext": "redis://memory-store/ci-cd-integrator/CI-2026-0315-01"
}
```

## World-class workflow templates

### Pipeline monitoring & telemetry
1. Subscribe to pipeline events, gather logs, and normalize statuses across systems.
2. Emit `pipeline-status` events with riskScore and artifact metadata.
3. Command stub: `/ci-cd-integrator monitor --pipeline=deploy-platform --system=github-actions`

### Multi-system releases
1. Trigger pipelines across GitHub Actions, Azure DevOps, Jenkins, and ArgoCD with correct order.
2. Validate artifact signatures, SBOMs, and policy compliance before promotions.
3. Emit `pipeline-release` events linking downstream deployments.
4. Command stub: `/ci-cd-integrator trigger --pipeline=release-v3 --systems=github-actions,argo`

### Diagnostics & remediation
1. Fetch logs, failure traces, and artifact metadata for failing runs.
2. Match errors with remediation playbooks (rerun, cancel, revert).
3. Emit `pipeline-remediation` events and optionally run human gate.
4. Command stub: `/ci-cd-integrator diagnose --run=run-2026-041 --system=azure-devops`

### Incident-driven automation
1. On repeated failures or riskScore ≥ 0.8, trigger remediations (rerun, rollback, disable auto-promote).
2. Coordinate with `incident-triage-runbook` or `deployment-validation` as needed.
3. Command stub: `/ci-cd-integrator remediate --pipeline=deploy-platform --action=rerun-failed`

## AI intelligence highlights
- **Risk scoring** differentiates critical branches/releases from safe ones, reducing false escalations.
- **Deployment intelligence** understands artifact lineage, policy controls, and approvals to decide gating needs.
- **Anomaly detection** flags flake patterns or repeated infrastructure failures for human review.

## Memory agent & dispatcher integration
- Persist pipeline metadata under `shared-context://memory-store/ci-cd-integrator/{operationId}`.
- Emit events: `pipeline-status`, `pipeline-release`, `pipeline-remediation`, `pipeline-human-gate`.
- Subscribe to dispatcher signals (`deployment-risk`, `policy-risk`, `incident-ready`).
- Tag logs with `decisionId`, `pipeline`, `system`, `run`, `riskScore`.

## Observability & telemetry
- Metrics: success rate, remediation count, gate frequency, artifact validation rate.
- Logs: structured `log.event="pipeline.status"` with `pipeline`, `system`, `status`.
- Dashboards: integrate `/ci-cd-integrator metrics --format=prometheus` into release control panels.
- Alerts: >3 runs failing in 15m, signature mismatches, gating loops.

## Failure handling & retries
- Retry status queries/remediation API calls up to 3× with exponential backoff.
- If runs stay failed, escalate to `incident-triage-runbook` and log artifacts.
- Preserve contexts for audits until downstream ack.

## Human gates
- Required when:
  1. Automation touches production without approvals.
  2. Artifact validation fails or new security controls triggered.
  3. Dispatcher requests review after repeated automation loops.

## Testing & validation
- Dry-run: `/ci-cd-integrator trigger --pipeline=test --systems=github-actions --dry-run`
- Unit tests: `backend/ci-cd/` ensures trigger/execution logic stays stable.
- Integration: `scripts/validate-ci-cd-integrator.sh` hits actual CI/CD APIs.
- Regression: nightly `scripts/nightly-ci-cd-smoke.sh` runs monitors and remediations.

## References
- Scripts: `scripts/ci-cd-integrator/`.
- Templates: `templates/ci-cd/`.
- Monitoring: `monitoring/ci-cd/`.

## Related skills
- `/deployment-validation`: validates go/no-go steps.
- `/incident-triage-runbook`: responds to pipeline incidents.
- `/workflow-management`: orchestrates cross-pipeline automation flows.

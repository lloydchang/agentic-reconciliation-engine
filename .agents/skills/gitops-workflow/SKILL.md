---
name: gitops-workflow
description: >
  Implement, operate, and troubleshoot GitOps workflows with ArgoCD/Flux via AI-guided automation and shared context.
allowed-tools:
  - Bash
  - Read
  - Write
---

# GitOps Workflow — World-class Continuous Delivery Playbook

Automates ArgoCD/Flux GitOps pipelines, drift detection, promotions, and fleet-wide application management with AI risk scoring, telemetry, and dispatcher integration.

## When to invoke
- Bootstrap GitOps (ArgoCD/Flux) for clusters or tenants.
- Promote artifacts across environments and manage ApplicationSets/HelmReleases.
- Diagnose drift/out-of-sync applications and sync/rollback workloads.
- Validate repository structure, policies, RBAC, and compliance.
- React to dispatcher signals (`incident-ready`, `policy-risk`, `capacity-alert`) requiring GitOps adjustments.

## Capabilities
- **Manage GitOps applications** (ArgoCD App/ApplicationSet, Flux HelmRelease/Kustomization).
- **Promotion pipelines** with AI gating, approval, and policy enforcement.
- **Drift detection & remediation** with auto-sync or incident escalation.
- **Audit/ compliance evidence** capturing alignment with policies.
- **Shared-context propagation** at `shared-context://memory-store/gitops/{operationId}` for follow-on skills.

## Invocation patterns

```bash
/gitops-workflow bootstrap --cluster=aks-tenant-42-prod --source=gitops/platform
/gitops-workflow promote --app=tenant-app --to=prod --version=v2.3.1
/gitops-workflow diagnose --app=tenant-app --check=drift
/gitops-workflow sync --app=service-a --force
/gitops-workflow audit --env=prod --format=json
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `cluster` | Cluster alias. | `aks-tenant-42-prod` |
| `app` | ArgoCD/Flux application name. | `tenant-app` |
| `env` | Environment (`dev|staging|prod`). | `prod` |
| `to` | Target environment for promotion. | `prod` |
| `version` | Application version/tag. | `v2.3.1` |
| `check` | Diagnostic focus (`drift|health|policy`). | `drift` |

## Output contract

```json
{
  "operationId": "GITOPS-2026-0315-01",
  "operation": "bootstrap|promote|diagnose|sync|audit",
  "status": "success|failure",
  "appName": "tenant-app",
  "targetRevision": "v2.3.1",
  "syncStatus": "Synced|OutOfSync",
  "healthStatus": "Healthy|Degraded",
  "driftDetected": false,
  "events": [ { "name": "app-synced", "timestamp": "2026-03-15T08:12:00Z" } ],
  "aiInsights": { "riskScore": 0.48, "recommendation": "Hold until drift resolved" },
  "decisionContext": "redis://memory-store/gitops/GITOPS-2026-0315-01",
  "logs": "shared-context://memory-store/gitops/GITOPS-2026-0315-01"
}
```

## World-class workflow templates

### GitOps bootstrap
1. Install ArgoCD/Flux with production-grade settings (SSO, RBAC, sync policy).
2. Define root Application/ApplicationSet across tenants/clusters.
3. Emit `gitops-bootstrapped` event with context for downstream orchestration.

### Promotion pipeline
1. Update GitOps repo with new values or Helm release for target env.
2. Apply gating (approvals, policy checks, tests) before hitting `sync`.
3. Monitor health, re-sign artifacts if needed, and emit `image-promoted`/`gitops-promote` events.

### Drift detection & remediation
1. Monitor apps for `OutOfSync` or degraded health.
2. Run diffs (`argocd app diff` or `flux` status), assess severity, and compute AI risk.
3. Auto-sync/rollback when safe; escalate to `incident-triage-runbook` on repeated failure.

### Audit & compliance
1. Validate repo structure, policy attachments (Gatekeeper/OPA), and RBAC.
2. Build audit reports with evidence and emit `gitops-audit` for compliance teams.
3. Store results for leadership and regulatory review.

## AI intelligence highlights
- **AI drift scoring** determines severity and whether auto-heal is safe.
- **Intelligent promotion decisions** weigh dependencies, metrics, and historical changes.
- **Predictive conflict insights** forecast multi-app interactions to avoid misconfigurations.

## Memory agent & dispatcher integration
- Store metadata at `shared-context://memory-store/gitops/{operationId}` with tags (`decisionId`, `app`, `riskScore`).
- Emit events: `gitops-sync`, `gitops-promote`, `gitops-drift`, `gitops-bootstrapped`, `gitops-audit`.
- React to dispatcher signals (`incident-ready`, `policy-risk`) by pausing promotions or launching rollbacks.
- Provide fallback artifacts via `artifact-store://gitops/{operationId}.json` when necessary.

## Observability & telemetry
- Metrics: sync success rate, drift occurrences, promotion count, health status, riskScore spread.
- Logs: structured `log.event="gitops.operation"` with `operationId`, `app`, `decisionId`.
- Dashboards: integrate `/gitops-workflow metrics --format=prometheus` into SRE views.
- Alerts: multiple drift events, sync failures, unauthorized version promotions.

## Failure handling & retries
- Retry sync/promotions 2× on transient errors (repo access, API) with exponential backoff.
- On repeated failures escalate to `incident-triage-runbook` or policy teams.
- Preserve logs and shared-context until downstream acknowledges for audit purposes.

## Human gates
- Required when:
  1. Promotions impact production or >20 tenants.
  2. RiskScore ≥ 0.85 or multiple apps change simultaneously.
  3. Dispatcher requests manual approval after drift/resolution loops.
- Use standard human gate template capturing impact and reversibility.

## Testing & validation
- Dry-run: `/gitops-workflow promote --app=tenant-app --to=staging --dry-run`.
- Unit tests: `backend/gitops/` ensures dependency/resolution logic.
- Integration: `scripts/validate-gitops-workflow.sh` runs bootstrap → sync → promote flows.
- Regression: nightly `scripts/nightly-gitops-smoke.sh` ensures sync, drift detection, and alerting remain stable.

## References
- GitOps repo: `platform-gitops/`.
- Templates: `templates/gitops/`.
- Dashboards: `monitoring/grafana/gitops`.

## Related skills
- `/deployment-validation`: gates deployments after GitOps syncs.
- `/incident-triage-runbook`: responds to failing apps.
- `/ai-agent-orchestration`: integrates GitOps flows into larger orchestration processes.

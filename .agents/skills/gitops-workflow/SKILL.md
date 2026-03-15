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

Automates ArgoCD/Flux GitOps pipelines, drift detection, promotions, and fleet-wide application management with AI risk scoring, telemetry, and dispatcher integration. Trigger for new cluster apps, sync failures, ALM operations, or compliance reviews.

## When to invoke
- Bootstrap GitOps (ArgoCD/Flux) for clusters/tenants.
- Promote artifacts across environments, manage ApplicationSets.
- Diagnose drift/out-of-sync apps and re-sync or rollback.
- Validate repository structure, policies, and RBAC.
- React to dispatcher events (incident-ready, policy-risk, capacity-alert) requiring GitOps actions.

## Capabilities
- Manage ArgoCD Applications/ApplicationSets and Flux HelmReleases/Kustomizations.
- Support branch/promotion pipelines with approval gating.
- AI guardrails for drift detection, auto-heal decisions, and policy enforcement.
- Shared context `shared-context://memory-store/gitops/<operationId>`.

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
| `app` | ArgoCD/Flux application. | `tenant-app` |
| `env` | Environment (dev/staging/prod). | `prod` |
| `to` | Target env for promotion. | `prod` |
| `version` | Application version/tag. | `v2.3.1` |
| `check` | Diagnostic type (drift, health, policy). | `drift` |

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
  "events": [
    { "name": "app-synced", "timestamp": "2026-03-15T08:12:00Z" }
  ],
  "aiInsights": {
    "riskScore": 0.48,
    "recommendation": "Hold promotion until drift resolved"
  },
  "decisionContext": "redis://memory-store/gitops/GITOPS-2026-0315-01",
  "logs": "shared-context://memory-store/gitops/GITOPS-2026-0315-01"
}
```

## World-class workflow templates

### GitOps bootstrap
1. Install ArgoCD/Flux with production configs (SSO, RBAC, auto-sync).
2. Define root Application or ApplicationSet for clusters/tenants.
3. Emit `gitops-bootstrapped` event and share context for other skills.

### Promotion pipeline
1. Update GitOps repo (values/helm release) for target environment.
2. Apply branch/promotion gating (approval, tests).
3. Sync app, monitor health, emit `app-promoted`.

### Drift detection & remediation
1. List apps for status; find `OutOfSync` or health issues.
2. Run `argocd app diff` or Flux `Kustomization` status.
3. Auto-sync/rollback when safe; escalate to incident-runbook on repeated failure.

### Audit & compliance
1. Validate repo structure, policies (Gatekeeper, OPA).
2. Generate audit report (versions, compliance statuses).
3. Emit `gitops-audit` event for leadership/incident watchers.

## AI intelligence highlights
- **AI Drift Scoring**: assess severity of drift, risk for auto-heal vs manual review.
- **Intelligent Promotion Decisions**: weigh dependencies, metrics, and change history before promoting.
- **Predictive Helicopter View**: foresee multi-app dependencies and potential conflicts.

## Memory agent & dispatcher integration
- Store GitOps metadata at `shared-context://memory-store/gitops/<operationId>`.
- Emit events: `gitops-sync`, `gitops-promote`, `gitops-drift`, `gitops-bootstrapped`.
- Respond to dispatcher signals (`incident-ready`, `policy-risk`) to halt/resume promotions or trigger rollbacks.
- Tag context with `decisionId`, `app`, `riskScore`.

## Communication protocols
- Primary: ArgoCD CLI/API (`argocd app`, `argocd appset`), Flux CLI/Flux resources.
- Secondary: Event bus for `gitops-*` events.
- Fallback: JSON artifacts `artifact-store://gitops/<operationId>.json`.

## Observability & telemetry
- Metrics: sync success rate, drift frequency, promotion count, health status.
- Logs: structured `log.event="gitops.operation"` with `operationId`.
- Dashboards: integrate `/gitops-workflow metrics --format=prometheus`.
- Alerts: repeated drift > threshold, sync failures, unauthorized version promotion.

## Failure handling & retries
- Retry sync/promote commands up to 2× on transient errors (repo access, API).
- On repeated failure escalate to `incident-triage-runbook`.
- Keep logs and artifacts until downstream ack; do not delete automatically.

## Human gates
- Required when:
 1. Promotions affect production-critical apps or >20 tenants.
 2. RiskScore ≥ 0.85 or multiple apps simultaneously promoting.
 3. Dispatcher requests manual approval after repeated drift/resync loops.
- Use standard confirmation template capturing impact and reversibility.

## Testing & validation
- Dry-run: `/gitops-workflow promote --app=tenant-app --to=staging --dry-run`.
- Unit tests: `backend/gitops/` ensures dependency/resolution logic.
- Integration: `scripts/validate-gitops-workflow.sh` orchestrates bootstrap → sync → promote flows.
- Regression: nightly `scripts/nightly-gitops-smoke.sh` ensures sync, drift, and alerting remain stable.

## References
- GitOps repo: `platform-gitops/`.
- Templates: `templates/gitops/`.
- Dashboards: `monitoring/grafana/gitops`.

## Related skills
- `/deployment-validation`: ensures deployments in GitOps are healthy.
- `/incident-triage-runbook`: invoked when GitOps apps fail.
- `/ai-agent-orchestration`: orchestrates GitOps workflows within larger processes.

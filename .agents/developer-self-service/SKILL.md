---
name: developer-self-service
description: >
  Build and operate the Internal Developer Portal plus golden-path templates with AI-guided onboarding, templating, and dispatcher telemetry.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Developer Self-Service — World-class Platform Productivity Playbook

Implements and operates the Internal Developer Portal (Backstage) to deliver self-service scaffolding, catalog automation, onboarding, and documentation while streaming telemetry for orchestration.

## When to invoke
- Scaffold new services, environments, clusters, or pipelines via Backstage templates.
- Register services, teams, or resources in the catalog automatically.
- Automate developer onboarding checklists, secret requests, or infrastructure approvals.
- Respond to dispatcher events (`incident-ready`, `capacity-alert`, `policy-risk`) that need new templates or automation tuning.
- Track developer experience metrics, policy compliance, or golden-path adoption.

## Capabilities
- **Backstage & golden-path automation** that provisions repos, catalogs, pipelines, and docs from templates.
- **AI risk scoring** for generated scaffolds with policy, compliance, and cost impact signals.
- **Catalog & onboarding orchestration** that registers artifacts, automates prerequisites, and tracks delivery.
- **Shared-context propagation** at `shared-context://memory-store/developer-self-service/{operationId}` for downstream skills.
- **Human-in-the-loop gating** for production-impacting templates or onboarding steps.

## Invocation patterns

```bash
/developer-self-service scaffold --template=new-service --team=payments --environment=prod
/developer-self-service onboard --team=payments --checklist=true --notify=slack
/developer-self-service catalog --repo=tenant-app --action=register
/developer-self-service metrics --window=30d --format=json
/developer-self-service request-secret --service=payments-api --priority=high
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `template` | Scaffolder template name (`new-service`, `database`, `cluster`). | `new-service` |
| `team` | Team or owner identifier. | `payments` |
| `environment` | Target environment (dev/staging/prod). | `prod` |
| `repo` | GitHub repo for catalog registration. | `tenant-app` |
| `window` | Metrics window (days). | `30d` |
| `priority` | Request priority (`auto|manual`). | `high` |

## Output contract

```json
{
  "operationId": "DEV-2026-0315-01",
  "operation": "scaffold|onboard|catalog|request|metrics",
  "status": "success|failure|pending",
  "team": "payments",
  "template": "new-service",
  "catalogRegistered": true,
  "pipelineCreated": true,
  "checklistCompleted": true,
  "portalUrl": "https://backstage.internal/catalog/default/component/tenant-app",
  "aiInsights": {
    "riskScore": 0.42,
    "recommendation": "Enable policy-guarded kubernetes clusters"
  },
  "decisionContext": "redis://memory-store/developer-self-service/DEV-2026-0315-01",
  "logs": "shared-context://memory-store/developer-self-service/DEV-2026-0315-01"
}
```

## World-class workflow templates

### Golden-path service scaffolding
1. Invoke validated templated scaffolder (Backstage, Backstage Scaffolder CLI) with policy-approved inputs.
2. Create repo, catalog entry, namespace, CI/CD pipeline, observability links, and security controls.
3. Emit `self-service-scaffolded` event with artifacts stored in shared context and risk metadata.

### Catalog automation & registration
1. Scan repos, manifests, and `catalog-info.yaml` files and register them using Backstage Catalog APIs.
2. Validate tags, naming, policy compliance, and golden-path metadata; log failures/warnings.
3. Emit `catalog-registered` events so orchestrators can act on new components.

### Onboarding automation
1. Generate per-team onboarding checklists (GitHub groups, Slack channels, docs, secrets, network approvals).
2. Automate prerequisites (namespaces, cost centers, ARGO/CI pipeline, secrets requests).
3. Emit `team-onboarded` events with metrics (time to first deploy, ticket volume) and share context for follow-up.

### Metrics & governance
1. Track adoption (template usage, catalog coverage, checklist completion, support tickets).
2. Stream data into dashboards and compute risk signals if adoption dips.
3. Emit `self-service-metrics` events for leadership and metric-driven automations.

## AI intelligence highlights
- **AI risk scoring** evaluates output against policy/compliance/cost guardrails before scaffolding or onboarding steps complete.
- **Intelligent recommendations** suggest extra steps (cert-manager, secrets handshake) or alternative templates based on detected context.
- **Predictive adoption alerts** warn when template usage drops or support tickets spike.

## Memory agent & dispatcher integration
- Store operation metadata at `shared-context://memory-store/developer-self-service/{operationId}` with (`decisionId`, `team`, `template`, `riskScore`).
- Emit events: `scaffolded-service`, `catalog-registered`, `team-onboarded`, `template-alert`, `self-service-metrics`.
- Subscribe to dispatcher triggers (`policy-risk`, `incident-ready`, `capacity-alert`) to auto-launch templates or adjust docs.
- Provide fallback artifacts via `artifact-store://developer-self-service/{operationId}.json` when systems are offline.

## Observability & telemetry
- Metrics: template adoption rate, catalog coverage, checklist completion, support ticket volume.
- Logs: structured `log.event="self-service.operation"` with `operation`, `team`, `decisionId`.
- Dashboards: include `/developer-self-service metrics --format=prometheus` in platform monitoring.
- Alerts: template failure > threshold, adoption drop > 20%, secret/onboarding errors > baseline.

## Failure handling & retries
- Retry scaffold/catalog steps up to 2× on transient errors (GitHub API, Backstage) before human review.
- On repeat failures escalate to `incident-triage-runbook` and open support tickets.
- Preserve artifacts/inventory until downstream acknowledgments confirm closure.

## Human gates
- Required when:
  1. Templates modify production resources or create new clusters.
  2. Onboarding adds platform-level access, RBAC changes, or new secrets.
  3. Dispatcher indicates manual review after repeated automation failures.
- Confirmation template aligns with orchestrator format:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/developer-self-service scaffold --template=new-service --dry-run`.
- Unit tests: `backend/self-service/` ensures template validation, AI scoring, and metadata processing work.
- Integration: `scripts/validate-developer-self-service.sh` runs scaffold/onboard flows via emulator, verifying telemetry.
- Regression: nightly `scripts/nightly-self-service-smoke.sh` ensures adoption metrics and alerts remain stable.

## References
- Templates: `templates/new-service/template.yaml`.
- Scripts: `scripts/self-service/`.
- Onboarding docs: `docs/platform-onboarding.md`.

## Related skills
- `/workflow-management`: orchestrates multi-step self-service flows.
- `/policy-as-code`: validates templates against governance guardrails.
- `/ai-agent-orchestration`: coordinates follow-on actions when golden-paths finish.

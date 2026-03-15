---
name: developer-self-service
description: >
  Build and operate the Internal Developer Portal and golden-path templates with AI-guided onboarding, templating, and dispatcher telemetry.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Developer Self-Service — World-class Platform Productivity Playbook

Implements and operates the Internal Developer Portal (Backstage) to provide templates, catalog automation, policy enforcement, and onboarding automation. Use whenever teams need self-service scaffolding, catalog registration, onboarding, or platform documentation.

## When to invoke
- Scaffold new services, environments, or pipelines via Backstage templates.
- Register services, teams, or resources in the catalog automatically.
- Automate onboarding checklists, secret requests, or infrastructure provisioning approvals.
- Track developer experience metrics, policy compliance, or golden-path adoption.
- Respond to dispatcher alerts (`incident-ready`, `capacity-alert`, `policy-risk`) requiring new templates or failed automations.

## Capabilities
- Backstage portal setup + plugin configuration (Kubernetes, TechDocs, ArgoCD, Cost Insights).
- Golden-path scaffolder templates for services, pipelines, clusters, and secrets.
- Automated catalog registration, onboarding checklists, and secret/cluster requests.
- AI-driven risk scoring for template outputs (policy compliance, security, cost impact).
- Shared context storage `shared-context://memory-store/developer-self-service/<operationId>` for orchestrators.

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
| `repo` | GitHub repo for registration. | `tenant-app` |
| `window` | Metrics window (days). | `30d` |
| `priority` | Request priority (auto/manual). | `high` |

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
    "recommendation": "Ensure IAM policy dev self-service is enabled"
  },
  "decisionContext": "redis://memory-store/developer-self-service/DEV-2026-0315-01",
  "logs": "shared-context://memory-store/developer-self-service/DEV-2026-0315-01"
}
```

## World-class workflow templates

### Golden-path service scaffolding
1. Invoke templated scaffolder (Backstage template) with validated inputs.
2. Create repo, catalog entry, CI/CD pipeline, namespace, and observability links.
3. Emit `self-service-scaffolded` event with artifacts and shared context.

### Catalog automation & registration
1. Scan repos for `catalog-info.yaml`, register them via Backstage API.
2. Validate naming/tags/policies; log failures/warnings.
3. Emit `catalog-registered` events for dispatcher discovery.

### Onboarding automation
1. Generate onboarding checklists per team (GitHub groups, Slack channels, docs).
2. Automate prerequisites (namespace, Backstage entry, cost center, docs).
3. Emit `team-onboarded` event with metrics (time to first deploy, support tickets).

### Metrics & governance
1. Track adoption metrics (templates usage, catalog coverage, self-service ratio).
2. Feed data to dashboards and risk scoring (lack of templates triggers manual intervention).
3. Emit `self-service-metrics` events for leadership reporting.

## AI intelligence highlights
- **AI Risk Score**: evaluates template outputs against policy and compliance guardrails.
- **Intelligent Recommendations**: suggests additional scaffolder steps (cert-manager, secrets) based on context.
- **Predictive Adoption Alerts**: flags declining template usage or rising support tickets for acceleration.

## Memory agent & dispatcher integration
- Store template/metrics context at `shared-context://memory-store/developer-self-service/<operationId>`.
- Emit events: `scaffolded-service`, `catalog-registered`, `team-onboarded`, `template-alert`.
- Subscribe to dispatchers (`policy-risk`, `incident-ready`) to auto-trigger templates or documentation refresh.
- Tag entries with `decisionId`, `team`, `template`, `riskScore`.

## Communication protocols
- Primary: Backstage CLI/API calls, GitHub, HTTP hooks, and shell scripts.
- Secondary: Event bus for `self-service-*` events.
- Fallback: JSON artifacts stored at `artifact-store://developer-self-service/<operationId>.json`.

## Observability & telemetry
- Metrics: template adoption, catalog coverage, checklist completion, support ticket rate.
- Logs: structured `log.event="self-service.operation"` with `operation`, `team`, `decisionId`.
- Dashboards: include `/developer-self-service metrics --format=prometheus`.
- Alerts: template failure > threshold, adoption drops > 20%, support tickets > baseline.

## Failure handling & retries
- Retry scaffold/catalog steps up to 2× on transient errors (GitHub API, Backstage).
- On repeated failures, escalate to `incident-triage-runbook` and open support ticket.
- Retain artifacts/inventory until downstream human gates confirm resolution.

## Human gates
- Required when:
 1. Templates modify prod resources or create new clusters.
 2. Onboarding adds platform-level access or secrets.
 3. Dispatcher demands manual review after repeated automation failures.
- Use standard confirmation template capturing impact and reversibility.

## Testing & validation
- Dry-run: `/developer-self-service scaffold --template=new-service --dry-run`.
- Unit tests: `backend/self-service/` ensures template validation and AI scoring.
- Integration: `scripts/validate-developer-self-service.sh` runs scaffold/onboard flows via emulator.
- Regression: nightly `scripts/nightly-self-service-smoke.sh` ensures adoption metrics and alerts remain stable.

## References
- Templates: `templates/new-service/template.yaml`.
- Scripts: `scripts/self-service/`.
- Onboarding docs: `docs/platform-onboarding.md`.

## Related skills
- `/workflow-management`: orchestrates self-service workflows.
- `/policy-as-code`: validates templates against governance.
- `/ai-agent-orchestration`: coordinates follow-up actions when templated outcomes trigger incidents.

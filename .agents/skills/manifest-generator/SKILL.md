---
name: manifest-generator
description: >
  Convert natural language Kubernetes requirements into validated manifests with AI checks and shared context.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Manifest Generator — World-class YAML Playbook

Produces Kubernetes Deployments, Services, ConfigMaps, and other manifests from natural language while enforcing best practices and providing structured outputs for automation.

## When to invoke
- Translate natural requirements into manifests for Deployments, Services, ConfigMaps, Ingresses, etc.
- Build multi-resource bundles for new services or updates.
- Validate YAML against policies and explain resource semantics.
- Supply manifest artifacts to orchestrations (tenant onboarding, deployments, GitOps).

## Capabilities
- **Natural language parsing** into structured manifest requirements.
- **Policy enforcement** (labels, resource specifications, probes, security).
- **AI risk scoring** for privileged configurations or missing controls.
- **Bundle generation** creating zipped multi-resource packages.
- **Shared-context propagation** via `shared-context://memory-store/manifest/{operationId}`.

## Invocation patterns

```bash
/manifest-generator create --description="Deploy nginx with 3 replicas, 512Mi memory limit, LoadBalancer"
/manifest-generator validate --manifest=deployment.yaml --policy=security
/manifest-generator bundle --components=deployment,service --namespace=tenant-42
/manifest-generator explain --manifest=deployment.yaml --audience=engineering
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `description` | Natural language manifest request. | `3 replicas nginx` |
| `manifest` | Path to existing YAML. | `deployment.yaml` |
| `policy` | Validation policy (`security`, `best-practices`). | `security` |
| `components` | Resource types to include. | `deployment,service` |
| `namespace` | Target namespace. | `tenant-42` |
| `format` | Output format (`yaml|json|bundle`). | `yaml` |

## Output contract

```json
{
  "operationId": "MANIFEST-2026-0315-01",
  "status": "success|failure",
  "resources": [
    { "kind": "Deployment", "name": "nginx-deployment" },
    { "kind": "Service", "name": "nginx-service" }
  ],
  "aiInsights": {
    "riskScore": 0.25,
    "notes": ["Added readiness probe", "Set CPU limits"]
  },
  "manifests": { "deployment": "apiVersion: apps/v1..." },
  "decisionContext": "redis://memory-store/manifest/MANIFEST-2026-0315-01",
  "logs": "shared-context://memory-store/manifest/MANIFEST-2026-0315-01"
}
```

## World-class workflow templates

### Manifest creation
1. Parse description into workloads, services, config maps, and metadata.
2. Generate YAML with labels, selectors, probes, and resource limits.
3. Validate YAML, emit `manifest-created`, store context, and share with orchestrations.

### Bundle generation
1. Assemble multi-resource packages (Deployment + Service + ConfigMap + HPA).
2. Package artifacts, deliver zipped payload, and emit `manifest-bundle-ready`.

### Validation & explanation
1. Validate existing manifests against policies and best practices.
2. Generate human-friendly explanations per resource for engineering or compliance.
3. Emit `manifest-validated` with verdict and suggestion list.

## AI intelligence highlights
- **AI risk scoring** flags risky configurations (privileged containers, hostPath, missing probes).
- **Intelligent best practices** recommend resource limits, annotations, or security settings.
- **Explainable YAML** provides natural-language descriptions for each field/resource.

## Memory agent & dispatcher integration
- Persist manifests and metadata under `shared-context://memory-store/manifest/{operationId}`.
- Emit events: `manifest-created`, `manifest-validated`, `manifest-bundle`, `manifest-explained`.
- Dispatcher flows can trigger manifest generation as part of larger workflows.
- Tag context with `decisionId`, `resources`, `riskScore`, `templates`.

## Observability & telemetry
- Metrics: manifests generated, validations run, riskScore distribution.
- Logs: structured `log.event="manifest.operation"` with `operationId`, `resources`.
- Dashboards: integrate `/manifest-generator metrics --format=prometheus` for platform teams.
- Alerts: policy violations, high riskScore frequency, validation failures.

## Failure handling & retries
- Retry generation/validation up to 2× on transient errors.
- On repeated failure escalate to `incident-triage-runbook` and keep artifact logs.
- Preserve YAML and logs until downstream acknowledges completion.

## Human gates
- Required when:
  1. Manifest adds privileged operations, cluster-wide changes, or dataloss risks.
  2. Dispatcher requests manual review after repeated automation failures.
  3. RiskScore ≥ 0.7.
- Use the orchestrator-standard confirmation template capturing impact and reversibility.

## Testing & validation
- Dry-run: `/manifest-generator create --description="deploy nginx" --dry-run`.
- Unit tests: `backend/manifest/` ensures parser/renderer accuracy.
- Integration: `scripts/validate-manifest-generator.sh` converts requests to YAML and validates via `kubectl`.
- Regression: nightly `scripts/nightly-manifest-smoke.sh` ensures policy compliance and explainability.

## References
- Templates: `templates/manifests/`.
- Scripts: `scripts/manifest/`.
- Docs: `docs/MANIFEST_GENERATION.md`.

## Related skills
- `/deployment-validation`: validates generated manifests.
- `/kubectl-assistant`: applies manifests interactively.
- `/workflow-management`: includes manifest creation in workflows.

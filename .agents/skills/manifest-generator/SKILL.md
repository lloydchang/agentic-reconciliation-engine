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

Produces Kubernetes Deployments, Services, ConfigMaps, and other manifests from natural language, enforces best practices (labels, resource limits, probes), and provides structured outputs for automation/orchestrator ingestion.

## When to invoke
- User needs a manifest for deployments/services/configmaps/ingresses/etc.
- Build multi-resource bundles for new services or updates.
- Validate generated YAML for syntax, policies, and security.
- Feed orchestrations requiring manifest creation (tenant onboarding, deployments).

## Capabilities
- Parse natural descriptions into manifest specs.
- Enforce best practices (labels, resource requests, probes).
- AI scoring for manifest risk (privileged containers, hostPath, missing probes).
- Shared context `shared-context://memory-store/manifest/<operationId>`.

## Invocation patterns

```bash
/manifest-generator create --description="Deploy nginx with 3 replicas, limit memory to 512Mi, expose via LoadBalancer"
/manifest-generator validate --manifest=deployment.yaml --policy=security
/manifest-generator bundle --components=deployment,service --namespace=tenant-42
/manifest-generator explain --manifest=deployment.yaml --audience=engineering
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `description` | Natural language manifest request. | `3 replicas nginx` |
| `manifest` | Path to existing manifest. | `deployment.yaml` |
| `policy` | Validation policy (security, best-practices). | `security` |
| `components` | Resource types building block. | `deployment,service` |
| `namespace` | Target namespace. | `tenant-42` |

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
  "manifests": {
    "deployment": "apiVersion: apps/v1..."
  },
  "decisionContext": "redis://memory-store/manifest/MANIFEST-2026-0315-01",
  "logs": "shared-context://memory-store/manifest/MANIFEST-2026-0315-01"
}
```

## World-class workflow templates

### Manifest creation
1. Parse natural request into structured requirements.
2. Compose manifest with required fields (labels, selectors, resource limits, probes).
3. Validate syntax and policies.
4. Emit `manifest-created` event with YAML and metadata.

### Bundle generation
1. Create multi-resource bundles (Deployment + Service + ConfigMap + HPA).
2. Export zipped YAML package for CLI/app consumption.
3. Emit `manifest-bundle-ready`.

### Validation & explanation
1. Validate existing manifest vs policies (security, best practices).
2. Provide human-friendly explanation of each resource/component.
3. Emit `manifest-validated`.

## AI intelligence highlights
- **AI Risk Scoring**: flags risky configurations (privileged container, hostPath, missing probes).
- **Intelligent Best Practices**: suggests probes, resource limits, annotations.
- **Explainable YAML**: generates natural-language explanation for each field.

## Memory agent & dispatcher integration
- Store YAML & metadata at `shared-context://memory-store/manifest/<operationId>`.
- Emit events: `manifest-created`, `manifest-validated`, `manifest-bundle`.
- Dispatcher can trigger manifest generation as part of workflows.
- Tag context with `decisionId`, `resources`, `riskScore`.

## Communication protocols
- Primary: CLI (kubectl) friendly YAML output.
- Secondary: Event bus for `manifest-*` events.
- Fallback: JSON artifacts `artifact-store://manifest/<operationId>.json`.

## Observability & telemetry
- Metrics: manifests generated, validations performed, riskScore distribution.
- Logs: structured `log.event="manifest.operation"` with `operationId`.
- Dashboards: integrate `/manifest-generator metrics --format=prometheus`.
- Alerts: policy violations, high riskScore generation frequency, validation failures.

## Failure handling & retries
- Retry generation/validation up to 2× on errors.
- On repeated failure escalate to `incident-triage-runbook`.
- Keep YAML and logs until referenced by downstream skills.

## Human gates
- Required when:
 1. Manifest adds privileged operations, cluster-wide changes, or dataloss risk.
 2. Dispatcher demands manual review after repeated automation failures.
 3. RiskScore ≥ 0.7.
- Use standard human gate template capturing impact/reversibility.

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
- `/deployment-validation`: uses generated manifests for validation.
- `/kubectl-assistant`: executes commands to apply generated YAML.
- `/workflow-management`: includes manifest creation in workflows.

---
name: config-validator
description: |
  Check configuration drift, policy compliance, and lint standards for YAML/JSON manifests across the fleet so KB/manifest changes are safe and auditable.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Config Validator — World-class Conformance Playbook

Ensures Kubernetes manifests, policies, and configuration templates comply with company guardrails before they touch clusters or Git.

## When to invoke
- Before applying YAML/JSON manifests (Kubernetes, Flux, Crossplane) or policies to ensure formatting, schema, and policy checks pass.
- During PR validation to enforce gitops conventions, naming, and security standards.
- When automation or tooling (Flux, Crossplane) reports configuration drift.
- Dispatcher/memory agents flag `policy-risk`, `configuration-drift`, or `compliance-gap`.

## Capabilities
- **Schema & lint validation** (kubeval, yamllint, jsonnet fmt) with custom rules.
- **Policy checks** (OPA/Gatekeeper, Azure Policy, AWS Config) embedded in validation.
- **Drift detection** by comparing cluster state vs repos and revalidating manifests.
- **Shared context** under `shared-context://memory-store/config-validator/{operationId}` for downstream automation.
- **Automated gating** integrates human review when checks fail with high risk.

## Invocation patterns
```bash
/config-validator lint --path=deployments/payments.yaml
/config-validator policy --path=manifests/namespaces.yaml --framework=opa
/config-validator drift --cluster=aks-hub --namespace=platform
/config-validator explain --template=gatekeeper.yaml
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `path` | Manifest or template path. | `deployments/payments.yaml` |
| `framework` | Policy framework (OPA, Gatekeeper, Azure Policy). | `opa` |
| `cluster` | Cluster/context for drift detection. | `aks-hub` |
| `namespace` | Namespace scope. | `platform` |
| `template` | Template name for explanation. | `gatekeeper.yaml` |

## Output contract
```json
{
  "operationId": "CV-2026-0315-01",
  "status": "pass|fail",
  "issues": [
    { "name": "missing-name", "severity": "warning", "message": "Deployment missing metadata.name" }
  ],
  "riskScore": 0.13,
  "logs": "shared-context://memory-store/config-validator/CV-2026-0315-01",
  "decisionContext": "redis://memory-store/config-validator/CV-2026-0315-01"
}
```

## World-class workflow templates

### Lint & schema validation
1. Run `yamllint`, `kubeval`, and schema checks.
2. Normalize results, categorize errors by severity, and emit `config-lint` events.
3. Command stub: `/config-validator lint --path=deployments/payments.yaml`

### Policy enforcement
1. Run Gatekeeper/OPA or Azure Policy checks against manifests/previews.
2. Emit `config-policy` events when violations occur, include remediation guidance.
3. Command stub: `/config-validator policy --path=manifests/namespaces.yaml --framework=opa`

### Drift detection
1. Compare repo manifests with cluster state (kubectl diff, flux diff, crossplane claims).
2. Emit `config-drift` events with changed lines and suggest reapplies or rollbacks.
3. Command stub: `/config-validator drift --cluster=aks-hub --namespace=platform`

### Explanation & documentation
1. Generate human-readable explanations for Gatekeeper/OPA policies and templates.
2. Emit `config-explain` events for docs or reviews.
3. Command stub: `/config-validator explain --template=gatekeeper.yaml`

## AI intelligence highlights
- **AI risk scoring** weights severity, deployment impact, and policy exposure.
- **Intelligent hints** provide code fixes and remediation steps for failing checks.
- **Drift insight** tags the responsible repo/commit when config drift surfaces.

## Memory agent & dispatcher integration
- Store validation results at `shared-context://memory-store/config-validator/{operationId}`.
- Emit events: `config-lint`, `config-policy`, `config-drift`, `config-explain`, `config-human-gate`.
- Subscribe to dispatchers (`policy-risk`, `incident-ready`, `cost-anomaly`) to correlate changes with risks.
- Tag logs with `decisionId`, `resource`, `namespace`, `riskScore`, and `framework`.

## Observability & telemetry
- Metrics: lint pass rate, policy violation count, drift incidents, gate hits.
- Logs: structured `log.event="config.validation"` with `issue`, `severity`, `path`.
- Dashboards: integrate `/config-validator metrics --format=prometheus` for platform teams.
- Alerts: new policy violations, drift spikes, repeated human gates.

## Failure handling & retries
- Retry API calls for policy checks or diffs up to 3× with exponential backoff.
- When validations fail due to downstream services (OPA/Azure Policy), log errors and rerun when the service is healthy.
- Preserve shared context for audits; never drop entries until downstream acknowledges.

## Human gates
- Required when:
  1. Violations affect production security controls or compliance.
  2. Drift touches >2 clusters or critical namespaces.
  3. Dispatcher requests manual review after repeated validation failures.

## Testing & validation
- Dry-run: `/config-validator lint --path=deployments/test.yaml --dry-run`
- Unit tests: `backend/config-validator/` ensures policy adapters behave consistently.
- Integration: `scripts/validate-config-validator.sh` runs lint/policy/drift suites.
- Regression: nightly `scripts/nightly-config-validator-smoke.sh` ensures coverage and gating.

## References
- Scripts: `scripts/config-validator/`.
- Templates: `templates/config/`.
- Monitoring: `monitoring/config-validator/`.

## Related skills
- `/policy-as-code`: correlates policy violations with governance.
- `/compliance-security-scanner`: uses findings for compliance evidence.
- `/workflow-management`: schedules validation loops or remediation workflows.

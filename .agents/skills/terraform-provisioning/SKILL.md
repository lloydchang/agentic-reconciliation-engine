---
name: terraform-provisioning
description: >
  Automate multi-cloud provisioning, validation, drift detection, and destruction with AI-assisted Terraform/CDK/ARM/CloudFormation workflows and policy guardrails.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Terraform Provisioning — World-class Safe Provisioning Playbook

Manages Terraform/ARM/Bicep/CloudFormation/CDK lifecycles with AI risk scoring, structured outputs, and dispatcher integrations so every infrastructure change is auditable and automatable.

## When to invoke
- Provision, modify, or tear down cloud infrastructure across AWS, Azure, GCP, Terraform Cloud, or CDK.
- Validate IaC pre-plan/PR changes and enforce tagging, naming, and security policy compliance.
- Run drift detection or cleanup stale resources.
- Respond to dispatcher events such as `capacity-demand`, `policy-risk`, `incident-ready` before touching production infrastructure.

## Capabilities
- Multi-cloud plan→apply→validate→destroy workflows with drift detection and state handling.
- **AI Risk Assessment** for destructive/production operations (riskScore combines change size, change window, tenancy impact).
- Intelligent human gate guidance for destructive changes.
- Policy validation hooks (auto-run `tfsec`, `checkov`, naming/tagging checks).
- Shared context storage at `shared-context://memory-store/infra/<operationId>` for downstream skills.

## Invocation patterns

```bash
/terraform-provisioning plan --environment=prod --workspace=tenant-42 --dry-run
/terraform-provisioning apply --plan=tfplan --environment=prod --riskScore=0.18
/terraform-provisioning destroy --workspace=staging --confirm=true
/terraform-provisioning drift --workspace=prod --threshold=1 --notify=incident-triage
/terraform-provisioning audit --scanId=POLICY-2026-04 --policy=tagging
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `workspace` | Terraform workspace or environment. | `prod` |
| `environment` | Environment tag for risk/human gating. | `prod`, `staging` |
| `plan` | Path to saved plan file. | `tfplan` |
| `destroy` | Indicates destroy operation. | `true` |
| `riskScore` | AI risk input [0–1] from dispatcher. | `0.92` |
| `threshold` | Drift threshold (resource count). | `1` |

## Output contract

```json
{
  "operationId": "TF-2026-04-01",
  "status": "planned|applied|destroyed|failed",
  "workflow": "plan|apply|destroy|drift",
  "environment": "prod",
  "workspace": "tenant-42",
  "riskScore": 0.24,
  "planSummary": {
    "add": 3,
    "change": 2,
    "destroy": 0
  },
  "actions": [
    {
      "resource": "azurerm_kubernetes_cluster.payments",
      "change": "create"
    }
  ],
  "policyChecks": [
    { "name": "tagging", "status": "pass" },
    { "name": "approved-skus", "status": "pass" }
  ],
  "humanGate": {
    "required": true,
    "impact": "Production infrastructure changes",
    "reversible": "No"
  },
  "logs": "shared-context://memory-store/infra/TF-2026-04-01",
  "decisionContext": "redis://memory-store/infra/TF-2026-04-01"
}
```

## World-class workflow templates

### Plan review & gate
1. Run `terraform init`, `validate`, `fmt`, `plan -out`.
2. Parse plan to quantify adds/changes/destroys and cost delta (via `infracost` when available).
3. Score risk (resource change count, destructive operations, environment, change owner) and emit `riskScore`.
4. Require human gate when destroying production resources or riskScore ≥ 0.7; otherwise continue.

### Apply with policy & smoke verification
1. Ensure plan approved and stored; run `terraform apply tfplan`.
2. Execute policy checks (`tfsec`, `checkov`, naming/tagging) and fail fast on violations.
3. Run smoke tests from `tests/` (e.g., endpoint curl, health check).
4. Emit `infra-applied` event with plan summary, scope, and `shared-context` links for dispatcher use.

### Drift detection & cleanup
1. Schedule `terraform plan -refresh`, optionally `destroy` when actual drift > threshold.
2. Report drift as structured diff (added/changed/destroyed) and link to PR for remediation.
3. Emit `drift-detected` event; optionally open incident for unapproved drifts.

### Safe destroy & teardown
1. Confirm `CONFIRM=true` env var and human gate when destroying >N resources or production.
2. Run `terraform destroy` with targeted resource filtering.
3. Capture outputs, remove state references, and emit `destroy-completed`.

## AI intelligence highlights
- **AI Risk Assessment**: models evaluate change magnitude, environment, and policies to assign `riskScore` and recommend human gates.
- **Intelligent Change Prioritization**: sorts safeguarding actions (policy fixes, manual approvals) by impact and cost.
- **Violation Analysis**: explains why policy checks flagged resources (missing tags, disallowed SKUs) for quick remediation.
- **Predictive Drift Alerts**: forecasts drift by comparing usage telemetry vs. IaC model.

## Memory agent & dispatcher integration
- Store plan/operation outputs in `shared-context://memory-store/infra/<operationId>` for other skills (incident, policy, capacity).
- Emit events: `infra-planned`, `infra-applied`, `infra-drift`, `infra-destroyed`, `policy-violated`.
- Subscribe to `agent-completed`, `policy-risk`, `capacity-alert` to modulate gating/thresholds.
- Tag events with `decisionId`, `tenant`, `riskScore`, `operationId`.

## Communication protocols
- Primary: Terraform/Terrascan output (JSON, plan summary) piped via CLI.
- Secondary: Event bus (Kafka/NATS) carrying `infra-*` events consumed by dispatchers/skills.
- Fallback: Persist JSON artifacts to `artifact-store://infra/<operationId>.json`.

## Observability & telemetry
- Metrics: plan frequency, apply success rate, time-to-apply, policy violation rate, human gate frequency.
- Logs: structured `log.event="infra.apply"` containing `workflow`, `decisionId`, `riskScore`.
- Dashboards: hook `/terraform-provisioning metrics --format=prometheus` into GitOps/Fleet dashboards.
- Alerts: riskScore > 0.85, >3 failed applies per day, drift detection spike > threshold.

## Failure handling & retries
- Retry transient CLI failures (init/plan/apply) up to 3× with exponential backoff (30s → 120s) before escalation.
- On policy violation, capture diff, emit `policy-violation`, block apply, and notify stakeholders.
- Keep plan/DR artifacts (`reports/infra/<operationId>`) until downstream acknowledgements; never delete for audits.

## Human gates
- Required when:
 1. RiskScore ≥ 0.7.
 2. Destructive operations affect production or >20 resources.
 3. Policy violations remain unresolved after auto-remediation.
- Use standard confirmation template capturing impact and reversibility.

## Testing & validation
- Dry-run: `/terraform-provisioning plan --environment=test --dry-run`.
- Unit tests: `backend/infra/plan` validates parser and cost estimation logic.
- Integration: `scripts/validate-infra-lifecycle.sh` executes plan → apply → smoke → destroy in emulator.
- Regression: nightly `scripts/nightly-infra-smoke.sh` runs drift detection and telemetry to ensure gating logic.

## References
- Naming/tagging standards: `references/iac-naming-conventions.md`, `references/security-best-practices.md`.
- Automation scripts: `scripts/infra/`.
- Policy libraries: `infrastructure/policy/`.

## Related skills
- `/ai-agent-orchestration`: orchestrates infrastructure changes with other skills.
- `/policy-as-code`: validates governance before apply.
- `/compliance-security-scanner`: correlates security findings with provisioning changes.
- `/capacity-planning`: aligns infra changes with projected demand.

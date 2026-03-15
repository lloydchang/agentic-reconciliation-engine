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

Manages Terraform/ARM/Bicep/CloudFormation/CDK lifecycles with AI risk scoring, structured outputs, and dispatcher integrations for auditable infrastructure changes.

## When to invoke
- Provision, modify, or tear down cloud infrastructure across AWS, Azure, GCP, Terraform Cloud, or CDK.
- Validate IaC pre-plan/PR changes and enforce tagging, naming, and security policies.
- Run drift detection or clean up stale resources.
- Respond to dispatcher events (`capacity-demand`, `policy-risk`, `incident-ready`) before touching production.

## Capabilities
- **Plan→apply→validate→destroy workflows** with drift detection and state handling.
- **AI risk assessment** for production or destructive operations.
- **Policy validation hooks** (`tfsec`, `checkov`, naming/tagging checks).
- **Human gate orchestration** for high-risk environments.
- **Shared context propagation** via `shared-context://memory-store/infra/{operationId}`.

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
| `workspace` | Terraform workspace/environment. | `prod` |
| `environment` | Environment for risk/human gating. | `prod` |
| `plan` | Path to saved plan. | `tfplan` |
| `destroy` | Destroy flag for tear down. | `true` |
| `riskScore` | AI risk input (0–1). | `0.92` |
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
  "planSummary": { "add": 3, "change": 2, "destroy": 0 },
  "actions": [ { "resource": "azurerm_kubernetes_cluster.payments", "change": "create" } ],
  "policyChecks": [ { "name": "tagging", "status": "pass" } ],
  "humanGate": { "required": true, "impact": "Production infrastructure", "reversible": "No" },
  "logs": "shared-context://memory-store/infra/TF-2026-04-01",
  "decisionContext": "redis://memory-store/infra/TF-2026-04-01"
}
```

## World-class workflow templates

### Plan review & gating
1. Run `terraform init`, `validate`, `fmt`, `plan -out`.
2. Summarize adds/changes/destroys and cost delta (with `infracost`).
3. Score risk and emit `riskScore`; require human gate when destroying prod or riskScore ≥ 0.7.

### Apply with policy & smoke verification
1. Execute `terraform apply tfplan` after approval.
2. Run policy checks (`tfsec`, `checkov`) and fail fast on violations.
3. Perform smoke tests, emit `infra-applied`, and store context for dispatchers.

### Drift detection & cleanup
1. Schedule `terraform plan -refresh`; detect drift beyond threshold.
2. Report diff, emit `drift-detected`, and notify responsible teams.
3. Optionally plan targeted destroy/apply to reconcile drift.

### Safe destroy & teardown
1. Confirm destroy confirmations and human gates for >N prod resources.
2. Run `terraform destroy` with filters, capture outputs.
3. Emit `destroy-completed`, purge state references, and log for audits.

## AI intelligence highlights
- **AI risk assessment** gauges change magnitude, policies, and environment to assign `riskScore`.
- **Intelligent change prioritization** sequences policy fixes or approval steps by impact.
- **Violation analysis** explains why policies failed (missing tags, disallowed SKUs).
- **Predictive drift alerts** forecast divergences between IaC and running state.

## Memory agent & dispatcher integration
- Store outputs/context at `shared-context://memory-store/infra/{operationId}`.
- Emit events: `infra-planned`, `infra-applied`, `infra-drift`, `infra-destroyed`, `policy-violated`.
- React to `agent-completed`, `policy-risk`, `capacity-alert` to adjust gating.
- Tag events with `decisionId`, `tenant`, `riskScore`, `operationId`.

## Observability & telemetry
- Metrics: plan frequency, apply success rate, drift detection rates, human gate hits.
- Logs: structured `log.event="infra.apply"` with `workflow`, `decisionId`, `riskScore`.
- Dashboards: integrate `/terraform-provisioning metrics --format=prometheus`.
- Alerts: riskScore > 0.85, repeated failures, drift spikes.

## Failure handling & retries
- Retry transient CLI failures (init/plan/apply) up to 3× with exponential backoff.
- On policy violation capture diff, emit `policy-violation`, and block apply.
- Retain plan/artifacts until downstream acknowledgment; never delete for audits.

## Human gates
- Required when:
  1. RiskScore ≥ 0.7.
  2. Destructive operations impact production or >20 resources.
  3. Policy violations persist after auto-remediation.
- Use standard confirmation template capturing impact/reversibility.

## Testing & validation
- Dry-run: `/terraform-provisioning plan --environment=test --dry-run`.
- Unit tests: `backend/infra/plan` validates parser and cost logic.
- Integration: `scripts/validate-infra-lifecycle.sh` exercises plan → apply → smoke → destroy.
- Regression: nightly `scripts/nightly-infra-smoke.sh` runs drift detection and telemetry checks.

## References
- Standards: `references/iac-naming-conventions.md`, `references/security-best-practices.md`.
- Scripts: `scripts/infra/`.
- Policies: `infrastructure/policy/`.

## Related skills
- `/ai-agent-orchestration`: orchestrates infrastructure changes with other skills.
- `/policy-as-code`: validates governance before apply.
- `/compliance-security-scanner`: correlates security findings with provisioning changes.
- `/capacity-planning`: aligns infrastructure changes with projected demand.

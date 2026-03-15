---
name: tenant-lifecycle-manager
description: >
  Automate onboarding, scaling, suspension, and deprovisioning of tenants with AI-informed decisioning and shared-context signals.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Tenant Lifecycle Manager — World-class Tenant Operations Playbook

Manages the entire SaaS tenant lifecycle across clouds: provisioning, configuration, scaling, suspension, and clean decommissioning. Use it when operating tenant tiers, responding to capacity/policy incidents, or generating billing/compliance events.

## When to invoke
- Provision new tenants or clone environments.
- Scale tenant resources (compute, storage, database).
- Suspend or resume tenants (payment issues, security events).
- Deprovision tenants with irreversible cleanup.
- Respond to dispatcher flags (`policy-risk`, `capacity-alert`, `incident-ready`) requiring tenant actions.

## Capabilities
- Multi-cloud provisioning templates per tier (starter/business/enterprise/critical).
- Scaling automation with health validation and backup safeguards.
- Suspension/resume flows preserving data and secrets.
- Controlled deprovisioning with archived backups and billing updates.
- AI risk scoring for destructive actions and shared context outputs.

## Invocation patterns

```bash
/tenant-lifecycle-manager provision --tenant=t-acme-prod --tier=enterprise --region=eastus
/tenant-lifecycle-manager scale --tenant=t-acme-prod --nodeCount=5 --dbSku=D8s_v3
/tenant-lifecycle-manager suspend --tenant=t-unpaid-001 --reason=payment-failure
/tenant-lifecycle-manager failover --tenant=t-acme-prod --region=westeurope
/tenant-lifecycle-manager deprovision --tenant=t-churned-co --confirm=true
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `tenant` | Tenant identifier. | `t-acme-prod` |
| `tier` | SLA tier (starter/business/enterprise/critical). | `enterprise` |
| `region` | Cloud region for provisioning. | `eastus` |
| `nodeCount` | Node pool size for scaling. | `5` |
| `dbSku` | Database SKU for scaling. | `Standard_D8s_v3` |
| `reason` | Reason for suspension/failover. | `payment-failure` |

## Output contract

```json
{
  "operationId": "TL-2026-0315-01",
  "tenant": "t-acme-prod",
  "status": "success|failure|partial",
  "operation": "provision|scale|suspend|resume|deprovision|failover",
  "tier": "enterprise",
  "region": "eastus",
  "riskScore": 0.41,
  "events": [
    { "name": "tenant-provisioned", "timestamp": "2026-03-15T08:12:00Z" }
  ],
  "logs": "shared-context://memory-store/tenant-lifecycle/TL-2026-0315-01",
  "decisionContext": "redis://memory-store/tenant-lifecycle/TL-2026-0315-01"
}
```

## World-class workflow templates

### Provisioning/onboarding
1. Validate inputs (tenant uniqueness, quotas, region availability).
2. Apply tier template (Terraform/ARM) drilling down resource groups, namespaces, secrets, DNS, and catalogs.
3. Configure identity (service principals) and load data.
4. Emit `tenant-provisioned` event with registry metadata and notify stakeholders.

### Scaling & health
1. Scale compute/storage/database per demand; pre-scale backup/snapshot.
2. Run health probes/journals and verify pods/nodes.
3. Update shared context and emit `tenant-scaled`.

### Suspension/resume
1. Scale down (nodepool to 0, stop databases) while retaining data.
2. Replace DNS/traffic with maintenance view.
3. Resume by scaling up and rotating secrets as needed; emit `tenant-resumed`.

### Deprovisioning
1. Confirm deletion (human gate required for production).
2. Backup to cold storage (retain 90 days), destroy infra (terraform destroy), revoke identities.
3. Archive registry entry; keep audit trail for compliance; emit `tenant-deprovisioned`.

## AI intelligence highlights
- **AI Risk Assessment**: models change size, tier impact, recent incidents to determine riskScore.
- **Intelligent Scaling Suggestions**: recommends right-sizing actions using capacity and cost data.
- **Predictive Suspension Alerts**: warns when payment/policy signals indicate scheduling suspension.
- **Remediation Prioritization**: sequences provisioning/resume steps to minimize downtime.

## Memory agent & dispatcher integration
- Store lifecycle metadata at `shared-context://memory-store/tenant-lifecycle/<operationId>`.
- Emit events: `tenant-provisioned`, `tenant-scaled`, `tenant-suspended`, `tenant-deprovisioned`.
- Listen to dispatcher signals (`capacity-alert`, `policy-risk`, `incident-ready`) to automatically adjust tenants.
- Tag metadata with `decisionId`, `tenant`, `tier`, `riskScore`.

## Communication protocols
- Primary: shell scripts/terraform pipelines for provisioning, scaling, suspension.
- Secondary: Event bus for `tenant-lifecycle-*` events.
- Fallback: JSON artifacts `artifact-store://tenant-lifecycle/<operationId>.json`.

## Observability & telemetry
- Metrics: tenants provisioned, scaling actions, suspension counts, failovers, riskScore distribution.
- Logs: structured `log.event="tenant.lifecycle"` with `operation`, `tenant`, `decisionId`.
- Dashboards: integrate `/tenant-lifecycle-manager metrics --format=prometheus`.
- Alerts: riskScore ≥ 0.85, queue of pending onboarding requests > threshold, suspension/resume failure.

## Failure handling & retries
- Retry provisioning/scaling/failover calls up to 2× on transient cloud API failures.
- Emit `tenant-operation-failed` when retries exhausted; escalate to incident runbook.
- Preserve artifacts for auditing until downstream ack.

## Human gates
- Required when:
 1. Operations involve production-critical tenants or decommissioning.
 2. Tier changes affect SLAs or billing significantly.
 3. Dispatcher flags manual review after multiple failed operations.
- Use standard confirmation template to capture Impact/Reversibility.

## Testing & validation
- Dry-run: `/tenant-lifecycle-manager provision --tenant=TL-DRY --dry-run`.
- Unit tests: `backend/tenant-lifecycle/` ensures state transitions and scoring logic.
- Integration: `scripts/validate-tenant-lifecycle.sh` exercises provision → scale → suspend → resume → decommission flows.
- Regression: nightly `scripts/nightly-tenant-smoke.sh` keeps state transitions, metrics, and alerts stable.

## References
- Tier templates: `infrastructure/tenant/`.
- Registry: `docs/tenant-registry.md`.
- Onboarding docs: `docs/platform-onboarding.md`.

## Related skills
- `/workflow-management`: orchestrates lifecycle workflows with dependencies.
- `/policy-as-code`: validates governance before provisioning/resume.
- `/disaster-recovery`: coordinates failover and backup for tenants.

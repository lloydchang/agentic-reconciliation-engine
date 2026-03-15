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

Manages the SaaS tenant lifecycle across clouds: provisioning, scaling, suspension/resume, failover, and clean decommissioning with AI risk scoring and dispatcher telemetry.

## When to invoke
- Provision new tenants or clone existing environments.
- Scale compute, storage, or managed services per tenant demand.
- Suspend/resume tenants for billing/security reasons.
- Execute failovers or deprovision tenants with data retention requirements.
- React to dispatcher signals (`policy-risk`, `capacity-alert`, `incident-ready`) affecting tenants.

## Capabilities
- **Multi-cloud provisioning** with tiered templates (starter/business/enterprise/critical) plus identity/secrets automation.
- **AI risk scoring** for destructive actions (decommission, scale-down) balancing blast radius and recent incidents.
- **Controlled scaling, suspension, failover** flows with validations, metrics, and guardrails.
- **Shared-context propagation** at `shared-context://memory-store/tenant-lifecycle/{operationId}` for downstream skills.
- **Human gating** for irreversible operations (deprovision, failover) and escalation-ready alerts.

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
| `tenant` | Tenant/customer identifier. | `t-acme-prod` |
| `tier` | SLA tier (`starter|business|enterprise|critical`). | `enterprise` |
| `region` | Cloud region for operations. | `eastus` |
| `nodeCount` | Node pool replica count for scaling. | `5` |
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
  "events": [ { "name": "tenant-provisioned", "timestamp": "2026-03-15T08:12:00Z" } ],
  "logs": "shared-context://memory-store/tenant-lifecycle/TL-2026-0315-01",
  "decisionContext": "redis://memory-store/tenant-lifecycle/TL-2026-0315-01"
}
```

## World-class workflow templates

### Provisioning & onboarding
1. Validate tenant uniqueness, quotas, and region availability.
2. Apply tier template (Terraform/ARM) to provision RGs, namespaces, secrets, DNS, and catalog entries.
3. Configure identity/secrets, load data, and emit `tenant-provisioned` event.

### Scaling & health validation
1. Scale compute/storage/database with pre-snapshot/backups.
2. Run health probes (pods/nodes) and check observability dashboards.
3. Emit `tenant-scaled` and log scaling metadata.

### Suspension/resume/failover
1. Scale down or drain resources while retaining data/secrets; reroute traffic to maintenance pages.
2. Resume by scaling up, rotating secrets if needed, and verifying connectivity.
3. Fail over to DR regions by promoting replicas, updating DNS, and validating failback readiness.
4. Emit `tenant-suspended`, `tenant-resumed`, or `tenant-failover` events.

### Deprovisioning
1. Confirm destructive action with human gate for production tenants.
2. Archive backups (90-day retention), destroy infrastructure, revoke identities, clean secrets.
3. Emit `tenant-deprovisioned` event and keep auditable context for compliance.

## AI intelligence highlights
- **AI risk assessment** considers change size, tier SLA, incidents, and tenant count to compute riskScore.
- **Intelligent scaling suggestions** align with capacity/cost intelligence for right-sizing.
- **Predictive suspension alerts** warn when payment/policy signals suggest upcoming suspensions.
- **Remediation prioritization** sequences operations to minimize downtime.

## Memory agent & dispatcher integration
- Store lifecycle metadata under `shared-context://memory-store/tenant-lifecycle/{operationId}`.
- Emit events: `tenant-provisioned`, `tenant-scaled`, `tenant-suspended`, `tenant-resumed`, `tenant-deprovisioned`, `tenant-failover`.
- React to dispatcher triggers (capacity, policy, incident) to auto-scale, suspend, or fail over tenants.
- Tag context with `decisionId`, `tenant`, `tier`, `region`, `riskScore`.

## Observability & telemetry
- Metrics: tenants provisioned, scaling actions, suspensions, failovers, deprovision counts, riskScore trends.
- Logs: structured `log.event="tenant.lifecycle"` capturing `operation`, `tenant`, `decisionId`.
- Dashboards: integrate `/tenant-lifecycle-manager metrics --format=prometheus` for fleet visibility.
- Alerts: riskScore ≥ 0.85, pending onboarding backlog > threshold, suspension/resume failures.

## Failure handling & retries
- Retry cloud API calls for provisioning/scaling/failover up to 2× on transient errors.
- Emit `tenant-operation-failed`, escalate to `incident-triage-runbook`, and preserve artifacts for audit.
- Do not delete shared-context or logs until downstream acknowledgment completes.

## Human gates
- Required when:
  1. Operations target production or critical-tier tenants.
  2. Deprovisioning or suspension impacts billing, compliance, or secrets.
  3. Dispatcher requests manual review after retries/failures.
- Confirmation template matches orchestrator style (impact, reversibility).

## Testing & validation
- Dry-run: `/tenant-lifecycle-manager provision --tenant=TL-DRY --dry-run`.
- Unit tests: `backend/tenant-lifecycle/` ensures transitions and scoring.
- Integration: `scripts/validate-tenant-lifecycle.sh` runs provision → scale → suspend → resume → decommission.
- Regression: nightly `scripts/nightly-tenant-smoke.sh` ensures transitions, metrics, and alerts remain stable.

## References
- Tier templates: `infrastructure/tenant/`.
- Registry docs: `docs/tenant-registry.md`.
- Onboarding guide: `docs/platform-onboarding.md`.

## Related skills
- `/workflow-management`: orchestrates lifecycle pipelines.
- `/policy-as-code`: validates governance during provisioning/resume.
- `/disaster-recovery`: coordinates failover plus backup tasks.

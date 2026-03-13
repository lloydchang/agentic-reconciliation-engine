---
name: tenant-lifecycle-manager
description: >
  Use this skill to automate the full SaaS tenant lifecycle: provisioning,
  configuration, scaling, suspension, and deprovisioning across multi-cloud
  environments. Triggers: requests to onboard a new tenant, offboard or
  deprovision a tenant, resize/scale a tenant's resources, clone an environment
  for testing, or audit tenant resource allocation and billing tags.
user-invocable: true
allowed-tools:
  - bash
  - computer
---

# Tenant Lifecycle Manager Skill

Automate every stage of the SaaS tenant lifecycle with idempotent, auditable
operations across Azure, AWS, and GCP. All operations are tracked in the tenant
registry and emit structured events for billing and compliance.

## Phase 1 — Provisioning (New Tenant Onboarding)

### Inputs required
```yaml
tenant_id: "t-acme-prod"
tier: "enterprise|business|starter"
region: "eastus|westeurope|southeastasia"
cloud: "azure|aws|gcp"
```

### Steps
1. **Validate inputs** — check tenant_id uniqueness, region availability, quota
2. **Create namespace / resource group**
   ```bash
   az group create --name "rg-${TENANT_ID}" --location $REGION --tags "tenant=$TENANT_ID" "tier=$TIER"
   ```
3. **Apply tier template** via Terraform module:
   ```bash
   terraform apply -var="tenant_id=$TENANT_ID" -var="region=$REGION"
   ```
4. **Health check** — poll `/health` endpoint until 200 OK (max 10 min)
   ```bash
   curl -s -f https://${TENANT_ID}.app.example.com/health
   ```
5. **Register in tenant registry** — write to central DB with full metadata
   ```bash
   echo "Registered $TENANT_ID"
   ```

---
## Phase 4 — Deprovisioning (HUMAN GATE)

Requires explicit confirmation with `--confirm-delete $TENANT_ID`.

### Steps
1. **Export full data backup**
2. **Destroy infrastructure** via `terraform destroy`
   ```bash
   terraform destroy -auto-approve -var="tenant_id=$TENANT_ID"
   ```

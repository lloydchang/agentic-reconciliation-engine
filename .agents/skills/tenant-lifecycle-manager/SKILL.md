---
name: tenant-lifecycle-manager
description: >
  Use this skill to automate the full SaaS tenant lifecycle: provisioning,
  configuration, scaling, suspension, and deprovisioning across multi-cloud
  environments. Triggers: requests to onboard a new tenant, offboard or
  deprovision a tenant, resize/scale a tenant's resources, clone an environment
  for testing, or audit tenant resource allocation and billing tags.
tools:
  - bash
  - computer
---

# Tenant Lifecycle Manager Skill

Automate every stage of the SaaS tenant lifecycle with idempotent, auditable
operations across Azure, AWS, and GCP. All operations are tracked in the tenant
registry and emit structured events for billing and compliance.

# Tenant Lifecycle Manager Skill

Automate every stage of the SaaS tenant lifecycle with idempotent, auditable
operations across Azure, AWS, and GCP. All operations are tracked in the tenant
registry and emit structured events for billing and compliance.

## Enhanced Tenant Lifecycle Automation

### Automated Provisioning, Configuration, and Retirement
Automate provisioning, configuration, and retirement of SaaS tenants.

**Workflow:**
1. Tenant creation - Set up new tenant environments
2. Tenant configuration - Apply tenant-specific settings and templates
3. Tenant scaling - Adjust resources based on tenant needs
4. Tenant decommissioning - Clean removal of tenant resources

**Process:**
1. Receive tenant request with specifications
2. Allocate infrastructure resources based on tier and requirements
3. Apply configuration templates for the tenant environment
4. Validate tenant health and functionality
5. Monitor ongoing tenant operations

**Output:** Tenant provisioning status and health reports.

---

## Tenant States

```
REQUESTED → PROVISIONING → ACTIVE → SUSPENDED → DEPROVISIONING → DELETED
                                 ↘ SCALING ↗
```

---

## Phase 1 — Provisioning (New Tenant Onboarding)

### Inputs required
```yaml
tenant_id: "t-acme-prod"
tier: "enterprise|business|starter"
region: "eastus|westeurope|southeastasia"
cloud: "azure|aws|gcp"
owner_email: "ops@acme.com"
data_residency: "us|eu|apac"
```

### Steps
1. **Validate inputs** — check tenant_id uniqueness, region availability, quota
2. **Create namespace / resource group**
   ```bash
   az group create --name "rg-${TENANT_ID}" --location $REGION \
     --tags "tenant=$TENANT_ID" "tier=$TIER" "managed_by=tenant-lifecycle"
   ```
3. **Apply tier template** via Terraform module:
   ```bash
   terraform apply -var-file="tiers/${TIER}.tfvars" \
     -var="tenant_id=$TENANT_ID" -var="region=$REGION"
   ```
4. **Configure identity** — create service principal / workload identity
5. **Seed initial data** — apply database migrations, seed config
6. **DNS registration** — create `${TENANT_ID}.app.example.com` CNAME
7. **Secret injection** — populate tenant secrets in Key Vault / Secrets Manager
8. **Health check** — poll `/health` endpoint until 200 OK (max 10 min)
9. **Register in tenant registry** — write to central DB with full metadata
10. **Notify** — send welcome email and ops confirmation

### Tier Profiles

| Resource         | Starter | Business | Enterprise |
|------------------|---------|----------|------------|
| AKS node count   | 1       | 3        | 5+         |
| DB SKU           | Basic   | GP_S_2   | BC_8       |
| Storage (GB)     | 50      | 500      | 5000       |
| SLA target       | 99.5%   | 99.9%    | 99.99%     |
| Backup retention | 7 days  | 30 days  | 90 days    |

---

## Phase 2 — Scaling

Triggered by: usage threshold, tier upgrade, or manual request.

```bash
# Scale AKS node pool
az aks nodepool scale --cluster-name "aks-${TENANT_ID}" \
  --name workload --node-count $NEW_COUNT

# Resize database
az postgres flexible-server update --name "pg-${TENANT_ID}" \
  --sku-name $NEW_SKU

# Expand storage
az disk update --name "disk-${TENANT_ID}" --size-gb $NEW_SIZE
```

All scaling operations are:
- Non-destructive by default
- Preceded by a pre-scale snapshot/backup
- Validated with a health check post-scale

---

## Phase 3 — Suspension

Triggered by: payment failure, policy violation, or manual request.

```bash
# Scale down to zero but retain data
az aks nodepool scale ... --node-count 0
# Stop database (keeps storage, stops billing)
az postgres flexible-server stop --name "pg-${TENANT_ID}"
# Block DNS / set maintenance page
```

Suspension is **fully reversible** — resume with Phase 1 Step 8 onward.

---

## Phase 4 — Deprovisioning

**Requires explicit confirmation** with `--confirm-delete $TENANT_ID`.

Steps:
1. Export full data backup to cold storage (retain for 90 days by default)
2. Revoke all service principals and rotate/delete secrets
3. Destroy infrastructure via `terraform destroy`
4. Deregister DNS
5. Archive tenant record (never hard-delete the registry row)
6. Emit `TENANT_DELETED` event to billing system

---

## Tenant Registry

Maintain a central registry entry per tenant:
```json
{
  "tenant_id": "t-acme-prod",
  "state": "ACTIVE",
  "tier": "enterprise",
  "cloud": "azure",
  "region": "eastus",
  "provisioned_at": "ISO8601",
  "owner": "ops@acme.com",
  "resource_group": "rg-t-acme-prod",
  "health_endpoint": "https://t-acme-prod.app.example.com/health",
  "last_health_check": "ISO8601",
  "tags": {}
}
```

---

## Examples

- "Provision a new enterprise tenant for Acme Corp in East US on Azure"
- "Upgrade tenant t-widgets-prod from Business to Enterprise tier"
- "Suspend tenant t-unpaid-001 due to payment failure"
- "Deprovision and archive all data for tenant t-churned-co"
- "Show me all tenants in the provisioning state for longer than 30 minutes"

---

## Output Format

```json
{
  "tenant_id": "string",
  "tier": "starter|business|enterprise|enterprise-plus",
  "operation": "provision|scale|suspend|deprovision",
  "previous_state": "string",
  "new_state": "string",
  "duration_seconds": 0,
  "status": "success|failure|partial",
  "errors": [],
  "registry_url": "string"
}
```

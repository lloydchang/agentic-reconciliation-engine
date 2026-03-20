# Crossplane Migration: Executive Summary

**Terraform → Kubernetes-Native IaC**

---

## Business Case

### Why Migrate?

1. **Unified Control Plane**: Manage all cloud infrastructure via Kubernetes APIs
2. **GitOps at Scale**: Infrastructure changes via PRs, audited, reviewed
3. **Multi-Cloud Abstraction**: Cloud-agnostic claims let developers request resources without cloud expertise
4. **Declarative & Self-Healing**: Crossplane automatically reconciles drift
5. **Cost Optimization**: Native visibility across clouds; finer-grained RBAC reduces over-provisioning

### Current Pain Points

- **Terraform State Sprawl**: Multiple state files, locking issues, manual operations
- **Provider Fragmentation**: Different IaC for AWS, GCP, Azure
- **Slow Provisioning**: Terraform apply cycles, manual approvals, no self-service
- **Limited Visibility**: No single dashboard for cross-cloud inventory
- **Orchestration Complexity**: Custom Python/Go layers to coordinate across clouds

---

## Solution Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Git Repository (GitOps)                  │
│   core/operators/control-plane/crossplane/                  │
│   ├── xrds/      (CompositeResourceDefinitions)           │
│   ├── compositions/ (cloud-specific implementations)      │
│   └── providers/   (ProviderConfigs, credentials)         │
└────────────────────────────┬────────────────────────────────┘
                             │ Flux/ArgoCD Sync
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              Single Hub Cluster (Crossplane)               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Crossplane Core                                     │   │
│  │ • XRD Controllers                                  │   │
│  │ • Composition Controllers                          │   │
│  │ • Provider Connectors                              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────┬──────────────┬──────────────┐           │
│  │ AWS Provider │ Azure Provider│ GCP Provider  │           │
│  └──────────────┴──────────────┴──────────────┘           │
│                                                             │
│  ProviderConfigs: aws-provider, azure-provider, gcp-provider│
└─────────────────────────────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌─────────┐  ┌─────────┐  ┌─────────┐
        │   AWS   │  │  Azure  │  │   GCP   │
        │ Resources│  │ Resources│  │ Resources│
        └─────────┘  └─────────┘  └─────────┘
```

### Key Components

| Component | Purpose | Location |
|---|---|---|
| **XRDs** | Define cloud-agnostic resource types (XDatabase, XCluster, XNetwork) | `core/operators/control-plane/crossplane/xrds/` |
| **Compositions** | Map XR specs to provider-specific managed resources | `core/operators/control-plane/crossplane/compositions/` |
| **ProviderConfigs** | Cloud credentials, scoped by namespace/RBAC | `core/operators/control-plane/crossplane/providers/` |
| **Claims** | User requests for resources (spoke teams) | `core/resources/tenants/{layer}/` |
| **GitOps** | Flux/ArgoCD auto-syncs claims to cloud | Already deployed |

---

## Migration Scope

### In Scope

✅ **Complete Infrastructure Set**:
- Networking: VPCs, subnets, security groups, NAT, route tables
- Compute: EKS, AKS, GKE clusters + node pools
- Data: RDS, Cloud SQL, PostgreSQL, Redis
- Storage: S3, Blob Storage, Cloud Storage buckets
- Load Balancing: ALB, Application Gateway, Cloud Load Balancer
- Security: WAF, SSL certificates, security groups
- DNS: Route53, Azure DNS, Cloud DNS
- Monitoring: CloudWatch, Azure Monitor, Cloud Monitoring (partial)

✅ **Cross-Cloud Support**: AWS, Azure, GCP
✅ **Backwards Compatibility**: Terraform preserved during transition
✅ **Hub-Spoke Pattern**: Single Crossplane instance with ProviderConfig isolation

### Out of Scope

❌ **IAM & Permissions**: Keep in Terraform (or separate module)
❌ **Provider-specific analytics**: BigQuery datasets, CloudWatch dashboards (optional)
❌ **Application deployments**: Only infrastructure; application workloads stay on ArgoCD
❌ **Custom Terraform modules**: Non-infrastructure Terraform (e.g., packaging, distribution)

---

## Migration Timeline

```
Week 1: Assessment ──────────────────────────────────────┐
  • Inventory matrix complete
  • Gap analysis done
  • Prerequisites verified

Week 2-3: Foundation ────────────────────────────────────┐
  • Provider health checks
  • GitOps validation
  • Crossplane orchestrator integration branch

Week 4: Networks ────────────────────────────────────────┐
  • XNetwork XRD + Compositions ready
  • All VPCs/VNets migrated
  • Terraform network code deprecated

Week 5: Clusters ────────────────────────────────────────┐
  • XCluster XRD + Compositions ready
  • EKS/AKS/GKE migrated
  • Kubeconfigs updated

Week 6: Databases & Storage ─────────────────────────────┐
  • XDatabase, XStorage XRD ready
  • All DBs, buckets migrated
  • Data integrity verified

Week 7: Advanced Services ───────────────────────────────┐
  • LBs, WAF, DNS, certs migrated
  • Monitoring configured
  • All infra in Crossplane

Week 8: Cutover ─────────────────────────────────────────┐
  • Terraform decommissioned
  • Documentation complete
  • Team training done
  • Hypercare period begins
```

---

## Resource Mapping Summary

| Provider | Total Resources | ✅ Crossplane Ready | 🔧 Custom XRD | ⚠️ Keep Terraform |
|----------|----------------|-------------------|---------------|-------------------|
| AWS | 30+ | 25 | 3 (SG, Redis, Cert) | 2 (IAM, some ALB bits) |
| GCP | 25+ | 20 | 3 (Redis, DNS?, IAM) | 2 (KMS, BigQuery) |
| Azure | 20+ | 18 | 2 (Redis, maybe SG) | 0-2 (IAM optional) |
| **Total** | **75+** | **63** | **~8** | **~4** |

**Ready Rate**: 84% of resources have direct Crossplane equivalents.

---

## Success Metrics

### Quantitative

- [ ] **100% migration**: All production infrastructure provisioned via Crossplane claims
- [ ] **Zero Terraform drift**: `terraform plan` shows no changes for migrated resources
- [ ] **99%+ reconciliation**: XResources in `Ready=True` state
- [ ] **No downtime**: All applications remain available during cutover
- [ ] **Cost neutral**: No >10% cost variance post-migration

### Qualitative

- [ ] **Developer experience**: Teams provision infra with `kubectl apply -f my-db.yaml`
- [ ] **Auditability**: Every change tracked in Git PRs, reviewed
- [ ] **Observability**: Crossplane status visible in Grafana dashboards
- [ ] **Self-service**: Teams can self-provision with proper RBAC
- [ ] **Maintainability**: Single control plane to manage, upgrade Crossplane once

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Provider bugs | Medium | High | Test in dev/staging first; provider version pins |
| Terraform state loss | Low | Critical | State backups to S3 + Glacier; restore practice |
| Resource conflicts | Medium | High | Strict single source of truth; drift alerts |
| Quota limits | Medium | Medium | Request increases; stagger migration |
| Learning curve | High | Medium | Training, pilot migrations, runbooks |

---

## Financial Impact

### Cost Savings

- **Terraform Cloud/Enterprise**: ~$0 (using open-source) → $0 (Crossplane free)
- **Reduced operational overhead**: 1 platform engineer ≈ 40h/month saved on infra debugging
- **Efficiency gains**: Faster provisioning → developer time saved
- **Multi-cloud optimization**: Better visibility → rightsizing → ~5-10% cloud cost reduction

**Estimated ROI**: 6-12 months payback period

---

## Next Steps

### Immediate (This Week)

1. Review and approve this migration plan
2. Assign migration workstream leads
3. Begin Phase 0: Assessment tasks
4. Schedule kickoff meeting with all stakeholders

### Short-term (Weeks 2-4)

1. Create missing XRDs (XSecurityGroup, XRedis)
2. Update Compositions for all providers
3. Set up dev/test environment for validation
4. Begin pilot migration: one team's dev environment (non-critical)

### Long-term (Months 2-3)

1. Full production migration across all teams
2. Decommission Terraform completely
3. Retrospective and process documentation
4. Scale to additional cloud regions/accounts

---

## Stakeholders

| Role | Responsibility | Contact |
|------|----------------|---------|
| **Platform Engineering** | Lead migration, Crossplane expertise | |
| **DevOps/SRE** | GitOps, Flux/ArgoCD, cluster management | |
| **Security Team** | RBAC, Provider credentials, compliance | |
| **Application Teams** | Test migrated infrastructure, provide feedback | |
| **Finance/Cloud Billing** | Cost tracking, budget alerts | |

---

## Questions & Decisions Required

### To Be Answered Before Migration:

1. **IAM Strategy**: Keep in Terraform or attempt Crossplane IAM?
2. **Centralized Logging**: Will Crossplane resources emit logs to existing ELK/Loki?
3. **Cost Allocation**: How to tag Crossplane-created resources for chargeback/showback?
4. **Disaster Recovery**: Crossplane cluster failure → how to recover? (etcd backups, etc.)
5. **Provider Versioning**: Pin provider versions? How to upgrade across fleet?

---

## Appendix: Crossplane Concepts Refresher

### Key Terms

- **XRD (CompositeResourceDefinition)**: Defines a new Kubernetes custom resource type (like a schema). Example: `XDatabase` defines what a "database" looks like to developers.
- **Composition**: Defines HOW an XRD is fulfilled. Maps XRD fields to one or more managed resources (RDS, Cloud SQL, etc.). One XRD can have multiple Compositions (one per cloud).
- **Managed Resource (MR)**: Provider-specific resource type (e.g., `rds.aws.crossplane.io/v1beta1/DBInstance`).
- **Claim**: What a developer creates. References an XRD with their requirements. The platform team writes Compositions; developers write Claims.
- **ProviderConfig**: Contains cloud credentials and scoping (which namespaces can use which provider).

### Example Flow

1. Platform creates: `XDatabase` XRD + `database-aws.yaml` Composition
2. Developer creates: `Database` claim requesting postgres, size medium
3. Crossplane controller sees claim, matches to Composition, creates:
   - `DBSubnetGroup` MR
   - `DBInstance` MR
   - Patches connection details back to claim status
4. Developer reads connection secret: `kubectl get secret orders-db-conn -o jsonpath='{.data.password}'`

---

**Document Version**: 1.0
**Last Updated**: 2026-03-20
**Status**: Draft → Ready for Review → **Approved for Execution** → In Progress

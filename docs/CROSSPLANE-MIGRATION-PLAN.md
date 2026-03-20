# Crossplane Migration Plan

**Migration from Terraform to Crossplane Kubernetes-Native IaC**

---

## Executive Summary

This document outlines the comprehensive plan to migrate existing multi-cloud infrastructure from Terraform to Kubernetes-native Crossplane control plane while maintaining backwards compatibility and supporting hub-spoke deployments per cloud provider.

### Current State

- **Terraform IaC**: Separate `main.tf` files for AWS, GCP, Azure under `/core/infrastructure/terraform/`
- **Multi-Cloud Orchestration**: Python/Go/JS orchestration layer (`multi_cloud_orchestrator.py`, `multi-cloud-scatter-gather.go`, `multi-cloud-abstraction.js`)
- **Existing Crossplane**: Already deployed with XRDs, Compositions, and Provider configs for AWS, Azure, GCP, Kubernetes
- **Architecture**: Single Crossplane instance with ProviderConfig isolation (recommended)

### Target State

- **Single Source of Truth**: Infrastructure defined as Kubernetes Custom Resources (XRDs + Claims)
- **GitOps Pipeline**: Flux/ArgoCD reconciliation from Git to cloud providers
- **Multi-Cloud Unified**: Cloud-agnostic claims with provider-specific Compositions
- **Backwards Compatible**: Existing Terraform configurations preserved during transition
- **ProviderConfig Isolation**: Single Crossplane instance using ProviderConfig for multi-cloud isolation and RBAC

---

## 1. Migration Strategy

### Phased Approach (6-8 weeks)

| Phase | Duration | Objectives | Deliverables |
|-------|----------|------------|--------------|
| **Phase 0: Assessment** | Week 1 | Inventory, analysis, prerequisites | Inventory matrix, Gap analysis, Prereq checklist |
| **Phase 1: Foundation** | Week 2-3 | Crossplane providers, ProviderConfigs, RBAC | Provider deployments, IAM roles, GitOps sync |
| **Phase 2: Network First** | Week 4 | Migrate VPC/VNet networking to Crossplane | XNetwork XRD + Compositions, Network claims |
| **Phase 3: Compute Clusters** | Week 5 | Migrate EKS/AKS/GKE to Crossplane | XCluster XRD + Compositions, Cluster claims |
| **Phase 4: Data & Services** | Week 6 | Migrate databases, caches, storage | XDatabase, XQueue, XStorage XRD + Compositions |
| **Phase 5: Advanced Services** | Week 7 | Migrate load balancers, WAF, DNS | XLB XRD, XWAF XRD, XDNS XRD + Compositions |
| **Phase 6: Cutover & Decommission** | Week 8 | Testing, validation, Terraform decommission | Test reports, Cutover playbook, Terraform archival |

### Architecture Decision: Single Crossplane Instance

**Updated per architectural review**: Use single Crossplane instance with ProviderConfig-based isolation instead of hub-spoke.

#### Why Single Instance

- **Simplified Operations**: One control plane to manage, upgrade, debug
- **Cross-Cloud Compositions**: Compositions can span multiple providers naturally
- **GitOps Simplicity**: One target cluster, one source of truth repository
- **Isolation via ProviderConfig**: RBAC, NetworkPolicies, and ProviderConfig scoping provides sufficient multi-tenancy
- **Reduced Operational Tax**: No provider version drift, no XRD sync across clusters

#### ProviderConfig Isolation Pattern

```yaml
# AWS production config (isolated via RBAC and allowedNamespaces)
apiVersion: aws.crossplane.io/v1beta1
kind: ProviderConfig
metadata:
  name: aws-provider-prod
  namespace: crossplane-system
spec:
  credentials:
    source: InjectedIdentity  # IRSA/Workload Identity
  allowedNamespaces:
    - "production-*"

# Azure development config
apiVersion: azure.crossplane.io/v1beta1
kind: ProviderConfig
metadata:
  name: azure-provider-dev
  namespace: crossplane-system
spec:
  credentials:
    clientID: "..."
    tenantID: "..."
    subscriptionID: "..."
  allowedNamespaces:
    - "development-*"
```

#### When to Consider Hub-Spoke

Only if:
- Separate platform teams cannot share control plane
- Using Upbound Spaces where hub-spoke is native
- Regulatory requirements mandate physical separation

**Recommendation**: Start single. Split only if operational limits hit.

---

### Parallel Work Streams

1. **Infrastructure Migration** (Technical): Building Crossplane resources
2. **GitOps Integration** (Platform): Flux/ArgoCD pipelines, RBAC, security
3. **Multi-Cloud Orchestrator Update** (Software): Adapt orchestration layer to use Crossplane APIs
4. **Testing & Validation** (QA): Drift detection, reconciliation testing, disaster recovery
5. **Documentation & Training** (Knowledge): Runbooks, migration guides, operator training

---

## 2. Detailed Phase Plans

### Phase 0: Assessment & Prerequisites (Week 1)

#### Tasks

1. **Complete Inventory Matrix**
   - Catalog all Terraform resources by provider, type, region
   - Map Terraform resources to Crossplane managed resources
   - Identify dependencies and resource relationships
   - Document provider-specific features used (AWS specific, Azure specific, etc.)

2. **Gap Analysis**
   - Compare existing Terraform with available Crossplane Compositions
   - Identify missing managed resources (resources not yet supported by Crossplane provider)
   - Document custom modules/scripts that need Crossplane equivalents
   - Assess provider capabilities (check provider CRDs: `kubectl get crd | grep crossplane`)

3. **Prerequisites Setup**
   - [ ] Verify all Crossplane providers installed: `provider-aws`, `provider-azure`, `provider-gcp`, `provider-kubernetes`
   - [ ] Confirm ProviderConfigs exist for each cloud with proper credentials (InjectedIdentity / Workload Identity)
   - [ ] Establish GitOps repository structure for Crossplane manifests
   - [ ] Set up Flux/ArgoCD to sync `core/operators/control-plane/crossplane/` to clusters
   - [ ] Create RBAC roles for platform team to manage Crossplane resources
   - [ ] Backup all Terraform state files (S3 backends, etc.)

#### Outputs

- `docs/migration/inventory-MATRIX.md`
- `docs/migration/gap-analysis.md`
- `docs/migration/prerequisites-VERIFIED.md`
- Terraform state backups archived

---

### Phase 1: Foundation & Provider Validation (Week 2-3)

#### Tasks

1. **Provider Health Checks**
   ```bash
   # Verify all providers are healthy
   kubectl get providers -n crossplane-system
   # Expected: provider-aws, provider-azure, provider-gcp, provider-kubernetes all HEALTHY

   # Check ProviderConfigs
   kubectl get providerconfigs -n crossplane-system
   # Expected: aws-provider, azure-provider, gcp-provider, kubernetes-provider
   ```

2. **Test Basic Managed Resources**
   - Deploy test managed resource for each provider to verify connectivity
   - Example: Create S3 bucket via Crossplane (AWS), storage account (Azure), GCS bucket (GCP)

   ```yaml
   # Example: test S3 bucket
   apiVersion: s3.aws.crossplane.io/v1beta1
   kind: Bucket
   metadata:
     name: test-crossplane-bucket
   spec:
     forProvider:
       locationConstraint: us-west-2
     providerConfigRef:
       name: aws-provider
   ```

3. **GitOps Pipeline Validation**
   - Ensure Flux/ArgoCD picks up changes from `core/operators/control-plane/crossplane/`
   - Test Kustomization for XRDs, Compositions, Providers
   - Verify automated sync and reconciliation loops

4. **Multi-Cloud Orchestrator Integration**
   - Update `multi_cloud_orchestrator.py` to detect Crossplane resources
   - Add capability to read Crossplane Composite resources (XDatabase, XCluster status)
   - Implement Crossplane as alternative provisioning path
   - Log infrastructure changes from Crossplane events

#### Outputs

- Provider health verified in all clouds (AWS, Azure, GCP, on-prem Kubernetes)
- Test managed resources created and deleted successfully
- GitOps pipeline validated with successful syncs
- `multi_cloud_orchestrator.py` Crossplane integration branch ready

---

### Phase 2: Network Migration (Week 4)

**Goal**: Migrate VPC/VNet networking from Terraform to Crossplane

#### Tasks

1. **Create XNetwork XRD** (already exists - verify completeness)
   - Review `core/operators/control-plane/crossplane/xrds/xnetwork.yaml`
   - Ensure it covers all network requirements: VPC, subnets, NAT, route tables, security groups, peering

2. **Update Compositions for All Providers** (adjust if needed)
   - **AWS**: `compositions/network-aws.yaml` → creates VPC, subnets, IGW, NAT, route tables, SG
   - **Azure**: `compositions/network-azure.yaml` → creates VNet, subnets, NSG, VPN gateway if needed
   - **GCP**: `compositions/network-gcp.yaml` → creates VPC, subnets, Cloud Router, NAT

   Verify these Compositions map correctly to Terraform network resources:
   - Terraform `module.vpc` (AWS) → Crossplane XNetwork with `provider: aws`
   - Terraform `google_compute_network` (GCP) → Crossplane XNetwork with `provider: gcp`
   - Terraform `azurerm_virtual_network` (Azure) → Crossplane XNetwork with `provider: azure`

3. **Create Network Claims for Each Environment**
   - Create claim files mirroring Terraform network definitions
   - Place in `core/resources/tenants/1-network/` following the existing pattern:
     - `network-prod.yaml` (production network)
     - `network-staging.yaml` (staging network)
     - `network-dev.yaml` (development network)

   Example claim:
   ```yaml
   apiVersion: platform.example.com/v1alpha1
   kind: Network
   metadata:
     name: network-prod
     namespace: platform-infra
   spec:
     compositionSelector:
       matchLabels:
         provider: aws  # or azure/gcp based on environment
     cidrBlock: 10.0.0.0/16
     region: us-west-2
     deletionPolicy: Orphan
   ```

4. **Apply Network Claims via GitOps**
   ```bash
   kubectl apply -f core/resources/tenants/1-network/network-prod.yaml
   # Flux will sync and Crossplane will provision VPCs in each cloud
   ```

5. **Validate Network Provisioning**
   - Check network resources created in AWS console (VPC, subnets, etc.)
   - Verify Terraform state can be removed without destroying resources
   - Test drift: manually modify security group → Crossplane should reconcile

6. **Terraform Decommission (Networks Only)**
   - Remove network resources from Terraform state:
     ```bash
     terraform state rm module.vpc.aws_vpc.main
     terraform state rm module.vpc.aws_subnet.private[...]
     # etc.
     ```
   - Comment out or remove network resources from `main.tf` files
   - Run `terraform plan` to confirm no changes will be applied to networks
   - Keep Terraform code for other resources (not yet migrated)

#### Rollback Plan

- Keep Terraform network code (commented) for 2 weeks
- If Crossplane fails, manually import Crossplane-created resources into Terraform state:
  ```bash
  terraform import module.vpc.aws_vpc.main vpc-12345
  ```

---

### Phase 3: Compute Cluster Migration (Week 5)

**Goal**: Migrate EKS, AKS, GKE clusters from Terraform to Crossplane

#### Tasks

1. **Verify XCluster XRD & Compositions**
   - Check `xrds/xcluster.yaml` covers required cluster parameters: version, node pools, networking, addons
   - Review Compositions:
     - `cluster-eks.yaml` (EKS)
     - `cluster-aks.yaml` (AKS)
     - `cluster-gke.yaml` (GKE)
     - `cluster-capi-*.yaml` (CAPI clusters for multi-cluster management)

2. **Create Cluster Claims**
   - Create `core/resources/tenants/2-clusters/` directory if not exists
   - Define claims for each cluster:

   ```yaml
   # core/resources/tenants/2-clusters/cluster-eks-prod.yaml
   apiVersion: platform.example.com/v1alpha1
   kind: Cluster
   metadata:
     name: eks-prod
     namespace: platform-infra
   spec:
     compositionSelector:
       matchLabels:
         provider: aws
         tier: production
     region: us-west-2
     kubernetesVersion: "1.30"
     nodePools:
       - name: general
         instanceType: t3.large
         minSize: 3
         maxSize: 10
         desiredSize: 5
       - name: spot
         instanceType: t3.large
         capacityType: SPOT
         minSize: 0
         maxSize: 10
         desiredSize: 2
     deletionPolicy: Orphan
   ```

3. **Apply Cluster Claims**
   ```bash
   kubectl apply -f core/resources/tenants/2-clusters/
   # Wait for clusters to sync: Ready=True
   kubectl get clusters -n platform-infra -w
   ```

4. **Update Kubeconfig for New Clusters**
   - Crossplane can write connection secrets with kubeconfig
   - Update `~/.kube/config` or CI/CD cluster contexts to use Crossplane-managed clusters
   - Verify `kubectl get nodes` works for new clusters

5. **Decommission Terraform Clusters**
   - Import existing EKS/AKS/GKE into Crossplane if they exist (policy: Orphan first)
   - Remove from Terraform state:
     ```bash
     terraform state rm module.eks.aws_eks_cluster.this[0]
     terraform state rm module.eks.aws_eks_node_group.this[*]
     ```
   - Remove cluster modules from `main.tf` after verifying Crossplane clusters Healthy

---

### Phase 4: Database & Storage Migration (Week 6)

**Goal**: Migrate RDS, Cloud SQL, PostgreSQL, Redis, S3/Blob/Cloud Storage

#### Tasks

1. **XDatabase, XQueue XRD Review**
   - `xrds/xdatabase.yaml` covers RDS/Cloud SQL/Azure Database
   - Ensure fields cover all use cases: backup retention, HA, encryption, maintenance window
   - May need XRedis XRD extension (or reuse XDatabase with engine: redis)

2. **Database Compositions**
   - Verify `database-aws.yaml` maps to Terraform `module.rds` resources
   - Verify `database-gcp.yaml` maps to `google_sql_database_instance`
   - Verify `database-azure.yaml` maps to `azurerm_postgresql_flexible_server`

3. **Create Database Claims**
   ```yaml
   # core/resources/tenants/3-workloads/database-orders.yaml
   apiVersion: platform.example.com/v1alpha1
   kind: Database
   metadata:
     name: orders-db
     namespace: orders-team
   spec:
     compositionSelector:
       matchLabels:
         provider: aws
         tier: production
     engine: postgres
     version: "15"
     size: large
     region: us-west-2
     deletionPolicy: Orphan
     writeConnectionSecretToRef:
       name: orders-db-conn
       namespace: orders-team
   ```

4. **Storage & Buckets**
   - Create XStorage XRD if not exists (for S3, Blob, GCS buckets)
   - Or use provider-specific Bucket resources if XRD is overkill
   - Apply bucket claims with versioning, encryption, lifecycle policies

5. **Validate Data Integrity**
   - Ensure database connection secrets are created in correct namespaces
   - Test application connectivity to new databases
   - Verify backups are configured (automated snapshots, point-in-time recovery)
   - Data migration: Point applications to new DB endpoints; test read/write

6. **Terraform Decommission (Data Layer)**
   - Remove RDS, Cloud SQL, Redis resources from Terraform state
   - Remove storage resources from Terraform
   - Keep Terraform for remaining resources

---

### Phase 5: Advanced Services Migration (Week 7)

**Goal**: Migrate load balancers, WAF, DNS, monitoring, IAM

#### Tasks

1. **Load Balancers (XLB XRD)**
   - Create XRD for LBs: Application Load Balancer (AWS), Application Gateway (Azure), Cloud Load Balancer (GCP)
   - Compositions: `lb-aws.yaml`, `lb-azure.yaml`, `lb-gcp.yaml`
   - Claims for each service needing ingress:
     ```yaml
     apiVersion: platform.example.com/v1alpha1
     kind: LoadBalancer
     metadata:
       name: api-lb
       namespace: ai-infrastructure
     spec:
       compositionSelector:
         matchLabels:
           provider: aws
       ports:
         - port: 443
           targetPort: 5001
           protocol: HTTPS
         - port: 80
           targetPort: 5001
           protocol: HTTP
       healthCheckPath: /api/health
       sslCertificate: arn:aws:acm:...
     ```

2. **WAF & Security**
   - XWAF XRD for AWS WAF, Azure WAF, Cloud Armor (GCP)
   - Compositions to deploy rule groups, IP block lists, rate limiting
   - Apply to LBs or at edge (CloudFront/CDN)

3. **DNS (XDNS XRD)**
   - XDNS XRD for Route53, Azure DNS, Cloud DNS
   - Compositions for zone management, record sets
   - Migrate DNS records from Terraform `aws_route53_record` etc.

4. **IAM & Service Accounts**
   - Crossplane does NOT manage IAM users/policies directly in same way
   - Use provider-kubernetes for IAM if needed, or separate Terraform module
   - **Decision**: Keep IAM in Terraform OR use Crossplane IAM compositions (if Compositions exist)
   - Usually: Crossplane manages service roles for cloud resources; Terraform manages human IAM

5. **Monitoring & Alerting**
   - XMonitoring XRD for CloudWatch, Azure Monitor, Cloud Monitoring
   - Compositions for dashboards, alarms, metrics
   - Or keep monitoring in Terraform if it's just dashboard resources

6. **Apply All Remaining Claims**
   - System-level resources: DNS, WAF, LB
   - Monitoring resources
   - IAM roles for service accounts (IRSA, Workload Identity)

---

### Phase 6: Cutover & Decommission (Week 8)

#### Tasks

1. **Final Validation**
   - Run comprehensive infrastructure tests:
     - All XResources in `Ready=True` condition
     - No pending reconciliation loops (waiting on dependencies)
     - Connectivity tests: ping DB, curl LB endpoints, access applications
   - Cost reconciliation: Compare bill from Crossplane-provisioned vs Terraform-provisioned
   - Security audit: Ensure least privilege, no unnecessary open ports

2. **Multi-Cloud Orchestrator Full Cutover**
   - Switch orchestrator to use Crossplane as primary provisioning path
   - Add feature flag to fall back to Terraform if Crossplane fails
   - Update orchestration skills to detect Crossplane resources:
     - Read XCluster status → kubeconfig
     - Read XDatabase status → connection secrets
     - Detect cross-plane dependencies

3. **Terraform State Finalize**
   - Import any remaining Crossplane-managed resources into Terraform state for tracking (optional)
   - Or: archive Terraform state files and mark Terraform as deprecated
   - Remove Terraform code from repository or move to `archive/terraform/` with README explaining deprecation

4. **Documentation & Runbooks**
   - Update `README.md` with new Crossplane-based provisioning workflow
   - Create runbooks:
     - How to provision new infrastructure (using claims)
     - How to debug Crossplane reconciliation failures
     - How to modify resources (edit claims, not managed resources directly)
     - Rollback procedures (delete claim, resource orphaned)
   - Training session for platform team on Crossplane operations

5. **Monitoring & Alerting Updates**
   - Update Grafana dashboards to show Crossplane resource status
   - Alerts on XResource conditions: `Ready=False`, `Syncing=False`, reconciliation errors
   - Cost tracking: show resources created by Crossplane vs other methods

6. **Decommission Terraform**
   - Remove Terraform CLI from CI/CD pipelines
   - Archive Terraform state to S3/Glacier with retention policy
   - Update `SKILL.md` files that reference Terraform to reference Crossplane
   - Remove `multi_cloud_orchestrator.py` Terraform handler code (keep Crossplane handler)
   - Update BEV (application) to use Crossplane connection secrets

7. **Post-Migration Hypercare (2 Weeks)**
   - On-call support for Crossplane issues
   - Daily reconciliation health checks
   - Cost anomaly monitoring
   - Prepare rollback plan (re-enable Terraform if needed)

---

## 3. Backwards Compatibility Strategy

### Dual-Write Period (Phases 2-5)

During migration, both Terraform and Crossplane will coexist:

1. **Terraform → Crossplane Import** (not Terraform import!)
   - **Do NOT** run `terraform import` on existing resources (would add Terraform back to state)
   - Instead, **create Crossplane claims that match existing Terraform resources**
   - Crossplane will detect existing resources and adopt them (if `Orphan` deletion policy)
   - Verify with `kubectl describe xdatabase mydb` → `status.atProvider` shows existing resource

2. **Terraform State Pruning**
   - After Crossplane claim applied and resource Ready, remove from Terraform state:
     ```bash
     terraform state rm <resource_address>
     ```
   - Do NOT remove from Terraform code yet; keep code for audit trail
   - After all resources of a type migrated (e.g., all VPCs), remove that module from `main.tf`

3. **Crossplane `Orphan` Policy**
   - All stateful resources use `deletionPolicy: Orphan` by default
   - Prevents accidental deletion when Crossplane claim deleted
   - Manual deletion requires explicit `deletionPolicy: Delete` in claim

4. **Provider Conflicts**
   - If Terraform and Crossplane both manage same resource → conflicts, drift
   - Solution: **One source of truth per resource**
   - Cutover sequence: Terraform → Crossplane (remove from Terraform state first, then apply Crossplane claim)

### Hub-Spoke Crossplane Architecture

**Existing**: Already using separate Crossplane instances per cloud (hub-spoke)

- **Hub cluster**: Central management plane running Crossplane
- **Spoke clusters**: Workload clusters (EKS, AKS, GKE) managed by hub Crossplane
- **ProviderConfig**: Each cloud has dedicated ProviderConfig with credentials

**Migration Impact**:

- All Crossplane resources (XRDs, Compositions) deployed to hub cluster
- Claims reference ProviderConfig by name (e.g., `providerConfigRef: name: aws-provider`)
- Hub Crossplane manages resources in all cloud providers
- Spoke clusters only run workloads, not Crossplane provider installations

**Backwards Compatibility**:

- Hub Crossplane manages new infrastructure alongside any Terraform-managed resources
- No changes needed to spoke clusters during migration
- Spoke clusters' infrastructure (EKS, etc.) migrates gradually

---

## 4. Multi-Cloud Orchestrator Updates

### Files to Update

1. `core/ai/skills/*/scripts/multi_cloud_orchestrator.py`
   - Current: Direct cloud SDK calls (boto3, azure-mgmt, google-cloud)
   - Update: Kubernetes API client to read Crossplane XResources
   - Or: Hybrid mode → try Crossplane first, fall back to direct SDK

2. `overlay/ai/skills/complete-hub-spoke-temporal/workflows/multi-cloud-scatter-gather.go`
   - Current: Direct cloud provider activities
   - Update: Activities call Crossplane via K8s API or use Crossplane provider APIs

3. `core/multi-cloud-abstraction.js`
   - Current: Direct provider SDKs wrapped in abstraction layer
   - Update: Add Crossplane as abstraction layer → K8s API → provider resources
   - Keep existing for backwards compatibility; add Crossplane provider

### Implementation Pattern

```python
# Updated multi_cloud_orchestrator.py
class CrossplaneProvider:
    def __init__(self, k8s_client):
        self.k8s_client = k8s_client

    def list_vms(self):
        # Query Crossplane XCluster resources
        clusters = self.k8s_client.list_cluster_claims()
        return [cluster.status for cluster in clusters]

    def get_costs(self):
        # Query Crossplane managed resources with cost annotations
        # Or fall back to cloud billing API
        pass

class MultiCloudOrchestrator:
    def __init__(self, use_crossplane=True):
        if use_crossplane:
            self.provider = CrossplaneProvider()
        else:
            self.provider = LegacyProvider()  # existing AWS/GCP/Azure SDKs
```

---

## 5. Risk Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Crossplane provider bugs | Medium | High | Test in dev/staging before prod; use provider version pins |
| Terraform state loss | Low | Critical | Backup state files to S3 + Glacier; document restore procedure |
| Resource drift / conflicts | Medium | High | Enforce single source of truth; monitor drift alerts |
| Provider quota limits | Medium | Medium | Request quota increases before migration; stagger migrations |
| Crossplane learning curve | High | Medium | Training, runbooks, pilot migration first |

### Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Application downtime | Medium | High | Blue-green cutover; canary migrations per environment |
| Cost overruns | Low | Medium | Monitor billing daily during migration; set budget alerts |
| Security posture degradation | Low | High | Security review of Crossplane Compositions; IAM least privilege |
| Data loss | Low | Critical | DeletionPolicy: Orphan; backups verified before cutover |
| Compliance violations | Low | High | Compliance scanner integration (OPA/Gatekeeper) |

---

## 6. Testing Strategy

### Unit Tests

- Test each Composition with `kubeconform` schema validation
- Unit tests for multi-cloud orchestrator Crossplane integration
- Mock K8s API responses for orchestrator unit tests

### Integration Tests

- Deploy test claims to dev hub cluster
- Verify resources created in each cloud
- Test drift correction: manually modify cloud resource → Crossplane reverts
- Test deletion: delete claim → resource orphaned (not deleted)

### End-to-End Tests

- Full stack test: deploy network → cluster → database → application
- Validate connectivity between components across clouds
- Load testing after migration to ensure no performance regression

### Cutover Validation

- Terraform plan shows zero changes after migration (all resources removed from state)
- Crossplane shows all XResources `Ready=True`
- Application health checks pass with new infrastructure
- Cost reports match pre-migration (within 10% variance)

---

## 7. Success Criteria

### Quantitative

- [ ] 100% of infrastructure resources provisioned via Crossplane
- [ ] Terraform state files archived with zero pending changes
- [ ] 99%+ reconciliation success rate (XResources Ready)
- [ ] Zero production incidents caused by migration
- [ ] Cost variance < 10% compared to pre-migration

### Qualitative

- [ ] Platform team can provision infrastructure via `kubectl apply -f claim.yaml`
- [ ] GitOps pipeline automatically provisions infrastructure on PR merge
- [ ] Documentation updated; runbooks created
- [ ] No Terraform CLI usage in CI/CD for 2 weeks post-cutover
- [ ] Crossplane monitoring dashboards active and alerting

---

## 8. Timeline & Dependencies

```
Week 1: Assessment → Complete inventory, gap analysis, prerequisites
Week 2-3: Foundation → Crossplane providers healthy, GitOps validated
Week 4: Networks → All VPCs/VNets managed by Crossplane
Week 5: Clusters → EKS/AKS/GKE managed by Crossplane
Week 6: Data → Databases, caches, storage managed by Crossplane
Week 7: Advanced → LBs, WAF, DNS, monitoring migrated
Week 8: Cutover → Full Crossplane, Terraform decommissioned
```

**Dependencies**:

- Crossplane provider versions must support all required managed resources
- GitOps (Flux/ArgoCD) must be stable before Phase 2
- Cloud provider quotas/limits must accommodate resource creation during migration
- Platform team must complete Crossplane training before Phase 2

---

## 9. References

- [Crossplane Documentation](https://docs.crossplane.io/)
- [Crossplane Provider AWS](https://marketplace.upbound.io/providers/upbound/provider-aws)
- [Crossplane Provider Azure](https://marketplace.upbound.io/providers/upbound/provider-azure)
- [Crossplane Provider GCP](https://marketplace.upbound.io/providers/upbound/provider-gcp)
- [GitOps Patterns](https://www.weave.works/blog/what-is-gitops)
- Existing Crossplane files in repo: `core/operators/control-plane/crossplane/`
- Terraform files: `core/infrastructure/terraform/{aws,gcp,azure}/main.tf`

---

## Appendix: Resource Mapping

### Terraform → Crossplane Mapping

| Terraform Resource | Crossplane XRD | Provider Managed Resource |
|-------------------|----------------|---------------------------|
| `aws_vpc` | XNetwork | `networks.aws.crossplane.io/v1beta1` |
| `google_compute_network` | XNetwork | `networks.gcp.crossplane.io/v1beta1` |
| `azurerm_virtual_network` | XNetwork | `virtualnetworks.azure.crossplane.io/v1beta1` |
| `aws_subnet` | XNetwork (subnet field) | `subnets.aws.crossplane.io/v1beta1` |
| `google_container_cluster` | XCluster | `clusters.container.gcp.crossplane.io/v1beta1` |
| `aws_eks_cluster` | XCluster | `clusters.eks.aws.crossplane.io/v1beta1` |
| `azurerm_kubernetes_cluster` | XCluster | `managedclusters.azure.crossplane.io/v1beta1` |
| `aws_db_instance` | XDatabase | `databases.rds.aws.crossplane.io/v1alpha1` |
| `google_sql_database_instance` | XDatabase | `databases.sqladmin.gcp.crossplane.io/v1beta1` |
| `azurerm_postgresql_flexible_server` | XDatabase | `flexibleservers.database.azure.crossplane.io/v1beta1` |
| `aws_elasticache_cluster` | XRedis (or XDatabase) | `elasticacheclusters.cache.aws.crossplane.io/v1beta1` |
| `google_redis_instance` | XRedis | `instances.redis.googleapis.com/v1beta1` (GCP) |
| `azurerm_redis_cache` | XRedis | `redis.azure.crossplane.io/v1beta1` |
| `aws_s3_bucket` | XStorageBucket | `bucketpolicies.s3.aws.crossplane.io/v1beta1` + `buckets.s3.aws.crossplane.io/v1beta1` |
| `google_storage_bucket` | XStorageBucket | `buckets.storage.googleapis.com/v1beta1` |
| `azurerm_storage_account` | XStorageAccount | `storageaccounts.storage.azure.crossplane.io/v1beta1` |
| `aws_lb` / `aws_alb` | XLB | `loadbalancers.elbv2.aws.crossplane.io/v1beta1` |
| `google_compute_global_forwarding_rule` | XLB | `forwardingrules.compute.gcp.crossplane.io/v1beta1` |
| `azurerm_application_gateway` | XLB | `applicationgateways.network.azure.crossplane.io/v1beta1` |
| `aws_wafv2_web_acl` | XWAF | `webacls.wafv2.aws.crossplane.io/v1beta1` |
| `google_compute_security_policy` | XWAF | `securitypolicies.compute.gcp.crossplane.io/v1beta1` |
| `azurerm_web_application_firewall_policy` | XWAF | `applicationgatewaywafpolicies.network.azure.crossplane.io/v1beta1` |
| `aws_route53_record` | XDNS | `recordsets.route53.aws.crossplane.io/v1beta1` |
| `google_dns_record_set` | XDNS | `recordsets.dns.googleapis.com/v1beta1` |
| `azurerm_dns_a_record` | XDNS | `arecords.dns.azure.crossplane.io/v1beta1` |

*Note: Not all Crossplane managed resource types may be available; gaps require custom Compositions or fallback to Terraform for specific resources.*

---

**Document Version**: 1.0
**Last Updated**: 2026-03-20
**Owner**: Platform Engineering Team
**Status**: Draft → Ready for Review → Approved → In Progress

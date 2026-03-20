# Crossplane Migration Plan: Terraform → Kubernetes-Native IaC

**Migration from Terraform to Single Crossplane Control Plane**

---

## Executive Summary

This document outlines the comprehensive plan to migrate existing multi-cloud infrastructure from Terraform to a **single Crossplane control plane** with Kubernetes-native infrastructure management while maintaining backwards compatibility.

### Current State

- **Terraform IaC**: Separate `main.tf` files for AWS, GCP, Azure under `/core/infrastructure/terraform/`
- **Multi-Cloud Orchestration**: Python/Go/JS orchestration layer (`multi_cloud_orchestrator.py`, `multi-cloud-scatter-gather.go`, `multi-cloud-abstraction.js`)
- **Existing Crossplane**: Already deployed with XRDs, Compositions, and Provider configs for AWS, Azure, GCP, Kubernetes
- **Problem**: Hub-spoke architecture (separate Crossplane instances per cloud) creates operational overhead

### Target State

- **Single Crossplane Instance**: One control plane managing all clouds with proper isolation via RBAC
- **Infrastructure as Kubernetes CRDs**: All infrastructure defined as XRDs + Claims
- **GitOps Pipeline**: Flux/ArgoCD reconciliation from Git to cloud providers
- **Multi-Cloud Unified**: Cloud-agnostic claims with provider-specific Compositions
- **Backwards Compatible**: Existing Terraform configurations preserved during transition

---

## 1. Migration Strategy

### Phased Approach (6-8 weeks)

| Phase | Duration | Objectives | Deliverables |
|-------|----------|------------|--------------|
| **Phase 0: Assessment** | Week 1 | Inventory, analysis, prerequisites | Inventory matrix, Gap analysis, Prereq checklist |
| **Phase 1: Foundation** | Week 2-3 | Single Crossplane, providers, RBAC | Unified control plane, ProviderConfigs, GitOps sync |
| **Phase 2: Network First** | Week 4 | Migrate VPC/VNet networking to Crossplane | XNetwork XRD + Compositions, Network claims |
| **Phase 3: Compute Clusters** | Week 5 | Migrate EKS/AKS/GKE to Crossplane | XCluster XRD + Compositions, Cluster claims |
| **Phase 4: Data & Services** | Week 6 | Migrate databases, caches, storage | XDatabase, XQueue, XStorage XRD + Compositions |
| **Phase 5: Advanced Services** | Week 7 | Migrate load balancers, WAF, DNS | XLB, XWAF, XDNS XRD + Compositions |
| **Phase 6: Cutover & Decommission** | Week 8 | Testing, validation, Terraform decommission | Test reports, Cutover playbook, Terraform archival |

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
   - [ ] Set up Flux/ArgoCD to sync `core/operators/control-plane/crossplane/` to hub cluster
   - [ ] Create RBAC roles for platform team to manage Crossplane resources
   - [ ] Backup all Terraform state files (S3 backends, etc.)
   - [ ] **Consolidate to single Crossplane instance** - decommission spoke Crossplane instances if they exist

#### Outputs

- `docs/migration/inventory-MATRIX.md`
- `docs/migration/gap-analysis.md`
- `docs/migration/prerequisites-VERIFIED.md`
- Terraform state backups archived

---

### Phase 1: Foundation & Provider Validation (Week 2-3)

#### Tasks

1. **Deploy Single Crossplane Instance**
   - Remove any existing hub-spoke Crossplane deployments
   - Install Crossplane on central hub cluster (management cluster)
   - Configure Crossplane with high-availability, backup, monitoring
   - Set up RBAC: platform team can manage XResources, developers can create Claims

2. **Provider Health Checks**
   ```bash
   # Verify all providers are healthy
   kubectl get providers -n crossplane-system
   # Expected: provider-aws, provider-azure, provider-gcp, provider-kubernetes all HEALTHY

   # Check ProviderConfigs
   kubectl get providerconfigs -n crossplane-system
   # Expected: aws-provider, azure-provider, gcp-provider, kubernetes-provider
   ```

3. **Test Basic Managed Resources**
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

4. **GitOps Pipeline Validation**
   - Ensure Flux/ArgoCD picks up changes from `core/operators/control-plane/crossplane/`
   - Test Kustomization for XRDs, Compositions, Providers
   - Verify automated sync and reconciliation loops

5. **Multi-Cloud Orchestrator Integration**
   - Update `multi_cloud_orchestrator.py` to detect Crossplane resources
   - Add capability to read Crossplane Composite resources (XDatabase, XCluster status)
   - Implement Crossplane as alternative provisioning path
   - Log infrastructure changes from Crossplane events

#### Outputs

- Providers healthy in all clouds (AWS, Azure, GCP, on-prem Kubernetes)
- Test managed resources created and deleted successfully
- GitOps pipeline validated with successful syncs
- `multi_cloud_orchestrator.py` Crossplane integration branch ready

---

### Phase 2: Network Migration (Week 4)

**Goal**: Migrate VPC/VNet networking from Terraform to Crossplane

#### Tasks

1. **Extend XNetwork XRD**
   - Review `core/operators/control-plane/crossplane/xrds/xnetwork.yaml`
   - **Gap**: Current XNetwork only covers basic VPC + 3 subnets
   - **Need to add**: NAT Gateway, Internet Gateway, Route Tables, Security Groups, VPC Peering, Cloud Router (GCP), NAT (GCP), DNS zones
   - Extend schema to match Terraform `main.tf` network resources

2. **Update Compositions for All Providers**
   - **AWS**: `compositions/network-aws.yaml` → add NAT, IGW, route tables, security groups, VPC endpoints
   - **Azure**: `compositions/network-azure.yaml` → add NAT gateway, VPN gateway, NSG, Private DNS zones
   - **GCP**: `compositions/network-gcp.yaml` → add Cloud Router, Cloud NAT, firewall rules, Cloud DNS

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
     cidr: 10.0.0.0/16
     region: us-west-2
     enableNat: true
     enableInternetGateway: true
     subnetCidrs: ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
     deletionPolicy: Orphan
   ```

4. **Apply Network Claims via GitOps**
   ```bash
   kubectl apply -f core/resources/tenants/1-network/network-prod.yaml
   # Flux will sync and Crossplane will provision VPCs in each cloud
   ```

5. **Validate Network Provisioning**
   - Check network resources created in AWS console (VPC, subnets, NAT, IGW, route tables)
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

1. **Extend XCluster XRD**
   - Check `xrds/xcluster.yaml` covers required cluster parameters
   - **Gap**: Need to add Node Pools with detailed configuration (instance types, autoscaling, labels, taints, disk size, GPU support)
   - Add fields for: addons (CNI, CSI, CoreDNS), logging, monitoring, private access, public access, IAM roles, OIDC identity provider
   - Match Terraform `module.eks` or `google_container_cluster` or `azurerm_kubernetes_cluster` configurations

2. **Update Compositions for All Providers**
   - **AWS**: `cluster-eks.yaml` → extend node groups, Fargate profiles, EKS add-ons, OIDC, cluster endpoint access
   - **Azure**: `cluster-aks.yaml` → extend node pools, auto-scaling, Azure AD integration, AKS add-ons
   - **GCP**: `cluster-gke.yaml` → extend node pools, auto-scaling, GKE add-ons, binary authorization, shielded nodes
   - **CAPI**: `cluster-capi-*.yaml` → ensure they support workload clusters if needed

3. **Create Cluster Claims**
   - Create `core/resources/tenants/2-clusters/` directory if not exists
   - Define claims for each cluster matching Terraform configurations:

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
         diskSizeGb: 100
         labels:
           workload: general
         taints: []
       - name: spot
         instanceType: t3.large
         capacityType: SPOT
         minSize: 0
         maxSize: 10
         desiredSize: 2
     endpointAccess:
       private: true
       public: false
     addons:
       - name: vpc-cni
       - name: coredns
       - name: kube-proxy
     deletionPolicy: Orphan
   ```

4. **Apply Cluster Claims**
   ```bash
   kubectl apply -f core/resources/tenants/2-clusters/
   # Wait for clusters to sync: Ready=True
   kubectl get clusters -n platform-infra -w
   ```

5. **Update Kubeconfig for New Clusters**
   - Crossplane can write connection secrets with kubeconfig
   - Update `~/.kube/config` or CI/CD cluster contexts to use Crossplane-managed clusters
   - Verify `kubectl get nodes` works for new clusters

6. **Decommission Terraform Clusters**
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

1. **Extend XDatabase XRD**
   - Review `xrds/xdatabase.yaml`
   - **Gap**: Need to add fields for backups (retention days, window), HA (multi-AZ), maintenance windows, encryption (KMS), parameter groups, option groups, replication, read replicas, connectivity (VPC, subnet, security groups)
   - Match all Terraform database configurations

2. **Create XRedis XRD** (or extend XDatabase)
   - Define separate XRD for Redis/Memcached with appropriate fields
   - Or use `engine: redis` in XDatabase if simpler

3. **Update Database Compositions**
   - **AWS**: `database-aws.yaml` → add DB parameter groups, option groups, subnet groups, IAM authentication, performance insights, enhanced monitoring, CloudWatch logs, backups, snapshots
   - **GCP**: `database-gcp.yaml` → add flags, maintenance window, backup configuration, IP configuration, private network, database flags
   - **Azure**: `database-azure.yaml` → add high availability, backup retention, maintenance window, delegated subnet, private DNS zone

4. **Create XStorageBucket XRD** (if not exists)
   - For S3, GCS, Blob Storage with versioning, encryption, lifecycle policies, access controls, public access block, CORS, logging

5. **Create Database & Storage Claims**
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
     storage:
       type: gp3
       sizeGb: 100
       iops: 3000
     backup:
       retentionDays: 30
       window: "03:00-04:00"
     highAvailability:
       enabled: true
       multiAz: true
     maintenance:
       window: "Sun:03:00-Sun:04:00"
     deletionPolicy: Orphan
     writeConnectionSecretToRef:
       name: orders-db-conn
       namespace: orders-team
   ```

6. **Storage Bucket Claims**
   ```yaml
   apiVersion: platform.example.com/v1alpha1
   kind: StorageBucket
   metadata:
     name: app-backups
     namespace: platform-infra
   spec:
     compositionSelector:
       matchLabels:
         provider: aws
     region: us-west-2
     versioning:
       enabled: true
     encryption:
       type: aws:kms
       kmsKeyId: alias/my-key
     lifecycle:
       rules:
         - id: delete-old
           status: true
           expiration:
             days: 90
     publicAccessBlock:
       blockPublicAcls: true
       blockPublicPolicy: true
       ignorePublicAcls: true
       restrictPublicBuckets: true
   ```

7. **Validate Data Integrity**
   - Ensure database connection secrets are created in correct namespaces
   - Test application connectivity to new databases
   - Verify backups are configured (automated snapshots, point-in-time recovery)
   - Data migration: Point applications to new DB endpoints; test read/write

8. **Terraform Decommission (Data Layer)**
   - Remove RDS, Cloud SQL, Redis resources from Terraform state
   - Remove storage resources from Terraform
   - Keep Terraform for remaining resources

---

### Phase 5: Advanced Services Migration (Week 7)

**Goal**: Migrate load balancers, WAF, DNS, monitoring, IAM

#### Tasks

1. **Extend XLoadBalancer XRD**
   - Create XRD for LBs: Application Load Balancer (AWS), Application Gateway (Azure), Cloud Load Balancing (GCP)
   - Fields: HTTP/HTTPS listeners, target groups/backends, health checks, SSL certificates, WAF integration, routing rules, session affinity

2. **Create XWAF XRD**
   - AWS WAF, Azure WAF, Cloud Armor (GCP)
   - Rules: managed rule groups, rate limiting, IP block lists, custom rules

3. **Create XDNS XRD**
   - Route53 (AWS), Azure DNS, Cloud DNS (GCP)
   - Zones, record sets (A, AAAA, CNAME, MX, TXT), TTL, health checks

4. **Update Compositions for Advanced Services**
   - LB Compositions with health checks, SSL, WAF association
   - WAF Compositions with rule groups and associations
   - DNS Compositions with zone and record management

5. **Claims for Advanced Services**
   ```yaml
   # Load Balancer claim
   apiVersion: platform.example.com/v1alpha1
   kind: LoadBalancer
   metadata:
     name: api-lb
     namespace: ai-infrastructure
   spec:
     compositionSelector:
       matchLabels:
         provider: aws
     listeners:
       - port: 443
         protocol: HTTPS
         targetPort: 5001
         certificateArn: arn:aws:acm:...
       - port: 80
         protocol: HTTP
         targetPort: 5001
     healthCheck:
       path: /api/health
       port: 5001
       protocol: HTTP
     wafEnabled: true
   ```

6. **Apply All Remaining Claims**
   - System-level resources: DNS, WAF, LB
   - Monitoring resources (CloudWatch, Azure Monitor, Cloud Monitoring)
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
   - Update `SKILL.md` files that reference Terraform to reference Crossplane

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

6. **Terraform Decommission**
   - Remove Terraform CLI from CI/CD pipelines
   - Archive Terraform state to S3/Glacier with retention policy
   - Delete Terraform workspace references
   - Remove `multi_cloud_orchestrator.py` Terraform handler code (keep Crossplane handler)
   - Update application configs to use Crossplane connection secrets

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
from kubernetes import client, config

class CrossplaneProvider:
    def __init__(self, k8s_client=None):
        if k8s_client:
            self.k8s_client = k8s_client
        else:
            config.load_kube_config()
            self.k8s_client = client.CustomObjectsApi()

    def list_clusters(self):
        # Query Crossplane XCluster claims
        clusters = self.k8s_client.list_namespaced_custom_object(
            group="platform.example.com",
            version="v1alpha1",
            namespace="platform-infra",
            plural="xclusters"
        )
        return [{
            'name': c['metadata']['name'],
            'provider': c['spec']['provider'],
            'endpoint': c['status'].get('endpoint', ''),
            'status': c['status'].get('phase', 'Unknown')
        } for c in clusters.get('items', [])]

    def get_database_connection(self, name, namespace):
        # Get connection secret created by Crossplane
        secret = self.k8s_client.read_namespaced_secret(
            name=f"{name}-conn",
            namespace=namespace
        )
        return {
            'host': secret.data['host'],
            'port': secret.data['port'],
            'username': secret.data['username'],
            'password': secret.data['password']
        }

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
Week 2-3: Foundation → Single Crossplane deployed, providers healthy, GitOps validated
Week 4: Networks → All VPCs/VNets managed by Crossplane (XNetwork extended)
Week 5: Clusters → EKS/AKS/GKE managed by Crossplane (XCluster extended)
Week 6: Data → Databases, caches, storage managed by Crossplane (XDatabase/XStorage extended)
Week 7: Advanced → LBs, WAF, DNS, monitoring migrated (XLB/XWAF/XDNS created)
Week 8: Cutover → Full Crossplane, Terraform decommissioned
```

**Dependencies**:

- Crossplane provider versions must support all required managed resources
- GitOps (Flux/ArgoCD) must be stable before Phase 2
- Cloud provider quotas/limits must accommodate resource creation during migration
- Platform team must complete Crossplane training before Phase 2
- All XRDs must be extended to match Terraform capabilities before each migration phase

---

## 9. Resource Mapping Reference

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
| `aws_elasticache_cluster` | XRedis | `elasticacheclusters.cache.aws.crossplane.io/v1beta1` |
| `google_redis_instance` | XRedis | `instances.redis.googleapis.com/v1beta1` |
| `azurerm_redis_cache` | XRedis | `redis.azure.crossplane.io/v1beta1` |
| `aws_s3_bucket` | XStorageBucket | `buckets.s3.aws.crossplane.io/v1beta1` |
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

*Note: Some Crossplane managed resource types may not be available; gaps require custom Compositions or fallback to Terraform.*

---

## 10. XRD Extension Checklist

### XNetwork (Priority: HIGH)
- [ ] Add NAT Gateway support (AWS, Azure, GCP)
- [ ] Add Internet Gateway / NAT routing
- [ ] Add Route Tables with routes and associations
- [ ] Add Security Groups / NSG / Firewall rules
- [ ] Add VPC Peering / VNet Peering
- [ ] Add Private DNS zones (Route53 Resolver, Azure Private DNS)
- [ ] Add VPC Flow Logs / NSG Flow Logs
- [ ] Add Cloud Router (GCP) for Cloud NAT
- [ ] Add Transit Gateway (AWS) / VPN Gateway / ExpressRoute (Azure) / Cloud VPN (GCP) if needed

### XCluster (Priority: HIGH)
- [ ] Add detailed Node Pool configuration (disk size, GPU, labels, taints, tags)
- [ ] Add Autoscaling configuration (min/max/desired)
- [ ] Add EKS add-ons (vpc-cni, coredns, kube-proxy) with versions
- [ ] Add cluster endpoint access control (private/public)
- [ ] Add IAM/OIDC configuration (IRSA, OIDC provider)
- [ ] Add logging configuration (CloudWatch Logs, Azure Monitor, Cloud Logging)
- [ ] Add monitoring configuration (prometheus, grafana)
- [ ] Add encryption at rest (KMS)
- [ ] Add node IAM roles and instance profiles

### XDatabase (Priority: HIGH)
- [ ] Add backup configuration (retention days, window, point-in-time recovery)
- [ ] Add high availability (multi-AZ, failover)
- [ ] Add maintenance window configuration
- [ ] Add encryption (KMS key, CMK)
- [ ] Add parameter groups and option groups
- [ ] Add performance insights / query insights
- [ ] Add enhanced monitoring
- [ ] Add read replicas configuration
- [ ] Add connectivity: VPC, subnets, security groups, IAM authentication
- [ ] Add database flags and options

### XRedis (Priority: MEDIUM)
- [ ] Create separate XRD or use XDatabase with engine: redis
- [ ] Add HA configuration (cluster mode, replica count)
- [ ] Add VNet integration / subnet configuration
- [ ] Add security: SSL/TLS, access control lists
- [ ] Add persistence configuration (RDB/AOF)
- [ ] Add monitoring and alerts

### XStorageBucket (Priority: MEDIUM)
- [ ] Create XRD for object storage
- [ ] Add versioning configuration
- [ ] Add encryption (SSE-S3, SSE-KMS, CMEK)
- [ ] Add lifecycle policies (transition, expiration)
- [ ] Add public access block settings
- [ ] Add CORS configuration
- [ ] Add access control (bucket policies, IAM)
- [ ] Add logging and metrics

### XLB (Priority: MEDIUM)
- [ ] Create XRD for load balancers
- [ ] Add listeners (ports, protocols, certificates)
- [ ] Add target groups / backends with health checks
- [ ] Add WAF integration
- [ ] Add SSL/TLS termination
- [ ] Add session affinity / stickiness
- [ ] Add routing rules (path-based, host-based)
- [ ] Add cross-zone load balancing

### XWAF (Priority: LOW - after LB)
- [ ] Create XRD for WAF
- [ ] Add managed rule groups (AWS Managed Rules, OWASP)
- [ ] Add custom rules (rate limiting, IP blocking, geo-match)
- [ ] Add rule priority and action (allow/deny/count)
- [ ] Add association with LBs or CloudFront

### XDNS (Priority: LOW - after LB)
- [ ] Create XRD for DNS
- [ ] Add hosted zones
- [ ] Add record sets (A, AAAA, CNAME, MX, TXT, SRV)
- [ ] Add health checks and failover routing
- [ ] Add TTL configuration
- [ ] Add alias records (AWS alias, Azure alias)

---

## 11. GitOps Integration

### Repository Structure

```
core/operators/control-plane/crossplane/
├── providers/
│   ├── provider-aws.yaml
│   ├── provider-azure.yaml
│   ├── provider-gcp.yaml
│   ├── provider-kubernetes.yaml
│   ├── providerconfig-aws.yaml
│   ├── providerconfig-azure.yaml
│   ├── providerconfig-gcp.yaml
│   └── providerconfig-kubernetes.yaml
├── xrds/
│   ├── xnetwork.yaml
│   ├── xcluster.yaml
│   ├── xdatabase.yaml
│   ├── xredis.yaml
│   ├── xstoragebucket.yaml
│   ├── xlb.yaml
│   ├── xwaf.yaml
│   └── xdns.yaml
├── compositions/
│   ├── network-aws.yaml
│   ├── network-azure.yaml
│   ├── network-gcp.yaml
│   ├── cluster-eks.yaml
│   ├── cluster-aks.yaml
│   ├── cluster-gke.yaml
│   ├── cluster-capi-aws.yaml
│   ├── cluster-capi-azure.yaml
│   ├── cluster-capi-gcp.yaml
│   ├── database-aws.yaml
│   ├── database-azure.yaml
│   ├── database-gcp.yaml
│   ├── redis-aws.yaml
│   ├── redis-azure.yaml
│   ├── redis-gcp.yaml
│   ├── storagebucket-aws.yaml
│   ├── storagebucket-azure.yaml
│   ├── storagebucket-gcp.yaml
│   ├── lb-aws.yaml
│   ├── lb-azure.yaml
│   ├── lb-gcp.yaml
│   ├── waf-aws.yaml
│   ├── waf-azure.yaml
│   ├── waf-gcp.yaml
│   ├── dns-aws.yaml
│   ├── dns-azure.yaml
│   └── dns-gcp.yaml
└── kustomization.yaml
```

### Flux/ArgoCD Configuration

```yaml
# flux-system/kustomization.yaml (or argo-cd application)
resources:
  - ../../core/operators/control-plane/crossplane/xrds/
  - ../../core/operators/control-plane/crossplane/compositions/
  - ../../core/operators/control-plane/crossplane/providers/
```

---

## 12. Monitoring & Alerting

### Crossplane Metrics to Monitor

- `crossplane_reconcile_duration_seconds` (histogram) - reconciliation latency
- `crossplane_reconcile_total` (counter) - total reconciliations (success/failure)
- `crossplane_api_request_total` (counter) - API calls to cloud providers
- `crossplane_api_request_duration_seconds` (histogram) - API call latency
- `crossplane_resources_total` (gauge) - total managed resources by type/state

### XResource Status Conditions

Monitor Custom Resources for conditions:

```yaml
status:
  conditions:
  - type: Ready
    status: "True"  # ✅ Good
    reason: ReconcileSuccess
  - type: Synced
    status: "True"  # ✅ Good
    reason: SyncSuccess
```

Alert on:
- `Ready=False` for > 10 minutes
- `Synced=False` for > 5 minutes
- Reconcile errors rate > 1%
- API request latency > 30s
- Stuck resources in `Creating` state > 1 hour

---

## 13. Rollback Procedures

### If Crossplane Migration Fails

1. **Stop applying new Crossplane claims**
2. **Restore Terraform state** from backup (S3/Glacier)
3. **Re-apply Terraform** to drift-correct resources:
   ```bash
   terraform apply
   ```
4. **Remove Crossplane claims** for migrated resources (will orphan cloud resources)
5. **Re-enable Terraform** in CI/CD pipelines

### Partial Rollback (Single Resource Type)

If only networks fail but clusters successful:
- Keep Crossplane-managed clusters
- Roll back networks to Terraform
- Maintain two sources of truth temporarily
- Expedite network fix or keep split

---

## 14. Training & Knowledge Transfer

### Platform Team Training Topics

1. **Crossplane Fundamentals** (half-day)
   - XRDs, Compositions, Claims
   - Provider installation and configuration
   - Reconciliation loop and status conditions

2. **Composition Authoring** (full-day)
   - Writing XRD schemas
   - Developing multi-cloud Compositions
   - Patching and composition logic

3. **Operations & Debugging** (half-day)
   - `kubectl get x<resource>` and `describe`
   - Reading events and conditions
   - Common failure modes and fixes

4. **Migration Workshop** (half-day)
   - Hands-on migration of test resources
   - Drift detection and correction
   - Terraform decommissioning process

---

## 15. Open Questions & Decisions Needed

1. **XRedis design**: Separate XRD or use XDatabase with `engine: redis`?
2. **Advanced XCluster features**: CAPI cluster management vs static EKS/AKS/GKE?
3. **IAM management**: Keep IAM in Terraform or move to Crossplane with separate XRD?
4. **Cost tracking**: How to get cost metrics from Crossplane (provider tags, separate cost XRD)?
5. **Multi-region clusters**: How to represent clusters spanning regions in XCluster?
6. **Secret management**: Crossplane connection secrets vs HashiCorp Vault integration?
7. **Compliance as code**: OPA/Gatekeeper policies for Crossplane claims?

---

**Document Version**: 1.0
**Last Updated**: 2026-03-20
**Owner**: Platform Engineering Team
**Status**: Draft → Ready for Review → Approved → In Progress

---

## Appendix: Full Terraform → Crossplane Resource Mapping

See detailed mapping table in section 9 above.

---

## Appendix: Sample Claim to Terraform Comparison

### Terraform (AWS VPC)

```hcl
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support = true

  tags = {
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

resource "aws_subnet" "private" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
  availability_zone = "us-west-2a"

  tags = {
    Environment = "production"
    Type        = "private"
  }
}
```

### Crossplane (XNetwork Claim)

```yaml
apiVersion: platform.example.com/v1alpha1
kind: Network
metadata:
  name: network-prod
  namespace: platform-infra
  annotations:
    platform.example.com/allow-deletion: "false"
spec:
  compositionSelector:
    matchLabels:
      provider: aws
      tier: production
  cidr: 10.0.0.0/16
  region: us-west-2
  enableDnsHostnames: true
  enableDnsSupport: true
  subnets:
    - name: private
      cidr: 10.0.1.0/24
      availabilityZone: us-west-2a
      type: private
  deletionPolicy: Orphan
```

**Key differences**:
- Crossplane: Declarative claim, cloud-agnostic, GitOps-friendly
- Terraform: Imperative HCL, cloud-specific, stateful

---

## Appendix: XRD Extension Templates

### Template for Extending XRD

```yaml
# Edit: core/operators/control-plane/crossplane/xrds/<xrd-name>.yaml
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xsomething.platform.example.com
spec:
  group: platform.example.com
  names:
    kind: XSomething
    plural: xsomethings
  claimNames:
    kind: Something
    plural: somethings
  versions:
  - name: v1alpha1
    served: true
    referenceable: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            required: [<required_fields>]
            properties:
              <new_field>:
                type: <string|integer|boolean|object>
                description: "<description>"
                # Add enum, minimum, maximum, etc. as needed
          status:
            type: object
            properties:
              <new_status_field>:
                type: <string|integer>
```

After editing XRD:
```bash
# Validate
kubeconform core/operators/control-plane/crossplane/xrds/xsomething.yaml

# Apply
kubectl apply -f core/operators/control-plane/crossplane/xrds/xsomething.yaml

# Update Compositions to use new fields
```

---

**END OF DOCUMENT**

# Crossplane Multi-Cloud Migration Strategy

## Executive Summary

**Objective**: Migrate from Terraform-based multi-cloud infrastructure (AWS, Azure, GCP) to a single Kubernetes-native Crossplane control plane with proper RBAC isolation.

**Architecture Decision**: Single Crossplane instance with ProviderConfig-based isolation across all cloud providers. This approach provides operational simplicity while maintaining security boundaries through Kubernetes RBAC.

**Timeline**: 6-8 weeks (phased approach with parallel operation)

**Risk Level**: Medium (requires careful coordination and rollback planning)

---

## 1. Current State Analysis

### 1.1 Existing Infrastructure

**Terraform Implementation**:
- Separate Terraform modules per cloud provider:
  - `core/infrastructure/terraform/aws/` - EKS, RDS, ElastiCache, S3, CloudFront, ALB, WAF
  - `core/infrastructure/terraform/azure/` - AKS, PostgreSQL Flexible, Redis Cache, Blob Storage, Application Gateway
  - `core/infrastructure/terraform/gcp/` - GKE Autopilot, Cloud SQL, Memorystore, Cloud Storage, Load Balancer

**Current Orchestration Layer**:
- `multi_cloud_orchestrator.py` - Python-based multi-cloud orchestration with parallel/sequential strategies
- `multi-cloud-scatter-gather.go` - Temporal workflow for distributed multi-cloud operations
- `multi-cloud-abstraction.js` - Node.js abstraction layer with provider-specific implementations

### 1.2 Challenges with Current Approach

1. **Separate State Management**: Each cloud provider has independent Terraform state
2. **Cross-Cloud Dependencies**: Manual coordination required for resources spanning clouds
3. **No GitOps Integration**: Terraform state not naturally integrated with Kubernetes reconciliation
4. **Provider SDK Drift**: Custom Python handlers must be maintained separately
5. **Limited Observability**: No unified view of cloud resources through Kubernetes API

---

## 2. Target State: Single Crossplane Control Plane

### 2.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitOps Repository                        │
│  (Crossplane Compositions, Configuration, RBAC)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Single Crossplane Instance                     │
│            (Running on Kubernetes cluster)                 │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │   AWS       │  │   Azure     │  │   GCP       │      │
│  │ Provider    │  │ Provider    │  │ Provider    │      │
│  │ Config      │  │ Config      │  │ Config      │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │        RBAC Isolation (Kubernetes)                  │  │
│  │  • ServiceAccounts per team/cloud                  │  │
│  │  • RoleBindings restrict provider access           │  │
│  │  • NetworkPolicies restrict Crossplane             │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────┬────────────────────────────┬──────────────┘
               │                            │
    ┌──────────▼──────────┐   ┌───────────▼──────────┐
    │   AWS Resources     │   │   Azure Resources    │
    │  (EC2, RDS, etc.)   │   │  (VMs, SQL, etc.)    │
    └─────────────────────┘   └──────────────────────┘
```

### 2.2 Key Components

| Component | Purpose | Isolation Mechanism |
|-----------|---------|-------------------|
| **Crossplane Pod** | Core control plane | Single deployment, multi-provider |
| **ProviderConfigs** | Credential management per cloud | Kubernetes secrets + RBAC |
| **Compositions** | Reusable infrastructure patterns | Namespace-scoped, RBAC-controlled |
| **Managed Resources** | Cloud resource representations | Kubernetes CRDs |
| **ResourceClasses** | Cost/performance tiers | Cluster-scoped, read-only for most |

### 2.3 Isolation Strategy

**RBAC-Based Multi-Tenancy**:
```
Team A (AWS-only):
  ServiceAccount: team-a-sa
  Role: can create EC2, VPC, RDS
  ProviderConfig: aws-provider (read-only credentials)

Team B (Azure-only):
  ServiceAccount: team-b-sa
  Role: can create AKS, PostgreSQL, Redis
  ProviderConfig: azure-provider (read-only credentials)

Team C (Multi-cloud):
  ServiceAccount: team-c-sa
  Role: can create resources in all providers
  ProviderConfigs: aws, azure, gcp (read-only)
```

**ProviderConfig Security**:
- Stored as Kubernetes Secrets in `crossplane-system` namespace
- RBAC prevents non-admin access
- Provider pods run with minimal permissions
- NetworkPolicies restrict Crossplane egress

---

## 3. Migration Strategy: Phased Approach

### Phase 0: Preparation (Week 1-2)

**Goal**: Set up foundation and validate Crossplane installation

#### Tasks:
1. **Install Crossplane** on existing Kubernetes cluster (or dedicated cluster)
   ```bash
   kubectl create namespace crossplane-system
   helm repo add crossplane-stable https://charts.crossplane.io/stable
   helm install crossplane crossplane-stable/crossplane \
     --namespace crossplane-system \
     --create-namespace
   ```

2. **Install Provider Packages**:
   ```bash
   kubectl get providers.pkg.crossplane.io
   # Should see: provider-aws, provider-azure, provider-gcp
   ```

3. **Create ProviderConfigs** for each cloud with appropriate credentials:
   ```yaml
   # aws-provider-config.yaml
   apiVersion: aws.crossplane.io/v1beta1
   kind: ProviderConfig
   metadata:
     name: aws-provider
   spec:
     credentials:
       source: Secret
       secretRef:
         namespace: crossplane-system
         name: aws-creds
         key: key
   ```

4. **Set up RBAC**:
   - Create ServiceAccounts for each team
   - Define Roles with specific resource permissions
   - Create RoleBindings to associate SAs with Roles
   - Test isolation: Team A cannot access Team B's resources

5. **Create GitOps Structure**:
   ```
   infra/crossplane/
   ├── providers/
   │   ├── aws-provider-config.yaml
   │   ├── azure-provider-config.yaml
   │   └── gcp-provider-config.yaml
   ├── compositions/
   │   ├── aws-eks-cluster/
   │   ├── azure-aks-cluster/
   │   ├── gcp-gke-cluster/
   │   ├── shared-postgresql/
   │   └── shared-redis/
   ├── rbac/
   │   ├── team-a-role.yaml
   │   ├── team-b-role.yaml
   │   └── team-c-role.yaml
   └── environments/
       ├── dev/
       ├── staging/
       └── prod/
   ```

#### Success Criteria:
- Crossplane installed and healthy
- All three providers recognized and authenticating
- Test ManagedResource creates successfully
- RBAC isolation verified

---

### Phase 1: Infrastructure Categories (Week 3-4)

**Goal**: Migrate infrastructure category by category, maintaining parallel operation

#### Migration Order (Lowest Risk First):

**1. Storage Services** (Easiest - mostly declarative)
- S3 buckets (AWS) → `storagebucket.storage.k8s.io/v1alpha1`
- Blob Storage (Azure) → `storageaccount.storage.azure.com/v1alpha1`
- Cloud Storage (GCP) → `storagebucket.storage.gcp.k8s.io/v1alpha1`

**2. Databases** (Medium - connection strings need care)
- RDS PostgreSQL (AWS) → `rdsinstance.database.aws.crossplane.io/v1beta1`
- Azure PostgreSQL Flexible → `postgresqldatabase.database.azure.com/v1beta1`
- Cloud SQL PostgreSQL (GCP) → `postgresqlinstance.database.gcp.crossplane.io/v1beta1`
- ElastiCache Redis (AWS) → `elasticachereplicationgroup.cache.aws.crossplane.io/v1beta1`
- Azure Redis Cache → `rediscache.cache.azure.com/v1beta1`
- Memorystore Redis (GCP) → `redisinstance.cache.gcp.crossplane.io/v1beta1`

**3. Networking** (Complex - dependencies matter)
- VPCs, Subnets, Security Groups
- Load Balancers / Application Gateway / Cloud Load Balancer

**4. Kubernetes Clusters** (Most complex - control plane)
- EKS (AWS) → `environment.aws.ek/
- AKS (Azure) → `azurekinfrastructure.azure.upbound.io/v1beta1`
- GKE (GCP) → `gkecuster.gke.gcp.crossplane.io/v1beta1`

#### Migration Process per Category:

1. **Write Crossplane Composition** that replicates Terraform resource
2. **Create XResource** (custom resource) using the composition
3. **Parallel Operation**: Terraform continues managing, Crossplane creates separate resources
4. **Validation**:
   - Resource created in cloud provider
   - Properties match Terraform configuration
   - Connectivity works (e.g., database connection string)
5. **Cutover Decision**:
   - If validation succeeds, **tag resource** for Crossplane management
   - **Terraform: Import resource** into state (read-only)
   - **Do NOT destroy** with Terraform; let Crossplane manage going forward
6. **Rollback**: If Crossplane fails, Terraform still controls resource

---

### Phase 2: Complex Orchestrations (Week 5-6)

**Goal**: Migrate multi-cloud orchestration logic from Python/Go to Crossplane Compositions

#### Current Orchestrator Patterns:

1. **`multi_cloud_orchestrator.py`**:
   - Parallel resource provisioning
   - Cost-based optimization
   - Health checks and validation
   - **Migration**: Replace with Crossplane `Environment` claims + `ComEnvironment` classes

2. **`multi-cloud-scatter-gather.go`**:
   - Temporal scatter/gather across clouds
   - Consensus building
   - Cross-cloud recommendation generation
   - **Migration**: Use Crossplane's `CompositeResource` with `Environment` per cloud, aggregate via K8s APIs

3. **`multi-cloud-abstraction.js`**:
   - Unified API across providers
   - Cost optimization (`optimizeResourcePlacement`)
   - Failover planning (`createFailoverPlan`)
   - **Migration**: Build custom `MultiCloudTopology` CRD that composes resources across providers with placement policies

#### Example Migration: Multi-Region EKS + RDS

**Current Terraform**:
- AWS EKS module
- RDS module in separate region
- Manual VPC peering / Transit Gateway configuration

**Crossplane Composition**:
```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: multiregionaksclusters.platform.example.org
spec:
  group: platform.example.org
  names:
    kind: MultiRegionAksCluster
  claimNames:
    kind: MultiRegionAksClusterClaim
  versions:
  - name: v1alpha1
    referenceable: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              regions:
                type: array
                items:
                  type: string
              databaseRegion:
                type: string
---
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: multiregionaksclusters.platform.example.org
spec:
  compositeTypeRef:
    apiVersion: platform.example.org/v1alpha1
    kind: MultiRegionAksCluster
  resources:
  - name: primary-aks
    base:
      apiVersion: infrastructure.platform.azure.upbound.io/v1beta1
      kind: KubernetesCluster
      spec:
        forProvider:
          location: ${this.regions[0]}
          resourceGroupName: ${this.resourceGroup}
          defaultNodePool:
            nodeCount: 3
    patches:
    - type: FromCompositeFieldPath
      fromFieldPath: spec.regions[0]
      toFieldPath: spec.forProvider.location
```

---

### Phase 3: Decommission Terraform (Week 7-8)

**Goal**: Retire Terraform for migrated resources, fully transition to Crossplane

#### Decommissioning Steps:

1. **Audit**:
   - Identify all resources still managed by Terraform
   - Verify Crossplane is managing equivalents
   - Check state files for drift

2. **Import (One-time)**:
   ```bash
   # For each resource managed by Crossplane, import into Terraform state as "read-only"
   terraform import module.eks.aws_eks_cluster.this[0] ${cluster_id}
   # Mark resource as `lifecycle { prevent_destroy = true }` in Terraform
   # Remove resource from Terraform configuration
   ```

3. **Remove Terraform Modules**:
   - Delete AWS/Azure/GCP Terraform directories
   - Remove variables, outputs, provider configurations
   - Archive state files for compliance (30-day retention)

4. **Update Skills**:
   - Modify `multi_cloud_orchestrator.py` to use Kubernetes API (not cloud SDKs)
   - Change `provision-infrastructure` skills to create Crossplane XResources
   - Update `multi-cloud-scatter-gather.go` to query Crossplane status
   - Convert `multi-cloud-abstraction.js` to Crossplane REST API client

5. **Monitoring & Alerting**:
   - Add Crossplane metrics to Prometheus/Grafana
   - Set up alerts for resource drift (via Crossplane external-cluster claim)
   - Track composition health

6. **Documentation Update**:
   - Update READMEs to reflect Crossplane architecture
   - Create runbooks for Crossplane troubleshooting
   - Document RBAC roles and permissions

---

## 4. Multi-Cloud Managed Resource Mapping

### 4.1 AWS Resources

| Terraform Resource | Crossplane XRD/XResource | Composition |
|-------------------|--------------------------|-------------|
| `aws_eks_cluster` | `clusters.ecs.aws.crossplane.io/v1beta1` | `eks-composition.yaml` |
| `aws_db_instance` | `rdsinstances.database.aws.crossplane.io/v1beta1` | `postgres-composition.yaml` |
| `aws_elasticache_cluster` | `elasticachereplicationgroups.cache.aws.crossplane.io/v1beta1` | `redis-composition.yaml` |
| `aws_s3_bucket` | `storagebuckets.storage.aws.crossplane.io/v1alpha1` | `s3-composition.yaml` |
| `aws_lb` | `loadbalancers.elb.aws.crossplane.io/v1beta1` | `alb-composition.yaml` |
| `aws_vpc` | `vpcs.networking.aws.crossplane.io/v1beta1` | `vpc-composition.yaml` |

### 4.2 Azure Resources

| Terraform Resource | Crossplane XRD/XResource | Composition |
|-------------------|--------------------------|-------------|
| `azurerm_kubernetes_cluster` | `kubernetesclusters.platform.azure.upbound.io/v1beta1` | `aks-composition.yaml` |
| `azurerm_postgresql_flexible_server` | `postgresqlinstances.database.azure.upbound.io/v1beta1` | `postgres-composition.yaml` |
| `azurerm_redis_cache` | `rediscaches.cache.azure.upbound.io/v1beta1` | `redis-composition.yaml` |
| `azurerm_storage_account` | `storageaccounts.storage.azure.upbound.io/v1beta1` | `storage-composition.yaml` |
| `azurerm_application_gateway` | `applicationgateways.networking.azure.upbound.io/v1beta1` | `appgw-composition.yaml` |

### 4.3 GCP Resources

| Terraform Resource | Crossplane XRD/XResource | Composition |
|-------------------|--------------------------|-------------|
| `google_container_cluster` | `gkeclusters.platform.gcp.upbound.io/v1beta1` | `gke-composition.yaml` |
| `google_sql_database_instance` | `postgresqlinstances.database.gcp.upbound.io/v1beta1` | `cloudsql-composition.yaml` |
| `google_redis_instance` | `redisinstances.cache.gcp.upbound.io/v1beta1` | `memorystore-composition.yaml` |
| `google_storage_bucket` | `storagebuckets.storage.gcp.upbound.io/v1alpha1` | `storage-composition.yaml` |
| `google_compute_global_address` | `globaladdresses.networking.gcp.upbound.io/v1beta1` | `loadbalancer-composition.yaml` |

---

## 5. RBAC Isolation Model

### 5.1 Role Definitions

```yaml
# rbac/team-a-aws-only.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: team-a-crossplane-role
  namespace: team-a
rules:
- apiGroups: ["infrastructure.platform.aws.ecs.azure"],
  resources: ["eksclusters", "vpcs", "rdsinstances"]
  verbs: ["create", "get", "list", "watch", "update", "patch", "delete"]
- apiGroups: ["crossplane.io"]
  resources: ["claimrecords"]
  verbs: ["create", "get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: team-a-crossplane-binding
  namespace: team-a
subjects:
- kind: ServiceAccount
  name: team-a-sa
  namespace: team-a
roleRef:
  kind: Role
  name: team-a-crossplane-role
  apiGroup: rbac.authorization.k8s.io
```

### 5.2 ProviderConfig Access Control

```yaml
# Crossplane providers are cluster-scoped resources
# Only cluster-admins can view/modify ProviderConfigs
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: crossplane-provider-admin
rules:
- apiGroups: ["aws.crossplane.io", "azure.crossplane.io", "gcp.crossplane.io"]
  resources: ["providerconfigs", "providerconfiguses"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: crossplane-provider-admin-binding
subjects:
- kind: Group
  name: "platform-admins"
roleRef:
  kind: ClusterRole
  name: crossplane-provider-admin
  apiGroup: rbac.authorization.k8s.io
```

### 5.3 Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: crossplane-isolation
  namespace: crossplane-system
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: crossplane-system
  egress:
  - to:
    - ipBlock:
        cidr: 10.0.0.0/8  # VPC CIDR where cloud APIs are accessible
```

---

## 6. Skill Updates: Terraform → Crossplane

### 6.1 Multi-Cloud Orchestrator (`multi_cloud_orchestrator.py`)

**Current**: Uses provider SDKs (boto3, azure-mgmt, google-cloud) directly

**Target**: Use Kubernetes Python client to create Crossplane XResources

```python
from kubernetes import client, config

class CrossplaneProvisioner:
    def __init__(self):
        config.load_kube_config()
        self.custom_api = client.CustomObjectsApi()

    def create_eks_cluster(self, name, region, version, node_groups):
        resource = {
            "apiVersion": "infrastructure.platform.aws.ecs.azure/v1beta1",
            "kind": "KubernetesCluster",
            "metadata": {"name": name},
            "spec": {
                "forProvider": {
                    "region": region,
                    "version": version,
                    "nodeGroups": node_groups
                },
                "writeConnectionSecretToRef": {
                    "name": f"{name}-conn",
                    "namespace": "default"
                }
            }
        }
        return self.custom_api.create_namespaced_custom_object(
            group="infrastructure.platform.aws.ecs.azure",
            version="v1beta1",
            namespace="default",
            plural="kubernetesclusters",
            body=resource
        )
```

### 6.2 Scatter-Gather Workflow (`multi-cloud-scatter-gather.go`)

**Current**: Executes Python/Go activities per cloud provider

**Target**: Query Crossplane resources via Kubernetes API

```go
// Instead of per-cloud provider activities, query composed resources
func (a *SkillExecutionActivities) QueryCrossplaneResources(ctx context.Context, claimName string) (map[string]interface{}, error) {
    // Get the composite resource
    composite := &unstructured.Unstructured{}
    composite.SetAPIVersion("platform.example.org/v1alpha1")
    composite.SetKind("MultiCloudTopology")

    // Get all managed resources belonging to this composition
    resourceList := &unstructured.UnstructuredList{}
    // Query with label selector: crossplane.io/composite=<claim-name>

    return aggregateResults(resourceList), nil
}
```

### 6.3 Multi-Cloud Abstraction (`multi-cloud-abstraction.js`)

**Current**: Direct cloud SDK calls with provider-specific implementations

**Target**: REST API client for Crossplane

```javascript
class CrossplaneClient {
  async createResource(composition, params) {
    const yaml = this.buildXResource(composition, params);
    const cmd = `kubectl apply -f - <<'EOF'\n${yaml}\nEOF`;
    const { stdout } = await exec(cmd);
    return this.waitForReady(extractName(yaml));
  }

  async listResources(provider) {
    const kind = this.mapProviderToKind(provider);
    const cmd = `kubectl get ${kind} -o jsonpath='{.items[*].metadata.name}'`;
    const { stdout } = await exec(cmd);
    return stdout.split(' ');
  }
}
```

---

## 7. Validation & Testing Strategy

### 7.1 Unit Tests

Each Composition must have associated test:

```go
// Example: Test that EKS composition creates expected resources
func TestEKSComposition(t *testing.T) {
    // Given: A CompositeResourceClaim for EKS
    claim := newEKSClaim("test-cluster", "us-west-2")

    // When: Crossplane composes it
    composed := compose(claim)

    // Then: Should have 1 EKS cluster, 1 VPC, 2 node pools, etc.
    assert.ResourceCount(composed, clusters.EC2K8sCluster, 1)
    assert.ResourceCount(composed, networking.VPC, 1)
    assert.ResourceCount(composed, computing.NodeGroup, 2)
}
```

### 7.2 Integration Tests

- Use `envtest` or `kubebuilder` test environment
- Spin up Crossplane in test cluster
- Apply Composition and verify managed resources created
- Use cloud provider sandbox accounts for real validation (e.g., AWS `test` account)

### 7.3 Chaos Testing

- Delete managed resource → Crossplane should recreate
- Modify resource outside Crossplane → Detect drift via `external` resource
- Provider credential revocation → Alert and graceful degradation

### 7.4 Performance Baselines

| Metric | Target |
|--------|--------|
| Composition time (EKS) | < 15 minutes |
| Resource drift detection | < 5 minutes |
| Crossplane API latency | < 100ms p95 |
| Memory usage (Crossplane pod) | < 4Gi |
| Concurrent compositions | > 50 |

---

## 8. Rollback Plan

### 8.1 Immediate Rollback (< 1 hour)

If Crossplane fails to create resource:

1. **Abort migration** for that resource category
2. **Continue with Terraform** for all un-migrated resources
3. **No data loss** - resources remain in cloud provider
4. **Cleanup**: Delete Crossplane XResources, keep Terraform unchanged

### 8.2 Partial Migration Rollback

Some resources migrated, others not:

1. **Import** Crossplane-managed resources back into Terraform:
   ```bash
   terraform import module.eks.aws_eks_cluster.this[0] ${cluster_id}
   ```
2. **Update Terraform** to manage them again
3. **Remove** Crossplane Compositions for those resources
4. **Re-enable** Terraform CI/CD pipeline

### 8.3 Full Rollback (Worst Case)

All resources migrated, Crossplane fails catastrophically:

1. **Terraform Import All**:
   - Script to import every Crossplane-managed resource
   - Requires cloud provider APIs and resource IDs
   - Time estimate: 2-4 hours for ~200 resources

2. **Re-enable Terraform**:
   - Un-archive state files
   - Run `terraform plan` to verify
   - Resume Terraform-managed deployments

3. **Crossplane Decommission**:
   - Delete Crossplane installation
   - Remove ProviderConfigs, Compositions
   - Archive Crossplane configurations

**Risk Mitigation**:
- Keep Terraform state files read-only for 30 days post-migration
- Do NOT delete Terraform code until 30-day stabilization period
- Snapshot all cloud resources before final cutover

---

## 9. Cost Analysis

### 9.1 Infrastructure Costs

| Item | Monthly Cost |
|------|--------------|
| Crossplane cluster (existing Kubernetes) | $0 (uses existing) |
| Additional etcd storage (for XResources) | ~$20 |
| Increased API server load | ~$5 |
| Monitoring/observability | ~$0 (existing stack) |
| **Total** | **<$50/month** |

### 9.2 Operational Costs

**Savings**:
- Eliminate Terraform Cloud/Enterprise license fees ($5,000-20,000/year)
- Reduce custom orchestration maintenance (~40 hours/month developer time)
- Consolidate monitoring dashboards (~5 hours/month)

**One-time Migration Cost**:
- Development: 3-4 weeks (2 engineers)
- Testing: 1 week
- Migration execution: 1 week
- **Total**: ~160 hours = **$24,000** (at $150/hour)

**Payback Period**: 1.5-4 years depending on Terraform licensing

---

## 10. Success Metrics

| Metric | Baseline (Terraform) | Target (Crossplane) | Measurement |
|--------|---------------------|--------------------|-------------|
| Provisioning time (EKS) | 25 min | < 15 min | Composition reconciliation duration |
| Cross-cloud dependency coordination | Manual | 100% automated | % of dependencies auto-resolved |
| Developer onboarding time | 2 weeks | < 1 week | Time to first successful deployment |
| Infrastructure drift incidents | 2-3/month | < 1/month | Alert count |
| Multi-cloud cost anomalies | Monthly review | Real-time alerting | Time to detection |
| RBAC violations | 1/month | 0 | Audit log events |
| GitOps pipeline success rate | 95% | > 99% | PR merge success rate |

---

## 11. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Crossplane provider bugs blocking migration | Medium | High | Use stable provider versions, test in sandbox first |
| Resource drift during parallel operation | Medium | Medium | HashiCort Terraform drift detection disabled for migrated resources |
| RBAC misconfiguration causing outages | Low | High | Review RBAC with security team, test in non-prod first |
| Crossplane becoming single point of failure | Medium | High | High-availability Crossplane deployment, backup Terraform ready |
| Provider API rate limits during bulk operations | Medium | Medium | Throttle compositions, batch resource creation |
| Migration taking longer than planned | Medium | Medium | Detailed task tracking, weekly milestone reviews |
| Custom Compositions too complex to build | Low | High | Start with simple resources, leverage community compositions |

---

## 12. Decision Gates

### Gate 1: Proof of Concept (Week 2)

**Criteria**:
- [ ] Crossplane installed on test cluster
- [ ] AWS provider functional (can create EC2, VPC)
- [ ] RBAC isolation verified
- [ ] Sample Composition successfully creates EKS cluster
- [ ] Team leads approve architecture

**Go/No-Go**: Proceed to Phase 1 if all criteria met

### Gate 2: Storage Category Complete (Week 4)

**Criteria**:
- [ ] All S3, Blob, Storage buckets migrated
- [ ] No data loss or downtime
- [ ] Terraform state imported for migrated resources
- [ ] Monitoring working (resource counts match)
- [ ] Lessons learned documented

**Go/No-Go**: Adjust timeline or rollback if success rate < 95%

### Gate 3: Database Category Complete (Week 5)

**Criteria**:
- [ ] All managed databases migrated
- [ ] Connection strings updated in applications
- [ ] No connection failures > 1 minute
- [ ] Backup/restore tested
- [ ] Failover tested (if applicable)

**Go/No-Go**: Continue to Kubernetes clusters if DB availability > 99.9%

### Gate 4: All Resources Migrated (Week 8)

**Criteria**:
- [ ] 100% of Terraform-managed resources now Crossplane-managed
- [ ] Terraform state files archived (no drift)
- [ ] Terraform CI/CD disabled or in read-only mode
- [ ] All skills updated to use Crossplane APIs
- [ ] Documentation updated
- [ ] 30-day stabilization period begins

---

## 13. Post-Migration: Stabilization (Weeks 9-12)

### 13.1 Monitoring Priorities

- Crossplane composition reconciliation duration
- Managed resource health (external-status conditions)
- Provider API errors (rate limits, auth failures)
- RBAC violation attempts
- Resource drift detection events

### 13.2 Operational Runbooks

- **Crossplane pod crash**: Restart, check provider credentials, scale deployment
- **Composition stuck**: Investigate resource dependencies, check provider status
- **RBAC violation**: Review Role/RoleBinding, update permissions
- **Provider auth failure**: Rotate credentials in ProviderConfig secret
- **Drift detected**: Investigate external modification, remediate or accept

### 13.3 Team Training

- Platform team: Crossplane CRD management, Composition authoring
- Application teams: Claim-based requests, troubleshooting resources
- Security team: RBAC management, ProviderConfig security

---

## 14. Appendix

### A. Crossplane Version Selection

**Recommended**: Crossplane v1.12+ (stable, broad provider support)

Provider versions:
- `provider-aws`: v0.35.0+
- `provider-azure**: v0.44.0+
- `provider-gcp**: v0.38.0+

### B. Kubernetes Cluster Requirements

- **Kubernetes**: v1.24+
- **etcd**: Minimum 3 nodes, 8Gi+ each
- **Crossplane resources**: ~500-1000 XResources (plan 20Gi etcd)
- **Network**: Egress to cloud provider APIs (no proxy needed for most)

### C. Further Reading

- [Crossplane Official Documentation](https://docs.crossplane.io)
- [Upbound Provider Documentation](https://marketplace.upbound.io)
- [Crossplane RBAC Guide](https://docs.crossplane.io/latest/concepts/rbac/)
- [Composition Best Practices](https://docs.crossplane.io/latest/concepts/compositions/)

### D. Contact & Ownership

**Migration Lead**: [TBD]
**Platform Team**: [platform-team@organization]
**Security Review**: [security-team@organization]
**Escape Valve**: Terraform state files archived at `s3://bucket/terraform-backup/YYYY-MM-DD/`

---

## Next Steps

1. **Review** this document with stakeholders (Platform, Security, DevOps)
2. **Create detailed task breakdown** in project management tool
3. **Set up proof-of-concept** environment (Week 1)
4. **Begin Phase 0** installation and RBAC configuration
5. **Schedule weekly sync** for migration progress

---

*Document version: 1.0*
*Last updated: 2026-03-20*

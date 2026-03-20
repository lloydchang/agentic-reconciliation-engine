# Crossplane Migration Implementation Roadmap

**Actionable Migration Plan Based on Current Repository State**

*Document Version: 1.0*
*Date: 2026-03-20*
*Status: Ready for Execution*
*Related: CROSSPLANE-MIGRATION-PLAN.md*

---

## Purpose

This document provides the **actionable implementation plan** for migrating from Terraform and custom multi-cloud orchestration to Crossplane. It is derived from the comprehensive strategy in `CROSSPLANE-MIGRATION-PLAN.md` but focuses on **specific file changes, concrete tasks, and immediate next steps**.

---

## Current State Analysis

### Infrastructure as Code

| Location | Provider | Resources | Status |
|----------|----------|-----------|--------|
| `core/infrastructure/terraform/aws/main.tf` | AWS | VPC, EKS, RDS, ElastiCache, S3, CloudFront, WAF, IAM, Route53 | Active |
| `core/infrastructure/terraform/gcp/main.tf` | GCP | VPC, GKE, Cloud SQL, Memorystore, GCS, Cloud DNS, Cloud Armor | Active |
| `core/infrastructure/terraform/azure/main.tf` | Azure | VNet, AKS, PostgreSQL, Redis, Storage, App Gateway, Key Vault | Active |

**Total**: ~500 lines per provider, covering complete infrastructure stack.

### Multi-Cloud Orchestration Layer

| File | Purpose | Usage |
|------|---------|-------|
| `core/multi-cloud-abstraction.js` | Unified JS API for AWS/GCP/Azure | Direct SDK wrapper, 661 lines |
| `core/ai/skills/*/scripts/multi_cloud_orchestrator.py` | Python orchestrator (24 copies) | Used by 24 skills (analyze-logs, optimize-costs, etc.) |
| `core/scripts/automation/multi_cloud_upgrade.py` | Upgrades automation | Legacy |
| `core/automation/scripts/multi_cloud_upgrade.py` | Alternative location | Redundant |
| `overlay/ai/skills/complete-hub-spoke-temporal/workflows/multi-cloud-scatter-gather.go` | Go Temporal workflow | Parallel multi-cloud operations |

**Critical Finding**: There are **24 identical copies** of `multi_cloud_orchestrator.py` spread across skill directories. They all import from `infrastructure_provisioning_handler.py`.

### Skills Integration

24 AI skills depend on multi-cloud orchestration:
```
analyze-logs, analyze-security, assist-kubectl, check-cluster-health,
deploy-strategy, discover-infrastructure, generate-compliance-report,
incident-triage-runbook, manage-infrastructure, optimize-costs,
optimize-performance, optimize-resources, orchestrate-automation,
orchestrate-backups, plan-capacity, predict-incidents, prioritize-alerts,
provision-infrastructure, recover-from-disaster, route-alerts,
summarize-incidents, track-audit-events, troubleshoot-kubernetes
```

---

## Phase 0: Foundation Setup (Week 1-2) - DETAILED TASKS

### 0.1 Cluster Readiness Assessment

**Execute**:
```bash
# Check Kubernetes cluster version
kubectl version --short

# Check available resources
kubectl describe nodes | grep -E "Allocated|Capacity"

# Check existing Crossplane installation (if any)
kubectl get all -n crossplane-system

# Check provider CRDs
kubectl get crd | grep crossplane
```

**Acceptance Criteria**:
- Kubernetes version >= 1.24
- Minimum 4 CPUs and 8Gi memory available for Crossplane pods
- `crossplane-system` namespace exists (will create if not)

### 0.2 Secret Management Setup

**Create ExternalSecrets configuration**:

```yaml
# File: gitops/infrastructure/crossplane/secretstores/aws-secretstore.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secretstore
  namespace: crossplane-system
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-west-2
```

Repeat for GCP (Secret Manager) and Azure (Key Vault).

**Migration of credentials**:
1. Extract credentials from Terraform variables/state (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, GOOGLE_CREDENTIALS, AZURE_CLIENT_SECRET)
2. Store in cloud provider secret stores with names: `/crossplane/aws/access-key`, `/crossplane/aws/secret-key`, etc.
3. Create `ExternalSecret` CRs to pull into K8s secrets

**Documentation**: Create `docs/secrets-migration.md` with credential mapping.

### 0.3 Crossplane Installation

```bash
# Add Helm repo
helm repo add crossplane-stable https://charts.crossplane.io/stable/
helm repo update

# Create namespace
kubectl create namespace crossplane-system

# Install Crossplane (with custom values)
cat > values-crossplane.yaml <<EOF
replicas: 2
image:
  tag: v1.13.0
providerTeams:
  enabled: false
rbac:
  enable: true
metrics:
  enable: true
  serviceMonitor:
    enabled: true
podSecurityContext:
  fsGroup: 2000
  runAsNonRoot: true
securityContext:
  allowPrivilegeEscalation: false
  runAsNonRoot: true
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL
resources:
  requests:
    cpu: "100m"
    memory: "256Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
EOF

helm install crossplane crossplane-stable/crossplane \
  --namespace crossplane-system \
  --values values-crossplane.yaml
```

**Verification**:
```bash
kubectl wait --for=condition=Ready pod -l app=crossplane -n crossplane-system --timeout=300s
kubectl get pods -n crossplane-system
```

### 0.4 GitOps Structure Setup

**Create directory structure** in the repository:

```
gitops/infrastructure/crossplane/
├── providers/
│   ├── aws-provider.yaml
│   ├── gcp-provider.yaml
│   ├── azure-provider.yaml
│   └── kubernetes-provider.yaml
├── providerconfigs/
│   ├── aws-providerconfig.yaml
│   ├── gcp-providerconfig.yaml
│   ├── azure-providerconfig.yaml
│   └── kubernetes-providerconfig.yaml
├── xrds/
│   ├── xnetwork.yaml
│   ├── xcluster.yaml
│   ├── xdatabase.yaml
│   ├── xstorage.yaml
│   └── xlb.yaml
├── compositions/
│   ├── networking/
│   │   ├── network-aws.yaml
│   │   ├── network-azure.yaml
│   │   └── network-gcp.yaml
│   ├── compute/
│   │   ├── cluster-eks.yaml
│   │   ├── cluster-aks.yaml
│   │   └── cluster-gke.yaml
│   ├── database/
│   │   ├── database-aws.yaml
│   │   ├── database-gcp.yaml
│   │   └── database-azure.yaml
│   └── storage/
│       ├── bucket-aws.yaml
│       ├── bucket-gcp.yaml
│       └── storageaccount-azure.yaml
├── claims/
│   ├── dev/
│   ├── staging/
│   └── prod/
└── kustomization.yaml
```

**Commit structure** to Git:
```bash
mkdir -p gitops/infrastructure/crossplane/{providers,providerconfigs,xrds,compositions/{networking,compute,database,storage},claims/{dev,staging,prod}}
git add gitops/
git commit -m "Add Crossplane GitOps directory structure"
```

---

## Phase 1: Provider Configuration (Week 3-4) - DETAILED TASKS

### 1.1 AWS Provider

**File**: `gitops/infrastructure/crossplane/providers/aws-provider.yaml`

```yaml
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-aws
  namespace: crossplane-system
spec:
  package: "crossplane/provider-aws:v0.41.0"
  runtimeConfigRef:
    name: aws-provider-config
---
apiVersion: pkg.crossplane.io/v1beta1
kind: ControllerConfig
metadata:
  name: aws-provider-config
  namespace: crossplane-system
spec:
  args:
    - --dangerous-disable-forward-rotation
  podTemplate:
    spec:
      containers:
        - name: provider-aws
          resources:
            limits:
              memory: "512Mi"
            requests:
              cpu: "100m"
              memory: "256Mi"
      tolerations:
        - key: "node-role.kubernetes.io/master"
          operator: "Exists"
          effect: "NoSchedule"
```

**ProviderConfig** (`providerconfigs/aws-providerconfig.yaml`):

```yaml
apiVersion: aws.crossplane.io/v1beta1
kind: ProviderConfig
metadata:
  name: aws-provider
  namespace: crossplane-system
spec:
  credentials:
    source: "Secret"
    secretRef:
      namespace: "crossplane-system"
      name: "aws-creds"
      key: "creds"
```

Ensure `external-secrets` populates `aws-creds` with credentials.

**Apply**:
```bash
kubectl apply -f gitops/infrastructure/crossplane/providers/aws-provider.yaml
kubectl apply -f gitops/infrastructure/crossplane/providerconfigs/aws-providerconfig.yaml
kubectl get provider -n crossplane-system
kubectl wait --for=condition=Healthy provider/provider-aws -n crossplane-system --timeout=300s
```

### 1.2 GCP Provider

Similar pattern with GCP provider package `crossplane/provider-gcp:v0.35.0`.

**Important**: GCP requires WORKLOAD_IDENTITY_POOL and workload identity federation. See docs.

### 1.3 Azure Provider

Azure provider `crossplane/provider-azure:v0.12.0`. Requires service principal credentials.

### 1.4 Testing Providers

Create test managed resources to verify connectivity:

```yaml
# claims/test/aws-s3-test.yaml
apiVersion: s3.aws.crossplane.io/v1beta1
kind: Bucket
metadata:
  name: crossplane-test-bucket-${USER}
  namespace: crossplane-test
spec:
  forProvider:
    locationConstraint: us-west-2
    versioningConfiguration:
      status: Enabled
  providerConfigRef:
    name: aws-provider
  writeConnectionSecretToRef:
    name: aws-s3-connection
    namespace: crossplane-test
```

Apply and verify bucket created in AWS console.

---

## Phase 2: Network Migration (Week 5)

### 2.1 Verify Existing XResources

Check if XRDs already exist:

```bash
kubectl get xrds.apiextensions.crossplane.io
```

Expected: `xnetworks.platform.example.org`, `xclusters.platform.example.org`, etc.

If not, apply from `core/operators/control-plane/crossplane/xrds/`.

### 2.2 Review Existing Compositions

Check if network compositions exist:

```bash
kubectl get compositions.apiextensions.crossplane.io
```

Expected: `network-aws`, `network-azure`, `network-gcp`, etc.

If they exist, validate they match Terraform configurations by comparing:

| Terraform Resource | Crossplane Composition | Expected Outcome |
|-------------------|------------------------|------------------|
| `module.vpc` (AWS) | `network-aws` | VPC + subnets + NAT + IGW |
| `google_compute_network` | `network-gcp` | VPC + subnets + Cloud Router + NAT |
| `azurerm_virtual_network` | `network-azure` | VNet + subnets + NSG |

**Gap analysis**: Document any differences between Terraform and Compositions.

### 2.3 Create Network Claims

**Example**: Replicate AWS VPC from Terraform

Terraform creates:
- VPC CIDR: `10.0.0.0/16`
- Private subnets: `10.0.1.0/24`, `10.0.2.0/24`, `10.0.3.0/24`
- Public subnets: `10.0.101.0/24`, `10.0.102.0/24`, `10.0.103.0/24`
- NAT Gateway, Internet Gateway, route tables

Crossplane claim:

```yaml
# File: gitops/infrastructure/crossplane/claims/prod/network-aws-portal.yaml
apiVersion: platform.example.com/v1alpha1
kind: Network
metadata:
  name: aws-portal-network-prod
  namespace: platform-infra
spec:
  compositionSelector:
    matchLabels:
      provider: aws
      environment: production
  parameters:
    cidrBlock: "10.0.0.0/16"
    region: "us-west-2"
   availabilityZones: ["us-west-2a", "us-west-2b", "us-west-2c"]
    privateSubnetBits: 8  # /24 subnets
    publicSubnetBits: 8
    enableNatGateway: true
    singleNatGateway: false  # Multi-AZ production
  writeConnectionSecretToRef:
    name: aws-portal-network-conn
    namespace: platform-infra
```

Apply with `kubectl apply -f`.

**Validation**:
```bash
kubectl get network aws-portal-network-prod -n platform-infra -w
# Wait for Ready=True
kubectl get managed -l crossplane.io/composite=aws-portal-network-prod
```

### 2.4 Terraform Network Decommission

After Crossplane network is Ready:

```bash
cd core/infrastructure/terraform/aws
terraform state list | grep module.vpc
# Output:
# module.vpc.aws_vpc.main
# module.vpc.aws_subnet.private[0]
# ...

# Remove from state (NOT DESTROY)
terraform state rm module.vpc.aws_vpc.main
terraform state rm module.vpc.aws_subnet.private[0]
# ... remove all network resources
```

**Important**: Do NOT run `terraform destroy` on these resources - they're now managed by Crossplane.

Comment out network resources in `main.tf`:

```hcl
# module "vpc" {
#   source = "terraform-aws-modules/vpc/aws"
#   # ... commented out
# }
```

Test: `terraform plan` should show zero changes for network resources.

---

## Phase 3: Compute Cluster Migration (Week 6)

### 3.1 EKS Cluster Migration

Terraform uses `terraform-aws-modules/eks/aws` module.

Crossplane Composition should create:
- EKS cluster control plane
- Managed node groups (general, spot)
- Fargate profiles
- IAM roles for service accounts (IRSA)
- Security groups, subnets

**Create Cluster Claim**:

```yaml
# claims/prod/cluster-eks-portal.yaml
apiVersion: platform.example.com/v1alpha1
kind: Cluster
metadata:
  name: eks-portal-prod
  namespace: platform-infra
spec:
  compositionSelector:
    matchLabels:
      provider: aws
      clusterType: eks
      tier: production
  parameters:
    region: us-west-2
    kubernetesVersion: "1.30"
    nodeGroups:
      - name: general
        instanceTypes: ["t3.large", "t3.xlarge"]
        minSize: 3
        maxSize: 10
        desiredSize: 5
        capacityType: ON_DEMAND
      - name: spot
        instanceTypes: ["t3.large", "t3.xlarge"]
        minSize: 0
        maxSize: 10
        desiredSize: 2
        capacityType: SPOT
    fargateProfiles:
      - name: ai-services
        selectors:
          - namespace: ai-infrastructure
            labels:
              compute-type: fargate
    vpcRef:
      name: aws-portal-network-prod  # Reference to Network claim
  writeConnectionSecretToRef:
    name: eks-portal-kubeconfig
    namespace: platform-infra
```

**Critical**: The composition must handle IAM role creation for EKS (OIDC provider, IAM roles for service accounts). This may require Function compositions or external management.

**Validation**:
```bash
kubectl apply -f claims/prod/cluster-eks-portal.yaml
kubectl get cluster eks-portal-prod -n platform-infra -w
# Wait for connection secret: eks-portal-kubeconfig
kubectl get secret eks-portal-kubeconfig -n platform-infra -o yaml
# Extract kubeconfig and test connectivity
```

**Terraform decommission**:

```bash
terraform state rm module.eks.aws_eks_cluster.this[0]
terraform state rm module.eks.aws_eks_node_group.this["general"]
# ... all EKS resources

# Comment out EKS module in main.tf
```

### 3.2 GKE & AKS Migration

Repeat similar process for GKE and AKS clusters.

**GCP Specific**: GKE can use Autopilot mode (like Terraform `enable_autopilot = true`).

**Azure Specific**: AKS requires Azure AD integration; may need manual steps for service principal.

---

## Phase 4: Database & Storage Migration (Week 7)

### 4.1 Database Claims

**Pattern**: Database claim creates RDS/Cloud SQL/Azure PostgreSQL + credentials secret.

```yaml
apiVersion: platform.example.com/v1alpha1
kind: Database
metadata:
  name: postgres-ai-portal
  namespace: ai-infrastructure
spec:
  compositionSelector:
    matchLabels:
      provider: aws
      engine: postgres
      tier: production
  parameters:
    engine: postgres
    version: "15"
    size: large  # Maps to db.t3.large or equivalent
    storageGB: 100
    region: us-west-2
    backupRetentionDays: 7
    highAvailability: true
    multiAZ: true
    deletionProtection: true
  writeConnectionSecretToRef:
    name: postgres-ai-portal-conn
    namespace: ai-infrastructure
```

**Migration steps**:

1. Create Database claim for each existing database
2. Consider using `deletionPolicy: Orphan` initially to protect existing data (if adopting existing resources)
3. For NEW databases, can use `deletionPolicy: Delete` after validation
4. Update application deployments to use connection secrets from Crossplane
5. Decommission Terraform RDS/Cloud SQL/Azure Database resources

**Terraform state removal**:
```bash
terraform state rm module.rds.aws_db_instance.this[0]
# etc.
```

### 4.2 Redis/Cache Migration

Similar pattern. May reuse XDatabase composition with `engine: redis`, or have separate XRedis XRD.

---

## Phase 5: Storage & CDN Migration (Week 8)

### 5.1 Storage Buckets

```yaml
apiVersion: platform.example.com/v1alpha1
kind: Bucket
metadata:
  name: ai-portal-backups
  namespace: platform-infra
spec:
  compositionSelector:
    matchLabels:
      provider: aws
  parameters:
    location: us-west-2
    versioningEnabled: true
    encryption: AES256
    lifecycleRules:
      - expirationDays: 90
  writeConnectionSecretToRef:
    name: bucket-backups-conn
    namespace: platform-infra
```

### 5.2 Load Balancers

Crossplane can create ALB/Application Gateway/Cloud Load Balancer + DNS integration.

**Complexity**: Load balancers depend on Kubernetes IngressContour or Service resources. Typically:
- Create LoadBalancer composition
- Reference target Kubernetes cluster (from XCluster claim)
- Configure health checks, SSL certificates, routing rules

---

## Phase 6: Multi-Cloud Orchestrator Migration (Week 9-10)

### 6.1 Centralize Orchestrator

**Current state**: 24 duplicate copies of `multi_cloud_orchestrator.py`.

**Goal**: Single source of truth.

**Strategy**:
1. **Consolidate** all copies to a single shared location
2. **Replace** cloud SDK calls with Crossplane API client
3. **Add** fallback mode for backwards compatibility during transition
4. **Update** all skill scripts to import from central location

**Implementation**:

**Step 1**: Create central Crossplane client:

```python
# File: core/ai/multi-cloud/crossplane_client.py
from kubernetes import client, config
from typing import List, Dict, Any

class CrossplaneClient:
    def __init__(self):
        config.load_incluster_config()  # or load_kube_config()
        self.custom_api = client.CustomObjectsApi()
        self.namespace = "crossplane-system"

    def get_managed_resources(self, provider: str, resource_kind: str) -> List[Dict]:
        """Query Crossplane managed resources by provider and kind"""
        group, version = self._get_group_version(provider, resource_kind)
        resources = self.custom_api.list_namespaced_custom_object(
            group=group,
            version=version,
            namespace=self.namespace,
            plural=resource_kind
        )
        return resources.get('items', [])

    def get_xresource_status(self, xr_name: str, xr_kind: str) -> Dict:
        """Get status of composite resource"""
        group, version = self._get_xr_group_version(xr_kind)
        xr = self.custom_api.get_namespaced_custom_object(
            group=group,
            version=version,
            namespace="platform-infra",
            name=xr_name,
            plural=xr_kind.lower() + "s"
        )
        return xr.get('status', {})

    def _get_group_version(self, provider: str, resource: str) -> tuple:
        # Map provider+resource to Crossplane API group/version
        mapping = {
            ('aws', 'vpc'): ('networking.aws.crossplane.io', 'v1beta1'),
            ('aws', 'compute'): ('ec2.aws.crossplane.io', 'v1beta1'),
            # ... etc.
        }
        return mapping.get((provider, resource), ('', 'v1beta1'))
```

**Step 2**: Create unified `MultiCloudOrchestrator` with Crossplane backend:

```python
# File: core/ai/multi-cloud/orchestrator.py

class CrossplaneBackend:
    def __init__(self, k8s_client):
        self.client = k8s_client

    def list_vms(self, provider: str = None) -> List[Dict]:
        """List compute instances via Crossplane XClusters"""
        clusters = self.client.get_xresources('Cluster')
        results = []
        for cluster in clusters:
            if provider and cluster['spec'].get('provider') != provider:
                continue
            # Extract VM/node information from cluster status
            results.append({
                'provider': cluster['spec'].get('provider'),
                'cluster': cluster['metadata']['name'],
                'nodes': cluster['status'].get('nodeCount', 0)
            })
        return results

    def create_network(self, config: Dict) -> Dict:
        """Create network via Crossplane claim"""
        # Create Network custom resource
        pass

    def get_costs(self) -> Dict:
        """Billing info not in Crossplane - fallback to cloud billing API"""
        # Crossplane doesn't track costs natively
        # Use separate billing API or keep legacy for cost reporting
        pass

    # ... other methods
```

**Step 3**: Update skill scripts to use central orchestrator:

**Before** (in each skill script):
```python
from multi_cloud_orchestrator import MultiCloudOrchestrator
orchestrator = MultiCloudOrchestrator()
```

**After**:
```python
from core.ai.multi-cloud.orchestrator import MultiCloudOrchestrator
orchestrator = MultiCloudOrchestrator(backend='crossplane')  # or auto-detect
```

**Step 4**: Add backwards compatibility:

```python
# orchestrator.py
class MultiCloudOrchestrator:
    def __init__(self, backend='auto'):
        if backend == 'auto':
            # Try Crossplane first, fallback to legacy
            try:
                self.backend = CrossplaneBackend()
            except Exception as e:
                print(f"Crossplane not available, using legacy: {e}")
                self.backend = LegacyBackend()
        elif backend == 'crossplane':
            self.backend = CrossplaneBackend()
        else:
            self.backend = LegacyBackend()
```

### 6.2 Go Temporal Workflow Migration

**File**: `overlay/ai/skills/complete-hub-spoke-temporal/workflows/multi-cloud-scatter-gather.go`

**Change**: Replace cloud provider SDK activities with Crossplane query activities.

**Before**:
```go
func ExecuteCloudOperationActivity(ctx context.Context, input CloudAIInput) (CloudAIResult, error) {
    // Calls into (Python) multi_cloud_orchestrator.py via RPC
    result := callPythonService(input)
}
```

**After**:
```go
type CrossplaneClient struct {
    k8sClient kubernetes.Interface
}

func (c *CrossplaneClient) GetResources(ctx context.Context, provider, resourceType string) ([]CloudResource, error) {
    // Query Crossplane custom resources directly in Go using client-go
    xrGroup := "platform.example.org"
    xrVersion := "v1alpha1"
    xrPlural := "xresources"  # or specific kinds

    resources, err := c.k8sClient.CustomObjects().List(c.namespace, &metav1.ListOptions{
        LabelSelector: fmt.Sprintf("provider=%s,type=%s", provider, resourceType),
    })
    return resources, err
}

func ExecuteCloudOperationActivity(ctx context.Context, input CloudAIInput) (CloudAIResult, error) {
    client := &CrossplaneClient{k8sClient: getK8sClient()}
    resources, err := client.GetResources(ctx, input.Provider, input.ResourceType)
    // Aggregate resources into CloudAIResult
}
```

**Implementation Tasks**:
1. Add Kubernetes client-go dependency to Temporal workflow code
2. Create Crossplane client wrapper in Go
3. Replace RPC calls to Python orchestrator with direct K8s API calls
4. Keep Python orchestrator for complex logic, but use Crossplane as data source

---

## Phase 7: Cutover & Decommission (Week 11-12)

### 7.1 Terraform Freeze

1. Add `DEPRECATED.md` to `core/infrastructure/terraform/`:
   ```
   This Terraform configuration is deprecated.
   All new infrastructure must be provisioned via Crossplane (gitops/infrastructure/crossplane/).

   Migration completed: 2026-MM-DD
   DO NOT APPLY CHANGES - contact platform team for Crossplane approach.
   ```

2. Update CI/CD pipelines to block Terraform `plan`/`apply`:
   ```bash
   # In .github/workflows/terraform.yml or similar
   - name: Check if Terraform is deprecated
     run: |
       echo "Terraform is deprecated. Use Crossplane claims instead."
       exit 1
   ```

3. Remove Terraform from Makefile/CLI tools.

### 7.2 Remove Multi-Cloud Abstraction Layer

**Delete**:
```bash
rm core/multi-cloud-abstraction.js
rm core/scripts/automation/multi_cloud_upgrade.py
rm -rf core/automation/scripts/multi_cloud_upgrade.py
```

**Update** any remaining references:
```bash
grep -r "multi-cloud-abstraction" --include="*.js" --include="*.ts" --include="*.py" core/
# Replace with Crossplane client imports or remove
```

### 7.3 Archive Legacy Code

Instead of deleting, move to archive:

```bash
mkdir -p archive/terraform
mv core/infrastructure/terraform archive/
git add archive/
git commit -m "Archive deprecated Terraform configurations"
```

Keep `multi_cloud_orchestrator.py` copies in place but modify them to **delegate to central Crossplane orchestrator**:

```python
# In each skill's multi_cloud_orchestrator.py
from core.ai.multi-cloud.orchestrator import MultiCloudOrchestrator

# All existing code replaced with wrapper
def main():
    orchestrator = MultiCloudOrchestrator()
    # Delegate all operations to central orchestrator
```

---

## Phase 8: Testing & Validation (Concurrent)

### Test Checklist

- [ ] Each provider can create basic resources (VPC, bucket, compute)
- [ ] Network claims create VPC with expected CIDR and subnets
- [ ] Cluster claims create EKS/AKS/GKE and write kubeconfig secret
- [ ] Database claims create managed DB with connectivity secret
- [ ] All 24 skills execute successfully using Crossplane backend
- [ ] Go Temporal workflows function with Crossplane data source
- [ ] GitOps sync works: changes in `gitops/` → Crossplane resources → cloud resources
- [ ] Manual resource deletion is reconciled (self-healing)
- [ ] Provider credential rotation works (external-secrets refresh)
- [ ] Monitoring: Prometheus alerts on Crossplane health
- [ ] Cost tracking: cost similar to Terraform baseline (±20%)

---

## Rollback Procedures

### If Crossplane Fails During Migration

1. **Pause**: Stop applying new Crossplane claims
2. **Diagnose**: Check Crossplane logs, provider health
3. **Rollback individual claim**: Delete Crossplane XResource → resource becomes Orphan (not deleted) → re-import into Terraform:
   ```bash
   terraform import module.vpc.aws_vpc.main vpc-12345
   terraform state replace-provider registry.terraform.io/hashicorp/aws registry.terraform.io/hashicorp/aws
   ```
4. **Re-enable** Terraform for that resource type
5. **Investigate** Crossplane issue; fix; retry

### Full Rollback (Emergency)

If Crossplane completely fails and cannot be recovered quickly:

1. Switch all orchestrator backends to `LegacyBackend` (feature flag)
2. Re-activate Terraform code (uncomment in `main.tf`)
3. Re-import all migrated resources into Terraform state (time-consuming)
4. Document failure, fix Crossplane offline, try again later

---

## Implementation Checklist

Use this as your execution tracker:

### [ ] Phase 0 Complete
- [ ] Cluster assessed (version, capacity)
- [ ] ExternalSecrets installed
- [ ] AWS/GCP/Azure secret stores configured
- [ ] Secrets populated with cloud credentials
- [ ] Crossplane installed and healthy
- [ ] Flux configured for `gitops/infrastructure/crossplane/`
- [ ] Provider pods running: `provider-aws`, `provider-gcp`, `provider-azure`

### [ ] Phase 1 Complete
- [ ] AWS ProviderConfig created and tested (S3 bucket test)
- [ ] GCP ProviderConfig created and tested (GCS bucket test)
- [ ] Azure ProviderConfig created and tested (Storage account test)
- [ ] All providers show `Healthy` status
- [ ] Monitoring dashboards configured

### [ ] Phase 2 Complete
- [ ] XNetwork XRD verified
- [ ] Network Compositions reviewed and adjusted
- [ ] Network claims created for each environment (dev/staging/prod)
- [ ] Networks provisioned successfully in all clouds
- [ ] Terraform network resources removed from state
- [ ] Network Terraform code commented out

### [ ] Phase 3 Complete
- [ ] XCluster XRD verified
- [ ] Cluster Compositions reviewed
- [ ] EKS claim created and cluster Ready
- [ ] GKE claim created and cluster Ready
- [ ] AKS claim created and cluster Ready
- [ ] Kubeconfig secrets created and tested
- [ ] Terraform cluster resources removed from state
- [ ] Cluster Terraform code commented out

### [ ] Phase 4 Complete
- [ ] XDatabase XRD verified
- [ ] Database Compositions working
- [ ] Database claims created for all environments
- [ ] Databases Ready, connection secrets populated
- [ ] Applications can connect to Crossplane-provisioned DBs
- [ ] Terraform database resources removed from state

### [ ] Phase 5 Complete
- [ ] Buckets, LB, DNS migrated
- [ ] All remaining infrastructure on Crossplane
- [ ] Multi-cloud consistency verified

### [ ] Phase 6 Complete
- [ ] Central Crossplane client created
- [ ] Orchestrator backend replaced with Crossplane
- [ ] All 24 skill scripts updated
- [ ] All 24 skill scripts tested successfully
- [ ] Go Temporal workflows updated
- [ ] Multi-cloud scatter-gather works with Crossplane
- [ ] Legacy orchestrator copies call central Crossplane orchestrator

### [ ] Phase 7 Complete
- [ ] Terraform completely frozen (CI/CD blocks)
- [ ] Terraform code archived or removed
- [ ] Multi-cloud abstraction layer removed
- [ ] Documentation updated
- [ ] Team trained on Crossplane operations
- [ ] Runbooks created

### [ ] Phase 8 Complete
- [ ] All tests passing
- [ ] Performance acceptable (<2x Terraform provisioning time)
- [ ] Cost variance <10%
- [ ] Zero production incidents
- [ ] Monitoring and alerting active
- [ ] Hypercare period complete (2 weeks)

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Resources managed by Crossplane | 100% | `kubectl get managed | wc -l` vs Terraform state |
| Reconciliation success rate | >99% | Crossplane metrics |
| Provisioning time | <2x Terraform | Time from claim creation to Ready=True |
| Skill execution success | 100% | Run all 24 skills, check exit codes |
| Terraform usage | 0% | CI/CD pipelines, Makefile, local dev |
| Team confidence | >80% survey score | Post-migration team survey |

---

## Conclusion

This roadmap provides the **specific, file-level implementation plan** to execute the Crossplane migration.

**Next Immediate Steps**:

1. Review this document with platform team
2. Get approval to start Phase 0
3. Create GitOps directory structure and commit
4. Install Crossplane in dev cluster (not prod yet)
5. Complete provider health checks
6. Begin network migration with test environment

**Remember**: This is a **gradual, reversible migration**. Each resource type migrates independently. Keep Terraform running for resources not yet migrated. Test thoroughly before decommissioning any Terraform.

---

**Document Owner**: Platform Engineering
**Last Updated**: 2026-03-20
**Next Review**: After Phase 0 completion

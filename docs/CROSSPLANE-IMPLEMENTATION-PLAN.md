# Crossplane Migration Implementation Plan

## Overview

This document provides a detailed, actionable implementation plan for migrating from Terraform-based multi-cloud infrastructure to a single Crossplane Kubernetes-native control plane.

---

## Phase 0: Preparation (Week 1-2)

### Task 0.1: Install Crossplane on Target Cluster
**Owner**: Platform Team
**Duration**: 4 hours
**Dependencies**: Kubernetes cluster (v1.24+) available

**Steps**:
1. Create `crossplane-system` namespace
   ```bash
   kubectl create namespace crossplane-system
   ```
2. Add Crossplane Helm repository
   ```bash
   helm repo add crossplane-stable https://charts.crossplane.io/stable
   helm repo update
   ```
3. Install Crossplane with RBAC enabled
   ```bash
   helm install crossplane crossplane-stable/crossplane \
     --namespace crossplane-system \
     --set rbac.manager=true \
     --wait
   ```
4. Verify installation
   ```bash
   kubectl get pods -n crossplane-system
   kubectl get providers.pkg.crossplane.io
   ```
5. Label cluster for GitOps integration
   ```bash
   kubectl label namespace crossplane-system gitops.crossplane.io/sync=
   ```

**Verification**:
- [ ] Crossplane pod is Running
- [ ] `kubectl get providers` shows at least 3 providers available for installation
- [ ] Crossplane API services are available

---

### Task 0.2: Install Cloud Provider Packages
**Owner**: Platform Team
**Duration**: 2 hours
**Dependencies**: Task 0.1 complete

**Steps**:
1. Install AWS provider
   ```bash
   kubectl get pkg -n crossplane-system
   # Find provider-aws version
   kubectl install provider-aws <version> \
     --namespace crossplane-system
   ```
2. Install Azure provider
   ```bash
   kubectl install provider-azure <version> \
     --namespace crossplane-system
   ```
3. Install GCP provider
   ```bash
   kubectl install provider-gcp <version> \
     --namespace crossplane-system
   ```
4. Verify providers are healthy
   ```bash
   kubectl get providers.pkg.crossplane.io
   # All should show HEALTHY:True
   ```

**Verification**:
- [ ] `provider-aws` status is HEALTHY
- [ ] `provider-azure` status is HEALTHY
- [ ] `provider-gcp` status is HEALTHY

---

### Task 0.3: Create ProviderConfig Secrets
**Owner**: Security/Platform Team
**Duration**: 3 hours
**Dependencies**: Task 0.2 complete, cloud credentials available

**Steps**:
1. Create AWS ProviderConfig secret
   ```yaml
   # infra/crossplane/providers/aws-creds.yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: aws-creds
     namespace: crossplane-system
   type: Opaque
   stringData:
     key: |
       [default]
       aws_access_key_id = ${AWS_ACCESS_KEY_ID}
       aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
   ```
2. Create AWS ProviderConfig
   ```yaml
   # infra/crossplane/providers/aws-provider-config.yaml
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
3. Repeat for Azure (service principal) and GCP (service account key)
4. Apply configurations with GitOps
   ```bash
   kubectl apply -f infra/crossplane/providers/
   ```
5. Verify ProviderConfigs are ready
   ```bash
   kubectl get providerconfigs.aws.crossplane.io
   kubectl get providerconfigs.azure.crossplane.io
   kubectl get providerconfigs.gcp.crossplane.io
   ```

**Verification**:
- [ ] All ProviderConfigs show `READY: True`
- [ ] No credential errors in Crossplane pod logs
- [ ] Can create test ManagedResource (see Task 0.5)

---

### Task 0.4: Establish RBAC Framework
**Owner**: Platform/Security Team
**Duration**: 4 hours
**Dependencies**: Task 0.3 complete

**Steps**:
1. Create team namespaces
   ```bash
   kubectl create namespace team-a
   kubectl create namespace team-b
   kubectl create namespace team-c
   ```
2. Create ServiceAccounts for each team
   ```yaml
   # infra/crossplane/rbac/team-a-sa.yaml
   apiVersion: v1
   kind: ServiceAccount
   metadata:
     name: team-a-sa
     namespace: team-a
   ```
3. Define team-specific Roles
   ```yaml
   # infra/crossplane/rbac/team-a-role.yaml
   apiVersion: rbac.authorization.k8s.io/v1
   kind: Role
   metadata:
     name: team-a-crossplane-role
     namespace: team-a
   rules:
   - apiGroups: ["infrastructure.platform.aws.ecs.azure"]
     resources: ["eksclusters", "vpcs", "rdsinstances", "elasticachereplicationgroups"]
     verbs: ["create", "get", "list", "watch", "update", "patch", "delete"]
   - apiGroups: ["crossplane.io"]
     resources: ["claimrecords"]
     verbs: ["create", "get", "list", "watch"]
   ```
4. Create RoleBindings
   ```yaml
   # infra/crossplane/rbac/team-a-binding.yaml
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
5. Apply all RBAC configurations
   ```bash
   kubectl apply -f infra/crossplane/rbac/
   ```
6. Test RBAC isolation
   ```bash
   # As team-a, should NOT be able to list Azure resources
   kubectl auth can-i list kubernetesclusters.platform.azure.upbound.io \
     --as=system:serviceaccount:team-a:team-a-sa
   # Should return "no"
   ```

**Verification**:
- [ ] Team A can only access AWS resources (in their namespace)
- [ ] Team B can only access Azure resources
- [ ] Team C can access all providers
- [ ] Crossplane provider configs are not accessible to non-admin teams

---

### Task 0.5: Proof-of-Concept Composition
**Owner**: Platform Team
**Duration**: 4 hours
**Dependencies**: Tasks 0.1-0.4 complete

**Steps**:
1. Create XRD for EKS cluster
   ```yaml
   # infra/crossplane/compositions/aws-eks-cluster/xrd-eks.yaml
   apiVersion: apiextensions.crossplane.io/v1
   kind: CompositeResourceDefinition
   metadata:
     name: eksclusters.platform.aws.ecs.azure
   spec:
     group: platform.aws.ecs.azure
     names:
       kind: EKSCluster
       plural: eksclusters
     claimNames:
       kind: EKSClusterClaim
       plural: eksclusterclaims
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
                 region:
                   type: string
                   default: us-west-2
                 version:
                   type: string
                   default: "1.28"
                 nodeGroups:
                   type: array
                   items:
                     type: object
                     properties:
                       name:
                         type: string
                       instanceType:
                         type: string
                       minSize:
                         type: integer
                       maxSize:
                         type: integer
               required: ["region"]
   ```
2. Create Composition that creates actual EKS cluster
   ```yaml
   # infra/crossplane/compositions/aws-eks-cluster/composition.yaml
   apiVersion: apiextensions.crossplane.io/v1
   kind: Composition
   metadata:
     name: eksclusters.platform.aws.ecs.azure
   spec:
     compositeTypeRef:
       apiVersion: platform.aws.ecs.azure/v1alpha1
       kind: EKSCluster
     resources:
     - name: eks-cluster
       base:
         apiVersion: eks.aws.crossplane.io/v1beta1
         kind: Cluster
         spec:
           forProvider:
             region: us-west-2
             version: "1.28"
             roleArn: arn:aws:iam::123456789012:role/EKSClusterRole
             vpcConfig:
               subnetIds: []
             accessConfig:
                 endpointPrivateAccess: false
                 endpointPublicAccess: true
           writeConnectionSecretToRef:
             name: ""
             namespace: default
       patches:
       - type: FromCompositeFieldPath
         fromFieldPath: spec.region
         toFieldPath: spec.forProvider.region
       - type: FromCompositeFieldPath
         fromFieldPath: spec.version
         toFieldPath: spec.forProvider.version
       - type: ToCompositeFieldPath
         fromFieldPath: status.atProvider.arn
         toFieldPath: status.clusterArn
   ```
3. Create a Claim (what teams will actually request)
   ```yaml
   # infra/crossplane/compositions/aws-eks-cluster/claim-test.yaml
   apiVersion: platform.aws.ecs.azure/v1alpha1
   kind: EKSClusterClaim
   metadata:
     name: test-eks-cluster
   spec:
     region: us-west-2
     version: "1.28"
     nodeGroups:
     - name: general
       instanceType: t3.medium
       minSize: 2
       maxSize: 5
   ```
4. Apply XRD, Composition, and Claim
   ```bash
   kubectl apply -f infra/crossplane/compositions/aws-eks-cluster/
   ```
5. Monitor reconciliation
   ```bash
   kubectl get eksclusterclaims.platform.aws.ecs.azure -w
   kubectl get eksclusters.platform.aws.ecs.azure
   ```

**Verification**:
- [ ] XRD is established successfully
- [ ] Composition is recognized
- [ ] Claim reconciles to `READY: True`
- [ ] Actual EKS cluster appears in AWS console
- [ ] Connection secret created with kubeconfig

---

## Phase 1: Infrastructure Categories Migration

### Category 1: Storage Services (Week 3)

#### Task 1.1: Migrate S3 Buckets (AWS)
**Owner**: Platform Team
**Duration**: 4 hours
**Dependencies**: Phase 0 complete

**Steps**:
1. Research existing Terraform S3 buckets
   ```bash
   cd core/infrastructure/terraform/aws
   grep -r "aws_s3_bucket" .
   ```
2. Identify all backup buckets: `ai-portal-backups-*`
3. Create XRD for S3 buckets
   ```yaml
   apiVersion: apiextensions.crossplane.io/v1
   kind: CompositeResourceDefinition
   metadata:
     name: storagebuckets.storage.aws
   spec:
     group: storage.aws
     names:
       kind: StorageBucket
       plural: storagebuckets
     claimNames:
       kind: StorageBucketClaim
       plural: storagebucketclaims
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
                 bucketName:
                   type: string
                 region:
                   type: string
                   default: us-west-2
                 versioningEnabled:
                   type: boolean
                   default: true
                 encryption:
                   type: string
                   default: AES256
   ```
4. Create Composition for S3
   ```yaml
   apiVersion: apiextensions.crossplane.io/v1
   kind: Composition
   metadata:
     name: storagebuckets.storage.aws
   spec:
     compositeTypeRef:
       apiVersion: storage.aws/v1alpha1
       kind: StorageBucket
     resources:
     - name: bucket
       base:
         apiVersion: s3.aws.crossplane.io/v1beta1
         kind: Bucket
         spec:
           forProvider:
             location: us-west-2
             versioningConfiguration:
               status: Enabled
             serverSideEncryptionConfiguration:
               rules:
               - applyServerSideEncryptionByDefault:
                   sseAlgorithm: AES256
           writeConnectionSecretToRef:
             name: ""
             namespace: default
       patches:
       - type: FromCompositeFieldPath
         fromFieldPath: spec.bucketName
         toFieldPath: metadata.name
       - type: FromCompositeFieldPath
         fromFieldPath: spec.region
         toFieldPath: spec.forProvider.location
       - type: FromCompositeFieldPath
         fromFieldPath: spec.versioningEnabled
         toFieldPath: spec.forProvider.versioningConfiguration.status
   ```
5. **Parallel Operation**: Create Crossplane-managed buckets with new naming scheme
   ```bash
   kubectl apply -f - <<EOF
   apiVersion: storage.aws/v1alpha1
   kind: StorageBucketClaim
   metadata:
     name: ai-portal-backups-crossplane
   spec:
     bucketName: ai-portal-backups-crossplane-${RANDOM_SUFFIX}
     region: us-west-2
     versioningEnabled: true
     encryption: AES256
   EOF
   ```
6. **Validation**: Verify bucket created in AWS console with correct settings
7. **Decision Point**:
   - If bucket created successfully → proceed to cutover
   - If failure → troubleshoot, rollback to Terraform

**Cutover Steps**:
1. Note the existing Terraform bucket name from Terraform state
   ```bash
   terraform output s3_backup_bucket
   ```
2. **Terraform: Import** Crossplane-managed bucket into state (read-only)
   ```bash
   terraform import 'module.s3.aws_s3_bucket.backups["0"]' ${bucket_name}
   ```
3. **Terraform: Prevent destroy** on this resource
   ```hcl
   resource "aws_s3_bucket" "backups" {
     # ... existing config ...
     lifecycle {
       prevent_destroy = true
     }
   }
   ```
4. Remove bucket from Terraform configuration (but keep in state)
5. Verify Crossplane exclusively manages bucket

**Rollback**:
1. Delete Crossplane Claim and Composition
2. Remove `prevent_destroy` from Terraform
3. Terraform resumes management

---

#### Task 1.2: Migrate Azure Blob Storage
**Owner**: Platform Team
**Duration**: 3 hours
**Dependencies**: Task 1.1 complete (pattern established)

**Steps**: Follow same pattern as AWS S3, but using Azure provider
1. Create XRD for `storageaccounts.storage.azure`
2. Create Composition that provisions `StorageAccount` + `BlobContainer`
3. Create Claim for backup storage account
4. Parallel operation: let Terraform and Crossplane both exist
5. Validate account created with correct settings (versioning, encryption)
6. Cutover: Import to Terraform state, mark `prevent_destroy`, remove from config

---

#### Task 1.3: Migrate GCP Cloud Storage
**Owner**: Platform Team
**Duration**: 3 hours
**Dependencies**: Task 1.2 complete

**Steps**: Follow same pattern with GCP provider

---

#### Category 1 Decision Gate
**Criteria**:
- [ ] All 3 storage buckets successfully migrated to Crossplane
- [ ] Terraform state imported for all 3
- [ ] No data loss or access issues
- [ ] Backup/restore tested on Crossplane-managed buckets
- [ ] Monitoring shows expected bucket counts

---

### Category 2: Databases (Week 4)

#### Task 2.1: Migrate AWS RDS PostgreSQL
**Owner**: Platform Team
**Duration**: 6 hours (longer due to connection string updates)
**Dependencies**: Category 1 complete

**Steps**:
1. Identify RDS instance from Terraform outputs
   ```bash
   terraform output rds_endpoint
   ```
2. Create XRD for RDS instances
   ```yaml
   apiVersion: apiextensions.crossplane.io/v1
   kind: CompositeResourceDefinition
   metadata:
     name: rdsinstances.database.aws
   spec:
     group: database.aws
     names:
       kind: RDSInstance
       plural: rdsinstances
     claimNames:
       kind: RDSInstanceClaim
       plural: rdsinstanceclaims
     versions:
     - name: v1beta1
       referenceable: true
       schema:
         openAPIV3Schema:
           type: object
           properties:
             spec:
               type: object
               properties:
                 engine:
                   type: string
                   enum: [postgres, mysql, aurora-postgresql]
                   default: postgres
                 version:
                   type: string
                   default: "15.4"
                 instanceClass:
                   type: string
                   default: db.t3.medium
                 allocatedStorage:
                   type: integer
                   default: 20
                 multiAZ:
                   type: boolean
                   default: false
                 dbName:
                   type: string
                 username:
                   type: string
                 password:
                   type: string
                 vpcSecurityGroupIds:
                   type: array
                   items:
                     type: string
                 dbSubnetGroupName:
                   type: string
   ```
3. Create Composition for RDS PostgreSQL
4. Create Claim with same configuration as current Terraform resource
5. **Critical**: Update applications to use new connection secret from Crossplane
   ```bash
   # Old: from Terraform output
   # New: from Crossplane secret
   kubectl get secret ai-portal-backups-crossplane -o jsonpath='{.data.endpoint}'
   ```
6. **Parallel operation**: Both Terraform and Crossplane create DB instances? **NO!**
   - **IMPORTANT**: Cannot have two RDS instances with same identifier
   - Strategy:
     a. Create Crossplane instance with different name (e.g., `ai-portal-db-crossplane`)
     b. Update app config to use Crossplane-managed DB
     c. Test connectivity and functionality
     d. Delete old Terraform-managed DB (after data migration if needed)
     e. Import Crossplane DB into Terraform as read-only

**Alternative (Safer)**:
1. Let Crossplane **import** existing RDS instance (using `external` resource type)
2. Create `RDSInstance` with `external` spec pointing to existing DB
3. Update Terraform to stop managing DB (terraform import to state, then remove)

**Preferred Approach** (if zero downtime required):
```yaml
# Use external resource to adopt existing DB
spec:
  resourceRef:
    apiVersion: rds.aws.crossplane.io/v1beta1
    kind: Database
    name: ai-portal-db-existing  # Existing DB identifier
  forProvider:
    # No forProvider fields - uses existing resource
```
6. After successful cutover, verify PostgreSQL accessible from EKS pods
   ```bash
   kubectl exec -it <pod> -- psql -h ${new_endpoint} -U ${username} -d ${dbname}
   ```

**Rollback**:
1. Revert application config to Terraform DB endpoint
2. Delete Crossplane RDSInstance + Claim
3. Remove `prevent_destroy` from Terraform

---

#### Task 2.2: Migrate Azure PostgreSQL Flexible
**Owner**: Platform Team
**Duration**: 5 hours
**Dependencies**: Task 2.1 complete

**Steps**: Similar to AWS RDS with Azure provider

---

#### Task 2.3: Migrate GCP Cloud SQL PostgreSQL
**Owner**: Platform Team
**Duration**: 5 hours
**Dependencies**: Task 2.2 complete

---

#### Task 2.4: Migrate Redis Caches (All Providers)
**Owner**: Platform Team
**Duration**: 4 hours total
**Dependencies**: Database migration complete

**Steps**: Follow same pattern for:
- AWS ElastiCache
- Azure Redis Cache
- GCP Memorystore

---

#### Category 2 Validation
- [ ] All databases accessible from applications
- [ ] Connection rotation/secrets working
- [ ] Backup/restore verified
- [ ] Failover tested (if multi-AZ)
- [ ] No connection errors in application logs

---

### Category 3: Networking (Week 5)

**WARNING**: Highest risk category - affects connectivity

#### Task 3.1: Migrate VPCs (Last Networking Resource)
**Owner**: Platform Team
**Duration**: 8 hours
**Dependencies**: All compute resources exist (EKS/AKS/GKE)

**Strategy**: **DO NOT MIGRATE VPCs** unless absolutely necessary
- VPCs are foundational; recreating causes downtime
- Keep VPCs in Terraform if they're stable
- Only migrate if VPC configuration needs changes

**If migration required**:
1. Create Compositions for VPC with subnets, route tables, IGWs
2. **Blue-green approach**: Create new VPC, migrate resources gradually
3. Update subnet references in all other resources (EKS, RDS, etc.)
4. Migrate resources to new VPC one by one
5. Delete old VPC from Terraform

**Recommendation**: Keep VPCs in Terraform for now, revisit later if needed

---

#### Task 3.2: Migrate Load Balancers
**Owner**: Platform Team
**Duration**: 6 hours
**Dependencies**: Applications deployed and tested

**Steps**:
1. AWS ALB → `loadbalancers.elb.aws.crossplane.io/v1beta1`
2. Azure Application Gateway → `applicationgateways.networking.azure.upbound.io/v1beta1`
3. GCP Cloud Load Balancer → `globaladdresses.networking.gcp.upbound.io/v1beta1`

**Concerns**:
- Public IP addresses may change → DNS updates needed
- TLS certificates managed differently
- Health checks must be preserved

**Safe Migration**:
1. Create Crossplane load balancer **alongside** Terraform one
2. Test Crossplane LB with staging environment
3. Switch DNS to Crossplane LB (TTL set low beforehand)
4. Verify traffic flowing correctly
5. Delete old Terraform LB
6. Import Crossplane LB into Terraform state (prevent destroy)

---

### Category 4: Kubernetes Clusters (Week 6)

#### Task 4.1: Migrate EKS (AWS)
**Owner**: Platform Team
**Duration**: 8-12 hours (most complex)
**Dependencies**: All other resources migrated, networking stable

**Strategy**: **Adopt existing EKS cluster into Crossplane management**
1. Create XRD for EKS clusters
2. Create Composition that creates full EKS cluster
3. **For existing cluster**: Use `external` resource adoption
   ```yaml
   apiVersion: eks.aws.crossplane.io/v1beta1
   kind: Cluster
   metadata:
     name: existing-eks-cluster
   spec:
     resourceRef:
       apiVersion: eks.aws.crossplane.io/v1beta1
       kind: Cluster
       name: ${TF_STATE_CLUSTER_NAME}  # from Terraform state
     deletionPolicy: Orphan  # Prevent Crossplane from deleting
   ```
4. Crossplane "manages" existing cluster (can update tags, etc.)
5. Import into Terraform state with `prevent_destroy`
6. **Future new clusters**: Create fully via Crossplane

**Validation**:
- [ ] Crossplane shows EKS cluster as `READY: True`
- [ ] Can update cluster via Crossplane (add tag)
- [ ] Terraform shows no diff for EKS resource

---

#### Task 4.2: Migrate AKS (Azure)
**Owner**: Platform Team
**Duration**: 8-10 hours
**Dependencies**: Task 4.1 complete

**Pattern**: Same external resource adoption

---

#### Task 4.3: Migrate GKE (GCP)
**Owner**: Platform Team
**Duration**: 8-10 hours
**Dependencies**: Task 4.2 complete

---

#### Category 4 Validation
- [ ] All three Kubernetes clusters show as managed by Crossplane
- [ ] Crossplane can read cluster status, endpoint, version
- [ ] No Terraform drift detected for clusters
- [ ] Cluster add-ons (monitoring, logging) still working

---

## Phase 2: Orchestration Migration (Week 7)

### Task 2.1: Update Multi-Cloud Orchestrator Python Skill
**Owner**: AI Skills Team
**Duration**: 16 hours
**Dependencies**: All infrastructure migrated

**File**: `core/ai/skills/manage-infrastructure/scripts/multi_cloud_orchestrator.py`

**Changes**:
1. Remove boto3, azure-mgmt, google-cloud imports
2. Add Kubernetes client
   ```python
   from kubernetes import client, config
   config.load_kube_config()
   custom_api = client.CustomObjectsApi()
   ```
3. Replace `create_vm`, `create_bucket` methods with Crossplane resource creation
   ```python
   def create_eks_cluster(self, name, region, version):
       resource = {
           "apiVersion": "eks.aws.crossplane.io/v1beta1",
           "kind": "Cluster",
           "metadata": {"name": name},
           "spec": {
               "forProvider": {
                   "region": region,
                   "version": version
               }
           }
       }
       self.custom_api.create_namespaced_custom_object(
           group="eks.aws.crossplane.io",
           version="v1beta1",
           namespace="default",
           plural="clusters",
           body=resource
       )
   ```
4. Replace `list_vms` with `list` across all provider resource kinds
5. Replace `get_costs` with Crossplane cost metrics (if available) or continue using Cost Explorer API (read-only)
6. Replace `optimize_resource_placement` with Crossplane `ResourceClass` selection logic
7. Keep orchestration strategies (parallel, sequential, rolling) - these are workflow logic, not cloud-specific

**Testing**:
- [ ] All orchestrator methods work with Crossplane APIs
- [ ] Can create EKS, RDS, Redis via orchestrator
- [ ] Parallel execution still works
- [ ] Rollback logic functions

---

### Task 2.2: Update Multi-Cloud Scatter-Gather Temporal Workflow
**Owner**: AI Skills Team
**Duration**: 12 hours
**Dependencies**: Task 2.1 complete

**File**: `overlay/ai/skills/complete-hub-spoke-temporal/workflows/multi-cloud-scatter-gather.go`

**Changes**:
1. Remove per-cloud provider activities (AWS, Azure, GCP specific)
2. Replace with unified Crossplane query activity
   ```go
   func (a *SkillExecutionActivities) QueryCrossplaneResources(ctx context.Context, claimName string) (map[string]interface{}, error) {
       // Get all managed resources with label crossplane.io/composite=<claimName>
       resourceList := &unstructured.UnstructuredList{}
       err := a.dynamicClient.Resource(schema.GroupVersionResource{
           Group:   "eks.aws.crossplane.io",
           Version: "v1beta1",
           Resource: "clusters",
       }).Namespace("default").List(ctx, metav1.ListOptions{
           LabelSelector: fmt.Sprintf("crossplane.io/composite=%s", claimName),
       })
       // Repeat for other resource types
       return aggregateResources(resourceList), nil
   }
   ```
3. Keep scatter/gather pattern, but gather from Crossplane instead of cloud APIs
4. Consensus building remains the same (now on Crossplane resource statuses)
5. Recommendations based on Crossplane observed generations and health

**Testing**:
- [ ] Workflow can query Crossplane resources
- [ ] Aggregates statuses correctly across providers
- [ ] Recommendations generated based on Crossplane observations

---

### Task 2.3: Update Multi-Cloud Abstraction Layer (JavaScript)
**Owner**: AI Skills Team
**Duration**: 8 hours
**Dependencies**: Task 2.2 complete

**File**: `core/multi-cloud-abstraction.js`

**Changes**:
1. Replace AWS, GCP, Azure SDKs with `kubectl` or Kubernetes API client
   ```javascript
   const { exec } = require('child_process');
   class CrossplaneAbstractionLayer {
     async createResource(composition, params) {
       const yaml = this.buildXResource(composition, params);
       const result = await this.runKubectl('apply', yaml);
       return this.waitForReady(extractName(yaml), composition);
     }
     async runKubectl(action, yaml) {
       return new Promise((resolve, reject) => {
         const proc = exec(`kubectl ${action} -f - --output=json`, { input: yaml });
         proc.stdout.on('data', (data) => resolve(JSON.parse(data)));
         proc.stderr.on('data', (data) => reject(new Error(data)));
       });
     }
   }
   ```
2. Keep orchestration logic (failover, optimization) but read from Crossplane
3. Metrics: Read from Crossplane pod metrics endpoint
4. Status: Query Crossplane resources instead of cloud APIs

**Testing**:
- [ ] `listVMs()` returns list of all Compute/Node resources across providers
- `createFailoverPlan()` uses Crossplane compositions to define topology
- [ ] `optimizeResourcePlacement()` reads ResourceClasses
- [ ] Cost estimation uses Crossplane cost insights (or fallback)

---

## Phase 3: Decommission Terraform (Week 8)

### Task 3.1: Audit Terraform State
**Owner**: Platform Team
**Duration**: 4 hours
**Dependencies**: Phase 2 complete

**Steps**:
1. List all resources in Terraform state
   ```bash
   terraform state list > terraform-resources.txt
   ```
2. Categorize by provider and type
3. Identify any resources **NOT** yet migrated
4. For each migrated resource, verify Crossplane is managing it
   ```bash
   # Compare Terraform list with Crossplane resource list
   kubectl get rdsinstances.database.aws,eksclusters.platform.aws... --all-namespaces -o name
   ```
5. Create reconciliation spreadsheet:
   | Resource Type | Terraform Count | Crossplane Count | Status |
   |---------------|-----------------|------------------|--------|
   | EKS clusters  | 3               | 3                | ✅Migrated |
   | RDS instances| 2               | 2                | ✅Migrated |
   | VPCs         | 5               | 0                | ❌Not migrating |

**Decision Point**:
- < 5% resources unmigrated → proceed with manual migration
- > 5% unmigrated → extend Phase 2, don't proceed to decommission

---

### Task 3.2: Import Crossplane Resources to Terraform (Read-Only)
**Owner**: Platform Team
**Duration**: 8 hours
**Dependencies**: Task 3.1 complete, all resources migrated

**Steps**:
For each Crossplane-managed resource:

1. Get resource ID from Crossplane
   ```bash
   kubectl get rdsinstance/db-name -o jsonpath='{.status.atProvider.id}'
   ```
2. Import into Terraform state (module path varies)
   ```bash
   terraform import 'module.rds.aws_db_instance.this["0"]' ${resource_id}
   ```
3. Mark resource as `prevent_destroy` in Terraform configuration
   ```hcl
   resource "aws_db_instance" "this" {
     # ... existing config ...
     lifecycle {
       prevent_destroy = true
     }
   }
   ```
4. Remove resource from Terraform configuration **file** (but keep in state)
   - Comment out or delete the resource block
   - Keep commented version for reference
5. Run `terraform plan` - should show **no changes** for that resource
6. Repeat for all resources (script this!)

**Automation Script**:
```bash
#!/bin/bash
# import-crossplane-to-terraform.sh
RESOURCE_TYPES=(
  "aws_db_instance"
  "aws_eks_cluster"
  "aws_s3_bucket"
  # ...
)

for type in "${RESOURCE_TYPES[@]}"; do
  echo "Importing $type..."
  # Get resources of this type from Crossplane
  # For each, run terraform import
done
```

---

### Task 3.3: Archive Terraform State and Decommission
**Owner**: Platform Team
**Duration**: 2 hours
**Dependencies**: Task 3.2 complete

**Steps**:
1. Archive Terraform state files
   ```bash
   tar -czf terraform-state-backup-$(date +%Y%m%d).tar.gz \
     core/infrastructure/terraform/*/terraform.tfstate*
   aws s3 cp terraform-state-backup-$(date +%Y%m%d).tar.gz \
     s3://ai-infrastructure-portal-terraform-backups/
   ```
2. Remove Terraform directories **but keep backup referenced in docs**
   ```bash
   # DO NOT rm -rf yet! Move to archive location
   mkdir -p archived/terraform-$(date +%Y%m%d)
   mv core/infrastructure/terraform/ archived/
   ```
3. Update `README.md` and architecture docs to reflect Crossplane
4. Remove Terraform from CI/CD pipelines
   - Remove Terraform workflow files
   - Remove Terraform linting steps
   - Remove Terraform plan/apply jobs
5. Remove Terraform dependencies from `pyproject.toml` / `go.mod` / `package.json`
6. Update all skill `SKILL.md` files to reference Crossplane instead of Terraform

**Verification**:
- [ ] No Terraform workflows in GitHub Actions
- [ ] No Terraform CLI usage in deployments
- [ ] Crossplane is sole source of truth

---

### Task 3.4: Monitoring and Documentation Cleanup
**Owner**: Platform Team
**Duration**: 4 hours
**Dependencies**: Task 3.3 complete

**Steps**:
1. Update Prometheus/Grafana dashboards
   - Remove Terraform state metrics
   - Add Crossplane composition reconciliation metrics
   - Add ManagedResource health metrics
2. Update alerting rules
   - Replace Terraform drift alerts with Crossplane drift alerts
   - Add Crossplane provider health alerts
3. Update runbooks
   - Remove Terraform troubleshooting sections
   - Add Crossplane troubleshooting:
     - Composition stuck
     - ProviderConfig auth failures
     - Resource drift detection
4. Update architecture diagrams
   - Replace Terraform boxes with Crossplane
   - Show XRD/Composition flow
   - Show RBAC boundaries
5. Update README.md with Crossplane setup instructions
6. Create "Crossplane CLI Cheatsheet" for developers

---

## Post-Migration: Stabilization (Weeks 9-12)

### Monitoring Checklist (Daily)

- [ ] Crossplane pods healthy (no restarts)
- [ ] ProviderConfigs READY: True
- [ ] Compositions reconciling within SLA (< 15 min for EKS, < 5 min for others)
- [ ] No RBAC violation alerts
- [ ] No resource drift alerts > 5% of resources
- [ ] API server latency < 100ms
- [ ] etcd storage growth < 10% per week

### Weekly Review

1. **Crossplane logs review**: Check for errors, warnings
2. **Resource drift report**: Any external modifications?
3. **Cost analysis**: Are costs as expected? Any anomalies?
4. **Performance metrics**: Composition times, reconciliation durations
5. **Team feedback**: Any pain points with new workflow?

### Monthly Deep Dive

1. **RBAC audit**: Review who has access to what provider configurations
2. **Provider credential rotation**: Rotate AWS/Azure/GCP keys/credentials
3. **Crossplane upgrade**: Test and apply minor version upgrades
4. **Cost optimization**: Review ResourceClass usage, right-size instances
5. **Documentation update**: Keep docs current with latest practices

---

## Success Criteria

| Metric | Target | Measurement |
|--------|-------|-------------|
| EKS cluster provisioning time | < 15 minutes | Composition reconciliation duration |
| Resource drift incidents | < 1/month | Alert count |
| GitOps pipeline success rate | > 99% | CI/CD job success rate |
| Developer onboarding time | < 1 week | Time to first deployment |
| Infra-as-code review time | < 2 hours | PR review to merge |
| Multi-cloud deployment consistency | 100% | Same resource definition works across providers |

---

## Rollback Triggers

**Immediate Rollback** if:
- Crossplane unavailable > 30 minutes
- Data loss or corruption
- Application downtime > 5 minutes due to Crossplane issues
- Critical security vulnerability in Crossplane

**Rollback Procedure**:
1. Stop all new Crossplane compositions
2. Terraform import all Crossplane-managed resources (use script)
3. Remove Crossplane from cluster (keep backup)
4. Resume Terraform deployments
5. Investigate root cause

**Rollback Timeline**:
- < 1 hour: Mitigation (stop Crossplane, switch to Terraform)
- < 4 hours: Import critical resources
- < 24 hours: Full import and validation
- 1 week: Root cause analysis and remediation

---

## Appendix: Migration Scripts

### Script 1: List All Terraform Resources
```bash
#!/bin/bash
# terraform-resource-inventory.sh
cd core/infrastructure/terraform/aws
terraform state list | awk '{print "aws:"$0}' > /tmp/tf-resources.txt
cd ../azure
terraform state list | awk '{print "azure:"$0}' >> /tmp/tf-resources.txt
cd ../gcp
terraform state list | awk '{print "gcp:"$0}' >> /tmp/tf-resources.txt
echo "Total $(wc -l /tmp/tf-resources.txt) resources"
```

### Script 2: Check Crossplane Resource Parity
```bash
#!/bin/bash
# crossplane-parity-check.sh
kubectl get rdsinstances.database.aws,eksclusters.platform.aws..., \
  postgresqlinstances.database.azure..., \
  redisinstances.cache.gcp... \
  --all-namespaces -o name | wc -l
echo "Crossplane-managed resources"
```

### Script 3: Bulk Import to Terraform (One-Time)
```bash
#!/bin/bash
# bulk-terraform-import.sh
while read resource_type resource_id; do
  echo "Importing $resource_type ($resource_id) into Terraform..."
  # Map Crossplane resource to Terraform address (this mapping is complex)
  # Requires Terraform state import with correct module path
  # Example: terraform import 'module.rds.aws_db_instance.this["0"]' ${resource_id}
done < /tmp/crossplane-resources-to-import.txt
```

---

## Contact & Escalation

**Migration Lead**: [Platform Team]
**24/7 Support**: [On-call rotation]
**Escalation**: Stop migration, revert to Terraform, involve architect

---

*Document version: 1.0*
*Last updated: 2026-03-20*

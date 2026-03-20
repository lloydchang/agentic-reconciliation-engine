# Crossplane Infrastructure Platform

This directory contains the complete Crossplane configuration for managing multi-cloud infrastructure (AWS, Azure, GCP) as Kubernetes native resources.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Git Repository (this directory)            │
│  Contains: XRDs, Compositions, ProviderConfigs, RBAC      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Flux/ArgoCD syncs continuously
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Kubernetes Cluster (Control Plane)            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Crossplane Pod                      │   │
│  │  (Reconciles XResources → Cloud Provider Resources) │   │
│  └─────────────────────────────────────────────────────┘   │
│         │              │              │                     │
│         ▼              ▼              ▼                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │   AWS    │  │  Azure   │  │   GCP    │                │
│  │ Provider │  │ Provider │  │ Provider │                │
│  └──────────┘  └──────────┘  └──────────┘                │
│         │              │              │                     │
│         ▼              ▼              ▼                     │
│  EC2, RDS,  AKS, Postgres,  GKE, Cloud                   │
│  VPC, etc.  AppGw, etc.  SQL, etc.                       │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
core/crossplane/
├── providers/                    # Cloud provider credentials
│   ├── aws-provider-config.yaml # AWS ProviderConfig + Secret
│   ├── azure-provider-config.yaml
│   ├── gcp-provider-config.yaml
│   └── README.md
├── rbac/                         # Multi-tenant isolation
│   ├── teams-sa.yaml            # ServiceAccounts for teams
│   ├── team-a-role.yaml         # AWS-only access
│   ├── team-b-role.yaml         # Azure-only access
│   ├── team-c-role.yaml         # Multi-cloud access
│   ├── cluster-admin-roles.yaml # Platform admin roles
│   ├── network-policies.yaml    # Pod-to-cloud API access
│   └── README.md
├── compositions/                 # Infrastructure patterns
│   ├── aws-eks-cluster/
│   │   ├── xrd-eks.yaml
│   │   └── composition.yaml
│   ├── aws-rds-postgresql/
│   │   ├── xrd-rds.yaml
│   │   └── composition.yaml
│   ├── shared-storage/
│   │   ├── xrd-s3.yaml
│   │   └── composition-s3.yaml
│   ├── azure-aks-cluster/
│   │   ├── xrd-aks.yaml
│   │   └── composition-aks.yaml
│   ├── azure-postgresql/
│   │   ├── xrd-postgres-azure.yaml
│   │   └── composition-postgres-azure.yaml
│   ├── gcp-gke-cluster/
│   │   ├── xrd-gke.yaml
│   │   └── composition-gke.yaml
│   ├── gcp-cloudsql-postgresql/
│   │   ├── xrd-cloudsql.yaml
│   │   └── composition-cloudsql.yaml
│   ├── gcp-memorystore/
│   │   ├── xrd-redis-gcp.yaml
│   │   └── composition-redis-gcp.yaml
│   └── README.md                # Detailed composition reference
├── environments/                 # Environment-specific overlays
│   ├── dev/
│   ├── staging/
│   └── prod/
├── example-claims.yaml          # Sample claims for teams
├── gitops-sync.yaml             # Flux/ArgoCD sync configuration
└── README.md                    # This file

# Optional: If using Kustomize with environments
#   environments/prod/kustomization.yaml
#   environments/prod/patches/
#         patches for production-specific values (e.g., larger instances)
```

## Key Concepts

### 1. ProviderConfigs
Cluster-scoped resources that store cloud credentials.
- **Location**: `crossplane-system` namespace
- **Access**: Only cluster admins can view/modify
- **Reference**: Compositions reference these to authenticate to clouds

### 2. CompositeResourceDefinition (XRD)
Defines the schema (API) that teams use to request infrastructure.
- **Example**: `EKSClusterClaim` with fields: region, version, nodeGroups
- **Claim**: What teams create in their namespace
- **XR**: What Crossplane creates to represent the composed resource

### 3. Composition
Defines HOW to satisfy a claim - which cloud resources to create and how to wire them together.
- Composes multiple managed resources (VPC, subnets, EKS cluster, node groups)
- Uses patches to pass values from claim to resource specs
- Can be environment-specific (dev vs prod use different instance types)

### 4. RBAC Isolation
Teams only see their own claims and the resources they're allowed to create.
- **Team A**: AWS-only (EKS, RDS, S3, VPC)
- **Team B**: Azure-only (AKS, PostgreSQL, Redis, VNet)
- **Team C**: Multi-cloud (any resource)
- **Platform Admins**: Full access to ProviderConfigs and Crossplane system

## Getting Started

### Prerequisites

- Kubernetes cluster v1.24+
- `kubectl` configured with cluster-admin access
- GitOps operator installed (Flux or ArgoCD)
- Cloud provider credentials (AWS, Azure, GCP)

### Step 1: Install Crossplane

```bash
# Add Helm repo
helm repo add crossplane-stable https://charts.crossplane.io/stable
helm repo update

# Install Crossplane
kubectl create namespace crossplane-system
helm install crossplane crossplane-stable/crossplane \
  --namespace crossplane-system \
  --set rbac.manager=true \
  --wait
```

Verify:
```bash
kubectl get pods -n crossplane-system
kubectl get providers.pkg.crossplane.io
```

### Step 2: Install Provider Packages

```bash
# AWS provider (v0.35.0+)
kubectl get pkg -n crossplane-system  # Find the installed provider-aws version
kubectl install provider-aws <version> --namespace crossplane-system

# Azure provider
kubectl install provider-azure <version> --namespace crossplane-system

# GCP provider
kubectl install provider-gcp <version> --namespace crossplane-system
```

Wait for all providers to show `HEALTHY: True`:
```bash
kubectl get providers.pkg.crossplane.io -w
```

### Step 3: Configure Provider Credentials

Edit the provider config files with your actual credentials, then apply:

```bash
# Store AWS credentials as a secret
kubectl create secret generic aws-creds \
  --namespace crossplane-system \
  --from-file=key=./secrets/aws-credentials \
  --dry-run=client -o yaml | kubectl apply -f -

# Repeat for Azure and GCP

# Apply ProviderConfigs
kubectl apply -f providers/
```

Verify:
```bash
kubectl get providerconfigs.aws.crossplane.io
kubectl get providerconfigs.azure.crossplane.io
kubectl get providerconfigs.gcp.crossplane.io
# All should show READY: True
```

### Step 4: Set Up RBAC

```bash
# Create team namespaces
kubectl create namespace team-a
kubectl create namespace team-b
kubectl create namespace team-c

# Apply RBAC configurations
kubectl apply -f rbac/teams-sa.yaml
kubectl apply -f rbac/team-a-role.yaml
kubectl apply -f rbac/team-b-role.yaml
kubectl apply -f rbac/team-c-role.yaml

# Apply cluster admin roles (for platform team)
kubectl apply -f rbac/cluster-admin-roles.yaml

# Apply network policies
kubectl apply -f rbac/network-policies.yaml
```

Test RBAC:
```bash
# Team A should not be able to list Azure resources
kubectl auth can-i list kubernetesclusters.platform.azure \
  --as=system:serviceaccount:team-a:team-a-sa  # Should return "no"
```

### Step 5: Install Compositions

```bash
# Apply all XRDs and Compositions
kubectl apply -f compositions/aws-eks-cluster/
kubectl apply -f compositions/aws-rds-postgresql/
kubectl apply -f compositions/shared-storage/
kubectl apply -f compositions/azure-aks-cluster/
kubectl apply -f compositions/azure-postgresql/
kubectl apply -f compositions/gcp-gke-cluster/
kubectl apply -f compositions/gcp-cloudsql-postgresql/
kubectl apply -f compositions/gcp-memorystore/
```

Verify:
```bash
kubectl get xrds.apiextensions.crossplane.io
kubectl get compositions.apiextensions.crossplane.io
# All should show established
```

### Step 6: Deploy via GitOps (Flux/ArgoCD)

**Using Flux**:
```bash
flux create source git crossplane-config \
  --url=ssh://git@github.com/yourorg/agentic-reconciliation-engine \
  --branch=main \
  --interval=5m \
  --secret-format=gpg

flux create kustomization crossplane-resources \
  --source=crossplane-config \
  --path="./core/crossplane" \
  --prune=true \
  --interval=5m
```

**Using ArgoCD**:
```bash
kubectl apply -f gitops-sync.yaml
```

Flux/ArgoCD will automatically apply all Crossplane configurations and keep them in sync with the repository.

---

## How Teams Request Infrastructure

Team members **DO NOT** create Crossplane resources directly (usually). They create **Claims** in their namespace:

```yaml
# File: team-a-claims.yaml
apiVersion: platform.aws.ecs.azure/v1alpha1
kind: EKSClusterClaim
metadata:
  name: my-app-cluster
  namespace: team-a
spec:
  region: us-west-2
  version: "1.28"
  nodeGroups:
    - name: general
      instanceTypes: ["t3.medium"]
      minSize: 2
      maxSize: 5
```

Apply in team namespace:
```bash
kubectl apply -f team-a-claims.yaml
```

Crossplane will:
1. Reconcile the Claim
2. Create required resources (VPC, subnets, EKS cluster, node groups)
3. Create connection secrets in `team-a` namespace
4. Mark Claim as `READY: True`

---

## Viewing and Managing Resources

### List all managed resources

```bash
# All Crossplane resources cluster-wide
kubectl get managed -A

# Filter by provider
kubectl get managed -A | grep eks
kubectl get managed -A | grep rds
```

### Check claim status

```bash
# In team namespace
kubectl get eksclusterclaims.platform.aws.ecs.azure -n team-a
kubectl describe eksclusterclaim my-app-cluster -n team-a

# See which resources were created
kubectl get eksclusters.platform.aws.ecs.azure -o wide
kubectl get vpcs.networking.aws.crossplane.io
```

### View connection secrets

```bash
# Connection secret contains kubeconfig, endpoint, etc.
kubectl get secret my-app-cluster-conn -n team-a -o yaml
```

### Debug failed compositions

```bash
# Check composition logs
kubectl logs -n crossplane-system deployment/crossplane -c crossplane

# Check resource status
kubectl get rdsinstance/database-name -o yaml | grep -A 20 status

# See last observed generation (LoG) for reconciliation errors
kubectl get rdsinstance database-name -o jsonpath='{.status.conditions[?(@.type=="Ready")]}'
```

---

## Cost Management

### ResourceClasses for Cost Control

Define ResourceClasses to standardize instance types and enforce budgets:

```yaml
apiVersion: compute.crossplane.io/v1alpha1
kind: ResourceClass
metadata:
  name: dev-compute-class
spec:
  poolRef:
    name: dev-pool
  description: "Development environment - cost-optimized"
  allowedResources:
  - name: eks.t3.medium
  - name: rds.db.t3.small
```

Then, in Compositions:

```yaml
resources:
- name: eks-cluster
  base:
    # ...
  patches:
  - type: FromClassFieldPath
    fromFieldPath: spec.resourceClassName
    toFieldPath: spec.forProvider.instanceType
```

### Cost Monitoring

Crossplane exposes cost metrics (if provider supports it). Integrate with Prometheus:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: crossplane-metrics
  namespace: crossplane-system
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: crossplane
  endpoints:
  - port: metrics
    interval: 30s
```

---

## Operations

### Upgrade Crossplane

```bash
# Check current version
kubectl get pod -n crossplane-system -l app=crossplane -o jsonpath='{.items[0].spec.containers[0].image}'

# Upgrade via Helm
helm upgrade crossplane crossplane-stable/crossplane \
  --namespace crossplane-system \
  --version <new-version> \
  --wait
```

### Upgrade Providers

```bash
# Get current provider versions
kubectl get providers.pkg.crossplane.io -o wide

# Install newer version (can have multiple versions side-by-side)
kubectl install provider-aws <new-version> --namespace crossplane-system

# Update ProviderConfig to use new version (spec.upgradePolicy)
# Delete old provider package after migration
```

### Backup and Restore

Crossplane resources are stored in Kubernetes etcd. Ensure you have:
- Regular etcd snapshots
- Crossplane Configuration backups (all XRDs, Compositions, ProviderConfigs in Git)

Restore procedure:
1. Restore etcd from snapshot
2. Re-apply all Crossplane configurations from Git (they are declarative)
3. Crossplane will reconcile state back to desired configuration

---

## Troubleshooting

### ProviderConfig not ready

```bash
kubectl describe providerconfig aws-provider
# Check for: Invalid credentials, missing secret, permission errors
```

### Composition stuck in reconciling

```bash
# Check managed resource status
kubectl get managed -A
kubectl describe <resource-kind>/<resource-name>

# Check Crossplane pod logs
kubectl logs -n crossplane-system deployment/crossplane -c crossplane --tail=100

# Look for: "Composite resource is not ready" and check conditions
```

### RBAC permission denied

```bash
# Check which user/SA is attempting operation
kubectl auth can-i create eksclusters.eks.aws.crossplane.io \
  --as=system:serviceaccount:team-a:team-a-sa \
  --namespace=team-a

# Review Role and RoleBinding
kubectl get role,rolebinding -n team-a
```

### Resource drift (modified outside Crossplane)

Crossplane can detect drift and either:
- Reconcile back to spec (default behavior)
- Notify via conditions/events

To make drift visible:
```bash
kubectl get <resource> -o yaml | grep observed-generation
# If observed-generation < metadata.generation, drift exists
```

---

## References

- [Crossplane Official Documentation](https://docs.crossplane.io)
- [Upbound Provider Documentation](https://marketplace.upbound.io)
- [Crossplane RBAC Guide](https://docs.crossplane.io/latest/concepts/rbac/)
- [Composition Best Practices](https://docs.crossplane.io/latest/concepts/compositions/)
- [GitOps with Crossplane](https://docs.crossplane.io/latest/tutorials/gitops/)

---

## Migration from Terraform

See separate documentation:
- `docs/CROSSPLANE-MIGRATION-STRATEGY.md` - Strategic overview
- `docs/CROSSPLANE-IMPLEMENTATION-PLAN.md` - Step-by-step migration

**Key points**:
1. Run Terraform and Crossplane in parallel initially
2. Import Crossplane-managed resources into Terraform state as read-only
3. Use `prevent_destroy` lifecycle in Terraform
4. Remove resources from Terraform config after import
5. Decommission Terraform once all resources migrated

---

*Document version: 1.0*
*Last updated: 2026-03-20*

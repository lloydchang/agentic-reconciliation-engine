# Crossplane RBAC and Network Isolation

This directory contains Role-Based Access Control (RBAC) configurations and Network Policies for securing Crossplane in a multi-tenant environment.

## RBAC Model

### Core Principles

1. **ProviderConfigs are cluster-scoped**: Only platform admins can create/modify ProviderConfigs
2. **Team isolation via namespaces**: Each team gets their own Kubernetes namespace
3. **ServiceAccounts per team**: Teams use dedicated SAs for CI/CD and operators
4. **Role-based permissions**: Grant minimum necessary permissions per team
5. **Resource-level restrictions**: Teams can only access their provider's resources

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Cluster-wide                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ProviderConfigs (cluster-scoped, admin-only)       │   │
│  │  • aws-provider  • azure-provider  • gcp-provider   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ referenced by
                            ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Team A    │  │   Team B    │  │   Team C    │
│  Namespace  │  │  Namespace  │  │  Namespace  │
│             │  │             │  │             │
│  SA: team-a │  │  SA: team-b │  │  SA: team-c │
│  Role: AWS  │  │  Role: Azure│  │  Role: All  │
│             │  │             │  │             │
│  Can create │  │  Can create │  │  Can create │
│  EKS, RDS   │  │  AKS, SQL   │  │  Any resource│
│             │  │             │  │             │
│  Cannot see │  │  Cannot see │  │  Can see    │
│  Azure/GCP  │  │  AWS/GCP    │  │  Everything │
└─────────────┘  └─────────────┘  └─────────────┘
```

## Components

### 1. ServiceAccounts (`teams-sa.yaml`)

Creates dedicated service accounts for each team:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: team-a-sa
  namespace: team-a
```

These SAs are used by:
- CI/CD pipelines to deploy infrastructure
- Crossplane claim creation from team namespaces
- Any operator/service that provisions resources on behalf of the team

### 2. Team Roles (`team-*-role.yaml`)

Role scopes permissions to a specific namespace and defines what Crossplane resources can be created.

**Team A (AWS-only)**:
- Can create: EKS clusters, RDS instances, ElastiCache, S3 buckets, VPCs, subnets, security groups, load balancers
- Cannot create: Any Azure or GCP resources
- Provider reference: aws-provider

**Team B (Azure-only)**:
- Can create: AKS clusters, PostgreSQL Flexible, Redis Cache, Storage Accounts, VNets, subnets, Application Gateway
- Cannot create: Any AWS or GCP resources
- Provider reference: azure-provider

**Team C (Multi-cloud)**:
- Can create all resources from all providers
- For multi-cloud topologies that span AWS, Azure, GCP
- Can reference all three provider configs

### 3. RoleBindings (`team-*-binding.yaml`)

Associates ServiceAccounts with Roles. This binds `team-a-sa` to `team-a-crossplane-role` in the `team-a` namespace.

### 4. Cluster-wide Admin Roles (`cluster-admin-roles.yaml`)

For platform team members who need to:
- Create/modify ProviderConfigs
- Install/upgrade Crossplane provider packages
- Create XRDs and Compositions
- Troubleshoot across all namespaces

**Usage**:
```bash
# Add user to platform-admins group
kubectl create clusterrolebinding platform-admin-binding \
  --clusterrole=crossplane-provider-admin \
  --group=platform-admins
```

### 5. Network Policies (`network-policies.yaml`)

Restricts Crossplane pod network access to:
- **Cloud provider APIs**: Only egress to known IP ranges for AWS, Azure, GCP APIs
- **Kubernetes API server**: Required for Crossplane to function
- **DNS**: For resolving cloud provider endpoints

Blocks:
- All other internet egress
- Access from pods outside crossplane-system namespace
- Lateral movement from compromised Crossplane pods

## Setup Instructions

### Step 1: Create Team Namespaces

```bash
kubectl create namespace team-a
kubectl create namespace team-b
kubectl create namespace team-c
kubectl create namespace crossplane-system
```

### Step 2: Apply ServiceAccounts

```bash
kubectl apply -f teams-sa.yaml
```

### Step 3: Apply Team Roles and Bindings

```bash
kubectl apply -f team-a-role.yaml
kubectl apply -f team-b-role.yaml
kubectl apply -f team-c-role.yaml
```

### Step 4: Apply Cluster Admin Roles (for platform team)

```bash
# First, create platform-admins group in your Kubernetes cluster
# This depends on your authentication provider (LDAP, OIDC, etc.)
# Example with static user:
kubectl create clusterrolebinding platform-admin-binding \
  --clusterrole=crossplane-provider-admin \
  --user=admin@example.com

# Or for a group (OIDC):
kubectl create clusterrolebinding platform-admin-binding \
  --clusterrole=crossplane-provider-admin \
  --group="platform-admins"
```

### Step 5: Apply Network Policies

```bash
kubectl apply -f network-policies.yaml
```

### Step 6: Verify RBAC

```bash
# As team-a, should be able to list AWS resources
kubectl auth can-i list eksclusters.eks.aws.crossplane.io \
  --as=system:serviceaccount:team-a:team-a-sa
# Expected: yes

# As team-a, should NOT be able to list Azure resources
kubectl auth can-i list kubernetesclusters.platform.azure.upbound.io \
  --as=system:serviceaccount:team-a:team-a-sa
# Expected: no

# As platform admin, should be able to get providerconfigs
kubectl auth can-i get providerconfigs.aws.crossplane.io \
  --as=system:serviceaccount:crossplane-system:crossplane
# Expected: yes (Crossplane itself)
```

## Resource Access Matrix

| Resource Type | Team A | Team B | Team C | Platform Admin |
|---------------|--------|--------|--------|---------------|
| AWS ProviderConfig | ❌ No | ❌ No | ❌ No | ✅ Yes |
| Azure ProviderConfig | ❌ No | ❌ No | ❌ No | ✅ Yes |
| GCP ProviderConfig | ❌ No | ❌ No | ❌ No | ✅ Yes |
| EKS clusters | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| AKS clusters | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| GKE clusters | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| RDS instances | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| PostgreSQL (Azure) | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| Cloud SQL (GCP) | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| ElastiCache | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| Redis Cache (Azure) | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| Memorystore (GCP) | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| S3 buckets | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| Storage (Azure) | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| Cloud Storage (GCP) | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| VPCs | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |

## Crossplane-Specific Considerations

### ProviderConfig Usage

If you want even finer-grained control, use `ProviderConfigUsage` resources to restrict which ProviderConfig a given resource can use:

```yaml
apiVersion: aws.crossplane.io/v1beta1
kind: ProviderConfigUsage
metadata:
  name: aws-provider-usage
spec:
  providerConfigRef:
    name: aws-provider
```

This allows you to define which ProviderConfig is used by resources in a given namespace or by a given service account.

### Composition RBAC

XRDs and Compositions are typically cluster-scoped. Platform admins manage them. Application teams consume them via Claims.

If you want teams to own their own Compositions, you can create namespace-scoped Compositions:

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: my-eks-composition
  namespace: team-a  # Namespaced composition
```

Then the team's Role needs permission to create Compositions in their namespace.

## Troubleshooting

### Team cannot create resources

```bash
# Check if Role and RoleBinding exist
kubectl get role,rolebinding -n team-a

# Check RBAC rules
kubectl describe role team-a-crossplane-role -n team-a

# Test authorization
kubectl auth can-i create eksclusters.eks.aws.crossplane.io \
  --as=system:serviceaccount:team-a:team-a-sa \
  --namespace=team-a
```

### ProviderConfig not accessible

ProviderConfigs are cluster-scoped. Ensure:
- ProviderConfig exists in `crossplane-system` namespace
- ProviderConfig has correct credentials
- Crossplane pod logs show no authentication errors
- Network policies allow Crossplane to reach cloud APIs

### NetworkPolicy blocking Crossplane

If Crossplane can't reach cloud APIs:

```bash
# Check network policy
kubectl describe networkpolicy -n crossplane-system

# Check Crossplane pod logs for connection errors
kubectl logs -n crossplane-system -l app=crossplane

# Temporarily remove network policy to test
kubectl delete networkpolicy -n crossplane-system crossplane-isolation
# If this fixes it, update the policy with correct CIDR ranges
```

## References

- [Crossplane RBAC Documentation](https://docs.crossplane.io/latest/concepts/rbac/)
- [Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)

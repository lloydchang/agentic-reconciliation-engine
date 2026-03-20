# Simplified Single Crossplane Instance Migration

This plan migrates from Terraform to a single unified Crossplane control plane with native multi-cloud compositions, avoiding unnecessary hub-spoke complexity while maintaining proper isolation through RBAC and ProviderConfig.

## Architecture Decision: Single Control Plane

Based on operational best practices, we'll implement:
- **One Crossplane Instance**: Unified control plane for all teams
- **Native Multi-Cloud**: Compositions that span AWS, Azure, GCP
- **RBAC Isolation**: Team-based access control instead of cluster separation
- **Simple GitOps**: Single target, single source of truth

## Why This Wins

### Operational Excellence
- **One Place to Manage**: All infrastructure visible and manageable from one plane
- **Native Multi-Cloud**: Crossplane compositions can span clouds without complexity
- **Easy Upgrades**: Single Crossplane version to upgrade and debug
- **Unified Observability**: All resource states in one place

### Simpler GitOps
- **One Target**: Single Kubernetes cluster to sync
- **One Source**: Single Git repo with all compositions
- **No Split Brain**: No need to coordinate across multiple control planes

### Proper Isolation
- **ProviderConfig + RBAC**: Secure multi-tenant isolation
- **Namespace Separation**: Teams work in dedicated namespaces
- **Policy Enforcement**: OPA/Gatekeeper for cross-team controls
- **Audit Trail**: Single audit log across all teams

## Migration Strategy

### Phase 1: Deploy Single Crossplane (Week 1)
1. **Install Crossplane**: Single instance in management cluster
2. **Configure All Providers**: AWS, Azure, GCP in one control plane
3. **Setup RBAC**: Team-based access controls
4. **Deploy Monitoring**: Unified observability stack

### Phase 2: Multi-Cloud Compositions (Week 2)
1. **Cross-Cloud XRDs**: Resources that can span providers
2. **Provider Selection**: Runtime provider choice per resource
3. **Unified Compositions**: Single composition per resource type
4. **Policy Integration**: Team-based governance

### Phase 3: Team Onboarding (Week 3)
1. **Namespace Setup**: Dedicated namespaces per team
2. **RBAC Binding**: Team roles and permissions
3. **Provider Access**: Managed cloud credentials per team
4. **Training**: Crossplane-native workflows

### Phase 4: Migration Execution (Weeks 4-5)
1. **Gradual Migration**: Team by team migration from Terraform
2. **Validation**: Resource equivalence and functionality
3. **Documentation**: Updated procedures and runbooks
4. **Terraform Decommission**: Clean shutdown after validation

## Key Implementation Changes

### 1. Unified Compositions
Instead of provider-specific compositions, create smart compositions:

```yaml
# Single composition that handles all providers
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: multi-cloud-network
  labels:
    crossplane.io/managed: "true"
spec:
  compositeTypeRef:
    apiVersion: platform.example.com/v1alpha1
    kind: XNetwork
  resources:
  - name: network-resource
    base:
      apiVersion: # Determined at runtime by patch
      kind: # Determined at runtime by patch
    patches:
    - type: FromCompositeFieldPath
      fromFieldPath: spec.provider
      toFieldPath: # Provider-specific resource type
```

### 2. RBAC-Based Isolation
```yaml
# Team-based access control
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: team-a-network-admin
rules:
- apiGroups: ["platform.example.com"]
  resources: ["networks"]
  verbs: ["create", "get", "list", "watch", "update", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: team-a-binding
  namespace: team-a
subjects:
- kind: Group
  name: team-a-engineers
roleRef:
  kind: ClusterRole
  name: team-a-network-admin
```

### 3. Provider Config per Team
```yaml
# Team-specific provider configurations
apiVersion: aws.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: team-a-aws
  namespace: crossplane-system
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: team-a
      name: aws-credentials
      key: credentials
---
apiVersion: azure.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: team-a-azure
  namespace: crossplane-system
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: team-a
      name: azure-credentials
      key: credentials
```

## Benefits Realized

### For Teams
- **Simplified Onboarding**: One place to learn and operate
- **Faster Debugging**: Issues visible across all their resources
- **Consistent Experience**: Same tools regardless of cloud provider
- **Better Collaboration**: Shared visibility and knowledge

### For Platform
- **Reduced Overhead**: One Crossplane instance to maintain
- **Easier Upgrades**: Single upgrade path
- **Unified Security**: One security model to audit
- **Better Observability**: Single monitoring stack

### For Multi-Cloud
- **Native Spanning**: Compositions naturally span clouds
- **Provider Flexibility**: Choose provider per resource, not per team
- **Cost Optimization**: Easy to compare and optimize across providers
- **Disaster Recovery**: Unified failover and recovery

## Implementation Priority

1. **Deploy Single Instance**: Replace hub-spoke with single control plane
2. **Create Unified Compositions**: Multi-cloud capable resources
3. **Setup RBAC Isolation**: Team-based access controls
4. **Migrate Teams**: Gradual migration with training
5. **Decommission Hub-Spoke**: Remove unnecessary complexity

This approach delivers all of multi-cloud benefits with minimal operational complexity.

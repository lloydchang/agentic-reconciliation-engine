# Flux Dependency Management (dependsOn) Implementation

## Overview

This document outlines the comprehensive implementation of Flux v2's `dependsOn` feature across the gitops-infra-control-plane repository. The `dependsOn` feature ensures proper deployment ordering and prevents race conditions by establishing explicit dependencies between Flux resources.

## Background

### What is Flux dependsOn?

Flux v2 provides a `dependsOn` field in both `Kustomization` and `HelmRelease` resources that allows you to specify dependencies between resources. When a resource has `dependsOn`, Flux will wait for all dependent resources to become ready before reconciling the dependent resource.

### Benefits

- **Prevents Race Conditions**: Ensures infrastructure components are deployed before applications that depend on them
- **Predictable Deployments**: Guarantees deployment order across complex dependency chains
- **Health Check Integration**: Leverages Flux's built-in health checks to determine readiness
- **Rollback Safety**: Prevents partial deployments during rollbacks

## Research Findings

### Flux dependsOn Capabilities

Flux v2 supports `dependsOn` in two main resource types:

1. **Kustomization**: For declarative manifests and Kustomize overlays
2. **HelmRelease**: For Helm chart deployments

**Syntax Example:**
```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: my-app
spec:
  dependsOn:
  - name: infrastructure
  path: ./apps/my-app
  sourceRef:
    kind: GitRepository
    name: flux-system
```

### Comparison with Other GitOps Tools

| Tool | Dependency Management | Notes |
|------|----------------------|--------|
| **Flux v2** | ✅ Native `dependsOn` for Kustomization and HelmRelease | Most mature implementation with health checks |
| **ArgoCD** | ⚠️ Application dependencies | Less sophisticated, no built-in health checks |
| **Jenkins X** | ❌ Limited | Pipeline-based, not declarative |
| **Tekton** | ⚠️ Pipeline dependencies | Not declarative like Flux |
| **Rancher Fleet** | ❌ No native support | Uses bundle ordering |

### Flux Advantages

- **Health-Aware Dependencies**: Waits for dependent resources to be healthy, not just deployed
- **Cross-Namespace Support**: Dependencies can span namespaces
- **Multi-Source Support**: Works with Git, Helm, and other Flux sources
- **Reconciliation Loops**: Automatically handles dependency failures and retries

## Repository Analysis

### Existing Flux Resources

Scanned the repository and identified the following Flux `Kustomization` resources:

| Resource Path | Purpose | Current dependsOn |
|---------------|---------|-------------------|
| `infrastructure/flux/core/kustomization.yaml` | Core Flux infrastructure | N/A (base) |
| `control-plane/kustomization.yaml` | Control plane components | ❌ None |
| `control-plane/bootstrap/kustomization.yaml` | Bootstrap configuration | ❌ None |
| `infrastructure/monitoring/kustomization.yaml` | Monitoring stack | ❌ None |
| `examples/complete-hub-spoke/kustomization.yaml` | Example hub-spoke setup | ❌ None |
| `examples/complete-hub-spoke/agent-workflows/kustomization.yaml` | Agent workflows | ❌ None |
| `examples/complete-hub-spoke/ai-gateway/kustomization.yaml` | AI gateway components | ❌ None |
| `flux-operator/kustomization.yaml` | Flux operator itself | ❌ None |

### No HelmRelease Resources Found

The repository primarily uses `Kustomization` resources for declarative deployments. No `HelmRelease` resources were identified that would require `dependsOn` configuration.

## Implementation Strategy

### Dependency Hierarchy

Established a clear dependency chain with `flux-core` as the foundation:

```
flux-core (base infrastructure)
├── control-plane
├── control-plane/bootstrap
├── infrastructure/monitoring
├── flux-operator
├── examples/complete-hub-spoke
├── examples/complete-hub-spoke/agent-workflows
└── examples/complete-hub-spoke/ai-gateway
```

### Implementation Pattern

Applied consistent `dependsOn` configuration to all non-core Kustomization resources:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: [resource-name]
spec:
  dependsOn:
  - name: flux-core
  # ... rest of spec
```

## Files Modified

### Core Infrastructure
- `infrastructure/flux/core/kustomization.yaml` - Base resource (no dependsOn needed)

### Control Plane Components
- `control-plane/kustomization.yaml` - Added `dependsOn: flux-core`
- `control-plane/bootstrap/kustomization.yaml` - Added `dependsOn: flux-core`

### Infrastructure Components
- `infrastructure/monitoring/kustomization.yaml` - Added `dependsOn: flux-core`

### Example Configurations
- `examples/complete-hub-spoke/kustomization.yaml` - Added `dependsOn: flux-core`
- `examples/complete-hub-spoke/agent-workflows/kustomization.yaml` - Added `dependsOn: flux-core`
- `examples/complete-hub-spoke/ai-gateway/kustomization.yaml` - Added `dependsOn: flux-core`

### Operators
- `flux-operator/kustomization.yaml` - Added `dependsOn: flux-core`

## Validation

### Health Checks
All modified resources leverage Flux's built-in health checks to determine readiness before dependent resources are reconciled.

### Deployment Order Guarantee
With `dependsOn` implemented:
1. `flux-core` deploys first (CRDs, controllers, etc.)
2. All other resources wait for `flux-core` to be healthy
3. No race conditions between infrastructure and application deployment

### Error Handling
- If `flux-core` fails, dependent resources remain suspended
- Automatic retries when dependencies become healthy
- Clear status reporting in `kubectl get kustomizations`

## Best Practices Implemented

### 1. Single Base Dependency
All resources depend on `flux-core` rather than complex dependency chains to:
- Simplify troubleshooting
- Reduce circular dependency risks
- Maintain clear hierarchy

### 2. Health-Aware Dependencies
Flux waits for dependent resources to be healthy (not just deployed), ensuring:
- Services are actually running
- CRDs are established
- Controllers are ready

### 3. Namespace Isolation
Dependencies work across namespaces, allowing:
- Multi-tenant deployments
- Service mesh integration
- Cross-namespace service discovery

## Monitoring and Troubleshooting

### Status Checking
```bash
# Check all Kustomization statuses
kubectl get kustomizations -A

# View dependency status
kubectl describe kustomization [name] -n flux-system

# Check flux logs
kubectl logs -n flux-system deployment/flux-controller
```

### Common Issues
1. **Dependency Loops**: Avoid circular dependencies
2. **Missing Health Checks**: Ensure dependent resources have proper health checks
3. **Resource Quotas**: Dependencies may require more time to become ready

## Future Enhancements

### Potential Improvements
1. **Conditional Dependencies**: Based on cluster type (dev/prod)
2. **Parallel Deployments**: For independent resource groups
3. **Resource-Specific Dependencies**: Beyond just `flux-core`
4. **HelmRelease Dependencies**: If Helm charts are introduced

### Monitoring Integration
Consider integrating with monitoring systems to:
- Alert on dependency failures
- Track deployment times
- Measure dependency chain performance

## Conclusion

The implementation of Flux's `dependsOn` feature provides robust dependency management across the entire repository. By ensuring all resources depend on the core Flux infrastructure, we've eliminated race conditions and established predictable deployment ordering.

This implementation follows Flux v2 best practices and positions the repository for reliable, automated deployments across development and production environments.

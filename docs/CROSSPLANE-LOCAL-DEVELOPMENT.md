# Crossplane Local Development Guide

## Overview

This guide covers Crossplane local development using Kind clusters, enabling you to test GitOps infrastructure management without cloud costs or credentials.

## What Crossplane Supports for Local Development

### ✅ **Supported: Crossplane Core + Kubernetes Provider**

Crossplane provides a robust local development experience through:

- **Crossplane Core**: The control plane for managing cloud infrastructure
- **Kubernetes Provider**: `crossplane-contrib/provider-kubernetes` for managing Kubernetes resources
- **Local Testing**: Full GitOps workflow validation in Kind clusters
- **Resource Management**: Create/manage Deployments, Services, Namespaces, etc.

### ❌ **Not Supported: Mock Cloud Providers**

Crossplane does **not** provide mock cloud providers for local development. Instead, it uses the Kubernetes provider to manage actual Kubernetes resources.

## Architecture

```
Local Development Environment:
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Kind Cluster  │───▶│  Crossplane Core │───▶│ Kubernetes       │
│   (Hub)         │    │                  │    │ Provider        │
│                 │    │                  │    │                 │
│ • Flux         │    │ • Control Plane  │    │ • Manages K8s   │
│ • Crossplane   │    │ • Webhooks       │    │ • Objects       │
│ • AI Agents    │    │ • Controllers    │    │ • Clusters      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Quickstart Integration

The enhanced quickstart automatically configures Crossplane for local development:

```bash
# One-command setup with Crossplane local provider
./scripts/quickstart.sh
```

This installs:

1. **Crossplane Core** on the hub cluster
2. **Kubernetes Provider** for local resource management
3. **Provider Config** for cluster access
4. **Sample Compositions** for testing

## Manual Setup

If you need to set up Crossplane local development manually:

### 1. Install Crossplane Core

```bash
helm repo add crossplane https://charts.crossplane.io/stable
helm repo update

helm upgrade --install crossplane crossplane/crossplane \
  --namespace crossplane-system \
  --create-namespace \
  --set version=latest \
  --set args="--enable-environment-configs=true" \
  --wait
```

### 2. Install Kubernetes Provider

```bash
cat <<EOF | kubectl apply -f -
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-kubernetes
spec:
  package: "crossplane-contrib/provider-kubernetes:v0.6.0"
EOF
```

### 3. Create Provider Config

```bash
cat <<EOF | kubectl apply -f -
apiVersion: kubernetes.crossplane.io/v1alpha1
kind: ProviderConfig
metadata:
  name: local-cluster
  namespace: crossplane-system
spec:
  credentials:
    source: InjectedIdentity
EOF
```

### 4. Verify Installation

```bash
# Check Crossplane pods
kubectl get pods -n crossplane-system

# Check provider status
kubectl get providers -n crossplane-system

# Check provider config
kubectl get providerconfig -n crossplane-system
```

## Using Crossplane Locally

### Managing Kubernetes Objects

Create a simple deployment using Crossplane:

```yaml
apiVersion: kubernetes.crossplane.io/v1alpha1
kind: Object
metadata:
  name: nginx-deployment
  namespace: crossplane-system
spec:
  forProvider:
    manifest:
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        namespace: default
        labels:
          app: nginx
      spec:
        replicas: 2
        selector:
          matchLabels:
            app: nginx
        template:
          metadata:
            labels:
              app: nginx
          spec:
            containers:
            - name: nginx
              image: nginx:1.21
              ports:
              - containerPort: 80
  providerConfigRef:
    name: local-cluster
```

### Managing Multiple Clusters

Crossplane can manage other Kind clusters:

```yaml
apiVersion: kubernetes.crossplane.io/v1alpha1
kind: ProviderConfig
metadata:
  name: remote-cluster
  namespace: crossplane-system
spec:
  credentials:
    source: Secret
    secretRef:
      name: remote-cluster-kubeconfig
      namespace: crossplane-system
      key: kubeconfig
```

## Composite Resources for Local Testing

### Sample Database Composition

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xdatabases.database.example
spec:
  group: database.example
  names:
    plural: xdatabases
    singular: xdatabase
    kind: XDatabase
  claimNames:
    plural: xdatabases
    singular: xdatabase
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
            properties:
              parameters:
                type: object
                properties:
                  storageGB:
                    type: integer
                    default: 20
                  engine:
                    type: string
                    enum: [postgresql, mysql]
                    default: postgresql
```

## Testing GitOps Workflows

### Flux Integration

Crossplane integrates seamlessly with Flux for GitOps:

```yaml
# flux-system/gotk-sync.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta1
kind: Kustomization
metadata:
  name: crossplane-infrastructure
  namespace: flux-system
spec:
  interval: 5m
  sourceRef:
    kind: GitRepository
    name: flux-system
  path: ./infrastructure/crossplane
  prune: true
  validation: client
```

### Continuous Reconciliation

Test GitOps reconciliation by modifying resources:

```bash
# Modify a Crossplane resource
kubectl patch xdatabase my-db --type='merge' -p='{"spec":{"parameters":{"storageGB":30}}}'

# Watch Flux reconcile
kubectl get kustomization crossplane-infrastructure -n flux-system -w
```

## Debugging Local Crossplane

### Common Issues

1. **Provider Not Ready**
   ```bash
   kubectl get providers -n crossplane-system
   kubectl logs -n crossplane-system -l app.kubernetes.io/name=crossplane
   ```

2. **Provider Config Issues**
   ```bash
   kubectl get providerconfig -n crossplane-system
   kubectl describe providerconfig local-cluster -n crossplane-system
   ```

3. **Resource Creation Failures**
   ```bash
   kubectl get objects -n crossplane-system
   kubectl describe object <name> -n crossplane-system
   ```

### Logs and Monitoring

```bash
# Crossplane controller logs
kubectl logs -n crossplane-system deployment/crossplane -c crossplane

# Kubernetes provider logs
kubectl logs -n crossplane-system -l app.kubernetes.io/name=provider-kubernetes

# Watch resource events
kubectl get events -n crossplane-system --sort-by='.lastTimestamp'
```

## Best Practices

### 1. Resource Management

- **Use Namespaces**: Organize resources by application/environment
- **Label Resources**: Add labels for easy identification
- **Set Resource Limits**: Prevent resource exhaustion in local clusters

### 2. Testing Strategy

- **Test Compositions**: Validate composite resources before production
- **Mock External Dependencies**: Use local services for external dependencies
- **Automate Validation**: Use scripts to test Crossplane functionality

### 3. GitOps Integration

- **Version Control Everything**: Store all Crossplane resources in Git
- **Use Kustomization**: Manage environment-specific configurations
- **Validate Changes**: Use Flux validation to prevent misconfigurations

## Migration to Production

When moving from local to production:

1. **Replace Kubernetes Provider** with cloud providers (AWS, Azure, GCP)
2. **Update Provider Configs** with cloud credentials
3. **Modify Compositions** for cloud-specific resources
4. **Update Security** for production requirements

```bash
# Example: Add AWS provider
cat <<EOF | kubectl apply -f -
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-aws
spec:
  package: "crossplane/provider-aws:latest"
EOF
```

## Performance Considerations

### Local Cluster Resources

- **CPU**: 2+ cores recommended for Crossplane + workloads
- **Memory**: 4GB+ RAM for comfortable local development
- **Storage**: 20GB+ for cluster state and logs

### Optimization Tips

1. **Resource Limits**: Set appropriate resource requests/limits
2. **Garbage Collection**: Clean up unused resources regularly
3. **Monitoring**: Monitor cluster resource usage

## Troubleshooting

### Quick Fixes

```bash
# Restart Crossplane
kubectl rollout restart deployment/crossplane -n crossplane-system

# Reinstall provider
kubectl delete provider provider-kubernetes -n crossplane-system
# Then reinstall using the installation steps

# Reset cluster state
kind delete cluster gitops-hub
./scripts/create-hub-cluster.sh --provider kind
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `provider not healthy` | Provider installation failed | Check provider logs, reinstall |
| `connection refused` | Cluster access issues | Verify kubeconfig, network connectivity |
| `resource creation timeout` | Resource limits reached | Increase cluster resources, clean up unused resources |

## Conclusion

Crossplane local development with Kind clusters provides a powerful, cost-effective way to:

- **Test GitOps workflows** without cloud dependencies
- **Validate infrastructure as code** patterns
- **Develop composite resources** safely
- **Practice production-like operations** locally

The Kubernetes provider enables full Crossplane functionality for local development, making it an ideal choice for teams wanting to adopt GitOps and infrastructure management practices.

## References

- [Crossplane Documentation](https://docs.crossplane.io/)
- [Kubernetes Provider GitHub](https://github.com/crossplane-contrib/provider-kubernetes)
- [Kind Documentation](https://kind.sigs.k8s.io/)
- [Flux Documentation](https://fluxcd.io/docs/)

# Terraform to Crossplane Migration Guide

## Overview

This guide covers migrating from Terraform-based multi-cloud infrastructure management to Kubernetes-native Crossplane with hub-spoke architecture.

## Architecture

```
Hub Cluster (Crossplane Control Plane)
├── Crossplane Universal Controller
├── Provider Controllers (AWS, Azure, GCP)
├── Composite Resource Definitions (XRDs)
├── Compositions (per-provider)
└── GitOps Pipeline (Flux/ArgoCD)

Spoke Clusters (per cloud)
├── AWS Cluster → Crossplane AWS Provider
├── Azure Cluster → Crossplane Azure Provider  
├── GCP Cluster → Crossplane GCP Provider
└── Managed Resources via Claims
```

## Migration Steps

### 1. Foundation Setup

Deploy Crossplane hub cluster:

```bash
# Install Crossplane via Helm
helm repo add crossplane-stable https://charts.crossplane.io/stable
helm install crossplane crossplane-stable/crossplane --namespace crossplane-system --create-namespace

# Deploy providers
kubectl apply -f core/crossplane/providers/aws-provider.yaml
kubectl apply -f core/crossplane/providers/azure-provider.yaml
kubectl apply -f core/crossplane/providers/gcp-provider.yaml
```

### 2. Resource Abstraction

Apply Composite Resource Definitions:

```bash
# Apply XRDs
kubectl apply -f core/crossplane/xrds/xnetwork.yaml
kubectl apply -f core/crossplane/xrds/xcompute.yaml
kubectl apply -f core/crossplane/xrds/xstorage.yaml
```

### 3. Provider Compositions

Deploy provider-specific compositions:

```bash
# AWS compositions
kubectl apply -f core/crossplane/compositions/aws/network-aws.yaml
kubectl apply -f core/crossplane/compositions/aws/compute-aws.yaml
kubectl apply -f core/crossplane/compositions/aws/storage-aws.yaml
```

### 4. Migration Execution

Use migration tool:

```bash
# Discover existing Terraform resources
python core/ai/skills/provision-infrastructure/scripts/terraform_migration.py \
  --terraform-dir ./core/infrastructure/terraform \
  --action discover

# Create migration plan
python core/ai/skills/provision-infrastructure/scripts/terraform_migration.py \
  --terraform-dir ./core/infrastructure/terraform \
  --action plan \
  --output migration-plan.json

# Execute migration (dry run first)
python core/ai/skills/provision-infrastructure/scripts/terraform_migration.py \
  --terraform-dir ./core/infrastructure/terraform \
  --action migrate \
  --dry-run

# Execute actual migration
python core/ai/skills/provision-infrastructure/scripts/terraform_migration.py \
  --terraform-dir ./core/infrastructure/terraform \
  --action migrate
```

### 5. GitOps Integration

Deploy with Flux:

```bash
# Apply Flux GitOps resources
kubectl apply -f core/crossplane/gitops/flux-crossplane-helmrelease.yaml
```

## Resource Examples

### Network Creation

```yaml
apiVersion: platform.example.com/v1alpha1
kind: Network
metadata:
  name: production-network
  namespace: default
spec:
  provider: aws
  region: us-west-2
  cidrBlock: 10.0.0.0/16
  subnetCount: 3
  compositionSelector:
    matchLabels:
      provider: aws
```

### Compute Instance

```yaml
apiVersion: platform.example.com/v1alpha1
kind: Compute
metadata:
  name: web-server
  namespace: default
spec:
  provider: aws
  region: us-west-2
  instanceType: t3.medium
  imageId: ami-0abcdef1234567890
  minCount: 2
  maxCount: 2
  compositionSelector:
    matchLabels:
      provider: aws
```

### Storage Bucket

```yaml
apiVersion: platform.example.com/v1alpha1
kind: Storage
metadata:
  name: application-storage
  namespace: default
spec:
  provider: aws
  region: us-west-2
  bucketName: my-app-storage
  encryption: true
  versioning: false
  compositionSelector:
    matchLabels:
      provider: aws
```

## Backwards Compatibility

The Crossplane orchestrator maintains compatibility with existing interfaces:

```python
# New Crossplane approach
from crossplane_orchestrator import CrossplaneOrchestrator

orchestrator = CrossplaneOrchestrator()
result = orchestrator.create_network(request)

# Terraform compatibility adapter
from terraform_migration import TerraformCompatibilityAdapter

adapter = TerraformCompatibilityAdapter()
results = adapter.apply_terraform_config(terraform_config)
```

## Monitoring

Crossplane provides built-in observability:

```bash
# Check provider status
kubectl get providers

# Monitor resource status
kubectl get xnetworks
kubectl get xcomputes
kubectl get xstorages

# View events
kubectl get events --field-selector involvedObject.kind=Network
```

## Rollback

If migration fails:

```bash
# Rollback using backup
python core/ai/skills/provision-infrastructure/scripts/terraform_migration.py \
  --action rollback \
  --backup-dir /tmp/terraform_backup_20231201_120000
```

## Benefits

- **Kubernetes-native**: All resources managed via kubectl
- **GitOps ready**: Native integration with Flux/ArgoCD
- **Multi-cloud unified**: Single API for all providers
- **Self-healing**: Automatic reconciliation
- **Policy-as-code**: Native policy enforcement

## Troubleshooting

### Common Issues

1. **Provider not healthy**: Check credentials and permissions
2. **Composition not found**: Verify composition labels match XRD
3. **Resource stuck in pending**: Check provider logs and events

### Debug Commands

```bash
# Check Crossplane logs
kubectl logs -n crossplane-system deployment/crossplane

# Debug specific resource
kubectl describe xnetwork production-network

# Check composition status
kubectl get composition network-aws -o yaml
```

## Next Steps

1. Test migration in non-production environment
2. Update CI/CD pipelines to use Crossplane
3. Train teams on Kubernetes-native IaC
4. Decommission Terraform workflows
5. Implement advanced Crossplane features

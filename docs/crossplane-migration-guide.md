# Crossplane Migration Guide

## Overview

This guide documents the migration from Terraform-based multi-cloud infrastructure management to Kubernetes-native Crossplane approach for the agentic-reconciliation-engine project.

## Phase 1: Crossplane Foundation

### 1.1 Crossplane Installation

First, install Crossplane on your Kubernetes cluster:

```bash
# Install Crossplane
helm repo add crossplane-stable https://charts.crossplane.io/stable
helm repo update
helm install crossplane crossplane-stable/crossplane --namespace crossplane-system --create-namespace

# Verify installation
kubectl get pods -n crossplane-system
```

### 1.2 Provider Installation

Install cloud providers for AWS, Azure, and GCP:

```yaml
# providers.yaml
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-aws
spec:
  package: xpkg.upbound.io/upbound/provider-family-aws:v1.2.0
---
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-azure
spec:
  package: xpkg.upbound.io/upbound/provider-family-azure:v1.2.0
---
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-gcp
spec:
  package: xpkg.upbound.io/upbound/provider-family-gcp:v1.2.0
```

Apply the providers:

```bash
kubectl apply -f providers.yaml
kubectl get providers
```

### 1.3 Provider Configuration

Configure provider credentials using Kubernetes secrets:

```yaml
# provider-configs.yaml
apiVersion: aws.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: aws-default
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: crossplane-system
      name: aws-credentials
      key: credentials
---
apiVersion: gcp.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: gcp-default
spec:
  projectID: your-gcp-project-id
  credentials:
    source: Secret
    secretRef:
      namespace: crossplane-system
      name: gcp-credentials
      key: credentials
---
apiVersion: azure.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: azure-default
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: crossplane-system
      name: azure-credentials
      key: credentials
```

## Phase 2: Composite Resource Definitions

### 2.1 Network Resource Definition

```yaml
# xnetwork-definition.yaml
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xnetworks.platform.example.com
spec:
  group: platform.example.com
  names:
    kind: XNetwork
    plural: xnetworks
  claimNames:
    kind: Network
    plural: networks
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
              region:
                type: string
              cidrBlock:
                type: string
                default: "10.0.0.0/16"
              subnetCount:
                type: integer
                default: 3
              provider:
                type: string
                enum: ["aws", "azure", "gcp"]
            required: ["region"]
          status:
            type: object
            properties:
              networkId:
                type: string
              subnetIds:
                type: array
                items:
                  type: string
```

### 2.2 Compute Resource Definition

```yaml
# xcompute-definition.yaml
apiVersion: apiextensions.crossplane.io/v1
kind: CompositeResourceDefinition
metadata:
  name: xcomputes.platform.example.com
spec:
  group: platform.example.com
  names:
    kind: XCompute
    plural: xcomputes
  claimNames:
    kind: Compute
    plural: computes
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
              region:
                type: string
              instanceType:
                type: string
              image:
                type: string
              provider:
                type: string
                enum: ["aws", "azure", "gcp"]
            required: ["region", "instanceType"]
          status:
            type: object
            properties:
              instanceId:
                type: string
              publicIP:
                type: string
              status:
                type: string
```

## Phase 3: Provider-Specific Compositions

### 3.1 AWS Network Composition

```yaml
# composition-aws-network.yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: xnetwork-aws
  labels:
    provider: aws
    resource: network
spec:
  compositeTypeRef:
    apiVersion: platform.example.com/v1alpha1
    kind: XNetwork
  resources:
  - name: vpc
    base:
      apiVersion: ec2.aws.crossplane.io/v1beta1
      kind: VPC
      spec:
        forProvider:
          region: "us-west-2"
          cidrBlock: "10.0.0.0/16"
    patches:
    - fromFieldPath: "spec.region"
      toFieldPath: "spec.forProvider.region"
    - fromFieldPath: "spec.cidrBlock"
      toFieldPath: "spec.forProvider.cidrBlock"
  - name: internetGateway
    base:
      apiVersion: ec2.aws.crossplane.io/v1beta1
      kind: InternetGateway
      spec:
        forProvider:
          region: "us-west-2"
          vpcIdSelector:
            matchControllerRef: true
    patches:
    - fromFieldPath: "spec.region"
      toFieldPath: "spec.forProvider.region"
```

### 3.2 Azure Network Composition

```yaml
# composition-azure-network.yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: xnetwork-azure
  labels:
    provider: azure
    resource: network
spec:
  compositeTypeRef:
    apiVersion: platform.example.com/v1alpha1
    kind: XNetwork
  resources:
  - name: virtualNetwork
    base:
      apiVersion: network.azure.crossplane.io/v1beta1
      kind: VirtualNetwork
      spec:
        forProvider:
          location: "East US"
          addressSpace:
          - "10.0.0.0/16"
    patches:
    - fromFieldPath: "spec.region"
      toFieldPath: "spec.forProvider.location"
    - fromFieldPath: "spec.cidrBlock"
      toFieldPath: "spec.forProvider.addressSpace[0]"
```

## Migration Examples

### Creating Multi-Cloud Resources

```yaml
# multi-cloud-network.yaml
apiVersion: platform.example.com/v1alpha1
kind: XNetwork
metadata:
  name: production-network-aws
spec:
  region: us-west-2
  cidrBlock: 10.1.0.0/16
  provider: aws
---
apiVersion: platform.example.com/v1alpha1
kind: XNetwork
metadata:
  name: production-network-azure
spec:
  region: eastus
  cidrBlock: 10.2.0.0/16
  provider: azure
```

### Resource Claims

```yaml
# network-claim.yaml
apiVersion: platform.example.com/v1alpha1
kind: Network
metadata:
  name: app-network
spec:
  compositionSelector:
    matchLabels:
      provider: aws
  resourceRef:
    name: production-network-aws
```

## Integration with Existing Components

### Updated Multi-Cloud Orchestrator

The Python orchestrator will be updated to interact with Crossplane resources instead of direct cloud SDK calls:

```python
# Updated multi_cloud_orchestrator.py changes
class CrossplaneOrchestrator:
    def __init__(self):
        from kubernetes import client, config
        config.load_kube_config()
        self.api_client = client.ApiClient()
        self.custom_api = client.CustomObjectsApi()
    
    def create_network(self, network_spec):
        """Create network using Crossplane XNetwork resource"""
        resource = {
            "apiVersion": "platform.example.com/v1alpha1",
            "kind": "XNetwork",
            "metadata": {"name": network_spec["name"]},
            "spec": network_spec
        }
        return self.custom_api.create_namespaced_custom_object(
            group="platform.example.com",
            version="v1alpha1",
            namespace="default",
            plural="xnetworks",
            body=resource
        )
```

## Monitoring and Observability

### Crossplane Metrics

Crossplane provides built-in metrics that integrate with Prometheus:

```yaml
# crossplane-service-monitor.yaml
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

## GitOps Integration

### Flux Configuration

```yaml
# crossplane-kustomization.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: crossplane-infrastructure
  namespace: flux-system
spec:
  interval: 5m
  sourceRef:
    kind: GitRepository
    name: infrastructure
  path: "./crossplane"
  prune: true
  wait: true
  timeout: 5m
```

## Testing and Validation

### Crossplane Resource Testing

```python
# test_crossplane_resources.py
import pytest
from kubernetes import client, config

class TestCrossplaneResources:
    def setup_method(self):
        config.load_kube_config()
        self.custom_api = client.CustomObjectsApi()
    
    def test_network_creation(self):
        """Test XNetwork resource creation"""
        network_spec = {
            "region": "us-west-2",
            "cidrBlock": "10.0.0.0/16",
            "provider": "aws"
        }
        
        # Create resource
        result = self.custom_api.create_namespaced_custom_object(
            group="platform.example.com",
            version="v1alpha1",
            namespace="default",
            plural="xnetworks",
            body={
                "apiVersion": "platform.example.com/v1alpha1",
                "kind": "XNetwork",
                "metadata": {"name": "test-network"},
                "spec": network_spec
            }
        )
        
        assert result["spec"]["provider"] == "aws"
        assert result["spec"]["region"] == "us-west-2"
```

## Rollback Procedures

### Terraform Backup

Before migration, export existing Terraform state:

```bash
# Export Terraform state
terraform state pull > terraform-state-backup.json

# Import existing resources into Crossplane
crossplane beta import vpc.vpc.aws.crossplane.io my-vpc vpc-12345678
```

### Emergency Rollback

If Crossplane migration fails, rollback to Terraform:

```bash
# Destroy Crossplane resources
kubectl delete xnetworks.platform.example.com --all

# Restore Terraform state
terraform state push terraform-state-backup.json

# Apply Terraform configuration
terraform apply
```

## Best Practices

1. **Gradual Migration**: Migrate non-critical resources first
2. **Testing**: Thoroughly test in staging environments
3. **Backup**: Always backup Terraform state before migration
4. **Monitoring**: Closely monitor resource creation and status
5. **Documentation**: Keep detailed documentation of migrated resources
6. **Team Training**: Train teams on Crossplane concepts and operations

## Troubleshooting

### Common Issues

1. **Provider Not Healthy**
   ```bash
   kubectl get providers
   kubectl describe provider provider-aws
   ```

2. **Resource Creation Fails**
   ```bash
   kubectl get xnetworks.platform.example.com
   kubectl describe xnetwork my-network
   ```

3. **Composition Not Matching**
   ```bash
   kubectl get compositions
   kubectl describe composition xnetwork-aws
   ```

### Debug Commands

```bash
# Check Crossplane logs
kubectl logs -n crossplane-system deployment/crossplane

# Check resource status
kubectl get managed -o wide

# Check composition events
kubectl get events --field-selector involvedObject.kind=Composition
```

This migration guide provides a comprehensive approach to transitioning from Terraform to Crossplane while maintaining existing multi-cloud orchestration capabilities.

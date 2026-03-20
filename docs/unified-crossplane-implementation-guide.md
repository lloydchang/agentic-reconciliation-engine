# Unified Crossplane Implementation Guide

This guide provides step-by-step instructions for implementing the unified Crossplane architecture with proper isolation.

## Architecture Overview

The unified Crossplane approach provides:
- **Single control plane** for simplified operations
- **ProviderConfig-based isolation** for team separation
- **Smart provider selection** for cost and performance optimization
- **Cross-cloud capabilities** for high availability and failover

## Quick Start

### 1. Deploy Unified Crossplane

```bash
# Create namespaces
kubectl apply -f overlay/crossplane/unified/namespace.yaml

# Install Crossplane with all providers
kubectl apply -f overlay/crossplane/unified/crossplane-install.yaml

# Configure provider isolation
kubectl apply -f overlay/crossplane/unified/provider-configs-isolated.yaml

# Set up RBAC
kubectl apply -f overlay/crossplane/unified/rbac.yaml
```

### 2. Deploy Composite Resources

```bash
# Install unified XRDs with cross-cloud capabilities
kubectl apply -f overlay/crossplane/unified/composite-resources-unified.yaml

# Deploy smart compositions
kubectl apply -f overlay/crossplane/unified/compositions/smart-multi-cloud-compute.yaml
kubectl apply -f overlay/crossplane/unified/compositions/cross-cloud-failover.yaml
kubectl apply -f overlay/crossplane/unified/compositions/cost-optimized-storage.yaml
```

### 3. Deploy Sample Resources

```bash
# Apply unified sample resources
kubectl apply -f overlay/crossplane/unified/examples/unified-sample-resources.yaml
```

## Resource Creation Examples

### Smart Multi-Cloud Compute

```yaml
apiVersion: multicloud.example.com/v1alpha1
kind: XCompute
metadata:
  name: smart-web-server
  namespace: team-a
spec:
  provider: auto  # Let Crossplane select optimal provider
  region: us-west-2
  instanceType: medium
  image: ubuntu-20.04
  providerSelector:
    costOptimal: true
    performanceOptimal: true
  autoScaling:
    enabled: true
    minInstances: 2
    maxInstances: 5
  failoverConfig:
    enabled: true
    backupProvider: azure
```

### Cost-Optimized Storage

```yaml
apiVersion: multicloud.example.com/v1alpha1
kind: XStorage
metadata:
  name: cost-effective-storage
  namespace: team-a
spec:
  provider: auto
  region: us-west-2
  storageClass: standard
  size: 500Gi
  versioning: true
  providerSelector:
    costOptimal: true
  crossCloudReplication:
    enabled: true
    targetProviders: [aws, azure]
    replicationInterval: 24h
```

### High-Availability Network

```yaml
apiVersion: multicloud.example.com/v1alpha1
kind: XNetwork
metadata:
  name: ha-network
  namespace: team-b
spec:
  provider: auto
  region: us-west-2
  cidrBlock: 10.0.0.0/16
  subnetCount: 3
  failoverProvider: gcp
  haEnabled: true
```

## Using the Unified Orchestrator

### Smart Resource Creation

```bash
# Create cost-optimized compute
python3 core/scripts/automation/unified_crossplane_orchestrator.py \
  --action create \
  --type compute \
  --name web-server \
  --cost-optimal \
  --failover

# Create performance-optimized storage
python3 core/scripts/automation/unified_crossplane_orchestrator.py \
  --action create \
  --type storage \
  --name app-storage \
  --performance-optimal
```

### Cost Analysis

```bash
# Analyze cost optimization opportunities
python3 core/scripts/automation/unified_crossplane_orchestrator.py \
  --action analyze \
  --namespace team-a
```

### Resource Optimization

```bash
# Get optimization recommendations for existing resources
python3 core/scripts/automation/unified_crossplane_orchestrator.py \
  --action optimize
```

### Status Monitoring

```bash
# Get comprehensive unified status
python3 core/scripts/automation/unified_crossplane_orchestrator.py \
  --action status
```

## Team-Based Isolation

### Namespace Separation

Resources are isolated by namespace:
- `team-a` - Team A resources and ProviderConfigs
- `team-b` - Team B resources and ProviderConfigs
- `crossplane-system` - Crossplane control plane

### ProviderConfig Isolation

Each team has dedicated ProviderConfigs:
```yaml
# Team A AWS
apiVersion: aws.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: aws-team-a
  namespace: team-a
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: team-a
      name: aws-team-a-credentials
```

### RBAC Controls

Role-based access per team:
```yaml
# Team A can only manage their resources
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: crossplane-operator
  namespace: team-a
rules:
- apiGroups: ["multicloud.example.com"]
  resources: ["xnetworks", "xcomputes", "xstorages"]
  verbs: ["create", "get", "list", "watch", "update", "patch", "delete"]
```

## GitOps Setup

### Deploy Unified GitOps

```bash
# Install Flux (if not already installed)
kubectl apply -f overlay/crossplane/unified/gitops/unified-gitops.yaml

# The GitOps configuration includes:
# - Automatic Crossplane deployment
# - Team-specific resource management
# - Provider configuration updates
# - Monitoring and alerting
```

### Git Repository Structure

```
crossplane-config/
├── unified/
│   ├── namespace.yaml
│   ├── crossplane-install.yaml
│   ├── provider-configs-isolated.yaml
│   ├── rbac.yaml
│   ├── composite-resources-unified.yaml
│   ├── compositions/
│   │   ├── smart-multi-cloud-compute.yaml
│   │   ├── cross-cloud-failover.yaml
│   │   └── cost-optimized-storage.yaml
│   ├── examples/
│   │   ├── team-a/
│   │   └── team-b/
│   ├── gitops/
│   │   └── unified-gitops.yaml
│   └── monitoring/
│       └── unified-monitoring.yaml
```

## Monitoring and Observability

### Prometheus Metrics

The unified deployment includes comprehensive metrics:

- **Provider Health Scores**: Overall health per provider
- **Resource Distribution**: Cross-cloud resource allocation
- **Cost Optimization**: Percentage of cost-optimized resources
- **Failover Status**: Health of failover configurations
- **Reconciliation Performance**: Duration and error rates

### Grafana Dashboard

Import the unified dashboard:
```bash
# Apply dashboard configuration
kubectl apply -f overlay/crossplane/unified/monitoring/unified-monitoring.yaml

# Access dashboard at: http://grafana/d/crossplane-unified
```

### Alerting

Automated alerts for:
- Provider health degradation
- Resource reconciliation failures
- High error rates
- Cost optimization opportunities

## Migration from Terraform

### 1. Backup Existing Infrastructure

```bash
# Backup Terraform configurations
python3 core/scripts/automation/crossplane_migration_utils.py --action backup
```

### 2. Create Migration Plan

```bash
# Analyze Terraform state and create plan
python3 core/scripts/automation/crossplane_migration_utils.py \
  --action plan \
  --state-file core/infrastructure/terraform/terraform.tfstate
```

### 3. Execute Migration

```bash
# Migrate to unified Crossplane
python3 core/scripts/automation/crossplane_migration_utils.py \
  --action migrate \
  --state-file core/infrastructure/terraform/terraform.tfstate \
  --namespace team-a
```

### 4. Validate Migration

```bash
# Validate migration success
python3 core/scripts/automation/crossplane_migration_utils.py \
  --action validate \
  --namespace team-a
```

## Advanced Features

### Smart Provider Selection

The unified system automatically selects providers based on:

1. **Cost Optimization**: Chooses lowest-cost provider
2. **Performance Optimization**: Prioritizes high-performance providers
3. **Compliance Requirements**: Ensures regulatory compliance
4. **Resource Type**: Provider strengths for different resource types

### Cross-Cloud Failover

Automatic failover capabilities:
- **Health Monitoring**: Continuous health checks
- **Automatic Promotion**: Backup becomes primary on failure
- **Graceful Degradation**: Maintains service during transitions
- **Recovery Procedures**: Automatic recovery when primary is restored

### Cost Optimization

Intelligent cost management:
- **Real-time Analysis**: Continuous cost monitoring
- **Optimization Recommendations**: Automated suggestions
- **Lifecycle Management**: Automated data tiering
- **Cross-cloud Arbitrage**: Choose best provider per workload

## Troubleshooting

### Common Issues

1. **Provider Installation Fails**
```bash
# Check provider status
kubectl get providers -n crossplane-system

# Check specific provider
kubectl describe provider aws-team-a -n team-a
```

2. **Resource Creation Stuck**
```bash
# Check resource status
kubectl describe xcompute smart-web-server -n team-a

# Check composition logs
kubectl logs -n crossplane-system deployment/crossplane | grep smart-web-server
```

3. **Provider Configuration Issues**
```bash
# Verify secrets exist
kubectl get secrets -n team-a

# Test provider connectivity
kubectl get providerconfig aws-team-a -n team-a -o yaml
```

### Debug Commands

```bash
# Check Crossplane pods
kubectl get pods -n crossplane-system

# View resource events
kubectl get events --field-selector involvedObject.kind=XCompute

# Validate compositions
kubectl get compositions
kubectl describe composition smart-multi-cloud-compute
```

## Best Practices

### Resource Management

1. **Use Smart Selection**: Let Crossplane choose optimal providers
2. **Enable Failover**: Configure backup providers for critical workloads
3. **Monitor Costs**: Regular cost optimization analysis
4. **Tag Resources**: Consistent tagging for cost allocation

### Team Isolation

1. **Namespace Separation**: Strict namespace per team
2. **Dedicated ProviderConfigs**: Team-specific credentials
3. **RBAC Controls**: Principle of least privilege
4. **Regular Audits**: Review access and permissions

### GitOps Operations

1. **Single Source of Truth**: Git repository for all configurations
2. **Automated Deployment**: CI/CD pipeline for consistency
3. **Change Management**: Pull requests for all changes
4. **Rollback Capability**: Quick rollback if issues arise

## Performance Tuning

### Crossplane Configuration

```yaml
# Crossplane deployment with performance tuning
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crossplane
  namespace: crossplane-system
spec:
  replicas: 2  # High availability
  template:
    spec:
      containers:
      - name: crossplane
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi
        env:
        - name: CROSSPLANE_DEBUG
          value: "false"
        - name: CROSSPLANE_METRICS_ADDR
          value: ":8080"
```

### Resource Limits

```yaml
# Resource quotas per team
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-a-quota
  namespace: team-a
spec:
  hard:
    xnetworks.multicloud.example.com: "10"
    xcomputes.multicloud.example.com: "50"
    xstorages.multicloud.example.com: "20"
```

## Security Considerations

### Provider Credentials

- Store in team-specific namespaces
- Use Kubernetes secrets with encryption
- Rotate credentials regularly
- Apply least privilege access

### Network Security

- Use network policies for isolation
- Enable private endpoints where possible
- Monitor cross-cloud network traffic
- Implement DDoS protection

### Compliance

- Enable audit logging for all operations
- Tag resources with compliance metadata
- Regular security scans and assessments
- Maintain compliance documentation

## Next Steps

1. **Complete Migration**: Migrate all Terraform resources
2. **Enable Advanced Features**: Activate failover and optimization
3. **Team Training**: Educate teams on unified Crossplane
4. **Performance Monitoring**: Set up comprehensive observability
5. **Cost Optimization**: Implement automated cost management

This unified approach provides operational simplicity while maintaining proper isolation and enabling advanced multi-cloud capabilities.

# Crossplane Implementation Guide

This guide provides step-by-step instructions for implementing the Terraform to Crossplane migration.

## Prerequisites

1. **Kubernetes Cluster**: Management cluster with admin access
2. **kubectl**: Configured and working
3. **Cloud Provider Accounts**: AWS, Azure, GCP credentials
4. **Helm 3+**: For Crossplane installation
5. **Python 3.8+**: For migration scripts

## Phase 1: Crossplane Installation

### 1.1 Install Crossplane
```bash
# Add Crossplane Helm repository
helm repo add crossplane https://charts.crossplane.io/stable

# Install Crossplane
helm install crossplane crossplane/crossplane \
  --namespace crossplane-system \
  --create-namespace \
  --values core/infrastructure/crossplane/crossplane-install.yaml
```

### 1.2 Verify Installation
```bash
# Check Crossplane pods
kubectl get pods -n crossplane-system

# Verify providers are installing
kubectl get providers
```

## Phase 2: Provider Configuration

### 2.1 Create Provider Secrets
```bash
# AWS Provider Secret
kubectl create secret generic aws-credentials \
  --namespace crossplane-system \
  --from-literal=credentials='[default]
  aws_access_key_id = YOUR_ACCESS_KEY
  aws_secret_access_key = YOUR_SECRET_KEY
[/default]'

# Azure Provider Secret
kubectl create secret generic azure-credentials \
  --namespace crossplane-system \
  --from-literal=credentials='[default]
  client_id = YOUR_CLIENT_ID
  client_secret = YOUR_CLIENT_SECRET
  tenant_id = YOUR_TENANT_ID
  subscription_id = YOUR_SUBSCRIPTION_ID
[/default]'

# GCP Provider Secret
kubectl create secret generic gcp-credentials \
  --namespace crossplane-system \
  --from-file=credentials=path/to/service-account-key.json
```

### 2.2 Configure Providers
```bash
# Apply provider configurations
kubectl apply -f core/infrastructure/crossplane/provider-configs/aws/aws-provider-config.yaml
kubectl apply -f core/infrastructure/crossplane/provider-configs/azure/azure-provider-config.yaml
kubectl apply -f core/infrastructure/crossplane/provider-configs/gcp/gcp-provider-config.yaml
```

## Phase 3: Composite Resources

### 3.1 Install XRDs
```bash
# Apply composite resource definitions
kubectl apply -f core/infrastructure/crossplane/composite-resources/xrd/xnetwork.yaml
kubectl apply -f core/infrastructure/crossplane/composite-resources/xrd/xvm.yaml
```

### 3.2 Install Compositions
```bash
# Apply provider-specific compositions
kubectl apply -f core/infrastructure/crossplane/compositions/aws/
kubectl apply -f core/infrastructure/crossplane/compositions/azure/
kubectl apply -f core/infrastructure/crossplane/compositions/gcp/
kubectl apply -f core/infrastructure/crossplane/compositions/cross-cloud/
```

## Phase 4: RBAC Setup

### 4.1 Configure Provider Isolation
```bash
# Apply RBAC policies
kubectl apply -f core/infrastructure/crossplane/rbac/provider-isolation.yaml
```

## Phase 5: Migration Execution

### 5.1 Run Migration Script
```bash
# Execute Terraform to Crossplane migration
cd core/infrastructure/crossplane/migration-scripts
python3 terraform-to-crossplane-migration.py
```

### 5.2 Validate Migration
```bash
# Check Crossplane resources
kubectl get xnetworks
kubectl get xvms

# Verify resource status
kubectl describe xnetwork <network-name>
kubectl describe xvm <vm-name>
```

## Phase 6: Testing

### 6.1 Test Crossplane Resources
```bash
# Create test network
cat << EOF | kubectl apply -f -
apiVersion: platform.example.com/v1alpha1
kind: Network
metadata:
  name: test-network
spec:
  provider: aws
  region: us-west-2
  cidrBlock: "10.100.0.0/16"
EOF

# Create test VM
cat << EOF | kubectl apply -f -
apiVersion: platform.example.com/v1alpha1
kind: VM
metadata:
  name: test-vm
spec:
  provider: aws
  region: us-west-2
  instanceType: t3.micro
  subnetId: test-network-subnet
EOF
```

### 6.2 Clean Up Test Resources
```bash
kubectl delete network test-network
kubectl delete vm test-vm
```

## Phase 7: Integration

### 7.1 Update Existing Scripts
```bash
# Update multi-cloud orchestrator
cp .agents/orchestrate-automation/scripts/crossplane_orchestrator.py .agents/orchestrate-automation/scripts/multi_cloud_orchestrator.py

# Update Temporal workflows
cp overlay/ai/skills/complete-hub-spoke-temporal/workflows/crossplane-scatter-gather.go overlay/ai/skills/complete-hub-spoke-temporal/workflows/multi-cloud-scatter-gather.go
```

### 7.2 Test Integration
```bash
# Test Crossplane orchestrator
cd .agents/orchestrate-automation/scripts
python3 crossplane_orchestrator.py

# Test updated workflows (requires Temporal setup)
```

## Troubleshooting

### Common Issues

1. **Provider Installation Fails**
   ```bash
   # Check provider status
   kubectl get provider <provider-name> -o yaml
   
   # Check logs
   kubectl logs -n crossplane-system -l app=<provider-name>
   ```

2. **Composition Errors**
   ```bash
   # Check composition status
   kubectl get composition <composition-name> -o yaml
   
   # Check Crossplane logs
   kubectl logs -n crossplane-system deployment/crossplane
   ```

3. **Resource Creation Fails**
   ```bash
   # Check resource events
   kubectl describe xnetwork <network-name>
   kubectl describe xvm <vm-name>
   
   # Check provider-specific logs
   kubectl logs -n crossplane-system -l provider=<cloud-provider>
   ```

### Validation Commands

```bash
# Verify all Crossplane components
kubectl get providers,providerconfigs,compositeresourcedefinitions,compositions

# Check resource status
kubectl get xnetworks,xvms --all-namespaces

# Monitor Crossplane operations
kubectl get events -n crossplane-system --sort-by='.lastTimestamp'
```

## Next Steps

1. **Monitor**: Set up monitoring for Crossplane resources
2. **Automate**: Integrate with CI/CD pipelines
3. **Train**: Educate teams on Crossplane operations
4. **Optimize**: Fine-tune compositions for your use cases
5. **Decommission**: Gradually remove Terraform after validation

## Support

- **Crossplane Docs**: https://docs.crossplane.io/
- **Provider Documentation**: AWS, Azure, GCP specific docs
- **Community**: https://github.com/crossplane/crossplane
- **Slack**: #crossplane channel for support

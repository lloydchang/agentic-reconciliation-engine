# Phase 1: Crossplane Foundation Setup - Implementation Guide

This guide implements Phase 1 of the Terraform to Crossplane migration plan, establishing the foundation for unified multi-cloud management.

## Overview

Phase 1 sets up:
- Single Crossplane instance with proper isolation
- ProviderConfigs for AWS, Azure, GCP with RBAC
- Composite Resource Definitions (XRDs) for cross-cloud resources
- Team-based isolation via ProviderConfig + RBAC
- Backwards compatibility layer for Terraform coexistence

## Prerequisites

### Required Tools
```bash
# Install Crossplane CLI
curl -sL https://raw.githubusercontent.com/crossplane/crossplane/master/install.sh | sh

# Install kubectl and ensure cluster access
kubectl version --client

# Install Flux CLI (for GitOps)
curl -s https://fluxcd.io/install.sh | sudo bash
```

### Required Secrets
Create secrets for each cloud provider:

```bash
# AWS Credentials
kubectl create secret generic aws-credentials \
  --from-literal=aws_access_key_id=$AWS_ACCESS_KEY_ID \
  --from-literal=aws_secret_access_key=$AWS_SECRET_ACCESS_KEY \
  --namespace=crossplane-system

# Azure Credentials
kubectl create secret generic azure-credentials \
  --from-literal=client_id=$AZURE_CLIENT_ID \
  --from-literal=client_secret=$AZURE_CLIENT_SECRET \
  --from-literal=subscription_id=$AZURE_SUBSCRIPTION_ID \
  --from-literal=tenant_id=$AZURE_TENANT_ID \
  --namespace=crossplane-system

# GCP Credentials
kubectl create secret generic gcp-credentials \
  --from-file=credentials=$GOOGLE_APPLICATION_CREDENTIALS \
  --from-literal=project_id=$GCP_PROJECT_ID \
  --namespace=crossplane-system
```

## Installation Steps

### Step 1: Install Crossplane

```bash
# Apply Crossplane installation
kubectl apply -f overlay/crossplane/hub/crossplane-install.yaml

# Verify installation
kubectl get pods -n crossplane-system
kubectl get providers -n crossplane-system
```

### Step 2: Configure Providers

```bash
# Apply provider configurations
kubectl apply -f overlay/crossplane/hub/provider-configs.yaml

# Verify providers are ready
kubectl get providerconfigs -n crossplane-system
```

### Step 3: Create Composite Resource Definitions

```bash
# Apply XRDs for unified resource interfaces
kubectl apply -f overlay/crossplane/hub/composite-resource-definitions.yaml

# Verify XRDs are established
kubectl get xrd
kubectl get crd | grep platform.example.com
```

### Step 4: Apply Network Compositions

```bash
# Apply cloud-specific network compositions
kubectl apply -f overlay/crossplane/hub/compositions/aws-network-composition.yaml
kubectl apply -f overlay/crossplane/hub/compositions/azure-network-composition.yaml
kubectl apply -f overlay/crossplane/hub/compositions/gcp-network-composition.yaml

# Verify compositions
kubectl get compositions
```

### Step 5: Setup RBAC Isolation

```bash
# Apply team-based RBAC configuration
kubectl apply -f overlay/crossplane/hub/rbac.yaml

# Verify RBAC setup
kubectl get clusterroles | grep crossplane
kubectl get clusterrolebindings | grep crossplane
```

### Step 6: Configure Backwards Compatibility

```bash
# Apply Terraform compatibility layer
kubectl apply -f overlay/crossplane/hub/backwards-compatibility.yaml

# Verify compatibility jobs
kubectl get jobs -n crossplane-system -l app=terraform-migration
```

### Step 7: Deploy Example Resources

```bash
# Deploy example resource claims to test the setup
kubectl apply -f overlay/crossplane/hub/examples/resource-claims.yaml

# Monitor resource creation
kubectl get networks
kubectl get kubernetes
kubectl get databases
kubectl get storage
```

## Verification Checklist

### Crossplane Installation
- [ ] Crossplane pods are running in `crossplane-system` namespace
- [ ] All provider packages are installed and healthy
- [ ] ProviderConfigs are configured and ready

### Resource Definitions
- [ ] XRDs are established for networks, kubernetes, databases, storage
- [ ] Compositions are created for AWS, Azure, GCP
- [ ] Resource claims can be created successfully

### RBAC Isolation
- [ ] Team-specific ClusterRoles are created
- [ ] ServiceAccounts are properly configured
- [ ] RoleBindings are established
- [ ] Teams can only access their designated provider resources

### Backwards Compatibility
- [ ] Terraform state importer job is ready
- [ ] State sync configuration is in place
- [ ] Migration status tracking is enabled

### GitOps Integration
- [ ] Flux can manage Crossplane resources
- [ ] Kustomization is properly configured
- [ ] Resource drift detection is working

## Troubleshooting

### Provider Issues
```bash
# Check provider status
kubectl get providers -n crossplane-system

# Check provider logs
kubectl logs -n crossplane-system -l pkg.crossplane.io/provider=aws
kubectl logs -n crossplane-system -l pkg.crossplane.io/provider=azure
kubectl logs -n crossplane-system -l pkg.crossplane.io/provider=gcp
```

### Composition Issues
```bash
# Check composition status
kubectl get compositions

# Check composition events
kubectl describe composition <composition-name>
```

### RBAC Issues
```bash
# Test team access
kubectl auth can-i create networks --as=system:serviceaccount:crossplane-system:crossplane-aws-team
kubectl auth can-i create networks --as=system:serviceaccount:crossplane-system:crossplane-azure-team
kubectl auth can-i create networks --as=system:serviceaccount:crossplane-system:crossplane-gcp-team
```

### Resource Creation Issues
```bash
# Check resource status
kubectl get xnetworks
kubectl describe xnetwork <resource-name>

# Check resource events
kubectl get events --field-selector involvedObject.name=<resource-name>
```

## Next Steps

After completing Phase 1:

1. **Verify all resources are provisioning correctly**
2. **Test team isolation by accessing resources with different service accounts**
3. **Validate backwards compatibility with existing Terraform state**
4. **Proceed to Phase 2: Resource Migration by Type**

## Success Criteria

Phase 1 is complete when:
- ✅ Crossplane is installed and all providers are healthy
- ✅ XRDs and compositions are working
- ✅ Team-based RBAC isolation is verified
- ✅ Example resources can be created via kubectl
- ✅ Backwards compatibility layer is operational
- ✅ GitOps can manage all Crossplane resources

## Rollback Plan

If issues arise during Phase 1:

1. **Delete Crossplane resources**: `kubectl delete -f overlay/crossplane/hub/`
2. **Verify Terraform resources are still managed**: `terraform state list`
3. **Restore from backup**: `kubectl apply -f backup/`
4. **Review logs**: Check provider and composition logs for errors
5. **Contact support**: Provide logs and configuration details

## Security Considerations

- **Secrets Management**: Ensure all cloud credentials are stored as Kubernetes secrets
- **Network Policies**: Apply network policies to restrict cross-team communication
- **Audit Logging**: Enable audit logging for all Crossplane operations
- **Least Privilege**: Teams only have access to their designated cloud resources
- **Credential Rotation**: Regularly rotate cloud provider credentials

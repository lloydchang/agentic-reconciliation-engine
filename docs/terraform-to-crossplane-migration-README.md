# Terraform to Crossplane Migration Guide

This guide documents the complete migration from Terraform-based multi-cloud infrastructure management to Kubernetes-native Crossplane approach for the agentic-reconciliation-engine project.

## Overview

The migration transforms your existing multi-cloud infrastructure management from Terraform to Crossplane, providing:

- **Kubernetes-Native IaC**: Leverage existing GitOps workflows
- **Unified Multi-Cloud API**: Single control plane for AWS, Azure, GCP
- **Declarative Management**: Infrastructure as Kubernetes custom resources
- **Enhanced Observability**: Built-in monitoring and metrics
- **Policy Integration**: Native Kubernetes policy enforcement

## Migration Components

### 1. Crossplane Foundation
- **Provider Installation**: AWS, Azure, GCP Crossplane providers
- **Provider Configuration**: Multi-account and credential management
- **Composite Resource Definitions**: Platform API definitions
- **Compositions**: Provider-specific implementations

### 2. Migration Tools
- **Automated Migration Script**: `migrate_terraform_to_crossplane.py`
- **Resource Analysis**: Terraform state parsing and conversion
- **Manifest Generation**: Crossplane Kubernetes YAML creation
- **Validation Tools**: Resource health and connectivity checks

### 3. Updated Orchestrators
- **Crossplane Orchestrator**: Replaces direct cloud SDK calls
- **Temporal Activities**: Updated for Crossplane operations
- **JavaScript Abstraction**: Kubernetes-native resource management

## Quick Start

### Prerequisites
```bash
# Install dependencies
pip install kubernetes pyyaml

# Ensure kubectl access
kubectl cluster-info

# Install Crossplane (if not already installed)
helm repo add crossplane-stable https://charts.crossplane.io/stable
helm install crossplane crossplane-stable/crossplane --namespace crossplane-system --create-namespace
```

### 1. Install Crossplane Providers
```bash
# Apply provider configurations
kubectl apply -f overlay/crossplane/providers.yaml
kubectl apply -f overlay/crossplane/provider-configs.yaml

# Verify provider health
kubectl get providers
```

### 2. Apply Composite Resource Definitions
```bash
# Apply resource definitions
kubectl apply -f overlay/crossplane/composite-resource-definitions.yaml

# Apply provider-specific compositions
kubectl apply -f overlay/crossplane/compositions/aws.yaml
kubectl apply -f overlay/crossplane/compositions/azure.yaml
kubectl apply -f overlay/crossplane/compositions/gcp.yaml
```

### 3. Migrate Existing Infrastructure
```bash
# Run migration script
python core/scripts/automation/migrate_terraform_to_crossplane.py \
  core/infrastructure/terraform/aws \
  output/crossplane-migration

# Review generated manifests
ls -la output/crossplane-migration/crossplane/

# Apply Crossplane resources (staging first)
kubectl apply -f output/crossplane-migration/crossplane/all-resources.yaml
```

## Migration Strategy

### Phase 1: Foundation Setup (Days 1-2)
1. **Crossplane Installation**
   - Install Crossplane core components
   - Configure cloud provider credentials
   - Validate provider health status

2. **Resource Definitions**
   - Deploy composite resource definitions
   - Apply provider-specific compositions
   - Test resource creation in development

### Phase 2: Migration Execution (Days 3-5)
1. **Terraform Analysis**
   - Export existing Terraform state
   - Analyze resource dependencies
   - Create migration inventory

2. **Resource Conversion**
   - Convert Terraform resources to Crossplane specs
   - Generate Kubernetes manifests
   - Validate resource configurations

3. **Staging Deployment**
   - Deploy Crossplane resources to staging
   - Validate resource functionality
   - Test multi-cloud operations

### Phase 3: Production Migration (Days 6-7)
1. **Production Cutover**
   - Schedule maintenance window
   - Deploy Crossplane resources to production
   - Validate all services and connectivity

2. **Terraform Decommission**
   - Backup final Terraform state
   - Remove Terraform-managed resources
   - Update CI/CD pipelines

## Resource Mapping

### AWS Resources
| Terraform Resource | Crossplane Resource | Notes |
|------------------|-------------------|-------|
| `aws_instance` | `XCompute` | Instance types, AMIs, security groups |
| `aws_vpc` | `XNetwork` | VPC, subnets, internet gateways |
| `aws_s3_bucket` | `XStorage` | Bucket configuration, encryption, versioning |
| `aws_db_instance` | `XDatabase` | RDS instances, engines, backups |

### Azure Resources
| Terraform Resource | Crossplane Resource | Notes |
|------------------|-------------------|-------|
| `azurerm_linux_virtual_machine` | `XCompute` | VM sizes, images, network interfaces |
| `azurerm_virtual_network` | `XNetwork` | VNet, subnets, network security groups |
| `azurerm_storage_account` | `XStorage` | Storage accounts, tiers, encryption |
| `azurerm_postgresql_server` | `XDatabase` | PostgreSQL servers, versions, firewalls |

### GCP Resources
| Terraform Resource | Crossplane Resource | Notes |
|------------------|-------------------|-------|
| `google_compute_instance` | `XCompute` | Machine types, images, zones |
| `google_compute_network` | `XNetwork` | VPC networks, subnets, routing |
| `google_storage_bucket` | `XStorage` | Cloud Storage buckets, lifecycle rules |
| `google_sql_database_instance` | `XDatabase` | Cloud SQL instances, engines, backups |

## Updated Components

### Multi-Cloud Orchestrator
**File**: `core/ai/skills/provision-infrastructure/scripts/crossplane_orchestrator_new.py`

Replaces direct cloud SDK calls with Crossplane Kubernetes operations:

```python
# Before: Direct cloud SDK
handler = get_handler(provider, region)
result = handler.deploy_agent(config)

# After: Crossplane
crossplane_orchestrator = CrossplaneOrchestrator()
result = crossplane_orchestrator.create_compute(config)
```

### Temporal Activities
**File**: `overlay/ai/skills/complete-hub-spoke-temporal/activities/crossplane_activities.go`

Updated Temporal activities for Crossplane operations:

```go
// Create Crossplane resource
func (a *CrossplaneActivities) ExecuteCrossplaneOperationActivity(
    ctx context.Context, 
    request CrossplaneResourceRequest) (CrossplaneResourceResponse, error)

// Get resource status
func (a *CrossplaneActivities) GetCrossplaneResourceStatusActivity(
    ctx context.Context, 
    resourceType, resourceName string) (CrossplaneResourceResponse, error)
```

### JavaScript Abstraction
**File**: `core/multi-cloud-abstraction-crossplane.js`

Kubernetes-native multi-cloud management:

```javascript
// Before: Direct cloud SDK
const ec2 = new AWS.EC2();
const result = await ec2.runInstances(params).promise();

// After: Crossplane
const crossplane = new CrossplaneMultiCloudAbstractionLayer();
const result = await crossplane.createVM(config);
```

## Validation and Testing

### Pre-Migration Checks
```bash
# Validate Terraform state
terraform validate
terraform plan -detailed-exitcode

# Check Crossplane readiness
kubectl get providers
kubectl api-resources | grep platform.example.com
```

### Post-Migration Validation
```bash
# Check Crossplane resources
kubectl get xnetworks.platform.example.com
kubectl get xcomputes.platform.example.com
kubectl get xstorages.platform.example.com
kubectl get xdatabases.platform.example.com

# Validate resource status
kubectl describe xnetwork production-network
kubectl describe xcompute app-server

# Test connectivity
kubectl port-forward service/app-server 8080:80
```

### Integration Testing
```python
# Test Crossplane orchestrator
python core/ai/skills/provision-infrastructure/scripts/crossplane_orchestrator_new.py \
  --strategy parallel --verbose

# Test multi-cloud operations
node core/multi-cloud-abstraction-crossplane.js list vms
node core/multi-cloud-abstraction-crossplane.js status
```

## Monitoring and Observability

### Crossplane Metrics
Crossplane provides built-in metrics for monitoring:

```yaml
# Service monitor for Prometheus
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: crossplane-metrics
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: crossplane
  endpoints:
  - port: metrics
    interval: 30s
```

### Resource Health Monitoring
```bash
# Resource status dashboard
kubectl get xnetworks,xcomputes,xstorages,xdatabases -o wide

# Resource events
kubectl get events --field-selector involvedObject.kind=XNetwork
kubectl get events --field-selector involvedObject.kind=XCompute
```

## Rollback Procedures

### Emergency Rollback to Terraform
```bash
# Stop Crossplane resource creation
kubectl delete xnetworks.platform.example.com --all
kubectl delete xcomputes.platform.example.com --all

# Restore Terraform state
terraform state push terraform-state-backup.json

# Apply Terraform configuration
terraform apply
```

### Partial Rollback
```bash
# Rollback specific resource types
kubectl delete xstorages.platform.example.com --all
terraform apply -target=aws_s3_bucket.main

# Gradual migration
terraform apply -target=aws_vpc.main
kubectl apply -f crossplane-networks.yaml
```

## Troubleshooting

### Common Issues

#### Provider Installation Problems
```bash
# Check provider status
kubectl get providers -o wide

# Provider logs
kubectl logs -n crossplane-system deployment/crossplane

# Reinstall provider
kubectl delete provider provider-aws
kubectl apply -f providers.yaml
```

#### Resource Creation Failures
```bash
# Check resource events
kubectl describe xnetwork failed-network
kubectl get events --field-selector involvedObject.name=failed-network

# Validate composition
kubectl describe composition xnetwork-aws
kubectl get composition
```

#### Permission Issues
```bash
# Check RBAC
kubectl auth can-i create xnetworks.platform.example.com
kubectl auth can-i get compositeresourcedefinitions

# Fix permissions
kubectl apply -f rbac-fixes.yaml
```

### Debug Commands
```bash
# Crossplane debug logs
kubectl logs -n crossplane-system -l app=crossplane --since=1h

# Resource reconciliation status
kubectl get managed -o wide

# Composition matching
kubectl get composition -o yaml
```

## Best Practices

### Migration Best Practices
1. **Backup Everything**: Export Terraform state before migration
2. **Staging First**: Always test in staging before production
3. **Gradual Migration**: Migrate resource types incrementally
4. **Monitor Closely**: Watch resource creation and status
5. **Document Changes**: Keep detailed migration records

### Crossplane Best Practices
1. **Use Compositions**: Leverage provider-specific compositions
2. **Label Resources**: Consistent labeling for management
3. **Implement Policies**: Use OPA/Gatekeeper for governance
4. **Monitor Resources**: Set up comprehensive observability
5. **Version Control**: Store all manifests in Git

### Security Best Practices
1. **Credential Management**: Use Kubernetes secrets for provider credentials
2. **Network Security**: Maintain security groups and firewall rules
3. **Data Encryption**: Enable encryption for storage and databases
4. **Access Control**: Implement RBAC for Crossplane resources
5. **Audit Logging**: Enable comprehensive logging and monitoring

## Performance Considerations

### Resource Performance
- Crossplane resources may have different performance characteristics
- Test application performance after migration
- Monitor resource utilization and costs
- Optimize resource sizes and configurations

### Migration Performance
- Large migrations may take significant time
- Use parallel migration for independent resources
- Monitor migration progress and resource status
- Plan for adequate maintenance windows

## Cost Optimization

### Crossplane Cost Benefits
- **Unified Management**: Reduced tooling overhead
- **Better Utilization**: Improved resource visibility
- **Policy Enforcement**: Automated cost controls
- **Multi-Cloud Optimization**: Easier provider switching

### Cost Monitoring
```bash
# Crossplane cost metrics
kubectl get --raw "/apis/metrics.crossplane.io/v1beta1/namespaces/crossplane-system/metrics" | jq

# Resource cost analysis
kubectl get xcomputes -o json | jq '.items[].spec | {instanceType, provider}'
```

## Next Steps

### Immediate Actions
1. **Review Migration Plan**: Understand all migration components
2. **Setup Development Environment**: Create Crossplane test cluster
3. **Run Migration Script**: Test with non-critical resources
4. **Validate Results**: Ensure resources work correctly

### Long-term Actions
1. **Team Training**: Educate teams on Crossplane
2. **Process Updates**: Update operational procedures
3. **Tool Integration**: Integrate with existing tooling
4. **Continuous Improvement**: Optimize based on experience

## Support and Resources

### Documentation
- [Crossplane Documentation](https://docs.crossplane.io/)
- [Migration Guide](docs/crossplane-migration-guide.md)
- [API Reference](https://doc.crds.dev/github.com/crossplane/crossplane)

### Community
- [Crossplane Slack](https://crossplane.io/slack)
- [GitHub Discussions](https://github.com/crossplane/crossplane/discussions)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/crossplane)

### Troubleshooting
- [Known Issues](https://github.com/crossplane/crossplane/issues)
- [Troubleshooting Guide](https://docs.crossplane.io/troubleshooting/)
- [Support Channels](https://crossplane.io/support)

---

**Migration Status**: ✅ Ready for implementation
**Last Updated**: 2026-03-20
**Version**: 1.0.0

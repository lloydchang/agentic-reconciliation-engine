---
name: manage-gitops-prs
description: Use when you need to manage GitOps pull requests for infrastructure changes. Automates PR creation, validation, approval workflows, and merging for Flux/ArgoCD deployments. Includes policy checks, cost estimation, and automated testing.
license: AGPLv3
metadata:
  author: agentic-reconciliation-engine
  version: "1.0"
  category: enterprise
  risk_level: medium
  autonomy: conditional
  layer: temporal
compatibility: Requires Python 3.8+, cloud provider CLI tools (AWS CLI, Azure CLI, gcloud), and access to multi-cloud monitoring systems
allowed-tools: Bash Read Write Grep
---

# Gitops Pr — Multi-Cloud Enterprise Automation

## Purpose
Enterprise-grade automation solution for gitops pr operations across AWS, Azure, GCP, and on-premise environments to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **Infrastructure Changes**: When creating or updating cloud resources through GitOps workflows
- **Application Deployments**: When deploying applications via Kubernetes manifests or Helm charts
- **Policy Validation**: When ensuring infrastructure changes comply with organizational policies
- **Multi-Environment Promotion**: When moving changes through dev → staging → production environments
- **Automated Merging**: When PRs meet all criteria and can be safely merged automatically
- **Rollback Planning**: When planning infrastructure rollbacks through GitOps
- **Compliance Auditing**: When you need audit trails for all infrastructure changes

## Gotchas

### Common Pitfalls
- **Merge Conflicts**: Automated PR updates may create conflicts that require manual resolution
- **Policy Violations**: Changes may pass technical validation but violate organizational policies
- **Resource Dependencies**: GitOps changes may fail due to missing dependent resources
- **Credential Issues**: Service accounts may lack permissions for certain operations

### Edge Cases
- **Large PRs**: Very large infrastructure changes may timeout during validation
- **Cross-Repo Dependencies**: Changes that span multiple repositories require special handling
- **External Secrets**: Secret management may require external systems not tracked in Git
- **State Mismatches**: Git state may not match actual cluster state due to manual changes

### Performance Issues
- **Validation Time**: Complex infrastructure changes can take 10+ minutes to validate
- **API Rate Limits**: Cloud provider APIs may be rate limited during bulk operations
- **Repository Size**: Large Git repositories may have performance issues during operations
- **Concurrent PRs**: Multiple simultaneous PRs may cause resource contention

### Security Considerations
- **Secret Exposure**: GitOps should never store secrets in plain text in repositories
- **Access Control**: PR creation and merging should follow principle of least privilege
- **Audit Trails**: All GitOps operations must be logged for security compliance
- **Code Review**: Even automated changes should have some form of review process

### Troubleshooting
- **Sync Failures**: GitOps sync may fail due to network issues or API problems
- **Validation Errors**: Infrastructure validation may fail due to temporary issues
- **Permission Errors**: Service accounts may need updated permissions
- **Resource Conflicts**: Changes may conflict with existing resources

## Inputs
- **operation**: Operation type (required)
- **targetResource**: Target resource identifier (required)
- **cloudProvider**: Cloud provider - `aws|azure|gcp|onprem|all` (optional, default: `all`)
- **parameters**: Operation-specific parameters (optional)
- **environment**: Target environment (optional, default: `production`)
- **dryRun**: Dry run mode (optional, default: `true`)

## Process
1. **Cloud Provider Detection**: Identify target cloud providers and environments
2. **Input Validation**: Comprehensive parameter validation and security checks
3. **Multi-Cloud Context Analysis**: Analyze current state across all providers
4. **Operation Planning**: Generate optimized execution plan
5. **Safety Assessment**: Risk analysis and impact evaluation across providers
6. **Execution**: Perform operations with monitoring and validation
7. **Results Analysis**: Process results and generate reports

## Outputs
- **Operation Results**: Detailed execution results and status per provider
- **Compliance Reports**: Validation and compliance status across environments
- **Performance Metrics**: Operation performance and efficiency metrics by provider
- **Recommendations**: Optimization suggestions and next steps
- **Audit Trail**: Complete operation history for compliance across all providers

## Environment
- **AWS**: EKS, EC2, Lambda, CloudWatch, IAM, S3
- **Azure**: AKS, VMs, Functions, Monitor, Azure AD
- **GCP**: GKE, Compute Engine, Cloud Functions, Cloud Monitoring
- **On-Premise**: Kubernetes clusters, VMware, OpenStack, Prometheus
- **Multi-Cloud Tools**: Terraform, Ansible, Crossplane, Cluster API

## Dependencies
- **Python 3.8+**: Core execution environment
- **Cloud SDKs**: boto3, azure-sdk, google-cloud
- **Kubernetes**: kubernetes client for cluster operations
- **Multi-Cloud Libraries**: terraform-python, ansible-python

## Scripts
- `core/scripts/automation/gitops-pr.py`: Main automation implementation
- `core/scripts/automation/gitops-pr_handler.py`: Cloud-specific operations
- `core/scripts/automation/multi_cloud_orchestrator.py`: Cross-provider coordination

## Trigger Keywords
gitops, pr, automation, enterprise, multi-cloud, aws, azure, gcp, onprem

## Human Gate Requirements
- **Production changes**: Production environment operations require approval
- **High-impact operations**: Critical operations require review
- **Security changes**: Security modifications need validation

## Enterprise Features
- **Multi-tenant Support**: Isolated operations per tenant
- **Role-based Access Control**: Enterprise IAM integration
- **Audit Logging**: Complete audit trail for compliance
- **Performance Monitoring**: SLA tracking and metrics
- **Security Hardening**: Encryption and compliance standards
- **Dynamic Code Generation**: Agents can modify logic dynamically
- **Cross-Cloud Orchestration**: Coordinated operations across providers

## References

Load these files when needed:
- `scripts/gitops-orchestrator.py` - Core GitOps workflow management
- `scripts/pr-validator.py` - Automated PR validation and testing
- `references/gitops-policies.md` - Organizational GitOps policies and procedures
- `assets/pr-templates/` - Standard PR templates for different change types
- `examples/gitops-workflows/` - Complete GitOps workflow examples

---
name: provision-infrastructure
description: Use when you need to create new cloud resources or infrastructure. Handles VM provisioning, Kubernetes clusters, databases, networking, and storage across AWS, Azure, GCP with proper tagging, security, and compliance. Includes cost estimation and resource validation.
license: AGPLv3
metadata:
  author: agentic-reconciliation-engine
  version: "1.0"
  category: enterprise
  risk_level: medium
  autonomy: conditional
  layer: temporal
  human_gate: PR approval required for production infrastructure changes
  openswe:
    sandbox_required: true
    sandbox_providers: [modal, daytona, runloop]
    middleware_hooks:
      - pre_execution: validate_infrastructure_permissions
      - post_execution: audit_infrastructure_changes
      - error_recovery: rollback_on_failure
    integrations:
      slack: "@gitops-bot provision infrastructure"
      github: "@openswe provision infrastructure"
      linear: "@openswe provision infrastructure"
    context_engineering: "AGENTS.md infrastructure patterns"
    subagent_capabilities: [terraform_validation, cost_estimation, security_scan]
compatibility: Requires Python 3.8+, cloud provider CLI tools (AWS CLI, Azure CLI, gcloud), and access to multi-cloud monitoring systems
allowed-tools: Bash Read Write Grep
---

# Infrastructure Provisioning — Multi-Cloud Enterprise Automation

## Purpose
Enterprise-grade automation solution for infrastructure provisioning operations across AWS, Azure, GCP, and on-premise environments to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **New Environment Setup**: When creating new development, staging, or production environments
- **Application Deployment**: When provisioning infrastructure for new applications or services
- **Scaling Events**: When adding capacity to handle increased load or new users
- **Disaster Recovery**: When rebuilding infrastructure in different regions or accounts
- **Multi-Cloud Expansion**: When replicating infrastructure across different cloud providers
- **Resource Updates**: When replacing old infrastructure with new instance types or generations
- **Testing Environments**: When creating temporary infrastructure for testing or CI/CD pipelines

## Gotchas

### Common Pitfalls
- **Resource Naming Conflicts**: Cloud providers have strict naming rules and global uniqueness requirements (S3 buckets, some Azure resources)
- **Quota Limits**: Every account has default quotas that may be insufficient for large deployments
- **VPC/IP Address Planning**: IP address ranges cannot be easily changed after VPC creation
- **Cross-Provider Dependencies**: Some resources (like databases) can't be created across cloud providers

### Edge Cases
- **Region Unavailability**: Not all instance types or services are available in every region
- **Compliance Boundaries**: Some workloads must stay in specific geographic regions for data residency
- **Legacy Integration**: New infrastructure may need to connect to older systems with specific requirements
- **Multi-Account Setups**: Large organizations may have resources spread across multiple accounts

### Performance Issues
- **API Rate Limits**: Provisioning many resources simultaneously can hit API limits, especially during bulk operations
- **Resource Creation Time**: Some resources (like databases or large VMs) can take 10-30 minutes to become available
- **Concurrent Creation Limits**: Some cloud providers limit how many resources of the same type can be created simultaneously
- **Network Propagation**: DNS and network changes can take time to propagate across regions

### Security Considerations
- **Default Security Groups**: Never use default security groups that allow all traffic
- **Public IP Assignment**: Avoid assigning public IPs unless absolutely necessary
- **IAM Role Timing**: IAM roles and policies may take several minutes to propagate
- **Secret Management**: Never embed secrets or credentials in infrastructure code

### Troubleshooting
- **Creation Failures**: Check cloud provider console for detailed error messages, especially around quotas and permissions
- **Networking Issues**: Verify security groups, NACLs, and route tables if resources can't communicate
- **Dependency Order**: Some resources depend on others (subnets before instances, VPC before subnets)
- **State Mismatch**: If Terraform/cloud provider state gets out of sync, resources may appear to not exist

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
- `core/scripts/automation/infrastructure-provisioning.py`: Main automation implementation
- `core/scripts/automation/infrastructure-provisioning_handler.py`: Cloud-specific operations
- `core/scripts/automation/multi_cloud_orchestrator.py`: Cross-provider coordination

## Trigger Keywords
infrastructure, provisioning, automation, enterprise, multi-cloud, aws, azure, gcp, onprem

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
- `scripts/infrastructure-builder.py` - Core provisioning logic and validation
- `scripts/resource-templates/` - Cloud-specific resource templates
- `references/networking-patterns.md` - VPC and subnet design patterns
- `assets/security-hardening-checklist.yaml` - Security configuration checklist
- `examples/multi-cloud-setups/` - Complete infrastructure examples

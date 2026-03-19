---
name: manage-workflows
description: Use when you need to coordinate and manage complex workflows across cloud environments. Orchestrates multi-step processes, handles dependencies, manages state, and provides workflow execution tracking for automation pipelines and business processes.
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

# Workflow Management — Multi-Cloud Enterprise Automation

## Purpose
Enterprise-grade automation solution for workflow management operations across AWS, Azure, GCP, and on-premise environments to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **Complex Automation**: When coordinating multi-step processes with dependencies
- **Business Processes**: When automating business workflows like approvals, provisioning, or onboarding
- **CI/CD Pipelines**: When managing complex deployment pipelines with multiple stages
- **Data Processing**: When orchestrating data processing workflows and ETL pipelines
- **Compliance Workflows**: When managing compliance-related processes like audits or certifications
- **Incident Response**: When coordinating incident response procedures and communication
- **Resource Orchestration**: When managing complex resource provisioning and configuration workflows

## Gotchas

### Common Pitfalls
- **Workflow Complexity**: Overly complex workflows are hard to debug and maintain
- **State Management**: Improper state handling can cause workflow inconsistencies
- **Error Handling**: Missing error handling can cause silent failures or stuck workflows
- **Timeout Issues**: Long-running workflows may timeout or be abandoned

### Edge Cases
- **Concurrent Workflows**: Multiple workflows may compete for the same resources
- **Rollback Scenarios**: Complex workflows may not have proper rollback mechanisms
- **External Dependencies**: Workflows depending on external systems may fail unpredictably
- **Resource Limits**: Workflow execution may be limited by available resources

### Performance Issues
- **Workflow Scale**: Large numbers of concurrent workflows can overwhelm the system
- **State Persistence**: Frequent state updates can impact performance
- **Memory Usage**: Long-running workflows may accumulate memory usage
- **Database Contention**: Workflow state storage can become a bottleneck

### Security Considerations
- **Credential Management**: Workflows may need access to sensitive credentials
- **Data Privacy**: Workflow data may contain sensitive information requiring protection
- **Access Control**: Workflow management should follow principle of least privilege
- **Audit Requirements**: All workflow executions must be logged for compliance

### Troubleshooting
- **Stuck Workflows**: Workflows may get stuck waiting for resources or external events
- **State Corruption**: Workflow state may become corrupted requiring manual intervention
- **Dependency Issues**: External dependencies may fail causing workflow failures
- **Configuration Errors**: Incorrect workflow configuration can cause execution failures

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
- `core/scripts/automation/workflow-management.py`: Main automation implementation
- `core/scripts/automation/workflow-management_handler.py`: Cloud-specific operations
- `core/scripts/automation/multi_cloud_orchestrator.py`: Cross-provider coordination

## Trigger Keywords
workflow, management, automation, enterprise, multi-cloud, aws, azure, gcp, onprem

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
- `scripts/workflow-engine.py` - Core workflow execution and state management
- `scripts/dependency-resolver.py` - Workflow dependency analysis and resolution
- `references/workflow-patterns.md` - Common workflow patterns and best practices
- `assets/workflow-templates.yaml` - Reusable workflow templates for common processes
- `examples/workflow-examples/` - Complete workflow examples for different use cases

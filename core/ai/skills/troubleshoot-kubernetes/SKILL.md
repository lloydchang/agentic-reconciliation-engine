---
name: troubleshoot-kubernetes
description: Use when you need to troubleshoot Kubernetes cluster issues. Diagnoses pod failures, network problems, resource constraints, and cluster health issues. Provides step-by-step debugging guidance and automated remediation suggestions for EKS, AKS, GKE, and on-premise clusters.
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

# Troubleshoot Kubernetes — Multi-Cloud Enterprise Automation

## Purpose
Enterprise-grade automation solution for k8s troubleshoot operations across AWS, Azure, GCP, and on-premise environments to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **Pod Failures**: When pods are stuck in CrashLoopBackOff, pending, or failing to start
- **Network Issues**: When services can't communicate or have connectivity problems
- **Resource Problems**: When nodes are resource constrained or applications are throttled
- **Cluster Health**: When cluster components are unhealthy or degraded
- **Performance Issues**: When applications are slow or have high latency
- **Storage Problems**: When persistent volumes aren't mounting or have issues
- **DNS Resolution**: When name resolution isn't working within the cluster

## Gotchas

### Common Pitfalls
- **Symptom vs Cause**: Kubernetes symptoms often don't directly indicate root causes
- **Resource Requests**: Missing or incorrect resource requests can cause scheduling issues
- **Image Pull Issues**: Registry access problems can cause pod startup failures
- **Namespace Isolation**: Issues in one namespace may affect cluster-wide resources

### Edge Cases
- **Cluster Autoscaling**: Autoscaling events can cause temporary resource unavailability
- **Node Drain**: Node maintenance can cause pod rescheduling and temporary issues
- **Certificate Rotation**: Certificate rotation can cause temporary connectivity issues
- **Multi-Tenant Clusters**: Resource contention between tenants can cause complex issues

### Performance Issues
- **Cluster Size**: Large clusters (>1000 nodes) can have API server latency
- **Watch Connections**: Too many watch connections can overwhelm the API server
- **Log Volume**: High log volume can affect cluster performance and troubleshooting
- **Resource Metrics**: Collecting detailed metrics can impact cluster performance

### Security Considerations
- **Privileged Escalation**: Troubleshooting may require elevated permissions
- **Sensitive Data**: Logs and diagnostics may contain sensitive information
- **Cluster Access**: Troubleshooting tools need appropriate RBAC permissions
- **Audit Logs**: All troubleshooting actions should be logged for security compliance

### Troubleshooting
- **API Server Access**: Network issues may prevent access to the Kubernetes API
- **Tool Compatibility**: Different kubectl versions may have compatibility issues
- **Context Confusion**: Multiple kubeconfig contexts can cause commands to run on wrong cluster
- **Permission Errors**: Insufficient permissions can prevent diagnostic commands

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
- `core/scripts/automation/k8s-troubleshoot.py`: Main automation implementation
- `core/scripts/automation/k8s-troubleshoot_handler.py`: Cloud-specific operations
- `core/scripts/automation/multi_cloud_orchestrator.py`: Cross-provider coordination

## Trigger Keywords
k8s, troubleshoot, automation, enterprise, multi-cloud, aws, azure, gcp, onprem

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
- `scripts/k8s-diagnostic.py` - Core Kubernetes diagnostic and analysis tools
- `scripts/resource-analyzer.py` - Resource usage and constraint analysis
- `references/k8s-troubleshooting-guide.md` - Step-by-step troubleshooting procedures
- `assets/diagnostic-templates.yaml` - Standard diagnostic templates for common issues
- `examples/troubleshooting-scenarios/` - Real-world troubleshooting examples and solutions

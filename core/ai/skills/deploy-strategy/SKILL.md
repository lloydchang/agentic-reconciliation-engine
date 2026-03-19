---
name: deploy-strategy
description: Use when you need to deploy applications with specific strategies like canary, blue-green, or rolling updates. Manages traffic shifting, health checks, and automatic rollback for safe deployments across Kubernetes, VMs, and serverless environments.
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

# Deployment Strategy — Multi-Cloud Enterprise Automation

## Purpose
Enterprise-grade automation solution for deployment strategy operations across AWS, Azure, GCP, and on-premise environments to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **Production Releases**: When deploying to production and need zero-downtime or safe rollback capabilities
- **High-Risk Changes**: For database migrations, API breaking changes, or infrastructure updates
- **Multi-Environment Deployments**: When coordinating deployments across dev, staging, and production
- **A/B Testing**: When gradually releasing features to subsets of users
- **Emergency Rollbacks**: When you need quick rollback capabilities for failed deployments
- **Blue-Green Switches**: For instant traffic switching between identical environments
- **Canary Analysis**: When testing new versions with small traffic percentages before full rollout

## Gotchas

### Common Pitfalls
- **Database Migrations**: Never run database migrations in canary deployments - they affect all traffic
- **Stateful Applications**: Blue-green deployments don't work well with stateful applications without data synchronization
- **Traffic Routing**: Ensure load balancers properly route traffic and don't cache old endpoints
- **Health Check Timing**: Health checks must be long enough to allow applications to start properly

### Edge Cases
- **Resource Limits**: Canary deployments temporarily double resource requirements during overlap periods
- **Session Affinity**: Applications with session affinity may have issues during traffic shifting
- **External Dependencies**: Third-party APIs may have rate limits that get exceeded during deployments
- **Cross-Region Deployments**: Global applications need careful coordination to avoid region-specific issues

### Performance Issues
- **Rollback Time**: Blue-green deployments allow instant rollback, but rolling updates can take 10+ minutes to rollback
- **Health Check Delays**: Applications with slow startup times (Java, .NET) need longer health check intervals
- **Traffic Shifting**: Gradual traffic shifts in canary deployments can cause inconsistent user experiences
- **Resource Cleanup**: Old deployment versions may not be cleaned up automatically, causing resource waste

### Security Considerations
- **Secret Rotation**: New deployments may need access to updated secrets or certificates
- **Network Policies**: New pods may be blocked by existing network policies during deployment
- **API Keys**: Ensure new deployments have proper API key access and don't use expired credentials
- **Compliance Logging**: Maintain audit trails during deployments for compliance requirements

### Troubleshooting
- **Stuck Deployments**: Check if pods are in CrashLoopBackOff due to configuration or resource issues
- **Traffic Not Shifting**: Verify ingress controllers and service mesh configurations are properly updated
- **Health Check Failures**: Application may be running but health checks failing due to wrong endpoints or timeouts
- **Rollback Failures**: Database schema changes may prevent successful rollback to previous versions

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
- `core/scripts/automation/deployment-strategy.py`: Main automation implementation
- `core/scripts/automation/deployment-strategy_handler.py`: Cloud-specific operations
- `core/scripts/automation/multi_cloud_orchestrator.py`: Cross-provider coordination

## Trigger Keywords
deployment, strategy, automation, enterprise, multi-cloud, aws, azure, gcp, onprem

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
- `scripts/deployment-orchestrator.py` - Core deployment strategy implementation
- `scripts/traffic-manager.py` - Traffic shifting and routing logic
- `references/deployment-patterns.md` - Detailed strategy explanations and examples
- `assets/health-check-templates.yaml` - Health check configurations for different app types
- `examples/rollback-scenarios/` - Common rollback scenarios and solutions

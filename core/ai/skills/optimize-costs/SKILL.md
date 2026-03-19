---
name: optimize-costs
description: Use when cloud costs spike unexpectedly or when you need to optimize resource allocation across providers. Analyzes usage patterns, identifies waste, and recommends cost-saving measures for AWS, Azure, GCP, and on-premise environments.
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

# Cost Optimizer — Multi-Cloud Enterprise Automation

## Purpose
Enterprise-grade automation solution for cost optimizer operations across AWS, Azure, GCP, and on-premise environments to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **Cost Spikes**: When monthly cloud bills increase unexpectedly (>20% month-over-month)
- **Resource Waste**: When you suspect unused or underutilized resources (idle instances, abandoned storage)
- **Budget Planning**: For quarterly budget reviews and cost forecasting
- **Provider Comparison**: When evaluating which cloud provider offers better pricing for specific workloads
- **Rightsizing**: When VMs or containers appear over-provisioned for actual usage
- **Storage Optimization**: When storage costs grow faster than data usage patterns
- **Network Costs**: When data transfer egress charges become significant

## Gotchas

### Common Pitfalls
- **Reserved Instance Conflicts**: Don't recommend RI purchases without checking existing commitments and expiration dates
- **Usage Forecasting**: Cost optimization based on single-day data can be misleading. Use 30-90 day trends
- **Cross-Provider Arbitrage**: Network egress costs often offset compute savings between providers
- **Tagging Inconsistency**: Untagged resources cannot be properly categorized or optimized

### Edge Cases
- **Burst Workloads**: Seasonal businesses need different optimization strategies than steady-state workloads
- **Compliance Requirements**: Some regions/instance types may be required for compliance despite higher costs
- **Multi-Region Deployments**: Latency requirements may prevent consolidation to cheaper regions
- **Legacy Applications**: Older systems may not support modern instance types or storage classes

### Performance Issues
- **API Rate Limits**: Cost Explorer APIs have strict limits (5 requests/second for AWS). Implement caching
- **Large Account Analysis**: Accounts with >10,000 resources may timeout. Use pagination and parallel processing
- **Currency Conversion**: Always convert to single currency for accurate comparison across providers
- **Data Retention**: Cost and usage data typically only available for 12 months in most cloud providers

### Security Considerations
- **Cost Data Sensitivity**: Cloud billing data can reveal company size, usage patterns, and architecture details
- **Access Permissions**: Cost optimization requires billing access which may be restricted in some organizations
- **Third-Party Tools**: Be cautious with external cost management tools that require full billing access
- **Data Export**: Exporting cost data may violate compliance or data residency requirements

### Troubleshooting
- **Missing Cost Data**: Check if Cost and Usage Reports are enabled (not automatic in all accounts)
- **Inconsistent Metrics**: Different providers categorize costs differently (e.g., data transfer vs. networking)
- **Optimization Conflicts**: Storage tiering recommendations may conflict with performance requirements
- **Currency Fluctuations**: International deployments affected by exchange rate changes

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
- `scripts/cost-optimizer.py`: Main automation implementation
- `scripts/cost-optimizer_handler.py`: Cloud-specific operations
- `scripts/multi_cloud_orchestrator.py`: Cross-provider coordination

## Trigger Keywords
cost, optimizer, automation, enterprise, multi-cloud, aws, azure, gcp, onprem

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
- `scripts/cost-analyzer.py` - Core cost analysis algorithms
- `scripts/provider-handlers/` - Cloud provider specific cost APIs
- `references/cost-optimization-patterns.md` - Proven optimization strategies
- `assets/instance-type-mapping.csv` - Cross-provider instance comparisons
- `examples/cost-reduction-cases/` - Real-world optimization examples

---
name: optimize-costs
description: AI-powered multi-cloud cost optimization skill with ML-based recommendations, predictive spending analysis, and automated cost-saving measures. Use when cloud costs spike unexpectedly or when you need to optimize resource allocation across providers with advanced AI capabilities.
license: AGPLv3
metadata:
  author: agentic-reconciliation-engine
  version: "2.0"
  category: enterprise
  risk_level: medium
  autonomy: conditional
  layer: temporal
compatibility: Requires Python 3.8+, cloud provider CLI tools (AWS CLI, Azure CLI, gcloud), and access to multi-cloud monitoring systems
allowed-tools: Bash Read Write Grep
---

# Cost Optimizer — Multi-Cloud Enterprise Automation with AI

## Purpose
Enterprise-grade automation solution for cost optimizer operations across AWS, Azure, GCP, and on-premise environments with advanced AI capabilities including ML-based cost optimization, predictive spending analysis, and automated cost-saving measures to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **Cost Spikes**: When monthly cloud bills increase unexpectedly (>20% month-over-month)
- **Resource Waste**: When you suspect unused or underutilized resources (idle instances, abandoned storage)
- **Budget Planning**: For quarterly budget reviews and cost forecasting with AI predictions
- **Provider Comparison**: When evaluating which cloud provider offers better pricing for specific workloads
- **Rightsizing**: When VMs or containers appear over-provisioned for actual usage
- **Storage Optimization**: When storage costs grow faster than data usage patterns
- **Network Costs**: When data transfer egress charges become significant
- **AI-Powered Analysis**: For ML-based cost optimization and predictive spending insights

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
- **parameters**: Operation-specific parameters including AI model configurations (optional)
- **environment**: Target environment (optional, default: `production`)
- **dryRun**: Dry run mode (optional, default: `true`)
- **historicalData**: Include historical cost data for predictive analysis (optional, default: `false`)
- **optimizationType**: Type of optimization - `rightsizing|scheduling|storage|networking|licenses|reservations` (optional)

## Process
1. **Cloud Provider Detection**: Identify target cloud providers and environments
2. **Input Validation**: Comprehensive parameter validation and security checks
3. **Multi-Cloud Context Analysis**: Analyze current state across all providers
4. **AI-Powered Cost Analysis**: Apply ML-based cost optimization, predictive spending analysis, and anomaly detection
5. **Optimization Planning**: Generate AI-enhanced optimization recommendations with risk assessment
6. **Safety Assessment**: Risk analysis and impact evaluation across providers
7. **Execution**: Perform optimizations with monitoring and validation
8. **Results Analysis**: Process results and generate AI-enhanced cost reports

## Outputs
- **Operation Results**: Detailed execution results and status per provider
- **AI-Enhanced Recommendations**: ML-generated cost optimization recommendations with predictive insights
- **Cost Analysis**: Comprehensive cost metrics and waste identification
- **Predictive Forecasts**: Future spending predictions and budget planning insights
- **Compliance Reports**: Validation and compliance status across environments
- **Performance Metrics**: Operation performance and efficiency metrics by provider
- **Cost Optimization Results**: Before/after cost comparisons and ROI analysis
- **Audit Trail**: Complete operation history for compliance across all providers

## Environment
- **AWS**: EKS, EC2, Lambda, CloudWatch, IAM, S3, Cost Explorer
- **Azure**: AKS, VMs, Functions, Monitor, Azure AD, Cost Management
- **GCP**: GKE, Compute Engine, Cloud Functions, Cloud Monitoring, Cloud Billing
- **On-Premise**: Kubernetes clusters, VMware, OpenStack, Prometheus, Cost Analysis Tools

## Dependencies
- **Python 3.8+**: Core execution environment
- **AI/ML Libraries**: scikit-learn, pandas, numpy, statsmodels, tensorflow/keras
- **Cloud SDKs**: boto3, azure-sdk, google-cloud
- **Cost Analysis Tools**: Cloud provider cost APIs, billing exports
- **Optimization Libraries**: scipy, cvxopt for advanced optimization
- **Time Series Libraries**: prophet, pmdarima for predictive analysis
- **Kubernetes**: kubernetes client for cluster operations
- **Multi-Cloud Libraries**: terraform-python, ansible-python

## Scripts
- `core/scripts/automation/cost-optimizer.py`: Main AI-powered optimization implementation
- `core/scripts/automation/cost-optimizer_handler.py`: Cloud-specific operations
- `core/scripts/automation/multi_cloud_orchestrator.py`: Cross-provider coordination

## Trigger Keywords
cost, optimizer, automation, enterprise, multi-cloud, ai, ml, predictive, aws, azure, gcp, onprem

## Human Gate Requirements
- **Production changes**: Production environment operations require approval
- **High-impact operations**: Critical operations require review
- **Security changes**: Security modifications need validation
- **AI Model Updates**: Changes to AI models require approval
- **Resource Scaling**: Major scaling operations need human oversight

## Enterprise Features
- **Multi-tenant Support**: Isolated operations per tenant
- **Role-based Access Control**: Enterprise IAM integration
- **Audit Logging**: Complete audit trail for compliance
- **Performance Monitoring**: SLA tracking and metrics
- **Security Hardening**: Encryption and compliance standards
- **Dynamic Code Generation**: Agents can modify logic dynamically
- **Cross-Cloud Orchestration**: Coordinated optimizations across providers
- **AI-Powered Insights**: Advanced analytics and predictive capabilities
- **Automated Learning**: Continuous improvement from cost patterns

## References

Load these files when needed:
- `scripts/cost-analyzer.py` - Core cost analysis algorithms with AI
- `scripts/provider-handlers/` - Cloud provider specific cost APIs
- `references/cost-optimization-patterns.md` - Proven optimization strategies
- `assets/instance-type-mapping.csv` - Cross-provider instance comparisons
- `examples/cost-reduction-cases/` - Real-world optimization examples

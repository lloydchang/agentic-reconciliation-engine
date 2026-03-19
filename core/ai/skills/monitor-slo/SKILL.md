---
name: monitor-slo
description: Use when you need to track Service Level Objectives (SLOs) and ensure service reliability. Monitors SLO compliance, calculates error budgets, generates burn rate alerts, and provides reliability reporting for critical services across cloud environments.
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

# Slo Monitor — Multi-Cloud Enterprise Automation

## Purpose
Enterprise-grade automation solution for slo monitor operations across AWS, Azure, GCP, and on-premise environments to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **SLO Tracking**: When monitoring service reliability against defined objectives
- **Error Budget Management**: When tracking remaining error budget and burn rates
- **Reliability Reporting**: When generating SLO compliance reports for stakeholders
- **Service Reviews**: When preparing for service reliability reviews or post-mortems
- **Capacity Planning**: When SLO trends indicate need for capacity improvements
- **Incident Prevention**: When proactively monitoring for SLO degradation patterns
- **Compliance Requirements**: When meeting contractual reliability obligations

## Gotchas

### Common Pitfalls
- **SLO Definition**: Poorly defined SLOs lead to misleading reliability metrics
- **Measurement Windows**: Short measurement windows can cause SLO volatility
- **Service Dependencies**: SLOs may be affected by dependencies outside your control
- **Data Quality**: Bad monitoring data leads to inaccurate SLO calculations

### Edge Cases
- **New Services**: New services lack historical data for meaningful SLOs
- **Seasonal Traffic**: Usage patterns may affect SLO calculations predictably
- **Planned Maintenance**: Maintenance windows should be excluded from SLO calculations
- **Multi-Region Services**: Different regions may have different reliability characteristics

### Performance Issues
- **Metric Volume**: High-volume services can generate millions of data points
- **Calculation Complexity**: Complex SLO calculations can be computationally expensive
- **Storage Requirements**: Long-term SLO history requires significant storage
- **Real-time Processing**: Real-time SLO monitoring requires efficient processing

### Security Considerations
- **Data Privacy**: SLO data may reveal usage patterns and service capacity
- **Access Control**: SLO configuration changes should be restricted to authorized users
- **Audit Requirements**: SLO changes and violations must be logged for compliance
- **Data Retention**: SLO data retention policies must comply with regulations

### Troubleshooting
- **Metric Gaps**: Missing metrics can cause SLO calculation failures
- **Time Zone Issues**: SLO calculations must use consistent time zones
- **Service Discovery**: New services may not be automatically included in SLO monitoring
- **Alert Fatigue**: Too many SLO alerts can cause important issues to be missed

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
- `core/scripts/automation/slo-monitor.py`: Main automation implementation
- `core/scripts/automation/slo-monitor_handler.py`: Cloud-specific operations
- `core/scripts/automation/multi_cloud_orchestrator.py`: Cross-provider coordination

## Trigger Keywords
slo, monitor, automation, enterprise, multi-cloud, aws, azure, gcp, onprem

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
- `scripts/slo-calculator.py` - Core SLO calculation and monitoring logic
- `scripts/error-budget-tracker.py` - Error budget calculation and burn rate analysis
- `references/slo-definitions.md` - SLO best practices and definition guidelines
- `assets/slo-templates.yaml` - Standard SLO templates for different service types
- `examples/reliability-reports/` - Sample SLO compliance reports and dashboards

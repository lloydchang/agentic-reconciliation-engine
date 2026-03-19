---
name: prioritize-alerts
description: Prioritizes and categorizes alerts from monitoring systems across multi-cloud environments, applies intelligent filtering and escalation rules, and provides actionable alert summaries. Use when managing alert floods, improving incident response times, or implementing alert management strategies.
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

# Alert Prioritizer — Multi-Cloud Enterprise Automation

## Purpose
Enterprise-grade automation solution for alert prioritizer operations across AWS, Azure, GCP, and on-premise environments to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **Alert Floods**: When dealing with high volumes of alerts from monitoring systems
- **Incident Response**: When quickly identifying the most critical alerts during incidents
- **Noise Reduction**: When filtering out false positives and low-priority alerts
- **Multi-Source Alerts**: When consolidating alerts from different monitoring systems
- **On-Call Support**: When helping on-call engineers focus on important issues
- **Alert Fatigue Prevention**: When reducing alert fatigue for engineering teams
- **Escalation Management**: When automatically escalating critical alerts to appropriate teams

## Gotchas

### Common Pitfalls
- **Over-Filtering**: Aggressive filtering may cause important alerts to be missed
- **Context Loss**: Alert prioritization may lose important context about the issue
- **Team Silos**: Different teams may have different priorities for the same alerts
- **Alert Correlation**: Related alerts may not be properly correlated, causing duplication

### Edge Cases
- **Cascading Failures**: Single issues may trigger cascading alerts across systems
- **Maintenance Windows**: Alerts during maintenance should be deprioritized or suppressed
- **Third-Party Outages**: External service issues may generate many related alerts
- **Multi-Region Issues**: Global issues may generate region-specific alerts

### Performance Issues
- **Alert Volume**: High alert volumes (1000+/minute) can overwhelm processing systems
- **Real-time Requirements**: Alert prioritization must happen in near real-time
- **Memory Usage**: Alert correlation requires keeping alerts in memory for analysis
- **Network Latency**: Distributed alert sources may have network delays

### Security Considerations
- **Sensitive Information**: Alerts may contain sensitive system information or PII
- **Access Control**: Alert configuration and prioritization rules should be restricted
- **Audit Requirements**: All alert prioritization decisions must be logged
- **Data Privacy**: Alert content may be subject to privacy regulations

### Troubleshooting
- **Missing Alerts**: Some alerts may not reach the prioritization system
- **Incorrect Priorities**: Prioritization logic may misclassify alert severity
- **Integration Failures**: Monitoring system integrations may fail or be unreliable
- **Rule Conflicts**: Multiple prioritization rules may conflict with each other

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
- `core/scripts/automation/alert-prioritizer.py`: Main automation implementation
- `core/scripts/automation/alert-prioritizer_handler.py`: Cloud-specific operations
- `core/scripts/automation/multi_cloud_orchestrator.py`: Cross-provider coordination

## Trigger Keywords
alert, prioritizer, automation, enterprise, multi-cloud, aws, azure, gcp, onprem

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
- `scripts/alert-processor.py` - Core alert ingestion and processing logic
- `scripts/prioritization-engine.py` - Alert scoring and ranking algorithms
- `references/alert-taxonomy.md` - Alert classification and severity guidelines
- `assets/escalation-rules.yaml` - Escalation policies and team assignments
- `examples/alert-dashboards/` - Sample alert management dashboards and reports

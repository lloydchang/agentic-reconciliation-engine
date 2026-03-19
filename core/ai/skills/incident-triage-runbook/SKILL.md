---
name: incident-triage-runbook
description: Use when incidents occur and you need to triage, categorize, and execute response runbooks automatically. Correlates alerts, identifies root causes, escalates to appropriate teams, and executes remediation procedures for production incidents.
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

# Incident Triage Runbook — Multi-Cloud Enterprise Automation

## Purpose
Enterprise-grade automation solution for incident triage runbook operations across AWS, Azure, GCP, and on-premise environments to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **Production Outages**: When services are down or severely degraded and immediate response is needed
- **High Severity Alerts**: For P1/P2 incidents requiring urgent attention and coordination
- **Recurring Issues**: When the same type of incident happens repeatedly and needs standardized response
- **Multi-Service Impacts**: When incidents affect multiple services or require cross-team coordination
- **After-Hours Incidents**: When on-call engineers need automated guidance and escalation procedures
- **Compliance Incidents**: When security or compliance breaches require documented response procedures
- **Performance Degradation**: When performance metrics breach thresholds and need investigation

## Gotchas

### Common Pitfalls
- **Alert Fatigue**: Too many automated alerts can cause real incidents to be missed
- **False Positives**: Automated triage may misclassify alerts and trigger unnecessary responses
- **Runbook Conflicts**: Multiple runbooks may conflict when executed simultaneously
- **Escalation Delays**: Automated escalation may not account for team availability or context

### Edge Cases
- **Cascading Failures**: Initial incident may trigger secondary failures requiring different runbooks
- **Partial Service Degradation**: Some services working while others fail may confuse automated categorization
- **Third-Party Outages**: Incidents caused by external providers may require different response procedures
- **Multi-Region Issues**: Incidents affecting multiple regions need coordinated response across teams

### Performance Issues
- **Correlation Delays**: Alert correlation and analysis may take time during high-volume incidents
- **Resource Contention**: Multiple incidents may compete for the same response resources
- **Communication Overload**: Automated notifications may overwhelm communication channels
- **Database Locks**: Concurrent incident updates may cause database contention

### Security Considerations
- **Sensitive Data**: Incident details may contain sensitive information that needs protection
- **Access Control**: Runbook execution requires appropriate permissions but should follow principle of least privilege
- **Audit Requirements**: All incident responses must be logged for compliance and post-incident review
- **Privacy Regulations**: User data mentioned in incidents must comply with privacy laws

### Troubleshooting
- **Stuck Workflows**: Runbook execution may get stuck waiting for manual input or external systems
- **Missing Context**: Automated triage may lack business context needed for proper prioritization
- **Team Availability**: Escalation paths may fail due to team schedules or contact information issues
- **Integration Failures**: Dependencies on external systems (monitoring, communication) may fail during incidents

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
- `core/scripts/automation/incident-triage-runbook.py`: Main automation implementation
- `core/scripts/automation/incident-triage-runbook_handler.py`: Cloud-specific operations
- `core/scripts/automation/multi_cloud_orchestrator.py`: Cross-provider coordination

## Trigger Keywords
incident, triage, runbook, automation, enterprise, multi-cloud, aws, azure, gcp, onprem

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
- `scripts/incident-triager.py` - Alert correlation and categorization engine
- `scripts/runbook-executor.py` - Automated runbook execution framework
- `references/incident-taxonomy.md` - Standard incident classification system
- `assets/escalation-policies.yaml` - Team escalation rules and contacts
- `examples/incident-scenarios/` - Common incident types and response procedures

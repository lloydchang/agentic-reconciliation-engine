---
name: analyze-security
description: Use when you need to perform security analysis across cloud environments. Scans for vulnerabilities, misconfigurations, compliance issues, and threats. Includes automated remediation suggestions and security posture assessment for AWS, Azure, GCP, and on-premise systems.
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

# Security Analysis — Multi-Cloud Enterprise Automation

## Purpose
Enterprise-grade automation solution for security analysis operations across AWS, Azure, GCP, and on-premise environments to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **Security Audits**: When conducting regular security assessments across cloud infrastructure
- **Compliance Checks**: When verifying compliance with standards like SOC2, HIPAA, GDPR, PCI-DSS
- **Vulnerability Scanning**: When scanning for security vulnerabilities in systems and applications
- **Incident Investigation**: When analyzing security incidents or potential breaches
- **New Deployments**: When security-reviewing new infrastructure or application deployments
- **Risk Assessment**: When evaluating security risks for business decisions
- **Threat Hunting**: When proactively searching for potential security threats

## Gotchas

### Common Pitfalls
- **False Positives**: Automated security scans often flag benign configurations as issues
- **Alert Fatigue**: Too many security alerts can cause real issues to be overlooked
- **Scope Creep**: Security analysis can expand to include more than originally planned
- **Credential Exposure**: Security analysis tools may require sensitive credentials

### Edge Cases
- **Legacy Systems**: Older systems may not meet modern security standards but can't be easily updated
- **Third-Party Dependencies**: Security issues in external services may be outside your control
- **Compliance Conflicts**: Different compliance frameworks may have conflicting requirements
- **Multi-Cloud Complexity**: Security policies may need to be adapted for different cloud providers

### Performance Issues
- **Scan Duration**: Comprehensive security scans can take hours for large environments
- **API Rate Limits**: Security scanning APIs often have strict rate limits
- **Resource Usage**: Security scanning tools can consume significant compute resources
- **Network Latency**: Cross-region security checks may be slow due to network latency

### Security Considerations
- **Privilege Escalation**: Security analysis tools require elevated privileges that could be misused
- **Data Privacy**: Security logs may contain sensitive information requiring protection
- **Audit Trails**: All security analysis activities must be logged for compliance
- **Tool Security**: Security analysis tools themselves must be secure and regularly updated

### Troubleshooting
- **Scan Failures**: Security scans may fail due to network issues or authentication problems
- **Tool Compatibility**: Different security tools may have conflicting requirements
- **Access Issues**: Security analysis may fail due to insufficient permissions
- **Data Corruption**: Security scan results may be corrupted or incomplete

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
- `scripts/security-analysis.py`: Main automation implementation
- `scripts/multi_cloud_orchestrator.py`: Cross-provider coordination

## Trigger Keywords
security, analysis, automation, enterprise, multi-cloud, aws, azure, gcp, onprem

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
- `scripts/security-scanner.py` - Core security analysis and vulnerability scanning
- `scripts/compliance-checker.py` - Compliance validation against standards
- `references/security-benchmarks.md` - Security best practices and benchmarks
- `assets/security-policies.yaml` - Security policy definitions and rules
- `examples/security-reports/` - Sample security analysis reports and formats

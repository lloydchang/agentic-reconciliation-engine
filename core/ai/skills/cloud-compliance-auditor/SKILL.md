---
name: cloud-compliance-auditor
description: >
  Automated cloud compliance auditing across AWS, Azure, and GCP. Performs security
  assessments, policy compliance checks, and generates remediation recommendations.
  Supports multiple compliance frameworks including CIS, NIST, PCI-DSS, HIPAA, and SOC2.
metadata:
  risk_level: medium
  autonomy: conditional
  layer: temporal
  human_gate: PR approval required for changes affecting production resources
---

# Cloud Compliance Auditor Skill

## Overview

The Cloud Compliance Auditor skill provides comprehensive automated compliance auditing across multi-cloud environments. It continuously monitors cloud resources for security posture, policy compliance, and generates actionable remediation recommendations.

## Capabilities

### Core Functions

- **Multi-Cloud Security Analysis**: Analyzes AWS Security Hub, Azure Policy, and GCP Security Center findings
- **Compliance Framework Validation**: Checks against CIS, NIST, PCI-DSS, HIPAA, and SOC2 standards
- **Automated Remediation**: Generates and applies automated remediation for common compliance violations
- **Comprehensive Reporting**: Produces detailed compliance reports with executive summaries

### Supported Cloud Providers

- **AWS**: Security Hub, Config, GuardDuty, IAM, CloudTrail
- **Azure**: Security Center, Policy, Sentinel, Azure AD
- **GCP**: Security Command Center, Cloud Asset Inventory, IAM audit logs

### Compliance Frameworks

- **CIS Controls**: Center for Internet Security benchmarks
- **NIST**: National Institute of Standards and Technology frameworks
- **PCI-DSS**: Payment Card Industry Data Security Standard
- **HIPAA**: Health Insurance Portability and Accountability Act
- **SOC2**: Service Organization Control 2

## Usage

### Basic Compliance Check

```bash
# Run compliance audit across all clouds
skill invoke cloud-compliance-auditor audit --framework CIS --severity HIGH

# Audit specific AWS account
skill invoke cloud-compliance-auditor aws-audit --account-id 123456789012 --region us-east-1

# Generate compliance report
skill invoke cloud-compliance-auditor report --framework NIST --format PDF
```

### Automated Remediation

```bash
# Apply automated remediation (dry-run by default)
skill invoke cloud-compliance-auditor remediate --finding-id aws-001 --dry-run

# Apply remediation with confirmation
skill invoke cloud-compliance-auditor remediate --finding-id azure-002 --confirm
```

### Continuous Monitoring

```bash
# Enable continuous compliance monitoring
skill invoke cloud-compliance-auditor monitor --interval 1h --alert-threshold 5

# Set up compliance alerts
skill invoke cloud-compliance-auditor alerts --email admin@company.com --slack #compliance
```

## Configuration

### Required Environment Variables

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1

# Azure Credentials
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=your_tenant_id
AZURE_SUBSCRIPTION_ID=your_subscription_id

# GCP Credentials
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCP_PROJECT_ID=your_project_id
GCP_ORGANIZATION_ID=your_organization_id
```

### Skill Configuration

```yaml
# .claude/skills/cloud-compliance-auditor/config.yaml
compliance_frameworks:
  - CIS
  - NIST
  - PCI-DSS

severity_thresholds:
  critical: immediate_action
  high: within_24h
  medium: within_72h
  low: within_7d

remediation:
  auto_apply: false
  dry_run: true
  approval_required: true

reporting:
  schedule: "0 9 * * 1"  # Weekly on Monday at 9 AM
  recipients:
    - email: compliance@company.com
    - slack: #compliance-alerts
  formats:
    - JSON
    - PDF
    - HTML
```

## MCP Server Integration

This skill integrates with the `cloud-compliance` MCP server for enhanced capabilities:

### Available MCP Tools

- `aws_security_hub_analysis`: Analyze AWS Security Hub findings
- `azure_policy_compliance`: Check Azure Policy compliance
- `gcp_security_assessment`: Assess GCP Security Center findings
- `multi_cloud_compliance_report`: Generate comprehensive reports
- `automated_remediation_suggestions`: Get remediation recommendations

### MCP Usage Example

```javascript
// Using the MCP server directly
const result = await mcp.call('aws_security_hub_analysis', {
  region: 'us-east-1',
  severity: 'HIGH',
  compliance_standard: 'CIS'
});
```

## Implementation Details

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Cloud APIs    │    │ Compliance Engine│    │  Reporting      │
│                 │    │                  │    │                 │
│ • AWS SDK       │───▶│ • Rule Engine    │───▶│ • PDF Generator │
│ • Azure SDK     │    │ • Policy Checker │    │ • Email Sender  │
│ • GCP SDK       │    │ • Risk Scoring   │    │ • Slack Bot     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Compliance Rules

The skill uses a comprehensive rule set covering:

1. **Identity and Access Management**
   - MFA enforcement
   - Least privilege access
   - Access key rotation
   - Privileged account monitoring

2. **Data Protection**
   - Encryption at rest
   - Encryption in transit
   - Data classification
   - Backup and recovery

3. **Network Security**
   - Security group rules
   - Network segmentation
   - DDoS protection
   - DNS security

4. **Monitoring and Logging**
   - Audit trail completeness
   - Log retention policies
   - Real-time monitoring
   - Alert configuration

### Risk Scoring

Each finding is scored based on:

- **Impact**: Potential business impact
- **Likelihood**: Probability of exploitation
- **Detectability**: Ease of detection
- **Compliance**: Regulatory requirements

Risk scores range from 1-100, with corresponding severity levels.

## Best Practices

### 1. Regular Compliance Scans
- Schedule compliance scans at least weekly
- Run additional scans after major infrastructure changes
- Use different severity thresholds for different environments

### 2. Remediation Strategy
- Start with critical and high-severity findings
- Use dry-run mode before applying remediation
- Document all remediation actions

### 3. Reporting and Communication
- Share compliance reports with stakeholders
- Track compliance trends over time
- Maintain an audit trail of all compliance activities

### 4. Continuous Improvement
- Review and update compliance rules regularly
- Incorporate new regulatory requirements
- Learn from compliance incidents

## Troubleshooting

### Common Issues

**Cloud API Authentication Errors**
```bash
# Verify credentials
aws sts get-caller-identity
az account show
gcloud auth list
```

**Missing Compliance Findings**
```bash
# Check cloud service configuration
skill invoke cloud-compliance-auditor check-config --provider aws
skill invoke cloud-compliance-auditor check-config --provider azure
skill invoke cloud-compliance-auditor check-config --provider gcp
```

**Report Generation Failures**
```bash
# Verify reporting configuration
skill invoke cloud-compliance-auditor test-report --format PDF
skill invoke cloud-compliance-auditor test-email --recipient test@company.com
```

### Debug Mode

```bash
# Enable debug logging
export CLOUD_COMPLIANCE_DEBUG=true
skill invoke cloud-compliance-auditor audit --debug
```

## Integration Examples

### CI/CD Pipeline Integration

```yaml
# .github/workflows/compliance-check.yml
name: Compliance Check
on: [push, pull_request]

jobs:
  compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Compliance Audit
        run: |
          skill invoke cloud-compliance-auditor audit \
            --framework CIS \
            --severity HIGH \
            --output compliance-report.json
      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: compliance-report
          path: compliance-report.json
```

### Slack Integration

```javascript
// Slack bot integration
const complianceResults = await skill.invoke('cloud-compliance-auditor', {
  action: 'audit',
  framework: 'CIS',
  severity: 'HIGH'
});

if (complianceResults.critical_issues > 0) {
  await slack.postMessage({
    channel: '#compliance-alerts',
    text: `🚨 ${complianceResults.critical_issues} critical compliance issues detected!`
  });
}
```

## Performance Considerations

### Optimization Tips

1. **Batch Processing**: Process multiple resources in parallel
2. **Caching**: Cache compliance results for unchanged resources
3. **Incremental Scans**: Only scan changed resources since last scan
4. **Rate Limiting**: Respect cloud API rate limits

### Resource Usage

- **Memory**: ~500MB for large-scale compliance scans
- **CPU**: Moderate usage during rule processing
- **Network**: High usage during cloud API calls
- **Storage**: ~100MB for compliance data and reports

## Security Considerations

### Data Protection

- All cloud credentials are encrypted at rest
- Compliance data is stored in secure, access-controlled storage
- Sensitive findings are redacted in reports

### Access Control

- Principle of least privilege for cloud API access
- Role-based access for compliance reports
- Audit logging for all compliance activities

## Version History

### v1.0.0
- Initial release with AWS, Azure, and GCP support
- CIS and NIST compliance frameworks
- Basic reporting capabilities

### v1.1.0
- Added PCI-DSS and HIPAA frameworks
- Enhanced remediation capabilities
- Improved reporting formats

### v1.2.0
- Multi-cloud compliance reports
- Automated remediation suggestions
- Slack and email integration

## Support and Contributing

### Getting Help

- Documentation: `/docs/cloud-compliance-auditor.md`
- Examples: `/examples/cloud-compliance/`
- Community: `#cloud-compliance` Slack channel

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

### License

This skill is licensed under the MIT License. See LICENSE file for details.

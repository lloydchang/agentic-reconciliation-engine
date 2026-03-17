---
title: Cloud Security Scan Procedure
type: runbook
category: cloud-compliance
version: 1.0.0
last_updated: 2024-03-15
author: Security Team
reviewer: Compliance Officer
tags: [security, compliance, scanning, aws, azure, gcp]
related_docs: [compliance-frameworks.md, remediation-procedures.md]
---

# Cloud Security Scan Procedure

## Overview

This runbook provides step-by-step procedures for conducting comprehensive security scans across multi-cloud environments using the Cloud Compliance Auditor AI Agent Skill.

## Prerequisites

### Required Access
- Cloud provider admin or security auditor permissions
- Access to Cloud Compliance Auditor AI Agent Skill
- Read access to security tools and logs
- Permissions to create security findings and remediation tickets

### Tools and Dependencies
- Cloud Compliance Auditor AI Agent Skill
- Cloud provider CLI tools (AWS CLI, Azure CLI, gcloud)
- Security scanning tools (AWS Security Hub, Azure Security Center, GCP Security Command Center)
- Ticketing system integration (Jira, ServiceNow)

## Procedure

### 1. Initiate Security Scan

#### 1.1 Prepare Scan Configuration
```bash
# Set scan parameters
export SCAN_SCOPE="all"  # Options: all, production, staging, development
export COMPLIANCE_FRAMEWORK="CIS,NIST,SOC2"
export SEVERITY_THRESHOLD="medium"
export REMEDIATION_MODE="dry_run"  # Options: dry_run, auto, manual

# Configure scan targets
export AWS_ACCOUNTS="123456789012,987654321098"
export AZURE_SUBSCRIPTIONS="sub-001,sub-002"
export GCP_PROJECTS="project-prod,project-staging"
```

#### 1.2 Execute Cloud Compliance Scan
```bash
# Run comprehensive security scan
skill invoke cloud-compliance-auditor scan \
  --scope $SCAN_SCOPE \
  --framework $COMPLIANCE_FRAMEWORK \
  --severity-threshold $SEVERITY_THRESHOLD \
  --remediation-mode $REMEDIATION_MODE \
  --accounts $AWS_ACCOUNTS \
  --subscriptions $AZURE_SUBSCRIPTIONS \
  --projects $GCP_PROJECTS
```

### 2. Monitor Scan Progress

#### 2.1 Check Scan Status
```bash
# Monitor scan progress
skill invoke cloud-compliance-auditor status --scan-id <scan-id>

# Get detailed progress information
skill invoke cloud-compliance-auditor progress --scan-id <scan-id> --verbose
```

#### 2.2 Review Scan Metrics
```bash
# Get scan metrics and statistics
skill invoke cloud-compliance-auditor metrics --scan-id <scan-id>

# Export scan results for analysis
skill invoke cloud-compliance-auditor export --scan-id <scan-id> --format json --output scan-results.json
```

### 3. Analyze Security Findings

#### 3.1 Review Findings Summary
```bash
# Get findings summary by severity
skill invoke cloud-compliance-auditor findings-summary --scan-id <scan-id> --group-by severity

# Get findings by compliance framework
skill invoke cloud-compliance-auditor findings-summary --scan-id <scan-id> --group-by framework

# Get findings by resource type
skill invoke cloud-compliance-auditor findings-summary --scan-id <scan-id> --group-by resource-type
```

#### 3.2 Detailed Findings Analysis
```bash
# Get detailed findings for critical issues
skill invoke cloud-compliance-auditor findings --scan-id <scan-id> --severity critical --detailed

# Get findings for specific compliance framework
skill invoke cloud-compliance-auditor findings --scan-id <scan-id> --framework CIS --detailed

# Get findings for specific resource type
skill invoke cloud-compliance-auditor findings --scan-id <scan-id> --resource-type aws_s3_bucket --detailed
```

### 4. Generate Compliance Reports

#### 4.1 Create Executive Summary
```bash
# Generate executive summary report
skill invoke cloud-compliance-auditor report \
  --scan-id <scan-id> \
  --type executive \
  --format pdf \
  --output compliance-executive-summary.pdf
```

#### 4.2 Create Technical Report
```bash
# Generate detailed technical report
skill invoke cloud-compliance-auditor report \
  --scan-id <scan-id> \
  --type technical \
  --format html \
  --include-remediation \
  --output compliance-technical-report.html
```

#### 4.3 Create Compliance Dashboard
```bash
# Generate compliance dashboard data
skill invoke cloud-compliance-auditor dashboard \
  --scan-id <scan-id> \
  --format json \
  --output compliance-dashboard.json
```

### 5. Remediation Planning

#### 5.1 Prioritize Findings
```bash
# Get prioritized remediation list
skill invoke cloud-compliance-auditor prioritize-findings --scan-id <scan-id>

# Get auto-remediation candidates
skill invoke cloud-compliance-auditor auto-remediation-candidates --scan-id <scan-id>
```

#### 5.2 Create Remediation Plan
```bash
# Generate remediation plan
skill invoke cloud-compliance-auditor remediation-plan \
  --scan-id <scan-id> \
  --priority critical,high \
  --include-effort-estimate \
  --output remediation-plan.json
```

### 6. Execute Remediation

#### 6.1 Automated Remediation
```bash
# Apply automated remediation (dry run first)
skill invoke cloud-compliance-auditor remediate \
  --scan-id <scan-id> \
  --auto-only \
  --dry-run

# Apply automated remediation (actual execution)
skill invoke cloud-compliance-auditor remediate \
  --scan-id <scan-id> \
  --auto-only \
  --confirm
```

#### 6.2 Manual Remediation Tasks
```bash
# Create manual remediation tickets
skill invoke cloud-compliance-auditor create-tickets \
  --scan-id <scan-id> \
  --manual-only \
  --ticket-system jira \
  --project SECURITY
```

### 7. Validation and Verification

#### 7.1 Validate Remediation
```bash
# Validate remediation effectiveness
skill invoke cloud-compliance-auditor validate-remediation \
  --scan-id <scan-id> \
  --remediation-id <remediation-id>

# Re-scan after remediation
skill invoke cloud-compliance-auditor rescan \
  --original-scan-id <scan-id> \
  --focus remediated-resources
```

#### 7.2 Compliance Verification
```bash
# Verify compliance status
skill invoke cloud-compliance-auditor verify-compliance \
  --scan-id <scan-id> \
  --framework $COMPLIANCE_FRAMEWORK
```

## Troubleshooting

### Common Issues

#### Scan Initialization Failures
```bash
# Check cloud provider credentials
skill invoke cloud-compliance-auditor check-credentials --provider aws
skill invoke cloud-compliance-auditor check-credentials --provider azure
skill invoke cloud-compliance-auditor check-credentials --provider gcp

# Verify permissions
skill invoke cloud-compliance-auditor check-permissions --provider aws --account 123456789012
```

#### Scan Performance Issues
```bash
# Check scan performance metrics
skill invoke cloud-compliance-auditor performance --scan-id <scan-id>

# Optimize scan configuration
skill invoke cloud-compliance-auditor optimize --scan-id <scan-id> --parallel-scans true
```

#### Findings Processing Errors
```bash
# Debug findings processing
skill invoke cloud-compliance-auditor debug-findings --scan-id <scan-id> --verbose

# Re-process failed findings
skill invoke cloud-compliance-auditor reprocess-findings --scan-id <scan-id> --failed-only
```

### Error Resolution

#### Credential Issues
1. Verify cloud provider credentials are correctly configured
2. Check IAM permissions for required security APIs
3. Ensure credentials haven't expired
4. Validate service account permissions

#### API Rate Limits
1. Implement exponential backoff for API calls
2. Use parallel processing with rate limiting
3. Schedule scans during off-peak hours
4. Request API quota increases if needed

#### Large Environment Scans
1. Break down scans by region or resource type
2. Use incremental scanning for large environments
3. Implement scan result caching
4. Optimize scan scope and filters

## Best Practices

### Scan Configuration
- Use appropriate severity thresholds for different environments
- Schedule regular scans (daily for production, weekly for staging)
- Implement scan result retention policies
- Use consistent naming conventions for scans

### Remediation Strategy
- Prioritize critical and high-severity findings
- Use automated remediation for well-understood issues
- Implement manual review for complex security issues
- Track remediation progress and completion rates

### Compliance Management
- Map findings to specific compliance requirements
- Maintain audit trails for all compliance activities
- Regularly review and update compliance frameworks
- Document exceptions and justifications

## Integration Points

### Incident Management
```bash
# Create security incidents for critical findings
skill invoke cloud-compliance-auditor create-incidents \
  --scan-id <scan-id> \
  --severity critical \
  --incident-system pagerduty
```

### Change Management
```bash
# Create change requests for remediation
skill invoke cloud-compliance-auditor create-change-requests \
  --scan-id <scan-id> \
  --change-system servicenow
```

### Monitoring and Alerting
```bash
# Set up security monitoring alerts
skill invoke cloud-compliance-auditor setup-alerts \
  --severity critical,high \
  --alert-channels slack,email,pagerduty
```

## Reporting and Documentation

### Automated Reports
```bash
# Schedule automated reports
skill invoke cloud-compliance-auditor schedule-reports \
  --type weekly,monthly \
  --recipients security-team@company.com,compliance@company.com \
  --format pdf,html
```

### Documentation Updates
```bash
# Update documentation with scan results
skill invoke cloud-compliance-auditor update-documentation \
  --scan-id <scan-id> \
  --docs-path .claude/references/knowledge-base/
```

## Security Considerations

### Data Protection
- Encrypt scan results and reports
- Implement access controls for sensitive findings
- Use secure channels for data transmission
- Regularly rotate API credentials

### Audit Trail
- Maintain comprehensive audit logs
- Track all scan activities and modifications
- Document remediation decisions and justifications
- Regularly review audit trail completeness

## Performance Optimization

### Scan Efficiency
- Use parallel scanning for multiple accounts
- Implement incremental scanning for large environments
- Cache scan results for unchanged resources
- Optimize API call patterns and batching

### Resource Management
- Monitor scan resource utilization
- Implement scan result cleanup policies
- Use appropriate compute resources for scan processing
- Optimize database queries for findings storage

## Emergency Procedures

### Security Incident Response
1. Immediately initiate emergency scan for affected resources
2. Create security incident tickets for critical findings
3. Implement emergency remediation procedures
4. Notify security team and stakeholders

### Compliance Violations
1. Document compliance violations with detailed evidence
2. Create remediation plans with specific timelines
3. Notify compliance officers and legal team
4. Implement immediate risk mitigation measures

## Maintenance and Updates

### Regular Maintenance
- Update compliance frameworks and rule sets
- Review and optimize scan configurations
- Maintain and update documentation
- Monitor and improve scan performance

### Tool Updates
- Keep Cloud Compliance Auditor AI Agent Skill updated
- Update cloud provider CLI tools and SDKs
- Maintain compatibility with cloud provider API changes
- Test new features and improvements

## Training and Knowledge Transfer

### Team Training
- Conduct regular training on security scanning procedures
- Provide hands-on experience with Cloud Compliance Auditor
- Share best practices and lessons learned
- Maintain training documentation and materials

### Knowledge Management
- Document common issues and solutions
- Share scan results and insights with team
- Maintain knowledge base articles and procedures
- Conduct regular knowledge sharing sessions

---

## Appendix

### A. Quick Reference Commands

```bash
# Quick scan
skill invoke cloud-compliance-auditor scan --scope production --framework CIS

# Critical findings only
skill invoke cloud-compliance-auditor findings --scan-id <id> --severity critical

# Auto-remediation
skill invoke cloud-compliance-auditor remediate --scan-id <id> --auto-only --confirm

# Executive report
skill invoke cloud-compliance-auditor report --scan-id <id> --type executive --format pdf
```

### B. Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SCAN_SCOPE` | Scan scope (all, production, staging, development) | all |
| `COMPLIANCE_FRAMEWORK` | Compliance frameworks (CIS, NIST, SOC2, PCI-DSS, HIPAA) | CIS |
| `SEVERITY_THRESHOLD` | Minimum severity level (low, medium, high, critical) | medium |
| `REMEDIATION_MODE` | Remediation mode (dry_run, auto, manual) | dry_run |

### C. Contact Information

- **Security Team**: security@company.com
- **Compliance Officer**: compliance@company.com
- **Cloud Operations**: cloud-ops@company.com
- **Emergency Contact**: security-emergency@company.com

### D. Related Documents

- [Compliance Frameworks Overview](../governance/compliance-standards/compliance-frameworks.md)
- [Remediation Procedures](remediation-procedures.md)
- [Security Policies](../governance/security-policies/)
- [Incident Response Runbook](../incident-response/security-incident-response.md)

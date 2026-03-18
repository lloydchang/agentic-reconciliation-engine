---
name: compliance-validation
description: >
  Validates pull requests against regulatory, security, and organizational compliance requirements. Ensures changes meet GDPR, HIPAA, PCI-DSS, and other compliance frameworks.
metadata:
  risk_level: low
  autonomy: fully_auto
  layer: temporal
  human_gate: None - informational only
  cost_management:
    token_limit: 350
    cost_threshold: 0.10
    model_preference: "local:llama.cpp"
---

# Compliance Validation Skill

This skill performs automated compliance validation on pull requests, ensuring changes adhere to regulatory requirements, security standards, and organizational policies.

## Compliance Frameworks Supported

### 1. Data Protection & Privacy
- **GDPR**: EU General Data Protection Regulation compliance
- **CCPA**: California Consumer Privacy Act requirements
- **LGPD**: Brazilian General Data Protection Law
- **PIPEDA**: Canadian Personal Information Protection and Electronic Documents Act

### 2. Healthcare & Medical
- **HIPAA**: Health Insurance Portability and Accountability Act
- **HITECH**: Health Information Technology for Economic and Clinical Health Act
- **HITRUST**: Healthcare security framework
- **FDA 21 CFR Part 11**: Electronic records and signatures

### 3. Financial Services
- **PCI-DSS**: Payment Card Industry Data Security Standard
- **SOX**: Sarbanes-Oxley Act compliance
- **GLBA**: Gramm-Leach-Bliley Act privacy requirements
- **FFIEC**: Federal Financial Institutions Examination Council guidelines

### 4. Industry-Specific
- **NIST Cybersecurity Framework**: National Institute of Standards and Technology
- **ISO 27001**: Information security management systems
- **CIS Controls**: Center for Internet Security critical security controls
- **MITRE ATT&CK**: Adversarial tactics, techniques, and common knowledge

## Validation Categories

### 1. Data Handling Compliance
- **Data Classification**: Proper labeling of sensitive data
- **Retention Policies**: Data lifecycle management compliance
- **Cross-Border Transfers**: International data transfer restrictions
- **Consent Management**: User consent and preference handling

### 2. Security Controls
- **Access Controls**: Role-based access and least privilege
- **Encryption Requirements**: Data at rest and in transit encryption
- **Audit Logging**: Comprehensive activity logging and monitoring
- **Incident Response**: Breach notification and response procedures

### 3. Code Quality Standards
- **Secure Coding**: OWASP Top 10 and CWE compliance
- **Dependency Management**: Third-party library security and licensing
- **Configuration Security**: Secure defaults and configuration validation
- **API Security**: RESTful API security and authentication

### 4. Operational Compliance
- **Change Management**: Proper change approval and documentation
- **Risk Assessment**: Security and privacy impact assessments
- **Vendor Management**: Third-party vendor compliance verification
- **Training Requirements**: Security awareness and compliance training

## Automated Validation Rules

### GDPR Compliance Checks
```yaml
gdpr_checks:
  - rule: "data_processing_inventory"
    description: "Verify data processing activities are documented"
    severity: "high"
  - rule: "lawful_basis"
    description: "Ensure lawful basis for data processing"
    severity: "critical"
  - rule: "data_subject_rights"
    description: "Implement data subject access and deletion rights"
    severity: "high"
  - rule: "breach_notification"
    description: "Verify 72-hour breach notification capability"
    severity: "critical"
```

### HIPAA Security Rule Validation
```yaml
hipaa_checks:
  - rule: "access_controls"
    description: "Technical access controls for ePHI"
    severity: "critical"
  - rule: "audit_controls"
    description: "Audit logs for ePHI access and modifications"
    severity: "high"
  - rule: "integrity_protection"
    description: "Data integrity and authentication mechanisms"
    severity: "high"
  - rule: "transmission_security"
    description: "Secure transmission of ePHI"
    severity: "critical"
```

### PCI-DSS Requirements
```yaml
pci_dss_checks:
  - rule: "cardholder_data_protection"
    description: "Never store sensitive authentication data"
    severity: "critical"
  - rule: "encryption_standards"
    description: "Use strong cryptography and security protocols"
    severity: "high"
  - rule: "access_control_measures"
    description: "Restrict access to cardholder data"
    severity: "critical"
  - rule: "network_security"
    description: "Implement network segmentation and firewalls"
    severity: "high"
```

## Integration Points

### Compliance Dashboards
- **Real-time Status**: Compliance posture visualization
- **Violation Tracking**: Historical compliance issues and resolutions
- **Audit Reports**: Automated compliance reporting for auditors
- **Risk Scoring**: Quantitative compliance risk assessment

### Notification Systems
- **Compliance Alerts**: Immediate notification of violations
- **Audit Notifications**: Upcoming audit and review reminders
- **Remediation Tracking**: Compliance issue resolution monitoring
- **Certification Renewals**: Compliance certification expiration tracking

## Usage Examples

### Healthcare PR Validation
```yaml
workflows:
  hipaa-pr-validation:
    on: pull_request
    skills:
      - compliance-validation
    inputs:
      frameworks: ["hipaa", "gdpr"]
      scope: "healthcare_data"
      severity_threshold: "medium"
```

### Financial Services Compliance
```yaml
workflows:
  financial-compliance:
    triggers:
      - files_changed: ["src/payment/**", "config/security/**"]
    skills:
      - compliance-validation
    inputs:
      frameworks: ["pci_dss", "sox"]
      environment: "production"
      require_approval: true
```

### Multi-Framework Validation
```yaml
workflows:
  enterprise-compliance:
    on: pull_request
    steps:
      - skill: compliance-validation
        inputs:
          frameworks: ["gdpr", "ccpa", "iso27001", "nist"]
          custom_rules: "company-security-policy.yaml"
      - skill: risk-assessment
      - gate: compliance_approved
        condition: violations_critical == 0 && violations_high <= 2
```

## Output Format

```json
{
  "summary": {
    "overall_compliance": "compliant",
    "frameworks_checked": ["gdpr", "hipaa", "pci_dss"],
    "total_violations": 3,
    "critical_violations": 0,
    "blocking_issues": false
  },
  "framework_results": {
    "gdpr": {
      "status": "compliant",
      "score": 95,
      "violations": [
        {
          "rule": "data_retention_policy",
          "severity": "medium",
          "description": "Data retention period exceeds recommended limits",
          "recommendation": "Implement automated data purging after retention period"
        }
      ]
    },
    "hipaa": {
      "status": "compliant",
      "score": 98,
      "violations": []
    },
    "pci_dss": {
      "status": "warning",
      "score": 87,
      "violations": [
        {
          "rule": "encryption_key_rotation",
          "severity": "high",
          "description": "Encryption keys not rotated within required timeframe",
          "recommendation": "Implement automated key rotation policy"
        }
      ]
    }
  },
  "recommendations": [
    {
      "framework": "gdpr",
      "priority": "medium",
      "action": "update_data_retention_policy",
      "description": "Review and update data retention schedules"
    },
    {
      "framework": "pci_dss",
      "priority": "high",
      "action": "implement_key_rotation",
      "description": "Deploy automated encryption key rotation"
    }
  ],
  "audit_trail": {
    "validation_timestamp": "2024-01-15T10:30:00Z",
    "validator_version": "2.1.0",
    "rules_version": "2024.Q1",
    "scan_duration_seconds": 45
  }
}
```

## Configuration Options

### Framework-Specific Settings
```yaml
compliance_config:
  gdpr:
    data_classification_required: true
    consent_management_check: true
    breach_notification_test: false
  hipaa:
    ephi_detection_enabled: true
    audit_log_verification: true
    encryption_validation: true
  pci_dss:
    scope_limitation: "cardholder_environment"
    quarterly_scanning: true
    penetration_testing: "annual"
```

### Custom Compliance Rules
```yaml
custom_rules:
  - name: "company_data_handling"
    description: "Internal data handling and classification policy"
    rules:
      - pattern: "sensitive_data"
        action: "flag_for_review"
        severity: "medium"
      - pattern: "pii_fields"
        action: "require_encryption"
        severity: "high"
```

## Violation Remediation

### Automated Fixes
- **Configuration Updates**: Automatic security configuration corrections
- **Documentation Updates**: Compliance documentation generation
- **Alert Configuration**: Monitoring and alerting setup
- **Access Control**: Permission and role adjustments

### Manual Review Requirements
- **Policy Exceptions**: Documented exceptions with approval
- **Risk Acceptances**: Formal risk acceptance documentation
- **Compensating Controls**: Alternative security measures
- **Timeline Extensions**: Compliance deadline extensions with justification

## Reporting and Analytics

### Compliance Metrics
- **Compliance Score Trends**: Historical compliance performance
- **Violation Categories**: Most common compliance issues
- **Framework Coverage**: Compliance framework adoption metrics
- **Remediation Time**: Average time to resolve compliance issues

### Audit Preparation
- **Evidence Collection**: Automated evidence gathering for audits
- **Gap Analysis**: Identification of compliance gaps
- **Remediation Tracking**: Compliance issue resolution progress
- **Certification Readiness**: Assessment of certification readiness

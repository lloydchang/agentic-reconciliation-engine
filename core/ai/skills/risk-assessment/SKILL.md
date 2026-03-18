---
name: risk-assessment
description: >
  Evaluates pull requests for risk levels including security, operational, compliance, and business impact. Provides risk scoring and mitigation recommendations.
metadata:
  risk_level: low
  autonomy: fully_auto
  layer: temporal
  human_gate: None - informational only
  cost_management:
    token_limit: 400
    cost_threshold: 0.10
    model_preference: "local:llama.cpp"
---

# Risk Assessment Automation

This skill performs comprehensive risk assessment of pull requests across multiple dimensions, providing quantitative risk scores and actionable mitigation strategies.

## Risk Dimensions Assessed

### 1. Security Risk
- **Authentication Changes**: Impact on access control mechanisms
- **Data Exposure**: Potential for sensitive data leakage
- **Injection Vulnerabilities**: SQL, XSS, command injection risks
- **Cryptographic Weaknesses**: Weak encryption or key management
- **Dependency Vulnerabilities**: Third-party library security issues

### 2. Operational Risk
- **Performance Impact**: CPU, memory, storage, or network degradation
- **Availability Concerns**: Risk of service downtime or reduced capacity
- **Scalability Issues**: Inability to handle increased load
- **Monitoring Gaps**: Loss of observability or alerting
- **Rollback Complexity**: Difficulty reverting changes if needed

### 3. Compliance Risk
- **Regulatory Violations**: GDPR, HIPAA, PCI-DSS compliance issues
- **Data Sovereignty**: Geographic data storage requirements
- **Audit Trail**: Logging and accountability requirements
- **Retention Policies**: Data lifecycle compliance
- **Access Controls**: Role-based access and least privilege

### 4. Business Impact Risk
- **Revenue Impact**: Potential effect on business operations
- **Customer Experience**: User-facing functionality changes
- **Market Risk**: Competitive positioning implications
- **Legal Exposure**: Contract or liability implications
- **Brand Reputation**: Public perception consequences

## Risk Scoring Methodology

### Quantitative Scoring (1-10 Scale)
- **1-2**: Negligible risk, routine changes
- **3-4**: Low risk, minimal impact potential
- **5-6**: Moderate risk, requires monitoring
- **7-8**: High risk, needs mitigation planning
- **9-10**: Critical risk, requires senior approval

### Qualitative Assessment
- **Scope**: Files, components, services affected
- **Complexity**: Technical difficulty and testing requirements
- **Dependencies**: External systems and teams impacted
- **Timeline**: Urgency and deployment window constraints

## Mitigation Recommendations

### Automatic Recommendations
- **Security Controls**: Additional authentication, encryption, validation
- **Testing Requirements**: Unit tests, integration tests, security scans
- **Monitoring Enhancements**: Additional metrics, alerts, dashboards
- **Operational Safeguards**: Feature flags, canary deployments, rollback plans

### Approval Requirements
- **Peer Review**: Additional reviewers for high-risk changes
- **Security Review**: Mandatory for security-critical modifications
- **Architecture Review**: Complex system changes requiring approval
- **Compliance Review**: Regulatory or legal impact assessments

## Integration Points

- **GitHub Integration**: Automatic PR labeling and required reviewers
- **CI/CD Pipeline**: Gates and quality checks based on risk level
- **Jira/ServiceNow**: Ticket creation for high-risk changes
- **Slack/Teams**: Notification channels for risk alerts

## Usage Examples

```yaml
# High-risk PR workflow
workflows:
  high-risk-pr:
    triggers:
      - risk_score >= 7
    actions:
      - notify: "@security-team"
      - require_reviews: 3
      - schedule: "maintenance-window"
      - create_incident: "high-risk-deployment"

# Compliance-gated workflow
workflows:
  compliance-gated:
    triggers:
      - compliance_impact: "high"
    actions:
      - notify: "@compliance-officer"
      - require_approval: "legal"
      - audit_log: "compliance-review"
```

## Output Format

```json
{
  "overall_risk_score": 7.5,
  "risk_level": "high",
  "dimensions": {
    "security": 8.2,
    "operational": 6.8,
    "compliance": 7.1,
    "business": 7.9
  },
  "critical_findings": [
    {
      "dimension": "security",
      "severity": "critical",
      "description": "Database credential exposure in config file",
      "mitigation": "Move credentials to secure vault, implement rotation"
    }
  ],
  "recommendations": [
    {
      "type": "security_review",
      "priority": "immediate",
      "assignee": "@security-team"
    },
    {
      "type": "rollback_plan",
      "priority": "high",
      "description": "Prepare database backup and rollback script"
    }
  ],
  "approval_requirements": [
    "security_review",
    "architecture_review",
    "compliance_officer"
  ]
}
```

## Configuration

Risk assessment thresholds can be customized:

```yaml
risk_thresholds:
  security:
    critical: 9.0
    high: 7.0
    medium: 5.0
  operational:
    critical: 8.5
    high: 6.5
    medium: 4.5
  compliance:
    critical: 9.5
    high: 8.0
    medium: 6.0
```

## Risk Categories

### Critical Risk (9-10)
- Core infrastructure changes
- Security system modifications
- Data schema alterations
- External API breaking changes

### High Risk (7-8)
- New feature deployments
- Database performance changes
- Third-party integration updates
- Configuration management changes

### Medium Risk (5-6)
- Bug fixes and patches
- Minor feature enhancements
- Documentation updates
- Test improvements

### Low Risk (3-4)
- Code refactoring
- Style and formatting changes
- Comment updates
- Test additions

### Negligible Risk (1-2)
- Documentation updates
- Minor typo corrections
- Metadata changes
- Build configuration tweaks

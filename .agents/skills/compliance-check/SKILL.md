---
name: compliance-check
description: Start and monitor compliance checks for SOC2, GDPR, HIPAA standards. Use when verifying infrastructure compliance, preparing for audits, or ensuring regulatory requirements are met.
argument-hint: "[targetResource] [complianceType] [priority]"
disable-model-invocation: false
user-invocable: true
allowed-tools: 
  - Bash
  - Read
  - Write
  - Grep
---

# Compliance Check Skill

Starts comprehensive compliance workflows using the Temporal AI Agents system to verify that infrastructure and applications meet regulatory standards.

## Usage
```bash
/compliance-check vm-web-server-001 SOC2 high
/compliance-check database-cluster-prod GDPR
/compliance-check all-resources HIPAA critical
```

## Instructions

When this skill is invoked:

1. **Parse Arguments**: Extract targetResource, complianceType, and priority from $ARGUMENTS
2. **Start Compliance Workflow**: Call the Temporal AI Agents API to start compliance check
3. **Monitor Progress**: Track workflow execution and provide status updates
4. **Generate Report**: Create comprehensive compliance report with findings

### Step-by-Step Process

#### 1. Parse Input Arguments
```bash
# Default values if not provided
targetResource="$1" || "all-resources"
complianceType="$2" || "full-scan"  
priority="$3" || "normal"
```

#### 2. Start Compliance Check
Execute API call to Temporal backend:
```bash
curl -X POST http://localhost:8081/api/v1/compliance/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TEMPORAL_API_KEY" \
  -d '{
    "targetResource": "'$targetResource'",
    "complianceType": "'$complianceType'",
    "priority": "'$priority'"
  }'
```

#### 3. Monitor Workflow Progress
Poll workflow status every 5 seconds:
```bash
# Get workflow ID from start response
workflowId="extracted-from-response"

# Monitor loop
while true; do
  status=$(curl -s "http://localhost:8081/api/v1/workflows/$workflowId")
  # Parse and display progress
  if [[ "$status" == *"completed"* ]] || [[ "$status" == *"failed"* ]]; then
    break
  fi
  sleep 5
done
```

#### 4. Generate Compliance Report
Create detailed report with:
- Compliance score (0-100)
- Issues found by category
- Remediation recommendations
- Approval status
- Audit trail

## Compliance Types Supported

### SOC2 (Security, Availability, Processing, Integrity, Confidentiality)
- Access control verification
- Encryption standards validation
- Audit trail completeness
- Incident response procedures

### GDPR (General Data Protection Regulation)
- Data processing consent
- Right to be forgotten implementation
- Data breach notification procedures
- International data transfer compliance

### HIPAA (Health Insurance Portability and Accountability Act)
- Protected health information (PHI) security
- Audit controls validation
- Transmission security verification
- Administrative safeguards assessment

### Full-Scan
- Comprehensive evaluation across all standards
- Integrated compliance dashboard
- Cross-standard requirement analysis

## Priority Levels

- **critical**: Immediate execution, resource-intensive analysis
- **high**: Priority queue, comprehensive scanning
- **normal**: Standard execution, balanced analysis
- **low**: Background execution, basic checks

## Output Format

The skill generates:
1. **Real-time Updates**: Progress indicators during execution
2. **Summary Report**: Compliance score and key findings
3. **Detailed Findings**: Itemized list of compliance issues
4. **Remediation Plan**: Specific actions to achieve compliance
5. **Audit Documentation**: Complete evidence trail

## Integration with Temporal AI Agents

This skill interfaces with:
- `start_compliance_check` workflow function
- `get_compliance_status` monitoring function
- `request_human_review` for failed compliance items
- Infrastructure emulator for safe testing

## Error Handling

- Invalid resource IDs: Provide resource discovery suggestions
- API connectivity issues: Fallback to local compliance checks
- Insufficient permissions: Request elevated access or alternative approaches
- Timeout scenarios: Implement partial reporting with resumption capability

## Supporting Files

- [templates/compliance-report.md](templates/compliance-report.md): Report template
- [scripts/compliance-validator.sh](scripts/compliance-validator.sh): Validation logic
- [assets/compliance-checklist.json](assets/compliance-checklist.json): Requirements database

## Examples

### Basic SOC2 Check
```bash
/compliance-check web-server-prod-001 SOC2 high
```

### GDPR Compliance for All Resources
```bash
/compliance-check all-resources GDPR normal
```

### Critical HIPAA Validation
```bash
/compliance-check patient-database-cluster HIPAA critical
```

## Best Practices

1. **Resource Discovery**: Use `/infrastructure-discovery` to identify target resources
2. **Baseline Establishment**: Run initial compliance check before making changes
3. **Continuous Monitoring**: Schedule regular compliance checks using `/loop`
4. **Documentation**: Keep detailed records of all compliance activities
5. **Human Review**: Always involve human reviewers for critical compliance failures

## Related Skills

- `/security-analysis`: Complementary security vulnerability scanning
- `/infrastructure-discovery`: Resource identification and classification
- `/workflow-management`: Monitor and manage compliance workflows
- `/cost-optimization`: Balance compliance requirements with cost efficiency

## OpenAI Codex Integration

This section documents the OpenAI Codex-style compliance check automation that has been integrated into the Claude skills framework.

### Systematic Compliance Check Approach

When performing compliance checks, follow this systematic approach:

#### 1. Policy Definition
- Define compliance rules and requirements
- Create policy validation criteria
- Document compliance frameworks (SOC2, GDPR, HIPAA, etc.)
- Establish compliance baselines

#### 2. Configuration Analysis
- Examine system configurations against policies
- Check security settings and access controls
- Validate encryption and data protection
- Review logging and monitoring requirements

#### 3. Automated Checks
- Run compliance validation scripts
- Check for policy violations
- Generate compliance reports
- Flag non-compliant resources

#### 4. Remediation Guidance
- Provide specific remediation steps
- Prioritize violations by severity
- Generate compliance tickets or tasks
- Track remediation progress

### Compliance Areas
- **Security**: Access controls, encryption, network security
- **Data Privacy**: Data handling, consent management, retention
- **Infrastructure**: Resource configurations, deployment standards
- **Operational**: Change management, incident response, backup

### Common Checks
```bash
# Security group validation
# IAM policy analysis
# Encryption verification
# Logging configuration check
# Backup validation
```

### Reporting
- Generate compliance dashboards
- Create compliance scorecards
- Export compliance reports
- Track compliance trends over time

### Integration Points
- Connect to policy management systems
- Integrate with ticketing systems
- Link to audit trails
- Sync with governance tools

### File Locations
- Compliance rules: `backend/compliance/`
- Check scripts: `scripts/compliance/`
- Reports: `reports/compliance/`
- Configurations: `config/compliance.yaml`

### Best Practices
- Maintain up-to-date compliance rules
- Document all compliance exceptions
- Regularly review and update policies
- Implement automated remediation where possible
- Keep audit trails for all compliance activities

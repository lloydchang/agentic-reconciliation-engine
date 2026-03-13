---
name: security-analysis
description: Perform comprehensive security analysis with dynamic context injection. Use when scanning for vulnerabilities, analyzing security posture, or responding to security incidents.
argument-hint: "[targetResource] [scanType] [priority]"
context: fork
agent: Explore
allowed-tools: 
  - "Bash(nmap *, nikto *, sqlmap *, metasploit *, curl *, wget *)"
---

# Security Analysis Skill

Advanced security analysis with dynamic context injection and real-time threat intelligence. This skill uses command injection to gather live security data before analysis.

## Usage
```bash
/security-analysis web-server-001 vulnerability high
/security-analysis network-infrastructure full critical
/security-analysis database-cluster configuration normal
```

## Dynamic Context Injection

This skill uses the `!`command`` syntax to inject real-time security data:

### Pre-Analysis Intelligence Gathering
- **Current Threat Landscape**: !`curl -s https://cve.circl.lu/api/last | jq -r '.[0:5] | .[].id'`
- **Active IP Reputation**: !`curl -s "https://api.abuseipdb.com/api/v2/check?ip=$TARGET_IP&maxAgeInDays=7" -H "Key: $ABUSEIPDB_KEY"`
- **Port Scan Results**: !`nmap -sS -O -oX - $TARGET_IP 2>/dev/null | head -50`
- **Web Application Headers**: !`curl -s -I https://$TARGET_DOMAIN | head -20`

### Real-time Security Feeds
- **Malware Hashes**: !`curl -s https://hashdb.openanalysis.net/hash | head -20`
- **CISA Alerts**: !`curl -s https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json | jq -r '.vulnerabilities[0:10] | .[].cveID'`
- **Security Blogs**: !`curl -s https://feeds.feedburner.com/TheHackersNews | head -10`

## Analysis Workflow

### 1. Target Identification & Reconnaissance
```bash
# Dynamic target discovery
TARGET_RESOURCE="$1" || "all-resources"
SCAN_TYPE="$2" || "full"
PRIORITY="$3" || "normal"

# Extract target details from infrastructure emulator
TARGET_DETAILS=!`curl -s "http://localhost:8081/api/v1/resources/$TARGET_RESOURCE" | jq -r '.'`

# Network mapping
NETWORK_MAP=!`nmap -sn 192.168.1.0/24 2>/dev/null | grep "Nmap scan report"`
```

### 2. Vulnerability Assessment
```bash
# CVE database lookup
CVE_DATA=!`curl -s "https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=$SERVICE_NAME" | jq -r '.vulnerabilities[0:10] | .[].cve.id'`

# Service enumeration
SERVICES=!`nmap -sV -oX - $TARGET_IP 2>/dev/null | xpath '//service[@product]' 2>/dev/null`

# Web application analysis
WEB_HEADERS=!`curl -s -I -L https://$TARGET_DOMAIN 2>/dev/null`
```

### 3. Threat Intelligence Integration
```bash
# IOC (Indicators of Compromise) checking
IOC_CHECK=!`curl -s "https://api.threatintelligenceplatform.com/v1/ioc?ip=$TARGET_IP" -H "Authorization: Bearer $TI_API_KEY"`

# Malware analysis
MALWARE_SCAN=!`clamscan --no-summary --detect-pua=yes /path/to/scanned/files 2>/dev/null | head -20`
```

### 4. Security Posture Analysis
```bash
# Configuration review
CONFIG_AUDIT=!`find /etc -name "*.conf" -exec grep -l "password\|secret\|key" {} \; 2>/dev/null | head -10`

# Permission analysis
PERMISSION_AUDIT=!`find /var/www -type f -perm /o+w 2>/dev/null | head -20`

# Log analysis for suspicious activity
LOG_ANALYSIS=!`grep -i "failed\|error\|attack\|intrusion" /var/log/auth.log | tail -20`
```

## Scan Types

### Vulnerability Scan
- CVE matching against NVD database
- Service version enumeration
- Configuration weakness detection
- Patch level assessment

### Malware Scan
- File signature analysis
- Behavioral pattern detection
- Memory analysis for rootkits
- Network traffic analysis

### Configuration Scan
- Security setting validation
- Policy compliance checking
- Hardening assessment
- Best practice verification

### Full Scan
- Comprehensive analysis including all scan types
- Deep system inspection
- Advanced persistent threat detection
- Complete security posture assessment

## Priority Levels

### Critical
- Immediate execution with maximum resources
- Real-time threat intelligence integration
- Automated incident response triggers
- Executive notification

### High
- Priority queue with enhanced scanning
- Detailed vulnerability analysis
- Comprehensive reporting
- Security team notification

### Normal
- Standard scanning procedures
- Balanced resource usage
- Regular reporting format

### Low
- Background execution with minimal impact
- Basic security checks
- Summary reporting only

## Output Format

### Executive Summary
- Risk Level: Critical/High/Medium/Low
- Vulnerabilities Found: X critical, Y high, Z medium
- Overall Security Score: X/100
- Immediate Actions Required: Y

### Technical Details
- Vulnerability list with CVSS scores
- Affected systems and services
- Exploitation difficulty assessment
- Recommended patches and mitigations

### Threat Intelligence
- Active threats targeting similar systems
- Recent CVEs affecting detected services
- IOCs found in environment
- Attack surface analysis

### Remediation Plan
- Immediate actions (0-24 hours)
- Short-term fixes (1-7 days)
- Long-term improvements (1-30 days)
- Continuous monitoring recommendations

## Integration with Temporal AI Agents

### API Endpoints Used
- `start_security_scan`: Initiates security analysis workflow
- `get_security_report`: Retrieves detailed security findings
- `request_human_review`: Escalates critical findings
- `discover_resources`: Identifies targets for analysis

### Workflow Orchestration
1. **Discovery Phase**: Identify target resources and attack surface
2. **Scanning Phase**: Execute selected scan type with dynamic context
3. **Analysis Phase**: Correlate findings with threat intelligence
4. **Reporting Phase**: Generate comprehensive security report
5. **Response Phase**: Trigger automated or manual response actions

## Advanced Features

### Machine Learning Integration
- Anomaly detection in system behavior
- Pattern recognition for attack identification
- Predictive threat analysis
- Automated risk scoring

### Real-time Monitoring
- Continuous security posture monitoring
- Automated alert generation
- Dynamic threat adaptation
- Live dashboard integration

### Compliance Integration
- SOC2 security control validation
- GDPR data protection verification
- HIPAA security safeguards assessment
- Industry-specific compliance checking

## Error Handling & Fallbacks

### Network Connectivity Issues
- Fallback to cached threat intelligence
- Local vulnerability database usage
- Offline scanning capabilities
- Queued analysis when connectivity restored

### API Rate Limiting
- Exponential backoff implementation
- Multiple threat intelligence sources
- Local caching strategies
- Graceful degradation of features

### Resource Constraints
- Adaptive scanning based on available resources
- Prioritized analysis of critical assets
- Background processing for non-critical scans
- Resource usage monitoring and optimization

## Security Considerations

### Data Protection
- Encrypted storage of scan results
- Secure transmission of sensitive data
- Access control for security findings
- Audit trail of all security activities

### Safe Scanning Practices
- Non-destructive scanning methods
- Rate limiting to avoid service disruption
- Backup and rollback procedures
- Isolated scanning environments

### Ethical Considerations
- Authorization verification before scanning
- Responsible disclosure of vulnerabilities
- Compliance with legal requirements
- Privacy protection during analysis

## Supporting Files

- [templates/security-report.md](templates/security-report.md): Security analysis report template
- [scripts/vulnerability-scanner.sh](scripts/vulnerability-scanner.sh): Automated vulnerability scanning
- [assets/threat-integration.json](assets/threat-integration.json): Threat intelligence configuration
- [scripts/incident-response.sh](scripts/incident-response.sh): Automated response procedures

## Examples

### Critical Vulnerability Scan
```bash
/security-analysis production-web-server vulnerability critical
```

### Full Security Assessment
```bash
/security-analysis entire-infrastructure full high
```

### Configuration Security Review
```bash
/security-analysis database-cluster configuration normal
```

## Related Skills

- `/compliance-check`: Regulatory compliance validation
- `/infrastructure-discovery`: Asset identification and classification
- `/workflow-management`: Security workflow orchestration
- `/cost-optimization`: Security cost-benefit analysis

## Best Practices

1. **Authorization**: Always ensure proper authorization before scanning
2. **Impact Assessment**: Understand potential impact of security scans
3. **Documentation**: Maintain detailed records of all security activities
4. **Continuous Monitoring**: Implement ongoing security monitoring
5. **Regular Updates**: Keep security tools and threat intelligence current
6. **Incident Response**: Have clear response procedures for critical findings
7. **Compliance Alignment**: Ensure security activities support compliance requirements

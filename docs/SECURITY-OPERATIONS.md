# Security Operations Guide

## Overview

This guide provides comprehensive security operations procedures for the GitOps Infra Control Plane, including monitoring, incident response, and ongoing security maintenance.

## 🔍 Security Monitoring

### Dashboard Access

**Security Dashboard**: Available in Grafana under "GitOps Security Dashboard"

**Key Metrics to Monitor**:

- Secret access events
- Failed authentication attempts
- Network policy violations
- Pod security issues
- RBAC violations
- Certificate expiry
- Security alerts

### Alert Configuration

**Critical Alerts** (Immediate Response Required):

- Secret exposure detected
- Unauthorized access attempts
- Privileged pod creation
- Network policy violations from external sources

**High Priority Alerts** (Response within 1 hour):

- RBAC violations
- Pod security context issues
- Certificate expiry < 7 days

**Medium Priority Alerts** (Response within 24 hours):

- Secret age > 90 days
- Image security issues
- Audit log volume spikes

### Log Monitoring

**Key Logs to Monitor**:

```bash
# Kubernetes audit logs
kubectl logs -n kube-system -l app=audit-logging

# SealedSecrets controller logs
kubectl logs -n kube-system -l name=sealed-secrets-controller

# Flux CD logs
kubectl logs -n flux-system -l app=kustomize-controller
kubectl logs -n flux-system -l app=helm-controller
```

## 🚨 Incident Response Procedures

### Incident Classification

| Severity | Response Time | Escalation |
|----------|---------------|------------|
| CRITICAL | Immediate | Management + Security Team |
| HIGH | 1 hour | Security Team Lead |
| MEDIUM | 24 hours | DevOps Team |
| LOW | 72 hours | Team Lead |
| INFO | 1 week | Documentation |

### Response Workflow

#### 1. Detection

```bash
# Run security audit
./scripts/security-audit.sh

# Check for active alerts
kubectl get prometheusrules -n monitoring
kubectl get alerts -n monitoring
```

#### 2. Assessment

```bash
# Use incident response automation
./scripts/incident-response.sh secret-exposure <secret_name> <namespace> <severity>

# For unauthorized access
./scripts/incident-response.sh unauthorized-access <user> <resource> <action> <severity>

# For pod security issues
./scripts/incident-response.sh pod-security <pod_name> <namespace> <issue> <severity>
```

#### 3. Containment

- Isolate affected resources
- Apply temporary restrictions
- Rotate compromised secrets
- Block malicious traffic

#### 4. Eradication

- Remove malicious components
- Update security policies
- Patch vulnerabilities
- Clean up evidence

#### 5. Recovery

- Restore services
- Monitor for recurrence
- Update monitoring rules
- Document lessons learned

### Common Incident Types

#### Secret Exposure

```bash
# Immediate response
./scripts/incident-response.sh secret-exposure grafana-credentials monitoring CRITICAL

# Follow-up actions
./scripts/rotate-secrets.sh --push
kubectl get events -n monitoring --field-selector involvedObject.name=grafana-credentials
```

#### Unauthorized Access

```bash
# Investigate unauthorized access
./scripts/incident-response.sh unauthorized-access unknown-user pods create HIGH

# Review user permissions
kubectl get rolebindings,clusterrolebindings --all-namespaces | grep <user>
```

#### Pod Security Issues

```bash
# Handle privileged pods
./scripts/incident-response.sh pod-security privileged-pod default privileged CRITICAL

# Review security contexts
kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.securityContext}{"\n"}{end}'
```

## 🔄 Routine Security Operations

### Daily Tasks

**Morning Security Check**:

```bash
# Run quick security scan
./scripts/security-audit.sh

# Check for new incidents
./scripts/incident-response.sh list

# Review overnight alerts
kubectl get alerts -n monitoring -l severity="critical"
```

**End-of-Day Review**:

```bash
# Generate daily security report
./scripts/security-audit.sh > audit-reports/daily-$(date +%Y%m%d).log

# Check secret ages
find . -name "*secrets.yaml" -exec stat -c "%Y %n" {} \; | sort -n

# Review Git changes for security issues
git log --since="1 day ago" --oneline --grep="security\|secret\|password"
```

### Weekly Tasks

**Monday - Security Review**:

```bash
# Comprehensive security audit
./scripts/security-audit.sh

# Review incident reports
ls -la incident-reports/ | tail -5

# Update security dashboard
# (Manual review of Grafana dashboard)
```

**Wednesday - Policy Review**:

```bash
# Review network policies
kubectl get networkpolicies --all-namespaces

# Review RBAC policies
kubectl get roles,rolebindings --all-namespaces

# Check for policy violations
kubectl get events --all-namespaces --field-selector reason="NetworkPolicyReject"
```

**Friday - Maintenance**:

```bash
# Rotate old secrets if needed
find . -name "*secrets.yaml" -mtime +90 -exec dirname {} \; | sort -u | while read dir; do
    echo "Considering rotation for secrets in: $dir"
done

# Update security documentation
# (Manual review and updates)
```

### Monthly Tasks

**First Week - Security Assessment**:

```bash
# Full infrastructure security audit
./scripts/security-audit.sh

# Penetration testing coordination
# (External team coordination)

# Security training review
# (Team training session)
```

**Third Week - Compliance Check**:

```bash
# Compliance audit
./scripts/security-audit.sh --compliance

# Policy compliance verification
kubectl get networkpolicies --all-namespaces -o yaml | yq eval '.items[].spec' -

# Generate compliance report
# (Automated report generation)
```

## 🛡️ Security Maintenance

### Secret Management

**Regular Rotation Schedule**:

- Database passwords: Every 90 days
- Service accounts: Every 180 days
- API keys: Immediately upon compromise
- Certificates: Before expiry (30 days buffer)

**Rotation Procedure**:

```bash
# Check for secrets needing rotation
find . -name "*secrets.yaml" -mtime +90

# Rotate secrets
./scripts/rotate-secrets.sh --push

# Verify rotation success
kubectl get secrets --all-namespaces -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.creationTimestamp}{"\n"}{end}'
```

### Network Policy Maintenance

**Monthly Review**:

```bash
# Check policy effectiveness
kubectl get networkpolicies --all-namespaces -o yaml

# Review denied traffic
kubectl get events --all-namespaces --field-selector reason="NetworkPolicyReject"

# Update policies as needed
# (Manual policy updates)
```

### RBAC Maintenance

**Quarterly Review**:

```bash
# Review role assignments
kubectl get roles,rolebindings --all-namespaces
kubectl get clusterroles,clusterrolebindings

# Check for unused permissions
# (Manual audit of role usage)

# Update roles based on principle of least privilege
# (Manual role updates)
```

## 📊 Security Metrics and KPIs

### Key Performance Indicators

**Security Health Score**:

- Secret management compliance: 100%
- Network policy coverage: >90%
- RBAC compliance: 100%
- Incident response time: <1 hour for critical

**Incident Metrics**:

- Mean Time to Detect (MTTD): <15 minutes
- Mean Time to Respond (MTTR): <1 hour (critical)
- Incident recurrence rate: <5%
- False positive rate: <10%

**Compliance Metrics**:

- Policy compliance rate: 95%
- Audit finding resolution: 100% within SLA
- Security training completion: 100%

### Reporting

**Daily Security Brief**:

- New incidents
- Critical alerts
- Security health status

**Weekly Security Report**:

- Incident trends
- Policy compliance
- Risk assessment
- Recommended actions

**Monthly Security Review**:

- Comprehensive security posture
- Compliance status
- Risk mitigation progress
- Security investment ROI

## 🔧 Tools and Automation

### Security Scripts

**Available Scripts**:

- `scripts/security-audit.sh` - Comprehensive security audit
- `scripts/rotate-secrets.sh` - Automated secret rotation
- `scripts/incident-response.sh` - Incident response automation
- `scripts/test-secret-deployment.sh` - Secret deployment testing

**Usage Examples**:

```bash
# Full security audit
./scripts/security-audit.sh

# Rotate all secrets
./scripts/rotate-secrets.sh --push

# Respond to incident
./scripts/incident-response.sh secret-exposure grafana-credentials monitoring CRITICAL

# Test secret deployment
./scripts/test-secret-deployment.sh
```

### Monitoring Tools

**Grafana Dashboard**:

- Security metrics visualization
- Alert status overview
- Incident tracking

**Prometheus Alerts**:

- Automated alerting rules
- Severity-based notification
- Integration with incident response

**Kubernetes Audit Logging**:

- Comprehensive audit trail
- Security event capture
- Compliance reporting

## 🚨 Emergency Procedures

### Security Incident Escalation

**Immediate Escalation (Critical)**:

1. Call security team: +1-xxx-xxx-xxxx
2. Enable incident response war room
3. Notify management
4. Begin containment procedures

**Standard Escalation (High)**:

1. Create incident ticket
2. Notify security team lead
3. Begin investigation
4. Update stakeholders

### Disaster Recovery

**Security Disaster Recovery**:

1. Isolate affected systems
2. Activate backup infrastructure
3. Restore from clean backups
4. Verify system integrity
5. Resume operations with enhanced monitoring

### Communication Procedures

**Internal Communication**:

- Slack #security-incidents channel
- Email notifications to security team
- Management briefings

**External Communication**:

- Customer notifications (if required)
- Regulatory reporting (if required)
- Public statements (if required)

## 📚 Training and Awareness

### Security Training

**New Team Members**:

- GitOps security overview
- Secret management procedures
- Incident response basics
- Security tool usage

**Ongoing Training**:

- Monthly security briefings
- Quarterly incident response drills
- Annual security certification
- Threat intelligence updates

### Security Awareness

**Best Practices**:

- Never commit secrets to Git
- Use SealedSecrets for all sensitive data
- Follow principle of least privilege
- Report suspicious activity immediately

**Common Pitfalls**:

- Hardcoding passwords in configs
- Using overly permissive RBAC
- Ignoring security alerts
- Skipping security reviews

## 🔄 Continuous Improvement

### Security Program Evolution

**Regular Reviews**:

- Quarterly security program review
- Annual risk assessment
- Bi-annual penetration testing
- Ongoing threat modeling

**Process Improvements**:

- Automate manual security tasks
- Enhance monitoring capabilities
- Improve incident response procedures
- Update security policies

**Technology Updates**:

- Evaluate new security tools
- Update security configurations
- Patch security vulnerabilities
- Adopt security best practices

---

**Document Version**: 1.0.0  
**Last Updated**: $(date)  
**Next Review**: $(date -d "+30 days" +%Y-%m-%d)  
**Security Team**: <security@company.com>  
**Incident Response**: <incidents@company.com>

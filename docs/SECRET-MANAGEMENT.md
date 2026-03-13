# Secret Management in GitOps Infra Control Plane

## Overview

This document outlines the secure secret management practices implemented in the GitOps Infra Control Plane to prevent secret exposure and ensure compliance with security best practices.

## Security Incident Response

### Recent Fix
A security incident was identified where hardcoded passwords were exposed in the Prometheus HelmRelease configuration. The following actions were taken:

1. **Identified exposed secrets:**
   - Grafana admin password: `admin123`
   - Grafana secret key: `SW2YcwTIb9zpOOhoPsMm`
   - Database password: `grafana`
   - SMTP password placeholder: `smtp_password`

2. **Remediation steps:**
   - Created SealedSecret resource for Grafana credentials
   - Updated HelmRelease to use secret references
   - Removed all hardcoded passwords from configuration

## Secret Management Architecture

### SealedSecrets Controller
We use Bitnami's SealedSecrets controller for secure secret management:
- Secrets are encrypted at rest in Git
- Only the cluster with the private key can decrypt secrets
- Prevents secret exposure in version control

### Secret Structure
```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: application-credentials
  namespace: target-namespace
spec:
  encryptedData:
    SECRET_KEY: <encrypted-value>
  template:
    metadata:
      name: application-credentials
      namespace: target-namespace
    type: Opaque
```

## Best Practices

### 1. Never Hardcode Secrets
- ❌ `password: admin123`
- ✅ `passwordFromSecret: true`

### 2. Use Secret References in HelmReleases
```yaml
env:
  - name: DATABASE_PASSWORD
    valueFrom:
      secretKeyRef:
        name: database-credentials
        key: PASSWORD
```

### 3. Encrypt Secrets Before Commit
```bash
# Create a regular secret first
kubectl create secret generic app-secrets \
  --from-literal=PASSWORD=your-secure-password \
  --dry-run=client -o yaml > secret.yaml

# Seal the secret
kubeseal --format yaml < secret.yaml > sealed-secret.yaml
```

### 4. Validate Secret References
Ensure all secret references in HelmReleases point to existing SealedSecrets.

## Secret Rotation

### Regular Rotation Schedule
- Database passwords: Every 90 days
- Service accounts: Every 180 days
- API keys: Immediately upon compromise

### Rotation Process
1. Generate new credentials
2. Update SealedSecret with new values
3. Apply to cluster
4. Verify application connectivity
5. Remove old credentials

## Monitoring and Alerting

### Secret Access Monitoring
- Monitor Kubernetes audit logs for secret access
- Alert on unusual secret access patterns
- Track secret creation and deletion events

### Compliance Checks
- Regular scans for hardcoded secrets in Git
- Automated validation of secret references
- Security policy enforcement

## Emergency Procedures

### If Secrets Are Exposed
1. **Immediate Actions:**
   - Rotate all exposed secrets immediately
   - Revoke any compromised credentials
   - Update SealedSecrets with new values

2. **Investigation:**
   - Review access logs during exposure window
   - Identify potential unauthorized access
   - Document the incident timeline

3. **Prevention:**
   - Implement pre-commit hooks for secret detection
   - Add automated security scanning
   - Provide security training to team members

## Tools and Commands

### Creating SealedSecrets
```bash
# Install kubeseal
go install github.com/bitnami-labs/sealed-secrets/v2/cmd/kubeseal@latest

# Create and seal a secret
kubectl create secret generic my-secret \
  --from-literal=KEY=value \
  --dry-run=client -o yaml | kubeseal --format yaml > sealed-secret.yaml
```

### Validating Secret References
```bash
# Check for hardcoded secrets
grep -r "password\|secret\|key" --include="*.yaml" --include="*.yml" .

# Validate secret references
kubectl get sealedsecrets --all-namespaces
```

## Contact and Support

For security incidents or questions about secret management:
- Security Team: security@company.com
- DevOps Team: devops@company.com
- Incident Response: incidents@company.com

## References

- [SealedSecrets Documentation](https://github.com/bitnami-labs/sealed-secrets)
- [Kubernetes Secret Management](https://kubernetes.io/docs/concepts/configuration/secret/)
- [GitOps Security Best Practices](https://fluxcd.io/docs/security/)

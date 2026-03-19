---
name: certificate-rotation
description: >
  Automates TLS certificate lifecycle management across all GitOps-managed clusters.
  Detects expiring certificates, generates new ones, updates manifests, and handles
  rotation workflows with proper validation and rollback capabilities.
metadata:
  risk_level: medium
  autonomy: conditional
  layer: temporal
  human_gate: PR approval required for production certificates
  cost_limit: 100
  execution_model: "local:llama.cpp"
  planning_model: "local:llama.cpp"
  cost_management:
    token_limit: 100
    cost_threshold: 0.10 # USD
    model_preference: "local:llama.cpp"
  execution:
    background_enabled: true
    parallel_capable: true
    notification_channels: ["slack", "github"]
  dependencies:
    required_skills: []
    conflicts_with: []
    order_constraints: []
---

# Certificate Rotation Skill

This skill automates the complete TLS certificate lifecycle management process across GitOps-managed infrastructure.

## When to Use

Use this skill when:
- Certificates are approaching expiration (within 30 days)
- You need to bulk update certificates across multiple clusters
- Certificate authorities or signing methods need to be changed
- Security policies require certificate refresh

## What This Skill Does

### 1. Certificate Discovery
- Scans all GitOps repositories for TLS certificate references
- Identifies certificates in Kubernetes secrets, config maps, and manifests
- Checks certificate expiration dates and chain validity
- Maps certificate dependencies and relationships

### 2. Expiration Analysis
- Calculates time to expiration for all certificates
- Prioritizes certificates based on criticality and expiration timeline
- Generates expiration reports and recommendations
- Identifies certificates requiring immediate attention

### 3. Certificate Generation
- Generates new certificates using configured CA or external providers
- Maintains existing certificate formats and attributes
- Handles wildcard certificates and SAN extensions
- Supports multiple certificate providers (Let's Encrypt, internal CA, etc.)

### 4. Manifest Updates
- Updates Kubernetes manifests with new certificate data
- Maintains GitOps workflow and PR processes
- Preserves certificate metadata and annotations
- Handles certificate bundle updates

### 5. Validation and Testing
- Validates new certificates before deployment
- Tests certificate chain verification
- Performs connectivity and handshake tests
- Validates certificate compatibility with services

### 6. Rollback Planning
- Creates rollback plans for each certificate change
- Maintains backup of previous certificates
- Documents rollback procedures and timelines
- Tests rollback scenarios in non-production

## Implementation Details

### Required Tools and Access
- Access to GitOps repositories (read/write)
- Certificate generation tools (openssl, cert-manager, etc.)
- Kubernetes cluster access for validation
- Communication channels for notifications

### Configuration Requirements
```yaml
certificate_rotation:
  expiration_threshold: 30 # days
  batch_size: 10 # certificates per batch
  validation_timeout: 300 # seconds
  rollback_retention: 90 # days
  notification_channels:
    - slack: "#cert-rotation"
    - email: "security-team@company.com"
  certificate_authorities:
    - name: "internal-ca"
      type: "vault"
      config: {...}
    - name: "letsencrypt"
      type: "acme"
      config: {...}
```

### Execution Steps

1. **Pre-flight Checks**
   - Validate tool availability and permissions
   - Check Git repository status and branch protection
   - Verify cluster connectivity and access rights

2. **Certificate Discovery**
   - Run: `scripts/discover-certificates.sh`
   - Output: Certificate inventory and expiration analysis

3. **Manual Review and Planning**
   - Review discovered certificates and expiration dates
   - Plan rotation schedule based on criticality
   - Prepare new certificates using organization's CA tools

4. **Validation and Testing**
   - Test new certificates in non-production environments
   - Verify certificate chain and compatibility
   - Document rollback procedures

5. **PR Creation**
   - Update GitOps manifests with new certificates
   - Create pull request following GitOps workflow
   - Include summary and testing evidence

6. **Notification**
   - Send notifications to configured channels
   - Include summary and next steps

## Success Criteria

- All expiring certificates are identified and updated
- New certificates pass validation tests
- GitOps workflows are maintained
- No service disruptions during rotation
- Rollback plans are documented and tested

## Error Handling

### Common Issues
- Certificate generation failures
- Git repository conflicts
- Validation test failures
- Cluster connectivity issues

### Recovery Procedures
- Failed certificate generation: Retry with different parameters
- Git conflicts: Manual resolution and re-run
- Validation failures: Investigate and fix certificate issues
- Cluster issues: Pause rotation and notify administrators

## Monitoring and Observability

### Metrics to Track
- Number of certificates rotated
- Time to complete rotation
- Certificate validation success rate
- Rollback frequency
- Service disruption incidents

### Logging Requirements
- Detailed execution logs
- Certificate change audit trail
- Error and warning messages
- Performance metrics

## Security Considerations

- Private key protection and access controls
- Certificate authority authentication
- Git repository access restrictions
- Audit trail for all certificate operations
- Compliance with security policies

## Integration Points

- **GitOps Tools**: Flux, ArgoCD for deployment
- **Certificate Management**: cert-manager, Vault
- **Monitoring**: Prometheus, Grafana for metrics
- **Alerting**: AlertManager for notifications
- **Security Tools**: Vulnerability scanners, compliance checkers

## References

Load these files when needed:
- `scripts/discover-certificates.sh` - Certificate discovery script

## External Resources

For certificate generation and validation, refer to:
- **cert-manager documentation**: https://cert-manager.io/docs/
- **Vault PKI secrets engine**: https://www.vaultproject.io/docs/secrets/pki
- **OpenSSL documentation**: https://www.openssl.org/docs/
- Organization-specific CA tools and security policies

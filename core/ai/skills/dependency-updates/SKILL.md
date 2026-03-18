---
name: dependency-updates
description: >
  Automates dependency updates across GitOps-managed infrastructure including
  container images, Helm charts, Terraform modules, and software packages.
  Scans for outdated dependencies, checks compatibility, and creates PRs with updates.
metadata:
  risk_level: medium
  autonomy: conditional
  layer: temporal
  human_gate: PR approval required for major version changes
  cost_limit: 80
  execution_model: "local:llama.cpp"
  planning_model: "local:llama.cpp"
  cost_management:
    token_limit: 80
    cost_threshold: 0.08 # USD
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

# Dependency Updates Skill

This skill automates the complete dependency management process across GitOps-managed infrastructure, ensuring all components stay up-to-date with security patches and feature updates.

## When to Use

Use this skill when:
- Dependencies are outdated and need updates
- Security vulnerabilities require immediate patching
- New features or improvements are available in newer versions
- Regular maintenance cycles require dependency refresh

## What This Skill Does

### 1. Dependency Discovery
- Scans GitOps repositories for dependency references
- Identifies container images, Helm charts, Terraform modules
- Maps dependency relationships and constraints
- Builds comprehensive dependency inventory

### 2. Version Analysis
- Checks current versions against latest available
- Identifies security vulnerabilities in outdated versions
- Analyzes breaking changes between versions
- Prioritizes updates based on risk and benefit

### 3. Compatibility Testing
- Tests new versions in non-production environments
- Validates configuration compatibility
- Checks for breaking changes in APIs
- Performs integration testing

### 4. Update Planning
- Creates phased update strategies
- Plans rollback procedures
- Schedules updates to minimize disruption
- Coordinates with dependent services

### 5. Manifest Updates
- Updates GitOps manifests with new versions
- Maintains version constraints and pinning
- Updates documentation and changelogs
- Preserves custom configurations

### 6. Validation and Testing
- Validates updated configurations
- Performs smoke tests on updated services
- Checks for runtime compatibility
- Validates security improvements

## Implementation Details

### Required Tools and Access
- Access to GitOps repositories (read/write)
- Container registry access
- Helm chart repositories
- Terraform module registry access
- CI/CD pipeline integration

### Configuration Requirements
```yaml
dependency_updates:
  scan_interval: 7 # days
  auto_update_minor: true
  auto_update_patch: true
  auto_update_major: false
  security_only: false
  test_environments:
    - staging
    - testing
  notification_channels:
    - slack: "#dependency-updates"
    - email: "devops-team@company.com"
  registries:
    - name: "docker-hub"
      type: "docker"
      config: {...}
    - name: "github-container"
      type: "ghcr"
      config: {...}
```

### Execution Steps

1. **Pre-flight Checks**
   - Validate tool availability and permissions
   - Check Git repository status
   - Verify registry connectivity

2. **Dependency Discovery**
   - Run: `scripts/discover-dependencies.sh`
   - Output: `dependency-inventory.json`

3. **Version Analysis**
   - Run: `scripts/analyze-versions.sh`
   - Output: `version-analysis.json`

4. **Compatibility Testing**
   - Run: `scripts/test-compatibility.sh`
   - Output: `test-results.json`

5. **Update Planning**
   - Run: `scripts/plan-updates.sh`
   - Output: `update-plan.json`

6. **Manifest Updates**
   - Run: `scripts/update-dependencies.sh`
   - Output: Updated GitOps manifests

7. **Validation**
   - Run: `scripts/validate-updates.sh`
   - Output: `validation-report.json`

8. **PR Creation**
   - Run: `scripts/create-pr.sh`
   - Output: Pull request with dependency updates

## Success Criteria

- All outdated dependencies are identified
- Security vulnerabilities are patched
- Updates pass compatibility tests
- No service disruptions during updates
- Rollback plans are documented

## Error Handling

### Common Issues
- Registry connectivity problems
- Version incompatibilities
- Configuration conflicts
- Test failures

### Recovery Procedures
- Registry issues: Retry with alternative registries
- Incompatibilities: Manual version selection
- Conflicts: Manual resolution and re-run
- Test failures: Investigate and fix issues

## Monitoring and Observability

### Metrics to Track
- Number of dependencies updated
- Time to complete updates
- Test success rate
- Rollback frequency
- Security vulnerabilities patched

### Logging Requirements
- Detailed execution logs
- Dependency change audit trail
- Error and warning messages
- Performance metrics

## Security Considerations

- Registry authentication and access controls
- Vulnerability scanning of new versions
- Supply chain security validation
- Audit trail for all dependency changes
- Compliance with security policies

## Integration Points

- **Container Registries**: Docker Hub, GCR, ECR, GHCR
- **Helm Repositories**: Official, private, custom
- **Terraform Registry**: Module registry, provider registry
- **Security Tools**: Trivy, Grype, Snyk
- **CI/CD**: GitHub Actions, GitLab CI, Jenkins

## References

Load these files when needed:
- `scripts/discover-dependencies.sh` - Dependency discovery script
- `scripts/analyze-versions.sh` - Version analysis script
- `scripts/test-compatibility.sh` - Compatibility testing script
- `references/dependency-formats.md` - Dependency format specifications
- `references/security-policies.md` - Security policy requirements

---
name: manifest-generator
description: |
  Generate, validate, and optimize Kubernetes manifests, Helm charts, Kustomize overlays, and infrastructure-as-code with AI-powered best practices and security validation.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Manifest Generator — AI-Powered Infrastructure Manifest Creation

Intelligent generation and validation of Kubernetes manifests, Helm charts, Kustomize configurations, and infrastructure-as-code templates with security scanning, best practices enforcement, and multi-environment optimization.

## When to invoke
- Creating new Kubernetes deployments from application specifications.
- Generating infrastructure manifests for cloud resources.
- Converting existing configurations to GitOps-ready formats.
- Optimizing manifests for production security and scalability.
- Implementing configuration management across environments.
- Automating manifest generation for CI/CD pipelines.

## Capabilities
- **Kubernetes manifest generation**: Deployments, Services, ConfigMaps, Secrets, etc.
- **Helm chart creation**: Automated chart generation with dependencies.
- **Kustomize overlay management**: Environment-specific customizations.
- **Infrastructure-as-code**: Terraform, CloudFormation, ARM templates.
- **Security validation**: Automated security scanning and hardening.
- **Multi-environment support**: Development, staging, production variants.

## Invocation patterns
```bash
/manifest-generator create --resource=deployment --app=my-app --image=nginx:latest
/manifest-generator helm --chart=my-app --version=1.0.0 --dependencies=postgresql
/manifest-generator kustomize --base=base --overlay=production --patches=strategic
/manifest-generator validate --manifest=deployment.yaml --security-scan=true
/manifest-generator optimize --target=production --cost-reduction=true
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `resource` | Kubernetes resource type. | `deployment`, `service` |
| `app` | Application name. | `my-web-app` |
| `image` | Container image reference. | `nginx:1.21` |
| `chart` | Helm chart name. | `my-app-chart` |
| `overlay` | Kustomize overlay name. | `production` |
| `security-scan` | Enable security validation. | `true` |

## Output contract
```json
{
  "operationId": "MG-2026-0315-01",
  "manifests": [
    {
      "type": "kubernetes",
      "resource": "deployment",
      "content": {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
          "name": "my-app",
          "namespace": "production"
        },
        "spec": {
          "replicas": 3,
          "template": {
            "spec": {
              "containers": [
                {
                  "name": "app",
                  "image": "nginx:latest",
                  "securityContext": {
                    "runAsNonRoot": true,
                    "runAsUser": 101
                  }
                }
              ]
            }
          }
        }
      },
      "validation": {
        "security": "passed",
        "bestPractices": "passed",
        "warnings": []
      }
    }
  ],
  "recommendations": [
    {
      "type": "security",
      "action": "Add network policies",
      "priority": "high",
      "impact": "Isolate pod traffic"
    }
  ]
}
```

## Dispatcher integration
**Triggers:**
- `new-application`: Application deployment requiring manifests
- `infrastructure-change`: Infrastructure updates needing manifests
- `security-update`: Security hardening requiring manifest changes
- `environment-promotion`: Environment-specific manifest generation

**Emits:**
- `manifests-generated`: Validated manifests ready for deployment
- `security-violations`: Security issues found in generated manifests
- `optimization-complete`: Optimized manifests with performance improvements
- `deployment-ready`: Complete manifest set ready for GitOps deployment

## AI intelligence features
- **Smart templating**: Context-aware manifest generation based on application type
- **Security hardening**: Automatic application of security best practices
- **Performance optimization**: Resource limit recommendations and HPA configuration
- **Dependency analysis**: Automatic detection and configuration of service dependencies
- **Compliance automation**: Regulatory compliance rule application

## Human gates
- **Production deployments**: Critical manifests require SRE review
- **Security changes**: Manifests affecting security posture need validation
- **Cost impacts >$1000/month**: Resource allocation changes require approval
- **Breaking changes**: API version updates need stakeholder approval

## Telemetry and monitoring
- Manifest generation success rates
- Security violation detection accuracy
- Template usage and effectiveness metrics
- Deployment success rates from generated manifests
- Time-to-deployment improvements

## Testing requirements
- Manifest syntax validation and schema compliance
- Security scanning integration testing
- Multi-environment deployment simulation
- Performance impact assessment
- Compliance rule validation

## Failure handling
- **Template errors**: Fallback to basic templates with warnings
- **Validation failures**: Detailed error messages with remediation steps
- **Security violations**: Block deployment with required fixes
- **Dependency conflicts**: Automatic resolution suggestions
- **API changes**: Version compatibility warnings and alternatives

## Related skills
- **config-validator**: Manifest validation and policy checking
- **deployment-validation**: Pre-deployment manifest testing
- **policy-as-code**: Security and compliance policy integration
- **gitops-workflow**: GitOps integration for manifest deployment

## Security considerations
- Automated security scanning of all generated manifests
- Sanitization of sensitive configuration values
- RBAC permission validation for deployed resources
- Audit trails for all manifest generation operations
- Encryption of secrets and sensitive data

## Performance characteristics
- Generation time: <5 seconds for standard manifests
- Validation speed: <2 seconds per manifest
- Template library: 500+ pre-built, optimized templates
- Concurrent processing: 100+ manifest generations per minute
- Memory usage: <100MB for complex multi-resource generation

## Scaling considerations
- Distributed generation across multiple nodes
- Template caching and pre-compilation
- Batch processing for large-scale deployments
- Horizontal scaling based on generation load
- CDN distribution of template libraries

## Success metrics
- Manifest accuracy: >98% syntactically correct generations
- Security compliance: >95% generated manifests pass security scans
- Deployment success: >90% of generated manifests deploy successfully
- Time savings: 70% reduction in manual manifest creation time
- Error reduction: 80% fewer deployment failures from manifest issues

## API endpoints
```yaml
# REST API
POST /api/v1/manifests/generate
POST /api/v1/manifests/validate
POST /api/v1/manifests/optimize
POST /api/v1/manifests/helm

# GraphQL
mutation GenerateManifest($resource: String!, $app: String!) {
  generateManifest(resource: $resource, app: $app) {
    content
    validation {
      security
      bestPractices
    }
  }
}
```

## CLI usage
```bash
# Install
npm install -g @agentskills/manifest-generator

# Generate deployment
manifest-generator create --resource=deployment --app=my-app --image=nginx:latest

# Create Helm chart
manifest-generator helm --chart=my-app --version=1.0.0

# Validate manifest
manifest-generator validate --manifest=deployment.yaml --security-scan=true
```

## Configuration
```yaml
manifestGenerator:
  templates:
    kubernetes:
      baseImages:
        - nginx:latest
        - alpine:latest
      securityDefaults:
        runAsNonRoot: true
        readOnlyRootFilesystem: true
    helm:
      chartRepository: https://charts.example.com
      defaultVersion: "1.0.0"
  validation:
    securityScanners:
      - trivy
      - checkov
    policyChecks:
      - pod-security-standards
      - network-policies
  environments:
    production:
      replicas: 3
      resources:
        limits:
          cpu: "1"
          memory: "1Gi"
  security:
    auditLogging: true
    secretEncryption: true
```

## Examples

### Kubernetes deployment generation
```bash
/manifest-generator create --resource=deployment --app=my-app --image=nginx:latest --env=production

# Generated: Complete deployment manifest with security hardening
# Security: Non-root user, read-only filesystem, resource limits
# Best practices: Health checks, anti-affinity, rolling updates
# Validation: All security checks passed
# Ready for: GitOps deployment to production
```

### Helm chart creation
```bash
/manifest-generator helm --chart=my-app --dependencies=postgresql,rabbitmq --version=1.0.0

# Created: Complete Helm chart with dependencies
# Components: Deployment, Service, ConfigMap, Secret
# Dependencies: PostgreSQL and RabbitMQ subcharts
# Security: Encrypted secrets, RBAC roles
# Testing: Included test manifests and CI pipeline
```

### Security validation
```bash
/manifest-generator validate --manifest=deployment.yaml --security-scan=true

# Validation: Security scan completed
# Issues found: 2 medium-risk vulnerabilities
# Fixes applied: Updated base image, added security context
# Compliance: CIS Kubernetes benchmarks met
# Recommendation: Add network policies for isolation
```

## Migration guide

### From manual manifest creation
1. Analyze existing manifests and identify patterns
2. Configure manifest-generator with organizational standards
3. Generate replacement manifests with validation
4. Test in development environment before production
5. Implement automated generation in CI/CD pipelines

### From existing tools
- **kubectl dry-run**: manifest-generator provides validated, production-ready manifests
- **Helm template**: Enhanced with security scanning and optimization
- **Kustomize**: AI-powered overlay generation and conflict resolution
- **Terraform**: Infrastructure manifest generation with compliance

## Troubleshooting

### Common issues
- **Template conflicts**: Review configuration and override settings
- **Validation failures**: Check security policies and compliance rules
- **Dependency resolution**: Verify chart repositories and versions
- **Environment overrides**: Ensure proper overlay configuration
- **Resource conflicts**: Check namespace and naming conventions

### Debug mode
```bash
manifest-generator --debug create --resource=deployment --app=my-app --verbose
# Shows: template selection, parameter binding, validation steps
```

## Future roadmap
- Multi-cluster manifest generation and synchronization
- AI-powered manifest optimization and cost prediction
- Integration with GitOps operators for automated deployment
- Advanced security scanning with threat modeling
- Real-time manifest validation in CI/CD pipelines
- Support for emerging platforms (WASM, serverless containers)

---

*Last updated: March 15, 2026*
*Version: 1.0.0*

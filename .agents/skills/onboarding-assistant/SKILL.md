---
name: onboarding-assistant
description: |
  Build and operate the Internal Developer Portal plus golden-path templates with AI-guided onboarding, templating, and dispatcher telemetry.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Onboarding Assistant — Intelligent Developer Experience Platform

AI-powered developer onboarding platform providing golden-path templates, self-service provisioning, and guided workflows for infrastructure and application deployment across enterprise environments.

## When to invoke
- New team members joining requiring development environment setup.
- New projects needing standardized infrastructure provisioning.
- Technology stack evaluation and golden-path template creation.
- Developer experience optimization and workflow automation.
- Self-service portal management and template curation.
- Compliance and security integration for developer workflows.

## Capabilities
- **Golden-path templates**: Curated, production-ready infrastructure templates.
- **Self-service provisioning**: Guided workflows for environment setup.
- **Developer portal**: Centralized hub for tools, documentation, and resources.
- **Compliance automation**: Security and compliance checks in onboarding flows.
- **Workflow orchestration**: Multi-step onboarding process automation.
- **Analytics and insights**: Usage patterns and developer experience metrics.

## Invocation patterns
```bash
/onboarding-assistant setup --team=platform-team --stack=react-k8s --environment=dev
/onboarding-assistant template --create=my-app-template --base=web-app --customizations=security
/onboarding-assistant portal --configure --integrations=github,slack,jira
/onboarding-assistant guide --new-hire=john.doe --role=backend-developer
/onboarding-assistant analyze --usage --timeframe=30d --team=platform
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `team` | Target development team. | `platform-team` |
| `stack` | Technology stack identifier. | `react-k8s`, `spring-boot` |
| `environment` | Target environment. | `dev`, `staging`, `prod` |
| `template` | Template name or identifier. | `my-app-template` |
| `role` | Developer role for guidance. | `backend-developer` |
| `integrations` | External tool integrations. | `github,slack,jira` |

## Output contract
```json
{
  "operationId": "OA-2026-0315-01",
  "onboarding": {
    "team": "platform-team",
    "members": [
      {
        "name": "john.doe",
        "role": "backend-developer",
        "status": "in-progress",
        "progress": {
          "completed": ["environment-provisioned", "access-granted"],
          "pending": ["code-repository-setup", "ci-pipeline-configured"],
          "percentage": 60
        },
        "resources": {
          "developmentEnvironment": "ready",
          "documentation": "https://portal.company.com/docs/backend-developer",
          "slackChannels": ["#platform-team", "#backend-devs"],
          "repositories": ["platform/backend-service"]
        }
      }
    ],
    "templates": [
      {
        "name": "spring-boot-k8s",
        "compliance": "passed",
        "security": "scanned",
        "usage": 45
      }
    ]
  },
  "recommendations": [
    {
      "action": "add-monitoring-template",
      "reason": "Improve observability adoption",
      "impact": "Better system monitoring and alerting"
    }
  ]
}
```

## Dispatcher integration
**Triggers:**
- `new-team-member`: Developer onboarding workflow initiation
- `new-project`: Project scaffolding and template selection
- `template-update`: Golden-path template maintenance and updates
- `compliance-change`: Security policy updates requiring template changes
- `usage-analytics`: Developer experience optimization opportunities

**Emits:**
- `onboarding-started`: Developer onboarding process initiated
- `environment-ready`: Development environment provisioned and configured
- `template-created`: New golden-path template available
- `portal-updated`: Developer portal changes deployed
- `insights-generated`: Developer experience analytics and recommendations

## AI intelligence features
- **Personalized guidance**: Role-based onboarding paths and recommendations
- **Template optimization**: ML-driven template improvement based on usage patterns
- **Workflow automation**: Intelligent process orchestration and decision making
- **Compliance intelligence**: Automated policy application and validation
- **Experience analytics**: Developer journey analysis and bottleneck identification

## Human gates
- **Production access**: Sensitive environment access requires manager approval
- **Security policies**: Compliance-related changes need security team review
- **Template publishing**: Golden-path templates require technical review
- **Cost impacts**: Resource provisioning above thresholds needs approval

## Telemetry and monitoring
- Onboarding completion rates and time-to-productivity
- Template usage and success rates
- Developer satisfaction scores
- Portal engagement metrics
- Compliance violation rates in self-service flows

## Testing requirements
- End-to-end onboarding workflow testing
- Template validation across different environments
- Portal functionality and integration testing
- Performance testing under concurrent usage
- Security testing of self-service capabilities

## Failure handling
- **Provisioning failures**: Automatic rollback and alternative template selection
- **Access issues**: Escalation to appropriate teams with detailed context
- **Template errors**: Fallback to basic templates with manual intervention
- **Integration failures**: Degraded mode operation with manual workarounds
- **Compliance blocks**: Clear guidance on required actions for approval

## Related skills
- **developer-self-service**: Portal and template management integration
- **deployment-validation**: Template validation before publishing
- **policy-as-code**: Compliance integration in templates
- **gitops-workflow**: GitOps integration for environment provisioning

## Security considerations
- Multi-factor authentication for sensitive operations
- Role-based access control for template management
- Audit trails for all onboarding and provisioning activities
- Secure credential management in development environments
- Compliance scanning of all golden-path templates

## Performance characteristics
- Environment provisioning: <15 minutes for standard setups
- Template generation: <5 seconds for pre-built templates
- Portal response time: <2 seconds for standard queries
- Concurrent users: Support for 1000+ simultaneous users
- Template library: 200+ curated templates with instant access

## Scaling considerations
- Distributed provisioning across multiple cloud regions
- Horizontal scaling of portal services
- Template caching and CDN distribution
- Queue-based processing for high-volume onboarding
- Multi-tenant architecture for enterprise deployments

## Success metrics
- Time-to-productivity: <2 hours average for new developers
- Self-service adoption: >80% of provisioning through portal
- Template success rate: >95% successful deployments
- Developer satisfaction: >4.5/5 average rating
- Compliance rate: >99% of environments meet security standards

## API endpoints
```yaml
# REST API
POST /api/v1/onboarding/setup
POST /api/v1/onboarding/template
POST /api/v1/onboarding/guide
POST /api/v1/onboarding/portal

# GraphQL
mutation StartOnboarding($team: String!, $members: [String!]!) {
  startOnboarding(team: $team, members: $members) {
    operationId
    status
    estimatedCompletion
  }
}
```

## CLI usage
```bash
# Install
npm install -g @agentskills/onboarding-assistant

# Setup team environment
onboarding-assistant setup --team=platform-team --stack=react-k8s

# Create golden-path template
onboarding-assistant template --create=my-app-template --base=web-app

# Guide new hire onboarding
onboarding-assistant guide --new-hire=john.doe --role=backend-developer
```

## Configuration
```yaml
onboardingAssistant:
  portal:
    url: https://portal.company.com
    integrations:
      github:
        org: company
        token: ${GITHUB_TOKEN}
      slack:
        workspace: company
        token: ${SLACK_TOKEN}
  templates:
    goldenPaths:
      - name: react-k8s
        stack: react
        platform: kubernetes
        compliance: required
      - name: spring-boot
        stack: java
        platform: kubernetes
        security: enhanced
    customizations:
      security: [network-policies, rbac, secrets-management]
      monitoring: [prometheus, grafana, alerting]
  environments:
    dev:
      autoProvision: true
      resourceLimits: standard
    staging:
      autoProvision: false
      approvalRequired: true
  security:
    mfaRequired: true
    auditLogging: true
    complianceScanning: true
```

## Examples

### New developer onboarding
```bash
/onboarding-assistant guide --new-hire=john.doe --role=backend-developer --team=platform

# Onboarding: Initiated for John Doe (Backend Developer)
# Environment: Development environment provisioning started
# Resources: Repository access granted, Slack channels joined
# Documentation: Role-specific guides and best practices provided
# Timeline: Full productivity expected in 4 hours
# Next steps: Code repository setup, CI pipeline configuration
```

### Golden-path template creation
```bash
/onboarding-assistant template --create=ecommerce-api --base=spring-boot --customizations=security,monitoring

# Template: ecommerce-api created from spring-boot base
# Customizations: Security hardening, monitoring integration added
# Compliance: CIS benchmarks, SOC2 requirements validated
# Testing: Automated tests included, security scanning passed
# Publishing: Template available in developer portal
# Usage: 3 teams already using similar patterns
```

### Portal analytics and optimization
```bash
/onboarding-assistant analyze --usage --timeframe=30d --team=platform

# Analytics: 45 onboarding workflows completed this month
# Bottlenecks: Environment provisioning taking 25 minutes average
# Optimization: Template caching implemented, reduced to 12 minutes
# Recommendations: Add self-service database provisioning
# Impact: 50% reduction in onboarding time expected
```

## Migration guide

### From manual onboarding processes
1. Document current onboarding workflows and identify pain points
2. Configure onboarding-assistant with organizational templates
3. Migrate existing documentation to portal format
4. Implement automated provisioning for common environments
5. Train teams on self-service capabilities and best practices

### From existing developer portals
- **Backstage**: onboarding-assistant provides AI-powered guidance
- **Internal wikis**: Enhanced with interactive workflows and automation
- **Custom scripts**: Replaced with validated, monitored templates
- **Manual provisioning**: Automated with compliance and security checks

## Troubleshooting

### Common issues
- **Environment provisioning timeouts**: Check resource quotas and cloud limits
- **Template validation failures**: Review compliance requirements and configurations
- **Integration authentication**: Verify API tokens and permissions
- **Portal access issues**: Check network policies and authentication settings
- **Template conflicts**: Resolve version conflicts and dependency issues

### Debug mode
```bash
onboarding-assistant --debug setup --team=platform-team --verbose
# Shows: provisioning steps, template selection, integration calls
```

## Future roadmap
- AI-powered developer skill assessment and personalized learning paths
- Predictive resource provisioning based on project requirements
- Advanced analytics for developer productivity optimization
- Integration with AI coding assistants for accelerated onboarding
- Multi-cloud golden-path templates with cost optimization
- Quantum-resistant security for enterprise developer environments

---

*Last updated: March 15, 2026*
*Version: 1.0.0*

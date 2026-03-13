# Agent Behavior Rules

This document outlines the core behavioral constraints and governance rules that govern all AI agent operations within the Temporal AI Agents sandbox. These rules ensure safe, auditable, and predictable agent behavior.

## Core Principles

### Safety First
- **Never execute destructive operations without explicit approval**
- All agent actions must maintain system stability and data integrity
- Critical operations require human oversight and confirmation

### Audit Trail
- **All agent actions must be logged and traceable**
- Every operation generates comprehensive audit logs with full context
- Logs include user identity, timestamp, resources affected, and operation outcomes

### Human Oversight
- **Critical decisions require human review**
- High-risk operations trigger human-in-the-loop checkpoints
- Escalation protocols ensure human judgment for complex scenarios

### Idempotency
- **Operations should be safe to retry**
- Agent actions should produce the same result when executed multiple times
- State verification ensures consistent outcomes across retries

## Repository Access Rules

### Allowed Directories
- **Read/write access:**
  - `backend/` - Go Temporal workflows and activities
  - `frontend/` - React/TypeScript Backstage application
  - `cli/` - Command-line interface components
  - `docs/` - Documentation and interface specifications
- **Read-only access:**
  - Root configuration files (README.md, package.json, etc.)
- **Forbidden modifications:**
  - `dist/`, `build/`, or generated files
  - Migration files (use skills instead)
  - Infrastructure configurations without approval
  - Protected branches

## Workflow Execution Rules

### Trigger Conditions
- **Use SKILL.md files for specialized workflows**
- Require explicit user approval for destructive operations
- Validate inputs before executing workflows
- Maintain state consistency across retries

### Error Handling
- **Log all failures with context**
- Retry transient failures automatically (up to 3 attempts)
- Escalate critical failures to human operators
- Provide meaningful error messages with actionable guidance

## Code Generation Rules

### Standards Compliance
- **Follow TypeScript/JavaScript best practices**
- Use established patterns from existing codebase
- Include proper error handling and logging
- Add comprehensive tests for new functionality

### File Organization
- **Place new components in appropriate directories**
- Follow naming conventions from existing code
- Update imports and dependencies correctly
- Maintain clean git history with descriptive commits

## Security Constraints

### Command Restrictions
- **No direct shell execution without tool approval**
- No network requests to unapproved endpoints
- No file system operations outside allowed paths
- No database modifications without migration workflows

### Data Protection
- **Never expose sensitive configuration**
- Sanitize all user inputs before processing
- Use secure communication channels (HTTPS/TLS)
- Respect data retention policies and compliance requirements

## Testing Requirements

### Before Committing
- **Run all existing tests**: `npm test`
- **Lint code**: `npm run lint`
- **Build successfully**: `npm run build`
- **Update documentation** for API changes

### Workflow Validation
- **Test workflows with mock data first**
- Verify error handling paths and edge cases
- Check resource cleanup on failures
- Validate state persistence across workflow lifecycle

## Deployment Rules

### Staging Environment
- **Deploy to staging before production**
- Run integration tests in staging
- Verify monitoring and logging setup
- Perform security scans before promotion

### Production Deployment
- **Require code review approval**
- Use blue-green deployment strategy
- Monitor key metrics post-deployment
- Maintain rollback plan and procedures

## Communication Standards

### User Interaction
- **Provide clear, actionable feedback**
- Explain complex operations in simple terms
- Offer progress updates for long-running tasks
- Suggest next steps when appropriate

### Error Reporting
- **Include error codes and descriptions**
- Provide troubleshooting guidance
- Suggest contact information for issues
- Log errors with full context for debugging

## Interface-Specific Rules

### REST API Usage
- **Use proper HTTP methods and status codes**
- Validate all inputs and outputs
- Rate limit requests appropriately
- Document API endpoints clearly with examples

### MCP Server Interaction
- **Follow MCP protocol specifications**
- Handle tool registration correctly
- Manage resource subscriptions properly
- Provide comprehensive tool metadata

### CLI Operations
- **Use consistent command structure**
- Provide help text and examples
- Support both interactive and scripted modes
- Handle signals gracefully (SIGINT, SIGTERM)

### GUI/Dashboard Access
- **Ensure responsive design**
- Provide accessibility features (WCAG compliance)
- Include loading states and error handling
- Support keyboard navigation

### AI Assistant Integration
- **Follow SKILL.md specifications**
- Provide clear instructions and examples
- Handle edge cases gracefully
- Maintain conversation context

## Monitoring and Observability

### Required Metrics
- **Workflow execution times and success rates**
- Error rates by component and skill
- Resource utilization (CPU, memory, network)
- User interaction patterns and adoption

### Logging Standards
- **Use structured logging with consistent fields**
- Include correlation IDs for request tracing
- Log security events appropriately
- Maintain audit trails for compliance

## Scaling Considerations

### Performance Optimization
- **Optimize workflow execution paths**
- Cache frequently accessed data
- Use efficient algorithms and data structures
- Monitor resource consumption patterns

### Concurrency Management
- **Handle concurrent workflow executions**
- Prevent resource conflicts with proper locking
- Implement proper locking mechanisms
- Support horizontal scaling across instances

## Emergency Procedures

### System Outages
- **Activate backup workflows if available**
- Notify stakeholders of issues
- Provide status updates regularly
- Restore services with minimal downtime

### Security Incidents
- **Isolate affected systems**
- Preserve evidence for investigation
- Communicate transparently with users
- Implement remediation measures promptly

## Development Workflow

### Feature Development
1. **Create issue/ticket for work**
2. **Implement changes following rules above**
3. **Write/update tests**
4. **Update documentation**
5. **Submit pull request for review**

### Code Review Process
- **Review code for security issues**
- Verify compliance with agent rules
- Test functionality thoroughly
- Ensure documentation is updated
- Approve only after all checks pass

## Skill System Specifications

### Complete Skill Index
The following 28 skills are available for automated operations. Each skill follows the Agent Skills specification from agentskills.io.

| Trigger keywords | Skill to load | Human Gate Required |
|------------------|---------------|---------------------|
| terraform, provision infra, IaC, drift detect | `terraform-provisioning` | `apply` in prod |
| pipeline, CI/CD, build failure, DORA | `cicd-pipeline-monitor` | Re-trigger prod |
| incident, alert, P1, P2, outage, degraded | `incident-triage-runbook` | Novel P0/P1 decisions |
| tenant, onboard, new customer, offboard | `tenant-lifecycle-manager` | Offboard/delete |
| scan, CVE, compliance, checkov, trivy | `compliance-security-scanner` | No (scan only) |
| SLA, SLO, error budget, breach | `sla-monitoring-alerting` | No (monitoring only) |
| deploy, rollout, smoke test, canary gate | `deployment-validation` | GO/NO-GO in prod |
| KPI, metrics, report, DORA, quarterly | `kpi-report-generator` | Before send |
| runbook, documentation, ADR, wiki | `runbook-documentation-gen` | No |
| email, comms, announcement, stakeholder | `stakeholder-comms-drafter` | Always (never auto-sends) |
| kubernetes, cluster, AKS, node pool, upgrade | `kubernetes-cluster-manager` | Any prod cluster change |
| cost, spend, waste, FinOps, savings | `cost-optimisation` | Resource deletion |
| secret, certificate, rotation, Key Vault, cert-manager | `secrets-certificate-manager` | Root CA rotation |
| migrate, migration, move workload, cutover | `workload-migration` | Prod cutover |
| policy, OPA, Gatekeeper, governance, tagging | `policy-as-code` | Deny-all policy changes |
| capacity, forecast, headroom, growth | `capacity-planning` | No (analysis only) |
| monitoring, Prometheus, Grafana, Loki, tracing | `observability-stack` | Prod alerting changes |
| networking, VNet, VPC, private endpoint, DNS, NSG | `multi-cloud-networking` | Hub firewall changes |
| database, PostgreSQL, SQL, backup, restore, failover | `database-operations` | PITR restore, failover |
| disaster recovery, DR, failover, RPO, RTO, drill | `disaster-recovery` | Any prod failover |
| GitOps, ArgoCD, Flux, sync, ApplicationSet | `gitops-workflow` | Prod promotion |
| service mesh, Istio, mTLS, circuit breaker, traffic split | `service-mesh` | Strict mTLS in prod |
| container, image, ACR, scan, sign, promote | `container-registry` | Prod registry push |
| developer portal, Backstage, self-service, golden path | `developer-self-service` | Enterprise resource requests |
| audit, SIEM, Sentinel, security event, log query | `audit-siem` | No (read-only queries) |
| change request, CAB, change freeze, risk score | `change-management` | Major/emergency changes |
| chaos, load test, resilience, fault injection, k6 | `chaos-load-testing` | Any prod chaos |
| onboard tenant, P1 incident, QBR, full workflow | `orchestrator` | Per constituent skill |

For any request matching multiple keywords, load the `orchestrator` skill first to determine if a composite workflow applies.

## Identity & Role

You are a world-class engineer and cloud architect powering Cloud AI Agent.

You:
- Automate operational tasks end-to-end using the skills above
- Never take destructive or irreversible actions without explicit human confirmation
- Always log your reasoning step-by-step before executing commands
- Report results in the structured JSON schema defined in each skill
- Escalate to humans when confidence is low or risk is high
- Prefer idempotent operations; always verify state before and after changes

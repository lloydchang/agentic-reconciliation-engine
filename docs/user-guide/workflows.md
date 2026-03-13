# Workflows

The AI Agents Sandbox enables complex multi-agent orchestration through composite workflows that coordinate multiple skills in sequence. Workflows can be triggered automatically on schedules or invoked through natural language requests.

## How Workflows Work

Workflows are pre-defined sequences of skills that work together to accomplish complex operational tasks. Each workflow:

- Coordinates multiple AI agents working in parallel or sequence
- Includes human-in-the-loop checkpoints for critical decisions
- Provides comprehensive status tracking and error handling
- Can be triggered by schedules, events, or direct requests

## The 10 Composite Workflows

### WF-01: Full Tenant Onboarding
**Trigger:** "Onboard [tenant] as enterprise tier in [region]"  
**Steps:** 13  
**Skills:** terraform-provisioning, kubernetes-cluster-manager, secrets-certificate-manager, multi-cloud-networking, database-operations, developer-self-service, observability-stack, policy-as-code, audit-siem, compliance-security-scanner, cost-optimisation, capacity-planning, gitops-workflow

**What it does:**
1. Provisions infrastructure (VMs, networks, storage)
2. Sets up Kubernetes cluster with monitoring
3. Configures secrets management and certificates
4. Deploys database with HA configuration
5. Creates developer portal access
6. Implements governance policies
7. Sets up audit logging
8. Performs initial compliance scan
9. Configures cost monitoring
10. Validates capacity planning
11. Enables GitOps deployments
12. Generates onboarding documentation
13. Sends completion notifications

### WF-02: P0/P1 Incident Response
**Trigger:** "Take over P0/P1 incident response"  
**Steps:** 9  
**Skills:** incident-triage-runbook, observability-stack, runbook-documentation-gen, stakeholder-comms-drafter, compliance-security-scanner, audit-siem, sla-monitoring-alerting, change-management, orchestrator

**What it does:**
1. Assesses incident severity and impact
2. Gathers observability data and metrics
3. Generates incident runbook and response plan
4. Drafts stakeholder communications
5. Performs security analysis if applicable
6. Reviews audit logs for related events
7. Monitors SLA compliance during incident
8. Documents change management decisions
9. Coordinates follow-up actions and post-mortem

### WF-03: Weekly Compliance Scan
**Trigger:** Automatic (Monday 06:00 UTC)  
**Steps:** 6  
**Skills:** compliance-security-scanner, policy-as-code, audit-siem, runbook-documentation-gen, kpi-report-generator, stakeholder-comms-drafter

**What it does:**
1. Scans all resources for compliance violations
2. Validates policy enforcement
3. Reviews audit logs for suspicious activity
4. Updates compliance documentation
5. Generates compliance KPI reports
6. Drafts stakeholder notifications for issues

### WF-04: Monthly Executive Report
**Trigger:** Automatic (1st of month 07:00 UTC)  
**Steps:** 7  
**Skills:** kpi-report-generator, sla-monitoring-alerting, cost-optimisation, capacity-planning, compliance-security-scanner, runbook-documentation-gen, stakeholder-comms-drafter

**What it does:**
1. Aggregates all platform KPIs and metrics
2. Analyzes SLA performance and error budgets
3. Reviews cost optimization opportunities
4. Assesses capacity utilization trends
5. Summarizes compliance posture
6. Generates comprehensive executive report
7. Drafts stakeholder communications (requires human approval to send)

### WF-05: Pre-Release Readiness Check
**Trigger:** "Is v[X] ready to release?"  
**Steps:** 7  
**Skills:** deployment-validation, cicd-pipeline-monitor, compliance-security-scanner, chaos-load-testing, observability-stack, container-registry, gitops-workflow

**What it does:**
1. Validates deployment manifests and configurations
2. Reviews CI/CD pipeline status and test results
3. Performs security and compliance scanning
4. Executes chaos engineering tests
5. Validates observability and monitoring setup
6. Checks container image security and provenance
7. Confirms GitOps deployment readiness

### WF-06: QBR Preparation
**Trigger:** "Prepare the Q[N] QBR deck"  
**Steps:** 8  
**Skills:** kpi-report-generator, cost-optimisation, capacity-planning, compliance-security-scanner, runbook-documentation-gen, stakeholder-comms-drafter, sla-monitoring-alerting, change-management

**What it does:**
1. Compiles quarterly performance metrics
2. Analyzes cost trends and optimization achievements
3. Reviews capacity planning and utilization
4. Summarizes compliance improvements
5. Documents major incidents and changes
6. Assesses SLA performance
7. Reviews change management effectiveness
8. Generates comprehensive QBR presentation (requires human approval)

### WF-07: New Cluster Provisioning
**Trigger:** "Provision a new [env] cluster in [region]"  
**Steps:** 7  
**Skills:** terraform-provisioning, kubernetes-cluster-manager, secrets-certificate-manager, policy-as-code, observability-stack, gitops-workflow, service-mesh

**What it does:**
1. Provisions cloud infrastructure with Terraform
2. Deploys Kubernetes cluster with required configuration
3. Sets up secrets management and certificate authorities
4. Implements governance policies and admission controllers
5. Deploys comprehensive observability stack
6. Configures GitOps tooling (ArgoCD/Flux)
7. Sets up service mesh for traffic management

### WF-08: Security Incident Response
**Trigger:** "Sentinel fired — investigate [alert]"  
**Steps:** 4  
**Skills:** audit-siem, incident-triage-runbook, compliance-security-scanner, stakeholder-comms-drafter

**What it does:**
1. Analyzes security event details and context
2. Reviews related audit logs and patterns
3. Performs targeted security scanning
4. Drafts incident response communications

### WF-09: DR Drill Execution
**Trigger:** "Run the quarterly DR drill"  
**Steps:** 5  
**Skills:** disaster-recovery, database-operations, observability-stack, runbook-documentation-gen, stakeholder-comms-drafter

**What it does:**
1. Initiates disaster recovery procedures
2. Tests database failover and restoration
3. Validates observability during failover
4. Documents drill results and lessons learned
5. Generates post-drill reports and communications

### WF-10: Platform Team Onboarding
**Trigger:** "Onboard the [team name] engineering team"  
**Steps:** 13  
**Skills:** developer-self-service, gitops-workflow, observability-stack, secrets-certificate-manager, policy-as-code, compliance-security-scanner, audit-siem, runbook-documentation-gen, kubernetes-cluster-manager, container-registry, cicd-pipeline-monitor, change-management, stakeholder-comms-drafter

**What it does:**
1. Creates team access and permissions
2. Sets up GitOps repositories and workflows
3. Configures monitoring and alerting
4. Provisions secrets and certificates
5. Applies team-specific policies
6. Performs security assessment
7. Enables audit logging
8. Generates team documentation
9. Creates Kubernetes namespaces and RBAC
10. Sets up container registry access
11. Configures CI/CD pipelines
12. Updates change management processes
13. Sends onboarding completion notifications

## Workflow Architecture

### Orchestrator Skill
All composite workflows are coordinated by the `orchestrator` skill (S18), which:

- Parses natural language requests to identify appropriate workflows
- Manages workflow state and progress tracking
- Handles inter-skill communication and data flow
- Implements human-in-the-loop checkpoints
- Provides comprehensive error handling and rollback

### Skill Dependencies
Workflows leverage complex skill interdependencies:

```
orchestrator (S18)
        │
        ├── tenant-lifecycle-manager (S04)
        │       ├── terraform-provisioning (S01)
        │       ├── kubernetes-cluster-manager (S11)
        │       ├── multi-cloud-networking (S19)
        │       ├── database-operations (S20)
        │       └── secrets-certificate-manager (S13)
        │
        ├── incident-triage-runbook (S03)
        │       ├── observability-stack (S17)
        │       ├── runbook-documentation-gen (S09)
        │       └── stakeholder-comms-drafter (S10)
        │
        ├── deployment-validation (S07)
        │       ├── cicd-pipeline-monitor (S02)
        │       ├── gitops-workflow (S22)
        │       └── container-registry (S24)
        │
        ├── compliance-security-scanner (S05)
        │       ├── policy-as-code (S15)
        │       ├── audit-siem (S26)
        │       └── secrets-certificate-manager (S13)
        │
        └── kpi-report-generator (S08)
                ├── sla-monitoring-alerting (S06)
                ├── cost-optimisation (S12)
                └── capacity-planning (S16)
```

## Monitoring Workflows

### Temporal UI
Monitor workflow execution in real-time at `http://localhost:8080`

### Status Tracking
```bash
# Check workflow status
curl http://localhost:8081/workflow/status?id=<workflow-id>

# Signal workflow continuation
curl -X POST http://localhost:8081/workflow/signal/<workflow-id> \
  -d '{"signal": "approval", "value": true}'
```

### CLI Monitoring
```bash
# List active workflows
./cli workflow status

# Monitor specific workflow
./cli workflow status <workflow-id>
```

## Custom Workflows

You can create custom workflows by:

1. Defining skill sequences in workflow templates
2. Adding human gate checkpoints
3. Configuring error handling and rollback procedures
4. Setting up monitoring and alerting

See **[Extending](../developer-guide/extending.md)** for details on creating custom workflows.

## Next Steps

- Learn about individual **[Skills](../user-guide/skills-reference.md)**
- Understand **[Agent Behavior](../developer-guide/agent-behavior.md)** and governance
- Explore **[Troubleshooting](../user-guide/troubleshooting.md)** common issues

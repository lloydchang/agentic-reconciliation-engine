# Operational Procedures

This document outlines the operational protocols, human-in-the-loop procedures, and workflow execution standards that govern agent operations in the Temporal AI Agents sandbox.

## Reasoning Protocol

Before executing any non-trivial operation, agents must follow this systematic reasoning process:

### 8-Step Operational Protocol

1. **State current environment** — Confirm cluster, tenant, region, and environment context
2. **Identify the skill** — Verify which SKILL.md specification applies to the operation
3. **Check for change freeze** — Query `change-management` skill if operating in production environment
4. **Risk assess** — Evaluate risk score; if >50, request human confirmation
5. **Show the plan** — Present exact commands and steps to be executed
6. **Execute step by step** — Perform operations sequentially with full logging
7. **Validate** — Run post-action health checks and verification
8. **Report** — Return results in standardized JSON schema format

## Human Gates & Safety Controls

Certain operations require explicit human confirmation and cannot be bypassed:

### Critical Operations (Always Require Approval)

#### Destructive / Irreversible Actions
- `terraform destroy` on any environment
- Deleting a Kubernetes namespace or cluster
- Dropping or truncating a database
- Deleting more than 5 resources in a single operation
- Removing a tenant from the registry (offboard)

#### High-Blast-Radius Changes
- Any change affecting more than 20 tenants simultaneously
- Modifying hub VNet peering or firewall policy
- Changing a shared Key Vault access policy
- Disabling a security control (mTLS, policy enforcement)

#### Production Deployments
- Any deployment to `prod` environment outside maintenance windows
- Rolling back a production database migration
- Triggering a region failover

#### Authentication & Access
- Creating or deleting cluster-admin role bindings
- Rotating the root CA certificate
- Issuing an emergency break-glass credential
- Disabling an Azure AD account

#### Financial Impact
- Any action projected to increase monthly spend by more than $5,000
- Deleting reserved instances or savings plans

### Human Gate Format

When human approval is required:

```
⚠️  HUMAN GATE: [action description]
    Impact: [what will change]
    Reversible: [Yes/No — how to undo if No]
    Type YES to proceed or NO to abort:
```

## Output Standards

All operation results must follow this standardized JSON wrapper:

```json
{
  "agent_run": {
    "request": "verbatim user request",
    "skill_used": "skill-name",
    "workflow": "WORKFLOW-XX or standalone",
    "started_at": "ISO8601",
    "completed_at": "ISO8601",
    "status": "success|failure|partial|pending_human_gate",
    "steps": [
      { "step": 1, "action": "description", "result": "success|failure", "output": "..." }
    ],
    "human_gates_triggered": [],
    "errors": [],
    "result": { /* skill-specific output schema */ }
  }
}
```

## Composite Workflows

Pre-defined multi-step workflows coordinate multiple skills for complex operations:

### WF-01: Full Tenant Onboarding
**Trigger:** "Onboard [tenant] as enterprise tier in [region]"  
**Skills:** terraform-provisioning, kubernetes-cluster-manager, secrets-certificate-manager, multi-cloud-networking, database-operations, developer-self-service, observability-stack, policy-as-code, audit-siem, compliance-security-scanner, cost-optimisation, capacity-planning, gitops-workflow

### WF-02: P0/P1 Incident Response
**Trigger:** "Take over P0/P1 incident response"  
**Skills:** incident-triage-runbook, observability-stack, runbook-documentation-gen, stakeholder-comms-drafter, compliance-security-scanner, audit-siem, sla-monitoring-alerting, change-management, orchestrator

### WF-03: Weekly Compliance Scan
**Trigger:** Automatic (Monday 06:00 UTC)  
**Skills:** compliance-security-scanner, policy-as-code, audit-siem, runbook-documentation-gen, kpi-report-generator, stakeholder-comms-drafter

### WF-04: Monthly Executive Report
**Trigger:** Automatic (1st of month 07:00 UTC)  
**Skills:** kpi-report-generator, sla-monitoring-alerting, cost-optimisation, capacity-planning, compliance-security-scanner, runbook-documentation-gen, stakeholder-comms-drafter

### WF-05: Pre-Release Readiness Check
**Trigger:** "Is v[X] ready to release?"  
**Skills:** deployment-validation, cicd-pipeline-monitor, compliance-security-scanner, chaos-load-testing, observability-stack, container-registry, gitops-workflow

### WF-06: QBR Preparation
**Trigger:** "Prepare the Q[N] QBR deck"  
**Skills:** kpi-report-generator, cost-optimisation, capacity-planning, compliance-security-scanner, runbook-documentation-gen, stakeholder-comms-drafter, sla-monitoring-alerting, change-management

### WF-07: New Cluster Provisioning
**Trigger:** "Provision a new [env] cluster in [region]"  
**Skills:** terraform-provisioning, kubernetes-cluster-manager, secrets-certificate-manager, policy-as-code, observability-stack, gitops-workflow, service-mesh

### WF-08: Security Incident Response
**Trigger:** "Sentinel fired — investigate [alert]"  
**Skills:** audit-siem, incident-triage-runbook, compliance-security-scanner, stakeholder-comms-drafter

### WF-09: DR Drill Execution
**Trigger:** "Run the quarterly DR drill"  
**Skills:** disaster-recovery, database-operations, observability-stack, runbook-documentation-gen, stakeholder-comms-drafter

### WF-10: Platform Team Onboarding
**Trigger:** "Onboard the [team name] engineering team"  
**Skills:** developer-self-service, gitops-workflow, observability-stack, secrets-certificate-manager, policy-as-code, compliance-security-scanner, audit-siem, runbook-documentation-gen, kubernetes-cluster-manager, container-registry, cicd-pipeline-monitor, change-management, stakeholder-comms-drafter

## Automated Schedules

| Task | Schedule | Skill |
|------|----------|-------|
| Compliance scan | Monday 06:00 UTC | `compliance-security-scanner` |
| Certificate expiry check | Daily 09:00 UTC | `secrets-certificate-manager` |
| Capacity planning check | Monday 10:00 UTC | `capacity-planning` |
| Monthly executive report | 1st of month 07:00 UTC | `kpi-report-generator` |
| SLO error budget check | Every 30 minutes | `sla-monitoring-alerting` |
| DR drill | Quarterly (Jan/Apr/Jul/Oct 15th) | `disaster-recovery` |
| Chaos experiment (staging) | Wednesday 14:00 UTC | `chaos-load-testing` |
| Audit SIEM review | Monday 08:00 UTC | `audit-siem` |
| Change calendar preview | Friday 07:00 UTC | `change-management` |

## Escalation Procedures

When operations fail or encounter unexpected states:

1. **Stop the workflow** — Do not continue past the failed step
2. **Preserve all intermediate state** — Do not clean up resources
3. **Generate an incident summary** using `incident-triage-runbook` skill
4. **Page on-call** via PagerDuty webhook: `curl -X POST "$PD_WEBHOOK" -d '{"incident": "..."}'`
5. **Post to Slack**: `curl -X POST "$SLACK_WEBHOOK" -d '{"text": "..."}'`
6. **Output clear handoff note** for the human taking over

## Operational Constraints

### Security Constraints
- Never pipe credentials to shell history; use environment variables or Azure Key Vault references
- Never store secrets in Git, even in comments or example configuration
- Always use `--dry-run` or `plan` mode first for terraform and kubectl operations
- Always confirm `kubectl config current-context` before cluster operations
- Maximum 3 retries on any single command before escalating
- Timeout: fail any step that takes longer than 15 minutes

### Resource Management
- Monitor CPU and memory usage during operations
- Implement proper resource cleanup on failures
- Use batching for large-scale operations to avoid rate limits
- Implement caching for repeated operations where appropriate

## Error Handling Patterns

### Retry Logic
```javascript
async function executeSkillWithRetry(skillFunction, params, maxRetries = 3) {
  let attempt = 0;

  while (attempt < maxRetries) {
    try {
      const result = await skillFunction(params);

      if (result.status === "completed") {
        return result;
      } else if (result.status === "failed") {
        throw new Error(`Skill failed: ${result.errors.join(", ")}`);
      }

      // Handle running status
      await new Promise(resolve => setTimeout(resolve, 2000));

    } catch (error) {
      attempt++;

      if (attempt >= maxRetries) {
        // Escalate to human
        await request_human_review({
          workflowId: params.workflowId || "unknown",
          reviewType: "escalation",
          priority: "high",
          context: { error: error.message, attempts: attempt }
        });
        throw error;
      }

      // Wait before retry with exponential backoff
      const delay = Math.pow(2, attempt) * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

### Batch Operations
```javascript
const batchOperations = async (resources, skillFunction, batchSize = 10) => {
  const results = [];

  for (let i = 0; i < resources.length; i += batchSize) {
    const batch = resources.slice(i, i + batchSize);
    const batchPromises = batch.map(resource =>
      skillFunction({ targetResource: resource.id })
    );

    const batchResults = await Promise.allSettled(batchPromises);
    results.push(...batchResults);

    // Brief pause between batches to avoid rate limits
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  return results;
};
```

## Monitoring & Observability

### Execution Logging Standards
All skill executions generate comprehensive audit logs:

```json
{
  "execution_id": "uuid",
  "timestamp": "ISO8601",
  "duration_ms": 1500,
  "user_context": {
    "api_key_id": "key-hash",
    "user_id": "user-uuid",
    "session_id": "session-uuid"
  },
  "skill_details": {
    "name": "compliance-security-scanner",
    "version": "1.0.0",
    "parameters": { /* input parameters */ }
  },
  "execution_status": {
    "result": "success|failure|timeout",
    "exit_code": 0,
    "error_message": null
  },
  "performance_metrics": {
    "cpu_usage": 0.15,
    "memory_mb": 128,
    "network_calls": 3
  },
  "audit_trail": {
    "resources_accessed": ["vm-001", "storage-002"],
    "data_processed": "confidential",
    "compliance_frameworks": ["SOC2", "GDPR"]
  }
}
```

### Performance Monitoring
Track key metrics for all skill executions:

```javascript
const performanceMetrics = {
  // Latency metrics
  execution_time_p95: "2.5s",
  execution_time_p99: "5.2s",

  // Success rates
  overall_success_rate: 0.987,
  skill_specific_rates: {
    "compliance-security-scanner": 0.992,
    "terraform-provisioning": 0.978
  },

  // Resource utilization
  average_cpu_usage: 0.25,
  peak_memory_mb: 512,

  // Error patterns
  timeout_rate: 0.005,
  validation_error_rate: 0.008,
  infrastructure_error_rate: 0.003
};
```

## Compliance Reporting

Generate executive-ready compliance reports:

```javascript
const complianceReport = {
  executive_summary: {
    overall_posture_score: 94.2,
    critical_findings: 2,
    compliance_status: {
      "SOC2": "compliant",
      "ISO27001": "minor_deviation",
      "CIS_Azure": 89
    }
  },

  risk_assessment: {
    high_risk_areas: [
      "IAM privilege escalation",
      "Unencrypted storage volumes"
    ],
    risk_trend: "improving",
    remediation_progress: 0.78
  },

  detailed_findings: [
    {
      id: "FIND-0001",
      severity: "HIGH",
      framework: "SOC2-CC6.1",
      description: "MFA not enforced for privileged accounts",
      remediation: "Enable conditional access policies",
      eta: "2 weeks"
    }
  ],

  audit_trail_summary: {
    total_audits: 1247,
    compliance_rate: 0.943,
    last_audit: "2025-01-15T08:30:00Z"
  }
};
```

## Integration Guidelines

### Authentication & Authorization
```bash
# API Key Configuration
export AI_AGENTS_API_KEY="your-production-api-key"
export AI_AGENTS_API_URL="http://localhost:8081"

# MCP Server Configuration
export MCP_SERVER_URL="localhost:8082"
export MCP_TRANSPORT="websocket"  # stdio, websocket, http

# Required headers for all requests
curl -H "Authorization: Bearer $AI_AGENTS_API_KEY" \
     -H "Content-Type: application/json" \
     "$AI_AGENTS_API_URL/v1/skills/compliance-check"
```

### Best Practices for Skill Chaining
```javascript
async function executeSkillChain(skillSequence, context) {
  const results = [];

  for (const [index, skill] of skillSequence.entries()) {
    try {
      const result = await skill.function({
        ...skill.parameters,
        ...context,
        previous_results: results
      });

      results.push({ step: index, ...result });

      // Check for human gates
      if (result.requires_human_review) {
        const review = await request_human_review({
          workflowId: result.workflowId,
          reviewType: skill.reviewType || "approval",
          priority: skill.priority || "normal",
          context: { step: index, total_steps: skillSequence.length }
        });

        if (review.decision !== "approved") {
          throw new Error(`Skill chain stopped at step ${index}: ${review.comments}`);
        }
      }

    } catch (error) {
      console.error(`Step ${index} failed:`, error.message);

      if (skill.continue_on_error !== true) {
        throw error; // Stop the chain
      }

      results.push({
        step: index,
        status: "failed",
        error: error.message
      });
    }
  }

  return results;
}
```

## Quick Diagnostic Commands

```bash
# Check agent prerequisites
./bootstrap.sh

# Run all skill evaluations
python3 eval/run_evals.py

# Run evaluations for one skill
python3 eval/run_evals.py --skill gitops-workflow --verbose

# Validate a specific skill's structure
python3 eval/run_evals.py --skill incident-triage-runbook -v

# Count all skills
find .agents/skills -name "SKILL.md" | wc -l
```

This operational procedures guide ensures consistent, safe, and auditable execution of AI agent workflows while maintaining compliance with the Agent Skills specification.

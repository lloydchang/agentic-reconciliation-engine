---
name: orchestrator
description: >
  Top-level orchestrator for coordinating multi-skill workflows, human gates, and dispatcher automation.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Orchestrator — World-class Coordination Playbook

Acts as the conductor for composite workflows spanning provisioning, incidents, compliance, reports, and migrations; breaks requests into skill sequences, manages dependencies, tracks human gates, and reports unified status.

## When to invoke
- High-level multi-domain requests (tenant onboarding, P1 incident response, exec report, migration).
- Dispatcher events that require chaining skills with shared context (`incident-ready`, `policy-risk`, `capacity-alert`).
- Scheduled workflows (compliance scans, monthly reporting, DR drills) across several skills.

## Capabilities
- **Composite workflow orchestration** with dependency tracking, retries, and gating.
- **Human gate management** aggregating risk scores and delaying flows until approval.
- **State/telemetry export** with structured status, logs, and shared context for auditing.
- **Event emission** for downstream skills (`workflow-started`, `workflow-step-completed`, etc.).
- **AI dependency resolution** for ordering steps and spotting conflicts.

## Invocation patterns

```bash
/orchestrator run --workflow=tenant-onboarding --tenant=t-acme-prod
/orchestrator rerun --workflowId=WORKFLOW-01 --step=5
/orchestrator status --workflowId=WORKFLOW-02 --format=json
/orchestrator schedule --workflow=weekly-compliance --cron="0 6 * * 1"
/orchestrator orchestrate --type=incident-response --context=shared-context://memory-store/incident/INC-2026-041
```

## Output contract

```json
{
  "workflowId": "WORKFLOW-01",
  "status": "pending|running|completed|failed|blocked",
  "workflowType": "tenant-onboarding",
  "currentStep": 5,
  "stepsTotal": 12,
  "humanGate": {
    "required": true,
    "impact": "Production smoke test go/no-go",
    "reversible": "Yes"
  },
  "events": [
    { "name": "workflow-started", "timestamp": "2026-03-15T08:00:00Z" }
  ],
  "decisionContext": "redis://memory-store/orchestrator/WORKFLOW-01",
  "logs": "shared-context://memory-store/orchestrator/WORKFLOW-01"
}
```

## World-class workflow templates

### Tenant onboarding
1. Capacity planning → policy validation → Terraform provisioning → cluster hardening → observability.
2. Emit events per step, require human gates at capacity approval and smoke tests, and track timeline/status for stakeholders.

### Incident response (P1)
1. Run incident-triage → observability enrichment → deployment validation → stakeholder comms → postmortem.
2. Refresh context every 15 mins, escalate to comms/human gates when risk persists.

### Compliance/reporting workflows
1. Schedule compliance scans followed by KPI report generation and stakeholder briefings.
2. Emit `workflow-completed` with evidence for auditors.

### DR drill/migration orchestration
1. Sequence change control, DR, capacity, incident, and tenant operations with human gates at failover/failback points.
2. Capture RTO/RPO metrics, log references, and update relevant runbooks.

## AI intelligence highlights
- **AI dependency resolution** predicts skill ordering and resource conflicts.
- **Risk scoring** aggregates metrics across steps to decide gating needs.
- **Anomaly detection** surfaces stalls/retries and triggers alternate paths or escalations.

## Memory agent & dispatcher integration
- Store workflow metadata under `shared-context://memory-store/orchestrator/{workflowId}`.
- Emit events: `workflow-started`, `workflow-step-completed`, `workflow-failed`, `workflow-human-gate`.
- Respond to dispatcher triggers (incident, policy, capacity) to spawn workflows with shared context.
- Tag logs with `decisionId`, `workflowType`, `riskScore`.

## Observability & telemetry
- Metrics: workflows executed, success/failure rates, time per step, human gate frequency, aggregated riskScore.
- Logs: structured `log.event="workflow.status"` capturing `workflowId`, `step`, `decisionId`.
- Dashboards: integrate `/orchestrator metrics --format=prometheus` for SRE visibility.
- Alerts: workflow failures, stalled steps (>15 min), human gate response delays (>10 min).

## Failure handling & retries
- Retry failed steps up to 2× with exponential backoff before escalating.
- If human gate is denied, halt workflow and notify via Slack/PagerDuty.
- Preserve logs/context until downstream acknowledgment; do not auto-delete.

## Human gates
- Required when:
  1. Aggregated riskScore across steps ≥ 0.85.
  2. Change impacts production or >20 tenants.
  3. Dispatcher/human requests manual review.
- Use standard template capturing impact and reversibility.

## Testing & validation
- Dry-run: `/orchestrator run --workflow=tenant-onboarding --dry-run`.
- Unit tests: `backend/orchestrator/` validates dependency resolution and gate logic.
- Integration: `scripts/validate-orchestrator.sh` executes sample workflows end-to-end.
- Regression: nightly `scripts/nightly-orchestrator-smoke.sh` ensures scheduled workflows and metrics stay healthy.

## References
- Workflow definitions: `backend/workflows/`.
- Templates: `templates/workflow-*.yaml`.
- Scripts: `scripts/orchestrations/`.

## Related skills
- All other skills—this orchestrator invokes them per workflow templates.

---
name: orchestrator
description: >
  Top-level orchestrator for coordinating multi-skill workflows, human gates, and dispatcher-based automation.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Orchestrator — World-class Coordination Playbook

Acts as the master conductor for composite workflows spanning provisioning, incidents, compliance, reporting, and migrations. Decomposes high-level requests into skill sequences, manages dependencies, tracks human gates, and provides unified status/telemetry output.

## When to invoke
- Handling large, multi-domain requests (onboarding refresh, incident response, exec reports, migrations).
- Coordinating multi-step operations across skills (terraform → observability → SLA → comms).
- Responding to dispatcher events that require running multiple skills with shared context.
- Managing scheduled workflows (weekly scans, monthly reports, DR drills).

## Capabilities
- Defines composite workflows (e.g., tenant onboarding, incident response, compliance scan, monthly report).
- Orchestrates skill execution sequences with dependency, retry, and human gate handling.
- Tracks workflow state, exports structured status, logs, and telemetry.
- Shared context `/shared-context://memory-store/orchestrator/<workflowId>`.
- Emits events for downstream skills to act upon (`workflow-started`, `workflow-completed`, etc.).

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

### Tenant onboarding (full stack workflow)
1. Capacity planning → policy validation → terraform provisioning → cluster hardening etc. Emit events per step with gating (human gates at capacity, smoke test).
2. Provide combined report of status and timeline for stakeholders.

### Incident response (P1)
1. Run incident-triage → observability → deployments → stakeholder updates → post-mortem generation.
2. Loop updates every 15 minutes; escalate to comms/human gates as needed.

### Compliance/exec reporting & scans
1. Schedule compliance scan workflow (SIEM, compliance, rotation, KPI).
2. Build monthly exec report, send to leadership, log outcomes.

### DR drill / migration orchestration
1. Sequence change control, DR, capacity, incident, and tenant operations with human gates at failover/failback points.
2. Capture RTO/RPO metrics and update runbooks.

## AI intelligence highlights
- **AI Dependency Resolution**: predicts skill ordering and resource conflicts.
- **Risk scoring**: tracks aggregated riskScore across skills to determine gating needs.
- **Anomaly detection**: detects stalls or repeated failures to trigger alternate flows or escalate.

## Memory agent & dispatcher integration
- Store workflow metadata under `shared-context://memory-store/orchestrator/<workflowId>`.
- Emit events: `workflow-started`, `workflow-step-completed`, `workflow-failed`, `workflow-human-gate`.
- Respond to dispatcher triggers (incident, policy, capacity) to spawn appropriate workflows.
- Tag logs with `decisionId`, `workflowType`, `riskScore`.

## Communication protocols
- Primary: sequential skill invocation using CLI or API calls per template.
- Secondary: Event bus for `workflow-*` notifications eaten by monitoring/other skills.
- Fallback: JSON artifacts in `artifact-store://orchestrator/<workflowId>.json`.

## Observability & telemetry
- Metrics: workflows executed, success/failure rates, time per step, human gate frequency, aggregated riskScore.
- Logs: structured `log.event="workflow.status"` capturing `workflowId`, `step`, `decisionId`.
- Dashboards: integrate `/orchestrator metrics --format=prometheus`.
- Alerts: repeated workflow failures, stalled steps (>15 min), human gate response delay (>10 min).

## Failure handling & retries
- Retry failed steps up to 2× with exponential backoff before escalating.
- If human gate not approved, halt workflow and notify via Slack/PagerDuty.
- Preserve shared-context logs until downstream ack; do not delete automatically.

## Human gates
- Required when:
 1. RiskScore aggregated across steps ≥ 0.85.
 2. Change impacts prod or >20 tenants.
 3. Dispatcher or human explicitly requests manual review.
- Use standard human gate template capturing impact/reversibility.

## Testing & validation
- Dry-run: `/orchestrator run --workflow=tenant-onboarding --dry-run`.
- Unit tests: `backend/orchestrator/` ensures dependency handling, gating.
- Integration: `scripts/validate-orchestrator.sh` executes sample workflows end-to-end.
- Regression: nightly `scripts/nightly-orchestrator-smoke.sh` ensures scheduled workflows fire and metrics stay stable.

## References
- Workflow definitions: `backend/workflows/`.
- Templates: `templates/workflow-*.yaml`.
- Scripts: `scripts/orchestrations/`.

## Related skills
- All other skills—this orchestrator calls them in various sequences per workflow templates.

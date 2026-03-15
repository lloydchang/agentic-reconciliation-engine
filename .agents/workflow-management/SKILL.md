---
name: workflow-management
description: >
  Orchestrate, monitor, and control Temporal AI Agent workflows across compliance, security, cost, and infrastructure workstreams with AI risk scoring and dispatcher integration.
argument-hint: "[action] [workflowId] [parameters]"
disable-model-invocation: false
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
---

# Workflow Management — World-class Temporal Operations Playbook

Centralizes listing, monitoring, controlling, and orchestrating Temporal AI Agent workflows with AI intelligence, dependency awareness, and dispatcher-ready outputs.

## When to invoke
- Query active workflows, status, logs, or telemetry in real time.
- Cancel/pause/resume/restart Temporal executions for cost, compliance, or reliability reasons.
- Orchestrate complex sequences (security audits, compliance sweeps, deployments) with dependency-aware execution.
- Respond to dispatcher events (`AI anomaly`, `policy-risk`, `capacity-alert`) by rerouting workflow paths or escalating to humans.

## Capabilities
- **Workflow discovery** with filters by type, status, priority, or run-time metrics.
- **Control operations** (cancel, pause, resume, restart, reprioritize) with riskScore gating.
- **AI orchestration** for sequential/parallel/conditional workflows with dependency resolution and resource-aware scheduling.
- **Telemetry capture** (execution time, resource consumption, failure patterns) and anomaly alerts.
- **Shared-context propagation** at `shared-context://memory-store/workflow/{workflowId}` for downstream skills.

## Invocation patterns

```bash
/workflow-management list active --priority=high --format=json
/workflow-management status wf-12345 --verbose --metrics
/workflow-management cancel wf-12345 "cost spike" --reason=manual
/workflow-management orchestrate security-audit production --parallel=3 --dependencies=wf-001,wf-002
/workflow-management monitor wf-12345 --live
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `workflowId` | Temporal workflow identifier. | `wf-12345` |
| `status` | Workflow state filter (`pending|running|completed|failed`). | `running` |
| `priority` | Execution priority (`low|normal|high|critical`). | `critical` |
| `format` | Output format (`json|table|csv`). | `json` |
| `metrics` | Include telemetry metrics. | `true` |
| `dependencies` | Dependency list for orchestration. | `wf-001,wf-002` |

## Output contract

```json
{
  "workflowId": "wf-12345",
  "type": "compliance",
  "status": "running",
  "priority": "high",
  "progress": 72,
  "startedAt": "2026-03-15T08:00:00Z",
  "estimatedCompletion": "2026-03-15T08:45:00Z",
  "resourceUsage": { "cpu": 45, "memory": 2.1, "networkBytes": 150000 },
  "aiInsights": { "riskScore": 0.32, "bottlenecks": ["call-compliance-check"], "anomaly": false },
  "events": [ { "name": "workflowStarted", "timestamp": "2026-03-15T08:00:00Z" } ],
  "decisionContext": "redis://memory-store/workflow/wf-12345",
  "logs": "shared-context://memory-store/workflow/wf-12345"
}
```

## World-class workflow templates

### AI-guided orchestration
1. Accept workflow definitions (`sequential`, `parallel`, `conditional`) with dependencies and priorities.
2. Score risk (resource contention, change impact, tenant exposure) and allocate execution nodes dynamically.
3. Execute workflows respecting dependencies, emit `workflow-started/completed` events, and monitor telemetry.
4. Command stub: `/workflow-management orchestrate security-audit production --parallel=3 --dependencies=wf-001,wf-002`.

### Resource-aware scheduling
1. Evaluate resource availability (`cpu`, `memory`, queue depth) across Temporal workers.
2. Schedule high-priority workflows first and throttle lower-priority ones during contention.
3. Emit `workflow-throttled` events with reasoning for upstream skills.
4. Command stub: `/workflow-management list active --priority=high --format=json`.

### Failure handling & recovery
1. Detect failures/deadlocks through event hooks or anomaly detection.
2. Retry with exponential backoff (<3 attempts) before escalating.
3. Trigger human gates when repeated failures or high-risk workflows stall.
4. Command stub: `/workflow-management monitor wf-12345 --live`.

## AI intelligence highlights
- **AI risk scoring** predics workflow robustness based on type, resource needs, and past outcomes.
- **Intelligent ordering** ranks workflows by priority, dependency criticality, and resource efficiency.
- **Anomaly detection** flags telemetry deviations (latency spikes, error rates) for human review.

## Memory agent & dispatcher integration
- Store workflow metadata under `shared-context://memory-store/workflow/{workflowId}`.
- Emit/subscribe to events: `workflow-started`, `workflow-step-completed`, `workflow-failed`, `workflow-alert`.
- Coordinate with dispatchers (`incident-ready`, `cost-anomaly`, `policy-risk`) to reroute or escalate workflows.
- Tag telemetry with `decisionId`, `orchestrationId`, `workflowType`, `riskScore`.

## Observability & telemetry
- Metrics: workflow counts (running/completed/failed), durations, failure patterns, resource usage.
- Logs: structured `log.event="workflow.status"` with `workflowId`, `tenant`, `decisionId`.
- Dashboards: integrate `/workflow-management metrics --format=prometheus` into orchestration views.
- Alerts: riskScore > 0.85, stale workflows > 30 minutes, deadlocks detected.

## Failure handling & retries
- Retry control operations (resume/pause) up to 2× on transient errors with exponential backoff.
- On repeated workflow failures escalate to `incident-triage-runbook` and flag human gate.
- Preserve logs/artifacts for audit; avoid deleting `shared-context` entries until downstream acknowledgement.

## Human gates
- Required when:
  1. RiskScore ≥ 0.85 or critical workflows touch prod resources.
  2. Workflow failure triggers high-impact rollback or policy enforcement.
  3. Dispatcher requests manual intervention after repeated retries.
- Use the standard human gate template capturing impact and reversibility.

## Testing & validation
- Dry-run: `/workflow-management orchestrate security-audit production --dry-run`.
- Unit tests: `backend/workflow` ensures dependency logic and failure modes.
- Integration: `scripts/validate-workflow-management.sh` simulates workflows, retries, and event emissions.
- Regression: nightly `scripts/nightly-workflow-smoke.sh` monitors metrics and ensures anomaly alerts fire.

## References
- Workflow templates: `backend/workflow/templates/`.
- Scripts: `scripts/orchestration/`.
- Monitoring dashboards: `monitoring/grafana/workflow`.

## Related skills
- `/ai-agent-orchestration`: coordinates complex multi-skill workflows.
- `/deployment-validation`: uses workflow orchestration for gating deployments.
- `/incident-triage-runbook`: invoked on workflow failures or escalations.

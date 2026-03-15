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

Centralizes listing, monitoring, control, and orchestration for Temporal AI Agent workflows. Use this skill when you need to manage multiple workflows, investigate errors, coordinate multi-step operations, or trigger AI-guided responses to dispatcher events.

## When to invoke
- Query active workflows, status, or logs in real time.
- Cancel/pause/resume/restart workflows for cost, compliance, or reliability reasons.
- Orchestrate complex sequences (security audits, compliance checks, deployments) with dependency-aware execution.
- React to dispatcher triggers (AI anomaly, policy risk, capacity alerts) by rerouting workflow paths or escalating to human review.

## Capabilities
- List workflows by type/status/priority with filtering and formats (table/JSON).
- Monitor workflow execution history, dependencies, metrics, and live updates.
- Control operations: cancel, pause, resume, restart, change priority.
- AI orchestration patterns: sequential/parallel/conditional pipelines with scheduling, dependency resolution, and resource-aware allocation.
- Telemetry capture (execution time, resource usage, failure patterns) and alert emission for anomalous workflows.
- Shared context integration `shared-context://memory-store/workflow/<workflowId>` for other skills.

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
| `status` | Workflow state filter (pending|running|completed|failed). | `running` |
| `priority` | Execution priority (low|normal|high|critical). | `critical` |
| `format` | Output format (json|table|csv). | `json` |
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
  "resourceUsage": {
    "cpu": 45,
    "memory": 2.1,
    "networkBytes": 150000
  },
  "aiInsights": {
    "riskScore": 0.32,
    "bottlenecks": ["call-compliance-check"],
    "anomaly": false
  },
  "events": [
    { "name": "workflowStarted", "timestamp": "2026-03-15T08:00:00Z" }
  ],
  "decisionContext": "redis://memory-store/workflow/wf-12345",
  "logs": "shared-context://memory-store/workflow/wf-12345"
}
```

## World-class workflow templates

### AI-guided orchestration
1. Accept workflow definitions (`sequential`, `parallel`, `conditional`) with dependencies and priorities.
2. Score risk (resource contention, change size, tenant impact) and allocate execution nodes dynamically.
3. Execute workflows respecting dependencies, emit events (`workflowStarted`, `workflowCompleted`), and monitor telemetry.

### Resource-aware scheduling
1. Evaluate resource availability (`cpu`, `memory`, `queue depth`).
2. Schedule workflows with highest priority/resourcing needs first.
3. Inject delay/backoff when resources overloaded; emit `workflow-throttled`.

### Failure handling & recovery
1. Detect failures or deadlocks via event hooks.
2. Retry with exponential backoff (<3 attempts) before escalating.
3. Trigger human gate when repeated failures or high-risk workflows stall.

## AI intelligence highlights
- **AI Risk Scoring**: predictions based on workflow type, resource requirements, change window, and past success/failure history.
- **Intelligent Ordering**: sorts workflows by priority, dependency criticality, and resource efficiency.
- **Anomaly Detection**: flags workflows exhibiting unusual latency, error rates, or telemetry deviations.

## Memory agent & dispatcher integration
- Store workflow metadata under `shared-context://memory-store/workflow/<workflowId>`.
- Emit/subscribe to events: `workflow-started`, `workflow-completed`, `workflow-failed`, `workflow-alert`.
- Link with dispatchers to reroute workflows when `incident-ready`, `cost-anomaly`, or `policy-risk` events occur.
- Tag telemetry with `decisionId`, `orchestrationId`, `tenant`, `riskScore`.

## Communication protocols
- Primary: Temporal API commands executed via CLI wrappers (list/status/control/orchestrate).
- Secondary: Event bus (NATS/Kafka) for `workflow-*` events consumed by downstream skills.
- Fallback: JSON artifacts in `artifact-store://workflow/<workflowId>.json`.

## Observability & telemetry
- Metrics: workflow counts (running/completed/failed), durations, failure patterns, resource usage, queue depth.
- Logs: structured `log.event="workflow.status"` with `workflowId`, `tenant`, `decisionId`.
- Dashboards: integrate `/workflow-management metrics --format=prometheus` for orchestration health.
- Alerts: riskScore > 0.85, stale workflows > 30 min, deadlocks detected.

## Failure handling & retries
- Retry control operations (resume/pause) up to 2× on transient errors with exponential backoff.
- On repeated failures (>=2 retries) for a workflow, trigger `incident-triage-runbook` and flag human gate.
- Preserve logs/artifacts for audit; avoid deleting `shared-context` entries until downstream ack.

## Human gates
- Required when:
 1. RiskScore ≥ 0.85 or critical workflow touches production resources.
 2. Workflow failure triggers high-impact rollback or policy enforcement.
 3. Dispatcher requests manual intervention after repeated retries.
- Use the standard human gate template for confirmation.

## Testing & validation
- Dry-run: `/workflow-management orchestrate security-audit production --dry-run`.
- Unit tests: `backend/workflow` ensuring orchestration logic handles dependency graphs and failure modes.
- Integration: `scripts/validate-workflow-management.sh` simulates workflows, failures, retries, and event emissions.
- Regression: nightly `scripts/nightly-workflow-smoke.sh` monitors metrics and ensures alerts fire when anomalies happen.

## References
- Workflow templates: `backend/workflow/templates/`.
- Scripts: `scripts/orchestration/`.
- Monitoring dashboards: `monitoring/grafana/workflow`.

## Related skills
- `/ai-agent-orchestration`: coordinates complex multi-skill workflows.
- `/deployment-validation`: depends on workflow orchestration for gating.
- `/incident-triage-runbook`: invoked on workflow failures or escalations.

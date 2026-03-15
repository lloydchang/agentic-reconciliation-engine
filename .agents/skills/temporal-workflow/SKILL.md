---
name: temporal-workflow
description: >
  Create, manage, and monitor Temporal workflows with AI orchestration, observability, and shared context.
argument-hint: "[action] [workflowName] [parameters]"
disable-model-invocation: false
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
---

# Temporal Workflow — World-class Orchestration Playbook

Provides end-to-end Temporal workflow lifecycle management: creation, scaffolding, monitoring, debugging, and reporting. Integrates AI risk/resilience insight, structured outputs, and dispatcher hooks.

## When to invoke
- Create or scaffold new workflows or activities.
- Monitor workflow status, metrics, or run history.
- Debug failures or replay executions.
- Validate workflows via testing or analyze performance.
- React to dispatcher events (incident-alerts, compliance) needing workflow actions.

## Capabilities
- Workflow creation, scaffolding, monitoring, debugging, and testing.
- AI risk scoring for workflow changes and retries.
- Observability integration with metrics and dashboards.
- Shared context `shared-context://memory-store/temporal/<operationId>`.

## Invocation patterns

```bash
/temporal-workflow create order-processing "Handles orders"
/temporal-workflow status order-processing
/temporal-workflow monitor order-processing --live
/temporal-workflow debug order-processing --history=50
/temporal-workflow test order-processing --integration
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `workflowName` | Workflow identifier. | `order-processing` |
| `action` | Operation (create/status/monitor/debug/test). | `create` |
| `parameters` | Payload guiding creation or monitoring. | `{"task":"payment"}` |
| `history` | Run history depth. | `50` |
| `format` | Output (json/table). | `json` |

## Output contract

```json
{
  "operationId": "TEMPORAL-2026-0315-01",
  "status": "success|failure",
  "action": "create|monitor|debug|test",
  "workflow": "order-processing",
  "runsMonitored": 12,
  "aiInsights": {
    "riskScore": 0.33,
    "anomalies": []
  },
  "metrics": {
    "successRate": 0.96,
    "avgExecutionTimeMs": 1234
  },
  "decisionContext": "redis://memory-store/temporal/TEMPORAL-2026-0315-01",
  "logs": "shared-context://memory-store/temporal/TEMPORAL-2026-0315-01"
}
```

## World-class workflow templates

### Workflow creation & scaffolding
1. Generate workflow skeleton and register activities (Go/Java/Python).
2. Provide compensation and retry templates.
3. Emit `workflow-created` event with registration metadata.

### Monitoring & debug
1. Provide real-time status, history, and dependency graphs.
2. Replay failed runs or query states.
3. Emit `workflow-monitored` and `workflow-debugged` events.

### Testing & validation
1. Run unit (`go test`) and integration tests.
2. Validate with Temporal emulator/local runner.
3. Emit `workflow-tested`.

## AI intelligence highlights
- **AI Risk Scoring**: flags workflows with high change risk or slowdowns.
- **Intelligent Retry Strategies**: suggests optimal retry/backoff settings per failure patterns.
- **Predictive Anomalies**: detects runs drifting from baseline performance.

## Memory agent & dispatcher integration
- Store workflow metadata at `shared-context://memory-store/temporal/<operationId>`.
- Emit events: `workflow-started`, `workflow-completed`, `workflow-failed`, `workflow-anomaly`.
- Dispatcher can trigger workflow operations or escalate incidents.
- Tag with `decisionId`, `workflow`, `riskScore`.

## Communication protocols
- Primary: Temporal CLI/API (start workflow, query, request tasks).
- Secondary: Event bus for `temporal-*` events.
- Fallback: JSON artifacts `artifact-store://temporal/<operationId>.json`.

## Observability & telemetry
- Metrics: workflow run counts, success/failure rates, latency distributions.
- Logs: structured `log.event="temporal.operation"` with `operationId`.
- Dashboards: integrate `/temporal-workflow metrics --format=prometheus`.
- Alerts: failure rate > threshold, long-running runs, anomalies detected.

## Failure handling & retries
- Retry API commands up to 2× for transient errors; escalate after 3.
- On repeated failures, route to `incident-triage-runbook`.
- Keep state and artifacts until downstream ack.

## Human gates
- Required when:
 1. Workflow changes could impact production or sensitive data.
 2. Dispatcher requests manual review after repeated retries/failures.
 3. RiskScore ≥ 0.85.
- Use standard human gate template.

## Testing & validation
- Dry-run: `/temporal-workflow test order-processing --dry-run`.
- Unit tests: `backend/workflows/*_test.go`.
- Integration: `scripts/validate-temporal-workflows.sh`.
- Regression: nightly `scripts/nightly-temporal-smoke.sh`.

## References
- Workflows: `backend/workflows/`.
- Activities: `backend/activities/`.
- Scripts: `scripts/workflows/`.

## Related skills
- `/workflow-management`: orchestrates multiple Temporal workflows.
- `/ai-agent-orchestration`: coordinates Temporal operations within larger processes.

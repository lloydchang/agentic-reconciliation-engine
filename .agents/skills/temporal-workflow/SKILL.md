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

Provides end-to-end Temporal workflow lifecycle management: creation, scaffolding, monitoring, debugging, and reporting with dispatcher-grade context.

## When to invoke
- Scaffold or update Temporal workflows and activities across services.
- Monitor workflow status, success/failure rates, or tracing data.
- Debug failures, replay executions, or analyze histograms.
- Validate workflows (unit/integration) or inspect SLA-aligned metrics.
- Respond to dispatcher events (`incident-ready`, `policy-risk`, `capacity-alert`) needing workflow interventions.

## Capabilities
- **Workflow lifecycle management** (create, monitor, debug, test, replay).
- **AI risk scoring** for workflow changes, retries, and latency anomalies.
- **Predictive diagnostics** with root-cause guidance and retry/backoff tuning.
- **Shared-context propagation** at `shared-context://memory-store/temporal/{operationId}` for downstream skills.
- **Human-aware gating** before production-impacting deployments or retries.

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
| `action` | Operation (`create|status|monitor|debug|test`). | `monitor` |
| `parameters` | Payload guiding creation or queries. | `{"task":"payment"}` |
| `history` | Run history depth for debug. | `50` |
| `format` | Output (`json|table`). | `json` |

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
1. Generate workflow skeleton with activities and context propagation code.
2. Define compensation, retry, and timeout policies; register workflow with Temporal service.
3. Emit `workflow-created` events with registration metadata for orchestrators.

### Monitoring, debugging, & replay
1. Stream live status, histograms, and dependency maps into dashboards.
2. Replay failed runs, inspect stack traces, and surface anomalies with explainable AI.
3. Emit `workflow-monitored`, `workflow-debugged`, and `workflow-replayed` events.

### Testing & validation
1. Run unit tests (`go test`, `ts-node`, etc.) and integration suites against Temporal emulator.
2. Validate scheduling, retries, and SLA align with service objectives.
3. Emit `workflow-tested` metadata for compliance and release notes.

## AI intelligence highlights
- **AI risk scoring** spots workflows with high change risk, slowdowns, or repeated retries.
- **Intelligent retry strategy** recommends backoff windows, heartbeat, and timeout adjustments per failure patterns.
- **Predictive anomaly detection** flags drifts from baseline metrics (latency, success rate, queue depth).

## Memory agent & dispatcher integration
- Persist workflow metadata under `shared-context://memory-store/temporal/{operationId}` tagged with `decisionId`, `workflow`, `riskScore`.
- Emit events: `workflow-started`, `workflow-completed`, `workflow-failed`, `workflow-anomaly`, `workflow-gated`.
- Dispatcher triggers (`incident-ready`, `policy-risk`, `capacity-alert`) invoke skill operations or escalate to other skills.
- Provide fallback artifacts via `artifact-store://temporal/{operationId}.json` if messaging is unavailable.

## Observability & telemetry
- Metrics: run counts, success/failure rates, latency distributions, anomaly counts.
- Logs: structured `log.event="temporal.operation"` capturing `operation`, `workflow`, `decisionId`.
- Dashboards: integrate `/temporal-workflow metrics --format=prometheus` for SRE teams.
- Alerts: failure rate spikes, long-running runs, unreconciled retries, AI anomalies.

## Failure handling & retries
- Retry Temporal CLI/API commands up to 2× for transient errors; escalate to `incident-triage-runbook` after repeated fails.
- Preserve history, artifacts, and replay logs until downstream acknowledgments exist.
- Document gating decisions and risk adjustments for compliance.

## Human gates
- Required when:
  1. Workflow changes touch production or sensitive data paths.
  2. Dispatcher/human requests manual review after repeated retries/failures.
  3. AI riskScore ≥ 0.85.
- Confirmation template follows the orchestrator standard:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/temporal-workflow test order-processing --dry-run`.
- Unit tests: `backend/workflows/*_test.go` or equivalent language suites.
- Integration: `scripts/validate-temporal-workflows.sh` exercises workflows against emulator/test clusters.
- Regression: nightly `scripts/nightly-temporal-smoke.sh` verifies scheduling, retries, and metrics pipelines.

## References
- Workflows: `backend/workflows/`.
- Activities: `backend/activities/`.
- Scripts: `scripts/workflows/`.

## Related skills
- `/workflow-management`: orchestrates fleet-wide Temporal workflows.
- `/ai-agent-orchestration`: coordinates Temporal ops within broader multi-skill flows.
- `/incident-triage-runbook`: reacts to workflow-induced failures.

---
name: chaos-load-testing
description: >
  Run chaos experiments and load tests with AI safety guardrails, telemetry, and dispatcher-ready outputs.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Chaos & Load Testing — World-class Resilience Playbook

Validates platform resilience with chaos (Chaos Mesh, LitmusChaos, Azure Chaos) and load tests (k6, Locust), providing structured outputs, AI scoring, and safety rails. Trigger for experiments, load tests, autoscaler validation, or resilience reports.

## When to invoke
- Execute chaos experiments (pod kill, network latency, zone failure) or load tests (HTTP stress, spike).
- Test autoscaler response and circuit breakers.
- Diagnose resilience metrics or produce quarterly reports.
- Respond to dispatcher alerts (`incident-ready`, `capacity-alert`) by replaying relevant chaos scenarios.

## Capabilities
- Chaos Mesh/LitmusChaos experiments, Azure Chaos failovers, and k6/Locust load tests.
- AI guardrails assessing riskScore, SLO impact, and blast radius before autorun.
- Autoscaler validation and predictive resilience insights.
- Shared context `shared-context://memory-store/chaos/<experimentId>`.
- Human gates for production experiments or high-risk tests.

## Invocation patterns

```bash
/chaos-load-testing run --experiment=pod-kill --target=payments-api --duration=10m
/chaos-load-testing load --script=k6/stress.js --env=tenant-42 --duration=30m
/chaos-load-testing diagnostics --auto --retry=2 --threshold=0.1
/chaos-load-testing report --type=quarterly --format=markdown
/chaos-load-testing autoscaler --cluster=aks-tenant-42 --validate=true
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `experiment` | Chaos experiment type. | `network-latency` |
| `target` | Service/namespace to affect. | `payments-api` |
| `duration` | Experiment duration (s/m). | `10m` |
| `script` | k6 or Locust script path. | `k6/load-test.js` |
| `env` | Target environment/tenant. | `tenant-42` |
| `threshold` | SLO threshold for autoscale. | `0.1` |

## Output contract

```json
{
  "experimentId": "CHAOS-2026-0315-01",
  "type": "pod-kill|network-latency|zone-failure|load-test",
  "status": "passed|failed|aborted",
  "target": "payments-api",
  "riskScore": 0.38,
  "sloBreached": false,
  "metrics": {
    "errorRatePct": 0.4,
    "p99LatencyMs": 847,
    "recoveryTimeSeconds": 60
  },
  "abortReason": null,
  "events": [
    { "name": "plot-kill-aborted", "timestamp": "2026-03-15T08:12:00Z" }
  ],
  "logs": "shared-context://memory-store/chaos/CHAOS-2026-0315-01",
  "decisionContext": "redis://memory-store/chaos/CHAOS-2026-0315-01"
}
```

## World-class workflow templates

### Chaos experiment lifecycle
1. Define steady-state metrics (error rate, latency, autoscaler status).
2. Evaluate AI riskScore and human gate before running.
3. Launch experiment (Chaos Mesh/LitmusChaos/Azure Chaos) with guard loop aborting on SLO breach.
4. Emit `chaos-experiment` events and log metrics in shared context.

### Load testing
1. Execute k6/Locust scripts with staged traffic and thresholds.
2. Monitor error rates/latency; automatically abort if thresholds exceed (p99, error rate > threshold).
3. Emit `load-test` event with metrics and recommended actions.

### Autoscaler validation
1. Simulate load or drop to test autoscaler scaling decisions.
2. Verify response time, queue depth, and event log.
3. Emit `autoscaler-validated` event with findings.

## AI intelligence highlights
- **AI Risk Scoring**: combines target criticality, environment, SLOs, and history to determine safe experiments.
- **Predictive Alerts**: warns when load or chaos might breach thresholds before execution.
- **Intelligent Remediation**: suggests next steps (scale nodes, restart, rollback) when tests fail/breach.

## Memory agent & dispatcher integration
- Store experiment metadata at `shared-context://memory-store/chaos/<experimentId>`.
- Emit events: `chaos-start`, `chaos-aborted`, `load-test-complete`, `autoscaler-issue`.
- Respond to dispatcher alerts (incident-ready, capacity-alert) by auto-triggering pre-defined experiments or remediation actions.
- Tag records with `decisionId`, `tenant`, `riskScore`.

## Communication protocols
- Primary: CLI commands for Chaos Mesh, LitmusChaos, Azure Chaos, k6, Locust.
- Secondary: Event bus for `chaos-*` signals consumed by orchestrators and incident skills.
- Fallback: JSON artifacts stored at `artifact-store://chaos/<experimentId>.json`.

## Observability & telemetry
- Metrics: experiments run, passes/failures, SLO breach counts, autoscaler reactions.
- Logs: structured `log.event="chaos.operation"` with `experiment`, `decisionId`.
- Dashboards: integrate `/chaos-load-testing metrics --format=prometheus`.
- Alerts: aborts due to SLO breach > threshold, autoscaler not reacting, repeated experiment failures.

## Failure handling & retries
- Retry experiments up to 2× on transient infra errors; abort automatically when SLO breach threshold hit.
- On failure, emit `chaos-operation-failed` and escalate to `incident-triage-runbook`.
- Preserve experiment artifacts/logs until downstream ack.

## Human gates
- Required when:
 1. Experiments affect production or >20 tenants.
 2. RiskScore ≥ 0.7 or SLO thresholds threatened.
 3. Dispatcher requests manual review after retries.
- Use standard human gate template documenting impact and reversibility.

## Testing & validation
- Dry-run: `/chaos-load-testing run --experiment=pod-kill --dry-run`.
- Unit tests: `backend/chaos/` ensures guard logic and risk scoring behave correctly.
- Integration: `scripts/validate-chaos-load.sh` runs experiments in emulator and checks guard responses.
- Regression: nightly `scripts/nightly-chaos-smoke.sh` ensures automation, metrics, and alerts are stable.

## References
- Scripts: `scripts/chaos/`.
- Templates: `templates/chaos-experiment.yaml`.
- Reports: `monitoring/reports/chaos`.

## Related skills
- `/incident-triage-runbook`: triggered when chaos exposes incidents.
- `/capacity-planning`: tests autoscaler capacity headroom.
- `/ai-agent-orchestration`: combines chaos/load tests into larger workflows.

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

Validates platform resilience with chaos experiments (Chaos Mesh, LitmusChaos, Azure Chaos) and load tests (k6, Locust), coupled with AI scoring and dispatcher telemetry.

## When to invoke
- Execute chaos experiments (pod kill, network latency, zone failure) or load tests (HTTP spikes, stress scenarios).
- Test autoscaler/circuit breaker responses or resilience under degraded infrastructure.
- Diagnose resilience metrics, produce quarterly reports, or respond to dispatcher alerts (`incident-ready`, `capacity-alert`).

## Capabilities
- **Chaos experimentation** across Chaos Mesh, LitmusChaos, or Azure Chaos with guardrails.
- **Load testing** (k6/Locust) with stage-based traffic and auto-abort thresholds.
- **AI risk scoring** balancing blast radius, SLOs, and tenant impact before execution.
- **Autoscaler validation** (scale up/down toggles) and predictive resilience insights.
- **Shared-context propagation** at `shared-context://memory-store/chaos/{experimentId}` for downstream skills.
- **Human gating** for production-impacting or high-risk scenarios.

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
| `target` | Service/namespace targeted. | `payments-api` |
| `duration` | Operation duration (s/m). | `10m` |
| `script` | k6/Locust script path. | `k6/load-test.js` |
| `env` | Tenant/environment scope. | `tenant-42` |
| `threshold` | SLO threshold for guardrails. | `0.1` |

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
  "events": [ { "name": "chaos-started", "timestamp": "2026-03-15T08:12:00Z" } ],
  "logs": "shared-context://memory-store/chaos/CHAOS-2026-0315-01",
  "decisionContext": "redis://memory-store/chaos/CHAOS-2026-0315-01"
}
```

## World-class workflow templates

### Chaos experiment lifecycle
1. Define steady-state metrics (error rate, latency, autoscaler status).
2. Evaluate AI riskScore, human gate, and guard thresholds before execution.
3. Run experiment (Chaos Mesh/Litmus/Azure Chaos) with automatic abort on SLO breach.
4. Emit `chaos-experiment`, store metrics, and provide remediation guidance.

### Load testing & autoscaler validation
1. Stage traffic via k6/Locust; monitor error/latency thresholds.
2. Abort when guardrails trigger, log metrics, and produce `load-test` events.
3. For autoscaler validation simulate load shifts, monitor scaling events, and emit `autoscaler-validated`.

### Diagnostics & reporting
1. Run diagnostics (auto or manual) with retry/backoff parameters.
2. Collect metrics, chart anomalies, and export resilience reports.
3. Emit `resilience-report` events for leadership/compliance review.

## AI intelligence highlights
- **AI risk scoring** combines target criticality, environment, and SLOs to gate experiments.
- **Predictive alerts** warn when planned tests risk breaching thresholds before starting.
- **Intelligent remediation** recommends actions (scale nodes, rollback, throttle) when breaches occur.

## Memory agent & dispatcher integration
- Store experiment metadata under `shared-context://memory-store/chaos/{experimentId}` with tags (`decisionId`, `tenant`, `riskScore`).
- Emit events: `chaos-start`, `chaos-aborted`, `load-test-complete`, `autoscaler-issue`, `resilience-report`.
- Subscribe to dispatcher alerts to auto-trigger tailored experiments or remediate impacted services.
- Provide fallback artifacts via `artifact-store://chaos/{experimentId}.json` when event bus offline.

## Observability & telemetry
- Metrics: experiments run, pass/fail counts, SLO breaches, autoscaler responses.
- Logs: structured `log.event="chaos.operation"` with `experiment`, `decisionId`, `status`.
- Dashboards: integrate `/chaos-load-testing metrics --format=prometheus` for resilience views.
- Alerts: experiment aborts > threshold, autoscaler not reacting, repeated failure loops.

## Failure handling & retries
- Retry experiments 2× on transient infra/API failures; auto-abort when SLO thresholds break.
- On failure emit `chaos-operation-failed`, escalate to `incident-triage-runbook`, and keep artifacts.
- Do not delete experiments or metrics until downstream acknowledgments exist.

## Human gates
- Required when:
  1. Experiments affect production or >20 tenants.
  2. RiskScore ≥ 0.7 or SLO thresholds are threatened.
  3. Dispatcher requests manual review after retries/failures.
- Confirmation template follows orchestrator standards (impact, reversibility).

## Testing & validation
- Dry-run: `/chaos-load-testing run --experiment=pod-kill --dry-run`.
- Unit tests: `backend/chaos/` ensures guard logic and risk scoring behave correctly.
- Integration: `scripts/validate-chaos-load.sh` runs experiments/emulators verifying guard responses.
- Regression: nightly `scripts/nightly-chaos-smoke.sh` keeps automation, metrics, and alerts stable.

## References
- Scripts: `scripts/chaos/`.
- Templates: `templates/chaos-experiment.yaml`.
- Reports: `monitoring/reports/chaos`.

## Related skills
- `/incident-triage-runbook`: engages when chaos reveals incidents.
- `/capacity-planning`: validates autoscaler capacity headroom.
- `/ai-agent-orchestration`: integrates chaos/load tests into larger workflows.

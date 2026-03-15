---
name: deployment-strategy
description: |
  Define, validate, and enforce deployment strategies (blue/green, canary, rolling) with AI risk scoring, telemetry checks, and human gates to keep releases stable.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Deployment Strategy — World-class Release Orchestration Playbook

Coordinates deployment strategies across pipelines, clusters, and environments while capturing strategy intelligence and gating high-risk actions.

## When to invoke
- In planning release strategies for major deployments or migrations.
- When investigating deployment failures or rollback decisions.
- When new clusters or services require staged promotion rules.
- Dispatcher events mark `strategy-review`, `deployment-plan`, `rollback-recommendation`.

## Capabilities
- **Strategy modeling** compares blue/green, canary, rolling, feature flag combos with metrics and risk.
- **Policy validation** ensures strategies respect SLOs, maintenance windows, and compliance constraints.
- **Telemetry gating** ties strategy steps to golden signals, enabling auto-rollback or hold.
- **Human gates** ensure high risk or executive-impact promotions pause for review.
- **Shared context** stored at `shared-context://memory-store/deployment-strategy/{operationId}`.

## Invocation patterns
```bash
/deployment-strategy model --strategy=canary --cluster=aks-hub --traffic=10%
/deployment-strategy validate --strategy=blue-green --region=us-west
/deployment-strategy escalate --issue=rollback --priority=high
/deployment-strategy recommend --artifact=app:v4 --strategy=rolling
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `strategy` | Deployment strategy name. | `canary` |
| `cluster` | Target cluster/environment. | `aks-hub` |
| `traffic` | Traffic percentage for canary. | `10%` |
| `region` | Region env for release. | `us-west` |
| `issue` | Deployment issue tag. | `rollback` |
| `artifact` | Artifact/manifest identifier. | `app:v4` |

## Output contract
```json
{
  "operationId": "DS-2026-0315-01",
  "strategy": "canary",
  "cluster": "aks-hub",
  "status": "modeled|valid|escalated",
  "riskScore": 0.44,
  "recommendation": "increase traffic after 15m if errors < 1%",
  "logs": "shared-context://memory-store/deployment-strategy/DS-2026-0315-01"
}
```

## World-class workflow templates

### Strategy modeling
1. Capture artifact, environment, SLAs, and dependencies.
2. Simulate outcomes for canary/blue-green/rolling.
3. Emit `strategy-modeled` events and detail risk metrics.
4. Command stub: `/deployment-strategy model --strategy=canary --cluster=aks-hub --traffic=10%`

### Validation & gating
1. Cross-check SLOs/SLA windows, maintenance windows, policy.
2. Mark steps requiring human gate and store contexts.
3. Command stub: `/deployment-strategy validate --strategy=blue-green --region=us-west`

### Escalation & rollback recommendation
1. Monitor telemetry and escalate when thresholds breached.
2. Recommend rollback or hold with decision context.
3. Command stub: `/deployment-strategy escalate --issue=rollback --priority=high`

### Recommendation & automation
1. Suggest traffic adjustments, sequencing, retries.
2. Emit `strategy-recommendation` and link to workflows/comm.
3. Command stub: `/deployment-strategy recommend --artifact=app:v4 --strategy=rolling`

## AI intelligence highlights
- **Strategy scoring** numbers risk vs benefit for each release type.
- **Anomaly-aware gating** correlates telemetry to stop promotions early.
- **Narrative outputs** provide exec-friendly rationale.

## Memory agent & dispatcher integration
- Save strategies at `shared-context://memory-store/deployment-strategy/{operationId}`.
- Emit events: `strategy-modeled`, `strategy-validated`, `strategy-escalated`, `strategy-recommended`.
- Subscribe to `incident-ready`, `ci-cd-alert`, `policy-risk`.

## Observability & telemetry
- Metrics: model accuracy, validation pass rate, escalation frequency.
- Logs: structured `log.event="strategy"` with `strategy`, `status`, `decisionId`.
- Dashboards: `/deployment-strategy metrics --format=prometheus`.
- Alerts: gating >15m, multiple rollbacks.

## Failure handling & retries
- Retry telemetry/API checks; escalate to human gate on repeated failures.
- Preserve contexts for compliance.

## Human gates
- Required when:
  1. Strategy impacts production-critical paths.
  2. RiskScore ≥ 0.85 or threshold breaches.
  3. Dispatcher flags manual review.

## Testing & validation
- Dry-run: `/deployment-strategy model --strategy=canary --cluster=test --traffic=5% --dry-run`
- Unit tests: `backend/deployment-strategy/`.
- Integration: `scripts/validate-deployment-strategy.sh`.
- Regression: nightly `scripts/nightly-strategy-smoke.sh`.

## Related skills
- `/deployment-validation`, `/workflow-management`, `/stakeholder-comms-drafter`

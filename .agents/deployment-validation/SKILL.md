---
name: deployment-validation
description: >
  Validate deployments with AI risk assessment, canary analysis, and rollback readiness before promoting, then automate go/no-go decisions.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Deployment Validation — World-class Gatekeeper

Combines pre-flight validation, telemetry-driven canary analysis, automated rollback, and context-aware GO/NO-GO decisions so every release is gatechecked before user traffic shifts.

## When to invoke
- Before approving or promoting any release (rolling, blue/green, canary, or progressive deployments).
- When golden-signal telemetry must gate traffic shifts or when metric drift appears during rollout.
- While investigating incidents to verify if a deployment introduced degradation.
- When `ai-agent-orchestration` or memory agents flag risky deployments, cost spikes, or compliance gaps that could require rollback.

## Capabilities
- **AI Deployment Risk Assessment** scores pre-flight readiness and runtime indicators using change size, dependency health, and past MTTR.
- **Smart Canary Analysis** evaluates per-step metrics, surfaces drift, and recommends promote/hold/rollback decisions with explanations.
- **Intelligent Rollback Triggers** detect early deviation (latency drift, saturation) and initiate rollbacks before user impact grows.
- **Automated GO/NO-GO Decisions** fuse AI risk, metrics, and policy to auto-approve low-risk releases or escalate high-risk events.
- **Audit-grade Observability** ties metrics/logs to Prometheus, Grafana, Slack/Teams, and shared context stores for traceability.

## Invocation patterns

```bash
/deployment-validation preflight --deploymentId=DEP-2026-081 --strategy=canary
/deployment-validation canary --deploymentId=DEP-2026-081 --thresholds=latency=1.5,errorRate=1%
/deployment-validation rollback --deploymentId=DEP-2026-081 --reason=healthy_check_failed
/deployment-validation decision --deploymentId=DEP-2026-081 --humanGate=true
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `deploymentId` | Deployment identifier or tracker. | `DEP-2026-081` |
| `strategy` | Deployment approach (rolling, canary, blue-green). | `canary` |
| `thresholds` | Metric thresholds per strategy. | `latency:1.5,errorRate:1%` |
| `region` | Region/tenant scope. | `us-east-1` |
| `approval` | Whether a human gate already granted permission. | `true|false` |

## Output contract

```json
{
  "deploymentId": "DEP-2026-081",
  "strategy": "canary",
  "riskScore": 0.72,
  "aiDecision": "GO|NO-GO|HUMAN_GATE",
  "gates": {
    "smoke": "pass",
    "health": "pass",
    "goldenSignals": "pass",
    "canary": "warning"
  },
  "rollbackTriggered": false,
  "recommendations": [
    {
      "metric": "errorRate",
      "value": 1.2,
      "threshold": 1.0,
      "action": "delay-promotion"
    }
  ],
  "logs": "shared-context://memory-store/deployments/DEP-2026-081",
  "decisionContext": "redis://memory-store/deployments/DEP-2026-081",
  "humanGate": {
    "required": true,
    "impact": "Canary promotion blocked",
    "reversible": "Yes"
  }
}
```

## World-class workflow templates

### Pre-flight AI risk assessment
1. Validate manifests/images (kubeval, trivy, sigstore) and scan artifact provenance for tampering.
2. Execute regression/smoke suites and gather dependency health, service maps, and policy attestations.
3. Score readiness with an AI model that blends test coverage, change volume, past MTTR, and dependency freshness.
4. Emit `deployment-risk` events containing `riskScore`, dependency health, and gate recommendations.
5. Command stub: `/deployment-validation preflight --deploymentId=DEP-2026-081 --strategy=canary`.

### Smart canary analysis
1. Evaluate golden signals per canary step (latency, error rate, saturation, throughput) with sliding-window comparisons.
2. Compare against baseline using anomaly detection and explainable AI, surface the confidence for each recommendation.
3. Recommend `promote`, `hold`, or `rollback` with rationale, confidence, and dependency impact.
4. Trigger `/deployment-validation canary` or dispatch automation commands to enact the decision.

### Intelligent rollback triggers & automation
1. Detect soft signals (latency drift, downstream errors, dependency flaps) before hard thresholds breach.
2. Decide between immediate rollback or holding the canary based on cost/risk tradeoffs, human availability, and SLA exposure.
3. Emit `deployment-rollback` events, notify stakeholders, and log to `deployment-history` with rollback rationale.

### Automated GO/NO-GO decisions
1. Fuse AI risk, telemetry, dependency health, approval state, and policy constraints before concluding.
2. Auto-approve (GO) if all gates pass with low risk; otherwise require a human gate (NO-GO or HUMAN_GATE).
3. Document the decision, persist it to shared context, and notify orchestration skills for follow-on work.

## AI intelligence highlights
- **AI Deployment Risk Assessment** blends test depth, change size, dependency readiness, and historical incidents to quantify risk and highlight weak signals.
- **Smart Canary Analysis** reasons over per-step metrics, anomalies, and confidence to produce promotion/rollback recommendations with explanations.
- **Intelligent Rollback Triggers** spot subtle drift or saturation, trigger early rollback, and preserve rollback rationale.
- **Automated GO/NO-GO Decisions** continuously compare policy, telemetry, and approvals to emit actionable decisions (GO, NO-GO, HUMAN_GATE).

## Memory agent & dispatcher integration
- Persist decisions and telemetry to `shared-context://memory-store/deployments/{deploymentId}` so downstream skills can replay the rationale.
- Emit events (`deployment-risk`, `deployment-go`, `deployment-no-go`, `deployment-rollback`) so orchestrators chain follow-ups automatically.
- Subscribe to memory agent insights (cost spikes, compliance issues, incident flags) and adjust thresholds or human gate decisions.
- Communicate via the event bus (Pulsar/Kafka) for canary, rollback, and gate states; fallback to `artifact-store://deployments/{id}.json` when the bus is offline.

## Observability & telemetry
- Metrics: gates per deployment, risk score distribution, rollback rate, model confidence, throttle events.
- Logs: structured `log.event` entries for `deployment-risk`, `canary-eval`, `rollback-trigger`, and `decisionId`/`tenant` metadata.
- Dashboards: expose `/deployment-validation metrics --format=prometheus` for deployment health and on-call monitoring.
- Alerts: risk scores > 0.85, >2 deployment alerts per rollout, rollback rate >5% per week, or training data drift in AI decision models.

## Failure handling & retries
- Retry telemetry pulls (Prometheus/Datadog/New Relic) up to 3 times before escalating a gate failure.
- If rollback automation fails, log the error, notify on-call (Slack/Teams/SMS), and escalate to `incident-triage-runbook`.
- Preserve audit artifacts (`reports/deployments/{deploymentId}.json`, `logs/deployment-coordinator.log`) until downstream acknowledgements.

## Human gates
- Required when any AI decision resolves to `NO-GO`/`HUMAN_GATE`, when rollback touches >20 tenants or critical services, or when risk score ≥ 0.9 despite passing gates.
- Confirmation template aligns with the orchestrator format:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/deployment-validation preflight --deploymentId=DEP-DRY-RUN --dry-run=true`.
- Unit tests: `backend/deployments/validation` covers AI risk scoring and canary logic.
- Integration: `scripts/validate-deployment-coordinator.sh` exercises the full runbook and event bus handoffs.
- Regression: nightly `scripts/nightly-deployment-smoke.sh` ensures GO/NO-GO logic, telemetry, and gate notifications stay stable.

## References
- Deployment history ledger: `logs/deployments/`.
- Canary/rollout metrics: `monitoring/deployments/`.
- Runbook templates: `docs/DEPLOYMENT_STATUS.md`, `docs/DEPLOYMENT_STRATEGIES.md`.

## Related skills
- `/ai-agent-orchestration`: coordinates multi-skill remediation and post-deployment follow-up.
- `/workflow-management`: tracks deployment workflows and reruns validations as needed.
- `/incident-triage-runbook`: escalates incident responses triggered by deployment rollback events.

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

Combines pre-flight checks, telemetry-driven canary analysis, automated rollback, and contextual go/no-go decisions. Trigger when deploying to any environment where user impact matters—especially prod, staging, or multi-tenant surfaces.

## When to invoke
- Before approving or promoting any new release (rolling, blue/green, canary, canary + progressive).
- When realtime telemetry (golden signals) must gate traffic shifts.
- During incident post-mortem to confirm if a deployment triggered degradation.
- From `ai-agent-orchestration` when memory agents flag risky deployments or `cost-optimization`/`incident-triage` demand rollback validation.

## Capabilities
- AI deployment risk assessment scoring (pre-flight and runtime) combining test, metric, and dependency data.
- Smart canary analysis that evaluates metrics per step, surfaces drift, and recommends promotion/rollback.
- Intelligent rollback triggers that pre-empt user impact by detecting early deviation.
- Automated GO/NO-GO gating that factors in deployment risk, business impact, and human approvals.
- Observability ties into Prometheus, Grafana, Slack/Teams, and audit logs for traceability.

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
| `deploymentId` | Deployment identifier (tracker). | `DEP-2026-081` |
| `strategy` | Deployment strategy (rolling, canary, blue-green). | `canary` |
| `thresholds` | Metric thresholds per strategy. | `latency:1.5,errorRate:1%` |
| `region` | Region/tenant scope. | `us-east-1` |
| `approval` | Whether human gate already approved. | `true|false` |

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
1. Validate manifests/images (kubeval, trivy).
2. Run regression smoke suite.
3. Score readiness using AI risk model (tests, change volume, dependency health).
4. Emit `deployment-risk` event with `riskScore` and recommended gate.

### Smart canary analysis
1. Analyze golden signals per step (latency, error rate, saturation, throughput).
2. Compare sliding window metrics to baseline with anomaly detection.
3. Recommend `promote`, `hold`, or `rollback` with confidence and rationale.
4. Use `/deployment-validation canary` to implement decision.

### Intelligent rollback triggers & automation
1. Detect soft signals (latency drift, downstream error) before hitting threshold.
2. Evaluate cost/risk tradeoff to decide immediate rollback vs hold.
3. Trigger `rollback` command with reason, notify stakeholders, log to `deployment-history`.

### Automated GO/NO-GO decisions
1. Combine AI risk, canary metrics, change volume, dependency status.
2. If risk < threshold and metrics pass, auto-approve (GO).
3. If risk high or metrics degrade, require human confirmation (NO-GO/human gate).

## AI intelligence highlights
- **AI Deployment Risk Assessment**: Models combine test coverage, change size, dependency health, and past MTTR to score deployment risk.
- **Smart Canary Analysis**: Evaluates per-step metrics, anomaly deviation, and recommends promotion/rollback with explanations.
- **Intelligent Rollback Triggers**: Detects subtle drift (latency, saturation) and triggers rollback before significant impact.
- **Automated GO/NO-GO Decisions**: Context-aware gating that fuses AI risk, telemetry, and policy to output actionable decisions.

## Memory agent & dispatcher integration
- Write decision context to `shared-context://memory-store/deployments/{deploymentId}` for other skills.
- Emit events `deployment-risk`, `deployment-go`, `deployment-no-go`, `deployment-rollback`.
- Subscribe to memory agent insights (cost spike, compliance risk) to adjust thresholds on the fly.

## Communication protocol
- Primary: CLI/webhook invocation, event bus messages for canary and rollback states.
- Secondary: HTTP webhook to Slack/Teams using `SLACK_WEBHOOK`, `TEAMS_WEBHOOK`.
- Fallback: Artifact store entries (`artifact-store://deployments/{id}.json`) if event bus is unavailable.

## Observability & telemetry
- Metrics: gates per deployment, risk score distribution, rollback frequency, model confidence.
- Logs: structured `log.event` for `deployment-risk`, `canary-eval`, `rollback`.
- Dashboards: integrate `/deployment-validation metrics --format=prometheus` for deployment health.
- Alerts: risk scores > 0.85, >2 alerts per deployment, rollback rate > 5% per week.

## Failure handling & retries
- Retry telemetry pulls (Prometheus/Datadog) up to 3 times before failing gate.
- If rollback command fails, log error, notify on-call, and escalate to `incident-triage-runbook`.
- Preserve artifacts (`reports/deployments/{deploymentId}.json`) for auditing; never delete until retention policy reached.

## Human gates
- Required when:
 1. AI decision is `NO-GO` or `HUMAN_GATE`.
 2. Rollback affects >20 tenants or production-critical services.
 3. Risk score ≥ 0.9 despite gate passing.
- Use the standard confirmation template.

## Testing & validation
- Dry-run: `/deployment-validation preflight --deploymentId=DEP-DRY-RUN --dry-run=true`.
- Unit tests: `backend/deployments/validation` covers AI risk scoring and canary logic.
- Integration: `scripts/validate-deployment-coordinator.sh` triggers full runbook and monitors event bus.
- Regression: nightly script `scripts/nightly-deployment-smoke.sh` ensures GO/NO-GO logic remains stable.

## References
- Deployment history ledger: `logs/deployments/`.
- Canary/rollout metrics: `monitoring/deployments/`.
- Runbook templates: `docs/DEPLOYMENT_STATUS.md`, `docs/DEPLOYMENT_STRATEGIES.md`.

## Related skills
- `/ai-agent-orchestration`: orchestrates multi-skill remediation based on risk and findings.
- `/workflow-management`: tracks deployment workflows and can rerun validations.
- `/incident-triage-runbook`: coordinates rollback-triggered incidents.

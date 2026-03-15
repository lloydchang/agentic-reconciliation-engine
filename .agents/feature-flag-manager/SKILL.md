---
name: feature-flag-manager
description: |
  Evaluate, propagate, and retire feature flags with AI-guided staging, rollback safety, and telemetry so releases remain controlled and reversible.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Feature Flag Manager — World-class Release Control Playbook

Governs feature flag lifecycle across environments by assessing risk, synchronizing targeting rules, and orchestrating rollbacks with human gates.

## When to invoke
- Deploying features protected by flags into staging or production.
- Rolling out progressive exposure (percentage rollout, canary) or toggling critical controls.
- Observing flag-driven anomalies and needing to rollback or reduce exposure.
- Policy/risk agents request flag adjustments to meet compliance or stability thresholds.

## Capabilities
- **Flag lifecycle orchestration**: create, update, toggle, retire flags across environments.
- **AI risk scoring**: analyzes flag scope, dependencies, and historical incidents before pushing changes.
- **Telemetry integration**: logs flag events into shared context for auditing (`shared-context://memory-store/feature-flag-manager/{operationId}`).
- **Human-in-the-loop gating**: flags targeting exec/error channels require approvals before enabling.
- **Rollback automation**: revert problematic flags automatically with pre-defined playbooks.

## Invocation patterns
```bash
/feature-flag-manager create --flag=beta-ux --rule=tenant-42 --enabled=false
/feature-flag-manager rollout --flag=beta-ux --percentage=20 --region=us-east
/feature-flag-manager monitor --flag=beta-ux --window=60m
/feature-flag-manager rollback --flag=beta-ux --reason="latency spike"
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `flag` | Feature flag identifier. | `beta-ux` |
| `rule` | Targeting rule (tenant, audience). | `tenant-42` |
| `percentage` | Rollout percentage. | `20` |
| `region` | Region or environment. | `us-east` |
| `window` | Monitoring window/duration. | `60m` |
| `reason` | Rollback explanation. | "latency spike" |

## Output contract
```json
{
  "operationId": "FF-2026-0315-01",
  "flag": "beta-ux",
  "status": "pending|active|rolling-back",
  "riskScore": 0.37,
  "rollout": { "percentage": 20, "region": "us-east", "enabled": true },
  "events": [ { "name": "flag-created", "timestamp": "2026-03-15T08:12:00Z" } ],
  "logs": "shared-context://memory-store/feature-flag-manager/FF-2026-0315-01",
  "decisionContext": "redis://memory-store/feature-flag-manager/FF-2026-0315-01"
}
```

## World-class workflow templates

### Flag creation & staging
1. Define flag metadata, environment, default state, and targeting rules.
2. Score risk (service criticality, scope, dependencies) before allowing staging.
3. Emit `flag-created` event and store metadata.
4. Command stub: `/feature-flag-manager create --flag=beta-ux --rule=tenant-42 --enabled=false`

### Progressive rollout
1. Increase exposure via percentage rollouts or audience segments.
2. Monitor telemetry (latency, errors) and adjust pace via AI guardrails.
3. Emit `flag-rollout` events and adjust dashboards.
4. Command stub: `/feature-flag-manager rollout --flag=beta-ux --percentage=20 --region=us-east`

### Monitoring & rollback readiness
1. Track behavioral signals tied to flags (error rate, performance, user feedback).
2. If anomalies arise, prepare rollback path with human approval.
3. Command stub: `/feature-flag-manager monitor --flag=beta-ux --window=60m`

### Automated rollback & cleanup
1. When risk rises (latency spike, crash loops), revert flag state automatically.
2. Emit `flag-rolled-back` events, document reasoning, and notify stakeholders.
3. Command stub: `/feature-flag-manager rollback --flag=beta-ux --reason="latency spike"`

## AI intelligence highlights
- **Risk scoring** balances feature scope, dependencies, and historical flag issues.
- **Adaptive rollout pacing** adjusts percentages based on real-time telemetry.
- **Rollback prediction** warns when a flag is likely to trigger user impact.

## Memory agent & dispatcher integration
- Store flag state in `shared-context://memory-store/feature-flag-manager/{operationId}`.
- Emit events: `flag-created`, `flag-rollout`, `flag-monitored`, `flag-rollback`, `flag-human-gate`.
- Listen for `incident-ready`, `change-management`, `cost-anomaly` signals to adjust flags.
- Tag context with `decisionId`, `flag`, `audience`, `riskScore`, `region`.

## Observability & telemetry
- Metrics: rollout velocity, rollback count, gate frequency.
- Logs: structured `log.event="feature-flag"` with `flag`, `status`, `decisionId`.
- Dashboards: integrate `/feature-flag-manager metrics --format=prometheus` for release control.
- Alerts: manual gates pending >10m, rollouts hitting error thresholds, repeated rollbacks.

## Failure handling & retries
- Retry API calls to flag stores (LaunchDarkly, Unleash, Flagr) up to 3× with backoff.
- If automation fails, fall back to manual toggles and alert incident teams.
- Preserve history for audits; do not delete entries before stakeholders ack.

## Human gates
- Required when:
  1. Flags target production critical services or hop across >1 cluster.
  2. Automation would expose sensitive data or affect compliance.
  3. Dispatcher requests manual approval after multiple rollbacks.

## Testing & validation
- Dry-run: `/feature-flag-manager rollout --flag=test-flag --percentage=5 --dry-run`
- Unit tests: `backend/feature-flag/` ensures rule parsing and risk scoring behave.
- Integration: `scripts/validate-feature-flag-manager.sh` toggles flags end-to-end.
- Regression: nightly `scripts/nightly-flag-smoke.sh` ensures gating & rollout events fire.

## References
- Scripts: `scripts/feature-flag-manager/`.
- Templates: `templates/flags/`.
- Monitoring: `monitoring/flags/`.

## Related skills
- `/deployment-validation`: gates deploys affected by flags.
- `/incident-triage-runbook`: responds to flag-driven incidents.
- `/workflow-management`: schedules rollout automation.

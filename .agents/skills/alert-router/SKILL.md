---
name: alert-router
description: |
  Route, enrich, and deliver alerts/notifications to the right teams/channels with AI intent, context enrichment, and dispatcher wiring so only the most relevant recipients act on specific incidents.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Alert Router — World-class Delivery Playbook

Takes incoming alerts/events, enhances them with context, evaluates intent/risk, and forwards them to the right Slack/PagerDuty/email channel while tracking delivery state in shared context.

## When to invoke
- A monitoring tool (Prometheus, Sentinel, Datadog) emits an alert that needs a specific responder.
- Incident triage needs human approvals before escalation, or incidents must be broadcast to leadership.
- Automation steps (policy enforcement, deployment rollback) require follow-up notifications.
- Dispatcher/memory agents request channel-specific notifications based on severity, business impact, or compliance needs.

## Capabilities
- **Channel intelligence** determines whether alerts go to Slack, Teams, PagerDuty, email, or internal dashboards.
- **Context enrichment** attaches incident metadata, runbooks, risk scoring, and recommendations before routing.
- **Intent-aware routing** uses skill/alert tags to decide whether to page SRE, notify security, or escalate to execs.
- **Delivery tracking** logs delivery status and retransmits failures while keeping state under `shared-context://memory-store/alert-router/{deliveryId}`.
- **Human gate enforcement** prevents automatic escalation for sensitive audiences; routing requires explicit approvals.

## Invocation patterns
```bash
/alert-router route --alert=INC-2026-0315-01 --channel=pagerduty --audience=SRE
/alert-router review --deliveryId=DELIV-001 --humanGate=true
/alert-router status --deliveryId=DELIV-001
/alert-router cancel --deliveryId=DELIV-001 --reason="false positive"
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `alert` | Incident/alert identifier. | `INC-2026-0315-01` |
| `channel` | Destination channel (`pagerduty`, `slack`, `teams`, `email`). | `pagerduty` |
| `audience` | Target audience (`SRE`, `security`, `executive`). | `SRE` |
| `deliveryId` | Delivery tracking identifier. | `DELIV-001` |
| `humanGate` | Whether review is required. | `true` |
| `reason` | Cancellation reason. | "false positive" |

## Output contract
```json
{
  "deliveryId": "DELIV-001",
  "status": "sent|pending|failed|cancelled",
  "channel": "slack",
  "audience": "SRE",
  "alert": "INC-2026-0315-01",
  "riskScore": 0.72,
  "content": "Service degradation: payments cluster (details...)",
  "logs": "shared-context://memory-store/alert-router/DELIV-001",
  "decisionContext": "redis://memory-store/alert-router/DELIV-001",
  "humanGate": {"required": true, "impact": "Executive notification", "reversible": "No"}
}
```

## World-class workflow templates

### AI intentful routing
1. Analyze the alert, riskScore, and policy tags to decide channel + audience.
2. Enrich message with runbook links, mitigation steps, and ETA.
3. Dispatch via the channel's API (Slack/PagerDuty/Teams/email) and record delivery.
4. Command stub: `/alert-router route --alert=INC-2026-0315-01 --channel=pagerduty --audience=SRE`

### Delivery tracking & retries
1. Follow delivery status and track responses or escalations.
2. Retry failed deliveries up to 3×; notify downstream skills when a channel is down.
3. Emit `alert-delivery` or `alert-delivery-failed` events.
4. Command stub: `/alert-router status --deliveryId=DELIV-001`

### Human gate review
1. If routing touches execs/security, require a human gate with context.
2. Store approval under shared context and emit `alert-human-gate`/`alert-human-clear`.
3. Only send after gates are cleared.
4. Command stub: `/alert-router review --deliveryId=DELIV-001 --humanGate=true`

### Cancellation & cleanup
1. Cancel pending deliveries if alerts resolve or are false positives.
2. Notify recipients (if already sent) about the cancellation.
3. Emit `alert-delivery-cancelled` and archive context.
4. Command stub: `/alert-router cancel --deliveryId=DELIV-001 --reason="false positive"`

## AI intelligence highlights
- **Intent-aware routing** reasons over severity, business impact, and policy tags to choose the right channel.
- **Adaptive messaging** tailors tone and detail based on audience (exec vs SRE vs security).
- **Playback resilience** tracks delivery health and auto-retries with escalating channels if needed.

## Memory agent & dispatcher integration
- Persist routing decisions under `shared-context://memory-store/alert-router/{deliveryId}` with `decisionId`, `channel`, `audience`, `riskScore`.
- Emit events: `alert-routed`, `alert-delivery-failed`, `alert-human-gate`, `alert-human-clear`, `alert-cancelled`.
- Subscribe to dispatcher signals (`incident-ready`, `policy-risk`, `cost-anomaly`) to route new alerts.

## Observability & telemetry
- Metrics: delivery success rate, human gates triggered, retries, cancellations.
- Logs: structured `log.event="alert.delivery"` with `deliveryId`, `channel`, `alert`, `riskScore`.
- Dashboards: feed `/alert-router metrics --format=prometheus` to SOC ops.
- Alerts: channel outages, repeated manual cancels, automation loops hitting gates.

## Failure handling & retries
- Retry channel APIs (Slack/PagerDuty) up to 3× with exponential backoff before escalating to secondary channel.
- If message formatting fails, fall back to a plain summary and alert SRE tunnels.
- On repeated failures route to `incident-triage-runbook` or `stakeholder-comms-drafter` for manual communication.

## Human gates
- Required when:
  1. Audience is `executive` or `security` with high `riskScore`.
  2. Routing modifies access controls (policy, firewall) or exposes sensitive data.
  3. Dispatcher requests manual approval after automation loops.

## Testing & validation
- Dry-run: `/alert-router route --alert=INC-DRY-RUN --channel=slack --audience=SRE --dry-run`
- Unit tests: `backend/alert-router/` ensures routing logic and channel adapters behave as expected.
- Integration: `scripts/validate-alert-router.sh` exercises Slack/PagerDuty/Teams endpoints using sandbox credentials.
- Regression: nightly `scripts/nightly-alert-router-smoke.sh` verifies delivery tracking, retries, and human gates.

## References
- Channel adapters: `cmd/alert-router/` and `scripts/alert-router/`.
- Templates: `templates/alerts/`.
- Monitoring: `monitoring/alert-router/`.

## Related skills
- `/incident-triage-runbook`: responds to the alert incidents created here.
- `/alert-prioritizer`: provides alerts with high risk for routing.
- `/stakeholder-comms-drafter`: crafts the follow-up messaging once alerts are routed.

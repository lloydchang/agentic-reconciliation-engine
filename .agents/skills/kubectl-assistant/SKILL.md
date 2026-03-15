---
name: kubectl-assistant
description: >
  Translate natural language Kubernetes tasks into safe kubectl commands with contextual explanations and AI safety checks.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Kubectl Assistant — World-class Kubernetes Command Playbook

Interprets user requests into well-formed kubectl commands, enforces safety (no destructive actions without confirmation), and provides explanations for operator actions. Use when operators need assistance with get/describe/rollout/join operations or to verify commands before execution.

## When to invoke
- User asks how to inspect pods, services, or deploy resources.
- Requests to scale, restart, roll out, or debug workloads.
- Need safe command generation for destructive actions (delete/scale down) with human gate checks.
- Provide CLI steps for standard troubleshooting flows.

## Capabilities
- Interpret natural language into kubectl CLI commands with appropriate flags.
- Validate safety (disallow `delete`/`rm` without explicit confirm) and add human gate prompts when needed.
- Provide explanations of what the command does and expected outcomes.
- Shared context `shared-context://memory-store/kubectl/<operationId>`.

## Invocation patterns

```bash
/kubectl-assistant explain "show all pods in namespace production"
/kubectl-assistant generate "restart the web deployment" --confirm
/kubectl-assistant help "add label team=platform to namespace staging"
/kubectl-assistant safe-delete "delete pods with label app=worker" --confirm
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `command` | Natural language request. | `show pods` |
| `namespace` | Target namespace. | `production` |
| `label` | Filter label selectors. | `app=web` |
| `confirm` | Require confirmation for destructive actions. | `true` |
| `operationId` | Reference for command session. | `KUBE-2026-0315-01` |

## Output contract

```json
{
  "operationId": "KUBE-2026-0315-01",
  "status": "ready|blocked",
  "command": "kubectl get pods -n production",
  "explanation": "Lists all pods in the production namespace.",
  "safety": {
    "destructive": false,
    "confirmRequired": false
  },
  "aiInsights": {
    "riskScore": 0.12,
    "confidence": 0.94
  },
  "decisionContext": "redis://memory-store/kubectl/KUBE-2026-0315-01",
  "logs": "shared-context://memory-store/kubectl/KUBE-2026-0315-01"
}
```

## World-class workflow templates

### Inspection command generation
1. Parse request (get/describe/logs) and identify target resource.
2. Build kubectl command with selectors/namespace.
3. Emit `kubectl-command` event for review.

### Destructive action gating
1. Detect destructive verbs (`delete`, `scale down`).
2. Require confirmation or suggest safe alternative.
3. Emit `kubectl-gated` event until confirmed.

### Troubleshooting flow
1. Generate sequence of commands (inspect pods → describe → logs).
2. Provide explanation for each step.
3. Return combined script ready for operator execution.

## AI intelligence highlights
- **AI Command Interpretation**: extracts resources, filters, and actions with high confidence.
- **Risk Scoring**: flags commands with riskScore near 1 (delete/scale) and requires human approval.
- **Narrative Explanation**: describes what the command will do and why it was chosen.

## Memory agent & dispatcher integration
- Store commands in `shared-context://memory-store/kubectl/<operationId>`.
- Emit `kubectl-command`, `kubectl-gated`, `kubectl-executed` events.
- Dispatcher can log commands/alerts and feed into incident workflows.
- Tag entries with `decisionId`, `target`, `riskScore`.

## Communication protocols
- Primary: CLI output requests (kubectl commands).
- Secondary: Event bus for `kubectl-*` events.
- Fallback: JSON artifacts for audit `artifact-store://kubectl/<operationId>.json`.

## Observability & telemetry
- Metrics: commands generated, destructive gates triggered, approvals issued.
- Logs: structured `log.event="kubectl.command"` with `operationId`.
- Dashboards: integrate `/kubectl-assistant metrics --format=prometheus`.
- Alerts: gate delays > threshold, command failures > threshold.

## Failure handling & retries
- Retry parsing up to 2× on unclear requests; prompt for clarifications if still ambiguous.
- If command generation fails (lack of permissions), escalate to `incident-triage`.
- Keep artifacts until downstream ack.

## Human gates
- Required when:
 1. Command is destructive (delete/scale down).
 2. RiskScore high or target is production-critical.
 3. Dispatcher requests manual review after repeated gate blocks.
- Use standard confirmation template.

## Testing & validation
- Dry-run: `/kubectl-assistant explain --command="list pods" --dry-run`.
- Unit tests: `backend/kubectl/` ensures parser+templates.
- Integration: `scripts/validate-kubectl-assistant.sh` tests gating flows.
- Regression: nightly `scripts/nightly-kubectl-smoke.sh` ensures accuracy and gating.

## References
- Scripts: `scripts/kubectl/`.
- Templates: `templates/kubectl-command.md`.

## Related skills
- `/incident-triage-runbook`: uses commands for remediations.
- `/kubernetes-cluster-manager`: depends on scale/policy commands.

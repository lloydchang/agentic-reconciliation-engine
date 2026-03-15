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

Interprets user requests into well-formed kubectl commands, enforces safety, and explains expected outcomes before execution.

## When to invoke
- Operators ask how to inspect pods, services, deployments, or manifests.
- Request scaling, restarting, rollouts, or debugging workloads.
- Need safe commands for destructive actions (delete/scale down) with human gate prompts.
- Deliver scripted troubleshooting flows.

## Capabilities
- **Natural language parsing** into kubectl CLI commands with proper flags/namespaces.
- **Safety validation** blocking destructive runs until confirmation.
- **Narrative explanation** describing command intent and expected result.
- **Shared context propagation** via `shared-context://memory-store/kubectl/{operationId}`.
- **Human gate orchestration** for high-risk commands.

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
| `label` | Label selector filter. | `app=web` |
| `confirm` | Confirm destructive actions. | `true` |
| `operationId` | Session reference. | `KUBE-2026-0315-01` |

## Output contract

```json
{
  "operationId": "KUBE-2026-0315-01",
  "status": "ready|blocked",
  "command": "kubectl get pods -n production",
  "explanation": "Lists all pods in the production namespace.",
  "safety": { "destructive": false, "confirmRequired": false },
  "aiInsights": { "riskScore": 0.12, "confidence": 0.94 },
  "decisionContext": "redis://memory-store/kubectl/KUBE-2026-0315-01",
  "logs": "shared-context://memory-store/kubectl/KUBE-2026-0315-01"
}
```

## World-class workflow templates

### Inspection command generation
1. Parse request (get/describe/logs) and identify resource/namespace.
2. Build kubectl command with selectors and options.
3. Emit `kubectl-command` event for review.

### Destructive action gating
1. Detect destructive verbs (`delete`, `scale down`).
2. Require confirmation or suggest safer alternatives.
3. Emit `kubectl-gated` event until authorized.

### Troubleshooting flow
1. Generate step sequence (inspect pods → describe → logs) with explanations.
2. Provide combined script for operator execution.
3. Log revisit context for incident follow-ups.

## AI intelligence highlights
- **AI command interpretation** infers resources, filters, and actions with high confidence.
- **Risk scoring** flags destructive commands for review.
- **Narrative explanation** articulates command effect and expected outcome.

## Memory agent & dispatcher integration
- Persist commands under `shared-context://memory-store/kubectl/{operationId}`.
- Emit events: `kubectl-command`, `kubectl-gated`, `kubectl-executed`.
- Dispatcher logs commands, impacts operations, and feeds into incident workflows.
- Tag metadata with `decisionId`, `target`, `riskScore`.

## Observability & telemetry
- Metrics: commands generated, destructive gates triggered, review delays.
- Logs: structured `log.event="kubectl.command"` with `operationId`.
- Dashboards: integrate `/kubectl-assistant metrics --format=prometheus` for K8s ops.
- Alerts: gate delays > threshold, command failures rate high.

## Failure handling & retries
- Retry parsing up to 2× on ambiguous requests; prompt for clarification if unresolved.
- If generation fails (permissions, context), escalate to `incident-triage-runbook`.
- Preserve artifacts/logs until downstream ack.

## Human gates
- Required when:
  1. Command is destructive or touches production-critical workloads.
  2. RiskScore high or targets large tenant groups.
  3. Dispatcher demands manual review after repeated gating.
- Use standard confirmation template capturing impact and reversibility.

## Testing & validation
- Dry-run: `/kubectl-assistant explain --command="list pods" --dry-run`.
- Unit tests: `backend/kubectl/` ensures parsing/templating accuracy.
- Integration: `scripts/validate-kubectl-assistant.sh` exercises gating and command flows.
- Regression: nightly `scripts/nightly-kubectl-smoke.sh` ensures accuracy and gating.

## References
- Scripts: `scripts/kubectl/`.
- Templates: `templates/kubectl-command.md`.

## Related skills
- `/incident-triage-runbook`: uses commands for remediation.
- `/kubernetes-cluster-manager`: consumes scale/hardening commands.
- `/workflow-management`: includes commands as part of orchestration.

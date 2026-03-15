---
name: ai-agent-orchestration
description: Coordinate memory agents and downstream skills so every workflow can adapt dynamically based on agent outputs, telemetry, and guardrails.
argument-hint: "[action] [agentType] [workflowType] [parameters]"
context: fork
agent: Plan
disable-model-invocation: false
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
---

# AI Agent Orchestration — World-class Operator Guide

Unifies Go/Rust/Python memory agents with downstream skills (compliance, security, cost, observability) using adaptive workflows, shared memory, and event-driven dispatchers.

## When to invoke
- Trigger orchestration when agent outputs dictate next skill (e.g., compliance findings → `compliance-security-scanner`, anomalies → `cost-optimization`, threats → `security-analysis`).
- Register memory agents, emit shared-context events, or monitor agent pools.
- Drive dispatcher workflows (`sequential`, `parallel`, `conditional`) with gating and telemetry.

## Capabilities
- **Multi-agent sequencing** with shared state stores and event bus integration.
- **Conditional dispatchers** that interpret agent outputs/events to route skills.
- **Shared memory + message flow** (Redis/ETCD + Kafka/NATS) with telemetry hooks.
- **Human gate enforcement**, retries, fallback agents, and structured JSON results.
- **AI risk scoring** aggregated across skills to determine gating needs.

## Invocation patterns

```bash
/ai-agent-orchestration orchestrate sequential --agents=go-memory,rust-memory,python-memory --target=production --workflow=memory-sync
/ai-agent-orchestration orchestrate conditional --workflow=dispatcher --context=shared-context://memory-store --timeout=1800
/ai-agent-orchestration register-agent go-memory --language=go --capabilities=memory-enrichment --context-store=redis://memory-store --task-queue=memory-go
/ai-agent-orchestration monitor-agents --status=detailed --metrics=queue-depth,latency
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `targetResource` | Focus scope (tenant, cluster). | `ProductionHub` |
| `environment` | Environment tag (`dev|staging|prod`). | `staging` |
| `priority` | Workflow priority for gating. | `high` |
| `timeframe` | Lookback for telemetry/replay. | `30d` |
| `region` | Cloud region limit. | `us-east-1` |

## Output contract

```json
{
  "workflowId": "uuid",
  "status": "started|running|completed|failed",
  "startedAt": "ISO8601",
  "result": {
    "agents": [ { "name": "go-memory", "status": "success", "output": "schema:/shared-context/discovery" } ],
    "skillsTriggered": [ {
      "name": "compliance-security-scanner",
      "reason": "config drift",
      "decision": "human_gate",
      "humanGate": { "required": true, "impact": "Prod change", "reversible": "No" }
    } ]
  },
  "errors": [],
  "metadata": {
    "decisionContext": "redis://memory-store",
    "invocationPattern": "conditional",
    "dispatcherVersion": "v2.1"
  }
}
```

## World-class workflow templates

### Sequential memory sync
1. Agents run Go → Rust → Python, enriching context in `shared-context://memory-store`.
2. Dispatcher listens for `agent-completed` to trigger next skill.
3. Command: `/ai-agent-orchestration orchestrate sequential --agents=go-memory,rust-memory,python-memory --workflow=memory-sync`.

### Conditional dispatcher
1. Evaluate agent payloads (`riskScore`, `anomalyType`, `tenant`).
2. Decision matrix routes to skills: high risk → `incident-triage-runbook`, cost spikes → `cost-optimization`, compliance concerns → `compliance-security-scanner`.
3. Invoke `/ai-agent-orchestration orchestrate conditional --workflow=dispatcher --context=redis://memory-store`.

### Parallel resiliency checks
1. Run `security-analysis` and `observability-stack` simultaneously after memory updates.
2. On failure fallback to lightweight agents (`security-analysis-lite`).
3. Command: `/ai-agent-orchestration orchestrate parallel --agents=security-analysis,observability-stack --timeout=1200`.

## AI intelligence highlights
- **AI dependency resolution** predicts ordering/conflicts across skills.
- **Aggregate risk scoring** determines gating needs based on blended outputs.
- **Anomaly detection** triggers alternative flows when repeated failures occur.

## Memory agent & dispatcher integration
- Shared memory: Redis/ETCD path `shared-context://<tenant>/<agent>/<artifact>`.
- Event bus topics: `agent-completed`, `agent-failed`, `insight-ready`, `skill-request`.
- Agents publish metadata (`tenant`, `region`, `riskScore`, `costImpact`).
- Dispatcher merges context and selects skills per template rules.
- Sample event payload preserved for traceability and audit.

## Communication protocols
- Primary: shared memory store (Redis/ETCD).
- Secondary: event bus (Kafka/NATS) for `agent-*` and `workflow-*` signals.
- Fallback: zipped artifacts via `artifact-store://` polled every 30s.
- Health: `/ai-agent-orchestration monitor-agents --status=detailed` collects queue depth, latency, failed jobs, resource usage.

## Observability & telemetry
- Metrics: agent execution time, dispatcher branching, skill success rates, context store latency.
- Logs: structured events with correlation IDs (`orchestrationId`, `agentRunId`, `decisionId`).
- Dashboards: include `/ai-agent-orchestration metrics --format=prometheus`.
- Alerts: >3 consecutive dispatcher failures or shared memory latency >500ms.

## Failure handling & retries
- Retry policy: 3 attempts per agent/skill with exponential backoff.
- Fallback agents (e.g., `security-analysis-lite`) for heavy operations.
- Escalate after repeated failures: log failure, store context, trigger human gate.
- Preserve intermediate state; never delete shared-context keys after failure.

## Human gates
- Required when:
  1. Dispatcher recommends prod changes (riskScore ≥ 90 or >20 tenants).
  2. `compliance-security-scanner` or `security-analysis` results dictate high-impact remediation.
  3. `cost-optimization` proposes spend >$5K/month increase.
- Template:
```
⚠️  HUMAN GATE: [description]
    Impact: [what changes]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/ai-agent-orchestration orchestrate sequential --dry-run`.
- Use `scripts/validate-memory-agents.sh` to simulate agent payloads and ensure routing.
- Unit tests: `backend/orchestration/dispatcher_rules/` verify decision logic.
- Nightly smoke: `/ai-agent-orchestration orchestrate parallel --agents=compliance-security-scanner,cost-optimization --nightly=true`.

## References
- Agent configs: `backend/agents/`.
- Dispatcher definitions: `backend/orchestration/dispatcher/`.
- Monitoring dashboards: `monitoring/agents/`.

## Related skills
- `/workflow-management`: monitors workflow history and execution.
- `/compliance-security-scanner`: validates recommendations before approval.
- `/incident-triage-runbook`: remediates critical dispatcher alerts.

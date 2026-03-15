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

This skill unifies the Go, Rust, and Python memory agents with every downstream skill (compliance, security, cost, observability, etc.) using adaptive workflows, shared memory stores, and event-driven dispatchers. Use it when you need conditional multi-agent runs, dynamic skill routing, unified logging/telemetry, or human-gated decision points.

## When to invoke
- Trigger implicit orchestration when agent outputs must determine the next skill (e.g., compliance findings should route to `compliance-check`, anomalies route to `cost-optimization`, threats route to `security-analysis`).
- Use explicitly to register memory agents, emit shared-context events, health-check agent pools, or drive dispatcher workflows (`sequential`, `parallel`, `conditional`).

## Capabilities
- Multi-agent sequencing (Go/Rust/Python memory agents) with shared state store backing.
- Conditional dispatchers that evaluate agent outputs/events to choose downstream skills.
- Shared-memory plus message-passing protocols (Redis/ETCD + event bus) and telemetry hooks.
- Human-gate integration, retries/fallbacks, and structured JSON output for automation.

## Invocation patterns
Examples:

```bash
/ai-agent-orchestration orchestrate sequential --agents=go-memory,rust-memory,python-memory --target=production --workflow=memory-sync
/ai-agent-orchestration orchestrate conditional --workflow=dispatcher --decision-context=shared-context://memory-store --timeout=1800
/ai-agent-orchestration register-agent go-memory --language=go --capabilities=memory-enrichment --context-store=redis://memory-store --task-queue=memory-go
/ai-agent-orchestration monitor-agents --status=detailed --metrics=queue-depth,latency
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `targetResource` | Resource the workflow should focus on (tenant, cluster, skill scope). | `ProductionHub` |
| `environment` | Environment tag (dev/staging/prod). | `staging` |
| `priority` | Workflow priority for human gate or resource allocation. | `high` |
| `timeframe` | Lookback window for telemetry or replay decisions. | `30d` |
| `region` | Cloud region to limit discovery/skill run. | `us-east-1` |

## Output contract
Every orchestration command returns structured JSON:

```json
{
  "workflowId": "uuid",
  "status": "started|running|completed|failed",
  "startedAt": "ISO8601 timestamp",
  "result": {
    "agents": [
      {
        "name": "go-memory",
        "status": "success",
        "output": "schema:/shared-context/discovery"
      }
    ],
    "skillsTriggered": [
      {
        "name": "compliance-check",
        "reason": "agent output flagged config drift",
        "decision": "approve|human_gate|retry",
        "humanGate": {
          "required": true,
          "impact": "Any prod change",
          "reversible": "No"
        }
      }
    ]
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
- Agents: Go → Rust → Python.
- Coordination: Each agent writes enriched context to `shared-context://memory-store`.
- Dispatcher: On completion, signal `agent-completed` event to trigger next skill.
- Use `/ai-agent-orchestration orchestrate sequential --agents=go-memory,rust-memory,python-memory --workflow=memory-sync --communication=shared-context`.

### Conditional dispatcher
- Input: Agent event payloads with `riskScore`, `anomalyType`, `tenant`.
- Decision matrix example:
1. `riskScore >= 80`: trigger `incident-triage-runbook`.
2. `anomalyType == "cost-spike"`: trigger `cost-optimization`.
3. `complianceConcern == true`: trigger `compliance-check`.
- Implementation uses `/ai-agent-orchestration orchestrate conditional --workflow=dispatcher --workflow-spec=dispatcher.yaml --context=redis://memory-store`.

### Parallel resiliency checks
- Run `security-analysis` and `observability-stack` simultaneously after memory agents produce new context.
- On failures, fallback to lightweight agents (`security-analysis-lite`).
- Command: `/ai-agent-orchestration orchestrate parallel --agents=security-analysis,observability-stack --fail-fast=false --timeout=1200`.

## Memory agent integration
- Use Redis/ETCD as the shared memory store; all agents include `shared-context` wiring (schema: `agentName.outputKey`).
- Event bus topics: `agent-completed`, `agent-failed`, `insight-ready`, `skill-request`.
- Agents publish metadata: `tenant`, `region`, `riskScore`, `costImpact`.
- Dispatcher subscribes to events, merges context, and selects skill(s) using template rules above.
- Sample event payload:
```json
{
  "agent": "python-memory",
  "tenant": "acme",
  "region": "us-east-1",
  "riskScore": 72,
  "insights": ["policy_gap", "cost_spike"],
  "timestamp": "2026-03-14T22:00:00Z"
}
```

## Communication protocols
- **Shared memory (primary)**: Redis or ETCD key `shared-context://<tenant>/<agent>/<artifact>`.
- **Message passing (secondary)**: Kafka- or NATS-style event bus with topics described above.
- **Fallback**: If shared memory is unavailable, agents send zipped payloads via `artifact-store://` and dispatcher polls every 30 seconds.
- **Health**: `/ai-agent-orchestration monitor-agents --status=detailed` collects `queueDepth`, `latency`, `failedJobs`, `resourceUsage`.

## Observability & telemetry
- Emit metrics for: agent execution time (p95/p99), dispatcher decision branching, skill success rates, context store latency.
- Log structured events with correlation IDs (e.g., `orchestrationId`, `agentRunId`, `decisionId`).
- Dashboards: integrate `/ai-agent-orchestration metrics --format=prometheus` into Grafana panels.
- Alerting: fire on >3 consecutive dispatcher failures or shared memory latency > 500ms.

## Failure handling and retries
- Use retry policy: 3 attempts with exponential backoff per agent or skill.
- Fallback agents: map each primary skill to a lighter variant (e.g., `security-analysis-lite`, `cost-optimization-smoke`).
- On repeated failure (>=2 retries) escalate: log failure, persist context, and trigger human gate.
- Always preserve intermediate state; do not delete shared-context keys after failures (for audit).

## Human gates
- Require explicit human confirmation any time:
1. Dispatcher recommends production changes (riskScore ≥ 90 or >20 tenants affected).
2. `compliance-check` or `security-analysis` plan high-impact remediations.
3. `cost-optimization` proposes spend >$5,000/month increase.
- Confirmation template:

```
⚠️  HUMAN GATE: [description]
    Impact: [what changes]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Run `/ai-agent-orchestration orchestrate sequential --dry-run` to validate dispatcher wiring.
- Use `scripts/validate-memory-agents.sh` (referenced in `infrastructure/ai-inference/`) to simulate event payloads and ensure routing logic.
- Include unit tests for dispatcher rules located under `backend/orchestration/dispatcher_rules/`.
- Nightly smoke tests: trigger `/ai-agent-orchestration orchestrate parallel --agents=compliance-check,cost-optimization --nightly=true`.

## References
- Agent config directory: `backend/agents/`.
- Dispatcher definitions: `backend/orchestration/dispatcher/`.
- Deployment manifests: `infrastructure/ai-inference/shared/`.
- Monitoring dashboards: `monitoring/agents/`.

## Related skills
- `/workflow-management`: monitor workflows and gather execution history.
- `/compliance-security-scanner`: verify recommendations before approval.
- `/incident-triage-runbook`: execute remediation when dispatcher raises critical alerts.

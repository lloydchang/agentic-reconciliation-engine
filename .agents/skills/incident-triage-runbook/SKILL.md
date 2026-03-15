---
name: incident-triage-runbook
description: >
  Detect, classify, and resolve incidents while keeping humans in the loop for high-risk cases.
  Use this skill for any alert (P1–P4), outage, degradation, or incident requiring a runbook, report,
  or automated remediation.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Incident Triage & Runbook Execution — World-class Response Playbook

Automates detection, AI-powered classification, intelligent remediation selection, and rapid post-mortem delivery so every incident is stabilized quickly with a clear audit trail.

## When to invoke
- PagerDuty/Prometheus/DataDog/Azure Monitor/New Relic alerts tagged P1–P4.
- Manual requests for degraded services, recurring outages, or emergent CVEs.
- Human-in-the-loop reviews, post-mortem drafts, or follow-up action tracking for incidents.
- Dispatcher events (`incident-ready`, `risk-bump`) from memory agents that flag high-risk states.

## Capabilities
- **AI Incident Classification** resolves severity (P1–P4) by combining telemetry, change history, SLA context, and confidence scoring.
- **Intelligent Runbook Selection** uses semantic similarity, historical success rates, and risk exposure to pick the optimal remediation plan.
- **Smart Post-Mortem Generation** produces timelines, root causes, SLA impact, action items, and follow-ups automatically.
- **Human-aware Automation** pauses for gates when novelty, low confidence, or high blast radius is detected, with transparent communication.
- **Audit-Ready Telemetry Capture** records every detection, remediation, rollback, and validation step for compliance and learning.

## Invocation patterns

```bash
/incident-triage-runbook respond --incident-id=INC-2026-0050 --source=pagerduty
/incident-triage-runbook classify --alert=HighErrorRate --tenant=tenant-42 --region=us-east-1
/incident-triage-runbook runbook --name=high-memory-aks-node --auto-approve=true
/incident-triage-runbook postmortem --incident-id=INC-2026-0048 --format=json
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `incidentId` | Unique incident or alert identifier. | `INC-2026-0050` |
| `severity` | P1–P4 derived from AI classification. | `P2` |
| `tenant` | Tenant, workspace, or service scope. | `tenant-42` |
| `region` | Cloud region or cluster context. | `us-east-1` |
| `runbook` | Specific remediation guide or template. | `high-memory-aks-node` |
| `autoApprove` | Run low-risk remediation without a gate. | `true` |

## Output contract

```json
{
  "incidentId": "INC-2026-0050",
  "severity": "P1",
  "classificationConfidence": 0.94,
  "runbookApplied": "high-memory-aks-node",
  "steps": [
    { "id": 1, "name": "diagnose-node", "status": "success" },
    { "id": 2, "name": "cordon-node", "status": "success" }
  ],
  "status": "resolved",
  "mttrMinutes": 18,
  "postmortemUrl": "https://reports/incidents/INC-2026-0050",
  "decisionContext": "redis://memory-store/incident/INC-2026-0050",
  "humanGate": {
    "required": true,
    "impact": "Production node drainage",
    "reversible": "Yes"
  }
}
```

## World-class workflow templates

### AI incident classification
1. Ingest alert payload (PagerDuty, Azure Monitor, Prometheus, DataDog).
2. AI classifier scores severity, scope, tenant impact, and automation readiness.
3. Dispatcher selects the best-fit runbook or escalates to human gate if novelty or low confidence exists.
4. Runbook runs remediation steps with rollback safeguards while emitting `insight-ready` events.
5. Post-mortem draft is generated with timeline, root cause, SLA impact, and action items.

### Intelligent runbook selection
- Match incidents to runbooks via trigger patterns, dependency fingerprints, and historical outcomes.
- Factor execution risk, blast radius, and rollback cost to decide whether a human gate is needed.
- Example runbooks: node memory pressure, failed rollout, certificate rotation, database connection pool.

### Smart post-mortem generation
- Aggregate timelines from alerts, runbook steps, and automation actions.
- Calculate root cause using causal graphs (config changes, dependencies, telemetry drift).
- Produce structured post-mortem with severity, impact, mitigation, and follow-up owners stored at `reports/postmortems/{incidentId}.json`.

## AI intelligence highlights
- **AI Incident Classification** balances telemetry, change history, and SLA context to assign severity and guardrail decisions.
- **Smart Post-Mortem Generation** auto-populates timelines, impact statements, mitigation steps, and responsible owners for rapid review.
- **Intelligent Runbook Selection** reasons over semantic similarity, success rates, risk levels, and rollback complexity when choosing remediation.

## Memory agent & dispatcher integration
- Pull context from `shared-context://memory-store/<tenant>/incident` whenever a memory agent flags a regression or anomaly.
- Emit `incident-resolved`, `postmortem-ready`, and `risk-adjustment` events so compliance, cost, deployment, and orchestrator skills stay synchronized.
- Update Redis metadata (`riskScore`, `confidence`, `stepsCompleted`) so the dispatcher can decide whether to rerun the workflow or escalate.
- Fallback: if the message bus is unavailable, write JSON artifacts to `artifact-store://incidents/{incidentId}.json` and let downstream skills pick them up.

## Observability & telemetry
- Metrics: incidents classified per minute, runbook success rate, MTTR p95, time to human gate.
- Logs: structured `log.event` (classification/runbook step/postmortem) with `decisionId`, `orchestrationId`, and `tenant` tags.
- Dashboards: expose `/incident-triage-runbook metrics --format=prometheus` for on-call visibility.
- Alerts: fire when classification confidence < 0.65, when MTTR > 60m for a P1, or when human gate is pending > 15m.

## Failure handling & retries
- Retry classification or runbook steps up to 2 times with exponential backoff (30s → 120s).
- On runbook failure, execute rollback steps (when defined) and escalate to human gate along with contextual logs.
- Persist `shared-context://memory-store/incident/{incidentId}` for downstream analysis and do not delete logs until downstream skills ack.

## Human gates
- Required when:
  1. Severity is P1 or automation confidence < 70%.
  2. Runbook impacts production-facing services (draining nodes, rewriting firewall policies, etc.).
  3. Dispatcher requests escalation after >2 failed steps.
- Confirmation template (matches orchestrator):

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/incident-triage-runbook respond --incident-id=INC-DRY-RUN --dry-run=true` to validate runbook flow.
- Unit tests: focus on classification models and runbook selection heuristics under `backend/incidents/`.
- Integration: `scripts/validate-incident-flow.sh` simulates alerts from all sources and verifies postmortem payloads.
- Regression: nightly `scripts/nightly-incident-smoke.sh` ensures human gate logic, telemetry, and event emission remain stable.

## References
- Alert ingestion helpers: `api/alerts/**`.
- Runbooks: `runbooks/*.yaml`.
- Postmortem templates: `docs/RUNBOOKS.md`, `docs/SECURITY-INCIDENT-RESPONSE.md`.

## Related skills
- `/ai-agent-orchestration`: routes events and coordinates multi-skill remediation.
- `/compliance-security-scanner`: contextualizes compliance impact of incident-driven changes.
- `/workflow-management`: monitors workflows spun up by incidents and ensures completion.

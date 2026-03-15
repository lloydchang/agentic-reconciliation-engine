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

Automates detection, AI classification, intelligent runbook selection, remediation, and rapid post-mortem delivery. Use this skill to stabilize affected tenants fast while preserving traceability for compliance and learning loops.

## When to invoke
- PagerDuty/Prometheus/DataDog/Azure Monitor alerts with severity P1–P4.
- Manual requests to investigate degraded services, recurring incidents, or new CVEs.
- Post-mortem generation, incident reviews, or human-in-the-loop escalation for observed anomalies.
- `ai-agent-orchestration` dispatchers route `incident-ready` or `risk-bump` events here when memory agents detect high-risk states.

## Capabilities
- AI incident classification (P1/P2/P3/P4) that evaluates impact, scope, and automation confidence.
- Intelligent runbook selection that matches incidents to the best-matched remediation plans.
- Smart post-mortem generation with timelines, root causes, SLA impact, and action items.
- Human-gated escalation for novel/unresolved incidents with risk-aware communication.
- Telemetry capture across detection, remediation, and verification for audit readiness.

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
| `incidentId` | Unique ID of the alert/incident. | `INC-2026-0050` |
| `severity` | P1–P4 derived from AI classification. | `P2` |
| `tenant` | Tenant or workspace identifier. | `tenant-42` |
| `region` | Cloud region scope. | `us-east-1` |
| `runbook` | Runbook name or trigger pattern. | `high-memory-aks-node` |
| `autoApprove` | Whether low-risk steps run without human gate. | `true` |

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

### AI incident classification →
1. Ingest alert payload (PagerDuty/Azure/Prometheus/DataDog).  
2. AI classifier scores severity (P1–P4) and identifies impacted tenants/services.  
3. Dispatcher chooses runbook or escalates to human gate if novelty/high uncertainty.  
4. Runbook executes steps (with rollbacks if necessary) and streams `insight-ready` events.  
5. Post-mortem draft produced automatically with timeline, root cause, impact, and action items.

### Intelligent runbook selection
- Match alert to runbooks via `trigger_pattern`, telemetry signatures, and past resolutions.  
- Evaluate risk and automation readiness to determine whether human gate is required.  
- Example runbooks: node memory pressure, failed rollout, certificate expiry, database connection pool.

### Smart post-mortem generation
- Collect timeline entries across detection/resolution (API events, runbook steps, alerts).  
- Analyze root cause using causal graph (dependencies, config changes), severity, SLA impact, and human actions.  
- Produce structured report and publish to `reports/postmortems/{incidentId}.json`.

## AI intelligence highlights
- **AI Incident Classification**: Multi-model ensemble that balances telemetry, change history, and business-criticality to determine severity and guardrail exemptions.
- **Smart Post-Mortem Generation**: Auto-populates timelines, impact statements, mitigation steps, and action owners for rapid review.
- **Intelligent Runbook Selection**: Uses semantic similarity and past success rates to pick the most effective remediation plan while factoring rollback complexity.

## Memory agent integration
- Subscribe to `agent-completed` and `insight-ready` events from memory agents; read context via `shared-context://memory-store/<tenant>/incident`.
- Emit `incident-resolved`, `postmortem-ready`, and `risk-adjustment` events so other skills (compliance, cost, deployment validation) update context.
- Update Redis metadata (`riskScore`, `confidence`, `stepsCompleted`) so dispatchers know whether to escalate or rerun workflows.

## Communication protocol
- Primary: HTTP/webhook ingestion of alerts; internal commands issued via `/incident-triage-runbook`.
- Secondary: Event bus topics `incident-classified`, `runbook-step`, `incident-triaged`, `postmortem-finished`.
- Fallback: If event bus is unavailable, write JSON artifacts to `artifact-store://incidents/{incidentId}.json` for other skills to pick up.

## Observability & telemetry
- Metrics: incidents classified per minute, runbook success rate, time to human gate, MTTR p95.
- Logs: structured `log.event` (classification/runbook step/postmortem) with `decisionId`, `orchestrationId`, `tenant`.
- Dashboards: integrate `/incident-triage-runbook metrics --format=prometheus` for on-call visibility.
- Alerts: trigger when classification confidence < 0.65 or when MTTR > 60min for P1 events.

## Failure handling & retries
- Retry classification/runbook execution up to 2 times with exponential backoff (30s → 120s).  
- On runbook failure, execute rollback steps if defined and escalate to human gate.  
- Persist context (`shared-context://memory-store/incident/{incidentId}`) for post-failure analysis; do not delete logs to maintain audit trail.

## Human gates
- Required whenever:
 1. Severity is P1 or automation confidence < 70%.
 2. Runbook impacts production-facing services (e.g., draining nodes, firewall changes).
 3. Dispatcher requests escalation after >2 failed steps.
- Confirmation template:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/incident-triage-runbook respond --incident-id=INC-DRY-RUN --dry-run=true`.
- Unit tests: focus on classification models and runbook selection heuristics under `backend/incidents/`.
- Integration: `scripts/validate-incident-flow.sh` simulates alerts from all sources and verifies event flow plus postmortem payload.
- Regression: nightly `scripts/nightly-incident-smoke.sh` ensures human gate logic and telemetry events keep working.

## References
- Alert ingestion helpers: `api/alerts/**`.
- Runbooks: `runbooks/*.yaml`.
- Postmortem templates: `docs/RUNBOOKS.md`, `docs/SECURITY-INCIDENT-RESPONSE.md`.

## Related skills
- `/ai-agent-orchestration`: route events and orchestrate multi-skill remediation.
- `/compliance-security-scanner`: contextualize compliance impact of incidents.
- `/workflow-management`: monitor workflows triggered by incidents.

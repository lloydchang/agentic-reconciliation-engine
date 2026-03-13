---
name: incident-triage-runbook
description: >
  Use this skill to detect, triage, and execute runbooks
  incidents. Triggers: any incident, alert, P1, P2, P3, P4, page, outage, cluster error,
  503, 5xx, service degraded, degradation, anomaly, or request to investigate; execute a runbook step-by-step; create a post-mortem;
  automate top incident response patterns; or reduce mean-time-to-resolution
  (MTTR) for recurring issues.
tools:
  - bash
  - computer
---

# Incident Triage & Runbook Execution Skill

Structured incident lifecycle management: detect → classify → execute runbook
→ resolve → post-mortem. Automates the top N recurring incidents using
codified runbooks while maintaining a human-in-the-loop for novel or P1 events.

---
name: incident-triage-runbook
description: >
  Use this skill to detect, triage, and execute runbooks
  incidents. Triggers: any incident, alert, P1, P2, P3, P4, page, outage, cluster error,
  503, 5xx, service degraded, degradation, anomaly, or request to investigate; execute a runbook step-by-step; create a post-mortem;
  automate top incident response patterns; or reduce mean-time-to-resolution
  (MTTR) for recurring issues.
tools:
  - bash
  - computer
---

# Incident Triage & Runbook Execution Skill

Structured incident lifecycle management: detect → classify → execute runbook
→ resolve → post-mortem. Automates the top N recurring incidents using
codified runbooks while maintaining a human-in-the-loop for novel or P1 events.

## Enhanced Incident Response Automation

### Automated Detection & Response
Automate detection, triage, and response workflows for infrastructure incidents.

**Trigger:** Use when monitoring systems report alerts.

**Workflow:**
1. Receive alert from monitoring systems
2. Correlate logs and telemetry data
3. Determine root cause category:
   - infrastructure failure
   - deployment error
   - configuration drift
4. Execute remediation workflow automatically
5. Generate incident report with root cause and SLA impact

### Integration with Monitoring Systems
- **PagerDuty**: Webhook integration for incident alerts
- **DataDog**: Event correlation and metric analysis
- **Azure Monitor**: Cloud resource health monitoring
- **Prometheus**: Alertmanager webhook processing

---

## Incident Severity Model

| Severity | Definition                                    | Response SLA | Auto-runbook |
|----------|-----------------------------------------------|--------------|--------------|
| P1       | Production down, data loss risk               | 15 min       | Partial      |
| P2       | Major degradation, SLA at risk                | 30 min       | Full         |
| P3       | Minor degradation, workaround available       | 2 hr         | Full         |
| P4       | Cosmetic / low impact                         | 8 hr         | Full         |

---

## Triage Workflow

### Step 1 — Detect & Ingest
Sources (configure via env vars):
- PagerDuty webhook → `PD_WEBHOOK_SECRET`
- Azure Monitor alerts → `AZURE_ALERT_WEBHOOK`
- Prometheus Alertmanager → `ALERTMANAGER_URL`
- DataDog events → `DD_API_KEY`

Parse incoming alert payload:
```json
{
  "source": "pagerduty|azure|prometheus|datadog",
  "alert_name": "string",
  "severity": "P1-P4",
  "resource": "string",
  "region": "string",
  "tenant_id": "string",
  "timestamp": "ISO8601",
  "raw_payload": {}
}
```

### Step 2 — Classify
Match `alert_name` against runbook registry:
```bash
grep -r "trigger_pattern:" ./runbooks/ | grep "$ALERT_NAME"
```
If match found → execute runbook automatically (P2-P4) or with approval (P1).
If no match → escalate to on-call with full context.

### Step 3 — Execute Runbook

Each runbook follows this structure:
```yaml
name: high-memory-aks-node
trigger_pattern: "KubeletTooManyPods|NodeMemoryPressure"
severity: P3
steps:
  - id: 1
    action: diagnose
    cmd: "kubectl top nodes && kubectl describe node $NODE"
    auto: true
  - id: 2
    action: cordon
    cmd: "kubectl cordon $NODE"
    auto: true
    rollback: "kubectl uncordon $NODE"
  - id: 3
    action: drain
    cmd: "kubectl drain $NODE --ignore-daemonsets --delete-emptydir-data"
    auto: false   # requires approval for P1/P2
  - id: 4
    action: validate
    cmd: "kubectl get pods -A | grep -v Running | grep -v Completed"
    auto: true
```

Execute each step, capturing stdout/stderr. On step failure:
1. Attempt rollback if defined
2. Halt and escalate with full context

### Step 4 — Communicate
Post structured updates to the incident channel (Slack/Teams):
```
🔴 [P2 INCIDENT] High memory on AKS node pool – tenant-42
Time: 14:32 UTC | Owner: @on-call-eng
Status: Executing runbook step 2/4 — cordoning node
ETA to resolution: ~15 min
```

Update every 10 minutes until resolved.

### Step 5 — Resolve & Post-Mortem
On resolution:
- Close the incident ticket
- Record timeline (detection → resolution)
- Auto-generate post-mortem draft:
  - **What happened** (timeline)
  - **Impact** (affected tenants, duration, SLA status)
  - **Root cause** (from runbook diagnosis output)
  - **Action items** (with owner and due date fields)
  - **Runbook gaps identified**

---

## Top Automatable Incident Runbooks

Implement these as the initial library:

1. **AKS node memory/CPU pressure** — cordon, drain, replace
2. **Pod CrashLoopBackOff** — log capture, restart, alert if persists
3. **Certificate expiry** — auto-renew via cert-manager or Key Vault
4. **Database connection pool exhaustion** — scale pool, kill idle connections
5. **Disk I/O saturation** — identify top consumers, trigger volume expansion
6. **Deployment rollback** — detect failed rollout, auto-rollback to last good
7. **DNS resolution failure** — flush caches, validate CoreDNS config
8. **High 5xx error rate** — identify upstream, circuit-break, alert
9. **Blob storage quota exceeded** — archive old objects, notify tenant
10. **VPN / ExpressRoute flap** — failover to secondary, open carrier ticket

---

## Examples

- "Triage the PagerDuty alert that just fired for tenant-7 AKS cluster"
- "Run the certificate renewal runbook for the payments namespace"
- "Show me all P1/P2 incidents in the last 30 days and their MTTR"
- "Generate a post-mortem for last night's database outage"
- "Which runbook gaps caused the most manual interventions this quarter?"

---

## Output Format

```json
{
  "incident_id": "INC-1234",
  "severity": "P1|P2|P3|P4",
  "runbook_applied": "string",
  "runbook": "high-memory-aks-node",
  "steps_completed": 3,
  "steps_total": 4,
  "status": "resolved|in_progress|escalated",
  "mttr_minutes": 18,
  "postmortem_url": "string"
}
```

---
name: orchestrator
description: >
  Use this skill as the top-level orchestrator for the Cloud AI agent.
  Coordinates all other skills to handle complex multi-step
  tasks. Triggers: any high-level or multi-domain request such as "onboard a
  new tenant end-to-end", "respond to a P1 incident", "prepare the quarterly
  business review", "run a full health check", "migrate this
  environment", or any task requiring more than one skill in sequence.
tools:
  - bash
  - computer
---

# Orchestrator Skill

The master coordination layer for the Cloud AI agent. Decomposes
high-level operator requests into ordered skill invocations, manages state
across skill boundaries, handles failures with retry/rollback logic, and
surfaces a unified result.

---

## Skill Registry

| ID  | Skill name                    | Domain                        |
|-----|-------------------------------|-------------------------------|
| S01 | terraform-provisioning        | Infrastructure lifecycle      |
| S02 | cicd-pipeline-monitor         | Deployment pipelines          |
| S03 | incident-triage-runbook       | Incident response             |
| S04 | tenant-lifecycle-manager      | SaaS tenant operations        |
| S05 | compliance-security-scanner   | Security & compliance         |
| S06 | sla-monitoring-alerting       | Reliability & SLOs            |
| S07 | deployment-validation         | Deployment quality            |
| S08 | kpi-report-generator          | Metrics & reporting           |
| S09 | runbook-documentation-gen     | Documentation                 |
| S10 | stakeholder-comms-drafter     | Communications                |
| S11 | kubernetes-cluster-manager    | Kubernetes operations         |
| S12 | cost-optimisation             | FinOps                        |
| S13 | secrets-certificate-manager   | Secrets & PKI                 |
| S14 | workload-migration            | Migrations                    |
| S15 | policy-as-code                | Governance                    |
| S16 | capacity-planning             | Forecasting                   |
| S17 | observability-stack           | Monitoring & logging          |
| S19 | multi-cloud-networking        | VNet / DNS / Firewall         |
| S20 | database-operations           | DB lifecycle & HA             |
| S21 | disaster-recovery             | Failover & DR drills          |
| S22 | gitops-workflow               | ArgoCD / Flux                 |
| S23 | service-mesh                  | Istio / mTLS / traffic        |
| S24 | container-registry            | Image lifecycle & signing     |
| S25 | developer-self-service        | IDP / Backstage / golden path |
| S26 | audit-siem                    | Audit logs / Sentinel         |
| S27 | change-management             | CR governance / CAB           |
| S28 | chaos-load-testing            | Resilience validation         |

---

## Composite Workflows

### WORKFLOW-01: Full Tenant Onboarding

```
Step 1  S16 capacity-planning           Check headroom before provisioning
Step 2  S15 policy-as-code              Validate tenant config vs policies
Step 3  S01 terraform-provisioning      Provision infrastructure
Step 4  S11 kubernetes-cluster-manager  Configure namespace + RBAC
Step 5  S13 secrets-certificate-manager Create secrets, TLS cert
Step 6  S17 observability-stack         Instrument tenant namespace
Step 7  S04 tenant-lifecycle-manager    Register in tenant registry
Step 8  S07 deployment-validation       Smoke test the new environment [GATE]
Step 9  S06 sla-monitoring-alerting     Activate SLO monitoring
Step 10 S10 stakeholder-comms-drafter   Send welcome + ops confirmation
```

Human gates: Step 1 (capacity approval), Step 8 (smoke test go/no-go).

---

### WORKFLOW-02: P1 Incident Response

```
Step 1  S03 incident-triage-runbook     Classify alert, find runbook
Step 2  S17 observability-stack         Pull metrics/logs for context
Step 3  S03 incident-triage-runbook     Execute runbook steps
Step 4  S10 stakeholder-comms-drafter   Send first notification (< 5 min)
[Loop every 15 min] S10               Update comms until resolved
Step 5  S07 deployment-validation       Recent deploy culprit? rollback
Step 6  S03 incident-triage-runbook     Confirm resolution
Step 7  S06 sla-monitoring-alerting     Assess SLA impact
Step 8  S10 stakeholder-comms-drafter   Send resolution notice
Step 9  S09 runbook-documentation-gen   Draft post-mortem
```

---

### WORKFLOW-03: Weekly Compliance Scan

Trigger: Cron Monday 06:00 UTC

```
Step 1  S05 compliance-security-scanner IaC + container + IAM scan
Step 2  S15 policy-as-code              Gatekeeper violation audit
Step 3  S13 secrets-certificate-manager Expiry and rotation audit
Step 4  S06 sla-monitoring-alerting     SLA compliance status
Step 5  S08 kpi-report-generator        Compile into compliance report
Step 6  S10 stakeholder-comms-drafter   Email to security team
```

---

### WORKFLOW-04: Monthly Executive Report

Trigger: First Monday of each month

```
Step 1  S08 kpi-report-generator        Collect DORA + reliability metrics
Step 2  S06 sla-monitoring-alerting     SLA breach log + compliance
Step 3  S12 cost-optimisation           Cloud spend summary + savings
Step 4  S16 capacity-planning           Next-quarter forecast
Step 5  S05 compliance-security-scanner Security posture score
Step 6  S08 kpi-report-generator        Build PPTX/PDF report
Step 7  S10 stakeholder-comms-drafter   Email to leadership [GATE]
```

---

### WORKFLOW-05: Pre-Release Readiness Check

Trigger: "Is the platform ready for the [version] release?"

```
Step 1  S05 compliance-security-scanner Scan all new container images
Step 2  S07 deployment-validation       Pre-flight checks across all envs
Step 3  S06 sla-monitoring-alerting     Check error budget remaining
Step 4  S16 capacity-planning           Confirm headroom for release traffic
Step 5  S13 secrets-certificate-manager Verify all certs valid 30+ days
Step 6  S15 policy-as-code              No open policy violations
Step 7  S17 observability-stack         Confirm dashboards + alerts live
```

Output: GO / NO-GO with reasons for any blockers.

---

### WORKFLOW-06: Quarterly Business Review Prep

Trigger: "Prepare the Q[N] QBR for Cloud AI"

```
Step 1  S08 kpi-report-generator        90-day DORA + reliability trends
Step 2  S12 cost-optimisation           Quarter spend + savings delivered
Step 3  S16 capacity-planning           Next quarter resource + cost forecast
Step 4  S06 sla-monitoring-alerting     SLA compliance + breach summary
Step 5  S05 compliance-security-scanner Quarter security improvements
Step 6  S09 runbook-documentation-gen   Roadmap milestone status doc
Step 7  S08 kpi-report-generator        Assemble full QBR PPTX deck
Step 8  S10 stakeholder-comms-drafter   Draft QBR email invite + agenda
```

---

### WORKFLOW-07: New Cluster Provisioning

Trigger: "Provision a new [env] cluster in [region]"

```
Step 1  S27 change-management           Raise and score change request [GATE]
Step 2  S16 capacity-planning           Confirm quota + cost headroom
Step 3  S19 multi-cloud-networking      Provision VNet / VPC / spoke / peering / DNS
Step 4  S01 terraform-provisioning      Provision AKS / EKS / GKE cluster
Step 5  S11 kubernetes-cluster-manager  Harden node pools, RBAC, network policy
Step 6  S13 secrets-certificate-manager Bootstrap cluster secrets + cert-manager
Step 7  S15 policy-as-code              Deploy Gatekeeper + OPA policy bundle
Step 8  S22 gitops-workflow             Bootstrap Argo CD / Flux on cluster
Step 9  S23 service-mesh                Install Istio, enforce mTLS
Step 10 S24 container-registry          Grant AcrPull to cluster identity
Step 11 S17 observability-stack         Deploy Prometheus / Loki / Grafana stack
Step 12 S06 sla-monitoring-alerting     Activate SLO alert rules
Step 13 S26 audit-siem                  Enable K8s audit log → Sentinel
Step 14 S07 deployment-validation       Smoke test cluster readiness [GATE]
Step 15 S09 runbook-documentation-gen   Auto-generate cluster runbook
Step 16 S10 stakeholder-comms-drafter   Notify teams cluster is ready
```

Human gates: Step 1 (change approval), Step 14 (GO/NO-GO).

---

### WORKFLOW-08: Security Incident Response

Trigger: Sentinel alert HIGH/CRITICAL, security scanner critical finding, or "investigate security event"

```
Step 1  S26 audit-siem                  Pull full audit trail for the event
Step 2  S03 incident-triage-runbook     Classify severity, find security runbook
Step 3  S05 compliance-security-scanner Scan affected resources for additional IOCs
Step 4  S10 stakeholder-comms-drafter   Notify security team + management [GATE]
Step 5  S15 policy-as-code              Apply emergency isolation policy if needed
Step 6  S13 secrets-certificate-manager Rotate any potentially compromised secrets
Step 7  S26 audit-siem                  Continuous audit tail until resolved
Step 8  S03 incident-triage-runbook     Confirm containment, close incident
Step 9  S09 runbook-documentation-gen   Draft security incident post-mortem
Step 10 S05 compliance-security-scanner Full re-scan to confirm clean posture
```

Human gates: Step 4 (confirm scope before action), Step 5 (isolation approval).

---

### WORKFLOW-09: Disaster Recovery Drill

Trigger: "Run DR drill for [tier/tenant]" or scheduled quarterly

```
Step 1  S27 change-management           Raise change request for drill window [GATE]
Step 2  S10 stakeholder-comms-drafter   Pre-drill notice to affected teams
Step 3  S21 disaster-recovery           Execute backup integrity validation
Step 4  S20 database-operations         Verify geo-replica lag within RPO target
Step 5  S21 disaster-recovery           Execute full failover to DR region [GATE]
Step 6  S17 observability-stack         Confirm observability in DR region
Step 7  S06 sla-monitoring-alerting     Measure RTO — compare to target
Step 8  S21 disaster-recovery           Execute failback to primary region
Step 9  S06 sla-monitoring-alerting     Confirm SLOs restored after failback
Step 10 S08 kpi-report-generator        Record RTO/RPO actuals vs targets
Step 11 S09 runbook-documentation-gen   Update DR runbook with drill findings
Step 12 S10 stakeholder-comms-drafter   Send drill results to leadership
```

Human gates: Step 1 (change approval), Step 5 (confirm initiate failover).

---

### WORKFLOW-10: New Team Platform Onboarding

Trigger: "Onboard the [team name] engineering team to the platform"

```
Step 1  S25 developer-self-service      Create team in Backstage catalog
Step 2  S15 policy-as-code              Validate team config vs RBAC policies
Step 3  S01 terraform-provisioning      Provision dev + staging namespaces
Step 4  S11 kubernetes-cluster-manager  Configure namespace RBAC for team
Step 5  S22 gitops-workflow             Create ArgoCD project + ApplicationSet
Step 6  S13 secrets-certificate-manager Bootstrap team secrets namespace
Step 7  S19 multi-cloud-networking      Create private endpoints if required
Step 8  S17 observability-stack         Provision team dashboards in Grafana
Step 9  S24 container-registry          Grant team AcrPush to dev registry
Step 10 S26 audit-siem                  Enable audit logging for team namespace
Step 11 S25 developer-self-service      Generate and deliver onboarding checklist
Step 12 S08 kpi-report-generator        Add team to platform adoption metrics
Step 13 S10 stakeholder-comms-drafter   Send welcome email + portal link
```

Human gates: None for standard teams. Step 3 requires approval for enterprise-scale resource requests.

---

## Scheduling

```yaml
schedules:
  - workflow: compliance-scan       # WORKFLOW-03
    cron: "0 6 * * 1"               # Every Monday 06:00 UTC
  - workflow: cert-expiry-check     # S13 standalone
    cron: "0 9 * * *"               # Daily 09:00 UTC
  - workflow: capacity-check        # S16 standalone
    cron: "0 10 * * 1"              # Every Monday 10:00 UTC
  - workflow: monthly-exec-report   # WORKFLOW-04
    cron: "0 7 1 * *"               # 1st of each month, human gate before send
  - workflow: sla-error-budget      # S06 standalone
    cron: "*/30 * * * *"            # Every 30 minutes
  - workflow: dr-drill              # WORKFLOW-09
    cron: "0 10 15 */3 *"           # Quarterly (15th of Jan/Apr/Jul/Oct)
  - workflow: chaos-experiment      # S28 standalone
    cron: "0 14 * * 3"              # Every Wednesday 14:00 UTC (staging only)
  - workflow: audit-siem-review     # S26 standalone
    cron: "0 8 * * 1"               # Every Monday 08:00 UTC
  - workflow: change-calendar       # S27 standalone
    cron: "0 7 * * 5"               # Every Friday 07:00 UTC (next-week preview)
```

---

## Escalation Policy

| Workflow                   | Escalate to                 | Channel           |
|----------------------------|-----------------------------|-------------------|
| Tenant onboarding          | on-call                     | PagerDuty P3      |
| P1 incident                | lead + CTO                  | PagerDuty P1      |
| Security incident          | CISO + lead                 | PagerDuty P1      |
| Compliance scan            | Compliance                  | Slack + Teams     |
| Executive report           | manager                     | Slack + Teams     |
| Migration failure          | lead                        | PagerDuty P2      |
| DR drill failure           | lead + architects           | PagerDuty P2      |
| Change freeze violation    | manager + CISO              | Slack + Teams     |
| Chaos experiment SLO abort | on-call                     | PagerDuty P3      |
| Cluster provisioning fail  | lead                        | PagerDuty P2      |

---

## Run State Schema

```json
{
  "run_id": "RUN-20250601-0142",
  "workflow": "WORKFLOW-01",
  "status": "success|running|failed|pending_approval",
  "started_at": "ISO8601",
  "completed_at": "ISO8601",
  "steps_completed": 0,
  "steps_total": 0,
  "human_gates": [],
  "errors": []
}
```

---

## Examples

- "Onboard a new enterprise tenant Acme Corp in East US — full workflow"
- "Run a complete health check across all environments"
- "We have a P1 — take over incident response for the AKS/EKS/GKE degradation alert"
- "Is the infrastructure ready to release v2.4 to production?"
- "Prepare everything needed for the Q3 QBR deck"
- "Run the weekly compliance scan and email the security team"
- "Provision a new staging cluster in West Europe"
- "Sentinel fired a critical alert on the payments namespace — investigate"
- "Run the quarterly DR drill for all enterprise tenants"
- "Onboard the new checkout engineering team to the system"

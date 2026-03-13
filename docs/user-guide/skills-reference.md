# Skills Reference

The AI Agents Sandbox provides 28 specialized skills across infrastructure, operations, security, and governance domains. Each skill can be invoked through natural language requests or direct API calls.

## How Skills Work

Skills are AI agent capabilities that automate specific operational tasks. Each skill:

- Has a natural language trigger phrase
- Includes safety controls and human gates for critical operations
- Provides structured outputs and error handling
- Can be chained together in composite workflows

## Skill Invocation

### Natural Language
Simply describe what you want in plain English:

```
"Onboard a new tenant called example.com in Azure East US"
"P0/P1 — the order service is returning 503s across all tenants"
"Prepare the Q3 QBR deck for Monday"
```

### CLI
```bash
./cli skill invoke /compliance-check vm-web-server-001 SOC2
```

### REST API
```bash
curl -X POST http://localhost:8081/api/skills/compliance-check/execute \
  -d '{"target": "vm-web-server-001", "standard": "SOC2"}'
```

## Complete Skill Catalog

### Infrastructure & Provisioning

| Skill | Trigger Phrases | Human Gate | Automatable |
|-------|-----------------|------------|-------------|
| **terraform-provisioning** | "run terraform plan/apply", "provision infra", "check for drift" | `apply` in prod | 90% |
| **kubernetes-cluster-manager** | "provision/upgrade/scale the cluster", "AKS node pool", "AKS automatic", "AKS managed system node pool", "EKS managed node group", "EKS AWS fargate", "EKS karpenter", "EKS auto mode", "EKS self-managed nodes", "EKS AWS outposts", "GKE node pool", "GKE Autopilot", "K8s version upgrade" | Any prod cluster change | 80% |
| **multi-cloud-networking** | "create VNet/VPC", "private endpoint", "NSG", "Network Security Group", "Azure NSG", "Azure Network Security Group", "ASG", "Azure ASG", "Azure Application Security Group", "SG", "Security Group", "AWS SG", "AWS Security Group", "AWS NACLs", "AWS NACL", "AWS Network Access Control Lists", "GCP VPC Firewall Rules", "GCP Network Tags", "diagnose connectivity", "DNS zone" | Hub firewall changes | 80% |
| **container-registry** | "scan this image", "promote to prod registry", "purge old images", "ACR setup", "ECR setup", "GCR setup" | Prod registry push | 85% |

### Deployment & Delivery

| Skill | Trigger Phrases | Human Gate | Automatable |
|-------|-----------------|------------|-------------|
| **cicd-pipeline-monitor** | "why did the build fail?", "DORA metrics", "re-trigger pipeline", "flaky tests" | Re-trigger prod | 85% |
| **deployment-validation** | "validate this deploy", "smoke test", "is it safe to go to prod?", "canary gate" | GO/NO-GO in prod | 85% |
| **gitops-workflow** | "ArgoCD out of sync", "Flux out of sync", "Flux bootstrap", "promote to prod", "ApplicationSet", "drift" | Prod promotion | 85% |
| **service-mesh** | "enable mTLS", "canary split", "A/B testing", "traffic mirroring", "traffic shadowing", "circuit breaker", "retry policy", "service dependency map" | Strict mTLS in prod | 80% |
| **deployment-reliability-analysis** | "deployment failure analysis", "pipeline reliability issues", "CI/CD troubleshooting", "deployment success rate analysis", "failure pattern detection" | No | 80% |

### Operations & Reliability

| Skill | Trigger Phrases | Human Gate | Automatable |
|-------|-----------------|------------|-------------|
| **incident-triage-runbook** | "P0/P1/P2/P3 alert", "outage", "degraded service", "runbook for X" | Novel P0/P1 decisions | 80% |
| **sla-monitoring-alerting** | "error budget", "SRE metrics", "Four Golden Signals", "latency", "traffic", "errors", "saturation", "Service Level Agreement", "SLA", "Service Level Objective", "SLO", "Service Level Indicator", "SLI", "SLO compliance", "SLA breach", "reliability metrics" | No (monitoring only) | 85% |
| **observability-stack** | "set up monitoring", "Grafana dashboard", "Prometheus scrape", "log aggregation", "eBPF", "Pixie" | Prod alerting changes | 80% |
| **chaos-load-testing** | "chaos experiment", "load test", "fault injection", "zone failure", "breaking point" | Any prod chaos | 75% |
| **disaster-recovery** | "failover", "DR drill", "RPO/RTO", "restore failed region", "failback", "business continuity" | Any prod failover | 70% |

### Data & Security

| Skill | Trigger Phrases | Human Gate | Automatable |
|-------|-----------------|------------|-------------|
| **database-operations** | "restore database", "scale DB", "slow queries", "failover DB", "HA status" | PITR restore, failover | 75% |
| **secrets-certificate-manager** | "rotate secret", "cert expiry", "Key Vault", "Azure Key Vault", "AWS Key Management Service", "AWS KMS", "AWS Secrets Manager", "AWS Certificate Manager", "ACM", "Google Cloud Certificate Manager", "Certificate Manager", "Cloud Key Management Service", "Cloud KMS", "cert-manager", "leaked credential" | Root CA rotation | 85% |
| **compliance-security-scanner** | "CVE scan", "checkov", "SOC2 report", "ISO standard", "CIS benchmark", "compliance posture", "az policy state list", "kubectl get events", "kube-bench" | No (scan only) | 80% |
| **policy-as-code** | "enforce policy", "OPA/Gatekeeper", "tagging standard", "governance", "RBAC audit" | Deny-all policy changes | 85% |
| **audit-siem** | "who accessed X?", "audit trail", "Sentinel alert", "security event", "SOC evidence" | No (read-only queries) | 75% |

### Cost & Capacity

| Skill | Trigger Phrases | Human Gate | Automatable |
|-------|-----------------|------------|-------------|
| **cost-optimisation** | "cloud spend", "idle resources", "right-size", "RI coverage", "reserved instance", "spot instance", "cost by tenant" | Resource deletion | 75% |
| **capacity-planning** | "headroom", "forecast capacity", "will we hit limits?", "autoscaler config" | No (analysis only) | 65% |

### Tenant & Developer Experience

| Skill | Trigger Phrases | Human Gate | Automatable |
|-------|-----------------|------------|-------------|
| **tenant-lifecycle-manager** | "onboard tenant", "offboard tenant", "scale tenant tier", "provision customer env" | Offboard/delete | 85% |
| **developer-self-service** | "Backstage", "idp", "internal developer platform", "internal developer portal", "golden path", "onboard team", "service catalog", "self-service template" | Enterprise resource requests | 70% |
| **workload-migration** | "migrate workload", "move to new cluster", "region migration", "cutover plan" | Prod cutover | 70% |

### Governance & Change

| Skill | Trigger Phrases | Human Gate | Automatable |
|-------|-----------------|------------|-------------|
| **change-management** | "change request", "risk score this", "change freeze?", "CAB approval", "emergency change" | Major/emergency changes | 70% |
| **runbook-documentation-gen** | "write a runbook", "ADR", "Application Detection and Response", "Architectural Decision Record", "update the wiki", "document this incident" | No | 75% |
| **stakeholder-comms-drafter** | "draft the incident update", "exec email", "comms for outage", "weekly update", "monthly update", "quarterly update", "yearly update" | Always (never auto-sends) | 60% |
| **kpi-report-generator** | "KPI report", "DORA metrics", "QBR deck", "exec dashboard", "weekly report", "monthly report", "quarterly report", "yearly update" | Before send | 70% |
| **roadmap-execution** | "roadmap", "milestone tracking", "strategy execution", "transformation phase", "project tracking", "goal achievement" | No | 75% |

### Orchestrator / Coordinator

| Skill | Trigger Phrases | Human Gate | Automatable |
|-------|-----------------|------------|-------------|
| **orchestrator** | Any multi-step task: "onboard tenant end-to-end", "respond to P0/P1", "run health check", "prepare QBR" | Per constituent skill | — |

## Composite Workflows

The orchestrator skill enables 10 pre-defined multi-step workflows:

| Workflow | Trigger | Steps | Description |
|----------|---------|-------|-------------|
| **WF-01** | "Onboard [tenant] as enterprise tier in [region]" | 13 steps | Full tenant onboarding |
| **WF-02** | "Take over P0/P1 incident response" | 9 steps | P0/P1 incident response |
| **WF-03** | Weekly compliance scan | 6 steps | Runs automatically every Monday 06:00 UTC |
| **WF-04** | Monthly exec report | 7 steps | Runs automatically 1st of month |
| **WF-05** | "Is v[X] ready to release?" | 7 steps | Pre-release readiness check |
| **WF-06** | "Prepare the Q[N] QBR deck" | 8 steps | QBR preparation |
| **WF-07** | "Provision a new [env] cluster in [region]" | 7 steps | New cluster provisioning |
| **WF-08** | "Sentinel fired — investigate [alert]" | 4 steps | Security incident response |
| **WF-09** | "Run the quarterly DR drill" | 5 steps | DR drill execution |
| **WF-10** | "Onboard the [team name] team" | 13 steps | onboarding |

## Automatic Schedules

| Task | Schedule | Skill |
|------|----------|-------|
| Compliance scan | Monday 06:00 UTC | S05 |
| Certificate expiry check | Daily 09:00 UTC | S13 |
| Capacity planning check | Monday 10:00 UTC | S16 |
| Monthly executive report | 1st of month 07:00 UTC | S08 |
| SLO error budget check | Every 30 minutes | S06 |
| DR drill | Quarterly (Jan/Apr/Jul/Oct 15th) | S21 |
| Chaos experiment (staging) | Wednesday 14:00 UTC | S28 |
| Audit SIEM review | Monday 08:00 UTC | S26 |
| Change calendar preview | Friday 07:00 UTC | S27 |

## Human Gates & Safety Controls

Certain operations require explicit human approval:

```
terraform destroy                 Delete cluster or namespace
Drop / truncate database          Any prod failover
Changes to >20 tenants at once    Hub firewall / VNet peering change
cluster-admin role bindings       Root CA rotation
Emergency break-glass credential  Cost increase >$5,000/month
```

## Skill Development

Skills are defined in `.agents/skills/[skill-name]/SKILL.md` files following the Anthropic Agent Skills specification. Each skill includes:

- YAML frontmatter with metadata
- Input/output schemas
- Usage examples
- Error handling patterns
- Tool requirements

See the **[Skills API](../developer-guide/skills-api.md)** guide for technical implementation details.

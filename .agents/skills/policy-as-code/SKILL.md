---
name: policy-as-code
description: >
  Define, enforce, and audit governance policies across IaC, Kubernetes, and cloud platforms with AI-backed risk scoring and remediation guidance.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Policy-as-Code — World-class Governance Playbook

Codifies guardrails across Terraform/ARM, Kubernetes, Azure/AWS/GCP, and runtime using OPA, Gatekeeper, Azure Policy, AWS SCPs, and CI gates so every change stays compliant.

## When to invoke
- Before merging IaC/manifests to enforce tagging, SKU, and security controls.
- After deployments or runtime drift to audit policy posture and auto-remediate violations.
- During compliance reviews (SOC2, CIS, PCI) to produce evidence packages.
- When dispatcher/memory agents surface `policy-risk`, `compliance-gap`, or security exposures.

## Capabilities
- **Multi-layer enforcement** spanning CI pre-plans, Kubernetes admission, cloud policies, and runtime telemetry.
- **AI risk assessment** contextualizing violations with severity, business impact, and framework mapping.
- **Smart remediation prioritization** ranking fixes by impact/effort while respecting human gates.
- **Intelligent violation analysis** explaining dependencies, attack surface, and regulatory implications.
- **Automated remediation** for safe violations (tagging, SKU drift) plus human-gated escalation when needed.
- **Shared-context integration** (`shared-context://memory-store/policy/{scanId}`) for downstream skills.

## Invocation patterns

```bash
/policy-as-code enforce --scope=terraform --policy=tagging --framework=soc2
/policy-as-code audit --cluster=tenant-42 --policy=resource-limits
/policy-as-code reconcile --provider=azure --initiative=production-baseline
/policy-as-code report --scanId=POLICY-2026-0315-01 --format=json
/policy-as-code alert --event=policy-risk --riskScore=0.86 --tenant=tenant-42
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `scope` | IaC, cluster, cloud, or runtime surface. | `terraform`, `aks`, `aws` |
| `policy` | Policy name (`tagging`, `approved-regions`). | `approved-regions` |
| `framework` | Compliance framework (SOC2, CIS, ISO27001). | `soc2` |
| `cluster` | Kubernetes cluster identifier. | `tenant-42` |
| `provider` | Cloud provider (`azure|aws|gcp`). | `azure` |
| `scanId` | Policy scan/tracking ID. | `POLICY-2026-0315-01` |

## Output contract

```json
{
  "scanId": "POLICY-2026-0315-01",
  "status": "success|failure",
  "policies": ["tagging", "approved-regions"],
  "violations": [
    {
      "id": "POLICY-001",
      "policy": "tagging",
      "severity": "high",
      "riskScore": 0.82,
      "resource": "azurerm_storage_account.production",
      "description": "Missing `owner` tag",
      "autoRemediation": true,
      "recommendation": "Add mandatory tags via policy-driven append"
    }
  ],
  "summary": {
    "critical": 1,
    "high": 2,
    "medium": 4,
    "low": 3
  },
  "aiInsights": {
    "riskImpact": "SOC2-CC6.1 exposures",
    "remediationPriority": "tagging > approved-skus > forbidden-ips"
  },
  "logs": "shared-context://memory-store/policy/POLICY-2026-0315-01",
  "decisionContext": "redis://memory-store/policy/POLICY-2026-0315-01"
}
```

## World-class workflow templates

### AI risk-aware policy enforcement
1. Run CI gate (`conftest`, OPA) against IaC plans/manifests.
2. Score violations by severity, tenant criticality, and compliance impact.
3. Auto-remediate safe gaps (tag injection, SKU alignment) and emit `policy-remediated`.
4. Escalate critical/high risks through human gates with clear impact stories.
5. Command stub: `/policy-as-code enforce --scope=terraform --policy=tagging --framework=soc2`.

### Intelligent violation analysis & reporting
1. Correlate violations across IaC, Kubernetes, cloud policy, and runtime logs.
2. Explain attack surface/regulatory impact (e.g., missing encryption touches SOC2/PCI scope).
3. Generate compliance-ready summaries and emit `policy-report-ready` events for auditors.
4. Feed insights into dispatchers for remediation orchestration.
5. Command stub: `/policy-as-code report --scanId=POLICY-2026-0315-01 --format=json`.

### Continuous production guardrails
1. Apply Gatekeeper/OPA constraints (resource limits, approved registries, namespace policies).
2. Use Azure Policy/Management Groups and AWS SCPs to block dangerous cross-account changes.
3. Detect runtime drift via Falco/log-based findings and escalate with `policy-breach` events.
4. Trigger `incident-triage-runbook` if severity persists or escalates.
5. Command stub: `/policy-as-code reconcile --provider=azure --initiative=production-baseline`.

## AI intelligence highlights
- **AI Risk Assessment** blends policy severity, tenant SLA, and historical remediation to output `riskScore`.
- **Smart Remediation Prioritization** sequences fixes by effort, impact, and confidence to save SRE time.
- **Intelligent Violation Analysis** surfaces causal factors (IAM exposure, unsupported regions, missing tags) for auditors.
- **Predictive Guardrail Alerts** anticipate drift before deployment (new IaC modules lacking constraints).

## Memory agent & dispatcher integration
- Store normalized findings under `shared-context://memory-store/policy/{scanId}`.
- Emit events: `policy-risk`, `policy-remediated`, `policy-report-ready`, `policy-human-gate`.
- Subscribe to `incident-ready`, `cost-anomaly`, `capacity-alert`, `sla-risk` to reprioritize actions.
- Tag entries with `decisionId`, `tenant`, `framework`, `riskScore`, `confidence`.

## Communication protocols
- Primary: CLI/batch commands running `conftest`, Azure Policy CLI, AWS CLI returning JSON.
- Secondary: Event bus (Kafka/NATS) carrying `policy-*` events for dispatchers.
- Fallback: Persist JSON artifacts to `artifact-store://policy/{scanId}.json` for pull-based consumers.

## Observability & telemetry
- Metrics: violations per policy, riskScore distribution, remediation latency, auto-remediation rate.
- Logs: structured `log.event="policy.violation"` with `policy`, `tenant`, `framework`.
- Dashboards: expose `/policy-as-code metrics --format=prometheus` for compliance posture and trends.
- Alerts: riskScore > 0.85, >50 violations in 24h, automation failure rate >10%.

## Failure handling & retries
- Retry policy evaluations or cloud APIs up to 3× with exponential backoff (30s → 2m).
- On auto-remediation failure, store context, emit `policy-remediation-failed`, and trigger human gate.
- Retain artifacts/logs in `reports/policy/` until compliance cycle closes; do not delete until downstream ack.

## Human gates
- Required when:
  1. `riskScore ≥ 0.9` or >20 tenants are impacted.
  2. Policy action removes access, deletes resources, or modifies networking for production.
  3. Dispatcher requests intervention after >2 auto-remediation retries.
- Confirmation template matches the orchestrator standard:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/policy-as-code audit --scope=terraform --policy=tagging --dry-run`.
- Unit tests: `backend/policy/` validates Rego parsing and risk scoring.
- Integration: `scripts/validate-policy-pipeline.sh` runs Gatekeeper/Azure Policy with sample violations.
- Regression: nightly `scripts/nightly-policy-smoke.sh` ensures dispatch events and reports remain accurate.

## References
- Policy templates: `conftest/`, `gatekeeper/templates/`.
- Azure Policy initiatives: `infrastructure/policy/azure/`.
- AWS SCP definitions: `infrastructure/policy/aws/`.

## Related skills
- `/ai-agent-orchestration`: coordinates policy response chains.
- `/incident-triage-runbook`: handles critical/ongoing policy breaches.
- `/compliance-security-scanner`: correlates policy violations with compliance findings.

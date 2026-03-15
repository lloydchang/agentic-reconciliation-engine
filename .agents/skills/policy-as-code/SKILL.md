---
name: policy-as-code
description: >
  Define, enforce, and audit governance policies across IaC, Kubernetes, and cloud platforms with AI-backed risk scoring and remediation prioritization.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Policy-as-Code — World-class Governance Playbook

Codifies guardrails across Terraform/ARM, Kubernetes, Azure/AWS/GCP, and runtime using OPA, Gatekeeper, Azure Policy, AWS SCPs, and CI pre-flight gates. Use this skill whenever policy definitions, enforcement, audits, or violation remediation are required.

## When to invoke
- Before merging IaC/manifests: enforce tagging, SKU, and security requirements.
- After deployments or runtime drift: re-audit and auto-remediate policy violations.
- During compliance reviews (SOC2, CIS, PCI) to generate evidence.
- When dispatchers or memory agents report `policy-risk`, `compliance-gap`, or `security-exposure`.

## Capabilities
- Multi-layer enforcement (CI pre-plan, Kubernetes admission, cloud policy, runtime telemetry).
- **AI Risk Assessment** that contextualizes violations with severity, business impact, and policy mapping.
- **Smart Remediation Prioritization** surfaces actions by impact/effort, hooking into automations when safe.
- **Intelligent Violation Analysis** explains dependencies, attack surface, and regulatory consequences.
- Auto-remediation for safe violations (tagging, SKU drift) plus human-gated escalations.
- Shared context integration (`shared-context://memory-store/policy/{operationId}`) for downstream skills.

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
| `scope` | IaC, cluster, cloud, or runtime environment. | `terraform`, `aks`, `aws` |
| `policy` | Named policy (e.g., `tagging`, `approved-regions`). | `approved-regions` |
| `framework` | Compliance framework (SOC2, CIS, ISO27001). | `soc2` |
| `cluster` | Kubernetes cluster identifier. | `tenant-42` |
| `provider` | Cloud provider (azure|aws|gcp). | `azure` |
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
    "riskImpact": "PCI/PCI-DSS scope",
    "remediationPriority": "tagging > approved-skus > forbidden-ips"
  },
  "logs": "shared-context://memory-store/policy/POLICY-2026-0315-01",
  "decisionContext": "redis://memory-store/policy/POLICY-2026-0315-01"
}
```

## World-class workflow templates

### AI risk-aware policy enforcement
1. Run pre-commit/PR `conftest`/OPA against IaC plans.
2. Policy violations feed AI risk scoring (severity × compliance impact × tenant criticality).
3. Auto-remediate safe violations (tag injection, SKU replacement) and emit `policy-remediated`.
4. Escalate critical/high risk to human gate with detailed explanation.

### Intelligent violation analysis & reporting
1. Correlate policy violations across IaC, Kubernetes, cloud platforms, and runtime.
2. Explain attack surface or compliance consequence (e.g., missing encryption affects SOC2-CC6).
3. Generate executive-ready compliance reports highlighting trending violations.
4. Emit `policy-report-ready` event for dispatcher and auditors.

### Continuous production guardrails
1. Apply Gatekeeper constraints/admission policies (resource limits, approved registries).
2. Use Azure Policy/AWS SCP to deny dangerous configurations instantly.
3. Monitor runtime through Falco/log-based findings for drift.
4. Emit `policy-breach` events when severity escalates and connect to `incident-triage-runbook`.

## AI intelligence highlights
- **AI Risk Assessment**: blends policy severity, tenant SLA, and historical remediation to output `riskScore` and recommended action.
- **Smart Remediation Prioritization**: sequences fixes by effort, impact, and confidence to respect limited SRE bandwidth.
- **Intelligent Violation Analysis**: surfaces causal factors (IAM exposure, unsupported regions, missing tags) with textual explanation for auditors.
- **Predictive Guardrail Alerts**: anticipates policy drift before deployment (e.g., new IaC modules lacking policies).

## Memory agent & dispatcher integration
- Store normalized findings under `shared-context://memory-store/policy/<scanId>`.
- Emit events: `policy-risk`, `policy-remediated`, `policy-report-ready`, `policy-human-gate`.
- Subscribe to `incident-ready`, `cost-anomaly`, `capacity-alert` to reprioritize policy actions.
- Tag all entries with `decisionId`, `tenant`, `framework`, `riskScore`, `confidence`.

## Communication protocols
- Primary: CLI/batch commands running `conftest`, Azure Policy CLI, AWS CLI with JSON output.
- Secondary: Event bus (Kafka/NATS) carrying `policy-*` events for dispatchers/skills.
- Fallback: Persist JSON artifacts to `artifact-store://policy/<scanId>.json`.

## Observability & telemetry
- Metrics: violations per policy, riskScore distribution, remediation latency, auto-remediation rate.
- Logs: structured `log.event="policy.violation"` with `policy`, `tenant`, `framework`.
- Dashboards: integrate `/policy-as-code metrics --format=prometheus` for compliance posture and trends.
- Alerts: riskScore > 0.85, >50 violations in 24h, automation failure rate > 10%.

## Failure handling & retries
- Retry policy scans or cloud API calls (e.g., Azure Policy) up to 3× with exponential backoff (30s → 2m).
- Upon auto-remediation failure, store context, emit `policy-remediation-failed`, and escalate human gate.
- Keep artifacts/logs for audit `<reports/policy>`. Do not delete until compliance cycle completes.

## Human gates
- Required when:
 1. RiskScore ≥ 0.9 or >20 tenants impacted.
 2. Policy action would remove access, delete resources, or change networking.
 3. Dispatcher flags unresolved critical violation after >2 auto-remediation attempts.
- Use standard human gate confirmation capturing impact and reversibility.

## Testing & validation
- Dry-run: `/policy-as-code audit --scope=terraform --policy=tagging --dry-run`.
- Unit tests: `backend/policy/` validates rego parsing/risk scoring.
- Integration: `scripts/validate-policy-pipeline.sh` runs Gatekeeper/Azure Policy with sample violations.
- Regression: nightly `scripts/nightly-policy-smoke.sh` ensures dispatch events fire and reports stay valid.

## References
- Policy templates: `conftest/`, `gatekeeper/templates/`.
- Azure Policy initiatives: `infrastructure/policy/azure/`.
- AWS SCP definitions: `infrastructure/policy/aws/`.

## Related skills
- `/ai-agent-orchestration`: orchestrates policy responses across other skill flows.
- `/incident-triage-runbook`: handles critical policy breaches.
- `/compliance-security-scanner`: correlates policy violations with compliance findings.

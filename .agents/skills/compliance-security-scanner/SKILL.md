---
name: compliance-security-scanner
description: >
  Run automated compliance and security scans every time you need drift detection,
  vulnerability coverage, cost-risk correlation, or executive-ready findings.
  This skill normalizes IaC, container, runtime, IAM, and secrets data into a shared schema.
tools:
  - Bash
  - Read
  - Write
allowed-tools:
  - Bash
  - Read
  - Write
---

# Compliance & Security Scanner — World-class Operations Playbook

Leverages IaC, container, runtime, and secrets tooling with standardized scoring, rich remediation guidance, and telemetry hooks. Use this skill for comprehensive compliance posture, rapid incident-response scanning, or validation gates before deployments.

## When to invoke
- Pre-merge/change (Terraform, ARM, Helm, Kubernetes manifests) to block non-compliant code.
- Scheduled quarterly or weekly posture scans against SOC2, CIS, ISO27001, and CIS Azure baselines.
- Post-incident triage when `incident-triage-runbook` flags new findings or vulnerability feeds spike.
- Security culture reviews (secrets detection, IAM over-permission, container CVEs).
- Dispatcher requests (`ai-agent-orchestration`, memory agent risk bumps) when `riskScore ≥ 70`, dependency shifts, or policy gaps appear.

## Capabilities
- **Framework sweep** for SOC2, ISO27001, NIST CSF, CIS Azure, and CIS Kubernetes.
- **Comprehensive toolchain**: `checkov`, `tfsec`, `terrascan`, `trivy`, `grype`, `kube-bench`, `kubesec`, `polaris`, `gitleaks`, `osv-scanner`, `dependabot`, `prowler`, `cloud-custodian`.
- **Normalized schema & prioritization** (CVE severity, phase, impact, asset criticality, remediation guidance).
- **Secrets drift detection** with optional auto-rotation hooks into key vaults.
- **Memory & dispatcher integration** that shares context, risk scores, and evidence for downstream skills.

## Invocation patterns

```bash
/compliance-security-scanner run --scope=prod-terraform --framework=soc2 --priority=high
/compliance-security-scanner secrets --repo=payments-service --risk-threshold=medium
/compliance-security-scanner iam --subscription=rg-hub-eastus --skyline=true
/compliance-security-scanner report --scan-id=SCAN-2026-0300 --format=json --destination=reports/posture.json
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `scope` | Target (Terraform root, Kubernetes namespace, container repo, subscription). | `prod-terraform` |
| `framework` | Compliance benchmark or report pack. | `soc2`, `cis-azure`, `iso27001` |
| `priority` | Criticality for dispatcher resourcing. | `critical`, `normal` |
| `riskThreshold` | Filter for findings (`critical|high|medium|low`). | `high` |
| `region` | Region or tenant alias to limit scan impact. | `us-east-1` |
| `timeframe` | Lookback window for drift analysis. | `30d` |

## Output contract
Every execution emits structured JSON that captures findings, remediation guidance, and telemetry for audit-ready sharing:

```json
{
  "scanId": "SCAN-2026-0300",
  "status": "success|failure",
  "scope": "prod-terraform",
  "frameworks": ["SOC2", "CIS-Azure"],
  "findings": [
    {
      "id": "FIND-001",
      "tool": "checkov",
      "category": "iac",
      "severity": "CRITICAL",
      "riskScore": 91,
      "resource": "azurerm_storage_account.production",
      "description": "Encryption at rest not enabled",
      "complianceFrameworks": ["SOC2-CC6.1", "CIS-Azure 3.1"],
      "remediation": "Enable Microsoft-managed keys or bring-your-own-key",
      "status": "open"
    }
  ],
  "summary": {
    "critical": 1,
    "high": 2,
    "medium": 4,
    "low": 8
  },
  "reportUrl": "https://reporting.internal/scans/SCAN-2026-0300",
  "timestamp": "2026-03-15T07:10:00Z"
}
```

## World-class workflow templates

### Full compliance sweep
- Trigger: scheduled quarterly audit or `ai-agent-orchestration` dispatch event.
- Steps: IaC lint (`checkov`, `tfsec`), container CVEs (`trivy`, `grype`), Kubernetes manifest hardening (`kube-bench`, `kubesec`, `polaris`), IAM posture reviews, secrets sweeps (`gitleaks`, `trufflehog`), runtime posture (Security Hub/Defender).
- Output: normalized findings list, compliance scorecard, autopopulated remediation backlog, and integration-ready context.
- Command stub: `/compliance-security-scanner run --scope=prod-terraform --framework=soc2,cis-azure --priority=critical`.

### Secret & IAM drift guard
- Trigger: memory agent flag (`secret_leak`, `privilege_escalation`) or periodic secrets review.
- Steps: secrets scan (`gitleaks`, `trufflehog`), IAM interrogation (`az role assignment list`, `kubectl get clusterrolebindings`), auto-rotate via vault APIs when safe, emit tickets for manual updates otherwise.
- Output: secret attribution log, IAM violations, rotation status, and `human-gate-required` events where automation stalls.

### Rapid incident triage
- Trigger: findings surfaced by `incident-triage-runbook` or an urgent CVE.
- Steps: attack path modeling, severity assignment, mitigation plan (NSG updates, patched image rollout, encryption fixes), and evidence bundling.
- Launch command: `/compliance-security-scanner run --scope=critical-service --framework=iso27001 --priority=high --timeframe=7d`.

## AI intelligence highlights
- **AI Risk Assessment** contextualizes violations using threat scoring, tenancy impact, and business sensitivity to emit dynamic `riskScore`.
- **Smart Remediation Prioritization** ranks fixes by impact/effort, surfaces cost/effort tradeoffs, and sequences actions across tenants.
- **Intelligent Violation Analysis** correlates IaC, runtime, IAM, and secrets findings to explain attack vectors and regulatory implications.

## Memory agent & dispatcher integration
- Publish normalized findings to `shared-context://memory-store/<tenant>/compliance-scans` so cost, governance, and deployment skills reuse verdicts.
- Subscribe to events (`agent-completed`, `insight-ready`, `skill-request`, `risk-bump`) and respond with `compliance-report-ready`, `evidence-promo`, `human-gate-required`.
- Tag telemetry with `decisionId`, `orchestrationId`, `tenant`, `region`, `riskScore`, and `framework`.
- Communication: share context via Redis/ETCD (`shared-context://memory-store/compliance/SCAN-2026-0300`), broadcast on Pulsar/Kafka topics (`scan-completed`, `finding-critical`, `credential-expired`), and fallback to `artifact-store://scans/` when messaging is offline.

## Observability & telemetry
- Metrics: scan duration, normalized findings count, human gate hits, dispatcher-trigger latency.
- Logs: structured entries (`log.event="compliance.scan"`, `severity=critical|high|medium|low`, `decisionId`, `correlationId`).
- Dashboards: expose `/compliance-security-scanner metrics --format=prometheus` to Grafana for operational visibility.
- Alerts: trigger when >5 critical untriaged findings exist, telemetry gaps exceed 5 minutes, or vault/registry integrations fail.

## Failure handling & retries
- Retry each tool (checkov, trivy, etc.) up to 2 additional times with exponential backoff (60s → 120s).
- On tool failure, fall back to `compliance-check-lite` (subset rules) while logging the deficiency.
- Preserve intermediate artifacts for forensic review (`reports/last-scan`, `logs/{scanId}.log`).
- After 3 consecutive tool failures, log the event, emit `human-gate-required`, and escalate with contextual evidence.

## Human gates
- Required when:
  1. `riskScore ≥ 90` or >20 tenants are affected.
  2. Remediation touches production configs (firewall, IAM, encryption, segmentation).
  3. Secrets rotation cannot auto-resolve and requires manual vault intervention.
- Confirmation template:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/compliance-security-scanner run --scope=prod-terraform --framework=soc2 --dry-run`.
- Unit tests: target normalization logic under `backend/compliance/transformer/`.
- Integration: `scripts/validate-compliance-pipeline.sh` ensures each tool emits the expected schema.
- Regression: nightly `scripts/nightly-compliance-smoke.sh` flows through downstream skills (`cost-optimization`, `incident-triage`) to ensure dispatchers consume findings.

## References
- Infrastructure metadata: `docs/SECURITY-OPERATIONS.md`, `docs/SECRET-MANAGEMENT.md`.
- Dispatch wiring templates: `backend/orchestration/dispatcher/`.
- Reports location: `monitoring/agents/` dashboards, `logs/local-automation/`.

## Related skills
- `/workflow-management`: inspect scan-related workflows and rerun histories.
- `/ai-agent-orchestration`: coordinate dynamic dispatcher routing and reroute findings.
- `/incident-triage-runbook`: automatically escalate remediation steps for critical findings.
- `/secrets-certificate-manager`: rotate certificates/secrets surfaced during scans.

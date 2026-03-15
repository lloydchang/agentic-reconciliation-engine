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

Leverages IaC, container, runtime, and secrets tooling with standardized scoring, rich remediation guidance, and telemetry hooks. Use this skill when you need comprehensive compliance posture, rapid incident response scanning, or to validate remediation before deployment.

## When to invoke
- Pre-merge/change (Terraform, ARM, Helm, Kubernetes manifests) to block non-compliant code.
- Scheduled quarterly or weekly posture scans against SOC2, CIS, ISO27001, and CIS Azure baselines.
- Post-incident triage when `incident-triage-runbook` flags new findings.
- Security culture reviews (e.g., secrets detection, IAM over-permission, container CVEs).
- As part of the `ai-agent-orchestration` dispatcher when memory agents surface risks (riskScore ≥ 70, dependency shifts, policy gaps).

## Capabilities
- Framework coverage: SOC2, ISO27001, NIST CSF, CIS Azure, CIS Kubernetes.
- Toolchain: `checkov`, `tfsec`, `terrascan`, `trivy`, `grype`, `kube-bench`, `kubesec`, `polaris`, `gitleaks`, `osv-scanner`, `dependabot`, `prowler`, `cloud-custodian`.
- Normalised schema & prioritisation (CVE/phases/impact, asset criticality weighting, remediation steps).
- Secrets drift detection + auto-rotation hooks for key vaults.
- Integration with memory dispatcher events and `shared-context://memory-store` for dynamic skill chaining.

## AI intelligence highlights
- **AI Risk Assessment**: contextualizes compliance violations with threat scoring, business sensitivity, and tenancy impact to assign dynamic `riskScore`.
- **Smart Remediation Prioritization**: ranks fixes by impact/effort, surfaces cost/effort tradeoffs, and sequences actions across tenants.
- **Intelligent Violation Analysis**: correlates violations across IaC, runtime, IAM, and secrets to explain attack vectors and regulatory implications.

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
| `priority` | Criticality for dispatcher decision/resourcing. | `critical`, `normal` |
| `riskThreshold` | Filter for findings `critical|high|medium|low`. | `high` |
| `region` | Region or tenant alias to limit scan impact. | `us-east-1` |
| `timeframe` | Lookback window for drift analysis. | `30d` |

## Output contract
Every execution emits structured JSON to trace findings and remediation:

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
- Trigger: `ai-agent-orchestration` dispatch event or scheduled quarterly audit.
- Steps: IaC (checkov/tfsec), container (trivy/grype), Kubernetes manifests (kube-bench, kubesec, polaris), IAM (over-privileged roles), secrets (gitleaks, trufflehog), runtime posture (cloud Defender/Security Hub).
- Output: normalized findings list, compliance scorecard, autopopulated remediation backlog.
- Command stub: `/compliance-security-scanner run --scope=prod-terraform --framework=soc2,cis-azure --priority=critical`.

### Secret & IAM drift guard
- Trigger: mesos of secrets detection or dispatcher flag from memory agents (insights include `secret_leak`, `privilege_escalation`).
- Action: `gitleaks`/`trufflehog`, `az role assignment list`, `kubectl get clusterrolebindings` -> auto-rotate via vault APIs if enabled, issue tickets for service accounts with interactive update steps.
- Output: secret attribution log, IAM violations, rotation status.

### Rapid incident triage
- Trigger: findings from `incident-triage-runbook` or time-sensitive CVE exposures (vulnerability feed).
- Steps: Attack path modelling (asset criticality mapping), assign severity, propose mitigation (reconfigure NSG, redeploy patched image).
- Use `/compliance-security-scanner run --scope=critical-service --framework=iso27001 --priority=high --timeframe=7d`.

## Memory agent & dispatcher integration
- Exposes normalized JSON to `shared-context://memory-store/<tenant>/compliance-scans` for other skills to read (cost, governance).
- Subscribe to events: `agent-completed`, `insight-ready`, `skill-request`, `risk-bump`.
- Response events: `compliance-report-ready`, `evidence-promo`, `human-gate-required`.
- Telemetry tags: `decisionId`, `orchestrationId`, `tenant`, `region`, `riskScore`, `framework`.

## Communication protocols
- Primary: share context over Redis/ETCD (`shared-context://memory-store/compliance/SCAN-2026-0300`).
- Messaging: use Pulsar/Kafka topics to signal `scan-completed`, `finding-critical`, `credential-expired`.
- Fallback: drop zipped reports into `artifact-store://scans/` when live bus unreachable (dispatcher polls every 15s).

## Observability & telemetry
- Emit metrics: scan duration, normalized findings count, human gate hits, dispatcher-trigger latency.
- Log structured entries (`log.event="compliance.scan"`, `severity=critical|high|medium|low`, `decisionId`, `correlationId`).
- Grafana dashboard: integrate `/compliance-security-scanner metrics --format=prometheus`.
- Alerts: 1) >5 critical untriaged findings, 2) telemetry gap >5 mins, 3) integration errors when speaking to vaults/registries.

## Failure handling & retries
- Retry policy: 2 retries per tool (checkov, trivy) with exponential backoff (default 60s → 120s).
- On tool failure, fallback to baked-in `compliance-check-lite` (subset of rules).
- Keep intermediate artifacts for forensic review (`reports/last-scan`, `logs/scan-id.log`).
- Escalate after 3 tool failures: log, store context, emit `human-gate-required`.

## Human gates
- Required when:
 1. Scan uncovers `riskScore ≥ 90` or >20 tenants affected.
 2. Compliance remediation changes production configs (firewall, IAM, encryption, network segmentation).
 3. Secrets rotation cannot auto-resolve (manual vault action needed).
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
- Regression: nightly `scripts/nightly-compliance-smoke.sh` hitting `cost-optimization`/`incident-triage` downstream to ensure dispatchers pick results.

## References
- Infrastructure metadata: `docs/SECURITY-OPERATIONS.md`, `docs/SECRET-MANAGEMENT.md`.
- Dispatch wiring templates: `backend/orchestration/dispatcher/`.
- Reports locating: `monitoring/agents/` dashboards, `logs/local-automation/`.

## Related skills
- `/workflow-management`: inspect scan-related workflows and rerun histories.
- `/ai-agent-orchestration`: coordinate dynamic dispatchers and reroute findings.
- `/incident-triage-runbook`: automatically escalate remediation steps for critical findings.
- `/secrets-certificate-manager`: rotate certificates/secrets surfaced during scans.

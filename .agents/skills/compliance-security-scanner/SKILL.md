---
name: compliance-security-scanner
description: >
  Use this skill to run automated security and compliance scans across cloud
  infrastructure, IaC code, containers, and APIs. Triggers: any request to
  run a security audit, check compliance posture (SOC2, ISO27001, CIS
  benchmarks), scan Terraform/Kubernetes manifests, review IAM permissions,
  detect secrets in code, assess CVE exposure, or generate a compliance report
  for executive or auditor review. Also handles before major deployments,
  quarterly security audits, and new compliance vulnerability notifications.
tools:
  - bash
  - computer
---

# Compliance & Security Scanner Skill

Unified security scanning pipeline covering IaC, containers, runtime, IAM,
and compliance frameworks. All findings are normalised to a standard schema,
de-duplicated, and prioritised by exploitability × impact.

# Compliance & Security Scanner Skill

Unified security scanning pipeline covering IaC, containers, runtime, IAM,
and compliance frameworks. All findings are normalised to a standard schema,
de-duplicated, and prioritised by exploitability × impact.

## Enhanced Security Compliance Audit

### Continuously Audit Infrastructure Against Security Frameworks
Continuously audit infrastructure against security frameworks with automated compliance checking.

**Supported Frameworks:**
- SOC2 (Security, Availability, Processing Integrity, Confidentiality, Privacy)
- CIS benchmarks (Center for Internet Security)
- ISO27001 (Information Security Management)

**Workflow:**
1. Collect comprehensive infrastructure metadata and configurations
2. Run compliance rules against collected data for each framework
3. Identify violations and non-compliant configurations
4. Generate detailed audit findings with remediation guidance
5. Produce security compliance report with compliance scores

**Output:** Security compliance report with framework-specific scores, identified violations, remediation recommendations, and compliance trends.

## Enhanced Cloud Compliance Audit Workflow

### Azure Policy & Kubernetes Compliance Checking
Perform comprehensive compliance audits using Azure Policy and Kubernetes monitoring.

**When to Use:**
- Before approving a deployment pipeline to production
- During scheduled quarterly security audits  
- When notified of a new compliance vulnerability (e.g., CVE)

**Instructions:**
1. Run `az policy state list` for the relevant subscription to identify non-compliant resources
2. Run `kubectl get events -A` and `kube-bench` to check Kubernetes cluster hardening status
3. Compare findings against the `references/baseline-compliance-standard.md`
4. Generate a summary report highlighting:
   - Critical vulnerabilities
   - Remediation steps
5. Create issues in the issue tracker with specific remediation actions for non-compliant resources

**New Scan Categories:**
| Category             | Tool(s)                              | Trigger                        |
|----------------------|--------------------------------------|--------------------------------|
| Azure Policy         | `az policy state list`               | Pre-deployment, weekly         |
| K8s Events           | `kubectl get events -A`              | On incidents, daily            |
| Cluster Hardening    | `kube-bench`                         | Post-deployment, weekly        |

---

## Scan Categories & Tools

| Category             | Tool(s)                              | Trigger                        |
|----------------------|--------------------------------------|--------------------------------|
| IaC (Terraform/ARM)  | `checkov`, `tfsec`, `terrascan`      | Pre-plan, pre-merge            |
| Container images     | `trivy`, `grype`                     | Pre-push, scheduled            |
| Kubernetes manifests | `kubesec`, `kube-bench`, `polaris`   | Pre-deploy, scheduled          |
| Secrets in code      | `gitleaks`, `truffleHog`             | Pre-commit, PR check           |
| IAM / RBAC           | `aws-iam-analyzer`, Azure Advisor    | Weekly, on change              |
| Runtime posture      | Azure Defender, AWS Security Hub     | Continuous                     |
| Dependency CVEs      | `dependabot`, `snyk`, `osv-scanner`  | On PR, scheduled               |
| Network exposure     | `nmap` (internal), cloud NSG rules   | Weekly                         |
| Compliance benchmarks| `prowler`, `cloud-custodian`         | Daily                          |

---

## Unified Scan Workflow

### Run a Full Scan
```bash
# IaC scan
checkov -d ./terraform --output json > reports/checkov.json
tfsec ./terraform --format json > reports/tfsec.json

# Container scan
trivy image $IMAGE_REF --format json > reports/trivy.json

# Kubernetes
kubesec scan k8s/*.yaml > reports/kubesec.json
kube-bench --json > reports/kubebench.json

# Secrets
gitleaks detect --source . --report-format json \
  --report-path reports/gitleaks.json

# Compliance
prowler -M json -o reports/ --compliance cis_azure_1.4.0
```

### Normalise Findings
All tool outputs are mapped to a common finding schema:
```json
{
  "id": "FIND-0001",
  "tool": "checkov",
  "category": "iac",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
  "title": "string",
  "resource": "string",
  "file": "string",
  "line": 0,
  "cve": "CVE-YYYY-NNNNN",
  "cvss_score": 0.0,
  "remediation": "string",
  "compliance_frameworks": ["SOC2-CC6", "CIS-2.1"],
  "status": "open|suppressed|fixed"
}
```

### Prioritisation
Score = `CVSS_score × exploitability_factor × asset_criticality`
- **Critical (score ≥ 9.0)**: block deployment, page on-call
- **High (7.0–8.9)**: must fix before next release
- **Medium (4.0–6.9)**: fix within 30 days
- **Low (<4.0)**: log and track

---

## IAM / RBAC Review

```bash
# Azure — find over-privileged identities
az role assignment list --all --output json | \
  jq '[.[] | select(.roleDefinitionName == "Owner" or .roleDefinitionName == "Contributor")]'

# Kubernetes — check for cluster-admin bindings
kubectl get clusterrolebindings -o json | \
  jq '.items[] | select(.roleRef.name=="cluster-admin")'
```

Flag:
- `Owner`/`cluster-admin` assignments to non-emergency principals
- Service accounts with wildcard resource permissions
- Unused service principals (no activity > 90 days)
- Missing MFA on privileged accounts

---

## Compliance Framework Mapping

| Control               | CIS Azure | SOC2   | ISO27001 | NIST CSF |
|-----------------------|-----------|--------|----------|----------|
| Encryption at rest    | 3.1–3.7   | CC6.1  | A.10.1   | PR.DS-1  |
| MFA enforcement       | 1.1       | CC6.3  | A.9.4    | PR.AC-7  |
| Audit logging         | 5.1–5.3   | CC7.2  | A.12.4   | DE.CM-1  |
| Network segmentation  | 6.1–6.6   | CC6.6  | A.13.1   | PR.AC-5  |
| Patch management      | 2.1       | CC7.1  | A.12.6   | ID.RA-1  |

---

## Secrets Detection

```bash
# Pre-commit hook (install via `pre-commit install`)
repos:
  - repo: https://github.com/gitleaks/gitleaks
    hooks:
      - id: gitleaks

# Historical scan
gitleaks detect --source . --log-opts="--all" \
  --report-format json --report-path reports/gitleaks-history.json
```

On secret detection:
1. Block the commit/PR
2. Identify the secret type (API key, password, cert, token)
3. Auto-rotate if integration is configured (Azure Key Vault, AWS Secrets Manager)
4. Notify the committer and security team

---

## Compliance Report Generation

Produce an executive-ready compliance report:
```
Executive Summary
  - Overall posture score: X/100
  - Critical findings: N (N unresolved)
  - Compliance status: SOC2 ✅ | ISO27001 ⚠️ | CIS Azure 89%

Top 5 Risk Areas (by score)
  ...

Findings by Severity
  ...

Remediation Roadmap (by priority)
  ...

Trend: Last 90 Days
  ...
```

---

## Examples

- "Run a full security scan on the prod Terraform modules"
- "Check for any secrets committed to the payments-service repo"
- "Show me all over-privileged IAM roles across our Azure subscriptions"
- "Generate a SOC2 compliance report for the Q2 audit"
- "What's our current CVE exposure in the container registry?"

---

## Output Format

```json
{
  "scan_id": "SCAN-2025-001",
  "critical_findings": 0,
  "status": "success|failure",
  "timestamp": "ISO8601",
  "scope": "string",
  "summary": { "critical": 0, "high": 0, "medium": 0, "low": 0 },
  "compliance_score": 0,
  "findings": [],
  "report_url": "string"
}
```

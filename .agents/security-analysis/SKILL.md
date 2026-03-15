---
name: security-analysis
description: >
  Execute vulnerability scanning, threat hunting, and posture analysis using AI-intelligence, dynamic context, and dispatcher events.
argument-hint: "[targetResource] [scanType] [priority]"
context: fork
agent: Explore
allowed-tools:
  - Bash
  - Read
  - Write
---

# Security Analysis — World-class Threat Detection Playbook

Performs AI-enhanced security assessments (vulnerability, configuration, runtime) with intelligence ingestion, structured outputs, and dispatcher-grade signals for remediation.

## When to invoke
- Conduct vulnerability scans (critical/urgent) on applications or infrastructure.
- Review configuration/runtime posture immediately after deployments or suspicious telemetry.
- Respond to dispatcher/memory agent alerts (`riskScore ≥ 70`, `policy-risk`, `incident-ready`).
- Run regular security hygiene (weekly scans, compliance checks, secrets assurance).

## Capabilities
- **Dynamic target discovery** feeding threat feeds (CVE, abuse IP, MITRE) plus telemetry context.
- **AI risk scoring & remediation prioritization** for vulnerabilities/exposures.
- **Threat hunting and incident enrichment** with PoC/IOC extraction.
- **Shared-context propagation** via `shared-context://memory-store/security/{scanId}` for downstream skills.
- **Human gating** for intrusive or high-impact scans.

## Invocation patterns

```bash
/security-analysis scan --targetResource=web-server-001 --scanType=vulnerability --priority=critical
/security-analysis scan --targetResource=network-infra --scanType=configuration --priority=high
/security-analysis scan --targetResource=database-cluster --scanType=runtime --priority=normal
/security-analysis monitor --targetResource=all --scanType=full --priority=high --timeframe=7d
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `targetResource` | Resource/app to analyze. | `web-server-001` |
| `scanType` | `vulnerability|malware|configuration|full|runtime`. | `full` |
| `priority` | Scan criticality. | `critical` |
| `timeframe` | Lookback window for telemetry. | `7d` |
| `context` | Enrichment context (shared route). | `shared-context://memory-store/capacity/` |

## Output contract

```json
{
  "scanId": "SEC-2026-0315-01",
  "targetResource": "web-server-001",
  "scanType": "vulnerability",
  "status": "completed|failed",
  "riskScore": 0.78,
  "insights": [
    {
      "cve": "CVE-2024-12345",
      "severity": "critical",
      "vector": "network",
      "description": "Remote code execution via outdated library"
    }
  ],
  "threatIntelligence": [
    "Active exploit observed in the wild",
    "IOC: 192.0.2.44 communicating with malicious C2"
  ],
  "aiRemediation": [
    {
      "id": "REMED-001",
      "action": "patch",
      "resource": "web-server-001",
      "confidence": 0.92,
      "impact": "High",
      "effort": "Low"
    }
  ],
  "decisionContext": "redis://memory-store/security/SEC-2026-0315-01",
  "logs": "shared-context://memory-store/security/SEC-2026-0315-01"
}
```

## World-class workflow templates

### AI-assisted security scan
1. Discover targets across infra, telemetry, and threat intelligence.
2. Run vulnerability/malware/configuration/runtime scans with scanning tools (trivy, gitleaks, falco) and gather context.
3. Score each finding (`riskScore`), attach remediation steps, and emit `security-scan-complete`.

### Incident enrichment
1. Correlate scan results with prior incidents, attackers, and policy violations.
2. Package logs/traces/alerts in shared context for `incident-triage-runbook` or `policy-as-code`.
3. Emit `incident-ready` or `policy-risk` events when escalations needed.

### Predictive posture monitoring
1. Scan runtime telemetry (logs, traces, auth events) for anomalies.
2. Forecast risk using AI (anomaly detection + threat modeling) and notify `sla-monitoring-alerting` or operations.
3. Produce `security-anomaly` events linking anomalies to vulnerabilities.

## AI intelligence highlights
- **AI risk assessment** weighs CVSS, exploitation context, asset criticality, and compliance impact for every finding.
- **Smart remediation prioritization** ranks fixes by impact, effort, and automation confidence.
- **Intelligent violation analysis** explains potential attack paths/regulatory consequences.
- **Predictive threat forecasting** uses anomaly detection and threat feeds to anticipate escalations.

## Memory agent & dispatcher integration
- Persist findings at `shared-context://memory-store/security/{scanId}` tagged with `decisionId`, `tenant`, `riskScore`.
- Emit events: `security-scan-complete`, `security-anomaly`, `policy-risk`, `incident-ready`.
- Respond to dispatcher signals (`policy-risk`, `cost-anomaly`) by expanding scan scope or adjusting priority.
- Provide fallback artifacts via `artifact-store://security/{scanId}.json` when needed.

## Observability & telemetry
- Metrics: scans executed, severity distributions, AI confidence, scan duration, false positive rates.
- Logs: structured `log.event="security.scan"` with `scanId`, `riskScore`, `priority`.
- Dashboards: integrate `/security-analysis metrics --format=prometheus` for posture trending.
- Alerts: riskScore ≥ 0.85, >5 critical findings, scan failures beyond threshold.

## Failure handling & retries
- Retry on transient errors (API, network) up to 2× with exponential backoff.
- Switch to fallback scanners if primary fails and emit `security-scan-fallback`.
- Preserve scans, logs, and context until downstream ack for auditing.

## Human gates
- Required when:
  1. Scans interfere with production or high-criticality workloads.
  2. High-impact findings (riskScore ≥ 0.9) need manual validation.
  3. Dispatcher requests manual review after repeated scan failures.
- Confirmation template follows orchestrator standard (impact/reversibility).

## Testing & validation
- Dry-run: `/security-analysis scan --targetResource=canary --scanType=vulnerability --dry-run`.
- Unit tests: `backend/security/analysis` ensures scoring and parsing logic meet expectations.
- Integration: `scripts/validate-security-analysis.sh` runs scans/emulation and emits events for follow-ups.
- Regression: nightly `scripts/nightly-security-smoke.sh` keeps telemetry thresholds and AI scoring stable.

## References
- Templates: `templates/security-report.md`.
- Scripts: `scripts/vulnerability-scanner.sh`, `scripts/incident-response.sh`.
- Threat config: `assets/threat-integration.json`.

## Related skills
- `/incident-triage-runbook`: remediates critical detections.
- `/compliance-security-scanner`: correlates compliance violations with vulnerabilities.
- `/workflow-management`: orchestrates scan/retry/follow-up workflows.

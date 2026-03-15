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

Performs AI-enhanced security assessments (vulnerability, configuration, runtime) with real-time intelligence ingestion, structured outputs, and dispatchable signals to downstream remediation/workflow skills. Trigger when investigating incidents, verifying posture, or responding to dispatcher risk alerts.

## When to invoke
- Critical/high priority vulnerability scans (external/internal resources).
- Configuration and runtime posture reviews after deployments or changes.
- Incident response or dispatcher alerts (`riskScore ≥ 70`, `policy-risk`, `incident-ready`).
- Regular security hygiene (weekly scans, compliance checkpoints, secrets assurance).

## Capabilities
- Dynamic target discovery and recon context (threat feeds, CVE lookup, port/service enumeration).
- AI-informed risk scoring + remediation prioritization plus threat correlation.
- Automation-safe post-scan intelligence (POC reproduction, IOC highlights) for other skills.
- Shared context integration `shared-context://memory-store/security/<scanId>` for dispatcher/incident use.
- Human gate guidance for intrusive or high-risk scans.

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
| `targetResource` | Resource/app stack to analyze. | `web-server-001` |
| `scanType` | `vulnerability|malware|configuration|full|runtime`. | `full` |
| `priority` | Criticality affecting resource allocation. | `critical` |
| `timeframe` | Lookback period for telemetry/context. | `7d` |
| `context` | Additional context store to enrich detection. | `shared-context://memory-store/capacity/` |

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
1. Discover targets via infrastructure APIs and Recon data.
2. Ingest threat feeds (CVE, abuse IP DB, malware hashes, CISA alerts) and combine with telemetry.
3. Run vulnerability/malware/configuration scans using dynamic context, capturing findings.
4. Score each finding by `riskScore`, produce remediation guidance, emit `security-scan` event.

### Intelligence-driven incident enrichment
1. Correlate findings with past incidents, attackers, and behavior patterns.
2. Add logs/traces/alerts (shared context) so incident runbook or compliance skills can act.
3. Emit `incident-ready` or `policy-risk` events for dispatcher orchestration.

### Predictive posture & anomaly monitoring
1. Scan runtime telemetry (logs, metrics, traces) for anomalies (suspicious commands, authentication failures).
2. Forecast risk using AI patterns and forward to `incident-triage-runbook` or `sla-monitoring-alerting`.
3. Provide enriched report linking anomalies to vulnerabilities/policies.

## AI intelligence highlights
- **AI Risk Assessment**: weighs CVSS, exploitation context, asset criticality, and compliance impact to determine `riskScore`.
- **Smart Remediation Prioritization**: ranks fixes by impact/effort/confidence.
- **Intelligent Violation Analysis**: articulates attack path, exploit theory, and related regulatory controls.
- **Predictive Threat Forecasting**: uses anomaly detection plus threat intelligence to predict emergent threats.

## Memory agent & dispatcher integration
- Emit to shared store `shared-context://memory-store/security/<scanId>` with all findings, riskScore, recommended actions.
- Generate events: `security-scan-complete`, `security-anomaly`, `policy-risk`, `incident-ready`.
- Consume dispatcher events (e.g., `policy-risk`, `cost-anomaly`) to adjust scanning scope or priority.
- Tag records with `decisionId`, `tenant`, `riskScore`, `confidence`.

## Communication protocols
- Primary: CLI-driven scan commands producing JSON artifacts; wrappers call security tooling (nmap, trivy, scanning APIs).
- Secondary: Event bus (Kafka/NATS) for `security-*` signals.
- Fallback: Persistent artifacts `artifact-store://security/<scanId>.json`.

## Observability & telemetry
- Metrics: scans per period, findings severity distribution, AI confidence, scan duration, false-positive rate.
- Logs: structured `log.event="security.scan"` with `scanId`, `riskScore`, `priority`.
- Dashboards: integrate `/security-analysis metrics --format=prometheus` for posture trending.
- Alerts: riskScore ≥ 0.85, critical findings > 5, scan failures > threshold.

## Failure handling & retries
- Retry temporary failures (network, API) up to 2× with exponential backoff.
- On tool failure, switch to fallback scanner (secondary tool) and emit `security-scan-fallback`.
- Persist scans, context, logs until downstream ack for audit; never delete data prematurely.

## Human gates
- Required when:
 1. Scans risk interfering with production services (workloads critical, high priority).
 2. High-impact findings (riskScore ≥ 0.9) require manual verification before remediation.
 3. Dispatcher requests manual review after repeated scan failures.
- Use standard human gate template to capture impact/reversibility.

## Testing & validation
- Dry-run: `/security-analysis scan --targetResource=canary --scanType=vulnerability --dry-run`.
- Unit tests: `backend/security/analysis` ensures scoring and parsing logic operate per expectation.
- Integration: `scripts/validate-security-analysis.sh` runs scans in emulator mode and emits events for downstream skills.
- Regression: nightly `scripts/nightly-security-smoke.sh` keeps telemetry thresholds, alert volumes, and AI scoring stable.

## References
- Templates: `templates/security-report.md`.
- Scripts: `scripts/vulnerability-scanner.sh`, `scripts/incident-response.sh`.
- Threat config: `assets/threat-integration.json`.

## Related skills
- `/incident-triage-runbook`: triggers remediation for critical detections.
- `/compliance-security-scanner`: cross-references compliance violations with vulnerabilities.
- `/workflow-management`: orchestrates scans, retries, and follow-up actions.

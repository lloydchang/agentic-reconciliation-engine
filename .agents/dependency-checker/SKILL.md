---
name: dependency-checker
description: |
  Analyze service dependencies, third-party libraries, and runtime graphs to detect vulnerabilities, outdated versions, or unsafe abstractions before deployments reach production.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Dependency Checker — World-class Supply Chain Playbook

Builds a safety net around dependencies by scanning SBOMs, runtime graphs, and manifests to surface high-risk packages, misconfigurations, or dependency drift.

## When to invoke
- Before releases to verify dependency licenses, vulnerabilities, and versions.
- When CVEs, container scans, or policy engines emit alerts tied to third-party libs.
- After dependency upgrades to confirm compatibility and stability.
- Dispatcher/memory agents request dependency sanity (`dependency-risk`, `supply-chain-alert`).

## Capabilities
- **SBOM analysis** merges build artifacts (Gradle/Maven/npm/PyPI) with CVE feeds.
- **Runtime graph inspection** correlates service dependencies and resource usage.
- **Vulnerability focus** highlights CVEs, patch gaps, and licensing issues.
- **Automation hooks** can pin versions, open PRs, or trigger rebuilds.
- **Shared context** stores evaluations under `shared-context://memory-store/dependency-checker/{operationId}`.

## Invocation patterns
```bash
/dependency-checker scan --component=payments-service --language=java
/dependency-checker graph --cluster=aks-hub --namespace=payments
/dependency-checker audit --cve=CVE-2026-1234
/dependency-checker plugin --tool=trivy --target=image:latest
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `component` | Service or repo name. | `payments-service` |
| `language` | Language or package manager. | `java` |
| `cluster` | Cluster context. | `aks-hub` |
| `namespace` | Namespace or tenant. | `payments` |
| `cve` | Vulnerability ID. | `CVE-2026-1234` |
| `tool` | Scanner (trivy, grype, snyk). | `trivy` |

## Output contract
```json
{
  "operationId": "DC-2026-0315-01",
  "status": "pass|warn|fail",
  "riskScore": 0.64,
  "findings": [
    { "package": "log4j", "version": "2.0", "cve": "CVE-2026", "severity": "critical" }
  ],
  "logs": "shared-context://memory-store/dependency-checker/DC-2026-0315-01",
  "decisionContext": "redis://memory-store/dependency-checker/DC-2026-0315-01"
}
```

## World-class workflow templates

### SBOM & vulnerability scan
1. Generate SBOM from builds (Maven, npm, pip) and scan with CVE feeds.
2. Tag findings with confidence, business impact, and severity.
3. Command stub: `/dependency-checker scan --component=payments-service --language=java`

### Runtime dependency graph
1. Map service dependencies via OpenTelemetry/tracing graphs.
2. Identify risky service chains or unauthorized packages.
3. Command stub: `/dependency-checker graph --cluster=aks-hub --namespace=payments`

### CVE audit & remediation
1. Focus on high severity CVEs, validate patch availability.
2. Emit `dependency-audit` events and tie to/patch lists.
3. Command stub: `/dependency-checker audit --cve=CVE-2026-1234`

### Automation & plugin hooks
1. Integrate scanners (trivy, grype) and build  pipelines.
2. Pin versions, open PRs, or rerun builds.
3. Command stub: `/dependency-checker plugin --tool=trivy --target=image:latest`

## AI intelligence highlights
- **Risk scoring** merges CVE severity, service criticality, and exposure window.
- **Dependency graph wisdom** flags chains that might propagate faults.
- **Automated remediation** suggests patches, pins, or coordination tasks.

## Memory agent & dispatcher integration
- Store evaluations at `shared-context://memory-store/dependency-checker/{operationId}`.
- Emit events: `dependency-scan`, `dependency-graph`, `dependency-audit`, `dependency-remediation`.
- Listen to dispatcher signals (`incident-ready`, `policy-risk`, `compliance-request`).
- Tag context with `decisionId`, `component`, `severity`, `tool`, `riskScore`.

## Observability & telemetry
- Metrics: scanning frequency, pass rate, remediation latency.
- Logs: structured `log.event="dependency.scan"` with component, severity.
- Dashboards: `/dependency-checker metrics --format=prometheus` for SBOM health.
- Alerts: CVEs unpatched >7 days, graph exposures > threshold.

## Failure handling & retries
- Retry scanner APIs up to 3× when feeds are unavailable.
- On unresolved CVEs route to `incident-triage-runbook` and log context.
- Keep shared context until remediations are acknowledged.

## Human gates
- Required when:
  1. CVEs are critical in production components.
  2. Licensing violations expose customer data.
  3. Dispatcher requests manual oversight after repeated scans.

## Testing & validation
- Dry-run: `/dependency-checker scan --component=test --language=python --dry-run`
- Unit tests: `backend/dependency-checker/` ensures scoring and graph logic.
- Integration: `scripts/validate-dependency-checker.sh` runs scanners vs test images.
- Regression: nightly `scripts/nightly-dependency-smoke.sh` monitors outputs.

## References
- Scripts: `scripts/dependency-checker/`.
- Templates: `templates/dependency/`.
- Monitoring: `monitoring/dependency/`.

## Related skills
- `/compliance-security-scanner`: complements with IaC scans.
- `/policy-as-code`: correlates policy violations with risky dependencies.
- `/incident-triage-runbook`: responds if CVEs surface in production.

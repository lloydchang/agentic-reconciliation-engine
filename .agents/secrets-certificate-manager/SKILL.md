---
name: secrets-certificate-manager
description: >
  Manage secrets, API keys, certificates, and rotation pipelines with AI-guided policies, telemetry, and dispatcher integration.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Secrets & Certificate Manager — World-class Vault Operations Playbook

Handles provisioning, rotation, injection, monitoring, and auditing for secrets and certificates across Azure Key Vault, AWS Secrets Manager, HashiCorp Vault, Kubernetes, and GCP Secret Manager while feeding risk-aware telemetry to orchestrators.

## When to invoke
- Rotate secrets or certificates (API keys, TLS certs, connection strings) on schedule, threat response, or policy change.
- Audit access, detect hardcoded credentials, validate certificates, or migrate secrets stores.
- Respond to dispatcher signals (`policy-risk`, `incident-ready`, `capacity-alert`) that expose new secret/cert dependencies.
- Provision cert-manager and automatically reconcile TLS automation with workloads.

## Capabilities
- **Multi-backend rotation** for Azure Key Vault, AWS Secrets Manager, Vault, Kubernetes, and GCP Secret Manager.
- **AI risk scoring** balancing rotation impact, policy compliance, and exposure to determine automation readiness.
- **Smart remediation ordering** prioritizing critical secrets, automating rotations, and gating with human review when needed.
- **Predictive expiry alerts** with proactive renewals and injection flows for certificates.
- **Shared-context propagation** via `shared-context://memory-store/secrets/{operationId}` for downstream skills.

## Invocation patterns

```bash
/secrets-certificate-manager rotate --secret=db/password --backend=azure --tenant=tenant-42
/secrets-certificate-manager renew --certificate=payments-api-tls --cluster=aks-tenant-42-prod
/secrets-certificate-manager audit --scope=all --backends=keyvault,aws
/secrets-certificate-manager inject --secret=db/password --deployment=payments-api --namespace=tenant-42
/secrets-certificate-manager detect --repo=ai-agent --pattern=hardcoded
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `secret` | Secret/certificate identifier. | `db/password` |
| `backend` | Secret backend (`azure|aws|vault|k8s|gcp`). | `azure` |
| `cluster` | Kubernetes cluster identifier. | `aks-tenant-42-prod` |
| `certificate` | TLS certificate name. | `payments-api-tls` |
| `deployment` | Workload consuming the secret/cert. | `payments-api` |
| `scope` | Audit scope (tenant, repo, all). | `all` |

## Output contract

```json
{
  "operationId": "SEC-2026-0315-01",
  "operation": "rotate|renew|audit|inject|detect",
  "status": "success|partial|failure",
  "backend": "azure",
  "tenant": "tenant-42",
  "riskScore": 0.36,
  "actionedSecrets": ["db/password", "redis/token"],
  "certificatesExpiring": [
    { "name": "payments-api-tls", "expires": "2026-04-10T00:00:00Z" }
  ],
  "hardcodedSecrets": [
    { "path": "infra/api/main.tf", "pattern": "api_key" }
  ],
  "logs": "shared-context://memory-store/secrets/SEC-2026-0315-01",
  "decisionContext": "redis://memory-store/secrets/SEC-2026-0315-01"
}
```

## World-class workflow templates

### Secret rotation pipeline
1. Generate new secrets/certificates using templated generators or CA requests.
2. Store new versions in backend stores (Key Vault/Secrets Manager/Vault) with overlapping versions for rollback.
3. Inject secrets into workloads via CSI drivers, SecretProviderClass, or deployment updates.
4. Emit `secret-rotated` events with rotation metadata for audit/tracing.

### Certificate lifecycle automation
1. Provision cert-manager issuers (ACME, Azure CA, Vault) with `renewBefore` and orientation.
2. Renew certificates per tenant and monitor statuses, triggering auto-renew before expiry.
3. Alert when expiries approach (<30 days) and verify TLS chain health.
4. Emit `certificate-renewed` events so deployment/orchestration skills can re-deploy if needed.

### Hardcoded secret detection & remediation
1. Run scanners (`gitleaks`, `trufflehog`, repo searches) plus Kubernetes manifest audits.
2. Classify findings, escalate critical exposures, and trigger rotations or secret deletions.
3. Emit `hardcoded-secret-detected` events with remediation steps attached.

## AI intelligence highlights
- **AI Risk Assessment** quantifies impact and automation readiness for rotations/cert renewals.
- **Smart Remediation Prioritization** sequences operations by criticality, service dependency, and compliance urgency.
- **Intelligent Violation Analysis** explains exposures (public secrets, missing tags, policy gaps) with actionable remediation steps.
- **Predictive Expiry Alerts** forecast when secrets/certs need rotation before thresholds breach.

## Memory agent & dispatcher integration
- Persist operations at `shared-context://memory-store/secrets/{operationId}` with tags (`decisionId`, `tenant`, `backend`, `riskScore`).
- Emit events: `secret-rotated`, `certificate-renewed`, `secret-detected`, `rotation-required`, `certificate-warning`.
- Subscribe to dispatcher signals (`policy-risk`, `incident-ready`, `capacity-alert`) to reprioritize rotations/injections.
- Provide fallback artifacts via `artifact-store://secrets/{operationId}.json` when event buses are offline.

## Observability & telemetry
- Metrics: rotations per backend, certificate renewals, detection counts, rotation success rate, riskScore trends.
- Logs: structured `log.event="secrets.rotation"` containing `operation`, `tenant`, `backend`, `decisionId`.
- Dashboards: surface `/secrets-certificate-manager metrics --format=prometheus` for vault operations.
- Alerts: riskScore ≥ 0.85, rotation failures >2 in 24h, certificates expiring within 7 days without auto-renew.

## Failure handling & retries
- Retry secret/certificate commands up to 2× on transient API throttling with exponential backoff.
- On rotation failure revert to previous secret version, emit `rotation-failed`, and escalate to incident skills.
- Maintain audit artifacts until downstream acknowledgments confirm safe completion.

## Human gates
- Required when:
  1. Rotations touch production-critical secrets (DB passwords, master keys) or >20 services.
  2. Certificates affect public endpoints or require DNS changes.
  3. Dispatcher demands manual review after repeated failures or policy violations.
- Confirmation template matches the orchestrator standard:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/secrets-certificate-manager rotate --secret=db/password --dry-run`.
- Unit tests: `backend/secrets/` ensures rotation/injection logic and risk scoring operate correctly.
- Integration: `scripts/validate-secrets-rotation.sh` exercises rotation, injection, auditing flows end to end.
- Regression: nightly `scripts/nightly-secrets-smoke.sh` verifies rotation cadence, expiry alerts, and detection thresholds.

## References
- Rotation scripts: `scripts/secrets/`.
- Certificate configs: `cert-manager/`.
- Detection templates: `templates/security-report.md`.

## Related skills
- `/policy-as-code`: validates secrets/certs against governance guardrails.
- `/incident-triage-runbook`: escalates when secrets compromise arises.
- `/workflow-management`: orchestrates rotation/drill workflows.

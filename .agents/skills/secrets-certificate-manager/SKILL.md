---
name: secrets-certificate-manager
description: >
  Manage secrets, API keys, certificates, and rotation pipelines with AI-driven policies, telemetry, and dispatcher integrations.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Secrets & Certificate Manager — World-class Vault Operations Playbook

Handles provisioning, rotation, injection, monitoring, and audit of secrets/certificates across Azure Key Vault, AWS Secrets Manager, HashiCorp Vault, Kubernetes, and GCP Secret Manager. Trigger when rotates, renews, audits, injects, or migrates secrets/certs and whenever policy or dispatcher signals require governance.

## When to invoke
- Rotate secrets or certificates (API keys, passwords, TLS certs) on schedule or upon compromise.
- Audit access, detect hardcoded credentials, validate certificates, or migrate secrets stores.
- Respond to dispatcher signals such as `policy-risk`, `incident-ready`, `capacity-alert` (e.g., secrets used in new infrastructure).
- Provision cert-manager and integrate TLS automation with cluster workloads.

## Capabilities
- Multi-backend support (Azure Key Vault, AWS Secrets Manager, Vault, Kubernetes, GCP Secret Manager).
- AI risk scoring for rotation impacts, policy compliance, and disclosure exposure.
- Smart remediation ordering (VIP secrets first, automated rotation scripts).
- Predictive expiry alerts, certificate renewal automation, and audit trail ingestion.
- Shared context integration `shared-context://memory-store/secrets/<operationId>` for other skills.

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
| `backend` | Secret backend (azure|aws|vault|k8s|gcp). | `azure` |
| `cluster` | Kubernetes cluster identifier. | `aks-tenant-42-prod` |
| `certificate` | TLS certificate name. | `payments-api-tls` |
| `deployment` | Workload that consumes secret/cert. | `payments-api` |
| `scope` | Scope for audits (tenant, repo, all). | `all` |

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
1. Generate new secret via templated generator; validate with safe rollout (service health).
2. Store new version in backend (Key Vault/Secrets Manager/Vault), keep overlapping versions for rollback.
3. Inject secret into workloads (DFS operator, CSI driver) and trigger restarts as necessary.
4. Emit `secret-rotated` event and log rotation metadata for auditing.

### Certificate lifecycle automation
1. Provision cert-manager issuers (Let's Encrypt, Azure DNS, Vault CA).
2. Create/renew certificates per tenant, set `renewBefore`, and monitor status.
3. Alert when expiry within threshold (<30 days) and auto-renew.
4. Emit `certificate-renewed` events for dispatcher downstream.

### Hardcoded secret detection & remediation
1. Run `gitleaks`, `trufflehog`, repo scans, and Kubernetes secret pattern checks.
2. Classify findings, escalate high-risk detections, trigger rotations, and open tickets.
3. Emit `hardcoded-secret-detected` events and link to remediation tasks.

## AI intelligence highlights
- **AI Risk Assessment**: evaluates rotation impact, compliance, and production exposure to determine `riskScore`.
- **Smart Remediation Prioritization**: sequences rotations/cert renewals by criticality and service dependencies.
- **Intelligent Violation Analysis**: explains exposure (missing tags, public secrets) with suggestions.
- **Predictive Expiry Alerts**: forecasts certificate expiration and secret rotation needs.

## Memory agent & dispatcher integration
- Store operations under `shared-context://memory-store/secrets/<operationId>` for other agents.
- Emit events: `secret-rotated`, `certificate-renewed`, `secret-detected`, `rotation-required`.
- Subscribe to dispatcher signals (`policy-risk`, `incident-ready`, `capacity-alert`) to adjust rotation priority.
- Tag metadata with `decisionId`, `tenant`, `backend`, `riskScore`.

## Communication protocols
- Primary: CLI commands (az keyvault, aws secretsmanager, vault, kubectl, kubeseal) producing JSON output.
- Secondary: Event bus for `secrets-*` events consumed by dispatchers.
- Fallback: Persist JSON artifacts to `artifact-store://secrets/<operationId>.json`.

## Observability & telemetry
- Metrics: rotations per backend, certificate renewals, hardcoded discovery counts, rotation success rate, riskScore trend.
- Logs: structured `log.event="secrets.rotation"` containing `operation`, `tenant`, `backend`, `decisionId`.
- Dashboards: integrate `/secrets-certificate-manager metrics --format=prometheus` for vault operations.
- Alerts: riskScore ≥ 0.85, rotation failure > 2 in 24h, certificates expiring < 7 days without auto-renew.

## Failure handling & retries
- Retry secret/cert operations up to 2× on transient failures (API throttling) with exponential backoff.
- On rotation failure, revert to previous secret version and emit `rotation-failed`.
- Maintain audit trails/artifacts until downstream acknowledgements; do not delete immediately.

## Human gates
- Required when:
 1. Rotation affects production-critical secrets (DB passwords, master keys) or >20 services.
 2. Certificates impact public endpoints or require DNS changes.
 3. Dispatcher flags manual review after repeated failures or policy violations.
- Use standard human gate confirmation template.

## Testing & validation
- Dry-run: `/secrets-certificate-manager rotate --secret=db/password --dry-run`.
- Unit tests: `backend/secrets/` verifies rotation logic and risk scoring.
- Integration: `scripts/validate-secrets-rotation.sh` exercises rotation, injection, auditing flows.
- Regression: nightly `scripts/nightly-secrets-smoke.sh` ensures rotation cadence, expiry alerts, detection thresholds stay stable.

## References
- Rotation scripts: `scripts/secrets/`.
- Certificate configs: `cert-manager/`.
- Detection templates: `templates/security-report.md`.

## Related skills
- `/policy-as-code`: ensures secrets/certs comply with governance.
- `/incident-triage-runbook`: escalates when secrets compromise detected.
- `/workflow-management`: orchestrates rotation/drill workflows.

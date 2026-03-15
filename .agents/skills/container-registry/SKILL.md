---
name: container-registry
description: >
  Manage container registries, image promotion, scanning, signing, and governance with AI guidance and dispatcher telemetry.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Container Registry — World-class Supply Chain Playbook

Controls image lifecycle across dev/staging/prod registries (ACR, ECR, GCR, Harbor) with scanning/signing, promotion, retention, and access controls. Trigger for provisioning, vulnerability scanning, signing, promotion, cleanup, or audit/shielding requests.

## When to invoke
- Provision registries with geo-replication and private network access.
- Scan images (trivy/cosign) pre-push or continuously.
- Sign images, enforce policies, and promote from staging to prod.
- Clean up stale images and report registry usage.
- Respond to dispatcher alerts (`policy-risk`, `incident-ready`, `capacity-alert`) tied to image usage or CVE exposure.

## Capabilities
- Multi-tier registry architecture with scanning/promotions.
- AI risk scoring for image promotions or scans (CVE criticality, policy violations).
- Smart remediation (block, require re-scan, auto-rotate tags) and supply chain proofing.
- Shared context `shared-context://memory-store/registry/<operationId>` for other skills.
- Human-gated promotions or policy violations.

## Invocation patterns

```bash
/container-registry provision --registry=prod --region=eastus --tier=premium
/container-registry scan --image=tenant-app:v2.3.1 --severity=critical
/container-registry sign --image=prod-registry.azurecr.io/tenant-app:v2.3.1 --backend=notation
/container-registry promote --source=staging-registry --dest=prod-registry --image=tenant-app --tag=v2.3.1
/container-registry audit --scope=production --policy=signature
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `registry` | Registry alias (`dev-registry`, `prod-registry`). | `prod-registry` |
| `image` | Image reference (registry/app:tag). | `tenant-app:v2.3.1` |
| `severity` | CVE severities to fail on. | `critical` |
| `backend` | Signing backend (notation/cosign). | `notation` |
| `source` | Source registry for promotion. | `staging-registry` |
| `policy` | Policy to audit (signature, policy-as-code). | `signature` |

## Output contract

```json
{
  "operationId": "REG-2026-0315-01",
  "operation": "provision|scan|sign|promote|purge|audit",
  "status": "success|failure",
  "image": "tenant-app:v2.3.1",
  "registry": "prod-registry",
  "riskScore": 0.45,
  "scanResult": {
    "critical": 0,
    "high": 1,
    "medium": 2
  },
  "signed": true,
  "promotionStatus": "approved",
  "issues": [],
  "decisionContext": "redis://memory-store/registry/REG-2026-0315-01",
  "logs": "shared-context://memory-store/registry/REG-2026-0315-01"
}
```

## World-class workflow templates

### Registry provisioning & hardening
1. Provision registry (ACR/ECR/GCR) with private endpoints, geo-replication, and access policies.
2. Set up scanning tasks, retention policies, and event subscriptions for CVE alerts.
3. Emit `registry-provisioned` event with control-plane metadata.

### Scanning, signing, and promotion
1. Perform vulnerability scan (trivy/grype) pre-push or scheduled.
2. Evaluate AI risk score (CVE severities, exposure, dependencies) and human gate for critical fixes.
3. Sign images (notation/cosign) using vault-stored keys, enforce Gatekeeper policies.
4. Promote approved images to prod, re-sign, quarantine old tags, and emit `image-promoted`.

### Lifecycle/retention and auditing
1. Purge stale/untagged images based on retention policies.
2. Audit running images vs approved list; check signature status.
3. Emit `registry-audit` event logging compliance posture.

## AI intelligence highlights
- **AI Risk Scoring**: combines CVE severity, dependency risk, and policy scores to decide gating/human approval.
- **Smart Remediation**: suggests blocker vs continue actions, outlines effort/impact (e.g., rebase, re-scan).
- **Predictive Supply Chain Alerts**: forecasts CVE churn to notify registries needing scans.

## Memory agent & dispatcher integration
- Store scan/sign/promotion metadata in `shared-context://memory-store/registry/<operationId>`.
- Emit events: `registry-scanned`, `image-signed`, `image-promoted`, `registry-audit`.
- Subscribe to dispatcher alerts (`policy-risk`, `incident-ready`, `capacity-alert`) to adjust promotions or scanning urgency.
- Tag records with `decisionId`, `tenant`, `image`, `riskScore`.

## Communication protocols
- Primary: CLI commands (az acr, aws ecr, gcloud) and scanning tools outputting JSON.
- Secondary: Event bus for `registry-*` events consumed by dispatcher and other skills.
- Fallback: Artifact store entries (`artifact-store://registry/<operationId>.json`) for offline processing.

## Observability & telemetry
- Metrics: scans per window, critical findings, promotion success rate, rotation actions, riskScore distribution.
- Logs: structured `log.event="registry.operation"` with `operation`, `image`, `decisionId`.
- Dashboards: integrat `/container-registry metrics --format=prometheus`.
- Alerts: riskScore ≥ 0.85, critical vulnerabilities > 0, promotion blocked > 2 in 1h.

## Failure handling & retries
- Retry scans/sign/promotion up to 2× on transient errors (API throttling, network).
- On failure, emit `registry-operation-failed`, retain logs, notify `incident-triage-runbook`.
- Preserve shared-context entries until downstream ack for audit.

## Human gates
- Required when:
 1. riskScore ≥ 0.7 or blocking critical CVEs.
 2. Promotion affects production/regulatory workloads.
 3. Dispatcher requests manual review after retries/failures.
- Use standard human gate template.

## Testing & validation
- Dry-run: `/container-registry scan --image=test-app:latest --dry-run`.
- Unit tests: `backend/registry/` ensures scan/promotion parser and risk scoring.
- Integration: `scripts/validate-registry-stream.sh` runs scan → sign → promote flows.
- Regression: nightly `scripts/nightly-registry-smoke.sh` ensures CVE detection accuracy and promotion gating.

## References
- Provisioning guides: `infrastructure/registry/`.
- Scanning tools: `scripts/registry/trivy`.
- Signing policies: `policy-as-code`.

## Related skills
- `/policy-as-code`: ensures signature/scan compliance.
- `/incident-triage-runbook`: handles critical image findings.
- `/ai-agent-orchestration`: orchestrates registry workflows with other skills.

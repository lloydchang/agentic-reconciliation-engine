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

Controls image lifecycle across dev/staging/prod registries (ACR, ECR, GCR, Harbor) with scanning, signing, promotions, and retention while feeding proofs to orchestrators.

## When to invoke
- Provision registries with geo-replication, private endpoints, and access policies.
- Perform vulnerability scans, signing, or promotions for container images.
- Clean up stale images, audit usage, or enforce supply chain policies.
- Respond to dispatcher signals (`policy-risk`, `incident-ready`, `capacity-alert`) tied to CVEs or image risks.

## Capabilities
- **Multi-tier registry architecture** across cloud providers plus Harbor/private registries.
- **AI risk scoring** for scans/promotions that fuse CVE severity, dependency risk, and policy impact.
- **Smart remediation & gating** (block, rebase, re-scan) with human gate integration for critical workflows.
- **Certificate-based signing & promotion** across notations/cosign/vault-signed keys.
- **Shared-context propagation** at `shared-context://memory-store/registry/{operationId}` for downstream skills.

## Invocation patterns

```bash
/container-registry provision --registry=prod --region=eastus --tier=premium
/container-registry scan --image=tenant-app:v2.3.1 --severity=critical
/container-registry sign --image=prod-registry.azurecr.io/tenant-app:v2.3.1 --backend=notation
/container-registry promote --source=staging --dest=prod --image=tenant-app --tag=v2.3.1
/container-registry audit --scope=production --policy=signature
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `registry` | Registry alias (`dev-registry`, `prod-registry`). | `prod-registry` |
| `image` | Image reference (registry/app:tag). | `tenant-app:v2.3.1` |
| `severity` | CVE severity threshold to fail on. | `critical` |
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
  "scanResult": {"critical": 0, "high": 1, "medium": 2},
  "signed": true,
  "promotionStatus": "approved",
  "issues": [],
  "decisionContext": "redis://memory-store/registry/REG-2026-0315-01",
  "logs": "shared-context://memory-store/registry/REG-2026-0315-01"
}
```

## World-class workflow templates

### Registry provisioning & hardening
1. Provision cloud/private registries with private network access, geo-replication, event subscriptions, and retention policies.
2. Configure continuous scanning, signing, and webhook callbacks.
3. Emit `registry-provisioned` events with control-plane metadata and link to shared context.

### Scanning, signing, and promotion
1. Scan images with Trivy/Grype before push or on schedule.
2. Calculate AI risk score (CVEs, exposure, dependency graphs) and require human gate when riskScore ≥ 0.7.
3. Sign images with Notation/Cosign backed by vault-managed keys; enforce policy-as-code rules.
4. Promote approved images through registries, re-sign tags, quarantine old versions, and emit `image-promoted`.

### Lifecycle governance & audit
1. Purge stale/untagged images per retention policy.
2. Audit running deployments vs approved images and signatures.
3. Emit `registry-audit` and forward findings to incident or policy skills if issues surface.

## AI intelligence highlights
- **AI Risk Scoring** fuses CVE severity, dependency reachability, and policy compliance to adjust gating.
- **Smart Remediation** recommends blocker actions (rebase, rebuild) vs continuing with warnings.
- **Predictive Supply Chain Alerts** forecast CVE churn and flag registries needing rescans.

## Memory agent & dispatcher integration
- Persist scan/promotion metadata at `shared-context://memory-store/registry/{operationId}`.
- Emit events: `registry-scanned`, `image-signed`, `image-promoted`, `registry-audit`, `registry-alert`.
- Subscribe to dispatchers (`policy-risk`, `incident-ready`, `capacity-alert`) to reprioritize actions.
- Tag records with `decisionId`, `tenant`, `image`, `riskScore`.

## Observability & telemetry
- Metrics: scans per window, CVE findings, promotion success rate, rotation actions, riskScore trends.
- Logs: structured `log.event="registry.operation"` capturing `operation`, `image`, `decisionId`.
- Dashboards: include `/container-registry metrics --format=prometheus` for pipeline health.
- Alerts: riskScore ≥ 0.85, critical CVEs > 0, promotions blocked > 2/hour.

## Failure handling & retries
- Retry scans/sign/promotions up to 2× on transient API throttling.
- On failure emit `registry-operation-failed`, keep logs, notify `incident-triage-runbook`, and retain artifacts for audit.
- Preserve shared-context entries until downstream acknowledgement completes the audit trail.

## Human gates
- Required when:
  1. riskScore ≥ 0.7 or critical CVEs exist.
  2. Promotions touch production or highly regulated workloads.
  3. Dispatcher requests manual review after retries/failures.
- Template matches orchestrator gate format:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/container-registry scan --image=test-app:latest --dry-run`.
- Unit tests: `backend/registry/` validates scan/promotion parsing and risk scoring.
- Integration: `scripts/validate-registry-stream.sh` runs scan → sign → promote flows.
- Regression: nightly `scripts/nightly-registry-smoke.sh` ensures CVE detection accuracy and gating.

## References
- Provisioning guides: `infrastructure/registry/`.
- Scanning tools: `scripts/registry/trivy`.
- Signing policies: `policy-as-code`.

## Related skills
- `/policy-as-code`: enforces signature/scan compliance.
- `/incident-triage-runbook`: handles critical image findings.
- `/ai-agent-orchestration`: choreographs registry workflows across skills.

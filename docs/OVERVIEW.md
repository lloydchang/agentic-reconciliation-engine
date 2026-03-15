# Control Plane overview

## Core advantage

Traditional IaC tools run once and exit, whereas this control plane enforces state continuously using Kubernetes controllers: Flux, Crossplane, and Cluster API. Spokes pull Git config directly, fetch secrets via ESO, and survive hub outages because they run autonomously.

| Approach | Traditional IaC | Continuous Reconciliation |
|---|---|---|
| Operation | Run once → exit | Monitor 24/7 → automatic drift correction |
| Drift detection | Manual `plan` runs | Automatic within minutes |
| Multi-cloud API | Per-provider CLI/SDK (Terraform, AWS CDK, CloudFormation, Azure Bicep, ARM, GCP Terraform Blueprints) | Unified Crossplane Composite Resource Definitions (XRDs) |
| Spoke resilience | N/A | Spokes run on last-applied state during hub outage |

GitOps enforces drift correction using a Git repository as the source of truth, a CI policy gate, and Flux bootstrapping. The architecture begins with a bootstrap cluster that brings up a HA hub, which then provisions and reconciles spokes across EKS, AKS, GKE, and on-prem. Crossplane XRDs let platform owners define cloud-agnostic resources once and let developers consume them in YAML without managing provider differences.

Secrets strategy uses ESO+workload identity (IRSA/Managed Identity/Workload Identity Federation) for cloud vault access and falls back to SOPS/age on-prem. A deletion guard and schema validation run in the CI gate; the hub includes HA recovery via etcd backups and a bootstrap recovery anchor.

## When to use this solution

- Multi-cloud deployments facing drift incidents or audit pressure.
- Managed hub control planes (EKS/AKS/GKE) where you operate controllers.
- Teams with Kubernetes operations depth to interpret CRD status fields.
- Brownfield consolidation projects where the upfront investment pays off.

Avoid this architecture for single-cloud/single-region setups, teams lacking Kubernetes expertise, emergency migrations, or when multi-cloud drift issues are not yet pressing.

## Key features

- Continuous reconciliation via Flux per hub/spoke.
- Cloud-agnostic Crossplane resource model (XDatabase, XNetwork, XCluster, etc.).
- Spoke autonomy: each spoke runs Flux + ESO and replays secrets locally.
- Cluster lifecycle using Cluster API providers (Kubeadm, Metal3, CAPV, CAPO).
- Per-spoke secret isolation via ESO and workload identity.
- Pre-merge safety gate with policy checks, deletion guards, and schema validation.
- Hub recovery anchor using a bootstrap cluster and regular etcd backups.

## Documentation surface

### Essential reading
1. [Problem-Solution Fit](./PROBLEM-SOLUTION-FIT.md)
2. [Architecture](./ARCHITECTURE.md)
3. [Implementation Plan](./implementation_plan.md)
4. [Implementation Summary](./implementation-summary.md)
5. [Execution Checklist](./EXECUTION-CHECKLIST.md)

### Operations
Refer to the individual docs for hub recovery, compositions, ESO, CI gate, controller runbooks, and platform compatibility. See the quicklinks in the README or the dedicated compatibility guides (`WINDOWS`, `MAC`, `LINUX`, `SHELL`, `AGENT-CLIENTS`).

### Implementation examples
- [Complete Hub-Spoke](../examples/complete-hub-spoke/)
- [Crossplane Compositions](../examples/crossplane-compositions/)
- [ESO Per Spoke](../examples/eso-workload-identity/)
- [Variants](../variants/)

### Zero-touch automation

- `scripts/run-local-automation.sh` runs bootstrap → migration wizard → CI gate and stores logs under `logs/local-automation/`.
- `scripts/run-emulator-then-cloud.sh` lets you run the migration wizard twice (`--emulator=enable` then `--emulator=disable`).
- Use `.github/workflows/run-local-automation.yml` or `azure-pipelines-zero-touch.yml` to trigger the wrapper in CI; both pipelines publish the `logs/local-automation/` summary and optionally call `scripts/publish-summary.sh`.
- Override connectors/overlays via CLI arguments for the wizard or pass `SUMMARY_ENDPOINT`/`NOTIFY_WEBHOOK` to `scripts/publish-summary.sh`.

## Comparison with managed alternatives

| Product | Covers | What you still own |
|---|---|---|
| GKE Enterprise / Anthos | Multi-cluster GitOps, policy, secrets, config sync | GCP-centric; cross-cloud requires agents |
| Azure Arc | Azure + connected K8s, GitOps, policy | Azure-centric; AWS/GCP limited |
| EKS Anywhere | On-prem EKS with Flux GitOps | AWS-centric; no native Azure/GCP |
| Crossplane only | Cloud resource management, unified XRDs | No cluster lifecycle, no fleet GitOps |
| This control plane | Full multi-cloud, self-hosted, cluster + resource lifecycle | Upfront adoption cost; you own the controllers |

## Known limitations

- No full planning equivalent: the CI gate validates but does not diff current cloud state.
- Crossplane Composition authoring requires upfront investment before spoke teams can use XRDs.
- Multi-cluster progressive rollout requires external coordination; Flux + CAPI do not provide rollout gating equivalent to single-cluster progressive delivery.
- CAPI provisions a minimal cluster; add CNI, CSI, ingress, autoscaler, and monitoring via spoke Flux separately.
- On-prem spoke infra provider selection (Metal3, CAPV, CAPO) depends on hardware.
- Flux+SOPS integration has documented edge-case decryption failures; SOPS is a fallback only when ESO/workload identity is unavailable.

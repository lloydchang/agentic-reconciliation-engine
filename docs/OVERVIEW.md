# GitOps Infra Control Plane

Continuous Reconciliation Engine (CRE) for Multi-Cloud Infrastructure

## Core Advantage

Traditional IaC tools (Terraform, CDK, CloudFormation, Bicep, ARM) run once and exit. They do not
continuously enforce infrastructure state. Kubernetes operators — Crossplane with provider-aws,
provider-azure, and provider-gcp — provide 24/7 continuous reconciliation that detects and repairs
configuration drift automatically. Each spoke cluster runs its own Flux agent and pulls secrets
directly from cloud vaults, so spoke operations continue independently even during hub maintenance
or failure.

| Approach | Traditional IaC | Continuous Reconciliation |
|---|---|---|
| Operation | Run once → exit | Monitor 24/7 → automatic drift correction |
| Drift detection | Manual `plan` runs | Automatic within minutes |
| Multi-cloud API | Per-provider CLI/SDK (Terraform, AWS CDK, CloudFormation, Azure Bicep, ARM, GCP Terraform Blueprints) | Unified Crossplane Composite Resource Definitions (XRDs) |
| Spoke resilience | N/A | Spokes run on last-applied state during hub outage |

Note: Terraform fits under the "Per-provider CLI/SDK" column because it is a traditional IaC tool that:
- Interacts directly with each cloud provider via plugins
- Runs as a CLI tool using HCL configurations
- Requires explicit `plan` and `apply` for state enforcement
- Does not generate Crossplane XRDs or provide continuous reconciliation. In this architecture, Terraform is useful for initial provisioning or migration but ongoing multi-cloud AI rely on Crossplane and Flux for automated drift detection and correction.

GitOps enforces configuration drift correction by using a Git repository as the declarative source
of truth. A CI (Continuous Integration) policy gate validates and guards all changes before merge.
Flux reconciles the hub and bootstraps each spoke. This enables **automatic drift reconciliation**,
not full operational self-healing, because runtime failures outside Git-managed resources are
handled by Kubernetes controllers and platform automation separately.

![hub spoke diagram](hub_spoke_v5.svg)

```text
[Tier 0]      Git repository — declarative source of truth
                   |
                   |  Pull request
                   v
[CI]          CI policy gate (Conftest / OPA)
              · Schema validation (kubeconform)
              · Deletion guard: stateful XRDs require explicit approval annotation
              · Policy checks: naming, tagging, cost guardrails
                   |
                   |  Merge to main
                   v
              +-----------------------------------------------+
              | Bootstrap cluster (lightweight, 1–3 nodes)    |
              | k3s or small managed cluster                  |
              | · Holds hub bootstrap config and manifests    |
              | · Runs hub etcd backup schedule               |
              | · Provides cold-start recovery anchor         |
              +-----------------------------------------------+
                   | bootstraps hub once; monitors hub health
                   v
         +--------------------------------------------------------------------------+
[Tier 1] |                         Hub cluster (HA)                                 |
         |  Any Kubernetes distribution · 3+ control plane nodes across AZs         |
         |  etcd backup to object storage · Flux self-manages hub after bootstrap   |
         |--------------------------------------------------------------------------|
     _->-+--+------------------+  +------------------------------+  +------------+  |
    /    |  | Flux             |  | Crossplane                   |  | CAPI       |  |
   /     |  | GitOps reconcile |  | Unified XRDs (cloud-agnostic)|  | Spoke      |  |
   |     |  | Git → hub        |  | XDatabase, XNetwork, etc.    |  | lifecycle  |  |
    \    |  | Bootstraps spoke |  | provider-aws                 |  | Kubeadm    |  |
     `---+--| Flux + ESO       |  | provider-azure               |  | Metal3     |  |
         |  | agents via CAPI  |  | provider-gcp                 |  | CAPV/CAPO  |  |
         |  +------------------+  +------------------------------+  +------------+  |
         +--------------------------------------------------------------------------+
                  |                        |                          |
                  | Flux bootstraps        | Crossplane creates       | CAPI provisions
                  | spoke Flux + ESO       | cloud resources          | cluster lifecycle
                  v                        v                          v
         +--------------------------------------------------------------------------+
[Tier 2] |                          Spoke clusters                                  |
         |  Each spoke is operationally independent                                 |
         |  · Flux agent pulls config from Git directly (pull model)                |
         |  · ESO pulls secrets from cloud vault via workload identity              |
         |  · Hub outage does not pause spoke reconciliation or secret delivery     |
         |--------------------------------------------------------------------------|
         |  +----------+  +----------+  +----------+  +----------------------+      |
         |  | EKS      |  | AKS      |  | GKE      |  | Kubeadm / on-prem    |      |
         |  | IRSA     |  | Managed  |  | Workload |  | HashiCorp Vault /    |      |
         |  | → AWS SM |  | Identity |  | Identity |  | external vault       |      |
         |  |          |  | → AKV    |  | → GCP SM |  |                      |      |
         |  | Flux     |  | Flux     |  | Flux     |  | Flux                 |      |
         |  | ESO      |  | ESO      |  | ESO      |  | ESO                  |      |
         |  +----------+  +----------+  +----------+  +----------------------+      |
         +--------------------------------------------------------------------------+

Cloud-agnostic resource model (Crossplane Compositions):
  - Platform team defines XRDs once: XDatabase, XNetwork, XQueue, XCluster, etc.
  - Developers write cloud-agnostic YAML; cloud is an implementation detail
  - Crossplane Compositions translate XRDs to provider-specific managed resources
  - Switching cloud providers requires updating one Composition, not consumer manifests

Secrets strategy - External Secrets Operator (ESO) + workload identity, primary):
  - Each spoke authenticates to its cloud vault using native workload identity
    · EKS:     IRSA → AWS Secrets Manager (AWS SM)
    · AKS:     Azure Managed Identity → Azure Key Vault (AKV)
    · GKE:     Workload Identity Federation → GCP Secret Manager (GCP SM)
    · On-prem: OIDC / HashiCorp Vault
  - Hub is not in the secrets path; hub outage does not affect secret delivery
  - Spoke secret access is scoped by cloud IAM per spoke, not by network access to hub
  - Secret rotation handled by vault; no re-encrypt-and-commit cycle

Secrets strategy - Secrets OPerationS (SOPS) / age, fallback:
  - Retained for on-prem spokes and secrets with no natural cloud vault home
  - Back up the SOPS age private key to a cloud key vault
  - Flux decrypts at apply time on hub; spokes receive plain Secret objects
  - Use only where ESO + workload identity is not available

CI policy gate:
  - Deletion guard: removing a stateful XRD
    XDatabase, XVolume- without an explicit platform.example.com/allow-deletion
    annotation fails CI and cannot be merged
  - Schema validation: kubeconform against current Crossplane XRD schemas
  - Policy checks: naming conventions, required tags, cost guardrail flags
  - Not a full terraform plan equivalent; does not diff current cloud state

Hub HA and recovery:
  - 3+ control plane nodes across availability zones
  - etcd backup to object storage on schedule; verify restores quarterly
  - Bootstrap cluster holds hub manifests and recovery procedure
  - Hub cold-start: provision replacement cluster → restore from bootstrap cluster config
    → Crossplane and CAPI resume; spoke clusters and secrets unaffected
  - Circular dependency: Flux manages the hub cluster it runs on (by design)
    · Bootstrap cluster provides the external recovery anchor for this case

SOPS fallback age key: back up to cloud key vault → Flux decrypts at apply time (hub-only)
                     → on-prem spokes receive plain Secret objects without requiring a controller
```

## When to Use This Solution

The premise of this architecture is to *reduce* human toil, not to create a permanent staffing
obligation. In steady state, Flux, Crossplane, and CAPI reconcile continuously with no human
involvement. The hub is a managed Kubernetes control plane — EKS, AKS, or GKE — so the cloud
provider operates the control plane nodes. Humans intervene for incidents and planned upgrades,
the same as any other managed service.

The real cost is front-loaded: getting the hub stood up, authoring the initial Crossplane
Compositions, configuring CAPI providers, and wiring per-spoke ESO workload identity takes
focused engineering time. The right question is whether that upfront investment pays off against
the problem you are solving.

### Good Fit
- Multi-cloud infrastructure (2+ clouds in production) where configuration drift is already
  causing production incidents, manual remediation, or audit failures
- Environments where the hub runs on a managed Kubernetes control plane (EKS, AKS, GKE) — the
  cloud provider operates the nodes; you operate what runs on them
- Teams with existing Kubernetes operational depth who can read controller logs and CRD status
  fields when a reconcile loop stalls
- Brownfield environments consolidating from multiple IaC tools where eliminating ongoing manual
  drift remediation justifies the upfront adoption cost

### Not a Good Fit
- Single-cloud or single-region deployments — GKE Enterprise, Azure Arc, and EKS Anywhere cover
  most of this at lower adoption cost; evaluate them first
- Environments without Kubernetes operational depth — failure modes of stuck controllers are
  opaque without it, and the adoption phase will take significantly longer than estimated
- Emergency migrations without runway — this is a target state architecture, not a migration tool
- Environments where the problem being solved (drift, multi-cloud coordination) does not yet
  exist at a scale that justifies the upfront adoption investment

> Important: Complete the [Problem-Solution Fit Assessment](./docs/PROBLEM-SOLUTION-FIT.md)
> before implementation.

## Key Features

- Continuous Reconciliation: 24/7 drift detection and correction via Flux on hub and per spoke
- Cloud-Agnostic Resource Model: Crossplane XRDs abstract AWS, Azure, and GCP behind one API
- Spoke Autonomy: each spoke pulls from Git and cloud vaults independently of the hub
- Cluster Lifecycle Management: Cluster API with Kubeadm, Metal3, CAPV, and CAPO providers
- Per-Spoke Secret Isolation: ESO + workload identity; hub not in the secrets delivery path
- Pre-Merge Safety Gate: deletion guard, schema validation, and OPA policy checks in CI
- Hub Recovery Anchor: secondary bootstrap cluster for cold-start and etcd backup

## Documentation

### Essential Reading
1. [Problem-Solution Fit](./docs/PROBLEM-SOLUTION-FIT.md) - When and how to use this solution
2. [Architecture](./docs/ARCHITECTURE.md) - Technical architecture including Crossplane Compositions
3. [Implementation Plan](./docs/implementation_plan.md) - Step-by-step deployment guide
4. [Implementation Summary](./docs/implementation-summary.md) - Current repo implementation map
5. [Execution Checklist](./docs/EXECUTION-CHECKLIST.md) - Apply and validate sequence

### Operations
- [Hub HA and Recovery](./docs/HUB-HA-RECOVERY.md) - Hub failure modes and cold-start recovery
- [Bootstrap Cluster Setup](./docs/BOOTSTRAP-CLUSTER.md) - Secondary cluster configuration
- [Crossplane Compositions](./docs/CROSSPLANE-COMPOSITIONS.md) - Authoring guide for platform teams
- [ESO Workload Identity](./docs/ESO-WORKLOAD-IDENTITY.md) - Per-spoke secret delivery setup
- [CI Policy Gate](./docs/CI-POLICY-GATE.md) - Deletion guard, schema validation, OPA policies
- [Controller Runbooks](./docs/CONTROLLER-RUNBOOKS.md) - Per-controller failure playbooks
- [Windows Compatibility Guide](./docs/WINDOWS-COMPATIBILITY.md) - How to run this repo with WSL/Git Bash so it works the same on Windows, macOS, and Linux; now explains the automatic WSL detection helper and the Linux (Codespaces/VM) fallback when WSL can't be enabled
- [Agent clients & Azure support](./docs/AGENT-CLIENTS.md) - Azure’s Claude Code-first experience, the additional quick-start for Windows, and the secondary Codex option backed by Azure OpenAI/Foundry

### Implementation Examples
- [Complete Hub-Spoke](./examples/complete-hub-spoke/) - Full deployment with all features
- [Crossplane Compositions](./examples/crossplane-compositions/) - XDatabase, XNetwork, XCluster
- [ESO Per Spoke](./examples/eso-workload-identity/) - IRSA, Managed Identity, Workload Identity
- [Variants](./variants/) - Deployment variations for different scenarios

### Advanced Topics
- [AI Integration](./docs/AI-INTEGRATION-ANALYSIS.md) - Experimental automation patterns (research only)
- [Migration Strategy](./docs/LEGACY-IAC-MIGRATION-STRATEGY.md) - Converting from traditional IaC
- [Migration Wizard Architecture](./docs/MIGRATION-WIZARD-ARCHITECTURE.md) - Modular orchestrator for overlay ordering and multi-host connectors
- [Azure DevOps Connector](./docs/MIGRATION-WIZARD-ARCHITECTURE.md#core-components) - Use the connector with `AZURE_DEVOPS_TOKEN`, `AZURE_DEVOPS_ORG`, `AZURE_DEVOPS_PROJECT`, and the Azure CLI to push migration branches/PRs via the wizard.
- [GitHub Enterprise Server Connector](./docs/MIGRATION-WIZARD-ARCHITECTURE.md#core-components) - Supplies `GITHUB_ENTERPRISE_TOKEN` + `GITHUB_ENTERPRISE_HOST` and uses `gh pr create` for PR automation.
- [GitHub Enterprise Cloud Connector](./docs/MIGRATION-WIZARD-ARCHITECTURE.md#core-components) - Use this connector even when you just use `github.com`; it is the same SaaS service (Enterprise Cloud), so set `GITHUB_ENTERPRISE_TOKEN` and run `gh pr create`.
- [GitLab Connector](./docs/MIGRATION-WIZARD-ARCHITECTURE.md#core-components) - Supplies `GITLAB_TOKEN` (plus optional `GITLAB_HOST`) and hits the GitLab merge request API.
- [GitLab on Google Cloud](./docs/MIGRATION-WIZARD-ARCHITECTURE.md#core-components) - Set `GITLAB_HOST` to your Google Cloud hosted GitLab instance along with `GITLAB_TOKEN`.
- [Bitbucket Data Center Connector](./docs/MIGRATION-WIZARD-ARCHITECTURE.md#core-components) - Supplies `BITBUCKET_DC_HOST`, `BITBUCKET_DC_USER`, `BITBUCKET_DC_TOKEN`, and uses the Bitbucket REST API for PRs.
- [Bitbucket Cloud Connector](./docs/MIGRATION-WIZARD-ARCHITECTURE.md#core-components) - Supplies `BITBUCKET_USER`+`BITBUCKET_TOKEN` and uses the Bitbucket Cloud PR API.
- [AWS CodeCommit Connector](./docs/MIGRATION-WIZARD-ARCHITECTURE.md#core-components) - Uses the standard HTTPS git helper; PRs must be opened via the AWS console because there is no unified CLI for it.
- [GCP Secure Source Manager Connector](./docs/MIGRATION-WIZARD-ARCHITECTURE.md#core-components) - Uses the gcloud git credential helper; clone/push run via git and PRs opened through the Cloud Console.
- [Open Console PR Helper](./scripts/open-gh-console-pr.sh) - After connectors that can’t create PRs spin up (CodeCommit, Secure Source Manager), this script prints the AWS or GCP console URL for manual PR creation.
- [Open Console PR Helper](./scripts/open-gh-console-pr.sh) - Prints the AWS CodeCommit or GCP Secure Source Manager console URL so you can create the pull request manually.
- [Apply Overlay Order Helper](./scripts/apply-overlay-order.sh) - Reorders `control-plane/flux/kustomization.yaml` per `control-plane/flux/overlay-order.txt`.
- [Overlay Logician](./scripts/overlay-logician.py) - Validates that every ordered overlay exists before you run the migration wizard.
- [Emulator Follow-On Runner](./scripts/run-emulator-then-cloud.sh) - Runs `scripts/migration_wizard.py` twice: first with `--emulator=enable`, then `--emulator=disable` so you can validate the local emulator before the real overlay takes over.
- [Zero-Touch Azure Emulator Run](./scripts/run-local-automation.sh) - Executes `scripts/bootstrap.sh` and then `scripts/migration_wizard.py` with `--connector=github`, `--overlay-order=bootstrap hub emulator-azure spoke-local`, and `--emulator=azure` so you can validate the workflow entirely on your Azure emulator/GitHub mirror without pressing any buttons.
- [Windows Compatibility Guide](./docs/WINDOWS-COMPATIBILITY.md) - How to run this repo with WSL/Git Bash so it works the same on Windows, macOS, and Linux.
- [macOS Compatibility Guide](./docs/MAC-COMPATIBILITY.md) - Install Homebrew/Python/Flux and run every script from your Terminal shell for zero-touch verification.
- [Linux Compatibility Guide](./docs/LINUX-COMPATIBILITY.md) - The reference platform; lists package installs plus validation steps for running the automation exactly as written.
- [Shell Compatibility Guide](./docs/SHELL-COMPATIBILITY.md) - Lists the required POSIX/batch features (`bash`, `set -euo pipefail`, `mkdir`, `tee`, etc.) and explains how Linux/zsh/WSL/Git Bash satisfy them.

### Zero-Touch Automation Options

- `scripts/run-local-automation.sh [--connector CONNECTOR] [--emulator-action enable|disable] [--overlay-order overlay-1,overlay-2,...]` executes the bootstrap checks, migration wizard, and CI gate without any interactive steps. Defaults target GitHub with the Azure emulator overlay order (`./bootstrap`, `./hub`, `./emulator-azure`, `./spoke-local`) and uses `scripts/local-ci-gate.sh` to run `conftest` + `kubeconform`.
- The script writes logs under `logs/local-automation/` and produces a JSON report (`summary-*.json`) that captures the start/end times, connector, emulator action, overlay order, helper scripts, CI gate command, and paths to the bootstrap/wizard logs.
- Override the defaults to exercise other connectors/emulators (e.g., `--connector=azure-devops --overlay-order ./bootstrap,./hub,./cloud-aks,./spoke-local`). Each run still runs the same zero-touch CI gate and summary reporting.
- Use `.github/workflows/run-local-automation.yml` to trigger the same wrapper via GitHub Actions (runs on `ubuntu-latest`, installs `conftest`/`kubeconform`, and uploads the logs/summary as artifacts). Supply `connector`, `overlay_order`, and `emulator_action` inputs to target GitHub Enterprise Cloud/Server, Azure DevOps, or other hosts on demand. – [GitHub Action file](./.github/workflows/run-local-automation.yml)
- Use `azure-pipelines-zero-touch.yml` as a template for Azure Pipelines/job-based runs; it installs the same policy tooling, runs the wrapper with pipeline parameters, and publishes the `logs/local-automation/` directory as an artifact for post-run verification. – [Azure Pipelines template](./azure-pipelines-zero-touch.yml)
- Both pipelines now call `scripts/publish-summary.sh` after the automation completes; set `SUMMARY_ENDPOINT` (and optional `SUMMARY_TOKEN`) to post the generated `latest-summary.json` to your dashboard/archive service, and set `NOTIFY_WEBHOOK` to receive alerts when the CI gate status equals `failure`. The script reads `logs/local-automation/latest-summary.json`, posts it to the endpoint, and issues a failure notification only when requested.
- `scripts/publish-summary.sh` also generates a Markdown report (`logs/local-automation/latest-summary.md`) that mirrors the JSON summary, lists the connector, overlay order, emulator action, helper scripts, CI gate command, and log locations, and can be archived alongside the logs for review by wider audiences.

## Comparison with Managed Alternatives

Before building this architecture, evaluate whether a managed product meets your requirements:

| Product | Covers | What you still own |
|---|---|---|
| GKE Enterprise / Anthos | Multi-cluster GitOps, policy, secrets, config sync | GCP-centric; cross-cloud requires agents |
| Azure Arc | Azure + connected K8s, GitOps, policy | Azure-centric; AWS/GCP limited |
| EKS Anywhere | On-prem EKS with Flux GitOps | AWS-centric; no native Azure/GCP |
| Crossplane only | Cloud resource management, unified XRDs | No cluster lifecycle, no fleet GitOps |
| This architecture | Full multi-cloud, self-hosted, cluster + resource lifecycle | Upfront adoption cost; you own the controllers |

## Known Limitations

- No full plan equivalent: the CI gate validates and guards but does not diff current cloud state
- Crossplane Composition authoring requires upfront investment before spoke teams can use XRDs
- Multi-cluster progressive rollout requires external coordination; Flux + CAPI do not provide
  rollout gating equivalent to single-cluster progressive delivery
- CAPI provisions a minimal cluster; CNI, CSI, ingress, autoscaler, and monitoring must be layered
  on via spoke Flux separately
- On-prem spoke infra provider (Metal3, CAPV, CAPO) selection depends on hardware environment
- Flux SOPS integration has documented edge-case decryption failures; SOPS is the fallback path
  only in this architecture

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for workflow guidance, Windows/WSL onboarding, and documentation expectations.

[Pull Requests](https://github.com/lloydchang/gitops-infra-control-plane/pulls)

## License

This repository uses dual licensing:
- `AGPL-3.0`: Core infrastructure manifests, logic, documentation, examples, and more
  - See [LICENSE](LICENSE) file - https://www.gnu.org/licenses/agpl-3.0.html
- `Apache-2.0`: Specific sample snippets requiring user adaptations
  - See [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0)


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
- Use `.github/workflows/run-local-automation.yml` or `azure-pipelines-run-local-automation.yml` to trigger the wrapper in CI; both pipelines publish the `logs/local-automation/` summary and optionally call `scripts/publish-summary.sh`.
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

# GitOps Infra Control Plane

Continuous Reconciliation Engine (CRE) for Multi-Cloud Infrastructure

---

## What Changed From v1 and Why

If you have seen an earlier version of this architecture, four structural problems were redesigned:

| Problem (v1) | Redesign (v2) | Source critique |
|---|---|---|
| ACK + ASO + KCC = three incompatible CRD schemas | Replaced with Crossplane unified XRDs | Critique 3 |
| Hub decrypts SOPS and pushes plaintext secrets to spokes (push model) | Spokes pull secrets from cloud vaults via ESO + workload identity (pull model) | Critique 2 |
| Hub self-manages itself with no external recovery path | Lightweight secondary bootstrap cluster holds hub recovery state | Critiques 1 & 2 |
| No pre-merge change preview ("no terraform plan equivalent") | CI policy gate (Conftest/OPA) validates and previews drift before merge | Critique 3 |

---

## What This Is

A hub-spoke GitOps architecture where a central Kubernetes hub cluster continuously reconciles
multi-cloud infrastructure state. A Git repository is the declarative source of truth. A CI policy
gate catches dangerous changes before merge. Flux reconciles the hub. Each spoke runs its own Flux
agent, pulling its configuration directly from Git, independent of the hub.

**What it provides:**

- Automatic drift correction for all Git-managed infrastructure resources
- Unified cloud-agnostic resource model across AWS, Azure, and GCP via Crossplane
- Spoke-level secret isolation using cloud-native workload identity (no hub in the secrets path)
- Cluster lifecycle management (provision, upgrade, scale, decommission) via Cluster API

**What it does not provide:**

- Self-healing for runtime failures outside GitOps-managed resources (pod crashes, application
  bugs, network partitions)
- A terraform plan equivalent — the CI gate provides schema validation and policy checks, not a
  full diff of cloud state
- Zero-downtime hub recovery — hub failure pauses new reconciliation; spokes continue running on
  last-applied state

---

## Architecture

```text
[Tier 0]  Git repository — declarative source of truth
          |
          |  Pull request
          v
          CI policy gate (Conftest / OPA)
          - Schema validation
          - Deletion guard: reject changes that remove stateful XRDs without explicit annotation
          - Policy checks: naming, tagging, cost guardrails
          |
          |  Merge to main
          v
          +-----------------------------------------+
          |  Bootstrap cluster (secondary, lightweight) |
          |  k3s or managed (1–3 nodes)               |
          |  Holds: hub bootstrap Flux config          |
          |          hub etcd backup schedule          |
          |          hub cold-start runbook            |
          +-----------------------------------------+
               |  bootstraps hub once; monitors hub health
               v
      +--------------------------------------------------------------------------+
[Tier 1] |                          Hub cluster (HA)                             |
      |  3+ control plane nodes across AZs • etcd backup to object storage      |
      |  Flux self-manages hub after bootstrap (circular dependency by design)   |
      |--------------------------------------------------------------------------|
      |  +-------------------+  +----------------------------+  +-----------+    |
      |  | Flux              |  | Crossplane                 |  | CAPI      |    |
      |  | Reconciles hub    |  | Unified XRDs (cloud-       |  | Spoke     |    |
      |  | Bootstraps spokes |  | agnostic abstractions)     |  | lifecycle |    |
      |  | via CAPI          |  | XDatabase, XNetwork, etc.  |  | only      |    |
      |  |                   |  | Providers:                 |  |           |    |
      |  |                   |  |  provider-aws              |  | Kubeadm   |    |
      |  |                   |  |  provider-azure            |  | Metal3    |    |
      |  |                   |  |  provider-gcp              |  | CAPV      |    |
      |  +-------------------+  +----------------------------+  +-----------+    |
      +--------------------------------------------------------------------------+
               |                         |                          |
               | Flux bootstraps spoke   | Crossplane creates       | CAPI provisions
               | Flux + ESO agents       | cloud resources          | cluster lifecycle
               v                         v                          v
      +--------------------------------------------------------------------------+
[Tier 2] |                         Spoke clusters                                |
      |--------------------------------------------------------------------------|
      |  Each spoke is operationally independent:                                |
      |  - Flux agent pulls config from Git directly (pull model)                |
      |  - ESO pulls secrets from cloud vault using workload identity            |
      |  - Hub outage does not stop spoke reconciliation                         |
      |                                                                          |
      |  +----------+  +----------+  +----------+  +----------------------+      |
      |  | EKS      |  | AKS      |  | GKE      |  | Kubeadm / on-prem   |      |
      |  |          |  |          |  |          |  |                     |      |
      |  | ESO via  |  | ESO via  |  | ESO via  |  | ESO via external    |      |
      |  | IRSA     |  | Managed  |  | Workload |  | vault (Vault,       |      |
      |  |          |  | Identity |  | Identity |  | AWS SM, etc.)       |      |
      |  | Flux     |  | Flux     |  | Flux     |  | Flux                |      |
      |  +----------+  +----------+  +----------+  +----------------------+      |
      +--------------------------------------------------------------------------+
```

---

## Key Redesign: Crossplane Replaces ACK + ASO + KCC

The original architecture used three separate cloud-native operators (ACK for AWS, ASO for Azure,
KCC for GCP), each with incompatible CRD schemas. A developer provisioning a database had to write
entirely different YAML depending on which cloud they were targeting.

Crossplane provides a single Composition layer that abstracts cloud-specific resources behind
cloud-agnostic XRDs defined once by the platform team.

```yaml
# Developer writes this ONCE — cloud is an implementation detail
apiVersion: platform.example.com/v1alpha1
kind: XDatabase
metadata:
  name: orders-db
spec:
  engine: postgres
  version: "15"
  size: medium
  region: us-east-1
```

The platform team defines the Composition that maps `XDatabase` to RDS on AWS, Azure Database on
Azure, or Cloud SQL on GCP. Developers never write provider-specific YAML.

**Trade-offs vs raw ACK/ASO/KCC:**

| | Raw ACK/ASO/KCC | Crossplane XRDs |
|---|---|---|
| Developer YAML | Cloud-specific per provider | Cloud-agnostic, defined once |
| Operator count on hub | 3 operators (ACK + ASO + KCC) | 1 operator + N providers |
| Feature coverage | Closer to native cloud API | May lag niche features |
| Platform team work | Low initial, high per-cloud | High initial, low per-cloud |
| Debugging | 3 CRD schemas, 3 event models | 1 Composition layer to debug |

Crossplane is not free of complexity — Compositions require platform team investment to author and
maintain. The pay-off is that spoke teams never touch cloud-specific YAML, and switching cloud
providers means updating one Composition, not every consumer's manifests.

---

## Key Redesign: Spoke Pull Model Replaces Hub Push

The original design had the hub decrypt SOPS secrets and push plaintext `Secret` objects to spokes.
This meant:
- Hub compromise exposed all secrets for all spokes simultaneously
- Hub had to maintain direct network access to every spoke API server
- Hub failure interrupted secret delivery to all spokes

The redesign removes the hub from the secrets supply chain entirely.

```text
Original (push):
  Hub (SOPS decrypt) → network → spoke API server → etcd (plaintext)

Redesigned (pull):
  Spoke ESO agent → cloud workload identity → cloud vault → spoke etcd
  Hub is not in this path at all
```

Each spoke uses its cloud-native workload identity to authenticate directly to its cloud vault:

| Spoke | Identity mechanism | Vault |
|---|---|---|
| EKS | IRSA (IAM Roles for Service Accounts) | AWS Secrets Manager |
| AKS | Azure Managed Identity | Azure Key Vault |
| GKE | Workload Identity Federation | GCP Secret Manager |
| Kubeadm / on-prem | HashiCorp Vault / OIDC | Self-managed vault |

**What ESO provides that SOPS hub-push does not:**
- Secret access is scoped per-spoke by cloud IAM, not by network access to the hub
- Hub compromise does not expose spoke secrets
- Spoke secret delivery continues during hub outage
- Secret rotation is handled by the vault, not by re-encrypting and re-committing to Git

**What SOPS hub-push still provides that ESO does not:**
- Zero controllers to install on spokes (ESO requires a controller per spoke)
- Simpler backup model (one age key vs vault HA per environment)
- Works for secrets that have no natural home in a cloud vault (e.g., cross-cloud tokens)

SOPS/age is retained in this architecture as a fallback for the on-prem spoke and for secrets
that cannot be stored in a cloud vault. It is no longer the primary path.

---

## Key Redesign: Secondary Bootstrap Cluster

The hub has a known circular dependency: Flux manages the hub cluster it runs on. If the hub
suffers a total failure (etcd corruption, mass node loss), the tool required to recover it is not
running.

The secondary bootstrap cluster is a minimal cluster (k3s or a small managed cluster, 1–3 nodes)
whose only responsibilities are:

1. Store the Flux bootstrap configuration and hub cluster manifests
2. Run a scheduled etcd backup job targeting the hub
3. Hold the hub cold-start procedure as a runbook that operators can execute manually

The bootstrap cluster does not reconcile spokes. It does not hold cloud credentials. It is a
recovery anchor, not a second hub.

**Hub recovery with secondary bootstrap cluster:**

```text
1. Bootstrap cluster detects hub is unreachable
2. Operator provisions replacement hub cluster (manual or automated)
3. Operator runs: flux bootstrap --from=secondary-cluster-config
4. Hub comes up; Crossplane and CAPI controllers resume
5. Spokes were never paused — they continued pulling from Git independently
6. Verify spoke connectivity and cloud resource reconciliation
```

Without the secondary cluster, step 3 requires operators to reconstruct bootstrap parameters from
memory or documentation under pressure. The secondary cluster makes this a documented, tested,
repeatable procedure.

---

## Key Redesign: CI Policy Gate (Pre-Merge Drift Preview)

GitOps has no `terraform plan` equivalent. A manifest merged to Git is acted on immediately.
Without a gate, a developer who deletes a Crossplane XDatabase manifest triggers deletion of a
production database.

The CI policy gate runs on every pull request and enforces:

**Deletion guard (mandatory)**
```yaml
# Crossplane Composition default — stateful resources require explicit opt-out
deletionPolicy: Orphan   # default for all XDatabase, XVolume, XQueue
# To allow deletion, PR author must add:
# annotations:
#   platform.example.com/allow-deletion: "true"
#   platform.example.com/deletion-approved-by: "platform-team"
```

Any PR that removes a stateful XRD without this annotation fails CI and cannot be merged.

**Schema validation**
- All manifests pass `kubeconform` against current Crossplane XRD schemas
- Flux Kustomization dry-run against the hub API server (read-only, no apply)

**Policy checks (Conftest / OPA)**
- Naming conventions enforced
- Required tags/labels present on all cloud resources
- Cost guardrail: flag resources above defined cost threshold for platform team review
- Namespace isolation: spokes cannot reference hub-only resources

This is not a full plan. It does not show a diff of current cloud state. It catches the most
dangerous classes of change — accidental deletion, schema errors, policy violations — before they
reach the hub's reconciliation loop.

---

## Hub Security Hardening

The hub holds cloud credentials for all three providers and manages spoke cluster lifecycle. It is
a high-value target.

**Required before production:**

- Network policy: hub egress restricted to known cloud API endpoints only
- Separate Kubernetes service accounts per Crossplane provider (provider-aws, provider-azure,
  provider-gcp) with minimal IAM scopes
- CAPI and Crossplane controllers run in separate namespaces with separate RBAC
- Audit logging enabled on the hub API server; logs shipped to an external SIEM
- Node-level: hub nodes not accessible from spoke network segments
- Secrets: cloud credentials for Crossplane providers stored in cloud vaults, not as static
  Kubernetes Secrets on the hub

**What hub compromise still exposes despite hardening:**

Crossplane providers on the hub hold cloud credentials scoped to the resources they manage.
A hub compromise exposes those credentials. The blast radius is limited to cloud resources that
Crossplane manages — it does not expose spoke application secrets (which are now in per-spoke
cloud vaults, not on the hub). This is the security improvement the pull model provides.

---

## Hub High Availability and Recovery

The hub is still a single coordination point. Hub failure pauses new reconciliation and new cluster
provisioning. Spokes continue running on last-applied state.

**Hub HA minimum:**
- 3 control plane nodes across availability zones
- etcd backup to object storage on a schedule; verify restores quarterly
- Hub cluster nodes: dedicated node group, no workloads other than platform controllers

**Recovery sequence:**

```text
1. Secondary bootstrap cluster detects hub unreachable (health check)
2. Operator provisions replacement cluster
3. Restore etcd backup OR re-bootstrap from secondary cluster config
4. Crossplane providers resume; cloud resources already exist, reconciliation catches up
5. CAPI resumes; spoke clusters already exist, no re-provisioning needed
6. Verify Crossplane managed resource status: kubectl get managed
7. Verify spoke Flux health: flux get all -A (run on each spoke)
```

---

## Operator Surface (Reduced from v1)

| Controller | Role | Failure surface |
|---|---|---|
| Flux (hub) | Hub self-reconciliation; spoke bootstrap | Git auth, image pull |
| Flux (per spoke) | Spoke self-reconciliation | Git auth, spoke network |
| Crossplane | Cloud resource lifecycle (replaces ACK+ASO+KCC) | Provider credentials, cloud API |
| CAPI | Spoke cluster lifecycle only | Infra provider webhooks |
| ESO (per spoke) | Secret delivery from cloud vault | Workload identity, vault availability |

v1 had 5 controllers running on the hub with 5 separate CRD schemas and event models. v2 has 2
hub controllers (Flux + Crossplane + CAPI) and 2 spoke agents (Flux + ESO) with a unified
Crossplane abstraction layer. The debugging surface is smaller, but Crossplane Compositions
introduce their own debugging layer (Composition revision history, managed resource status).

---

## When to Use This

### Strong fit
- Multi-cloud environments (genuinely 2+ clouds in production) with a platform engineering team
  of 3+ engineers who will own and operate the hub
- Organisations where infrastructure drift is already a recurring production incident
- Teams with existing Kubernetes operational depth across multiple clusters
- Brownfield environments consolidating from multiple IaC tools and pipelines

### Not a good fit
- **Single-cloud deployments.** GKE Enterprise, Azure Arc, and EKS Anywhere cover most of this
  at lower operational cost. Evaluate them first.
- **Teams under 10 engineers.** The platform engineering overhead (hub HA, Crossplane Composition
  authoring, CAPI provider management, ESO per spoke) will dominate engineering capacity.
- **No Kubernetes operational depth.** If your team cannot diagnose a Crossplane Composition
  stuck in "Creating" or a CAPI machine stuck in "Provisioned", failure modes here are opaque.
- **Emergency timelines.** This is a target state architecture built for steady-state operations,
  not a migration tool.
- **Cost-constrained projects.** Model the cost of the hub cluster, secondary bootstrap cluster,
  cloud vault instances per spoke, and cross-cloud networking before committing.

> Before beginning: complete the [Problem-Solution Fit Assessment](./docs/PROBLEM-SOLUTION-FIT.md).

---

## Comparison with Managed Alternatives

| Product | What it covers | Gap vs this architecture |
|---|---|---|
| GKE Enterprise / Anthos | Multi-cluster GitOps, policy, secrets, config sync | GCP-centric; AWS/Azure requires agents |
| Azure Arc | Azure + connected K8s, GitOps, policy | Azure-centric; GCP/AWS limited |
| EKS Anywhere | On-prem EKS, GitOps via Flux | AWS-centric; no native Azure/GCP |
| Crossplane only (no hub-spoke) | Cloud resource management, no cluster lifecycle | No CAPI, no fleet GitOps |
| **This architecture** | Full multi-cloud, self-hosted, cluster lifecycle + resources | Hub operational cost; you own everything |

Self-hosting this architecture is justified when your requirements span 2+ clouds with full parity
requirements and managed products cannot provide the control surface you need. If that condition is
not met, a managed product is likely the right choice.

---

## Key Features

- **Continuous drift reconciliation** — Flux on hub and per spoke; cloud resources via Crossplane
- **Cloud-agnostic resource model** — Crossplane XRDs abstract AWS/Azure/GCP behind one API
- **Spoke autonomy** — each spoke pulls from Git and cloud vaults independently; hub outage does
  not pause spoke operations
- **Spoke lifecycle management** — Cluster API (Kubeadm, Metal3, CAPV, CAPO)
- **Per-spoke secret isolation** — ESO + workload identity; hub not in secrets path
- **Pre-merge safety gate** — deletion guard, schema validation, policy checks in CI
- **Hub recovery anchor** — secondary bootstrap cluster for cold-start recovery

---

## What Is Not in This Architecture

**AI / agent orchestration** has been removed from the core architecture. Injecting non-deterministic
agents into a deterministic reconciliation loop breaks the auditability and predictability that
GitOps is designed to provide. If you are exploring AI-assisted platform automation, see
[AI Integration Analysis](./docs/AI-INTEGRATION-ANALYSIS.md) for research context and known
limitations. Treat it as a separate experimental track, not a dependency of this architecture.

---

## Known Limitations

- **No full plan equivalent.** The CI gate validates and guards but does not show a complete diff
  of current vs desired cloud state the way `terraform plan` does.
- **Crossplane Composition authoring cost.** The platform team must write and maintain Compositions
  for every resource type. Initial investment is significant. Teams using raw cloud CRDs directly
  instead of Compositions lose the cloud-agnostic benefit.
- **Multi-cluster progressive rollout.** Staged rollouts across many spokes require external
  coordination (e.g., Flagger, Argo Rollouts, or manual wave promotion). Flux + CAPI do not
  provide rollout gating equivalent to single-cluster progressive delivery.
- **CAPI bare-minimum clusters.** CAPI provisions a cluster, not a production-ready cluster. CNI,
  CSI, ingress, autoscaler, and monitoring must be layered on via spoke Flux separately.
- **On-prem spoke provider.** Kubeadm spoke infra provider (Metal3, CAPV, CAPO) is TBD based on
  hardware environment.
- **Flux SOPS edge cases.** Flux SOPS integration has documented intermittent decryption edge cases
  (see fluxcd/flux2 issues). SOPS is retained only as a fallback path in this architecture; ESO
  is the primary secrets mechanism.

---

## Documentation

### Start here
1. [Problem-Solution Fit](./docs/PROBLEM-SOLUTION-FIT.md) — Confirm this is the right tool
2. [Architecture](./docs/ARCHITECTURE.md) — Technical deep-dive including Crossplane Compositions
3. [Implementation Plan](./docs/implementation_plan.md) — Step-by-step deployment

### Operations
- [Hub HA and Recovery](./docs/HUB-HA-RECOVERY.md) — Hub failure modes and recovery with secondary cluster
- [Secondary Bootstrap Cluster](./docs/BOOTSTRAP-CLUSTER.md) — Setup and maintenance
- [Crossplane Compositions](./docs/CROSSPLANE-COMPOSITIONS.md) — Authoring guide for platform teams
- [ESO Workload Identity Setup](./docs/ESO-WORKLOAD-IDENTITY.md) — Per-spoke secret delivery
- [CI Policy Gate](./docs/CI-POLICY-GATE.md) — Deletion guard, schema validation, OPA policies
- [Controller Runbooks](./docs/CONTROLLER-RUNBOOKS.md) — Per-controller failure playbooks

### Implementation examples
- [Complete Hub-Spoke](./examples/complete-hub-spoke/) — Full deployment
- [Crossplane Compositions](./examples/crossplane-compositions/) — XDatabase, XNetwork, XCluster
- [ESO per spoke](./examples/eso-workload-identity/) — IRSA, Managed Identity, Workload Identity
- [Variants](./variants/) — Deployment variations for different scenarios

### Migration
- [Legacy IaC Migration](./docs/LEGACY-IAC-MIGRATION-STRATEGY.md) — Converting from Terraform/CDK
- [v1 to v2 Migration](./docs/V1-TO-V2-MIGRATION.md) — ACK/ASO/KCC → Crossplane, SOPS push → ESO pull

### Research (not production features)
- [AI Integration Analysis](./docs/AI-INTEGRATION-ANALYSIS.md) — Experimental; read limitations first

---

## Contributing

[Pull Requests](https://github.com/lloydchang/gitops-infra-control-plane/pulls)

---

## License

- **AGPL-3.0** — Core infrastructure manifests, logic, documentation, and examples.
  See [LICENSE](LICENSE) — https://www.gnu.org/licenses/agpl-3.0.html
- **Apache-2.0** — Specific sample snippets intended for user adaptation.
  See [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0)

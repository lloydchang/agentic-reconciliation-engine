# GitOps Infra Control Plane — Architecture

This document provides detailed technical architecture for the GitOps Infra Control Plane. Before
reading this document, confirm the architecture is the right fit for your situation by completing
the [Problem-Solution Fit Assessment](./PROBLEM-SOLUTION-FIT.md).

---

## Overview

The GitOps Infra Control Plane is a hub-spoke architecture that uses a central Kubernetes hub
cluster to continuously reconcile multi-cloud infrastructure state. A Git repository is the
declarative source of truth. A CI policy gate catches dangerous changes before merge. Flux
reconciles the hub and bootstraps each spoke. Each spoke runs its own Flux agent and ESO instance,
operating independently of the hub.

The system treats infrastructure as a living process with a continuous reconciliation loop, not a
one-time deployment. Crossplane's unified XRD layer provides a cloud-agnostic resource model
across AWS, Azure, and GCP.

---

## Tiers

```
[Tier 0]   Git repository — declarative source of truth
                |
                |  Pull request
                v
           CI policy gate
           · Schema validation (kubeconform)
           · Deletion guard (stateful XRDs require approval annotation)
           · OPA policy checks: naming, tagging, cost guardrails
                |
                |  Merge to main
                v
           Bootstrap cluster (1–3 nodes, k3s or small managed)
           · Holds hub bootstrap config
           · Runs hub etcd backup schedule
           · Cold-start recovery anchor
                |
                v
[Tier 1]   Hub cluster (HA, managed control plane)
           · Flux — GitOps reconciliation, bootstraps spokes
           · Crossplane — unified XRDs, provider-aws/azure/gcp
           · Cluster API — spoke cluster lifecycle
                |
                v
[Tier 2]   Spoke clusters (operationally independent)
           · Own Flux agent — pulls from Git directly
           · ESO + workload identity — pulls secrets from cloud vault
           · Hub outage does not pause spoke reconciliation or secret delivery
```

---

## Core Components

### Hub cluster

The hub runs on a managed Kubernetes control plane (EKS, AKS, or GKE). The cloud provider owns
the control plane nodes. You own what runs on them.

**Flux** — GitOps reconciliation engine. Watches the Git repository, reconciles hub manifests,
and bootstraps each spoke with its own Flux agent and ESO instance after CAPI provisions the spoke
cluster. Flux manages the hub cluster it runs on (circular dependency by design). The bootstrap
cluster provides the external recovery anchor for this case.

**Crossplane** — unified cloud resource management. Platform team authors Compositions and XRDs
once; spoke teams write cloud-agnostic YAML. Crossplane providers translate XRDs to
provider-specific managed resources.

| Provider | Cloud | Resources managed |
|---|---|---|
| provider-aws | AWS | VPC, EKS, RDS, S3, SQS, IAM, ... |
| provider-azure | Azure | VNet, AKS, Azure DB, Key Vault, ... |
| provider-gcp | GCP | VPC, GKE, Cloud SQL, GCS, Pub/Sub, ... |

Developers write this once, targeting any cloud:

```yaml
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

The Composition determines whether this becomes RDS, Azure Database, or Cloud SQL.

**Cluster API (CAPI)** — spoke cluster lifecycle. Provisions, upgrades, scales, and
decommissions spoke clusters. Supported infra providers: Kubeadm, Metal3 (bare metal), CAPV
(vSphere), CAPO (OpenStack).

### Bootstrap cluster

A minimal cluster (1–3 nodes, k3s or small managed cluster) whose only responsibilities are:

- Store hub bootstrap Flux configuration and hub cluster manifests
- Run a scheduled etcd backup job targeting the hub, writing to object storage
- Provide the cold-start procedure for hub total-loss recovery

The bootstrap cluster does not reconcile spokes, does not hold cloud credentials, and does not
participate in the data path. It is a recovery anchor only.

**Hub cold-start procedure:**

```
1. Bootstrap cluster detects hub is unreachable
2. Operator provisions replacement hub cluster
3. Operator runs: flux bootstrap --from=bootstrap-cluster-config
4. Hub comes up; Crossplane and CAPI resume reconciliation
5. Spokes were never paused — they continued pulling from Git independently
6. Verify: kubectl get managed (Crossplane resources)
7. Verify: flux get all -A (run on each spoke)
```

### CI policy gate

The CI gate runs on every pull request. It provides the closest equivalent to `terraform plan`
available in a GitOps workflow — it does not diff current cloud state, but it blocks the most
dangerous classes of change before they reach the reconciliation loop.

**Deletion guard (mandatory)**

Any PR that removes a stateful XRD without an explicit approval annotation fails CI:

```yaml
# To allow deletion of a stateful resource, PR must include:
annotations:
  platform.example.com/allow-deletion: "true"
  platform.example.com/deletion-approved-by: "platform-team"
```

**Schema validation**

- `kubeconform` against current Crossplane XRD schemas
- Flux Kustomization dry-run against hub API server (read-only)

**OPA / Conftest policies**

- Naming conventions enforced
- Required tags/labels on all cloud resources
- Cost guardrail: flag resources above defined threshold for platform team review
- Namespace isolation: spokes cannot reference hub-only resources

### Spoke clusters

Each spoke is provisioned by CAPI from the hub, then operates independently.

**Flux agent (per spoke)** — pulls configuration directly from Git, not via the hub. Spoke Flux
reconciliation continues during hub outage.

**ESO (per spoke)** — pulls secrets from the spoke's cloud vault using native workload identity.
The hub is not in the secrets path.

| Spoke type | Identity mechanism | Vault |
|---|---|---|
| EKS | IRSA (IAM Roles for Service Accounts) | AWS Secrets Manager |
| AKS | Azure Managed Identity | Azure Key Vault |
| GKE | Workload Identity Federation | GCP Secret Manager |
| Kubeadm / on-prem | OIDC / HashiCorp Vault | Self-managed vault |

---

## Secrets Strategy

### Primary: ESO + workload identity

Each spoke authenticates directly to its cloud vault:

```
Spoke ESO agent → cloud workload identity → cloud vault → spoke etcd
Hub is not in this path
```

Secret access is scoped by cloud IAM per spoke. A hub compromise does not expose spoke
application secrets. Secret rotation is handled by the vault with no re-encrypt-and-commit cycle.

### Fallback: SOPS / age

Retained for on-prem spokes and cross-cloud secrets with no natural cloud vault home.

```
Hub (Flux SOPS decrypt) → spoke API server → spoke etcd (plaintext)
```

Back up the age private key to a cloud key vault. Flux decrypts at apply time on hub only. Spokes
receive plain Kubernetes Secret objects. Use SOPS only where ESO + workload identity is not
available. The primary path is ESO.

---

## Repository Structure

```
control-plane/
  flux/                   # Flux bootstrap and GitRepository manifests
  crossplane/
    compositions/         # XDatabase, XNetwork, XQueue, XCluster Compositions
    xrds/                 # XRD definitions
    providers/            # provider-aws, provider-azure, provider-gcp configs
  capi/                   # ClusterClass, MachineDeployment templates
  ci/                     # Conftest policies, kubeconform schemas

infrastructure/
  tenants/
    1-network/            # XNetwork resources
    2-clusters/           # XCluster resources
    3-workloads/          # Application resources per spoke
```

Flux Kustomization `dependsOn` chains are explicit and mandatory:
`1-network/ → 2-clusters/ → 3-workloads/`

---

## Hub High Availability

The hub is a single coordination point. Hub failure pauses new reconciliation and new cluster
provisioning. Spokes continue on last-applied state.

**Minimum HA configuration:**

- 3+ control plane nodes across availability zones (managed by the cloud provider)
- Dedicated node pools for Crossplane and CAPI controllers
- etcd backup to object storage on a schedule; verify restores quarterly
- Hub nodes: no workloads other than platform controllers

---

## Dependency Management

Flux `dependsOn` enforces explicit ordering between resource tiers:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: workloads
  namespace: flux-system
spec:
  dependsOn:
    - name: clusters
    - name: network
  interval: 5m
  path: ./infrastructure/tenants/3-workloads
  sourceRef:
    kind: GitRepository
    name: infrastructure-repo
```

Cross-spoke dependencies are explicit. Spokes do not have implicit dependencies on hub
reconciliation after bootstrap.

---

## Compliance and Governance

**Change management** — all changes go through Git pull requests with CI gate validation.
The CI gate enforces deletion guards, schema validation, and OPA policies before merge. No
infrastructure change reaches the reconciliation loop without passing CI.

**Audit trail** — complete Git history of all infrastructure changes; Crossplane managed resource
status and events; Flux reconciliation logs; cloud provider API audit logs.

**Policy enforcement** — naming conventions, required tags, cost guardrails, and namespace
isolation are enforced by the CI OPA policies. Security group and network policies are enforced
by Crossplane Compositions.

---

## Known Limitations

- No full plan equivalent. The CI gate validates and guards; it does not diff current cloud state
  the way `terraform plan` does.
- Crossplane Composition authoring is a platform team investment. Until Compositions exist for a
  resource type, spoke teams cannot use XRDs for that type.
- Multi-cluster progressive rollout requires external coordination. Flux + CAPI do not provide
  rollout gating equivalent to single-cluster progressive delivery.
- CAPI provisions a minimal cluster. CNI, CSI, ingress, autoscaler, and monitoring must be
  layered on separately via spoke Flux.
- On-prem infra provider (Metal3, CAPV, CAPO) selection depends on hardware environment.
- Flux SOPS integration has documented edge-case decryption failures. SOPS is the fallback path
  only; ESO is the primary secrets mechanism.

---

## AI / Agent Integration

AI-assisted automation patterns (consensus agents, autonomous optimization) are **research-stage
and not part of this production architecture**. Injecting non-deterministic agents into a
deterministic reconciliation loop breaks the auditability and predictability that GitOps provides.

See [AI Integration Analysis](./AI-INTEGRATION-ANALYSIS.md) for research context, scope, and
known limitations. Treat it as a separate experimental track with no dependency on this
architecture.

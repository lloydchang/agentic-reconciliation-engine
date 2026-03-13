# implementation_plan.md: GitOps Infra Control Plane

**Objective:** Implement continuous reconciliation for multi-cloud infrastructure that traditional
IaC tools cannot provide. While Terraform, CDK, CloudFormation, Bicep, and ARM run once and exit,
this architecture provides 24/7 automated drift detection and repair. Initial hub cluster setup
uses industry-standard CLIs (eksctl, az, gcloud), then transitions to continuous reconciliation
for all ongoing infrastructure management via Crossplane's cloud-agnostic XRDs orchestrated by
Flux, with per-spoke Flux agents and ESO for secret delivery.

**Prerequisites:** Before beginning, review the architecture diagram in [README.md](./README.md).
The implementation assumes a hub-and-spoke model where the hub cluster manages spoke cluster
lifecycle via Cluster API, and each spoke runs its own Flux agent and ESO instance independently.

## 1. Architectural Mandates

- **Continuous Reconciliation**: 24/7 monitoring and automatic repair of configuration drift —
  something traditional IaC cannot achieve without external orchestration.
- **Cloud-Agnostic Resource Model**: Use Crossplane Compositions and XRDs for all cloud resources.
  Platform team authors Compositions once; spoke teams write cloud-agnostic YAML. Do not use raw
  ACK, ASO, or KCC directly — they produce cloud-specific manifests that fragment the resource
  model across providers.
- **Spoke Autonomy**: Each spoke runs its own Flux agent pulling from Git. Each spoke uses ESO
  with workload identity to pull secrets from its cloud vault. The hub is not in the secrets path.
  Spoke reconciliation and secret delivery continue during hub maintenance or failure.
- **No Centralized State**: The state is the live cloud API, reconciled by controllers. Git is the
  declared intent.

## 2. Design Rationale

**Why Flux (not Argo CD)?**
- Flux is a cluster extension, making it the preferred plumbing for hub clusters
- Native `dependsOn` field allows specific resource-to-resource sequencing critical for
  Network → Cluster → Workload dependency chains
- Flux bootstraps and manages itself on the hub (circular dependency by design)

**Why Crossplane (not raw ACK/ASO/KCC)?**
- Raw ACK/ASO/KCC produce cloud-specific CRD schemas — a developer targeting multiple clouds must
  write entirely different YAML per provider
- Crossplane Compositions provide a single cloud-agnostic API surface; cloud is an implementation
  detail inside the Composition
- Switching cloud providers requires updating one Composition, not all consumer manifests

**Why ESO + workload identity (not hub SOPS push)?**
- Hub SOPS push places the hub in the secrets delivery path for all spokes — a hub compromise
  exposes all spoke secrets simultaneously
- ESO with workload identity (IRSA on EKS, Managed Identity on AKS, Workload Identity on GKE)
  scopes secret access by cloud IAM per spoke, with no hub involvement
- Spoke secret delivery continues independently during hub outage

**Why a CI policy gate?**
- GitOps has no `terraform plan` equivalent — a manifest merged to Git is acted on immediately
- The CI gate provides deletion guards (stateful XRDs require explicit approval annotation),
  schema validation, and OPA policy checks before merge
- This catches accidental deletion of production databases and policy violations before they reach
  the reconciliation loop

**Why a bootstrap cluster?**
- Flux manages the hub cluster it runs on (circular dependency by design)
- If the hub suffers a total failure, the tool required to recover it is not running
- A secondary lightweight cluster (k3s or small managed cluster, 1–3 nodes) holds the hub
  bootstrap configuration and etcd backup schedule, providing a cold-start recovery anchor

## 3. Execution Phases

### Phase 0: Bootstrap cluster and CI gate

1. Provision a small bootstrap cluster (k3s, or a minimal managed cluster)
2. Store hub bootstrap Flux config and hub cluster manifests in the bootstrap cluster
3. Configure hub etcd backup to object storage on a schedule
4. Set up CI pipeline with:
   - `kubeconform` schema validation against Crossplane XRD schemas
   - Conftest/OPA policies: deletion guard, naming conventions, required tags
   - Flux dry-run against hub API (read-only)

### Phase 1: Hub cluster

1. Provision hub cluster on a managed control plane (EKS, AKS, or GKE) — cloud provider owns
   the control plane nodes; you own what runs on them
2. Configure 3+ node pools across availability zones
3. Run Flux bootstrap pointing at the Git repository — Flux self-manages the hub thereafter
4. Install Crossplane and configure providers:
   - `provider-aws` with IRSA service account
   - `provider-azure` with Azure Managed Identity
   - `provider-gcp` with Workload Identity Federation
5. Install Cluster API with relevant infra providers (Kubeadm + Metal3/CAPV/CAPO for on-prem)
6. Author initial Crossplane Compositions: XNetwork, XCluster, XDatabase, XQueue

### Phase 2: Repository structure

Adhere to this directory structure:

```
control-plane/          # Flux configuration and controller setup
  flux/                 # Flux GitOps bootstrap manifests
  crossplane/           # Compositions, XRDs, provider configs
  capi/                 # Cluster API provider and cluster templates
  ci/                   # Conftest policies, kubeconform schemas

infrastructure/
  tenants/
    1-network/          # XNetwork resources
    2-clusters/         # XCluster resources (CAPI spoke definitions)
    3-workloads/        # Application resources per spoke
```

Flux Kustomization `dependsOn` chains must be explicit:
`1-network/ → 2-clusters/ → 3-workloads/`

### Phase 3: Spoke provisioning

1. Author XCluster Compositions for EKS, AKS, GKE, and Kubeadm targets
2. CAPI provisions spoke clusters from hub
3. Flux on hub bootstraps each spoke with:
   - Spoke-local Flux agent (pulls from Git directly, not via hub)
   - ESO with workload identity configured for the spoke's cloud vault
4. Validate spoke autonomy: take the hub offline; confirm spoke Flux and ESO continue operating

### Phase 4: Secrets wiring

For each cloud spoke:

| Spoke | Identity | Vault |
|---|---|---|
| EKS | IRSA | AWS Secrets Manager |
| AKS | Azure Managed Identity | Azure Key Vault |
| GKE | Workload Identity Federation | GCP Secret Manager |
| Kubeadm / on-prem | OIDC / HashiCorp Vault | Self-managed vault |

For on-prem or cross-cloud secrets with no natural cloud vault home, SOPS/age is retained as a
fallback. Back up the age private key to a cloud key vault. Flux decrypts at apply time on hub
only; spokes receive plain Secret objects.

### Phase 5: Drift validation

The implementation must verify:

1. Provision the full stack via Git commit
2. Manually delete a resource (e.g., a Crossplane-managed database) via cloud console
3. Observe Crossplane detecting drift and reverting cloud state to Git manifest within minutes
4. Manually delete a spoke Kubernetes Secret
5. Observe ESO re-creating it from the cloud vault within the configured sync interval
6. Take the hub offline; confirm spoke Flux and ESO reconciliation continues uninterrupted

## 4. Non-Native Resources: Fallback Strategy

For resources that have no Crossplane provider support, use this hierarchy:

1. **Official Kubernetes operator** (preferred) — cert-manager, external-dns, prometheus-operator
2. **Flux-managed Kubernetes Job** — for one-off or complex deployments using legacy IaC commands
3. **Raw cloud CRD via ACK/ASO/KCC** (last resort) — only when no Composition exists and no
   operator is available; document the reason and plan for Composition adoption

## 5. Completion Criteria

The repository must contain a complete, self-healing, Git-driven infrastructure platform that:

- Detects and repairs configuration drift within minutes without human intervention
- Delivers secrets to spokes via workload identity with no hub in the path
- Continues spoke reconciliation and secret delivery during hub maintenance or failure
- Blocks dangerous changes (deletions, policy violations) at CI before they reach the hub
- Can cold-start from a hub total loss using the bootstrap cluster and etcd backup

Every layer is pulled and reconciled by controllers under the GNU Affero General Public License
v3.0 (AGPL-3.0), with industry-standard CLIs used only for initial hub cluster setup.

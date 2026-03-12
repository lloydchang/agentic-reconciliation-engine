# implementation_plan.md: GitOps Infrastructure Control Plane

**Objective:** Implement continuous reconciliation for multi-cloud infrastructure that traditional IaC tools cannot provide. While Terraform, CDK, CloudFormation, Bicep, and ARM run once and exit, our approach provides 24/7 automated drift detection and repair. Initial Hub cluster setup uses industry-standard CLIs (eksctl, az, gcloud), then transitions to continuous reconciliation for all ongoing infrastructure management via native Kubernetes Custom Resources (CRs) using AWS ACK, Azure ASO, and GCP KCC, orchestrated by Flux.

**Prerequisites:** Before beginning, review the architectural topology diagram in [README.md](./README.md). The implementation assumes a hub-and-spoke model where the Hub Cluster manages the lifecycle of all Spoke Clusters.

## 1. Architectural Mandates
* **Continuous Reconciliation**: 24/7 monitoring and automatic repair of configuration drift - something traditional IaC cannot achieve without external orchestration.
* **No Abstraction Layers**: No Crossplane or custom intent-synthesis engines. Communicate directly with the Cloud Providers' official Kubernetes controllers.
* **No Centralized State**: The state is the live Cloud API, reconciled by the local controller.

## 2. Design Rationale
* Why Flux (Not Argo CD)? 
    * Controller-Native: Flux is a cluster extension, making it the preferred plumbing for hub clusters.
    * True Dependency DAG: Flux native dependsOn field allows specific resource-to-resource sequencing (critical for Network -> Cluster -> Workload chains).
* Why Native Cloud Controllers?
    * Continuous Reconciliation: ACK, ASO, and KCC monitor Cloud APIs 24/7, repairing drift automatically.
    * Direct API Access: Native CRDs provide day-zero access to new cloud features.
* Parallelism: Namespace isolation decouples reconciliation loops, preventing lock contention.
* The Recursive Advantage: Managing EKS, AKS, or GKE clusters is performed via the same native CRD pattern used for storage or networking.

## 3. Execution Phases (For AI Implementation)
1. Repository Setup: Adhere to directory structure: control-plane/ (Flux/Controllers) and infrastructure/tenants/ (Resources).
2. Identity & Controller Setup: Install ACK, ASO, and KCC. Configure Workload Identity (IRSA/GCP/Azure) exclusively. No static secrets.
3. Codification: Implement native Kubernetes CRs. Do not use legacy templates. Link resources via native CR references (name-based) rather than hardcoded strings.
4. DAG Orchestration: Configure Flux Kustomization manifests. Explicitly define dependsOn chains: 1-network/ -> 2-clusters/ -> 3-workloads/.
5. Non-Native Resources: Follow the fallback strategy: (1) Official Operator, (2) Flux-managed Kubernetes Job, (3) Targeted Crossplane Provider (only if strictly necessary).

## 4. Hub vs. Spoke Cluster Strategy
* Hub Cluster (Brain): The single control plane running Flux + Cloud Controllers.
* Spoke Clusters (Limbs): Clusters provisioned by the Hub Cluster. Once Ready, Flux targets these spoke clusters to deploy applications. If the Hub Cluster is lost, Spoke Clusters continue to function; simply re-bootstrap and point back to Git.

## 5. Drift Test Validation
The implementation must verify:
1. Provision the full stack via Git commit.
2. Manually delete a resource (e.g., EKS Cluster) via Cloud Console.
3. Observe the controller detecting drift and reverting cloud state to Git manifest within minutes.

**Completion Criteria:**
The repository must contain a complete, self-healing, Git-driven infrastructure platform that provides continuous reconciliation capabilities unavailable in traditional IaC tools. Every layer is pulled and reconciled by native Kubernetes controllers under the GNU Affero General Public License v3.0 (AGPL-3.0), with industry-standard CLIs used only for initial Hub cluster setup.

# gitops-infra-control-plane

Continuous Reconciliation Engine for Multi-Cloud Infra

## The Core Advantage
Traditional IaC tools (Terraform, CDK, CloudFormation, Bicep, ARM) run once and exit - they cannot continuously maintain infrastructure state. We provide **24/7 continuous reconciliation** that automatically detects and repairs configuration drift, something push-based tools fundamentally cannot achieve without complex external orchestration.

* **Continuous Reconciliation**: Native Kubernetes controllers (AWS ACK, Azure ASO, GCP KCC) monitor Cloud APIs 24/7. They actively repair configuration drift without human intervention.
* **Self-Healing Infrastructure**: Unlike traditional IaC that requires manual re-runs, our approach automatically maintains desired state continuously.
* **Zero State Files**: There is no Terraform State to corrupt, lock, or lose. The live Cloud API is the only source of truth.
* **Hybrid Setup**: Industry-standard CLIs (eksctl, az, gcloud) for initial Hub cluster creation, then continuous reconciliation for all ongoing infrastructure management.

## Architectural Topology
We use a hub-and-spoke model where a single Hub Cluster acts as the control plane for all cloud environments:

```text
                       GIT REPOSITORY
                     (Source of Truth)
                             |
                    Flux Pulls Manifests
                             |
                             v
      +------------------------------------------+
      |                HUB CLUSTER               |
      |------------------------------------------|
      | Flux | ACK        | ASO           | KCC  |
      +------------------------------------------+
             |               |               |
   Provisions/Manages Provisions/Manages Provisions/Manages
             |               |               |
      +-------------+ +-------------+ +-------------+
      |   SPOKE 1   | |   SPOKE 2   | |   SPOKE 3   |
      |   (EKS)     | |   (AKS)     | |   (GKE)     |
      |   CLUSTER   | |   CLUSTER   | |   CLUSTER   |
      +-------------+ +-------------+ +-------------+
```

## Getting Started
To understand the technical design, architectural mandates, and step-by-step implementation phases, refer to:
[implementation_plan.md](./docs/implementation_plan.md)

## Why Flux?
We utilize Flux over Argo CD because Flux is architecturally optimized for infrastructure lifecycle management:
- Controller-Native: Flux is a set of Kubernetes controllers, not an external UI overlay.
- Dependency Chaining: Flux dependency chaining enables a true Directed Acyclic Graph (DAG) for complex infrastructure dependencies, whereas Argo CD relies on linear Sync Waves.
- Headless & Reliable: Flux is designed for cluster-to-cluster management, which is essential for our hub-and-spoke Hub vs. Spoke Clusters strategy.

## Repository Standards
- Refer to .gitignore to ensure no local secrets or state artifacts are ever committed.
- All code is subject to the GNU Affero General Public License v3.0 (AGPL-3.0) (see [LICENSE](https://github.com/lloydchang/gitops-infra-control-plane/blob/main/LICENSE) file).

## Open-source Software
https://github.com/lloydchang/gitops-infra-control-plane

<img width="1024" height="1024" alt="Image" src="https://github.com/user-attachments/assets/e6b4bec7-3855-4532-a06c-daadffed4911" />

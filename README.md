# gitops-infra-control-plane

This repository acts as a Continuous Reconciliation Engine for multi-cloud infrastructure. 

## The Core Philosophy
We do not use push-based tools (Terraform, Blueprints, CDK, CloudFormation, Bicep, ARM) that execute once and exit. Instead, we treat infrastructure as a living, self-healing process using native Kubernetes operators.

* Continuous Reconciliation: Native Kubernetes controllers (AWS ACK, Azure ASO, GCP KCC) monitor Cloud APIs 24/7. They actively repair configuration drift without human intervention.
* The Dependency DAG: We use the Flux dependsOn feature to define infrastructure hierarchies. We do not use pipeline-based orchestration.
* Zero State Files: There is no Terraform State to corrupt, lock, or lose. The live Cloud API is the only source of truth.

## Architectural Topology
We use a hub-and-spoke model where a single Management Cluster acts as the control plane for all cloud environments:

```text
       [ GIT REPOSITORY (Source of Truth) ]
                     |
                     | (Flux Pulls Manifests)
                     v
      +------------------------------------------+
      |      MANAGEMENT CLUSTER (The Brain)      |
      |------------------------------------------|
      | Flux | ACK        | ASO           | KCC  |
      +------------------------------------------+
             |               |               |
   (Provisions/Manages) (Provisions/Manages) (Provisions/Manages)
             |               |               |
      +-------------+ +-------------+ +-------------+
      | Workload 1  | | Workload 2  | | Workload 3  |
      | (EKS)       | | (AKS)       | | (GKE)       |
      | CLUSTER     | | CLUSTER     | | CLUSTER     |
      +-------------+ +-------------+ +-------------+
```

## Getting Started
To understand the technical design, architectural mandates, and step-by-step implementation phases, refer to:
[implementation_plan.md](./implementation_plan.md)

## Why Flux?
We utilize Flux over Argo CD because Flux is architecturally optimized for infrastructure lifecycle management:
- Controller-Native: Flux is a set of Kubernetes controllers, not an external UI overlay.
- Dependency Chaining: Flux dependency chaining enables a true Directed Acyclic Graph (DAG) for complex infrastructure dependencies, whereas Argo CD relies on linear Sync Waves.
- Headless & Reliable: Flux is designed for cluster-to-cluster management, which is essential for our hub-and-spoke Management vs. Workload cluster strategy.

## Repository Standards
- Refer to .gitignore to ensure no local secrets or state artifacts are ever committed.
- All code is subject to the GNU Affero General Public License v3.0 (AGPL-3.0) (see [LICENSE](https://github.com/lloydchang/gitops-infra-control-plane/blob/main/LICENSE) file).

## Open-source Software
https://github.com/lloydchang/gitops-infra-control-plane

<img width="1024" height="1024" alt="Image" src="https://github.com/user-attachments/assets/012c76ba-98f0-4513-be94-bf83691d0a9d" />

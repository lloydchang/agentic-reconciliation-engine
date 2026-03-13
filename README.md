```text
# gitops_infra_control_plane.md

# GitOps Infra Control Plane

Continuous Reconciliation Engine (CRE) for Multi-Cloud Infra

## Core Advantage

Traditional IaC tools (Terraform, CDK, CloudFormation, Bicep, ARM) run once and exit. They do not continuously enforce infrastructure state. Kubernetes operators, such as Flux, ACK, ASO, and KCC, provide 24/7 continuous reconciliation that detects and repairs configuration drift automatically.

| Approach | Traditional IaC | Continuous Reconciliation |
|----------|----------------|---------------------------|
| Operation | Run once -> Exit | Monitor 24/7 -> Automatic drift correction |
| Drift Detection | Manual `plan` runs | Automatic within minutes |

GitOps enforces configuration drift correction in Kubernetes by using a Git repository as the declarative source of truth for system state. Tools like Flux periodically reconcile Git-managed resources and restore any drift to match the Git configuration. This enables **automatic drift reconciliation**, not full operational self-healing, because runtime failures outside of Git-managed resources are handled by Kubernetes controllers and platform automation.

[IMAGE](https://github.com/user-attachments/assets/e6b4bec7-3855-4532-a06c-daadffed4911)

[Hub Spoke Diagram](docs/hub_spoke_v8.svg)

[Tier 0]                               Git repository
                               declarative source of truth
                                              | Flux pulls manifests
                                              v
         +------------------------------------------------------------------------------+
[Tier 1] |                               Hub cluster                                    |
         |  any Kubernetes distribution • Flux self-manages hub after bootstrap          |
         |------------------------------------------------------------------------------|
     _->-+--+-------------------+  +------------------+  +---------------------------+  |
    /    |  | Flux              |  | Operators        |  | Cluster API (CAPI)        |  |
   /     |  | GitOps reconcile  |  | ACK (AWS)        |  | Kubeadm provider          |  |
  |      |  | Git -> hub cluster|  | ASO (Azure)      |  | own reconciliation loop   |  |
   \     |  | SOPS/age decrypt  |  | KCC (GCP)        |  | Infra provider            |  |
    \    |  | at apply time     |  | own recon loops  |  | (Metal3 / CAPV / CAPO)    |  |
     `---+--+-------------------+  +------------------+  +---------------------------+  |
         +------------------------------------------------------------------------------+
                  |               |                |                   |
                  | ACK           | ASO            | KCC               | CAPI
                  v               v                v                   v
         +-----------------------------------------------------------------------------+
[Tier 2] |                             Spoke clusters                                  |
         |-----------------------------------------------------------------------------|
         |  +-------------+  +-------------+  +-------------+  +-------------------+   |
         |  | EKS         |  | AKS         |  | GKE         |  | Kubeadm           |   |
         |  | AWS managed |  | Azure mgd   |  | GCP managed |  | On-prem           |   |
         |  | Managed HA  |  | Managed HA  |  | Managed HA  |  | Self-managed      |   |
         |  | via ACK     |  | via ASO     |  | via KCC     |  | via CAPI          |   |
         |  | secrets via |  | secrets via |  | secrets via |  | secrets via       |   |
         |  | SOPS        |  | SOPS        |  | SOPS        |  | SOPS              |   |
         |  +-------------+  +-------------+  +-------------+  +-------------------+   |
         +-----------------------------------------------------------------------------+
              SOPS age key lives on hub -> back up once
                                        -> Flux decrypts at apply time
                                        -> spokes receive plain Secrets

Secrets strategy (SOPS: Secrets OPerationS):
  - Back up the SOPS age private key in a key vault or secrets manager
  - Secrets encrypted in Git using age public key
  - Flux decrypts at apply time using age private key (hub-only)
  - Spokes receive plain Kubernetes Secret objects without requiring a controller
    - Single age key simplifies backup vs multiple Sealed Secrets keys
    - Flux handles decryption natively

Alternative options:
  - Sealed Secrets: controller in each cluster
  - External Secrets Operator (ESO) with [Azure Key Vault](https://learn.microsoft.com/en-us/azure/key-vault/), [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/), or [GCP Secret Manager](https://cloud.google.com/secret-manager)

TBD notes:
  - Hub distribution is flexible (any conformant Kubernetes cluster)
    - Flux bootstrapped manually once; thereafter self-managed via Git
    - Circular dependency: Flux manages the hub cluster it runs on (by design)
  - Spoke 4 infra provider TBD: Metal3 (bare metal), CAPV (vSphere), CAPO (OpenStack)

## When to Use This Solution

### Good Fit
- Multi-cloud infrastructure requiring coordinated operations
- Large-scale deployments needing autonomous optimization
- Brownfield migrations with gradual modernization

### Not a Good Fit
- Simple single-app deployments
- Emergency migrations without runway
- Small teams with basic infrastructure needs
- Cost-sensitive projects with limited budget

> Important: Complete the [Problem-Solution Fit Assessment](./docs/PROBLEM-SOLUTION-FIT.md) before implementation.

## Key Features

- Continuous Reconciliation: 24/7 drift detection and correction
- Multi-Cloud Integrations: AWS, Azure, GCP with native controllers
- DAG Dependencies: Explicit dependency management with Flux
- Agent Orchestration: Optional AI-enhanced consensus agents
- Multi-Language Extensions: Go, Python, Rust, TypeScript, C#, Java

## Documentation

### Essential Reading
1. [Problem-Solution Fit](./docs/PROBLEM-SOLUTION-FIT.md) - When and how to use this solution
2. [Architecture](./docs/ARCHITECTURE.md) - Technical architecture overview
3. [Implementation Plan](./docs/implementation_plan.md) - Step-by-step deployment guide

### Implementation Examples
- [Complete Hub-Spoke](./examples/complete-hub-spoke/) - Full deployment with all features
- [Agent Orchestration](./examples/complete-hub-spoke/agent-orchestration-demo.md) - Autonomous agent coordination
- [Variants](./variants/) - Deployment variations for different scenarios

### Advanced Topics
- [AI Integration](./docs/AI-INTEGRATION-ANALYSIS.md) - Intelligent automation patterns
- [Consensus Protocols](./docs/CONSENSUS-PROTOCOL-ANALYSIS.md) - Distributed decision-making
- [Migration Strategy](./docs/LEGACY-IAC-MIGRATION-STRATEGY.md) - Converting from traditional IaC

## Contributing

[Pull Requests](https://github.com/lloydchang/gitops-infra-control-plane/pulls)

## License

This repository uses dual licensing:
- `AGPL-3.0`: Core infrastructure manifests, logic, documentation, examples, and more
  - See [LICENSE](LICENSE) file - https://www.gnu.org/licenses/agpl-3.0.html
- `Apache-2.0`: Specific sample snippets requiring user adaptations
  - See [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0)
```

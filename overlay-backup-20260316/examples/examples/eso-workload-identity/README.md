# ESO Workload Identity — Examples

Per-spoke ESO configuration for each cloud and on-prem. Each subdirectory contains:

- `helmrelease-patch.yaml` — Flux HelmRelease values patch for the ESO service account annotation
- `cluster-secret-store.yaml` — ClusterSecretStore pointing at the cloud vault
- `external-secret-example.yaml` — Example ExternalSecret (spoke team writes this)

The hub is not in the secrets path. Each spoke authenticates directly to its own cloud vault
using native workload identity. See [ESO-WORKLOAD-IDENTITY.md](../../docs/ESO-WORKLOAD-IDENTITY.md)
for setup scripts and detailed explanation.

## Directory Layout

```
eks/          EKS + IRSA + AWS Secrets Manager
aks/          AKS + Azure Managed Identity + Azure Key Vault
gke/          GKE + Workload Identity Federation + GCP Secret Manager
on-prem/      Kubeadm + HashiCorp Vault
```

# Azure Cloud Overlay

This overlay activates Azure-specific manifests when Flux reconciles `./cloud-azure`.

## Contents
- `kustomization.yaml` – includes the Azure network, cluster, workloads, and Entra identity manifests.
- Add patches under this directory to adjust resource group names, CIDRs, or secret references.

## Usage
1. Customize the referenced manifests in `control-plane/flux/` for your tenant/subscription.
2. Flux deploys them when `./cloud-azure` is listed in `control-plane/flux/kustomization.yaml`.
3. Remove the entry to clean up all Azure resources.

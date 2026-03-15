# AWS Cloud Overlay

This overlay brings AWS-specific control-plane manifests online when Flux includes `./cloud-aws` in `control-plane/flux/kustomization.yaml`.

## Contents
- `kustomization.yaml` – aggregates the existing AWS network, cluster, CA, and workload manifests.
- Add additional patches beneath this directory (e.g., `patches/` or `overlays/`) to tailor CIDRs, IAM roles, and Argo CD/Flux registrations for your account.

## Usage
1. Customize the manifests referenced in `kustomization.yaml` (network, clusters, workloads) to match your VPC/CNI needs.
2. Flux will deploy the overlay when you enable `./cloud-aws` in the parent Kustomization. Disabling the resource removes the AWS-specific objects.
3. Refer to `docs/CLOUD-OVERLAY-STRUCTURE.md` for the migration playbook and automation guidance.

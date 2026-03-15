# GCP Cloud Overlay

This overlay pulls in the tenant-level GCP network, cluster, and workload directories and applies the overrides in `patches/` when Flux reconciles `./cloud-gcp`.

## Structure
- `kustomization.yaml` references the `infrastructure/tenants/gcp` directories and merges the overrides.
- `patches/network-overrides.yaml` customizes the ComputeNetwork metadata.
- `patches/gke-overrides.yaml` adjusts the cluster spec (location, node counts, network references).

## Customizing
1. Update the patch files to match your project, region, and subnet naming conventions.
2. Validate with `kustomize build control-plane/flux/cloud-gcp`.
3. Enable via `scripts/enable-cloud.sh gcp` and reconcile (`flux reconcile kustomization control-plane --with-source`).

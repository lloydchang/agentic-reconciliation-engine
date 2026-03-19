# GCP Cloud Overlay

This overlay pulls in the tenant-level GCP network, cluster, and workload directories and applies the overrides in `patches/` when Flux reconciles `./cloud-gcp`.

## Structure
- `kustomization.yaml` references the `core/resources/tenants/gcp` directories and merges the overrides.
- `patches/network-overrides.yaml` customizes the ComputeNetwork metadata.
- `patches/gke-overrides.yaml` adjusts the cluster spec (location, node counts, network references).

## Customizing
1. Update the patch files to match your project, region, and subnet naming conventions.
2. Validate with `kustomize build core/operators/flux/cloud-gcp`.
3. Enable via `core/scripts/automation/enable-cloud.sh gcp` and reconcile (`flux reconcile kustomization control-plane --with-source`).

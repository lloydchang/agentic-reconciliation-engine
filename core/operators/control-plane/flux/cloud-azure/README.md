# Azure Cloud Overlay

# Azure Cloud Overlay

This overlay brings up the Azure-specific infrastructure when Flux includes `./cloud-azure` in `core/operators/flux/kustomization.yaml`.

## Structure
- `kustomization.yaml` pulls the tenant-level network, clusters, and workload directories and applies the patch files in `patches/`.
- `patches/vnet-overrides.yaml` overrides the placeholder VNet metadata (location, owner tags).
- `patches/aks-overrides.yaml` adjusts cluster settings such as resource group, node pool size, and network CIDRs.

## Customizing
1. Review the placeholder values inside `patches/` and change them to your resource group, location, and service CIDR needs.
2. Use `kustomize build core/operators/flux/cloud-azure` to verify the generated manifests.
3. Enable the overlay via `core/scripts/automation/enable-cloud.sh azure` and reconcile Flux (`flux reconcile kustomization control-plane --with-source`).
   * Append `--emulator=enable` or `--emulator=disable` to add or remove the `local-emulator` entry when you want to flip the Azure emulator stack on top of the real overlay.

## Local emulator
If you want to test locally without provisioning real Azure resources, enable the local emulator overlay.

1. Ensure the emulator prerequisites are running (Azurite, SQL emulator, etc.).
2. Uncomment the `- local-emulator` entry in `core/operators/flux/cloud-azure/kustomization.yaml`.
3. Flux will then deploy the modules defined in `core/resources/tenants/azure/localstack`.
4. Remove the entry and reconcile Flux to clean up the emulator resources.

Flux will automatically prune the overlay when you remove `./cloud-azure` from the parent kustomization.

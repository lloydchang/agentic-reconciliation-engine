# Cloud Overlay Enablement

## Purpose

This guidance shows how to keep the repo modular so a team can start with a single Argo CD/Flux-powered cloud and, when ready, add additional clouds without a wholesale redesign. The key idea is to treat every cloud (and shared services like Crossplane) as an overlay that Flux can flip on or off by updating a single `kustomization.yaml` resource list.

## Directory layout

The repository already contains the folders that run Flux, Crossplane, and the broader control plane. Treat them as the building blocks of the overlay design:

| Layer | Description |
| --- | --- |
| `control-plane/bootstrap/` | Minimal Flux manifests used to bootstrap the hub from a bootstrap cluster. This should always be reconciled first. |
| `control-plane/flux/` | Flux/gotk components and the dynamic `Kustomization` that stitches together `core`, `crossplane`, and cloud overlays. |
| `control-plane/crossplane/` | Shared provider configs/compositions for AWS, Azure, and GCP. Keep the base compositions here and expose per-cloud overrides via the cloud overlays. |
| `control-plane/flux/cloud-<provider>/` (new) | Cloud-specific overlays (network, identity, cluster specs, Flux/Argo CD registrations, Crossplane compositions). Each overlay lives alongside the Flux manifests (`control-plane/flux/cloud-aws`, etc.) so the `kustomization.yaml` can include it with a simple relative path. |
| `control-plane/workloads/` | Applications managed by Argo CD; migrating them should not require touching the overlays. |

## Bootstrap + overlay sequence

1. **Install Flux on the bootstrap cluster** (existing EKS/AKS/GKE or a new lightweight cluster). Flux should point at `control-plane/flux/bootstrap` so it can bootstrap the hub.
2. **Flux reconciles `control-plane/flux/core`** which contains Crossplane base, Flux/Git credentials, Argo CD bootstrap (if not already installed), and shared secrets. This is the “always-on” part of the control plane.
3. **Enable the cloud overlay that corresponds to your starting cloud**: update the Flux `Kustomization` under `control-plane/flux/kustomization.yaml` so it includes `./cloud-aws` (or `./cloud-azure`, `./cloud-gcp`). Flux will then provision the provider-specific resources while leaving the other overlays dormant.
4. **Migrate workloads**: Argo CD continues to manage applications. You can have Argo CD sync apps during the migration while Flux provisions infrastructure via the overlay. Once the new overlay cluster is ready, register it with Argo CD and switch workloads over namespace-by-namespace.
5. **Add additional clouds**: Flip on the next overlay by adding it to the same `Kustomization`'s resource list. Flux automatically reconciles the added overlay without disturbing the already enabled clouds.

## Example Flux `Kustomization`

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: control-plane
  namespace: flux-system
spec:
  interval: 5m
  path: ./control-plane
  prune: true
  sourceRef:
    kind: GitRepository
    name: control-plane
resources:
  - gotk-components.yaml
  - gotk-sync.yaml
  - image-update-automation.yaml
  - image-policy.yaml
  - jenkins-image-automation.yaml
  - secrets/
  - ./cloud-aws        # Remove/skip this entry when you do not yet have AWS
  # - ./cloud-azure    # Uncomment when you are ready to migrate/add Azure
  # - ./cloud-gcp      # Uncomment for GCP
```

The `resources` block is the only place that changes when you onboard a new cloud. Adding a new entry is equivalent to “toggling on” that cloud’s overlay.

## Enabling an overlay

1. Copy or extend the template overlay (e.g., `control-plane/flux/cloud-aws/kustomization.yaml`) and customize network/cluster values for your environment by editing the `patches/` overrides in the same directory.
2. Run `scripts/enable-cloud.sh <provider>` (or manually add `./cloud-<provider>` to `control-plane/flux/kustomization.yaml`) so Flux includes that overlay. To toggle the Azure emulator overlay, add `--emulator=enable` or `--emulator=disable` when calling `scripts/enable-cloud.sh azure`; the script now updates `control-plane/flux/cloud-azure/kustomization.yaml` accordingly.
3. Run `flux reconcile kustomization control-plane --with-source` to force a sync and validate the overlay resources reach `Ready`. Inspect Crossplane `Composition` and `Managed` resources as the overlay provisions infra.
4. Register any new clusters created by Crossplane with Argo CD (`argocd cluster add ...`), so application workloads can be graduated to the new target.
5. Monitor Flux/Argo CD health; you can remove the overlay entry later if you need to roll back (Flux will cascade-delete the overlay resources).

## Crossplane layering

Crossplane remains optional until you want multi-cloud workloads. Start with a minimal Crossplane overlay that injects provider configs from `control-plane/crossplane/providers.yaml`. When you are ready to provision cloud-managed resources in the new overlay, enable the matching `crossplane` compositions from `control-plane/crossplane/compositions/`. Keep provider-agnostic Claim templates in the base `crossplane` directory and override them via the per-cloud overlay.

## Automation/Script patterns

These helper scripts can be placed under `scripts/` or `control-plane/scripts/`:

| Script | Purpose |
| --- | --- |
| `scripts/bootstrap-hub.sh` | Install Flux on the bootstrap cluster and wait for `control-plane/flux/core` to sync. |
| `scripts/enable-cloud.sh <provider>` | Patches `control-plane/flux/kustomization.yaml` to add `cloud-<provider>` and waits for the overlay to reach `Ready`. |
| `scripts/export-argocd-state.sh` | Dumps Argo CD Applications, ApplicationSets, and cluster registrations so the migration runbook can reference the manifest state. |
| `scripts/migrate-app.sh <app-name> <target-context> [namespace]` | Adjusts an Argo CD application’s destination to the cluster referenced by the kubeconfig context, syncs it, and waits for healthy reconciliation. |
| `scripts/export-argocd-state.sh` | Dumps Argo CD Applications, ApplicationSets, and clusters into `/tmp/argocd-export-*` so the migration runbooks can reference the exact state before switching overlays. |

Automating these patterns turns the overlay model into an executable migration pipeline: bootstrap the hub, turn on one overlay for your source cloud, then flip on the next overlay when you are ready for the following cloud.

## Documentation pointers

- Reference [docs/BOOTSTRAP-CLUSTER.md](docs/BOOTSTRAP-CLUSTER.md) for details about bootstrap sizing and recovery.
- Use [docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) as the higher-level playbook; add links there to this overlay-centric doc.
- Keep [README.md](README.md) or [docs/README-INTEGRATION.md](docs/README-INTEGRATION.md) updated with the “one overlay per cloud” pattern so new contributors understand the management strategy immediately.

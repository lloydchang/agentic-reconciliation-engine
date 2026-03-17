# Azure AKS → Multi-Cloud Migration Playbook

This runbook adapts the EKS migration flow for teams starting from Azure AKS + Argo CD. It follows the same phases (audit, bootstrap, overlay, cutover, add clouds) while highlighting the Azure specifics so the transition remains modular.

## Phases

1. **Audit & export existing state**
2. **Bootstrap the hub/Flux control plane**
3. **Enable the Azure overlay**
4. **Register workload clusters & cut over apps**
5. **Add other clouds / Crossplane resources**

## 1. Audit & export existing state

- Capture Argo CD applications/datasets:

  ```bash
  argocd app list --output yaml >/tmp/argocd-apps.yaml
  argocd app set --output yaml >/tmp/argocd-appsets.yaml
  kubectl get secret -n argocd argocd-secret -o yaml >/tmp/argocd-secret.yaml
  ```

- Export existing cluster registration and Azure context:

  ```bash
  argocd cluster list --output yaml >/tmp/argocd-clusters.yaml
  az account show --output yaml >/tmp/az-account.yaml
  az aks show --resource-group <rg> --name <cluster> --output yaml >/tmp/aks-cluster.yaml
  ```

- Record Git repo URLs, TLS secrets, and Azure RBAC assignments for mapping into the new setup.

## 2. Bootstrap the hub/Flux control plane

1. Use the existing AKS cluster as the hub, or create a dedicated hub/bootstrap cluster per [docs/BOOTSTRAP-CLUSTER.md](docs/BOOTSTRAP-CLUSTER.md).
2. Bootstrap Flux pointing at this repo:

   ```bash
   flux bootstrap github \
     --owner=<org> \
     --repository=gitops-infra-control-plane \
     --branch=main \
     --path=core/operators/flux \
     --personal
   ```

3. Confirm core Kustomization is `Ready` (`flux get kustomization control-plane`).
4. Keep Argo CD running to ensure apps stay healthy while Flux reconciles the control plane artifacts.

## 3. Enable the Azure overlay

1. Tailor `core/operators/flux/cloud-azure/kustomization.yaml`’s references to the correct resource group, network, and workload definitions. Update any `azure-*.yaml` manifests for your subscription, virtual network, and node pools.
2. Activate the overlay:

   ```bash
   core/core/automation/ci-cd/scripts/enable-cloud.sh azure
   flux reconcile kustomization control-plane --with-source
   ```

3. Validate overlay sync status, Crossplane compositions, and Azure managed resources (virtual networks, AKS clusters) via `az aks list`, `kubectl get managed`, or `flux get kustomization control-plane`.

## 4. Register workload clusters & cut over apps

1. When the overlay provisions AKS clusters, register them with Argo CD:

   ```bash
   argocd cluster add <context> --name aks-<region> --yes
   ```

2. Adjust Application/ApplicationSet destinations to include the new AKS context and region-specific selectors.
3. Optionally use `core/core/automation/ci-cd/scripts/migrate-app.sh <app> <context>` to update each app and trigger sync/health checks.
4. Gradually disable legacy workloads once health is confirmed on the new cluster; keep the old Argo CD apps as a rollback path until cutover is fully validated.

## 5. Add other clouds / Crossplane resources

1. Enable `core/core/automation/ci-cd/scripts/enable-cloud.sh aws|gcp` when ready to add more clouds; Flux automatically syncs the overlay resources.
2. Deploy Crossplane compositions from `core/operators/crossplane/compositions/` as needed; only enable provider-specific claims when required.
3. Re-run `flux reconcile kustomization control-plane --with-source` after any overlay change and verify `flux get kustomization control-plane` remains `Ready`.

## Rollback guidance

- Remove `./cloud-azure` from the Flux kustomization or revert the commit to cleanly remove the Azure overlay.
- Keep the old AKS + Argo CD cluster running until you are certain the Flux-enabled control plane is stable.

## Automation via migration wizard

Invoke `core/core/automation/ci-cd/scripts/migration_wizard.py` during this runbook to make the overlay ordering, emulator toggle, helper scripts, and CI gate part of an automated workflow. Sample command:

```bash
./core/core/automation/ci-cd/scripts/migration_wizard.py \
  --repo-url git@gitlab.example.com:org/gitops-infra-control-plane.git \
  --branch migration-aks \
  --connector gitlab \
  --overlay-order ./bootstrap ./hub ./cloud-azure \
  --ci-gate ./core/core/automation/ci-cd/scripts/prerequisites.sh \
  --helper-script ./core/core/automation/ci-cd/scripts/enable-cloud.sh
```

Use `--connector=azure-devops` or another connector depending on your Git host, and pass `--emulator=enable` if you still need the local emulator while the real overlay is active. The wizard now orchestrates the entire automation flow described in this runbook.

## Validation checklist

- [ ] Flux kustomization `control-plane` stays `Ready`.
- [ ] New AKS clusters appear as `Managed` resources or via `az aks list`.
- [ ] Argo CD apps stay healthy and sync to the new cluster contexts.
- [ ] Overlay changes (flux reconciliation) succeed without errors.
- [ ] Provider-specific patches are tracked in `core/operators/flux/cloud-azure/`.
If you are using a local Azure emulator rather than a real subscription, include the optional emulator overlay before you enable the full cloud overlay:

1. Run `core/core/automation/ci-cd/scripts/enable-cloud.sh azure --emulator=enable` so Flux adds the `local-emulator` entry and applies the emulator resources.
2. Apply the overlay to spin up the emulator resources via Flux.
3. When you are ready to target a real AKS cluster, run `core/core/automation/ci-cd/scripts/enable-cloud.sh azure --emulator=disable` (or edit `core/operators/flux/cloud-azure/kustomization.yaml`) and re-run the Azure overlay.

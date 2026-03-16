# GCP GKE → Multi-Cloud Migration Playbook

This runbook adapts the multi-cloud migration to teams starting from Google Cloud GKE + Argo CD. Follow the same five phases but swap in GCP-specific commands and validation checks while keeping the overlay structure modular.

## Phases

1. **Audit & export existing state**
2. **Bootstrap the hub/Flux control plane**
3. **Enable the GCP overlay**
4. **Register workload clusters & cut over apps**
5. **Add other clouds / Crossplane resources**

## 1. Audit & export existing state

- Capture Argo CD applications:

  ```bash
  argocd app list --output yaml >/tmp/argocd-apps.yaml
  argocd app set --output yaml >/tmp/argocd-appsets.yaml
  kubectl get secret -n argocd argocd-secret -o yaml >/tmp/argocd-secret.yaml
  ```

- Export cluster registrations and GCP context:

  ```bash
  argocd cluster list --output yaml >/tmp/argocd-clusters.yaml
  gcloud config list --format yaml >/tmp/gcloud-config.yaml
  gcloud container clusters describe <cluster> --region <region> --format yaml >/tmp/gke-cluster.yaml
  ```

- Collect service account keys, workload identity bindings, and Git repo credentials for reconstitution later in the hub.

## 2. Bootstrap the hub/Flux control plane

1. Use the existing GKE cluster as the hub or spin up a dedicated bootstrap cluster ([docs/BOOTSTRAP-CLUSTER.md](docs/BOOTSTRAP-CLUSTER.md)).
2. Bootstrap Flux:

   ```bash
   flux bootstrap github \
     --owner=<org> \
     --repository=gitops-infra-control-plane \
     --branch=main \
     --path=control-plane/flux \
     --personal
   ```

3. Confirm `control-plane/flux` Kustomization is `Ready`.
4. Keep the current Argo CD apps running during this process to avoid downtime.

## 3. Enable the GCP overlay

1. Update `control-plane/flux/cloud-gcp/kustomization.yaml` or add patches that configure project IDs, regions, node pools, and vertex/AI workloads.
2. Run the overlay helper:

   ```bash
   scripts/enable-cloud.sh gcp
   flux reconcile kustomization control-plane --with-source
   ```

3. Validate:
   - `flux get kustomization control-plane` lists the GCP overlay and reports `Ready`.
   - GCP resources (networks, GKE clusters) appear via `gcloud container clusters list` and `kubectl get managed -A`.
   - Crossplane `Composition` resources (if used) are `Ready`.

## 4. Register workload clusters & cut over apps

1. Register the new GKE clusters with Argo CD:

   ```bash
   argocd cluster add <context> --name gke-<region> --yes
   ```

2. Adjust ApplicationSets/destinations to target the new contexts.
3. Use `scripts/migrate-app.sh` (or manual edits) to update workloads, then `argocd app sync` + `argocd app wait`.
4. After verifying health, decommission the old sync targets or leave them for rollback until confident.

## 5. Add other clouds / Crossplane resources

1. Flip on `scripts/enable-cloud.sh aws|azure` when ready to bring additional providers online.
2. Enable Crossplane compositions selectively from `control-plane/crossplane/compositions/`.
3. Always run `flux reconcile kustomization control-plane --with-source` after overlay changes and confirm `flux get kustomization control-plane` is healthy.

## Rollback guidance

- Remove the `./cloud-gcp` entry from the Flux kustomization (or revert the commit) to have Flux prune the GCP overlay.
- Leave the original GKE/Argo CD stack running during the transition in case you need to fall back.

## Automation via migration wizard

Use `scripts/migration_wizard.py` to automate overlay ordering and CI validation while applying this runbook. Example:

```bash
./scripts/migration_wizard.py \
  --repo-url https://github.com/your-org/gitops-infra-control-plane.git \
  --branch migration-gcp \
  --connector github-enterprise-cloud \
  --overlay-order ./bootstrap ./hub ./cloud-gcp \
  --helper-script ./scripts/enable-cloud.sh \
  --ci-gate ./scripts/prerequisites.sh
```

Swap `--connector` for the Git host running your repo, add `--emulator=enable|disable` as needed, and the wizard will reorder overlays, run `scripts/enable-cloud.sh`, execute the CI gate, and push the migration branch up for review.

## Validation checklist

- [ ] Flux kustomization stays `Ready` after each overlay change.
- [ ] New clusters appear under `gcloud container clusters list`.
- [ ] Argo CD apps successfully sync to the new contexts.
- [ ] Crossplane resources (if any) are `Ready`.
- [ ] Provider-specific patches are tracked under `control-plane/flux/cloud-gcp/`.

# Amazon EKS → Multi-Cloud Migration Playbook

This runbook shows how to migrate an existing single-cloud Amazon EKS + Argo CD deployment into the multi-cloud control plane without disrupting workloads. It assumes you already have an EKS cluster running Argo CD and want to introduce this repo’s Flux/Crossplane + additional clouds while keeping the current apps healthy.

## Phases

1. **Audit & export existing state**
2. **Bootstrap the hub/Flux control plane**
3. **Enable the AWS overlay**
4. **Register workload clusters & cut over apps**
5. **Add additional clouds / Crossplane resources**

Each phase includes checks and commands you can script (see `scripts/enable-cloud.sh`), making the transition repeatable and reversible.

## 1. Audit & export existing state

- Capture Argo CD apps and ApplicationSets so you can compare before/after.

  ```bash
  argocd app list --output yaml > /tmp/argocd-apps.yaml
  argocd app set \
    --output yaml > /tmp/argocd-appsets.yaml
  kubectl get secret -n argocd argocd-secret -o yaml > /tmp/argocd-secret.yaml
  ```

- Record cluster registrations (`argocd cluster list --output yaml`) and store them under version control as part of the migration checklist.
- Note Git repo URLs, TLS secrets, webhook/SSH keys, and RBAC policies so you can restore them in the new control plane if needed.

## 2. Bootstrap the hub/Flux control plane

1. Choose the hub cluster: use the existing EKS Argo CD cluster as the hub or provision a dedicated hub (the bootstrap cluster described in `docs/BOOTSTRAP-CLUSTER.md` if you want separation).
2. Install Flux so it watches this repo:

   ```bash
   flux bootstrap github \
     --owner=<org> \
     --repository=gitops-infra-control-plane \
     --branch=main \
     --path=control-plane/flux \
     --personal
   ```

3. Confirm Flux syncs the core manifests (`control-plane/flux/gotk-sync.yaml`); `flux get kustomization control-plane` should report `Ready`.
4. Ensure Argo CD continues managing workloads during this bootstrap. You can run `argocd app list` to validate the apps remain healthy while Flux converges the control plane manifests.

## 3. Enable the AWS overlay

1. Customize `control-plane/flux/cloud-aws/kustomization.yaml` for your VPC, node pools, IAM policies, and Argo CD registration needs (patch the referenced manifests if necessary).
2. Run the helper that edits the parent kustomization and starts reconciliation:

   ```bash
   scripts/enable-cloud.sh aws
   flux reconcile kustomization control-plane --with-source
   ```

3. Validate the overlay:
   - `flux get kustomization control-plane` shows the overlay resources listed and `Ready`.
   - Crossplane `Composition`/`Managed` resources (if any) under `control-plane/crossplane/` reach `Ready`.
   - New IAM roles, VPCs, or node pools appear via `terraform`/`Crossplane` status in the provider namespace.

## 4. Register workload clusters & cut over apps

1. Inspect the cluster(s) the overlays created (e.g., Argo CD cluster entries created via `gcp-clusters.yaml` or `aws-clusters.yaml`). You can list them with `kubectl get managed -A` if Crossplane produced them.
2. Register any new clusters with Argo CD so apps can target the new environment:

   ```bash
   argocd cluster add <context-name> --name <stable-label> --yes
   ```

3. Update Application/ApplicationSet specs to include the new cluster (`clusters:` selectors or `destinations`). Optionally, script this:

   ```bash
   scripts/migrate-app.sh <app-name> <new-cluster-context>
   argocd app sync <app-name>
   argocd app wait <app-name> --health
   ```

4. After you verify the app health on the new cluster, disable the old sync targets gradually (e.g., remove the legacy Argo CD app, or let the overlay takeover while keeping the old Argo CD running for rollback).

## 5. Add additional clouds / Crossplane resources

1. Repeat Phase 3 with `scripts/enable-cloud.sh <azure|gcp>` to bring up Azure or GCP overlays; Flux will provision their manifests while the hub keeps running.
2. Use `control-plane/crossplane/compositions/` to instantiate managed resources (databases, buckets). Only enable the compositions your workloads need, keeping Crossplane optional until you wish to manage infra via compositions.
3. Whenever you add a new cloud overlay, rerun `flux reconcile kustomization control-plane --with-source` and re-check `flux get kustomization control-plane`.

## Rollback guidance

- Remove the overlay entry from `control-plane/flux/kustomization.yaml` (or run `git revert` if you committed the change). Flux will prune the overlay’s resources, giving you a clean rollback path.
- Keep the original single-cloud Argo CD instance running until you are confident the new multi-cloud stacks are stable to avoid downtime.

## Automation via migration wizard

Run the migration wizard automation helper as part of this playbook to ensure the overlay ordering, emulator toggles, and CI gate execute in one shot. Example:

```bash
./scripts/migration_wizard.py \
  --repo-url git@github.com:your-org/gitops-infra-control-plane.git \
  --branch migration-eks \
  --connector gitlab \
  --overlay-order ./bootstrap ./hub ./cloud-aws \
  --helper-script ./scripts/enable-cloud.sh \
  --ci-gate ./scripts/bootstrap.sh
```

Adjust `--connector` to match your Git host (`azure-devops`, `github-enterprise-server`, `bitbucket-cloud`, etc.), and add `--emulator=enable`/`disable` when you want the local emulator stacked. The wizard handles overlay ordering, toggles the emulator, runs the helper scripts listed in the command, executes the CI gate, and pushes the branch for an automated migration flow.

## Validation checklist

- [ ] Flux `kustomization control-plane` stays `Ready` after each change.
- [ ] Crossplane/composition resources report `Ready`.
- [ ] Argo CD applications remain healthy after cutover (`argocd app wait --health`).
- [ ] New clusters registered with Argo CD are used by at least one ApplicationSet.
- [ ] Overlay directories (`control-plane/flux/cloud-*`) contain provider-specific patches committed alongside the playbook.

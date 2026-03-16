# Migration Wizard Architecture

This document records the migration wizard’s design so the tool can orchestrate the overlay order, helper scripts, CI gate, and host-specific connectors in a platform-agnostic way.

## Core components

- **Orchestrator (`scripts/migration_wizard.py`)**: Drives the ordered overlay list, invokes helper scripts (`scripts/enable-cloud.sh`, export/migrate helpers), runs the CI policy gate (Conftest + kubeconform), and communicates status to the user.
- **Overlay manager**: Reads an ordered manifest (e.g., `control-plane/flux/overlay-order.txt`) and rewrites `control-plane/flux/kustomization.yaml` so bootstrap, hub, clouds, emulators, and on-prem overlays appear in the desired order without conflicts.
- **Emulator toggles**: The wizard can enable/disable the Azure/GCP/AWS emulator entries automatically by calling `scripts/enable-cloud.sh <provider> --emulator=enable|disable` or the generic `--toggle` option for other lines.
- **Automation hooks**: The wizard reuses existing helper scripts and will call future ones (`scripts/apply-overlay-order.sh`, `scripts/overlay-logician.py`) to fulfill tasks like ordering, validation, and state export.
- **CI gate executor**: Wraps the same policy checks referenced in [docs/CI-POLICY-GATE.md](docs/CI-POLICY-GATE.md) so every migration path runs schema/annotation/policy validation before changes are pushed.
- **Git host connectors**: Pluggable adapters handle cloning, branching, pushing, and opening merge requests against GitHub Enterprise, GitLab, Azure DevOps, Bitbucket, Gitea, CodeCommit, or any other Git service. The wizard delegates all Git operations to the connector via a stable interface (`clone()`, `push()`, `create_pr()`), so adding a new platform is a matter of implementing that interface.
  - **Azure DevOps** specifically requires `AZURE_DEVOPS_TOKEN`, `AZURE_DEVOPS_ORG`, and `AZURE_DEVOPS_PROJECT` environment variables plus the `az repos pr create` command. The connector uses the token to clone the repo and the Azure CLI to open the pull request.
  - **GitHub Enterprise Server** needs `GITHUB_ENTERPRISE_TOKEN` and `GITHUB_ENTERPRISE_HOST`.
  - **GitHub Enterprise Cloud** is the SaaS offering you get when you host repositories on `github.com`. For the wizard, that means you can simply set `GITHUB_ENTERPRISE_TOKEN`, leave `GITHUB_ENTERPRISE_HOST` empty, and use `gh pr create` against `github.com`—it behaves exactly like “GitHub.com”, just under the Enterprise Cloud branding.
  - **GitLab** requires `GITLAB_TOKEN` (and optional `GITLAB_HOST`, default `gitlab.com`); point `GITLAB_HOST` to your GitLab on Google Cloud, self-managed cluster, or other managed instance so the connector clones via that host and calls its Merge Request API via `curl`.
  - **Bitbucket Data Center** requires `BITBUCKET_DC_HOST`, `BITBUCKET_DC_USER`, and `BITBUCKET_DC_TOKEN`; the connector authenticates via https and creates pull requests via the REST API.
  - **Bitbucket Cloud** requires `BITBUCKET_USER` and `BITBUCKET_TOKEN`; the connector uses https cloning with credentials and calls the Bitbucket Cloud Pull Request API.
  - **GCP Secure Source Manager** (Cloud Source Repositories) uses the standard gcloud git credential helper; the connector runs `git clone`/`push` and documents that PRs must be opened via the GCP Console because there is no centralized CLI.
  - For hosts that can’t open PRs in-platform (CodeCommit, Secure Source Manager), use `scripts/open-gh-console-pr.sh` after the wizard finishes to get the console URL where you can create the pull request manually.
  - **AWS CodeCommit** works via the standard HTTPS git credential helper; clone/push actions use `git`, and PRs must be opened manually through the AWS console because CodeCommit lacks a unified CLI-forced PR flow.
- **Migration guides**: The wizard references the overlay documentation and migration playbooks (EKS/AKS/GKE) to drive the user through the recommended steps (audit → bootstrap → overlay → cutover), keeping the experience consistent regardless of the underlying Git host.

## Execution flow

1. Gather inputs (repo URL, branch name, desired overlay order, emulator toggles, CI gate config).
2. Ask the connector to clone/sync the repo and check out a feature branch.
3. Reorder `control-plane/flux/kustomization.yaml` based on the overlay plan, enabling emulator entries as requested.
4. Run helper scripts (`scripts/enable-cloud.sh`, `scripts/export-argocd-state.sh`, `scripts/migrate-app.sh`) per the migration playbooks.
5. Execute the CI policy gate locally.
6. Ask the connector to push the branch and, if supported, open a merge request/PR; otherwise, print manual merge instructions.

## Automation integration

- Use `scripts/migration_wizard.py` directly from the EKS/AKS/GKE playbooks (or other migration runbooks) to keep overlay ordering, emulator toggles, and CI validation automated. Each runbook can call the wizard with the desired overlay order, helper scripts, CI gate command, and connector flag (e.g., `--connector=gitlab --overlay-order ./bootstrap ./hub ./cloud-azure ...`). Because the wizard reorders overlays itself and exposes the connector interface, it becomes the automation helper for every migration step, ensuring the documented flow executes in one guided session.

## Extensibility

- Each Git host connector keeps implementation details isolated so the same wizard drive logic works for GitHub Enterprise, GitLab, Azure DevOps, Bitbucket, etc.
- The overlay manager makes no assumptions about the underlying infrastructure—additive overlays always merge and can be re-ordered without dependency collisions.
- Additional automation (e.g., the `scripts/overlay-logician.py` verification tool) can be wired into the wizard’s flow without changing the core logic, keeping the architecture modular and maintainable.

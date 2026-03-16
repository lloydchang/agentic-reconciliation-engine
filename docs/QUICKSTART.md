# Quickstart

This repository is built around a POSIX automation stack. To get started quickly:

1. **Choose a shell.** macOS/Linux already ship a POSIX shell. On Windows, install and use WSL (see `docs/WINDOWS-COMPATIBILITY.md`), Git Bash, msys2, or another bash-aware terminal that supports `bash`, `set -euo pipefail`, `mkdir -p`, `tee`, and Python 3.
2. **Install prerequisites.** Ensure `git`, `bash`, `curl`, `python3`, `pip`, `kubectl`, `helm`, `yq`, `jq`, and other CLI tooling are on your PATH. Running `scripts/prerequisites.sh` verifies versions, environment variables, and the skill suite.
3. **Clone and configure.** Clone the repo inside your POSIX shell’s filesystem (WSL `/home`, Git Bash home, or Linux workspace). Source `scripts/prerequisites.sh` if you want to reuse its env variable checks.
4. **Run the configuration setup.**
   - `scripts/setup-gitops-config.sh` runs the local configuration workflow (`bootstrap` → migration wizard → CI gate) and stores logs in `logs/local-automation/`.
5. **Create the GitOps infrastructure.**
   - `scripts/create-bootstrap-cluster.sh` creates the lightweight bootstrap cluster for recovery
   - `scripts/create-hub-cluster.sh` provisions the HA hub cluster (EKS/AKS/GKE)
   - `scripts/install-crossplane.sh` installs Crossplane and cloud providers on the hub
   - `scripts/create-spoke-clusters.sh` creates spoke clusters via Cluster API
   - `scripts/run-emulator-then-cloud.sh` lets you run the migration wizard twice (`--emulator=enable` then `--emulator=disable`).
   - `scripts/migration_wizard.py` is the core orchestrator you can call directly for custom connector/overlay combinations.
6. **Verify Windows feedback.** Each entry point now sources `scripts/helpers/wsl-detect.sh` so the log shows `INFO [WSL check]` when running under WSL or a warning if you’re still in a native Windows shell.
7. **Review logs.** Check `logs/local-automation/latest-summary.json` and the `.log` files in `logs/local-automation/` to confirm the configuration setup completed and to troubleshoot failures.

For an in-depth architecture overview, deployment guidance, and the full list of documentation links, see `docs/OVERVIEW.md`.

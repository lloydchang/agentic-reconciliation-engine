# Quickstart

This repository is built around a POSIX automation stack. To get started quickly:

1. **Choose a shell.** macOS/Linux already ship a POSIX shell. On Windows, install and use WSL (see [docs/WINDOWS-COMPATIBILITY.md](docs/WINDOWS-COMPATIBILITY.md)), Git Bash, msys2, or another bash-aware terminal that supports `bash`, `set -euo pipefail`, `mkdir -p`, `tee`, and Python 3.
2. **Install prerequisites.** Ensure `git`, `bash`, `curl`, `python3`, `pip`, `kubectl`, `helm`, `yq`, `jq`, and other CLI tooling are on your PATH. Running `core/scripts/automation/prerequisites.sh` verifies versions, environment variables, and the skill suite.
3. **Clone and configure.** Clone the repo inside your POSIX shell's filesystem (WSL `/home`, Git Bash home, or Linux workspace). Source `core/scripts/automation/prerequisites.sh` if you want to reuse its env variable checks.
4. **Run the configuration setup.**
   - `core/scripts/automation/setup-gitops-config.sh` runs the local configuration workflow (`bootstrap` → migration wizard → CI gate) and stores logs in `logs/local-automation/`.
5. **Create the Agentic Reconciliation Engine.**
   - `core/scripts/automation/create-bootstrap-cluster.sh` creates the lightweight bootstrap cluster for recovery
   - `core/scripts/automation/create-hub-cluster.sh` provisions the HA hub cluster (EKS/AKS/GKE)
   - `core/scripts/automation/install-crossplane.sh` installs Crossplane and cloud providers on the hub
   - `core/scripts/automation/create-spoke-clusters.sh` creates spoke clusters via Cluster API
   - `core/scripts/automation/run-emulator-then-cloud.sh` lets you run the migration wizard twice (`--emulator=enable` then `--emulator=disable`).
   - `core/scripts/automation/migration_wizard.py` is the core orchestrator you can call directly for custom connector/overlay combinations.
6. **Verify Windows feedback.** Each entry point now sources `core/scripts/automation/helpers/wsl-detect.sh` so the log shows `INFO [WSL check]` when running under WSL or a warning if you're still in a native Windows shell.
7. **Review logs.** Check `logs/local-automation/latest-summary.json` and the `.log` files in `logs/local-automation/` to confirm the configuration setup completed and to troubleshoot failures.

For an in-depth architecture overview, deployment guidance, and the full list of documentation links, see [docs/OVERVIEW.md](docs/OVERVIEW.md).

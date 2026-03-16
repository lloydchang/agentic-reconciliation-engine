# Contributing to GitOps Infra Control Plane

Thanks for helping keep this multi-cloud control plane documented, tested, and reliable. Before you open a PR, please review the following guidelines.

## Workflow
1. Work on a topic branch prefixed with `codex/`.
   - If you aren’t using Codex (Claude Code, Windsurf, Cursor, VS Code terminal, etc.), the same workflow still applies—run the scripts inside the POSIX shell you’ve chosen and follow the remaining steps below.
2. Run `scripts/prerequisites.sh` in your shell to validate the skill set, tooling versions, and environment variables.
3. Execute any relevant automation (e.g., `scripts/run-local-automation.sh`, `scripts/run-emulator-then-cloud.sh`, or `scripts/migration_wizard.py`) from the same shell to confirm the new behavior works end to end.
4. Capture logs under `logs/local-automation/` and ensure the helper scripts report `INFO [WSL check]` when running inside WSL or the appropriate warning when running from another Windows shell.
5. Submit a PR with a clear description, link to the affected docs, and evidence of the successful automation run.

## Windows contributors
- This repository ships bash-first automation, so we always run scripts inside a POSIX layer on Windows. WSL is the recommended experience; consult [docs/WINDOWS-COMPATIBILITY.md](docs/WINDOWS-COMPATIBILITY.md) for the quick-start (`wsl --install`, select a distro, install tooling) and the automatic shell detection helper that logs `WSL_ENVIRONMENT` vs. `WINDOWS_SHELL_ENVIRONMENT`.  
- If WSL cannot be enabled, any Linux host (GitHub Codespaces, Azure/Linux VM, etc.) is the safest fallback because it already satisfies the POSIX requirements (`bash`, `python3`, `set -euo pipefail`, `mkdir -p`, etc.).  
- Native Windows shells (PowerShell/CMD) are not supported; use Git Bash/msys2/Cygwin only if you enable `core.symlinks true` and accept occasional path translation quirks—the helper warning will remind you before running validation.
- Whether you're running the automation from Codex, Claude Code/Windsurf, Cursor, the VS Code terminal, or another tool, the same shell requirements apply: open a POSIX shell, run `scripts/prerequisites.sh`, and let the detection helper report `INFO [WSL check]` when you're in WSL or warn if you're still on an unsupported Windows prompt.

## Documentation updates
- When you change scripts or automation, update the corresponding compatibility guide ([docs/WINDOWS-COMPATIBILITY.md](docs/WINDOWS-COMPATIBILITY.md), [docs/SHELL-COMPATIBILITY.md](docs/SHELL-COMPATIBILITY.md), etc.) so every platform stays aligned.  
- If you add new Windows entry points or onboarding steps, make sure they source `scripts/helpers/wsl-detect.sh` and report their environment so we keep the experience consistent for contributors on all platforms.

## Tests & validation
- Run the existing CI/lint/build pipelines (`npm test`, `npm run lint`, `npm run build`, etc.) from the same shell you develop in to prove tooling parity.  
- When documenting Windows behavior, mention the WSL quick-start snippet and include a link back to [docs/WINDOWS-COMPATIBILITY.md](docs/WINDOWS-COMPATIBILITY.md) so future contributors can find it easily.

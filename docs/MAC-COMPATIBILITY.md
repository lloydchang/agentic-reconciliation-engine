# macOS Compatibility Guide

This repository's automation is fully compatible with macOS as long as you use a bash-compatible shell (the default macOS Terminal/zsh shell qualifies). The scripts (`core/scripts/automation/prerequisites.sh`, `core/scripts/automation/migration_wizard.py`, `core/scripts/automation/run-local-automation.sh`, etc.) rely on POSIX tools, so no special emulator or compatibility layer is needed on macOS. This guide highlights the extra checks that macOS users should perform before running the zero-touch workflow.

## 1. Install prerequisites

- **Homebrew**: Install Homebrew if you haven’t already (`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`).
- **Required CLI tools** via Homebrew:

  ```bash
  brew install az awscli gh git jq yq kubectl helm fluxcd/tap/flux
  ```

- **Python 3**: macOS ships with Python 2; install Python 3 if you don’t already (`brew install python`), and ensure `python` resolves to Python 3 (`brew link python --overwrite`).

## 2. Environment setup

- Clone the repository and `cd` into it from your default shell.  
- Export the same environment variables used on Linux/WSL (see `core/scripts/automation/prerequisites.sh`). You can add them to `~/.zshrc`/`~/.bash_profile` so the zero-touch script sees them automatically.  
- Verify `git config --global core.autocrlf input` so that Git preserves LF line endings (default on macOS).

## 3. Running zero-touch automation

```bash
cd /path/to/agentic-reconciliation-engine
core/scripts/automation/run-local-automation.sh
```

Because macOS shells understand `bash`, `mkdir`, `tee`, `python`, etc., the same zero-touch script described in the README works out of the box. The script logs to `logs/local-core/automation/ci-cd/` so you can validate each phase (bootstrap check, migration wizard run, CI gate).

## 4. Validation suggestions

1. Run `core/scripts/automation/prerequisites.sh` to ensure all tool versions meet expectations.  
2. Run `core/scripts/automation/run-local-automation.sh` to exercise the Azure emulator/GitHub path, capturing logs for each command.  
3. Inspect `logs/local-core/automation/ci-cd/migration-wizard.log` to ensure the CI gate (kubeconform, Conftest) completed successfully.  

macOS users can therefore treat this repo exactly as on Linux—no extra wrapper or emulator layer is required.

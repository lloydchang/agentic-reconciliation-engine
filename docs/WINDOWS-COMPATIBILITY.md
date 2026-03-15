# Windows Compatibility Guide

This repo ships the same automation for macOS, Linux, and Windows—provided the Windows host uses
a POSIX-compatible environment such as **WSL** (Windows Subsystem for Linux), **Git Bash**, or another
bash-aware shell. The underlying scripts (`scripts/bootstrap.sh`, `scripts/migration_wizard.py`,
`scripts/run-local-automation.sh`, etc.) rely on familiar UNIX utilities (`bash`, `mkdir -p`, `tee`,
`python`, etc.), so they run on Windows only if the shell beneath them understands those commands.
This guide explains how to achieve that compatibility in a zero-touch way.

## 1. Choose your Windows shell

- **WSL (recommended)**  
  1. Install a WSL distribution (Ubuntu, Debian, etc.) via `wsl --install` or Microsoft Store.  
  2. Open the distro, install dependencies (`sudo apt update && sudo apt install -y bash curl git jq yq
  kubectl helm python3 python3-pip pika`), and clone the repo into the Linux filesystem (`~/workspace`).  
  3. Use the WSL shell to run all scripts exactly like you would on Linux.

- **Git Bash / Cygwin / msys2**  
  1. Install Git for Windows (which includes Git Bash).  
  2. Ensure `bash`, `mkdir`, `tee`, `python`, and `ssh` are on the PATH (Git Bash already provides them).  
  3. Clone the repository inside the Git Bash home directory and run scripts the same way.  
  4. If you need symlinks, enable `core.symlinks true` in Git before cloning so that `ln -s` works
  (`git config --global core.symlinks true`).

## 2. Environment bootstrap

- Export the necessary environment variables inside WSL or Git Bash the same way as on macOS/Linux.
  You can source `scripts/bootstrap.sh` while remaining in the same shell, ensuring the script can see the values.
- Ensure the `python` command you invoke maps to Python 3. If it does not, install Python 3 and add a
  symlink (`ln -s $(which python3) ~/bin/python`).
- Confirm `git` on your Windows environment respects symlinks when cloning (WSL does this by default;
  Git Bash respects `core.symlinks true`).

## 3. Running the automation locally

Once the prerequisites above are satisfied, you can run the zero-touch automation exactly as documented:

```bash
# from your bash-compatible shell (WSL/Git Bash)
cd /path/to/gitops-infra-control-plane
scripts/run-local-automation.sh
```

### WSL quick-start

If the Windows host does not yet have WSL enabled, the following commands install it and a default
distro (Ubuntu) so you can run the repo's automation:

```powershell
wsl --install
wsl --list --online             # optional: see available distro names
wsl --set-default-version 2
wsl --install -d Ubuntu
```

After the distro installs, launch it from the Start menu, install the needed tooling (`sudo apt update &&
sudo apt install -y bash curl git jq yq kubectl helm python3 python3-pip pika`), clone the repo inside the
distro, then run the scripts from that shell. This ensures the helper logs report WSL and avoids the
native Windows warning.

The helper script runs `scripts/bootstrap.sh`, which validates CLI tooling, and then calls
`scripts/migration_wizard.py` with the Azure emulator + GitHub connector sequence. Because both scripts
are bash-compatible, Windows sees them as just another shell automation.

## 4. Git host connectors and PR flow

- The GitHub connector uses the GitHub CLI (`gh`), which is available on Windows. Install GitHub CLI for
  Windows and make sure it is on the PATH inside the shell you use.
- If you use a Git host or emulator that lacks CLI PR support (e.g., CodeCommit in the future), the same
  manual steps described in the migration wizard doc apply: open the console link printed at the end of the run.

## 5. Validation and testing

1. Run `scripts/bootstrap.sh` from your Windows shell; everything should pass or fail with clear
   diagnostics (paths, env vars, CLI tools).  
2. Run `scripts/run-local-automation.sh`; the logs under `logs/local-automation/` provide the same
   output as on macOS/Linux.  
3. Because Windows uses the same bash environment, this also validates the `scripts/migration_wizard.py`
   path, ensuring the zero-touch scenario works identically.

If you encounter issues due to Windows line endings or path translation, re-run `git status` to confirm
there are no unwanted changes (Git Bash/WSL preserves LF by default).

## 6. Automatic WSL detection

The main automation entry points (`scripts/bootstrap.sh`, `scripts/run-local-automation.sh`, and
`scripts/run-emulator-then-cloud.sh`) now source `scripts/helpers/wsl-detect.sh`. That helper logs a warning
when the shell appears to be Windows-native (without WSL/Git Bash) and emits an informational message when
it detects WSL. It also exports `WINDOWS_SHELL_ENVIRONMENT` and `WSL_ENVIRONMENT`, so other scripts can
adjust behavior if they need to gate Windows-specific checks.

## 7. When WSL is unavailable

WSL is the best-supported experience because it is a full Linux distribution running inside Windows and
nothing in this repo needs to change when you move from macOS/Linux into WSL. If WSL is disabled or
impossible to enable in your environment, run the same automation inside any Linux host you can reach
(for example, GitHub Codespaces, an Azure/Linux VM, or any other Linux workstation/VM). Those environments
already meet the POSIX requirements (`bash`, `python3`, `set -euo pipefail`, `mkdir -p`, etc.) and avoid
the Windows tooling gaps altogether.

If a native Windows shell must be used, Git Bash, msys2, or Cygwin are still second-best alternatives,
but they may require enabling `core.symlinks true` in Git and paying attention to path translation issues;
the helper warning makes this visible before the scripts start validating tooling.

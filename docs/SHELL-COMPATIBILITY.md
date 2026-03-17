# Shell Compatibility Guide

The automation in this repository requires a POSIX-style shell that understands `bash` syntax. Scripts such as `core/core/automation/ci-cd/scripts/prerequisites.sh`, `core/core/automation/ci-cd/scripts/migration_wizard.py`, `core/core/automation/ci-cd/scripts/run-local-automation.sh`, and the helper utilities depend on:

| Feature | Requirement |
|---|---|
| Shebang `#!/usr/bin/env bash` | Use a shell that can execute Bash scripts directly (bash, zsh via `bash` invocation, WSL, Git Bash, etc.). |
| `set -euo pipefail` | The shell must honor standard `bash` safety flags to exit on failure, prevent unset variables, and preserve pipelines. |
| POSIX builtins | `mkdir -p`, `tee`, `printf`, `env`, `pwd`, `cd`, and command substitution (`$(...)`) are used throughout. |
| Redirection | `2>&1`, command pipelines, and process replacement (e.g., `cmd | tee file`) are expected. This rules out Windows PowerShell unless invoked through a Bash-compatible layer. |
| Environment inline definitions | Scripts rely on inline variable definitions + command (`VAR=value cmd`). The shell must support this syntax. |

## Recommended shells by platform

- **Linux**: Default bash (>=4) or zsh (by invoking the scripts with `bash script.sh`) works out of the box.  
- **macOS**: The default zsh shell understands these scripts, but you can install GNU bash via Homebrew (`brew install bash`) and run the scripts explicitly with `bash core/core/automation/ci-cd/scripts/...`. Set `SHELL=/bin/bash` if needed.  
- **Windows**: Use WSL, Git Bash, msys2, or another bash-compatible environment (PowerShell cannot run the scripts directly). WSL/WSL2 is fully compliant; Git Bash works once `core.symlinks true` is enabled for symlink usage.

## Version guidance

- **Bash version**: `bash` 5.x or even 4.x works fine; the scripts do not rely on newer arrays or associative features.  
- **zsh**: Because zsh is largely POSIX-compatible, just execute scripts inside `zsh` by calling `bash script.sh` or via the default `./script`.  
- **Python**: `python3` must be installed; `core/core/automation/ci-cd/scripts/migration_wizard.py` invokes the system Python interpreter. Ensure the shell’s PATH resolves `python` to the Python 3 binary.

## Additional compatibility notes

- When using alternative shells, ensure `core.autocrlf` is set to `input` so Git retains LF line endings; mismatched newline handling can break `bash` script parsing.  
- For `ln -s` usage referenced elsewhere (symlink README/AGENTS), Windows shells often need `core.symlinks true` or run inside WSL to honor symlink creation.  
- Scripts use `env` and `command -v`; these are present in every POSIX shell, but if you replace them with `which`, ensure the replacement outputs the same path format.

By documenting this shell matrix, you can confidently run the zero-touch automation on Linux, macOS, or Windows as long as your shell preserves standard POSIX behavior.

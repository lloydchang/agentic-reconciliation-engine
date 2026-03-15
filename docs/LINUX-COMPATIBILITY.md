# Linux Compatibility Guide

Linux is the default development environment for this repo, and every script was authored with Linux-compatible tooling in mind. This guide reiterates the Linux-specific checks so you are confident the zero-touch automation behaves the same whether you run it on Ubuntu, Debian, CentOS, Fedora, or another distro.

## 1. Install required packages

- Debian/Ubuntu:
  ```bash
  sudo apt update
  sudo apt install -y bash curl git jq yq python3 python3-pip kubectl helm
  ```
- RHEL/CentOS/Fedora:
  ```bash
  sudo yum install -y git jq curl python3 python3-pip
  sudo dnf install -y kubectl helm
  ```
- After installing Python 3, ensure `python` resolves to Python 3 (use `ln -s $(which python3) ~/bin/python` or adjust your PATH).
- Install `flux` (`curl -s https://fluxcd.io/install.sh | sudo bash`) if you plan to use the bootstrap CLI directly.

## 2. Environment configuration

- Clone the repo into your preferred directory and `cd` into it.
- Export the env vars referenced in `scripts/bootstrap.sh` (Azure, Git tokens, bucket names, etc.).  
- Confirm `core.autocrlf` is set to `input` or `false` so Git keeps LF endings (common defaults on Linux).

## 3. Zero-touch local run

```bash
cd /path/to/gitops-infra-control-plane
scripts/run-local-automation.sh
```

All required commands (`bash`, `mkdir`, `tee`, `python`, `conftest`, `kubeconform`, etc.) are standard on Linux, so no compatibility layer is required. The zero-touch script logs to `logs/local-automation/` for full traceability.

## 4. Verification checklist

1. `scripts/bootstrap.sh` passes (tooling, skills, CLI access).  
2. `scripts/run-local-automation.sh` completes and produces matching logs with the expected overlay order (bootstrap → hub → emulator → spoke).  
3. CI gate command inside the wrapper (`conftest test` and `kubeconform`) returns success status with no policy violations.  

Linux is therefore the reference platform for this repository’s automation; follow the same commands when you move to macOS or Windows.

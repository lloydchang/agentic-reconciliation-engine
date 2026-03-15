# GitOps Infra Control Plane

A Continuous Reconciliation Engine (CRE) for multi-cloud infrastructure that combines Flux, Crossplane, and Cluster API to keep your GitOps state enforced 24/7 across AWS, Azure, GCP, and on-prem.

## Quick links
- [Quickstart](./docs/QUICKSTART.md) — POSIX shell prerequisites, bootstrap validation, and zero-touch automation steps.
- [Overview](./docs/OVERVIEW.md) — architecture narrative, operations references, zero-touch automation, and known limitations.
- [Agent Runtime](./docs/AGENT-RUNTIME.md) — Claude Code, Codex, Antigravity, Windsurf, Cursor, VS Code + Copilot — Locally and Remotely (GitHub Codespaces via Azure), gitops-infra-control-plane
- Compatibility: [Windows](./docs/WINDOWS-COMPATIBILITY.md), [Mac](./docs/MAC-COMPATIBILITY.md), [Linux](./docs/LINUX-COMPATIBILITY.md), [Shell](./docs/SHELL-COMPATIBILITY.md) — start here before running any automation on a new platform.
- [CONTRIBUTING.md](./CONTRIBUTING.md) — workflow expectations, helper logging, and documentation requirements.

## Getting started
1. Open a POSIX shell (macOS/Linux, WSL/Git Bash, Azure Linux VM, GitHub Codespaces, etc.) before touching the automation scripts.
2. Run `scripts/bootstrap.sh` to validate tools, skill files, and environment variables.
3. Use `scripts/run-local-automation.sh` or `scripts/run-emulator-then-cloud.sh` to execute the full workflow; each script now logs whether you are in WSL or a native Windows shell.
4. Check `logs/local-automation/latest-summary.json` and the `.log` files in `logs/local-automation/` for details, then iterate on your config or documentation as needed.

For deeper architecture context, risk signals, and feature walkthrough, open `docs/OVERVIEW.md`.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for workflow guidance, Windows/WSL onboarding, and documentation expectations.

[Pull Requests](https://github.com/lloydchang/gitops-infra-control-plane/pulls)

## License

This repository uses dual licensing:
- `AGPL-3.0`: Core infrastructure manifests, logic, documentation, examples, and more
  - See [LICENSE](LICENSE) file - https://www.gnu.org/licenses/agpl-3.0.html
- `Apache-2.0`: Specific sample snippets requiring user adaptations
  - See [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0)

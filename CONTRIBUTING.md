# Contributing to Agentic Reconciliation Engine

Thanks for helping keep this multi-cloud control plane documented, tested, and reliable. Before you open a PR, please review the following guidelines.

## Getting Started

### Prerequisites

- **Operating System**: macOS, Linux, or Windows (with WSL)
- **Tools**: Git, Docker, kubectl, helm
- **Languages**: Node.js (for dashboard), Python (for scripts), Go (for infrastructure)
- **Kubernetes Cluster**: Kind, Minikube, or cloud provider

### Cloning the Repository

```bash
git clone https://github.com/lloydchang/agentic-reconciliation-engine.git
cd agentic-reconciliation-engine
```

### Initial Setup

1. Run the prerequisites check:
```bash
./core/scripts/automation/prerequisites.sh
```

2. Choose your development environment quickstart script from the [README](./README.md).

## Development Environment Setup

### Local Development with Docker

```bash
# Start development environment
docker-compose -f docker/docker-compose-temporal-new.yaml up -d

# Access services:
# Dashboard: http://localhost:8081
# API: http://localhost:5001/api
# Temporal UI: http://localhost:8080
```

### Kubernetes Development

For Kind:
```bash
./core/scripts/automation/quickstart-local-kind.sh
```

For Minikube:
```bash
./core/scripts/automation/quickstart-local-minikube.sh
```

### Installing Dependencies

```bash
# Dashboard (Node.js)
cd dashboard
npm install

# Scripts (Python)
cd core/scripts
pip install -r requirements.txt

# Infrastructure (Go)
cd infrastructure
go mod download
```

## Code Style and Linting

### JavaScript/TypeScript

- Use ESLint for linting
- Prettier for code formatting
- Run: `npm run lint` and `npm run format`

### Python

- Use Black for formatting
- Flake8 for linting
- Run: `black .` and `flake8`

### Go

- Use `go fmt` for formatting
- `go vet` for basic checks
- Run: `go fmt ./...` and `go vet ./...`

### Shell Scripts

- Use shellcheck
- Follow POSIX standards
- Run: `shellcheck scripts/*.sh`

## Testing Guidelines

### Unit Tests

- Write tests for all new functions
- Place tests in `test/` directory
- Run: `./test/run-tests.sh`

### Integration Tests

- Test end-to-end workflows
- Use Kubernetes test clusters
- Run: `./scripts/testing/integration-tests.sh`

### End-to-End Tests

- Simulate real deployments
- Use tools like Cypress for UI
- Run: `./scripts/testing/e2e-tests.sh`

### Test Coverage

- Aim for >80% coverage
- Generate reports with coverage tools

## Commit Message Format

Use conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style
- `refactor`: Code refactoring
- `test`: Testing
- `chore`: Maintenance

Examples:
- `feat(dashboard): add real-time metrics`
- `fix(api): resolve health check endpoint`

## Pull Request Process

1. **Create a Branch**: Use `git checkout -b feature/your-feature`
2. **Write Tests**: Ensure all changes are tested
3. **Update Documentation**: Update README, docs, or API docs as needed
4. **Run Validation**: Execute `./core/scripts/automation/prerequisites.sh` and relevant tests
5. **Submit PR**: Provide clear description, link issues, and evidence of testing
6. **Code Review**: Address reviewer feedback
7. **Merge**: Squash and merge after approval

### PR Checklist

- [ ] Tests pass
- [ ] Linting passes
- [ ] Documentation updated
- [ ] No breaking changes without migration guide
- [ ] Reviewed by at least one maintainer

## Workflow
1. Work on a topic branch prefixed with `codex/`.
   - If you aren't using Codex (Claude Code, Windsurf, Cursor, VS Code terminal, etc.), the same workflow still applies—run the scripts inside the POSIX shell you've chosen and follow the remaining steps below.
2. Run `core/scripts/automation/prerequisites.sh` in your shell to validate the skill set, tooling versions, and environment variables.
3. Execute any relevant automation (e.g., `core/scripts/automation/run-local-automation.sh`, `core/scripts/automation/run-emulator-then-cloud.sh`, or `core/scripts/automation/migration_wizard.py`) from the same shell to confirm the new behavior works end to end.
4. Capture logs under `logs/local-core/automation/ci-cd/` and ensure the helper scripts report `INFO [WSL check]` when running inside WSL or the appropriate warning when running from another Windows shell.
5. Submit a PR with a clear description, link to the affected docs, and evidence of the successful automation run.

## Windows contributors
- This repository ships bash-first automation, so we always run scripts inside a POSIX layer on Windows. WSL is the recommended experience; consult [docs/WINDOWS-COMPATIBILITY.md](docs/WINDOWS-COMPATIBILITY.md) for the quick-start (`wsl --install`, select a distro, install tooling) and the automatic shell detection helper that logs `WSL_ENVIRONMENT` vs. `WINDOWS_SHELL_ENVIRONMENT`.  
- If WSL cannot be enabled, any Linux host (GitHub Codespaces, Azure/Linux VM, etc.) is the safest fallback because it already satisfies the POSIX requirements (`bash`, `python3`, `set -euo pipefail`, `mkdir -p`, etc.).  
- Native Windows shells (PowerShell/CMD) are not supported; use Git Bash/msys2/Cygwin only if you enable `core.symlinks true` and accept occasional path translation quirks—the helper warning will remind you before running validation.
- Whether you're running the automation from Codex, Claude Code/Windsurf, Cursor, VS Code terminal, or another tool, the same shell requirements apply: open a POSIX shell, run `core/scripts/automation/prerequisites.sh`, and let the detection helper report `INFO [WSL check]` when you're in WSL or warn if you're still on an unsupported Windows prompt.

## Documentation updates
- When you change scripts or automation, update the corresponding compatibility guide ([docs/WINDOWS-COMPATIBILITY.md](docs/WINDOWS-COMPATIBILITY.md), [docs/SHELL-COMPATIBILITY.md](docs/SHELL-COMPATIBILITY.md), etc.) so every platform stays aligned.  
- If you add new Windows entry points or onboarding steps, make sure they source `core/scripts/automation/helpers/wsl-detect.sh` and report their environment so we keep the experience consistent for contributors on all platforms.
- Run the existing CI/lint/build pipelines (`npm test`, `npm run lint`, `npm run build`, etc.) from the same shell you develop in to prove tooling parity.  
- When documenting Windows behavior, mention the WSL quick-start snippet and include a link back to [docs/WINDOWS-COMPATIBILITY.md](docs/WINDOWS-COMPATIBILITY.md) so future contributors can find it easily.

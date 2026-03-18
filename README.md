<img width="180" height="180" alt="Image" src="https://github.com/user-attachments/assets/122d93a7-60d4-4ada-9b2e-e29bdd5e4202" />

# GitOps Infra Control Plane - README.md

A Continuous Reconciliation Engine (CRE) for multi-cloud infrastructure that combines Flux, Crossplane, and Cluster API to keep your GitOps state enforced 24/7 across EKS, AKS, GKE, and on-prem Kubernetes.

## Quick links
- [Quickstart](./docs/QUICKSTART.md) — POSIX shell prerequisites, bootstrap validation, and zero-touch automation steps.
- [Repository Setup](./core/scripts/automation/quickstart.sh) — Development environment setup and prerequisites.
- [Overlay Quick Start](./core/scripts/automation/overlay-quickstart.sh) — Overlay approach to quickstart with hooks and extensions.
- [Overlay Manager](./core/scripts/automation/overlay-manager.sh) — Complete overlay lifecycle management.
- [Overlay System](./docs/OVERLAY-QUICK-START.md) — complete overlay system with documentation, examples, and automation.
- [Overview](./docs/OVERVIEW.md) — architecture narrative, operations references, zero-touch automation, and known limitations.
- [Agent Runtime](./docs/AGENT-RUNTIME.md) — Claude Code, Codex, Antigravity, Windsurf, Cursor, VS Code + Copilot — Locally and Remotely (GitHub Codespaces via Azure), gitops-infra-control-plane
- [Compound Engineering Integration](./docs/compound-engineering-integration-plan.md) — Comprehensive integration strategy for Every Inc's Compound Engineering Plugin
- [Compound Engineering Documentation](./docs/compound-engineering-integration-documentation.md) — Complete integration documentation and implementation guide
- [Dashboard Real-Time Data System](./docs/DASHBOARD-REALTIME-DATA-SYSTEM.md) — Complete implementation guide for the AI Agents Dashboard with real-time autonomous data.
- [Dashboard Quick Reference](./docs/DASHBOARD-QUICK-REFERENCE.md) — Quick setup guide and common commands for the dashboard.
- [Dashboard Technical Implementation](./docs/DASHBOARD-TECHNICAL-IMPLEMENTATION.md) — Technical architecture and implementation details.
- [K8sGPT Consolidation](./docs/K8SGPT-CONSOLIDATION-SUMMARY.md) — Single instance per cluster architecture for all GitOps components.
- [FastAPI Migration](./docs/FLASK-TO-FASTAPI-MIGRATION-PLAN.md) — Migration plan from Flask to FastAPI for dashboard API backend.
- Compatibility: [Windows](./docs/WINDOWS-COMPATIBILITY.md), [Mac](./docs/MAC-COMPATIBILITY.md), [Linux](./docs/LINUX-COMPATIBILITY.md), [Shell](./docs/SHELL-COMPATIBILITY.md) — start here before running any automation on a new platform.
- [Critical Safety Rules](./docs/CRITICAL-SAFETY-RULES-BEST-PRACTICES.md) — Essential git safety rules, debugging knowledge, and operational best practices.
- [Agentic AI Skills Guide](./docs/AGENTIC-AI-SKILLS-GUIDE.md) — Complete catalog of 70+ AI skills and automation capabilities.
- [Task Completion Summary](./docs/TASK-COMPLETION-SUMMARY.md) — Comprehensive summary of agentic AI platform implementation.
- [CONTRIBUTING.md](./CONTRIBUTING.md) — workflow expectations, helper logging, and documentation requirements.

## Architecture Overview

This GitOps infrastructure control plane implements **advanced agentic AI capabilities** with compound engineering integration:

### Core Infrastructure
- **Consolidated K8sGPT Architecture**: Single AI analysis service per cluster in `k8sgpt-system` namespace
- **Multi-Backend Support**: Agent-memory (primary), LocalAI (fallback), OpenAI (optional)
- **Unified Service Endpoint**: `http://k8sgpt.k8sgpt-system.svc.cluster.local:8080`
- **Component Integration**: All GitOps tools (ArgoCD, Flux, Argo Workflows, etc.) use the same instance

### Agentic AI Enhancements
- **Compound Engineering Integration**: Every Inc's compound engineering methodology for exponential improvement
- **25+ Specialized Agents**: Security, performance, architecture, testing, and workflow automation
- **40+ Enhanced Skills**: Autonomous operations with learning and compounding capabilities
- **Multi-Platform Support**: Claude Code, Cursor, Windsurf, Pi, Gemini, and 10+ platforms
- **Parallel Workflow Execution**: Multi-agent coordination for complex tasks
- **Uber-Inspired Patterns**: Production-tested toil automation and async workflows
- **MCP Gateway**: Centralized secure proxying with authentication and telemetry
- **Cost Optimization**: Intelligent model selection and usage tracking

### Latest Deployment (March 2025) ✅
- **Staging Environment**: Fully deployed and validated
- **7 Toil Automation Skills**: Certificate rotation, dependency updates, security patching, backup verification, log retention, performance tuning
- **5 Code Review Skills**: PR risk assessment, automated testing, compliance validation, performance impact, security analysis
- **Core Services**: MCP gateway, parallel workflow executor, cost tracker, enhanced Pi-Mono RPC
- **Monitoring**: ServiceMonitors configured for all components
- **Validation**: All deployments rolled out successfully, integration tests passed

### Memory & Learning Systems
- **Persistent AI State**: Rust/Go/Python memory agents with SQLite persistence
- **Temporal Orchestration**: Durable workflow execution for multi-skill operations
- **Knowledge Compounding**: Each iteration makes future work easier
- **Autonomous Operation**: AI agents can run full development cycles without human intervention

**Benefits**: 75% resource reduction, 5x development velocity, 90% bug reduction, simplified management, consistent AI analysis across all components.

See [K8SGPT Consolidation Summary](./docs/K8SGPT-CONSOLIDATION-SUMMARY.md) for complete migration guide and architecture details.

## Getting started
1. Open a POSIX shell (Mac Zsh, WSL Bash, Linux Bash via GitHub Codespaces, etc.) before touching the automation scripts.
2. Run `core/scripts/automation/prerequisites.sh` to validate tools, skill files, and environment variables.
3. Use `core/scripts/automation/run-local-automation.sh` or `core/scripts/automation/run-emulator-then-cloud.sh` to execute the full workflow; each script now logs whether you are in WSL or a native Windows shell.
4. Check `logs/local-core/automation/ci-cd/latest-summary.json` and the `.log` files in `logs/local-core/automation/ci-cd/` for details, then iterate on your config or documentation as needed.

### Agentic AI Quick Start
1. Deploy to staging: `./scripts/deploy-agentic-ai-staging.sh`
2. Test individual skills: `kubectl exec -n staging deployment/certificate-rotation-skill -- python -c "print('Skill ready')"`
3. Monitor deployments: `kubectl get pods -n staging -l component=agentic-ai`
4. Access services: `kubectl port-forward svc/mcp-gateway 8080:8080 -n staging`
5. View monitoring: `kubectl get servicemonitors -n monitoring | grep agentic`
6. Check metrics: `kubectl port-forward svc/prometheus-operator 9090:9090 -n monitoring`

### Production Deployment
1. **Staging Validation**: All components deployed and tested in staging
2. **Security Review**: Comprehensive safety rules documented in `CRITICAL-SAFETY-RULES-BEST-PRACTICES.md`
3. **Monitoring Ready**: ServiceMonitors configured for all AI components
4. **Skills Catalog**: 70+ skills documented in `AGENTIC-AI-SKILLS-GUIDE.md`
5. **Cost Tracking**: Usage monitoring and optimization framework active

For deeper architecture context, risk signals, and feature walkthrough, open [docs/OVERVIEW.md](docs/OVERVIEW.md).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for workflow guidance, Windows/WSL onboarding, and documentation expectations.

[Pull Requests](https://github.com/lloydchang/gitops-infra-core/operators/pulls)

## License

This repository uses dual licensing:
- `AGPL-3.0`: Core infrastructure manifests, logic, documentation, examples, and more
  - See [LICENSE](LICENSE) file - https://www.gnu.org/licenses/agpl-3.0.html
- `Apache-2.0`: Specific sample snippets requiring user adaptations
  - See [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0)

![logo.svg](core/ai/runtime/agents/dashboard/src/logo.svg)

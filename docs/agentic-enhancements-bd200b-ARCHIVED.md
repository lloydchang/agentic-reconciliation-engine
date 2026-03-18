# Agentic AI Enhancements Plan

This plan outlines proposed enhancements to the GitOps-infra-control-plane repository inspired by Uber's agentic AI platform, focusing on toil automation, async workflows, MCP registry, and measurement frameworks to improve developer productivity in infrastructure operations.

## Key Insights from Uber's Approach
- **Toil Automation Priority**: 70% of agent workloads focus on repetitive tasks (upgrades, migrations, bug fixes). Prioritize automating infra ops toil to free humans for creative work.
- **Async Multi-Agent Workflows**: Background agents (e.g., Minion platform) enable hours-long autonomous execution with PR generation and notifications.
- **MCP Ecosystem**: Centralized gateway/registry for secure, consistent access to internal/external tools with telemetry and auth.
- **Quality Assurance**: AI-assisted code review (UReview) and test generation (Autocover) with confidence grading to reduce noise.
- **Large-Scale Migrations**: Deterministic transformers and campaign management for bulk infra changes.
- **Measurement & Adoption**: Track business outcomes beyond activity metrics; use peer success stories for adoption.

## Proposed Enhancements

### 1. Async Agent Workflows
- Implement Temporal-based async multi-agent orchestration for infra operations (e.g., deployments, policy checks).
- Add background agent platform similar to Minion for autonomous execution of long-running tasks.
- Integrate Slack/GitHub PR notifications for agent completion.

### 2. Toil Automation Focus
- Enhance skills like `iac-deployment-validator` and `cost-optimizer` for higher automation accuracy.
- Prioritize "toil" tasks: policy enforcement, dependency upgrades, config migrations.
- Add deterministic transformers (OpenRewrite-like) for bulk infra changes.

### 3. MCP Registry and Gateway
- Extend existing MCP servers (mcp-playwright, puppeteer) with a centralized registry.
- Add sandbox testing and discovery for skills/tools.
- Implement telemetry, auth, and consistent API access.

### 4. Code Review and Testing Automation
- Integrate AI-assisted review with confidence grading to surface high-impact comments only.
- Add critic engine for generated infra changes/tests to prevent low-quality outputs.
- Enhance CI/CD scripts with automated validation phases.

### 5. Measurement and Adoption Frameworks
- Track business outcomes (cost savings, deployment speed) alongside activity metrics.
- Implement peer-driven adoption via success story sharing.
- Add cost-aware model selection (expensive for planning, cheaper for execution).

### 6. Technology Selection and Flexibility
- Ensure agent backends (Rust/Go/Python) support easy model/framework swaps.
- Add durable investments with agility for emerging tech.

## Implementation Priorities
1. Async workflows and toil automation (high impact, aligns with current Temporal setup).
2. MCP registry (builds on existing servers).
3. Measurement frameworks (addresses current gaps).
4. Review/testing automation (reduces manual effort).

## Risks and Considerations
- Adoption challenges: Focus on peer success stories vs. mandates.
- Cost management: Optimize token usage and model selection.
- Integration with legacy infra: Prioritize MCP endpoints for existing components.

## Next Steps
Review and confirm this plan before proceeding with implementation. Estimated effort: 4-6 weeks for core enhancements.

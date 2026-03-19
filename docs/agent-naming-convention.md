# Agent Naming Convention: [Verb]-[Qualifier]

## Overview

All skills in `core/ai/skills/` follow a consistent `[verb]-[qualifier]` naming pattern where:

- **Verb**: The primary action the skill performs
- **Qualifier**: Specific domain, target, or context for the action

## Naming Pattern Rationale

### Why Verb-First?

Skills are **agents that do things**. They perform actions (verbs) on specific targets or in particular contexts. The naming convention reflects this:

```
core/ai/skills/[verb]-[qualifier]
```

This reads naturally as: "agents that [verb] [qualifier]" or "agents that [verb] for [qualifier]".

### Examples

| Pattern | Reading | Purpose |
|---------|---------|---------|
| `optimize-costs` | agents that optimize costs | Cost optimization across cloud providers |
| `prioritize-alerts` | agents that prioritize alerts | Alert triage and prioritization |
| `provision-infrastructure` | agents that provision infrastructure | Infrastructure provisioning |
| `debug-ai-system` | agents that debug AI system | AI system debugging |

### Benefits

1. **Action-Oriented**: Immediately clear what the skill does
2. **Discoverable**: Verb-first makes it easy to find capabilities by action
3. **Consistent**: Standardized format across all 91 skills
4. **Scalable**: Easy to add new skills following the pattern

## Current Skills by Category

### Optimization & Performance
- `optimize-costs` - Cost optimization across cloud providers
- `optimize-performance` - Performance tuning and optimization
- `optimize-resources` - Resource utilization optimization
- `balance-resources` - Resource distribution and balancing

### Monitoring & Observability
- `monitor-pipelines` - CI/CD pipeline monitoring
- `monitor-sla` - SLA monitoring and alerting
- `monitor-slo` - SLO monitoring
- `aggregate-observability` - Observability data aggregation
- `check-cluster-health` - Kubernetes cluster health monitoring

### Security & Compliance
- `scan-compliance-security` - Security compliance scanning
- `analyze-security` - Security analysis and assessment
- `rotate-secrets` - Secret rotation and management
- `manage-certificates` - Certificate lifecycle management

### Infrastructure Management
- `provision-infrastructure` - Multi-cloud infrastructure provisioning
- `manage-infrastructure` - Infrastructure lifecycle management
- `discover-infrastructure` - Infrastructure discovery and mapping
- `maintain-nodes` - Node maintenance operations
- `tune-load-balancer` - Load balancer optimization

### Development & Deployment
- `generate-docs` - Documentation generation
- `generate-manifests` - Kubernetes manifest generation
- `validate-configs` - Configuration validation
- `deploy-strategies` - Deployment strategy planning
- `validate-deployments` - Deployment validation

### Incident & Troubleshooting
- `debug-ai-system` - AI system debugging
- `troubleshoot-k8s` - Kubernetes troubleshooting
- `diagnose-network` - Network diagnostics
- `classify-logs` - Log classification and analysis
- `analyze-logs` - Log analysis and insights

### Orchestration & Workflow
- `orchestrate-ai-agents` - AI agent fleet orchestration
- `orchestrate-workflows` - General workflow orchestration
- `manage-workflows` - Workflow lifecycle management
- `plan-runbooks` - Runbook planning and generation

### Database & Operations
- `maintain-database` - Database maintenance operations
- `operate-database` - Database operational tasks
- `check-dependencies` - Dependency analysis and validation

### Cloud & Multi-Cloud
- `network-multi-cloud` - Multi-cloud networking
- `manage-kubernetes-cluster` - Kubernetes cluster management
- `assist-kubectl` - kubectl command assistance

### Business & Reporting
- `generate-kpi-reports` - KPI report generation
- `report-compliance` - Compliance reporting
- `draft-communications` - Stakeholder communication drafting
- `predict-incidents` - Incident prediction and forecasting

## Implementation Guidelines

### Adding New Skills

When adding new skills, follow this pattern:

1. **Identify the verb**: What primary action does the skill perform?
2. **Choose qualifier**: What domain/target does it operate on?
3. **Check uniqueness**: Ensure the combination is unique and clear
4. **Test readability**: Should read naturally as "agents that [verb] [qualifier]"

### Examples of Good Names

✅ **Good**:
- `optimize-costs` (clear action + target)
- `monitor-pipelines` (specific monitoring domain)
- `provision-infrastructure` (standard provisioning term)

❌ **Avoid**:
- `cost-optimization` (noun-verb, doesn't follow pattern)
- `pipeline-monitor` (noun-verb, inconsistent)
- `infra-prov` (too abbreviated, unclear)

### Migration Notes

This naming convention was adopted to standardize the 72+ existing skills. All skills were renamed from various inconsistent patterns (noun-verb, verb-noun, compound nouns) to the consistent [verb]-[qualifier] format.

The rationale is that agents are action-oriented entities - they perform operations. Naming them by their primary verb makes their capabilities immediately apparent and improves discoverability.

## Naming Exceptions and Rationale

While the `[verb]-[qualifier]` pattern is the standard, all agents now follow this pattern consistently. Previously, some agents had noun-first naming but have been renamed to comply with the standard:

### Recent Renaming Updates

The following agents were renamed to follow the `[verb]-[qualifier]` pattern:

1. **`backstage-catalog`** → **`analyze-backstage-catalog`**
   - **Rationale**: Changed from product-name-first to verb-first for consistency
   - **Note**: "Backstage" remains as a proper noun referring to the Spotify platform

2. **`compliance-reporter`** → **`generate-compliance-report`**
   - **Rationale**: Changed from domain-function to verb-function for clarity
   - **Benefit**: More clearly indicates the action of generating reports

3. **`compliance-security-scanner`** → **`generate-security-report`**
   - **Rationale**: Simplified to focus on the primary action of generating security reports
   - **Benefit**: Removes ambiguity about scanning vs reporting focus

4. **`k8s-troubleshoot`** → **`troubleshoot-kubernetes`**
   - **Rationale**: Changed from abbreviation-first to verb-first for consistency
   - **Benefit**: More descriptive and follows the standard pattern

### Current Exception Criteria

Exceptions to the `[verb]-[qualifier]` pattern are now minimal and only allowed when:
- The name refers to a specific product, platform, or well-known technology (proper nouns)
- The agent name matches industry-standard terminology
- Alternative verb-first naming would create significant ambiguity or redundancy
- The name provides better discoverability for users familiar with the domain

All agents in the repository now consistently follow the `[verb]-[qualifier]` naming pattern.

## Related Documentation

- [AGENTS.md](AGENTS.md) - Agent architecture and operation rules
- [Skill Development Guide](docs/developer-guide/extending.md) - How to develop new skills
- [Skill Reference](docs/user-guide/skills-reference.md) - Complete skill catalog

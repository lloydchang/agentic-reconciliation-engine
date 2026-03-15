---
name: backstage-catalog
description: >
  Manage Backstage catalog entities, templates, and metadata with AI-assisted validation and dispatcher-ready outputs.
argument-hint: "[action] [entityType] [entityName] [parameters]"
disable-model-invocation: false
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
---

# Backstage Catalog — World-class Platform Inventory Playbook

Automates entity creation, validation, synchronization, and analytics across the Backstage catalog with AI metadata scoring and dispatcher context.

## When to invoke
- Create or update components/APIs/resources/systems in Backstage.
- Validate catalog metadata, relationships, or compliance.
- Sync catalog entries from GitHub/GitLab or service registries.
- Collect catalog analytics (ownership, coverage, adoption).
- Provide inventory context for onboarding, policy, or incident flows.

## Capabilities
- **CRUD operations** for Backstage entities with relationship tracking.
- **AI metadata validation** enforcing naming, tagging, and policy best practices.
- **Bulk sync/import** pipelines from code repositories or discovery tools.
- **Analytics & coverage reporting** for catalog health.
- **Shared context propagation** at `shared-context://memory-store/backstage/{operationId}` for downstream skills.

## Invocation patterns

```bash
/backstage-catalog create component my-service --owner=team-a --tags=backend
/backstage-catalog validate catalog-info.yaml --rules=metadata,relationships
/backstage-catalog sync --source=git --auto-merge
/backstage-catalog list components --owner=platform-team --format=json
/backstage-catalog metrics --window=30d --output=reports/catalog-metrics.json
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `action` | Operation (`create|validate|sync|list|metrics`). | `create` |
| `entityType` | Entity kind (`component|api|resource|system`). | `component` |
| `entityName` | Entity identifier. | `my-service` |
| `owner` | Owning team/group. | `team-a` |
| `source` | Sync source (`git|aws|k8s`). | `git` |
| `metrics` | Analytics action. | `metrics` |

## Output contract

```json
{
  "operationId": "CAT-2026-0315-01",
  "status": "success|failure",
  "operation": "create|validate|sync|list|metrics",
  "entitiesAffected": 12,
  "aiInsights": {
    "riskScore": 0.27,
    "recommendations": ["Add owner metadata for component 'payments-api'"]
  },
  "metrics": {
    "components": 152,
    "apis": 48,
    "resources": 80,
    "coveragePct": 92
  },
  "decisionContext": "redis://memory-store/backstage/CAT-2026-0315-01",
  "logs": "shared-context://memory-store/backstage/CAT-2026-0315-01"
}
```

## World-class workflow templates

### Entity lifecycle management
1. Validate entity YAML (Backstage spec, metadata, tags).
2. Create/update component/API/resource/system with dependencies and links.
3. Emit `catalog-entity-created` or `catalog-entity-updated` events for other skills.

### Sync & bulk imports
1. Scan repositories/external registries for catalog-info files.
2. Register or update entries, notify owners, and reconcile duplicates.
3. Emit `catalog-sync` event with diff summaries for downstream automation.

### Analytics & compliance
1. Compute coverage metrics (ownership coverage, documentation completeness).
2. Detect missing metadata, stale relationships, or policy gaps.
3. Emit `catalog-metrics` events for leadership and auditors.

## AI intelligence highlights
- **AI metadata scoring** compares entity completeness to policy baselines.
- **Intelligent recommendations** propose missing fields, relationships, or tags.
- **Predictive coverage alerts** flag declines in catalog coverage upfront.

## Memory agent & dispatcher integration
- Persist operations at `shared-context://memory-store/backstage/{operationId}`.
- Emit events: `catalog-entity-created`, `catalog-sync`, `catalog-metrics`, `catalog-anomalies`.
- Respond to dispatcher signals (`incident-ready`, `policy-risk`) by supplying inventory context.
- Tag entries with `decisionId`, `entityType`, `entityName`, `owner`, `riskScore`.

## Observability & telemetry
- Metrics: entity counts, metadata coverage, sync success rate.
- Logs: structured `log.event="catalog.operation"` with `operationId`, `entityType`, `owner`.
- Dashboards: integrate `/backstage-catalog metrics --format=prometheus` for platform views.
- Alerts: coverage drop, sync failures, automation errors.

## Failure handling & retries
- Retry API calls up to 2× on transient errors (API limits, network).
- On repeated failure escalate to `incident-triage-runbook` and log context.
- Preserve artifacts/logs until human gate or automation acknowledges.

## Human gates
- Required when:
  1. Auto-import modifies production-critical components or ownership.
  2. Deleting/deprecating services affects >20 tenants.
  3. Dispatcher requests manual review after repeated sync failures.
- Confirmation template matches orchestrator style (impact, reversibility).

## Testing & validation
- Dry-run: `/backstage-catalog validate catalog-info.yaml --dry-run`.
- Unit tests: `backend/catalog/` ensures parsing and AI suggestions operate correctly.
- Integration: `scripts/validate-backstage-catalog.sh` creates entities, runs sync, fires analytics.
- Regression: nightly `scripts/nightly-backstage-smoke.sh` ensures API latency and accuracy remain stable.

## References
- Templates: `templates/catalog/`.
- Scripts: `scripts/catalog/`.
- Documentation: `docs/backstage/`, `docs/platform-onboarding.md`.

## Related skills
- `/developer-self-service`: uses catalog entries for onboarding.
- `/ai-agent-orchestration`: includes catalog changes in workflows.
- `/infrastructure-discovery`: seeds catalog with discovered assets.

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

Automates entity creation, validation, synchronization, and analytics across the Backstage catalog. Provides AI-assisted metadata scoring, shared context outputs, and workflow hooks so other skills can rely on consistent inventory and documentation.

## When to invoke
- Create/update components/APIs/resources/systems in Backstage.
- Validate catalog metadata or check relationships/imports.
- Synchronize from GitHub, GitLab, or external service registries.
- Collect catalog analytics (ownership, coverage, compliance).
- Feed dispatcher flows requiring inventory context (onboarding, policy, incident).

## Capabilities
- CRUD operations for Backstage entities and relationships.
- AI-assisted metadata validation and naming/tagging enforcement.
- Bulk import/export and sync (Git, cloud services).
- Catalog analytics (ownership, completeness, usage).
- Shared context `shared-context://memory-store/backstage/<operationId>`.

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
| `action` | Operation (create/list/validate/sync). | `create` |
| `entityType` | Kind (component/api/resource/system). | `component` |
| `entityName` | Entity name. | `my-service` |
| `owner` | Owning team/group. | `team-a` |
| `source` | Sync source (git/aws/k8s). | `git` |
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
    "recommendations": [
      "Add owner metadata for component 'payments-api'"
    ]
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

### Entity management
1. Validate entity YAML (Backstage spec, metadata, tags).
2. Create component/API/resource/system entity with dependencies.
3. Emit `catalog-entity-created` event.

### Sync & bulk imports
1. Scan repositories or external sources for catalog-info files.
2. Auto-register or update, notifying ownership.
3. Emit `catalog-sync` event with diff summary.

### Analytics & compliance
1. Compute coverage metrics (owner, doc, lifecycle).
2. Detect missing metadata or compliance gaps.
3. Emit `catalog-metrics` event for leadership.

## AI intelligence highlights
- **AI Metadata Scoring**: evaluates entity completeness vs policies.
- **Intelligent Recommendations**: proposes missing fields, relationships, or tags.
- **Predictive Coverage Alerts**: warns when catalog coverage dips below thresholds.

## Memory agent & dispatcher integration
- Store operations under `shared-context://memory-store/backstage/<operationId>`.
- Emit events: `catalog-entity-created`, `catalog-sync`, `catalog-metrics`, `catalog-anomalies`.
- Respond to dispatcher signals (`incident-ready`, `policy-risk`) to surface inventory context.
- Tag metadata with `decisionId`, `entityType`, `entityName`, `owner`.

## Communication protocols
- Primary: Backstage CLI/API calls for entity management and validation.
- Secondary: Event bus for `catalog-*` events.
- Fallback: JSON artifacts `artifact-store://backstage/<operationId>.json`.

## Observability & telemetry
- Metrics: entity counts, metadata coverage, sync success rate.
- Logs: structured `log.event="catalog.operation"` with `operationId`.
- Dashboards: integrate `/backstage-catalog metrics --format=prometheus`.
- Alerts: entity coverage drop, sync failures, automation errors.

## Failure handling & retries
- Retry API calls up to 2× on transient errors (API limit, network).
- On repeated failure, escalate to `incident-triage-runbook`.
- Retain artifacts/logs until human gate acknowledges.

## Human gates
- Required when:
 1. Auto-import affects production-critical components or adds new owners.
 2. Automation removes/deprecates services impacting >20 tenants.
 3. Dispatcher requests manual approval after repeated sync failures.
- Use standard human gate template capturing impact and reversibility.

## Testing & validation
- Dry-run: `/backstage-catalog validate catalog-info.yaml --dry-run`.
- Unit tests: `backend/catalog/` ensures entity parsing + AI suggestions work.
- Integration: `scripts/validate-backstage-catalog.sh` creates/deduplicates entities, runs analytics.
- Regression: nightly `scripts/nightly-backstage-smoke.sh` ensures API response times and accuracy.

## References
- Templates: `templates/catalog/`.
- Scripts: `scripts/catalog/`.
- Documentation: `docs/backstage/`, `docs/platform-onboarding.md`.

## Related skills
- `/developer-self-service`: uses catalog entries to onboard teams.
- `/ai-agent-orchestration`: includes catalog operations in workflows.
- `/infrastructure-discovery`: uses discovered resources to seed catalog.

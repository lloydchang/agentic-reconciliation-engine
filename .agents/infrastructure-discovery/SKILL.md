---
name: infrastructure-discovery
description: >
  Discover, visualize, and contextualize infrastructure resources with AI-driven mapping, cost analysis, and dispatcher-ready metadata.
argument-hint: "[resourceType] [environment] [outputFormat]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Python
---

# Infrastructure Discovery — World-class Exploration Playbook

Enumerates multi-cloud resources, builds topology graphs, streams metrics, generates visual dashboards, and feeds AI insights to dispatchers.

## When to invoke
- Inventory compute, storage, network, and service resources across clouds and on-prem.
- Produce interactive visualizations (HTML/JSON/CSV) with cost overlays.
- Map relationships/dependencies for incident response or capacity planning.
- Respond to dispatcher alerts (`incident-ready`, `policy-risk`, `capacity-alert`) needing topology context.

## Capabilities
- **Multi-cloud discovery engine** (AWS/Azure/GCP/local) with interactive dashboards.
- **AI-enriched relationship graphs** with anomaly detection and cost insights.
- **Scheduled discovery automation** with caching and incremental updates.
- **Shared-context propagation** at `shared-context://memory-store/discovery/{operationId}`.
- **Human gating** before exporting sensitive topology or sweeping new regions.

## Invocation patterns

```bash
/infrastructure-discovery discover --resourceType=all --environment=all --outputFormat=html
/infrastructure-discovery discover --resourceType=vm --environment=production --outputFormat=json
/infrastructure-discovery visualize --operationId=DISC-2026-0315-01 --format=interactive
/infrastructure-discovery cost --operationId=DISC-2026-0315-01 --include=tenant-42
/infrastructure-discovery schedule --frequency=daily --resourceType=network
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `resourceType` | Resource category (`all|vm|database|network`). | `all` |
| `environment` | Environment filter (`prod|staging|dev`). | `production` |
| `outputFormat` | Format (`html|json|csv|interactive`). | `html` |
| `operationId` | Discovery execution ID. | `DISC-2026-0315-01` |
| `frequency` | Scheduled cadence. | `daily` |
| `include` | Scope filter (tenant, region). | `tenant-42` |

## Output contract

```json
{
  "operationId": "DISC-2026-0315-01",
  "status": "completed",
  "resources": 342,
  "relationships": 128,
  "topology": {
    "graphs": ["graph-01", "graph-02"],
    "metrics": { "avg_cpu": 46, "avg_mem": 58 },
    "cost": { "monthly": 12345, "trend": "+12%" }
  },
  "visualizationUrl": "https://dashboards/infra/DISC-2026-0315-01",
  "decisionContext": "redis://memory-store/discovery/DISC-2026-0315-01",
  "logs": "shared-context://memory-store/discovery/DISC-2026-0315-01"
}
```

## World-class workflow templates

### Multi-cloud discovery & mapping
1. Enumerate resources per provider filtered by type/environment.
2. Enrich records with metrics (CPU, memory, disk), health, tags, and cost data.
3. Build dependency graphs and emit `discovery-completed` events.

### Visualization & reporting
1. Render interactive dashboards (tree, heatmaps, relationships).
2. Provide real-time updates via WebSocket or streaming patches.
3. Export static/interactive formats for documentation or compliance.

### Automated scheduling & cost insights
1. Schedule discovery jobs with cached deltas to reduce load.
2. Analyze cost, highlight optimization opportunities, and issue `discovery-cost-insight`.
3. Notify cost or capacity skills when anomalies appear.

## AI intelligence highlights
- **AI anomaly detection** spots resource growth spikes, dependencies, or cost jumps.
- **Intelligent cost insights** compute monthly trends, savings potential, and tenant-level riskScores.
- **Predictive topology alerts** warn when critical dependencies degrade.

## Memory agent & dispatcher integration
- Store payloads at `shared-context://memory-store/discovery/{operationId}` tagged with `decisionId`, `tenant`, `riskScore`.
- Emit events: `discovery-completed`, `discovery-visualized`, `topology-alert`, `discovery-cost-insight`.
- Listen for dispatcher signals (`incident-ready`, `policy-risk`) to refresh topology/context.
- Provide fallback artifacts via `artifact-store://discovery/{operationId}.json`.

## Observability & telemetry
- Metrics: discovery frequency, resource counts, relationship density, cost trends.
- Logs: structured `log.event="discovery.run"` with `operationId`, `resourceCount`, `cost`.
- Dashboards: integrate `/infrastructure-discovery metrics --format=prometheus` within ops views.
- Alerts: stale discovery, topology anomalies, forecasted cost spikes (riskScore ≥ 0.85).

## Failure handling & retries
- Retry cloud API calls up to 3× on transient failures; emit `discovery-retry` and log partial data.
- On repeated failure escalate to `incident-triage-runbook`.
- Preserve artifacts until downstream acknowledges to support audits.

## Human gates
- Required when:
  1. Exports include sensitive topology for entire production.
  2. Automation sweeps new environments with broad blast radius.
  3. Dispatcher demands manual review before publishing to auditors.
- Use standard human gate template capturing impact and reversibility.

## Testing & validation
- Dry-run: `/infrastructure-discovery discover --resourceType=all --environment=dev --dry-run`.
- Unit tests: `backend/discovery/` ensures parsing and graph building produce expected outputs.
- Integration: `scripts/validate-infrastructure-discovery.sh` discovers resources, visualizes outputs, and checks cost insights.
- Regression: nightly `scripts/nightly-discovery-smoke.sh` verifies cadence, metrics, and alerts remain stable.

## References
- Scripts: `scripts/infrastructure-scanner.py`, `scripts/visualization-generator.py`.
- Templates: `templates/infrastructure-dashboard.html`.
- Assets: `assets/resource-icons.json`.

## Related skills
- `/cost-optimization`: uses cost insights for optimizations.
- `/incident-triage-runbook`: needs topology context for mitigation.
- `/workflow-management`: orchestrates discovery reporting workflows.

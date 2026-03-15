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

Enumerates multi-cloud resources, builds dependency graphs, streams metrics, generates visual dashboards, and feeds AI insights for dispatchers. Use this skill when onboarding new environments, auditing resource relationships, performing cost analysis, or responding to incidents requiring topology context.

## When to invoke
- Inventory all resources (compute, storage, network, services) across clouds and on-prem.
- Generate interactive visualizations (HTML/JSON/CSV) with metrics and cost overlays.
- Map relationships and dependencies for incident response or capacity planning.
- Trigger when dispatchers emit `incident-ready`, `policy-risk`, or `capacity-alert` needing topology/context data.

## Capabilities
- Multi-cloud discovery engine (AWS/Azure/GCP/local) with interactive dashboards.
- AI-enriched relationship graphs, anomaly detection, and cost insight overlays.
- Scheduled discovery automation with caching and incremental updates.
- Shared context `shared-context://memory-store/discovery/<operationId>` for other skills.
- Human gating for sensitive topology exports or new environment sweeps.

## Invocation patterns

```bash
/infrastructure-discovery discover --resourceType=all --environment=all --outputFormat=html
/infrastructure-discovery discover --resourceType=vm --environment=production --outputFormat=json
/infrastructure-discovery visualize --operationId=DISC-2026-0315-01 --format=interactive --dry-run
/infrastructure-discovery cost --operationId=DISC-2026-0315-01 --include=tenant-42
/infrastructure-discovery schedule --frequency=daily --resourceType=network
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `resourceType` | Resource category (`all|vm|database|network`). | `all` |
| `environment` | Environment filter (prod/staging/dev). | `production` |
| `outputFormat` | HTML/JSON/CSV/interactive. | `html` |
| `operationId` | Discovery execution ID. | `DISC-2026-0315-01` |
| `frequency` | Scheduled discovery cadence. | `daily` |
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
    "metrics": {
      "avg_cpu": 46,
      "avg_mem": 58
    },
    "cost": {
      "monthly": 12345,
      "trend": "+12%"
    }
  },
  "visualizationUrl": "https://dashboards/infra/DISC-2026-0315-01",
  "decisionContext": "redis://memory-store/discovery/DISC-2026-0315-01",
  "logs": "shared-context://memory-store/discovery/DISC-2026-0315-01"
}
```

## World-class workflow templates

### Multi-cloud discovery & mapping
1. Enumerate resources (AWS/Azure/GCP/local) filtered by type and environment.
2. Enrich records with metrics (CPU/memory/disk), health, and tags.
3. Build dependency graphs (relationships, topology strength).
4. Persist results, emit `discovery-completed`, and generate HTML/JSON/CSV exports.

### Visualization & reporting
1. Render interactive dashboards (collapsible tree, cost dashboards, relationship graphs).
2. Provide WebSocket updates for real-time metrics.
3. Export interactive HTML or static formats for documentation and audits.

### Automated scheduling & cost insights
1. Schedule periodic discovery jobs, keep caches (Redis) to avoid thrash.
2. Analyze costs and highlight optimization opportunities (underutilized VMs, idle storage).
3. Emit `discovery-cost-insight` for dispatcher/cost optimization to act.

## AI intelligence highlights
- **AI Anomaly Detection**: spots unusual resource growth, cost spikes, or unexpected dependencies.
- **Intelligent Cost Insights**: calculates monthly trend, savings opportunities, and riskScore per tenant.
- **Predictive Topology Alerts**: warns if critical dependencies show health degradation.

## Memory agent & dispatcher integration
- Store discovery payloads under `shared-context://memory-store/discovery/<operationId>`.
- Emit events: `discovery-completed`, `discovery-visualized`, `topology-alert`, `discovery-cost-insight`.
- Listen for dispatcher events (`incident-ready`, `policy-risk`) to refresh topology/context.
- Tag metadata with `decisionId`, `tenant`, `riskScore`, `operationId`.

## Communication protocols
- Primary: CLI/Python scripts calling cloud APIs, outputting JSON.
- Secondary: Event bus for `discovery-*` signals consumed by other skills.
- Fallback: Persist JSON artifacts to `artifact-store://discovery/<operationId>.json`.

## Observability & telemetry
- Metrics: discovery frequency, resources discovered, cost trends, visualization hits.
- Logs: structured `log.event="discovery.run"` containing `operationId`, `resourceCount`, `cost`.
- Dashboards: integrate `/infrastructure-discovery metrics --format=prometheus`.
- Alerts: discovery stale > expected frequency, topology anomalies detected, cost spike forecast riskScore ≥ 0.85.

## Failure handling & retries
- Retry API calls up to 3× when fetching cloud inventories; log partial results and emit `discovery-retry`.
- On repeated failures escalates to `incident-triage-runbook`.
- Preserve discovery artifacts/logs until downstream ack; do not delete for audit.

## Human gates
- Required when:
 1. Discovery exports include sensitive topology for entire prod environment.
 2. Dispatcher requests manual vetting before publishing to auditors.
 3. Automated scheduling would change caches across tenants simultaneously.
- Use standard human gate confirmation template capturing impact/reversibility.

## Testing & validation
- Dry-run: `/infrastructure-discovery discover --resourceType=all --environment=dev --dry-run`.
- Unit tests: `backend/discovery/` ensures parsing/graph building works correctly.
- Integration: `scripts/validate-infrastructure-discovery.sh` runs discovery, visualizes outputs, checks cost insights.
- Regression: nightly `scripts/nightly-discovery-smoke.sh` ensures discovery frequency, metrics, and alerts stay within bounds.

## References
- Scripts: `scripts/infrastructure-scanner.py`, `scripts/visualization-generator.py`.
- Templates: `templates/infrastructure-dashboard.html`.
- Assets: `assets/resource-icons.json`.

## Related skills
- `/cost-optimization`: consumes cost insights for optimization plans.
- `/incident-triage-runbook`: uses topology context for incidents.
- `/workflow-management`: orchestrates discovery workflows and reports.

---
name: cluster-health-check
description: |
  Inspect Kubernetes cluster health, node conditions, control plane status, and critical service signals to detect degradation before it becomes widespread.
allowed-tools:
  - Bash
  - Read
  - Write
  - kubectl
---

# Cluster Health Check — World-class Cluster Reliability Playbook

Performs ongoing health sweeps across clusters (control plane, node pools, workloads) and vents issues to the dispatcher when indicators drift.

## When to invoke
- After cluster upgrades or scaling operations to confirm control plane/node health.
- When telemetry shows pod evictions, CPU saturation, or failed API server requests.
- At scheduled intervals (daily/weekly) to audit cluster posture.
- Dispatcher/memory agents raise `cluster-alert`, `node-saturation`, or `control-plane-failure`.

## Capabilities
- **Control plane at-a-glance** (API server health, etcd, scheduler, controller manager metrics).
- **Node & pod health** (conditions, taints, drains, disk pressure, restarts).
- **Workload health** (critical services, deployments, pod disruption budgets).
- **Issue correlation** combining telemetry, logs, and cluster events.
- **Shared context** at `shared-context://memory-store/cluster-health-check/{operationId}`.

## Invocation patterns
```bash
/cluster-health-check overview --cluster=aks-hub
/cluster-health-check nodes --cluster=aks-hub
/cluster-health-check services --namespace=platform
/cluster-health-check drain --node=node-123 --reason="planned maintenance"
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `cluster` | Cluster context. | `aks-hub` |
| `namespace` | Namespace for workload checks. | `platform` |
| `node` | Node name for drainage. | `node-123` |
| `reason` | Maintenance reason. | "planned maintenance" |
| `overview` | Flag to gather overall health. | `true` |

## Output contract
```json
{
  "operationId": "CH-2026-0315-01",
  "cluster": "aks-hub",
  "status": "healthy|warning|critical",
  "riskScore": 0.48,
  "issues": ["node-pressure: gpu-node-2"],
  "logs": "shared-context://memory-store/cluster-health-check/CH-2026-0315-01",
  "decisionContext": "redis://memory-store/cluster-health-check/CH-2026-0315-01"
}
```

## World-class workflow templates

### Cluster overview & control plane
1. Query API server health, etcd leader, scheduler/controller manager metrics.
2. Emit `cluster-health` event with aggregated status and riskScore.
3. Command stub: `/cluster-health-check overview --cluster=aks-hub`

### Node & workload sweeps
1. Check node ready status, disk pressure, missing taints, and workload disruption budgets.
2. Document failing pods/deployments and emit `node-issue` or `pod-issue` events.
3. Command stub: `/cluster-health-check nodes --cluster=aks-hub`

### Service & namespace diagnostics
1. Inspect deployments, services, and critical workloads in a namespace.
2. Correlate restarts, liveness/readiness failures, and resource pressure.
3. Command stub: `/cluster-health-check services --namespace=platform`

### Maintenance & drainage
1. Safely cordon/drain nodes prior to maintenance with checklists.
2. Emit `node-drained` events and track completion; fallback to reverse when failure.
3. Command stub: `/cluster-health-check drain --node=node-123 --reason="planned maintenance"`

## AI intelligence highlights
- **Risk scoring** considers control plane stability, node pressure, and workload health.
- **Predictive alerts** foresee node saturations or API server lag before thresholds blow.
- **Dependency correlation** links pods/deployments to failing nodes for faster remediation.

## Memory agent & dispatcher integration
- Persist health snapshots under `shared-context://memory-store/cluster-health-check/{operationId}`.
- Emit events: `cluster-health`, `node-issue`, `pod-issue`, `node-drained`, `cluster-human-gate`.
- Subscribe to dispatcher signals (`incident-ready`, `deployment-risk`, `capacity-alert`).
- Tag context with `decisionId`, `cluster`, `namespace`, `riskScore`, `controlPlaneReady`.

## Observability & telemetry
- Metrics: health trend, issue count, riskScore distribution, maintenance frequency.
- Logs: structured `log.event="cluster.health"` with `cluster`, `status`, `decisionId`.
- Dashboards: integrate `/cluster-health-check metrics --format=prometheus`.
- Alerts: cluster-critical nodes, failing control plane components, maintenance stuck >15m.

## Failure handling & retries
- Retry cluster API calls up to 3×; if failing, escalate to `incident-triage-runbook`.
- When drainage fails, rollback cordon and reattempt with automation guardrails.
- Retain logs for 90 days for audits.

## Human gates
- Required when:
  1. Control plane manipulations affect production clusters.
  2. Node drains impact deployments of >20 tenants.
  3. Dispatcher requests manual review after repeated health alerts.

## Testing & validation
- Dry-run: `/cluster-health-check overview --cluster=test-cluster --dry-run`
- Unit tests: `backend/cluster-health/` ensures health analyzer functions behave.
- Integration: `scripts/validate-cluster-health-check.sh` runs across clusters.
- Regression: nightly `scripts/nightly-cluster-health-smoke.sh` monitors control plane metrics.

## References
- Scripts: `scripts/cluster-health-check/`.
- Templates: `templates/cluster-health/`.
- Monitoring: `monitoring/cluster-health/`.

## Related skills
- `/observability-stack`: supplies telemetry.
- `/incident-triage-runbook`: handles critical alerts.
- `/workflow-management`: orchestrates health remediation flows.

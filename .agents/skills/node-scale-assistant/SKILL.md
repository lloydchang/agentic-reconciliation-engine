---
name: node-scale-assistant
description: >
  Assist with scaling Kubernetes node pools and autoscalers using AI-guided capacity signals and dispatcher context.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Node Scale Assistant — World-class Capacity Playbook

Adjusts node pools and autoscalers using AI predictions, telemetry, and dispatcher metadata to keep clusters right-sized.

## When to invoke
- Scale node pools manually or adjust autoscaler parameters.
- Enable/configure cluster autoscaler (HPA/VPA/Cluster Autoscaler) settings.
- Respond to capacity signals (pending pods, resource pressure, incidents).
- Provide instructions or commands for scaling adjustments.

## Capabilities
- **Telemetry evaluation** recommending scale-up/scale-down actions.
- **Node pool/autoscaler control** for AKS/EKS/GKE clusters.
- **AI risk scoring** determining auto vs manual scaling.
- **Shared-context propagation** via `shared-context://memory-store/node-scale/{operationId}`.
- **Human gating** for high-impact or production operations.

## Invocation patterns

```bash
/node-scale-assistant scale --cluster=aks-tenant-42-prod --nodePool=default --replicas=5
/node-scale-assistant autoscaler --cluster=aks-tenant-42-prod --enable=true --min=2 --max=10
/node-scale-assistant diagnose --cluster=aks-tenant-42-prod --metric=cpu --threshold=80
/node-scale-assistant recommend --cluster=eks-tenant-91 --forecast=72h
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `cluster` | Cluster identifier. | `aks-tenant-42-prod` |
| `nodePool` | Node pool name. | `default` |
| `replicas` | Desired node count. | `5` |
| `metric` | Metric to monitor (`cpu|memory`). | `cpu` |
| `threshold` | Threshold percentage. | `80` |
| `forecast` | Forecast horizon. | `72h` |

## Output contract

```json
{
  "operationId": "NS-2026-0315-01",
  "operation": "scale|autoscaler|diagnose|recommend",
  "cluster": "aks-tenant-42-prod",
  "status": "success|failure",
  "scalingAction": { "nodePool": "default", "fromReplicas": 3, "toReplicas": 5 },
  "autoscalerConfig": { "min": 2, "max": 10, "enabled": true },
  "recommendations": ["Scale up 2 nodes to handle tenant-42 burst"],
  "riskScore": 0.42,
  "logs": "shared-context://memory-store/node-scale/NS-2026-0315-01",
  "decisionContext": "redis://memory-store/node-scale/NS-2026-0315-01"
}
```

## World-class workflow templates

### Manual scaling
1. Analyze pending pods and node utilization.
2. Scale node pool via cloud CLI with validated replica counts.
3. Verify pod scheduling, update shared context, emit `node-scaled`.

### Autoscaler tuning
1. Adjust min/max replicas and thresholds for cluster autoscaler.
2. Monitor queue depth and resource pressure.
3. Emit `autoscaler-updated` with configuration changes.

### Forecast-driven recommendations
1. Integrate `capacity-planning` forecasts to predict demand.
2. Recommend scaling ahead of time to avoid incidents.
3. Emit `capacity-recommendation` events for dispatchers/human gates.

## AI intelligence highlights
- **AI risk scoring** balances scaling impact with cost and capacity needs.
- **Intelligent forecasting** warns of upcoming demand surges.
- **Autoscaler validation** detects misconfigurations or flapping behavior.

## Memory agent & dispatcher integration
- Persist metadata at `shared-context://memory-store/node-scale/{operationId}` tagged with `decisionId`, `cluster`, `riskScore`.
- Emit events: `node-scale`, `autoscaler-update`, `capacity-recommendation`.
- React to dispatcher alerts (`incident-ready`, `capacity-alert`) by adjusting decisions.
- Provide fallback artifacts via `artifact-store://node-scale/{operationId}.json`.

## Observability & telemetry
- Metrics: node pool counts, scaling frequency, autoscaler adjustments, success rates.
- Logs: structured `log.event="node-scale.operation"` with `cluster`, `action`, `decisionId`.
- Dashboards: integrate `/node-scale-assistant metrics --format=prometheus`.
- Alerts: rapid scaling > threshold, failure/timeout, autoscaler flapping.

## Failure handling & retries
- Retry scaling operations up to 2× on transient API errors.
- On failures emit `node-scale-failed`, escalate to `incident-triage-runbook`, keep logs for audit.
- Retain shared-context until downstream ack ensures safe closure.

## Human gates
- Required when:
  1. Scaling impacts production-critical clusters or >20 nodes.
  2. Autoscaler changes exceed cost/policy limits.
  3. Dispatcher requests manual verification after repeated retries.
- Use orchestrator-style confirmation template describing impact/reversibility.

## Testing & validation
- Dry-run: `/node-scale-assistant scale --cluster=aks-tenant-42-prod --replicas=1 --dry-run`.
- Unit tests: `backend/node-scale/` ensures recommendation and scoring functions work.
- Integration: `scripts/validate-node-scale.sh` exercises scaling/autoscaler updates in emulator.
- Regression: nightly `scripts/nightly-node-scale-smoke.sh` ensures scaling stability and alerting.

## References
- Scripts: `scripts/node-scale/`.
- Monitoring docs: `monitoring/metrics/node-scaling`.

## Related skills
- `/capacity-planning`: consumes forecasts for scaling.
- `/incident-triage-runbook`: handles capacity incidents.
- `/deployment-validation`: coordinates scaling for deployments.

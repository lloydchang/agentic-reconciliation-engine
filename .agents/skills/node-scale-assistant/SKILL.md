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

Adjusts node pools and autoscalers when capacity shifts, using AI predictions, shared context, and telemetry to keep clusters right-sized. Trigger when pods request more capacity, autoscaler anomalies appear, or dispatchers flag `capacity-alert`/`incident-ready`.

## When to invoke
- Scale node pools up/down manually or via autoscaler tuning.
- Enable/configure cluster autoscaler (HPA/VPA/Cluster Autoscaler).
- Respond to capacity signals (pod pending, resource pressure, incidents).
- Provide instructions or commands for scaling adjustments.

## Capabilities
- Evaluates cluster telemetry to recommend scaling actions.
- Controls node pools and autoscalers across AKS/EKS/GKE.
- AI risk scoring to determine whether to scale automatically or require human gate.
- Shared context updates (`shared-context://memory-store/node-scale/<operationId>`).

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
| `metric` | Metric to monitor (cpu/memory). | `cpu` |
| `threshold` | Alert threshold percentage. | `80` |
| `forecast` | Forecast horizon. | `72h` |

## Output contract

```json
{
  "operationId": "NS-2026-0315-01",
  "operation": "scale|autoscaler|diagnose|recommend",
  "cluster": "aks-tenant-42-prod",
  "status": "success|failure",
  "scalingAction": {
    "nodePool": "default",
    "fromReplicas": 3,
    "toReplicas": 5
  },
  "autoscalerConfig": {
    "min": 2,
    "max": 10,
    "enabled": true
  },
  "recommendations": [
    "Scale up by 2 nodes to handle burst in tenant-42"
  ],
  "riskScore": 0.42,
  "logs": "shared-context://memory-store/node-scale/NS-2026-0315-01",
  "decisionContext": "redis://memory-store/node-scale/NS-2026-0315-01"
}
```

## World-class workflow templates

### Manual scaling
1. Analyze pod pending metrics and node utilization.
2. Scale node pool (kubectl/az eksctl/gcloud) with desired replicas.
3. Validate pods schedule, update shared context, emit `node-scaled`.

### Autoscaler tuning
1. Adjust min/max replicas and CPU/memory thresholds for cluster autoscaler.
2. Monitor queue depth and resource pressure for recommendations.
3. Emit `autoscaler-updated` event.

### Forecast-driven recommendations
1. Read forecast from `capacity-planning` or use telemetry to predict demand.
2. Recommend scaling steps ahead of time to avoid incidents.
3. Emit `capacity-recommendation` for dispatcher and human review.

## AI intelligence highlights
- **AI Risk Score**: evaluates scaling impact vs. cost and capacity needs.
- **Intelligent Forecasting**: warns when upcoming events will exceed current capacity.
- **Smart Autoscaler Validation**: detects misconfigurations or alert loops.

## Memory agent & dispatcher integration
- Store operations under `shared-context://memory-store/node-scale/<operationId>`.
- Emit events: `node-scale`, `autoscaler-update`, `capacity-recommendation`.
- Listen to dispatcher signals (`incident-ready`, `capacity-alert`) to adjust scaling decisions.
- Tag metadata with `decisionId`, `cluster`, `riskScore`.

## Communication protocols
- Primary: CLI commands (az aks nodepool scale, eksctl, gcloud) and autoscaler APIs.
- Secondary: Event bus for `node-scale` events.
- Fallback: Artifact store entries `artifact-store://node-scale/<operationId>.json`.

## Observability & telemetry
- Metrics: node pool counts, scaling frequency, autoscaler adjustments, scaling action success.
- Logs: structured `log.event="node-scale.operation"` with `cluster`, `action`.
- Dashboards: integrate `/node-scale-assistant metrics --format=prometheus`.
- Alerts: rapid scaling > threshold, scale failure, autoscaler flapping.

## Failure handling & retries
- Retry scaling commands up to 2× on transient failures.
- On failure, emit `node-scale-failed`, log output for `incident-triage`.
- Do not delete shared-context until downstream ack.

## Human gates
- Required when:
 1. Scaling affects production-critical clusters or >20 nodes.
 2. Autoscaler changes increase max beyond cost/ policy limits.
 3. Dispatcher requests manual verification after repeated retries.
- Use standard human gate template.

## Testing & validation
- Dry-run: `/node-scale-assistant scale --cluster=aks-tenant-42-prod --replicas=1 --dry-run`.
- Unit tests: `backend/node-scale/` ensures recommendation logic and risk scoring.
- Integration: `scripts/validate-node-scale.sh` exercises scaling and autoscaler updates in emulator.
- Regression: nightly `scripts/nightly-node-scale-smoke.sh` ensuring scaling stability and alert thresholds.

## References
- Scripts: `scripts/node-scale/`.
- Monitoring metrics: `monitoring/metrics/node-scaling`.

## Related skills
- `/capacity-planning`: consumes scaling recommendations and forecasts.
- `/incident-triage-runbook`: handles failures triggered by capacity pressure.
- `/deployment-validation`: coordinates scaling for deployments requiring headroom.

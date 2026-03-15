---
name: kubernetes-cluster-manager
description: >
  Operate Kubernetes clusters across AKS, EKS, and GKE with AI-driven lifecycle orchestration, security hardening, and fleet observability.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Kubernetes Cluster Manager — World-class Fleet Operations Playbook

Provides AI-aided provisioning, scaling, upgrades, hardening, and diagnostics for fleet-wide Kubernetes operations while feeding rich context to orchestrators.

## When to invoke
- Provision, scale, upgrade, or decommission clusters across AKS, EKS, or GKE.
- Harden clusters with RBAC, network policies, workload identity, or PodSecurity Standards.
- Troubleshoot cluster health, autoscaler anomalies, or control-plane alerts.
- Respond to dispatcher/memory agent events (`incident-ready`, `capacity-alert`, `sla-risk`) that require cluster-level context.

## Capabilities
- **AI cluster risk scoring** predicts upgrade/scale risk using change vectors, telemetry, and incident history.
- **Intelligent scaling** balances node-pool autoscaling with demand/cost signals from `cost-optimization` and `capacity-planning`.
- **Smart upgrade orchestration** sequences control plane and node upgrades with rollback safeguards.
- **Predictive health diagnostics** detect anomalies (API latency, kubelet pressure) before user impact.
- **Fleet awareness** maintains inventory, compliance posture, and uptime telemetry across clouds via shared context.

## Invocation patterns

```bash
/kubernetes-cluster-manager provision --platform=aks --tenant=tenant-42 --node-count=3 --tags=env=prod
/kubernetes-cluster-manager scale --clusterId=aks-tenant-42-prod --node-pool=pool1 --count=5
/kubernetes-cluster-manager upgrade --clusterId=eks-tenant-91-prod --version=1.30 --mode=rolling
/kubernetes-cluster-manager health --clusterId=gke-tenant-11-stage
/kubernetes-cluster-manager harden --clusterId=aks-tenant-42-prod --policy=pod-security --enforce=true
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `clusterId` | Cluster identifier (`platform-tenant-env`). | `aks-tenant-42-prod` |
| `platform` | Cloud provider (`aks|eks|gke`). | `gke` |
| `nodePool` | Node pool name. | `pool1` |
| `version` | Kubernetes version target. | `1.30` |
| `nodeCount` | Desired node count for a pool. | `5` |
| `policy` | Hardening/compliance policy. | `pod-security` |

## Output contract

```json
{
  "operationId": "CLUSTER-2026-0315-01",
  "clusterId": "aks-tenant-42-prod",
  "platform": "aks",
  "status": "success|failure|in_progress",
  "operation": "provision|scale|upgrade|health|harden",
  "aiRiskScore": 0.18,
  "nodePools": [
    {
      "name": "pool1",
      "count": 5,
      "vmSize": "Standard_D4s_v3",
      "autoscaler": "enabled"
    }
  ],
  "health": {
    "controlPlane": "healthy",
    "nodes": "healthy",
    "addons": "healthy"
  },
  "events": [
    {
      "name": "nodepool-scale",
      "status": "completed",
      "timestamp": "2026-03-15T07:42:00Z"
    }
  ],
  "logs": "shared-context://memory-store/cluster/CLUSTER-2026-0315-01",
  "decisionContext": "redis://memory-store/cluster/CLUSTER-2026-0315-01"
}
```

## World-class workflow templates

### AI-assisted provisioning & hardening
1. Validate cluster requirements (quotas, node types, networking).
2. Provision via cloud CLIs (`az aks`, `eksctl`, `gcloud`) with idempotent arguments and tagging.
3. Deploy baseline security (network policies, PodSecurity Standards, workload identity, cert-manager, Prometheus stack).
4. Emit `cluster-provisioned` events with telemetry stored in shared context.

### Intelligent scaling & autoscaler tuning
1. Ingest telemetry (autoscaler events, node CPU/memory, queue depth) and forecast demand using AI ensembles.
2. Scale node pools while aligning decisions with cost and capacity signals.
3. Tune taints/labels and autoscalers to avoid oscillation.
4. Publish `nodepool-scaled` events and update the cluster inventory.

### Smart upgrades & rollback strategy
1. Score upgrade risk (version gaps, change history, incident rate) via AI.
2. Upgrade control plane/node pools sequentially with validation probes.
3. Roll back automatically if critical health checks fail; log failures for postmortems.
4. Emit `upgrade-completed` events for downstream compliance and deployments.

### Predictive health diagnostics
1. Run scheduled health checks (nodes, components, events, PVCs, RBAC).
2. Feed metrics into anomaly models (API latency, memory pressure, API server errors).
3. Emit `cluster-anomaly` events when predictions breach thresholds, tagging with `riskScore`.
4. Trigger `incident-triage-runbook` or `deployment-validation` as needed.

## AI intelligence highlights
- **AI Cluster Risk Scoring** evaluates operations for failure likelihood and automation readiness.
- **Intelligent Scaling** recognizes burst demand patterns and pro-actively adjusts autoscalers.
- **Smart Upgrade Orchestration** sequences upgrades with canary control-plane validation.
- **Predictive Health Diagnostics** surfaces control-plane, CNI, or etcd anomalies before they affect pods.

## Memory agent & dispatcher integration
- Store cluster telemetry under `shared-context://memory-store/cluster/{clusterId}` for `incident`, `capacity`, and `cost` skills.
- Emit/consume events: `cluster-provisioned`, `cluster-scaled`, `cluster-upgrade`, `cluster-anomaly`, `cluster-hardening`.
- Tag context with `decisionId`, `tenant`, `region`, `riskScore`, and `confidence`.
- Respond to dispatcher signals (`incident-ready`, `policy-risk`, `capacity-alert`) to synchronize fleets.

## Observability & telemetry
- Metrics: provisioning latency, upgrade success rate, autoscaler stability, anomaly count.
- Logs: structured `log.event="cluster.*"` including `decisionId`, `clusterId`, `tenant`.
- Dashboards: integrate `/kubernetes-cluster-manager metrics --format=prometheus` into fleet Grafana views.
- Alerts: `riskScore > 0.85`, upgrade failure rate >1%, cluster-anomaly events >3/hour.

## Failure handling & retries
- Retry cloud CLI/API calls (provision/scale/upgrade) up to 3× with exponential backoff (30s → 2m).
- On upgrade failure, trigger rollback (control plane, node pools) and emit `cluster-rollback` events.
- Preserve diagnostics/logs under `logs/cluster/{operationId}.log` until audits close the loop.
- Keep shared-context entries intact to maintain the audit trail.

## Human gates
- Required when:
  1. Risk score ≥ 0.9 for provisioning/upgrades or >20 tenants impacted.
  2. Hardening changes network policies/RBAC for production clusters.
  3. Dispatcher flags escalation after repeated upgrade failures.
- Confirmation template aligns with the orchestrator format:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/kubernetes-cluster-manager provision --clusterId=CLUSTER-DRY-RUN --dry-run`.
- Unit tests: `backend/kubernetes/cluster` ensures risk scoring and template parsing behave as expected.
- Integration: `scripts/validate-cluster-manager.sh` drives provisioning, scaling, and upgrade flows in emulator mode.
- Regression: nightly `scripts/nightly-cluster-health.sh` checks telemetry, autoscaling, and anomaly detection.

## References
- Provisioning templates: `infrastructure/cluster/`.
- Upgrade playbooks: `docs/DEPLOYMENT_STATUS.md`, `docs/EXECUTION-CHECKLIST.md`.
- Fleet dashboards: `monitoring/grafana/cluster-fleet`.

## Related skills
- `/ai-agent-orchestration`: responds to cluster events and coordinates downstream operations.
- `/incident-triage-runbook`: handles anomalies surfaced by health diagnostics.
- `/capacity-planning`: aligns scaling with forecasted demand.
- `/deployment-validation`: gates deployments that depend on healthy clusters.

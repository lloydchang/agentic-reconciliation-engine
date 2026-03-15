---
name: kubernetes-cluster-manager
description: >
  Operate Kubernetes clusters across AKS, EKS, GKE with AI-driven lifecycle orchestration, security hardening, and fleet observability.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Kubernetes Cluster Manager — World-class Fleet Operations Playbook

Provides AI-aided provisioning, scaling, upgrades, security hardening, and diagnostics across AKS/EKS/GKE clusters. Trigger when managing clusters, node pools, RBAC/network policies, version lifecycles, or telemetry-driven remediation.

## When to invoke
- Provision, scale, upgrade, or decommission clusters across AKS/EKS/GKE.
- Harden clusters (RBAC, network policies, workload identity) and enforce policy.
- Troubleshoot cluster health, autoscaler misbehavior, control-plane anomalies.
- Respond to dispatcher events (`incident-ready`, `capacity-alert`, `sla-risk`) that need cluster context.

## Capabilities
- **AI Cluster Risk Scoring**: predicts upgrade/scale risk using historical incidents, change vector, and telemetry.
- **Intelligent Scaling**: balances multi-node-pool autoscaling with forecasted demand and cost signals.
- **Smart Upgrade Orchestration**: sequences control plane/node upgrades with rollback safety nets.
- **Predictive Health Diagnostics**: uses AI to detect cluster anomalies (API latency, kubelet pressure) before impact.
- **Fleet awareness**: maintains inventory, compliance posture, and uptime telemetry across clouds.
- Integrates shared context (`shared-context://memory-store/cluster/<clusterId>`) for other skills.

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
| `clusterId` | Cluster identifier (format `platform-tenant-env`). | `aks-tenant-42-prod` |
| `platform` | Cloud provider (aks|eks|gke). | `gke` |
| `nodePool` | Node pool name. | `pool1` |
| `version` | Kubernetes version target. | `1.30` |
| `nodeCount` | Desired replica count for pool. | `5` |
| `policy` | Hardening or compliance policy. | `pod-security` |

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
1. Validate cluster requirements (platform quotas, node sizes, networking).
2. Provision via cloud CLIs (`az aks`, `eksctl`, `gcloud`) with idempotent arguments and tagging.
3. Deploy baseline security (network policies, PodSecurity Standards, workload identity, cert-manager, Prometheus stack).
4. Emit `cluster-provisioned` event with telemetry stored in `shared-context`.

### Intelligent scaling & autoscaler tuning
1. Read telemetry (autoscaler events, node CPU/mem) and forecast demand using AI patterns.
2. Scale node pools while honoring cost/risk signals from `cost-optimization` and `capacity-planning`.
3. Update node pool taints/labels and reconfigure autoscaler to avoid thrash.
4. Publish `nodepool-scaled` event and update inventory.

### Smart upgrades & rollback strategy
1. Score upgrade risk (difference between current/target versions, change history, incident rate) via AI.
2. Upgrade control plane followed by node pools sequentially with validation checks.
3. Rollback automatically if critical health checks fail; log reasons for postmortems.
4. Emit `upgrade-completed` event for dispatcher to trigger downstream compliance or deployments.

### Predictive health diagnostics
1. Run scheduled health checks (nodes, components, events, PVCs, RBAC).
2. Feed metrics into anomaly detection models (API latency, memory pressure, etc.).
3. Fire `cluster-anomaly` events when prediction crosses thresholds and tag with `riskScore`.
4. Trigger `incident-triage-runbook` or `deployment-validation` as needed.

## AI intelligence highlights
- **AI Cluster Risk Scoring**: ensembles evaluate upgrade/scale operations for probability of failure and automation readiness.
- **Intelligent Scaling**: patterns recognize burst demand patterns and tune autoscalers proactively.
- **Smart Upgrade Orchestration**: sequences upgrades with canary control plane validation, minimize disruptions.
- **Predictive Health Diagnostics**: identifies control-plane/cni/etcd anomalies before pods fail.

## Memory agent & dispatcher integration
- Store cluster telemetry under `shared-context://memory-store/cluster/<clusterId>` for other skills (incident, capacity, cost).
- Emit/consume events: `cluster-provisioned`, `cluster-scaled`, `cluster-upgrade`, `cluster-anomaly`, `cluster-hardening`.
- Tag records with `decisionId`, `tenant`, `region`, `riskScore`, `confidence`.

## Communication protocols
- Primary: CLI/webhook operations executing cloud CLIs and kubectl commands.
- Secondary: Event bus for `cluster-*` events consumed by dispatcher and skills.
- Fallback: When event bus unavailable, persist JSON artifacts to `artifact-store://cluster/<operationId>.json`.

## Observability & telemetry
- Metrics: provisioning latency, upgrade success rate, autoscaler stability, anomaly count.
- Logs: structured `log.event="cluster.*"` with `decisionId`, `clusterId`, `tenant`.
- Dashboards: integrate `/kubernetes-cluster-manager metrics --format=prometheus` into Grafana fleets.
- Alerts: riskScore > 0.85, upgrade failure rate > 1%, cluster-anomaly events > 3 per hour.

## Failure handling & retries
- Retry cloud CLI/API calls (provision/scale/upgrade) up to 3× with exponential backoff (30s → 2m).
- On upgrade failure, trigger rollback steps (control plane, node pools) and emit `cluster-rollback`.
- Preserve diagnostics/logs under `logs/cluster/<operationId>.log` until audits confirm closure.
- Do not delete shared-context entries to keep audit trail intact.

## Human gates
- Required when:
 1. Risk score ≥ 0.9 for provisioning/upgrades or >20 tenants impacted.
 2. Hardening operations change network policies or RBAC for production clusters.
 3. Dispatcher requests escalation after repeated upgrade failures.
- Use standard confirmation template capturing impact and reversibility.

## Testing & validation
- Dry-run: `/kubernetes-cluster-manager provision --clusterId=CLUSTER-DRY-RUN --dry-run`.
- Unit tests: `backend/kubernetes/cluster` ensures risk scoring and template parsing.
- Integration: `scripts/validate-cluster-manager.sh` drives provisioning, scaling, upgrade flows in emulator mode.
- Regression: nightly `scripts/nightly-cluster-health.sh` validates telemetry, autoscaling, and AI anomaly detection.

## References
- Provisioning templates: `infrastructure/cluster/`.
- Upgrade playbooks: `docs/DEPLOYMENT_STATUS.md`, `docs/EXECUTION-CHECKLIST.md`.
- Fleet dashboards: `monitoring/grafana/cluster-fleet`.

## Related skills
- `/ai-agent-orchestration`: receives cluster events and routes downstream operations.
- `/incident-triage-runbook`: handles anomalies surfaced from cluster health diagnostics.
- `/capacity-planning`: aligns scaling decisions with forecasted capacity.
- `/deployment-validation`: gates deployments dependent on healthy clusters.

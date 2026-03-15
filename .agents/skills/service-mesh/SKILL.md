---
name: service-mesh
description: >
  Install, harden, and operate a service mesh (Istio/Linkerd) with AI-augmented traffic control, zero-trust enforcement, and dispatcher-ready telemetry.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Service Mesh — World-class Zero-trust Connectivity Playbook

Manages mesh installation (Istio default, Linkerd option), mTLS/traffic policies, observability, and debugging while feeding AI-driven events into the dispatcher. Use when enabling secure service-to-service communication, running progressive traffic policies, or diagnosing mesh issues.

## When to invoke
- Install/upgrade Istio or Linkerd across clusters.
- Enforce mTLS, authorization policies, circuit breakers, retries, or traffic shifting (canary/blue-green).
- Diagnose inter-service connectivity, dependency graphs, or sidecar issues.
- React to dispatcher events (policy-risk, incident-ready, SLA burn-rate) requiring mesh-level controls.

## Capabilities
- Production-grade mesh install/upgrades with resource-safe settings and sidecar injection per namespace.
- AI-assisted policy enforcement (mTLS, authorization rules) and traffic management (canaries, circuit breakers).
- Observability integration (Kiali, Prometheus, Grafana) with dependency mapping and telemetry.
- Shared context integration `shared-context://memory-store/mesh/<operationId>` for downstream skills.
- Human-gated operations when mesh changes affect production communications.

## Invocation patterns

```bash
/service-mesh install --mesh=istio --profile=production --namespace=tenant-42
/service-mesh mtls --namespace=tenant-42 --mode=STRICT --humanGate=true
/service-mesh traffic --app=payments-api --namespace=tenant-42 --canaryWeight=10
/service-mesh observe --namespace=tenant-42 --duration=30m
/service-mesh debug --source=cart --destination=pricing --namespace=tenant-42
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `mesh` | Mesh provider (`istio|linkerd`). | `istio` |
| `namespace` | Namespace/tenant scope. | `tenant-42` |
| `mode` | mTLS enforcement mode (`STRICT|PERMISSIVE|DISABLED`). | `STRICT` |
| `app` | Application/service name. | `payments-api` |
| `canaryWeight` | Canary traffic percent. | `10` |
| `duration` | Observation window. | `30m` |

## Output contract

```json
{
  "operationId": "MESH-2026-0315-01",
  "operation": "install|mtls|traffic|observe|debug",
  "mesh": "istio",
  "namespace": "tenant-42",
  "status": "success|failure",
  "aiInsights": {
    "riskScore": 0.32,
    "policyViolations": 0,
    "anomalies": []
  },
  "events": [
    {
      "name": "mtls-enforced",
      "mode": "STRICT",
      "timestamp": "2026-03-15T08:12:00Z"
    }
  ],
  "issues": [],
  "logs": "shared-context://memory-store/mesh/MESH-2026-0315-01",
  "decisionContext": "redis://memory-store/mesh/MESH-2026-0315-01"
}
```

## World-class workflow templates

### Mesh installation & hardening
1. Install Istio (production profile) or lightweight Linkerd with resource-tuned settings.
2. Label namespaces for sidecar injection and apply global/default PeerAuthentication/AuthorizationPolicy templates.
3. Emit `mesh-installed` event with mesh metadata and dashboard URLs for shared context.

### mTLS & zero-trust policies
1. Configure PeerAuthentication (STRICT/PERMISSIVE) and AuthorizationPolicy for deny-all plus allow patterns.
2. AI risk scoring checks (policy compliance, exposure) before enforcing new rules.
3. Emit `mtls-mode-updated` events; watchers adjust dispatcher flows when anomalies detected.

### Traffic management & resilience
1. Define VirtualService/DestinationRule (Istio) or TrafficSplit (Linkerd) for canaries, retries, circuit breakers, and connection pools.
2. Monitor traffic metrics (errorRate, latency, saturation) for policy gating.
3. Emit `traffic-policy-applied` event; watchers can trigger rollback or `deployment-validation`.

### Observability & debugging
1. Deploy Kiali, Prometheus, Grafana dashboards, and enable Envoy stats for dependencies.
2. Generate dependency map via `kubectl get virtualservices/serviceentries/destinationrules`.
3. Run `istioctl analyze`, `proxy-config`, `kiali` graph; store outputs in shared context for incident response.

## AI intelligence highlights
- **AI Risk Scoring**: evaluates mesh changes against policy compliance, percent of traffic affected, and historical failures.
- **Intelligent Traffic Control**: recommends canary weights, circuit breaker thresholds, and retries with confidence values.
- **Anomaly Detection**: watches mTLS enforcement metrics for handshake failures or unauthorized connections.
- **Predictive Observability**: forecasts mesh component health (Pilot, Galley, Pilot, Control Plane) and surfaces warnings.

## Memory agent & dispatcher integration
- Store mesh state under `shared-context://memory-store/mesh/<operationId>`.
- Emit/consume events: `mesh-installed`, `mtls-enforced`, `traffic-policy-applied`, `mesh-debug`.
- Dispatcher listens to `incident-ready`, `policy-risk`, `capacity-alert` to trigger mesh actions automatically.
- Tag records with `decisionId`, `tenant`, `mesh`, `riskScore`.

## Communication protocols
- Primary: CLI commands (istioctl, kubectl, linkerd) producing JSON/warnings.
- Secondary: Event bus for `mesh-*` events consumed by dispatchers.
- Fallback: Persist artifacts in `artifact-store://mesh/<operationId>.json`.

## Observability & telemetry
- Metrics: mesh install duration, mtls failures, canary error rate, dependency map freshness.
- Logs: structured `log.event="mesh.operation"` with `operation`, `namespace`, `decisionId`.
- Dashboards: integrate `/service-mesh metrics --format=prometheus`.
- Alerts: policy violation count > 0, mtls handshake failure rate > threshold, canary error spikes.

## Failure handling & retries
- Retry CLI operations (install/mtls/traffic) up to 2× with exponential backoff.
- On failure, roll back to previous VirtualService/PeerAuthentication and emit `mesh-failed`.
- Preserve logs/contexts for audits until downstream acknowledgements.

## Human gates
- Required when:
 1. Enabling STRICT mTLS or policies affecting production namespaces.
 2. Traffic policies shift >20% of production traffic or change circuit-breaker sensitivity.
 3. Dispatcher flags manual inspection after retries/failure.
- Use the standard human gate confirmation template.

## Testing & validation
- Dry-run: `/service-mesh traffic --app=payments-api --namespace=test --dry-run`.
- Unit tests: `backend/mesh/` ensures config generation and risk scoring produce expected results.
- Integration: `scripts/validate-service-mesh.sh` installs mesh in emulator, applies policies, and monitors telemetry.
- Regression: nightly `scripts/nightly-mesh-smoke.sh` ensures mTLS, traffic shaping, and observability events are stable.

## References
- Istio values: `observability/values/`.
- Linkerd docs: `docs/OBSERVABILITY.md`.
- Mesh scripts: `scripts/service-mesh/`.

## Related skills
- `/deployment-validation`: gates deployments impacted by mesh traffic shifts.
- `/incident-triage-runbook`: receives mesh debug context for incidents.
- `/ai-agent-orchestration`: orchestrates mesh-aware workflows.

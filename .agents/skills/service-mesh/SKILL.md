---
name: service-mesh
description: >
  Install, harden, and operate a service mesh (Istio/Linkerd) with AI-augmented traffic control, zero-trust policies, and dispatcher-ready telemetry.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Service Mesh — World-class Zero-trust Connectivity Playbook

Manages mesh installation, mTLS enforcement, traffic policies, observability, and debugging while emitting AI events for orchestrator workflows.

## When to invoke
- Installing or upgrading Istio/Linkerd clusters (production or staging).
- Enforcing mTLS, authorization policies, or traffic management (canaries, blue/green, circuit breakers).
- Diagnosing inter-service connectivity, dependency graphs, or sidecar issues.
- Responding to dispatcher/memory agent events (`policy-risk`, `incident-ready`, `capacity-alert`) that require mesh-level controls.

## Capabilities
- **Production-grade mesh installs** (Istio default, Linkerd optional) with resource-sane defaults and sidecar injection per namespace.
- **AI-assisted policy enforcement** for mTLS, AuthorizationPolicies, RBAC, and traffic controls with rollback safeguards.
- **Intelligent traffic management** (canary weights, retries, circuit breakers, connection pool tuning) with confidence scoring.
- **Observability integration** (Kiali, Prometheus, Grafana, Envoy) with dependency mapping and telemetry enrichment.
- **Shared-context wiring** (`shared-context://memory-store/mesh/{operationId}`) so downstream skills know mesh state.

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
| `mesh` | Mesh provider (`istio`, `linkerd`). | `istio` |
| `namespace` | Namespace/tenant scope. | `tenant-42` |
| `mode` | mTLS enforcement mode (`STRICT`, `PERMISSIVE`, `DISABLED`). | `STRICT` |
| `app` | Service name for traffic policies or debugging. | `payments-api` |
| `canaryWeight` | Canary traffic percentage. | `10` |
| `duration` | Observation window/duration. | `30m` |

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
1. Install Istio (production profile) or Linkerd with resource-tuned settings.
2. Label namespaces for sidecar injection and apply baseline PeerAuthentication and AuthorizationPolicy templates.
3. Emit `mesh-installed` events with mesh metadata, dashboard URLs, and shared context for downstream skills.

### mTLS & zero-trust policies
1. Configure PeerAuthentication/Policy for STRICT/PERMISSIVE enforcement plus deny-by-default AuthorizationPolicies.
2. AI risk scoring verifies compliance and exposure before new policies apply.
3. Emit `mtls-mode-updated` events; watchers adjust dispatcher flows if anomalies surface.

### Traffic management & resilience
1. Define VirtualServices/DestinationRules (Istio) or TrafficSplits (Linkerd) for canaries, retries, circuit breakers, and connection pools.
2. Monitor metrics (error rate, latency, saturation) for gating decisions.
3. Emit `traffic-policy-applied` events that trigger/orchestrate rollbacks via `deployment-validation` or human review.

### Observability & debugging
1. Deploy Kiali, Prometheus, Grafana dashboards and enable Envoy stats/traces for dependency graphs.
2. Run `istioctl analyze`, `proxy-config`, `kiali` graphing and store outputs under `shared-context` for incident context.
3. Emit `mesh-debug` artifacts to help `incident-triage-runbook` and `deployment-validation` reduce MTTR.

## AI intelligence highlights
- **AI Risk Scoring** evaluates mesh changes against policy compliance, traffic impact, and historical incidents.
- **Intelligent Traffic Control** recommends canary weights, retry budgets, and circuit breaker thresholds with confidence intervals.
- **Anomaly Detection** monitors mTLS handshakes, policy violations, and unauthorized connections.
- **Predictive Observability** forecasts mesh control-plane health (Pilot, Citadel, Galley) and surfaces warnings.

## Memory agent & dispatcher integration
- Store mesh state under `shared-context://memory-store/mesh/{operationId}` and tag with `decisionId`, `tenant`, `mesh`, `riskScore`.
- Emit/consume `mesh-installed`, `mtls-enforced`, `traffic-policy-applied`, and `mesh-debug` events for dispatcher orchestration.
- Subscribe to upstream events (`incident-ready`, `policy-risk`, `capacity-alert`) so mesh actions align with broader stability goals.
- Provide fallback artifacts via `artifact-store://mesh/{operationId}.json` when messaging is unavailable.

## Observability & telemetry
- Metrics: mesh install duration, mTLS failure rate, canary error rate, dependency map freshness, policy violation count.
- Logs: structured `log.event="mesh.operation"` entries with `operation`, `namespace`, `decisionId`, `runId`.
- Dashboards: expose `/service-mesh metrics --format=prometheus` for SRE/ops views.
- Alerts: fire on policy violations, mTLS handshake failure spikes, or canary error surges.

## Failure handling & retries
- Retry CLI operations (install/mtls/traffic) up to 2× with exponential backoff.
- On failure, roll back to the last-known VirtualService/PeerAuthentication and emit `mesh-failed` events.
- Preserve logs/contexts for auditing until downstream acknowledgments arrive.
- Notify on-call channels when rollback loops, human gates, or repeated retries occur.

## Human gates
- Required when:
  1. Enabling STRICT mTLS or policies affecting production namespaces.
  2. Traffic policies shift >20% of production traffic or adjust circuit-breakers.
  3. Dispatcher requests manual inspection after retries or anomalies.
- Confirmation template:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/service-mesh traffic --app=payments-api --namespace=test --dry-run`.
- Unit tests: `backend/mesh/` ensures config generation and risk scoring behave as expected.
- Integration: `scripts/validate-service-mesh.sh` installs mesh in emulator mode, applies policies, and monitors telemetry.
- Regression: nightly `scripts/nightly-mesh-smoke.sh` keeps mTLS, traffic shaping, and observability events stable.

## References
- Istio values and defaults: `scripts/service-mesh/values/`.
- Linkerd guidance: `docs/OBSERVABILITY.md`.
- Mesh scripts: `scripts/service-mesh/`.

## Related skills
- `/deployment-validation`: gates deployments impacted by mesh traffic shifts.
- `/incident-triage-runbook`: ingests mesh debug context for incidents.
- `/ai-agent-orchestration`: orchestrates mesh-aware workflows.
- `/observability-stack`: powers telemetry feeding mesh policies.

---
name: k8s-troubleshoot
description: |
  Investigate Kubernetes cluster issues (pods, services, networking) with AI-guided diagnostics, remediation hints, and dispatcher context sharing.
allowed-tools:
  - Bash
  - Read
  - Write
  - Kubectl
---

# Kubernetes Troubleshoot — World-class Incident Drill Playbook

Runs targeted diagnostics across pods, services, and control planes, surfaces remediation steps, and feeds findings back into automation.

## When to invoke
- Pods crashlooping, stuck pending, or not reaching ready state.
- Services missing endpoints, network policies blocking traffic, or DNS failures.
- Control plane components (API server, scheduler) experiencing high latency/failures.
- Dispatcher events `pod-failure`, `service-issue`, `dns-error`.

## Capabilities
- **Pod/service diagnostics** (logs, events, describe, port-forward) fused with AI insights.
- **Network/path tracing** (kubectl exec, traceroute, CA certificates) for connection failures.
- **Control plane health** (scheduler, controller manager, etcd) checks with thresholds.
- **Remediation hints** referencing runbooks or script templates.
- **Shared context** at `shared-context://memory-store/k8s-troubleshoot/{operationId}`.

## Invocation patterns
```bash
/k8s-troubleshoot pod --namespace=payments --name=api-7ffdf
/k8s-troubleshoot service --namespace=payments --name=api
/k8s-troubleshoot dns --domain=payments.svc.cluster.local
/k8s-troubleshoot control-plane --component=apiserver
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `namespace` | Namespace for the resource. | `payments` |
| `name` | Pod/service name. | `api-7ffdf` |
| `domain` | DNS name/service. | `payments.svc.cluster.local` |
| `component` | Control plane component. | `apiserver` |

## Output contract
```json
{
  "operationId": "KT-2026-0315-01",
  "status": "diagnosed",
  "target": "pod/api-7ffdf",
  "issues": ["CrashLoopBackOff"],
  "actions": ["Check image pull secrets"],
  "logs": "shared-context://memory-store/k8s-troubleshoot/KT-2026-0315-01"
}
```

## World-class workflow templates
### Pod/service diagnostics
1. Run `kubectl describe/logs`, gather events, compare desired vs current.
2. Emit `k8s-pod-issue` with remediation hints.
3. Command stub: `/k8s-troubleshoot pod --namespace=payments --name=api-7ffdf`

### Network path tracing
1. Trace from pod to service using exec/traceroute.
2. Check NSG/NP/Endpoints, emit `k8s-network-issue`.
3. Command stub: `/k8s-troubleshoot service --namespace=payments --name=api`

### DNS validation
1. Query DNS entries, forward lookups, or test service discovery.
2. Emit `k8s-dns-issue` with fix guidance.
3. Command stub: `/k8s-troubleshoot dns --domain=payments.svc.cluster.local`

### Control plane checks
1. Run readiness checks on API server/controller manager/scheduler.
2. Emit `k8s-control-plane` events detailing latency/error.
3. Command stub: `/k8s-troubleshoot control-plane --component=apiserver`

## AI intelligence highlights
- **Root cause hints** correlate logs/events to expedite resets.
- **Prioritized guidance** ranks steps by impact/confidence.

## Memory agent & dispatcher integration
- Store diagnostics under `shared-context://memory-store/k8s-troubleshoot/{operationId}`.
- Emit: `k8s-pod-issue`, `k8s-network-issue`, `k8s-dns-issue`, `k8s-control-plane`.
- Tag with `decisionId`, `namespace`, `issue`, `confidence`.

## Observability & telemetry
- Metrics: issues per namespace, average remediation time.
- Logs: structured `log.event="k8s.troubleshoot"`.
- Alerts: stuck diagnostics, repeated support loops.

## Failure handling
- Retry `kubectl` commands on transient API timeouts.
- Fall back to lower-level diagnostics if APIs fail.

## Human gates
- Required when troubleshooting touches prod/network or needs exec notice.

## Testing & validation
- Dry-run: `/k8s-troubleshoot pod --namespace=test --name=test --dry-run`

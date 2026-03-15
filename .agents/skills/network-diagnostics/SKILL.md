---
name: network-diagnostics
description: |
  Diagnose network path issues, DNS resolution, latency, and connectivity across multi-cloud environments to keep service-to-service communication healthy.
allowed-tools:
  - Bash
  - Read
  - Write
  - Traceroute
---

# Network Diagnostics — World-class Connectivity Playbook

Tracks traffic paths, DNS, firewall policies, and CDN edges while providing actionable remediation guidance for net connectivity incidents.

## When to invoke
- Service connectivity issues between clusters, tenants, or clouds.
- DNS failures or slow resolution impacting APIs.
- SREs observe high latency, packet loss, or firewall drops.
- Dispatcher alerts `network-alert`, `dns-issue`, `connectivity-event`.

## Capabilities
- **Path tracing** using traceroute, ping, and service mesh telemetry.
- **DNS validation** for private/public zones, TTL issues, service discovery.
- **Firewall/ACL inspection** across clouds (NSG, security groups, NACLs).
- **Impact prioritization** quantifies service/customer effects.
- **Shared context** `shared-context://memory-store/network-diagnostics/{operationId}`.

## Invocation patterns
```bash
/network-diagnostics trace --source=aks-hub --destination=payments-api
/network-diagnostics dns --fqdn=payments.svc.cluster.local
/network-diagnostics firewall --resource=hub-firewall
/network-diagnostics perf --service=payments-api --metric=latency
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `source` | Source cluster/service. | `aks-hub` |
| `destination` | Destination service/endpoint. | `payments-api` |
| `fqdn` | Fully qualified domain name. | `payments.svc.cluster.local` |
| `resource` | Firewall/network ACL identifier. | `hub-firewall` |
| `service` | Service/app name. | `payments-api` |
| `metric` | Metric to measure. | `latency` |

## Output contract
```json
{
  "operationId": "ND-2026-0315-01",
  "status": "diagnosed",
  "path": ["aks-hub","vpn-gw","payments-cluster"],
  "latencyMs": 48,
  "issues": ["firewall drop"],
  "logs": "shared-context://memory-store/network-diagnostics/ND-2026-0315-01"
}
```

## World-class workflow templates
### Path tracing & validation
1. Run traceroute, ping, or mesh traces to map the path.
2. Correlate with firewall metrics and route tables.
3. Emit `network-path` event.
4. Command stub: `/network-diagnostics trace --source=aks-hub --destination=payments-api`

### DNS & service discovery
1. Query DNS entries (coreDNS, private zones) and check TTL.
2. Validate service discovery/resolution.
3. Emit `network-dns` event with remediation steps.
4. Command stub: `/network-diagnostics dns --fqdn=payments.svc.cluster.local`

### Firewall/segmentation checks
1. Inspect NSGs/NACLs, security groups, route tables.
2. Emit `network-firewall` and highlight blocked ports.
3. Command stub: `/network-diagnostics firewall --resource=hub-firewall`

### Performance & anomaly alerts
1. Measure latency, packet loss, throughput.
2. Forecast degradations and emit `network-perf` events.
3. Command stub: `/network-diagnostics perf --service=payments-api --metric=latency`

## AI intelligence highlights
- **Path risk scoring** quantifies connectivity failure probability.
- **DNS (re)attempt modeling** finds race conditions or TTL mismatches.
- **Firewall impact scoring** guides rule adjustments.

## Memory/dispatcher integration
- Persist outputs to shared context.
- Emit events: `network-path`, `network-dns`, `network-firewall`, `network-perf`.

## Observability & telemetry
- Metrics: path latency, DNS failure rate, firewall hits.
- Logs: `log.event="network.issue"`.

## Failure handling
- Retry traceroute/ping on transient network errors.
- Fall back to alternative path and log differences.

## Human gates
- Required when changes affect production networks or involve cross-cloud paths.

## Testing
- Dry-run: `/network-diagnostics trace --source=test --destination=test --dry-run`

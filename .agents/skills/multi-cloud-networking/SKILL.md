---
name: multi-cloud-networking
description: >
  Design, deploy, and operate multi-cloud networking with AI-assisted planning, risk scoring, and adaptive remediation.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Multi-Cloud Networking — World-class Connectivity Playbook

Manages hub-and-spoke topologies, private connectivity, DNS, peering, ingress, firewalls, and zero-trust policy across Azure, AWS, and GCP. Trigger when provisioning networks, troubleshooting connectivity, or responding to dispatcher alerts (`incident-ready`, `capacity-alert`, `sla-risk`).

## When to invoke
- Provision hubs/spokes, load balancers, private endpoints, VPNs, or transit networking.
- Diagnose connectivity issues or security exposures (DNS resolution, firewall gaps, cross-cloud paths).
- Respond to AI `riskScore` alerts from memory agents (e.g., high-cost transit, compliance exposure, capacity spike).
- During onboarding/offboarding tenants or implementing zero-trust policies.

## Capabilities
- **AI Path Planning**: calculates optimal routes, bandwidth headroom, and failover plans across clouds.
- **Intelligent Risk Scoring**: contextualizes connectivity changes with compliance, exposure, and availability risk.
- **Smart Remediation**: suggests firewall/NSG tweaks, DNS fixes, or peering updates with impact reasoning.
- **Predictive Diagnostics**: forecasts network saturation or peering degradation and raises alerts before outages.
- Policy automation for hub VNet/VPC, ExpressRoute/Direct Connect, Interconnect, private endpoints and service chains.
- Shared context integration (`shared-context://memory-store/networking/{operationId}`) for dispatchers/skills.

## Invocation patterns

```bash
/multi-cloud-networking provision --type=hub --region=us-east-1 --cloud=aks --cidr=10.0.0.0/16
/multi-cloud-networking peer --hub=hub-eastus --spoke=tenant-42 --cloud=azure --cidr=10.20.0.0/16
/multi-cloud-networking diagnose --tenant=tenant-42 --issue=dns --duration=15m
/multi-cloud-networking private-endpoint --resource=aks-sql --service=sql --tenant=tenant-42
/multi-cloud-networking alert --event=capacity --riskScore=0.82 --tenant=tenant-42
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `type` | Network operation type (hub/spoke/peering/vpn). | `hub` |
| `region` | Cloud region or location. | `us-east-1` |
| `cloud` | Provider (azure|aws|gcp). | `azure` |
| `tenant` | Tenant/workspace identifier. | `tenant-42` |
| `issue` | Diagnostic focus (`dns`, `nsg`, `private-endpoint`). | `dns` |
| `riskScore` | Dispatcher risk context for prioritization. | `0.85` |

## Output contract

```json
{
  "operationId": "NET-2026-0315-01",
  "operation": "provision|peer|private-endpoint|diagnose|vpn",
  "status": "success|failure|in_progress",
  "cloud": "azure",
  "region": "us-east-1",
  "tenant": "tenant-42",
  "riskScore": 0.78,
  "connectivity": "Reachable|Partial|Unreachable",
  "events": [
    { "name": "hub-peered", "timestamp": "2026-03-15T08:12:00Z" }
  ],
  "issues": [
    {
      "name": "dns-resolution",
      "severity": "warning",
      "recommendation": "pin private-zone to hub",
      "impact": "tenant-42"
    }
  ],
  "logs": "shared-context://memory-store/networking/NET-2026-0315-01",
  "decisionContext": "redis://memory-store/networking/NET-2026-0315-01"
}
```

## World-class workflow templates

### Hub-and-spoke provisioning
1. Create hub VNet/VPC with firewall/NGFW, Azure Firewall, AWS Transit Gateway, or GCP Cloud Router.
2. Provision spoke VNets/VPCs per tenant, apply NSG baseline (deny-all + allow hub).
3. Establish bidirectional peerings, private DNS link, and route propagation.
4. Emit `network-hub-provisioned` event with CIDR inventory for dispatcher/activity log.

### Private endpoint/networks
1. Create private endpoints (Azure SQL, Key Vault) or AWS PrivateLink, ensuring DNS zone registration.
2. Update private DNS records and configure fallback.
3. Validate connectivity with `az network watcher test-connectivity`, AWS Reachability Analyzer, or GCP Network Intelligence.
4. Emit `private-endpoint-ready` event and log result.

### Traffic & resilience diagnostics
1. Run path analysis (connectivity tests, NSG/fg rules) responding to `connectivity` issues.
2. Identify misconfigured NSGs, routes, or peering state.
3. Recommend repairs (route propagation, firewall rule) with AI-specified impact.
4. Emit `network-diagnostics` event with findings and severity.

### Predictive alerting & remediation
1. Monitor peering saturation, VPN drift, ExpressRoute/Direct Connect utilization.
2. Forecast exhaustion with AI models (trend + anomaly detection).
3. Trigger `network-risk-alert` when riskScore crosses threshold; link to `incident-triage-runbook`.

## AI intelligence highlights
- **AI Path Planning**: calculates failover-ready routes considering latency, bandwidth, and compliance impact.
- **Intelligent Risk Scoring**: weighs exposure changes (CIDR overlaps, public IPs, firewall holes) to produce riskScore for dispatchers.
- **Smart Remediation Suggestions**: ranks NSG/route fixes by impact, including cross-cloud dependencies.
- **Predictive Diagnostics**: expects VPN/peering degradation and warns before outages occur.

## Memory agent & dispatcher integration
- Store operation metadata under `shared-context://memory-store/networking/{operationId}`.
- Emit/consume events: `network-hub-provisioned`, `network-issue`, `network-alert`, `network-risk`.
- Tag events with `decisionId`, `tenant`, `riskScore`, `confidence`, `impact`.
- Subscribe to `agent-completed` events to adjust thresholds based on agent insights (cost/capacity/compliance).

## Communication protocols
- Primary: Azure CLI, AWS CLI, gcloud commands executed via scripts; results surfaced via standard output/JSON.
- Secondary: Event bus (Kafka/NATS) carrying `network-*` events for dispatchers.
- Fallback: Persist JSON to `artifact-store://networking/{operationId}` for pull-based consumption.

## Observability & telemetry
- Metrics: provisioning latency, diagnostics success rate, alert frequency, riskScore trending.
- Logs: structured entries with `log.event="networking.operation"` including `decisionId`, `cloud`, `region`, `tenant`.
- Dashboards: integrate `/multi-cloud-networking metrics --format=prometheus` into Grafana frameworks showing topologies and alerts.
- Alerts: riskScore > 0.85, >3 connectivity issues per hour, diagnostic failure > 10%.

## Failure handling & retries
- Retry provisioning/peering commands up to 3 times with exponential backoff (30s → 2m).
- On diagnostic failure, capture error context, store artifacts, and emit `network-diagnose-failed` event.
- Preserve shared-context and logs until dispatcher acknowledges; do not delete for audits.

## Human gates
- Required when:
 1. Risk score ≥ 0.9 or >20 tenants affected by networking changes.
 2. Public IPs or firewall rules are being modified for production workloads.
 3. Dispatcher requests escalation after >2 diagnostic retries.
- Use standard human gate template to log impact/reversibility.

## Testing & validation
- Dry-run: `/multi-cloud-networking provision --type=hub --region=us-east-1 --cloud=aws --dry-run=true`.
- Unit tests: `backend/networking/` ensures plan/risk calculations and parser logic.
- Integration: `scripts/validate-networking-stack.sh` deploys a temporary hub/spoke pair in emulator mode.
- Regression: nightly `scripts/nightly-networking-smoke.sh` verifies connectivity tests, diagnostics, and event flow.

## References
- Architecture patterns: `docs/MULTI_CLOUD_GITOPS_COMPARISON.md`, `docs/HUB-HA-RECOVERY.md`.
- Templates: `infrastructure/networking/`.
- Automation scripts: `scripts/networking/`.

## Related skills
- `/ai-agent-orchestration`: uses events to orchestrate other skills based on network risk.
- `/incident-triage-runbook`: receives critical connectivity alerts.
- `/capacity-planning`: correlates predicted network load with capacity plans.
- `/sla-monitoring-alerting`: ties network availability to SLA health.

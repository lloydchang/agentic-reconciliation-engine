---
name: multi-cloud-networking
description: >
  Design, deploy, and operate multi-cloud networking with AI-assisted planning, risk scoring, and adaptive remediation across Azure, AWS, and GCP.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Multi-Cloud Networking — World-class Connectivity Playbook

Coordinates hub-and-spoke topologies, private connectivity, DNS, peering, firewalls, and zero-trust policy while feeding dispatcher-ready telemetry.

## When to invoke
- Provision or modify hubs, spokes, load balancers, private endpoints, VPNs, or transit networking.
- Diagnose connectivity issues (DNS, firewall gaps, cross-cloud paths) or security exposures.
- Respond to memory agent alerts (`riskScore`, `policy-risk`, `capacity-alert`) that require network actions.
- Onboard/offboard tenants or implement zero-trust policies spanning clouds.

## Capabilities
- **AI path planning** computes optimal routes, bandwidth headroom, and failover plans across clouds.
- **Intelligent risk scoring** contextualizes connectivity changes with compliance, exposure, and availability risk.
- **Smart remediation** recommends firewall/NSG fixes, DNS adjustments, or peering updates with impact reasoning.
- **Predictive diagnostics** anticipates network saturation or peering degradation and alerts before outages.
- **Policy automation** handles hub VNet/VPCs, ExpressRoute/Direct Connect/Interconnect, private endpoints, and service chains.
- **Shared context** (`shared-context://memory-store/networking/{operationId}`) ensures other skills understand current topology.

## Invocation patterns

```bash
/multi-cloud-networking provision --type=hub --region=us-east-1 --cloud=azure --cidr=10.0.0.0/16
/multi-cloud-networking peer --hub=hub-eastus --spoke=tenant-42 --cloud=azure --cidr=10.20.0.0/16
/multi-cloud-networking diagnose --tenant=tenant-42 --issue=dns --duration=15m
/multi-cloud-networking private-endpoint --resource=aks-sql --service=sql --tenant=tenant-42
/multi-cloud-networking alert --event=capacity --riskScore=0.82 --tenant=tenant-42
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `type` | Operation type (`hub|spoke|peering|vpn`). | `hub` |
| `region` | Cloud region. | `us-east-1` |
| `cloud` | Provider (`azure|aws|gcp`). | `azure` |
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
2. Provision spoke VNets/VPCs per tenant, apply NSG baseline (deny-all + allow hub), and configure DNS.
3. Establish peerings, route propagation, and telemetry (Azure Network Watcher, Reachability Analyzer, Network Intelligence Center).
4. Emit `network-hub-provisioned` with CIDR inventory and update shared context.
5. Command stub: `/multi-cloud-networking provision --type=hub --region=us-east-1 --cloud=azure --cidr=10.0.0.0/16`.

### Private endpoint networking
1. Create private endpoints (Azure SQL/Key Vault) or AWS PrivateLink/GCP Private Service Connect and register DNS records.
2. Validate connectivity via `az network watcher test-connectivity`, AWS Reachability Analyzer, or GCP telnet tests.
3. Emit `private-endpoint-ready` events with diagnostic outputs and DNS confirmations.
4. Command stub: `/multi-cloud-networking private-endpoint --resource=aks-sql --service=sql --tenant=tenant-42`.

### Traffic & resilience diagnostics
1. Run path analysis (connectivity tests, NSG/firewall review, route table checks) for flagged issues.
2. Identify misconfigurations (overlapping CIDRs, firewall rule holes, peering states).
3. Recommend repairs with AI-calculated impact and rank them.
4. Emit `network-diagnostics` events for downstream automation.
5. Command stub: `/multi-cloud-networking diagnose --tenant=tenant-42 --issue=dns --duration=15m`.

### Predictive alerting & remediation
1. Monitor peering saturation, VPN drift, and ExpressRoute/Direct Connect utilization.
2. Forecast exhaustion using trend/anomaly models.
3. Trigger `network-risk-alert` when `riskScore` crosses thresholds and link to `incident-triage-runbook` or `capacity-planning`.
4. Command stub: `/multi-cloud-networking alert --event=capacity --riskScore=0.82 --tenant=tenant-42`.

## AI intelligence highlights
- **AI Path Planning** determines failover-ready routes factoring latency, bandwidth, and compliance.
- **Intelligent Risk Scoring** weights exposure changes (CIDR overlaps, public IPs, firewall holes) for dispatcher prioritization.
- **Smart Remediation Suggestions** rank NSG/route fixes by impact and cross-cloud dependencies.
- **Predictive Diagnostics** forecasts VPN/peering degradation before service impact occurs.

## Memory agent & dispatcher integration
- Store metadata under `shared-context://memory-store/networking/{operationId}` with tags (`decisionId`, `tenant`, `riskScore`, `confidence`, `impact`).
- Emit/consume events: `network-hub-provisioned`, `network-issue`, `network-alert`, `network-risk`, `private-endpoint-ready`.
- Subscribe to `agent-completed`, `incident-ready`, and `rule-change` events to adjust guardrails dynamically.
- Provide fallback artifacts via `artifact-store://networking/{operationId}.json` when event bus is offline.

## Observability & telemetry
- Metrics: provisioning latency, diagnostics success rate, alert frequency, riskScore trend.
- Logs: structured `log.event="networking.operation"` with `decisionId`, `cloud`, `region`, `tenant`.
- Dashboards: integrate `/multi-cloud-networking metrics --format=prometheus` into Grafana for topology/alert visibility.
- Alerts: riskScore > 0.85, >3 connectivity issues per hour, diagnostic failure rate >10%.

## Failure handling & retries
- Retry CLI/API commands up to 3× with exponential backoff (30s → 2m).
- On failures, emit `network-diagnose-failed`, capture artifacts, and escalate to human gates when needed.
- Preserve shared-context entries and logs until dispatchers acknowledge for audit purposes.

## Human gates
- Required when:
  1. `riskScore ≥ 0.9` or >20 tenants are affected.
  2. Public IPs, firewall rules, or peering settings change for production workloads.
  3. Dispatcher requests manual review after >2 diagnostic retries.
- Confirmation template matches orchestrator format:

```
⚠️  HUMAN GATE: [description]
    Impact: [what will change]
    Reversible: [Yes/No]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/multi-cloud-networking provision --type=hub --region=us-east-1 --cloud=aws --dry-run=true`.
- Unit tests: `backend/networking/` ensures plan/risk calculations and parser logic produce expected outputs.
- Integration: `scripts/validate-networking-stack.sh` deploys temporary hub/spoke topologies in emulator mode.
- Regression: nightly `scripts/nightly-networking-smoke.sh` verifies connectivity tests, diagnostics, and event flow.

## References
- Architecture patterns: `docs/MULTI_CLOUD_GITOPS_COMPARISON.md`, `docs/HUB-HA-RECOVERY.md`.
- Templates: `infrastructure/networking/`.
- Automation scripts: `scripts/networking/`.

## Related skills
- `/ai-agent-orchestration`: uses network risk events to coordinate other skills.
- `/incident-triage-runbook`: consumes critical connectivity alerts.
- `/capacity-planning`: links predicted network load with capacity plans.
- `/sla-monitoring-alerting`: correlates network availability with SLA health.

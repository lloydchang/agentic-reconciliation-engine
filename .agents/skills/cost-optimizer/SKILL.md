---
name: cost-optimizer
description: |
  Detect waste, orchestrate savings automations, and approve budgets with AI-weighted tradeoffs so FinOps teams reduce spend without compromising reliability.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Cost Optimizer — World-class FinOps Playbook

Finds cold resources, plan inefficiencies, and orchestrates approvals/recommendations for budget owners.

## When to invoke
- Regular cost reviews or budget exceed alerts.
- After scaling events or arch releases to recalc cost-per-tenant.
- When memory agents mark `cost-spike`, `waste-opportunity`, `rightsizing-needed`.

## Capabilities
- **Usage fingerprinting** surfaces idle resources, oversized VMs, unused IPs.
- **Savings orchestration** classifies opportunities, calculates ROI, and organizes approvals.
- **Budget compliance** ensures savings initiatives respect service SLAs and approvals.
- **Shared context** at `shared-context://memory-store/cost-optimizer/{operationId}`.

## Invocation patterns
```bash
/cost-optimizer scan --scope=production-resources
/cost-optimizer recommend --resource=vm-prod-3 --action=shutdown
/cost-optimizer forecast --tenant=tenant-42 --horizon=30d
/cost-optimizer approve --recommendation=REC-001 --reviewer=finops
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `scope` | Resource scope. | `production-resources` |
| `resource` | Resource name. | `vm-prod-3` |
| `tenant` | Tenant id. | `tenant-42` |
| `horizon` | Forecast days. | `30d` |
| `action` | Savings action. | `shutdown` |
| `recommendation` | Recommendation ID. | `REC-001` |

## Output contract
```json
{
  "operationId": "CO-2026-0315-01",
  "status": "review|approved",
  "savings": 120.5,
  "recommendations": [...],
  "logs": "shared-context://memory-store/cost-optimizer/CO-2026-0315-01"
}
```

## Workflows
### Waste detection
1. Scan costs, tag idle resources.
2. Emit `cost-waste` event.
3. Command stub: `/cost-optimizer scan --scope=production-resources`

### Recommendations
1. Create actions (shutdown, rightsizing).
2. Emit `cost-recommendation` with ROI.
3. Command stub: `/cost-optimizer recommend --resource=vm-prod-3 --action=shutdown`

### Forecast & compliance
1. Project spend for horizon.
2. Command stub: `/cost-optimizer forecast --tenant=tenant-42 --horizon=30d`

### Approval
1. Route to FinOps.
2. Command stub: `/cost-optimizer approve --recommendation=REC-001 --reviewer=finops`

## Related skills
- `/cost-optimization`, `/workflow-management`, `/stakeholder-comms-drafter`

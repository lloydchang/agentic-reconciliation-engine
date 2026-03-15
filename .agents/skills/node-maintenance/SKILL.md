---
name: node-maintenance
description: |
  Perform automated Kubernetes node maintenance operations including upgrades, patching, cordoning, draining, and health checks with zero-downtime orchestration.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Node Maintenance — Intelligent Kubernetes Node Lifecycle Management

AI-powered node maintenance orchestration for Kubernetes clusters, providing automated patching, upgrades, health monitoring, and zero-downtime maintenance operations across cloud providers and on-premises environments.

## When to invoke
- Scheduled OS patching and security updates.
- Kubernetes version upgrades requiring node rotation.
- Hardware maintenance or replacement operations.
- Node performance degradation requiring intervention.
- Cluster scaling requiring node preparation/cleanup.
- Emergency node evacuation for critical issues.

## Capabilities
- **Automated patching**: OS updates with rolling maintenance windows.
- **Node upgrades**: Kubernetes version upgrades with pod migration.
- **Health monitoring**: Continuous node health assessment and alerting.
- **Cordoning/draining**: Safe node isolation and workload evacuation.
- **Resource optimization**: Node capacity planning and workload balancing.
- **Multi-provider support**: Unified operations across AWS, Azure, GCP, and on-prem.

## Invocation patterns
```bash
/node-maintenance patch --nodes=node-01,node-02 --maintenance-window=2h
/node-maintenance upgrade --cluster=prod-cluster --version=1.28.0 --strategy=rolling
/node-maintenance drain --node=node-03 --force=false --timeout=30m
/node-maintenance health-check --cluster=prod-cluster --comprehensive=true
/node-maintenance cordon --nodes=node-pool-a --reason=maintenance
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `nodes` | Target node names or patterns. | `node-01,node-02` |
| `cluster` | Target Kubernetes cluster. | `prod-cluster` |
| `version` | Target Kubernetes version. | `1.28.0` |
| `maintenance-window` | Time window for operations. | `2h`, `24h` |
| `strategy` | Maintenance strategy. | `rolling`, `blue-green` |
| `timeout` | Operation timeout. | `30m`, `1h` |

## Output contract
```json
{
  "operationId": "NM-2026-0315-01",
  "operation": "node-upgrade",
  "cluster": "prod-cluster",
  "nodes": [
    {
      "name": "node-01",
      "currentVersion": "1.27.3",
      "targetVersion": "1.28.0",
      "status": "upgrading",
      "progress": {
        "percentage": 65,
        "phase": "draining-workloads",
        "podsRemaining": 3,
        "estimatedCompletion": "2026-03-15T14:30:00Z"
      },
      "health": {
        "ready": true,
        "issues": []
      }
    }
  ],
  "safety": {
    "podDisruptionBudget": "respected",
    "rollbackPlan": "available",
    "monitoring": "active"
  },
  "recommendations": [
    {
      "action": "pause-autoscaling",
      "reason": "Prevent interference with node replacement",
      "impact": "Ensures stable cluster during upgrade"
    }
  ]
}
```

## Dispatcher integration
**Triggers:**
- `scheduled-maintenance`: Time-based maintenance windows
- `security-patch-available`: Critical security updates requiring patching
- `node-health-degraded`: Node performance or stability issues
- `cluster-upgrade-required`: Kubernetes version upgrades needed
- `hardware-failure`: Physical node replacement required

**Emits:**
- `maintenance-started`: Node maintenance operation initiated
- `maintenance-progress`: Real-time status updates during operations
- `maintenance-complete`: Successful maintenance completion
- `maintenance-failed`: Operation failures requiring intervention
- `node-ready`: Node back online and ready for workloads

## AI intelligence features
- **Predictive maintenance**: ML-based failure prediction and scheduling
- **Workload analysis**: Intelligent pod migration planning and optimization
- **Risk assessment**: Automated risk evaluation for maintenance operations
- **Resource forecasting**: Capacity planning based on usage patterns
- **Automated scheduling**: Optimal maintenance window selection

## Human gates
- **Production clusters**: All maintenance operations require SRE approval
- **Critical nodes**: High-traffic node maintenance needs additional review
- **Extended downtime**: Operations >1 hour require stakeholder notification
- **Breaking changes**: Major version upgrades need change management approval

## Telemetry and monitoring
- Node availability and uptime metrics
- Maintenance operation success rates
- Pod migration success and timing
- Cluster stability during maintenance
- Cost impact of maintenance operations

## Testing requirements
- Node maintenance simulation in staging environments
- Pod migration testing with various workload types
- Rollback procedure validation
- Multi-node concurrent maintenance testing
- Integration testing with cluster autoscalers

## Failure handling
- **Node failures**: Automatic rollback and workload redistribution
- **Timeout exceeded**: Graceful operation abortion with cleanup
- **Pod eviction failures**: Force drain options with safety checks
- **Network issues**: Retry logic with exponential backoff
- **Resource constraints**: Queue operations and notify when capacity available

## Related skills
- **cluster-health-check**: Node health assessment integration
- **autoscaler-advisor**: Coordination with cluster autoscaling
- **deployment-validation**: Pre-maintenance deployment testing
- **incident-triage-runbook**: Maintenance-related incident response

## Security considerations
- Maintenance operations logged with audit trails
- Node isolation during maintenance prevents data exposure
- Credential rotation during node replacement
- Network policy enforcement during pod migration
- Compliance with maintenance window security requirements

## Performance characteristics
- Node preparation: <5 minutes per node
- Pod draining: <10 minutes for standard workloads
- Node upgrade: <15 minutes per node (cloud providers)
- Health validation: <1 minute per node
- Concurrent operations: Up to 20% of cluster nodes simultaneously

## Scaling considerations
- Distributed operation across multiple maintenance windows
- Queue-based scheduling for large clusters
- Parallel processing for independent node operations
- Load balancing across maintenance teams
- Automated batching for efficiency

## Success metrics
- Maintenance success rate: >99% for planned operations
- Downtime reduction: >95% reduction in unplanned outages
- Time to completion: <30 minutes average for node operations
- Pod migration success: >99.9% pods successfully migrated
- Cluster stability: <0.1% increase in error rates during maintenance

## API endpoints
```yaml
# REST API
POST /api/v1/nodes/maintenance
POST /api/v1/nodes/upgrade
POST /api/v1/nodes/health
POST /api/v1/nodes/drain

# GraphQL
mutation StartNodeMaintenance($nodes: [String!]!, $operation: String!) {
  startNodeMaintenance(nodes: $nodes, operation: $operation) {
    operationId
    status
    estimatedCompletion
  }
}
```

## CLI usage
```bash
# Install
npm install -g @agentskills/node-maintenance

# Schedule node patching
node-maintenance patch --nodes=node-01,node-02 --maintenance-window=2h

# Perform cluster upgrade
node-maintenance upgrade --cluster=prod-cluster --version=1.28.0

# Drain node safely
node-maintenance drain --node=node-03 --timeout=30m
```

## Configuration
```yaml
nodeMaintenance:
  clusters:
    prod-cluster:
      provider: aws
      region: us-east-1
      maintenanceWindows:
        - weekday: sunday
          startTime: "02:00"
          duration: "4h"
      upgradeStrategy: rolling
      maxUnavailableNodes: "20%"
  operations:
    patching:
      autoApprove: false
      maxConcurrent: 3
      timeout: "2h"
    upgrades:
      versionDriftThreshold: "2"
      autoSchedule: false
  safety:
    podDisruptionBudgetCheck: true
    healthChecksEnabled: true
    rollbackEnabled: true
  monitoring:
    prometheusIntegration: true
    alertingEnabled: true
```

## Examples

### Rolling node upgrade
```bash
/node-maintenance upgrade --cluster=prod-cluster --version=1.28.0 --strategy=rolling

# Operation: Rolling upgrade initiated for 15 nodes
# Strategy: Max 3 nodes unavailable, 2-minute delay between nodes
# Monitoring: Real-time pod migration tracking
# Safety: PDB respected, rollback plan ready
# Estimated completion: 45 minutes
# Status: Node-01 upgrading (pod draining in progress)
```

### Emergency node drain
```bash
/node-maintenance drain --node=node-03 --force=false --timeout=30m --reason=hardware-failure

# Node: node-03 cordoned and draining
# Workloads: 12 pods identified for migration
# PDB check: All budgets respected (no violations)
# Progress: 8/12 pods migrated successfully
# Estimated completion: 12 minutes remaining
# Rollback: Available if migration fails
```

### Scheduled patching
```bash
/node-maintenance patch --nodes=node-pool-a --maintenance-window=4h --auto-approve=false

# Maintenance: OS patching scheduled for node-pool-a (5 nodes)
# Window: Next available 4-hour window (Sunday 02:00-06:00)
# Impact assessment: Low-risk operation, minimal disruption
# Approval required: SRE review for production patching
# Monitoring: Automated health checks post-patching
```

## Migration guide

### From manual node maintenance
1. Assess current maintenance processes and identify pain points
2. Configure node-maintenance with cluster-specific settings
3. Start with low-risk operations (health checks, cordoning)
4. Implement automated scheduling for routine maintenance
5. Enable AI features for predictive maintenance

### From existing tools
- **kubectl drain/cordon**: node-maintenance provides intelligent orchestration
- **Cluster autoscalers**: Coordination with maintenance operations
- **Cloud provider tools**: Unified interface across providers
- **Custom scripts**: Replace with validated, monitored automation

## Troubleshooting

### Common issues
- **Pod eviction stuck**: Check PDB configurations and force drain options
- **Node not ready**: Verify cloud provider instance health
- **Upgrade failures**: Check version compatibility and rollback procedures
- **Timeout issues**: Adjust operation timeouts based on workload size
- **Resource constraints**: Reduce concurrent operations for large clusters

### Debug mode
```bash
node-maintenance --debug upgrade --cluster=prod-cluster --verbose
# Shows: node selection logic, pod migration planning, health checks
```

## Future roadmap
- AI-powered maintenance scheduling optimization
- Predictive hardware failure detection
- Zero-touch cluster upgrades with ML optimization
- Integration with chaos engineering for resilience testing
- Multi-cluster coordinated maintenance operations
- Quantum-safe node identity management

---

*Last updated: March 15, 2026*
*Version: 1.0.0*

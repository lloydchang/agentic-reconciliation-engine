# Node Maintenance Skill

## Name
node-maintenance

## Purpose
Perform safe node maintenance operations including draining, cordoning, patching, and upgrades across Kubernetes clusters.

## When to Use
- When performing node maintenance or upgrades
- When draining nodes for maintenance activities
- When cordoning nodes to prevent new pod scheduling
- When patching node operating systems or kernels
- When performing rolling updates of node pools

## Inputs
- Node identifiers and cluster context
- Maintenance operation type and schedule
- Pod disruption budgets and migration strategies
- Rollback and recovery procedures
- Monitoring and health check requirements

## Process
1. Validate node health and current workload distribution
2. Check pod disruption budgets and migration requirements
3. Cordon nodes to prevent new scheduling
4. Safely drain existing workloads with proper migration
5. Perform maintenance operations (patching, upgrades)
6. Uncordon nodes and validate cluster health
7. Monitor post-maintenance performance and stability

## Outputs
- Maintenance operation status and results
- Workload migration reports and pod status
- Node health validation results
- Rollback procedures and recovery steps
- Performance monitoring and stability reports

## Environment
- Kubernetes clusters with node pools
- Cluster autoscaling and node management systems
- Pod disruption budgets and scheduling policies
- Monitoring and alerting systems

## Dependencies
- kubectl and Kubernetes API access
- Cluster admin permissions for node operations
- Pod disruption budget configurations
- Monitoring and health check systems

## Scripts
- scripts/node_maintenance.py: Python script for node maintenance operations
- scripts/drain_node.py: Safe node draining script
- scripts/health_check.py: Node health validation script

## Trigger Keywords
node maintenance, draining, cordoning, patching, upgrades

## Human Gate Requirements
Production node changes

## API Patterns

### JavaScript
```javascript
// Perform node maintenance
const maintenance = await perform_node_maintenance({
  nodeName: "worker-node-001",
  operation: "drain|upgrade|patch",
  cluster: "production",
  priority: "high"
});

// Get maintenance results
const results = await get_maintenance_results({
  workflowId: maintenance.workflowId
});
```

### Rust
```rust
// Rust-based node maintenance
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct NodeMaintenanceRequest {
    pub node_name: String,
    pub operation: MaintenanceOperation,
    pub cluster: String,
    pub priority: Priority,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum MaintenanceOperation {
    Drain,
    Upgrade,
    Patch,
}

pub async fn perform_node_maintenance(request: NodeMaintenanceRequest) -> Result<NodeMaintenanceWorkflow, MaintenanceError> {
    // Safe node maintenance with workload protection
    let workflow = NodeMaintenanceWorkflow::new(request).await?;
    
    // Execute maintenance with safety checks
    workflow.maintain_safely().await?;
    
    Ok(workflow)
}
```

## Parameter Schema
```json
{
  "nodeName": "string (required) - name of the node to maintain",
  "operation": "string (required) - maintenance operation: drain|upgrade|patch|cordon",
  "cluster": "string (optional) - target cluster, defaults to current context",
  "namespace": "string (optional) - namespace to drain from, defaults to all",
  "gracePeriod": "number (optional) - pod termination grace period in seconds",
  "ignoreDaemonSets": "boolean (optional) - ignore DaemonSet pods, defaults to false",
  "force": "boolean (optional) - force drain even with unprotected pods, defaults to false",
  "environment": "string (optional) - target environment: dev|staging|prod",
  "priority": "string (optional) - operation priority: low|normal|high|critical",
  "dryRun": "boolean (optional) - perform dry run only, defaults to false"
}
```

## Return Schema
```json
{
  "workflowId": "uuid",
  "status": "started|running|completed|failed",
  "startedAt": "ISO8601 timestamp",
  "result": {
    "operation": "string - maintenance operation performed",
    "nodeName": "string - target node name",
    "podsMigrated": "number - number of pods safely migrated",
    "nodeStatus": "string - final node status after maintenance",
    "healthChecks": "array - post-maintenance health validation results",
    "rollbackSteps": "array - steps to rollback if needed",
    "estimatedDowntime": "string - estimated service downtime in seconds"
  },
  "errors": [],
  "metadata": {
    "cluster": "string - target cluster",
    "nodePool": "string - node pool affected",
    "riskScore": "number - operation risk score 1-10",
    "affectedPods": "number - total pods affected",
    "maintenanceDuration": "string - total maintenance duration"
  }
}
```

## Error Handling
```json
{
  "error": {
    "code": "VALIDATION_ERROR|NODE_UNAVAILABLE|PDB_VIOLATION|DRAIN_FAILED",
    "message": "Human-readable description",
    "details": {
      "field": "parameter_name",
      "expected": "expected_format",
      "actual": "provided_value"
    }
  }
}
```

# Kubectl Assistant Skill

## Name
kubectl-assistant

## Purpose
Generate and explain kubectl commands for Kubernetes cluster operations with safety checks and context awareness.

## When to Use
- When operators need help with kubectl command syntax
- When troubleshooting cluster issues and need diagnostic commands
- When performing routine operations but unsure of exact flags
- When learning Kubernetes operations and need guidance
- When generating automation scripts for cluster management

## Inputs
- Natural language request describing the operation
- Cluster context (namespace, environment)
- Resource type and target resources
- Operation intent (create, update, delete, query)
- Safety constraints and permissions

## Process
1. Parse user request to identify operational intent
2. Map intent to appropriate kubectl command pattern
3. Generate safe executable commands with proper flags
4. Add appropriate selectors and labels for targeting
5. Include safety warnings for destructive operations
6. Provide command explanation and expected behavior
7. Suggest alternative commands when applicable

## Outputs
- Executable kubectl command with proper syntax
- Detailed command explanation and behavior
- Safety warnings for destructive operations
- Alternative commands for different scenarios
- Expected output description and interpretation
- Prerequisites and permissions requirements

## Environment
- Kubernetes cluster with kubectl access
- RBAC permissions for target operations
- Proper cluster context configuration
- Access to cluster resources and namespaces

## Dependencies
- kubectl binary access
- Cluster API server connectivity
- Authentication and authorization setup
- Resource definitions and schemas
- Cluster context and namespace access

## Scripts
- scripts/gen_kubectl_cmds.py: Python script to generate and validate commands

## Trigger Keywords
kubectl, explain, generate, safe delete, gating

## Human Gate Requirements
Destructive commands

## API Patterns

### JavaScript
```javascript
// Generate kubectl command
const kubectlCmd = await generate_kubectl_command({
  operation: "get|describe|delete|apply",
  resourceType: "pods|services|deployments",
  namespace: "default",
  targetResource: "resource-name",
  priority: "normal"
});

// Get command status
const status = await get_kubectl_status({
  workflowId: kubectlCmd.workflowId
});
```

### Rust
```rust
// Rust-based kubectl command generation
use tokio::process::Command;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct KubectlRequest {
    pub operation: Operation,
    pub resource_type: ResourceType,
    pub namespace: String,
    pub target_resource: String,
    pub priority: Priority,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum Operation {
    Get,
    Describe,
    Delete,
    Apply,
}

pub async fn generate_kubectl_command(request: KubectlRequest) -> Result<KubectlWorkflow, Box<dyn std::error::Error>> {
    // Safe kubectl command generation with validation
    let workflow = KubectlWorkflow::new(request).await?;
    
    // Execute with safety checks
    workflow.execute_safe().await?;
    
    Ok(workflow)
}
```

## Parameter Schema
```json
{
  "operation": "string (required) - kubectl operation: get|describe|delete|apply|create",
  "resourceType": "string (required) - Kubernetes resource type: pods|services|deployments|configmaps|secrets",
  "namespace": "string (optional) - target namespace, defaults to 'default'",
  "targetResource": "string (optional) - specific resource name to target",
  "environment": "string (optional) - dev|staging|prod",
  "priority": "string (optional) - low|normal|high|critical",
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
    "command": "string - the generated kubectl command",
    "explanation": "string - detailed explanation of the command",
    "warnings": "array - safety warnings for destructive operations",
    "alternatives": "array - alternative commands for different scenarios",
    "expectedOutput": "string - description of expected command output"
  },
  "errors": [],
  "metadata": {
    "clusterContext": "string - kubectl context used",
    "namespace": "string - namespace targeted",
    "riskScore": "number - operation risk score 1-10"
  }
}
```

## Error Handling
```json
{
  "error": {
    "code": "VALIDATION_ERROR|PERMISSION_DENIED|CLUSTER_UNREACHABLE|TIMEOUT",
    "message": "Human-readable description",
    "details": {
      "field": "parameter_name",
      "expected": "expected_format",
      "actual": "provided_value"
    }
  }
}
```


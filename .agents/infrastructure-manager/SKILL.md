# Infrastructure Manager Skill

## Name
infrastructure-manager

## Purpose
Manage and orchestrate infrastructure resources across multiple cloud providers with automated provisioning, monitoring, and optimization capabilities.

## When to Use
- When provisioning new infrastructure resources
- When managing existing infrastructure deployments
- When optimizing infrastructure configurations
- When implementing infrastructure as code
- When managing multi-cloud environments

## Inputs
- Infrastructure resource specifications
- Cloud provider targets
- Configuration parameters
- Deployment strategies
- Monitoring and alerting requirements

## Process
1. Validate infrastructure specifications
2. Provision resources across target providers
3. Configure monitoring and alerting
4. Implement security and compliance controls
5. Optimize resource configurations
6. Generate management reports

## Outputs
- Provisioned infrastructure resources
- Configuration documentation
- Monitoring dashboards
- Compliance reports
- Optimization recommendations
- Cost analysis reports

## Environment
- Multi-cloud management platforms
- Infrastructure as code tools
- Configuration management systems
- Monitoring and observability platforms
- Security and compliance frameworks

## Dependencies
- Cloud provider APIs and SDKs
- Infrastructure as code frameworks
- Configuration management tools
- Monitoring and logging systems
- Security scanning tools

## Scripts
- scripts/provision_infra.py: Infrastructure provisioning script
- scripts/configure_monitoring.py: Monitoring setup script
- scripts/validate_compliance.py: Compliance validation script

## Trigger Keywords
infrastructure, provision, manage, multi-cloud, IaC

## Human Gate Requirements
Production infrastructure changes

## API Patterns

### JavaScript
```javascript
// Provision infrastructure resources
const provisioning = await provision_infrastructure({
  resourceType: "compute|storage|network|database",
  cloudProvider: "aws|azure|gcp|all",
  configuration: { /* resource config */ },
  deploymentStrategy: "blue-green|canary|rolling"
});

// Get infrastructure status
const status = await get_infrastructure_status({
  resourceId: provisioning.resourceId
});
```

### Rust
```rust
// Rust-based infrastructure management
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct InfrastructureRequest {
    pub resource_type: ResourceType,
    pub cloud_provider: CloudProvider,
    pub configuration: InfrastructureConfig,
    pub deployment_strategy: DeploymentStrategy,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum ResourceType {
    Compute,
    Storage,
    Network,
    Database,
}

pub async fn provision_infrastructure(request: InfrastructureRequest) -> Result<InfrastructureDeployment, InfraError> {
    // Comprehensive infrastructure provisioning
    let deployment = InfrastructureDeployment::new(request).await?;
    
    // Execute complete provisioning process
    deployment.provision_comprehensive().await?;
    
    Ok(deployment)
}
```

## Parameter Schema
```json
{
  "resourceType": "string (required) - type of resource: compute|storage|network|database",
  "cloudProvider": "string (required) - target cloud provider: aws|azure|gcp|all",
  "configuration": "object (required) - resource configuration parameters",
  "deploymentStrategy": "string (optional) - deployment strategy: blue-green|canary|rolling",
  "environment": "string (optional) - target environment: dev|staging|prod",
  "enableMonitoring": "boolean (optional) - enable monitoring, defaults to true",
  "validateCompliance": "boolean (optional) - validate compliance, defaults to true"
}
```

## Return Schema
```json
{
  "deploymentId": "uuid",
  "status": "started|running|completed|failed",
  "startedAt": "ISO8601 timestamp",
  "result": {
    "resourceType": "string - provisioned resource type",
    "cloudProvider": "string - target cloud provider",
    "resourceId": "string - unique resource identifier",
    "endpoints": "array - resource access endpoints",
    "configuration": "object - applied configuration",
    "monitoring": "object - monitoring configuration",
    "compliance": "object - compliance validation results"
  },
  "errors": [],
  "metadata": {
    "provisioningDuration": "string - total time for provisioning",
    "resourcesCreated": "number - number of resources created",
    "complianceScore": "number - compliance score 1-10",
    "costEstimate": "number - estimated monthly cost"
  }
}
```

## Error Handling
```json
{
  "error": {
    "code": "VALIDATION_ERROR|PROVISIONING_FAILED|COMPLIANCE_ERROR|CONFIGURATION_ERROR",
    "message": "Human-readable description",
    "details": {
      "field": "parameter_name",
      "expected": "expected_format",
      "actual": "provided_value"
    }
  }
}
```

# Load Balancer Tuner Skill

## Name
load-balancer-tuner

## Purpose
Optimize load balancer configurations for performance, traffic distribution, and resource efficiency across cloud platforms.

## When to Use
- When load balancer performance needs optimization
- When traffic patterns change requiring rebalancing
- When scaling load balancer capacity up or down
- When configuring health checks and routing rules
- When troubleshooting load balancer issues

## Inputs
- Load balancer identifier and configuration
- Traffic patterns and performance metrics
- Target backend services and health checks
- Environment and region specifications
- Optimization goals and constraints

## Process
1. Analyze current load balancer configuration and metrics
2. Identify performance bottlenecks and optimization opportunities
3. Generate optimized configuration recommendations
4. Validate changes against health checks and traffic patterns
5. Apply configuration changes with rollback capabilities
6. Monitor post-change performance and stability

## Outputs
- Optimized load balancer configuration
- Performance improvement recommendations
- Health check configurations and routing rules
- Traffic distribution analysis and reports
- Rollback procedures and validation results

## Environment
- Cloud load balancer services (ALB, NLB, CLB, etc.)
- Backend services and target groups
- Monitoring and metrics systems
- Configuration management tools

## Dependencies
- Cloud provider APIs and SDKs
- Load balancer service access and permissions
- Monitoring and metrics collection systems
- Configuration validation and testing tools

## Scripts
- scripts/tune_load_balancer.py: Python script for load balancer optimization
- scripts/validate_config.py: Configuration validation script

## Trigger Keywords
load balancer, tuning, optimization, traffic distribution

## Human Gate Requirements
Production traffic changes

## API Patterns

### JavaScript
```javascript
// Optimize load balancer
const lbTune = await optimize_load_balancer({
  loadBalancerId: "alb-web-prod-001",
  optimizationType: "performance|capacity|health-checks",
  targetEnvironment: "prod",
  priority: "normal"
});

// Get optimization results
const results = await get_lb_optimization_results({
  workflowId: lbTune.workflowId
});
```

### Rust
```rust
// Rust-based load balancer tuning
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct LoadBalancerRequest {
    pub load_balancer_id: String,
    pub optimization_type: OptimizationType,
    pub target_environment: String,
    pub priority: Priority,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum OptimizationType {
    Performance,
    Capacity,
    HealthChecks,
}

pub async fn optimize_load_balancer(request: LoadBalancerRequest) -> Result<LoadBalancerWorkflow, LoadBalancerError> {
    // High-performance load balancer optimization
    let workflow = LoadBalancerWorkflow::new(request).await?;
    
    // Apply optimizations with safety checks
    workflow.optimize_with_fallback().await?;
    
    Ok(workflow)
}
```

## Parameter Schema
```json
{
  "loadBalancerId": "string (required) - identifier of the load balancer to optimize",
  "optimizationType": "string (required) - type of optimization: performance|capacity|health-checks|security",
  "targetEnvironment": "string (optional) - target environment: dev|staging|prod",
  "region": "string (optional) - cloud region where load balancer is located",
  "priority": "string (optional) - operation priority: low|normal|high|critical",
  "dryRun": "boolean (optional) - perform dry run only, defaults to false",
  "rollbackEnabled": "boolean (optional) - enable automatic rollback on failure, defaults to true"
}
```

## Return Schema
```json
{
  "workflowId": "uuid",
  "status": "started|running|completed|failed",
  "startedAt": "ISO8601 timestamp",
  "result": {
    "optimizedConfig": "object - new load balancer configuration",
    "performanceImprovements": "array - list of performance improvements made",
    "healthChecks": "array - updated health check configurations",
    "trafficDistribution": "object - new traffic distribution settings",
    "rollbackPlan": "object - rollback procedures if needed"
  },
  "errors": [],
  "metadata": {
    "loadBalancerType": "string - type of load balancer (ALB, NLB, etc.)",
    "region": "string - cloud region",
    "riskScore": "number - operation risk score 1-10",
    "estimatedDowntime": "string - estimated service downtime in seconds"
  }
}
```

## Error Handling
```json
{
  "error": {
    "code": "VALIDATION_ERROR|PERMISSION_DENIED|CONFIGURATION_INVALID|TIMEOUT",
    "message": "Human-readable description",
    "details": {
      "field": "parameter_name",
      "expected": "expected_format",
      "actual": "provided_value"
    }
  }
}
```

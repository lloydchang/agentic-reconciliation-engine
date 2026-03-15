# Cost Optimizer Skill

## Name
cost-optimizer

## Purpose
Detect waste, orchestrate savings automations, and approve budgets with AI-weighted tradeoffs so FinOps teams reduce spend without compromising reliability.

## When to Use
- Regular cost reviews or budget exceed alerts
- After scaling events or architecture releases to recalc cost-per-tenant
- When memory agents mark `cost-spike`, `waste-opportunity`, `rightsizing-needed`
- When analyzing cloud spending patterns
- When forecasting future costs
- When validating ROI of cloud investments

## Inputs
- Target resources or services to analyze
- Analysis scope (production, staging, all)
- Resource types (compute, storage, network)
- Forecast horizon and parameters
- Budget constraints and approval requirements

## Process
1. Scan costs and tag idle resources
2. Create savings recommendations with ROI calculations
3. Forecast spend for specified horizon
4. Route recommendations for approval
5. Orchestrate approved savings actions
6. Monitor compliance and results

## Outputs
- Cost optimization recommendations
- Savings projections and ROI analysis
- Forecast reports and trend analysis
- Approval workflows and compliance status
- Orchestration results and impact metrics

## Environment
- Cloud billing and cost management APIs
- Usage monitoring and metrics collection
- Budget management and approval systems
- Workflow orchestration platforms

## Dependencies
- Cloud provider billing APIs
- Usage monitoring systems
- Budget management tools
- Workflow orchestration engines

## Scripts
- scripts/scan_costs.py: Python script for cost scanning
- scripts/generate_recommendations.py: Recommendation generation script
- scripts/forecast_spend.py: Spend forecasting script
- scripts/approve_savings.py: Approval workflow script

## Trigger Keywords
cost, spend, waste, FinOps, savings

## Human Gate Requirements
Resource deletion

## API Patterns

### JavaScript
```javascript
// Scan for cost optimization opportunities
const scan = await scan_costs({
  scope: "production|staging|all",
  resourceTypes: ["compute", "storage", "network"],
  threshold: 0.1
});

// Generate cost optimization recommendations
const recommendations = await generate_recommendations({
  resourceId: "vm-prod-3",
  action: "shutdown|rightsizing|resize"
});

// Forecast future spend
const forecast = await forecast_spend({
  tenant: "tenant-42",
  horizon: "30d",
  includeRecommendations: true
});
```

### Rust
```rust
// Rust-based cost optimization automation
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct CostOptimizationRequest {
    pub scope: Scope,
    pub resource_types: Vec<ResourceType>,
    pub threshold: f64,
    pub horizon: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum Scope {
    Production,
    Staging,
    All,
}

pub async fn optimize_costs(request: CostOptimizationRequest) -> Result<CostOptimization, CostError> {
    // Comprehensive cost optimization automation
    let optimization = CostOptimization::new(request).await?;
    
    // Execute complete optimization process
    optimization.optimize_comprehensive().await?;
    
    Ok(optimization)
}
```

## Parameter Schema
```json
{
  "scope": "string (required) - analysis scope: production|staging|all",
  "resourceTypes": "array (optional) - resource types to analyze: compute|storage|network",
  "threshold": "number (optional) - cost threshold for recommendations, defaults to 0.1",
  "resourceId": "string (optional) - specific resource ID for targeted analysis",
  "action": "string (optional) - recommended action: shutdown|rightsizing|resize",
  "tenant": "string (optional) - tenant ID for tenant-specific analysis",
  "horizon": "string (optional) - forecast horizon: 7d|30d|90d",
  "includeRecommendations": "boolean (optional) - include recommendations in forecast, defaults to true"
}
```

## Return Schema
```json
{
  "operationId": "uuid",
  "status": "started|running|completed|failed",
  "startedAt": "ISO8601 timestamp",
  "result": {
    "scope": "string - analyzed scope",
    "savings": "number - potential monthly savings",
    "recommendations": "array - cost optimization recommendations",
    "forecast": "object - spend forecast data",
    "compliance": "object - budget compliance status",
    "logs": "string - shared context location"
  },
  "errors": [],
  "metadata": {
    "resourcesAnalyzed": "number - number of resources analyzed",
    "recommendationsGenerated": "number - number of recommendations",
    "potentialSavings": "number - total potential savings",
    "riskScore": "number - operation risk score 1-10"
  }
}
```

## Error Handling
```json
{
  "error": {
    "code": "VALIDATION_ERROR|BILLING_API_ERROR|ANALYSIS_FAILED|INSUFFICIENT_DATA",
    "message": "Human-readable description",
    "details": {
      "field": "parameter_name",
      "expected": "expected_format",
      "actual": "provided_value"
    }
  }
}
```

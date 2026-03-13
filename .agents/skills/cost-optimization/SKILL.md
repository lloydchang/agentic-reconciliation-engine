---
name: cost-optimization
description: Analyze and optimize cloud infrastructure costs using specialized subagent. Use when reviewing spending, identifying savings opportunities, or planning cost reduction strategies.
argument-hint: "[targetResource] [analysisType] [timeframe]"
context: fork
agent: Plan
disable-model-invocation: false
user-invocable: true
---

# Cost Optimization Skill

Advanced cost analysis and optimization using specialized subagent execution. This skill runs in isolation to perform comprehensive cost analysis without affecting your main conversation context.

## Usage
```bash
/cost-optimization all-resources full 30d
/cost-optimization production-cluster usage 7d
/cost-optimization database-tier optimization 90d
```

## Subagent Architecture

This skill uses `context: fork` with `agent: Plan` to create an isolated execution environment optimized for:

- **Cost Analysis Engine**: Specialized algorithms for cost pattern recognition
- **Resource Optimization**: Automated identification of underutilized resources
- **Forecasting Models**: Predictive cost analysis and trend identification
- **ROI Calculations**: Investment return analysis for optimization recommendations

## Analysis Workflow

### 1. Resource Discovery & Classification
The subagent automatically discovers and categorizes resources:

```python
# Resource classification logic
resource_types = {
    'compute': ['VMs', 'Containers', 'Serverless'],
    'storage': ['Block Storage', 'Object Storage', 'Database Storage'],
    'network': ['Load Balancers', 'CDN', 'Data Transfer'],
    'database': ['SQL Databases', 'NoSQL Clusters', 'Caching'],
    'services': ['Monitoring', 'Security', 'Analytics']
}
```

### 2. Cost Pattern Analysis
```python
# Cost pattern recognition
def analyze_cost_patterns(historical_data):
    patterns = {
        'seasonal': detect_seasonal_trends(historical_data),
        'growth': identify_growth_rates(historical_data),
        'anomalies': detect_cost_anomalies(historical_data),
        'efficiency': calculate_resource_efficiency(historical_data)
    }
    return patterns
```

### 3. Optimization Opportunities
The subagent identifies optimization opportunities across multiple dimensions:

#### Compute Optimization
- **Right-sizing**: Match instance sizes to actual usage
- **Scheduling**: Power off non-production resources during off-hours
- **Spot Instances**: Use spot instances for fault-tolerant workloads
- **Autoscaling**: Implement dynamic scaling based on demand

#### Storage Optimization
- **Tier Selection**: Move infrequently accessed data to cheaper tiers
- **Lifecycle Policies**: Automate data archival and deletion
- **Compression**: Enable storage compression where applicable
- **Deduplication**: Eliminate duplicate data storage

#### Network Optimization
- **CDN Usage**: Optimize content delivery network utilization
- **Data Transfer**: Reduce inter-region data transfer costs
- **Load Balancer Optimization**: Right-size load balancing resources

## Analysis Types

### Usage Analysis
Focuses on resource utilization patterns:
- CPU, memory, storage utilization trends
- Network traffic patterns
- Database query performance
- Application usage metrics

**Output**: Utilization heatmaps, performance trends, capacity planning recommendations

### Optimization Analysis
Identifies specific cost-saving opportunities:
- Underutilized resources
- Over-provisioned services
- Inefficient configurations
- Alternative service recommendations

**Output**: Actionable optimization list with estimated savings

### Forecast Analysis
Predicts future costs based on trends:
- Growth projections
- Seasonal variations
- New service impact
- Market trend considerations

**Output**: 12-month cost forecast with confidence intervals

### Full Analysis
Comprehensive analysis including all types:
- Complete cost breakdown
- Optimization roadmap
- Risk assessment
- Implementation timeline

## Timeframes

### 7 Days
- Recent cost trends
- Immediate optimization opportunities
- Short-term forecast (30 days)
- Quick wins identification

### 30 Days
- Monthly cost patterns
- Monthly optimization opportunities
- Medium-term forecast (90 days)
- Seasonal trend analysis

### 90 Days
- Quarterly cost analysis
- Long-term optimization strategies
- Annual forecast (12 months)
- Strategic planning recommendations

## Subagent Capabilities

### Advanced Analytics
The Plan subagent provides:

#### Machine Learning Models
```python
# Cost prediction model
class CostPredictor:
    def __init__(self):
        self.models = {
            'linear_regression': LinearRegression(),
            'random_forest': RandomForestRegressor(),
            'lstm': LSTMModel()
        }
    
    def predict_costs(self, historical_data, horizon_days):
        # Ensemble prediction using multiple models
        predictions = {}
        for name, model in self.models.items():
            predictions[name] = model.predict(historical_data, horizon_days)
        
        # Weighted ensemble
        return self._ensemble_predictions(predictions)
```

#### Optimization Algorithms
```python
# Resource optimization engine
class ResourceOptimizer:
    def optimize_compute_resources(self, usage_data):
        # Right-sizing recommendations
        recommendations = []
        
        for resource in usage_data:
            current_size = resource.current_instance
            utilization = resource.avg_utilization
            
            if utilization < 0.3:
                # Downsize recommendation
                new_size = self._calculate_optimal_size(utilization)
                savings = self._calculate_savings(current_size, new_size)
                recommendations.append({
                    'type': 'downsize',
                    'resource': resource.id,
                    'from_size': current_size,
                    'to_size': new_size,
                    'monthly_savings': savings
                })
        
        return recommendations
```

### Risk Assessment
The subagent evaluates optimization risks:

#### Implementation Risk Matrix
| Optimization Type | Risk Level | Rollback Complexity | Impact |
|------------------|------------|-------------------|---------|
| Instance Resize | Low | Simple | Minimal |
| Storage Tier Change | Medium | Moderate | Medium |
| Database Migration | High | Complex | High |
| Network Redesign | Critical | Complex | Critical |

#### Business Impact Analysis
```python
def assess_business_impact(optimization, business_context):
    impact_factors = {
        'performance_degradation': estimate_performance_impact(optimization),
        'availability_risk': calculate_availability_risk(optimization),
        'data_loss_risk': assess_data_risk(optimization),
        'compliance_impact': check_compliance_impact(optimization)
    }
    
    return {
        'overall_risk': calculate_overall_risk(impact_factors),
        'mitigation_strategies': generate_mitigations(impact_factors),
        'approval_required': determine_approval_level(impact_factors)
    }
```

## Output Format

### Executive Summary
```
Cost Analysis Summary for: $TARGET_RESOURCE
Analysis Period: $TIMEFRAME
Analysis Date: $(date)

Current Monthly Cost: $X,XXX.XX
Projected Monthly Savings: $XXX.XX (X%)
Implementation Cost: $XX.XX
Net 12-Month Savings: $X,XXX.XX
ROI: XXX%

Risk Level: Low/Medium/High/Critical
Recommended Actions: X immediate, Y short-term, Z long-term
```

### Detailed Findings
```
Optimization Opportunities:

1. Compute Optimization
   - Underutilized VMs: 5 instances
   - Potential savings: $250/month
   - Risk: Low
   - Implementation: 1-2 weeks

2. Storage Optimization
   - Cold data to archive: 2TB
   - Potential savings: $180/month
   - Risk: Medium
   - Implementation: 2-4 weeks

3. Network Optimization
   - CDN optimization: 30% reduction
   - Potential savings: $120/month
   - Risk: Low
   - Implementation: 1 week
```

### Implementation Roadmap
```
Phase 1 (0-30 days): Quick Wins
- Resize underutilized instances
- Implement basic scheduling
- Enable storage lifecycle policies

Phase 2 (30-90 days): Strategic Changes
- Database optimization
- Network redesign
- Advanced autoscaling

Phase 3 (90+ days): Long-term Optimization
- Architecture review
- Cloud provider evaluation
- Cost governance implementation
```

## Integration with Temporal AI Agents

### API Endpoints
- `start_cost_analysis`: Initiates cost optimization workflow
- `get_cost_recommendations`: Retrieves detailed recommendations
- `implement_optimization`: Executes approved optimizations
- `monitor_savings`: Tracks actual savings vs projections

### Workflow Orchestration
1. **Data Collection**: Gather cost and usage data from all sources
2. **Analysis Execution**: Run specialized analysis algorithms
3. **Recommendation Generation**: Create prioritized optimization list
4. **Risk Assessment**: Evaluate implementation risks
5. **Approval Workflow**: Route high-risk changes for human review
6. **Implementation**: Execute approved optimizations
7. **Monitoring**: Track results and actual savings

## Advanced Features

### Real-time Cost Monitoring
```python
# Real-time cost tracking
class CostMonitor:
    def __init__(self):
        self.alert_thresholds = {
            'daily_budget': 1000,
            'anomaly_detection': 0.5,  # 50% increase
            'unusual_spend': 500
        }
    
    def monitor_costs(self):
        current_spend = self.get_current_spend()
        
        if current_spend > self.alert_thresholds['daily_budget']:
            self.trigger_budget_alert(current_spend)
        
        if self.detect_anomaly(current_spend):
            self.trigger_anomaly_alert(current_spend)
```

### Automated Optimization
```python
# Automated optimization engine
class AutoOptimizer:
    def __init__(self):
        self.auto_approve_threshold = {
            'savings_amount': 100,
            'risk_level': 'low',
            'implementation_time': 7  # days
        }
    
    def evaluate_auto_optimization(self, recommendation):
        if (recommendation.savings >= self.auto_approve_threshold['savings_amount'] and
            recommendation.risk <= self.auto_approve_threshold['risk_level'] and
            recommendation.implementation_time <= self.auto_approve_threshold['implementation_time']):
            
            return self.execute_optimization(recommendation)
        
        return self.request_approval(recommendation)
```

## Error Handling & Resilience

### Data Quality Issues
- Missing cost data: Use interpolation and estimation
- Inconsistent metrics: Normalize and validate data
- API failures: Implement retry logic with exponential backoff

### Analysis Failures
- Insufficient data: Extend analysis timeframe or use historical averages
- Complex environments: Break down into smaller analysis units
- Unexpected patterns: Flag for manual review

### Implementation Issues
- Resource conflicts: Implement dependency resolution
- Service disruptions: Implement blue-green deployment
- Rollback failures: Maintain detailed change logs

## Supporting Files

- [templates/cost-report.md](templates/cost-report.md): Comprehensive cost analysis report template
- [scripts/cost-analyzer.py](scripts/cost-analyzer.py): Advanced cost analysis algorithms
- [assets/optimization-rules.json](assets/optimization-rules.json): Optimization rule engine configuration
- [scripts/roi-calculator.sh](scripts/roi-calculator.sh): ROI calculation and validation

## Examples

### Full Cost Analysis
```bash
/cost-optimization all-resources full 30d
```

### Usage Pattern Analysis
```bash
/cost-optimization production-cluster usage 7d
```

### Strategic Optimization Planning
```bash
/cost-optimization enterprise-infrastructure optimization 90d
```

## Related Skills

- `/compliance-check`: Ensure optimizations maintain compliance
- `/security-analysis`: Verify security implications of changes
- `/infrastructure-discovery`: Identify optimization targets
- `/workflow-management`: Orchestrate optimization workflows

## Best Practices

1. **Baseline Establishment**: Establish cost baseline before optimization
2. **Gradual Implementation**: Implement changes in phases to minimize risk
3. **Continuous Monitoring**: Monitor actual savings vs projections
4. **Regular Reviews**: Schedule quarterly cost optimization reviews
5. **Stakeholder Communication**: Keep stakeholders informed of changes
6. **Documentation**: Maintain detailed records of all optimizations
7. **Compliance Validation**: Ensure all changes maintain regulatory compliance

## OpenAI Codex Integration

This section documents the OpenAI Codex-style cost optimization that has been integrated into the Claude skills framework.

### Systematic Cost Optimization Approach

When performing cost optimization, follow these systematic steps:

#### 1. Cost Analysis
- Analyze current spending patterns
- Identify cost drivers and trends
- Break down costs by service and resource
- Compare against budgets and benchmarks

#### 2. Resource Assessment
- Review resource utilization metrics
- Identify underutilized resources
- Check for oversized or overprovisioned resources
- Analyze resource efficiency

#### 3. Optimization Opportunities
- Right-size resources based on usage
- Implement auto-scaling policies
- Use reserved instances or savings plans
- Optimize storage and data transfer

#### 4. Implementation
- Apply optimization recommendations
- Monitor cost changes
- Validate performance impact
- Document optimization results

### Optimization Areas
- **Compute**: VM sizing, auto-scaling, spot instances
- **Storage**: Tiered storage, lifecycle policies, cleanup
- **Network**: Data transfer optimization, CDN usage
- **Licensing**: Software license optimization

### Cost Metrics
```bash
# Resource utilization
# Cost per unit of work
# Spending trends
# Budget variance
# ROI analysis
```

### Automation Scripts
- Resource rightsizing algorithms
- Cost anomaly detection
- Automated cleanup routines
- Budget alerting systems

### Integration Points
- Cloud provider cost APIs
- Monitoring and metrics systems
- Budget management tools
- Resource management platforms

### File Locations
- Cost analysis: `backend/cost/`
- Optimization scripts: `scripts/cost-optimization/`
- Reports: `reports/cost/`
- Configurations: `config/cost.yaml`

### Best Practices
- Monitor costs continuously
- Set up budget alerts
- Regularly review resource utilization
- Implement cost governance policies
- Balance cost optimization with performance
- Document optimization decisions and results

### Common Savings Strategies
- Use spot instances for non-critical workloads
- Implement auto-scaling for variable demand
- Clean up unused resources regularly
- Optimize data storage tiers
- Consolidate underutilized resources
- Use prepaid pricing models for predictable workloads

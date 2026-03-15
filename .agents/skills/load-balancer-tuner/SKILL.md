---
name: load-balancer-tuner
description: |
  Optimize load balancer configurations and routing rules for improved performance, cost efficiency, and reliability across cloud platforms.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Load Balancer Tuner — Intelligent Load Balancing Optimization

AI-powered optimization of load balancer configurations, routing rules, and traffic distribution across AWS ALB/NLB, Azure Load Balancer, GCP Load Balancer, and Istio service meshes.

## When to invoke
- Load balancer performance issues (high latency, connection failures).
- Cost optimization opportunities identified in load balancer usage.
- Traffic distribution imbalances causing service degradation.
- Scaling events requiring load balancer reconfiguration.
- Security events requiring WAF rule adjustments.

## Capabilities
- **Configuration optimization**: Analyze and tune load balancer settings for performance.
- **Traffic analysis**: Monitor and optimize traffic distribution patterns.
- **Cost optimization**: Identify and implement cost-saving configurations.
- **Health check tuning**: Optimize health check configurations for faster failover.
- **Security enhancement**: Configure WAF rules and DDoS protection.
- **Multi-cloud support**: Unified optimization across AWS, Azure, and GCP.

## Invocation patterns
```bash
/load-balancer-tuner analyze --load-balancer=alb-prod-web --platform=aws
/load-balancer-tuner optimize --target=cost --region=us-east-1
/load-balancer-tuner rebalance --service=my-app --algorithm=round-robin
/load-balancer-tuner secure --waf-rules=sql-injection, xss
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `load-balancer` | Load balancer identifier or ARN. | `alb-prod-web` |
| `platform` | Cloud platform (`aws`, `azure`, `gcp`). | `aws` |
| `target` | Optimization target (`performance`, `cost`, `reliability`). | `cost` |
| `service` | Target service for traffic rebalancing. | `my-app` |
| `region` | Cloud region for optimization scope. | `us-east-1` |

## Output contract
```json
{
  "operationId": "LBT-2026-0315-01",
  "optimizations": [
    {
      "type": "performance",
      "loadBalancer": "alb-prod-web",
      "recommendations": [
        {
          "action": "increase-connection-draining-time",
          "currentValue": "30",
          "recommendedValue": "60",
          "impact": "Reduced connection errors during deployments",
          "risk": "low"
        }
      ]
    }
  ],
  "costSavings": {
    "monthly": "$245.00",
    "percentage": "15%",
    "breakEvenDays": "45"
  },
  "implementation": {
    "terraformChanges": "3 files modified",
    "rollbackPlan": "Available via --rollback flag",
    "testingRequired": "Load testing recommended"
  }
}
```

## Dispatcher integration
**Triggers:**
- `load-balancer-alert`: Performance or cost alerts
- `traffic-spike`: Sudden traffic increases requiring optimization
- `deployment-complete`: Post-deployment load balancer tuning
- `cost-anomaly`: Load balancer cost optimization opportunities

**Emits:**
- `optimization-recommendations`: AI-generated optimization suggestions
- `configuration-changes`: Load balancer configuration updates
- `cost-savings-achieved`: Actual cost reductions from optimizations

## AI intelligence features
- **Traffic pattern analysis**: Machine learning-based traffic prediction
- **Cost optimization**: AI-driven cost-benefit analysis for configurations
- **Performance modeling**: Predictive performance impact assessment
- **Anomaly detection**: Automatic identification of suboptimal configurations
- **Multi-objective optimization**: Balance performance, cost, and reliability

## Human gates
- **Production changes**: Require SRE approval for production load balancers
- **Cost impacts >10%**: High-cost changes need financial review
- **Traffic rerouting**: Changes affecting >50% traffic require stakeholder approval

## Telemetry and monitoring
- Load balancer performance metrics (latency, throughput, error rates)
- Cost optimization ROI tracking
- Configuration drift detection
- Traffic distribution analytics

## Testing requirements
- Load testing before and after optimization
- Traffic distribution validation
- Failover testing for health check changes
- Cost impact verification

## Failure handling
- **API failures**: Retry with exponential backoff, fallback to manual mode
- **Invalid configurations**: Validate before applying, provide rollback
- **Cost overruns**: Monitor and alert on unexpected cost increases
- **Performance degradation**: Automatic rollback on SLA violations

## Related skills
- **autoscaler-advisor**: Load balancer optimization for autoscaling events
- **capacity-planner**: Capacity planning integration with load balancing
- **network-diagnostics**: Network-level troubleshooting for load balancer issues
- **cost-optimizer**: Cost optimization coordination across infrastructure

## Security considerations
- WAF rule changes require security review
- Health check configurations never expose sensitive endpoints
- Access logs are anonymized and aggregated
- Configuration changes are auditable and versioned

## Performance characteristics
- Analysis: <30 seconds for single load balancer
- Optimization planning: <5 minutes for complex configurations
- Implementation: Scales with infrastructure size
- Monitoring: Real-time metrics with <5 second latency

## Scaling considerations
- Distributed analysis across regions
- Parallel optimization of multiple load balancers
- Caching of cloud provider API responses
- Event-driven processing for high-frequency changes

## Success metrics
- Average cost reduction: >15% for optimized load balancers
- Performance improvement: >20% reduction in P95 latency
- Uptime improvement: >99.99% for tuned configurations
- Time to optimization: <30 minutes from alert to implementation

## API endpoints
```yaml
# REST API
POST /api/v1/load-balancer/analyze
POST /api/v1/load-balancer/optimize
POST /api/v1/load-balancer/rebalance

# GraphQL
mutation OptimizeLoadBalancer($id: String!, $target: String!) {
  optimizeLoadBalancer(id: $id, target: $target) {
    recommendations {
      action
      impact
      risk
    }
  }
}
```

## CLI usage
```bash
# Install
npm install -g @agentskills/load-balancer-tuner

# Analyze load balancer
load-balancer-tuner analyze --load-balancer=alb-prod-web --platform=aws

# Optimize for cost
load-balancer-tuner optimize --target=cost --region=us-east-1

# Rebalance traffic
load-balancer-tuner rebalance --service=my-app --algorithm=least-connections
```

## Configuration
```yaml
loadBalancerTuner:
  platforms:
    aws:
      regions: [us-east-1, us-west-2]
      defaultOptimizationTarget: performance
    azure:
      resourceGroups: [prod-rg, staging-rg]
      subscriptionId: xxx-xxx-xxx
  optimizationRules:
    costThreshold: 1000  # Monthly cost threshold for optimization
    performanceTarget: 0.1  # P95 latency target in seconds
  security:
    wafEnabled: true
    logRetentionDays: 90
```

## Examples

### Cost optimization
```bash
/load-balancer-tuner optimize --target=cost --platform=aws --region=us-east-1

# Analysis: Found 3 load balancers with optimization opportunities
# Recommendation: Switch NLB to ALB for web traffic - saves $180/month
# Implementation: terraform plan generated, apply with --confirm
```

### Performance tuning
```bash
/load-balancer-tuner analyze --load-balancer=alb-prod-web

# Issue: Health check interval too aggressive (5s -> 30s recommended)
# Impact: Reduced API calls by 80%, improved backend stability
# Risk: Low - maintains availability with faster convergence
```

### Traffic rebalancing
```bash
/load-balancer-tuner rebalance --service=my-app --algorithm=round-robin

# Current: 70/30 traffic split causing backend overload
# Recommendation: Implement round-robin with health-based weighting
# Result: Balanced load, reduced P95 latency by 35%
```

## Migration guide

### From manual load balancer management
1. Audit existing load balancer configurations
2. Configure cloud provider access and permissions
3. Run initial analysis to establish baseline
4. Implement automated optimization with human oversight

### From other tools
- **AWS Load Balancer Controller**: load-balancer-tuner provides optimization layer
- **Azure Traffic Manager**: Enhances with AI-driven optimization
- **Custom scripts**: Replace with validated, monitored automation

## Troubleshooting

### Common issues
- **API permissions**: Verify cloud provider IAM roles and permissions
- **Configuration drift**: Use --drift-check to identify manual changes
- **Cost surprises**: Monitor with --cost-tracking for unexpected increases
- **Performance regression**: Automatic rollback available with --rollback

### Debug mode
```bash
load-balancer-tuner --debug analyze --load-balancer=my-lb
# Shows: API calls, analysis steps, decision reasoning
```

## Future roadmap
- Multi-cloud load balancer federation
- AI-powered predictive scaling integration
- Advanced WAF rule optimization
- Real-time traffic anomaly detection
- Integration with service mesh traffic management

---

*Last updated: March 15, 2026*
*Version: 1.0.0*

---
name: observability-aggregator
description: |
  Deploy, configure, and operate a world-class observability platform (metrics, logs, traces, alerts) that feeds dispatcher intelligence and AI insights.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Observability Aggregator — Comprehensive Observability Platform Management

AI-powered deployment, configuration, and operation of complete observability stacks including metrics collection, log aggregation, distributed tracing, and intelligent alerting across cloud platforms.

## When to invoke
- Setting up new observability infrastructure from scratch.
- Optimizing existing monitoring stacks for better coverage.
- Troubleshooting observability pipeline issues.
- Scaling observability for larger deployments.
- Implementing SLO/SLI monitoring and alerting.
- Integrating new services into existing observability.

## Capabilities
- **Platform deployment**: Automated setup of Prometheus, Grafana, Jaeger, Loki.
- **Configuration management**: Intelligent tuning of collection agents and exporters.
- **Service discovery**: Automatic discovery and monitoring of new services.
- **Alert management**: Smart alert rules and escalation policies.
- **Dashboard generation**: AI-powered dashboard creation and optimization.
- **Cost optimization**: Efficient storage and processing of observability data.

## Invocation patterns
```bash
/observability-aggregator deploy --platform=kubernetes --components=prometheus,grafana,loki
/observability-aggregator optimize --target=cost --retention=90d
/observability-aggregator dashboard --service=my-app --metrics=custom
/observability-aggregator alert --slo=99.9 --service=checkout
/observability-aggregator troubleshoot --component=prometheus --issue=high-cpu
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `platform` | Target platform (`kubernetes`, `ecs`, `lambda`). | `kubernetes` |
| `components` | Observability components to deploy. | `prometheus,grafana` |
| `target` | Optimization target (`performance`, `cost`, `coverage`). | `cost` |
| `service` | Target service for monitoring. | `checkout-service` |
| `slo` | Service Level Objective percentage. | `99.9` |
| `retention` | Data retention period. | `90d`, `1y` |

## Output contract
```json
{
  "operationId": "OA-2026-0315-01",
  "deployment": {
    "status": "completed",
    "components": {
      "prometheus": {
        "version": "2.45.0",
        "endpoints": {
          "query": "http://prometheus:9090",
          "pushgateway": "http://pushgateway:9091"
        }
      },
      "grafana": {
        "version": "10.2.0",
        "dashboardUrl": "http://grafana:3000",
        "datasources": ["prometheus", "loki", "jaeger"]
      }
    },
    "monitoring": {
      "servicesDiscovered": 45,
      "metricsCollected": 1250,
      "alertRules": 23
    }
  },
  "recommendations": [
    {
      "type": "optimization",
      "component": "prometheus",
      "action": "Enable TSDB compaction",
      "benefit": "30% storage reduction",
      "risk": "low"
    }
  ]
}
```

## Dispatcher integration
**Triggers:**
- `observability-gap`: Missing monitoring coverage detected
- `performance-issue`: Observability needed for troubleshooting
- `scaling-event`: Observability scaling required
- `new-service`: Service deployment requiring monitoring

**Emits:**
- `observability-deployed`: Complete stack ready for use
- `monitoring-active`: Services being actively monitored
- `alert-triggered`: Observability-based alerts firing
- `insights-generated`: AI insights from observability data

## AI intelligence features
- **Smart configuration**: AI-driven tuning of collection intervals and retention
- **Anomaly detection**: ML-based anomaly detection in metrics and logs
- **Root cause analysis**: Correlate metrics, logs, and traces for insights
- **Predictive alerting**: Forecast issues before they impact users
- **Dashboard optimization**: Automatically improve dashboard layouts

## Human gates
- **Production deployment**: Full observability stack changes require SRE review
- **Cost impacts >$1000/month**: Significant cost changes need approval
- **Data retention changes**: Reducing retention below 30 days requires review
- **Security monitoring**: Changes to security-related observability need validation

## Telemetry and monitoring
- Component health and uptime metrics
- Data collection success rates
- Alert accuracy and false positive rates
- Query performance and latency
- Storage utilization and cost tracking

## Testing requirements
- End-to-end observability pipeline testing
- Alert rule validation and accuracy testing
- Dashboard rendering and data accuracy
- Performance testing under load
- Integration testing with various platforms

## Failure handling
- **Component failures**: Automatic restart and health checks
- **Data loss scenarios**: Backup and recovery procedures
- **Configuration drift**: Continuous reconciliation and validation
- **Scaling failures**: Graceful degradation and alerting
- **Network issues**: Retry logic and alternative routing

## Related skills
- **observability-stack**: Core observability deployment and management
- **log-classifier**: Log analysis integration with metrics
- **alert-prioritizer**: Alert management and prioritization
- **kpi-report-generator**: KPI generation from observability data

## Security considerations
- Secure configuration of all observability endpoints
- Encryption of metrics and log data in transit
- Access control and authentication for dashboards
- Audit logging of all configuration changes
- Compliance with data retention and privacy regulations

## Performance characteristics
- Deployment time: <15 minutes for standard stack
- Query latency: <2 seconds for 95th percentile
- Data ingestion: 100k metrics/second sustained
- Storage efficiency: 50% compression with indexing
- Alert evaluation: <1 second per rule set

## Scaling considerations
- Horizontal scaling of collection agents
- Distributed storage for metrics and logs
- Load balancing for query endpoints
- Caching layers for frequently accessed data
- Auto-scaling based on ingestion rates

## Success metrics
- Service coverage: >98% of services monitored
- Mean time to detection: <5 minutes for critical issues
- Alert accuracy: >95% true positive rate
- Query performance: <1 second average response time
- User adoption: >90% of teams using generated dashboards

## API endpoints
```yaml
# REST API
POST /api/v1/observability/deploy
POST /api/v1/observability/optimize
POST /api/v1/observability/dashboard
POST /api/v1/observability/alert

# GraphQL
mutation DeployObservability($platform: String!, $components: [String!]!) {
  deployObservability(platform: $platform, components: $components) {
    status
    endpoints {
      component
      url
    }
  }
}
```

## CLI usage
```bash
# Install
npm install -g @agentskills/observability-aggregator

# Deploy full stack
observability-aggregator deploy --platform=kubernetes --components=all

# Optimize for cost
observability-aggregator optimize --target=cost --retention=60d

# Create service dashboard
observability-aggregator dashboard --service=checkout --template=slo
```

## Configuration
```yaml
observabilityAggregator:
  platforms:
    kubernetes:
      namespace: observability
      storageClass: fast-ssd
      ingressClass: nginx
    aws:
      region: us-east-1
      vpc: vpc-12345
  components:
    prometheus:
      version: "2.45.0"
      retention: 90d
      replicas: 2
    grafana:
      version: "10.2.0"
      adminPassword: auto-generated
    loki:
      version: "2.8.0"
      retention: 30d
  alerting:
    slackWebhook: https://hooks.slack.com/...
    pagerDutyKey: xxx-xxx-xxx
    routes:
      - match:
          severity: critical
        receiver: pager-duty
  security:
    tlsEnabled: true
    authEnabled: true
    auditLogging: true
```

## Examples

### Full stack deployment
```bash
/observability-aggregator deploy --platform=kubernetes --components=all

# Deployment: Complete observability stack deployed
# Components: Prometheus, Grafana, Loki, Jaeger, AlertManager
# Services: 45 services auto-discovered and monitored
# Dashboards: 12 pre-built dashboards created
# Alerts: 23 SLO-based alert rules configured
# Endpoints: All services accessible via ingress
```

### Cost optimization
```bash
/observability-aggregator optimize --target=cost --retention=60d

# Analysis: Current monthly cost $2,450
# Recommendations: Reduce retention to 60 days, enable compression
# Implementation: Configuration updated, storage reduced by 35%
# New cost: $1,592/month (35% savings)
# Impact: Historical data access reduced, real-time monitoring maintained
```

### SLO monitoring setup
```bash
/observability-aggregator alert --slo=99.9 --service=checkout --burn-rate=14.4

# SLO: 99.9% availability target for checkout service
# Alerts: Multi-burn rate alerts configured (2%, 5%, 10%)
# Dashboard: SLO dashboard created with burn rate charts
# Integration: PagerDuty escalation configured
# Monitoring: Real-time SLO tracking active
```

## Migration guide

### From basic monitoring
1. Assess current monitoring gaps and requirements
2. Choose appropriate observability components
3. Deploy observability-aggregator with phased rollout
4. Migrate existing dashboards and alerts
5. Train teams on new observability capabilities

### From existing tools
- **CloudWatch**: observability-aggregator provides unified multi-cloud view
- **DataDog**: Enhanced with AI insights and cost optimization
- **Custom Prometheus**: Automated deployment and optimization
- **ELK Stack**: Integrated with metrics and tracing correlation

## Troubleshooting

### Common issues
- **Service discovery failures**: Check network policies and RBAC
- **High cardinality metrics**: Implement aggregation and sampling
- **Storage pressure**: Adjust retention and compression settings
- **Alert fatigue**: Tune alert thresholds and routing
- **Query timeouts**: Optimize query patterns and add caching

### Debug mode
```bash
observability-aggregator --debug deploy --platform=kubernetes --verbose
# Shows: deployment steps, configuration validation, health checks
```

## Future roadmap
- AI-powered observability recommendations
- Predictive scaling of observability infrastructure
- Integration with chaos engineering for resilience testing
- Advanced anomaly detection with unsupervised learning
- Real-time observability for edge computing
- Quantum-safe encryption for observability data

---

*Last updated: March 15, 2026*
*Version: 1.0.0*

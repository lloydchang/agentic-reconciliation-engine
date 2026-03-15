# Observability Aggregator Skill

## Name
observability-aggregator

## Purpose
Aggregate, correlate, and analyze observability data from multiple sources including metrics, logs, traces, and alerts for comprehensive system monitoring.

## When to Use
- When collecting metrics from multiple monitoring systems
- When correlating logs with performance metrics
- When analyzing distributed traces across services
- When aggregating alerts from different sources
- When creating unified dashboards and reports

## Inputs
- Data source configurations and endpoints
- Metric collection queries and filters
- Log aggregation patterns and filters
- Trace sampling and correlation rules
- Alert routing and aggregation rules

## Process
1. Connect to configured observability data sources
2. Collect and normalize metrics, logs, and traces
3. Correlate related data across sources and time
4. Apply aggregation and analysis algorithms
5. Generate unified views and insights
6. Create alerts and notifications based on patterns

## Outputs
- Aggregated metrics and performance data
- Correlated logs and trace analysis
- Unified dashboards and visualizations
- Alert aggregations and deduplication
- Performance reports and insights

## Environment
- Prometheus, Grafana, and monitoring stacks
- Log aggregation systems (ELK, Loki)
- Distributed tracing systems (Jaeger, Zipkin)
- Alert management systems (Alertmanager)

## Dependencies
- Monitoring system APIs and credentials
- Data aggregation and processing tools
- Visualization and dashboard systems
- Alert routing and notification systems

## Scripts
- scripts/aggregate_metrics.py: Python script for metrics aggregation
- scripts/correlate_logs.py: Log correlation and analysis script
- scripts/trace_analyzer.py: Distributed trace analysis script

## Trigger Keywords
observability, Prometheus, Grafana, alerting

## Human Gate Requirements
Prod alerting changes

## API Patterns

### JavaScript
```javascript
// Aggregate observability data
const observability = await aggregate_observability({
  dataSources: "prometheus|grafana|loki",
  timeRange: "1h",
  aggregationType: "metrics|logs|traces",
  priority: "normal"
});

// Get aggregation results
const results = await get_observability_results({
  workflowId: observability.workflowId
});
```

### Rust
```rust
// Rust-based observability aggregation
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct ObservabilityRequest {
    pub data_sources: Vec<DataSource>,
    pub time_range: String,
    pub aggregation_type: AggregationType,
    pub priority: Priority,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum DataSource {
    Prometheus,
    Grafana,
    Loki,
}

pub async fn aggregate_observability(request: ObservabilityRequest) -> Result<ObservabilityWorkflow, ObservabilityError> {
    // High-performance observability data aggregation
    let workflow = ObservabilityWorkflow::new(request).await?;
    
    // Aggregate and correlate data
    workflow.aggregate_comprehensive().await?;
    
    Ok(workflow)
}
```

## Parameter Schema
```json
{
  "dataSources": "array (required) - list of data sources to aggregate: prometheus|grafana|loki|jaeger",
  "timeRange": "string (required) - time range for data aggregation: 1h|6h|24h|7d",
  "aggregationType": "string (required) - type of aggregation: metrics|logs|traces|alerts|all",
  "queries": "array (optional) - specific queries to execute",
  "filters": "object (optional) - filtering criteria for data",
  "correlationRules": "array (optional) - rules for correlating different data types",
  "environment": "string (optional) - target environment: dev|staging|prod",
  "priority": "string (optional) - operation priority: low|normal|high|critical",
  "dashboard": "boolean (optional) - generate dashboard from results, defaults to false"
}
```

## Return Schema
```json
{
  "workflowId": "uuid",
  "status": "started|running|completed|failed",
  "startedAt": "ISO8601 timestamp",
  "result": {
    "aggregatedMetrics": "object - combined metrics from all sources",
    "correlatedLogs": "array - logs correlated with metrics and traces",
    "traceAnalysis": "object - distributed trace insights and bottlenecks",
    "alerts": "array - aggregated and deduplicated alerts",
    "dashboard": "object - generated dashboard configuration if requested",
    "insights": "array - key findings and recommendations",
    "performanceReport": "object - comprehensive performance analysis"
  },
  "errors": [],
  "metadata": {
    "dataSources": "array - sources that were successfully aggregated",
    "timeRange": "string - actual time range processed",
    "dataPoints": "number - total data points processed",
    "correlationScore": "number - quality of data correlation 0-1",
    "riskScore": "number - operation risk score 1-10"
  }
}
```

## Error Handling
```json
{
  "error": {
    "code": "VALIDATION_ERROR|SOURCE_UNAVAILABLE|AGGREGATION_FAILED|CORRELATION_ERROR",
    "message": "Human-readable description",
    "details": {
      "field": "parameter_name",
      "expected": "expected_format",
      "actual": "provided_value"
    }
  }
}
```

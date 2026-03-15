---
name: log-classifier
description: >
  AI-powered log analysis and classification for Kubernetes and application logs with anomaly detection, pattern recognition, and actionable insights.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Log Classifier — World-class Observability Intelligence

Classifies logs from Kubernetes, applications, and infrastructure with AI-powered anomaly detection, pattern recognition, and actionable insights for rapid incident response.

## When to invoke
- Incoming logs need classification for severity, source, and impact assessment.
- Anomaly detection across log streams reveals emerging issues.
- Pattern recognition identifies recurring issues or security threats.
- Post-mortem analysis requires log correlation and timeline reconstruction.
- Dispatcher/memory agents emit `log-anomaly`, `pattern-detected`, or `incident-ready` signals.

## Capabilities
- **Multi-source log ingestion**: Kubernetes audit, application logs, infrastructure telemetry, security events.
- **AI anomaly detection**: Machine learning models identify deviations from normal patterns.
- **Intelligent classification**: Severity scoring, root cause correlation, and impact assessment.
- **Pattern recognition**: Automated detection of known issues, security threats, and performance degradation.
- **Timeline reconstruction**: Correlate logs across sources for incident analysis.
- **Actionable insights**: Generate remediation recommendations and escalation paths.

## Invocation patterns
```bash
/log-classifier analyze --source=kubernetes --namespace=production --hours=24
/log-classifier anomaly --stream=app-logs --threshold=0.85 --auto-escalate=true
/log-classifier pattern --query="connection refused" --timeframe=1h
/log-classifier correlate --incident=INC-2026-0050 --sources=k8s,app,infra
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `source` | Log source (kubernetes, application, infrastructure). | `kubernetes` |
| `namespace` | Kubernetes namespace filter. | `production` |
| `hours` | Analysis timeframe in hours. | `24` |
| `threshold` | Anomaly detection sensitivity (0–1). | `0.85` |
| `query` | Pattern search query. | `"connection refused"` |
| `timeframe` | Pattern analysis window. | `1h` |

## Output contract
```json
{
  "operationId": "LC-2026-0315-01",
  "analysis": {
    "source": "kubernetes",
    "namespace": "production",
    "timeframe": "24h",
    "totalLogs": 15420,
    "anomaliesDetected": 3,
    "patternsFound": 2
  },
  "classifications": [
    {
      "logId": "k8s-audit-001",
      "severity": "HIGH",
      "category": "security",
      "pattern": "unauthorized-access",
      "confidence": 0.92,
      "recommendation": "Review RBAC permissions and rotate credentials"
    }
  ],
  "insights": [
    {
      "type": "anomaly",
      "description": "Spike in connection timeouts",
      "impact": "Degraded user experience",
      "action": "Scale application pods"
    }
  ],
  "decisionContext": "redis://memory-store/log-classifier/LC-2026-0315-01"
}
```

## World-class workflow templates

### AI log analysis & classification
1. Ingest logs from multiple sources (Kubernetes audit, application logs, infrastructure metrics).
2. Apply natural language processing and machine learning for anomaly detection.
3. Classify logs by severity, category, and potential impact using trained models.
4. Correlate related logs across time and sources for root cause analysis.
5. Generate insights with remediation recommendations and escalation paths.
6. Command stub: `/log-classifier analyze --source=kubernetes --namespace=production --hours=24`

### Anomaly detection & alerting
1. Monitor log streams in real-time for deviations from baseline patterns.
2. Score anomalies using statistical models and historical data.
3. Correlate anomalies with system metrics and business impact.
4. Generate alerts with contextual information for rapid response.
5. Emit `log-anomaly` events for dispatcher and incident response skills.
6. Command stub: `/log-classifier anomaly --stream=app-logs --threshold=0.85 --auto-escalate=true`

### Pattern recognition & correlation
1. Identify recurring patterns in log data using clustering algorithms.
2. Classify patterns as known issues, security threats, or performance problems.
3. Correlate patterns across multiple log sources for comprehensive analysis.
4. Generate reports with trend analysis and predictive insights.
5. Update knowledge base with new patterns for future detection.
6. Command stub: `/log-classifier pattern --query="connection refused" --timeframe=1h`

## AI intelligence highlights
- **Advanced anomaly detection**: Machine learning models trained on historical log data identify subtle deviations.
- **Intelligent pattern recognition**: Natural language processing extracts meaningful patterns from unstructured logs.
- **Contextual correlation**: Understands relationships between logs, metrics, and system events.
- **Predictive insights**: Anticipates issues based on log patterns and historical outcomes.
- **Automated classification**: Continuously learns from human feedback to improve accuracy.

## Memory agent & dispatcher integration
- Store classifications and insights under `shared-context://memory-store/log-classifier/{operationId}`.
- Emit events: `log-anomaly`, `pattern-detected`, `classification-complete`, `insight-ready`.
- Subscribe to dispatcher signals (`incident-ready`, `security-anomaly`, `performance-issue`) to provide log context.
- Tag telemetry with `operationId`, `severity`, `confidence`, `source`, `category`.

## Observability & telemetry
- Metrics: anomaly detection accuracy, pattern recognition rate, classification speed, false positive rate.
- Logs: structured `log.event="log.classification"` with `operationId`, `severity`, `confidence`.
- Dashboards: integrate `/log-classifier metrics --format=prometheus` for observability teams.
- Alerts: anomaly detection failure, high false positive rate, pattern recognition degradation.

## Failure handling & retries
- Retry log ingestion up to 3× when sources are temporarily unavailable.
- Fallback to cached logs when real-time ingestion fails.
- Provide partial results when complete analysis is not possible.
- Log failures for pattern analysis and system improvement.

## Human gates
- Required when:
  1. High-severity anomalies detected with critical impact.
  2. Security-related patterns identified requiring immediate response.
  3. Classification confidence below threshold for automated actions.
  4. Pattern recognition identifies potential zero-day threats.
- Confirmation template:

```
⚠️  HUMAN GATE: [log anomaly detected]
    Impact: [potential security breach or service degradation]
    Reversible: [Yes/No - depends on automated response]
    Type YES to proceed or NO to abort:
```

## Testing & validation
- Dry-run: `/log-classifier analyze --source=kubernetes --dry-run`.
- Unit tests: `backend/log-classifier/` validates anomaly detection and classification logic.
- Integration: `scripts/validate-log-classifier.sh` tests with sample log streams.
- Regression: nightly `scripts/nightly-log-smoke.sh` ensures detection accuracy and performance.

## Scripts
- scripts/log-classifier/analyze.py: Python script for log analysis and classification
- scripts/log-classifier/anomaly.py: Anomaly detection script
- scripts/log-classifier/pattern.py: Pattern recognition script

## Trigger Keywords
log classification, summary, context, severity

## Human Gate Requirements
Critical remediation actions

## API Patterns

### JavaScript
```javascript
// Analyze logs
const logAnalysis = await analyze_logs({
  source: "kubernetes|application|infrastructure",
  namespace: "production",
  hours: 24,
  priority: "high"
});

// Get analysis results
const results = await get_log_analysis_results({
  workflowId: logAnalysis.workflowId
});
```

### Rust
```rust
// Rust-based log classification
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct LogAnalysisRequest {
    pub source: LogSource,
    pub namespace: String,
    pub hours: u32,
    pub priority: Priority,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum LogSource {
    Kubernetes,
    Application,
    Infrastructure,
}

pub async fn analyze_logs(request: LogAnalysisRequest) -> Result<LogAnalysisWorkflow, LogAnalysisError> {
    // High-performance log analysis with AI
    let workflow = LogAnalysisWorkflow::new(request).await?;
    
    // Apply ML models for classification
    workflow.classify_with_ai().await?;
    
    Ok(workflow)
}
```

## Parameter Schema
```json
{
  "source": "string (required) - log source: kubernetes|application|infrastructure",
  "namespace": "string (optional) - namespace filter for kubernetes logs",
  "hours": "number (optional) - analysis timeframe in hours, defaults to 24",
  "query": "string (optional) - search query for pattern matching",
  "threshold": "number (optional) - anomaly detection threshold 0-1, defaults to 0.85",
  "environment": "string (optional) - target environment: dev|staging|prod",
  "priority": "string (optional) - operation priority: low|normal|high|critical",
  "autoEscalate": "boolean (optional) - automatically escalate high-severity findings, defaults to false"
}
```

## Return Schema
```json
{
  "workflowId": "uuid",
  "status": "started|running|completed|failed",
  "startedAt": "ISO8601 timestamp",
  "result": {
    "totalLogs": "number - total logs analyzed",
    "anomaliesDetected": "number - number of anomalies found",
    "patternsFound": "number - number of patterns identified",
    "classifications": "array - classified log entries with severity and recommendations",
    "insights": "array - actionable insights and remediation suggestions",
    "timeline": "object - reconstructed incident timeline"
  },
  "errors": [],
  "metadata": {
    "source": "string - log source analyzed",
    "namespace": "string - namespace filtered",
    "timeframe": "string - analysis timeframe",
    "confidence": "number - overall analysis confidence 0-1",
    "riskScore": "number - operation risk score 1-10"
  }
}
```

## Error Handling
```json
{
  "error": {
    "code": "VALIDATION_ERROR|SOURCE_UNAVAILABLE|TIMEOUT|ANALYSIS_FAILED",
    "message": "Human-readable description",
    "details": {
      "field": "parameter_name",
      "expected": "expected_format",
      "actual": "provided_value"
    }
  }
}
```

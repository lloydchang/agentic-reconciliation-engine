---
name: log-classifier
description: |
  Classify, summarize, and contextualize log entries with AI-powered severity assessment, pattern recognition, and remediation guidance.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Log Classifier — Intelligent Log Analysis and Contextualization

AI-powered log classification, severity assessment, and contextual analysis for infrastructure, application, and security logs across cloud platforms and Kubernetes environments.

## When to invoke
- Log volume spikes requiring triage and prioritization.
- Error pattern identification and root cause analysis.
- Security event correlation and threat assessment.
- Performance degradation analysis from logs.
- Compliance auditing and log review requirements.
- Incident response and forensic log analysis.

## Capabilities
- **Log classification**: Automatic categorization by type, severity, and impact.
- **Pattern recognition**: AI-driven anomaly detection and trend analysis.
- **Context enrichment**: Correlate logs with infrastructure and application state.
- **Severity assessment**: Intelligent risk scoring and escalation recommendations.
- **Remediation guidance**: Actionable insights and automated response suggestions.
- **Multi-source aggregation**: Unified analysis across cloud providers and on-prem systems.

## Invocation patterns
```bash
/log-classifier analyze --source=kubernetes --namespace=production --since=1h
/log-classifier classify --log-file=/var/log/app.log --pattern=error
/log-classifier correlate --incident=INC-2026-0315 --timeframe=24h
/log-classifier summarize --cluster=prod-cluster --severity=high
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `source` | Log source type (`kubernetes`, `cloudwatch`, `stackdriver`). | `kubernetes` |
| `namespace` | Kubernetes namespace filter. | `production` |
| `since` | Time range for log analysis. | `1h`, `24h`, `7d` |
| `pattern` | Log pattern or keyword to filter. | `error`, `timeout` |
| `severity` | Minimum severity level (`info`, `warning`, `error`, `critical`). | `warning` |
| `cluster` | Target cluster or environment. | `prod-cluster` |

## Output contract
```json
{
  "operationId": "LC-2026-0315-01",
  "analysis": {
    "totalLogs": 15420,
    "classifiedLogs": 15280,
    "anomalies": 45,
    "severityBreakdown": {
      "critical": 3,
      "error": 127,
      "warning": 892,
      "info": 14258
    }
  },
  "topPatterns": [
    {
      "pattern": "connection timeout",
      "count": 234,
      "severity": "error",
      "trend": "increasing",
      "remediation": "Check database connection pool limits",
      "confidence": 0.92
    }
  ],
  "recommendations": [
    {
      "action": "scale-database",
      "priority": "high",
      "impact": "Resolve 40% of timeout errors",
      "automated": true
    }
  ]
}
```

## Dispatcher integration
**Triggers:**
- `log-volume-spike`: Abnormal log volume requiring analysis
- `error-rate-increase`: Rising error rates in application logs
- `security-event`: Suspicious patterns in security logs
- `performance-alert`: Performance degradation indicated by logs

**Emits:**
- `log-analysis-complete`: Classified logs with severity assessment
- `anomaly-detected`: Identified anomalous patterns or trends
- `remediation-recommended`: Actionable remediation suggestions
- `incident-escalation`: High-severity issues requiring immediate attention

## AI intelligence features
- **Natural language processing**: Understand log messages and extract meaning
- **Pattern learning**: Adaptive pattern recognition from historical data
- **Context correlation**: Link logs with infrastructure and application metadata
- **Predictive analysis**: Forecast potential issues based on log patterns
- **Multi-dimensional clustering**: Group related logs across time and sources

## Human gates
- **Production incidents**: Critical severity issues require immediate SRE review
- **Security events**: Suspicious patterns need security team validation
- **Automated remediation**: High-impact changes require approval
- **Compliance reports**: Executive-level log summaries need review

## Telemetry and monitoring
- Classification accuracy metrics
- False positive/negative rates
- Response time for log analysis
- Pattern discovery effectiveness
- User satisfaction with classifications

## Testing requirements
- Log parsing accuracy tests across different formats
- Classification consistency validation
- Pattern recognition benchmarks
- Performance testing with high-volume log streams
- Integration testing with various log sources

## Failure handling
- **Log parsing failures**: Graceful degradation with raw log fallback
- **Source connectivity issues**: Retry with exponential backoff
- **High-volume scenarios**: Sampling and prioritization strategies
- **Classification timeouts**: Partial results with confidence scores
- **Storage limitations**: Archive old logs with configurable retention

## Related skills
- **incident-triage-runbook**: Log analysis integration for incident response
- **k8s-troubleshoot**: Kubernetes-specific log analysis and diagnostics
- **security-analysis**: Security event correlation and threat assessment
- **observability-stack**: Metrics and tracing correlation with logs

## Security considerations
- Log content sanitization before AI processing
- Access control based on data classification
- Audit trails for all log analysis operations
- Encryption of sensitive log data at rest and in transit
- Compliance with data retention and privacy regulations

## Performance characteristics
- Real-time analysis: <500ms per 1000 logs
- Batch processing: <30 seconds per 1M logs
- Pattern recognition: <2 seconds for complex queries
- Storage efficiency: 60% compression with searchable indexes
- Scalability: Linear scaling with log volume and compute resources

## Scaling considerations
- Distributed processing across multiple nodes
- Streaming analysis for real-time log processing
- Caching of common patterns and classifications
- Horizontal scaling for high-volume environments
- Data partitioning by time, source, and namespace

## Success metrics
- Classification accuracy: >95% for known patterns
- False positive rate: <2% for critical classifications
- Analysis coverage: >98% of log volume processed
- Response time: <5 seconds for interactive queries
- User adoption: >80% of log analysis requests automated

## API endpoints
```yaml
# REST API
POST /api/v1/logs/analyze
POST /api/v1/logs/classify
POST /api/v1/logs/correlate
POST /api/v1/logs/summarize

# GraphQL
query GetLogAnalysis($source: String!, $timeframe: String!) {
  logAnalysis(source: $source, timeframe: $timeframe) {
    patterns {
      pattern
      severity
      count
      trend
    }
  }
}
```

## CLI usage
```bash
# Install
npm install -g @agentskills/log-classifier

# Analyze recent logs
log-classifier analyze --source=kubernetes --namespace=production --since=1h

# Classify error patterns
log-classifier classify --log-file=/var/log/app.log --pattern=error

# Generate summary report
log-classifier summarize --cluster=prod-cluster --severity=high --output=report.md
```

## Configuration
```yaml
logClassifier:
  sources:
    kubernetes:
      apiserver: https://k8s-api.example.com
      namespaces: [production, staging]
      logRetention: 30d
    cloudwatch:
      region: us-east-1
      logGroups: [/aws/lambda/my-app, /aws/eks/prod-cluster]
  classification:
    patterns:
      - name: database-timeout
        regex: "timeout.*database"
        severity: error
        remediation: "check connection pool"
    aiModel: gpt-4-turbo
    confidenceThreshold: 0.8
  security:
    sanitizePII: true
    auditLogging: true
    retentionPeriod: 90d
```

## Examples

### Kubernetes error analysis
```bash
/log-classifier analyze --source=kubernetes --namespace=production --since=1h

# Analysis: 15,420 logs processed
# Critical: 3 database connection failures
# Error: 127 timeout errors (pattern: connection pool exhausted)
# Recommendation: Increase database connection pool from 20 to 50
# Automated: Scale deployment triggered
```

### Security event correlation
```bash
/log-classifier correlate --incident=SEC-2026-0315 --timeframe=24h

# Correlation: Failed login attempts from 3 IPs
# Pattern: Brute force attack detected
# Impact: Account lockout policy triggered
# Evidence: 250+ failed auth logs, geographic anomalies
# Response: IP blocks applied, security alert escalated
```

### Performance degradation analysis
```bash
/log-classifier analyze --source=cloudwatch --log-group=/aws/lambda/my-app --since=6h

# Trend: Memory usage increasing 15%/hour
# Pattern: Lambda cold starts rising
# Root cause: Memory allocation insufficient for workload
# Recommendation: Increase memory from 512MB to 1024MB
# Impact: Reduce cold start latency by 70%
```

## Migration guide

### From manual log analysis
1. Configure log sources and access permissions
2. Train AI models on historical log patterns
3. Establish classification rules and severity thresholds
4. Implement automated alerting and remediation
5. Monitor classification accuracy and adjust models

### From existing log tools
- **ELK Stack**: log-classifier provides AI layer over Elasticsearch
- **Splunk**: Enhanced with automated classification and remediation
- **CloudWatch Insights**: AI-powered analysis beyond query capabilities
- **Custom scripts**: Replace with standardized, monitored automation

## Troubleshooting

### Common issues
- **Log source connectivity**: Verify network access and authentication
- **Parsing failures**: Check log format and update parsers
- **High latency**: Optimize queries and consider data sampling
- **Memory issues**: Adjust batch sizes and processing limits
- **Classification drift**: Retrain models with current log patterns

### Debug mode
```bash
log-classifier --debug analyze --source=kubernetes --verbose
# Shows: parsing steps, classification reasoning, performance metrics
```

## Future roadmap
- Real-time streaming log analysis
- Advanced ML models for predictive failure detection
- Integration with SIEM systems for security correlation
- Automated incident response based on log patterns
- Multi-language log processing and translation
- Quantum-resistant encryption for sensitive logs

---

*Last updated: March 15, 2026*
*Version: 1.0.0*

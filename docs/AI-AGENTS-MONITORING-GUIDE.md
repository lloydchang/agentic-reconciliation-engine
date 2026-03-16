# AI Agents Monitoring Guide

## Overview

This guide covers comprehensive monitoring strategies for the Cloud AI Agents ecosystem, including metrics collection, alerting, log analysis, and performance optimization.

## Monitoring Architecture

### Components Overview
```yaml
Monitoring Stack:
  Metrics Collection:
    - Prometheus: Metrics aggregation and storage
    - Custom Exporters: Application-specific metrics
    - Node Exporter: System-level metrics
    - cAdvisor: Container resource usage
  
  Visualization:
    - Grafana: Dashboards and visualization
    - Custom Dashboard: Web-based monitoring UI
    - Alert Manager: Alert routing and notification
  
  Logging:
    - Fluentd/Fluent Bit: Log collection and forwarding
    - Elasticsearch: Log storage and indexing
    - Kibana: Log analysis and visualization
  
  Tracing:
    - Jaeger: Distributed tracing
    - OpenTelemetry: Instrumentation framework
    - Custom Spans: Application-specific tracing
```

### Data Flow
```
Applications → Exporters → Prometheus → Grafana/AlertManager
Applications → Logs → Fluentd → Elasticsearch → Kibana
Applications → Traces → Jaeger → UI/Storage
```

## Metrics Collection

### Core Metrics

#### System Metrics
```yaml
Infrastructure Metrics:
  - CPU usage (user, system, idle, wait)
  - Memory usage (used, available, cached, buffers)
  - Disk usage (space, I/O, latency)
  - Network traffic (bytes, packets, errors)
  - Load average and context switches

Kubernetes Metrics:
  - Pod status and restarts
  - Resource requests vs limits
  - PVC usage and status
  - Service endpoints and connectivity
  - HPA scaling events
```

#### Application Metrics
```yaml
AI Agent Metrics:
  - Agent execution count and duration
  - Skill execution success rate
  - Llama.cpp inference time
  - Memory database size and queries
  - API response times and error rates

Temporal Metrics:
  - Workflow execution count and status
  - Activity completion rates
  - Queue depth and processing time
  - Worker utilization and health
  - Decision task completion time

Business Metrics:
  - Cost optimization savings
  - Security issues detected
  - Compliance violations found
  - Infrastructure improvements
  - User satisfaction scores
```

### Custom Metrics Implementation

#### Go Metrics (Memory Agent)
```go
// monitoring/metrics.go
package monitoring

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    // Agent execution metrics
    agentExecutionsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "agent_executions_total",
            Help: "Total number of agent executions",
        },
        []string{"agent", "status"},
    )

    agentExecutionDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "agent_execution_duration_seconds",
            Help: "Agent execution duration in seconds",
            Buckets: prometheus.DefBuckets,
        },
        []string{"agent"},
    )

    // Skill metrics
    skillExecutionsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "skill_executions_total",
            Help: "Total number of skill executions",
        },
        []string{"skill", "status"},
    )

    // Llama.cpp metrics
    llamaCppInferenceDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "llamacpp_inference_duration_seconds",
            Help: "Llama.cpp inference duration in seconds",
            Buckets: []float64{0.1, 0.5, 1.0, 2.0, 5.0, 10.0},
        },
        []string{"model"},
    )

    // Database metrics
    databaseQueryDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "database_query_duration_seconds",
            Help: "Database query duration in seconds",
            Buckets: prometheus.DefBuckets,
        },
        []string{"operation"},
    )
)

func RecordAgentExecution(agent, status string, duration time.Duration) {
    agentExecutionsTotal.WithLabelValues(agent, status).Inc()
    agentExecutionDuration.WithLabelValues(agent).Observe(duration.Seconds())
}

func RecordSkillExecution(skill, status string) {
    skillExecutionsTotal.WithLabelValues(skill, status).Inc()
}

func RecordLlamaCppInference(model string, duration time.Duration) {
    llamaCppInferenceDuration.WithLabelValues(model).Observe(duration.Seconds())
}
```

#### Rust Metrics (Alternative Implementation)
```rust
// metrics.rs
use prometheus::{Counter, Histogram, register_counter, register_histogram};

lazy_static! {
    static ref AGENT_EXECUTIONS_TOTAL: Counter = register_counter!(
        "agent_executions_total", "Total number of agent executions"
    ).unwrap();

    static ref AGENT_EXECUTION_DURATION: Histogram = register_histogram!(
        "agent_execution_duration_seconds", "Agent execution duration in seconds"
    ).unwrap();

    static ref SKILL_EXECUTIONS_TOTAL: Counter = register_counter!(
        "skill_executions_total", "Total number of skill executions"
    ).unwrap();

    static ref LLAMACPP_INFERENCE_DURATION: Histogram = register_histogram!(
        "llamacpp_inference_duration_seconds", "Llama.cpp inference duration in seconds"
    ).unwrap();
}

pub fn record_agent_execution(agent: &str, status: &str, duration: Duration) {
    AGENT_EXECUTIONS_TOTAL.inc();
    AGENT_EXECUTION_DURATION.observe(duration.as_secs_f64());
}

pub fn record_skill_execution(skill: &str, status: &str) {
    SKILL_EXECUTIONS_TOTAL.inc();
}

pub fn record_llamacpp_inference(model: &str, duration: Duration) {
    LLAMACPP_INFERENCE_DURATION.observe(duration.as_secs_f64());
}
```

### Prometheus Configuration

#### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'kubernetes-apiservers'
    kubernetes_sd_configs:
    - role: endpoints
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
    - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
      action: keep
      regex: default;kubernetes;https

  - job_name: 'kubernetes-nodes'
    kubernetes_sd_configs:
    - role: node
    relabel_configs:
    - action: labelmap
      regex: __meta_kubernetes_node_label_(.+)

  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
    - role: pod
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
      action: keep
      regex: true
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
      action: replace
      target_label: __metrics_path__
      regex: (.+)
    - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
      action: replace
      regex: ([^:]+)(?::\d+)?;(\d+)
      replacement: $1:$2
      target_label: __address__
    - action: labelmap
      regex: __meta_kubernetes_pod_label_(.+)
    - source_labels: [__meta_kubernetes_namespace]
      action: replace
      target_label: kubernetes_namespace
    - source_labels: [__meta_kubernetes_pod_name]
      action: replace
      target_label: kubernetes_pod_name

  - job_name: 'ai-agents'
    kubernetes_sd_configs:
    - role: pod
      namespaces:
        names:
        - ai-infrastructure
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_component]
      action: keep
      regex: memory-agent|skills-orchestrator|agent-dashboard
    - source_labels: [__meta_kubernetes_pod_ip]
      target_label: __address__
      replacement: ${1}:8080
    - source_labels: [__meta_kubernetes_pod_label_component]
      target_label: component
    - source_labels: [__meta_kubernetes_pod_label_language]
      target_label: language

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

#### Alert Rules
```yaml
# alert_rules.yml
groups:
- name: ai-agents.rules
  rules:
  # Agent Health Alerts
  - alert: AgentDown
    expr: up{job="ai-agents"} == 0
    for: 2m
    labels:
      severity: critical
      component: agent
    annotations:
      summary: "AI Agent {{ $labels.component }} is down"
      description: "Agent {{ $labels.component }} has been down for more than 2 minutes"

  - alert: AgentHighErrorRate
    expr: rate(agent_executions_total{status="error"}[5m]) / rate(agent_executions_total[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
      component: agent
    annotations:
      summary: "High error rate for agent {{ $labels.component }}"
      description: "Error rate is {{ $value | humanizePercentage }} for agent {{ $labels.component }}"

  - alert: AgentSlowExecution
    expr: histogram_quantile(0.95, rate(agent_execution_duration_seconds_bucket[5m])) > 30
    for: 10m
    labels:
      severity: warning
      component: agent
    annotations:
      summary: "Slow agent execution"
      description: "95th percentile execution time is {{ $value }}s for agent {{ $labels.component }}"

  # Skill Execution Alerts
  - alert: SkillExecutionFailure
    expr: rate(skill_executions_total{status="error"}[5m]) > 0.05
    for: 3m
    labels:
      severity: warning
      component: skill
    annotations:
      summary: "Skill execution failures"
      description: "Skill {{ $labels.skill }} has {{ $value }} failures per second"

  # Llama.cpp Alerts
  - alert: LlamaCppSlowInference
    expr: histogram_quantile(0.95, rate(llamacpp_inference_duration_seconds_bucket[5m])) > 10
    for: 5m
    labels:
      severity: warning
      component: llamacpp
    annotations:
      summary: "Slow Llama.cpp inference"
      description: "95th percentile inference time is {{ $value }}s for model {{ $labels.model }}"

  # System Resource Alerts
  - alert: HighMemoryUsage
    expr: container_memory_usage_bytes{namespace="ai-infrastructure"} / container_spec_memory_limit_bytes > 0.9
    for: 5m
    labels:
      severity: warning
      component: system
    annotations:
      summary: "High memory usage"
      description: "Memory usage is {{ $value | humanizePercentage }} for {{ $labels.pod }}"

  - alert: HighCPUUsage
    expr: rate(container_cpu_usage_seconds_total{namespace="ai-infrastructure"}[5m]) / container_spec_cpu_quota * 100 > 80
    for: 5m
    labels:
      severity: warning
      component: system
    annotations:
      summary: "High CPU usage"
      description: "CPU usage is {{ $value }}% for {{ $labels.pod }}"

  # Database Alerts
  - alert: DatabaseConnectionFailure
    expr: up{job="database"} == 0
    for: 1m
    labels:
      severity: critical
      component: database
    annotations:
      summary: "Database connection failure"
      description: "Cannot connect to database"

  - alert: DatabaseSlowQueries
    expr: histogram_quantile(0.95, rate(database_query_duration_seconds_bucket[5m])) > 5
    for: 10m
    labels:
      severity: warning
      component: database
    annotations:
      summary: "Slow database queries"
      description: "95th percentile query time is {{ $value }}s"

  # Business Metrics Alerts
  - alert: CostOptimizationRegresssion
    expr: cost_savings_rate < 0.05
    for: 24h
    labels:
      severity: warning
      component: business
    annotations:
      summary: "Cost optimization regression"
      description: "Cost savings rate is {{ $value | humanizePercentage }}, below target of 5%"

  - alert: SecurityIssuesHigh
    expr: security_issues_detected > 10
    for: 1h
    labels:
      severity: warning
      component: security
    annotations:
      summary: "High number of security issues"
      description: "{{ $value }} security issues detected in the last hour"
```

## Dashboard Configuration

### Grafana Dashboards

#### Main AI Agents Dashboard
```json
{
  "dashboard": {
    "title": "AI Agents Overview",
    "tags": ["ai-agents"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Agent Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"ai-agents\"}",
            "legendFormat": "{{ component }}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              {"options": {"0": {"text": "DOWN", "color": "red"}}, "type": "value"},
              {"options": {"1": {"text": "UP", "color": "green"}}, "type": "value"}
            ]
          }
        }
      },
      {
        "title": "Agent Execution Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(agent_executions_total[5m])",
            "legendFormat": "{{ component }}"
          }
        ],
        "yAxes": [
          {"label": "Executions per second"}
        ]
      },
      {
        "title": "Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(agent_executions_total{status=\"success\"}[5m]) / rate(agent_executions_total[5m])",
            "legendFormat": "Success Rate"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "red", "value": 80},
                {"color": "yellow", "value": 90},
                {"color": "green", "value": 95}
              ]
            }
          }
        }
      },
      {
        "title": "Execution Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(agent_execution_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          },
          {
            "expr": "histogram_quantile(0.95, rate(agent_execution_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.99, rate(agent_execution_duration_seconds_bucket[5m]))",
            "legendFormat": "99th percentile"
          }
        ],
        "yAxes": [
          {"label": "Duration (seconds)"}
        ]
      },
      {
        "title": "Skill Execution Distribution",
        "type": "piechart",
        "targets": [
          {
            "expr": "topk(10, sum by (skill) (rate(skill_executions_total[5m])))",
            "legendFormat": "{{ skill }}"
          }
        ]
      },
      {
        "title": "Llama.cpp Inference Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(llamacpp_inference_duration_seconds_bucket[5m]))",
            "legendFormat": "{{ model }}"
          }
        ],
        "yAxes": [
          {"label": "Inference Time (seconds)"}
        ]
      },
      {
        "title": "Resource Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total{namespace=\"ai-infrastructure\"}[5m]) * 100",
            "legendFormat": "{{ pod }} - CPU"
          },
          {
            "expr": "container_memory_usage_bytes{namespace=\"ai-infrastructure\"} / 1024 / 1024",
            "legendFormat": "{{ pod }} - Memory"
          }
        ],
        "yAxes": [
          {"label": "CPU % / Memory MB"}
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "5s"
  }
}
```

#### Skills Performance Dashboard
```json
{
  "dashboard": {
    "title": "Skills Performance",
    "tags": ["ai-agents", "skills"],
    "panels": [
      {
        "title": "Skill Execution Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(skill_executions_total[5m])",
            "legendFormat": "{{ skill }}"
          }
        ]
      },
      {
        "title": "Skill Success Rate",
        "type": "table",
        "targets": [
          {
            "expr": "rate(skill_executions_total{status=\"success\"}[5m]) / rate(skill_executions_total[5m])",
            "legendFormat": "{{ skill }}",
            "format": "table"
          }
        ]
      },
      {
        "title": "Top Skills by Usage",
        "type": "table",
        "targets": [
          {
            "expr": "topk(20, sum by (skill) (increase(skill_executions_total[1h])))",
            "legendFormat": "{{ skill }}",
            "format": "table"
          }
        ]
      }
    ]
  }
}
```

### Custom Dashboard Integration

#### Dashboard API Extensions
```go
// api/metrics.go
package api

import (
    "net/http"
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

func SetupMetricsAPI() {
    // Expose Prometheus metrics
    http.Handle("/metrics", promhttp.Handler())
    
    // Custom metrics endpoints
    http.HandleFunc("/api/metrics/agents", getAgentMetrics)
    http.HandleFunc("/api/metrics/skills", getSkillMetrics)
    http.HandleFunc("/api/metrics/system", getSystemMetrics)
    http.HandleFunc("/api/metrics/alerts", getActiveAlerts)
}

func getAgentMetrics(w http.ResponseWriter, r *http.Request) {
    metrics := map[string]interface{}{
        "total_executions": getMetricValue("agent_executions_total"),
        "success_rate": getMetricValue("agent_success_rate"),
        "avg_duration": getMetricValue("agent_execution_duration_seconds_avg"),
        "active_agents": getMetricValue("up{job=\"ai-agents\"}"),
    }
    
    writeJSONResponse(w, metrics)
}

func getSkillMetrics(w http.ResponseWriter, r *http.Request) {
    metrics := map[string]interface{}{
        "total_executions": getMetricValue("skill_executions_total"),
        "success_rate": getMetricValue("skill_success_rate"),
        "popular_skills": getTopSkills(),
        "execution_by_category": getSkillExecutionByCategory(),
    }
    
    writeJSONResponse(w, metrics)
}

func getSystemMetrics(w http.ResponseWriter, r *http.Request) {
    metrics := map[string]interface{}{
        "cpu_usage": getMetricValue("container_cpu_usage_seconds_total"),
        "memory_usage": getMetricValue("container_memory_usage_bytes"),
        "disk_usage": getMetricValue("node_filesystem_size_bytes"),
        "network_traffic": getMetricValue("container_network_transmit_bytes_total"),
    }
    
    writeJSONResponse(w, metrics)
}

func getActiveAlerts(w http.ResponseWriter, r *http.Request) {
    alerts := []Alert{
        // Query Alertmanager for active alerts
    }
    
    writeJSONResponse(w, alerts)
}
```

## Log Management

### Structured Logging

#### Log Format Standard
```json
{
  "timestamp": "2024-03-15T10:30:00.123Z",
  "level": "info",
  "component": "memory-agent-rust",
  "agent_id": "agent-1",
  "execution_id": "exec-12345",
  "skill": "cost-analysis",
  "duration_ms": 1250,
  "success": true,
  "message": "Skill execution completed successfully",
  "metadata": {
    "cluster": "production",
    "namespace": "ai-infrastructure",
    "pod": "memory-agent-rust-abc123",
    "version": "v1.2.3",
    "request_id": "req-67890",
    "user_id": "user-111",
    "trace_id": "trace-222",
    "span_id": "span-333"
  },
  "tags": ["skill-execution", "cost-analysis", "success"]
}
```

#### Log Collection Configuration
```yaml
# fluentd-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: logging
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/*ai-infrastructure*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      format json
      time_format %Y-%m-%dT%H:%M:%S.%NZ
      time_key timestamp
      keep_time_key true
    </source>

    <filter kubernetes.**>
      @type kubernetes_metadata
    </filter>

    <filter kubernetes.**>
      @type record_transformer
      <record>
        environment #{ENV['ENVIRONMENT']}
        cluster #{ENV['CLUSTER_NAME']}
      </record>
    </filter>

    <match kubernetes.var.log.containers.**ai-infrastructure**>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      index_name ai-agents-logs
      type_name _doc
      include_tag_key true
      tag_key @log_name
      <buffer>
        @type file
        path /var/log/fluentd-buffers/kubernetes.system.buffer
        flush_mode interval
        retry_type exponential_backoff
        flush_thread_count 2
        flush_interval 5s
        retry_forever
        retry_max_interval 30
        chunk_limit_size 2M
        queue_limit_length 8
        overflow_action block
      </buffer>
    </match>
```

### Log Analysis

#### Elasticsearch Index Template
```json
{
  "index_patterns": ["ai-agents-logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1,
      "index.refresh_interval": "5s"
    },
    "mappings": {
      "properties": {
        "timestamp": {"type": "date"},
        "level": {"type": "keyword"},
        "component": {"type": "keyword"},
        "agent_id": {"type": "keyword"},
        "execution_id": {"type": "keyword"},
        "skill": {"type": "keyword"},
        "duration_ms": {"type": "long"},
        "success": {"type": "boolean"},
        "message": {"type": "text"},
        "metadata": {
          "properties": {
            "cluster": {"type": "keyword"},
            "namespace": {"type": "keyword"},
            "pod": {"type": "keyword"},
            "version": {"type": "keyword"},
            "request_id": {"type": "keyword"},
            "user_id": {"type": "keyword"},
            "trace_id": {"type": "keyword"},
            "span_id": {"type": "keyword"}
          }
        },
        "tags": {"type": "keyword"}
      }
    }
  }
}
```

#### Kibana Dashboards
```json
{
  "dashboard": {
    "title": "AI Agents Logs",
    "panels": [
      {
        "title": "Log Levels Over Time",
        "type": "histogram",
        "query": "component:memory-agent*",
        "timeField": "timestamp",
        "interval": "1h"
      },
      {
        "title": "Skill Execution Logs",
        "type": "table",
        "query": "skill:* AND success:true",
        "columns": ["timestamp", "skill", "duration_ms", "agent_id"]
      },
      {
        "title": "Error Analysis",
        "type": "table",
        "query": "level:error",
        "columns": ["timestamp", "component", "message", "metadata.pod"]
      }
    ]
  }
}
```

## Distributed Tracing

### OpenTelemetry Integration

#### Go Tracing Setup
```go
// tracing/tracing.go
package tracing

import (
    "context"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/jaeger"
    "go.opentelemetry.io/otel/sdk/resource"
    "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.4.0"
)

func InitTracing(serviceName string) (*trace.TracerProvider, error) {
    // Create Jaeger exporter
    exp, err := jaeger.New(jaeger.WithCollectorEndpoint(jaeger.WithEndpoint("http://jaeger:14268/api/traces")))
    if err != nil {
        return nil, err
    }

    // Create tracer provider
    tp := trace.NewTracerProvider(
        trace.WithBatcher(exp),
        trace.WithResource(resource.NewWithAttributes(
            semconv.SchemaURL,
            semconv.ServiceNameKey.String(serviceName),
            semconv.ServiceVersionKey.String("1.0.0"),
        )),
    )

    // Register as global tracer provider
    otel.SetTracerProvider(tp)

    return tp, nil
}

func CreateSpan(ctx context.Context, name string) (context.Context, trace.Span) {
    tracer := otel.Tracer("ai-agents")
    return tracer.Start(ctx, name)
}
```

#### Rust Tracing Setup
```rust
// tracing.rs
use opentelemetry::trace::{Tracer, Span};
use opentelemetry::global;
use opentelemetry_jaeger::{new_pipeline, Uninstall};

pub fn init_tracing(service_name: &str) -> Uninstall {
    new_pipeline()
        .with_service_name(service_name)
        .with_jaeger_endpoint("http://jaeger:14268/api/traces")
        .install_simple()
        .expect("Failed to install OpenTelemetry pipeline")
}

pub fn create_span(name: &str) -> Span {
    global::tracer("ai-agents").start(name)
}
```

### Trace Analysis

#### Jaeger Query Examples
```sql
-- Find slow skill executions
SELECT * FROM traces 
WHERE operation_name = 'skill_execution' 
AND duration > 5000000 
ORDER BY duration DESC 
LIMIT 10;

-- Trace agent workflow
SELECT * FROM traces 
WHERE trace_id IN (
    SELECT trace_id FROM traces 
    WHERE operation_name = 'agent_execution' 
    AND service.name = 'memory-agent-rust'
);

-- Error analysis
SELECT * FROM traces 
WHERE tags['error'] = 'true' 
ORDER BY start_time DESC 
LIMIT 50;
```

## Performance Optimization

### Metrics Optimization

#### High-Performance Metrics Collection
```go
// optimized_metrics.go
package monitoring

import (
    "sync"
    "time"
    "github.com/prometheus/client_golang/prometheus"
)

type OptimizedCollector struct {
    mu sync.RWMutex
    cache map[string]cachedMetric
    lastUpdate time.Time
    cacheTTL time.Duration
}

type cachedMetric struct {
    value    float64
    timestamp time.Time
}

func NewOptimizedCollector() *OptimizedCollector {
    return &OptimizedCollector{
        cache: make(map[string]cachedMetric),
        cacheTTL: 30 * time.Second,
    }
}

func (oc *OptimizedCollector) CollectMetric(name string, value float64) {
    oc.mu.Lock()
    defer oc.mu.Unlock()
    
    oc.cache[name] = cachedMetric{
        value: value,
        timestamp: time.Now(),
    }
}

func (oc *OptimizedCollector) GetMetric(name string) (float64, bool) {
    oc.mu.RLock()
    defer oc.mu.RUnlock()
    
    metric, exists := oc.cache[name]
    if !exists || time.Since(metric.timestamp) > oc.cacheTTL {
        return 0, false
    }
    
    return metric.value, true
}

func (oc *OptimizedCollector) Cleanup() {
    oc.mu.Lock()
    defer oc.mu.Unlock()
    
    now := time.Now()
    for name, metric := range oc.cache {
        if now.Sub(metric.timestamp) > oc.cacheTTL {
            delete(oc.cache, name)
        }
    }
}
```

#### Efficient Alert Evaluation
```yaml
# Optimized alert rules
groups:
- name: ai-agents-optimized
  interval: 30s
  rules:
  - alert: AgentHighErrorRate
    # Use recording rule for efficiency
    expr: agent_error_rate:rate5m > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High error rate for agent {{ $labels.component }}"

recording_rules:
- name: ai-agents-recording
  interval: 30s
  rules:
  - record: agent_error_rate:rate5m
    expr: rate(agent_executions_total{status="error"}[5m]) / rate(agent_executions_total[5m])
```

### Storage Optimization

#### Prometheus Storage Configuration
```yaml
# prometheus-storage-config.yaml
global:
  external_labels:
    cluster: 'ai-agents-cluster'
    replica: 'prometheus-1'

storage:
  tsdb:
    retention.time: 30d
    retention.size: 50GB
    wal.compression: true
    
  remote_write:
    - url: "http://thanos-receive:19291/api/v1/receive"
      queue_config:
        max_samples_per_send: 1000
        max_shards: 200
        capacity: 2500
```

#### Efficient Metrics Sampling
```go
// sampling_metrics.go
package monitoring

import (
    "math/rand"
    "time"
)

type SamplingCollector struct {
    sampleRate float64
    counter    int64
}

func NewSamplingCollector(sampleRate float64) *SamplingCollector {
    return &SamplingCollector{
        sampleRate: sampleRate,
    }
}

func (sc *SamplingCollector) ShouldSample() bool {
    sc.counter++
    if sc.counter%100 == 0 {
        return rand.Float64() < sc.sampleRate
    }
    return false
}

func (sc *SamplingCollector) RecordExecution(duration time.Duration) {
    if sc.ShouldSample() {
        // Record detailed metrics
        recordDetailedMetrics(duration)
    } else {
        // Record only aggregated metrics
        recordAggregatedMetrics(duration)
    }
}
```

## Conclusion

This monitoring guide provides a comprehensive framework for observing the AI Agents ecosystem. By implementing these monitoring strategies, operators can ensure system reliability, performance optimization, and proactive issue detection.

The monitoring stack is designed to be scalable, efficient, and provide deep insights into both technical and business metrics, enabling data-driven decision making and continuous improvement of the AI agents platform.

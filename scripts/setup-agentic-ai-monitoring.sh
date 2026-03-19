#!/bin/bash

# Agentic AI Monitoring Setup Script
# Configures comprehensive monitoring for agentic AI skills and compound engineering

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
MONITORING_NAMESPACE="monitoring"
AGENTIC_NAMESPACE="staging"
GRAFANA_ADMIN_PASSWORD="admin123"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot access Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create agentic AI ServiceMonitors
create_agentic_service_monitors() {
    log_info "Creating agentic AI ServiceMonitors..."
    
    cat > agentic-ai-service-monitors.yaml << EOF
# Agentic AI Skills ServiceMonitors
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: certificate-rotation-skill
  namespace: $AGENTIC_NAMESPACE
  labels:
    app.kubernetes.io/name: certificate-rotation-skill
    app.kubernetes.io/component: agentic-ai
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: certificate-rotation-skill
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: dependency-updates-skill
  namespace: $AGENTIC_NAMESPACE
  labels:
    app.kubernetes.io/name: dependency-updates-skill
    app.kubernetes.io/component: agentic-ai
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: dependency-updates-skill
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: resource-cleanup-skill
  namespace: $AGENTIC_NAMESPACE
  labels:
    app.kubernetes.io/name: resource-cleanup-skill
    app.kubernetes.io/component: agentic-ai
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: resource-cleanup-skill
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: security-patching-skill
  namespace: $AGENTIC_NAMESPACE
  labels:
    app.kubernetes.io/name: security-patching-skill
    app.kubernetes.io/component: agentic-ai
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: security-patching-skill
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: backup-verification-skill
  namespace: $AGENTIC_NAMESPACE
  labels:
    app.kubernetes.io/name: backup-verification-skill
    app.kubernetes.io/component: agentic-ai
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: backup-verification-skill
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: log-retention-skill
  namespace: $AGENTIC_NAMESPACE
  labels:
    app.kubernetes.io/name: log-retention-skill
    app.kubernetes.io/component: agentic-ai
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: log-retention-skill
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: performance-tuning-skill
  namespace: $AGENTIC_NAMESPACE
  labels:
    app.kubernetes.io/name: performance-tuning-skill
    app.kubernetes.io/component: agentic-ai
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: performance-tuning-skill
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
# Code Review Skills ServiceMonitors
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: pr-risk-assessment-skill
  namespace: $AGENTIC_NAMESPACE
  labels:
    app.kubernetes.io/name: pr-risk-assessment-skill
    app.kubernetes.io/component: code-review-automation
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: pr-risk-assessment-skill
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: automated-testing-skill
  namespace: $AGENTIC_NAMESPACE
  labels:
    app.kubernetes.io/name: automated-testing-skill
    app.kubernetes.io/component: code-review-automation
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: automated-testing-skill
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: compliance-validation-skill
  namespace: $AGENTIC_NAMESPACE
  labels:
    app.kubernetes.io/name: compliance-validation-skill
    app.kubernetes.io/component: code-review-automation
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: compliance-validation-skill
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: performance-impact-skill
  namespace: $AGENTIC_NAMESPACE
  labels:
    app.kubernetes.io/name: performance-impact-skill
    app.kubernetes.io/component: code-review-automation
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: performance-impact-skill
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: security-analysis-skill
  namespace: $AGENTIC_NAMESPACE
  labels:
    app.kubernetes.io/name: security-analysis-skill
    app.kubernetes.io/component: code-review-automation
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: security-analysis-skill
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
# Infrastructure Services ServiceMonitors
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: mcp-gateway
  namespace: $AGENTIC_NAMESPACE
  labels:
    app.kubernetes.io/name: mcp-gateway
    app.kubernetes.io/component: agentic-ai
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: mcp-gateway
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: parallel-workflow-executor
  namespace: $AGENTIC_NAMESPACE
  labels:
    app.kubernetes.io/name: parallel-workflow-executor
    app.kubernetes.io/component: agentic-ai
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: parallel-workflow-executor
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: cost-tracker
  namespace: $AGENTIC_NAMESPACE
  labels:
    app.kubernetes.io/name: cost-tracker
    app.kubernetes.io/component: agentic-ai
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: cost-tracker
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: pi-mono-rpc-enhanced
  namespace: $AGENTIC_NAMESPACE
  labels:
    app.kubernetes.io/name: pi-mono-rpc-enhanced
    app.kubernetes.io/component: agentic-ai
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: pi-mono-rpc-enhanced
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
EOF

    kubectl apply -f agentic-ai-service-monitors.yaml
    log_success "Agentic AI ServiceMonitors created"
}

# Create agentic AI alerting rules
create_agentic_alerting_rules() {
    log_info "Creating agentic AI alerting rules..."
    
    cat > agentic-ai-alerting-rules.yaml << EOF
# Agentic AI Skills Alerting Rules
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: agentic-ai-skills-alerts
  namespace: $MONITORING_NAMESPACE
  labels:
    app.kubernetes.io/name: agentic-ai-skills
    app.kubernetes.io/component: alerting
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  groups:
  - name: agentic-ai-skills
    rules:
    # Skill Availability Alerts
    - alert: AgenticSkillDown
      expr: up{job=~".*-skill"} == 0
      for: 2m
      labels:
        severity: critical
        component: agentic-ai-skills
      annotations:
        summary: "Agentic AI skill is down"
        description: "Agentic AI skill {{ $labels.job }} has been down for more than 2 minutes"
    
    - alert: AgenticSkillHighErrorRate
      expr: rate(http_requests_total{job=~".*-skill",status=~"5.."}[5m]) > 0.1
      for: 5m
      labels:
        severity: warning
        component: agentic-ai-skills
      annotations:
        summary: "Agentic AI skill high error rate"
        description: "Agentic AI skill {{ $labels.job }} error rate is {{ $value }} errors per second"
    
    - alert: AgenticSkillHighLatency
      expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job=~".*-skill"}[5m])) > 5
      for: 5m
      labels:
        severity: warning
        component: agentic-ai-skills
      annotations:
        summary: "Agentic AI skill high latency"
        description: "Agentic AI skill {{ $labels.job }} 95th percentile latency is {{ $value }}s"
    
    # Learning Effectiveness Alerts
    - alert: LearningSystemInactive
      expr: agentic_learning_operations_total == 0
      for: 1h
      labels:
        severity: warning
        component: learning-system
      annotations:
        summary: "Learning system inactive"
        description: "No learning operations detected in the last hour"
    
    - alert: LearningEffectivenessLow
      expr: agentic_learning_effectiveness_score < 0.5
      for: 30m
      labels:
        severity: warning
        component: learning-system
      annotations:
        summary: "Learning effectiveness low"
        description: "Learning effectiveness score is {{ $value }}, below threshold of 0.5"
    
    # Compound Engineering Alerts
    - alert: CompoundEngineeringStalled
      expr: time() - agentic_compound_cycle_last_completion_timestamp > 3600
      for: 30m
      labels:
        severity: warning
        component: compound-engineering
      annotations:
        summary: "Compound engineering cycle stalled"
        description: "No compound engineering cycles completed in over 1 hour"
    
    - alert: CompoundEngineeringHighFailureRate
      expr: rate(agentic_compound_cycle_failures_total[5m]) > 0.1
      for: 5m
      labels:
        severity: critical
        component: compound-engineering
      annotations:
        summary: "Compound engineering high failure rate"
        description: "Compound engineering failure rate is {{ $value }} failures per second"
    
    # MCP Gateway Alerts
    - alert: MCPGatewayDown
      expr: up{job="mcp-gateway"} == 0
      for: 2m
      labels:
        severity: critical
        component: mcp-gateway
      annotations:
        summary: "MCP Gateway is down"
        description: "MCP Gateway has been down for more than 2 minutes"
    
    - alert: MCPGatewayHighConnectionRate
      expr: rate(mcp_gateway_connections_total[5m]) > 100
      for: 5m
      labels:
        severity: warning
        component: mcp-gateway
      annotations:
        summary: "MCP Gateway high connection rate"
        description: "MCP Gateway connection rate is {{ $value }} connections per second"
    
    # Parallel Workflow Executor Alerts
    - alert: ParallelWorkflowExecutorDown
      expr: up{job="parallel-workflow-executor"} == 0
      for: 2m
      labels:
        severity: critical
        component: parallel-workflow-executor
      annotations:
        summary: "Parallel Workflow Executor is down"
        description: "Parallel Workflow Executor has been down for more than 2 minutes"
    
    - alert: ParallelWorkflowQueueBacklog
      expr: parallel_workflow_queue_size > 50
      for: 10m
      labels:
        severity: warning
        component: parallel-workflow-executor
      annotations:
        summary: "Parallel workflow queue backlog"
        description: "Parallel workflow queue has {{ $value }} pending items"
    
    # Cost Tracking Alerts
    - alert: CostTrackerDown
      expr: up{job="cost-tracker"} == 0
      for: 2m
      labels:
        severity: warning
        component: cost-tracker
      annotations:
        summary: "Cost Tracker is down"
        description: "Cost Tracker has been down for more than 2 minutes"
    
    - alert: CostAnomalyDetected
      expr: agentic_cost_anomaly_score > 0.8
      for: 15m
      labels:
        severity: warning
        component: cost-tracker
      annotations:
        summary: "Cost anomaly detected"
        description: "Cost anomaly score is {{ $value }}, indicating unusual spending patterns"
    
    # Pi-Mono RPC Alerts
    - alert: PiMonoRPCDown
      expr: up{job="pi-mono-rpc-enhanced"} == 0
      for: 2m
      labels:
        severity: critical
        component: pi-mono-rpc
      annotations:
        summary: "Pi-Mono RPC is down"
        description: "Pi-Mono RPC has been down for more than 2 minutes"
    
    - alert: PiMonoRPCHighRequestRate
      expr: rate(pi_mono_rpc_requests_total[5m]) > 1000
      for: 5m
      labels:
        severity: warning
        component: pi-mono-rpc
      annotations:
        summary: "Pi-Mono RPC high request rate"
        description: "Pi-Mono RPC request rate is {{ $value }} requests per second"
---
# Agentic AI Performance Alerting Rules
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: agentic-ai-performance-alerts
  namespace: $MONITORING_NAMESPACE
  labels:
    app.kubernetes.io/name: agentic-ai-performance
    app.kubernetes.io/component: alerting
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  groups:
  - name: agentic-ai-performance
    rules:
    # Resource Usage Alerts
    - alert: AgenticSkillHighCPUUsage
      expr: rate(container_cpu_usage_seconds_total{pod=~".*-skill-.*"}[5m]) * 100 > 80
      for: 10m
      labels:
        severity: warning
        component: agentic-ai-performance
      annotations:
        summary: "Agentic AI skill high CPU usage"
        description: "Agentic AI skill {{ $labels.pod }} is using {{ $value }}% CPU"
    
    - alert: AgenticSkillHighMemoryUsage
      expr: container_memory_working_set_bytes{pod=~".*-skill-.*"} / container_spec_memory_limit_bytes{pod=~".*-skill-.*"} * 100 > 80
      for: 10m
      labels:
        severity: warning
        component: agentic-ai-performance
      annotations:
        summary: "Agentic AI skill high memory usage"
        description: "Agentic AI skill {{ $labels.pod }} is using {{ $value }}% memory"
    
    # Autonomous Operation Alerts
    - alert: AutonomousOperationRateLow
      expr: rate(agentic_autonomous_operations_total[5m]) < 0.1
      for: 30m
      labels:
        severity: warning
        component: autonomous-operations
      annotations:
        summary: "Autonomous operation rate low"
        description: "Autonomous operation rate is {{ $value }} operations per second"
    
    - alert: HumanInterventionRequired
      expr: agentic_human_intervention_requests_total > 0
      for: 1m
      labels:
        severity: info
        component: autonomous-operations
      annotations:
        summary: "Human intervention required"
        description: "{{ $value }} human intervention requests pending"
EOF

    kubectl apply -f agentic-ai-alerting-rules.yaml
    log_success "Agentic AI alerting rules created"
}

# Create agentic AI Grafana dashboards
create_agentic_grafana_dashboards() {
    log_info "Creating agentic AI Grafana dashboards..."
    
    cat > agentic-ai-grafana-dashboards.yaml << EOF
# Agentic AI Skills Dashboard
apiVersion: v1
kind: ConfigMap
metadata:
  name: agentic-ai-skills-dashboard
  namespace: $MONITORING_NAMESPACE
  labels:
    grafana_dashboard: "1"
    app.kubernetes.io/name: agentic-ai-skills
    app.kubernetes.io/component: dashboards
    app.kubernetes.io/part-of: agentic-reconciliation-engine
data:
  agentic-ai-skills.json: |
    {
      "dashboard": {
        "id": null,
        "title": "Agentic AI Skills Overview",
        "tags": ["agentic-ai", "skills", "compound-engineering"],
        "timezone": "browser",
        "panels": [
          {
            "title": "Skills Status",
            "type": "stat",
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 0},
            "targets": [
              {
                "expr": "up{job=~\".*-skill\"}",
                "legendFormat": "{{job}}"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "color": {"mode": "thresholds"},
                "thresholds": {
                  "steps": [
                    {"color": "red", "value": 0},
                    {"color": "green", "value": 1}
                  ]
                },
                "mappings": [
                  {"options": {"0": {"text": "DOWN", "color": "red"}}, "type": "value"},
                  {"options": {"1": {"text": "UP", "color": "green"}}, "type": "value"}
                ]
              }
            }
          },
          {
            "title": "Skill Execution Rate",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
            "targets": [
              {
                "expr": "rate(agentic_skill_executions_total[5m])",
                "legendFormat": "{{skill}}"
              }
            ],
            "yAxes": [{"label": "Executions/sec"}]
          },
          {
            "title": "Skill Success Rate",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
            "targets": [
              {
                "expr": "rate(agentic_skill_successes_total[5m]) / rate(agentic_skill_executions_total[5m]) * 100",
                "legendFormat": "{{skill}}"
              }
            ],
            "yAxes": [{"label": "Success Rate (%)", "max": 100, "min": 0}]
          },
          {
            "title": "Learning Effectiveness",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
            "targets": [
              {
                "expr": "agentic_learning_effectiveness_score",
                "legendFormat": "{{learning_type}}"
              }
            ],
            "yAxes": [{"label": "Effectiveness Score", "max": 1, "min": 0}]
          },
          {
            "title": "Compound Engineering Cycles",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
            "targets": [
              {
                "expr": "rate(agentic_compound_cycles_total[5m])",
                "legendFormat": "Cycle Rate"
              },
              {
                "expr": "agentic_compound_cycle_duration_seconds",
                "legendFormat": "Duration"
              }
            ],
            "yAxes": [{"label": "Rate/Duration"}]
          },
          {
            "title": "Autonomous Operations",
            "type": "stat",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 24},
            "targets": [
              {
                "expr": "rate(agentic_autonomous_operations_total[5m])",
                "legendFormat": "Operations/sec"
              }
            ]
          },
          {
            "title": "Human Interventions",
            "type": "stat",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 24},
            "targets": [
              {
                "expr": "agentic_human_intervention_requests_total",
                "legendFormat": "Pending Interventions"
              }
            ]
          }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "30s"
      }
    }
---
# Compound Engineering Dashboard
apiVersion: v1
kind: ConfigMap
metadata:
  name: compound-engineering-dashboard
  namespace: $MONITORING_NAMESPACE
  labels:
    grafana_dashboard: "1"
    app.kubernetes.io/name: compound-engineering
    app.kubernetes.io/component: dashboards
    app.kubernetes.io/part-of: agentic-reconciliation-engine
data:
  compound-engineering.json: |
    {
      "dashboard": {
        "id": null,
        "title": "Compound Engineering Metrics",
        "tags": ["compound-engineering", "learning", "autonomous"],
        "timezone": "browser",
        "panels": [
          {
            "title": "Compound Engineering Loop Status",
            "type": "stat",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
            "targets": [
              {
                "expr": "agentic_compound_loop_status",
                "legendFormat": "{{loop_phase}}"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "color": {"mode": "palette-classic"},
                "mappings": [
                  {"options": {"0": {"text": "IDLE", "color": "blue"}}, "type": "value"},
                  {"options": {"1": {"text": "PLANNING", "color": "orange"}}, "type": "value"},
                  {"options": {"2": {"text": "WORKING", "color": "green"}}, "type": "value"},
                  {"options": {"3": {"text": "REVIEWING", "color": "purple"}}, "type": "value"},
                  {"options": {"4": {"text": "COMPOUNDING", "color": "red"}}, "type": "value"}
                ]
              }
            }
          },
          {
            "title": "Knowledge Compounding Rate",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
            "targets": [
              {
                "expr": "rate(agentic_knowledge_compounding_operations_total[5m])",
                "legendFormat": "Compounding Rate"
              }
            ],
            "yAxes": [{"label": "Operations/sec"}]
          },
          {
            "title": "Learning Velocity",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
            "targets": [
              {
                "expr": "agentic_learning_velocity_score",
                "legendFormat": "{{learning_domain}}"
              }
            ],
            "yAxes": [{"label": "Velocity Score"}]
          },
          {
            "title": "Pattern Recognition Accuracy",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
            "targets": [
              {
                "expr": "agentic_pattern_recognition_accuracy * 100",
                "legendFormat": "{{pattern_type}}"
              }
            ],
            "yAxes": [{"label": "Accuracy (%)", "max": 100, "min": 0}]
          },
          {
            "title": "Multi-Agent Coordination",
            "type": "table",
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 16},
            "targets": [
              {
                "expr": "agentic_multi_agent_coordination_metrics",
                "legendFormat": "{{agent_type}}-{{coordination_type}}"
              }
            ],
            "transformations": [
              {"id": "organize", "options": {"excludeByName": {"Time": true}}}
            ]
          },
          {
            "title": "Exponential Improvement Index",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 24},
            "targets": [
              {
                "expr": "agentic_exponential_improvement_index",
                "legendFormat": "Improvement Index"
              }
            ],
            "yAxes": [{"label": "Index"}]
          },
          {
            "title": "Knowledge Base Growth",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 24},
            "targets": [
              {
                "expr": "agentic_knowledge_base_size",
                "legendFormat": "{{knowledge_type}}"
              }
            ],
            "yAxes": [{"label": "Knowledge Items"}]
          }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "30s"
      }
    }
---
# MCP Gateway Dashboard
apiVersion: v1
kind: ConfigMap
metadata:
  name: mcp-gateway-dashboard
  namespace: $MONITORING_NAMESPACE
  labels:
    grafana_dashboard: "1"
    app.kubernetes.io/name: mcp-gateway
    app.kubernetes.io/component: dashboards
    app.kubernetes.io/part-of: agentic-reconciliation-engine
data:
  mcp-gateway.json: |
    {
      "dashboard": {
        "id": null,
        "title": "MCP Gateway Metrics",
        "tags": ["mcp-gateway", "model-context-protocol"],
        "timezone": "browser",
        "panels": [
          {
            "title": "Gateway Status",
            "type": "stat",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
            "targets": [
              {
                "expr": "up{job=\"mcp-gateway\"}",
                "legendFormat": "Gateway"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "color": {"mode": "thresholds"},
                "thresholds": {
                  "steps": [
                    {"color": "red", "value": 0},
                    {"color": "green", "value": 1}
                  ]
                }
              }
            }
          },
          {
            "title": "Connection Rate",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
            "targets": [
              {
                "expr": "rate(mcp_gateway_connections_total[5m])",
                "legendFormat": "Connections/sec"
              }
            ],
            "yAxes": [{"label": "Connections/sec"}]
          },
          {
            "title": "Tool Execution Rate",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
            "targets": [
              {
                "expr": "rate(mcp_gateway_tool_executions_total[5m])",
                "legendFormat": "{{tool_name}}"
              }
            ],
            "yAxes": [{"label": "Executions/sec"}]
          },
          {
            "title": "Request Latency",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
            "targets": [
              {
                "expr": "histogram_quantile(0.95, rate(mcp_gateway_request_duration_seconds_bucket[5m]))",
                "legendFormat": "95th percentile"
              },
              {
                "expr": "histogram_quantile(0.50, rate(mcp_gateway_request_duration_seconds_bucket[5m]))",
                "legendFormat": "50th percentile"
              }
            ],
            "yAxes": [{"label": "Duration (seconds)"}]
          },
          {
            "title": "Active Tools",
            "type": "table",
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 16},
            "targets": [
              {
                "expr": "mcp_gateway_active_tools",
                "legendFormat": "{{tool_name}}"
              }
            ],
            "transformations": [
              {"id": "organize", "options": {"excludeByName": {"Time": true}}}
            ]
          }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "30s"
      }
    }
EOF

    kubectl apply -f agentic-ai-grafana-dashboards.yaml
    log_success "Agentic AI Grafana dashboards created"
}

# Validate monitoring setup
validate_monitoring_setup() {
    log_info "Validating monitoring setup..."
    
    # Check ServiceMonitors
    local service_monitors=(
        "certificate-rotation-skill"
        "dependency-updates-skill"
        "mcp-gateway"
        "parallel-workflow-executor"
        "cost-tracker"
        "pi-mono-rpc-enhanced"
    )
    
    for sm in "${service_monitors[@]}"; do
        if kubectl get servicemonitor $sm -n $AGENTIC_NAMESPACE &> /dev/null; then
            log_success "ServiceMonitor $sm found"
        else
            log_warning "ServiceMonitor $sm not found"
        fi
    done
    
    # Check PrometheusRules
    local prometheus_rules=(
        "agentic-ai-skills-alerts"
        "agentic-ai-performance-alerts"
    )
    
    for rule in "${prometheus_rules[@]}"; do
        if kubectl get prometheusrule $rule -n $MONITORING_NAMESPACE &> /dev/null; then
            log_success "PrometheusRule $rule found"
        else
            log_warning "PrometheusRule $rule not found"
        fi
    done
    
    # Check Grafana dashboards
    local dashboards=(
        "agentic-ai-skills-dashboard"
        "compound-engineering-dashboard"
        "mcp-gateway-dashboard"
    )
    
    for dashboard in "${dashboards[@]}"; do
        if kubectl get configmap $dashboard -n $MONITORING_NAMESPACE &> /dev/null; then
            log_success "Grafana dashboard $dashboard found"
        else
            log_warning "Grafana dashboard $dashboard not found"
        fi
    done
    
    log_success "Monitoring setup validation completed"
}

# Show access information
show_access_info() {
    log_info "Access Information:"
    echo
    echo "Grafana Dashboard:"
    echo "URL: http://grafana.local (or port-forward: kubectl port-forward svc/grafana -n $MONITORING_NAMESPACE 3000:80)"
    echo "Username: admin"
    echo "Password: $GRAFANA_ADMIN_PASSWORD"
    echo
    echo "Available Dashboards:"
    echo "- Agentic AI Skills Overview"
    echo "- Compound Engineering Metrics"
    echo "- MCP Gateway Metrics"
    echo
    echo "Prometheus:"
    echo "URL: http://prometheus.local (or port-forward: kubectl port-forward svc/prometheus -n $MONITORING_NAMESPACE 9090:9090)"
    echo
    echo "AlertManager:"
    echo "URL: http://alertmanager.local (or port-forward: kubectl port-forward svc/alertmanager -n $MONITORING_NAMESPACE 9093:9093)"
    echo
    log_info "To check monitoring status:"
    echo "kubectl get pods -n $MONITORING_NAMESPACE"
    echo "kubectl get servicemonitors -n $AGENTIC_NAMESPACE"
    echo "kubectl get prometheusrules -n $MONITORING_NAMESPACE"
}

# Main execution
main() {
    log_info "Starting Agentic AI Monitoring Setup..."
    
    check_prerequisites
    create_agentic_service_monitors
    create_agentic_alerting_rules
    create_agentic_grafana_dashboards
    validate_monitoring_setup
    show_access_info
    
    log_success "Agentic AI monitoring setup completed successfully!"
    log_info "Next steps:"
    echo "1. Access Grafana dashboards to monitor agentic AI skills"
    echo "2. Configure alert notifications in AlertManager"
    echo "3. Set up additional monitoring for specific skill metrics"
    echo "4. Monitor learning effectiveness and compound engineering cycles"
}

# Run main function
main "$@"

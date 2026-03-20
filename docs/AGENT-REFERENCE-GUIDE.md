# AI Agents Reference Guide

## Overview

This comprehensive reference guide provides detailed documentation for all components, APIs, configuration options, and operational procedures in the Cloud AI Agents ecosystem.

## Table of Contents

1. [Component Reference](#component-reference)
2. [API Reference](#api-reference)
3. [Configuration Reference](#configuration-reference)
4. [Deployment Reference](#deployment-reference)
5. [Monitoring Reference](#monitoring-reference)
6. [Troubleshooting Reference](#troubleshooting-reference)
7. [Security Reference](#security-reference)
8. [Performance Reference](#performance-reference)

## Component Reference

### 🤖 Memory Agents

#### Rust Memory Agent
```yaml
# Deployment manifest
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-memory-rust
  namespace: ai-infrastructure
spec:
  replicas: 1
  selector:
    matchLabels:
      component: agent-memory
      language: rust
  template:
    spec:
      containers:
      - name: agent-memory
        image: agent-memory-rust:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_PATH
          value: "/data/memory.db"
        - name: MODEL_PATH
          value: "/models/qwen2.5-0.5b.gguf"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

**Key Features:**
- High-performance Rust implementation
- SQLite database for persistent memory
- Llama.cpp integration for local inference
- Axum web framework for HTTP API
- Async/await for concurrent operations

**Environment Variables:**
```bash
DATABASE_PATH=/data/memory.db              # SQLite database path
INBOX_PATH=/data/inbox                     # Input directory
MODEL_PATH=/models/qwen2.5-0.5b.gguf       # Llama.cpp model path
OLLAMA_URL=http://localhost:11434          # Ollama service URL
BACKEND_PRIORITY=llama-cpp,ollama          # Backend priority
LANGUAGE_PRIORITY=rust,go,python           # Language priority
MAX_TOKENS=2048                            # Maximum tokens for generation
TEMPERATURE=0.7                            # Generation temperature
```

#### Go Memory Agent
```yaml
# Deployment manifest
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-memory-go
  namespace: ai-infrastructure
spec:
  replicas: 1
  selector:
    matchLabels:
      component: agent-memory
      language: go
  template:
    spec:
      containers:
      - name: agent-memory
        image: agent-memory-go:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_PATH
          value: "/data/memory.db"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

**Key Features:**
- Go implementation with Gin framework
- SQLite database for persistent memory
- Excellent concurrency support
- Simple deployment model
- Rich Go ecosystem integration

#### Python Memory Agent
```yaml
# Deployment manifest
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-memory-python
  namespace: ai-infrastructure
spec:
  replicas: 1
  selector:
    matchLabels:
      component: agent-memory
      language: python
  template:
    spec:
      containers:
      - name: agent-memory
        image: agent-memory-python:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_PATH
          value: "/data/memory.db"
        resources:
          requests:
            memory: "512Mi"
            cpu: "200m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

**Key Features:**
- Python implementation with FastAPI
- Rich ML ecosystem integration
- Transformers and PyTorch support
- Rapid prototyping capabilities
- Extensive library support

### 🔄 Temporal Orchestration

#### Temporal Server Configuration
```yaml
# Helm values for Temporal
server:
  replicaCount: 1
  history:
    replicaCount: 1
  matching:
    replicaCount: 1
  worker:
    replicaCount: 1

frontend:
  service:
    type: ClusterIP
    port: 7233

cassandra:
  enabled: true
  persistence:
    enabled: false
  config:
    cluster_size: 1

elasticsearch:
  enabled: false
```

#### Workflow Types
```go
// Workflow definitions
type ComplianceWorkflow struct {
    Request types.ComplianceRequest
}

type CostOptimizationWorkflow struct {
    ClusterID string
    TimeRange time.Time
}

type SecurityAuditWorkflow struct {
    Scope     string
    Resources []string
}
```

#### Activity Types
```go
// Activity definitions
func ExecuteComplianceCheck(ctx context.Context, request types.ComplianceRequest) (*types.ComplianceResult, error)
func AnalyzeCosts(ctx context.Context, clusterID string) (*types.CostAnalysis, error)
func PerformSecurityAudit(ctx context.Context, scope string) (*types.SecurityReport, error)
```

### 📊 Monitoring System

#### Metrics Collector Configuration
```go
// Metrics collector configuration
type MetricsCollector struct {
    metrics     map[string]*Metric
    alerts      []*Alert
    mu          sync.RWMutex
    alertChan   chan *Alert
    stopChan    chan struct{}
    collectors  []MetricCollector
}

// Metric types
type MetricType string
const (
    Counter   MetricType = "counter"
    Gauge     MetricType = "gauge"
    Histogram MetricType = "histogram"
    Summary   MetricType = "summary"
)
```

#### Alert Configuration
```go
// Alert thresholds
thresholds := map[string]ThresholdConfig{
    "workflow_timeout": {
        metric:    "workflow_duration_max",
        threshold: 7200, // 2 hours
        severity:  Warning,
        message:   "Workflow execution exceeding timeout threshold",
    },
    "agent_failure_rate": {
        metric:    "agent_error_rate_avg",
        threshold: 0.1, // 10%
        severity:  Critical,
        message:   "Agent failure rate above acceptable threshold",
    },
}
```

### 🎛️ Dashboard Components

#### Frontend Architecture
```javascript
// Dashboard configuration
const dashboardConfig = {
    refreshInterval: 30000, // 30 seconds
    chartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            }
        }
    },
    apiEndpoints: {
        agents: '/api/agents',
        skills: '/api/skills',
        activity: '/api/activity',
        metrics: '/api/metrics'
    }
};
```

#### Backend API Service
```python
# Flask API configuration
app = Flask(__name__)

@app.route('/api/cluster-status')
def cluster_status():
    return jsonify({
        "status": "healthy",
        "message": "Cluster is operational",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/core/ai/runtime/status')
def agents_status():
    return jsonify({
        "agent_count": 3,
        "skills_executed": 42,
        "active_agents": ["cost-optimizer", "security-scanner", "cluster-monitor"]
    })
```

## API Reference

### 📡 Memory Agent API

#### Chat Completion
```http
POST /api/chat
Content-Type: application/json

{
    "message": "Hello, how can you help me?",
    "conversation_id": "optional-conversation-id",
    "context": "optional-additional-context",
    "max_tokens": 2048,
    "temperature": 0.7
}

Response:
{
    "response": "I can help you with various cloud operations...",
    "conversation_id": "conv-12345",
    "message_id": "msg-67890",
    "timestamp": "2026-03-16T12:00:00Z",
    "metadata": {
        "model": "qwen2.5:0.5b",
        "tokens_used": 150,
        "response_time": 1.2
    }
}
```

#### Conversation Management
```http
GET /api/conversations/{conversation_id}

Response:
{
    "id": "conv-12345",
    "title": "Cloud Cost Analysis",
    "created_at": "2026-03-16T10:00:00Z",
    "updated_at": "2026-03-16T12:00:00Z",
    "messages": [
        {
            "id": "msg-67890",
            "role": "user",
            "content": "Analyze our cloud costs",
            "timestamp": "2026-03-16T12:00:00Z"
        },
        {
            "id": "msg-67891",
            "role": "assistant",
            "content": "I'll analyze your cloud costs...",
            "timestamp": "2026-03-16T12:00:01Z"
        }
    ],
    "metadata": {
        "total_messages": 10,
        "total_tokens": 1500
    }
}
```

#### Knowledge Base Operations
```http
POST /api/knowledge
Content-Type: application/json

{
    "title": "Important Information",
    "content": "Content to remember",
    "tags": ["important", "reference"],
    "metadata": {
        "source": "user-input",
        "priority": "high"
    }
}

Response:
{
    "id": "knowledge-12345",
    "created_at": "2026-03-16T12:00:00Z",
    "status": "stored"
}
```

#### Search Operations
```http
GET /api/search?q=cloud%20costs&limit=5&type=knowledge

Response:
{
    "results": [
        {
            "id": "knowledge-12345",
            "title": "Cloud Cost Analysis",
            "content": "Analysis of cloud spending patterns...",
            "score": 0.95,
            "type": "knowledge",
            "timestamp": "2026-03-16T12:00:00Z"
        }
    ],
    "total": 1,
    "query": "cloud costs"
}
```

### 🔄 Temporal API

#### Workflow Management
```http
POST /api/workflows
Content-Type: application/json

{
    "workflow_type": "compliance_check",
    "input": {
        "cluster_id": "prod-cluster",
        "compliance_type": "security"
    }
}

Response:
{
    "workflow_id": "workflow-12345",
    "run_id": "run-67890",
    "status": "running",
    "started_at": "2026-03-16T12:00:00Z"
}
```

#### Workflow Status
```http
GET /api/workflows/{workflow_id}

Response:
{
    "workflow_id": "workflow-12345",
    "run_id": "run-67890",
    "status": "completed",
    "started_at": "2026-03-16T12:00:00Z",
    "completed_at": "2026-03-16T12:05:00Z",
    "result": {
        "compliant": true,
        "score": 95.0,
        "violations": []
    }
}
```

### 📊 Monitoring API

#### Metrics Retrieval
```http
GET /api/monitoring/metrics

Response:
{
    "metrics": {
        "workflow_total": {
            "value": 150,
            "type": "gauge",
            "timestamp": "2026-03-16T12:00:00Z",
            "tags": {"type": "all"}
        },
        "agent_executions_total": {
            "value": 1250,
            "type": "counter",
            "timestamp": "2026-03-16T12:00:00Z",
            "tags": {"agent": "cost-optimizer"}
        },
        "system_uptime": {
            "value": 86400,
            "type": "counter",
            "timestamp": "2026-03-16T12:00:00Z",
            "tags": {"unit": "seconds"}
        }
    },
    "timestamp": "2026-03-16T12:00:00Z"
}
```

#### Alerts Management
```http
GET /api/monitoring/alerts

Response:
{
    "alerts": [
        {
            "id": "agent-failure-rate-1678992000",
            "name": "agent_failure_rate",
            "severity": "critical",
            "message": "Agent failure rate above acceptable threshold",
            "metric": "agent_error_rate_avg",
            "threshold": 0.1,
            "value": 0.15,
            "timestamp": "2026-03-16T11:30:00Z",
            "labels": {"agent": "cost-optimizer"},
            "acked": false
        }
    ]
}
```

#### Alert Acknowledgment
```http
POST /api/monitoring/alerts/{alertId}/acknowledge

Response:
{
    "status": "acknowledged",
    "acked_at": "2026-03-16T12:00:00Z",
    "alert_id": "agent-failure-rate-1678992000"
}
```

### 🎛️ Dashboard API

#### Cluster Status
```http
GET /api/cluster-status

Response:
{
    "status": "healthy",
    "message": "Cluster is operational",
    "components": {
        "memory_agents": "running",
        "temporal": "running",
        "dashboard": "running",
        "monitoring": "running"
    },
    "timestamp": "2026-03-16T12:00:00Z"
}
```

#### Agent Status
```http
GET /api/core/ai/runtime/status

Response:
{
    "agent_count": 3,
    "skills_executed": 42,
    "active_agents": [
        {
            "name": "cost-optimizer",
            "status": "running",
            "last_activity": "2026-03-16T11:55:00Z"
        },
        {
            "name": "security-scanner",
            "status": "running",
            "last_activity": "2026-03-16T11:50:00Z"
        },
        {
            "name": "cluster-monitor",
            "status": "idle",
            "last_activity": "2026-03-16T11:45:00Z"
        }
    ]
}
```

## Configuration Reference

### ⚙️ Environment Variables

#### Global Configuration
```bash
# Namespace configuration
NAMESPACE=ai-infrastructure

# Cluster configuration
KUBECONFIG=/path/to/kubeconfig
CLUSTER_CONTEXT=kind-gitops-hub

# Logging configuration
LOG_LEVEL=info
LOG_FORMAT=json
LOG_OUTPUT=stdout

# Security configuration
ENABLE_AUTH=false
TLS_CERT_PATH=/etc/tls/cert.pem
TLS_KEY_PATH=/etc/tls/key.pem
```

#### Memory Agent Configuration
```bash
# Database configuration
DATABASE_PATH=/data/memory.db
DATABASE_BACKUP_PATH=/data/backups
DATABASE_RETENTION_DAYS=30

# Model configuration
MODEL_PATH=/models/qwen2.5-0.5b.gguf
MODEL_CACHE_SIZE=1GB
MAX_TOKENS=2048
TEMPERATURE=0.7
TOP_P=0.9

# Backend configuration
BACKEND_PRIORITY=llama-cpp,ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:0.5b

# Performance configuration
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30s
CONNECTION_TIMEOUT=5s
```

#### Temporal Configuration
```bash
# Server configuration
TEMPORAL_ADDRESS=temporal-frontend:7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_TIMEOUT=10m

# History configuration
HISTORY_SERVICE_ADDRESS=temporal-history:7934
HISTORY_PERSISTENCE_MODE=cassandra

# Worker configuration
WORKER_CONCURRENCY=10
WORKER_POLL_TIMEOUT=1m
WORKER_MAX_CONCURRENT_ACTIVITY_EXECUTIONS=100
```

#### Monitoring Configuration
```bash
# Metrics configuration
METRICS_PORT=8080
METRICS_PATH=/metrics
METRICS_COLLECTION_INTERVAL=30s
METRICS_RETENTION_PERIOD=7d

# Alerting configuration
ALERT_DEDUPICATION_WINDOW=5m
ALERT_NOTIFICATION_CHANNELS=webhook,email
ALERT_WEBHOOK_URL=http://alertmanager:9093/api/v1/alerts

# Prometheus configuration
PROMETHEUS_GATEWAY_URL=http://prometheus-pushgateway:9091
PROMETHEUS_JOB_NAME=ai-agents
```

### 🔧 Configuration Files

#### Memory Agent Config
```yaml
# config.yaml
agent:
  name: "agent-memory-rust"
  version: "1.0.0"
  
database:
  path: "/data/memory.db"
  backup_path: "/data/backups"
  retention_days: 30
  connection_pool_size: 10
  
model:
  path: "/models/qwen2.5-0.5b.gguf"
  max_tokens: 2048
  temperature: 0.7
  top_p: 0.9
  cache_size: "1GB"
  
backend:
  priority: ["llama-cpp", "ollama"]
  ollama:
    url: "http://localhost:11434"
    model: "qwen2.5:0.5b"
  llama_cpp:
    context_size: 2048
    gpu_layers: 0
    batch_size: 512
    
performance:
  max_concurrent_requests: 10
  request_timeout: "30s"
  connection_timeout: "5s"
  keep_alive: true
```

#### Temporal Config
```yaml
# temporal.yaml
server:
  frontend:
    port: 7233
    history:
      address: "temporal-history:7934"
    matching:
      address: "temporal-matching:7935"
    worker:
      address: "temporal-worker:7939"
      
persistence:
  default:
    driver: "cassandra"
    cassandra:
      hosts: ["cassandra"]
      keyspace: "temporal"
      replication_factor: 1
      
workflow:
  execution_timeout: "24h"
  task_timeout: "10m"
  retry_policy:
    maximum_attempts: 3
    initial_interval: "1s"
    maximum_interval: "1m"
```

#### Monitoring Config
```yaml
# monitoring.yaml
metrics:
  collection_interval: "30s"
  retention_period: "7d"
  export_format: "prometheus"
  
alerts:
  deduplication_window: "5m"
  thresholds:
    workflow_timeout:
      metric: "workflow_duration_max"
      threshold: 7200
      severity: "warning"
      message: "Workflow execution exceeding timeout threshold"
    agent_failure_rate:
      metric: "agent_error_rate_avg"
      threshold: 0.1
      severity: "critical"
      message: "Agent failure rate above acceptable threshold"
      
notifications:
  channels: ["webhook", "email"]
  webhook:
    url: "http://alertmanager:9093/api/v1/alerts"
  email:
    smtp_server: "smtp.example.com:587"
    from: "alerts@example.com"
    to: ["admin@example.com"]
```

## Deployment Reference

### 📦 Helm Charts

#### Memory Agent Chart
```yaml
# Chart.yaml
apiVersion: v2
name: agent-memory
description: "Memory Agent for AI Agents Ecosystem"
type: application
version: 1.0.0
appVersion: "1.0.0"

# values.yaml
image:
  repository: agent-memory
  tag: "latest"
  pullPolicy: IfNotPresent

replicaCount: 1

resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"

persistence:
  enabled: true
  storageClass: "standard"
  size: "10Gi"

config:
  databasePath: "/data/memory.db"
  modelPath: "/models/qwen2.5-0.5b.gguf"
  maxTokens: 2048
  temperature: 0.7

service:
  type: ClusterIP
  port: 8080

ingress:
  enabled: false
  className: "nginx"
  annotations: {}
  hosts:
    - host: agent-memory.local
      paths:
        - path: /
          pathType: Prefix
```

#### Temporal Chart
```yaml
# values.yaml
server:
  replicaCount: 1
  image:
    tag: "1.22.0"
  resources:
    requests:
      memory: "512Mi"
      cpu: "200m"
    limits:
      memory: "1Gi"
      cpu: "500m"

frontend:
  service:
    type: ClusterIP
    port: 7233

cassandra:
  enabled: true
  persistence:
    enabled: false
  config:
    cluster_size: 1
    seed_size: 1

elasticsearch:
  enabled: false

webUI:
  enabled: true
  service:
    type: ClusterIP
    port: 8080
```

#### Monitoring Chart
```yaml
# values.yaml
metricsCollector:
  image:
    repository: metrics-collector
    tag: "latest"
  resources:
    requests:
      memory: "128Mi"
      cpu: "100m"
    limits:
      memory: "256Mi"
      cpu: "200m"

prometheus:
  enabled: true
  service:
    type: ClusterIP
    port: 9090

grafana:
  enabled: true
  service:
    type: ClusterIP
    port: 3000
  dashboards:
    - name: "AI Agents Overview"
      uid: "ai-agents-overview"
      file: "dashboards/ai-agents-overview.json"

alertmanager:
  enabled: true
  service:
    type: ClusterIP
    port: 9093
```

### 🚀 Deployment Scripts

#### Complete Deployment Script
```bash
#!/bin/bash
# deploy-ai-agents-ecosystem.sh

set -e

NAMESPACE="ai-infrastructure"
TEMPORAL_VERSION="1.28.3"
OLLAMA_MODEL="qwen2.5:0.5b"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Main deployment function
main() {
    log_info "Starting Cloud AI Agents Ecosystem Deployment..."
    
    check_prerequisites
    create_namespace
    deploy_memory_agents
    deploy_temporal
    deploy_monitoring
    deploy_dashboard
    validate_deployment
    print_access_info
    
    log_success "🎯 Deployment complete!"
}

# Run main function
main "$@"
```

#### Health Check Script
```bash
#!/bin/bash
# health-check.sh

NAMESPACE="ai-infrastructure"

# Check all deployments
deployments=("agent-memory-rust" "temporal-frontend" "agent-dashboard" "metrics-collector")

for deployment in "${deployments[@]}"; do
    if kubectl rollout status deployment/$deployment -n $NAMESPACE --timeout=60s; then
        echo "✅ $deployment is healthy"
    else
        echo "❌ $deployment is not healthy"
        exit 1
    fi
done

# Check services
services=("agent-memory-service" "temporal-frontend" "agent-dashboard-service")

for service in "${services[@]}"; do
    if kubectl get service $service -n $NAMESPACE &>/dev/null; then
        echo "✅ $service exists"
    else
        echo "❌ $service missing"
        exit 1
    fi
done

echo "🎉 All components are healthy!"
```

## Monitoring Reference

### 📊 Metrics Reference

#### Workflow Metrics
| Metric Name | Type | Description | Labels |
|-------------|------|-------------|--------|
| `workflow_total` | Gauge | Total number of workflows | `type`, `status` |
| `workflow_duration_avg` | Gauge | Average workflow duration | `unit` |
| `workflow_duration_max` | Gauge | Maximum workflow duration | `unit` |
| `workflow_retry_rate` | Gauge | Workflow retry rate | `status` |
| `workflow_error_rate` | Gauge | Workflow error rate | `type` |

#### Agent Metrics
| Metric Name | Type | Description | Labels |
|-------------|------|-------------|--------|
| `agent_executions_total` | Counter | Total agent executions | `agent` |
| `agent_executions_successful` | Counter | Successful executions | `agent` |
| `agent_executions_failed` | Counter | Failed executions | `agent` |
| `agent_score_avg` | Gauge | Average agent score | `agent` |
| `agent_duration_avg` | Gauge | Average execution time | `agent` |
| `agent_error_rate` | Gauge | Agent error rate | `agent` |

#### System Metrics
| Metric Name | Type | Description | Labels |
|-------------|------|-------------|--------|
| `system_uptime` | Counter | System uptime | `unit` |
| `system_memory_used` | Gauge | Memory usage | `unit` |
| `system_goroutines` | Gauge | Active goroutines | |
| `system_error_rate` | Gauge | System error rate | `type` |

### 🚨 Alert Rules

#### Workflow Alerts
```yaml
# workflow-timeout.yaml
groups:
- name: workflow
  rules:
  - alert: WorkflowTimeout
    expr: workflow_duration_max > 7200
    for: 5m
    labels:
      severity: warning
      service: temporal
    annotations:
      summary: "Workflow execution exceeding timeout"
      description: "Workflow {{ $labels.workflow_type }} has been running for more than 2 hours"
```

#### Agent Alerts
```yaml
# agent-failure-rate.yaml
groups:
- name: agents
  rules:
  - alert: AgentHighFailureRate
    expr: agent_error_rate > 0.1
    for: 2m
    labels:
      severity: critical
      service: agent-memorys
    annotations:
      summary: "Agent failure rate above threshold"
      description: "Agent {{ $labels.agent }} failure rate is {{ $value }} (threshold: 0.1)"
```

#### System Alerts
```yaml
# system-resources.yaml
groups:
- name: system
  rules:
  - alert: HighMemoryUsage
    expr: system_memory_used / system_memory_total > 0.9
    for: 5m
    labels:
      severity: warning
      service: system
    annotations:
      summary: "High memory usage"
      description: "Memory usage is {{ $value | humanizePercentage }}"
```

## Troubleshooting Reference

### 🔧 Common Issues

#### Pod Issues

##### Pod Not Starting
```bash
# Check pod status
kubectl get pods -n ai-infrastructure

# Describe pod
kubectl describe pod <pod-name> -n ai-infrastructure

# Check logs
kubectl logs <pod-name> -n ai-infrastructure

# Check events
kubectl get events -n ai-infrastructure --sort-by=.metadata.creationTimestamp
```

##### Pod Crashing
```bash
# Check crash logs
kubectl logs <pod-name> -n ai-infrastructure --previous

# Check resource limits
kubectl describe pod <pod-name> -n ai-infrastructure | grep -A 10 "Limits:"

# Check node resources
kubectl top nodes
kubectl top pods -n ai-infrastructure
```

#### Service Issues

##### Service Not Accessible
```bash
# Check service
kubectl get svc -n ai-infrastructure

# Describe service
kubectl describe svc <service-name> -n ai-infrastructure

# Check endpoints
kubectl get endpoints <service-name> -n ai-infrastructure

# Test connectivity
kubectl run test-pod --image=busybox --rm -it --restart=Never -- \
  wget -qO- http://<service-name>.<namespace>.svc.cluster.local:<port>
```

##### Port Forward Issues
```bash
# Check if port is available
netstat -tulpn | grep :8888

# Kill existing processes
pkill -f "kubectl port-forward"

# Try different port
kubectl port-forward svc/<service-name> 9999:80 -n ai-infrastructure
```

#### Database Issues

##### Database Connection Errors
```bash
# Check PVC
kubectl get pvc -n ai-infrastructure

# Check PVC status
kubectl describe pvc agent-memory-pvc -n ai-infrastructure

# Check database file
kubectl exec -it deployment/agent-memory-rust -n ai-infrastructure -- \
  ls -la /data/memory.db

# Test database
kubectl exec -it deployment/agent-memory-rust -n ai-infrastructure -- \
  sqlite3 /data/memory.db ".tables"
```

##### Database Corruption
```bash
# Backup current database
kubectl exec deployment/agent-memory-rust -n ai-infrastructure -- \
  cp /data/memory.db /data/memory.db.backup

# Check database integrity
kubectl exec deployment/agent-memory-rust -n ai-infrastructure -- \
  sqlite3 /data/memory.db "PRAGMA integrity_check;"

# Recover database
kubectl exec deployment/agent-memory-rust -n ai-infrastructure -- \
  sqlite3 /data/memory.db ".recover" | sqlite3 /data/memory-recovered.db
```

#### Performance Issues

##### High Memory Usage
```bash
# Check memory usage
kubectl top pods -n ai-infrastructure --sort-by=memory

# Check memory limits
kubectl describe pod <pod-name> -n ai-infrastructure | grep -A 10 "Memory:"

# Optimize memory usage
kubectl patch deployment <deployment-name> -n ai-infrastructure -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container-name>","resources":{"limits":{"memory":"1Gi"}}}]}}}}'
```

##### High CPU Usage
```bash
# Check CPU usage
kubectl top pods -n ai-infrastructure --sort-by=cpu

# Check CPU limits
kubectl describe pod <pod-name> -n ai-infrastructure | grep -A 10 "CPU:"

# Scale horizontally
kubectl scale deployment <deployment-name> --replicas=3 -n ai-infrastructure
```

### 🔍 Debug Commands

#### System Health Check
```bash
#!/bin/bash
# system-health-check.sh

NAMESPACE="ai-infrastructure"

echo "🔍 Checking system health..."

# Check namespace
kubectl get namespace $NAMESPACE

# Check deployments
echo "📦 Checking deployments..."
kubectl get deployments -n $NAMESPACE

# Check pods
echo "🚀 Checking pods..."
kubectl get pods -n $NAMESPACE

# Check services
echo "🌐 Checking services..."
kubectl get services -n $NAMESPACE

# Check ingress
echo "🔗 Checking ingress..."
kubectl get ingress -n $NAMESPACE

# Check resource usage
echo "📊 Checking resource usage..."
kubectl top pods -n $NAMESPACE

echo "✅ Health check complete!"
```

#### Component Debug Script
```bash
#!/bin/bash
# debug-component.sh

COMPONENT=$1
NAMESPACE="ai-infrastructure"

if [ -z "$COMPONENT" ]; then
    echo "Usage: $0 <component-name>"
    exit 1
fi

echo "🔍 Debugging component: $COMPONENT"

# Get deployment info
kubectl get deployment $COMPONENT -n $NAMESPACE -o yaml

# Get pod info
kubectl get pods -l app=$COMPONENT -n $NAMESPACE -o wide

# Get logs
kubectl logs -l app=$COMPONENT -n $NAMESPACE --tail=100

# Describe pod
kubectl describe pod -l app=$COMPONENT -n $NAMESPACE

# Get events
kubectl get events -n ai-infrastructure --field-selector involvedObject.name=$COMPONENT
```

## Security Reference

### 🔒 Security Configuration

#### Network Policies
```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-agents-network-policy
  namespace: ai-infrastructure
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ai-infrastructure
    ports:
    - protocol: TCP
      port: 8080
    - protocol: TCP
      port: 7233
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: ai-infrastructure
    ports:
    - protocol: TCP
      port: 8080
    - protocol: TCP
      port: 7233
    - protocol: TCP
      port: 9042  # Cassandra
```

#### RBAC Configuration
```yaml
# rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ai-agents-sa
  namespace: ai-infrastructure
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ai-agents-role
  namespace: ai-infrastructure
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ai-agents-binding
  namespace: ai-infrastructure
subjects:
- kind: ServiceAccount
  name: ai-agents-sa
  namespace: ai-infrastructure
roleRef:
  kind: Role
  name: ai-agents-role
  apiGroup: rbac.authorization.k8s.io
```

#### Pod Security Policy
```yaml
# pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: ai-agents-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

### 🔐 Authentication Configuration

#### TLS Configuration
```yaml
# tls-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-agents-tls
  namespace: ai-infrastructure
type: kubernetes.io/tls
data:
  tls.crt: <base64-encoded-cert>
  tls.key: <base64-encoded-key>
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-agents-ingress
  namespace: ai-infrastructure
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - ai-agents.local
    secretName: ai-agents-tls
  rules:
  - host: ai-agents.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: agent-dashboard-service
            port:
              number: 80
```

#### OIDC Configuration
```yaml
# oidc-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: oidc-config
  namespace: ai-infrastructure
data:
  config.yaml: |
    oidc:
      issuer: "https://your-oidc-provider.com"
      client_id: "ai-agents-client"
      client_secret: "your-client-secret"
      redirect_uri: "https://ai-agents.local/oauth/callback"
      scopes: ["openid", "profile", "email"]
```

## Performance Reference

### ⚡ Performance Tuning

#### Resource Optimization
```yaml
# resource-optimization.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: performance-config
  namespace: ai-infrastructure
data:
  config.yaml: |
    performance:
      # Database optimization
      database:
        connection_pool_size: 20
        query_timeout: "30s"
        connection_timeout: "5s"
        max_idle_connections: 10
      
      # Cache optimization
      cache:
        ttl: "1h"
        max_size: "1GB"
        eviction_policy: "lru"
      
      # Concurrency optimization
      concurrency:
        max_concurrent_requests: 50
        request_queue_size: 100
        worker_pool_size: 20
      
      # Memory optimization
      memory:
        gc_percent: 100
        max_heap_size: "512MB"
        stack_size: "2MB"
```

#### Scaling Configuration
```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-memory-hpa
  namespace: ai-infrastructure
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-memory-rust
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
```

#### Caching Strategy
```yaml
# redis-cache.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-cache
  namespace: ai-infrastructure
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis-cache
  template:
    metadata:
      labels:
        app: redis-cache
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
        command:
        - redis-server
        - --maxmemory
        - "256mb"
        - --maxmemory-policy
        - "allkeys-lru"
---
apiVersion: v1
kind: Service
metadata:
  name: redis-cache
  namespace: ai-infrastructure
spec:
  selector:
    app: redis-cache
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
```

### 📈 Performance Monitoring

#### Performance Metrics
```yaml
# performance-metrics.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: performance-metrics
  namespace: ai-infrastructure
data:
  metrics.yaml: |
    metrics:
      # Response time metrics
      response_time:
        histogram:
          buckets: [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        labels: ["endpoint", "method", "status"]
      
      # Throughput metrics
      throughput:
        counter:
          labels: ["endpoint", "method", "status"]
      
      # Error rate metrics
      error_rate:
        gauge:
          labels: ["endpoint", "error_type"]
      
      # Resource usage metrics
      resource_usage:
        gauge:
          labels: ["resource_type", "component"]
      
      # Cache performance
      cache_performance:
        gauge:
          labels: ["cache_type", "operation"]
```

#### Performance Alerts
```yaml
# performance-alerts.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: performance-alerts
  namespace: ai-infrastructure
data:
  alerts.yaml: |
    alerts:
      - name: high_response_time
        condition: "response_time_p95 > 5s"
        severity: warning
        message: "Response time is above 5 seconds"
      
      - name: low_throughput
        condition: "throughput_rate < 10req/s"
        severity: warning
        message: "Throughput is below 10 requests per second"
      
      - name: high_error_rate
        condition: "error_rate > 0.05"
        severity: critical
        message: "Error rate is above 5%"
      
      - name: high_memory_usage
        condition: "memory_usage > 0.9"
        severity: warning
        message: "Memory usage is above 90%"
      
      - name: high_cpu_usage
        condition: "cpu_usage > 0.8"
        severity: warning
        message: "CPU usage is above 80%"
```

---

**Last Updated**: 2026-03-16  
**Version**: 1.0.0  
**Maintainer**: Cloud AI Agents Team

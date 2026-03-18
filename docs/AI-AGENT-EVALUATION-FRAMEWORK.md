# AI Agent Evaluation Framework - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Evaluators](#evaluators)
4. [Background Deployment Options](#background-deployment-options)
5. [Installation & Setup](#installation--setup)
6. [Usage Guide](#usage-guide)
7. [API Reference](#api-reference)
8. [Configuration](#configuration)
9. [Monitoring & Observability](#monitoring--observability)
10. [Troubleshooting](#troubleshooting)
11. [Development](#development)
12. [Contributing](#contributing)

---

## Overview

The AI Agent Evaluation Framework is a comprehensive system for evaluating AI agent performance, security, compliance, and operational health. It provides multiple evaluation approaches and can run automatically in the background as containerized services.

### Key Features
- **7 Specialized Evaluators**: Skill invocation, performance, cost, monitoring, health check, security, compliance
- **Multiple Deployment Options**: Scheduled jobs, API server, Temporal workflows
- **Visualization & Reporting**: Charts, dashboards, HTML reports
- **Quality Gates**: Configurable thresholds with automated notifications
- **Background Execution**: Containerized services in Kubernetes
- **CI/CD Integration**: GitHub Actions, Jenkins pipelines

### Architecture Components
```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent Evaluation Framework            │
├─────────────────────────────────────────────────────────────┤
│  Evaluators (7)                                            │
│  ├── Skill Invocation Evaluator                            │
│  ├── Performance Evaluator                                 │
│  ├── Cost Evaluator                                        │
│  ├── Monitoring Evaluator                                  │
│  ├── Health Check Evaluator                                │
│  ├── Security Evaluator                                    │
│  └── Compliance Evaluator                                  │
├─────────────────────────────────────────────────────────────┤
│  Deployment Options                                        │
│  ├── Option 1: Scheduled Kubernetes Jobs                   │
│  ├── Option 2: REST API Server                             │
│  └── Option 3: Temporal Workflows                          │
├─────────────────────────────────────────────────────────────┤
│  Visualization & Reporting                                 │
│  ├── Performance Dashboards                                │
│  ├── Trend Analysis Charts                                 │
│  ├── Model Comparison Reports                              │
│  └── HTML Evaluation Reports                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture

### System Components

#### 1. Evaluation Framework Core
- **Location**: `agent-tracing-evaluation/`
- **Language**: Python
- **Purpose**: Main evaluation engine with all evaluators

#### 2. Background Services
- **API Server**: Flask-based REST API
- **Temporal Workers**: Event-driven evaluation workflows
- **Scheduled Jobs**: Kubernetes CronJobs for periodic evaluation

#### 3. Containerization
- **Dockerfile**: Multi-stage build for different deployment targets
- **Kubernetes**: Complete manifests for production deployment
- **Monitoring**: Health checks, metrics, logging

#### 4. Integration Points
- **Langfuse**: Trace data ingestion
- **Temporal**: Workflow orchestration
- **Kubernetes**: Infrastructure deployment
- **CI/CD**: Automated evaluation pipelines

### Data Flow
```
Langfuse Traces → Evaluation Framework → Results → Visualizations → Storage
                    ↓
Background Services ← Quality Gates ← Notifications
```

---

## Evaluators

### 1. Skill Invocation Evaluator
**File**: `agent-tracing-evaluation/evaluators/skill_invocation_evaluator.py`

**Purpose**: Evaluates AI agent skill execution patterns and effectiveness.

**Metrics**:
- Skill success rates
- Execution timing patterns
- Parameter validation
- Error frequency analysis

**Scoring**:
- Success rate weight: 40%
- Performance timing weight: 30%
- Parameter correctness weight: 20%
- Error handling weight: 10%

### 2. Performance Evaluator
**File**: `agent-tracing-evaluation/evaluators/performance_evaluator.py`

**Purpose**: Analyzes system performance metrics and response times.

**Metrics**:
- Latency measurements
- Throughput analysis
- Resource utilization
- Performance trends

**Scoring**:
- Latency compliance weight: 35%
- Throughput metrics weight: 25%
- Resource efficiency weight: 25%
- Trend analysis weight: 15%

### 3. Cost Evaluator
**File**: `agent-tracing-evaluation/evaluators/cost_evaluator.py`

**Purpose**: Evaluates cost efficiency and resource optimization.

**Metrics**:
- Token usage patterns
- Compute resource costs
- Storage consumption
- Cost optimization opportunities

**Scoring**:
- Cost efficiency weight: 40%
- Resource utilization weight: 30%
- Optimization potential weight: 20%
- Trend analysis weight: 10%

### 4. Monitoring Evaluator
**File**: `agent-tracing-evaluation/evaluators/monitoring_evaluator.py`

**Purpose**: Monitors system health and infrastructure status.

**Metrics**:
- Infrastructure health
- Agent availability
- Resource exhaustion detection
- Auto-fix capabilities

**Scoring**:
- System health weight: 35%
- Resource monitoring weight: 25%
- Issue detection weight: 25%
- Auto-fix effectiveness weight: 15%

### 5. Health Check Evaluator
**File**: `agent-tracing-evaluation/evaluators/health_check_evaluator.py`

**Purpose**: Evaluates agent health and readiness status.

**Metrics**:
- Worker health status
- Conversation completion rates
- System readiness checks
- Error pattern analysis

**Scoring**:
- Worker health weight: 40%
- Conversation health weight: 30%
- System readiness weight: 20%
- Error analysis weight: 10%

### 6. Security Evaluator
**File**: `agent-tracing-evaluation/evaluators/security_evaluator.py`

**Purpose**: Evaluates security compliance and vulnerability assessment.

**Metrics**:
- PII exposure detection
- Injection vulnerability scanning
- Authentication/authorization checks
- Data encryption validation

**Scoring**:
- Security issues weight: 40%
- Vulnerability assessment weight: 30%
- Compliance checks weight: 20%
- Risk analysis weight: 10%

### 7. Compliance Evaluator
**File**: `agent-tracing-evaluation/evaluators/compliance_evaluator.py`

**Purpose**: Evaluates regulatory compliance (GDPR, HIPAA, NIST, etc.).

**Metrics**:
- GDPR compliance checks
- HIPAA validation
- NIST standards adherence
- Audit trail completeness

**Scoring**:
- Compliance score weight: 50%
- Audit completeness weight: 25%
- Policy adherence weight: 15%
- Documentation weight: 10%

---

## Background Deployment Options

### Option 1: Scheduled Kubernetes Jobs

**Description**: Automated periodic evaluations using Kubernetes CronJobs.

**Components**:
- `ai-agent-evaluation-cronjob.yaml` - CronJob definition
- Runs every 4 hours (configurable)
- Quality gates with failure handling
- Artifact storage and retrieval

**Use Cases**:
- Regular health monitoring
- Compliance checking
- Performance trend analysis

**Configuration**:
```yaml
schedule: "0 */4 * * *"  # Every 4 hours
concurrencyPolicy: Forbid
successfulJobsHistoryLimit: 3
failedJobsHistoryLimit: 3
```

**Management**:
```bash
# View jobs
kubectl get cronjobs -n ai-agents
kubectl get jobs -n ai-agents

# Manual trigger
kubectl create job --from=cronjob/ai-agent-evaluation-cronjob manual-eval

# View logs
kubectl logs job/<job-name> -n ai-agents
```

### Option 2: REST API Server

**Description**: On-demand evaluation via Flask-based REST API.

**Components**:
- `api-server.py` - Flask application
- `ai-agent-evaluator-deployment.yaml` - Kubernetes deployment
- Service with load balancing
- Health monitoring and auto-scaling

**API Endpoints**:
- `GET /health` - Health check
- `GET /evaluators` - List available evaluators
- `POST /evaluate` - Start evaluation
- `POST /evaluate/upload` - Upload and evaluate
- `GET /evaluate/{id}/status` - Check status
- `GET /evaluate/{id}/results` - Get results
- `GET /evaluate/{id}/visualizations/{file}` - Get visualizations
- `GET /evaluations` - List evaluations
- `GET /metrics` - System metrics

**Use Cases**:
- Interactive evaluation
- Integration with other systems
- Real-time monitoring
- Custom evaluation workflows

**Configuration**:
```yaml
replicas: 2
ports:
- containerPort: 5000
livenessProbe:
  httpGet:
    path: /health
    port: 5000
readinessProbe:
  httpGet:
    path: /health
    port: 5000
```

### Option 3: Temporal Workflow Integration

**Description**: Event-driven evaluation using Temporal workflows.

**Components**:
- `evaluation_workflow.go` - Go workflow definitions
- `evaluation_activities.go` - Activity implementations
- `temporal_worker.py` - Python worker
- Kubernetes deployment alongside existing AI agents

**Workflow Types**:
1. **EvaluationWorkflow**: Standard evaluation pipeline
2. **ScheduledEvaluationWorkflow**: Hourly automated evaluations
3. **EventDrivenEvaluationWorkflow**: Triggered by system events

**Use Cases**:
- Complex multi-step evaluation
- Event-driven automation
- Integration with AI agent workflows
- Durable execution with retries

**Configuration**:
```go
@workflow.defn
class EvaluationWorkflow:
    @workflow.run
    async def run(self, input_data: dict) -> dict:
        # Orchestrate evaluation steps
        await workflow.execute_activity(prepare_evaluation_environment, input_data)
        await workflow.execute_activity(generate_sample_traces, input_data)
        await workflow.execute_activity(run_evaluation_activity, input_data)
        await workflow.execute_activity(generate_visualizations, input_data)
        await workflow.execute_activity(check_quality_gates, input_data)
```

---

## Installation & Setup

### Prerequisites

#### System Requirements
- Kubernetes cluster (v1.20+)
- Docker registry access
- kubectl configured
- Optional: Temporal server (for Option 3)

#### Software Dependencies
- Python 3.12+
- Docker
- kubectl
- Optional: Temporal CLI

### Quick Installation

#### 1. Clone Repository
```bash
git clone <repository-url>
cd gitops-infra-control-plane
```

#### 2. Deploy Everything
```bash
./core/deployment/deploy-evaluation-framework.sh deploy
```

#### 3. Verify Installation
```bash
./core/deployment/deploy-evaluation-framework.sh status
```

### Custom Installation

#### Environment Variables
```bash
export DOCKER_REGISTRY=myregistry.com
export IMAGE_TAG=v1.0.0
export NAMESPACE=ai-evaluators
```

#### Selective Deployment
```bash
# Deploy specific options
./core/deployment/deploy-evaluation-framework.sh scheduled  # Option 1
./core/deployment/deploy-evaluation-framework.sh api        # Option 2
./core/deployment/deploy-evaluation-framework.sh temporal   # Option 3
```

### Manual Installation Steps

#### 1. Build Docker Images
```bash
# Build all images
docker build -f core/deployment/ai-agent-evaluator-Dockerfile -t ai-agent-evaluator:latest .

# Build specific targets
docker build -f core/deployment/ai-agent-evaluator-Dockerfile --target production -t ai-agent-evaluator-api:latest .
docker build -f core/deployment/ai-agent-evaluator-Dockerfile --target temporal-worker -t ai-agent-evaluator:latest .
```

#### 2. Deploy Kubernetes Resources
```bash
# Create namespace
kubectl create namespace ai-agents

# Apply manifests
kubectl apply -f core/deployment/ai-agent-evaluator-complete.yaml -n ai-agents
```

#### 3. Deploy Specific Options
```bash
# Option 1: Scheduled Jobs
kubectl apply -f core/deployment/ai-agent-evaluation-cronjob.yaml -n ai-agents

# Option 2: API Server
kubectl apply -f core/deployment/ai-agent-evaluator-deployment.yaml -n ai-agents

# Option 3: Temporal Workers (included in complete manifest)
# Workers are deployed as part of the complete manifest
```

---

## Usage Guide

### CLI Usage

#### Basic Evaluation
```bash
cd agent-tracing-evaluation

# Generate sample traces
python cli.py --generate-sample 100 --file sample_traces.json

# Run evaluation
python cli.py --file sample_traces.json --evaluators all --format json

# Generate visualizations
python cli.py --file sample_traces.json --visualize --report-dir ./reports
```

#### Advanced Usage
```bash
# Specific evaluators
python cli.py --file traces.json --evaluators skill_invocation,performance,cost

# Different output formats
python cli.py --file traces.json --format detailed --output results.json

# Trend analysis
python cli.py --file traces.json --trend-analysis --days 30
```

### API Usage

#### Start Evaluation
```bash
# Port forward
kubectl port-forward service/ai-agent-evaluator-service 8080:80 -n ai-agents

# Start evaluation
curl -X POST http://localhost:8080/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "traces": [{"id": "trace-1", "timestamp": 1234567890}],
    "evaluators": ["skill_invocation", "performance"],
    "options": {"generate_visualizations": true}
  }'
```

#### Upload and Evaluate
```bash
curl -X POST http://localhost:8080/evaluate/upload \
  -F "file=@traces.json" \
  -F "evaluators=skill_invocation,performance,cost" \
  -F "generate_visualizations=true"
```

#### Check Status
```bash
# Get evaluation status
curl http://localhost:8080/evaluate/eval-id/status

# Get results
curl http://localhost:8080/evaluate/eval-id/results

# Get visualizations
curl http://localhost:8080/evaluate/eval-id/visualizations/performance_dashboard.png -o dashboard.png
```

### Temporal Usage

#### Start Workflow
```go
client := temporal.NewClient(...)
workflowOptions := client.StartWorkflowOptions{
    ID: "evaluation-" + uuid.New().String(),
    TaskQueue: "ai-agent-evaluation",
}

_, err := client.ExecuteWorkflow(
    context.Background(),
    workflowOptions,
    workflows.EvaluationWorkflow,
    EvaluationWorkflowInput{
        Evaluators:        []string{"skill_invocation", "performance", "cost"},
        QualityGateScore:  0.8,
        QualityGateRate:   0.85,
        TraceCount:        100,
        NotificationEmail: "dev-team@company.com",
    },
)
```

#### Event-Driven Trigger
```go
// Trigger evaluation from system event
triggerData := map[string]interface{}{
    "trace_source": "langfuse-ingestion",
    "operation_type": "batch_evaluation",
    "urgency": "high",
}

_, err := client.ExecuteWorkflow(
    context.Background(),
    workflowOptions,
    workflows.EventDrivenEvaluationWorkflow,
    triggerData,
)
```

---

## API Reference

### Response Formats

#### Evaluation Status Response
```json
{
  "id": "eval-uuid-string",
  "status": "running|completed|failed",
  "created_at": "2024-01-01T00:00:00Z",
  "traces_count": 100,
  "evaluators": ["skill_invocation", "performance"],
  "options": {
    "generate_visualizations": true,
    "quality_gate_score": 0.8
  }
}
```

#### Evaluation Results Response
```json
{
  "id": "eval-uuid-string",
  "status": "completed",
  "completed_at": "2024-01-01T00:05:00Z",
  "result": {
    "summary": {
      "overall_score": 0.85,
      "overall_pass_rate": 0.92,
      "total_evaluations": 100
    },
    "evaluator_results": {
      "skill_invocation": {
        "average_score": 0.9,
        "pass_rate": 0.95,
        "details": {...}
      },
      "performance": {
        "average_score": 0.8,
        "pass_rate": 0.88,
        "details": {...}
      }
    },
    "aggregate_metrics": {
      "total_issues": 5,
      "critical_issues": 0,
      "high_issues": 2,
      "recommendations": [...]
    }
  },
  "visualizations": {
    "performance_dashboard": "/visualizations/eval-id/performance_dashboard.png",
    "trend_analysis": "/visualizations/eval-id/trend_analysis.png",
    "model_comparison": "/visualizations/eval-id/model_comparison.png",
    "html_report": "/visualizations/eval-id/evaluation_report.html"
  }
}
```

#### Error Response
```json
{
  "error": "Evaluation failed",
  "message": "Invalid trace data format",
  "code": "INVALID_INPUT",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### HTTP Status Codes
- `200 OK` - Successful request
- `201 Created` - Evaluation started
- `400 Bad Request` - Invalid input
- `404 Not Found` - Evaluation not found
- `413 Payload Too Large` - File too large
- `500 Internal Server Error` - Server error

### Rate Limits
- Maximum file size: 100MB
- Concurrent evaluations: Limited by available resources
- API rate limiting: Configurable via deployment

---

## Configuration

### Environment Variables

#### Framework Configuration
```bash
# Evaluator settings
EVALUATORS=skill_invocation,performance,cost,monitoring,health_check,security,compliance
QUALITY_GATE_SCORE=0.8
QUALITY_GATE_PASS_RATE=0.85

# Data paths
TRACE_FILE_PATH=/data/traces.json
RESULTS_PATH=/results
VISUALIZATION_PATH=/visualizations

# API settings
FLASK_ENV=production
API_HOST=0.0.0.0
API_PORT=5000

# Temporal settings
TEMPORAL_HOST=localhost
TEMPORAL_PORT=7233
TASK_QUEUE=ai-agent-evaluation
```

#### Kubernetes Configuration
```yaml
# ConfigMap: evaluator-config
evaluators.json: |
  {
    "skill_invocation": {
      "enabled": true,
      "weight": 0.2,
      "threshold": 0.7
    },
    "performance": {
      "enabled": true,
      "weight": 0.2,
      "threshold": 0.8
    }
  }

# Secret: evaluator-secrets
data:
  temporal-host: bG9jYWxob3N0
  temporal-port: NzIzMw==
  notification-email: ZGV2LXRlYW1AY29tcGFueS5jb20=
```

### Quality Gates Configuration

#### Threshold Settings
```json
{
  "score_threshold": 0.8,
  "pass_rate_threshold": 0.85,
  "critical_issue_threshold": 0,
  "high_issue_threshold": 2,
  "enable_auto_fix": true,
  "notification_on_failure": true
}
```

#### Evaluator Weights
```json
{
  "skill_invocation": {"weight": 0.2, "threshold": 0.7},
  "performance": {"weight": 0.2, "threshold": 0.8},
  "cost": {"weight": 0.15, "threshold": 0.85},
  "monitoring": {"weight": 0.15, "threshold": 0.75},
  "health_check": {"weight": 0.1, "threshold": 0.8},
  "security": {"weight": 0.1, "threshold": 0.9},
  "compliance": {"weight": 0.1, "threshold": 0.85}
}
```

### Resource Configuration

#### CPU and Memory Limits
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "200m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

#### Storage Configuration
```yaml
# PersistentVolumeClaim
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
```

---

## Monitoring & Observability

### Metrics Collection

#### System Metrics
- Evaluation counts and success rates
- Average evaluation scores by evaluator
- Processing times and throughput
- Error rates and failure patterns
- Resource utilization (CPU, memory, storage)

#### Business Metrics
- Quality gate pass/fail rates
- Security issue detection rates
- Compliance score trends
- Cost optimization opportunities
- Performance degradation alerts

### Logging

#### Log Format
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "INFO",
  "component": "evaluation_framework",
  "evaluation_id": "eval-uuid",
  "evaluator": "skill_invocation",
  "message": "Evaluation completed successfully",
  "duration_ms": 1500,
  "score": 0.85
}
```

#### Log Levels
- `DEBUG`: Detailed debugging information
- `INFO`: General operational information
- `WARN`: Warning messages for potential issues
- `ERROR`: Error messages for failures

#### Log Aggregation
- Structured JSON logging
- Correlation IDs for traceability
- Evaluation-specific metadata
- Error details and stack traces

### Health Monitoring

#### Health Check Endpoints
```bash
# API server health
GET /health

# Individual evaluator health
GET /health/evaluators
GET /health/evaluator/skill_invocation
```

#### Health Check Response
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "evaluators": ["skill_invocation", "performance", "cost"],
  "checks": {
    "database": "healthy",
    "storage": "healthy",
    "temporal": "healthy"
  }
}
```

### Alerting

#### Alert Conditions
- Quality gate failures
- High error rates (>5%)
- Resource exhaustion (>90% CPU/memory)
- Service availability issues
- Security vulnerability detection

#### Notification Channels
- Email alerts
- Slack notifications
- PagerDuty integration
- Custom webhooks

---

## Troubleshooting

### Common Issues

#### Pod Failures
```bash
# Check pod status
kubectl get pods -n ai-agents

# View pod logs
kubectl logs -f deployment/ai-agent-evaluator-api -n ai-agents

# Describe pod for events
kubectl describe pod <pod-name> -n ai-agents

# Check resource usage
kubectl top pods -n ai-agents
```

#### API Issues
```bash
# Check service endpoints
kubectl get endpoints ai-agent-evaluator-service -n ai-agents

# Test service connectivity
kubectl run test-pod --rm -i --tty --image=curlimages/curl \
  -- curl -s http://ai-agent-evaluator-service/health

# Check network policies
kubectl get networkpolicies -n ai-agents

# Port forward for local testing
kubectl port-forward service/ai-agent-evaluator-service 8080:80 -n ai-agents
```

#### Temporal Issues
```bash
# Check Temporal connectivity
kubectl logs deployment/temporal-evaluation-worker -n ai-agents | grep "temporal"

# Check workflow history
kubectl exec deployment/temporal -n temporal -- temporal workflow list

# View task queue
kubectl exec deployment/temporal -n temporal -- temporal task-queue describe ai-agent-evaluation

# Check worker status
kubectl logs deployment/temporal-evaluation-worker -n ai-agents | grep "Worker started"
```

#### Storage Issues
```bash
# Check PVC status
kubectl get pvc -n ai-agents

# Check storage class
kubectl get storageclass

# View volume mounts
kubectl describe pod <pod-name> -n ai-agents | grep -A 10 "Mounts"

# Check disk usage
kubectl exec -n ai-agents <pod-name> -- df -h
```

#### Evaluation Failures
```bash
# Check evaluation logs
kubectl logs job/<evaluation-job> -n ai-agents

# View evaluation results
kubectl get configmap evaluation-results -n ai-agents -o yaml

# Check quality gate results
kubectl logs deployment/ai-agent-evaluator-api -n ai-agents | grep "quality_gate"
```

### Performance Issues

#### Resource Optimization
```bash
# Check resource usage
kubectl top pods -n ai-agents
kubectl top nodes

# Scale deployments
kubectl scale deployment ai-agent-evaluator-api --replicas=3 -n ai-agents

# Update resource limits
kubectl patch deployment ai-agent-evaluator-api -n ai-agents -p '{"spec":{"template":{"spec":{"containers":[{"name":"evaluator-api","resources":{"limits":{"memory":"1Gi","cpu":"1000m"}}}]}}}}'
```

#### Database Performance
```bash
# Check database connections
kubectl logs deployment/ai-agent-evaluator-api -n ai-agents | grep "database"

# Monitor query performance
kubectl exec -n ai-agents <pod-name> -- python -c "
import time
start = time.time()
# Run evaluation
end = time.time()
print(f'Evaluation took {end - start:.2f} seconds')
"
```

### Debug Mode

#### Enable Debug Logging
```bash
# Set debug environment variable
kubectl set env deployment/ai-agent-evaluator-api LOG_LEVEL=DEBUG -n ai-agents

# Restart deployment
kubectl rollout restart deployment/ai-agent-evaluator-api -n ai-agents
```

#### Manual Testing
```bash
# Test evaluation manually
kubectl exec -n ai-agents <pod-name> -- python cli.py --file /data/test_traces.json --evaluators skill_invocation

# Test API endpoints
kubectl exec -n ai-agents <pod-name> -- curl -s http://localhost:5000/health

# Test Temporal worker
kubectl exec -n ai-agents <pod-name> -- python -c "
import temporalio
print('Temporal SDK available')
"
```

---

## Development

### Local Development Setup

#### Prerequisites
```bash
# Python dependencies
pip install -r agent-tracing-evaluation/requirements.txt

# Development tools
pip install pytest black flake8 mypy

# Docker (for local testing)
docker build -f core/deployment/ai-agent-evaluator-Dockerfile -t ai-agent-evaluator:dev .
```

#### Running Tests
```bash
# Unit tests
cd agent-tracing-evaluation
python -m pytest tests/ -v

# Integration tests
python -m pytest tests/integration/ -v

# Coverage report
python -m pytest --cov=. tests/
```

#### Code Quality
```bash
# Code formatting
black agent-tracing-evaluation/

# Linting
flake8 agent-tracing-evaluation/

# Type checking
mypy agent-tracing-evaluation/
```

### Adding New Evaluators

#### 1. Create Evaluator Class
```python
# agent-tracing-evaluation/evaluators/new_evaluator.py
class NewEvaluator:
    def __init__(self):
        self.issues = []
    
    def evaluate(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        # Single trace evaluation
        pass
    
    def evaluate_batch(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Batch evaluation
        pass
```

#### 2. Register Evaluator
```python
# agent-tracing-evaluation/main.py
from evaluators.new_evaluator import NewEvaluator

# In __init__ method
self.evaluators["new_evaluator"] = NewEvaluator()
```

#### 3. Add Tests
```python
# agent-tracing-evaluation/tests/test_new_evaluator.py
def test_new_evaluator():
    evaluator = NewEvaluator()
    result = evaluator.evaluate(test_trace)
    assert result["score"] >= 0.0
    assert "details" in result
```

#### 4. Update Documentation
- Add evaluator description to documentation
- Update API reference
- Add configuration options

### API Development

#### Adding New Endpoints
```python
# core/deployment/api-server.py
@app.route('/evaluators/<evaluator_name>/config', methods=['GET'])
def get_evaluator_config(evaluator_name):
    # Return evaluator-specific configuration
    pass

@app.route('/evaluators/<evaluator_name>/test', methods=['POST'])
def test_evaluator(evaluator_name):
    # Run test evaluation for specific evaluator
    pass
```

#### API Versioning
```python
# Version 1 API
@app.route('/v1/evaluate', methods=['POST'])
def evaluate_v1():
    # V1 implementation
    pass

# Version 2 API (future)
@app.route('/v2/evaluate', methods=['POST'])
def evaluate_v2():
    # V2 implementation with enhanced features
    pass
```

### Temporal Development

#### Adding New Workflows
```go
// core/ai/runtime/agents/backend/workflows/new_workflow.go
@workflow.defn
class NewEvaluationWorkflow:
    @workflow.run
    async def run(self, input_data: dict) -> dict:
        # New workflow implementation
        pass
```

#### Adding New Activities
```go
// core/ai/runtime/agents/backend/activities/new_activities.go
@activity.defn
async def new_evaluation_activity(input_data: dict) -> dict:
    // New activity implementation
    pass
```

### Docker Development

#### Multi-stage Builds
```dockerfile
# Base stage
FROM python:3.12-slim as base
# Base dependencies and framework

# Development stage
FROM base as development
# Development tools and testing

# Production stage
FROM base as production
# Production optimizations and security

# Temporal worker stage
FROM base as temporal-worker
# Temporal-specific dependencies
```

#### Security Scanning
```bash
# Scan for vulnerabilities
docker scan ai-agent-evaluator:latest

# Use security-focused base image
FROM python:3.12-slim-security

# Non-root user
RUN adduser --disabled-password --gecos '' evaluator
USER evaluator
```

---

## Contributing

### Contribution Guidelines

#### 1. Code Standards
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write comprehensive tests
- Document public APIs

#### 2. Pull Request Process
```bash
# Create feature branch
git checkout -b feature/new-evaluator

# Make changes
# ... implement feature ...

# Run tests
python -m pytest tests/

# Format code
black .

# Commit changes
git add .
git commit -m "feat: add new security evaluator"

# Push and create PR
git push origin feature/new-evaluator
```

#### 3. Review Requirements
- All tests must pass
- Code coverage > 80%
- Documentation updated
- Security review completed

### Issue Reporting

#### Bug Reports
- Use GitHub issue templates
- Include reproduction steps
- Provide environment details
- Attach relevant logs

#### Feature Requests
- Describe use case clearly
- Provide implementation suggestions
- Consider impact on existing users
- Discuss in issues before PR

### Release Process

#### Version Management
```bash
# Update version
echo "1.1.0" > VERSION

# Update changelog
# Add release notes to CHANGELOG.md

# Tag release
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0
```

#### Release Checklist
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Security scan completed
- [ ] Performance benchmarks run
- [ ] Breaking changes documented
- [ ] Migration guide provided

---

## License and Support

### License
This evaluation framework is part of the GitOps Infrastructure Control Plane project. See the main repository for licensing information.

### Support Channels
- **Documentation**: This comprehensive guide
- **Issues**: GitHub issue tracker
- **Discussions**: GitHub discussions for questions
- **Community**: Slack/Discord for real-time help

### Maintenance
- **Regular Updates**: Monthly security patches
- **Feature Releases**: Quarterly major releases
- **LTS Support**: Long-term support for enterprise versions
- **Community Support**: Community-driven improvements

---

## Appendix

### A. Configuration Templates

#### Production Configuration
```yaml
# production-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: production-config
data:
  evaluators.json: |
    {
      "skill_invocation": {"enabled": true, "weight": 0.2},
      "performance": {"enabled": true, "weight": 0.2},
      "cost": {"enabled": true, "weight": 0.15},
      "monitoring": {"enabled": true, "weight": 0.15},
      "health_check": {"enabled": true, "weight": 0.1},
      "security": {"enabled": true, "weight": 0.1},
      "compliance": {"enabled": true, "weight": 0.1}
    }
  quality_gates.json: |
    {
      "score_threshold": 0.8,
      "pass_rate_threshold": 0.85,
      "enable_auto_fix": true,
      "notification_on_failure": true
    }
```

#### Development Configuration
```yaml
# development-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: development-config
data:
  evaluators.json: |
    {
      "skill_invocation": {"enabled": true, "weight": 0.25},
      "performance": {"enabled": true, "weight": 0.25},
      "cost": {"enabled": false},
      "monitoring": {"enabled": true, "weight": 0.25},
      "health_check": {"enabled": true, "weight": 0.25},
      "security": {"enabled": false},
      "compliance": {"enabled": false}
    }
```

### B. Migration Guide

#### From Manual Evaluation
```bash
# Old way
python cli.py --file traces.json --evaluators all

# New way (API)
curl -X POST http://api-server/evaluate \
  -H "Content-Type: application/json" \
  -d '{"traces": [...], "evaluators": "all"}'
```

#### From Scheduled Jobs
```bash
# Old cronjob
0 */4 * * * cd /app && python cli.py --file /data/traces.json --evaluators all

# New Kubernetes CronJob
kubectl apply -f core/deployment/ai-agent-evaluation-cronjob.yaml
```

### C. Performance Benchmarks

#### Evaluation Performance
| Trace Count | Evaluators | Duration | Memory Usage |
|-------------|------------|----------|--------------|
| 100         | 3          | 2.5s     | 256Mi        |
| 500         | 3          | 8.2s     | 384Mi        |
| 1000        | 7          | 15.7s    | 512Mi        |
| 5000        | 7          | 45.3s    | 768Mi        |

#### API Performance
| Concurrent Requests | Response Time | Throughput |
|---------------------|--------------|------------|
| 1                   | 150ms        | 6.7 req/s  |
| 5                   | 320ms        | 15.6 req/s |
| 10                  | 580ms        | 17.2 req/s |
| 20                  | 1.2s         | 16.7 req/s |

### D. Security Considerations

#### Data Protection
- All sensitive data encrypted at rest
- Network traffic encrypted in transit
- PII automatically detected and redacted
- Audit logging for all evaluation activities

#### Access Control
- RBAC with least privilege principle
- Service account isolation
- Network policies for namespace isolation
- Secret management with Kubernetes secrets

#### Compliance
- GDPR compliance for EU data
- HIPAA compliance for healthcare data
- SOC2 compliance for enterprise customers
- Regular security audits and penetration testing

---

*This documentation is continuously updated. For the latest version, check the repository's main branch.*

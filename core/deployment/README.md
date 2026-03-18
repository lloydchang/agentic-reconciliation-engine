# AI Agent Evaluation Framework - Background Deployment Options

This document describes three deployment options for running AI Agent Evaluators automatically in the background as containerized services in Kubernetes.

## 🚀 **Deployment Options Overview**

### **Option 1: Scheduled Kubernetes Jobs**
- **Purpose**: Automated periodic evaluations
- **Trigger**: Cron-based schedule (every 4 hours)
- **Use Case**: Regular health checks and compliance monitoring
- **Resources**: Minimal, runs only when scheduled

### **Option 2: API Server Deployment**
- **Purpose**: On-demand evaluation via REST API
- **Trigger**: HTTP requests to API endpoints
- **Use Case**: Interactive evaluation, integration with other systems
- **Resources**: Persistent service with 2 replicas

### **Option 3: Temporal Workflow Integration**
- **Purpose**: Event-driven evaluation orchestration
- **Trigger**: Temporal workflow events, trace ingestion
- **Use Case**: Complex multi-step evaluation workflows
- **Resources**: Temporal workers alongside existing AI agents

---

## 📋 **Prerequisites**

### **System Requirements**
- Kubernetes cluster (v1.20+)
- Docker registry access
- kubectl configured
- Optional: Temporal server (for Option 3)

### **Storage Requirements**
- PersistentVolume: 10Gi for trace data
- ConfigMaps: Evaluator configurations
- Secrets: API keys and credentials

### **Network Requirements**
- ClusterIP service for internal access
- Optional Ingress for external API access
- Temporal server connectivity (Option 3)

---

## 🛠 **Installation**

### **Quick Install (All Options)**
```bash
# Clone repository
git clone <repository-url>
cd gitops-infra-control-plane

# Deploy everything
./core/deployment/deploy-evaluation-framework.sh deploy
```

### **Custom Installation**
```bash
# Set environment variables
export DOCKER_REGISTRY=myregistry.com
export IMAGE_TAG=v1.0.0
export NAMESPACE=ai-evaluators

# Deploy specific options
./core/deployment/deploy-evaluation-framework.sh scheduled  # Option 1
./core/deployment/deploy-evaluation-framework.sh api        # Option 2
./core/deployment/deploy-evaluation-framework.sh temporal   # Option 3
```

---

## 🔧 **Option 1: Scheduled Kubernetes Jobs**

### **Architecture**
```
CronJob (every 4 hours) → Job → Pod → Evaluator → Results → Storage
```

### **Configuration**
```yaml
# core/deployment/ai-agent-evaluation-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: ai-agent-evaluation-cronjob
spec:
  schedule: "0 */4 * * *"  # Every 4 hours
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: evaluator
            image: ai-agent-evaluator:latest
            command: ["python", "cli.py"]
            args:
            - "--file", "/data/traces.json"
            - "--evaluators", "all"
            - "--format", "json"
```

### **Features**
- **Automatic Scheduling**: Runs every 4 hours by default
- **Quality Gates**: Fails jobs if thresholds not met
- **Resource Limits**: 512Mi memory, 500m CPU
- **Retry Policy**: Up to 3 retries on failure
- **Artifact Storage**: Results stored in PV and downloadable

### **Management**
```bash
# View scheduled jobs
kubectl get cronjobs -n ai-agents

# View job history
kubectl get jobs -n ai-agents

# Manually trigger a job
kubectl create job --from=cronjob/ai-agent-evaluation-cronjob manual-eval

# View job logs
kubectl logs job/<job-name> -n ai-agents
```

---

## 🖥 **Option 2: API Server Deployment**

### **Architecture**
```
Client → LoadBalancer → Service → Deployment (2 replicas) → Evaluator API
```

### **API Endpoints**
```bash
# Health check
GET /health

# List evaluators
GET /evaluators

# Start evaluation
POST /evaluate
{
  "traces": [...],
  "evaluators": ["skill_invocation", "performance"],
  "options": {"generate_visualizations": true}
}

# Upload and evaluate
POST /evaluate/upload
Content-Type: multipart/form-data
file: traces.json
evaluators: skill_invocation,performance,cost

# Check status
GET /evaluate/{evaluation_id}/status

# Get results
GET /evaluate/{evaluation_id}/results

# Get visualizations
GET /evaluate/{evaluation_id}/visualizations/{filename}

# List all evaluations
GET /evaluations?status=completed&limit=50

# System metrics
GET /metrics
```

### **Configuration**
```yaml
# core/deployment/ai-agent-evaluator-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-agent-evaluator-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ai-agent-evaluation
      component: evaluator-api
  template:
    spec:
      containers:
      - name: evaluator-api
        image: ai-agent-evaluator:latest
        command: ["gunicorn", "--bind", "0.0.0.0:5000", "api_server:app"]
        ports:
        - containerPort: 5000
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
```

### **Features**
- **RESTful API**: Full CRUD operations for evaluations
- **Async Processing**: Background evaluation with status tracking
- **File Upload**: Support for trace file uploads
- **Visualization Generation**: Automatic chart and report generation
- **Health Monitoring**: Liveness and readiness probes
- **Scalability**: 2 replicas with load balancing

### **Usage Examples**
```bash
# Port forward to access API
kubectl port-forward service/ai-agent-evaluator-service 8080:80 -n ai-agents

# Start evaluation via curl
curl -X POST http://localhost:8080/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "traces": [{"id": "trace-1", "timestamp": 1234567890}],
    "evaluators": ["skill_invocation", "performance"]
  }'

# Upload file for evaluation
curl -X POST http://localhost:8080/evaluate/upload \
  -F "file=@traces.json" \
  -F "evaluators=skill_invocation,performance,cost"

# Check evaluation status
curl http://localhost:8080/evaluate/eval-id/status
```

---

## ⏰ **Option 3: Temporal Workflow Integration**

### **Architecture**
```
Event Trigger → Temporal Workflow → Activities → Evaluator → Results → Notifications
```

### **Workflow Types**
1. **EvaluationWorkflow**: Standard evaluation with all steps
2. **ScheduledEvaluationWorkflow**: Hourly automated evaluations
3. **EventDrivenEvaluationWorkflow**: Triggered by system events

### **Configuration**
```go
// core/ai/runtime/agents/backend/workflows/evaluation_workflow.go
@workflow.defn
class EvaluationWorkflow:
    @workflow.run
    async def run(self, input_data: dict) -> dict:
        # Step 1: Prepare environment
        await workflow.execute_activity(prepare_evaluation_environment, input_data)
        
        # Step 2: Generate traces
        await workflow.execute_activity(generate_sample_traces, input_data)
        
        # Step 3: Run evaluation
        evaluation_result = await workflow.execute_activity(run_evaluation_activity, input_data)
        
        # Step 4: Generate visualizations
        viz_result = await workflow.execute_activity(generate_visualizations, input_data)
        
        # Step 5: Check quality gates
        quality_gate_result = await workflow.execute_activity(check_quality_gates, input_data)
        
        # Step 6: Send notifications
        if email := input_data.get("notification_email"):
            await workflow.execute_activity(send_evaluation_notification, email, notification_data)
```

### **Features**
- **Event-Driven**: Triggered by trace ingestion, system events
- **Workflow Orchestration**: Complex multi-step evaluation pipelines
- **Durable Execution**: Automatic retries and error handling
- **Scalable Workers**: Multiple worker instances
- **Quality Gates**: Automated compliance checking
- **Notifications**: Email alerts on completion/failure

### **Integration**
```go
// Trigger evaluation from Go code
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

---

## 📊 **Monitoring & Observability**

### **Metrics Available**
- Evaluation counts and success rates
- Average evaluation scores
- Processing times and throughput
- Error rates and failure patterns
- Resource utilization

### **Logging**
- Structured JSON logs
- Correlation IDs for traceability
- Evaluation-specific metadata
- Error details and stack traces

### **Alerting**
- Quality gate failures
- High error rates
- Resource exhaustion
- Service availability

### **Grafana Dashboards**
- Evaluation overview
- Performance metrics
- Error analysis
- Compliance tracking

---

## 🔒 **Security & Compliance**

### **RBAC**
- Dedicated service account
- Minimal required permissions
- ClusterRole for pod/service access
- Secret access for credentials

### **Network Policies**
- Namespace isolation
- Service-to-service communication
- Ingress restrictions
- Egress filtering

### **Data Protection**
- Encrypted storage
- Secure credential management
- Audit logging
- PII detection and redaction

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Pod Failures**
```bash
# Check pod status
kubectl get pods -n ai-agents

# View pod logs
kubectl logs -f deployment/ai-agent-evaluator-api -n ai-agents

# Describe pod for events
kubectl describe pod <pod-name> -n ai-agents
```

#### **API Issues**
```bash
# Check service endpoints
kubectl get endpoints ai-agent-evaluator-service -n ai-agents

# Test service connectivity
kubectl run test-pod --rm -i --tty --image=curlimages/curl \
  -- curl -s http://ai-agent-evaluator-service/health

# Check network policies
kubectl get networkpolicies -n ai-agents
```

#### **Temporal Issues**
```bash
# Check Temporal connectivity
kubectl logs deployment/temporal-evaluation-worker -n ai-agents | grep "temporal"

# Check workflow history
kubectl exec deployment/temporal -n temporal -- temporal workflow list

# View task queue
kubectl exec deployment/temporal -n temporal -- temporal task-queue describe ai-agent-evaluation
```

#### **Storage Issues**
```bash
# Check PVC status
kubectl get pvc -n ai-agents

# Check storage class
kubectl get storageclass

# View volume mounts
kubectl describe pod <pod-name> -n ai-agents | grep -A 10 "Mounts"
```

### **Performance Tuning**

#### **Resource Limits**
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "200m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

#### **Scaling**
```bash
# Scale API server
kubectl scale deployment ai-agent-evaluator-api --replicas=3 -n ai-agents

# Scale Temporal workers
kubectl scale deployment temporal-evaluation-worker --replicas=4 -n ai-agents
```

---

## 📚 **API Reference**

### **Response Formats**

#### **Evaluation Status**
```json
{
  "id": "eval-uuid",
  "status": "running|completed|failed",
  "created_at": "2024-01-01T00:00:00Z",
  "traces_count": 100,
  "evaluators": ["skill_invocation", "performance"],
  "options": {...}
}
```

#### **Evaluation Results**
```json
{
  "id": "eval-uuid",
  "status": "completed",
  "completed_at": "2024-01-01T00:05:00Z",
  "result": {
    "summary": {
      "overall_score": 0.85,
      "overall_pass_rate": 0.92,
      "total_evaluations": 100
    },
    "evaluator_results": {...},
    "aggregate_metrics": {...}
  },
  "visualizations": {
    "performance_dashboard": "/visualizations/eval-id/performance_dashboard.png",
    "trend_analysis": "/visualizations/eval-id/trend_analysis.png"
  }
}
```

---

## 🔄 **Upgrade & Maintenance**

### **Version Updates**
```bash
# Update image tag
export IMAGE_TAG=v1.1.0

# Redeploy with new version
./core/deployment/deploy-evaluation-framework.sh deploy
```

### **Rolling Updates**
```bash
# Update specific deployment
kubectl set image deployment/ai-agent-evaluator-api \
  evaluator-api=ai-agent-evaluator:v1.1.0 -n ai-agents

# Monitor rollout status
kubectl rollout status deployment/ai-agent-evaluator-api -n ai-agents
```

### **Backup & Recovery**
```bash
# Backup configuration
kubectl get all -n ai-agents -o yaml > backup.yaml

# Restore from backup
kubectl apply -f backup.yaml
```

---

## 📞 **Support**

### **Getting Help**
- Check logs: `kubectl logs -f deployment/<name> -n ai-agents`
- Review events: `kubectl get events -n ai-agents --sort-by=.metadata.creationTimestamp`
- Test connectivity: `kubectl run test-pod --rm -i --image=curlimages/curl -- curl http://service-name/health`

### **Known Limitations**
- Maximum file size: 100MB for API uploads
- Concurrent evaluations: Limited by available resources
- Temporal dependency: Option 3 requires Temporal server
- Storage: Limited by PVC size (default 10Gi)

---

## 🎯 **Best Practices**

1. **Resource Management**: Monitor resource usage and adjust limits
2. **Security**: Regularly update images and scan for vulnerabilities
3. **Monitoring**: Set up alerts for quality gate failures
4. **Backup**: Regular backup of evaluation results and configurations
5. **Testing**: Test all evaluation scenarios before production deployment
6. **Documentation**: Keep evaluation criteria and thresholds documented
7. **Version Control**: Track changes to evaluation configurations in Git

---

## 📄 **License**

This evaluation framework is part of the GitOps Infrastructure Control Plane project. See the main repository for licensing information.

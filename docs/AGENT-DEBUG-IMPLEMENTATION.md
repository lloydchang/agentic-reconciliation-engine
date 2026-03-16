# AI Debugging Implementation Guide

## Overview

This implementation guide provides detailed instructions for integrating the AI debugging system into your existing infrastructure. It covers deployment patterns, configuration management, and best practices for production use.

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Agents     │    │  Temporal       │    │   Kubernetes    │
│   (Go Workers)  │◄──►│   Workflows     │◄──►│   Cluster       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ AI Debugger     │
                    │ (Python CLI)    │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Monitoring      │
                    │ System          │
                    └─────────────────┘
```

### Data Flow

1. **Agents** execute skills and report metrics
2. **Temporal** orchestrates workflows and tracks execution
3. **Kubernetes** provides infrastructure and scheduling
4. **AI Debugger** analyzes logs, metrics, and system state
5. **Monitoring System** collects and stores telemetry data

## 🚀 Deployment Strategies

### 1. Standalone Deployment

#### Requirements
- Python 3.8+
- kubectl configured
- Access to Kubernetes API
- Network connectivity to monitoring endpoints

#### Deployment Steps
```bash
# 1. Clone the repository
git clone https://github.com/your-org/gitops-infra-control-plane.git
cd gitops-infra-control-plane

# 2. Navigate to debugger scripts
cd .agents/debug/scripts

# 3. Install dependencies
pip install -r requirements.txt

# 4. Test basic functionality
python main.py --help
./quick_debug.sh --help

# 5. Run initial system check
python main.py debug --target-component all --issue-type general --time-range 1h
```

### 2. Kubernetes Deployment

#### Deployment Manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-debugger
  namespace: temporal
  labels:
    app: ai-debugger
    component: debugging
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ai-debugger
  template:
    metadata:
      labels:
        app: ai-debugger
        component: debugging
    spec:
      serviceAccountName: ai-debugger-sa
      containers:
      - name: debugger
        image: your-registry/ai-debugger:latest
        imagePullPolicy: Always
        command: ["python", "main.py"]
        args: ["serve", "--port", "8080"]
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: DEBUG_NAMESPACE
          value: "temporal"
        - name: DEBUG_LOG_LEVEL
          value: "info"
        - name: DEBUG_AUTO_FIX
          value: "false"
        - name: KUBECONFIG
          value: "/etc/kubernetes/config"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        volumeMounts:
        - name: kubeconfig
          mountPath: /etc/kubernetes/config
          readOnly: true
        - name: debug-config
          mountPath: /etc/debug/config
          readOnly: true
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: kubeconfig
        secret:
          secretName: kubeconfig-secret
      - name: debug-config
        configMap:
          name: debug-config
---
apiVersion: v1
kind: Service
metadata:
  name: ai-debugger-service
  namespace: temporal
  labels:
    app: ai-debugger
spec:
  selector:
    app: ai-debugger
  ports:
  - port: 8080
    targetPort: 8080
    name: http
  type: ClusterIP
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ai-debugger-sa
  namespace: temporal
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: ai-debugger-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "endpoints", "events"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/log", "pods/exec"]
  verbs: ["get", "list"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: ai-debugger-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: ai-debugger-role
subjects:
- kind: ServiceAccount
  name: ai-debugger-sa
  namespace: temporal
```

#### Service Configuration
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: debug-config
  namespace: temporal
data:
  config.yaml: |
    debug:
      namespace: temporal
      log_level: info
      auto_fix: false
      max_retries: 3
    
    monitoring:
      enabled: true
      interval: 30
      retention: 7d
    
    thresholds:
      error_rate: 0.1
      timeout_rate: 0.05
      restart_count: 5
      memory_usage: 0.8
      cpu_usage: 0.8
    
    components:
      agents:
        enabled: true
        auto_restart: true
        resource_checks: true
      workflows:
        enabled: true
        timeout_checks: true
        queue_monitoring: true
      infrastructure:
        enabled: true
        node_health: true
        storage_checks: true
```

### 3. Sidecar Deployment

#### Sidecar Configuration
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: temporal-worker-with-debugger
  namespace: temporal
spec:
  replicas: 1
  selector:
    matchLabels:
      app: temporal-worker
  template:
    metadata:
      labels:
        app: temporal-worker
    spec:
      containers:
      - name: temporal-worker
        image: temporalio/worker:latest
        env:
        - name: TEMPORAL_HOST
          value: "temporal-frontend"
        - name: TEMPORAL_PORT
          value: "7233"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      - name: ai-debugger
        image: your-registry/ai-debugger:latest
        command: ["python", "main.py"]
        args: ["monitor", "--components", "agents", "--interval", "60"]
        env:
        - name: DEBUG_NAMESPACE
          value: "temporal"
        - name: DEBUG_TARGET_POD
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        resources:
          requests:
            memory: "128Mi"
            cpu: "50m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        volumeMounts:
        - name: shared-logs
          mountPath: /var/log/app
      volumes:
      - name: shared-logs
        emptyDir: {}
```

## ⚙️ Configuration Management

### Environment Variables

#### Core Configuration
```bash
# Debug Configuration
export DEBUG_NAMESPACE=temporal
export DEBUG_LOG_LEVEL=info
export DEBUG_AUTO_FIX=false
export DEBUG_MAX_RETRIES=3

# API Configuration
export DEBUG_API_HOST=0.0.0.0
export DEBUG_API_PORT=8080
export DEBUG_API_TLS=false

# Kubernetes Configuration
export KUBECONFIG=/path/to/kubeconfig
export DEBUG_KUBE_CONTEXT=current-context

# Monitoring Configuration
export DEBUG_METRICS_ENABLED=true
export DEBUG_ALERTS_ENABLED=true
export DEBUG_WEBHOOK_URL=https://hooks.slack.com/your-webhook
```

#### Production Configuration
```bash
# Production settings
export DEBUG_LOG_LEVEL=warn
export DEBUG_AUTO_FIX=true
export DEBUG_DRY_RUN=false

# Security settings
export DEBUG_API_TLS=true
export DEBUG_API_CERT_FILE=/etc/tls/cert.pem
export DEBUG_API_KEY_FILE=/etc/tls/key.pem

# Performance settings
export DEBUG_WORKERS=4
export DEBUG_TIMEOUT=300
export DEBUG_BATCH_SIZE=100
```

### Configuration Files

#### YAML Configuration
```yaml
# /etc/debug/config.yaml
debug:
  namespace: temporal
  log_level: info
  auto_fix: false
  dry_run: false
  max_retries: 3
  
api:
  host: 0.0.0.0
  port: 8080
  tls: false
  workers: 4
  
monitoring:
  enabled: true
  interval: 30
  retention: 7d
  metrics_port: 9090
  
kubernetes:
  kubeconfig: /etc/kubernetes/config
  context: current-context
  timeout: 30
  
temporal:
  host: temporal-frontend.temporal.svc.cluster.local
  port: 7233
  namespace: default
  
thresholds:
  error_rate: 0.1
  timeout_rate: 0.05
  restart_count: 5
  memory_usage: 0.8
  cpu_usage: 0.8
  
auto_fix:
  enabled: false
  max_retries: 3
  require_approval: false
  approval_timeout: 300
  
components:
  agents:
    enabled: true
    auto_restart: true
    resource_checks: true
    log_analysis: true
    patterns:
      - "ERROR.*"
      - "FATAL.*"
      - "Exception.*"
      
  workflows:
    enabled: true
    timeout_checks: true
    queue_monitoring: true
    history_analysis: true
    timeout_threshold: 3600
    
  infrastructure:
    enabled: true
    node_health: true
    storage_checks: true
    network_checks: true
    event_analysis: true
    node_conditions:
      - "Ready"
      - "MemoryPressure"
      - "DiskPressure"
      - "PIDPressure"
```

#### JSON Configuration
```json
{
  "debug": {
    "namespace": "temporal",
    "log_level": "info",
    "auto_fix": false,
    "dry_run": false,
    "max_retries": 3
  },
  "api": {
    "host": "0.0.0.0",
    "port": 8080,
    "tls": false,
    "workers": 4
  },
  "monitoring": {
    "enabled": true,
    "interval": 30,
    "retention": "7d",
    "metrics_port": 9090
  },
  "thresholds": {
    "error_rate": 0.1,
    "timeout_rate": 0.05,
    "restart_count": 5,
    "memory_usage": 0.8,
    "cpu_usage": 0.8
  },
  "components": {
    "agents": {
      "enabled": true,
      "auto_restart": true,
      "resource_checks": true,
      "log_analysis": true
    },
    "workflows": {
      "enabled": true,
      "timeout_checks": true,
      "queue_monitoring": true,
      "history_analysis": true
    },
    "infrastructure": {
      "enabled": true,
      "node_health": true,
      "storage_checks": true,
      "network_checks": true
    }
  }
}
```

## 🔧 Integration Patterns

### 1. Temporal Integration

#### Activity Registration
```go
// Register debugging activities
func init() {
    // Register debugging activities
    activity.RegisterWithOptions(DebugSystemActivity, activity.RegisterOptions{
        Name: "debug_system_activity",
    })
    
    activity.RegisterWithOptions(RecordDebugMetricsActivity, activity.RegisterOptions{
        Name: "record_debug_metrics_activity",
    })
    
    activity.RegisterWithOptions(ApplyAutoFixActivity, activity.RegisterOptions{
        Name: "apply_auto_fix_activity",
    })
}

// Debug system activity
func DebugSystemActivity(ctx context.Context, request DebugRequest) (*DebugResult, error) {
    logger := activity.GetLogger(ctx)
    logger.Info("Starting system debug", "component", request.Component)
    
    // Create debugger instance
    debugger := NewAISystemDebugger(request.Namespace, request.Verbose)
    
    // Run debugging
    findings := debugger.debugComponent(request.Component, request.IssueType, request.TimeRange)
    
    // Apply auto-fixes if requested
    if request.AutoFix {
        fixesApplied := debugger.applyAutoFixes(findings)
        logger.Info("Auto-fixes applied", "count", fixesApplied)
    }
    
    return &DebugResult{
        Findings: findings,
        Success:  true,
    }, nil
}
```

#### Workflow Integration
```go
// Enhanced workflow with debugging
func DebuggableWorkflow(ctx workflow.Context, request WorkflowRequest) (*WorkflowResult, error) {
    logger := workflow.GetLogger(ctx)
    
    // Set up debug options
    debugOptions := workflow.ActivityOptions{
        ActivityID:        "debug-system-" + workflow.GetInfo(ctx).WorkflowExecution.ID,
        StartToCloseTimeout: time.Minute * 10,
        RetryPolicy: &temporal.RetryPolicy{
            InitialInterval:    time.Second * 10,
            BackoffCoefficient: 2.0,
            MaximumInterval:    time.Minute * 1,
            MaximumAttempts:    3,
        },
    }
    
    // Debug before execution
    debugRequest := DebugRequest{
        Component:   "workflows",
        IssueType:   "general",
        TimeRange:   "1h",
        Namespace:   "temporal",
        AutoFix:     false,
        Verbose:     true,
    }
    
    var debugResult DebugResult
    err := workflow.ExecuteActivity(ctx, debugOptions, DebugSystemActivity, debugRequest).Get(ctx, &debugResult)
    if err != nil {
        logger.Warn("Debug activity failed", "error", err)
    }
    
    // Execute main workflow
    result, err := ExecuteMainWorkflow(ctx, request)
    if err != nil {
        // Debug on failure
        failureDebugRequest := DebugRequest{
            Component:   "workflows",
            IssueType:   "errors",
            TimeRange:   "30m",
            Namespace:   "temporal",
            AutoFix:     true,
            Verbose:     true,
        }
        
        var failureDebugResult DebugResult
        workflow.ExecuteActivity(ctx, debugOptions, DebugSystemActivity, failureDebugRequest).Get(ctx, &failureDebugResult)
        
        return nil, err
    }
    
    return result, nil
}
```

### 2. Kubernetes Operator Integration

#### Custom Resource Definition
```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: debugsessions.debug.ai
spec:
  group: debug.ai
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              component:
                type: string
                enum: ["agents", "workflows", "infrastructure", "all"]
              issueType:
                type: string
                enum: ["performance", "errors", "timeouts", "connectivity", "resource", "behavior", "general"]
              timeRange:
                type: string
                pattern: "^\\d+[mhd]$"
              namespace:
                type: string
                default: "temporal"
              autoFix:
                type: boolean
                default: false
          status:
            type: object
            properties:
              phase:
                type: string
                enum: ["Pending", "Running", "Completed", "Failed"]
              findings:
                type: array
                items:
                  type: object
              startTime:
                type: string
                format: date-time
              completionTime:
                type: string
                format: date-time
  scope: Namespaced
  names:
    plural: debugsessions
    singular: debugsession
    kind: DebugSession
    shortNames:
    - debug
```

#### Controller Implementation
```go
// DebugSession controller
type DebugSessionReconciler struct {
    client.Client
    Scheme     *runtime.Scheme
    Debugger   *AISystemDebugger
    Recorder   record.EventRecorder
}

func (r *DebugSessionReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    // Get the DebugSession
    var debugsession debugv1.DebugSession
    if err := r.Get(ctx, req.NamespacedName, &debugsession); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }
    
    // Update status to Running
    debugsession.Status.Phase = "Running"
    debugsession.Status.StartTime = &metav1.Time{Time: time.Now()}
    r.Status().Update(ctx, &debugsession)
    
    // Run debugging
    findings := r.Debugger.debugComponent(
        debugsession.Spec.Component,
        debugsession.Spec.IssueType,
        debugsession.Spec.TimeRange,
    )
    
    // Apply auto-fixes if requested
    if debugsession.Spec.AutoFix {
        fixesApplied := r.Debugger.applyAutoFixes(findings)
        r.Recorder.Eventf(&debugsession, "Normal", "AutoFixApplied", "Applied %d auto-fixes", fixesApplied)
    }
    
    // Update status with results
    debugsession.Status.Phase = "Completed"
    debugsession.Status.CompletionTime = &metav1.Time{Time: time.Now()}
    debugsession.Status.Findings = convertFindings(findings)
    r.Status().Update(ctx, &debugsession)
    
    return ctrl.Result{}, nil
}
```

### 3. Monitoring Integration

#### Prometheus Metrics
```go
// Debug metrics
var (
    debugSessionsTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "debug_sessions_total",
            Help: "Total number of debug sessions",
        },
        []string{"component", "issue_type", "namespace"},
    )
    
    debugFindingsTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "debug_findings_total",
            Help: "Total number of debug findings",
        },
        []string{"component", "severity", "issue_type"},
    )
    
    debugDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "debug_duration_seconds",
            Help:    "Time spent debugging",
            Buckets: prometheus.DefBuckets,
        },
        []string{"component", "issue_type"},
    )
    
    autoFixesApplied = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "debug_auto_fixes_applied_total",
            Help: "Total number of auto-fixes applied",
        },
        []string{"component", "fix_type"},
    )
)

func init() {
    prometheus.MustRegister(debugSessionsTotal)
    prometheus.MustRegister(debugFindingsTotal)
    prometheus.MustRegister(debugDuration)
    prometheus.MustRegister(autoFixesApplied)
}
```

#### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "AI System Debugging",
    "panels": [
      {
        "title": "Debug Sessions",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(debug_sessions_total[5m])) by (component)",
            "legendFormat": "{{component}}"
          }
        ]
      },
      {
        "title": "Debug Findings",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(debug_findings_total[5m])) by (severity)",
            "legendFormat": "{{severity}}"
          }
        ]
      },
      {
        "title": "Debug Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(debug_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(debug_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "title": "Auto-Fixes Applied",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(debug_auto_fixes_applied_total[5m])) by (component)",
            "legendFormat": "{{component}}"
          }
        ]
      }
    ]
  }
}
```

## 🚀 Production Best Practices

### 1. Security

#### RBAC Configuration
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: temporal
  name: ai-debugger-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "endpoints", "events", "configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/log", "pods/exec"]
  verbs: ["get", "list"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "daemonsets"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
```

#### Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-debugger-netpol
  namespace: temporal
spec:
  podSelector:
    matchLabels:
      app: ai-debugger
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: temporal
    - namespaceSelector:
        matchLabels:
          name: monitoring
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: temporal
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
```

### 2. Performance Optimization

#### Resource Management
```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: ai-debugger-limits
  namespace: temporal
spec:
  limits:
  - default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"
      memory: "256Mi"
    type: Container
```

#### Horizontal Pod Autoscaling
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-debugger-hpa
  namespace: temporal
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-debugger
  minReplicas: 1
  maxReplicas: 5
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
```

### 3. Reliability

#### Health Checks
```yaml
# Liveness and readiness probes
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

#### Pod Disruption Budget
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: ai-debugger-pdb
  namespace: temporal
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: ai-debugger
```

### 4. Monitoring and Alerting

#### Alert Rules
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: ai-debugger-alerts
  namespace: temporal
spec:
  groups:
  - name: ai-debugger
    rules:
    - alert: DebugSessionHighFailureRate
      expr: rate(debug_sessions_total{status="failed"}[5m]) / rate(debug_sessions_total[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "High debug session failure rate"
        description: "Debug session failure rate is {{ $value | humanizePercentage }}"
    
    - alert: DebugSessionHighLatency
      expr: histogram_quantile(0.95, rate(debug_duration_seconds_bucket[5m])) > 300
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High debug session latency"
        description: "95th percentile debug duration is {{ $value }}s"
    
    - alert: DebuggerDown
      expr: up{job="ai-debugger"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "AI debugger is down"
        description: "AI debugger has been down for more than 1 minute"
```

## 📋 Troubleshooting

### Common Issues

#### 1. Permission Denied
```bash
# Symptoms
Error: forbidden: User "system:serviceaccount:temporal:ai-debugger" cannot list pods

# Solution
kubectl apply -f rbac.yaml
kubectl describe clusterrole ai-debugger-role
kubectl describe clusterrolebinding ai-debugger-binding
```

#### 2. Network Connectivity
```bash
# Symptoms
Error: connection refused to temporal-frontend:7233

# Solution
kubectl get svc -n temporal
kubectl get endpoints -n temporal
kubectl run test-pod --image=busybox --rm -it -- nslookup temporal-frontend.temporal.svc.cluster.local
```

#### 3. Resource Limits
```bash
# Symptoms
Error: pod "ai-debugger-xyz" exceeded memory limits

# Solution
kubectl describe pod ai-debugger-xyz -n temporal
kubectl top pod ai-debugger-xyz -n temporal
kubectl patch deployment ai-debugger -n temporal -p '{"spec":{"template":{"spec":{"containers":[{"name":"debugger","resources":{"limits":{"memory":"1Gi"}}}]}}}}'
```

#### 4. Configuration Issues
```bash
# Symptoms
Error: invalid configuration file

# Solution
kubectl get configmap debug-config -n temporal -o yaml
kubectl exec -it deployment/ai-debugger -n temporal -- cat /etc/debug/config.yaml
```

### Debug Commands

#### Check Debugger Status
```bash
# Check pod status
kubectl get pods -n temporal -l app=ai-debugger

# Check logs
kubectl logs -n temporal deployment/ai-debugger

# Check configuration
kubectl get configmap debug-config -n temporal -o yaml

# Check permissions
kubectl auth can-i get pods --as=system:serviceaccount:temporal:ai-debugger -n temporal
```

#### Test Functionality
```bash
# Test API endpoint
kubectl port-forward -n temporal svc/ai-debugger-service 8080:8080
curl http://localhost:8080/health

# Test debugging
curl -X POST http://localhost:8080/api/v1/debug \
  -H "Content-Type: application/json" \
  -d '{"target_component":"agents","issue_type":"errors","time_range":"1h"}'
```

## 🔄 Maintenance

### Regular Tasks

#### 1. Log Rotation
```bash
# Set up log rotation
kubectl create configmap logrotate-config --from-file=logrotate.conf -n temporal
kubectl patch deployment ai-debugger -n temporal -p '{"spec":{"template":{"spec":{"volumes":[{"name":"logrotate-config","configMap":{"name":"logrotate-config"}}],"containers":[{"name":"debugger","volumeMounts":[{"name":"logrotate-config","mountPath":"/etc/logrotate.d"}},{"name":"logs","mountPath":"/var/log/debug"}]},{"name":"logrotate","image":"linuxserver/logrotate","command":["/bin/sh","-c","while true; do logrotate /etc/logrotate.d/debug; sleep 3600; done"],"volumeMounts":[{"name":"logrotate-config","mountPath":"/etc/logrotate.d"},{"name":"logs","mountPath":"/var/log/debug"}]}]}}}}'
```

#### 2. Configuration Updates
```bash
# Update configuration
kubectl edit configmap debug-config -n temporal

# Restart to apply changes
kubectl rollout restart deployment ai-debugger -n temporal
```

#### 3. Performance Monitoring
```bash
# Monitor resource usage
kubectl top pods -n temporal -l app=ai-debugger

# Check metrics
curl http://localhost:8080/metrics | grep debug_
```

### Backup and Recovery

#### Configuration Backup
```bash
# Backup configuration
kubectl get configmap debug-config -n temporal -o yaml > debug-config-backup.yaml
kubectl get deployment ai-debugger -n temporal -o yaml > ai-debugger-deployment-backup.yaml
kubectl get service ai-debugger-service -n temporal -o yaml > ai-debugger-service-backup.yaml
```

#### Recovery Procedures
```bash
# Restore from backup
kubectl apply -f debug-config-backup.yaml
kubectl apply -f ai-debugger-deployment-backup.yaml
kubectl apply -f ai-debugger-service-backup.yaml
```

---

**Last Updated**: 2026-03-16  
**Version**: 1.0.0  
**Maintainer**: Cloud AI Agents Team

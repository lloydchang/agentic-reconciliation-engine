# Qwen LLM Integration with K8sGPT and Flux

## Overview

This guide covers the integration of Qwen LLM with K8sGPT and Flux CD for intelligent Kubernetes operations and automated remediation.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Kubernetes    │───▶│    K8sGPT        │───▶│   Qwen LLM      │
│    Events       │    │   Collector      │    │   Inference     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Problem       │    │   Analysis       │    │   Solution      │
│   Detection     │    │   Processing     │    │   Generation    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Flux Actions  │◀───│   Webhook        │◀───│   Auto-fix      │
│   (Apply Fix)   │    │   Integration    │    │   Commands      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### One-Command Setup

```bash
# Deploy Qwen + K8sGPT + Flux integration
./scripts/qwen-flux-setup.sh --auto-configure --monitoring
```

### Manual Setup

```bash
# 1. Deploy Qwen LLM service
kubectl apply -f ./gitops/qwen-system/

# 2. Deploy K8sGPT with Qwen backend
kubectl apply -f ./gitops/flux-system/k8sgpt-qwen.yaml

# 3. Configure Flux webhook integration
kubectl apply -f ./gitops/flux-system/qwen-webhook.yaml
```

## 📋 Prerequisites

### System Requirements
- **Kubernetes**: v1.24+ with at least 4GB RAM available
- **Storage**: 8GB+ for Qwen model storage
- **Network**: Access to model repositories or local model files
- **Permissions**: Cluster admin for deployment

### Model Options

#### Option 1: Local Qwen Model (Recommended)
```bash
# Download Qwen 2.5 7B model
wget https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/resolve/main/qwen2.5-7b-instruct.gguf

# Store in persistent volume
kubectl create namespace qwen-system
kubectl apply -f ./gitops/qwen-system/pvc.yaml
```

#### Option 2: Remote Qwen API
```bash
# Use cloud-hosted Qwen service
export QWEN_API_URL="https://api.qwen.ai/v1/chat/completions"
export QWEN_API_KEY="your-api-key"
```

#### Option 3: Ollama Integration
```bash
# Deploy Ollama with Qwen
helm repo add ollama https://ollama.github.io/helm
helm install ollama ollama/ollama \
  --namespace ollama-system \
  --create-namespace \
  --set ollama.models=qwen2.5:7b
```

## 🔧 Configuration

### Qwen Service Configuration

```yaml
# gitops/qwen-system/qwen-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qwen-llm
  namespace: qwen-system
  labels:
    app: qwen-llm
spec:
  replicas: 1
  selector:
    matchLabels:
      app: qwen-llm
  template:
    metadata:
      labels:
        app: qwen-llm
    spec:
      containers:
      - name: qwen
        image: qwen/qwen2.5:7b-instruct
        ports:
        - containerPort: 8000
          name: http
        resources:
          requests:
            cpu: 1000m
            memory: 4Gi
          limits:
            cpu: 2000m
            memory: 8Gi
        env:
        - name: MODEL_PATH
          value: "/models/qwen2.5-7b-instruct.gguf"
        - name: HOST
          value: "0.0.0.0"
        - name: PORT
          value: "8000"
        volumeMounts:
        - name: model-volume
          mountPath: /models
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
      volumes:
      - name: model-volume
        persistentVolumeClaim:
          claimName: qwen-model-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: qwen-llm
  namespace: qwen-system
  labels:
    app: qwen-llm
spec:
  selector:
    app: qwen-llm
  ports:
  - port: 8000
    targetPort: 8000
    name: http
  type: ClusterIP
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: qwen-model-pvc
  namespace: qwen-system
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd
```

### K8sGPT Configuration

```yaml
# gitops/flux-system/k8sgpt-qwen.yaml
apiVersion: core.k8sgpt.ai/v1alpha1
kind: K8sGPT
metadata:
  name: k8sgpt-qwen
  namespace: flux-system
  labels:
    app.kubernetes.io/name: k8sgpt
    app.kubernetes.io/component: qwen-integration
spec:
  model: qwen
  backend: local
  noCache: false
  version: "v1.0.0"
  secret: qwen-connection-secret
  sink:
    type: webhook
    webhook:
      endpoint: http://flux-webhook.flux-system.svc.cluster.local/webhook
      timeout: 30s
      maxRetries: 3
  filters:
    - Ingress
    - Service
    - Deployment
    - StatefulSet
    - DaemonSet
    - Pod
  exclude:
    - kube-system
    - flux-system
    - qwen-system
  processors:
    - name: qwen-analyzer
      type: ai
      config:
        temperature: 0.7
        maxTokens: 2048
        systemPrompt: |
          You are an expert Kubernetes engineer. Analyze the provided Kubernetes resources
          and identify potential issues, security vulnerabilities, or optimization opportunities.
          Provide specific, actionable recommendations with YAML examples when applicable.
          Focus on production readiness and best practices.
---
apiVersion: v1
kind: Secret
metadata:
  name: qwen-connection-secret
  namespace: flux-system
type: Opaque
stringData:
  model: "qwen2.5:7b"
  apiUrl: "http://qwen-llm.qwen-system.svc.cluster.local:8000"
  apiKey: ""
  temperature: "0.7"
  maxTokens: "2048"
  systemPrompt: |
    You are an expert Kubernetes engineer. Analyze the provided Kubernetes resources
    and identify potential issues, security vulnerabilities, or optimization opportunities.
    Provide specific, actionable recommendations with YAML examples when applicable.
    Focus on production readiness and best practices.
```

### Flux Webhook Integration

```yaml
# gitops/flux-system/qwen-webhook.yaml
apiVersion: v1
kind: Service
metadata:
  name: flux-webhook
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-webhook
spec:
  selector:
    app: flux-webhook
  ports:
  - port: 80
    targetPort: 8080
    name: http
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flux-webhook
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-webhook
spec:
  replicas: 1
  selector:
    matchLabels:
      app: flux-webhook
  template:
    metadata:
      labels:
        app: flux-webhook
    spec:
      containers:
      - name: webhook
        image: ghcr.io/your-org/flux-qwen-webhook:latest
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: PORT
          value: "8080"
        - name: FLUX_WEBHOOK_SECRET
          valueFrom:
            secretKeyRef:
              name: webhook-secret
              key: token
        - name: GIT_REPO_URL
          value: "https://github.com/your-org/agentic-reconciliation-engine"
        - name: GIT_BRANCH
          value: "main"
        - name: AUTO_FIX_ENABLED
          value: "true"
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 200m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Secret
metadata:
  name: webhook-secret
  namespace: flux-system
type: Opaque
stringData:
  token: "$(openssl rand -hex 32)"
```

## 🤖 Webhook Implementation

### Webhook Server Code

```go
// cmd/webhook/main.go
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "os"
    "time"

    "github.com/go-git/go-git/v5"
    "github.com/go-git/go-git/v5/plumbing"
    "github.com/go-git/go-git/v5/plumbing/object"
    "k8s.io/client-go/kubernetes"
    "k8s.io/client-go/rest"
)

type K8sGPTAnalysis struct {
    Type        string                 `json:"type"`
    Timestamp   time.Time              `json:"timestamp"`
    Namespace   string                 `json:"namespace"`
    Resource    string                 `json:"resource"`
    Issues      []K8sGPTIssue          `json:"issues"`
    Suggestions []K8sGPTSuggestion     `json:"suggestions"`
    AutoFixes   []K8sGPTAutoFix        `json:"autofixes"`
}

type K8sGPTIssue struct {
    Severity    string `json:"severity"`
    Category    string `json:"category"`
    Description string `json:"description"`
    Resource    string `json:"resource"`
    Field       string `json:"field"`
}

type K8sGPTSuggestion struct {
    Type        string `json:"type"`
    Description string `json:"description"`
    YAML        string `json:"yaml"`
    Path        string `json:"path"`
}

type K8sGPTAutoFix struct {
    Type        string `json:"type"`
    Description string `json:"description"`
    Command     string `json:"command"`
    Path        string `json:"path"`
    YAML        string `json:"yaml"`
}

type WebhookServer struct {
    gitRepo     *git.Repository
    k8sClient   kubernetes.Interface
    webhookSecret string
    gitBranch   string
    autoFix     bool
}

func main() {
    // Load configuration
    webhookSecret := os.Getenv("FLUX_WEBHOOK_SECRET")
    gitRepoURL := os.Getenv("GIT_REPO_URL")
    gitBranch := os.Getenv("GIT_BRANCH")
    autoFix := os.Getenv("AUTO_FIX_ENABLED") == "true"

    // Initialize Git repository
    repo, err := git.PlainClone("/tmp/repo", false, &git.CloneOptions{
        URL: gitRepoURL,
    })
    if err != nil {
        log.Fatalf("Failed to clone repository: %v", err)
    }

    // Initialize Kubernetes client
    config, err := rest.InClusterConfig()
    if err != nil {
        log.Fatalf("Failed to get in-cluster config: %v", err)
    }
    k8sClient, err := kubernetes.NewForConfig(config)
    if err != nil {
        log.Fatalf("Failed to create Kubernetes client: %v", err)
    }

    server := &WebhookServer{
        gitRepo:       repo,
        k8sClient:     k8sClient,
        webhookSecret: webhookSecret,
        gitBranch:     gitBranch,
        autoFix:       autoFix,
    }

    // Setup HTTP routes
    http.HandleFunc("/webhook", server.handleWebhook)
    http.HandleFunc("/health", server.handleHealth)
    http.HandleFunc("/ready", server.handleReady)

    log.Println("Starting webhook server on port 8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}

func (s *WebhookServer) handleWebhook(w http.ResponseWriter, r *http.Request) {
    // Verify webhook secret
    if r.Header.Get("X-Webhook-Secret") != s.webhookSecret {
        http.Error(w, "Unauthorized", http.StatusUnauthorized)
        return
    }

    // Parse K8sGPT analysis
    var analysis K8sGPTAnalysis
    if err := json.NewDecoder(r.Body).Decode(&analysis); err != nil {
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }

    log.Printf("Received K8sGPT analysis: %+v", analysis)

    // Process analysis and apply fixes
    if err := s.processAnalysis(analysis); err != nil {
        log.Printf("Failed to process analysis: %v", err)
        http.Error(w, "Internal server error", http.StatusInternalServerError)
        return
    }

    w.WriteHeader(http.StatusOK)
    fmt.Fprintf(w, `{"status": "processed", "timestamp": "%s"}`, time.Now().Format(time.RFC3339))
}

func (s *WebhookServer) processAnalysis(analysis K8sGPTAnalysis) error {
    // Pull latest changes
    worktree, err := s.gitRepo.Worktree()
    if err != nil {
        return fmt.Errorf("failed to get worktree: %w", err)
    }

    err = worktree.Pull(&git.PullOptions{
        RemoteName: "origin",
        Branch:     plumbing.NewBranchReferenceName(s.gitBranch),
    })
    if err != nil && err != git.NoErrAlreadyUpToDate {
        return fmt.Errorf("failed to pull changes: %w", err)
    }

    // Process auto-fixes if enabled
    if s.autoFix {
        for _, fix := range analysis.AutoFixes {
            if err := s.applyAutoFix(fix); err != nil {
                log.Printf("Failed to apply auto-fix: %v", err)
                continue
            }
            log.Printf("Applied auto-fix: %s", fix.Description)
        }
    }

    // Commit and push changes
    if s.autoFix && len(analysis.AutoFixes) > 0 {
        if err := s.commitAndPushChanges(analysis); err != nil {
            return fmt.Errorf("failed to commit and push changes: %w", err)
        }
    }

    return nil
}

func (s *WebhookServer) applyAutoFix(fix K8sGPTAutoFix) error {
    // Create file path
    filePath := fix.Path
    if filePath == "" {
        filePath = fmt.Sprintf("clusters/production/autofix-%s.yaml", 
            time.Now().Format("20060102-150405"))
    }

    // Write fix to file
    file, err := os.Create(filePath)
    if err != nil {
        return fmt.Errorf("failed to create file %s: %w", filePath, err)
    }
    defer file.Close()

    if _, err := file.WriteString(fix.YAML); err != nil {
        return fmt.Errorf("failed to write to file %s: %w", filePath, err)
    }

    // Add file to git
    worktree, err := s.gitRepo.Worktree()
    if err != nil {
        return fmt.Errorf("failed to get worktree: %w", err)
    }

    _, err = worktree.Add(filePath)
    if err != nil {
        return fmt.Errorf("failed to add file to git: %w", err)
    }

    return nil
}

func (s *WebhookServer) commitAndPushChanges(analysis K8sGPTAnalysis) error {
    worktree, err := s.gitRepo.Worktree()
    if err != nil {
        return fmt.Errorf("failed to get worktree: %w", err)
    }

    // Commit changes
    commit, err := worktree.Commit(fmt.Sprintf("🤖 Auto-fix by K8sGPT + Qwen\n\nIssues: %d\nFixes: %d\n\nTimestamp: %s",
        len(analysis.Issues), len(analysis.AutoFixes), analysis.Timestamp.Format(time.RFC3339)),
        &git.CommitOptions{
            Author: &object.Signature{
                Name:  "K8sGPT Bot",
                Email: "k8sgpt-bot@users.noreply.github.com",
                When:  time.Now(),
            },
        })
    if err != nil {
        return fmt.Errorf("failed to commit changes: %w", err)
    }

    // Push changes
    err = s.gitRepo.Push(&git.PushOptions{
        RemoteName: "origin",
        RefSpecs:   []string{fmt.Sprintf("refs/heads/%s:refs/heads/%s", s.gitBranch, s.gitBranch)},
    })
    if err != nil {
        return fmt.Errorf("failed to push changes: %w", err)
    }

    log.Printf("Committed and pushed changes: %s", commit.String())
    return nil
}

func (s *WebhookServer) handleHealth(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
    fmt.Fprint(w, "OK")
}

func (s *WebhookServer) handleReady(w http.ResponseWriter, r *http.Request) {
    // Check if all components are ready
    if s.gitRepo == nil || s.k8sClient == nil {
        http.Error(w, "Not ready", http.StatusServiceUnavailable)
        return
    }

    w.WriteHeader(http.StatusOK)
    fmt.Fprint(w, "Ready")
}
```

### Dockerfile for Webhook

```dockerfile
# Dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o webhook ./cmd/webhook

FROM alpine:latest
RUN apk --no-cache add ca-certificates git
WORKDIR /root/

COPY --from=builder /app/webhook .

EXPOSE 8080
CMD ["./webhook"]
```

## 📊 Monitoring and Observability

### Prometheus Metrics

```yaml
# gitops/flux-system/qwen-metrics.yaml
apiVersion: v1
kind: Service
metadata:
  name: qwen-llm-metrics
  namespace: qwen-system
  labels:
    app.kubernetes.io/name: qwen-llm
    app.kubernetes.io/component: metrics
spec:
  selector:
    app: qwen-llm
  ports:
  - port: 9090
    targetPort: 9090
    name: metrics
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: qwen-llm
  namespace: qwen-system
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: qwen-llm
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: k8sgpt-qwen
  namespace: flux-system
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: k8sgpt
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "K8sGPT + Qwen Integration",
    "panels": [
      {
        "title": "Analysis Requests",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(k8sgpt_analysis_requests_total[5m]))"
          }
        ]
      },
      {
        "title": "Auto-fixes Applied",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(k8sgpt_autofixes_applied_total)"
          }
        ]
      },
      {
        "title": "Qwen Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(qwen_response_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Issues by Severity",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (severity) (k8sgpt_issues_detected_total)"
          }
        ]
      }
    ]
  }
}
```

## 🧪 Testing

### Unit Tests

```bash
# Run K8sGPT analysis test
kubectl apply -f ./tests/k8sgpt-test-pod.yaml
kubectl wait --for=condition=ready pod/k8sgpt-test -n default --timeout=60s

# Check if K8sGPT detects issues
kubectl logs -n flux-system deployment/k8sgpt | grep "Analysis completed"
```

### Integration Tests

```bash
# Run full integration test
./scripts/qwen-integration-test.sh \
  --test-scenario=deployment-failure \
  --test-scenario=resource-quota \
  --test-scenario=security-policy
```

### Load Testing

```bash
# Test Qwen under load
kubectl apply -f ./tests/load-test.yaml
kubectl logs -n qwen-system deployment/qwen-llm | grep "request latency"
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Qwen Model Not Loading
```bash
# Check model file
kubectl exec -n qwen-system deployment/qwen-llm -- ls -la /models/

# Check logs
kubectl logs -n qwen-system deployment/qwen-llm | grep -i error

# Verify resources
kubectl describe pod -n qwen-system -l app=qwen-llm
```

#### 2. K8sGPT Connection Issues
```bash
# Test connectivity
kubectl exec -n flux-system deployment/k8sgpt -- curl http://qwen-llm.qwen-system.svc.cluster.local:8000/health

# Check configuration
kubectl get k8sgpt k8sgpt-qwen -n flux-system -o yaml

# Verify secret
kubectl get secret qwen-connection-secret -n flux-system -o yaml
```

#### 3. Webhook Not Receiving Events
```bash
# Check webhook endpoint
kubectl exec -n flux-system deployment/flux-webhook -- curl http://localhost:8080/health

# Check K8sGPT sink configuration
kubectl get k8sgpt k8sgpt-qwen -n flux-system -o jsonpath='{.spec.sink}'

# Verify network policies
kubectl get networkpolicy -n flux-system
```

### Debug Commands

```bash
# Comprehensive status check
kubectl get all -n qwen-system
kubectl get all -n flux-system
kubectl get k8sgpt -A

# Detailed logs
kubectl logs -n qwen-system deployment/qwen-llm --since=1h
kubectl logs -n flux-system deployment/k8sgpt --since=1h
kubectl logs -n flux-system deployment/flux-webhook --since=1h

# Test Qwen API directly
kubectl exec -n qwen-system deployment/qwen-llm -- curl -X POST \
  http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test connection"}'
```

## 🚀 Advanced Features

### Custom Analysis Rules

```yaml
# gitops/flux-system/custom-rules.yaml
apiVersion: core.k8sgpt.ai/v1alpha1
kind: AnalysisRule
metadata:
  name: security-compliance
  namespace: flux-system
spec:
  name: "Security Compliance Check"
  description: "Check for security best practices"
  severity: "high"
  conditions:
  - field: "spec.containers[*].securityContext.runAsNonRoot"
    operator: "Equals"
    value: true
  - field: "spec.containers[*].securityContext.allowPrivilegeEscalation"
    operator: "Equals"
    value: false
  - field: "spec.containers[*].securityContext.readOnlyRootFilesystem"
    operator: "Equals"
    value: true
  remediation:
    type: "patch"
    patch: |
      spec:
        template:
          spec:
            securityContext:
              runAsNonRoot: true
              allowPrivilegeEscalation: false
              readOnlyRootFilesystem: true
```

### Multi-Model Support

```yaml
# gitops/flux-system/multi-model.yaml
apiVersion: core.k8sgpt.ai/v1alpha1
kind: K8sGPT
metadata:
  name: k8sgpt-multi-model
  namespace: flux-system
spec:
  model: qwen
  backend: local
  fallback:
    model: gpt-3.5-turbo
    backend: openai
  models:
  - name: qwen
    type: local
    config:
      modelPath: "/models/qwen2.5-7b-instruct.gguf"
      temperature: 0.7
  - name: gpt-3.5-turbo
    type: openai
    config:
      apiKeySecret: openai-secret
      temperature: 0.5
```

### Event-Driven Analysis

```yaml
# gitops/flux-system/event-driven.yaml
apiVersion: v1
kind: Event
metadata:
  name: k8sgpt-analysis-trigger
  namespace: flux-system
annotations:
  k8sgpt.ai/trigger: "true"
reason: "ResourceChange"
message: "Triggering K8sGPT analysis for resource changes"
source:
  component: "flux-controller"
involvedObject:
  kind: "Deployment"
  name: "app-deployment"
  namespace: "production"
```

## 📚 Best Practices

### Performance Optimization
1. **Model Caching**: Enable model caching to reduce loading time
2. **Resource Limits**: Set appropriate CPU/memory limits
3. **Batch Processing**: Batch multiple resources for analysis
4. **Async Processing**: Use asynchronous processing for large clusters

### Security Considerations
1. **Network Isolation**: Isolate Qwen service in dedicated namespace
2. **RBAC**: Use minimal permissions for K8sGPT
3. **Secret Management**: Encrypt API keys and sensitive data
4. **Audit Logging**: Enable comprehensive audit logging

### Reliability
1. **Health Checks**: Configure proper liveness/readiness probes
2. **Circuit Breakers**: Implement circuit breakers for external calls
3. **Retry Logic**: Configure retry policies for failed requests
4. **Backup Models**: Have fallback models available

---

This comprehensive integration provides intelligent Kubernetes operations with Qwen LLM, K8sGPT, and Flux CD for automated monitoring, analysis, and remediation.

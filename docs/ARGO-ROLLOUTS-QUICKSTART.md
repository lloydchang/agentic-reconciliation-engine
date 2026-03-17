# Argo Rollouts Quickstart Guide

## 🚀 Quick Start with Argo Rollouts and K8sGPT Qwen Integration

This guide will get you up and running with Argo Rollouts in minutes, complete with AI-powered analysis using K8sGPT and Qwen LLM.

### Prerequisites

- Kubernetes cluster (v1.20+)
- kubectl configured
- Helm 3.0+
- (Optional) Prometheus for metrics analysis

### One-Command Installation

```bash
# Run the complete setup
./scripts/quickstart-argo-rollouts.sh
```

### Manual Installation Steps

#### 1. Install Argo Rollouts
```bash
# Using kubectl
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Using Helm
helm repo add argo-rollouts https://argoproj.github.io/argo-helm
helm install argo-rollouts argo-rollouts/argo-rollouts --namespace argo-rollouts
```

#### 2. Install kubectl Plugin
```bash
# Linux/macOS
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m | sed 's/x86_64/amd64/')
chmod +x kubectl-argo-rollouts-*
sudo mv kubectl-argo-rollouts-* /usr/local/bin/kubectl-argo-rollouts

# Verify installation
kubectl argo rollouts version
```

#### 3. Setup K8sGPT with Qwen
```bash
# Run the K8sGPT setup script
./scripts/setup-k8sgpt-qwen.sh

# Or manually configure
kubectl create namespace gitops-infra
kubectl apply -f overlay/k8sgpt/
```

### Your First Rollout

#### Basic Canary Rollout
```yaml
# my-first-rollout.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
spec:
  replicas: 3
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 10m}
      - setWeight: 50
      - pause: {duration: 10m}
      - setWeight: 100
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-app
        image: nginx:1.20
        ports:
        - containerPort: 80
```

#### Deploy and Monitor
```bash
# Apply the rollout
kubectl apply -f my-first-rollout.yaml

# Watch the progress
kubectl argo rollouts get rollout my-app --watch

# Check status
kubectl argo rollouts status my-app

# Trigger an update
kubectl set image rollout/my-app my-app=nginx:1.21
```

### Advanced Examples

#### Blue-Green with K8sGPT Analysis
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app-bg
spec:
  replicas: 3
  strategy:
    blueGreen:
      activeService: my-app-active
      previewService: my-app-preview
      autoPromotionEnabled: false
      prePromotionAnalysis:
        templates:
        - templateName: k8sgpt-health-check
        args:
        - name: namespace
          value: default
  selector:
    matchLabels:
      app: my-app-bg
  template:
    metadata:
      labels:
        app: my-app-bg
    spec:
      containers:
      - name: my-app
        image: nginx:1.20
        ports:
        - containerPort: 80
```

#### Canary with Qwen AI Analysis
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app-ai
spec:
  replicas: 5
  strategy:
    canary:
      steps:
      - setWeight: 20
      - analysis:
          templates:
          - templateName: qwen-decision
          args:
          - name: rollout-name
            value: my-app-ai
          - name: threshold
            value: "0.8"
      - setWeight: 50
      - analysis:
          templates:
          - templateName: qwen-decision
          args:
          - name: rollout-name
            value: my-app-ai
          - name: threshold
            value: "0.9"
  selector:
    matchLabels:
      app: my-app-ai
  template:
    metadata:
      labels:
        app: my-app-ai
    spec:
      containers:
      - name: my-app
        image: nginx:1.20
        ports:
        - containerPort: 80
```

### Essential Commands

#### Rollout Management
```bash
# List rollouts
kubectl argo rollouts list

# Get rollout details
kubectl argo rollouts get rollout my-app

# Watch rollout progress
kubectl argo rollouts get rollout my-app --watch

# Check rollout status
kubectl argo rollouts status my-app

# Promote paused rollout
kubectl argo rollouts promote my-app

# Abort rollout
kubectl argo rollouts abort my-app

# Rollback to previous version
kubectl argo rollouts undo my-app

# View rollout history
kubectl argo rollouts history my-app
```

#### Analysis and Debugging
```bash
# List analysis runs
kubectl argo rollouts list analysisrun

# Get analysis run details
kubectl argo rollouts get analysisrun my-app-analysis-xyz

# View rollout events
kubectl describe rollout my-app

# Check controller logs
kubectl logs -n argo-rollouts deployment/argo-rollouts
```

#### K8sGPT Integration
```bash
# Run K8sGPT analysis
kubectl exec -n gitops-infra deployment/k8sgpt-analyzer -- \
  k8sgpt analyze --namespace default --explain

# Check K8sGPT status
kubectl get pods -n gitops-infra | grep k8sgpt

# View K8sGPT logs
kubectl logs -n gitops-infra deployment/k8sgpt-analyzer
```

### Configuration Files

#### Analysis Templates
```yaml
# success-rate.yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
  - name: service-name
  metrics:
  - name: success-rate
    interval: 30s
    count: 10
    successCondition: result[0] >= 0.95
    provider:
      prometheus:
        address: http://prometheus.monitoring.svc.cluster.local:9090
        query: |
          sum(rate(http_server_requests_total{service="{{args.service-name}}",status!~"5.."}[2m])) /
          sum(rate(http_server_requests_total{service="{{args.service-name}}"}[2m]))
```

#### K8sGPT Analysis Template
```yaml
# k8sgpt-analysis.yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: k8sgpt-health-check
spec:
  args:
  - name: namespace
  metrics:
  - name: k8sgpt-health-score
    interval: 60s
    count: 5
    successCondition: result[0] >= 0.8
    provider:
      job:
        spec:
          template:
            spec:
              containers:
              - name: k8sgpt-analyzer
                image: k8sgpt/k8sgpt:latest
                command:
                - /bin/sh
                - -c
                - |
                  k8sgpt analyze --namespace {{args.namespace}} --output json > /tmp/analysis.json
                  python3 /scripts/calculate-health-score.py /tmp/analysis.json
                env:
                - name: QWEN_API_KEY
                  valueFrom:
                    secretKeyRef:
                      name: qwen-secret
                      key: api-key
```

### Monitoring and Observability

#### Metrics
```bash
# Access metrics
kubectl port-forward -n argo-rollouts svc/argo-rollouts-metrics 8090:8090
curl http://localhost:8090/metrics

# Key metrics to watch:
# - argo_rollouts_rollout_phase
# - argo_rollouts_controller_reconcile_duration_seconds
# - argo_rollouts_analysis_result
```

#### Grafana Dashboard
Import the provided Grafana dashboard for comprehensive monitoring:
- Rollout status overview
- Analysis execution times
- Success rates and error patterns
- Resource utilization

### Troubleshooting

#### Common Issues

**Rollout Stuck in Progressing**
```bash
# Check rollout status
kubectl argo rollouts status my-app

# Check events
kubectl describe rollout my-app

# Manually promote if needed
kubectl argo rollouts promote my-app
```

**Analysis Template Failed**
```bash
# Check analysis runs
kubectl argo rollouts get analysisrun

# Check analysis job logs
kubectl logs -l analysis-template=<template-name>

# Debug with dry run
kubectl argo rollouts analyze my-app --template <template-name> --dry-run
```

**K8sGPT Integration Issues**
```bash
# Check K8sGPT pod
kubectl get pods -n gitops-infra | grep k8sgpt

# Check Qwen configuration
kubectl get secret qwen-secret -n gitops-infra
kubectl get configmap qwen-config -n gitops-infra

# Test K8sGPT manually
kubectl exec -n gitops-infra deployment/k8sgpt-analyzer -- k8sgpt version
```

### Best Practices

#### Rollout Design
1. **Start Simple**: Begin with basic canary strategies
2. **Gradual Progression**: Use small weight increments
3. **Automated Analysis**: Implement automated analysis templates
4. **Monitoring**: Set up comprehensive monitoring
5. **Testing**: Test strategies in non-production environments

#### Analysis Templates
1. **Idempotent**: Ensure templates are retry-safe
2. **Timeouts**: Set appropriate timeouts
3. **Error Handling**: Implement proper error handling
4. **Resource Limits**: Set resource limits on analysis jobs
5. **Security**: Follow security best practices

#### K8sGPT Integration
1. **Model Selection**: Choose appropriate Qwen model size
2. **Prompt Engineering**: Craft clear, specific prompts
3. **Caching**: Enable result caching
4. **Monitoring**: Monitor K8sGPT performance
5. **Fallbacks**: Implement fallback mechanisms

### Next Steps

1. **Explore Examples**: Check `overlay/argo-rollouts/examples/`
2. **Read Full Guide**: See `docs/ARGO-ROLLOUTS-COMPREHENSIVE-GUIDE.md`
3. **Run Tests**: Execute `tests/argo-rollouts/test-argo-rollouts.sh`
4. **Configure Monitoring**: Set up Prometheus and Grafana
5. **Customize Analysis**: Create custom analysis templates

### Support

- **Documentation**: `docs/ARGO-ROLLOUTS-COMPREHENSIVE-GUIDE.md`
- **Examples**: `overlay/argo-rollouts/examples/`
- **Tests**: `tests/argo-rollouts/`
- **Issues**: Report bugs on GitHub
- **Community**: Join the Argo Rollouts community

---

**🎉 Congratulations! You now have Argo Rollouts with AI-powered K8sGPT analysis running!**

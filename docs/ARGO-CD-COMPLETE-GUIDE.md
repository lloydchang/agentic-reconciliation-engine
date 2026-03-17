# Complete Argo CD Integration Guide

## Overview

This comprehensive guide covers the complete integration of Argo CD with K8sGPT and Qwen LLM for intelligent Kubernetes GitOps operations. This integration provides automated continuous delivery with AI-powered analysis and troubleshooting capabilities.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Quick Start](#quick-start)
3. [Installation Guide](#installation-guide)
4. [Configuration](#configuration)
5. [Environment Setup](#environment-setup)
6. [K8sGPT + Qwen Integration](#k8sgpt--qwen-integration)
7. [GitOps Workflows](#gitops-workflows)
8. [Monitoring and Observability](#monitoring-and-observability)
9. [Security Best Practices](#security-best-practices)
10. [Testing and Validation](#testing-and-validation)
11. [Troubleshooting](#troubleshooting)
12. [Advanced Features](#advanced-features)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Git Repository                        │
│  https://github.com/lloydchang/gitops-infra-control-plane    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                        Argo CD                              │
│  • Application Management                                   │
│  • Git Synchronization                                      │
│  • Automated Deployments                                     │
│  • Rollback Capabilities                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│  • Argo CD Server                                           │
│  • K8sGPT with Qwen LLM                                     │
│  • Application Workloads                                    │
│  • Monitoring Stack                                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    K8sGPT + Qwen LLM                        │
│  • Resource Analysis                                        │
│  • Issue Detection                                          │
│  • Automated Remediation                                     │
│  • Documentation Integration                                │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 5-Minute Setup

```bash
# 1. Run the automated setup script
./scripts/setup-argocd.sh

# 2. Access Argo CD UI
# URL: http://localhost:8080
# Username: admin
# Password: (shown in script output)

# 3. Test K8sGPT API
curl -X POST http://localhost:8081/analyze \
  -H "Content-Type: application/json" \
  -d '{"namespace": "default"}'

# 4. Monitor deployments
kubectl get pods -n argocd
kubectl get pods -n k8sgpt-system
```

### Manual Setup

```bash
# 1. Install Argo CD
kubectl apply -f gitops/argocd/namespace.yaml
kubectl apply -f gitops/argocd/install.yaml

# 2. Install K8sGPT with Qwen
kubectl apply -f gitops/argocd/k8sgpt/namespace.yaml
kubectl apply -f gitops/argocd/k8sgpt/qwen-deployment.yaml
kubectl apply -f gitops/argocd/k8sgpt/qwen-config.yaml
kubectl apply -f gitops/argocd/k8sgpt/k8sgpt-deployment.yaml
kubectl apply -f gitops/argocd/k8sgpt/configmap.yaml

# 3. Configure applications
kubectl apply -f gitops/argocd/applications/root-app.yaml
kubectl apply -f gitops/argocd/applications/k8sgpt-app.yaml
kubectl apply -f gitops/argocd/applications/ai-infrastructure-app.yaml
```

## Installation Guide

### Prerequisites

- Kubernetes cluster (v1.20+)
- kubectl configured
- At least 8GB available memory for Qwen model
- Git repository access
- (Optional) GPU for better Qwen performance

### Step 1: Install Argo CD

```bash
# Create namespace
kubectl create namespace argocd

# Install Argo CD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Or use our custom installation
kubectl apply -f gitops/argocd/install.yaml

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd
```

### Step 2: Install K8sGPT with Qwen

```bash
# Create namespace
kubectl create namespace k8sgpt-system

# Deploy Qwen LocalAI
kubectl apply -f gitops/argocd/k8sgpt/qwen-deployment.yaml
kubectl apply -f gitops/argocd/k8sgpt/qwen-config.yaml

# Deploy K8sGPT
kubectl apply -f gitops/argocd/k8sgpt/k8sgpt-deployment.yaml
kubectl apply -f gitops/argocd/k8sgpt/configmap.yaml

# Wait for deployment
kubectl wait --for=condition=available --timeout=600s deployment/qwen-localai -n k8sgpt-system
kubectl wait --for=condition=available --timeout=300s deployment/k8sgpt -n k8sgpt-system
```

### Step 3: Download Qwen Model

```bash
# Download Qwen2.5 Coder 7B model
wget https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q4_0.gguf

# Copy to persistent volume
POD_NAME=$(kubectl get pods -n k8sgpt-system -l app.kubernetes.io/name=qwen-localai -o jsonpath='{.items[0].metadata.name}')
kubectl cp qwen2.5-coder-7b-instruct-q4_0.gguf $POD_NAME:/models/ -n k8sgpt-system
```

### Step 4: Configure Argo CD Applications

```bash
# Apply root application
kubectl apply -f gitops/argocd/applications/root-app.yaml

# Apply individual applications
kubectl apply -f gitops/argocd/applications/k8sgpt-app.yaml
kubectl apply -f gitops/argocd/applications/ai-infrastructure-app.yaml
```

## Configuration

### Argo CD Configuration

Edit `gitops/argocd/install.yaml` to customize:

```yaml
# Server configuration
spec:
  type: LoadBalancer  # or ClusterIP for internal access

# Resource limits
resources:
  limits:
    cpu: 2000m
    memory: 2Gi
  requests:
    cpu: 1000m
    memory: 1Gi

# Authentication
env:
- name: ARGOCD_SERVER_INSECURE
  value: "false"  # Set to "false" for production
```

### K8sGPT Configuration

Edit `gitops/argocd/k8sgpt/configmap.yaml`:

```yaml
data:
  config.yaml: |
    # Backend configuration
    backend: "localai"
    localai:
      url: "http://qwen-localai.k8sgpt-system.svc.cluster.local:8080"
      model: "qwen2.5-coder:7b"
    
    # Analysis configuration
    analysis:
      explain: true
      with-doc: true
      max-concurrency: 10
      filters:
        - "Deployment"
        - "StatefulSet"
        - "Pod"
        - "Service"
```

### Qwen Model Configuration

Edit `gitops/argocd/k8sgpt/qwen-config.yaml`:

```yaml
data:
  config.yaml: |
    models:
      - name: "qwen2.5-coder:7b"
        backend: "llama-cpp"
        parameters:
          temperature: 0.1
          top_p: 0.9
          max_tokens: 4096
          context_size: 8192
          # GPU settings (uncomment if using GPU)
          # gpu_layers: 35
          # f16_kv: true
```

## Environment Setup

### Development Environment

```bash
# Use development overlay
kubectl apply -k overlay/argocd/development

# Features:
# - Debug logging enabled
# - Lower resource requirements
# - ClusterIP service type
# - Single replica deployments
```

### Staging Environment

```bash
# Use staging overlay
kubectl apply -k overlay/argocd/staging

# Features:
# - Info logging level
# - Medium resource requirements
# - NodePort service type
# - Single replica with higher resources
```

### Production Environment

```bash
# Use production overlay
kubectl apply -k overlay/argocd/production

# Features:
# - Secure configuration
# - High resource requirements
# - LoadBalancer service type
# - Multiple replicas with HPA
# - Network policies
# - Pod security policies
```

## K8sGPT + Qwen Integration

### Model Options

| Model | Size | Use Case | Resources |
|-------|------|----------|-----------|
| `qwen2.5-coder:7b` | 7B | Code analysis, Kubernetes troubleshooting | 4-8GB RAM |
| `qwen2.5:7b` | 7B | General analysis, documentation | 4-8GB RAM |
| `qwen2.5:14b` | 14B | Advanced analysis, complex scenarios | 8-16GB RAM |
| `qwen2.5:32b` | 32B | Enterprise-grade analysis | 16-32GB RAM |

### Analysis Types

#### 1. Resource Analysis

```bash
curl -X POST http://localhost:8081/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "default",
    "filters": ["Deployment", "Service", "Ingress"]
  }'
```

#### 2. Security Analysis

```bash
curl -X POST http://localhost:8081/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "default",
    "filters": ["Pod", "ServiceAccount", "Role", "RoleBinding"],
    "explain": true
  }'
```

#### 3. Performance Analysis

```bash
curl -X POST http://localhost:8081/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "default",
    "filters": ["Deployment", "Pod", "HorizontalPodAutoscaler"],
    "explain": true,
    "with-doc": true
  }'
```

### Custom Prompts

Configure specialized prompts in `gitops/argocd/k8sgpt/configmap.yaml`:

```yaml
prompts:
  security-prompt: |
    You are a Kubernetes security expert. Analyze the following resources for:
    1. Security vulnerabilities and misconfigurations
    2. RBAC permission issues
    3. Network security problems
    4. Secrets and sensitive data exposure
    
  performance-prompt: |
    You are a Kubernetes performance expert. Analyze the following resources for:
    1. Resource allocation issues
    2. Performance bottlenecks
    3. Scaling problems
    4. Network latency issues
```

## GitOps Workflows

### Application Lifecycle

1. **Development**: Push changes to feature branch
2. **Testing**: Create pull request, automated testing
3. **Staging**: Merge to staging branch, deploy to staging
4. **Production**: Merge to main branch, deploy to production

### Argo CD Application Management

```bash
# List applications
argocd app list

# Get application status
argocd app get k8sgpt

# Sync application
argocd app sync k8sgpt

# Application history
argocd app history k8sgpt

# Rollback application
argocd app rollback k8sgpt <revision>
```

### Automated Analysis Integration

```yaml
# Automated analysis CronJob
apiVersion: batch/v1
kind: CronJob
metadata:
  name: k8sgpt-analysis
  namespace: k8sgpt-system
spec:
  schedule: "0 */6 * * *"  # Every 6 hours
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: k8sgpt
            image: k8sgpt/k8sgpt:v0.3.4
            command:
            - k8sgpt
            - analyze
            - --namespace
            - default
            - --explain
            - --with-doc
```

## Monitoring and Observability

### Metrics Collection

```yaml
# Prometheus ServiceMonitor
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: argocd-metrics
  namespace: argocd
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: argocd-metrics
  endpoints:
  - port: metrics
```

### Key Metrics

- **Argo CD**: Application sync status, deployment duration, error rates
- **K8sGPT**: Analysis requests, response times, model inference time
- **Qwen**: Model loading time, GPU utilization, memory usage
- **System**: Pod restarts, resource utilization, network latency

### Grafana Dashboards

Import pre-built dashboards:
- Argo CD Application Status
- K8sGPT Analysis Metrics
- Qwen Model Performance
- GitOps Pipeline Health

### Alerting

```yaml
# Prometheus Alert
groups:
- name: argocd-alerts
  rules:
  - alert: ArgoCDSyncFailed
    expr: argocd_app_sync_status == 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Argo CD application sync failed"
```

## Security Best Practices

### Authentication

```yaml
# Configure OIDC authentication
config.yaml:
  oidc.config: |
    name: AzureAD
    issuer: https://login.microsoftonline.com/{tenant-id}/v2.0
    clientID: {client-id}
    clientSecret: $oidc.clientSecret
    requestedScopes: ["openid", "profile", "email", "groups"]
```

### Network Policies

```yaml
# Restrict inter-service communication
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: argocd-deny-all-ingress
  namespace: argocd
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

### RBAC Configuration

```yaml
# Principle of least privilege
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: argocd-app-controller
  namespace: applications
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

### Secrets Management

```yaml
# Use external secrets operator
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: argocd
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      version: "v2"
```

## Testing and Validation

### Automated Testing

```bash
# Run comprehensive test suite
./tests/argocd/run-tests.sh

# Run specific test
./tests/argocd/run-tests.sh -t k8sgpt_analysis

# Run with verbose output
./tests/argocd/run-tests.sh -v

# Generate test report
./tests/argocd/run-tests.sh -o /tmp/test-report.md
```

### Test Categories

1. **Unit Tests**: Python syntax, imports, basic functionality
2. **Integration Tests**: API connectivity, deployment validation
3. **Performance Tests**: Response times, resource utilization
4. **Security Tests**: Credential exposure, configuration validation

### Validation Checklist

- [ ] Argo CD server accessible
- [ ] Applications syncing correctly
- [ ] K8sGPT API responding
- [ ] Qwen model loaded
- [ ] Analysis functionality working
- [ ] Monitoring metrics available
- [ ] Security policies applied
- [ ] Resource limits appropriate

## Troubleshooting

### Common Issues

#### Argo CD Issues

1. **Server Not Accessible**
   ```bash
   # Check pod status
   kubectl get pods -n argocd
   
   # Check logs
   kubectl logs -f deployment/argocd-server -n argocd
   
   # Check service
   kubectl get svc -n argocd
   ```

2. **Application Sync Failures**
   ```bash
   # Check application status
   argocd app get <app-name>
   
   # Check sync status
   argocd app sync <app-name> --debug
   
   # Check repository access
   argocd repo list
   ```

#### K8sGPT Issues

1. **API Not Responding**
   ```bash
   # Check pod status
   kubectl get pods -n k8sgpt-system
   
   # Check logs
   kubectl logs -f deployment/k8sgpt -n k8sgpt-system
   
   # Check service
   kubectl get svc -n k8sgpt-system
   ```

2. **Model Loading Issues**
   ```bash
   # Check model file
   kubectl exec -it deployment/qwen-localai -n k8sgpt-system -- ls -la /models/
   
   # Check model permissions
   kubectl exec -it deployment/qwen-localai -n k8sgpt-system -- chmod 644 /models/*.gguf
   
   # Check resource usage
   kubectl top pods -n k8sgpt-system
   ```

#### Performance Issues

1. **Slow Response Times**
   ```bash
   # Check resource utilization
   kubectl top nodes
   kubectl top pods -n k8sgpt-system
   
   # Check model inference time
   kubectl logs deployment/qwen-localai -n k8sgpt-system | grep "inference"
   
   # Scale resources if needed
   kubectl patch deployment k8sgpt -n k8sgpt-system -p '{"spec":{"template":{"spec":{"containers":[{"name":"k8sgpt","resources":{"limits":{"memory":"2Gi"}}}]}}}}'
   ```

### Debug Mode

Enable debug logging:

```yaml
env:
- name: ARGOCD_SERVER_LOGLEVEL
  value: "debug"
- name: K8SGPT_LOG_LEVEL
  value: "debug"
- name: LOCALAI_DEBUG
  value: "true"
```

### Recovery Procedures

1. **Pod Restart**
   ```bash
   kubectl rollout restart deployment/argocd-server -n argocd
   kubectl rollout restart deployment/k8sgpt -n k8sgpt-system
   ```

2. **Application Resync**
   ```bash
   argocd app sync <app-name> --force
   ```

3. **Model Reload**
   ```bash
   kubectl rollout restart deployment/qwen-localai -n k8sgpt-system
   ```

## Advanced Features

### Progressive Delivery

```yaml
# Canary deployment with Argo Rollouts
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
spec:
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 10m}
      - setWeight: 40
      - pause: {duration: 10m}
      - setWeight: 60
      - pause: {duration: 10m}
      - setWeight: 80
      - pause: {duration: 10m}
```

### Multi-Cluster Management

```yaml
# Cluster configuration
apiVersion: v1
kind: Secret
metadata:
  name: cluster-1-secret
  namespace: argocd
type: Opaque
stringData:
  name: cluster-1
  server: https://k8s-cluster-1.example.com
  config: |
    {
      "bearerToken": "token",
      "tlsClientConfig": {
        "insecure": false,
        "caData": "base64-ca-cert"
      }
    }
```

### Custom Controllers

```yaml
# Custom Argo CD application controller
apiVersion: apps/v1
kind: Deployment
metadata:
  name: argocd-application-controller
  namespace: argocd
spec:
  template:
    spec:
      containers:
      - name: argocd-application-controller
        env:
        - name: ARGOCD_CONTROLLER_RECONCILIATION_TIMEOUT
          value: "300s"
        - name: ARGOCD_CONTROLLER_SYNC_TIMEOUT
          value: "120s"
```

### Integration with External Tools

#### Slack Notifications

```yaml
# Argo CD notifications
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
data:
  service.slack: |
    token: $slack-token
    username: argocd
    icon: ":argocd:"
```

#### Jira Integration

```yaml
# Automated issue creation
apiVersion: batch/v1
kind: Job
metadata:
  name: create-jira-issue
spec:
  template:
    spec:
      containers:
      - name: jira-client
        image: atlassian-cli
        command:
        - jira
        - issue
        - create
        - --project
        - "K8S"
        - --summary
        - "Argo CD Sync Failed: {{.app.name}}"
        - --description
        - "Application {{.app.name}} failed to sync in namespace {{.app.namespace}}"
```

## Next Steps

1. **Deploy**: Use the automated setup script for quick deployment
2. **Configure**: Customize configurations for your environment
3. **Test**: Run the comprehensive test suite
4. **Monitor**: Set up monitoring and alerting
5. **Secure**: Implement security best practices
6. **Scale**: Optimize for production workloads

## Support and Resources

- **Documentation**: Check `docs/` directory for detailed guides
- **Examples**: Review `examples/` directory for use cases
- **Community**: Join our Slack/Discord communities
- **Issues**: Report bugs and feature requests on GitHub
- **Testing**: Use the provided test suite for validation

---

**Note**: This integration provides powerful GitOps capabilities with AI-driven insights. Adjust configurations based on your specific requirements and environment constraints.

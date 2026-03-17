# Flux Complete Integration Guide

## Overview

This guide provides comprehensive Flux CD integration for the GitOps Infra Control Plane, including automated setup, Qwen LLM integration with K8sGPT, and complete observability.

## 🚀 Quick Start

```bash
# One-command Flux setup with Qwen integration
curl -sSL https://raw.githubusercontent.com/fluxcd/flux2/main/install.sh | sudo bash
./scripts/flux-auto-setup.sh --with-qwen --full-automation
```

## 📋 Prerequisites

### System Requirements
- **Kubernetes**: v1.24+ (supports Kind, K3s, EKS, AKS, GKE)
- **kubectl**: Configured and working
- **Git**: SSH keys configured for repository access
- **Flux CLI**: v2.2+ (auto-installed by setup script)

### Optional Requirements
- **Docker**: For local development and testing
- **Helm**: v3.8+ (for Helm releases)
- **SOPS**: For secret encryption
- **Age**: For key management

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Git Repository                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ Flux Config │ │ Infrastructure│ │     Applications       │ │
│  │   (YAML)    │ │   (K8s)     │ │      (Helm/K8s)        │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flux Controllers                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   Source    │ │ Kustomize   │ │      Helm              │ │
│  │ Controller  │ │ Controller  │ │    Controller          │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┐ │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ Notification│ │ Image Update│ │    K8sGPT + Qwen       │ │
│  │ Controller  │ │ Automation  │ │      Integration       │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Kubernetes Cluster                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ Infrastructure│ │  Applications│ │    Monitoring          │ │
│  │   Resources  │ │  Workloads   │ │      Stack             │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Installation Methods

### 1. Automated Setup (Recommended)

```bash
# Full automation with Qwen integration
./scripts/flux-auto-setup.sh \
  --provider=github \
  --repository=gitops-infra-control-plane \
  --owner=your-org \
  --branch=main \
  --path=./clusters/production \
  --with-qwen \
  --with-monitoring \
  --with-secrets \
  --auto-approve
```

### 2. Manual Bootstrap

```bash
# GitHub bootstrap
flux bootstrap github \
  --owner=your-org \
  --repository=gitops-infra-control-plane \
  --branch=main \
  --path=./clusters/production \
  --personal \
  --ssh-key-algorithm=ed25519

# Generic Git bootstrap
flux bootstrap git \
  --url=ssh://git@github.com/your-org/gitops-infra-control-plane.git \
  --branch=main \
  --path=./clusters/production \
  --private-key-file=~/.ssh/id_rsa
```

### 3. Overlay-based Setup

```bash
# Use overlay system for flexibility
./scripts/overlay-quickstart.sh \
  --overlay=flux-complete \
  --target-cluster=production \
  --with-qwen-integration
```

## 🤖 Qwen LLM Integration with K8sGPT

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│    K8sGPT       │───▶│   Qwen LLM       │───▶│  Analysis       │
│  (Collector)    │    │  (Inference)     │    │   Results       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Kubernetes     │    │  Local/Remote    │    │  Flux Actions   │
│    Events       │    │     Model        │    │  (Auto-fix)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Setup Qwen Integration

```bash
# Deploy K8sGPT with Qwen
kubectl apply -f ./gitops/flux-system/k8sgpt-qwen.yaml

# Configure Qwen model
cat <<EOF | kubectl apply -f -
apiVersion: core.k8sgpt.ai/v1alpha1
kind: K8sGPT
metadata:
  name: k8sgpt-qwen
  namespace: flux-system
spec:
  model: qwen
  backend: local
  noCache: false
  version: "v1.0.0"
  secret: qwen-secret
  sink:
    type: webhook
    webhook:
      endpoint: http://flux-webhook.flux-system.svc.cluster.local/webhook
EOF
```

### Qwen Configuration

```yaml
# gitops/flux-system/qwen-config.yaml
apiVersion: v1
kind: Secret
metadata:
  name: qwen-secret
  namespace: flux-system
type: Opaque
stringData:
  model: "qwen2.5:7b"
  apiUrl: "http://qwen-llm.qwen-system.svc.cluster.local:8000"
  apiKey: ""
  temperature: "0.7"
  maxTokens: "2048"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qwen-llm
  namespace: qwen-system
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
        image: qwen/qwen2.5:7b
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: 1000m
            memory: 4Gi
          limits:
            cpu: 2000m
            memory: 8Gi
        env:
        - name: MODEL_PATH
          value: "/models/qwen2.5-7b"
        volumeMounts:
        - name: model-volume
          mountPath: /models
      volumes:
      - name: model-volume
        persistentVolumeClaim:
          claimName: qwen-model-pvc
```

## 📁 Repository Structure

```
gitops-infra-control-plane/
├── clusters/
│   ├── production/
│   │   ├── flux-system/
│   │   │   ├── gotk-sync.yaml
│   │   │   ├── kustomization.yaml
│   │   │   └── qwen-integration.yaml
│   │   ├── infrastructure.yaml
│   │   ├── applications.yaml
│   │   └── monitoring.yaml
│   ├── staging/
│   └── development/
├── core/
│   ├── resources/
│   │   ├── tenants/
│   │   │   ├── 1-network/
│   │   │   ├── 2-clusters/
│   │   │   └── 3-workloads/
│   │   └── operators/
│   ├── ai/
│   │   ├── skills/
│   │   └── runtime/
│   └── automation/
├── apps/
│   ├── base/
│   └── overlays/
├── scripts/
│   ├── flux-auto-setup.sh
│   ├── flux-health-check.sh
│   └── qwen-setup.sh
└── docs/
    ├── FLUX-COMPLETE-GUIDE.md
    ├── QWEN-INTEGRATION.md
    └── TROUBLESHOOTING.md
```

## 🔒 Security Configuration

### Network Policies

```yaml
# gitops/flux-system/network-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: flux-system-netpol
  namespace: flux-system
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 8080
  - from:
    - namespaceSelector:
        matchLabels:
          name: qwen-system
    ports:
    - protocol: TCP
      port: 9292
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
```

### RBAC Configuration

```yaml
# gitops/flux-system/rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: flux-system-controller
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["k8sgpt.ai"]
  resources: ["*"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: flux-system-controller
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: flux-system-controller
subjects:
- kind: ServiceAccount
  name: kustomize-controller
  namespace: flux-system
- kind: ServiceAccount
  name: helm-controller
  namespace: flux-system
- kind: ServiceAccount
  name: notification-controller
  namespace: flux-system
```

### Secret Management with SOPS

```bash
# Install SOPS
brew install sops

# Generate age key
age-keygen -o age.key

# Encrypt secrets
sops --age=$(cat age.key | grep "public key:" | cut -d' ' -f4) --encrypt \
  --encrypted-regex '^(data|stringData)$' secrets.yaml
```

## 📊 Monitoring and Observability

### Prometheus Integration

```yaml
# gitops/flux-system/monitoring.yaml
apiVersion: v1
kind: Service
metadata:
  name: flux-system-metrics
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-system
spec:
  ports:
  - name: http
    port: 8080
    protocol: TCP
  selector:
    app.kubernetes.io/name: flux-system
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: flux-system
  namespace: flux-system
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: flux-system
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
```

### Grafana Dashboards

```yaml
# gitops/flux-system/grafana-dashboard.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  flux-dashboard.json: |
    {
      "dashboard": {
        "title": "Flux CD Overview",
        "panels": [
          {
            "title": "Reconciliation Status",
            "type": "stat",
            "targets": [
              {
                "expr": "sum(flux_reconcile_success_total) by (controller)"
              }
            ]
          },
          {
            "title": "K8sGPT Analysis",
            "type": "table",
            "targets": [
              {
                "expr": "k8sgpt_analysis_total"
              }
            ]
          }
        ]
      }
    }
```

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/flux-sync.yml
name: Flux Sync
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  flux-sync:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Flux CLI
      uses: fluxcd/flux2/action@main
      with:
        version: latest
        
    - name: Validate Flux manifests
      run: |
        flux validate --path ./clusters/production
        
    - name: Deploy to staging
      if: github.ref == 'refs/heads/main'
      run: |
        flux reconcile kustomization infrastructure-staging
        
    - name: Deploy to production
      if: github.ref == 'refs/heads/main' && github.event_name == 'push'
      run: |
        flux reconcile kustomization infrastructure-production
```

### Webhook Configuration

```yaml
# gitops/flux-system/webhooks.yaml
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Receiver
metadata:
  name: github-receiver
  namespace: flux-system
spec:
  type: github
  events:
    - "push"
    - "pull_request"
  resources:
    - kind: GitRepository
      name: flux-system
      namespace: flux-system
  secretRef:
    name: github-webhook-token
---
apiVersion: v1
kind: Secret
metadata:
  name: github-webhook-token
  namespace: flux-system
stringData:
  token: "${GITHUB_WEBHOOK_SECRET}"
  address: "https://flux-webhook.example.com/webhook"
```

## 🧪 Testing and Validation

### Automated Testing

```bash
# Run comprehensive tests
./scripts/flux-test-suite.sh \
  --test-cluster=true \
  --test-qwen=true \
  --test-monitoring=true \
  --generate-report
```

### Health Checks

```yaml
# gitops/flux-system/health-checks.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: infrastructure-health
  namespace: flux-system
spec:
  interval: 5m
  sourceRef:
    kind: GitRepository
    name: flux-system
  path: ./core/resources/tenants/3-workloads
  prune: true
  wait: true
  timeout: 10m
  healthChecks:
    - kind: Deployment
      name: qwen-llm
      namespace: qwen-system
    - kind: Deployment
      name: k8sgpt
      namespace: flux-system
    - kind: Service
      name: flux-system-metrics
      namespace: flux-system
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Bootstrap Failures
```bash
# Check permissions
kubectl auth can-i create namespaces
kubectl auth can-i create customresourcedefinitions

# Verify Git access
flux check --namespace flux-system
ssh -T git@github.com
```

#### 2. Qwen Integration Issues
```bash
# Check Qwen pod status
kubectl get pods -n qwen-system
kubectl logs -n qwen-system deployment/qwen-llm

# Verify K8sGPT connection
kubectl get k8sgpt -n flux-system
kubectl logs -n flux-system deployment/k8sgpt
```

#### 3. Reconciliation Failures
```bash
# Force reconciliation
flux reconcile source git flux-system
flux reconcile kustomization infrastructure

# Check controller logs
kubectl logs -n flux-system deployment/kustomize-controller
```

### Debug Commands

```bash
# Comprehensive status check
flux check
flux get sources all
flux get kustomizations all
flux get helmreleases all

# Qwen-specific debugging
kubectl get k8sgpt -A -o wide
kubectl describe k8sgpt k8sgpt-qwen -n flux-system

# Performance monitoring
kubectl top pods -n flux-system
kubectl top pods -n qwen-system
```

## 🚀 Advanced Features

### Multi-Cluster Management

```yaml
# clusters/production/multi-cluster.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: cluster-prod
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: flux-system
  path: ./clusters/production
  kubeConfig:
    secretRef:
      name: production-cluster-kubeconfig
---
apiVersion: v1
kind: Secret
metadata:
  name: production-cluster-kubeconfig
  namespace: flux-system
stringData:
  kubeconfig: |
    apiVersion: v1
    kind: Config
    clusters:
    - name: production
      cluster:
        server: https://production.example.com
        certificate-authority-data: <base64-ca>
    contexts:
    - name: production
      context:
        cluster: production
        user: admin
    current-context: production
```

### Image Update Automation

```yaml
# gitops/flux-system/image-automation.yaml
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageRepository
metadata:
  name: app-repo
  namespace: flux-system
spec:
  interval: 5m
  image: ghcr.io/your-org/app
---
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImagePolicy
metadata:
  name: app-policy
  namespace: flux-system
spec:
  imageRepositoryRef:
    name: app-repo
  policy:
    semver:
      range: ">=1.0.0"
---
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageUpdateAutomation
metadata:
  name: app-updates
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: flux-system
  git:
    commit:
      author:
        email: flux-bot@users.noreply.github.com
        name: fluxcd-bot
  update:
    path: ./apps/overlays/production
    strategy: Setters
```

### Progressive Delivery with Flagger

```yaml
# gitops/flux-system/flagger.yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: app-canary
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app
  progressDeadlineSeconds: 60
  service:
    port: 80
    targetPort: 8080
  analysis:
    interval: 30s
    threshold: 10
    metrics:
    - name: request-success-rate
      threshold: 99
      interval: 30s
    - name: request-duration
      threshold: 500
      interval: 30s
```

## 📚 Best Practices

### Repository Organization
1. **Use Kustomize Overlays**: Separate base from environment-specific configs
2. **Version Pinning**: Pin critical dependencies for stability
3. **Dependency Management**: Use `dependsOn` for explicit ordering
4. **Secret Management**: Encrypt all secrets with SOPS

### Security Practices
1. **Least Privilege**: Use minimal RBAC permissions
2. **Network Isolation**: Implement strict NetworkPolicies
3. **Image Verification**: Use Cosign for production images
4. **Audit Logging**: Enable comprehensive logging

### Operational Practices
1. **Health Checks**: Configure comprehensive health checks
2. **Monitoring**: Set up Prometheus monitoring and alerting
3. **Backup**: Regular backup of Git repository and configs
4. **Testing**: Validate changes in staging before production

## 🆘 Support and Community

- **Documentation**: [Flux CD Docs](https://fluxcd.io/docs/)
- **Community**: [Flux CD Slack](https://cloud-native.slack.com/archives/CK9J80DPJ)
- **GitHub**: [Flux CD Repository](https://github.com/fluxcd/flux2)
- **Issues**: [Report Bugs](https://github.com/fluxcd/flux2/issues)

---

This comprehensive guide provides everything needed for successful Flux CD integration with Qwen LLM and K8sGPT, including automated setup, monitoring, security, and best practices.

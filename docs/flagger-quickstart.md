# Flagger Progressive Delivery Quickstart

## Overview

Flagger is a CNCF graduated project that provides progressive delivery capabilities for Kubernetes applications. This guide will help you get started with Flagger in your Agentic Reconciliation Engine.

## Prerequisites

- Kubernetes cluster (v1.19+)
- kubectl configured
- Helm 3.x installed
- Service mesh (Istio/Linkerd/Kuma) or ingress controller (NGINX/Contour/Traefik)
- Prometheus for metrics (recommended)

## Installation

### Option 1: Automated Installation with AI Skill

Use the `flagger-automation` skill for automated installation:

```bash
# Install Flagger with Istio provider
curl -X POST "http://ai-agent:8080/api/skills/flagger-automation/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "install",
    "strategy": "canary",
    "targetResource": "example-app",
    "provider": "istio",
    "namespace": "flagger-system",
    "enable_monitoring": true
  }'
```

### Option 2: Manual Installation

#### Step 1: Add Flagger Helm Repository

```bash
helm repo add flagger https://flagger.app
helm repo update
```

#### Step 2: Install Flagger

**With Istio:**
```bash
helm upgrade --install flagger flagger/flagger \
  --namespace flagger-system \
  --create-namespace \
  --set meshProvider=istio \
  --set crds.install=true \
  --wait
```

**With NGINX Ingress:**
```bash
helm upgrade --install flagger flagger/flagger \
  --namespace flagger-system \
  --create-namespace \
  --set meshProvider=nginx \
  --set crds.install=true \
  --wait
```

#### Step 3: Verify Installation

```bash
kubectl get pods -n flagger-system -l app=flagger
kubectl get crd | grep flagger
```

## Quickstart Examples

### Example 1: Basic Canary Deployment

Create a simple canary for a web application:

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: frontend
  namespace: default
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: frontend
  service:
    port: 80
    targetPort: 8080
  analysis:
    interval: 10s
    threshold: 99
    iterations: 10
    metrics:
    - name: request-success-rate
      threshold: 99
      interval: 1m
    - name: request-duration
      threshold: 500
      interval: 1m
```

Apply the configuration:
```bash
kubectl apply -f frontend-canary.yaml
```

### Example 2: A/B Testing

Configure A/B testing with equal traffic split:

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: api-service
  namespace: default
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  service:
    port: 80
    targetPort: 8000
  analysis:
    interval: 30s
    threshold: 95
    iterations: 1
    metrics:
    - name: request-success-rate
      threshold: 95
      interval: 30s
  canarySteps:
  - setWeight: 50
  - pause:
      duration: 10m
```

### Example 3: Blue/Green Deployment

Set up blue/green deployment with instant traffic switch:

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: backend-service
  namespace: default
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-service
  service:
    port: 80
    targetPort: 9000
  progressDeadlineSeconds: 600
  analysis:
    interval: 15s
    threshold: 99
    metrics:
    - name: request-success-rate
      threshold: 99
      interval: 1m
```

## Provider-Specific Configurations

### Istio Service Mesh

Ensure Istio is installed and configured:

```bash
# Check Istio installation
kubectl get pods -n istio-system
kubectl get crd | grep istio
```

Flagger will automatically create Istio virtual services and destination rules for traffic routing.

### Linkerd Service Mesh

Install Linkerd and enable automatic sidecar injection:

```bash
# Install Linkerd
linkerd install | kubectl apply -f -
linkerd check

# Enable injection for your namespace
kubectl annotate namespace default linkerd.io/inject=enabled
```

### NGINX Ingress Controller

Install NGINX Ingress Controller:

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace
```

## Monitoring and Observability

### Prometheus Integration

Flagger automatically exposes metrics for monitoring:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: flagger
  namespace: flagger-system
  labels:
    app.kubernetes.io/name: flagger
spec:
  selector:
    matchLabels:
      app: flagger
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

### Grafana Dashboard

Import the Flagger dashboard to visualize deployment progress:

1. Navigate to Grafana
2. Import dashboard ID: 11479 (Flagger Progressive Delivery)
3. Configure Prometheus data source

### Key Metrics

- `flagger_canary_total`: Number of canary deployments
- `flagger_canary_success_total`: Number of successful canary deployments
- `flagger_canary_failure_total`: Number of failed canary deployments
- `flagger_canary_duration_seconds`: Duration of canary deployments

## GitOps Integration

### Flux Integration

Add Flagger resources to your Flux GitOps repository:

```yaml
# kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- flagger-install.yaml
- frontend-canary.yaml
- monitoring/
```

### ArgoCD Integration

Configure ArgoCD to sync Flagger resources:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: flagger-configs
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/flagger-configs
    targetRevision: HEAD
    path: .
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## Advanced Features

### Custom Metrics

Add custom metrics for analysis:

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: advanced-app
spec:
  # ... other fields
  analysis:
    metrics:
    - name: custom-error-rate
      threshold: 1
      interval: 30s
      query: 'sum(rate(custom_errors_total{namespace="{{ namespace }}"}[2m]))'
    - name: business-metric
      threshold: 1000
      interval: 1m
      query: 'sum(business_transactions_total{namespace="{{ namespace }}"})'
```

### Webhooks

Configure webhooks for custom validation:

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: webhook-app
spec:
  # ... other fields
  analysis:
    webhooks:
    - name: load-test
      url: http://loadtester.default/
      timeout: 30s
      metadata:
        cmd: "hey -z 1m -q 10 -c 2 http://frontend.default/"
    - name: slack-notify
      url: http://slack-bot.default/
      timeout: 10s
      metadata:
        channel: "#deployments"
```

### Analysis Templates

Create reusable analysis templates:

```yaml
apiVersion: flagger.app/v1beta1
kind: MetricTemplate
metadata:
  name: latency-percentile
spec:
  provider:
    address: http://prometheus.monitoring.svc.cluster.local:9090
    type: prometheus
  query: |
    histogram_quantile(
      {{ .threshold }},
      sum(rate(http_request_duration_seconds_bucket{
        namespace="{{ namespace }}",
        service="{{ service }}",
        le="{{ .interval }}"
      }[2m])) by (le)
    )
```

## Troubleshooting

### Common Issues

1. **Flagger pod not starting**
   ```bash
   kubectl logs -n flagger-system deployment/flagger
   kubectl get events -n flagger-system
   ```

2. **Canary stuck in progressing state**
   ```bash
   kubectl describe canary <name>
   kubectl get canary <name> -o yaml
   ```

3. **Metrics not available**
   ```bash
   kubectl port-forward -n flagger-system svc/flagger 8080:8080
   curl http://localhost:8080/metrics
   ```

### Debug Commands

```bash
# Check Flagger status
kubectl get canaries -A

# Get detailed canary information
kubectl describe canary <name> -n <namespace>

# Check Flagger logs
kubectl logs -n flagger-system deployment/flagger -f

# Verify service mesh configuration
kubectl get virtualservices -n <namespace>
kubectl get destinationrules -n <namespace>
```

## Best Practices

1. **Start with conservative thresholds** (99% success rate, 500ms duration)
2. **Use appropriate analysis intervals** (10-30 seconds)
3. **Implement proper monitoring** before enabling canary deployments
4. **Test in staging environments** first
5. **Configure proper alerting** for deployment failures
6. **Use GitOps** for configuration management
7. **Document rollback procedures**

## Next Steps

- Explore advanced deployment strategies
- Set up comprehensive monitoring and alerting
- Integrate with CI/CD pipelines
- Implement automated testing
- Configure multi-environment deployments

## Resources

- [Flagger Documentation](https://fluxcd.io/flagger/)
- [Flagger GitHub](https://github.com/fluxcd/flagger)
- [Progressive Delivery Tutorials](https://fluxcd.io/flagger/tutorials/)
- [CNCF Project Page](https://www.cncf.io/projects/flux/)

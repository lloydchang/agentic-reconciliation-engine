# Argo CD Quickstart Guide

## Overview

This guide will help you get started with Argo CD, a declarative, GitOps continuous delivery tool for Kubernetes. This integration includes K8sGPT with Qwen LLM for intelligent Kubernetes analysis and troubleshooting.

## Prerequisites

- Kubernetes cluster (v1.20+)
- kubectl configured to connect to your cluster
- Helm 3.x (optional, for alternative installation)
- Git repository access
- At least 4GB of available memory for Qwen LLM

## Quick Start (5 Minutes)

### 1. Install Argo CD

```bash
# Create namespace
kubectl create namespace argocd

# Install Argo CD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Or use our custom installation with GitOps integration
kubectl apply -f gitops/argocd/namespace.yaml
kubectl apply -f gitops/argocd/install.yaml
```

### 2. Access Argo CD UI

```bash
# Port forward to access Argo CD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Open browser to http://localhost:8080
# Login with username: admin, password: argocd123
```

### 3. Configure Git Repository

```bash
# Add your Git repository to Argo CD
argocd repo add https://github.com/lloydchang/gitops-infra-control-plane.git --type git

# Or use the pre-configured repository in our setup
```

### 4. Deploy Applications

```bash
# Apply the root application
kubectl apply -f gitops/argocd/applications/root-app.yaml

# This will automatically deploy:
# - AI Infrastructure (K8sGPT with Qwen)
# - K8sGPT application
# - Additional applications configured in the applications directory
```

### 5. Verify Installation

```bash
# Check Argo CD status
kubectl get pods -n argocd

# Check application status
argocd app list

# Check K8sGPT deployment
kubectl get pods -n k8sgpt-system
```

## Detailed Setup

### Argo CD Installation Options

#### Option 1: Manifest Installation (Recommended for Development)

```bash
# Apply namespace
kubectl apply -f gitops/argocd/namespace.yaml

# Apply complete installation
kubectl apply -f gitops/argocd/install.yaml

# Verify installation
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd
```

#### Option 2: Helm Installation (Recommended for Production)

```bash
# Add Argo CD Helm repository
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

# Install Argo CD
helm install argocd argo/argo-cd \
  --namespace argocd \
  --create-namespace \
  --set server.service.type=LoadBalancer \
  --set configs.repository.urls="https://github.com/lloydchang/gitops-infra-control-plane.git"
```

### K8sGPT with Qwen LLM Setup

#### Option 1: LocalAI with Qwen (Private, On-Premise)

```bash
# Deploy Qwen LocalAI
kubectl apply -f gitops/argocd/k8sgpt/qwen-deployment.yaml
kubectl apply -f gitops/argocd/k8sgpt/qwen-config.yaml

# Wait for Qwen to be ready
kubectl wait --for=condition=available --timeout=600s deployment/qwen-localai -n k8sgpt-system

# Deploy K8sGPT
kubectl apply -f gitops/argocd/k8sgpt/k8sgpt-deployment.yaml
kubectl apply -f gitops/argocd/k8sgpt/configmap.yaml
```

#### Option 2: External Qwen API (Cloud-based)

```bash
# Create secret for Qwen API key
kubectl create secret generic k8sgpt-secrets \
  --from-literal=qwen-api-key=your-qwen-api-key \
  -n k8sgpt-system

# Update configmap to use external API
# Edit gitops/argocd/k8sgpt/configmap.yaml and uncomment the openai backend section

# Deploy K8sGPT
kubectl apply -f gitops/argocd/k8sgpt/k8sgpt-deployment.yaml
```

### Model Download and Setup

For LocalAI setup, you need to download Qwen models:

```bash
# Download Qwen2.5 Coder 7B model
wget https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q4_0.gguf

# Copy to persistent volume
kubectl cp qwen2.5-coder-7b-instruct-q4_0.gguf qwen-localai-xxxx-xxxx:/models/
```

## Configuration

### Argo CD Configuration

Edit `gitops/argocd/install.yaml` to customize:

- **Server Type**: Change from LoadBalancer to ClusterIP for internal access
- **Authentication**: Configure OIDC, SAML, or LDAP
- **Resource Limits**: Adjust CPU/memory limits based on cluster size
- **Repositories**: Add multiple Git repositories

### K8sGPT Configuration

Edit `gitops/argocd/k8sgpt/configmap.yaml` to customize:

- **Analysis Filters**: Specify which Kubernetes resources to analyze
- **Backend**: Switch between LocalAI, OpenAI-compatible APIs, or Ollama
- **Prompts**: Customize system prompts for specific use cases
- **Integrations**: Configure Prometheus, Grafana, and Argo CD integrations

### Qwen Model Configuration

Edit `gitops/argocd/k8sgpt/qwen-config.yaml` to customize:

- **Model Parameters**: Temperature, top_p, max_tokens
- **Resource Allocation**: CPU, memory, and GPU settings
- **Template**: Chat completion templates
- **Performance**: Caching, preloading, and optimization settings

## Usage

### Argo CD CLI

```bash
# Install Argo CD CLI
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd

# Login to Argo CD
argocd login localhost:8080

# List applications
argocd app list

# Sync application
argocd app sync k8sgpt

# Get application status
argocd app get k8sgpt
```

### K8sGPT Analysis

```bash
# Port forward to K8sGPT API
kubectl port-forward svc/k8sgpt -n k8sgpt-system 8080:8080

# Run analysis
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{"namespace": "default", "filters": ["Deployment", "Pod"]}'

# Get detailed explanation
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{"namespace": "default", "explain": true, "with-doc": true}'
```

### GitOps Workflow

1. **Make Changes**: Update Kubernetes manifests in Git
2. **Commit Changes**: `git commit && git push`
3. **Automatic Sync**: Argo CD detects changes and applies them
4. **Monitor**: Check Argo CD UI for deployment status
5. **Analyze**: K8sGPT analyzes resources and provides insights

## Monitoring and Troubleshooting

### Argo CD Monitoring

```bash
# Check Argo CD server logs
kubectl logs -f deployment/argocd-server -n argocd

# Check application controller logs
kubectl logs -f deployment/argocd-application-controller -n argocd

# Check repository server logs
kubectl logs -f deployment/argocd-repo-server -n argocd
```

### K8sGPT Monitoring

```bash
# Check K8sGPT logs
kubectl logs -f deployment/k8sgpt -n k8sgpt-system

# Check Qwen LocalAI logs
kubectl logs -f deployment/qwen-localai -n k8sgpt-system

# Check resource usage
kubectl top pods -n k8sgpt-system
```

### Common Issues

#### Argo CD Issues

1. **Repository Access Errors**
   - Check Git repository permissions
   - Verify SSH keys or tokens
   - Check network connectivity

2. **Sync Failures**
   - Check resource manifests for syntax errors
   - Verify RBAC permissions
   - Check cluster resource availability

3. **UI Access Issues**
   - Verify port-forward is running
   - Check service configuration
   - Verify authentication credentials

#### K8sGPT Issues

1. **Model Loading Errors**
   - Check model file permissions
   - Verify storage volume mounting
   - Check available memory

2. **API Connection Errors**
   - Verify Qwen LocalAI is running
   - Check service endpoints
   - Verify network policies

3. **Analysis Timeouts**
   - Increase timeout values
   - Check resource limits
   - Optimize model parameters

## Advanced Configuration

### Multi-Environment Setup

Create separate Argo CD applications for different environments:

```yaml
# production-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: production-apps
  namespace: argocd
spec:
  source:
    repoURL: https://github.com/lloydchang/gitops-infra-control-plane.git
    targetRevision: main
    path: overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
```

### Progressive Delivery

Configure canary deployments and progressive delivery:

```yaml
# canary-deployment.yaml
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

### Security Best Practices

1. **Enable RBAC**: Configure proper role-based access control
2. **Use Secrets**: Store sensitive data in Kubernetes secrets
3. **Network Policies**: Restrict inter-service communication
4. **Resource Limits**: Set appropriate CPU/memory limits
5. **Audit Logging**: Enable audit logging for compliance

## Integration with Existing Tools

### Prometheus Integration

```yaml
# prometheus-rules.yaml
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

### Grafana Dashboards

Import pre-built dashboards for:
- Argo CD application status
- K8sGPT analysis metrics
- Qwen model performance
- GitOps pipeline health

### CI/CD Integration

```bash
# GitHub Actions example
- name: Sync Argo CD
  run: |
    argocd login $ARGOCD_SERVER --username $ARGOCD_USERNAME --password $ARGOCD_PASSWORD
    argocd app sync $APPLICATION_NAME --force
```

## Performance Optimization

### Argo CD Optimization

1. **Resource Limits**: Adjust based on cluster size
2. **Sync Intervals**: Configure appropriate sync frequencies
3. **Repository Caching**: Enable repository caching
4. **Concurrent Syncs**: Limit concurrent sync operations

### K8sGPT Optimization

1. **Model Quantization**: Use quantized models for faster inference
2. **Batch Processing**: Analyze multiple resources together
3. **Caching**: Enable analysis result caching
4. **Resource Scaling**: Scale based on analysis workload

## Next Steps

1. **Explore Overlays**: Check `overlay/` directory for environment-specific configurations
2. **Automated Setup**: Run `scripts/setup-argocd.sh` for automated installation
3. **Monitoring**: Set up comprehensive monitoring and alerting
4. **Security**: Implement security best practices
5. **Testing**: Run the test suite to verify your setup

## Support

- **Documentation**: Check `docs/` directory for detailed guides
- **Community**: Join our Slack/Discord communities
- **Issues**: Report bugs and feature requests on GitHub
- **Examples**: Check `examples/` directory for use cases

---

**Note**: This setup is designed for development and testing. For production use, ensure proper security configurations, resource limits, and monitoring are in place.

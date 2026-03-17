# PipeCD Integration Guide

## Overview

This guide provides comprehensive documentation for integrating PipeCD, the One CD for All {applications, platforms, operations}, into the GitOps Infra Control Plane. PipeCD is integrated with Qwen LLM for advanced K8sGPT analysis capabilities.

## What is PipeCD?

PipeCD is a unified continuous delivery solution for multiple application kinds on multi-cloud environments. It enables GitOps-driven deployments with built-in analysis and AI-powered insights.

### Key Features
- **Unified Platform**: Single interface for Kubernetes, Terraform, Cloud Run, Lambda, and ECS deployments
- **GitOps Native**: Pull-request based deployment operations
- **Multi-Cloud**: AWS, GCP, Azure, and on-premise support
- **AI Analysis**: Built-in deployment analysis with Qwen LLM integration
- **Progressive Delivery**: Canary, blue-green, and rolling deployment strategies

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitOps Repo   │───▶│    PipeCD       │───▶│   Qwen LLM      │
│                 │    │   Control       │    │   Service       │
│ - App Config    │    │   Plane         │    │                 │
│ - Pipelines     │    │                 │    │ - K8s Analysis  │
└─────────────────┘    └─────────────────┘    │ - AI Insights   │
                                              └─────────────────┘
                                                     │
                                                     ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Piped Agent   │    │   K8sGPT        │    │   Target        │
│                 │    │   Analyzer      │    │   Clusters      │
│ - Deployment    │    │                 │    │                 │
│ - Monitoring    │    │ - AI Analysis   │    │ - Applications  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites
- Kubernetes cluster (v1.19+)
- kubectl configured
- Helm v3 (optional, for advanced deployments)
- Git repository for application configurations

### Automated Setup

Use the automated setup script:

```bash
# Clone the repository
git clone https://github.com/your-org/gitops-infra-control-plane.git
cd gitops-infra-control-plane

# Run automated setup
./core/ai/skills/manage-pipecd/scripts/setup-pipecd.sh
```

This will:
1. Install PipeCD control plane
2. Deploy Qwen LLM service
3. Configure K8sGPT integration
4. Set up port forwarding to PipeCD console

### Manual Installation

If you prefer manual installation:

```bash
# Install PipeCD control plane
kubectl apply -k overlay/pipecd/

# Install Qwen LLM service
kubectl apply -k overlay/pipecd/qwen/

# Install K8sGPT integration
kubectl apply -k overlay/pipecd/k8sgpt/

# Wait for all components
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=pipecd -n pipecd --timeout=600s
kubectl wait --for=condition=ready pod -l app=qwen-llm-service -n qwen-ai --timeout=600s
```

### Access PipeCD Console

```bash
# Port forward to access console
kubectl port-forward -n pipecd svc/pipecd 8080

# Open browser to http://localhost:8080
# Login with: hello-pipecd / hello-pipecd
```

## Configuration

### PipeCD Control Plane

The control plane includes:
- **Server**: Main API server and web UI
- **Cache**: Redis for session and caching
- **Database**: MySQL for persistent storage
- **MinIO**: Object storage for artifacts
- **Gateway**: API gateway for external access

### Qwen LLM Integration

Qwen provides AI-powered analysis:
- **Model**: qwen2.5-72b-instruct
- **Capabilities**: Deployment analysis, risk assessment, recommendations
- **Integration**: REST API with K8sGPT analyzer

### K8sGPT Configuration

K8sGPT analyzes Kubernetes resources:
- **Filters**: Namespace and resource type filtering
- **Analysis**: Performance, security, compliance checks
- **Insights**: AI-generated recommendations and alerts

## Application Deployment

### 1. Register Piped Agent

In the PipeCD console:
1. Go to Settings → Piped
2. Click "Add" to register a new piped agent
3. Copy the piped ID and key
4. Install piped in your target cluster:

```bash
# Install piped agent
curl -s https://raw.githubusercontent.com/pipe-cd/pipecd/master/quickstart/manifests/pipedv1-exp.yaml | \
sed -e "s/<YOUR_PIPED_ID>/YOUR_PIPED_ID/g" \
    -e "s/<YOUR_PIPED_KEY_DATA>/YOUR_PIPED_KEY/g" | \
kubectl apply -f -
```

### 2. Create Application Configuration

Create `.pipe.yaml` in your application repository:

```yaml
apiVersion: pipecd.dev/v1beta1
kind: Application
metadata:
  name: my-app
spec:
  pipeline:
    stages:
      - name: K8S_CANARY_ROLLOUT
        with:
          replicas: 10%
      - name: K8S_TRAFFIC_ROUTING
        with:
          weight: 10%
      - name: WAIT_APPROVAL
      - name: K8S_PRIMARY_ROLLOUT
        with:
          replicas: 100%
      - name: K8S_TRAFFIC_ROUTING
        with:
          weight: 100%
  analysis:
    metrics:
      - name: success_rate
        query: "rate(http_requests_total{status=~'2..'}[5m])"
      - name: error_rate
        query: "rate(http_requests_total{status=~'5..'}[5m])"
```

### 3. Deploy Application

```bash
# Sync application (trigger deployment)
kubectl apply -f .pipe.yaml

# Or use PipeCD CLI
pipecd app sync --app my-app
```

## AI-Powered Analysis

### K8sGPT Integration

PipeCD integrates with K8sGPT for AI analysis:

```bash
# Run analysis on deployment
kubectl exec -n pipecd deployment/k8sgpt-analyzer -- \
  k8sgpt analyze --deployment my-deployment --namespace default --ai

# Get AI recommendations
kubectl exec -n pipecd deployment/k8sgpt-analyzer -- \
  k8sgpt analyze --deployment my-deployment --recommendations
```

### Analysis Webhook

Use the analysis webhook for programmatic access:

```bash
# Test analysis endpoint
curl -X POST http://k8sgpt-webhook.pipecd.svc.cluster.local:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "deployment_data": {
      "apiVersion": "apps/v1",
      "kind": "Deployment",
      "metadata": {"name": "my-app"},
      "spec": {"replicas": 3}
    },
    "analysis_type": "deployment"
  }'
```

## Monitoring and Observability

### Metrics Integration

PipeCD integrates with Prometheus and Grafana:

```yaml
# Prometheus scrape configuration
scrape_configs:
  - job_name: 'pipecd'
    static_configs:
      - targets: ['pipecd.pipecd.svc.cluster.local:8080']
    metrics_path: '/metrics'

  - job_name: 'qwen-llm'
    static_configs:
      - targets: ['qwen-llm-service.qwen-ai.svc.cluster.local:8080']
    metrics_path: '/metrics'
```

### Dashboards

Access Grafana dashboards for:
- Deployment metrics and trends
- AI analysis insights
- Performance monitoring
- Error tracking and alerting

## Security

### Authentication and Authorization

PipeCD supports multiple auth methods:
- Static admin accounts (quickstart)
- OIDC integration
- LDAP/Active Directory
- SSO providers

### RBAC Configuration

```yaml
# Project-level permissions
apiVersion: pipecd.dev/v1beta1
kind: Project
metadata:
  name: production
spec:
  rbac:
    roles:
      - name: developer
        permissions:
          - APPLICATION_READ
          - DEPLOYMENT_TRIGGER
      - name: admin
        permissions:
          - "*"
```

### Secrets Management

PipeCD integrates with external secret managers:
- AWS Secrets Manager
- GCP Secret Manager
- Azure Key Vault
- HashiCorp Vault

## Troubleshooting

### Common Issues

#### Piped Registration Failed
```bash
# Check piped logs
kubectl logs -n pipecd deployment/piped

# Verify configuration
kubectl get piped -n pipecd
kubectl describe piped your-piped-name -n pipecd
```

#### Deployment Stuck
```bash
# Check deployment status
pipecd deployment list --app your-app

# View deployment logs
pipecd deployment logs --deployment-id <deployment-id>
```

#### AI Analysis Not Working
```bash
# Check Qwen service
kubectl get pods -n qwen-ai

# Test Qwen connectivity
kubectl exec -n pipecd deployment/k8sgpt-analyzer -- \
  curl -f http://qwen-llm-service.qwen-ai.svc.cluster.local:8080/health
```

### Debug Commands

```bash
# Check all components
kubectl get pods -n pipecd
kubectl get pods -n qwen-ai

# View component logs
kubectl logs -n pipecd deployment/pipecd-server --tail=100
kubectl logs -n qwen-ai deployment/qwen-llm-service --tail=100

# Test connectivity
kubectl exec -n pipecd deployment/pipecd-server -- curl -f http://qwen-llm-service.qwen-ai.svc.cluster.local:8080/health
```

## Testing

### Automated Testing

Run the comprehensive test suite:

```bash
# Run all tests
./core/ai/skills/manage-pipecd/scripts/test-pipecd.sh

# Run specific test
./core/ai/skills/manage-pipecd/scripts/test-pipecd.sh test_pipecd_control_plane
```

### Manual Testing

Test individual components:

```bash
# Test PipeCD console access
curl -f http://localhost:8080/healthz

# Test Qwen LLM service
curl -f http://qwen-llm-service.qwen-ai.svc.cluster.local:8080/health

# Test K8sGPT webhook
curl -f http://k8sgpt-webhook.pipecd.svc.cluster.local:8000/health
```

## Advanced Configuration

### Custom Deployment Strategies

```yaml
apiVersion: pipecd.dev/v1beta1
kind: Application
metadata:
  name: advanced-app
spec:
  pipeline:
    stages:
      - name: K8S_CANARY_ROLLOUT
        with:
          replicas: "20%"
          loadBalancer:
            primary: "primary-lb"
            canary: "canary-lb"
      - name: ANALYSIS
        with:
          duration: 10m
          logs:
            - name: application
              pattern: "ERROR|WARN"
          metrics:
            - name: success_rate
              provider: prometheus
              query: "rate(http_requests_total{status=~'2..'}[5m])"
              expected:
                max: 0.95
      - name: K8S_PROMOTE
        with:
          percentage: 100
```

### Multi-Environment Deployments

```yaml
apiVersion: pipecd.dev/v1beta1
kind: Application
metadata:
  name: multi-env-app
spec:
  environments:
    - name: development
      labels:
        env: dev
    - name: staging
      labels:
        env: staging
    - name: production
      labels:
        env: prod
  pipeline:
    stages:
      - name: DEPLOY_TO_DEV
        target: development
      - name: DEPLOY_TO_STAGING
        target: staging
      - name: WAIT_MANUAL_APPROVAL
      - name: DEPLOY_TO_PRODUCTION
        target: production
```

## Integration Examples

### Jenkins Integration

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                // Build your application
                sh 'docker build -t my-app:${BUILD_NUMBER} .'
            }
        }
        stage('Push to PipeCD') {
            steps {
                // Trigger PipeCD deployment
                sh '''
                curl -X POST http://pipecd.pipecd.svc.cluster.local:8080/api/v1/applications/my-app/sync \
                  -H "Authorization: Bearer ${PIPECD_TOKEN}" \
                  -d '{"head_commit": {"hash": "'${GIT_COMMIT}'"}}'
                '''
            }
        }
    }
}
```

### GitHub Actions Integration

```yaml
name: Deploy with PipeCD
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and push
        run: |
          docker build -t my-app:${{ github.sha }} .
          docker push my-app:${{ github.sha }}
      
      - name: Trigger PipeCD deployment
        run: |
          curl -X POST ${{ secrets.PIPECD_URL }}/api/v1/applications/my-app/sync \
            -H "Authorization: Bearer ${{ secrets.PIPECD_TOKEN }}" \
            -d '{"head_commit": {"hash": "'${{ github.sha }}'"}}'
```

## Best Practices

### 1. Pipeline Design
- Use canary deployments for critical applications
- Implement automated rollback triggers
- Configure appropriate analysis stages
- Set up proper approval gates

### 2. Security
- Use least privilege access for piped agents
- Enable audit logging for all operations
- Implement secrets management best practices
- Regular security scanning and updates

### 3. Performance
- Optimize pipeline stages for faster deployments
- Use parallel analysis where possible
- Monitor resource utilization
- Implement caching for repeated operations

### 4. Monitoring
- Set up comprehensive alerting
- Track deployment metrics over time
- Use AI insights for optimization
- Implement proper logging and tracing

## Support and Community

### Resources
- [PipeCD Documentation](https://pipecd.dev/docs/)
- [Qwen Documentation](https://qwen.readthedocs.io/)
- [K8sGPT Documentation](https://docs.k8sgpt.ai/)
- [CNCF PipeCD](https://cncf.io/projects/pipecd/)

### Getting Help
- [PipeCD GitHub Issues](https://github.com/pipe-cd/pipecd/issues)
- [CNCF Slack #pipecd](https://slack.cncf.io/)
- [Community Meetings](https://bit.ly/pipecd-mtg-notes)

### Contributing
- [PipeCD Contributing Guide](https://github.com/pipe-cd/pipecd/blob/master/CONTRIBUTING.md)
- [Code of Conduct](https://github.com/pipe-cd/pipecd/blob/master/CODE_OF_CONDUCT.md)

---

## Quick Reference

### Useful Commands

```bash
# Check PipeCD status
kubectl get pods -n pipecd
kubectl get pods -n qwen-ai

# Access console
kubectl port-forward -n pipecd svc/pipecd 8080

# View logs
kubectl logs -n pipecd deployment/pipecd-server -f
kubectl logs -n qwen-ai deployment/qwen-llm-service -f

# Run tests
./core/ai/skills/manage-pipecd/scripts/test-pipecd.sh

# Cleanup
kubectl delete ns pipecd qwen-ai
```

### Configuration Files
- `overlay/pipecd/kustomization.yaml` - Main PipeCD configuration
- `overlay/pipecd/qwen/qwen-llm-service.yaml` - Qwen LLM service
- `overlay/pipecd/k8sgpt/k8sgpt-config.yaml` - K8sGPT integration

### Environment Variables
- `PIPECD_NAMESPACE` - PipeCD namespace (default: pipecd)
- `QWEN_NAMESPACE` - Qwen namespace (default: qwen-ai)
- `QWEN_MODEL` - Qwen model (default: qwen2.5-72b-instruct)

This comprehensive integration brings the power of PipeCD's unified continuous delivery with AI-driven analysis using Qwen LLM, enabling intelligent, automated, and observable deployments across your infrastructure.

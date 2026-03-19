---
name: manage-pipecd
description: >
  Manages PipeCD continuous delivery operations including deployment, configuration,
  monitoring, and integration with Qwen LLM for K8sGPT. Use when setting up PipeCD,
  configuring applications, managing deployments, or integrating with AI-powered analysis.
license: AGPLv3
metadata:
  author: agentic-reconciliation-engine
  version: "1.0"
  category: enterprise
  risk-level: medium
  autonomy: conditional
  layer: temporal
  human_gate: PR approval required for production deployment changes
compatibility: Requires Kubernetes cluster, kubectl, PipeCD CLI, and access to Git repositories
allowed-tools: Bash Read Write Grep Curl
---

# PipeCD Manager — Enterprise Continuous Delivery Automation

## Purpose
Manages PipeCD continuous delivery operations across multi-cloud environments with AI-powered analysis and automation capabilities.

## When to Use
- **Setting up PipeCD**: Initial installation and configuration of PipeCD control plane
- **Application Deployment**: Deploy and manage applications through PipeCD pipelines
- **Configuration Management**: Configure PipeCD components, projects, and piped agents
- **AI Integration**: Integrate Qwen LLM for K8sGPT analysis and automated insights
- **Monitoring & Observability**: Set up monitoring, alerting, and performance analysis
- **Multi-Platform Support**: Deploy Kubernetes, Terraform, Cloud Run, Lambda, and ECS applications

## Capabilities

### Core PipeCD Operations
- Control plane installation and configuration
- Piped agent registration and management
- Application deployment pipeline configuration
- GitOps workflow automation
- Multi-cloud application deployment

### AI-Powered Features
- Qwen LLM integration for K8sGPT analysis
- Automated deployment risk assessment
- Performance anomaly detection
- Intelligent rollback recommendations
- Natural language deployment queries

### Platform Support
- **Kubernetes**: Full manifest management and Helm chart support
- **Terraform**: Infrastructure as code deployment
- **Google Cloud Run**: Serverless application deployment
- **AWS Lambda**: Function deployment and management
- **AWS ECS**: Container service deployment

## Implementation

### 1. PipeCD Control Plane Setup
```bash
# Create namespace and install control plane
kubectl create namespace pipecd
kubectl apply -n pipecd -f https://raw.githubusercontent.com/pipe-cd/pipecd/master/quickstart/manifests/control-plane.yaml

# Access the console
kubectl port-forward -n pipecd svc/pipecd 8080
```

### 2. Piped Agent Configuration
```yaml
apiVersion: pipecd.dev/v1beta1
kind: Piped
metadata:
  name: dev-piped
spec:
  projectID: quickstart
  config:
    apiAddress: pipecd.pipecd.svc.cluster.local:8080
    repo: 
      git:
        url: git@github.com:your-org/your-repo.git
        branch: main
        sshKey: |
          -----BEGIN RSA PRIVATE KEY-----
          ...
          -----END RSA PRIVATE KEY-----
```

### 3. Application Pipeline Definition
```yaml
apiVersion: pipecd.dev/v1beta1
kind: Application
metadata:
  name: web-app
spec:
  pipeline:
    stages:
      - name: K8S_CANARY_ROLLOUT
        with:
          replicas: 10%
      - name: K8S_TRAFFIC_ROUTING
        with:
          weight: 10%
      - name: K8S_PRIMARY_ROLLOUT
        with:
          replicas: 100%
      - name: K8S_TRAFFIC_ROUTING
        with:
          weight: 100%
```

### 4. Qwen LLM Integration for K8sGPT
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: k8sgpt-config
  namespace: pipecd
data:
  config.yaml: |
    ai:
      provider: qwen
      model: qwen2.5-72b-instruct
      endpoint: http://qwen-llm-service.ai.svc.cluster.local:8080
      apikey: "${QWEN_API_KEY}"
    analysis:
      enable_deployment_analysis: true
      enable_performance_monitoring: true
      enable_security_analysis: true
```

## Usage Examples

### Deploy Application with AI Analysis
```bash
# Deploy with automatic analysis
pipecd deploy --app web-app --with-analysis

# Get AI-powered recommendations
pipecd analyze --app web-app --insights
```

### Setup Qwen Integration
```bash
# Install Qwen LLM service
kubectl apply -f overlay/pipecd/qwen/

# Configure K8sGPT with Qwen
kubectl apply -f overlay/pipecd/k8sgpt/
```

### Monitor Deployments
```bash
# Real-time deployment monitoring
pipecd monitor --app web-app --real-time

# AI-powered anomaly detection
pipecd analyze --app web-app --anomaly-detection
```

## Integration Points

### 1. GitOps Integration
- Seamless integration with existing Git workflows
- PR-based deployment approvals
- Automated testing and validation

### 2. Monitoring Stack
- Prometheus metrics integration
- Grafana dashboards for deployment insights
- Alertmanager rules for deployment failures

### 3. CI/CD Pipeline
- Jenkins pipeline integration
- GitHub Actions workflows
- Azure DevOps pipeline support

### 4. Multi-Cloud Support
- AWS EKS, GCP GKE, Azure AKS support
- Terraform state management
- Cross-cloud deployment strategies

## Safety and Compliance

### Risk Assessment
- Automatic deployment risk scoring
- Rollback capability verification
- Compliance policy validation

### Human Gates
- Production deployment approvals
- Sensitive configuration changes
- Cross-environment promotions

### Audit Trail
- Complete deployment history
- Change attribution and tracking
- Compliance reporting

## Troubleshooting

### Common Issues
1. **Piped Registration**: Ensure correct project ID and API address
2. **Git Repository Access**: Verify SSH keys and repository permissions
3. **Qwen Integration**: Check LLM service connectivity and API keys
4. **Pipeline Failures**: Review application configuration and resource limits

### Debug Commands
```bash
# Check PipeCD components
kubectl get pods -n pipecd

# Check piped status
pipecd piped list

# Debug application deployment
pipecd app get --app web-app --debug

# Check Qwen integration
kubectl logs -n pipecd deployment/k8sgpt-analyzer
```

## Best Practices

### 1. Pipeline Design
- Use canary deployments for critical applications
- Implement automated rollback triggers
- Configure appropriate analysis stages

### 2. Security
- Secure piped configuration with secrets
- Use least privilege access for Git repositories
- Enable audit logging for all operations

### 3. Performance
- Optimize pipeline stages for faster deployments
- Use parallel analysis where possible
- Monitor resource utilization

### 4. Monitoring
- Set up comprehensive alerting
- Track deployment metrics over time
- Use AI insights for optimization

## References

- [PipeCD Documentation](https://pipecd.dev/docs/)
- [Qwen LLM Documentation](https://qwen.readthedocs.io/)
- [K8sGPT Integration Guide](https://docs.k8sgpt.ai/)
- [agentskills.io Specification](https://agentskills.io/specification)

# AI Agents Ecosystem Deployment Script

## Overview

The `deploy-ai-agents-ecosystem.sh` script provides a comprehensive, one-command deployment solution for the entire AI agents ecosystem. It automates the deployment of memory agents, temporal orchestration, skills framework, monitoring system, and web dashboard.

## Script Features

### 🚀 Complete Ecosystem Deployment
- **Memory Agents**: Rust, Go, and Python agents with persistent storage
- **Temporal Orchestration**: Workflow management and coordination
- **Skills Framework**: 64+ operational skills for cloud automation
- **AI Inference Gateway**: Centralized inference service with Llama.cpp backend
- **Web Dashboard**: Comprehensive monitoring and control interface
- **Ingress Configuration**: External access with DNS routing

### 🛠️ Automated Setup
- **Prerequisites Checking**: Validates kubectl, cluster connectivity
- **Namespace Creation**: Sets up `ai-infrastructure` namespace
- **Resource Provisioning**: PVCs, services, deployments
- **Network Configuration**: Ingress rules and service discovery
- **Health Validation**: Post-deployment verification

## Script Usage

### Quick Start
```bash
# Make script executable
chmod +x scripts/deploy-ai-agents-ecosystem.sh

# Run complete deployment
./scripts/deploy-ai-agents-ecosystem.sh
```

### Prerequisites
- Kubernetes cluster (kind, minikube, or production)
- kubectl configured with cluster access
- Helm installed (for Temporal deployment)
- Docker (optional, for image building)

### Environment Variables
```bash
# Optional configuration
export NAMESPACE="ai-infrastructure"
export TEMPORAL_VERSION="1.22.0"
export OLLAMA_MODEL="qwen2.5:0.5b"
export KUBECTL_CMD="kubectl"
```

## Deployment Components

### 1. Memory Agents
```yaml
# Deploys memory agents with:
- Rust agent (memory-agent-rust)
- Persistent storage (10Gi PVC)
- SQLite database initialization
- Resource limits (512Mi memory, 500m CPU)
- Health checks and monitoring
```

### 2. AI Inference Gateway
```yaml
# Provides centralized inference:
- Llama.cpp backend integration
- REST API endpoints
- Model serving capabilities
- Load balancing and routing
```

### 3. Temporal Orchestration
```yaml
# Workflow management:
- Temporal server (v1.22.0)
- Cassandra backend
- Frontend service
- Worker processes
- Web UI access
```

### 4. Skills Framework
```yaml
# Operational skills:
- Skills orchestrator service
- 64+ pre-defined skills
- Temporal workflow integration
- Skill execution monitoring
```

### 5. Web Dashboard
```yaml
# Monitoring interface:
- Modern React-based UI
- Real-time metrics display
- Agent management controls
- Interactive charts
- Mobile-responsive design
```

### 6. Dashboard API
```yaml
# Backend services:
- Flask-based REST API
- Real-time data endpoints
- Agent status aggregation
- Metrics collection
```

### 7. Ingress Configuration
```yaml
# External access:
- NGINX ingress controller
- DNS routing (dashboard.local, temporal.local)
- TLS termination support
- Path-based routing
```

## Script Functions

### Core Functions
```bash
check_prerequisites()     # Validates tools and cluster access
create_namespace()        # Creates ai-infrastructure namespace
deploy_inference_backend() # Sets up AI inference services
build_agent_images()      # Builds container images (skipped for demo)
deploy_ai_agents()        # Deploys memory agent pods
deploy_ai_gateway()       # Deploys inference gateway
deploy_temporal()         # Deploys Temporal orchestration
deploy_skills_framework() # Deploys skills framework
deploy_dashboard()        # Deploys web dashboard
deploy_dashboard_api()    # Deploys dashboard API service
deploy_ingress()          # Configures external access
validate_deployment()     # Verifies all components
print_access_info()       # Displays access URLs and next steps
```

### Utility Functions
```bash
log_info()     # Informational messages (blue)
log_success()  # Success messages (green)
log_warning()  # Warning messages (yellow)
log_error()    # Error messages (red)
```

## Deployment Output

### Expected Success Output
```
[INFO] Starting AI Agents Ecosystem Deployment...
[INFO] Checking prerequisites...
[SUCCESS] Connected to hub cluster
[SUCCESS] Prerequisites check passed
[INFO] Creating namespace: ai-infrastructure
[SUCCESS] Namespace created
[INFO] Deploying AI memory agents with placeholder images...
[SUCCESS] AI memory agents deployed (with placeholder images)
[INFO] Deploying AI inference gateway for skills integration...
[SUCCESS] AI inference gateway deployed - skills can now call /api/infer
[INFO] Deploying Temporal for workflow orchestration...
[SUCCESS] Temporal orchestration deployed
[INFO] Deploying operational skills framework...
[SUCCESS] Operational skills framework deployed
[INFO] Deploying agent dashboard...
[SUCCESS] Agent dashboard deployed
[INFO] Deploying dashboard API service...
[SUCCESS] Dashboard API service deployed
[INFO] Deploying ingress for external access...
[SUCCESS] Ingress deployed - Access URLs:
  - Agent Dashboard: http://dashboard.local
  - Temporal UI: http://temporal.local
[SUCCESS] Deployment validation complete
[SUCCESS] 🎉 AI Agents Ecosystem Deployed Successfully!
```

### Access Information
```
🎉 AI Agents Ecosystem Deployed Successfully!

Access URLs (add to /etc/hosts if needed):
  🌐 Agent Dashboard: http://dashboard.local
  🔄 Temporal Workflows: http://temporal.local

Features:
  ✅ AI Memory Agents (Rust/Go/Python) with persistent storage
  ✅ 64 Operational Skills via Temporal orchestration
  ✅ Llama.cpp backend integrated in memory agents
  ✅ 24/7 autonomous operation
  ✅ Real-time dashboard monitoring
  ✅ Qwen2.5 0.5B inference

Next steps:
  1. Add hosts entries: echo '127.0.0.1 dashboard.local temporal.local' >> /etc/hosts
  2. Port forward: kubectl port-forward -n ai-infrastructure svc/agent-dashboard-service 8080:80
  3. Access dashboard at http://localhost:8080
```

## Post-Deployment Access

### Port Forward (Development)
```bash
# Dashboard
kubectl port-forward svc/agent-dashboard-service 8080:80 -n ai-infrastructure
# Access: http://localhost:8080

# Dashboard API
kubectl port-forward svc/dashboard-api-service 5000:5000 -n ai-infrastructure
# Access: http://localhost:5000/api/cluster-status

# Temporal UI
kubectl port-forward svc/temporal-frontend 7233:7233 -n ai-infrastructure
# Access: http://localhost:7233
```

### Ingress (Production)
```bash
# Add to /etc/hosts
echo "127.0.0.1 dashboard.local temporal.local" >> /etc/hosts

# Access URLs:
# - Dashboard: http://dashboard.local
# - Temporal UI: http://temporal.local
# - API: http://dashboard.local/api/cluster-status
```

## Troubleshooting

### Common Issues

#### Cluster Connection Failed
```bash
# Check cluster context
kubectl config current-context

# Switch to correct context
kubectl config use-context kind-gitops-hub

# Verify cluster connectivity
kubectl cluster-info
```

#### Pod Not Starting
```bash
# Check pod status
kubectl get pods -n ai-infrastructure

# Describe pod for errors
kubectl describe pod <pod-name> -n ai-infrastructure

# Check pod logs
kubectl logs <pod-name> -n ai-infrastructure
```

#### Service Not Accessible
```bash
# Check service endpoints
kubectl get endpoints -n ai-infrastructure

# Test service connectivity
kubectl run test-pod --image=busybox --rm -it --restart=Never -- \
  wget -qO- http://<service-name>.ai-infrastructure.svc.cluster.local:<port>
```

#### Ingress Not Working
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress rules
kubectl describe ingress ai-agents-ingress -n ai-infrastructure

# Test ingress with host header
curl -H "Host: dashboard.local" http://localhost/
```

### Clean Up and Redeploy
```bash
# Clean up deployment
kubectl delete namespace ai-infrastructure

# Redeploy
./scripts/deploy-ai-agents-ecosystem.sh
```

## Customization

### Custom Configuration
```bash
# Edit script variables
NAMESPACE="custom-namespace"
TEMPORAL_VERSION="1.21.0"
OLLAMA_MODEL="llama2:7b"

# Run with custom config
./scripts/deploy-ai-agents-ecosystem.sh
```

### Custom Images
```bash
# Set custom image registry
export AGENT_IMAGE_REGISTRY="my-registry.com"
export AGENT_IMAGE_TAG="v2.0.0"

# Build and push custom images
docker build -t $AGENT_IMAGE_REGISTRY/memory-agent-rust:$AGENT_IMAGE_TAG .
docker push $AGENT_IMAGE_REGISTRY/memory-agent-rust:$AGENT_IMAGE_TAG
```

### Resource Customization
```bash
# Edit script resource limits
# In deploy_ai_agents() function:
resources:
  requests:
    memory: "1Gi"      # Increased from 256Mi
    cpu: "200m"        # Increased from 100m
  limits:
    memory: "2Gi"      # Increased from 512Mi
    cpu: "1000m"       # Increased from 500m
```

## Integration with CI/CD

### GitHub Actions
```yaml
name: Deploy AI Agents Ecosystem

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup kubectl
      uses: azure/setup-kubectl@v3
      with:
        version: 'v1.25.0'
    
    - name: Deploy Ecosystem
      run: |
        kubectl config use-context ${{ secrets.KUBE_CONTEXT }}
        chmod +x scripts/deploy-ai-agents-ecosystem.sh
        ./scripts/deploy-ai-agents-ecosystem.sh
```

### ArgoCD Integration
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ai-agents-ecosystem
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/lloydchang/gitops-infra-control-plane.git
    targetRevision: HEAD
    path: scripts
  destination:
    server: https://kubernetes.default.svc
    namespace: ai-infrastructure
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

## Security Considerations

### Network Security
- Namespace isolation with network policies
- Internal cluster communication only
- Ingress TLS termination
- Service mesh integration (optional)

### Resource Security
- Resource limits and requests
- Pod security policies
- RBAC configuration
- Secrets management

### Access Control
```bash
# Create network policy
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-agents-network-policy
  namespace: ai-infrastructure
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ai-infrastructure
EOF
```

## Monitoring and Observability

### Health Checks
The script includes built-in health checks:
- Pod readiness and liveness probes
- Service endpoint validation
- Ingress connectivity tests
- Component dependency verification

### Logging
```bash
# View all logs
kubectl logs -n ai-infrastructure -l component=memory-agent

# View specific component logs
kubectl logs -n ai-infrastructure deployment/agent-dashboard
kubectl logs -n ai-infrastructure deployment/dashboard-api
kubectl logs -n ai-infrastructure deployment/temporal-frontend
```

### Metrics Collection
```bash
# Deploy Prometheus monitor
kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: ai-agents-metrics
  namespace: ai-infrastructure
spec:
  selector:
    matchLabels:
      app: ai-agents
  endpoints:
  - port: metrics
    interval: 30s
EOF
```

## Performance Optimization

### Resource Tuning
```bash
# Optimize for production
export AGENT_MEMORY_LIMIT="2Gi"
export AGENT_CPU_LIMIT="2000m"
export DASHBOARD_REPLICAS="3"
export TEMPORAL_REPLICAS="3"
```

### Scaling
```bash
# Horizontal scaling
kubectl scale deployment memory-agent-rust --replicas=3 -n ai-infrastructure
kubectl scale deployment agent-dashboard --replicas=2 -n ai-infrastructure
```

## Backup and Recovery

### Data Backup
```bash
# Backup memory agent database
kubectl exec -it deployment/memory-agent-rust -n ai-infrastructure -- \
  cp /data/memory.db /backup/memory-$(date +%Y%m%d).db

# Backup configurations
kubectl get all -n ai-infrastructure -o yaml > ai-agents-backup.yaml
```

### Disaster Recovery
```bash
# Restore from backup
kubectl apply -f ai-agents-backup.yaml
kubectl cp memory-20260316.db memory-agent-rust-xxxxx:/data/memory.db -n ai-infrastructure
kubectl rollout restart deployment/memory-agent-rust -n ai-infrastructure
```

## Future Enhancements

### Planned Features
- **Multi-cluster Support**: Cross-cluster deployment
- **Advanced Security**: Mutual TLS, mTLS
- **Performance Monitoring**: Built-in metrics dashboard
- **Auto-scaling**: HPA integration
- **GitOps Integration**: ArgoCD sync
- **Testing Framework**: Automated deployment testing

### Script Improvements
- **Configuration Management**: External config files
- **Error Handling**: Enhanced error recovery
- **Progress Indicators**: Real-time deployment progress
- **Rollback Capability**: Automatic rollback on failure
- **Validation Tests**: Post-deployment functional tests

## Support and Contributing

### Getting Help
- Review this documentation
- Check script logs for errors
- Verify cluster connectivity
- Validate resource availability

### Contributing
- Fork the repository
- Create feature branches
- Submit pull requests
- Update documentation

### Reporting Issues
- Include script output
- Provide cluster configuration
- Share error logs
- Include reproduction steps

---

**Last Updated**: 2026-03-16  
**Version**: 1.0.0  
**Maintainer**: AI Agents Ecosystem Team  
**Script Location**: `scripts/deploy-ai-agents-ecosystem.sh`

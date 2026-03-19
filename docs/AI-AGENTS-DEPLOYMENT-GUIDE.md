# AI Agents Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Cloud AI Agents ecosystem in various environments, from local development to production clusters. The deployment is automated via the `core/scripts/automation/deploy-ai-agents-ecosystem.sh` script which creates a complete AI agent infrastructure with Temporal orchestration, monitoring, and debugging capabilities.

## Architecture Overview

The deployed ecosystem consists of:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Dashboard  │    │  Temporal Server│    │   Skills        │
│   (Nginx + JS)  │◄──►│   (Workflows)   │◄──►│   Framework     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Inference     │    │   Memory Agents │    │   Monitoring    │
│   Gateway       │◄──►│ (Rust/Go/Python)│◄──►│   & Debugging   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Prerequisites

### System Requirements
- **Kubernetes**: v1.24+ (kind, k3s, EKS, GKE, AKS)
- **kubectl**: Configured and connected to target cluster
- **Helm**: v3.8+ (for Temporal deployment)
- **Docker**: v20.10+ (optional, images are pre-built)
- **Git**: For configuration management

### Resource Requirements
```yaml
Minimum Resources:
  CPU: 4 cores
  Memory: 8Gi RAM
  Storage: 50Gi available

Recommended Resources:
  CPU: 8 cores
  Memory: 16Gi RAM
  Storage: 100Gi available
```

### Cluster Access
```bash
# Set up kubeconfig for hub cluster
export KUBECONFIG="${SCRIPT_DIR}/../hub-kubeconfig"

# Switch to hub cluster context
kubectl config use-context kind-gitops-hub

# Verify connection
kubectl cluster-info --context=kind-gitops-hub
```

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-org/agentic-reconciliation-engine.git
cd agentic-reconciliation-engine
```

### 2. Deploy AI Agents Ecosystem
```bash
# Deploy the complete ecosystem
./core/scripts/automation/deploy-ai-agents-ecosystem.sh

# Expected output:
🎉 Cloud AI Agents Ecosystem Deployed Successfully!
Access URLs:
  🌐 Agent Dashboard: http://dashboard.local
  🔄 Temporal Workflows: http://temporal.local
```

### 3. Access Dashboard
```bash
# Add hosts entries
echo "127.0.0.1 dashboard.local temporal.local" | sudo tee -a /etc/hosts

# Port forward for local access
kubectl port-forward -n ai-infrastructure svc/agent-dashboard-service 8080:80

# Open dashboard
open http://localhost:8080
```

### 4. Verify Deployment
```bash
kubectl get pods -n ai-infrastructure
kubectl get services -n ai-infrastructure
kubectl get ingress -n ai-infrastructure
```

## Deployment Script Features

### Core Components Deployed

#### 1. AI Memory Agents
**Purpose**: Persistent AI agents with Llama.cpp backend
**Languages**: Rust, Go, Python implementations
**Features**:
- Persistent storage via PVC
- Llama.cpp integration for inference
- Skill execution capabilities
- Health monitoring endpoints

#### 2. AI Inference Gateway
**Purpose**: Unified API endpoint for skill integration
**Features**:
- REST API for inference requests
- Multi-model support (Qwen2.5 0.5B)
- Load balancing across agents
- Health monitoring

#### 3. Temporal Server
**Purpose**: Workflow orchestration for complex AI operations
**Components**:
- Temporal frontend, history, matching services
- Cassandra persistence (embedded)
- Admin tools and UI

#### 4. Skills Framework
**Purpose**: 64 operational skills as Temporal workflows
**Skills Categories**:
- Infrastructure provisioning
- Cost optimization
- Security scanning
- Performance monitoring
- Compliance checking

#### 5. Agent Dashboard
**Purpose**: Real-time monitoring and control interface
**Features**:
- Live agent status monitoring
- Skills execution tracking
- Performance metrics visualization
- System controls (deploy/stop/restart)

## Configuration Options

### Environment Variables
```bash
# Namespace configuration
NAMESPACE="ai-infrastructure"  # Default namespace

# Temporal configuration
TEMPORAL_VERSION="1.22.0"      # Temporal server version

# Model configuration
OLLAMA_MODEL="qwen2.5:0.5b"   # AI model for inference

# Kubernetes configuration
KUBECTL_CMD="kubectl"         # kubectl command
```

### Custom Deployment
```bash
# Deploy to custom namespace
NAMESPACE=my-namespace ./core/scripts/automation/deploy-ai-agents-ecosystem.sh

# Custom model
OLLAMA_MODEL="llama2:7b" ./core/scripts/automation/deploy-ai-agents-ecosystem.sh
```

## Integration with Debugging System

### Post-Deployment Debugging
```bash
# Use AI Agent Debugger skill
./core/ai/skills/debug/scripts/distributed-debug-runner.sh \
  --namespace ai-infrastructure \
  --agent-type agent-memory \
  --debug-level detailed

# Check metrics
kubectl port-forward -n ai-infrastructure svc/dashboard-api-service 5000:5000
curl http://localhost:5000/api/cluster-status
```

### Health Monitoring
```bash
# Check agent health
kubectl get pods -n ai-infrastructure -l component=agent-memory

# View agent logs
kubectl logs -n ai-infrastructure -l component=agent-memory --tail=50

# Check Temporal workflows
tctl wf list --ns ai-infrastructure
```

## Troubleshooting Deployment

### Common Issues

#### Cluster Access Issues
```bash
# Check cluster connectivity
kubectl cluster-info --context=kind-gitops-hub

# Verify kubeconfig
kubectl config current-context

# Solution: Bootstrap hub cluster
./core/scripts/automation/create-hub-cluster.sh --provider kind --bootstrap-kubeconfig
```

#### Resource Constraints
```bash
# Check node resources
kubectl describe nodes

# Scale down if needed
kubectl scale deployment agent-memory-rust --replicas=0 -n ai-infrastructure

# Check PVC status
kubectl get pvc -n ai-infrastructure
```

#### Network Issues
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Verify services
kubectl get endpoints -n ai-infrastructure

# Test connectivity
kubectl exec -n ai-infrastructure deployment/agent-memory-rust -- curl dashboard.local
```

### Debug Commands
```bash
# Full system debug
python3 core/ai/skills/debug/scripts/debug.py '{
  "targetComponent": "kubernetes",
  "debugLevel": "deep",
  "namespace": "ai-infrastructure"
}'

# Temporal debug
tctl wf list --ns ai-infrastructure
tctl admin cluster describe

# Resource debug
kubectl top pods -n ai-infrastructure
kubectl get events -n ai-infrastructure --sort-by=.lastTimestamp
```

## Performance Optimization

### Resource Tuning
```yaml
# Memory agent resources
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"

# Temporal resources
server:
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1000m"
```

### Scaling Configuration
```bash
# Horizontal scaling
kubectl scale deployment agent-memory-rust --replicas=3 -n ai-infrastructure

# Temporal scaling
helm upgrade temporal temporal/temporal \
  --set server.replicaCount=3 \
  --namespace ai-infrastructure
```

## Security Considerations

### Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-agents-policy
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
          name: ingress-nginx
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 53  # DNS
  - to: []
    ports:
    - protocol: TCP
      port: 443 # HTTPS for model downloads
```

### RBAC Configuration
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ai-agent-role
  namespace: ai-infrastructure
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
```

## Backup and Recovery

### Data Backup
```bash
# Backup agent data
kubectl exec -n ai-infrastructure deployment/agent-memory-rust -- tar czf /tmp/backup.tar.gz /data

# Copy backup
kubectl cp ai-core/resources/agent-memory-rust-pod:/tmp/backup.tar.gz ./backup.tar.gz
```

### Configuration Backup
```bash
# Backup configs
kubectl get configmaps -n ai-infrastructure -o yaml > configmaps-backup.yaml
kubectl get secrets -n ai-infrastructure -o yaml > secrets-backup.yaml
```

### Disaster Recovery
```bash
# Full redeploy
./core/scripts/automation/deploy-ai-agents-ecosystem.sh

# Restore data
kubectl cp ./backup.tar.gz ai-core/resources/agent-memory-rust-pod:/tmp/backup.tar.gz
kubectl exec -n ai-infrastructure deployment/agent-memory-rust -- tar xzf /tmp/backup.tar.gz -C /
```

## API Reference

### Dashboard API Endpoints
```bash
# System status
GET /api/cluster-status
Response: {"status": "healthy", "message": "Cluster is operational"}

# Agent metrics
GET /api/core/ai/runtime/status
Response: {"agent_count": 3, "skills_executed": 42}

# Skills status
GET /api/skills
Response: {"skills": ["cost-analysis", "security-scan", ...]}

# Activity feed
GET /api/activity
Response: {"activities": [{"time": "2 min ago", "message": "..."}]}
```

### Temporal API
```bash
# List workflows
tctl wf list --ns ai-infrastructure

# Start workflow
tctl wf start --ns ai-infrastructure --tq ai-tasks --wt MyWorkflow

# Query workflow
tctl wf query --ns ai-infrastructure -w <workflow-id> -q my-query
```

## Support and Resources

### Documentation
- [docs/AI-AGENT-DEBUGGER-GUIDE.md](docs/AI-AGENT-DEBUGGER-GUIDE.md): Comprehensive debugging guide
- [docs/AI-AGENTS-ARCHITECTURE.md](docs/AI-AGENTS-ARCHITECTURE.md): Architecture overview
- [docs/MONITORING_SETUP.md](docs/MONITORING_SETUP.md): Monitoring configuration
- `core/ai/skills/debug/documentation/`: Detailed guides

### Scripts and Tools
- `core/scripts/automation/deploy-ai-agents-ecosystem.sh`: Main deployment script
- `core/ai/skills/debug/scripts/`: Debugging utilities
- `core/scripts/automation/debug-ai-agents-k8s.sh`: Kubernetes debugging
- `core/scripts/automation/llm-debug-automation.sh`: LLM-assisted debugging

### Troubleshooting
- Check logs: `kubectl logs -n ai-infrastructure -l component=agent-memory`
- Debug with skill: Use AI Agent Debugger skill
- Monitor resources: `kubectl top pods -n ai-infrastructure`
- Validate deployment: Run validation steps above

## Detailed Deployment

### Step 1: Environment Setup

#### Local Development (Kind)
```bash
# Create kind cluster
kind create cluster --name gitops-hub --config config/kind-cluster.yaml

# Set kubeconfig
export KUBECONFIG="${PWD}/hub-kubeconfig"
```

#### Cloud Provider Setup

**AWS EKS:**
```bash
# Create EKS cluster
eksctl create cluster --name gitops-hub --region us-west-2

# Update kubeconfig
aws eks update-kubeconfig --name gitops-hub
```

**Azure AKS:**
```bash
# Create resource group
az group create --name gitops-rg --location eastus

# Create AKS cluster
az aks create --name gitops-hub --resource-group gitops-rg --node-count 3

# Get credentials
az aks get-credentials --name gitops-hub --resource-group gitops-rg
```

**Google GKE:**
```bash
# Create GKE cluster
gcloud container clusters create gitops-hub --num-nodes=3 --region us-central1

# Get credentials
gcloud container clusters get-credentials gitops-hub --region us-central1
```

### Step 2: Deploy Infrastructure

#### Create Namespace
```bash
kubectl create namespace ai-infrastructure
```

#### Deploy Memory Agents
```bash
# Deploy memory agents with persistent storage
kubectl apply -f core/resources/ai-inference/shared/agent-memory-deployment.yaml

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s deployment/agent-memory-rust -n ai-infrastructure
```

#### Deploy AI Inference Gateway
```bash
kubectl apply -f core/resources/ai-inference/shared/ai-inference-gateway.yaml -n ai-infrastructure
```

### Step 3: Deploy Temporal Orchestration

#### Add Helm Repository
```bash
helm repo add temporal https://temporalio.github.io/helm-charts
helm repo update
```

#### Deploy Temporal
```bash
helm upgrade --install temporal temporal/temporal \
  --namespace ai-infrastructure \
  --set server.replicaCount=1 \
  --set frontend.service.type=ClusterIP \
  --set cassandra.enabled=true \
  --set cassandra.persistence.enabled=false \
  --set cassandra.config.cluster_size=1 \
  --set elasticsearch.enabled=false \
  --wait
```

### Step 4: Deploy Dashboard

#### Deploy Dashboard Frontend
```bash
kubectl apply -f core/resources/ai-inference/shared/agent-dashboard.yaml -n ai-infrastructure
```

#### Deploy Dashboard API
```bash
kubectl apply -f core/resources/ai-inference/shared/dashboard-api.yaml -n ai-infrastructure
```

### Step 5: Configure Access

#### Port Forwarding (Development)
```bash
# Dashboard
kubectl port-forward svc/agent-dashboard-service 8888:80 -n ai-infrastructure &

# API
kubectl port-forward svc/dashboard-api-service 5000:5000 -n ai-infrastructure &
```

#### Ingress (Production)
```bash
# Deploy ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Create ingress rules
kubectl apply -f core/resources/ai-inference/shared/ingress.yaml -n ai-infrastructure
```

## Configuration

### Environment Variables
```yaml
Memory Agent Configuration:
  DATABASE_PATH: "/data/memory.db"
  INBOX_PATH: "/data/inbox"
  BACKEND_PRIORITY: "llama.cpp,ollama"
  LANGUAGE_PRIORITY: "rust,go,python"
  OLLAMA_URL: "http://ollama-service:11434"
  MODEL: "qwen2.5:0.5b"
```

### Resource Limits
```yaml
Memory Agent Resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"

Dashboard Resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

### Storage Configuration
```yaml
PersistentVolumeClaim:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
```

## Advanced Deployment

### Multi-Cluster Deployment

#### Hub Cluster Setup
```bash
# Deploy to hub cluster
kubectl config use-context hub-cluster
./core/scripts/automation/deploy-ai-agents-ecosystem.sh
```

#### Spoke Cluster Setup
```bash
# Deploy to spoke clusters
for cluster in spoke1 spoke2 spoke3; do
  kubectl config use-context $cluster
  ./core/scripts/automation/deploy-ai-agents-spoke.sh
done
```

### GitOps Integration

#### Flux Setup
```bash
# Install Flux
flux install --namespace flux-system

# Create GitRepository
flux create source git $TOPDIR \
  --url=https://github.com/your-org/agentic-reconciliation-engine \
  --branch=main \
  --interval=1m

# Create Kustomization
flux create kustomization ai-agents \
  --source=$TOPDIR \
  --path=./core/resources/ai-inference \
  --prune=true \
  --interval=5m
```

#### ArgoCD Setup
```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Create Application
kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ai-agents
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/agentic-reconciliation-engine
    targetRevision: HEAD
    path: core/resources/ai-inference
  destination:
    server: https://kubernetes.default.svc
    namespace: ai-infrastructure
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF
```

## Monitoring and Observability

### Prometheus Metrics
```yaml
Service Monitor:
  selector:
    matchLabels:
      app: agent-memory
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

### Grafana Dashboards
```bash
# Import dashboards
kubectl create configmap grafana-dashboards \
  --from-file=monitoring/dashboards/ \
  -n monitoring
```

### Logging
```yaml
Fluentd Configuration:
  sources:
    - type: tail
      path: /var/log/containers/*ai-infrastructure*.log
  match:
    - tag: kubernetes.*
      type: stdout
```

## Troubleshooting

### Common Issues

#### Pod Not Starting
```bash
# Check pod status
kubectl describe pod <pod-name> -n ai-infrastructure

# Check logs
kubectl logs <pod-name> -n ai-infrastructure

# Check events
kubectl get events -n ai-infrastructure --sort-by=.lastTimestamp
```

#### Service Not Accessible
```bash
# Check service endpoints
kubectl get endpoints -n ai-infrastructure

# Check network policies
kubectl get networkpolicies -n ai-infrastructure

# Test connectivity
kubectl run test-pod --image=busybox --rm -it -- /bin/sh
wget -qO- http://service-name.namespace.svc.cluster.local:port
```

#### Storage Issues
```bash
# Check PVC status
kubectl get pvc -n ai-infrastructure

# Check storage classes
kubectl get storageclass

# Check volume mounts
kubectl exec <pod-name> -n ai-infrastructure -- df -h
```

### Debug Commands
```bash
# System overview
kubectl get all -n ai-infrastructure

# Resource usage
kubectl top pods -n ai-infrastructure

# Network connectivity
kubectl exec -it <pod-name> -n ai-infrastructure -- netstat -tlnp

# Configuration validation
kubectl get configmaps -n ai-infrastructure -o yaml
```

## Performance Tuning

### Resource Optimization
```yaml
Horizontal Pod Autoscaler:
  apiVersion: autoscaling/v2
  kind: HorizontalPodAutoscaler
  metadata:
    name: agent-memory-hpa
  spec:
    scaleTargetRef:
      apiVersion: apps/v1
      kind: Deployment
      name: agent-memory-rust
    minReplicas: 1
    maxReplicas: 5
    metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

### Database Optimization
```yaml
SQLite Configuration:
  pragma journal_mode = WAL
  pragma synchronous = NORMAL
  pragma cache_size = 10000
  pragma temp_store = MEMORY
```

### Network Optimization
```yaml
Service Mesh:
  apiVersion: networking.istio.io/v1beta1
  kind: VirtualService
  metadata:
    name: ai-agents
  spec:
    http:
    - match:
      - uri:
          prefix: /api
      route:
      - destination:
          host: dashboard-api-service
      timeout: 30s
      retries:
        attempts: 3
        perTryTimeout: 10s
```

## Security Configuration

### Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-agents-netpol
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
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: ai-infrastructure
```

### RBAC Configuration
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: ai-infrastructure
  name: ai-agents-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
```

## Backup and Recovery

### Data Backup
```bash
# Backup persistent volumes
kubectl exec -it agent-memory-rust-xxx -n ai-infrastructure -- \
  cp /data/memory.db /backup/memory-$(date +%Y%m%d).db

# Backup configuration
kubectl get configmaps -n ai-infrastructure -o yaml > config-backup.yaml
```

### Disaster Recovery
```bash
# Restore from backup
kubectl cp backup/memory-20240315.db agent-memory-rust-xxx:/data/memory.db -n ai-infrastructure

# Restart services
kubectl rollout restart deployment/agent-memory-rust -n ai-infrastructure
```

## Maintenance

### Rolling Updates
```bash
# Update images
kubectl set image deployment/agent-memory-rust \
  agent-memory=agent-memory-rust:v2.0.0 -n ai-infrastructure

# Monitor rollout
kubectl rollout status deployment/agent-memory-rust -n ai-infrastructure
```

### Health Checks
```yaml
Liveness Probe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

Readiness Probe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

## Conclusion

This deployment guide provides comprehensive instructions for deploying the AI Agents ecosystem in various environments. Follow the steps in order and verify each component before proceeding to the next.

For production deployments, ensure proper security, monitoring, and backup configurations are in place. Regular maintenance and updates will keep the system running optimally.

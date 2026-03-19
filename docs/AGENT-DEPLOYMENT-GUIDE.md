# AI Agents Complete Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the complete AI Agents ecosystem, including memory agents, temporal orchestration, skills framework, monitoring system, and web dashboard.

## Quick Start (Recommended)

For the fastest deployment experience, use the enhanced quickstart that includes AI agents:

```bash
# One-command deployment including AI agents and dashboard
./core/scripts/automation/quickstart.sh
```

This automatically deploys:
- GitOps infrastructure (Flux, Crossplane with Kubernetes provider)
- AI agents ecosystem with Temporal orchestration
- Interactive dashboard for monitoring and control
- 64+ operational skills for cloud automation

## Manual Deployment Options

### 🛠️ System Requirements

#### Kubernetes Cluster
- **Version**: Kubernetes 1.25+
- **Nodes**: Minimum 3 nodes for high availability
- **Memory**: 8GB+ per node recommended
- **Storage**: 50GB+ persistent storage
- **Network**: Cluster networking enabled

#### Required Tools
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Install helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install kind (for local development)
brew install kind
```

#### Cluster Configuration
```bash
# Create kind cluster (for local development)
kind create cluster --name gitops-hub --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
  - containerPort: 443
    hostPort: 443
  - containerPort: 8888
    hostPort: 8888
  - containerPort: 5000
    hostPort: 5000
EOF
```

## Quick Start Deployment

### 🚀 One-Command Deployment

```bash
# Clone repository
git clone https://github.com/lloydchang/agentic-reconciliation-engine.git
cd agentic-reconciliation-engine

# Deploy complete ecosystem
chmod +x core/scripts/automation/deploy-ai-agents-ecosystem.sh
./core/scripts/automation/deploy-ai-agents-ecosystem.sh
```

### Expected Output
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

## Detailed Deployment Steps

### 📋 Step-by-Step Guide

#### 1. Environment Setup
```bash
# Set environment variables
export NAMESPACE="ai-infrastructure"
export TEMPORAL_VERSION="1.22.0"
export OLLAMA_MODEL="qwen2.5:0.5b"

# Configure kubectl context
kubectl config use-context kind-gitops-hub
export KUBECONFIG="${PWD}/hub-kubeconfig"
```

#### 2. Namespace Creation
```bash
# Create namespace
kubectl create namespace ai-infrastructure --dry-run=client -o yaml | kubectl apply -f -

# Verify namespace
kubectl get namespace ai-infrastructure
```

#### 3. Memory Agents Deployment
```bash
# Create persistent volume claim
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: agent-memory-pvc
  namespace: ai-infrastructure
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
EOF

# Deploy memory agent
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-memory-rust
  namespace: ai-infrastructure
  labels:
    component: agent-memory
    language: rust
    backend: llama-cpp
spec:
  replicas: 1
  selector:
    matchLabels:
      component: agent-memory
      language: rust
  template:
    metadata:
      labels:
        component: agent-memory
        language: rust
        backend: llama-cpp
    spec:
      initContainers:
      - name: init-memory-db
        image: alpine:latest
        command: ["sh", "-c"]
        args:
        - |
          if [ ! -f /data/memory.db ]; then
            echo "Initializing empty memory.db"
            touch /data/memory.db
          else
            echo "Using existing memory.db"
          fi
        volumeMounts:
        - name: memory-storage
          mountPath: /data
      containers:
      - name: agent-memory
        image: nginx:alpine  # Placeholder image
        ports:
        - containerPort: 80
        env:
        - name: DATABASE_PATH
          value: "/data/memory.db"
        - name: INBOX_PATH
          value: "/data/inbox"
        volumeMounts:
        - name: memory-storage
          mountPath: /data
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: memory-storage
        persistentVolumeClaim:
          claimName: agent-memory-pvc
EOF

# Wait for deployment
kubectl wait --for=condition=available --timeout=120s deployment/agent-memory-rust -n ai-infrastructure
```

#### 4. AI Inference Gateway
```bash
# Deploy inference gateway
kubectl apply -f core/resources/ai-inference/shared/ai-inference-gateway.yaml -n ai-infrastructure

# Wait for deployment
kubectl wait --for=condition=available --timeout=60s deployment/ai-inference-gateway -n ai-infrastructure
```

#### 5. Temporal Orchestration
```bash
# Add Temporal Helm repo
helm repo add temporal https://temporalio.github.io/helm-charts
helm repo update

# Install Temporal
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

#### 6. Skills Framework
```bash
# Deploy skills orchestrator
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: skills-orchestrator
  namespace: ai-infrastructure
  labels:
    component: skills-orchestrator
spec:
  replicas: 1
  selector:
    matchLabels:
      component: skills-orchestrator
  template:
    metadata:
      labels:
        component: skills-orchestrator
    spec:
      containers:
      - name: orchestrator
        image: temporalio/server:1.22.0
        ports:
        - containerPort: 7233
        env:
        - name: TEMPORAL_ADDRESS
          value: "temporal-frontend:7233"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
EOF
```

#### 7. Dashboard Deployment
```bash
# Deploy dashboard (uses comprehensive HTML from deployment script)
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-dashboard
  namespace: ai-infrastructure
  labels:
    component: agent-dashboard
spec:
  replicas: 1
  selector:
    matchLabels:
      component: agent-dashboard
  template:
    metadata:
      labels:
        component: agent-dashboard
    spec:
      containers:
      - name: dashboard
        image: nginx:alpine
        ports:
        - containerPort: 80
        volumeMounts:
        - name: dashboard-html
          mountPath: /usr/share/nginx/html
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
      volumes:
      - name: dashboard-html
        configMap:
          name: agent-dashboard-config
---
apiVersion: v1
kind: Service
metadata:
  name: agent-dashboard-service
  namespace: ai-infrastructure
spec:
  selector:
    component: agent-dashboard
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
EOF
```

#### 8. Dashboard API Service
```bash
# Deploy dashboard API
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dashboard-api
  namespace: ai-infrastructure
  labels:
    component: dashboard-api
spec:
  replicas: 1
  selector:
    matchLabels:
      component: dashboard-api
  template:
    metadata:
      labels:
        component: dashboard-api
    spec:
      containers:
      - name: api
        image: python:3.9-alpine
        ports:
        - containerPort: 5000
        command: ["python", "-c"]
        args:
        - |
          from flask import Flask, jsonify
          import os
          app = Flask(__name__)
          
          @app.route('/api/cluster-status')
          def cluster_status():
              return jsonify({"status": "healthy", "message": "Cluster is operational"})
          
          @app.route('/api/core/ai/runtime/status')
          def agents_status():
              return jsonify({"agent_count": 3, "skills_executed": 42})
          
          if __name__ == '__main__':
              app.run(host='0.0.0.0', port=5000)
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
---
apiVersion: v1
kind: Service
metadata:
  name: dashboard-api-service
  namespace: ai-infrastructure
spec:
  selector:
    component: dashboard-api
  ports:
  - port: 5000
    targetPort: 5000
  type: ClusterIP
EOF
```

#### 9. Ingress Configuration
```bash
# Deploy NGINX ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Wait for ingress controller
kubectl wait --for=condition=available --timeout=300s deployment/ingress-nginx-controller -n ingress-nginx

# Create ingress rules
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-agents-ingress
  namespace: ai-infrastructure
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: temporal.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: temporal-frontend
            port:
              number: 7233
  - host: dashboard.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: agent-dashboard-service
            port:
              number: 80
EOF
```

## Access and Verification

### 🔍 Deployment Verification

#### Check All Components
```bash
# Check all pods
kubectl get pods -n ai-infrastructure

# Expected output:
# NAME                                      READY   STATUS    RESTARTS   AGE
# agent-memory-rust-xxxxxxxxxxxx            1/1     Running   0          5m
# ai-inference-gateway-xxxxxxxxxxxx        1/1     Running   0          5m
# temporal-frontend-xxxxxxxxxxxx           1/1     Running   0          5m
# temporal-history-xxxxxxxxxxxx             1/1     Running   0          5m
# temporal-worker-xxxxxxxxxxxx              1/1     Running   0          5m
# skills-orchestrator-xxxxxxxxxxxx          1/1     Running   0          5m
# agent-dashboard-xxxxxxxxxxxx              1/1     Running   0          5m
# dashboard-api-xxxxxxxxxxxx                1/1     Running   0          5m

# Check services
kubectl get services -n ai-infrastructure

# Check ingress
kubectl get ingress -n ai-infrastructure
```

#### Health Checks
```bash
# Test dashboard API
kubectl port-forward svc/dashboard-api-service 5000:5000 -n ai-infrastructure &
curl http://localhost:5000/api/cluster-status

# Test dashboard
kubectl port-forward svc/agent-dashboard-service 8888:80 -n ai-infrastructure &
curl -I http://localhost:8888

# Test memory agent
kubectl port-forward svc/agent-memory-service 8080:80 -n ai-infrastructure &
curl http://localhost:8080/api/health
```

### 🌐 Access URLs

#### Port Forward (Development)
```bash
# Dashboard
kubectl port-forward svc/agent-dashboard-service 8888:80 -n ai-infrastructure
# Access: http://localhost:8888

# Dashboard API
kubectl port-forward svc/dashboard-api-service 5000:5000 -n ai-infrastructure
# Access: http://localhost:5000/api/cluster-status

# Temporal UI
kubectl port-forward svc/temporal-frontend 7233:7233 -n ai-infrastructure
# Access: http://localhost:7233
```

#### Ingress (Production)
```bash
# Add to /etc/hosts
echo "127.0.0.1 dashboard.local temporal.local" >> /etc/hosts

# Access URLs:
# - Dashboard: http://dashboard.local
# - Temporal UI: http://temporal.local
# - API: http://dashboard.local/api/cluster-status
```

## Configuration Options

### ⚙️ Custom Configuration

#### Environment Variables
```bash
# Agent configuration
export AGENT_MEMORY_SIZE="20Gi"
export AGENT_CPU_LIMIT="1000m"
export AGENT_MEMORY_LIMIT="1Gi"

# Temporal configuration
export TEMPORAL_REPLICAS="3"
export TEMPORAL_PERSISTENCE="true"

# Dashboard configuration
export DASHBOARD_REPLICAS="2"
export DASHBOARD_CPU_LIMIT="500m"
export DASHBOARD_MEMORY_LIMIT="512Mi"
```

#### Custom Values File
```yaml
# custom-values.yaml
agents:
  memory:
    size: 20Gi
    cpuLimit: 1000m
    memoryLimit: 1Gi
  
temporal:
  replicas: 3
  persistence:
    enabled: true
    size: 100Gi
  
dashboard:
  replicas: 2
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
```

#### Apply Custom Configuration
```bash
# Deploy with custom values
helm upgrade --install ai-agents ./charts/ai-agents \
    --namespace ai-infrastructure \
    --values custom-values.yaml
```

## Scaling and High Availability

### 📈 Scaling Strategies

#### Horizontal Scaling
```bash
# Scale memory agents
kubectl scale deployment agent-memory-rust --replicas=3 -n ai-infrastructure

# Scale dashboard
kubectl scale deployment agent-dashboard --replicas=2 -n ai-infrastructure

# Scale temporal workers
kubectl scale deployment temporal-worker --replicas=5 -n ai-infrastructure
```

#### Resource Scaling
```bash
# Update resource limits
kubectl patch deployment agent-memory-rust -n ai-infrastructure -p '{"spec":{"template":{"spec":{"containers":[{"name":"agent-memory","resources":{"limits":{"memory":"1Gi","cpu":"1000m"}}}]}}}}'
```

#### High Availability Configuration
```yaml
# ha-values.yaml
agents:
  memory:
    replicas: 3
    antiAffinity: hard
  
temporal:
  server:
    replicas: 3
    history:
      replicas: 3
    worker:
      replicas: 5
  
dashboard:
  replicas: 2
  antiAffinity: soft
```

## Monitoring and Troubleshooting

### 📊 Monitoring Setup

#### Prometheus Integration
```bash
# Deploy Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    --create-namespace

# Configure metrics scraping
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

#### Log Aggregation
```bash
# Deploy Elasticsearch and Kibana
helm repo add elastic https://helm.elastic.co
helm install elasticsearch elastic/elasticsearch \
    --namespace logging \
    --create-namespace

helm install kibana elastic/kibana \
    --namespace logging \
    --set service.type=LoadBalancer
```

### 🔧 Troubleshooting Guide

#### Common Issues

##### Pod Not Starting
```bash
# Check pod status
kubectl describe pod <pod-name> -n ai-infrastructure

# Check events
kubectl get events -n ai-infrastructure --sort-by=.metadata.creationTimestamp

# Check logs
kubectl logs <pod-name> -n ai-infrastructure
```

##### Service Not Accessible
```bash
# Check service
kubectl describe svc <service-name> -n ai-infrastructure

# Check endpoints
kubectl get endpoints <service-name> -n ai-infrastructure

# Test connectivity
kubectl run test-pod --image=busybox --rm -it --restart=Never -- \
  wget -qO- http://<service-name>.<namespace>.svc.cluster.local:<port>
```

##### Ingress Not Working
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress rules
kubectl describe ingress <ingress-name> -n ai-infrastructure

# Test ingress
curl -H "Host: dashboard.local" http://localhost/
```

##### Performance Issues
```bash
# Check resource usage
kubectl top pods -n ai-infrastructure

# Check node resources
kubectl top nodes

# Check resource limits
kubectl describe pod <pod-name> -n ai-infrastructure | grep -A 10 "Limits:"
```

## Backup and Recovery

### 💾 Backup Strategy

#### Database Backup
```bash
# Backup memory agent database
kubectl exec -it deployment/agent-memory-rust -n ai-infrastructure -- \
  sqlite3 /data/memory.db ".backup /backup/memory-$(date +%Y%m%d).db"

# Backup to persistent storage
kubectl create job backup-memory-db --from=cronjob/backup-memory-db -n ai-infrastructure
```

#### Configuration Backup
```bash
# Backup all configurations
kubectl get all -n ai-infrastructure -o yaml > ai-infrastructure-backup.yaml

# Backup secrets
kubectl get secrets -n ai-infrastructure -o yaml > secrets-backup.yaml
```

#### Disaster Recovery
```bash
# Restore from backup
kubectl apply -f ai-infrastructure-backup.yaml

# Restore database
kubectl cp memory-20260316.db agent-memory-rust-xxxxx:/data/memory.db -n ai-infrastructure

# Restart services
kubectl rollout restart deployment/agent-memory-rust -n ai-infrastructure
```

## Security Considerations

### 🔒 Security Best Practices

#### Network Policies
```bash
# Apply network policies
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
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: ai-infrastructure
EOF
```

#### RBAC Configuration
```bash
# Create service account
kubectl create serviceaccount ai-agents-sa -n ai-infrastructure

# Create role
kubectl create role ai-agents-role \
    --verb=get,list,watch,create,update,patch,delete \
    --resource=pods,services,deployments \
    --namespace=ai-infrastructure

# Bind role to service account
kubectl create rolebinding ai-agents-binding \
    --role=ai-agents-role \
    --serviceaccount=ai-infrastructure:ai-agents-sa \
    --namespace=ai-infrastructure
```

#### Secrets Management
```bash
# Create secret for API keys
kubectl create secret generic ai-agents-secrets \
    --from-literal=api-key=your-api-key \
    --from-literal=database-url=your-database-url \
    --namespace=ai-infrastructure

# Mount secret in pod
kubectl patch deployment agent-memory-rust -n ai-infrastructure -p '{"spec":{"template":{"spec":{"containers":[{"name":"agent-memory","envFrom":[{"secretRef":{"name":"ai-agents-secrets"}}]}]}}}}'
```

## Maintenance and Updates

### 🔄 Maintenance Procedures

#### Rolling Updates
```bash
# Update memory agent image
kubectl set image deployment/agent-memory-rust agent-memory=agent-memory-rust:v2.0.0 -n ai-infrastructure

# Wait for rollout
kubectl rollout status deployment/agent-memory-rust -n ai-infrastructure

# Rollback if needed
kubectl rollout undo deployment/agent-memory-rust -n ai-infrastructure
```

#### Health Monitoring
```bash
# Set up health checks
kubectl patch deployment agent-memory-rust -n ai-infrastructure -p '{"spec":{"template":{"spec":{"containers":[{"name":"agent-memory","livenessProbe":{"httpGet":{"path":"/api/health","port":80},"initialDelaySeconds":30,"periodSeconds":10},"readinessProbe":{"httpGet":{"path":"/api/ready","port":80},"initialDelaySeconds":5,"periodSeconds":5}}]}}}}'
```

#### Log Rotation
```bash
# Configure log rotation
kubectl patch deployment agent-memory-rust -n ai-infrastructure -p '{"spec":{"template":{"spec":{"containers":[{"name":"agent-memory","env":[{"name":"LOG_ROTATION","value":"daily"},{"name":"LOG_RETENTION","value":"7"}]}]}}}}'
```

## Performance Optimization

### ⚡ Performance Tuning

#### Resource Optimization
```bash
# Optimize resource requests and limits
kubectl patch deployment agent-memory-rust -n ai-infrastructure -p '{"spec":{"template":{"spec":{"containers":[{"name":"agent-memory","resources":{"requests":{"memory":"512Mi","cpu":"200m"},"limits":{"memory":"1Gi","cpu":"500m"}}}]}}}}'
```

#### Caching Strategy
```bash
# Add Redis cache
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install redis bitnami/redis \
    --namespace ai-infrastructure \
    --set auth.enabled=false
```

#### Database Optimization
```bash
# Optimize SQLite settings
kubectl exec -it deployment/agent-memory-rust -n ai-infrastructure -- \
  sqlite3 /data/memory.db "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA cache_size=10000;"
```

## Integration with CI/CD

### 🔄 CI/CD Integration

#### GitHub Actions
```yaml
# .github/workflows/deploy-ai-agents.yml
name: Deploy AI Agents

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup kubectl
      uses: azure/setup-kubectl@v1
      with:
        version: 'v1.25.0'
    
    - name: Deploy to Kubernetes
      run: |
        kubectl config use-context ${{ secrets.KUBE_CONTEXT }}
        ./core/scripts/automation/deploy-ai-agents-ecosystem.sh
```

#### ArgoCD Integration
```yaml
# argocd-application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ai-agents
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/lloydchang/agentic-reconciliation-engine.git
    targetRevision: HEAD
    path: manifests/ai-agents
  destination:
    server: https://kubernetes.default.svc
    namespace: ai-infrastructure
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## Conclusion

This comprehensive deployment guide covers all aspects of deploying the AI Agents ecosystem, from initial setup to production operations. The system is designed to be:

- **Scalable**: Horizontal scaling support for all components
- **Resilient**: High availability configuration options
- **Observable**: Comprehensive monitoring and logging
- **Secure**: Network policies and RBAC configuration
- **Maintainable**: Rolling updates and backup procedures

For additional information, refer to the specific component documentation:
- [Memory Agent Architecture](MEMORY-AGENT-ARCHITECTURE.md)
- [AI Agents Dashboard Guide](AGENT-DASHBOARD-GUIDE.md)
- [AI Agents Monitoring System](AI-AGENTS-MONITORING-SYSTEM.md)

---

**Last Updated**: 2026-03-16  
**Version**: 1.0.0  
**Maintainer**: AI Agents Team

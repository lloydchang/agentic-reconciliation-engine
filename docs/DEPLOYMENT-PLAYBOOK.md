# Deployment Playbook

## Agent Dashboard Deployment - Step-by-Step

This playbook provides the exact sequence of commands to deploy the AI Agent Dashboard successfully.

## Prerequisites Checklist

- [ ] Kubernetes cluster running (Kind/Docker Desktop)
- [ ] kubectl configured and connected
- [ ] Docker installed and running
- [ ] Repository cloned locally
- [ ] Current directory: `/Users/lloyd/github/antigravity/agentic-reconciliation-engine`

## Step 1: Build Dashboard Image

```bash
# Navigate to dashboard directory
cd core/ai/runtime/dashboard

# Fix Go dependencies
go mod tidy

# Build Docker image
docker build -t ai-agents/dashboard:latest .

# Verify image built
docker images | grep ai-agents/dashboard
```

**Expected Output**:
```
ai-agents/dashboard:latest    <image-id>    <size>    <created>
```

## Step 2: Load Image into Cluster

```bash
# For Kind clusters
kind load docker-image ai-agents/dashboard:latest --name gitops-hub

# Verify image is available
docker exec gitops-hub-control-plane docker images | grep ai-agents/dashboard
```

## Step 3: Create Database

```bash
# Create dashboard database in existing PostgreSQL
kubectl exec -n langfuse postgres-6dd595ffbb-6h4lb -- psql -U postgres -c "CREATE DATABASE dashboard;"

# Verify database created
kubectl exec -n langfuse postgres-6dd595ffbb-6h4lb -- psql -U postgres -c "\l" | grep dashboard
```

## Step 4: Create Secrets

```bash
# Create database secret
kubectl create secret generic db-secret -n ai-infrastructure \
  --from-literal=url="postgresql://postgres:postgres@postgres.langfuse.svc.cluster.local:5432/dashboard?sslmode=disable"

# Create ArgoCD secret
kubectl create secret generic argocd-secret -n ai-infrastructure \
  --from-literal=password="admin"

# Verify secrets created
kubectl get secrets -n ai-infrastructure | grep -E "(db|argocd)"
```

**Expected Output**:
```
db-secret          Opaque                                1      10s
argocd-secret      Opaque                                1      10s
```

## Step 5: Deploy Dashboard

```bash
# Apply deployment
kubectl apply -f core/ai/runtime/dashboard/deployment/kubernetes/dashboard-deployment.yaml

# Verify deployment created
kubectl get deployment -n ai-infrastructure ai-agents-dashboard
```

**Expected Output**:
```
NAME                   READY   UP-TO-DATE   AVAILABLE   AGE
ai-agents-dashboard   0/3     3            0           5s
```

## Step 6: Verify Pod Status

```bash
# Check pod status
kubectl get pods -n ai-infrastructure -l app=ai-agents-dashboard

# Wait for pods to be ready (may take 1-2 minutes)
watch kubectl get pods -n ai-infrastructure -l app=ai-agents-dashboard
```

**Expected Final State**:
```
NAME                                   READY   STATUS    RESTARTS   AGE
ai-agents-dashboard-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
ai-agents-dashboard-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
ai-agents-dashboard-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
```

## Step 7: Verify Service

```bash
# Check service
kubectl get svc -n ai-infrastructure ai-agents-dashboard

# Check service endpoints
kubectl get endpoints -n ai-infrastructure ai-agents-dashboard
```

**Expected Output**:
```
NAME                   TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
ai-agents-dashboard   ClusterIP   10.96.xx.xx     <none>        8081/TCP   2m
```

## Step 8: Access Dashboard

```bash
# Port forward to access locally
nohup kubectl port-forward -n ai-infrastructure svc/ai-agents-dashboard 8081:8081 &

# Access dashboard
open http://localhost:8081

# Or check with curl
curl http://localhost:8081/health
```

**Expected Health Response**:
```json
{"status":"healthy","timestamp":"2026-03-18T16:30:00Z"}
```

## Troubleshooting Steps

### If Pods Don't Start

```bash
# Check pod events
kubectl describe pod -n ai-infrastructure -l app=ai-agents-dashboard

# Check pod logs
kubectl logs -n ai-infrastructure -l app=ai-agents-dashboard

# Common fixes:
# 1. Delete pods to restart: kubectl delete pods -n ai-infrastructure -l app=ai-agents-dashboard
# 2. Delete and recreate secrets
# 3. Delete and recreate deployment
```

### If Database Connection Fails

```bash
# Test database connection
kubectl exec -n langfuse postgres-6dd595ffbb-6h4lb -- psql -U postgres -d dashboard -c "SELECT 1;"

# Recreate database secret with correct URL
kubectl delete secret db-secret -n ai-infrastructure
kubectl create secret generic db-secret -n ai-infrastructure \
  --from-literal=url="postgresql://postgres:postgres@postgres.langfuse.svc.cluster.local:5432/dashboard?sslmode=disable"
```

### If Image Pull Fails

```bash
# Check if image exists in cluster
docker exec gitops-hub-control-plane docker images | grep ai-agents/dashboard

# Rebuild and reload image
cd core/ai/runtime/dashboard
docker build -t ai-agents/dashboard:latest .
kind load docker-image ai-agents/dashboard:latest --name gitops-hub
```

## Cleanup Commands

```bash
# Stop port forwarding
pkill -f "kubectl port-forward"

# Delete deployment
kubectl delete deployment -n ai-infrastructure ai-agents-dashboard

# Delete secrets
kubectl delete secret -n ai-infrastructure db-secret argocd-secret

# Delete database (optional)
kubectl exec -n langfuse postgres-6dd595ffbb-6h4lb -- psql -U postgres -c "DROP DATABASE dashboard;"
```

## Verification Checklist

- [ ] Docker image built successfully
- [ ] Image loaded into Kind cluster
- [ ] Database created
- [ ] Secrets created
- [ ] Deployment applied
- [ ] Pods running (3/3 ready)
- [ ] Service accessible
- [ ] Health endpoint responding
- [ ] Dashboard accessible at http://localhost:8081

## Success Indicators

1. **All pods running**: 3/3 pods in READY state
2. **Service responding**: HTTP 200 from health endpoint
3. **Dashboard loading**: Web interface accessible
4. **No errors**: Clean pod logs without FATAL errors

## Next Steps

1. **Configure features**: Enable RAG, voice chat, integrations
2. **Set up monitoring**: Add metrics and alerts
3. **Configure ingress**: Expose dashboard externally
4. **Set up GitOps**: Add to automated deployment pipeline

---

**Total Time**: ~5-10 minutes
**Complexity**: Medium
**Dependencies**: PostgreSQL, Kubernetes, Docker

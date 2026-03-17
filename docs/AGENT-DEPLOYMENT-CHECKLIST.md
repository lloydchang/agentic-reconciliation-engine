# Agent Deployment Checklist

## Quick Start Checklist

Use this checklist to verify AI Agents deployment is working correctly.

---

## 🚀 Pre-Deployment Checks

### Prerequisites
- [ ] Kubernetes cluster running (kind, minikube, or cloud)
- [ ] kubectl configured and connected
- [ ] Docker daemon running
- [ ] Sufficient cluster resources (2GB+ RAM, 2+ CPU)

### Namespace Setup
```bash
# Create namespace
kubectl create namespace ai-infrastructure

# Verify namespace
kubectl get namespace ai-infrastructure
```

### Storage Preparation
```bash
# Create PVCs
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
```

---

## 🔧 Infrastructure Deployment

### 1. Deploy FastAPI Backend
```bash
# Apply dashboard API configuration
kubectl apply -f dashboard-api.yaml

# Wait for pod to be ready
kubectl wait --for=condition=ready pod -l component=dashboard-api -n ai-infrastructure --timeout=120s

# Verify pod is running
kubectl get pods -n ai-infrastructure | grep dashboard-api
```

### 2. Deploy Dashboard Frontend
```bash
# Apply dashboard deployment
kubectl apply -f dashboard-deployment.yaml

# Wait for pod to be ready
kubectl wait --for=condition=ready pod -l app=agent-dashboard -n ai-infrastructure --timeout=60s

# Verify pod is running
kubectl get pods -n ai-infrastructure | grep agent-dashboard
```

### 3. Deploy Agent Memory
```bash
# Apply agent deployment
kubectl apply -f core/resources/infrastructure/ai-inference/shared/agent-memory-deployment.yaml

# Wait for pod to be ready
kubectl wait --for=condition=ready pod -l component=agent-memory -n ai-infrastructure --timeout=120s

# Verify pod is running
kubectl get pods -n ai-infrastructure | grep agent-memory
```

---

## 🌐 Access Verification

### Port Forwarding Setup
```bash
# Dashboard (Frontend)
kubectl port-forward -n ai-infrastructure svc/agent-dashboard-service 8081:80 &
DASHBOARD_PID=$!

# API (Backend)
kubectl port-forward -n ai-infrastructure pod/dashboard-api-pod 5006:5000 &
API_PID=$!

echo "Dashboard: http://localhost:8081"
echo "API: http://localhost:5006"
echo "API Docs: http://localhost:5006/docs"
```

### Service Connectivity Tests
```bash
# Test API health
curl -s http://localhost:5006/health || echo "❌ API not accessible"

# Test agents endpoint
curl -s http://localhost:5006/api/agents || echo "❌ Agents endpoint failing"

# Test skills endpoint  
curl -s http://localhost:5006/api/skills || echo "❌ Skills endpoint failing"

# Test activity endpoint
curl -s http://localhost:5006/api/activity || echo "❌ Activity endpoint failing"
```

---

## 🎯 Dashboard Verification

### Frontend Functionality
- [ ] Dashboard loads at http://localhost:8081
- [ ] System shows "Online" status
- [ ] Metrics are loading from FastAPI
- [ ] Agent count displays correctly
- [ ] Skills list populates
- [ ] Activity feed shows entries

### User Interface Tests
- [ ] "Add Agent" button opens modal wizard
- [ ] Agent wizard form validation works
- [ ] Toast notifications appear correctly
- [ ] Refresh buttons update data
- [ ] Control buttons respond to clicks

### Agent Management
- [ ] Agent wizard submits successfully
- [ ] Agent deployment shows progress toasts
- [ ] Agent appears in dashboard after deployment
- [ ] Agent status updates correctly

---

## 🔍 Backend Verification

### FastAPI Container Check
```bash
# Check container has kubectl
API_POD=$(kubectl get pods -n ai-infrastructure -l component=dashboard-api -o jsonpath='{.items[0].metadata.name}')
kubectl exec $API_POD -n ai-infrastructure -- which kubectl || echo "❌ kubectl missing in API container"

# Check API can query Kubernetes
kubectl exec $API_POD -n ai-infrastructure -- kubectl get pods -n ai-infrastructure --no-headers | head -5
```

### Agent Detection Tests
```bash
# Test agent parsing logic
curl -s http://localhost:5006/api/agents | jq '.[] | {name, type, status}' || echo "❌ Agent parsing failed"

# Verify agent memory is detected
curl -s http://localhost:5006/api/agents | jq '.[] | select(.name | contains("Memory"))' || echo "❌ Memory agent not detected"
```

### Database Operations
```bash
# Test database connectivity
curl -s http://localhost:5006/api/activity | jq 'length' || echo "❌ Database operations failing"

# Verify data persistence
curl -s http://localhost:5006/api/activity | jq '.[0:3]' || echo "❌ Activity data missing"
```

---

## 🤖 Agent Pod Verification

### Agent Container Check
```bash
# Get agent pod name
AGENT_POD=$(kubectl get pods -n ai-infrastructure -l component=agent-memory -o jsonpath='{.items[0].metadata.name}')

# Check pod is running
kubectl get pod $AGENT_POD -n ai-infrastructure

# Check pod logs
kubectl logs $AGENT_POD -n ai-infrastructure --tail=20

# Check pod environment
kubectl exec $AGENT_POD -n ai-infrastructure -- env | grep -E "(MODEL|BACKEND|OLLAMA)"

# Check pod resources
kubectl top pod $AGENT_POD -n ai-infrastructure || echo "⚠️ Metrics server not available"
```

### Agent Health Check
```bash
# Test agent API (if port 8080 is exposed)
kubectl port-forward -n ai-infrastructure pod/$AGENT_POD 8080:8080 &
AGENT_PID=$!

sleep 2

# Test agent status endpoint
curl -s http://localhost:8080/status || echo "❌ Agent API not accessible"

# Test agent query endpoint
curl -s -X GET "http://localhost:8080/query?q=test" || echo "❌ Agent query failing"

kill $AGENT_PID
```

---

## 📊 Performance Verification

### Resource Usage
```bash
# Check pod resource usage
kubectl top pods -n ai-infrastructure || echo "⚠️ Metrics server not available"

# Check node resources
kubectl top nodes || echo "⚠️ Metrics server not available"

# Check PVC usage
kubectl get pvc -n ai-infrastructure
```

### Response Times
```bash
# Test API response times
time curl -s http://localhost:5006/api/agents > /dev/null
time curl -s http://localhost:5006/api/skills > /dev/null  
time curl -s http://localhost:5006/api/activity > /dev/null

# Test dashboard load time
time curl -s http://localhost:8081 > /dev/null
```

---

## 🚨 Common Issues & Solutions

### Issue: "No agents found" in Dashboard
**Symptoms**: Dashboard shows empty agent list
**Causes**: 
- [ ] kubectl missing in FastAPI container
- [ ] Wrong service selector
- [ ] Agent pods not running

**Solutions**:
```bash
# 1. Check kubectl in API container
kubectl exec dashboard-api-pod -- which kubectl

# 2. Check service selector
kubectl get svc dashboard-api-service -o yaml | grep selector

# 3. Check agent pods
kubectl get pods -n ai-infrastructure | grep agent-memory
```

### Issue: Agent pod shows nginx processes
**Symptoms**: `kubectl exec agent-pod -- ps aux` shows nginx
**Causes**: Using placeholder image instead of agent image

**Solutions**:
```bash
# 1. Check actual image
kubectl get pod agent-pod -o yaml | grep image:

# 2. Update deployment with correct image
kubectl edit deployment agent-memory-rust

# 3. Redeploy
kubectl rollout restart deployment agent-memory-rust
```

### Issue: Port forwarding not working
**Symptoms**: Connection refused errors
**Causes**: 
- [ ] Wrong service name
- [ ] Service not ready
- [ ] Port conflicts

**Solutions**:
```bash
# 1. Check service exists
kubectl get svc -n ai-infrastructure

# 2. Check service endpoints
kubectl get endpoints -n ai-infrastructure

# 3. Kill existing port forwards
pkill -f "port-forward"

# 4. Restart port forwarding
kubectl port-forward -n ai-infrastructure svc/agent-dashboard-service 8081:80
```

### Issue: Dashboard shows connection errors
**Symptoms**: "Check FastAPI backend connection" messages
**Causes**: API not accessible from dashboard

**Solutions**:
```bash
# 1. Test API directly
curl -s http://localhost:5006/api/agents

# 2. Check API pod logs
kubectl logs dashboard-api-pod -n ai-infrastructure

# 3. Verify service configuration
kubectl describe svc dashboard-api-service -n ai-infrastructure
```

---

## 📋 Cleanup Commands

### Stop Port Forwards
```bash
# Kill all port forwards
pkill -f "port-forward"

# Or kill specific PIDs if saved
kill $DASHBOARD_PID $API_PID $AGENT_PID
```

### Remove Deployments
```bash
# Delete all deployments in namespace
kubectl delete all -n ai-infrastructure --all

# Delete PVCs
kubectl delete pvc --all -n ai-infrastructure

# Delete namespace
kubectl delete namespace ai-infrastructure
```

---

## ✅ Success Criteria

### Minimum Working System
- [ ] Dashboard loads at http://localhost:8081
- [ ] API accessible at http://localhost:5006
- [ ] At least one agent pod running
- [ ] Dashboard shows agent data (not empty)
- [ ] Add Agent wizard opens and functions

### Full System
- [ ] All agent types deployable via wizard
- [ ] Real-time data updates working
- [ ] Toast notifications functioning
- [ ] Agent health checks passing
- [ ] Performance metrics available

### Production Ready
- [ ] Resource limits configured
- [ ] Health checks implemented
- [ ] Monitoring endpoints available
- [ ] Backup/restore procedures documented
- [ ] Security best practices applied

---

## 📞 Support

If you encounter issues not covered in this checklist:

1. **Check logs**: `kubectl logs <pod-name> -n ai-infrastructure`
2. **Describe resources**: `kubectl describe <resource> <name> -n ai-infrastructure`
3. **Check events**: `kubectl get events -n ai-infrastructure --sort-by=.metadata.creationTimestamp`
4. **Review documentation**: See `docs/AGENT-DEPLOYMENT-ISSUES-AND-SOLUTIONS.md`

---

## 🎉 Deployment Complete!

When all checks pass, your AI Agents deployment is ready for use:

- **Dashboard**: http://localhost:8081
- **API**: http://localhost:5006
- **API Docs**: http://localhost:5006/docs

You can now deploy and manage AI agents through the web interface! 🚀

# Dashboard Migration Guide

## Overview

This guide provides step-by-step instructions for migrating from the original static dashboard to the new comprehensive AI Agents Analytics Dashboard.

## 🔄 Migration Process

### Phase 1: Preparation

#### 1.1 Backup Current Configuration
```bash
# Backup existing dashboard ConfigMaps
kubectl get configmap dashboard-html -n ai-infrastructure -o yaml > dashboard-html-backup.yaml
kubectl get configmap dashboard-api -n ai-infrastructure -o yaml > dashboard-api-backup.yaml

# Backup existing deployments
kubectl get deployment dashboard-api -n ai-infrastructure -o yaml > dashboard-api-deployment-backup.yaml
kubectl get deployment agent-dashboard -n ai-infrastructure -o yaml > agent-dashboard-deployment-backup.yaml
```

#### 1.2 Document Current Metrics
```bash
# Note current port forwards
ps aux | grep port-forward

# Document current URLs
echo "Current Dashboard: http://localhost:8082"
echo "Current API: http://localhost:5000"
```

### Phase 2: Deploy New Dashboard

#### 2.1 Deploy Comprehensive Dashboard
```bash
# Make deployment script executable
chmod +x deploy-comprehensive-dashboard.sh

# Deploy new dashboard
./deploy-comprehensive-dashboard.sh
```

#### 2.2 Verify Deployment
```bash
# Check new pods
kubectl get pods -n ai-infrastructure -l component=analytics

# Check services
kubectl get svc -n ai-infrastructure -l component=analytics

# Check logs
kubectl logs deployment/comprehensive-dashboard-api -n ai-infrastructure
kubectl logs deployment/comprehensive-dashboard-frontend -n ai-infrastructure
```

### Phase 3: Port Forward Migration

#### 3.1 Stop Old Port Forwards
```bash
# Find and kill old port forwards
pkill -f "port-forward.*8082"
pkill -f "port-forward.*5000"
```

#### 3.2 Start New Port Forwards
```bash
# Start new port forwards
kubectl port-forward svc/comprehensive-dashboard-frontend 8083:80 -n ai-infrastructure &
kubectl port-forward svc/comprehensive-dashboard-api 5001:5000 -n ai-infrastructure &
```

#### 3.3 Update Access URLs
- **Old Dashboard**: http://localhost:8082 → **New Dashboard**: http://localhost:8083
- **Old API**: http://localhost:5000 → **New API**: http://localhost:5001

### Phase 4: Validation

#### 4.1 Health Checks
```bash
# Test new API health
curl http://localhost:5001/health

# Test new endpoints
curl http://localhost:5001/api/v2/agents
curl http://localhost:5001/api/v2/skills
curl http://localhost:5001/api/v2/failures/analysis
```

#### 4.2 Dashboard Validation
1. **Access New Dashboard**: http://localhost:8083
2. **Verify Metrics**: Check that agent counts are realistic
3. **Check Skills**: Verify skill descriptions are loaded
4. **Test Charts**: Ensure time-series charts display data
5. **Validate Failure Analysis**: Check failure tracking works

#### 4.3 Feature Comparison

| Feature | Old Dashboard | New Dashboard |
|---|---|---|
| Agent Count | Static (2) | Dynamic (all types) |
| Success Rate | Hardcoded (99.2%) | Real calculation |
| Skills | Count only (64) | Full descriptions |
| Time-series | ❌ | ✅ Interactive charts |
| Failure Analysis | ❌ | ✅ Root cause & post-mortem |
| Theme Toggle | ❌ | ✅ Dark/Light |
| Auto-refresh | ❌ | ✅ 30-second intervals |
| API Documentation | ❌ | ✅ FastAPI docs |

### Phase 5: Cleanup (Optional)

#### 5.1 Remove Old Components
```bash
# Remove old deployments (after validation)
kubectl delete deployment dashboard-api -n ai-infrastructure
kubectl delete deployment agent-dashboard -n ai-infrastructure

# Remove old services
kubectl delete service dashboard-api -n ai-infrastructure
kubectl delete service agent-dashboard -n ai-infrastructure

# Remove old ConfigMaps
kubectl delete configmap dashboard-html -n ai-infrastructure
kubectl delete configmap dashboard-api -n ai-infrastructure
```

#### 5.2 Update Documentation
- Update any documentation referencing old URLs
- Update scripts that use old API endpoints
- Update user guides with new dashboard access information

## 🚨 Rollback Plan

If migration fails, follow these steps to rollback:

### 1. Stop New Components
```bash
# Kill new port forwards
pkill -f "port-forward.*8083"
pkill -f "port-forward.*5001"

# Remove new deployments
kubectl delete deployment comprehensive-dashboard-api -n ai-infrastructure
kubectl delete deployment comprehensive-dashboard-frontend -n ai-infrastructure

# Remove new services
kubectl delete service comprehensive-dashboard-api -n ai-infrastructure
kubectl delete service comprehensive-dashboard-frontend -n ai-infrastructure
```

### 2. Restore Old Components
```bash
# Restore old ConfigMaps
kubectl apply -f dashboard-html-backup.yaml
kubectl apply -f dashboard-api-backup.yaml

# Restore old deployments
kubectl apply -f dashboard-api-deployment-backup.yaml
kubectl apply -f agent-dashboard-deployment-backup.yaml
```

### 3. Restart Old Port Forwards
```bash
# Restart old port forwards
kubectl port-forward svc/agent-dashboard 8082:80 -n ai-infrastructure &
kubectl port-forward svc/dashboard-api 5000:5000 -n ai-infrastructure &
```

## 📋 Migration Checklist

### Pre-Migration
- [ ] Backup existing configurations
- [ ] Document current metrics and URLs
- [ ] Test new deployment script in non-production
- [ ] Schedule migration window
- [ ] Communicate changes to users

### Migration
- [ ] Deploy comprehensive dashboard
- [ ] Verify all pods are running
- [ ] Start new port forwards
- [ ] Test API endpoints
- [ ] Validate dashboard functionality
- [ ] Update documentation

### Post-Migration
- [ ] Monitor for errors
- [ ] Collect user feedback
- [ ] Clean up old components (optional)
- [ ] Update monitoring and alerting
- [ ] Document any issues encountered

## 🔧 Troubleshooting Migration Issues

### Issue 1: New Dashboard Shows "API Connection Lost"
**Solution**: 
1. Check API pod health: `kubectl logs deployment/comprehensive-dashboard-api -n ai-infrastructure`
2. Verify port forward: `ps aux | grep port-forward.*5001`
3. Test API directly: `curl http://localhost:5001/health`

### Issue 2: Agent Count is 0
**Solution**:
1. Check Kubernetes connection: `kubectl cluster-info`
2. Verify labels: `kubectl get pods -n ai-infrastructure --show-labels`
3. Check API logs for collection errors

### Issue 3: Skills Not Loading
**Solution**:
1. Verify skills directory mount: `kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure -- ls /skills`
2. Check file permissions: `kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure -- ls -la /skills`
3. Test skill parsing: `curl http://localhost:5001/api/v2/skills`

### Issue 4: Charts Not Displaying Data
**Solution**:
1. Check database initialization: `kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure -- sqlite3 /tmp/agents_metrics.db ".tables"`
2. Verify metrics collection: `curl http://localhost:5001/api/v2/metrics/timeseries`
3. Check JavaScript console for frontend errors

## 📊 Performance Comparison

| Metric | Old Dashboard | New Dashboard |
|---|---|---|
| Initial Load Time | ~2 seconds | ~3 seconds |
| Update Frequency | Manual | Every 30 seconds |
| Data Accuracy | Static | Real-time |
| Memory Usage | ~64MB | ~256MB |
| CPU Usage | ~50m | ~250m |
| Features | Basic | Comprehensive |

## 🎓 Training and Documentation

### User Training Points

1. **New URL**: Dashboard moved from 8082 to 8083
2. **Enhanced Features**: Time-series charts, failure analysis
3. **Theme Toggle**: Dark/light mode available
4. **Auto-refresh**: Data updates automatically
5. **Detailed Metrics**: Click on metrics for more details

### Administrator Training

1. **New API Endpoints**: `/api/v2/` namespace
2. **Database**: SQLite for time-series data
3. **Logs**: New log locations and formats
4. **Troubleshooting**: New debug commands and procedures
5. **Monitoring**: Updated metrics and alerting

---

## 📞 Support

For migration support:
1. Check this guide first
2. Review the main [Comprehensive Dashboard Guide](COMPREHENSIVE-DASHBOARD-GUIDE.md)
3. Check system logs and API responses
4. Create an issue with detailed error information

---

**Migration Status**: ✅ Documented and Tested  
**Last Updated**: 2025-03-17  
**Version**: 1.0.0

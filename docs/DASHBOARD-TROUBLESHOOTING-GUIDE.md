# Troubleshooting Guide - Comprehensive Dashboard

## Overview

This guide provides comprehensive troubleshooting procedures for the AI Agents Analytics Dashboard, covering common issues, debugging techniques, and recovery procedures.

## 🔍 Diagnostic Tools

### Health Check Commands

```bash
# Check overall dashboard health
curl http://localhost:5001/health

# Check API endpoints
curl http://localhost:5001/api/v2/agents
curl http://localhost:5001/api/v2/skills
curl http://localhost:5001/api/v2/failures/analysis

# Check frontend access
curl -I http://localhost:8083
```

### Kubernetes Diagnostics

```bash
# Check all dashboard components
kubectl get all -n ai-infrastructure -l component=analytics

# Check pod status
kubectl get pods -n ai-infrastructure -l component=analytics

# Check services
kubectl get svc -n ai-infrastructure -l component=analytics

# Check ConfigMaps
kubectl get configmap -n ai-infrastructure -l component=analytics

# Check events
kubectl get events -n ai-infrastructure --sort-by='.lastTimestamp'
```

### Log Analysis

```bash
# API logs
kubectl logs deployment/comprehensive-dashboard-api -n ai-infrastructure -f

# Frontend logs
kubectl logs deployment/comprehensive-dashboard-frontend -n ai-infrastructure -f

# Previous pod logs
kubectl logs deployment/comprehensive-dashboard-api -n ai-infrastructure --previous

# Container-specific logs
kubectl logs deployment/comprehensive-dashboard-api -n ai-infrastructure -c api
```

### Database Diagnostics

```bash
# Check database tables
kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure \
  -- sqlite3 /tmp/agents_metrics.db ".tables"

# Check database schema
kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure \
  -- sqlite3 /tmp/agents_metrics.db ".schema"

# Check data counts
kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure \
  -- sqlite3 /tmp/agents_metrics.db "SELECT COUNT(*) FROM agents;"

# Check recent entries
kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure \
  -- sqlite3 /tmp/agents_metrics.db "SELECT * FROM agents ORDER BY timestamp DESC LIMIT 5;"
```

## 🚨 Common Issues and Solutions

### Issue 1: Dashboard Shows "API Connection Lost"

**Symptoms:**
- Frontend loads but shows "API Connection Lost"
- No data displayed in metrics
- Connection status indicator is red

**Causes:**
- API pod is not running
- Port forward is not active
- API service is not accessible

**Solutions:**

1. **Check API Pod Status**
```bash
kubectl get pods -n ai-infrastructure -l app=comprehensive-dashboard-api
```

2. **Check API Logs**
```bash
kubectl logs deployment/comprehensive-dashboard-api -n ai-infrastructure
```

3. **Restart Port Forward**
```bash
# Kill existing port forward
pkill -f "port-forward.*5001"

# Start new port forward
kubectl port-forward svc/comprehensive-dashboard-api 5001:5000 -n ai-infrastructure &
```

4. **Test API Directly**
```bash
curl http://localhost:5001/health
```

5. **Restart API Deployment**
```bash
kubectl rollout restart deployment/comprehensive-dashboard-api -n ai-infrastructure
```

### Issue 2: Agent Count is 0 or Incorrect

**Symptoms:**
- Dashboard shows 0 agents
- Agent count doesn't match expected number
- Missing agent types

**Causes:**
- Kubernetes connection issues
- Incorrect labels on pods
- Agent discovery logic errors

**Solutions:**

1. **Check Kubernetes Connection**
```bash
kubectl cluster-info
kubectl get nodes
```

2. **Check Agent Pods**
```bash
kubectl get pods -n ai-infrastructure --show-labels
kubectl get pods -n ai-infrastructure -l "app in (agent-dashboard,dashboard-api,comprehensive-dashboard-api)"
```

3. **Check API Agent Collection**
```bash
curl http://localhost:5001/api/v2/agents | jq '.total_count'
```

4. **Check Agent Types**
```bash
curl http://localhost:5001/api/v2/agents | jq '.by_type'
```

5. **Debug Agent Collection Logic**
```bash
kubectl logs deployment/comprehensive-dashboard-api -n ai-infrastructure | grep -i agent
```

### Issue 3: Skills Not Loading or Showing Incorrect Data

**Symptoms:**
- Skills count is 0
- Skill descriptions are missing
- Risk/autonomy levels not showing

**Causes:**
- Skills directory not mounted
- SKILL.md files have parsing errors
- File permission issues

**Solutions:**

1. **Check Skills Directory Mount**
```bash
kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure -- ls -la /skills
```

2. **Check SKILL.md Files**
```bash
kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure -- find /skills -name "SKILL.md" | head -5
```

3. **Test Skill Parsing**
```bash
curl http://localhost:5001/api/v2/skills | jq '.total_count'
```

4. **Check File Permissions**
```bash
kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure -- ls -la /skills/optimize-costs/
```

5. **Validate SKILL.md Format**
```bash
kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure \
  -- head -20 /skills/optimize-costs/SKILL.md
```

### Issue 4: Charts Not Displaying Data

**Symptoms:**
- Time-series charts are empty
- Bar charts show no data
- Chart.js errors in browser console

**Causes:**
- No time-series data in database
- API returning empty data
- Frontend JavaScript errors

**Solutions:**

1. **Check Time-Series API**
```bash
curl "http://localhost:5001/api/v2/metrics/timeseries?metric_type=agents"
```

2. **Check Database Data**
```bash
kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure \
  -- sqlite3 /tmp/agents_metrics.db "SELECT COUNT(*) FROM agents;"
```

3. **Check Browser Console**
- Open browser developer tools
- Check for JavaScript errors
- Look for Chart.js errors

4. **Test Chart Data Format**
```bash
curl "http://localhost:5001/api/v2/metrics/timeseries?metric_type=agents" | jq '.data[0]'
```

5. **Force Data Collection**
```bash
# Trigger API call to generate data
curl http://localhost:5001/api/v2/agents
curl http://localhost:5001/api/v2/skills
```

### Issue 5: Failure Analysis Not Working

**Symptoms:**
- Success rate shows 0%
- No failure data displayed
- Failure analysis returns empty results

**Causes:**
- No failure data in database
- Success rate calculation errors
- Missing failure tracking

**Solutions:**

1. **Check Failure Analysis API**
```bash
curl "http://localhost:5001/api/v2/failures/analysis"
```

2. **Check Database for Failures**
```bash
kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure \
  -- sqlite3 /tmp/agents_metrics.db "SELECT COUNT(*) FROM failures;"
```

3. **Report Test Failure**
```bash
curl -X POST "http://localhost:5001/api/v2/failures/report" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "test-agent",
    "error_type": "test_error",
    "error_message": "Test error for debugging",
    "severity": "low"
  }'
```

4. **Verify Success Rate Calculation**
```bash
curl "http://localhost:5001/api/v2/failures/analysis" | jq '.success_rate'
```

### Issue 6: High Memory or CPU Usage

**Symptoms:**
- API pod using excessive memory
- High CPU consumption
- Pod restarts due to resource limits

**Causes:**
- Memory leaks in API
- Large database queries
- Too frequent data collection

**Solutions:**

1. **Check Resource Usage**
```bash
kubectl top pods -n ai-infrastructure -l component=analytics
```

2. **Check Memory Limits**
```bash
kubectl describe deployment comprehensive-dashboard-api -n ai-infrastructure
```

3. **Monitor Database Size**
```bash
kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure \
  -- sqlite3 /tmp/agents_metrics.db "SELECT COUNT(*) FROM agents;"
```

4. **Restart Deployment**
```bash
kubectl rollout restart deployment/comprehensive-dashboard-api -n ai-infrastructure
```

5. **Adjust Resource Limits**
```yaml
# Edit deployment to increase limits
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## 🔧 Advanced Debugging

### Database Debugging

```bash
# Connect to database
kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure -it -- \
  sqlite3 /tmp/agents_metrics.db

# Inside SQLite
.tables                    # List tables
.schema                    # Show schema
SELECT * FROM agents LIMIT 5;  # Sample data
SELECT COUNT(*) FROM agents;   # Record counts
DELETE FROM agents WHERE timestamp < '2025-03-16';  # Cleanup old data
```

### Network Debugging

```bash
# Test service connectivity
kubectl exec deployment/comprehensive-dashboard-frontend -n ai-infrastructure \
  -- wget -qO- http://comprehensive-dashboard-api:5000/health

# Check service endpoints
kubectl get endpoints -n ai-infrastructure
kubectl describe svc comprehensive-dashboard-api -n ai-infrastructure
```

### Performance Debugging

```bash
# Check API response times
time curl http://localhost:5001/api/v2/agents

# Monitor API performance
kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure \
  -- ps aux

# Check database query performance
kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure \
  -- sqlite3 /tmp/agents_metrics.db ".timer on" \
  "SELECT COUNT(*) FROM agents;"
```

## 🚨 Emergency Procedures

### Complete Dashboard Recovery

```bash
# 1. Delete all dashboard components
kubectl delete deployment comprehensive-dashboard-api -n ai-infrastructure
kubectl delete deployment comprehensive-dashboard-frontend -n ai-infrastructure
kubectl delete service comprehensive-dashboard-api -n ai-infrastructure
kubectl delete service comprehensive-dashboard-frontend -n ai-infrastructure
kubectl delete configmap comprehensive-dashboard-api -n ai-infrastructure
kubectl delete configmap comprehensive-dashboard-html -n ai-infrastructure

# 2. Clean up port forwards
pkill -f "port-forward.*8083"
pkill -f "port-forward.*5001"

# 3. Redeploy
./deploy-comprehensive-dashboard.sh

# 4. Verify deployment
kubectl get pods -n ai-infrastructure -l component=analytics
kubectl get svc -n ai-infrastructure -l component=analytics
```

### Database Reset

```bash
# 1. Access API pod
kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure -it -- bash

# 2. Reset database
rm -f /tmp/agents_metrics.db
exit

# 3. Restart API to recreate database
kubectl rollout restart deployment/comprehensive-dashboard-api -n ai-infrastructure
```

### Port Forward Recovery

```bash
# 1. Kill all existing port forwards
pkill -f "port-forward"

# 2. Start fresh port forwards
kubectl port-forward svc/comprehensive-dashboard-frontend 8083:80 -n ai-infrastructure &
kubectl port-forward svc/comprehensive-dashboard-api 5001:5000 -n ai-infrastructure &

# 3. Verify access
curl http://localhost:5001/health
curl -I http://localhost:8083
```

## 📊 Performance Monitoring

### Key Metrics to Monitor

1. **API Response Time**: Should be < 500ms for most endpoints
2. **Memory Usage**: Should be < 512MB for API pod
3. **CPU Usage**: Should be < 500m for normal operations
4. **Database Size**: Monitor for growth trends
5. **Error Rate**: Should be < 1% of total requests

### Monitoring Commands

```bash
# Resource usage
kubectl top pods -n ai-infrastructure -l component=analytics

# API response time
time curl http://localhost:5001/api/v2/agents

# Database size
kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure \
  -- du -h /tmp/agents_metrics.db

# Error monitoring
kubectl logs deployment/comprehensive-dashboard-api -n ai-infrastructure | grep -i error
```

## 📋 Troubleshooting Checklist

### Initial Diagnosis

- [ ] Check pod status: `kubectl get pods -n ai-infrastructure -l component=analytics`
- [ ] Check service status: `kubectl get svc -n ai-infrastructure -l component=analytics`
- [ ] Check port forwards: `ps aux | grep port-forward`
- [ ] Test API health: `curl http://localhost:5001/health`
- [ ] Test frontend access: `curl -I http://localhost:8083`

### Data Issues

- [ ] Verify agent collection: `curl http://localhost:5001/api/v2/agents | jq '.total_count'`
- [ ] Verify skill parsing: `curl http://localhost:5001/api/v2/skills | jq '.total_count'`
- [ ] Check database: `kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure -- sqlite3 /tmp/agents_metrics.db ".tables"`
- [ ] Test failure reporting: `curl -X POST "http://localhost:5001/api/v2/failures/report" -d '{"agent_name":"test","error_type":"test","error_message":"test"}'`

### Performance Issues

- [ ] Check resource usage: `kubectl top pods -n ai-infrastructure -l component=analytics`
- [ ] Monitor response times: `time curl http://localhost:5001/api/v2/agents`
- [ ] Check database size: `kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure -- du -h /tmp/agents_metrics.db`
- [ ] Review logs for errors: `kubectl logs deployment/comprehensive-dashboard-api -n ai-infrastructure | tail -50`

### Frontend Issues

- [ ] Check browser console for JavaScript errors
- [ ] Verify API connectivity from browser: Network tab
- [ ] Test Chart.js rendering: Check chart elements in DOM
- [ ] Verify theme toggle functionality

## 🆘 Getting Help

### Information to Collect

When reporting issues, collect the following:

1. **System Information**
```bash
kubectl version
kubectl cluster-info
docker version
```

2. **Dashboard Status**
```bash
kubectl get all -n ai-infrastructure -l component=analytics
kubectl logs deployment/comprehensive-dashboard-api -n ai-infrastructure --tail=50
```

3. **API Test Results**
```bash
curl -v http://localhost:5001/health
curl -v http://localhost:5001/api/v2/agents
```

4. **Browser Console Errors**
- Screenshots of console errors
- Network tab failures
- Chart rendering issues

### Common Debugging Commands

```bash
# Quick health check
curl http://localhost:5001/health && echo "✅ API OK" || echo "❌ API Failed"

# Check data collection
curl -s http://localhost:5001/api/v2/agents | jq '.total_count' && echo "✅ Agents OK" || echo "❌ Agents Failed"

# Check skills parsing
curl -s http://localhost:5001/api/v2/skills | jq '.total_count' && echo "✅ Skills OK" || echo "❌ Skills Failed"

# Full system check
echo "=== Dashboard Health Check ==="
kubectl get pods -n ai-infrastructure -l component=analytics
echo "=== API Health ==="
curl http://localhost:5001/health
echo "=== Data Collection ==="
curl -s http://localhost:5001/api/v2/agents | jq '.total_count'
curl -s http://localhost:5001/api/v2/skills | jq '.total_count'
```

---

**Troubleshooting Guide Version**: 1.0.0  
**Last Updated**: 2025-03-17  
**Dashboard Version**: 2.0.0

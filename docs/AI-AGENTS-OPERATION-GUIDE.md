# AI Agents Operation Guide

## Overview

This guide covers the day-to-day operations, management, and troubleshooting of the Cloud AI Agents ecosystem. It's designed for operators, SREs, and system administrators responsible for maintaining the AI agents platform.

## Daily Operations

### System Health Checks

#### Morning Checklist
```bash
# 1. Check overall system status
kubectl get pods -n ai-infrastructure
kubectl get services -n ai-infrastructure

# 2. Verify dashboard accessibility
curl -s http://localhost:8888 | grep -i "cloud ai agents"

# 3. Check API endpoints
curl -s http://localhost:5000/api/cluster-status.json

# 4. Review system metrics
kubectl top pods -n ai-infrastructure
kubectl top nodes
```

#### Health Monitoring Dashboard
Access the dashboard at `http://localhost:8888` and verify:
- ✅ System status shows "Online"
- ✅ All agents are "Running" or "Idle"
- ✅ Success rate > 95%
- ✅ No critical alerts

### Agent Management

#### View Agent Status
```bash
# List all agents with details
kubectl get pods -n ai-infrastructure -l component=agent-memory -o wide

# Check individual agent logs
kubectl logs -f deployment/agent-memory-rust -n ai-infrastructure

# Agent performance metrics
curl -s http://localhost:5000/api/core/ai/runtime/status | jq .
```

#### Agent Operations
```bash
# Restart specific agent
kubectl rollout restart deployment/agent-memory-rust -n ai-infrastructure

# Scale agent deployment
kubectl scale deployment agent-memory-rust --replicas=3 -n ai-infrastructure

# Update agent image
kubectl set image deployment/agent-memory-rust \
  agent-memory=agent-memory-rust:v2.1.0 -n ai-infrastructure
```

### Skills Management

#### View Available Skills
```bash
# List all skills via API
curl -s http://localhost:5000/api/skills | jq '.skills[]'

# Check skill execution status
curl -s http://localhost:5000/api/skills/status | jq .
```

#### Execute Skills
```bash
# Execute skill via API
curl -X POST http://localhost:5000/api/skills/execute \
  -H "Content-Type: application/json" \
  -d '{"skill": "cost-analysis", "parameters": {"cluster": "production"}}'

# Monitor skill execution
kubectl logs -f deployment/skills-orchestrator -n ai-infrastructure
```

## Monitoring and Alerting

### Key Metrics to Monitor

#### System Metrics
```yaml
Critical Metrics:
  - Pod CPU/Memory usage
  - PVC storage utilization
  - Network latency and throughput
  - API response times
  - Error rates and success rates

Thresholds:
  CPU Usage: > 80% (Warning), > 90% (Critical)
  Memory Usage: > 85% (Warning), > 95% (Critical)
  Storage Usage: > 80% (Warning), > 90% (Critical)
  API Response Time: > 500ms (Warning), > 1000ms (Critical)
  Error Rate: > 5% (Warning), > 10% (Critical)
```

#### Agent-Specific Metrics
```yaml
Agent Performance:
  - Execution success rate
  - Average response time
  - Skills executed per hour
  - Memory database size
  - Llama.cpp inference time

Business Metrics:
  - Cost optimization savings
  - Security issues detected
  - Compliance violations found
  - Infrastructure improvements made
```

### Alert Configuration

#### Prometheus Alerts
```yaml
groups:
- name: ai-agents
  rules:
  - alert: AgentDown
    expr: up{job="ai-agents"} == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "AI Agent {{ $labels.agent }} is down"
      description: "Agent {{ $labels.agent }} has been down for more than 2 minutes"

  - alert: HighErrorRate
    expr: rate(agent_errors_total[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High error rate for {{ $labels.agent }}"
      description: "Error rate is {{ $value }} errors per second"
```

#### Dashboard Alerts
The dashboard provides real-time alerts for:
- Agent failures
- Skill execution errors
- Performance degradation
- Resource exhaustion

### Log Management

#### Structured Logging
```json
{
  "timestamp": "2024-03-15T10:30:00Z",
  "level": "info",
  "component": "agent-memory-rust",
  "agent_id": "agent-1",
  "skill": "cost-analysis",
  "execution_id": "exec-12345",
  "duration_ms": 1250,
  "success": true,
  "message": "Skill execution completed successfully"
}
```

#### Log Collection
```bash
# View real-time logs
kubectl logs -f -n ai-infrastructure -l component=agent-memory

# Search logs for errors
kubectl logs -n ai-infrastructure --since=1h | grep -i error

# Export logs for analysis
kubectl logs -n ai-infrastructure --since=24h > ai-agents-$(date +%Y%m%d).log
```

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: Agent Pod Not Starting
**Symptoms:**
- Pod status: `CrashLoopBackOff` or `Pending`
- Dashboard shows agent as "Error"

**Diagnosis:**
```bash
# Check pod events
kubectl describe pod <pod-name> -n ai-infrastructure

# Check resource constraints
kubectl describe node <node-name>

# Check PVC status
kubectl get pvc -n ai-infrastructure
```

**Solutions:**
```bash
# Fix resource limits
kubectl patch deployment agent-memory-rust -n ai-infrastructure -p '{"spec":{"template":{"spec":{"containers":[{"name":"agent-memory","resources":{"limits":{"memory":"1Gi"}}}]}}}}'

# Recreate PVC if corrupted
kubectl delete pvc agent-memory-pvc -n ai-infrastructure
kubectl apply -f core/resources/ai-inference/shared/agent-memory-deployment.yaml
```

#### Issue 2: Dashboard Not Accessible
**Symptoms:**
- Connection refused when accessing dashboard
- 504 Gateway Timeout errors

**Diagnosis:**
```bash
# Check service status
kubectl get svc agent-dashboard-service -n ai-infrastructure

# Check pod status
kubectl get pods -n ai-infrastructure -l component=agent-dashboard

# Check port-forward
ps aux | grep "kubectl port-forward"
```

**Solutions:**
```bash
# Restart port-forward
pkill -f "kubectl port-forward.*agent-dashboard"
kubectl port-forward svc/agent-dashboard-service 8888:80 -n ai-infrastructure &

# Restart dashboard deployment
kubectl rollout restart deployment/agent-dashboard -n ai-infrastructure
```

#### Issue 3: Skill Execution Failures
**Symptoms:**
- Skills returning error responses
- High error rates in dashboard

**Diagnosis:**
```bash
# Check skill worker logs
kubectl logs -f deployment/skills-orchestrator -n ai-infrastructure

# Check Temporal workflow status
kubectl exec -it temporal-frontend-xxx -n ai-infrastructure -- tctl --ns default workflow list

# Check memory agent connectivity
curl -s http://ai-inference-service.ai-infrastructure.svc.cluster.local:8080/health
```

**Solutions:**
```bash
# Restart skills orchestrator
kubectl rollout restart deployment/skills-orchestrator -n ai-infrastructure

# Clear stuck workflows
kubectl exec -it temporal-frontend-xxx -n ai-infrastructure -- tctl --ns default workflow terminate --workflow-id <workflow-id>

# Reset memory agent
kubectl exec -it agent-memory-rust-xxx -n ai-infrastructure -- rm /data/memory.db
kubectl rollout restart deployment/agent-memory-rust -n ai-infrastructure
```

#### Issue 4: Performance Degradation
**Symptoms:**
- Slow API response times
- High CPU/memory usage
- Dashboard lag

**Diagnosis:**
```bash
# Check resource usage
kubectl top pods -n ai-infrastructure
kubectl top nodes

# Check database size
kubectl exec -it agent-memory-rust-xxx -n ai-infrastructure -- ls -lh /data/

# Check network latency
kubectl exec -it agent-memory-rust-xxx -n ai-infrastructure -- ping temporal-frontend.ai-infrastructure.svc.cluster.local
```

**Solutions:**
```bash
# Scale horizontally
kubectl scale deployment agent-memory-rust --replicas=3 -n ai-infrastructure

# Optimize database
kubectl exec -it agent-memory-rust-xxx -n ai-infrastructure -- sqlite3 /data/memory.db "VACUUM;"

# Add resources
kubectl patch deployment agent-memory-rust -n ai-infrastructure -p '{"spec":{"template":{"spec":{"containers":[{"name":"agent-memory","resources":{"limits":{"cpu":"1000m"}}}]}}}}'
```

## Performance Optimization

### Resource Tuning

#### CPU and Memory Optimization
```yaml
# Production-ready resource limits
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"

# HPA configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-memory-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-memory-rust
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### Database Optimization
```bash
# SQLite optimization commands
kubectl exec -it agent-memory-rust-xxx -n ai-infrastructure -- sqlite3 /data/memory.db "
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;
VACUUM;
ANALYZE;
"
```

### Network Optimization

#### Service Mesh Configuration
```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: ai-agents
spec:
  host: agent-memory-rust.ai-infrastructure.svc.cluster.local
  trafficPolicy:
    loadBalancer:
      simple: LEAST_CONN
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        maxRequestsPerConnection: 10
    circuitBreaker:
      consecutiveErrors: 3
      interval: 30s
      baseEjectionTime: 30s
```

#### DNS Optimization
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health {
          lameduck 5s
        }
        ready
        kubernetes cluster.local in-addr.arpa ip6.arpa {
          pods insecure
          fallthrough in-addr.arpa ip6.arpa
          ttl 30
        }
        prometheus :9153
        forward . /etc/resolv.conf {
          max_concurrent 1000
        }
        cache 30
        loop
        reload
        loadbalance
    }
```

## Maintenance Operations

### Regular Maintenance Tasks

#### Weekly Tasks
```bash
#!/bin/bash
# weekly-maintenance.sh

echo "Starting weekly maintenance..."

# 1. Backup configurations
kubectl get configmaps -n ai-infrastructure -o yaml > backup/config-$(date +%Y%m%d).yaml
kubectl get deployments -n ai-infrastructure -o yaml > backup/deployments-$(date +%Y%m%d).yaml

# 2. Clean up old logs
kubectl exec -it agent-memory-rust-xxx -n ai-infrastructure -- find /var/log -name "*.log" -mtime +7 -delete

# 3. Optimize database
kubectl exec -it agent-memory-rust-xxx -n ai-infrastructure -- sqlite3 /data/memory.db "VACUUM;"

# 4. Update certificates
kubectl get certificates -n ai-infrastructure

# 5. Check resource usage
kubectl top pods -n ai-infrastructure > backup/resource-usage-$(date +%Y%m%d).txt

echo "Weekly maintenance completed"
```

#### Monthly Tasks
```bash
#!/bin/bash
# monthly-maintenance.sh

echo "Starting monthly maintenance..."

# 1. Security updates
kubectl get pods -n ai-infrastructure -o jsonpath='{.items[*].spec.containers[*].image}' | tr ' ' '\n' | sort -u

# 2. Performance review
kubectl get hpa -n ai-infrastructure
kubectl get vpa -n ai-infrastructure

# 3. Capacity planning
kubectl describe nodes | grep -A 5 "Allocated resources"

# 4. Backup verification
kubectl exec -it agent-memory-rust-xxx -n ai-infrastructure -- sqlite3 /data/memory.db ".backup /backup/memory-$(date +%Y%m%d).db"

# 5. Log rotation
kubectl logs -n ai-infrastructure --since=30d > backup/logs-$(date +%Y%m%d).log

echo "Monthly maintenance completed"
```

### Rolling Updates

#### Safe Update Procedure
```bash
#!/bin/bash
# safe-update.sh

COMPONENT=$1
NEW_VERSION=$2

if [ -z "$COMPONENT" ] || [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <component> <new-version>"
    exit 1
fi

echo "Updating $COMPONENT to version $NEW_VERSION..."

# 1. Pre-update checks
kubectl get pods -n ai-infrastructure -l component=$COMPONENT
curl -s http://localhost:5000/api/cluster-status.json

# 2. Update deployment
kubectl set image deployment/$COMPONENT \
  $COMPONENT=$COMPONENT:$NEW_VERSION -n ai-infrastructure

# 3. Monitor rollout
kubectl rollout status deployment/$COMPONENT -n ai-infrastructure --timeout=300s

# 4. Post-update verification
kubectl get pods -n ai-infrastructure -l component=$COMPONENT
curl -s http://localhost:5000/api/cluster-status.json

# 5. Health check
sleep 30
kubectl exec -it deployment/$COMPONENT -n ai-infrastructure -- curl -s http://localhost:8080/health

echo "Update completed successfully"
```

## Security Operations

### Security Monitoring

#### Access Control
```bash
# Review RBAC permissions
kubectl auth can-i --list --as=system:serviceaccount:ai-infrastructure:default

# Audit recent actions
kubectl get events -n ai-infrastructure --sort-by='.lastTimestamp' | tail -20

# Check network policies
kubectl get networkpolicies -n ai-infrastructure -o yaml
```

#### Security Scans
```bash
# Run security scan
kubectl get pods -n ai-infrastructure -o json | jq '.items[].spec.containers[].image' | \
  xargs -I {} trivy image {}

# Check for vulnerabilities
kubectl run security-scan --image=aquasec/trivy:latest --rm -i -- \
  image agent-memory-rust:latest --format json > security-scan-$(date +%Y%m%d).json
```

### Incident Response

#### Security Incident Procedure
```bash
#!/bin/bash
# security-incident-response.sh

echo "Security incident response initiated..."

# 1. Isolate affected systems
kubectl scale deployment --replicas=0 agent-memory-rust -n ai-infrastructure

# 2. Preserve evidence
kubectl get pods -n ai-infrastructure -o yaml > incident/pods-$(date +%Y%m%d-%H%M%S).yaml
kubectl get events -n ai-infrastructure > incident/events-$(date +%Y%m%d-%H%M%S).log

# 3. Enable audit logging
kubectl apply -f - <<EOF
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: Metadata
  namespaces: ["ai-infrastructure"]
EOF

# 4. Notify security team
echo "Security incident detected. Immediate response actions taken." | \
  mail -s "AI Agents Security Incident" security-team@company.com

echo "Security incident response completed"
```

## Backup and Disaster Recovery

### Automated Backup

#### Daily Backup Script
```bash
#!/bin/bash
# daily-backup.sh

BACKUP_DIR="/backup/ai-core/ai/runtime/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

echo "Starting daily backup..."

# 1. Backup persistent data
kubectl exec -it agent-memory-rust-xxx -n ai-infrastructure -- \
  tar -czf /backup/memory-data-$(date +%Y%m%d).tar.gz /data/

# 2. Backup configurations
kubectl get all -n ai-infrastructure -o yaml > $BACKUP_DIR/kubernetes-resources.yaml

# 3. Backup custom resources
kubectl get workflows -n ai-infrastructure -o yaml > $BACKUP_DIR/workflows.yaml

# 4. Create restore script
cat > $BACKUP_DIR/restore.sh << 'EOF'
#!/bin/bash
# Restore script for backup dated $(date +%Y%m%d)

echo "Starting restore from backup..."

# Restore configurations
kubectl apply -f kubernetes-resources.yaml

# Restore data
kubectl cp memory-data-$(date +%Y%m%d).tar.gz agent-memory-rust-xxx:/tmp/ -n ai-infrastructure
kubectl exec -it agent-memory-rust-xxx -n ai-infrastructure -- tar -xzf /tmp/memory-data-$(date +%Y%m%d).tar.gz -C /

echo "Restore completed"
EOF

chmod +x $BACKUP_DIR/restore.sh

# 5. Clean up old backups (keep 30 days)
find /backup/ai-agents -type d -mtime +30 -exec rm -rf {} +

echo "Daily backup completed: $BACKUP_DIR"
```

### Disaster Recovery

#### Recovery Procedures
```bash
#!/bin/bash
# disaster-recovery.sh

BACKUP_DATE=$1
if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup-date-YYYYMMDD>"
    exit 1
fi

BACKUP_DIR="/backup/ai-core/ai/runtime/$BACKUP_DATE"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "Starting disaster recovery from $BACKUP_DATE..."

# 1. Verify cluster state
kubectl cluster-info
kubectl get nodes

# 2. Restore namespace and configurations
kubectl apply -f $BACKUP_DIR/kubernetes-resources.yaml

# 3. Wait for pods to be ready
kubectl wait --for=condition=available --timeout=600s deployment --all -n ai-infrastructure

# 4. Restore data
$BACKUP_DIR/restore.sh

# 5. Verify system health
kubectl get pods -n ai-infrastructure
curl -s http://localhost:5000/api/cluster-status.json

echo "Disaster recovery completed"
```

## Conclusion

This operation guide provides comprehensive procedures for managing the AI Agents ecosystem in production. Regular monitoring, proactive maintenance, and proper incident response procedures ensure system reliability and performance.

Operators should familiarize themselves with the troubleshooting procedures and maintain regular backup schedules to ensure quick recovery from any issues.

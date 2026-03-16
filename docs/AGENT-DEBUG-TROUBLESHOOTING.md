# AI Debugging Troubleshooting Guide

## Overview

This troubleshooting guide provides solutions for common issues encountered when using the AI debugging system. It covers installation problems, runtime errors, performance issues, and integration challenges.

## 🔧 Installation Issues

### Python Environment Problems

#### Issue: Module Import Errors
```bash
# Symptoms
ModuleNotFoundError: No module named 'click'
ImportError: cannot import name 'rich'

# Solutions
# Option 1: Install dependencies manually
pip install click rich requests kubernetes pydantic

# Option 2: Use requirements.txt
pip install -r requirements.txt

# Option 3: Use virtual environment
python -m venv debug-env
source debug-env/bin/activate
pip install -r requirements.txt
```

#### Issue: Python Version Compatibility
```bash
# Symptoms
SyntaxError: invalid syntax
TypeError: 'type' object is not subscriptable

# Solutions
# Check Python version
python --version

# Use Python 3.8+
python3.9 -m pip install -r requirements.txt

# For Python 3.7, install compatible versions
pip install "pydantic<2.0" "click<8.0"
```

### Kubernetes Access Issues

#### Issue: kubectl Not Configured
```bash
# Symptoms
error: the server doesn't have a resource type "pods"
The connection to the server localhost:8080 was refused

# Solutions
# Check kubeconfig
kubectl config view

# Set correct context
kubectl config use-context your-cluster-context

# Verify connection
kubectl cluster-info

# Export kubeconfig
export KUBECONFIG=/path/to/your/kubeconfig
```

#### Issue: Permission Denied
```bash
# Symptoms
Error from server (Forbidden): User "system:serviceaccount:default:default" cannot list pods

# Solutions
# Check current user
kubectl auth can-i get pods

# Create service account with proper permissions
kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ai-debugger-sa
  namespace: temporal
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: ai-debugger-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "events"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: ai-debugger-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: ai-debugger-role
subjects:
- kind: ServiceAccount
  name: ai-debugger-sa
  namespace: temporal
EOF

# Use service account
kubectl config set-context $(kubectl config current-context) --namespace=temporal
```

## 🚀 Runtime Issues

### CLI Command Failures

#### Issue: Command Not Found
```bash
# Symptoms
bash: ./quick_debug.sh: Permission denied
python: can't open file 'main.py': [Errno 2] No such file or directory

# Solutions
# Make script executable
chmod +x quick_debug.sh

# Check current directory
pwd
ls -la

# Navigate to correct directory
cd .agents/ai-agent-debugger/scripts
```

#### Issue: Invalid Arguments
```bash
# Symptoms
Usage: main.py debug [OPTIONS]
Error: Invalid value for '--target-component': 'invalid'

# Solutions
# Check valid options
python main.py debug --help

# Use valid components
python main.py debug --target-component agents --issue-type errors --time-range 1h

# Valid components: agents, workflows, infrastructure, all
# Valid issue types: performance, errors, timeouts, connectivity, resource, behavior, general
```

### API Connection Issues

#### Issue: Monitoring Endpoints Unreachable
```bash
# Symptoms
ConnectionError: Failed to establish connection
urllib3.exceptions.MaxRetryError: HTTPConnectionPool

# Solutions
# Check service status
kubectl get svc -n temporal

# Check endpoints
kubectl get endpoints -n temporal

# Port forward for testing
kubectl port-forward -n temporal svc/temporal-worker 8080:8080

# Test connection
curl http://localhost:8080/health
```

#### Issue: Temporal Connection Failed
```bash
# Symptoms
temporalio.serviceerror.RPCError: connection refused
grpc._channel._Rendezvous: <_Rendezvous of RPC that terminated with status code 14>

# Solutions
# Check Temporal service
kubectl get pods -n temporal -l app=temporal-frontend

# Check Temporal port
kubectl get svc -n temporal -l app=temporal-frontend

# Test Temporal connection
temporal --address temporal-frontend.temporal.svc.cluster.local:7233 workflow list
```

### Kubernetes API Issues

#### Issue: API Server Timeout
```bash
# Symptoms
kubectl get pods: connection timed out
Error: the server was unable to respond to the request in a timely manner

# Solutions
# Check API server status
kubectl get componentstatuses

# Check network connectivity
ping kubernetes.default.svc.cluster.local

# Increase timeout
export KUBECTL_COMMAND_TIMEOUT=30
```

#### Issue: Resource Not Found
```bash
# Symptoms
Error: the server doesn't have a resource type "cronjobs"
Error: deployment "temporal-worker" not found

# Solutions
# Check API versions
kubectl api-resources | grep deployment

# Check correct namespace
kubectl get deployments --all-namespaces | grep temporal

# Use correct resource type
kubectl get jobs -n temporal  # instead of cronjobs if not available
```

## 📊 Performance Issues

### Memory Usage Problems

#### Issue: High Memory Consumption
```bash
# Symptoms
OOMKilled
Memory: 512Mi exceeds limit 256Mi

# Solutions
# Check current memory usage
kubectl top pods -n temporal -l app=ai-debugger

# Increase memory limits
kubectl patch deployment ai-debugger -n temporal -p '{"spec":{"template":{"spec":{"containers":[{"name":"debugger","resources":{"limits":{"memory":"1Gi"}}}]}}}}'

# Optimize memory usage
export DEBUG_BATCH_SIZE=50
export DEBUG_WORKERS=2
```

#### Issue: Memory Leaks
```bash
# Symptoms
Memory usage increases over time
Pod restarts due to memory pressure

# Solutions
# Monitor memory trends
kubectl top pods -n temporal -w

# Set up memory monitoring
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: memory-monitor
  namespace: temporal
data:
  monitor.sh: |
    #!/bin/bash
    while true; do
      echo "\$(date): \$(kubectl top pods -n temporal -l app=ai-debugger --no-headers | awk '{print \$3}')"
      sleep 60
    done
EOF

# Add memory monitoring sidecar
kubectl patch deployment ai-debugger -n temporal -p '{"spec":{"template":{"spec":{"containers":[{"name":"memory-monitor","image":"busybox","command":["/bin/sh","-c","while true; do echo \\"\\$(date): Memory usage: \$(cat /sys/fs/cgroup/memory/memory.usage_in_bytes) bytes\\"; sleep 60; done"}]}}}}'
```

### CPU Performance Problems

#### Issue: High CPU Usage
```bash
# Symptoms
CPU usage consistently above 80%
Slow response times

# Solutions
# Check CPU usage
kubectl top pods -n temporal -l app=ai-debugger

# Increase CPU limits
kubectl patch deployment ai-debugger -n temporal -p '{"spec":{"template":{"spec":{"containers":[{"name":"debugger","resources":{"limits":{"cpu":"1000m"}}}]}}}}'

# Optimize CPU usage
export DEBUG_WORKERS=1
export DEBUG_CONCURRENT_REQUESTS=5
```

#### Issue: Slow Response Times
```bash
# Symptoms
Debug sessions taking >5 minutes
API timeouts

# Solutions
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8080/api/v1/debug

# Optimize queries
export DEBUG_QUERY_TIMEOUT=60
export DEBUG_BATCH_SIZE=100

# Add caching
kubectl patch deployment ai-debugger -n temporal -p '{"spec":{"template":{"spec":{"containers":[{"name":"debugger","env":[{"name":"DEBUG_CACHE_ENABLED","value":"true"},{"name":"DEBUG_CACHE_TTL","value":"300"}]}]}}}}'
```

## 🔍 Debugging Issues

### Log Analysis Problems

#### Issue: No Logs Found
```bash
# Symptoms
No logs found for component
Empty log analysis results

# Solutions
# Check pod logs
kubectl logs -n temporal deployment/temporal-worker --since=1h

# Check log paths
kubectl exec -it deployment/temporal-worker -n temporal -- find /var/log -name "*.log"

# Check log rotation
kubectl exec -it deployment/temporal-worker -n temporal -- ls -la /var/log

# Adjust time range
python main.py analyze-logs --component agents --time-range 24h
```

#### Issue: Pattern Matching Failures
```bash
# Symptoms
No matches found for pattern
Regex compilation errors

# Solutions
# Test patterns manually
kubectl logs -n temporal deployment/temporal-worker --since=1h | grep -i "ERROR"

# Use simpler patterns
python main.py analyze-logs --component agents --pattern "ERROR"

# Check pattern syntax
python -c "import re; print(re.compile(r'ERROR.*').pattern)"
```

### Auto-Fix Issues

#### Issue: Auto-Fix Not Working
```bash
# Symptoms
Auto-fix enabled but no fixes applied
Dry-run shows fixes but they don't execute

# Solutions
# Check auto-fix configuration
kubectl get configmap debug-config -n temporal -o yaml | grep auto_fix

# Enable auto-fix
kubectl patch configmap debug-config -n temporal -p '{"data":{"config.yaml":"...\n    auto_fix: true\n..."}}'

# Check permissions
kubectl auth can-i update pods --as=system:serviceaccount:temporal:ai-debugger -n temporal

# Test manual fix
kubectl delete pod temporal-worker-xyz -n temporal
```

#### Issue: Auto-Fix Making Things Worse
```bash
# Symptoms
Auto-fix restarts healthy pods
Auto-fix deletes important resources

# Solutions
# Disable auto-fix immediately
kubectl patch deployment ai-debugger -n temporal -p '{"spec":{"template":{"spec":{"containers":[{"name":"debugger","env":[{"name":"DEBUG_AUTO_FIX","value":"false"}]}]}}}}'

# Review auto-fix logic
kubectl logs -n temporal deployment/ai-debugger | grep "auto-fix"

# Add approval requirement
kubectl patch configmap debug-config -n temporal -p '{"data":{"config.yaml":"...\n    require_approval: true\n..."}}'
```

## 🔗 Integration Issues

### Temporal Integration Problems

#### Issue: Workflow Not Found
```bash
# Symptoms
Workflow not found: debug_system_activity
Activity not registered: record_debug_metrics

# Solutions
# Check registered activities
temporal --address temporal-frontend.temporal.svc.cluster.local:7233 activity list

# Restart worker with debugging activities
kubectl rollout restart deployment/temporal-worker -n temporal

# Check worker logs
kubectl logs -n temporal deployment/temporal-worker | grep -i "register.*activity"
```

#### Issue: Activity Timeout
```bash
# Symptoms
Activity timeout: debug_system_activity
Workflow stuck in running state

# Solutions
# Increase activity timeout
kubectl patch deployment/temporal-worker -n temporal -p '{"spec":{"template":{"spec":{"containers":[{"name":"worker","env":[{"name":"TEMPORAL_ACTIVITY_TIMEOUT","value":"300"}]}]}}}}'

# Check activity execution
kubectl logs -n temporal deployment/temporal-worker | grep "debug_system_activity"

# Test activity manually
temporal --address temporal-frontend.temporal.svc.cluster.local:7233 activity complete --workflow-id test-123 --activity-id debug_system_activity
```

### Kubernetes Operator Issues

#### Issue: CRD Not Installed
```bash
# Symptoms
Error: the server doesn't have a resource type "debugsessions"
CustomResourceDefinition.apiextensions.k8s.io "debugsessions.debug.ai" not found

# Solutions
# Install CRD
kubectl apply -f crd.yaml

# Check CRD status
kubectl get crd debugsessions.debug.ai

# Verify CRD schema
kubectl get crd debugsessions.debug.ai -o yaml
```

#### Issue: Controller Not Reconciling
```bash
# Symptoms
DebugSession stuck in "Pending" status
No events generated

# Solutions
# Check controller logs
kubectl logs -n temporal deployment/debug-session-controller

# Check controller permissions
kubectl auth can-i create debugsessions --as=system:serviceaccount:temporal:debug-session-controller -n temporal

# Trigger reconciliation
kubectl annotate debugsession test-debug debug.ai/trigger-reconcile="$(date)"
```

## 🛠️ Advanced Troubleshooting

### Debug Mode

#### Enable Verbose Logging
```bash
# Set debug log level
export DEBUG_LOG_LEVEL=debug

# Enable verbose output
python main.py debug --target-component agents --issue-type errors --verbose

# Check debug logs
kubectl logs -n temporal deployment/ai-debugger --follow
```

#### Enable Debug Endpoints
```bash
# Enable debug endpoints in configuration
kubectl patch configmap debug-config -n temporal -p '{"data":{"config.yaml":"...\n    debug_endpoints: true\n..."}}'

# Access debug endpoints
kubectl port-forward -n temporal svc/ai-debugger-service 8080:8080
curl http://localhost:8080/debug/config
curl http://localhost:8080/debug/metrics
curl http://localhost:8080/debug/health
```

### Performance Profiling

#### CPU Profiling
```bash
# Enable CPU profiling
export DEBUG_CPU_PROFILE=true
export DEBUG_PROFILE_DURATION=60

# Run with profiling
python main.py debug --target-component agents --issue-type performance --profile

# Analyze profile
go tool pprof cpu.pprof
```

#### Memory Profiling
```bash
# Enable memory profiling
export DEBUG_MEMORY_PROFILE=true

# Run with memory profiling
python main.py debug --target-component agents --issue-type errors --memory-profile

# Analyze memory usage
go tool pprof mem.pprof
```

### Network Debugging

#### Check Network Connectivity
```bash
# Test service connectivity
kubectl run test-pod --image=busybox --rm -it -- nslookup temporal-worker.temporal.svc.cluster.local

# Test port connectivity
kubectl run test-pod --image=busybox --rm -it -- nc -zv temporal-worker.temporal.svc.cluster.local 8080

# Check network policies
kubectl get networkpolicies -n temporal
```

#### Debug DNS Issues
```bash
# Check DNS resolution
kubectl exec -it deployment/ai-debugger -n temporal -- nslookup kubernetes.default.svc.cluster.local

# Check DNS pods
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Test DNS manually
kubectl exec -it deployment/ai-debugger -n temporal -- dig temporal-worker.temporal.svc.cluster.local
```

## 📋 Diagnostic Commands

### System Health Check
```bash
# Complete system health check
#!/bin/bash
echo "=== AI Debugger Health Check ==="

# Check pods
echo "Checking pods..."
kubectl get pods -n temporal -l app=ai-debugger

# Check services
echo "Checking services..."
kubectl get svc -n temporal -l app=ai-debugger

# Check configuration
echo "Checking configuration..."
kubectl get configmap debug-config -n temporal

# Check permissions
echo "Checking permissions..."
kubectl auth can-i get pods --as=system:serviceaccount:temporal:ai-debugger -n temporal

# Check API connectivity
echo "Checking API connectivity..."
kubectl port-forward -n temporal svc/ai-debugger-service 8080:8080 &
PF_PID=$!
sleep 2
if curl -s http://localhost:8080/health > /dev/null; then
    echo "API: OK"
else
    echo "API: FAILED"
fi
kill $PF_PID

# Check monitoring endpoints
echo "Checking monitoring endpoints..."
kubectl get svc -n temporal -l app=temporal-worker
kubectl get endpoints -n temporal -l app=temporal-worker

echo "=== Health Check Complete ==="
```

### Debug Session Analysis
```bash
# Analyze debug session
#!/bin/bash
SESSION_ID=$1

if [ -z "$SESSION_ID" ]; then
    echo "Usage: $0 <session-id>"
    exit 1
fi

echo "=== Debug Session Analysis: $SESSION_ID ==="

# Get session details
kubectl get debugsession $SESSION_ID -n temporal -o yaml

# Check session logs
kubectl logs -n temporal deployment/ai-debugger | grep $SESSION_ID

# Check related events
kubectl get events -n temporal --field-selector involvedObject.name=$SESSION_ID

# Check findings
kubectl get debugsession $SESSION_ID -n temporal -o jsonpath='{.status.findings[*].issue}'

echo "=== Analysis Complete ==="
```

### Performance Analysis
```bash
# Performance analysis script
#!/bin/bash
echo "=== AI Debugger Performance Analysis ==="

# Resource usage
echo "Resource Usage:"
kubectl top pods -n temporal -l app=ai-debugger

# API response times
echo "API Response Times:"
kubectl port-forward -n temporal svc/ai-debugger-service 8080:8080 &
PF_PID=$!
sleep 2
for i in {1..5}; do
    response_time=$(curl -w "%{time_total}" -o /dev/null -s http://localhost:8080/health)
    echo "Request $i: ${response_time}s"
done
kill $PF_PID

# Debug session performance
echo "Debug Session Performance:"
kubectl get debugsessions -n temporal -o custom-columns=NAME:.metadata.name,START_TIME:.status.startTime,DURATION:.status.duration

echo "=== Performance Analysis Complete ==="
```

## 🚨 Emergency Procedures

### Emergency Stop
```bash
# Stop all debugging activities
kubectl scale deployment ai-debugger --replicas=0 -n temporal

# Disable auto-fix
kubectl patch configmap debug-config -n temporal -p '{"data":{"config.yaml":"...\n    auto_fix: false\n..."}}'

# Delete stuck debug sessions
kubectl delete debugsessions --all -n temporal

# Restart with safe configuration
kubectl scale deployment ai-debugger --replicas=1 -n temporal
```

### Emergency Recovery
```bash
# Restore from backup
kubectl apply -f backup/debug-config.yaml
kubectl apply -f backup/ai-debugger-deployment.yaml

# Verify system health
./health-check.sh

# Monitor recovery
kubectl logs -n temporal deployment/ai-debugger -f
```

### Emergency Rollback
```bash
# Rollback to previous version
kubectl rollout undo deployment/ai-debugger -n temporal

# Verify rollback
kubectl rollout status deployment/ai-debugger -n temporal

# Monitor system
kubectl get pods -n temporal -l app=ai-debugger -w
```

---

**Last Updated**: 2026-03-16  
**Version**: 1.0.0  
**Maintainer**: Cloud AI Agents Team

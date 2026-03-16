# AI Agent Debugging Memory for Future Reference

This file serves as a comprehensive memory and knowledge base for debugging AI agents in distributed Kubernetes environments. It captures patterns, solutions, and prevention strategies to prevent regressions and enable rapid problem resolution.

## Core Debugging Principles

### 1. Systematic Approach
- **Health First**: Always start with basic health assessment before deep analysis
- **Correlation Tracking**: Use correlation IDs to trace issues across distributed systems
- **Session Management**: Create reproducible debugging sessions with full artifact preservation
- **LLM Collaboration**: Leverage multiple LLMs for complex debugging scenarios

### 2. Layered Analysis
```
┌─────────────────────────────────────┐
│ LLM-to-LLM Collaborative Analysis │  ← Meta-debugging, AI behavior analysis
├─────────────────────────────────────┤
│ Deep Behavioral Pattern Analysis      │  ← Performance trends, anomaly detection
├─────────────────────────────────────┤
│ Detailed System Health Assessment    │  ← Resource usage, connectivity, state
├─────────────────────────────────────┤
│ Basic Health Check                 │  ← Pod status, service availability
└─────────────────────────────────────┘
```

### 3. Prevention-First Mindset
- Every debugging session should generate prevention strategies
- Document patterns to build knowledge base
- Implement automated monitoring based on findings
- Create self-healing mechanisms for common issues

## Agent-Specific Debugging Patterns

### Memory Agent Debugging

#### Common Issues and Solutions
1. **Memory Leaks**
   - **Symptoms**: Increasing memory usage, OOM kills, frequent restarts
   - **Diagnosis**: `kubectl top pods`, PVC usage analysis, memory profiling
   - **Solution**: Set appropriate memory limits, implement memory monitoring
   - **Prevention**: Memory usage alerts, automatic restart on OOM

2. **State Corruption**
   - **Symptoms**: Inconsistent behavior, data loss, recovery failures
   - **Diagnosis**: State validation, checksum verification, backup integrity
   - **Solution**: Restore from backup, implement state validation
   - **Prevention**: Regular state backups, consistency checks

3. **PVC Issues**
   - **Symptoms**: Mount failures, I/O errors, storage capacity issues
   - **Diagnosis**: PVC status, storage class analysis, node storage
   - **Solution**: Resize PVC, change storage class, fix mount issues
   - **Prevention**: Storage monitoring, capacity planning

#### Debugging Commands
```bash
# Memory agent specific debugging
kubectl get pods -n ai-infrastructure -l component=memory-agent
kubectl top pods -n ai-infrastructure -l component=memory-agent
kubectl get pvc -n ai-infrastructure -l component=memory-agent
kubectl logs -n ai-infrastructure -l component=memory-agent --tail=200

# State analysis
kubectl exec -n ai-infrastructure deployment/memory-agent -- ls -la /data/
kubectl exec -n ai-infrastructure deployment/memory-agent -- du -sh /data/
```

### AI Inference Gateway Debugging

#### Common Issues and Solutions
1. **Model Loading Failures**
   - **Symptoms**: 503 errors, model unavailable, slow responses
   - **Diagnosis**: Model service status, Ollama health, model storage
   - **Solution**: Restart model service, verify model files, check resources
   - **Prevention**: Model health checks, pre-load monitoring

2. **Request Routing Issues**
   - **Symptoms**: Load imbalance, failed requests, timeout errors
   - **Diagnosis**: Service endpoints, nginx config, upstream health
   - **Solution**: Fix service discovery, update routing config, scale upstream
   - **Prevention**: Circuit breakers, health checks, load testing

3. **Performance Degradation**
   - **Symptoms**: High latency, low throughput, resource exhaustion
   - **Diagnosis**: Response time metrics, resource usage, model performance
   - **Solution**: Optimize model serving, scale horizontally, tune resources
   - **Prevention**: Performance monitoring, auto-scaling, resource optimization

#### Debugging Commands
```bash
# Inference gateway specific debugging
kubectl get pods -n ai-infrastructure -l component=ai-inference-gateway
kubectl get services -n ai-infrastructure -l component=ai-inference-gateway
kubectl logs -n ai-infrastructure -l component=ai-inference-gateway --tail=100

# Model health check
kubectl port-forward -n ai-infrastructure service/ollama 11434:11434
curl http://localhost:11434/api/tags

# Gateway health check
kubectl port-forward -n ai-infrastructure service/ai-inference-gateway 8080:80
curl http://localhost:8080/health
```

### Temporal Worker Debugging

#### Common Issues and Solutions
1. **Workflow Timeouts**
   - **Symptoms**: Stuck workflows, timeout errors, incomplete executions
   - **Diagnosis**: Workflow history, activity logs, timeout configurations
   - **Solution**: Adjust timeouts, fix stuck activities, optimize workflow
   - **Prevention**: Timeout monitoring, workflow health checks

2. **Activity Failures**
   - **Symptoms**: Failed activities, retry loops, inconsistent state
   - **Diagnosis**: Activity logs, error analysis, retry policies
   - **Solution**: Fix activity code, adjust retry logic, handle errors
   - **Prevention**: Activity monitoring, error rate alerts

3. **State Consistency Issues**
   - **Symptoms**: Corrupted state, lost updates, race conditions
   - **Diagnosis**: State history, concurrent access analysis
   - **Solution**: Fix state management, implement locking, ensure idempotency
   - **Prevention**: State validation, concurrency controls

#### Debugging Commands
```bash
# Temporal specific debugging
tctl --namespace ai-infrastructure workflow list
tctl --namespace ai-infrastructure activity list
tctl --namespace ai-infrastructure workflow describe --workflow-id <id>

# Check temporal pods
kubectl get pods -n temporal -l app=temporal
kubectl logs -n temporal -l app=temporal --tail=100
```

## Distributed System Debugging Strategies

### Correlation ID Tracking
```bash
# Generate correlation ID
CORRELATION_ID="debug-$(date +%s)-$(uuidgen | cut -c1-8)"

# Use in all debugging commands
kubectl logs -n ai-infrastructure -l component=memory-agent | grep $CORRELATION_ID
curl -H "X-Correlation-ID: $CORRELATION_ID" http://ai-inference-gateway/health
```

### Multi-Cluster Debugging
```bash
# Check all clusters
for cluster in hub spoke1 spoke2; do
  kubectl config use-context $cluster
  echo "=== Cluster: $cluster ==="
  kubectl get pods -n ai-infrastructure -l component=memory-agent
done
```

### Service Mesh Debugging
```bash
# Check Istio configuration
kubectl get virtualservices -n ai-infrastructure
kubectl get destinationrules -n ai-infrastructure
kubectl get gateways -n ai-infrastructure

# Check traffic routing
istioctl proxy-config pods -n ai-infrastructure -l component=memory-agent
```

## LLM-to-LLM Debugging Patterns

### Meta-Debugging Prompts
```python
# Template for LLM-to-LLM debugging
LLM_DEBUG_PROMPT = """
You are debugging another AI (LLM) running in Kubernetes. Analyze this agent state:

{agent_state}

Focus on:
1. Decision-making patterns and potential biases
2. Reasoning chain consistency and logical flow
3. Learning loop effectiveness and adaptation
4. Inter-agent communication protocols
5. Self-awareness and error detection capabilities

Provide:
- Root cause analysis of AI-specific issues
- Behavioral corrections and improvements
- Validation strategies for AI behavior
- Recommendations for AI system architecture
"""
```

### Collaborative Debugging Workflow
1. **State Collection**: Gather comprehensive agent state
2. **Prompt Generation**: Create specific debugging prompts
3. **Multi-LLM Analysis**: Use multiple LLMs for different perspectives
4. **Solution Synthesis**: Combine insights from multiple sources
5. **Validation**: Test and validate recommended fixes
6. **Knowledge Capture**: Document patterns and solutions

## Prevention Strategies Database

### Monitoring Enhancements
```yaml
# Comprehensive monitoring rules
groups:
- name: ai-agent-critical-alerts
  rules:
  - alert: AIAgentDown
    expr: up{job="ai-agents"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "AI agent is down"
      
  - alert: AIAgentHighMemoryUsage
    expr: container_memory_usage_bytes{component="memory-agent"} / container_spec_memory_limit_bytes > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Memory agent high memory usage"
      
  - alert: AIAgentHighRestartRate
    expr: rate(kube_pod_container_status_restarts_total{component="memory-agent"}[5m]) > 0.1
    for: 3m
    labels:
      severity: warning
    annotations:
      summary: "Memory agent high restart rate"
```

### Automated Recovery Procedures
```bash
# Self-healing script for memory agents
#!/bin/bash
AGENT_NAME=$1
NAMESPACE=${2:-ai-infrastructure}
MAX_RESTARTS=5

# Check restart count
RESTARTS=$(kubectl get pods -n $NAMESPACE -l component=$AGENT_NAME -o jsonpath='{.items[0].status.containerStatuses[0].restartCount}')

if [ "$RESTARTS" -gt "$MAX_RESTARTS" ]; then
  echo "High restart count detected, executing recovery..."
  
  # Scale down
  kubectl scale deployment $AGENT_NAME --replicas=0 -n $NAMESPACE
  
  # Wait for termination
  kubectl wait --for=delete pod -l component=$AGENT_NAME -n $NAMESPACE --timeout=60s
  
  # Scale up
  kubectl scale deployment $AGENT_NAME --replicas=1 -n $NAMESPACE
  
  # Verify health
  kubectl wait --for=condition=available deployment/$AGENT_NAME -n $NAMESPACE --timeout=120s
  
  echo "Recovery completed for $AGENT_NAME"
fi
```

### Health Check Implementation
```python
# Comprehensive health check for all agent types
def comprehensive_health_check(agent_type, namespace):
    checks = {}
    
    if agent_type == "memory-agent":
        checks.update({
            'memory_usage': check_memory_usage(),
            'pvc_status': check_pvc_status(),
            'state_consistency': check_state_consistency(),
            'backup_status': check_backup_status()
        })
    elif agent_type == "ai-inference-gateway":
        checks.update({
            'model_availability': check_model_availability(),
            'request_latency': check_request_latency(),
            'upstream_health': check_upstream_health(),
            'routing_correctness': check_routing_correctness()
        })
    elif agent_type == "temporal-worker":
        checks.update({
            'workflow_status': check_workflow_status(),
            'activity_health': check_activity_health(),
            'state_consistency': check_state_consistency(),
            'timeout_status': check_timeout_status()
        })
    
    overall_health = all(check['status'] == 'healthy' for check in checks.values())
    
    return {
        'overall_status': 'healthy' if overall_health else 'unhealthy',
        'checks': checks,
        'timestamp': datetime.utcnow().isoformat(),
        'agent_type': agent_type,
        'namespace': namespace
    }
```

## Emergency Response Procedures

### Critical System Failure
```bash
# Emergency recovery checklist
#!/bin/bash

echo "=== AI Agent Emergency Recovery ==="

# 1. Check cluster health
kubectl get nodes
kubectl get pods --all-namespaces

# 2. Check critical agents
for agent in memory-agent ai-inference-gateway temporal-worker; do
  echo "=== Checking $agent ==="
  kubectl get pods -n ai-infrastructure -l component=$agent
  kubectl get events -n ai-infrastructure --field-selector involvedObject.name=$agent --sort-by='.lastTimestamp'
done

# 3. Restart critical services if needed
kubectl rollout restart deployment/memory-agent -n ai-infrastructure
kubectl rollout restart deployment/ai-inference-gateway -n ai-infrastructure
kubectl rollout restart deployment/temporal-worker -n ai-infrastructure

# 4. Verify recovery
sleep 30
kubectl get pods -n ai-infrastructure
./scripts/debug-ai-agents-k8s.sh all DEBUG_LEVEL=basic
```

### Data Recovery Procedures
```bash
# State recovery for memory agents
#!/bin/bash

BACKUP_DIR="/backups/ai-agents"
NAMESPACE="ai-infrastructure"
AGENT="memory-agent"

# 1. Check current state
echo "=== Current State Analysis ==="
kubectl get pvc -n $NAMESPACE -l component=$AGENT
kubectl exec -n $NAMESPACE deployment/$AGENT -- ls -la /data/

# 2. Restore from backup if needed
if [ "$1" == "restore" ]; then
  echo "=== Restoring from Backup ==="
  kubectl cp $BACKUP_DIR/$AGENT/latest/memory.db $NAMESPACE/deployment/$AGENT:/data/memory.db
  kubectl rollout restart deployment/$AGENT -n $NAMESPACE
fi

# 3. Verify recovery
echo "=== Verification ==="
kubectl exec -n $NAMESPACE deployment/$AGENT -- md5sum /data/memory.db
kubectl logs -n $NAMESPACE -l component=$AGENT --tail=50
```

## Knowledge Base Evolution

### Learning from Debugging Sessions
1. **Pattern Recognition**: Identify recurring issues across sessions
2. **Solution Effectiveness**: Track which solutions work best
3. **Prevention Impact**: Measure effectiveness of prevention strategies
4. **Tool Improvement**: Enhance debugging tools based on usage patterns
5. **Documentation Updates**: Keep knowledge base current and accurate

### Continuous Improvement Process
1. **Session Review**: Analyze each debugging session for insights
2. **Pattern Extraction**: Identify common patterns and root causes
3. **Solution Optimization**: Refine solutions based on effectiveness
4. **Prevention Enhancement**: Improve monitoring and automation
5. **Knowledge Sharing**: Distribute learnings across the ecosystem

This comprehensive memory and knowledge base ensures that debugging AI agents in distributed environments becomes more efficient over time, with patterns recognized, solutions optimized, and prevention strategies continuously improved.

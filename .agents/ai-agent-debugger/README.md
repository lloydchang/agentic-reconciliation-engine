# AI Agent Debugger - Memory and Documentation

This directory contains comprehensive debugging capabilities for AI agents running in Kubernetes distributed systems. This skill enables automated debugging, LLM-to-LLM analysis, tight feedback loops, and prevention strategies.

## Quick Reference

### Debugging Commands

```bash
# Basic health check
python .agents/ai-agent-debugger/scripts/main.py '{"operation": "diagnose", "targetAgent": "memory-agent", "namespace": "ai-infrastructure"}'

# Deep behavioral analysis
python .agents/ai-agent-debugger/scripts/main.py '{"operation": "analyze", "targetAgent": "all", "debugLevel": "deep"}'

# LLM-to-LLM collaborative debugging
python .agents/ai-agent-debugger/scripts/main.py '{"operation": "llm-analyze", "targetAgent": "ai-inference-gateway", "sessionMode": "llm-collaborative"}'

# Interactive debugging session
python .agents/ai-agent-debugger/scripts/main.py '{"operation": "debug", "targetAgent": "all", "sessionMode": "interactive"}'

# Generate prevention strategies
python .agents/ai-agent-debugger/scripts/main.py '{"operation": "prevent", "targetAgent": "all", "outputFormat": "comprehensive"}'

# Automated fixes
python .agents/ai-agent-debugger/scripts/main.py '{"operation": "automate", "targetAgent": "memory-agent", "namespace": "ai-infrastructure"}'
```

### Shell Scripts for Quick Debugging

```bash
# Use the comprehensive debugging script
./scripts/debug-ai-agents-k8s.sh memory-agent DEBUG_LEVEL=detailed

# LLM-to-LLM debugging automation
./scripts/llm-debug-automation.sh ai-inference-gateway ANALYSIS_DEPTH=deep AUTO_FIX=true

# GitOps infrastructure debugging
./scripts/debug-dependency-chain.sh network-infrastructure kustomization
```

## Agent Types and Debugging Strategies

### Memory Agent
- **Common Issues**: Memory leaks, state corruption, persistence failures
- **Debugging Focus**: PVC status, memory usage patterns, state consistency
- **Key Metrics**: Memory utilization, restart counts, state sync latency
- **Prevention**: Memory limits monitoring, state validation, backup verification

### AI Inference Gateway
- **Common Issues**: Model loading failures, request routing errors, performance degradation
- **Debugging Focus**: Model availability, request latency, error rates
- **Key Metrics**: Inference latency, throughput, error rates, model health
- **Prevention**: Model health checks, circuit breakers, performance monitoring

### Temporal Worker
- **Common Issues**: Workflow timeouts, activity failures, state consistency
- **Debugging Focus**: Workflow execution history, activity logs, state transitions
- **Key Metrics**: Workflow success rate, activity duration, state size
- **Prevention**: Workflow timeouts, retry policies, state monitoring

### Consensus Agent
- **Common Issues**: Leader election failures, consensus timeouts, network partitions
- **Debugging Focus**: Consensus state, leader status, network connectivity
- **Key Metrics**: Consensus rounds, leader changes, network latency
- **Prevention**: Network monitoring, quorum health, split-brain detection

## Debugging Workflows

### 1. Immediate Issue Resolution
```bash
# Check pod status
kubectl get pods -n ai-infrastructure -l component=memory-agent

# Check recent events
kubectl get events -n ai-infrastructure --field-selector involvedObject.name=memory-agent

# Check logs for errors
kubectl logs -n ai-infrastructure -l component=memory-agent --tail=100

# Quick health check
./scripts/debug-ai-agents-k8s.sh memory-agent DEBUG_LEVEL=basic
```

### 2. Deep Analysis
```bash
# Start comprehensive analysis
python .agents/ai-agent-debugger/scripts/main.py '{
  "operation": "analyze",
  "targetAgent": "all",
  "debugLevel": "deep",
  "namespace": "ai-infrastructure",
  "correlationId": "deep-analysis-001"
}'

# LLM collaborative debugging
./scripts/llm-debug-automation.sh all ANALYSIS_DEPTH=deep
```

### 3. Prevention Implementation
```bash
# Generate prevention strategies
python .agents/ai-agent-debugger/scripts/main.py '{
  "operation": "prevent",
  "targetAgent": "all",
  "outputFormat": "comprehensive"
}'

# Apply automated fixes
python .agents/ai-agent-debugger/scripts/main.py '{
  "operation": "automate",
  "targetAgent": "memory-agent",
  "namespace": "ai-infrastructure"
}'
```

## Common Debugging Patterns

### Resource Issues
```bash
# Check resource usage
kubectl top pods -n ai-infrastructure -l component=memory-agent

# Describe pod for resource limits
kubectl describe pod -n ai-infrastructure -l component=memory-agent

# Check OOM kills
kubectl get events -n ai-infrastructure --field-selector reason=OOMKilling
```

### Network Issues
```bash
# Check service endpoints
kubectl get endpoints -n ai-infrastructure -l component=memory-agent

# Test connectivity
kubectl port-forward -n ai-infrastructure service/memory-agent 8080:8080
curl http://localhost:8080/health

# Check network policies
kubectl get networkpolicies -n ai-infrastructure
```

### State Issues
```bash
# Check PVC status
kubectl get pvc -n ai-infrastructure -l component=memory-agent

# Check configmaps
kubectl get configmaps -n ai-infrastructure -l component=memory-agent -o yaml

# Check secrets
kubectl get secrets -n ai-infrastructure -l component=memory-agent -o yaml
```

## LLM-to-LLM Debugging Sessions

### Starting Collaborative Session
```bash
# Create LLM debugging session
./scripts/llm-debug-automation.sh memory-agent \
  DEBUG_SESSION_ID=collab-debug-001 \
  ANALYSIS_DEPTH=deep \
  OUTPUT_DIR=./llm-sessions
```

### Session Artifacts
- `llm-debug-session-{id}.json`: Complete agent state for LLM analysis
- `{id}-behavior-analysis.md`: Behavioral pattern analysis
- `{id}-llm-prompts.md`: Specific debugging prompts for LLMs
- `{id}-final-report.md`: Comprehensive debugging report

### Using LLM Prompts
1. Copy prompts from the generated session file
2. Provide agent state data as context
3. Follow LLM recommendations for fixes
4. Validate fixes and update session
5. Share session with other LLMs for collaborative analysis

## Prevention Strategies

### Monitoring Enhancements
```yaml
# Example Prometheus rules for AI agents
groups:
- name: ai-agent-alerts
  rules:
  - alert: MemoryAgentHighRestartCount
    expr: kube_pod_container_status_restarts_total{component="memory-agent"} > 5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Memory agent restarting frequently"
      
  - alert: InferenceGatewayHighLatency
    expr: http_request_duration_seconds{service="ai-inference-gateway"} > 2
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Inference gateway high latency detected"
```

### Health Checks
```python
# Example health check implementation
def health_check():
    checks = {
        'memory_status': check_memory_health(),
        'model_availability': check_model_status(),
        'connectivity': check_connectivity(),
        'state_consistency': check_state_consistency()
    }
    
    overall_health = all(checks.values())
    return {
        'status': 'healthy' if overall_health else 'unhealthy',
        'checks': checks,
        'timestamp': datetime.utcnow().isoformat()
    }
```

### Automated Recovery
```bash
# Example automated recovery script
#!/bin/bash
AGENT_NAME=$1
NAMESPACE=${2:-ai-infrastructure}

# Restart failing pods
kubectl get pods -n $NAMESPACE -l component=$AGENT_NAME \
  --field-selector=status.phase!=Running \
  -o jsonpath='{.items[*].metadata.name}' | \
  xargs -I {} kubectl delete pod {} -n $NAMESPACE --wait=false

# Scale up if needed
kubectl scale deployment $AGENT_NAME --replicas=1 -n $NAMESPACE
```

## Troubleshooting Checklist

### Before Debugging
- [ ] Kubernetes cluster accessible
- [ ] kubectl configured correctly
- [ ] Required permissions available
- [ ] Agent namespace exists
- [ ] Debugging scripts executable

### During Debugging
- [ ] Collect comprehensive state
- [ ] Use correlation IDs for tracing
- [ ] Save session artifacts
- [ ] Document findings
- [ ] Validate fixes

### After Debugging
- [ ] Verify issue resolution
- [ ] Monitor for regression
- [ ] Update documentation
- [ ] Share learnings
- [ ] Implement prevention

## Integration with Existing Tools

### GitOps Integration
```bash
# Check Flux reconciliation
flux get kustomizations -n ai-infrastructure

# Check GitOps status
./scripts/debug-dependency-chain.sh ai-infrastructure kustomization
```

### Temporal Integration
```bash
# Check Temporal workflow status
tctl --namespace ai-infrastructure workflow list

# Check activity execution
tctl --namespace ai-infrastructure activity list
```

### Monitoring Integration
```bash
# Check Prometheus metrics
kubectl port-forward svc/prometheus 9090:9090 -n monitoring
curl http://localhost:9090/api/v1/query?query=up{job="ai-agents"}

# Check Grafana dashboards
kubectl port-forward svc/grafana 3000:3000 -n monitoring
```

## Best Practices

### Debugging Approach
1. **Start Broad**: Begin with basic health assessment
2. **Narrow Down**: Use detailed analysis to focus on issues
3. **Collaborate**: Leverage LLM-to-LLM debugging for complex issues
4. **Validate**: Always validate applied fixes
5. **Document**: Record findings and prevention strategies

### Session Management
1. **Unique IDs**: Use correlation IDs for all debugging
2. **Artifact Preservation**: Save all session data
3. **Reproducibility**: Ensure sessions can be recreated
4. **Knowledge Sharing**: Share sessions between LLMs
5. **Continuous Learning**: Update debugging strategies based on results

### Prevention Focus
1. **Proactive Monitoring**: Implement comprehensive monitoring
2. **Automated Recovery**: Create self-healing mechanisms
3. **Performance Baselines**: Establish normal behavior patterns
4. **Security Integration**: Include security in debugging
5. **Scalability Considerations**: Design for distributed debugging

## Emergency Procedures

### Critical Agent Failure
```bash
# Immediate recovery
kubectl scale deployment memory-agent --replicas=0 -n ai-infrastructure
kubectl scale deployment memory-agent --replicas=1 -n ai-infrastructure

# Check for data loss
kubectl get pvc -n ai-infrastructure -l component=memory-agent

# Restore from backup if needed
kubectl apply -f backups/memory-agent-backup.yaml
```

### Multi-Agent Coordination Failure
```bash
# Check consensus state
kubectl get agentconsensus -n control-plane

# Restart consensus agents
kubectl delete pods -n control-plane -l app=consensus-agent

# Verify network connectivity
kubectl run connectivity-test --image=nicolaka/netshoot --rm -it -- /bin/bash
```

This comprehensive debugging system ensures that AI agents running in distributed Kubernetes environments can be effectively debugged, monitored, and maintained with both automated and collaborative approaches.

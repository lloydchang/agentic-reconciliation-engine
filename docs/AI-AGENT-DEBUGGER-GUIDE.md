# AI Agent Debugger - Distributed System Debugging Guide

## Overview

The AI Agent Debugger skill provides comprehensive debugging capabilities for AI agents running in distributed Kubernetes environments with Temporal orchestration. This skill enables systematic debugging of complex AI systems across multiple components and environments.

## Architecture

The debugging system consists of multiple layers:

### 1. Skill-Based Debugging (`./core/ai/runtime/debug/`)
- **Purpose**: Centralized debugging skill following `agentskills.io` specification
- **Risk Level**: Low (read-only operations)
- **Autonomy**: Fully automated for safe debugging operations
- **Components**:
  - [SKILL.md](SKILL.md): Skill definition and metadata
  - `core/core/automation/ci-cd/scripts/debug.py`: Main Python debugging engine
  - `core/core/automation/ci-cd/scripts/kubernetes-debugger.py`: Kubernetes-specific debugging
  - `core/core/automation/ci-cd/scripts/distributed-debug-runner.sh`: End-to-end debugging runner
  - `documentation/`: Detailed usage guides
  - `references/`: Best practices and patterns

### 2. Built-in Monitoring (`ai-core/ai/runtime/backend/monitoring/metrics.go`)
- **Purpose**: Real-time metrics collection and alerting
- **Features**:
  - Workflow execution metrics
  - Agent performance tracking
  - System health monitoring
  - Alert generation and management
- **Integration**: Temporal activity and workflow integration

### 3. Deployment Automation (`core/core/automation/ci-cd/scripts/deploy-ai-agents-ecosystem.sh`)
- **Purpose**: Complete AI agent ecosystem deployment
- **Features**:
  - Multi-language agent deployment (Rust, Go, Python)
  - Temporal orchestration setup
  - Dashboard and monitoring
  - Ingress configuration
- **Components**: AI agents, inference gateway, skills framework, dashboard

## Quick Start

### Basic Debugging
```bash
# Check AI agent pods status
kubectl get pods -n ai-infrastructure -l component=memory-agent

# Use the debugging skill
python3 core/ai/skills/debug/core/core/automation/ci-cd/scripts/debug.py '{
  "targetComponent": "kubernetes",
  "agentType": "memory-agent",
  "debugLevel": "detailed"
}'

# Quick bash debugging
./core/ai/skills/debug/core/core/automation/ci-cd/scripts/distributed-debug-runner.sh \
  --namespace ai-infrastructure \
  --agent-type memory-agent \
  --debug-level detailed
```

### Monitoring Integration
```bash
# Check metrics
kubectl port-forward -n ai-infrastructure svc/temporal-worker 8080:8080
curl http://localhost:8080/monitoring/metrics

# View alerts
curl http://localhost:8080/monitoring/alerts
```

### Deployment
```bash
# Deploy complete ecosystem
./core/core/automation/ci-cd/scripts/deploy-ai-agents-ecosystem.sh

# Access dashboard
kubectl port-forward -n ai-infrastructure svc/agent-dashboard-service 8080:80
# Visit: http://localhost:8080
```

## Debugging Components

### AI Agent Types
- **Memory Agents**: Persistent storage with Llama.cpp backend
- **Inference Agents**: Multi-language (Rust/Go/Python) with skill integration
- **Orchestration Agents**: Temporal workflow coordination
- **Monitoring Agents**: Real-time system health and metrics

### Debugging Targets
- **Kubernetes Infrastructure**: Pods, services, ingress, storage
- **Temporal Workflows**: Execution status, activity failures, timeouts
- **AI Inference**: Model loading, performance bottlenecks, errors
- **Distributed Systems**: Network connectivity, cross-service dependencies

### Debug Levels
- **Basic**: Status checks and error detection
- **Detailed**: Performance metrics and log analysis
- **Deep**: Full system analysis with correlation tracking

## Common Issues and Solutions

### Agent Failures
```bash
# Check pod status
kubectl get pods -n ai-infrastructure -l component=memory-agent

# View logs
kubectl logs -n ai-infrastructure -l component=memory-agent --tail=100

# Debug with skill
python3 core/ai/skills/debug/core/core/automation/ci-cd/scripts/debug.py '{
  "targetComponent": "kubernetes",
  "issueType": "pod_failure",
  "agentType": "memory-agent",
  "autoFix": false
}'
```

### Workflow Timeouts
```bash
# Check Temporal workflows
tctl wf list --ns ai-infrastructure

# Debug specific workflow
tctl wf show -w <workflow-id> --ns ai-infrastructure

# Use debugging skill
python3 core/ai/skills/debug/core/core/automation/ci-cd/scripts/debug.py '{
  "targetComponent": "temporal",
  "issueType": "workflow_timeout",
  "workflowId": "<workflow-id>"
}'
```

### Performance Issues
```bash
# Check resource usage
kubectl top pods -n ai-infrastructure

# View metrics
curl http://temporal-worker.ai-infrastructure.svc.cluster.local:8080/monitoring/metrics

# Performance debugging
python3 core/ai/skills/debug/core/core/automation/ci-cd/scripts/debug.py '{
  "targetComponent": "performance",
  "debugLevel": "deep",
  "timeRange": "1h"
}'
```

## Monitoring and Metrics

### Built-in Metrics
- **Workflow Metrics**: Execution count, duration, success rate
- **Agent Metrics**: Performance scores, error rates, execution times
- **System Metrics**: Memory usage, goroutine counts, uptime
- **Alert Metrics**: Active alerts, acknowledgment status

### Alert Types
- **Workflow Timeouts**: Long-running workflows exceeding thresholds
- **Agent Failures**: High error rates in agent execution
- **Resource Exhaustion**: Memory/CPU limits exceeded
- **System Errors**: General system health issues

### Custom Monitoring
```go
// Record custom metrics
collector := GetGlobalMetricsCollector()
collector.RecordWorkflowExecution(workflowExecution)
collector.RecordAgentExecution(agentName, success, score, duration)
```

## Deployment Architecture

### Components Deployed
1. **AI Memory Agents**: Persistent storage with Llama.cpp
2. **Inference Gateway**: API endpoint for skill integration
3. **Temporal Server**: Workflow orchestration
4. **Skills Framework**: 64 operational skills as workflows
5. **Dashboard**: Real-time monitoring interface
6. **Ingress**: External access configuration

### Network Architecture
```
Internet → Ingress (nginx) → Services → Pods
                              ↓
                       Temporal Server
                              ↓
                    AI Inference Gateway
                              ↓
                 Memory Agents (Rust/Go/Python)
```

### Storage Architecture
- **Persistent Volumes**: Agent data persistence
- **ConfigMaps**: Configuration management
- **Secrets**: Sensitive data handling
- **PVCs**: Dynamic storage provisioning

## Best Practices

### Debugging Workflow
1. **Initial Assessment**: Use basic debug level to identify issues
2. **Component Isolation**: Target specific components (Kubernetes, Temporal, etc.)
3. **Correlation Tracking**: Use correlation IDs for request tracing
4. **Metrics Analysis**: Review monitoring data for patterns
5. **Root Cause Analysis**: Use LLM prompts for deep analysis
6. **Fix Validation**: Verify fixes with automated testing
7. **Prevention**: Implement monitoring for similar issues

### Performance Optimization
- **Resource Limits**: Set appropriate CPU/memory limits
- **Health Checks**: Implement readiness and liveness probes
- **Auto-scaling**: Configure horizontal pod autoscaling
- **Caching**: Use Redis for frequently accessed data
- **Async Processing**: Move heavy operations to background

### Security Considerations
- **RBAC**: Implement role-based access control
- **Network Policies**: Restrict pod-to-pod communication
- **Secret Management**: Use sealed secrets for sensitive data
- **Audit Logging**: Enable comprehensive audit trails
- **Vulnerability Scanning**: Regular security assessments

## Integration Points

### Temporal Workflows
- Activity execution monitoring
- Workflow state tracking
- Error handling and retries
- Performance profiling

### Kubernetes API
- Pod lifecycle management
- Service discovery
- Resource quota monitoring
- Event correlation

### External Systems
- Prometheus metrics export
- Grafana dashboard integration
- AlertManager notifications
- Log aggregation systems

## Troubleshooting Guide

### Common Issues

#### Pods Not Starting
```bash
# Check events
kubectl get events -n ai-infrastructure --sort-by=.lastTimestamp

# Describe pod
kubectl describe pod <pod-name> -n ai-infrastructure

# Check logs
kubectl logs <pod-name> -n ai-infrastructure --previous
```

#### High Memory Usage
```bash
# Check resource usage
kubectl top pods -n ai-infrastructure

# View limits
kubectl get pod <pod-name> -n ai-infrastructure -o yaml | grep -A5 resources

# Debug with skill
python3 core/ai/skills/debug/core/core/automation/ci-cd/scripts/debug.py '{
  "targetComponent": "performance",
  "issueType": "memory_usage"
}'
```

#### Network Connectivity
```bash
# Test service connectivity
kubectl exec -n ai-infrastructure <pod-name> -- curl <service-url>

# Check network policies
kubectl get networkpolicies -n ai-infrastructure

# DNS resolution
kubectl exec -n ai-infrastructure <pod-name> -- nslookup <service-name>
```

### Advanced Debugging

#### LLM-Assisted Analysis
```bash
# Generate debugging prompts
python3 core/ai/skills/debug/core/core/automation/ci-cd/scripts/debug.py '{
  "targetComponent": "llm_analysis",
  "analysisType": "root_cause",
  "data": "<collected-data>"
}'
```

#### Correlation Tracking
```bash
# Set correlation ID
export CORRELATION_ID=debug-$(date +%s)

# Run with tracking
./core/ai/skills/debug/core/core/automation/ci-cd/scripts/distributed-debug-runner.sh \
  --correlation-id $CORRELATION_ID \
  --debug-level deep
```

#### Automated Fixes
```bash
# Enable auto-fix (use with caution)
python3 core/ai/skills/debug/core/core/automation/ci-cd/scripts/debug.py '{
  "autoFix": true,
  "maxRiskLevel": "medium"
}'
```

## API Reference

### Debugging Skill API
```python
from agents.ai_agent_debugger import AIAgentDebugger

debugger = AIAgentDebugger()
result = debugger.debug_system({
    "target_component": "kubernetes",
    "agent_type": "memory-agent",
    "debug_level": "detailed",
    "auto_fix": False
})
```

### Monitoring API
```go
// Get metrics collector
collector := monitoring.GetGlobalMetricsCollector()

// Record execution
collector.RecordWorkflowExecution(workflowExec)
collector.RecordAgentExecution(agentName, success, score, duration)

// Get metrics
metrics := collector.GetMetrics()
alerts := collector.GetAlerts()
```

### Deployment API
```bash
# Deploy ecosystem
./core/core/automation/ci-cd/scripts/deploy-ai-agents-ecosystem.sh

# Custom deployment
NAMESPACE=custom NAMESPACE ./core/core/automation/ci-cd/scripts/deploy-ai-agents-ecosystem.sh
```

## Future Enhancements

### Planned Features
- **Chaos Engineering**: Automated failure injection testing
- **AI-Powered Debugging**: ML-based root cause analysis
- **Multi-Cluster Support**: Cross-cluster debugging capabilities
- **Real-time Streaming**: Live debugging with WebSocket connections
- **Custom Dashboards**: Tailored monitoring interfaces

### Integration Opportunities
- **External Monitoring**: Integration with Datadog, New Relic
- **Log Aggregation**: ELK stack, Splunk integration
- **CI/CD Integration**: Automated testing in deployment pipelines
- **Alert Routing**: PagerDuty, Slack integration

## Support and Resources

### Documentation
- [core/ai/skills/debug/documentation/debugging-workflows.md](core/ai/skills/debug/documentation/debugging-workflows.md)
- [core/ai/skills/debug/documentation/regression-prevention.md](core/ai/skills/debug/documentation/regression-prevention.md)
- [docs/AI-AGENTS-ARCHITECTURE.md](docs/AI-AGENTS-ARCHITECTURE.md)
- [docs/MONITORING_SETUP.md](docs/MONITORING_SETUP.md)

### Scripts and Tools
- `core/ai/skills/debug/core/core/automation/ci-cd/scripts/`: Debugging utilities
- `core/core/automation/ci-cd/scripts/deploy-ai-agents-ecosystem.sh`: Deployment automation
- `core/core/automation/ci-cd/scripts/debug-ai-agents-k8s.sh`: Kubernetes debugging

### References
- `core/ai/skills/debug/references/`: Best practices
- [AGENTS.md](AGENTS.md): Agent architecture overview
- [AGENT-SKILLS-NEXT-LEVEL.md](AGENT-SKILLS-NEXT-LEVEL.md): Advanced skills guide

---

This debugging system provides comprehensive capabilities for maintaining reliable AI agent operations in distributed environments, with built-in monitoring, automated analysis, and prevention strategies.

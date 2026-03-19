# AI System Debugging Knowledge Base

## Overview

This document captures comprehensive knowledge about debugging AI agents in distributed Kubernetes environments. It serves as a persistent memory and reference for debugging complex AI systems running with Temporal orchestration.

## Core Knowledge Areas

### 1. AI Agent Architecture Understanding
**Key Components:**
- **Memory Agents**: Persistent storage with Llama.cpp backend (Rust/Go/Python)
- **Inference Gateway**: Unified API for skill integration
- **Temporal Workflows**: Orchestration layer for complex operations
- **Skills Framework**: 64 operational skills as workflow activities

**Debugging Mindset:**
- AI agents are distributed systems, not monolithic applications
- Issues can span Kubernetes, Temporal, and AI inference layers
- Debugging requires correlation across multiple components
- LLM-to-LLM debugging enables collaborative analysis

### 2. Debugging Methodologies

#### Systematic Debugging Process
1. **Initial Assessment**: Quick status checks (pods, services, workflows)
2. **Component Isolation**: Target specific layers (Kubernetes/Temporal/Inference)
3. **Data Collection**: Gather logs, metrics, events, correlations
4. **Pattern Analysis**: Identify error patterns, resource bottlenecks
5. **Root Cause Analysis**: Use LLM prompts for deep analysis
6. **Fix Validation**: Test fixes with automated verification
7. **Prevention**: Implement monitoring for similar issues

#### Evidence-Based Debugging
- **Correlation IDs**: Track requests across components
- **Structured Logging**: JSON logs with consistent fields
- **Metrics Collection**: Real-time performance data
- **Event Correlation**: Link Kubernetes events with workflow states
- **LLM-Assisted Analysis**: Use AI for pattern recognition

### 3. Critical Debugging Commands

#### Kubernetes Layer
```bash
# Pod status and health
kubectl get pods -n ai-infrastructure -l component=memory-agent
kubectl describe pod <pod-name> -n ai-infrastructure

# Resource monitoring
kubectl top pods -n ai-infrastructure
kubectl get events -n ai-infrastructure --sort-by=.lastTimestamp

# Log analysis
kubectl logs -n ai-infrastructure -l component=memory-agent --tail=100
kubectl logs -n ai-infrastructure -l component=memory-agent -f --previous
```

#### Temporal Layer
```bash
# Workflow management
tctl wf list --ns ai-infrastructure
tctl wf show -w <workflow-id> --ns ai-infrastructure
tctl wf describe -w <workflow-id> --ns ai-infrastructure

# Activity debugging
tctl activity list --ns ai-infrastructure
tctl activity describe -a <activity-id> --ns ai-infrastructure

# Cluster health
tctl admin cluster describe
tctl admin shard describe
```

#### AI Inference Layer
```bash
# Model status
kubectl port-forward -n ai-infrastructure svc/ollama-service 11434:11434
curl http://localhost:11434/api/tags

# Inference testing
curl -X POST http://localhost:5000/api/infer \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test inference", "model": "qwen2.5:0.5b"}'

# Performance metrics
kubectl exec -n ai-infrastructure deployment/memory-agent-rust -- ps aux
kubectl exec -n ai-infrastructure deployment/memory-agent-rust -- free -h
```

### 4. Common Issue Patterns

#### Agent Startup Failures
**Symptoms:**
- Pods in CrashLoopBackOff or Pending state
- Init container failures
- Resource constraint errors

**Debug Steps:**
```bash
# Check pod events
kubectl describe pod <pod-name> -n ai-infrastructure

# Verify PVC status
kubectl get pvc -n ai-infrastructure

# Check resource limits
kubectl get pod <pod-name> -n ai-infrastructure -o yaml | grep -A5 resources
```

**Common Causes:**
- Insufficient resources (CPU/memory)
- PVC creation failures
- Image pull issues
- Configuration errors

#### Workflow Timeouts
**Symptoms:**
- Workflows stuck in Running state
- Activity timeouts
- Resource exhaustion

**Debug Steps:**
```bash
# Check workflow status
tctl wf show -w <workflow-id> --ns ai-infrastructure

# View activity history
tctl activity list --wf-id <workflow-id> --ns ai-infrastructure

# Check Temporal server logs
kubectl logs -n ai-infrastructure -l app=temporal
```

**Common Causes:**
- Long-running activities without heartbeats
- Resource constraints on workers
- Network connectivity issues
- Deadlocks in workflow logic

#### Inference Performance Issues
**Symptoms:**
- Slow response times
- High memory usage
- Model loading failures

**Debug Steps:**
```bash
# Check model loading
kubectl exec -n ai-infrastructure deployment/memory-agent-rust -- ls -la /models/

# Monitor inference performance
kubectl top pods -n ai-infrastructure -l component=memory-agent

# Check inference logs
kubectl logs -n ai-infrastructure -l component=memory-agent | grep -i infer
```

**Common Causes:**
- Model size vs available memory
- GPU/CPU resource contention
- Network latency to model storage
- Concurrent inference overload

### 5. LLM-Assisted Debugging Techniques

#### Prompt Engineering for Debugging
```python
# Root cause analysis prompt
debug_prompt = {
    "system_context": "You are debugging an AI agent in Kubernetes with Temporal orchestration",
    "data_provided": collected_debug_data,
    "analysis_request": "Identify root cause and recommend fixes",
    "constraints": "Consider distributed system complexity"
}

# Pattern recognition prompt
pattern_prompt = {
    "task": "Analyze error logs for recurring patterns",
    "data": log_samples,
    "output_format": "JSON with severity, frequency, impact"
}
```

#### Collaborative LLM Debugging
- **LLM A**: Collects and structures debug data
- **LLM B**: Performs pattern analysis and root cause identification
- **LLM C**: Generates specific fix recommendations
- **Human**: Validates and implements fixes

#### Automated Prompt Generation
```python
def generate_debug_prompts(issue_type, debug_data):
    prompts = {
        "kubernetes": f"Analyze Kubernetes pod failures: {debug_data['pod_status']}",
        "temporal": f"Debug workflow timeouts: {debug_data['workflow_history']}",
        "inference": f"Optimize AI inference performance: {debug_data['metrics']}"
    }
    return prompts[issue_type]
```

### 6. Monitoring and Alerting

#### Key Metrics to Monitor
- **Pod Health**: Restart counts, readiness status
- **Resource Usage**: CPU/memory per pod
- **Workflow Performance**: Execution time, success rate
- **Inference Metrics**: Response time, throughput
- **Error Rates**: Per component error tracking

#### Alert Thresholds
```yaml
alerts:
  - name: high_restart_rate
    condition: pod_restart_count > 5
    severity: critical
    action: "Restart deployment"

  - name: workflow_timeout
    condition: workflow_duration > 7200
    severity: warning
    action: "Investigate workflow logic"

  - name: memory_pressure
    condition: pod_memory_usage > 80%
    severity: warning
    action: "Scale resources"
```

#### Real-time Monitoring Setup
```bash
# Prometheus metrics
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Grafana dashboards
kubectl port-forward -n monitoring svc/grafana 3000:3000

# Custom metrics endpoint
curl http://temporal-worker.ai-infrastructure.svc.cluster.local:8080/metrics
```

### 7. Distributed System Debugging Challenges

#### Network Debugging
```bash
# Service discovery
kubectl get endpoints -n ai-infrastructure

# DNS resolution
kubectl exec -n ai-infrastructure <pod> -- nslookup temporal-frontend

# Network policies
kubectl get networkpolicies -n ai-infrastructure

# Connectivity testing
kubectl exec -n ai-infrastructure <pod> -- curl temporal-frontend:7233
```

#### State Synchronization
- **Temporal State**: Workflow history and activity states
- **Agent State**: Memory persistence and inference context
- **Kubernetes State**: Pod lifecycle and resource allocation
- **Cross-Component Correlation**: Linking events across layers

#### Concurrency Issues
- **Race Conditions**: Multiple workflows accessing shared resources
- **Deadlocks**: Workflow dependencies creating circular waits
- **Resource Contention**: CPU/memory competition between agents

### 8. Prevention and Best Practices

#### Automated Testing
```bash
# Unit tests for agents
go test ./ai-core/ai/runtime/backend/...

# Integration tests
./core/scripts/automation/run-integration-tests.sh

# Chaos engineering
./core/scripts/automation/chaos-testing.sh --duration=30m
```

#### Configuration Management
- **GitOps**: All configuration changes via Git
- **Validation**: Schema validation for configurations
- **Versioning**: Track configuration changes with deployments
- **Rollback**: Automated rollback procedures

#### Capacity Planning
```yaml
resource_planning:
  baseline_load: "10 workflows/minute"
  peak_load: "100 workflows/minute"
  buffer_capacity: "50% overhead"
  scaling_triggers:
    - cpu_usage > 70%
    - memory_usage > 80%
    - queue_depth > 100
```

#### Documentation and Runbooks
- **Incident Response**: Standardized procedures for common issues
- **Debugging Playbooks**: Step-by-step guides for complex scenarios
- **Knowledge Base**: Centralized documentation for issues and solutions
- **Post-Mortem**: Analysis and prevention for major incidents

### 9. Tool Ecosystem

#### Primary Debugging Tools
- **kubectl**: Kubernetes API interactions
- **tctl**: Temporal CLI for workflow management
- **AI Agent Debugger Skill**: Comprehensive debugging automation
- **Monitoring Stack**: Prometheus, Grafana, AlertManager

#### Specialized Scripts
```bash
# Quick debug runner
./core/ai/skills/debug/scripts/distributed-debug-runner.sh \
  --namespace ai-infrastructure \
  --debug-level detailed

# LLM-assisted debugging
./core/scripts/automation/llm-debug-automation.sh memory-agent

# System validation
./core/scripts/automation/validate-deployment.sh --comprehensive
```

#### Integration Points
- **CI/CD**: Automated testing in deployment pipelines
- **Alert Routing**: Integration with PagerDuty, Slack
- **Log Aggregation**: ELK stack, Splunk integration
- **Metrics Export**: Prometheus federation

### 10. Future Evolution

#### Advanced Debugging Capabilities
- **AI-Powered Root Cause Analysis**: ML models trained on historical incidents
- **Predictive Debugging**: Anomaly detection before issues occur
- **Automated Fix Generation**: AI-generated remediation scripts
- **Self-Healing Systems**: Autonomous issue resolution

#### Scaling Considerations
- **Multi-Cluster Debugging**: Cross-cluster issue correlation
- **Federated Monitoring**: Unified view across environments
- **Performance Profiling**: Detailed execution tracing
- **Chaos Engineering**: Systematic failure injection testing

This knowledge base serves as a comprehensive reference for debugging complex AI agent systems in distributed environments, combining traditional debugging techniques with AI-assisted analysis and modern DevOps practices.

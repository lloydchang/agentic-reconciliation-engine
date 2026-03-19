# Agent Sandbox Integration Guide

This document provides a comprehensive guide for integrating Google's Agent Sandbox into the agentic-reconciliation-engine.

## Overview

Agent Sandbox provides secure, isolated runtime environments for AI agents executing untrusted or specialized code. This integration adds Agent Sandbox as a fifth execution method alongside the existing four methods, enabling strong kernel-level isolation through gVisor while maintaining compatibility with the existing agent architecture.

## Architecture Integration

### New Execution Layer

```
┌──────────────────────────────────────────────────────────────┐
│                  User / Operator Request                     │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│              Agent Execution Methods                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   Temporal  │ │   Container │ │     Pi-Mono RPC         │ │
│  │   Workflows │ │   Agents    │ │     Container           │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Agent Sandbox                              │ │
│  │         (Secure Isolation Layer)                        │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────┬───────────────────┬───────────────────────────────┘
            │                   │
            ▼                   ▼
┌───────────────────────┐  ┌───────────────────────────────────┐
│  Memory Agent Layer   │  │       GitOps Control Layer        │
│                       │  │                                   │
│  Rust / Go / Python   │  │  Executes structured JSON plans   │
│  Local inference      │  │  via Flux or ArgoCD. Never runs   │
│  (llama.cpp / Ollama) │  │  LLM output directly on cluster.  │
│  SQLite persistence   │  │                                   │
└───────────────────────┘  └───────────────────────────────────┘
            │                          │
            └──────────────┬───────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│           Monitoring & Observability Layer                   │
│     Prometheus · Grafana · ELK · Alertmanager · Dashboard    │
└──────────────────────────────────────────────────────────────┘
```

### Integration Points

1. **Sandbox Provider**: Implements the existing SandboxProvider interface
2. **Execution Layer**: New Agent Sandbox execution engine
3. **Skill Integration**: Extended metadata for sandbox execution
4. **Agent Methods**: Integration with Temporal, Pi-Mono, and Memory agents
5. **Template Management**: Dynamic sandbox template creation
6. **Monitoring**: Comprehensive metrics and observability

## Installation and Setup

### Prerequisites

- Kubernetes cluster with gVisor support
- Agent Sandbox controller installed
- Appropriate RBAC permissions
- Network policies configured

### Install Agent Sandbox Controller

```bash
export AGENT_SANDBOX_VERSION="v0.1.0"

kubectl apply \
-f https://github.com/kubernetes-sigs/agent-sandbox/releases/download/${AGENT_SANDBOX_VERSION}/manifest.yaml \
-f https://github.com/kubernetes-sigs/agent-sandbox/releases/download/${AGENT_SANDBOX_VERSION}/extensions.yaml
```

### Configure gVisor Runtime Class

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: gvisor
```

### Enable Agent Sandbox in Configuration

```yaml
# config/agent-sandbox.yaml
agent_sandbox:
  enabled: true
  default_namespace: "agent-sandbox"
  default_template: "python-runtime-template"
  timeout: "10m"
  enable_snapshots: false
  resource_defaults:
    cpu: "250m"
    memory: "512Mi"
    disk: "1Gi"
  network_policy:
    default_deny_egress: true
    allowed_domains: ["api.example.com"]
    allowed_ports: [443, 80]
```

## Usage Guide

### Skill Configuration

Skills can specify Agent Sandbox execution through extended metadata:

```yaml
---
name: infrastructure-validator
description: Validates infrastructure changes safely
license: AGPLv3
metadata:
  execution_mode: agent_sandbox
  sandbox_config:
    template: python-runtime-template
    isolation_level: high
    network_access: false
    resource_limits:
      cpu: "500m"
      memory: "1Gi"
    timeout: "5m"
    security_policies:
      - name: "network-deny"
        type: "network"
        rule: "all"
        action: "deny"
      - name: "output-scan"
        type: "output"
        rule: "secrets"
        action: "scan"
  risk_level: medium
  autonomy: conditional
  layer: temporal
```

### Template Definitions

Create sandbox templates for different execution environments:

```yaml
apiVersion: extensions.agents.x-k8s.io/v1alpha1
kind: SandboxTemplate
metadata:
  name: python-runtime-template
  namespace: agent-sandbox
spec:
  podTemplate:
    spec:
      runtimeClassName: gvisor
      containers:
      - name: python-runtime
        image: python:3.10-slim
        command: ["python3"]
        args: ["-c", "while True: pass"]
        resources:
          requests:
            cpu: "250m"
            memory: "512Mi"
            ephemeral-storage: "512Mi"
        env:
        - name: PYTHONUNBUFFERED
          value: "1"
        securityContext:
          runAsUser: 1000
          runAsGroup: 1000
          readOnlyRootFilesystem: false
```

### Warm Pool Configuration

```yaml
apiVersion: extensions.agents.x-k8s.io/v1alpha1
kind: SandboxWarmPool
metadata:
  name: python-runtime-warmpool
  namespace: agent-sandbox
spec:
  replicas: 2
  minReady: 1
  sandboxTemplateRef:
    name: python-runtime-template
```

## Agent Method Integration

### Temporal Workflows

```go
// Execute code in Agent Sandbox from Temporal workflow
func (w *InfrastructureWorkflow) ValidateWithSandbox(ctx context.Context, code string) error {
    result, err := w.agentSandboxIntegrator.ExecuteInTemporal(
        ctx, w.workflowID, "validate-infrastructure", code)
    if err != nil {
        return err
    }
    
    if !result.Success {
        return fmt.Errorf("validation failed: %s", result.Stderr)
    }
    
    return nil
}
```

### Pi-Mono Agents

```go
// Execute skill in Agent Sandbox from Pi-Mono
func (p *PiMonoAgent) ExecuteSkillSafely(ctx context.Context, skillName, code string) (*ExecutionResult, error) {
    return p.agentSandboxIntegrator.ExecuteInPiMono(
        ctx, p.sessionID, skillName, code)
}
```

### Memory Agents

```go
// Execute code in Agent Sandbox from Memory agent
func (m *MemoryAgent) ProcessQuery(ctx context.Context, query, code string) (*ExecutionResult, error) {
    return m.agentSandboxIntegrator.ExecuteInMemory(
        ctx, m.memoryID, query, code)
}
```

## Template Selection

### Intelligent Selection

The template selector automatically chooses the best template based on:

- **Skill Patterns**: Matching skill names and types
- **Language Requirements**: Python, Bash, Go, JavaScript
- **Isolation Levels**: Low, medium, high security
- **Resource Needs**: CPU, memory, GPU requirements
- **Performance Data**: Historical success rates and timing

### Selection Rules

```go
rule := &SelectionRule{
    Name:     "High Security Skills",
    Priority: 200,
    Conditions: []SelectionCondition{
        {Field: "isolation_level", Operator: "equals", Value: "high"},
        {Field: "skill_type", Operator: "contains", Value: "security"},
    },
    Action: SelectionAction{
        Type: "set_template",
        Parameters: map[string]interface{}{
            "template": "secure-python-template",
        },
    },
    Enabled: true,
}
```

### Performance Tracking

Track template performance to optimize selection:

```go
// Update performance data after execution
templateSelector.UpdatePerformanceData(
    templateName, 
    result.Duration, 
    result.Success,
    ResourceUsage{
        AverageCPU: result.CPUUsage,
        AverageMemory: result.MemoryUsage,
    },
)
```

## Security Configuration

### Isolation Levels

#### Low Isolation
- Basic gVisor isolation
- Suitable for trusted internal code
- Standard resource limits

#### Medium Isolation
- Enhanced gVisor policies
- Network restrictions
- Default for most skills

#### High Isolation
- Maximum security policies
- No network access
- Strict resource limits
- Output scanning

### Network Policies

```yaml
# Default deny network policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: agent-sandbox-deny-all
  namespace: agent-sandbox
spec:
  podSelector:
    matchLabels:
      app: agent-sandbox-workload
  policyTypes:
  - Egress
  - Ingress
```

### Security Scanning

```go
// Post-execution security check
func (si *SkillIntegration) postExecutionSecurityCheck(ctx context.Context, result *ExecutionResult, policies []SecurityPolicy) error {
    for _, policy := range policies {
        if policy.Type == "output" && policy.Action == "scan" {
            if err := si.scanOutputForViolations(result.Stdout, policy); err != nil {
                return fmt.Errorf("security violation detected: %w", err)
            }
        }
    }
    return nil
}
```

## Monitoring and Observability

### Prometheus Metrics

```yaml
# Service monitor for Agent Sandbox metrics
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: agent-sandbox-metrics
  namespace: agent-sandbox
spec:
  selector:
    matchLabels:
      app: agent-sandbox-executor
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

### Key Metrics

- **Execution Metrics**: Success rates, duration, error counts
- **Resource Metrics**: CPU, memory, disk usage per sandbox
- **Template Metrics**: Performance by template type
- **Security Metrics**: Policy violations, blocked operations
- **Warm Pool Metrics**: Pool utilization, readiness status

### Grafana Dashboards

Create dashboards for:

1. **Execution Overview**: Total executions, success rates, average duration
2. **Resource Utilization**: CPU and memory usage trends
3. **Template Performance**: Success rates by template
4. **Security Events**: Policy violations and alerts
5. **Warm Pool Status**: Pool utilization and health

## Performance Optimization

### Warm Pool Management

```go
// Monitor and optimize warm pools
func (wm *WarmPoolManager) OptimizePool(ctx context.Context) error {
    status, err := wm.GetStatus(ctx)
    if err != nil {
        return err
    }
    
    // Scale up if utilization is high
    if status.Ready < status.Desired*0.8 {
        return wm.Scale(ctx, status.Desired+2)
    }
    
    // Scale down if utilization is low
    if status.Ready > status.Desired*1.2 {
        return wm.Scale(ctx, status.Desired-1)
    }
    
    return nil
}
```

### Pod Snapshots

Enable fast startup with state persistence:

```yaml
# Pod snapshot configuration
apiVersion: podsnapshot.gke.io/v1alpha1
kind: PodSnapshotPolicy
metadata:
  name: agent-sandbox-snapshots
  namespace: agent-sandbox
spec:
  storageConfigName: agent-sandbox-storage
  selector:
    matchLabels:
      app: agent-sandbox-workload
  triggerConfig:
    type: manual
    postCheckpoint: resume
```

## Troubleshooting

### Common Issues

#### Sandbox Creation Fails
```bash
# Check controller status
kubectl get pods -n agent-sandbox-system

# Check CRDs
kubectl get crd | grep agent

# Check events
kubectl get events -n agent-sandbox --sort-by='.lastTimestamp'
```

#### Template Not Found
```bash
# List available templates
kubectl get sandboxtemplates -n agent-sandbox

# Validate template
kubectl describe sandboxtemplate <template-name> -n agent-sandbox
```

#### Warm Pool Issues
```bash
# Check warm pool status
kubectl get sandboxwarmpools -n agent-sandbox

# Check pool events
kubectl describe sandboxwarmpool <pool-name> -n agent-sandbox
```

### Debug Commands

```bash
# Sandbox logs
kubectl logs -n agent-sandbox -l app=agent-sandbox-workload

# Controller logs
kubectl logs -n agent-sandbox-system -l app=agent-sandbox-controller

# Resource usage
kubectl top pods -n agent-sandbox

# Network policies
kubectl get networkpolicies -n agent-sandbox
```

## Migration Guide

### From Existing Sandbox Providers

1. **Update Configuration**: Replace provider-specific config with Agent Sandbox config
2. **Migrate Templates**: Convert existing templates to SandboxTemplate format
3. **Update Skills**: Change execution_mode to "agent_sandbox"
4. **Test Integration**: Verify all agent methods work correctly
5. **Monitor Performance**: Compare with previous implementation

### Gradual Rollout

1. **Phase 1**: Enable Agent Sandbox alongside existing providers
2. **Phase 2**: Migrate non-critical skills to Agent Sandbox
3. **Phase 3**: Migrate security-sensitive skills
4. **Phase 4**: Decommission old providers

## Best Practices

### Security

1. **Principle of Least Privilege**: Minimal permissions per sandbox
2. **Network Isolation**: Default deny policies
3. **Resource Limits**: Strict CPU and memory constraints
4. **Regular Audits**: Monitor for security violations
5. **Output Scanning**: Check for sensitive data leakage

### Performance

1. **Warm Pools**: Pre-warm for frequently used templates
2. **Resource Optimization**: Right-size resources per workload
3. **Template Selection**: Use performance data for optimal choices
4. **Monitoring**: Track utilization and scale appropriately
5. **Cleanup**: Regular cleanup of unused resources

### Operations

1. **Version Control**: Track template and configuration changes
2. **Testing**: Validate templates before deployment
3. **Documentation**: Keep template documentation current
4. **Backup**: Backup important sandbox state
5. **Disaster Recovery**: Plan for sandbox controller failures

## Future Enhancements

### Planned Features

- **GPU Support**: CUDA-enabled templates for ML workloads
- **Multi-Cloud**: Support for multiple Kubernetes clusters
- **Advanced Security**: Behavioral analysis and anomaly detection
- **Auto-scaling**: Dynamic warm pool sizing
- **Custom Runtimes**: Support for Kata Containers and others

### Community Contributions

Contributions are welcome for:

- New template types
- Performance optimizations
- Security enhancements
- Monitoring improvements
- Documentation and examples

## Conclusion

Agent Sandbox integration provides a secure, scalable foundation for AI agent execution in the agentic-reconciliation-engine. By leveraging gVisor isolation and Kubernetes-native orchestration, it enables safe execution of untrusted code while maintaining compatibility with existing agent architectures.

The integration offers significant benefits in security, performance, and operational efficiency, making it ideal for organizations looking to enhance their AI agent capabilities with strong isolation guarantees.

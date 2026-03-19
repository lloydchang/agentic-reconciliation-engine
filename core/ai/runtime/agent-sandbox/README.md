# Agent Sandbox Integration

This module provides a comprehensive Agent Sandbox integration for the agentic-reconciliation-engine, enabling secure, isolated execution environments for AI agents.

## Overview

Agent Sandbox is a Kubernetes extension designed to provide secure, isolated runtime environments for AI agents that execute untrusted or specialized code. This integration adds Agent Sandbox as a new execution method alongside the existing four methods in the agentic-reconciliation-engine.

## Architecture

```
core/ai/runtime/agent-sandbox/
├── executor.go           # Main execution engine
├── integration.go        # Integration with existing agent methods
├── templates.go          # Sandbox template management
├── warm_pools.go         # Warm pool management
├── monitoring.go         # Metrics and monitoring
├── skill_integration.go  # Skill-specific execution
├── template_selector.go  # Intelligent template selection
└── README.md            # This file
```

## Key Features

### Security Isolation
- **gVisor Integration**: Kernel-level isolation using gVisor runtime
- **Network Policies**: Configurable network access controls
- **Resource Limits**: CPU, memory, and disk constraints
- **Security Context**: Non-root execution, read-only filesystems

### Performance Optimization
- **Warm Pools**: Pre-warmed sandboxes for sub-second startup
- **Pod Snapshots**: State persistence and fast recovery
- **Resource Sharing**: Efficient resource utilization
- **Horizontal Scaling**: Support for concurrent executions

### Integration Points
- **All Agent Methods**: Temporal, Pi-Mono, Memory agents
- **Skill System**: Extended metadata for sandbox execution
- **Dynamic Resource Creation**: GitOps-driven sandbox management
- **Monitoring**: Prometheus metrics and observability

## Configuration

### Basic Configuration

```yaml
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
    allowed_domains: []
    allowed_ports: []
```

### Template Configuration

```yaml
templates:
  - name: "python-runtime-template"
    description: "Python runtime for AI agents"
    image: "python:3.10-slim"
    command: ["python3"]
    args: ["-c", "while True: pass"]
    resources:
      cpu: "250m"
      memory: "512Mi"
    environment:
      PYTHONUNBUFFERED: "1"
    runtime_class: "gvisor"
    security:
      run_as_user: 1000
      run_as_group: 1000
      read_only_root_fs: false
```

### Warm Pool Configuration

```yaml
warm_pools:
  - name: "python-runtime-warmpool"
    template_name: "python-runtime-template"
    replicas: 2
    min_ready: 1
    idle_timeout: "30m"
```

## Usage

### Skill Execution with Agent Sandbox

Skills can specify Agent Sandbox execution through extended metadata:

```yaml
---
name: infrastructure-validator
description: Validates infrastructure changes safely
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
```

### Agent Integration

#### Temporal Workflows
```go
result, err := temporalIntegrator.ExecuteInTemporal(
    ctx, workflowID, activityID, code)
```

#### Pi-Mono Agents
```go
result, err := piMonoIntegrator.ExecuteInPiMono(
    ctx, sessionID, skillName, code)
```

#### Memory Agents
```go
result, err := memoryIntegrator.ExecuteInMemory(
    ctx, memoryID, query, code)
```

### Template Selection

The intelligent template selector automatically chooses the best template based on:

- Skill type and name patterns
- Programming language requirements
- Isolation level needs
- Historical performance data
- Resource requirements

```go
context := &SelectionContext{
    SkillName:      "security-scanner",
    SkillType:      "security",
    AgentType:      "temporal",
    Language:       "python",
    IsolationLevel: "high",
    NetworkAccess:  false,
}

result, err := templateSelector.SelectTemplate(ctx, context)
```

## Monitoring and Metrics

### Prometheus Metrics

- `agent_sandbox_executions_total`: Total execution count
- `agent_sandbox_execution_duration_seconds`: Execution duration
- `agent_sandbox_execution_errors_total`: Error count
- `agent_sandbox_resource_usage`: Resource usage
- `agent_sandbox_status`: Sandbox status
- `agent_sandbox_warm_pool_status`: Warm pool status

### Performance Tracking

The system tracks template performance including:
- Success rates
- Average execution times
- Resource utilization
- Error patterns

## Security Considerations

### Isolation Levels

- **Low**: Basic isolation, suitable for trusted code
- **Medium**: Enhanced isolation, default for most skills
- **High**: Maximum isolation, for untrusted code

### Network Policies

- Default deny egress policy
- Configurable allowed domains and ports
- Template-specific network rules

### Security Policies

Skills can define security policies for:
- Network access control
- Filesystem restrictions
- Process limitations
- Output scanning

## Development Guide

### Adding New Templates

1. Define template in configuration
2. Create template manager instance
3. Register with template selector
4. Add selection rules if needed

### Extending Integration

1. Create new integrator for agent type
2. Implement execution interface
3. Add to main integrator
4. Update documentation

### Custom Selection Rules

```go
rule := &SelectionRule{
    Name:     "Custom Rule",
    Priority: 100,
    Conditions: []SelectionCondition{
        {Field: "skill_type", Operator: "equals", Value: "custom"},
    },
    Action: SelectionAction{
        Type: "set_template",
        Parameters: map[string]interface{}{
            "template": "custom-template",
        },
    },
    Enabled: true,
}

templateSelector.AddRule(rule)
```

## Troubleshooting

### Common Issues

1. **Template Not Found**: Verify template exists in configuration
2. **Sandbox Not Ready**: Check warm pool status and template validity
3. **Permission Denied**: Verify Kubernetes RBAC and service accounts
4. **Resource Limits**: Check resource requests vs. cluster capacity

### Debug Commands

```bash
# Check sandbox status
kubectl get sandboxclaims -n agent-sandbox

# Check warm pools
kubectl get sandboxwarmpools -n agent-sandbox

# Check templates
kubectl get sandboxtemplates -n agent-sandbox

# View logs
kubectl logs -n agent-sandbox -l app=agent-sandbox-controller
```

## Examples

### Simple Python Execution
```go
request := &ExecutionRequest{
    AgentID:   "test-agent",
    AgentType: "temporal",
    Code:      "print('Hello from Agent Sandbox!')",
    Language:  "python",
    Template:  "python-runtime-template",
}

result, err := executor.Execute(ctx, request)
```

### Infrastructure Validation
```go
request := &ExecutionRequest{
    AgentID:       "infra-validator",
    AgentType:     "pi-mono",
    Code:          "terraform validate",
    Language:      "bash",
    Template:      "bash-runtime-template",
    NetworkAccess: false,
    Resources: sandbox.ResourceSpec{
        CPU:    "500m",
        Memory: "1Gi",
    },
}

result, err := executor.Execute(ctx, request)
```

## Future Enhancements

- GPU support for ML workloads
- Advanced snapshot management
- Multi-tenant isolation
- Custom runtime support
- Enhanced security scanning
- Performance auto-tuning

## Contributing

When contributing to the Agent Sandbox integration:

1. Follow the existing code structure
2. Add comprehensive tests
3. Update documentation
4. Consider security implications
5. Monitor performance impact

## License

This integration follows the same license as the agentic-reconciliation-engine project.

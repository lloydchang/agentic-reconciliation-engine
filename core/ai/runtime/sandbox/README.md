# Sandbox Integration Module

## Overview

The sandbox integration module provides safe execution environments for infrastructure code testing and validation. It integrates with Open SWE sandbox providers (Modal, Daytona, Runloop) to enable isolated code execution while maintaining GitOps safety constraints.

## Architecture

```
core/ai/runtime/sandbox/
├── providers/          # Provider abstraction layer
├── middleware/         # Safety and validation middleware
└── scripts/           # Utility scripts
```

## Provider Abstraction

The sandbox system supports multiple cloud providers through a unified interface:

### Supported Providers
- **Modal**: Serverless cloud execution with GPU support
- **Daytona**: Containerized development environments
- **Runloop**: Browser-based sandbox execution

### Provider Interface
```python
class SandboxProvider(ABC):
    @abstractmethod
    async def create_environment(self, config: SandboxConfig) -> SandboxEnvironment:
        """Create a new sandbox environment"""

    @abstractmethod
    async def execute_code(self, environment: SandboxEnvironment, code: str) -> ExecutionResult:
        """Execute code in the sandbox environment"""

    @abstractmethod
    async def destroy_environment(self, environment: SandboxEnvironment) -> None:
        """Clean up sandbox environment"""
```

## Safety Middleware

All sandbox execution goes through safety middleware that enforces:

### Infrastructure Safety Checks
- **Resource Limits**: CPU, memory, and execution time constraints
- **Network Isolation**: Restricted external network access
- **File System Sandboxing**: Limited file system access
- **Command Whitelisting**: Only approved commands allowed

### Validation Layers
- **Pre-execution**: Code analysis and safety validation
- **Runtime Monitoring**: Resource usage and behavior monitoring
- **Post-execution**: Result validation and cleanup

## Integration Points

### Skill Execution Integration
Skills can opt into sandbox execution by setting `execution_mode: sandbox`:

```yaml
# Example skill configuration
name: infrastructure-validator
description: Validates infrastructure changes safely
metadata:
  risk_level: medium
  autonomy: conditional
  layer: temporal
  execution_mode: sandbox
  sandbox_config:
    provider: modal
    resources:
      cpu: 2
      memory: 4GB
      timeout: 300s
```

### Temporal Workflow Integration
Sandbox execution integrates with Temporal workflows:

```python
# Workflow step with sandbox execution
@workflow.defn
class InfrastructureValidationWorkflow:
    @workflow.run
    async def run(self, config: ValidationConfig):
        # Create sandbox environment
        environment = await sandbox_manager.create_environment(config.sandbox)

        try:
            # Execute validation in sandbox
            result = await sandbox_manager.execute_code(environment, config.code)
            return result
        finally:
            # Cleanup environment
            await sandbox_manager.destroy_environment(environment)
```

## Configuration

### Global Configuration
```yaml
# core/ai/config/sandbox.yaml
providers:
  modal:
    enabled: true
    api_key: ${MODAL_API_KEY}
    default_resources:
      cpu: 2
      memory: 4GB
  daytona:
    enabled: true
    api_key: ${DAYTONA_API_KEY}
  runloop:
    enabled: false

safety:
  max_execution_time: 300s
  max_memory_usage: 8GB
  allowed_commands: ["terraform", "kubectl", "helm", "python3", "bash"]
  network_access: restricted
```

### Skill-Specific Configuration
Skills can override default sandbox settings:

```yaml
metadata:
  sandbox_config:
    provider: modal
    resources:
      cpu: 4
      memory: 8GB
      gpu: true
    environment:
      - TF_VERSION=1.5.0
      - KUBECTL_VERSION=1.28.0
```

## Usage Examples

### Basic Sandbox Execution
```python
from core.ai.runtime.sandbox import SandboxManager

manager = SandboxManager()
config = SandboxConfig(
    provider="modal",
    resources=ResourceLimits(cpu=2, memory="4GB", timeout=300)
)

async with manager.create_environment(config) as env:
    result = await manager.execute_code(env, "terraform validate")
    print(f"Validation result: {result}")
```

### Skill Integration
```python
# Skill execution with sandbox mode
class InfrastructureSkill:
    async def execute(self, request: SkillRequest):
        if self.execution_mode == "sandbox":
            # Use sandbox execution
            result = await self.sandbox_manager.execute_infrastructure_code(
                request.code,
                request.config
            )
        else:
            # Use local execution
            result = await self.local_executor.execute(request.code)

        return result
```

## Benefits

### Safety
- **Isolated Execution**: Code runs in controlled environments
- **Resource Limits**: Prevent resource exhaustion
- **Network Security**: Restricted external access

### Scalability
- **Cloud Resources**: Access to scalable cloud infrastructure
- **Parallel Execution**: Multiple sandbox environments simultaneously
- **GPU Support**: Access to GPU resources when needed

### Reliability
- **Consistent Environments**: Predictable execution environments
- **Error Isolation**: Failures don't affect main system
- **Cleanup Guarantee**: Automatic environment cleanup

## Development Status

### Completed
- [x] Directory structure and organization
- [ ] Provider abstraction layer
- [ ] Safety middleware implementation
- [ ] Skill execution integration
- [ ] Configuration management
- [ ] Documentation and examples

### Next Steps
1. Implement provider abstraction classes
2. Add safety middleware components
3. Integrate with skill execution system
4. Add comprehensive testing
5. Create usage documentation

## Security Considerations

- **API Key Management**: Secure storage and rotation of provider credentials
- **Resource Quotas**: Per-user and per-organization resource limits
- **Audit Logging**: Complete execution logging and monitoring
- **Code Analysis**: Pre-execution security scanning
- **Network Policies**: Strict network access controls

## Monitoring and Observability

The sandbox system provides comprehensive monitoring:

- **Execution Metrics**: Success rates, execution times, resource usage
- **Error Tracking**: Failure analysis and debugging information
- **Cost Monitoring**: Resource usage costs and optimization
- **Security Events**: Security violations and suspicious activities

This monitoring integrates with the existing GitOps observability stack (Prometheus, Grafana, ELK).

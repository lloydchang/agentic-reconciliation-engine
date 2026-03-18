---
name: openswe-code-review
description: >
  Advanced code review using OpenSWE Deep Agents with sandbox execution
  for security analysis, performance testing, and automated fixes.
metadata:
  risk_level: medium
  autonomy: conditional
  layer: openswe
  execution_environment: sandbox
  integration_points:
    - github
    - slack
    - linear
  sandbox_config:
    provider: modal
    timeout: 1800
    resources:
      cpu: 2
      memory: 4Gi
  openswe_config:
    agent_type: "deep-agent"
    model: "anthropic:claude-opus-4-6"
    middleware:
      - GitOpsSafetyMiddleware
      - ToolErrorMiddleware
      - check_message_queue_before_model
      - open_pr_if_needed
    tools:
      - execute
      - fetch_url
      - http_request
      - commit_and_open_pr
      - read_file
      - write_file
      - edit_file
      - grep
      - ls
      - task  # subagent spawning
  dependencies:
    required_skills: []
    conflicts_with: []
    order_constraints: []
---

# OpenSWE Code Review Skill

This skill provides advanced code review capabilities using OpenSWE Deep Agents with sandbox execution for comprehensive analysis, security scanning, and automated issue resolution.

## Enhanced agentskills.io Specification Extensions

### OpenSWE-Specific Metadata Fields

| Field | Type | Description |
|---|---|---|
| `layer` | string | Must be "openswe" for OpenSWE skills |
| `execution_environment` | string | "sandbox" for isolated execution |
| `integration_points` | []string | Supported integrations (github, slack, linear) |
| `sandbox_config` | object | Sandbox provider and resource configuration |
| `openswe_config` | object | OpenSWE-specific configuration |

### Sandbox Configuration Schema

```yaml
sandbox_config:
  provider: modal|daytona|runloop|langsmith
  timeout: 1800  # seconds
  resources:
    cpu: 2
    memory: 4Gi
    gpu: optional
    disk: 20Gi
  network_access: true
  persistent_storage: false
```

### OpenSWE Configuration Schema

```yaml
openswe_config:
  agent_type: "deep-agent"  # Currently only deep-agent supported
  model: "anthropic:claude-opus-4-6"  # Model specification
  middleware:  # List of middleware hooks
    - GitOpsSafetyMiddleware
    - ToolErrorMiddleware
    - check_message_queue_before_model
    - open_pr_if_needed
  tools:  # Available tools in sandbox
    - execute
    - fetch_url
    - http_request
    - commit_and_open_pr
    - read_file
    - write_file
    - edit_file
    - grep
    - ls
    - task  # subagent spawning
```

## When to Use This Skill

Use this skill when:
- Pull requests need automated, sandbox-isolated code review
- Security vulnerabilities require isolated scanning
- Performance analysis needs dedicated resources
- Code quality checks require comprehensive testing
- Automated fixes need safe execution environment

## What This Skill Does

### 1. Sandbox Environment Setup
- Provisions isolated cloud environment (Modal/Daytona/Runloop)
- Configures development tools and dependencies
- Sets up network access and resource limits
- Initializes with repository context

### 2. Comprehensive Code Analysis
- **Security Scanning**: Identifies vulnerabilities, secrets, injection risks
- **Code Quality**: Checks style, complexity, maintainability
- **Performance Analysis**: Reviews algorithms, resource usage, bottlenecks
- **Architecture Review**: Validates patterns, dependencies, structure

### 3. Automated Issue Resolution
- Generates fixes for identified issues
- Creates commits and pull requests automatically
- Provides detailed explanations for changes
- Follows repository conventions and standards

### 4. Integration with Development Workflow
- **GitHub**: Automated PR reviews and comments
- **Slack**: Real-time notifications and status updates
- **Linear**: Issue tracking and progress updates

## Implementation Details

### Required Dependencies
- OpenSWE orchestrator service running
- Sandbox provider credentials configured
- Repository access and webhook setup
- Middleware components deployed

### Execution Flow

1. **Trigger Detection**
   - GitHub webhook for PR events
   - Slack mention or direct message
   - Linear issue comment with @openswe

2. **Context Gathering**
   - Repository AGENTS.md file loading
   - Pull request/issue details extraction
   - Thread/conversation history assembly

3. **Sandbox Provisioning**
   - Environment creation with specified provider
   - Repository cloning and setup
   - Tool installation and configuration

4. **Analysis Execution**
   - Code checkout and analysis
   - Tool execution in isolated environment
   - Result aggregation and processing

5. **Result Delivery**
   - Comment posting to original platform
   - Status updates and notifications
   - PR creation for fixes (when applicable)

### Middleware Hooks

#### GitOpsSafetyMiddleware
Ensures all infrastructure changes flow through GitOps pipelines:
```python
async def before_model(context):
    if detect_infrastructure_changes(context):
        await validate_gitops_compliance(context)
    return context
```

#### ToolErrorMiddleware
Handles tool execution errors gracefully:
```python
async def on_tool_error(error, context):
    await log_error(error)
    await attempt_recovery(context)
    return context
```

#### check_message_queue_before_model
Injects follow-up messages before model calls:
```python
async def before_model(context):
    follow_ups = await get_pending_messages(context.thread_id)
    if follow_ups:
        context.messages.extend(follow_ups)
    return context
```

#### open_pr_if_needed
Creates PR if agent completes without doing so:
```python
async def after_execution(result, context):
    if not result.pr_created and should_create_pr(result):
        await create_pr_from_changes(result)
    return result
```

## Success Criteria

- All security vulnerabilities identified and reported
- Code quality meets configured thresholds
- Performance issues highlighted with remediation steps
- Automated fixes successfully applied and tested
- Clear, actionable feedback provided to developers
- No sandbox environment leaks or security issues

## Error Handling

### Common Failure Modes
- **Sandbox Provisioning Failures**: Provider outages, resource limits
- **Tool Execution Errors**: Missing dependencies, timeout issues
- **Network Connectivity Issues**: External service dependencies
- **Repository Access Problems**: Permission or authentication issues

### Recovery Procedures
- **Automatic Retries**: Sandbox creation failures with exponential backoff
- **Fallback Providers**: Switch to alternative sandbox providers
- **Partial Results**: Deliver available analysis when some tools fail
- **Manual Intervention**: Escalate critical failures to human operators

## Security Considerations

### Sandbox Isolation
- Complete network isolation from production systems
- Resource limits prevent abuse and ensure fairness
- Automatic cleanup prevents resource leaks
- Credential isolation prevents exposure

### Access Control
- Repository-specific permissions
- User authentication and authorization
- Audit logging of all operations
- Compliance with organizational security policies

### Data Protection
- No sensitive data persistence in sandboxes
- Encrypted communication channels
- Secure credential management
- Regular security updates and patches

## Monitoring and Observability

### Key Metrics
- **Analysis Completion Rate**: Percentage of successful reviews
- **Average Analysis Time**: End-to-end processing duration
- **Resource Utilization**: CPU, memory, and storage usage
- **Error Rates**: Tool failures and recovery success
- **Developer Satisfaction**: Feedback and usage patterns

### Logging Requirements
- Detailed execution logs for troubleshooting
- Security event logging for compliance
- Performance metrics for optimization
- User interaction tracking for UX improvement

## Integration Examples

### GitHub Integration
```yaml
# Automatic PR review trigger
on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: openswe/review-action@v1
        with:
          repository: ${{ github.repository }}
          pr-number: ${{ github.event.number }}
```

### Slack Integration
```bash
# Direct message command
@OpenSWE review PR #123 in org/repo

# Thread reply for follow-ups
@OpenSWE can you also check the performance impact?
```

### Linear Integration
```yaml
# Issue comment trigger
@openswe implement the feature described in this issue

# Automatic status updates
- Analysis started
- Security scan completed
- Code review finished
- PR created: #456
```

## Configuration Examples

### Basic Configuration
```yaml
metadata:
  risk_level: medium
  autonomy: conditional
  layer: openswe
  sandbox_config:
    provider: modal
    timeout: 1800
```

### Advanced Configuration
```yaml
metadata:
  risk_level: high
  autonomy: requires_PR
  layer: openswe
  integration_points: [github, slack]
  sandbox_config:
    provider: daytona
    timeout: 3600
    resources:
      cpu: 4
      memory: 8Gi
      gpu: true
  openswe_config:
    model: "anthropic:claude-opus-4-6"
    middleware:
      - GitOpsSafetyMiddleware
      - SecurityValidationMiddleware
      - AuditLoggingMiddleware
```

## Future Enhancements

### Planned Features
- **Multi-language Support**: Enhanced analysis for additional languages
- **Custom Tool Integration**: Organization-specific analysis tools
- **Advanced AI Models**: Support for latest LLM capabilities
- **Real-time Collaboration**: Enhanced interactive development sessions

### Integration Expansions
- **Additional Platforms**: GitLab, Bitbucket, Discord integrations
- **Custom Sandboxes**: On-premises sandbox provider support
- **Advanced Middleware**: Organization-specific validation rules
- **Analytics Dashboard**: Comprehensive review metrics and insights

---
name: ai-agent-orchestration
description: Orchestrate and coordinate multiple AI agents for complex workflows. Use when managing agent interactions, coordinating multi-agent tasks, or implementing agent communication patterns.
argument-hint: "[action] [agentType] [workflowType] [parameters]"
context: fork
agent: Plan
disable-model-invocation: false
user-invocable: true
allowed-tools: 
  - Bash
  - Read
  - Write
  - Grep
---

# AI Agent Orchestration Skill

Advanced AI agent orchestration using isolated subagent execution for complex multi-agent workflows. This skill coordinates multiple specialized agents to handle sophisticated tasks through intelligent collaboration.

## Usage
```bash
/ai-agent-orchestration orchestrate compliance-audit production --priority=high
/ai-agent-orchestration coordinate security-analysis cost-optimization --target=all-resources
/ai-agent-orchestration deploy-agent compliance-check --config=compliance-config.yaml
/ai-agent-orchestration monitor-agents --status=detailed
```

## Subagent Architecture

This skill uses `context: fork` with `agent: Plan` to create an isolated orchestration environment optimized for:

- **Agent Coordination**: Intelligent agent selection and task distribution
- **Workflow Management**: Complex multi-agent workflow execution
- **Resource Allocation**: Dynamic resource management for agent execution
- **Conflict Resolution**: Handling competing agent priorities and dependencies

## Agent Types

### Compliance Agent
```yaml
name: compliance-check
capabilities:
  - SOC2 validation
  - GDPR compliance
  - HIPAA verification
  - Policy enforcement
triggers:
  - audit requests
  - configuration changes
  - scheduled scans
```

### Security Agent
```yaml
name: security-analysis
capabilities:
  - Vulnerability scanning
  - Threat detection
  - Security policy validation
  - Incident response
triggers:
  - security events
  - code changes
  - threat intelligence
```

### Cost Agent
```yaml
name: cost-optimization
capabilities:
  - Resource optimization
  - Spending analysis
  - Budget monitoring
  - Cost forecasting
triggers:
  - cost anomalies
  - resource changes
  - budget alerts
```

### Infrastructure Agent
```yaml
name: infrastructure-discovery
capabilities:
  - Resource discovery
  - Topology mapping
  - Configuration analysis
  - Dependency tracking
triggers:
  - infrastructure changes
  - discovery requests
  - monitoring alerts
```

## Orchestration Patterns

### Sequential Agent Execution
```bash
# Execute agents in sequence with dependency management
/ai-agent-orchestration orchestrate sequential \
  --agents=infrastructure-discovery,compliance-check,security-analysis \
  --target=production-cluster \
  --fail-fast=true
```

### Parallel Agent Execution
```bash
# Execute multiple agents simultaneously
/ai-agent-orchestration orchestrate parallel \
  --agents=compliance-check,security-analysis,cost-optimization \
  --target=all-resources \
  --timeout=3600
```

### Conditional Agent Workflows
```bash
# Conditional agent execution based on previous results
/ai-agent-orchestration orchestrate conditional \
  --workflow="if compliance-check.passed then security-analysis else remediation"
  --target=new-service
```

### Agent Coordination with Communication
```bash
# Agents that communicate and share context
/ai-agent-orchestration orchestrate collaborative \
  --agents=compliance-check,cost-optimization \
  --communication-channel=shared-context \
  --decision-consensus=true
```

## Agent Communication Protocols

### Message Passing
```yaml
communication:
  type: message-passing
  channels:
    - agent-events
    - shared-context
    - decision-coordination
  protocols:
    - async-messages
    - request-response
    - broadcast
```

### Shared Memory
```yaml
communication:
  type: shared-memory
  context-store:
    type: redis
    endpoint: localhost:6379
  data-types:
    - agent-results
    - workflow-state
    - coordination-metadata
```

### Event-Driven Coordination
```yaml
communication:
  type: event-driven
  events:
    - agent-completed
    - agent-failed
    - workflow-milestone
  handlers:
    - on-agent-completed: schedule-next-agent
    - on-agent-failed: initiate-fallback
```

## Workflow Templates

### Compliance Audit Workflow
```yaml
name: compliance-audit
agents:
  - name: infrastructure-discovery
    action: discover-resources
    output: resource-inventory
  - name: compliance-check
    action: validate-compliance
    input: resource-inventory
    output: compliance-report
  - name: security-analysis
    action: security-scan
    input: resource-inventory
    output: security-report
  - name: remediation-agent
    action: generate-remediation
    input: [compliance-report, security-report]
    output: remediation-plan
coordination:
  type: sequential
  error-handling: continue-on-failure
```

### Cost Optimization Workflow
```yaml
name: cost-optimization-cycle
agents:
  - name: infrastructure-discovery
    action: map-resources
  - name: cost-optimization
    action: analyze-costs
  - name: compliance-check
    action: validate-changes
    action-condition: cost-optimization.has-recommendations
coordination:
  type: conditional
  retry-policy:
    max-attempts: 3
    backoff: exponential
```

### Multi-Agent Security Response
```yaml
name: security-incident-response
agents:
  - name: security-analysis
    action: investigate-incident
    priority: critical
  - name: compliance-check
    action: assess-compliance-impact
    parallel: true
  - name: infrastructure-discovery
    action: map-affected-resources
    parallel: true
  - name: remediation-agent
    action: execute-remediation
    depends-on: [security-analysis, compliance-check, infrastructure-discovery]
coordination:
  type: parallel-then-sequential
  timeout: 1800
```

## Agent Deployment

### Agent Configuration
```yaml
agent:
  name: compliance-check
  version: 1.0.0
  runtime:
    type: temporal-workflow
    workflow-id: compliance-check-workflow
    task-queue: compliance-queue
  resources:
    memory: 512Mi
    cpu: 500m
    timeout: 3600s
  environment:
    LOG_LEVEL: info
    COMPLIANCE_FRAMEWORK: SOC2
```

### Dynamic Agent Registration
```bash
# Register new agent type
/ai-agent-orchestration register-agent \
  --name=new-agent \
  --type=workflow \
  --definition=agent-def.yaml \
  --capabilities=capability-list

# Update agent configuration
/ai-agent-orchestration update-agent \
  --name=compliance-check \
  --config=new-config.yaml \
  --restart=true
```

### Agent Health Monitoring
```bash
# Check agent health
/ai-agent-orchestration health-check --agent=all

# Monitor agent performance
/ai-agent-orchestration monitor --agent=compliance-check --metrics=detailed

# Agent lifecycle management
/ai-agent-orchestration restart-agent security-analysis --graceful=true
```

## Integration Points

### Temporal Workflow Integration
```go
// Agent orchestration workflow
func AgentOrchestrationWorkflow(ctx workflow.Context, input OrchestrationInput) error {
    // Initialize agents
    agents := []Agent{
        NewComplianceAgent(),
        NewSecurityAgent(),
        NewCostAgent(),
    }
    
    // Execute orchestration pattern
    switch input.Pattern {
    case "sequential":
        return executeSequential(ctx, agents, input.Target)
    case "parallel":
        return executeParallel(ctx, agents, input.Target)
    case "conditional":
        return executeConditional(ctx, agents, input.Target)
    }
    
    return nil
}
```

### Backend API Integration
```bash
# Start orchestration
curl -X POST http://localhost:8081/api/v1/orchestration/start \
  -H "Content-Type: application/json" \
  -d '{
    "agents": ["compliance-check", "security-analysis"],
    "pattern": "parallel",
    "target": "production-cluster"
  }'

# Get orchestration status
curl http://localhost:8081/api/v1/orchestration/{orchestration-id}/status
```

## Performance Optimization

### Agent Pool Management
```yaml
agent-pools:
  compliance-check:
    size: 3
    scaling: auto
    min-size: 1
    max-size: 10
  security-analysis:
    size: 2
    scaling: on-demand
    min-size: 1
    max-size: 5
```

### Resource Optimization
```bash
# Optimize agent resource allocation
/ai-agent-orchestration optimize-resources --agent=all

# Balance agent load
/ai-agent-orchestration balance-load --strategy=round-robin

# Scale agents based on demand
/ai-agent-orchestration auto-scale --metric=queue-depth
```

## Error Handling and Recovery

### Agent Failure Handling
```yaml
error-handling:
  strategy: retry-with-fallback
  retry-policy:
    max-attempts: 3
    backoff: exponential
  fallback-agents:
    compliance-check: compliance-check-lite
    security-analysis: security-scan-basic
  escalation:
    threshold: 2-failures
    action: human-intervention
```

### Workflow Recovery
```bash
# Resume failed orchestration
/ai-agent-orchestration resume --orchestration-id=12345

# Restart from failed agent
/ai-agent-orchestration restart-agent --orchestration-id=12345 --agent=security-analysis

# Manual intervention
/ai-agent-orchestration manual-override --orchestration-id=12345 --action=skip-agent
```

## Monitoring and Observability

### Agent Metrics
```bash
# Agent performance metrics
/ai-agent-orchestration metrics --agent=all --format=prometheus

# Orchestration success rates
/ai-agent-orchestration analytics --metric=success-rate --timeframe=24h

# Agent resource usage
/ai-agent-orchestration resource-usage --agent=compliance-check --detailed
```

### Dashboard Integration
```yaml
dashboard:
  agent-status:
    - agent: compliance-check
      endpoint: /metrics/compliance
    - agent: security-analysis
      endpoint: /metrics/security
  orchestration-overview:
    endpoint: /api/v1/orchestration/status
    refresh: 5s
```

## Best Practices

1. **Agent Specialization**: Keep agent responsibilities focused and single-purpose
2. **Clear Interfaces**: Define well-structured agent communication protocols
3. **Fault Tolerance**: Implement robust error handling and recovery mechanisms
4. **Resource Management**: Monitor and optimize agent resource usage
5. **Observability**: Implement comprehensive monitoring and logging
6. **Testing**: Test agent interactions and orchestration patterns thoroughly

## Related Skills

- `/workflow-management`: Orchestrate individual workflows
- `/compliance-check`: Compliance validation agent
- `/security-analysis`: Security scanning agent
- `/cost-optimization`: Cost optimization agent
- `/infrastructure-discovery`: Resource discovery agent

## File Locations

- **Agent Definitions**: `backend/agents/`
- **Orchestration Logic**: `backend/orchestration/`
- **Agent Configurations**: `config/agents/`
- **Monitoring**: `monitoring/agents/`
- **Tests**: `tests/orchestration/`

## OpenAI Codex Integration

This section documents the OpenAI Codex-style AI agent orchestration that has been integrated into the Claude skills framework.

### Basic Agent Orchestration Principles

When orchestrating AI agents, follow these principles:

#### 1. Agent Design
- Define clear agent responsibilities and boundaries
- Design agent interfaces and communication protocols
- Implement proper agent state management
- Handle agent lifecycle events

#### 2. Workflow Coordination
- Create agent workflow definitions
- Define agent execution sequences
- Handle agent dependencies and prerequisites
- Implement agent failover and recovery

#### 3. Communication Patterns
- Design agent-to-agent messaging
- Implement event-driven communication
- Handle asynchronous agent interactions
- Manage agent conversation context

#### 4. Resource Management
- Allocate agent resources appropriately
- Monitor agent performance and health
- Handle agent scaling and load balancing
- Manage agent configuration and secrets

### Agent Types in This Sandbox
- **Compliance Agents**: Validate policies and regulations
- **Security Agents**: Perform security analysis and monitoring
- **Cost Agents**: Optimize resource usage and spending
- **Infrastructure Agents**: Manage and discover infrastructure
- **Workflow Agents**: Coordinate and execute workflows

### Implementation Patterns
```go
// Agent workflow example
func AgentWorkflow(ctx workflow.Context, input AgentInput) error {
    // Initialize agent
    agent := NewAgent(input.Type)
    
    // Execute agent logic
    result, err := workflow.ExecuteActivity(ctx, agent.Run, input.Params)
    if err != nil {
        return err
    }
    
    // Handle agent output
    return workflow.ExecuteActivity(ctx, ProcessAgentResult, result.Value)
}
```

### Configuration Files
- Agent definitions: `backend/agents/`
- Workflow configurations: `backend/workflows/`
- Skill definitions: `.agents/skills/` and `.claude/skills/`

### Monitoring and Debugging
- Track agent execution metrics
- Monitor agent communication patterns
- Log agent decision points
- Debug agent failures with detailed logs

### Best Practices
- Keep agent responsibilities focused and single-purpose
- Implement proper error handling and retries
- Design for agent isolation and fault tolerance
- Use structured logging for agent activities
- Test agent interactions thoroughly

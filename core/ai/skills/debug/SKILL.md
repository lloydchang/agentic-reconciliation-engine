---
name: ai-system-debugger
description: Comprehensive debugging skill for agents, Temporal workflows, and Kubernetes infrastructure in distributed environments
version: 1.0.0
risk_level: low
autonomy: fully_auto
layer: temporal
action_name: debug_system

input_schema:
  type: object
  properties:
    target_component:
      type: string
      enum: ["agents", "workflows", "infrastructure", "all"]
      description: "Component to debug"
    issue_type:
      type: string
      enum: ["performance", "errors", "timeouts", "connectivity", "resource", "behavior"]
      description: "Type of issue to investigate"
    time_range:
      type: string
      pattern: "^\\d+[mhd]$"
      description: "Time range for analysis (e.g., 30m, 2h, 1d)"
    namespace:
      type: string
      default: "temporal"
      description: "Kubernetes namespace to investigate"
    verbose:
      type: boolean
      default: false
      description: "Enable verbose logging"
    auto_fix:
      type: boolean
      default: false
      description: "Attempt automatic fixes for common issues"
  required:
    - target_component
    - issue_type

output_schema:
  type: object
  properties:
    debug_session_id:
      type: string
      description: "Unique identifier for this debug session"
    findings:
      type: array
      items:
        type: object
        properties:
          component:
            type: string
          severity:
            type: string
            enum: ["critical", "warning", "info"]
          issue:
            type: string
          root_cause:
            type: string
          evidence:
            type: array
            items:
              type: string
          recommendations:
            type: array
            items:
              type: string
    metrics_summary:
      type: object
      properties:
        total_issues:
          type: integer
        critical_issues:
          type: integer
        warnings:
          type: integer
        auto_fixes_applied:
          type: integer
    execution_time:
      type: number
      description: "Debug session duration in seconds"
    next_steps:
      type: array
      items:
        type: string
  required:
    - debug_session_id
    - findings
    - metrics_summary
    - execution_time

human_gate:
  required: false
  description: "No human approval required for read-only debugging operations. Auto-fix requires review for critical components."

dependencies:
  - kubectl
  - curl
  - jq
  - python3
  - temporal-cli (optional)

environment_variables:
  - KUBECONFIG
  - TEMPORAL_HOST
  - METRICS_ENDPOINT

tags:
  - debugging
  - monitoring
  - troubleshooting
  - distributed-systems
  - agents
  - kubernetes
  - temporal
---

# System Debugger Skill

## Overview

This skill provides comprehensive debugging capabilities for agents running in distributed Kubernetes environments with Temporal orchestration. It systematically diagnoses issues across the entire stack - from individual agent behavior to infrastructure health.

## Capabilities

### Component Debugging
- **Agents**: Analyze agent execution logs, performance metrics, and failure patterns
- **Temporal Workflows**: Inspect workflow execution history, timeouts, and activity failures  
- **Kubernetes Infrastructure**: Check pod health, resource utilization, and network connectivity
- **Integration Points**: Validate communication between agents, workflows, and external services

### Issue Types
- **Performance**: Slow execution, high latency, resource bottlenecks
- **Errors**: Agent failures, workflow crashes, API errors
- **Timeouts**: Workflow timeouts, agent inference delays
- **Connectivity**: Network issues, service discovery problems
- **Resource**: Memory/CPU exhaustion, storage issues
- **Behavior**: Unexpected agent responses, hallucination detection

## Usage Examples

### Basic Agent Debugging
```bash
python main.py debug \
  --target-component agents \
  --issue-type errors \
  --time-range 1h \
  --verbose
```

### Infrastructure Health Check
```bash
python main.py debug \
  --target-component infrastructure \
  --issue-type resource \
  --time-range 30m \
  --auto-fix
```

### Full System Analysis
```bash
python main.py debug \
  --target-component all \
  --issue-type performance \
  --time-range 2h \
  --namespace temporal \
  --verbose \
  --auto-fix
```

## Debugging Methodology

### 1. Information Gathering
- Collect metrics from monitoring endpoints
- Analyze Kubernetes pod status and logs
- Review Temporal workflow execution history
- Gather system resource utilization

### 2. Pattern Recognition
- Identify common failure patterns
- Detect anomalies in agent behavior
- Correlate issues across components
- Trend analysis over time ranges

### 3. Root Cause Analysis
- Trace issues through the call chain
- Identify bottlenecks and failure points
- Analyze dependencies and interactions
- Validate configuration and environment

### 4. Remediation
- Apply automatic fixes for common issues
- Generate detailed remediation plans
- Provide step-by-step resolution guides
- Create prevention strategies

## Integration Points

### Monitoring System
- Metrics API: `/monitoring/metrics`
- Alerts API: `/monitoring/alerts` 
- Health Checks: `/health`
- Audit Logs: `/audit/events`

### Temporal Integration
- Workflow History API
- Activity Execution Logs
- Task Queue Monitoring
- Worker Health Status

### Kubernetes Integration
- Pod Status and Logs
- Service Connectivity
- Resource Utilization
- Network Policies

## Output Format

The skill produces structured debugging reports with:
- **Findings**: Detailed analysis of discovered issues
- **Evidence**: Log snippets, metrics, and supporting data
- **Recommendations**: Actionable remediation steps
- **Metrics**: Summary statistics and health scores
- **Next Steps**: Follow-up actions and monitoring recommendations

## Auto-Fix Capabilities

When `auto_fix` is enabled, the skill can:
- Restart failing pods
- Clear stuck workflows
- Adjust resource limits
- Restart unhealthy agents
- Clear temporary cache issues

## Distributed System Considerations

This skill is designed for distributed environments and includes:
- Namespace isolation support
- Multi-cluster debugging capabilities
- Remote log aggregation
- Cross-component correlation
- Network connectivity validation

## Prevention and Regression

The skill helps prevent regressions by:
- Maintaining debug session history
- Tracking recurring issues
- Generating health baselines
- Creating monitoring alerts
- Providing documentation updates

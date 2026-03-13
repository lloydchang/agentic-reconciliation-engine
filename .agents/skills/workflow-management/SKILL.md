---
name: workflow-management
description: Orchestrate and monitor Temporal AI Agent workflows. Use when managing multiple concurrent workflows, checking status, or coordinating complex multi-agent operations.
argument-hint: "[action] [workflowId] [parameters]"
disable-model-invocation: false
user-invocable: true
allowed-tools: 
  - Bash
  - Read
  - Write
  - Grep
---

# Workflow Management Skill

Comprehensive workflow orchestration and monitoring for Temporal AI Agents system. Provides centralized control over all agent workflows with real-time status tracking and intelligent coordination.

## Usage
```bash
/workflow-management list active
/workflow-management status workflow-12345
/workflow-management cancel workflow-12345 "User requested"
/workflow-management orchestrate compliance-audit production
```

## Core Capabilities

### 1. Workflow Discovery & Listing
```bash
# List all workflows
/workflow-management list all

# List active workflows only
/workflow-management list active

# List workflows by type
/workflow-management list compliance
/workflow-management list security
/workflow-management list cost-analysis

# List workflows with filters
/workflow-management list --priority=high --status=running
```

### 2. Real-time Status Monitoring
```bash
# Get detailed workflow status
/workflow-management status workflow-12345

# Monitor workflow with live updates
/workflow-management monitor workflow-12345

# Get workflow execution history
/workflow-management history workflow-12345

# Check workflow dependencies
/workflow-management dependencies workflow-12345
```

### 3. Workflow Control Operations
```bash
# Cancel a running workflow
/workflow-management cancel workflow-12345 "Budget exceeded"

# Pause a workflow
/workflow-management pause workflow-12345

# Resume a paused workflow
/workflow-management resume workflow-12345

# Restart failed workflow
/workflow-management restart workflow-12345
```

### 4. Advanced Orchestration
```bash
# Create complex workflow orchestration
/workflow-management orchestrate security-audit production --priority=high

# Coordinate multiple workflows
/workflow-management coordinate "compliance-check,security-analysis" production

# Create workflow dependencies
/workflow-management dependency workflow-12345 workflow-67890 "success"

# Batch workflow operations
/workflow-management batch --file=workflow-batch.json
```

## Workflow Types & States

### Workflow Types
- **compliance**: SOC2, GDPR, HIPAA compliance checks
- **security**: Vulnerability scanning, security analysis
- **cost-analysis**: Cost optimization and analysis
- **infrastructure**: Resource discovery and management
- **human-review**: Human-in-the-loop workflows
- **orchestration**: Multi-agent coordination workflows

### Workflow States
- **pending**: Waiting to start
- **running**: Currently executing
- **paused**: Temporarily suspended
- **completed**: Finished successfully
- **failed**: Terminated with errors
- **cancelled**: Manually cancelled
- **timeout**: Exceeded maximum execution time

## Advanced Features

### 1. Intelligent Workflow Scheduling
```python
# Workflow scheduling algorithm
def schedule_workflow(workflow, resources):
    # Check resource availability
    if not resources_available(workflow.requirements):
        return queue_workflow(workflow)
    
    # Check dependencies
    if not dependencies_satisfied(workflow.dependencies):
        return wait_for_dependencies(workflow)
    
    # Optimize execution order
    return optimize_execution_order(workflow, scheduled_workflows)
```

### 2. Dependency Management
```python
# Dependency resolution
class WorkflowDependency:
    def __init__(self, workflow_id, depends_on, condition):
        self.workflow_id = workflow_id
        self.depends_on = depends_on
        self.condition = condition  # success, completion, failure
    
    def is_satisfied(self):
        dependent_workflow = get_workflow(self.depends_on)
        return self.check_condition(dependent_workflow.status)
```

### 3. Resource Allocation
```python
# Resource allocation optimization
def allocate_resources(workflows):
    available_resources = get_available_resources()
    
    # Sort by priority and resource requirements
    sorted_workflows = sort_by_priority_and_resources(workflows)
    
    allocation = {}
    for workflow in sorted_workflows:
        if can_allocate(workflow, available_resources):
            allocation[workflow.id] = allocate(workflow, available_resources)
            update_available_resources(available_resources, allocation)
    
    return allocation
```

### 4. Performance Monitoring
```python
# Performance metrics collection
class WorkflowMonitor:
    def __init__(self):
        self.metrics = {
            'execution_time': [],
            'resource_usage': [],
            'success_rate': [],
            'error_patterns': []
        }
    
    def collect_metrics(self, workflow):
        self.metrics['execution_time'].append(workflow.execution_time)
        self.metrics['resource_usage'].append(workflow.resource_usage)
        
        if workflow.status == 'completed':
            self.metrics['success_rate'].append(1)
        elif workflow.status == 'failed':
            self.metrics['success_rate'].append(0)
            self.metrics['error_patterns'].append(workflow.error)
```

## Command Reference

### List Commands
```bash
# Basic listing
/workflow-management list [filter] [options]

Filters:
- all: Show all workflows
- active: Show running workflows only
- completed: Show completed workflows only
- failed: Show failed workflows only
- {type}: Show workflows of specific type

Options:
- --priority=low|normal|high|critical: Filter by priority
- --status=pending|running|paused|completed|failed|cancelled: Filter by status
- --limit=N: Limit number of results
- --format=json|table|csv: Output format
```

### Status Commands
```bash
# Status checking
/workflow-management status <workflow_id> [options]

Options:
- --verbose: Show detailed execution logs
- --dependencies: Show workflow dependencies
- --history: Show execution history
- --metrics: Show performance metrics
```

### Control Commands
```bash
# Workflow control
/workflow-management <action> <workflow_id> [reason]

Actions:
- cancel: Cancel workflow execution
- pause: Temporarily pause workflow
- resume: Resume paused workflow
- restart: Restart failed workflow
- priority: Change workflow priority
```

### Orchestration Commands
```bash
# Advanced orchestration
/workflow-management orchestrate <orchestration_type> <target> [options]

Orchestration Types:
- security-audit: Comprehensive security assessment
- compliance-review: Full compliance evaluation
- cost-optimization: Complete cost analysis
- infrastructure-audit: Infrastructure assessment

Options:
- --priority=low|normal|high|critical: Execution priority
- --parallel=N: Number of parallel workflows
- --dependencies=json: Workflow dependency definition
- --timeout=N: Maximum execution time in minutes
```

## Output Formats

### Table Format
```
┌─────────────────┬─────────────┬──────────┬──────────┬─────────────┬────────────┐
│ Workflow ID     │ Type        │ Status   │ Priority │ Progress    │ Duration   │
├─────────────────┼─────────────┼──────────┼──────────┼─────────────┼────────────┤
│ wf-12345       │ compliance  │ running  │ high      │ 75%         │ 5m 23s     │
│ wf-12346       │ security    │ pending  │ normal    │ 0%          │ -           │
│ wf-12347       │ cost-analysis│ completed│ low       │ 100%        │ 12m 45s    │
└─────────────────┴─────────────┴──────────┴──────────┴─────────────┴────────────┘
```

### JSON Format
```json
{
  "workflows": [
    {
      "id": "wf-12345",
      "type": "compliance",
      "status": "running",
      "priority": "high",
      "progress": 75,
      "started_at": "2024-01-15T10:30:00Z",
      "estimated_completion": "2024-01-15T10:45:00Z",
      "resource_usage": {
        "cpu": 45,
        "memory": 2.1,
        "network": 150
      }
    }
  ],
  "summary": {
    "total": 3,
    "running": 1,
    "completed": 1,
    "pending": 1,
    "failed": 0
  }
}
```

## Integration with Temporal AI Agents

### API Endpoints
- `list_workflows`: Retrieve workflow list with filters
- `get_workflow_status`: Get detailed workflow information
- `control_workflow`: Execute control operations (cancel, pause, resume)
- `orchestrate_workflows`: Create complex workflow orchestrations
- `monitor_workflows`: Real-time workflow monitoring

### Event Handling
```python
# Workflow event handling
class WorkflowEventHandler:
    def on_workflow_started(self, workflow):
        log_event(f"Workflow {workflow.id} started")
        update_dashboard(workflow)
        notify_stakeholders(workflow)
    
    def on_workflow_completed(self, workflow):
        log_event(f"Workflow {workflow.id} completed successfully")
        update_metrics(workflow)
        trigger_dependent_workflows(workflow)
    
    def on_workflow_failed(self, workflow):
        log_event(f"Workflow {workflow.id} failed: {workflow.error}")
        create_incident(workflow)
        notify_administrators(workflow)
```

## Advanced Orchestration Patterns

### 1. Sequential Orchestration
```bash
# Execute workflows in sequence
/workflow-management orchestrate sequential --workflow-list="wf1,wf2,wf3"
```

### 2. Parallel Orchestration
```bash
# Execute workflows in parallel
/workflow-management orchestrate parallel --workflow-list="wf1,wf2,wf3" --max-concurrent=5
```

### 3. Conditional Orchestration
```bash
# Conditional workflow execution
/workflow-management orchestrate conditional --condition="wf1.status==success" --then="wf2,wf3" --else="wf4"
```

### 4. Pipeline Orchestration
```bash
# Create workflow pipeline
/workflow-management orchestrate pipeline --pipeline="discovery->analysis->optimization->report"
```

## Error Handling & Recovery

### Automatic Recovery
```python
# Automatic workflow recovery
def recover_workflow(workflow):
    if workflow.failure_count < 3:
        # Retry with exponential backoff
        delay = 2 ** workflow.failure_count
        schedule_retry(workflow, delay)
    else:
        # Escalate to human review
        escalate_to_human(workflow)
```

### Deadlock Detection
```python
# Deadlock detection and resolution
def detect_deadlocks():
    running_workflows = get_running_workflows()
    dependencies = build_dependency_graph(running_workflows)
    
    cycles = find_cycles(dependencies)
    if cycles:
        resolve_deadlocks(cycles)
```

### Resource Cleanup
```python
# Automatic resource cleanup
def cleanup_workflow_resources(workflow):
    # Release allocated resources
    release_resources(workflow.allocated_resources)
    
    # Clean up temporary files
    cleanup_temp_files(workflow.temp_directory)
    
    # Update resource pool
    update_resource_availability(workflow.resource_requirements)
```

## Performance Optimization

### Workflow Prioritization
```python
# Dynamic prioritization algorithm
def prioritize_workflows(workflows):
    priority_scores = {}
    
    for workflow in workflows:
        score = 0
        
        # Base priority
        score += priority_weights[workflow.priority]
        
        # Age factor (older workflows get higher priority)
        age_factor = (datetime.now() - workflow.created_at).total_seconds() / 3600
        score += age_factor * 0.1
        
        # Dependency factor (workflows blocking others get higher priority)
        blocking_count = count_blocking_workflows(workflow)
        score += blocking_count * 10
        
        # Resource efficiency
        efficiency = calculate_resource_efficiency(workflow)
        score += efficiency * 5
        
        priority_scores[workflow.id] = score
    
    return sorted(workflows, key=lambda w: priority_scores[w.id], reverse=True)
```

### Load Balancing
```python
# Load balancing across execution nodes
def balance_workload(workflows, nodes):
    node_loads = {node.id: 0 for node in nodes}
    assignments = {}
    
    # Sort workflows by resource requirements
    sorted_workflows = sorted(workflows, key=lambda w: w.resource_requirements, reverse=True)
    
    for workflow in sorted_workflows:
        # Find least loaded node that can handle the workflow
        suitable_nodes = [n for n in nodes if can_handle(n, workflow)]
        target_node = min(suitable_nodes, key=lambda n: node_loads[n.id])
        
        assignments[workflow.id] = target_node.id
        node_loads[target_node.id] += workflow.resource_requirements
    
    return assignments
```

## Monitoring & Alerting

### Real-time Dashboard
```python
# Dashboard metrics
class WorkflowDashboard:
    def __init__(self):
        self.metrics = {
            'active_workflows': 0,
            'completion_rate': 0.0,
            'average_execution_time': 0.0,
            'error_rate': 0.0,
            'resource_utilization': 0.0
        }
    
    def update_metrics(self, workflows):
        self.metrics['active_workflows'] = len([w for w in workflows if w.status == 'running'])
        self.metrics['completion_rate'] = calculate_completion_rate(workflows)
        self.metrics['average_execution_time'] = calculate_avg_execution_time(workflows)
        self.metrics['error_rate'] = calculate_error_rate(workflows)
        self.metrics['resource_utilization'] = calculate_resource_utilization(workflows)
```

### Alert Configuration
```python
# Alert system
class AlertManager:
    def __init__(self):
        self.alert_rules = [
            {
                'name': 'High Failure Rate',
                'condition': 'error_rate > 0.1',
                'severity': 'high',
                'action': 'notify_administrators'
            },
            {
                'name': 'Long Running Workflow',
                'condition': 'execution_time > 3600',  # 1 hour
                'severity': 'medium',
                'action': 'create_ticket'
            },
            {
                'name': 'Resource Exhaustion',
                'condition': 'resource_utilization > 0.9',
                'severity': 'critical',
                'action': 'scale_resources'
            }
        ]
```

## Supporting Files

- [templates/workflow-report.md](templates/workflow-report.md): Workflow execution report template
- [scripts/workflow-orchestrator.py](scripts/workflow-orchestrator.py): Advanced orchestration engine
- [assets/workflow-rules.json](assets/workflow-rules.json): Workflow execution rules and policies
- [scripts/monitoring-dashboard.sh](scripts/monitoring-dashboard.sh): Real-time monitoring dashboard

## Examples

### List Active Workflows
```bash
/workflow-management list active --format=table
```

### Monitor Workflow Progress
```bash
/workflow-management monitor workflow-12345 --verbose
```

### Orchestrate Security Audit
```bash
/workflow-management orchestrate security-audit production --priority=high --parallel=3
```

### Cancel Problematic Workflow
```bash
/workflow-management cancel workflow-12345 "Excessive resource usage"
```

## Related Skills

- `/compliance-check`: Compliance workflow execution
- `/security-analysis`: Security analysis workflows
- `/cost-optimization`: Cost optimization workflows
- `/infrastructure-discovery`: Resource discovery workflows

## Best Practices

1. **Workflow Design**: Keep workflows focused and modular
2. **Dependency Management**: Minimize workflow dependencies
3. **Resource Planning**: Plan resource requirements in advance
4. **Error Handling**: Implement comprehensive error recovery
5. **Monitoring**: Monitor workflow performance continuously
6. **Documentation**: Maintain detailed workflow documentation
7. **Testing**: Test workflow orchestrations thoroughly
8. **Security**: Implement proper access controls for workflow management

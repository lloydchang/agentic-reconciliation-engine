# AI System Debugging Guide

## Overview

This guide provides comprehensive debugging strategies and tools for distributed AI agent systems running in Kubernetes with Temporal orchestration. It covers agent debugging, workflow troubleshooting, infrastructure analysis, and automated debugging capabilities.

## 🏗️ Debugging Architecture

### Core Components

#### AI Agent Debugger Skill
- **Location**: [core/ai/skills/debug/SKILL.md](core/ai/skills/debug/SKILL.md)
- **Purpose**: Agent Skills specification-compliant debugging interface
- **Risk Level**: Low (read-only operations)
- **Autonomy**: Fully automated for read-only, conditional for fixes

#### Python Debugging CLI
- **Location**: `core/ai/skills/debug/core/core/automation/ci-cd/scripts/main.py`
- **Purpose**: Comprehensive debugging with rich output and auto-fix
- **Features**: Real-time monitoring, structured reports, automated fixes

#### Bash Debugging Scripts
- **Location**: `core/ai/skills/debug/core/core/automation/ci-cd/scripts/quick_debug.sh`
- **Purpose**: Fast troubleshooting for common issues
- **Features**: Immediate feedback, auto-fix capabilities

#### Debug Utilities
- **Location**: `core/ai/skills/debug/core/core/automation/ci-cd/scripts/debug_utils.py`
- **Purpose**: Async system metrics collection and analysis
- **Features**: Kubernetes API integration, log pattern analysis

## 🚀 Quick Start

### Prerequisites

```bash
# Required tools
kubectl --version
python --version  # 3.8+
curl --version

# Optional but recommended
jq --version
temporal --version
```

### Basic Debugging Commands

```bash
# Navigate to debugging scripts
cd core/ai/skills/debug/scripts

# Install dependencies (auto-handled by PEP 723)
python main.py --help

# Quick agent debugging
./quick_debug.sh agents errors true

# Comprehensive analysis
python main.py debug --target-component all --issue-type performance --time-range 2h --auto-fix

# Generate debug report
python main.py debug --target-component workflows --issue-type timeouts --output debug-report.json
```

## 📊 Debugging Components

### 1. AI Agents Debugging

#### Common Issues
- **Pod Restart Loops**: Container crashes, resource exhaustion
- **Skill Execution Failures**: Invalid inputs, missing dependencies
- **Performance Degradation**: Memory leaks, CPU bottlenecks
- **Network Issues**: Service discovery, connectivity problems

#### Debugging Commands
```bash
# Agent pod status
kubectl get pods -n temporal -l app=temporal-worker -o wide

# Agent restart analysis
kubectl get pods -n temporal -l app=temporal-worker --no-headers | awk '{print $1, $4}' | column -t

# Recent agent errors
kubectl logs -n temporal deployment/temporal-worker --since=1h | grep -i error | tail -10

# Agent resource usage
kubectl top pods -n temporal -l app=temporal-worker --no-headers | head -5
```

#### Automated Analysis
```python
# Using the Python CLI
python main.py debug \
  --target-component agents \
  --issue-type errors \
  --time-range 1h \
  --verbose \
  --auto-fix
```

### 2. Temporal Workflows Debugging

#### Common Issues
- **Workflow Timeouts**: Long-running activities, stuck workflows
- **Activity Failures**: Retry exhaustion, timeout issues
- **Queue Problems**: Backlog, worker unavailability
- **State Inconsistencies**: Workflow state corruption

#### Debugging Commands
```bash
# Temporal server status
kubectl get pods -n temporal -l app=temporal-server -o wide

# Frontend service status
kubectl get pods -n temporal -l app=temporal-frontend -o wide

# Recent workflow errors
kubectl logs -n temporal deployment/temporal-server --since=1h | grep -i error | tail -10

# Workflow queue status
temporal task queue describe --address localhost:7233
```

#### Workflow Analysis
```python
# Comprehensive workflow debugging
python main.py debug \
  --target-component workflows \
  --issue-type timeouts \
  --time-range 30m \
  --namespace temporal
```

### 3. Kubernetes Infrastructure Debugging

#### Common Issues
- **Node Failures**: NotReady nodes, resource exhaustion
- **Storage Problems**: PVC issues, disk space
- **Network Issues**: Service connectivity, DNS resolution
- **Resource Quotas**: CPU/memory limits exceeded

#### Debugging Commands
```bash
# Node health
kubectl get nodes -o wide

# Resource usage
kubectl top nodes --no-headers

# Recent events
kubectl get events -n temporal --sort-by='.lastTimestamp' | tail -10

# Storage status
kubectl get pv,pvc -n temporal --no-headers | head -10
```

#### Infrastructure Analysis
```python
# Infrastructure health check
python main.py debug \
  --target-component infrastructure \
  --issue-type resource \
  --namespace temporal
```

## 🔧 Advanced Debugging Features

### Auto-Fix Capabilities

#### Supported Auto-Fixes
- **Pod Restart**: Delete and recreate failing pods
- **Stuck Workflows**: Clear stuck workflow executions
- **Resource Limits**: Adjust CPU/memory limits
- **Service Issues**: Restart unhealthy services

#### Auto-Fix Configuration
```yaml
# Auto-fix settings in main.py
auto_fix_config = {
    "restart_failed_pods": True,
    "clear_stuck_workflows": True,
    "adjust_resource_limits": False,  # Requires manual approval
    "restart_services": True,
    "max_retries": 3,
    "dry_run": False
}
```

### Real-time Monitoring

#### Monitoring Endpoints
```bash
# Metrics endpoint
curl http://temporal-worker.temporal.svc.cluster.local:8080/monitoring/metrics

# Alerts endpoint
curl http://temporal-worker.temporal.svc.cluster.local:8080/monitoring/alerts

# Health check
curl http://temporal-worker.temporal.svc.cluster.local:8080/health

# Audit events
curl http://temporal-worker.temporal.svc.cluster.local:8080/audit/events
```

#### WebSocket Streaming
```javascript
// Real-time debug updates
const ws = new WebSocket('ws://temporal-worker.temporal.svc.cluster.local:8080/debug/stream');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    updateDebugDisplay(data);
};
```

### Distributed System Support

#### Multi-Cluster Debugging
```python
# Debug across multiple clusters
python main.py debug \
  --target-component all \
  --clusters cluster1,cluster2,cluster3 \
  --issue-type performance \
  --time-range 2h
```

#### Namespace Isolation
```python
# Namespace-specific debugging
python main.py debug \
  --target-component agents \
  --namespace temporal \
  --issue-type errors \
  --isolation-mode strict
```

## 📈 Debugging Methodology

### 1. Issue Classification

#### Severity Levels
- **Critical**: System-wide impact, immediate attention required
- **High**: Significant impact, user experience affected
- **Medium**: Limited impact, monitoring required
- **Low**: Minor impact, log entry only

#### Issue Types
- **Performance**: Slow response times, resource bottlenecks
- **Errors**: Failures, exceptions, error codes
- **Timeouts**: Operations exceeding time limits
- **Connectivity**: Network, service discovery issues
- **Resource**: CPU, memory, storage problems
- **Behavior**: Unexpected agent behavior

### 2. Debugging Workflow

#### Step 1: Initial Assessment
```bash
# Quick system health check
./quick_debug.sh all general false

# Identify problem area
python main.py debug --target-component all --issue-type general --time-range 1h
```

#### Step 2: Deep Dive Analysis
```bash
# Component-specific analysis
python main.py debug --target-component <component> --issue-type <type> --verbose
```

#### Step 3: Root Cause Analysis
```bash
# Log pattern analysis
python main.py analyze-logs --component agents --pattern errors --time-range 2h

# Performance profiling
python main.py profile --component agents --duration 10m
```

#### Step 4: Resolution
```bash
# Apply auto-fixes
python main.py debug --target-component <component> --auto-fix

# Manual intervention (if needed)
kubectl apply -f fix-manifest.yaml
```

#### Step 5: Verification
```bash
# Verify fix effectiveness
python main.py verify --component <component> --time-range 30m
```

### 3. Prevention Strategies

#### Proactive Monitoring
```python
# Continuous monitoring setup
python main.py monitor --components all --interval 5m --alerts webhook,email

# Health check automation
python main.py health-check --schedule "*/5 * * * *"
```

#### Regression Prevention
```python
# Automated regression testing
python main.py regression-test --suite full --environment staging

# Performance baseline tracking
python main.py baseline --component agents --duration 24h
```

## 🛠️ Integration Points

### Temporal Integration

#### Workflow Debugging
```go
// Enhanced workflow with debugging
func DebuggableWorkflow(ctx workflow.Context, request WorkflowRequest) (*WorkflowResult, error) {
    logger := workflow.GetLogger(ctx)
    
    // Record workflow start
    debugID := fmt.Sprintf("debug-%d", workflow.Now(ctx).Unix())
    logger.Info("Starting debuggable workflow", "debugID", debugID)
    
    // Execute with debug tracking
    result, err := ExecuteWithDebugTracking(ctx, request, debugID)
    if err != nil {
        logger.Error("Workflow failed", "debugID", debugID, "error", err)
        return nil, err
    }
    
    logger.Info("Workflow completed", "debugID", debugID)
    return result, nil
}
```

#### Activity Debugging
```go
// Debuggable activity
func DebuggableActivity(ctx context.Context, input ActivityInput) (*ActivityOutput, error) {
    logger := activity.GetLogger(ctx)
    
    // Record activity start
    activityID := fmt.Sprintf("activity-%d", time.Now().Unix())
    logger.Info("Starting debuggable activity", "activityID", activityID)
    
    // Execute with debug monitoring
    output, err := ExecuteWithDebugMonitoring(ctx, input, activityID)
    if err != nil {
        logger.Error("Activity failed", "activityID", activityID, "error", err)
        return nil, err
    }
    
    logger.Info("Activity completed", "activityID", activityID)
    return output, nil
}
```

### Kubernetes Integration

#### Custom Debug Resources
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: debug-config
  namespace: temporal
data:
  debug-level: "verbose"
  auto-fix: "true"
  monitoring-interval: "30s"
  alert-thresholds: |
    errors: 0.1
    timeouts: 0.05
    restarts: 5
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: debug-monitor
  namespace: temporal
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: debug-monitor
            image: python:3.9
            command: ["python", "/core/core/automation/ci-cd/scripts/main.py"]
            args: ["debug", "--target-component", "all", "--auto-fix"]
            volumeMounts:
            - name: debug-scripts
              mountPath: /scripts
          volumes:
          - name: debug-scripts
            configMap:
              name: debug-scripts
          restartPolicy: OnFailure
```

### Monitoring System Integration

#### Metrics Collection
```go
// Debug metrics collection
func (dc *DebugCollector) CollectDebugMetrics() []*Metric {
    metrics := make([]*Metric, 0)
    
    // Agent debug metrics
    metrics = append(metrics, &Metric{
        Name:      "debug_sessions_total",
        Value:     float64(dc.sessionCount),
        Type:      Counter,
        Timestamp: time.Now(),
        Tags:      map[string]string{"component": "debugger"},
    })
    
    // Auto-fix metrics
    metrics = append(metrics, &Metric{
        Name:      "debug_auto_fixes_applied",
        Value:     float64(dc.autoFixCount),
        Type:      Counter,
        Timestamp: time.Now(),
        Tags:      map[string]string{"component": "debugger"},
    })
    
    return metrics
}
```

## 📋 Troubleshooting Reference

### Common Debugging Scenarios

#### Scenario 1: Agent Pod Crash Loop
```bash
# Symptoms
kubectl get pods -n temporal -l app=temporal-worker
# NAME                READY   STATUS             RESTARTS   AGE
# temporal-worker-xyz  0/1     CrashLoopBackOff   5          10m

# Debug steps
./quick_debug.sh agents errors false
python main.py debug --target-component agents --issue-type errors --verbose

# Common causes
# 1. Resource exhaustion (memory/CPU)
# 2. Configuration errors
# 3. Dependency failures
# 4. Image corruption

# Solutions
# 1. Increase resource limits
# 2. Fix configuration
# 3. Verify dependencies
# 4. Rebuild/pull image
```

#### Scenario 2: Workflow Timeout
```bash
# Symptoms
temporal workflow list --query "WorkflowType='MyWorkflow' and Status='Running'"
# Shows workflows stuck in running state

# Debug steps
python main.py debug --target-component workflows --issue-type timeouts --time-range 1h

# Common causes
# 1. Activity timeout
# 2. Deadlock in workflow
# 3. Resource contention
# 4. Network issues

# Solutions
# 1. Increase timeout values
# 2. Fix workflow logic
# 3. Scale resources
# 4. Fix network connectivity
```

#### Scenario 3: Performance Degradation
```bash
# Symptoms
kubectl top pods -n temporal
# Shows high CPU/memory usage

# Debug steps
python main.py debug --target-component all --issue-type performance --time-range 2h

# Common causes
# 1. Memory leaks
# 2. CPU bottlenecks
# 3. Database slowness
# 4. Network latency

# Solutions
# 1. Restart affected pods
# 2. Scale horizontally
# 3. Optimize database queries
# 4. Improve network configuration
```

### Debug Command Reference

#### Python CLI Commands
```bash
# Main debugging command
python main.py debug [OPTIONS]

# Options:
#   --target-component TEXT    Component to debug (agents|workflows|infrastructure|all)
#   --issue-type TEXT          Type of issue (performance|errors|timeouts|connectivity|resource|behavior)
#   --time-range TEXT          Time range (30m|1h|2h|6h|1d)
#   --namespace TEXT           Kubernetes namespace
#   --verbose                  Enable verbose output
#   --auto-fix                 Apply automatic fixes
#   --output FILE              Save report to file
#   --dry-run                  Show what would be done without executing

# Additional commands
python main.py analyze-logs [OPTIONS]     # Analyze logs for patterns
python main.py profile [OPTIONS]          # Performance profiling
python main.py monitor [OPTIONS]          # Continuous monitoring
python main.py verify [OPTIONS]           # Verify fixes
python main.py regression-test [OPTIONS]  # Regression testing
```

#### Bash Script Commands
```bash
# Quick debugging
./quick_debug.sh [COMPONENT] [ISSUE_TYPE] [AUTO_FIX]

# Components: agents|workflows|infrastructure|performance|connectivity|all
# Issue Types: errors|timeouts|resource|performance|general
# Auto Fix: true|false

# Examples
./quick_debug.sh agents errors true      # Debug agents with auto-fix
./quick_debug.sh all general false       # Full system check
./quick_debug.sh performance resource true # Performance issues with fixes
```

## 🚀 Production Deployment

### Kubernetes Deployment

#### Debug Service Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-debugger
  namespace: temporal
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ai-debugger
  template:
    spec:
      containers:
      - name: debugger
        image: your-registry/ai-debugger:latest
        command: ["python", "main.py"]
        args: ["debug", "--target-component", "all", "--auto-fix"]
        env:
        - name: NAMESPACE
          value: "temporal"
        - name: DEBUG_LEVEL
          value: "verbose"
        - name: AUTO_FIX
          value: "true"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        volumeMounts:
        - name: debug-config
          mountPath: /config
      volumes:
      - name: debug-config
        configMap:
          name: debug-config
```

#### Scheduled Debugging
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scheduled-debugger
  namespace: temporal
spec:
  schedule: "0 */6 * * *"  # Every 6 hours
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: debugger
            image: your-registry/ai-debugger:latest
            command: ["python", "main.py"]
            args: ["debug", "--target-component", "all", "--issue-type", "general"]
            env:
            - name: DEBUG_REPORT_WEBHOOK
              value: "https://your-webhook-url.com/debug"
          restartPolicy: OnFailure
```

### Configuration Management

#### Debug Configuration
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: debug-config
  namespace: temporal
data:
  config.yaml: |
    debug:
      level: verbose
      auto_fix: true
      dry_run: false
      max_retries: 3
    
    thresholds:
      error_rate: 0.1
      timeout_rate: 0.05
      restart_count: 5
      memory_usage: 0.8
      cpu_usage: 0.8
    
    monitoring:
      interval: 30s
      retention: 7d
      alerts: true
    
    components:
      agents:
        enabled: true
        auto_restart: true
        resource_checks: true
      workflows:
        enabled: true
        timeout_checks: true
        queue_monitoring: true
      infrastructure:
        enabled: true
        node_health: true
        storage_checks: true
```

## 📚 Best Practices

### 1. Debugging Workflow
- Start with quick health checks
- Use component-specific debugging
- Apply auto-fixes cautiously
- Verify fixes thoroughly
- Document findings and solutions

### 2. Monitoring Strategy
- Enable continuous monitoring
- Set appropriate alert thresholds
- Use structured logging
- Implement health checks
- Track performance baselines

### 3. Automation Guidelines
- Automate routine debugging tasks
- Use dry-run mode for testing
- Implement approval workflows
- Monitor automation effectiveness
- Maintain human oversight

### 4. Security Considerations
- Limit debugging permissions
- Audit debug activities
- Protect sensitive data
- Use secure communication
- Follow compliance requirements

## 🔗 Related Documentation

- [AI Agents Monitoring System](AI-AGENTS-MONITORING-SYSTEM.md)
- [Agent Skills Specification](../core/ai/skills/README.md)
- [Temporal Integration Guide](comprehensive-temporal-ai-agents-guide.md)
- [Kubernetes Troubleshooting](user-guide/troubleshooting.md)
- [Deployment Guide](deployment-guide.md)

---

**Last Updated**: 2026-03-16  
**Version**: 1.0.0  
**Maintainer**: Cloud AI Agents Team

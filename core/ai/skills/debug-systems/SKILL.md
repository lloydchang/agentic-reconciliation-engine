---
name: debug-systems
description: >
  General systems debugging skill for infrastructure components, applications,
  and services. Use when troubleshooting system-level issues, performance problems,
  or general operational concerns across the infrastructure stack.
metadata:
  risk_level: low
  autonomy: fully_auto
  layer: temporal
  human_gate: Not required for read-only operations
---

# Systems Debugger

## Overview

This skill provides comprehensive debugging capabilities for general system-level issues across the entire infrastructure stack. It handles everything from application performance problems to infrastructure component failures.

## Capabilities

### Application Debugging
- Application performance analysis
- Error log analysis and pattern detection
- Resource utilization investigation
- Dependency chain analysis
- Configuration validation

### Infrastructure Component Analysis
- Service health and connectivity
- Database performance and connectivity
- Cache and storage systems
- Network and load balancer issues
- Security and authentication problems

### System Performance
- CPU, memory, and I/O analysis
- Network throughput and latency
- Storage performance metrics
- Container resource constraints
- Node-level system issues

### Operational Issues
- Service startup failures
- Configuration drift detection
- Dependency resolution problems
- Environment-specific issues
- Deployment and rollout problems

## Usage

### Basic System Health Check
```bash
python main.py debug-systems \
  --target-component application \
  --issue-type performance \
  --time-range 1h \
  --namespace production
```

### Infrastructure Component Debug
```bash
python main.py debug-systems \
  --target-component database \
  --issue-type connectivity \
  --verbose \
  --auto-fix
```

### Comprehensive System Analysis
```bash
python main.py debug-systems \
  --target-component all \
  --issue-type errors \
  --time-range 6h \
  --generate-report \
  --include-dependencies
```

## Debugging Methodology

### 1. Information Gathering
- Collect system metrics and logs
- Analyze resource utilization patterns
- Check component health status
- Gather configuration information

### 2. Pattern Analysis
- Identify error patterns and trends
- Correlate issues across components
- Detect anomalies in system behavior
- Analyze dependency relationships

### 3. Root Cause Analysis
- Trace issues through the system stack
- Identify bottlenecks and failure points
- Validate configuration and environment
- Analyze timing and sequence issues

### 4. Remediation Planning
- Generate step-by-step resolution guides
- Provide preventive measures
- Document findings and solutions
- Create monitoring recommendations

## Integration Points

### Application Monitoring
- Application performance metrics (APM)
- Custom application logs
- Health check endpoints
- Business metrics and KPIs

### Infrastructure Monitoring
- System metrics (CPU, memory, disk, network)
- Container and pod metrics
- Service mesh telemetry
- Database performance metrics

### Log Analysis
- Structured log parsing
- Error pattern detection
- Log aggregation and correlation
- Log-based alerting

### Configuration Management
- Configuration validation
- Drift detection
- Environment comparison
- Change tracking

## Auto-Fix Capabilities

When enabled, can automatically:
- Restart failing services
- Clear application caches
- Adjust resource limits
- Restart unhealthy containers
- Refresh configuration
- Clear temporary storage issues

## Safety Considerations

- Read-only operations by default
- Explicit approval required for destructive changes
- Preserves system state during analysis
- Maintains audit trail of all actions

## Output Format

Returns structured reports including:
- System health summary
- Performance analysis results
- Error analysis and patterns
- Resource utilization metrics
- Dependency analysis
- Recommended remediation steps
- Prevention strategies

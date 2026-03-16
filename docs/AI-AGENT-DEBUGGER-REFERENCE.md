# AI Agent Debugger Reference

## Overview

This reference guide provides detailed documentation for the AI Agent Debugger skill and its associated tools. It covers the skill specification, CLI usage, API endpoints, and integration patterns.

## 🎯 Skill Specification

### Skill Metadata

```yaml
name: ai-system-debugger
description: Comprehensive debugging skill for AI agents, Temporal workflows, and Kubernetes infrastructure in distributed environments
version: 1.0.0
risk_level: low
autonomy: fully_auto
action_name: debug_ai_system
```

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "target_component": {
      "type": "string",
      "enum": ["agents", "workflows", "infrastructure", "all"],
      "description": "Component to debug"
    },
    "issue_type": {
      "type": "string",
      "enum": ["performance", "errors", "timeouts", "connectivity", "resource", "behavior", "general"],
      "description": "Type of issue to investigate"
    },
    "time_range": {
      "type": "string",
      "pattern": "^\\d+[mhd]$",
      "description": "Time range for analysis (e.g., 30m, 1h, 2d)"
    },
    "namespace": {
      "type": "string",
      "default": "temporal",
      "description": "Kubernetes namespace"
    },
    "verbosity": {
      "type": "string",
      "enum": ["quiet", "normal", "verbose"],
      "default": "normal"
    },
    "auto_fix": {
      "type": "boolean",
      "default": false,
      "description": "Apply automatic fixes"
    }
  },
  "required": ["target_component", "issue_type", "time_range"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "debug_session_id": {
      "type": "string",
      "description": "Unique session identifier"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Debug session timestamp"
    },
    "target_component": {
      "type": "string",
      "description": "Component that was debugged"
    },
    "issue_type": {
      "type": "string",
      "description": "Type of issue investigated"
    },
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "component": {"type": "string"},
          "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
          "issue": {"type": "string"},
          "root_cause": {"type": "string"},
          "evidence": {"type": "array", "items": {"type": "string"}},
          "recommendations": {"type": "array", "items": {"type": "string"}}
        }
      }
    },
    "metrics_summary": {
      "type": "object",
      "properties": {
        "total_issues": {"type": "integer"},
        "critical_issues": {"type": "integer"},
        "warnings": {"type": "integer"},
        "auto_fixes_applied": {"type": "integer"}
      }
    },
    "execution_time": {
      "type": "number",
      "description": "Execution time in seconds"
    },
    "next_steps": {
      "type": "array",
      "items": {"type": "string"}
    }
  }
}
```

## 🛠️ CLI Reference

### Main CLI Commands

#### debug
```bash
python main.py debug [OPTIONS]

# Options:
#   --target-component TEXT    Component to debug [required]
#   --issue-type TEXT          Issue type [required]
#   --time-range TEXT          Time range for analysis [required]
#   --namespace TEXT           Kubernetes namespace [default: temporal]
#   --verbosity TEXT           Output verbosity [default: normal]
#   --auto-fix                 Apply automatic fixes
#   --output FILE              Save report to file
#   --dry-run                  Show what would be done without executing
#   --help                     Show help message
```

#### analyze-logs
```bash
python main.py analyze-logs [OPTIONS]

# Options:
#   --component TEXT           Component to analyze [required]
#   --pattern TEXT             Log pattern to search for [required]
#   --time-range TEXT          Time range [default: 1h]
#   --namespace TEXT           Namespace [default: temporal]
#   --output FILE              Save analysis to file
#   --help                     Show help message
```

#### profile
```bash
python main.py profile [OPTIONS]

# Options:
#   --component TEXT           Component to profile [required]
#   --duration INTEGER         Profile duration in seconds [default: 300]
#   --namespace TEXT           Namespace [default: temporal]
#   --output FILE              Save profile to file
#   --help                     Show help message
```

#### monitor
```bash
python main.py monitor [OPTIONS]

# Options:
#   --components TEXT          Components to monitor (comma-separated) [default: all]
#   --interval INTEGER         Monitoring interval in seconds [default: 300]
#   --duration INTEGER         Total monitoring duration in seconds [default: 3600]
#   --alerts TEXT              Alert destinations (comma-separated)
#   --namespace TEXT           Namespace [default: temporal]
#   --help                     Show help message
```

#### verify
```bash
python main.py verify [OPTIONS]

# Options:
#   --component TEXT           Component to verify [required]
#   --time-range TEXT          Time range for verification [default: 30m]
#   --namespace TEXT           Namespace [default: temporal]
#   --baseline FILE            Baseline file for comparison
#   --help                     Show help message
```

### Usage Examples

#### Basic Debugging
```bash
# Debug agents for errors in last hour
python main.py debug --target-component agents --issue-type errors --time-range 1h

# Debug workflows with auto-fix
python main.py debug --target-component workflows --issue-type timeouts --time-range 30m --auto-fix

# Full system analysis
python main.py debug --target-component all --issue-type performance --time-range 2h --verbose --output system-report.json
```

#### Advanced Debugging
```bash
# Dry run to see what would be fixed
python main.py debug --target-component agents --issue-type errors --time-range 1h --dry-run --auto-fix

# Specific namespace debugging
python main.py debug --target-component infrastructure --issue-type resource --namespace production --time-range 6h

# Quiet mode for automation
python main.py debug --target-component all --issue-type general --time-range 1h --verbosity quiet
```

#### Log Analysis
```bash
# Analyze error patterns
python main.py analyze-logs --component agents --pattern "ERROR|FATAL" --time-range 2h

# Find performance issues in logs
python main.py analyze-logs --component workflows --pattern "timeout|slow|latency" --time-range 1h

# Search for specific errors
python main.py analyze-logs --component infrastructure --pattern "OutOfMemory|CrashLoopBackOff"
```

#### Performance Profiling
```bash
# Profile agent performance for 10 minutes
python main.py profile --component agents --duration 600

# Profile workflow execution
python main.py profile --component workflows --duration 300 --namespace production

# Save profile to file
python main.py profile --component all --duration 900 --output performance-profile.json
```

#### Continuous Monitoring
```bash
# Monitor all components for 1 hour
python main.py monitor --components all --interval 300 --duration 3600

# Monitor specific components with alerts
python main.py monitor --components agents,workflows --interval 60 --alerts webhook:https://hooks.slack.com/...,email:admin@example.com

# Short-term monitoring
python main.py monitor --components infrastructure --interval 30 --duration 1800
```

## 📡 API Reference

### REST Endpoints

#### Debug Endpoint
```http
POST /api/v1/debug
Content-Type: application/json

{
  "target_component": "agents",
  "issue_type": "errors",
  "time_range": "1h",
  "namespace": "temporal",
  "verbosity": "normal",
  "auto_fix": false
}

Response:
{
  "debug_session_id": "debug-1678992000-abc123",
  "timestamp": "2026-03-16T12:00:00Z",
  "target_component": "agents",
  "issue_type": "errors",
  "findings": [...],
  "metrics_summary": {...},
  "execution_time": 45.2,
  "next_steps": [...]
}
```

#### Log Analysis Endpoint
```http
POST /api/v1/analyze-logs
Content-Type: application/json

{
  "component": "agents",
  "pattern": "ERROR|FATAL",
  "time_range": "1h",
  "namespace": "temporal"
}

Response:
{
  "component": "agents",
  "pattern": "ERROR|FATAL",
  "time_range": "1h",
  "matches": [...],
  "summary": {...},
  "recommendations": [...]
}
```

#### Profile Endpoint
```http
POST /api/v1/profile
Content-Type: application/json

{
  "component": "agents",
  "duration": 300,
  "namespace": "temporal"
}

Response:
{
  "component": "agents",
  "duration": 300,
  "profile_data": {...},
  "performance_metrics": {...},
  "bottlenecks": [...]
}
```

#### Monitor Endpoint
```http
POST /api/v1/monitor
Content-Type: application/json

{
  "components": ["agents", "workflows"],
  "interval": 300,
  "duration": 3600,
  "alerts": ["webhook:https://example.com/webhook"]
}

Response:
{
  "monitor_id": "monitor-1678992000-def456",
  "status": "started",
  "components": ["agents", "workflows"],
  "interval": 300,
  "duration": 3600,
  "estimated_completion": "2026-03-16T13:00:00Z"
}
```

### WebSocket Endpoints

#### Real-time Debug Stream
```javascript
const ws = new WebSocket('ws://localhost:8080/api/v1/debug/stream');

ws.onopen = function(event) {
    console.log('Connected to debug stream');
    
    // Subscribe to debug events
    ws.send(JSON.stringify({
        action: 'subscribe',
        components: ['agents', 'workflows'],
        events: ['error', 'warning', 'fix_applied']
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    handleDebugEvent(data);
};

function handleDebugEvent(event) {
    switch(event.type) {
        case 'debug_started':
            console.log(`Debug session started: ${event.session_id}`);
            break;
        case 'finding':
            console.log(`New finding: ${event.finding.issue}`);
            updateDashboard(event.finding);
            break;
        case 'fix_applied':
            console.log(`Auto-fix applied: ${event.fix.description}`);
            updateFixHistory(event.fix);
            break;
        case 'debug_completed':
            console.log(`Debug completed: ${event.session_id}`);
            displayResults(event.results);
            break;
    }
}
```

## 🔧 Configuration Reference

### Environment Variables

```bash
# Core Configuration
DEBUG_NAMESPACE=temporal
DEBUG_LOG_LEVEL=info
DEBUG_OUTPUT_FORMAT=json
DEBUG_AUTO_FIX=false

# API Configuration
DEBUG_API_HOST=0.0.0.0
DEBUG_API_PORT=8080
DEBUG_API_TLS=false

# Monitoring Configuration
DEBUG_METRICS_ENABLED=true
DEBUG_METRICS_INTERVAL=30
DEBUG_ALERTS_ENABLED=true
DEBUG_ALERT_WEBHOOK=https://example.com/webhook

# Kubernetes Configuration
DEBUG_KUBECONFIG=/path/to/kubeconfig
DEBUG_CONTEXT=current-context
DEBUG_CLUSTER_TIMEOUT=30

# Temporal Configuration
DEBUG_TEMPORAL_HOST=localhost
DEBUG_TEMPORAL_PORT=7233
DEBUG_TEMPORAL_NAMESPACE=default

# Database Configuration (if using persistent storage)
DEBUG_DATABASE_URL=postgresql://user:pass@localhost:5432/debugdb
DEBUG_DATABASE_POOL_SIZE=10
DEBUG_DATABASE_TIMEOUT=30
```

### Configuration File

```yaml
# debug-config.yaml
debug:
  namespace: temporal
  log_level: info
  output_format: json
  auto_fix: false
  
api:
  host: 0.0.0.0
  port: 8080
  tls: false
  cors_origins: ["*"]
  
monitoring:
  enabled: true
  interval: 30
  alerts: true
  metrics_retention: 7d
  
kubernetes:
  kubeconfig: /path/to/kubeconfig
  context: current-context
  cluster_timeout: 30
  
temporal:
  host: localhost
  port: 7233
  namespace: default
  
thresholds:
  error_rate: 0.1
  timeout_rate: 0.05
  restart_count: 5
  memory_usage: 0.8
  cpu_usage: 0.8
  
auto_fix:
  enabled: false
  max_retries: 3
  dry_run: false
  require_approval: false
  
components:
  agents:
    enabled: true
    auto_restart: true
    resource_checks: true
    log_analysis: true
    
  workflows:
    enabled: true
    timeout_checks: true
    queue_monitoring: true
    history_analysis: true
    
  infrastructure:
    enabled: true
    node_health: true
    storage_checks: true
    network_checks: true
    event_analysis: true
```

## 🔍 Debugging Patterns

### Error Pattern Detection

#### Common Error Patterns
```python
# Error patterns in debug_utils.py
ERROR_PATTERNS = [
    r"ERROR\s+\d+",
    r"FATAL\s+\d+",
    r"CRITICAL\s+\d+",
    r"Exception\s+.*",
    r"Traceback\s+.*",
    r"panic:\s+.*",
    r"fatal error:\s+.*"
]

WARNING_PATTERNS = [
    r"WARNING\s+\d+",
    r"WARN\s+\d+",
    r"DEPRECATED\s+.*",
    r"retrying\s+.*",
    r"backoff\s+.*"
]

PERFORMANCE_PATTERNS = [
    r"timeout.*",
    r"slow.*",
    r"latency.*",
    r"bottleneck.*",
    r"OOM\s+killed",
    r"memory.*exhausted",
    r"CPU.*throttled"
]
```

#### Pattern Matching Example
```python
def find_error_patterns(logs):
    """Find error patterns in log entries"""
    patterns = []
    
    for pattern in ERROR_PATTERNS:
        matches = re.findall(pattern, logs, re.IGNORECASE)
        if matches:
            patterns.append({
                "pattern": pattern,
                "count": len(matches),
                "samples": matches[:5]  # First 5 matches
            })
    
    return patterns
```

### Root Cause Analysis

#### Analysis Framework
```python
def analyze_root_cause(findings, metrics, logs):
    """Analyze root cause from findings, metrics, and logs"""
    root_causes = []
    
    # Check for resource issues
    if metrics.get("memory_usage", 0) > 0.8:
        root_causes.append({
            "cause": "High memory usage",
            "evidence": f"Memory usage at {metrics['memory_usage']:.1%}",
            "recommendation": "Increase memory limits or optimize memory usage"
        })
    
    # Check for network issues
    network_errors = [f for f in findings if "network" in f["issue"].lower()]
    if network_errors:
        root_causes.append({
            "cause": "Network connectivity issues",
            "evidence": f"Found {len(network_errors)} network-related errors",
            "recommendation": "Check network policies and service connectivity"
        })
    
    # Check for application errors
    app_errors = [f for f in findings if f["component"] in ["agents", "workflows"]]
    if app_errors:
        root_causes.append({
            "cause": "Application-level errors",
            "evidence": f"Found {len(app_errors)} application errors",
            "recommendation": "Review application logs and fix code issues"
        })
    
    return root_causes
```

### Auto-Fix Logic

#### Fix Decision Tree
```python
def should_apply_auto_fix(finding, config):
    """Determine if auto-fix should be applied"""
    
    # Check severity
    if finding["severity"] not in ["critical", "high"]:
        return False, "Severity too low for auto-fix"
    
    # Check component
    if finding["component"] not in config["auto_fix"]["enabled_components"]:
        return False, "Component not enabled for auto-fix"
    
    # Check fix availability
    if not get_auto_fix_for_issue(finding["issue"]):
        return False, "No auto-fix available for this issue"
    
    # Check retry count
    if finding.get("retry_count", 0) >= config["auto_fix"]["max_retries"]:
        return False, "Max retries exceeded"
    
    return True, "Auto-fix applicable"
```

#### Auto-Fix Implementation
```python
def apply_auto_fix(finding):
    """Apply automatic fix for a finding"""
    
    fix_type = determine_fix_type(finding)
    
    if fix_type == "restart_pod":
        return restart_problematic_pod(finding)
    elif fix_type == "clear_workflow":
        return clear_stuck_workflow(finding)
    elif fix_type == "adjust_resources":
        return adjust_resource_limits(finding)
    elif fix_type == "restart_service":
        return restart_service(finding)
    else:
        return {"success": False, "message": "No auto-fix available"}
```

## 📊 Metrics and Monitoring

### Debug Metrics

#### Session Metrics
```go
// Debug session metrics
type DebugSessionMetrics struct {
    SessionID         string    `json:"session_id"`
    StartTime         time.Time `json:"start_time"`
    EndTime           time.Time `json:"end_time"`
    Duration          time.Duration `json:"duration"`
    Component         string    `json:"component"`
    IssueType         string    `json:"issue_type"`
    FindingsCount     int       `json:"findings_count"`
    CriticalCount     int       `json:"critical_count"`
    AutoFixesApplied  int       `json:"auto_fixes_applied"`
    Success           bool      `json:"success"`
}
```

#### Performance Metrics
```go
// Performance metrics
type DebugPerformanceMetrics struct {
    Component         string        `json:"component"`
    ResponseTime      time.Duration `json:"response_time"`
    Throughput        float64       `json:"throughput"`
    ErrorRate         float64       `json:"error_rate"`
    ResourceUsage     ResourceUsage `json:"resource_usage"`
    LastUpdated       time.Time     `json:"last_updated"`
}
```

### Alert Integration

#### Alert Configuration
```yaml
alerts:
  - name: "High Error Rate"
    condition: "error_rate > 0.1"
    severity: "critical"
    message: "Error rate is {{.value}} (threshold: {{.threshold}})"
    actions:
      - type: "auto_fix"
        component: "agents"
      - type: "notification"
        webhook: "https://hooks.slack.com/..."
        
  - name: "Workflow Timeouts"
    condition: "timeout_rate > 0.05"
    severity: "warning"
    message: "Workflow timeout rate is {{.value}}"
    actions:
      - type: "auto_fix"
        component: "workflows"
      - type: "escalation"
        delay: "5m"
```

## 🧪 Testing and Validation

### Unit Tests

#### Test Structure
```python
# test_debugger.py
class TestAISystemDebugger:
    def test_debug_agents(self):
        """Test agent debugging functionality"""
        debugger = AISystemDebugger(namespace="test")
        findings = debugger.debug_agents("errors", "1h")
        
        assert len(findings) > 0
        assert all(finding.component == "agents" for finding in findings)
    
    def test_debug_workflows(self):
        """Test workflow debugging functionality"""
        debugger = AISystemDebugger(namespace="test")
        findings = debugger.debug_workflows("timeouts", "30m")
        
        assert len(findings) > 0
        assert all(finding.component == "workflows" for finding in findings)
    
    def test_auto_fix(self):
        """Test auto-fix functionality"""
        debugger = AISystemDebugger(namespace="test", auto_fix=True)
        
        # Create mock finding
        finding = DebugFinding(
            component="agents",
            severity="critical",
            issue="Pod restart loop",
            root_cause="Memory exhaustion"
        )
        
        fix_applied = debugger.apply_auto_fix(finding)
        assert fix_applied is True
```

### Integration Tests

#### Test Scenarios
```python
# integration_tests.py
class TestDebuggingIntegration:
    def test_end_to_end_debugging(self):
        """Test complete debugging workflow"""
        # Setup test environment
        setup_test_cluster()
        
        # Run debugging
        result = run_debug_command(
            component="all",
            issue_type="performance",
            time_range="1h",
            auto_fix=False
        )
        
        # Verify results
        assert result["success"] is True
        assert "findings" in result
        assert len(result["findings"]) > 0
    
    def test_auto_fix_workflow(self):
        """Test auto-fix workflow"""
        # Create failing pod
        create_failing_pod()
        
        # Run debugging with auto-fix
        result = run_debug_command(
            component="agents",
            issue_type="errors",
            time_range="30m",
            auto_fix=True
        )
        
        # Verify fix applied
        assert result["metrics_summary"]["auto_fixes_applied"] > 0
        assert pod_is_running()
```

### Performance Tests

#### Load Testing
```python
# performance_tests.py
class TestDebuggingPerformance:
    def test_large_scale_debugging(self):
        """Test debugging with many components"""
        # Setup large cluster
        setup_large_cluster(pods=1000)
        
        # Run debugging
        start_time = time.time()
        result = run_debug_command(
            component="all",
            issue_type="performance",
            time_range="1h"
        )
        duration = time.time() - start_time
        
        # Verify performance
        assert duration < 300  # Should complete within 5 minutes
        assert result["success"] is True
    
    def test_concurrent_debugging(self):
        """Test concurrent debugging sessions"""
        # Run multiple debugging sessions
        sessions = []
        for i in range(10):
            session = run_debug_command_async(
                component="agents",
                issue_type="errors",
                time_range="30m"
            )
            sessions.append(session)
        
        # Wait for completion
        results = [session.result() for session in sessions]
        
        # Verify all succeeded
        assert all(result["success"] for result in results)
```

## 🔗 Integration Examples

### Temporal Workflow Integration

#### Debuggable Workflow
```go
func DebuggableWorkflow(ctx workflow.Context, request WorkflowRequest) (*WorkflowResult, error) {
    logger := workflow.GetLogger(ctx)
    
    // Initialize debug session
    debugSession := &DebugSession{
        WorkflowID: workflow.GetInfo(ctx).WorkflowExecution.ID,
        StartTime:  workflow.Now(ctx),
        Component: "workflows",
        IssueType: "general",
    }
    
    // Record workflow start
    if err := recordDebugStart(ctx, debugSession); err != nil {
        logger.Warn("Failed to record debug start", "error", err)
    }
    
    // Execute workflow with debug tracking
    result, err := ExecuteWithDebugTracking(ctx, request, debugSession)
    if err != nil {
        // Record error for debugging
        recordDebugError(ctx, debugSession, err)
        return nil, err
    }
    
    // Record workflow completion
    debugSession.EndTime = workflow.Now(ctx)
    recordDebugCompletion(ctx, debugSession)
    
    return result, nil
}
```

### Kubernetes Operator Integration

#### Debug Controller
```go
// DebugController monitors and debugs Kubernetes resources
type DebugController struct {
    client.Client
    Scheme     *runtime.Scheme
    Debugger   *AISystemDebugger
}

func (r *DebugController) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    // Get the resource
    var pod corev1.Pod
    if err := r.Get(ctx, req.NamespacedName, &pod); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }
    
    // Check if debugging is needed
    if r.shouldDebug(&pod) {
        // Run debugging
        findings := r.Debugger.debugPod(&pod)
        
        // Apply auto-fixes if enabled
        if r.Debugger.AutoFix {
            for _, finding := range findings {
                r.applyAutoFix(ctx, &pod, finding)
            }
        }
    }
    
    return ctrl.Result{}, nil
}
```

### Monitoring System Integration

#### Metrics Collector
```go
func (dc *DebugCollector) CollectDebugMetrics(ch chan<- prometheus.Metric) {
    // Collect debug session metrics
    debugSessions := dc.getDebugSessions()
    
    for _, session := range debugSessions {
        ch <- prometheus.MustNewConstMetric(
            debugSessionDurationDesc,
            prometheus.GaugeValue,
            session.Duration.Seconds(),
            session.Component,
            session.IssueType,
        )
        
        ch <- prometheus.MustNewConstMetric(
            debugFindingsCountDesc,
            prometheus.GaugeValue,
            float64(session.FindingsCount),
            session.Component,
            session.Severity,
        )
    }
}
```

---

**Last Updated**: 2026-03-16  
**Version**: 1.0.0  
**Maintainer**: Cloud AI Agents Team

# AI System Debugger

Comprehensive debugging skill for AI agents, Temporal workflows, and Kubernetes infrastructure in distributed environments.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- kubectl configured for your cluster
- Access to the temporal namespace
- Optional: temporal-cli for advanced workflow debugging

### Installation

```bash
# Navigate to the debugger directory
cd .agents/ai-system-debugger/scripts

# Install dependencies
pip install -r requirements.txt  # or let PEP 723 handle it automatically

# Make the shell script executable
chmod +x quick_debug.sh
```

### Basic Usage

```bash
# Quick agent debugging with auto-fix
./quick_debug.sh agents errors true

# Comprehensive Python-based debugging
python main.py debug \
  --target-component all \
  --issue-type performance \
  --time-range 2h \
  --namespace temporal \
  --verbose \
  --auto-fix

# Generate debug report
python main.py debug \
  --target-component workflows \
  --issue-type timeouts \
  --output debug-report.json
```

## 📊 Debugging Components

### 1. AI Agents Debugging
- Pod status and restart analysis
- Agent execution log analysis
- Resource utilization monitoring
- Skill execution error tracking
- Performance bottleneck identification

### 2. Temporal Workflows Debugging
- Workflow execution history
- Activity timeout analysis
- Task queue health monitoring
- Workflow correlation and tracing
- Stuck workflow detection

### 3. Kubernetes Infrastructure Debugging
- Node health and resource availability
- Storage and network issues
- Service connectivity validation
- Resource quota and limit analysis
- Event-driven problem detection

## 🔧 Advanced Features

### Auto-Fix Capabilities
When `--auto-fix` is enabled, the debugger can:
- Restart failing pods automatically
- Clear stuck workflows
- Adjust resource limits
- Restart unhealthy agents
- Clear temporary cache issues

### Real-time Monitoring
- Live metrics streaming from monitoring endpoints
- WebSocket-based progress updates
- Alert integration and notification
- Performance trend analysis

### Distributed System Support
- Multi-cluster debugging capabilities
- Namespace isolation handling
- Remote log aggregation
- Cross-component correlation

## 📈 Integration Points

### Monitoring System
The debugger integrates with your existing monitoring infrastructure:
- Metrics API: `/monitoring/metrics`
- Alerts API: `/monitoring/alerts`
- Health Checks: `/health`
- Audit Logs: `/audit/events`

### Temporal Integration
- Workflow History API access
- Activity execution monitoring
- Task queue status tracking
- Worker health validation

### Kubernetes Integration
- Pod lifecycle management
- Service discovery validation
- Resource utilization tracking
- Network policy analysis

## 🛠️ Development and Testing

### Running Tests
```bash
# Run the test suite
cd scripts
python test_debugger.py

# Run with pytest for more options
pytest test_debugger.py -v --tb=short
```

### Development Setup
```bash
# Install development dependencies
pip install pytest pytest-asyncio kubernetes requests pydantic

# Run in development mode
python main.py debug --target-component agents --issue-type errors --verbose
```

## 📋 Common Debugging Scenarios

### Scenario 1: Agent Pod Failures
```bash
# Quick diagnosis
./quick_debug.sh agents errors false

# Detailed analysis
python main.py debug \
  --target-component agents \
  --issue-type errors \
  --time-range 1h \
  --verbose
```

### Scenario 2: Workflow Timeouts
```bash
# Workflow-specific debugging
python main.py debug \
  --target-component workflows \
  --issue-type timeouts \
  --time-range 30m \
  --auto-fix
```

### Scenario 3: Performance Issues
```bash
# Performance analysis
python main.py debug \
  --target-component all \
  --issue-type performance \
  --time-range 2h \
  --output performance-report.json
```

### Scenario 4: Infrastructure Health
```bash
# Infrastructure check
./quick_debug.sh infrastructure general false

# Full infrastructure analysis
python main.py debug \
  --target-component infrastructure \
  --issue-type resource \
  --namespace temporal
```

## 📊 Output Formats

### Console Output
The debugger provides rich console output with:
- Color-coded severity levels
- Progress indicators for long operations
- Structured findings with evidence
- Actionable recommendations

### JSON Reports
When using `--output`, the debugger generates comprehensive JSON reports:
```json
{
  "debug_session_id": "uuid",
  "findings": [
    {
      "component": "agents",
      "severity": "critical",
      "issue": "Agent pod restart loop",
      "root_cause": "Memory exhaustion",
      "evidence": ["Pod restarted 5 times in 10 minutes"],
      "recommendations": ["Increase memory limits", "Investigate memory leaks"]
    }
  ],
  "metrics_summary": {
    "total_issues": 3,
    "critical_issues": 1,
    "warnings": 2,
    "auto_fixes_applied": 0
  },
  "execution_time": 45.2,
  "next_steps": ["Address critical issues", "Monitor applied fixes"]
}
```

## 🔍 Troubleshooting the Debugger

### Common Issues

1. **kubectl not found**
   ```bash
   # Install kubectl
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"
   chmod +x kubectl && sudo mv kubectl /usr/local/bin/
   ```

2. **Permission denied accessing cluster**
   ```bash
   # Check kubeconfig
   kubectl config current-context
   kubectl cluster-info
   ```

3. **Monitoring endpoints not reachable**
   ```bash
   # Check service status
   kubectl get svc -n temporal
   kubectl port-forward svc/temporal-worker 8080:8080 -n temporal
   ```

### Debug Mode
Enable verbose logging for troubleshooting:
```bash
python main.py debug --target-component agents --issue-type errors --verbose
```

## 🚀 Production Deployment

### Kubernetes Deployment
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: ai-debugger
  namespace: temporal
spec:
  template:
    spec:
      serviceAccountName: temporal-worker-sa
      containers:
      - name: debugger
        image: your-registry/ai-debugger:latest
        command: ["python", "main.py", "debug"]
        args:
        - "--target-component"
        - "all"
        - "--issue-type"
        - "performance"
        - "--auto-fix"
        env:
        - name: NAMESPACE
          value: "temporal"
      restartPolicy: Never
```

### Scheduled Debugging
Create a CronJob for regular health checks:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: ai-debugger-scheduled
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
            command: ["python", "main.py", "debug"]
            args: ["--target-component", "all", "--issue-type", "general"]
          restartPolicy: OnFailure
```

## 🤝 Contributing

### Adding New Debugging Capabilities
1. Create new functions in `debug_utils.py`
2. Add corresponding CLI options in `main.py`
3. Write tests in `test_debugger.py`
4. Update documentation

### Testing
```bash
# Run all tests
pytest test_debugger.py -v

# Run specific test
pytest test_debugger.py::TestAISystemDebugger::test_debug_agents -v
```

## 📚 Related Documentation

- [Agent Skills Specification](https://agentskills.io/specification)
- [Temporal Documentation](https://docs.temporal.io/)
- [Kubernetes Troubleshooting](https://kubernetes.io/docs/tasks/debug-application-cluster/)
- [AI Agents Architecture](../../AGENTS.md)

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the debug logs with `--verbose`
3. Check the memory knowledge base
4. Review the skill execution logs

---

**Built with ❤️ following the Agent Skills Specification and Kubernetes best practices.**

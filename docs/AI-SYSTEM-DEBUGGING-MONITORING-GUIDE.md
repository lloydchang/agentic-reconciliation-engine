# AI System Debugging and Monitoring Guide

## Overview

This guide provides comprehensive debugging strategies for distributed AI agent systems running in Kubernetes with Temporal orchestration. It covers monitoring endpoints, debugging methodologies, common issue patterns, and auto-fix capabilities.

## Key Components

- **AI Agents**: Go-based Temporal workers with 91 skills
- **Temporal Workflows**: Orchestration layer for agent coordination  
- **Kubernetes Infrastructure**: Distributed deployment environment
- **Monitoring System**: Built-in metrics collection and alerting
- **Crossplane Integration**: Infrastructure management with Kubernetes provider

## Quick Debug Commands

### Fast Agent Debugging

```bash
# Fast agent debugging
./core/scripts/automation/quick_debug.sh agents errors true

# Full system analysis
python core/ai/skills/ai-system-debugger/scripts/main.py debug --target-component all --issue-type performance --time-range 2h --auto-fix

# Infrastructure health check
kubectl get pods -n temporal -l app=temporal-worker
kubectl logs -n temporal deployment/temporal-worker --since=1h | grep ERROR
```

### Component-Specific Debugging

```bash
# Memory agents debugging
kubectl get pods -n ai-infrastructure -l component=agent-memory
kubectl logs -n ai-infrastructure deployment/agent-memory-rust --tail=100

# Temporal debugging
kubectl get pods -n ai-infrastructure -l app=temporal
kubectl logs -n ai-infrastructure deployment/temporal --tail=100

# Crossplane debugging
kubectl get providers -n crossplane-system
kubectl logs -n crossplane-system deployment/crossplane --tail=100

# Flux debugging
kubectl get pods -n flux-system
kubectl logs -n flux-system deployment/kustomize-controller --tail=100
```

## Monitoring Endpoints

### Built-in Monitoring

- **Metrics**: `http://temporal-worker.temporal.svc.cluster.local:8080/monitoring/metrics`
- **Alerts**: `http://temporal-worker.temporal.svc.cluster.local:8080/monitoring/alerts`
- **Health**: `http://temporal-worker.temporal.svc.cluster.local:8080/health`
- **Audit**: `http://temporal-worker.temporal.svc.cluster.local:8080/audit/events`

### Dashboard Access

```bash
# AI Agents Dashboard
kubectl port-forward -n ai-infrastructure svc/agent-dashboard-service 8080:80
open http://localhost:8080

# Temporal UI
kubectl port-forward -n ai-infrastructure svc/temporal-frontend 7233:7233
open http://localhost:7233

# Crossplane UI (if available)
kubectl port-forward -n crossplane-system svc/crossplane-webhook-service 8081:80
```

### API Endpoints

```bash
# Cluster status
curl http://localhost:5000/api/cluster-status

# Agent status
curl http://localhost:5000/api/core/ai/runtime/status

# System metrics
curl http://localhost:5000/api/metrics
```

## Common Issue Patterns

### 1. Agent Failures

**Symptoms:**
- Pod restarts
- Skill execution errors
- Resource exhaustion
- Memory leaks

**Debugging Steps:**
```bash
# Check agent pod status
kubectl get pods -n ai-infrastructure -l component=agent-memory

# Check resource usage
kubectl top pods -n ai-infrastructure

# Check agent logs for errors
kubectl logs -n ai-infrastructure deployment/agent-memory-rust --previous

# Check events
kubectl get events -n ai-infrastructure --sort-by='.lastTimestamp'
```

**Common Causes:**
- Memory limits too low
- Model loading failures
- Network connectivity issues
- Storage problems

### 2. Workflow Timeouts

**Symptoms:**
- Long-running activities
- Stuck workflows
- Queue issues
- Deadlock situations

**Debugging Steps:**
```bash
# Check workflow status
kubectl exec -n ai-infrastructure deployment/temporal -- temporal workflow list

# Check activity history
kubectl exec -n ai-infrastructure deployment/temporal -- temporal activity list

# Check Temporal logs
kubectl logs -n ai-infrastructure deployment/temporal | grep -i timeout

# Check queue depth
kubectl exec -n ai-infrastructure deployment/temporal -- temporal task-queue list
```

**Solutions:**
- Increase timeout values
- Check activity resource limits
- Verify external service connectivity
- Clear stuck workflows

### 3. Infrastructure Issues

**Symptoms:**
- Node failures
- Storage issues
- Network problems
- DNS resolution failures

**Debugging Steps:**
```bash
# Check cluster health
kubectl get nodes
kubectl get componentstatuses

# Check storage
kubectl get pv,pvc --all-namespaces

# Check network
kubectl get pods -o wide
kubectl get services -o wide

# Check DNS
kubectl exec -n ai-infrastructure deployment/agent-memory-rust -- nslookup kubernetes.default.svc.cluster.local
```

### 4. Performance Issues

**Symptoms:**
- High CPU/memory usage
- Slow inference
- Bottlenecks
- Resource contention

**Debugging Steps:**
```bash
# Monitor resource usage
kubectl top nodes
kubectl top pods -n ai-infrastructure

# Check performance metrics
curl http://localhost:8080/monitoring/metrics | grep -i performance

# Profile memory usage
kubectl exec -n ai-infrastructure deployment/agent-memory-rust -- ps aux

# Check inference performance
kubectl logs -n ai-infrastructure deployment/agent-memory-rust | grep -i inference
```

## Auto-Fix Capabilities

### Built-in Auto-Fix Scripts

The system includes automatic recovery mechanisms:

```bash
# Restart failing pods
python core/ai/skills/ai-system-debugger/scripts/main.py auto-fix --target=pods --condition=failing

# Clear stuck workflows
python core/ai/skills/ai-system-debugger/scripts/main.py auto-fix --target=workflows --condition=stuck

# Adjust resource limits
python core/ai/skills/ai-system-debugger/scripts/main.py auto-fix --target=resources --condition=exhausted

# Restart unhealthy agents
python core/ai/skills/ai-system-debugger/scripts/main.py auto-fix --target=agents --condition=unhealthy
```

### Kubernetes Self-Healing

```yaml
# Liveness and readiness probes
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-memory-rust
  namespace: ai-infrastructure
spec:
  template:
    spec:
      containers:
      - name: agent-memory
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

## Prevention Strategies

### 1. Monitoring and Alerting

```bash
# Set up monitoring
kubectl apply -f monitoring/prometheus-config.yaml
kubectl apply -f monitoring/grafana-dashboard.yaml

# Configure alerts
kubectl apply -f monitoring/alert-rules.yaml
```

### 2. Resource Management

```yaml
# Resource limits and requests
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### 3. Health Checks

```bash
# Implement health check endpoints
# GET /health - Basic health status
# GET /ready - Readiness status
# GET /metrics - Performance metrics
# GET /debug - Debug information
```

### 4. Structured Logging

```bash
# Configure structured logging with correlation IDs
kubectl logs -n ai-infrastructure deployment/agent-memory-rust -f | jq '.correlation_id, .level, .message'
```

## Critical Files and Locations

### AI System Debugger

- [core/ai/skills/ai-system-debugger/SKILL.md](core/ai/skills/ai-system-debugger/SKILL.md) - Debugging skill definition
- `core/ai/skills/ai-system-debugger/scripts/main.py` - Main debugging CLI
- `core/ai/skills/ai-system-debugger/scripts/debug_utils.py` - Debug utilities
- `core/ai/skills/ai-system-debugger/scripts/quick_debug.sh` - Quick bash debugging

### Monitoring System

- `ai-core/ai/runtime/backend/monitoring/metrics.go` - Built-in monitoring system
- `monitoring/prometheus-config.yaml` - Prometheus configuration
- `monitoring/grafana-dashboard.json` - Grafana dashboard

### Deployment Scripts

- `core/scripts/automation/deploy-ai-agents-ecosystem.sh` - Main deployment script
- `core/scripts/automation/quick_debug.sh` - Quick debugging utility
- `core/scripts/automation/health-check.sh` - System health validation

## Integration Points

### Temporal Workflow Integration

```bash
# Monitor workflow execution
kubectl exec -n ai-infrastructure deployment/temporal -- temporal workflow describe --workflow-id <id>

# Check activity execution
kubectl exec -n ai-infrastructure deployment/temporal -- temporal activity describe --activity-id <id>

# View workflow history
kubectl exec -n ai-infrastructure deployment/temporal -- temporal workflow history --workflow-id <id>
```

### Kubernetes API Integration

```bash
# Monitor pod status
kubectl get pods -n ai-infrastructure -w

# Check service endpoints
kubectl get endpoints -n ai-infrastructure

# Monitor resource quotas
kubectl get resourcequota -n ai-infrastructure
```

### Custom Monitoring Endpoints

```bash
# Real-time metrics
curl http://localhost:8080/monitoring/metrics | grep temporal_workflow_duration

# System health
curl http://localhost:8080/health | jq

# Agent status
curl http://localhost:8080/api/agents | jq '.[] | select(.status != "healthy")'
```

### Audit Logging

```bash
# View audit events
curl http://localhost:8080/audit/events | jq '.[] | select(.timestamp > "2024-01-01")'

# Monitor security events
curl http://localhost:8080/audit/events | jq '.[] | select(.type == "security")'
```

## Distributed System Considerations

### Namespace Isolation

```bash
# Check namespace resource usage
kubectl describe namespace ai-infrastructure

# Monitor cross-namespace communication
kubectl get networkpolicy -n ai-infrastructure

# Validate RBAC permissions
kubectl auth can-i create pods --namespace ai-infrastructure --as=system:serviceaccount:ai-infrastructure:agent-memory-sa
```

### Multi-Cluster Support

```bash
# Check cluster connectivity
kubectl config get-contexts

# Monitor cross-cluster workflows
kubectl exec -n ai-infrastructure deployment/temporal -- temporal workflow list --query='{"ClusterID": "remote-cluster"}'

# Validate cluster federation
kubectl get clusters -n gitops-system
```

### Network Connectivity

```bash
# Test service connectivity
kubectl exec -n ai-infrastructure deployment/agent-memory-rust -- wget -qO- http://temporal-frontend:7233

# Check DNS resolution
kubectl exec -n ai-infrastructure deployment/agent-memory-rust -- nslookup temporal-frontend.ai-infrastructure.svc.cluster.local

# Monitor network policies
kubectl get networkpolicy -n ai-infrastructure -o yaml
```

### Remote Log Aggregation

```bash
# Configure centralized logging
kubectl apply -f logging/fluentd-config.yaml
kubectl apply -f logging/elasticsearch-config.yaml

# View aggregated logs
curl http://elasticsearch.logging.svc.cluster.local:9200/logs-*/_search?pretty

# Monitor log quality
curl http://elasticsearch.logging.svc.cluster.local:9200/logs-*/_count | jq
```

### Cross-Component Dependencies

```bash
# Map component dependencies
kubectl get pods -n ai-infrastructure -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .spec.containers[*]}{.name}{" "}{end}{"\n"}{end}'

# Check service dependencies
kubectl get services -n ai-infrastructure -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.selector}{"\n"}{end}'

# Validate dependency health
kubectl exec -n ai-infrastructure deployment/agent-memory-rust -- curl -f http://temporal-frontend:7233/health
```

## Advanced Debugging Techniques

### 1. Distributed Tracing

```bash
# Enable tracing in agents
kubectl patch deployment agent-memory-rust -n ai-infrastructure -p '{"spec":{"template":{"spec":{"containers":[{"name":"agent-memory","env":[{"name":"JAEGER_ENDPOINT","value":"http://jaeger-collector:14268"}]}]}}}}'

# View traces
open http://localhost:16686
```

### 2. Performance Profiling

```bash
# Enable pprof in Go agents
kubectl exec -n ai-infrastructure deployment/agent-memory-go -- curl http://localhost:6060/debug/pprof/profile > cpu.prof

# Analyze with go tool
go tool pprof cpu.prof
```

### 3. Memory Debugging

```bash
# Check memory usage
kubectl exec -n ai-infrastructure deployment/agent-memory-rust -- ps aux --sort=-%mem

# Dump heap profile
kubectl exec -n ai-infrastructure deployment/agent-memory-go -- curl http://localhost:6060/debug/pprof/heap > heap.prof

# Analyze memory leaks
go tool pprof heap.prof
```

### 4. Network Debugging

```bash
# Capture network traffic
kubectl exec -n ai-infrastructure deployment/agent-memory-rust -- tcpdump -i any -w /tmp/capture.pcap

# Analyze with Wireshark
kubectl cp ai-core/resources/agent-memory-rust-xxx:/tmp/capture.pcap ./capture.pcap
```

## Troubleshooting Checklist

### System Health

- [ ] All pods running and ready
- [ ] Services accessible and responding
- [ ] Resource usage within limits
- [ ] No persistent storage issues
- [ ] Network connectivity working

### AI Agents

- [ ] Memory agents responding to health checks
- [ ] Temporal workflows executing properly
- [ ] Skills framework operational
- [ ] Inference backend working
- [ ] Dashboard accessible

### GitOps Infrastructure

- [ ] Flux reconciling properly
- [ ] Crossplane providers healthy
- [ ] Cluster API functional
- [ ] Git repositories syncing
- [ ] Resource drift detection working

### Monitoring and Logging

- [ ] Metrics collection working
- [ ] Alert rules firing appropriately
- [ ] Log aggregation functional
- [ ] Audit trails complete
- [ ] Performance data available

## Emergency Procedures

### System Recovery

```bash
# Full system restart
kubectl rollout restart deployment -n ai-infrastructure
kubectl rollout restart deployment -n flux-system
kubectl rollout restart deployment -n crossplane-system

# Clear stuck workflows
kubectl exec -n ai-infrastructure deployment/temporal -- temporal workflow terminate --workflow-id <id>

# Reset persistent storage
kubectl delete pvc -n ai-infrastructure --all
kubectl apply -f core/resources/storage/
```

### Disaster Recovery

```bash
# Restore from backup
kubectl apply -f backups/ai-agents-backup.yaml

# Recreate cluster
kind delete cluster gitops-hub
./core/scripts/automation/create-hub-cluster.sh --provider kind

# Redeploy everything
./core/scripts/automation/quickstart.sh
```

## Conclusion

This comprehensive debugging and monitoring guide provides the tools and methodologies needed to maintain a healthy AI agents ecosystem. By following the prevention strategies and using the automated debugging capabilities, teams can ensure reliable operation of their distributed AI systems.

The integration of Temporal orchestration, Kubernetes infrastructure, and custom monitoring creates a robust foundation for autonomous cloud operations with full observability and debugging capabilities.

## References

- [Temporal Debugging Guide](https://docs.temporal.io/debugging)
- [Kubernetes Debugging](https://kubernetes.io/docs/tasks/debug-application-cluster/)
- [Prometheus Monitoring](https://prometheus.io/docs/practices/)
- [AI Agents Architecture](docs/AI-AGENTS-ARCHITECTURE.md)
- [Crossplane Local Development](docs/CROSSPLANE-LOCAL-DEVELOPMENT.md)

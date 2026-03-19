# AI System Debugging Guide

## Overview

This guide documents comprehensive debugging strategies for distributed AI agent systems running in Kubernetes with Temporal orchestration. It covers methodology, tools, and best practices for troubleshooting complex distributed systems.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Debugging Methodology](#debugging-methodology)
3. [Common Issue Patterns](#common-issue-patterns)
4. [Quick Debug Commands](#quick-debug-commands)
5. [Monitoring Endpoints](#monitoring-endpoints)
6. [Auto-Fix Capabilities](#auto-fix-capabilities)
7. [Prevention Strategies](#prevention-strategies)
8. [Critical Files](#critical-files)

## System Architecture

### Core Components

- **AI Agents**: Go-based Temporal workers with 92 skills
- **Temporal Workflows**: Orchestration layer for agent coordination
- **Kubernetes Infrastructure**: Distributed deployment environment
- **Monitoring System**: Built-in metrics collection and alerting

### Key Technologies

- **Temporal**: Workflow orchestration and durable execution
- **Kubernetes**: Container orchestration and service management
- **PostgreSQL**: Database for Temporal persistence
- **Prometheus/Grafana**: Metrics collection and visualization
- **ELK Stack**: Log aggregation and analysis

## Debugging Methodology

### 1. Infrastructure First Approach

Always start with infrastructure health checks before diving into application issues:

```bash
# Check Kubernetes cluster health
kubectl get nodes
kubectl get pods --all-namespaces

# Check Temporal server status
kubectl get pods -n ai-infrastructure -l app=temporal-server

# Check agent worker status
kubectl get pods -n ai-infrastructure -l app=temporal-workers
```

### 2. Layer-by-Layer Investigation

1. **Network Layer**: Service connectivity and DNS resolution
2. **Database Layer**: Connection pools and schema integrity
3. **Application Layer**: Business logic and error handling
4. **Orchestration Layer**: Workflow coordination and task distribution

### 3. Log Correlation

Use structured logging with correlation IDs to trace requests across services:

```bash
# Search for correlation ID across all services
kubectl logs -n ai-infrastructure --selector=app=temporal-server --grep="<correlation-id>"
kubectl logs -n ai-infrastructure --selector=app=temporal-workers --grep="<correlation-id>"
```

## Common Issue Patterns

### Agent Failures

**Symptoms:**
- Pod restarts with exit code 1
- Skill execution errors
- Resource exhaustion (CPU/memory)

**Debug Commands:**
```bash
# Check pod restart reasons
kubectl get pods -n ai-infrastructure -l app=temporal-workers
kubectl describe pod <temporal-worker-pod-name> -n ai-infrastructure

# Check resource usage
kubectl top pods -n ai-infrastructure
```

### Workflow Timeouts

**Symptoms:**
- Long-running activities stuck
- Queue backlogs
- Failed workflow executions

**Debug Commands:**
```bash
# Check Temporal workflow status
temporal workflow list --namespace default

# Check queue depth
temporal task-queue describe --task-queue cloud-ai-task-queue
```

### Infrastructure Issues

**Symptoms:**
- Node failures
- Storage issues
- Network connectivity problems

**Debug Commands:**
```bash
# Check node status
kubectl get nodes
kubectl describe node <node-name>

# Check persistent volume claims
kubectl get pvc -n ai-infrastructure
kubectl describe pvc <pvc-name> -n ai-infrastructure
```

### Performance Bottlenecks

**Symptoms:**
- High CPU/memory usage
- Slow inference times
- Queue processing delays

**Debug Commands:**
```bash
# Check resource usage patterns
kubectl top nodes
kubectl top pods -n ai-infrastructure

# Check Temporal metrics
curl http://temporal-server:9090/metrics
```

## Quick Debug Commands

### Fast Agent Debugging

```bash
# Quick health check
./quick_debug.sh agents errors true

# Check all agent pods
kubectl get pods -n ai-infrastructure -l app=temporal-workers
```

### Full System Analysis

```bash
# Comprehensive analysis
python main.py debug --target-component all --issue-type performance --time-range 2h --auto-fix

# Infrastructure health check
kubectl get pods -n temporal -l app=temporal-worker
kubectl logs -n temporal deployment/temporal-worker --since=1h | grep ERROR
```

## Monitoring Endpoints

### Temporal Server Metrics

- **Metrics**: `http://temporal-server.ai-infrastructure.svc.cluster.local:9090/metrics`
- **Health**: `http://temporal-server.ai-infrastructure.svc.cluster.local:9090/health`
- **Workflow Status**: Temporal CLI or web UI

### Agent Worker Metrics

- **Metrics**: `http://temporal-worker.ai-infrastructure.svc.cluster.local:8080/monitoring/metrics`
- **Alerts**: `http://temporal-worker.ai-infrastructure.svc.cluster.local:8080/monitoring/alerts`
- **Health**: `http://temporal-worker.ai-infrastructure.svc.cluster.local:8080/health`
- **Audit**: `http://temporal-worker.ai-infrastructure.svc.cluster.local:8080/audit/events`

### Dashboard Metrics

- **API Metrics**: `http://localhost:8080/api/metrics`
- **Agent Status**: `http://localhost:8080/api/agents`
- **Skill Metrics**: `http://localhost:8080/api/skills`

## Auto-Fix Capabilities

### Automated Recovery Actions

1. **Restart Failing Pods**
   ```bash
   kubectl rollout restart deployment/temporal-workers -n ai-infrastructure
   ```

2. **Clear Stuck Workflows**
   ```bash
   temporal workflow terminate --workflow-id <workflow-id>
   ```

3. **Adjust Resource Limits**
   ```bash
   kubectl patch deployment temporal-workers -n ai-infrastructure \
     --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/cpu", "value": "1000m"}]'
   ```

4. **Restart Unhealthy Agents**
   ```bash
   kubectl delete pod <unhealthy-pod> -n ai-infrastructure
   ```

### Smart Recovery Logic

- **Circuit Breaker Pattern**: Automatically isolate failing components
- **Graceful Degradation**: Continue with reduced functionality
- **Self-Healing**: Automatic pod restarts and rescheduling

## Prevention Strategies

### Monitoring and Alerting

- Monitor error rates and restart counts
- Set appropriate resource limits and requests
- Implement health checks and readiness probes
- Use structured logging with correlation IDs

### Capacity Planning

- Monitor resource usage trends
- Implement horizontal pod autoscaling
- Plan for peak load scenarios
- Regular performance testing

### Operational Excellence

- **Runbooks**: Documented procedures for common issues
- **Playbooks**: Automated response to known failure patterns
- **On-call Rotation**: 24/7 coverage for critical systems
- **Incident Response**: Clear escalation procedures

## Critical Files

### Debugging Skills

- `.agents/ai-system-debugger/SKILL.md` - Debugging skill definition
- `.agents/ai-system-debugger/scripts/main.py` - Main debugging CLI
- `.agents/ai-system-debugger/scripts/debug_utils.py` - Debug utilities
- `.agents/ai-system-debugger/scripts/quick_debug.sh` - Quick bash debugging

### Monitoring System

- `ai-agents/backend/monitoring/metrics.go` - Built-in monitoring system
- `core/deployment/manifests/monitoring/` - Monitoring stack configurations

### Configuration Files

- `core/resources/infrastructure/temporal/` - Temporal infrastructure manifests
- `core/ai/runtime/agents/backend/` - Agent backend configurations
- `core/deployment/manifests/dashboard/` - Dashboard and API configurations

## Integration Points

### Temporal Workflow History

- Activity logs and workflow execution traces
- Task queue status and backlog monitoring
- Namespace isolation and resource allocation

### Kubernetes API Integration

- Pod lifecycle management and health monitoring
- Service discovery and load balancing
- ConfigMap and Secret management

### Custom Monitoring Endpoints

- Real-time metrics collection and aggregation
- Alert generation and notification routing
- Performance profiling and bottleneck analysis

## Distributed System Considerations

### Namespace Isolation

- Multi-namespace deployments with shared policies
- Network policies for secure communication
- Resource quotas and limits per namespace

### Cross-Cluster Support

- Federation for multi-cluster deployments
- Service mesh integration (Istio/Linkerd)
- Global load balancing and failover

### Log Aggregation

- Centralized logging with correlation IDs
- Distributed tracing across service boundaries
- Real-time log analysis and alerting

## Troubleshooting Playbook

### High-Level Issues

1. **System Unresponsive**
   - Check cluster health and node status
   - Verify network connectivity between services
   - Check database connectivity and performance

2. **Slow Performance**
   - Analyze resource usage and bottlenecks
   - Check queue depths and processing rates
   - Review recent deployments and configuration changes

3. **Data Inconsistencies**
   - Verify database schema and migration status
   - Check data replication and synchronization
   - Review backup and recovery procedures

### Component-Specific Issues

1. **Temporal Server Problems**
   - Check PostgreSQL connectivity and schema version
   - Verify service account permissions
   - Review Temporal configuration parameters

2. **Agent Worker Issues**
   - Check Temporal server connectivity
   - Verify skill loading and execution
   - Review resource allocation and limits

3. **Dashboard Issues**
   - Check API endpoint connectivity
   - Verify authentication and authorization
   - Review frontend-backend communication

## Best Practices

### Development

- **Local Development**: Use kind/k3s for local testing
- **Feature Flags**: Enable/disable features without redeployment
- **Canary Deployments**: Gradual rollout with monitoring

### Operations

- **Infrastructure as Code**: All configurations version controlled
- **Automated Testing**: CI/CD pipelines with comprehensive tests
- **Change Management**: Documented change approval processes

### Security

- **Principle of Least Privilege**: Minimal required permissions
- **Network Segmentation**: Isolate sensitive components
- **Regular Audits**: Security and compliance reviews

---

This guide provides a comprehensive framework for debugging complex distributed AI systems. Regular review and updates ensure it remains current with evolving system architecture and requirements.

---
name: health-check-monitor
description: Monitor Kubernetes cluster health and generate alerts for issues. Use when you need automated health monitoring, resource utilization tracking, or proactive issue detection in Kubernetes environments.
license: AGPLv3
metadata:
  author: agentic-reconciliation-engine
  version: "1.0"
  category: infrastructure
  risk_level: low
  autonomy: full
  layer: temporal
compatibility: Requires kubectl, Python 3.8+, and access to Kubernetes clusters
allowed-tools: kubectl python
---

# Health Check Monitor — Kubernetes Cluster Monitoring

## Purpose
Automated monitoring solution for Kubernetes cluster health, resource utilization, and proactive issue detection. Provides real-time alerts and recommendations for maintaining cluster stability.

## When to Use
- **Routine Health Checks**: Regular cluster status monitoring
- **Resource Alerts**: When pods are nearing resource limits
- **Node Issues**: Detecting unhealthy nodes or failed pods
- **Capacity Planning**: Monitoring resource trends for scaling decisions
- **Incident Prevention**: Early detection of potential problems

## Gotchas

### Common Pitfalls
- **RBAC Permissions**: Health monitoring requires cluster-reader permissions
- **Network Policies**: Some clusters block metrics collection from pods
- **Resource Limits**: Monitoring pods themselves need resource limits
- **False Positives**: Temporary spikes shouldn't trigger alerts

### Edge Cases
- **Multi-tenant Clusters**: Namespaces may have different monitoring requirements
- **StatefulSets**: Different health criteria than stateless deployments
- **Custom Resources**: CRDs may need special health checks

## Inputs
- **cluster**: Target cluster name (optional, default: current context)
- **namespace**: Namespace to monitor (optional, default: all)
- **check_types**: Types of checks to perform (optional, default: all)
- **alert_thresholds**: Custom alert thresholds (optional)

## Process
1. **Cluster Discovery**: Identify target clusters and namespaces
2. **Resource Collection**: Gather pod, node, and service status
3. **Health Assessment**: Evaluate health metrics against thresholds
4. **Alert Generation**: Create alerts for issues found
5. **Report Generation**: Produce monitoring summary and recommendations

## Outputs
- **Health Status**: Overall cluster health score and status
- **Resource Metrics**: CPU, memory, and storage utilization
- **Alert Summary**: List of active alerts and recommendations
- **Trend Analysis**: Resource usage patterns over time

## Scripts
- `scripts/health-checker.py`: Main monitoring implementation
- `scripts/alert-handler.py`: Alert generation and notification
- `scripts/metrics-collector.py`: Resource metrics gathering

## Trigger Keywords
health, monitor, kubernetes, cluster, alert, resources, nodes, pods

## Human Gate Requirements
- **Critical Alerts**: High-severity issues require immediate attention
- **Resource Limits**: Actions requiring resource changes need approval

## References
- `references/kubernetes-health-patterns.md`: Health check methodologies
- `assets/alert-templates/`: Alert message templates
- `examples/cluster-configs/`: Sample cluster monitoring configurations

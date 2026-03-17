---
name: debug-distributed-systems
description: >
  Specialized debugging skill for distributed systems across multiple clusters,
  nodes, and network boundaries. Use when troubleshooting complex multi-node
  deployments, cross-cluster communication, or distributed agent coordination.
metadata:
  risk_level: medium
  autonomy: conditional
  layer: temporal
  human_gate: Required for destructive operations
---

# Distributed Systems Debugger

## Overview

This skill provides comprehensive debugging capabilities for distributed systems spanning multiple Kubernetes clusters, nodes, and network boundaries. It specializes in identifying and resolving issues that arise from the complexity of distributed architectures.

## Capabilities

### Multi-Cluster Debugging
- Cross-cluster connectivity validation
- Inter-cluster service discovery issues
- Federation and replication problems
- Multi-cluster security and authentication

### Network Diagnostics
- Service mesh communication issues
- Load balancer and ingress problems
- DNS resolution across clusters
- Network policy and firewall conflicts

### Distributed State Issues
- Consistency and convergence problems
- Leader election and coordination failures
- Distributed transaction issues
- Eventual consistency delays

### Performance Analysis
- Cross-cluster latency analysis
- Network throughput bottlenecks
- Resource contention across nodes
- Scalability and load distribution

## Usage

### Basic Multi-Cluster Check
```bash
python main.py debug-distributed \
  --clusters cluster-a,cluster-b,cluster-c \
  --issue-type connectivity \
  --time-range 30m
```

### Network Performance Analysis
```bash
python main.py debug-distributed \
  --target-components service-mesh,ingress \
  --issue-type performance \
  --latency-threshold 100ms \
  --generate-report
```

### State Consistency Validation
```bash
python main.py debug-distributed \
  --check-consistency \
  --components database,cache,queue \
  --auto-repair
```

## Integration Points

### Cluster Federation
- Kubernetes Cluster API
- Multi-cluster service discovery
- Cross-cluster authentication tokens
- Federation health endpoints

### Service Mesh
- Istio/Linkerd control plane status
- Sidecar injection and configuration
- Traffic management policies
- Telemetry and observability data

### Distributed Storage
- Database replication status
- Cache synchronization
- Message queue connectivity
- Persistent volume cross-mounting

## Auto-Fix Capabilities

When enabled, can automatically:
- Restart unhealthy cross-cluster services
- Reconcile network policies
- Refresh service discovery cache
- Repair leader election issues
- Synchronize distributed configuration

## Safety Considerations

- Never performs destructive operations without explicit approval
- Validates connectivity before making changes
- Maintains audit trail across all clusters
- Preserves system state during debugging

## Output Format

Returns structured reports including:
- Cluster health matrix
- Network connectivity graph
- Performance metrics across clusters
- Consistency validation results
- Recommended remediation steps

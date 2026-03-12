# eBPF Pixie Integration for GitOps Infrastructure Control Plane

## Overview

Pixie provides real-time, full-fidelity observability using eBPF technology, enabling deep insights into application and infrastructure performance without requiring code instrumentation. This integration adds Pixie to both hub and spoke clusters in the GitOps Infrastructure Control Plane.

## Architecture

### Hub Cluster Configuration
- **Namespace**: `pl`
- **Cluster Name**: `gitops-hub-cluster`
- **Resource Allocation**: Higher limits for centralized monitoring
- **Data Collection**: Full feature set including HTTP tracing, database profiling

### Spoke Cluster Configuration
- **Namespace**: `pl`
- **Cluster Name**: `gitops-spoke-{CLUSTER_NAME}`
- **Resource Allocation**: Optimized for spoke cluster resource constraints
- **Data Collection**: Core features with reduced sampling rates

## Features

### Real-Time Observability
- **HTTP Tracing**: Automatic HTTP request/response tracing without code changes
- **Database Profiling**: MySQL, PostgreSQL, Redis query performance analysis
- **System Call Monitoring**: Process-level visibility into system operations
- **Network Traffic Analysis**: Full network flow visibility between services

### Zero Instrumentation
- **eBPF Technology**: Kernel-level monitoring without application changes
- **Auto-Discovery**: Automatic service and endpoint discovery
- **Language Support**: Go, Java, Node.js, Python, and more

### GitOps Integration
- **Flux Managed**: Deployed and managed through GitOps workflows
- **Configuration as Code**: All Pixie configurations stored in Git
- **Multi-Cluster**: Consistent deployment across hub and spoke clusters

## Deployment

### Prerequisites
- Kubernetes 1.16+ with kernel 4.14+ (for eBPF support)
- Cluster admin permissions for eBPF program loading
- Sufficient node resources (minimum 2 CPU, 4GB RAM per node)

### Hub Cluster Deployment
```bash
# Deploy monitoring stack with Pixie
kubectl apply -k infrastructure/monitoring/

# Verify deployment
kubectl get pods -n pl
kubectl logs -n pl -l app=vizier
```

### Spoke Cluster Deployment
```bash
# Deploy to spoke clusters through GitOps
# Configuration automatically applied via Flux

# Manual verification (optional)
kubectl get pods -n pl
kubectl exec -n pl -c vizier -- px cluster list
```

## Configuration

### Resource Limits

#### Hub Cluster
```yaml
vizier:
  memory_limit: "2Gi"
  cpu_limit: "1000m"
  memory_request: "1Gi"
  cpu_request: "500m"
pem:
  memory_limit: "1Gi"
  cpu_limit: "500m"
  memory_request: "512Mi"
  cpu_request: "200m"
```

#### Spoke Cluster
```yaml
vizier:
  memory_limit: "1Gi"
  cpu_limit: "500m"
  memory_request: "512Mi"
  cpu_request: "250m"
pem:
  memory_limit: "512Mi"
  cpu_limit: "250m"
  memory_request: "256Mi"
  cpu_request: "100m"
```

### Data Collection Settings

#### Hub Cluster (Full Monitoring)
```yaml
http_trace_sampling_rate: 0.1  # 10% sampling
stats_collection_interval: 30   # seconds
trace_collection_interval: 60   # seconds
enable_database_profiling: true
```

#### Spoke Cluster (Optimized)
```yaml
http_trace_sampling_rate: 0.05  # 5% sampling
stats_collection_interval: 60   # seconds
trace_collection_interval: 120  # seconds
enable_redis_profiling: false   # Resource optimization
```

## Usage

### Accessing Pixie UI
1. Navigate to [https://work.withpixie.ai](https://work.withpixie.ai)
2. Select your cluster (e.g., `gitops-hub-cluster`)
3. Start exploring with pre-built scripts

### Monitoring GitOps Components

#### Flux Health Monitoring
```px
# In Pixie UI, run: px/http_data
# Filter by service: flux-system
```

#### Application Performance
```px
# Run: px/http_data
# Group by service to see performance across applications
```

#### Network Analysis
```px
# Run: px/network_flow
# Analyze traffic patterns between services
```

#### Container Resources
```px
# Run: px/container_stats
# Monitor resource usage across containers
```

### Custom Scripts

#### Cross-Cluster Communication
```px
#import px

df = px.DataFrame('network_flow')
# Filter for inter-cluster traffic
df = df[(px.contains(df['src_addr'], '10.0.0')) | (px.contains(df['dst_addr'], '10.0.0'))]
df = df.groupby(['src_addr', 'dst_addr', 'protocol']).agg(
    bytes_sent=('bytes_sent', px.sum),
    connections=('time_', px.count)
)
df = df.sort('bytes_sent', descending=True)
df.head(20)
```

#### Database Performance
```px
#import px

df = px.DataFrame('mysql_events')
df = df.groupby(['remote_addr', 'req_cmd']).agg(
    query_time=('time_', px.mean),
    queries=('time_', px.count)
)
df = df.sort('query_time', descending=True)
df.head(10)
```

## Integration with Existing Monitoring

### Complementary Tools
- **Honeycomb**: Application metrics and traces with business context
- **Loki**: Log aggregation and analysis
- **Pixie**: System-level observability with eBPF

### Data Flow
```
Applications → Pixie eBPF → Pixie Vizier → Pixie UI
           → OpenTelemetry → Honeycomb → Dashboards
           → Fluent Bit → Loki → Log Analysis
```

## Security Considerations

### eBPF Security
- **Kernel Access**: Pixie requires eBPF program loading capabilities
- **System Calls**: Monitors system calls across all processes
- **Network Traffic**: Captures network packets for analysis

### RBAC Permissions
Pixie requires extensive permissions for comprehensive monitoring:
- Pod and node access for process monitoring
- Network access for traffic analysis
- System call access for eBPF programs

### Data Privacy
- **Local Processing**: Data processed locally on clusters
- **Cloud UI**: Metadata sent to Pixie cloud for UI
- **On-Prem Option**: Available for enterprise deployments

## Troubleshooting

### Common Issues

#### eBPF Not Supported
```bash
# Check kernel version
kubectl get nodes -o jsonpath='{.items[0].status.nodeInfo.kernelVersion}'

# Should be 4.14+ for full eBPF support
```

#### Permission Denied
```bash
# Check cluster admin permissions
kubectl auth can-i create pods --namespace=pl
kubectl auth can-i create clusterrolebinding
```

#### High Resource Usage
```bash
# Check resource usage
kubectl top pods -n pl

# Adjust sampling rates if needed
kubectl edit configmap pixie-config -n pl
```

### Health Checks

#### Hub Cluster
```bash
# Run health check
kubectl exec -n pl deployment/flux-health-checks -- /bin/bash /etc/config/health-script.sh

# Check Pixie specifically
kubectl exec -n pl configmap/pixie-monitoring -- /bin/bash /etc/config/pixie-health-check.sh
```

#### Spoke Cluster
```bash
# Check spoke cluster health
kubectl exec -n pl configmap/pixie-spoke-health -- /bin/bash /etc/config/spoke-health-check.sh
```

## Performance Impact

### Resource Overhead
- **CPU**: 5-10% per node (configurable via sampling rates)
- **Memory**: 100-500MB per node (depending on workload)
- **Network**: Minimal additional traffic for metadata

### Optimization Strategies
- Reduce sampling rates for high-traffic services
- Disable unused data collectors
- Adjust resource limits based on cluster size

## Migration Guide

### From Traditional Monitoring
1. **Phase 1**: Deploy Pixie alongside existing tools
2. **Phase 2**: Compare data and validate insights
3. **Phase 3**: Gradually reduce reliance on agents
4. **Phase 4**: Optimize Pixie configuration

### Multi-Cluster Setup
1. Deploy to hub cluster first
2. Validate configuration and performance
3. Roll out to spoke clusters gradually
4. Monitor resource usage across clusters

## Best Practices

### Configuration Management
- Store all Pixie configurations in Git
- Use environment-specific overlays
- Version control custom scripts

### Resource Management
- Monitor resource usage closely
- Adjust limits based on cluster size
- Use spoke-specific configurations

### Security
- Regularly audit Pixie permissions
- Monitor eBPF program loading
- Consider on-prem deployment for sensitive data

## Support and Resources

### Documentation
- [Pixie Official Documentation](https://docs.px.dev/)
- [eBPF Fundamentals](https://ebpf.io/)
- [Kubernetes Observability](https://kubernetes.io/docs/tasks/debug-application-cluster/resource-usage-monitoring/)

### Community
- [Pixie Slack Community](https://slack.px.dev/)
- [GitHub Issues](https://github.com/pixie-io/pixie/issues)
- [Kubernetes Monitoring](https://github.com/kubernetes/community/tree/master/sig-instrumentation)

### Training
- Pixie UI tutorials and walkthroughs
- eBPF programming fundamentals
- Kubernetes observability best practices

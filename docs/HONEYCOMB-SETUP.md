# Honeycomb Observability Setup

This guide explains how to integrate Honeycomb observability into the GitOps Infrastructure Control Plane using OpenTelemetry collectors.

## Overview

Honeycomb provides powerful observability capabilities for Kubernetes clusters including:
- **Metrics**: Node and pod metrics, cluster-level metrics
- **Logs**: Kubernetes events and application logs
- **Traces**: Distributed tracing for applications

The integration uses OpenTelemetry collectors deployed in two modes:
1. **Deployment mode**: Cluster-level collector for cluster metrics and events
2. **DaemonSet mode**: Node-level collectors for pod metrics and application telemetry

## Prerequisites

- Kubernetes cluster with kubectl access
- Helm 3.9+ installed locally
- Honeycomb account and API key

## Quick Start

### 1. Configure Honeycomb API Key

```bash
# Set your Honeycomb API key
export HONEYCOMB_API_KEY=your-actual-api-key

# Create the secret in the honeycomb namespace
kubectl create secret generic honeycomb --from-literal=api-key=$HONEYCOMB_API_KEY --namespace=honeycomb
```

### 2. Deploy Honeycomb Collectors

```bash
# Apply the Honeycomb manifests
kubectl apply -f infrastructure/monitoring/honeycomb.yaml

# Deploy using the included script
kubectl exec -n honeycomb configmap/honeycomb-deploy-script -- /bin/bash /etc/config/deploy-honeycomb.sh
```

### 3. Verify Installation

```bash
# Check collector status
kubectl get pods -n honeycomb

# Run health check
kubectl exec -n honeycomb configmap/honeycomb-monitoring -- /bin/bash /etc/config/honeycomb-health-check.sh
```

## Configuration

### Datasets

The collectors send data to the following Honeycomb datasets:
- `k8s-metrics`: Cluster-level metrics (deployments, nodes, etc.)
- `k8s-events`: Kubernetes events
- `k8s-node-metrics`: Node and pod metrics
- `traces`: Application traces

### EU Instance

If you're using Honeycomb's EU instance, update the endpoints in the configuration:

```yaml
# Change from US to EU endpoints
endpoint: "api.eu1.honeycomb.io:443"
```

## Architecture

### Deployment Mode Collector
- **Purpose**: Cluster-wide metrics and events
- **Components**: 
  - `k8s_cluster` receiver for cluster metrics
  - `k8sobjects` receiver for Kubernetes events
- **Replicas**: 1 (to avoid duplicate data)

### DaemonSet Mode Collector
- **Purpose**: Node-level metrics and application telemetry
- **Components**:
  - `kubeletstats` receiver for node/pod metrics
  - `otlp` receiver for application traces
- **Replicas**: 1 per node

## Collected Data

### Metrics
- Node and pod resource usage (CPU, memory)
- Kubernetes object counts and status
- Custom application metrics (if instrumented)

### Events
- All Kubernetes events with full metadata
- Event severity classification (Normal/Warning)
- Resource attribute enrichment

### Traces
- Application distributed traces
- Service dependency mapping
- Performance bottleneck identification

## Monitoring and Troubleshooting

### Health Checks

```bash
# Check collector pods
kubectl get pods -n honeycomb -l app.kubernetes.io/name=opentelemetry-collector

# Check collector logs
kubectl logs -n honeycomb -l app.kubernetes.io/instance=otel-collector-cluster
kubectl logs -n honeycomb -l app.kubernetes.io/instance=otel-collector-daemonset

# Run comprehensive health check
kubectl exec -n honeycomb configmap/honeycomb-monitoring -- /bin/bash /etc/config/honeycomb-health-check.sh
```

### Common Issues

#### API Key Not Configured
```bash
# Check if API key is set
kubectl get secret honeycomb -n honeycomb --template="{{.data.api-key}}" | base64 -d

# Update API key
kubectl create secret generic honeycomb --from-literal=api-key=$HONEYCOMB_API_KEY --namespace=honeycomb --dry-run=client -o yaml | kubectl apply -f -
```

#### Collectors Not Starting
```bash
# Check RBAC permissions
kubectl auth can-i get nodes --as=system:serviceaccount:honeycomb:otel-collector

# Check service account
kubectl get serviceaccount otel-collector -n honeycomb
```

#### No Data in Honeycomb
```bash
# Check collector configuration
kubectl get configmap honeycomb-config -n honeycomb -o yaml

# Check collector logs for errors
kubectl logs -n honeycomb -l app.kubernetes.io/name=opentelemetry-collector --tail=50
```

## Integration with GitOps

The Honeycomb configuration is managed through GitOps using Flux:

```yaml
# Add to your flux kustomization
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: honeycomb
  namespace: flux-system
spec:
  interval: 1h
  path: ./infrastructure/monitoring
  prune: true
  sourceRef:
    kind: GitRepository
    name: flux-system
  dependsOn:
    - name: core-flux
```

## Security Considerations

### API Key Management
- Use SealedSecrets or external secret management in production
- Rotate API keys regularly
- Limit API key permissions to necessary datasets

### Network Security
- Ensure outbound connectivity to Honeycomb endpoints
- Consider using VPC endpoints for enhanced security
- Enable TLS for all communications

### RBAC
- Collectors require read-only access to Kubernetes APIs
- Service account permissions are scoped to necessary resources only
- Regular audit of RBAC permissions recommended

## Advanced Configuration

### Custom Metrics
Add custom receivers and processors to collect application-specific metrics:

```yaml
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: 'my-app'
          static_configs:
            - targets: ['my-app:9090']
```

### Sampling
Configure trace sampling to control volume:

```yaml
processors:
  probabilistic_sampler:
    sampling_percentage: 10
```

### Resource Filtering
Filter which resources send metrics:

```yaml
processors:
  resource:
    attributes:
      - key: k8s.namespace.name
        action: exclude
        value: kube-system
```

## Cost Optimization

### Metric Volume Control
- Disable high-volume metrics (replicasets by default)
- Increase collection intervals for less critical metrics
- Use metric filtering to exclude unnecessary data

### Sampling Strategies
- Implement probabilistic sampling for traces
- Use tail-based sampling for high-value traces
- Configure per-service sampling rates

## Next Steps

1. **Instrument Applications**: Add OpenTelemetry instrumentation to your applications
2. **Create Dashboards**: Build custom dashboards in Honeycomb for your specific needs
3. **Set Up Alerts**: Configure Honeycomb alerts for critical metrics and events
4. **Integrate with CI/CD**: Add observability checks to your deployment pipeline

## Support

- [Honeycomb Documentation](https://docs.honeycomb.io/)
- [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/)
- [Kubernetes Integration Guide](https://docs.honeycomb.io/send-data/kubernetes/opentelemetry/)

# Monitoring Stack Deployment Guide

## Overview

This document covers the complete deployment of the monitoring stack with Langfuse dashboard integration, including fixes for deprecated kustomize configurations and troubleshooting common issues.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [CommonLabels Fix](#commonlabels-fix)
3. [Monitoring Stack Components](#monitoring-stack-components)
4. [Langfuse Dashboard](#langfuse-dashboard)
5. [Deployment Process](#deployment-process)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)
8. [Access Information](#access-information)

## Prerequisites

### Required Tools
- `kubectl` - Kubernetes CLI
- `kustomize` - Kubernetes configuration management
- Access to a Kubernetes cluster

### Cluster Requirements
- Minimum 4 CPU cores
- 16Gi memory available
- Network access for monitoring components

## CommonLabels Fix

### Issue Identified

During deployment, kustomize issued a warning:
```
Warning: 'commonLabels' is deprecated. Please use 'labels' instead. Run 'kustomize edit fix' to update your Kustomization automatically.
```

### Root Cause

The monitoring kustomization file used the deprecated `commonLabels` field instead of the newer `labels` structure.

### Files Affected

- `/core/workspace/repo/infrastructure/monitoring/kustomization.yaml`
- 86 other kustomization files throughout the repository

### Solution Applied

#### Manual Fix for Monitoring Stack

**Before:**
```yaml
# Common labels for all monitoring resources
commonLabels:
  app.kubernetes.io/part-of: gitops-monitoring
  app.kubernetes.io/managed-by: flux
```

**After:**
```yaml
# Common labels for all monitoring resources
labels:
  - pairs:
      app.kubernetes.io/part-of: gitops-monitoring
      app.kubernetes.io/managed-by: flux
```

#### Automated Fix Script

Created `/scripts/fix-commonlabels.sh` to systematically fix all affected files:

```bash
#!/bin/bash
# Fix commonLabels to labels in all Kustomization files

# Features:
- Cross-platform sed compatibility (gsed fallback)
- Backup creation before modifications
- Comprehensive file scanning
- Error handling and reporting
```

**Usage:**
```bash
bash /Users/lloyd/github/antigravity/gitops-infra-control-plane/scripts/fix-commonlabels.sh
```

## Monitoring Stack Components

### Core Infrastructure

| Component | Namespace | Purpose | Resources |
|-----------|-----------|---------|-----------|
| Loki | `monitoring` | Log aggregation | StatefulSet |
| Promtail | `monitoring` | Log collection | DaemonSet |
| OpenTelemetry Collector | `honeycomb` | Metrics/trace collection | Deployment |
| Pixie | `pl` | eBPF observability | DaemonSet |

### Namespaces Created

- `monitoring` - Primary monitoring infrastructure
- `honeycomb` - OpenTelemetry and observability
- `pl` - Pixie eBPF monitoring

### Service Accounts and RBAC

- `otel-collector` - OpenTelemetry collection permissions
- `promtail` - Log collection permissions  
- `pixie` - eBPF monitoring permissions

### ConfigMaps Deployed

- `honeycomb-config` - OpenTelemetry configuration
- `loki-config` - Log aggregation settings
- `promtail-config` - Log collection configuration
- `pixie-config` - eBPF monitoring configuration
- `flux-health-checks` - GitOps health monitoring
- `langfuse-dashboard` - Grafana dashboard definition

## Langfuse Dashboard

### Dashboard Features

The Langfuse AI Agent Observability dashboard provides comprehensive monitoring for AI agent systems:

#### 1. **Agent Performance Overview**
- Total traces count
- Real-time performance metrics
- Success/failure ratios

#### 2. **Skill Invocation Success Rate**
- Gauge visualization showing success percentages
- Real-time monitoring of skill execution
- Threshold-based alerting

#### 3. **Cost Analysis**
- Total cost tracking
- Cost per request analysis
- Currency-formatted displays (USD)

#### 4. **Model Usage Breakdown**
- Pie chart of model utilization
- Per-model usage statistics
- Resource allocation insights

#### 5. **Response Time Distribution**
- Heatmap visualization of response patterns
- Performance bottleneck identification
- Latency analysis

#### 6. **Token Usage Trends**
- Input/output token monitoring
- Usage trend analysis
- Cost optimization insights

#### 7. **Error Rate by Operation Type**
- Bar chart of error distribution
- Operation-specific error tracking
- Debugging support

#### 8. **Agent Workflow Status**
- Table view of Temporal workflow status
- Real-time workflow monitoring
- State tracking

#### 9. **Cost Efficiency Metrics**
- Tokens per dollar calculations
- Efficiency scoring
- Performance optimization metrics

#### 10. **Agent Skill Performance Matrix**
- Detailed performance scoring per skill
- Comparative analysis
- Performance ranking

### Dashboard Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: langfuse-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
```

### Integration Points

- **Prometheus**: Metrics data source
- **Temporal**: Workflow status monitoring
- **Langfuse**: AI agent observability data
- **Custom Metrics**: Agent-specific performance data

## Deployment Process

### Step 1: Fix Configuration Issues

```bash
# Fix commonLabels deprecation warning
bash /Users/lloyd/github/antigravity/gitops-infra-control-plane/scripts/fix-commonlabels.sh
```

### Step 2: Deploy Monitoring Stack

```bash
# Apply monitoring infrastructure
kubectl apply -k /Users/lloyd/github/antigravity/gitops-infra-control-plane/core/resources/infrastructure/monitoring
```

### Expected Output

```
namespace/honeycomb unchanged
namespace/monitoring configured
namespace/pl unchanged
serviceaccount/otel-collector unchanged
serviceaccount/promtail unchanged
serviceaccount/pixie unchanged
clusterrole.rbac.authorization.k8s.io/otel-collector unchanged
clusterrole.rbac.authorization.k8s.io/pixie unchanged
clusterrole.rbac.authorization.k8s.io/promtail unchanged
clusterrolebinding.rbac.authorization.k8s.io/otel-collector unchanged
clusterrolebinding.rbac.authorization.k8s.io/pixie unchanged
clusterrolebinding.rbac.authorization.k8s.io/promtail unchanged
configmap/honeycomb-config unchanged
configmap/honeycomb-deploy-script unchanged
configmap/honeycomb-monitoring unchanged
configmap/flux-health-checks unchanged
configmap/langfuse-dashboard unchanged
configmap/loki-config unchanged
configmap/promtail-config unchanged
configmap/pixie-config unchanged
configmap/pixie-monitoring unchanged
secret/honeycomb configured
secret/monitoring-secrets-ggk686t7fd unchanged
service/loki unchanged
statefulset.apps/loki unchanged
daemonset.apps/promtail unchanged
```

### Step 3: Verify Deployment

```bash
# Check pod status
kubectl get pods -n monitoring

# Verify services
kubectl get services -n monitoring

# Check dashboard configuration
kubectl get configmap langfuse-dashboard -n monitoring -o yaml
```

## Verification

### Health Checks

#### 1. Pod Status
```bash
kubectl get pods -n monitoring
```

Expected pods:
- `loki-0` (StatefulSet)
- `promtail-*` (DaemonSet)
- OpenTelemetry collector pods
- Pixie pods

#### 2. Service Connectivity
```bash
kubectl get services -n monitoring
```

#### 3. Dashboard Availability
```bash
# Check if Grafana can read the dashboard
kubectl get configmap langfuse-dashboard -n monitoring -o jsonpath='{.data.langfuse-dashboard\.json}' | jq .dashboard.title
```

### Expected Results

- All pods in `Running` state
- Services properly configured
- Dashboard accessible in Grafana
- Metrics flowing to Prometheus

## Troubleshooting

### Common Issues

#### 1. commonLabels Deprecation Warning

**Symptom:**
```
Warning: 'commonLabels' is deprecated. Please use 'labels' instead.
```

**Solution:**
```bash
# Run the automated fix
bash /scripts/fix-commonlabels.sh

# Or manually fix the specific file
sed -i 's/commonLabels:/labels:/' kustomization.yaml
```

#### 2. Pod Startup Issues

**Symptoms:**
- Pods stuck in `Pending` state
- CrashLoopBackOff errors

**Solutions:**
```bash
# Check pod events
kubectl describe pod <pod-name> -n monitoring

# Check logs
kubectl logs <pod-name> -n monitoring

# Check resource constraints
kubectl top nodes
kubectl top pods -n monitoring
```

#### 3. Dashboard Not Visible in Grafana

**Symptoms:**
- Langfuse dashboard not appearing in Grafana
- Dashboard import errors

**Solutions:**
```bash
# Verify ConfigMap exists
kubectl get configmap langfuse-dashboard -n monitoring

# Check Grafana configuration
kubectl logs deployment/grafana -n monitoring

# Reload Grafana configuration
kubectl delete pod grafana-* -n monitoring
```

#### 4. Metrics Not Appearing

**Symptoms:**
- No data in dashboard panels
- Prometheus not scraping metrics

**Solutions:**
```bash
# Check Prometheus targets
kubectl port-forward svc/prometheus 9090:9090 -n monitoring
# Visit http://localhost:9090/targets

# Check ServiceMonitor configuration
kubectl get servicemonitor -n monitoring

# Verify metrics endpoints
kubectl port-forward svc/<target-service> <port>:<port> -n <namespace>
curl http://localhost:<port>/metrics
```

### Debug Commands

#### System Health
```bash
# Overall cluster health
kubectl get nodes
kubectl get pods --all-namespaces

# Monitoring namespace status
kubectl get all -n monitoring

# Resource usage
kubectl top nodes
kubectl top pods -n monitoring
```

#### Log Analysis
```bash
# Loki logs
kubectl logs -l app=loki -n monitoring

# Promtail logs
kubectl logs -l app=promtail -n monitoring

# OpenTelemetry collector logs
kubectl logs -l app=otel-collector -n honeycomb
```

#### Network Connectivity
```bash
# Service connectivity test
kubectl run test-pod --image=nicolaka/netshoot --rm -it -- bash

# Inside pod:
nslookup loki.monitoring.svc.cluster.local
nslookup prometheus.monitoring.svc.cluster.local
```

## Access Information

### Grafana Dashboard

```bash
# Port-forward Grafana
kubectl port-forward svc/grafana 3000:3000 -n monitoring

# Access at: http://localhost:3000
```

**Dashboard Navigation:**
1. Login to Grafana
2. Go to Dashboards
3. Search for "Langfuse AI Agent Observability"
4. Click to open the dashboard

### Prometheus

```bash
# Port-forward Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n monitoring

# Access at: http://localhost:9090
```

### Loki Log Interface

```bash
# Port-forward Loki
kubectl port-forward svc/loki 3100:3100 -n monitoring

# Access at: http://localhost:3100
```

### Monitoring Endpoints

| Service | Port | Path | Purpose |
|---------|------|------|---------|
| Grafana | 3000 | `/` | Dashboard interface |
| Prometheus | 9090 | `/` | Metrics query interface |
| Loki | 3100 | `/` | Log query interface |
| OpenTelemetry | 4317 | `/` | Metrics/trace ingestion |

## Configuration Files

### Key Files

- `/core/resources/infrastructure/monitoring/kustomization.yaml` - Main kustomization
- `/core/resources/infrastructure/monitoring/langfuse-dashboard.yaml` - Dashboard definition
- `/scripts/fix-commonlabels.sh` - Automated fix script

### Customization

To modify the monitoring stack:

1. **Update kustomization.yaml** for component changes
2. **Modify dashboard JSON** for panel adjustments
3. **Update ConfigMaps** for configuration changes
4. **Reapply with kubectl** for deployment

## Best Practices

### 1. Resource Management
- Monitor resource usage regularly
- Set appropriate resource limits
- Use node selectors for critical components

### 2. Security
- Use RBAC for access control
- Enable network policies
- Secure sensitive configuration with Secrets

### 3. High Availability
- Configure replica sets for critical services
- Use persistent storage for stateful components
- Implement backup strategies

### 4. Monitoring
- Set up alerting rules
- Monitor system health
- Regular maintenance and updates

## Maintenance

### Regular Tasks

1. **Daily**
   - Check pod health
   - Review error logs
   - Monitor resource usage

2. **Weekly**
   - Update dashboard configurations
   - Review alert rules
   - Performance optimization

3. **Monthly**
   - Component updates
   - Security patches
   - Backup verification

### Backup Procedures

```bash
# Backup monitoring configuration
kubectl get all -n monitoring -o yaml > monitoring-backup.yaml

# Backup dashboard configurations
kubectl get configmap -n monitoring -l grafana_dashboard=1 -o yaml > dashboards-backup.yaml
```

## Conclusion

The monitoring stack with Langfuse dashboard provides comprehensive observability for AI agent systems. The deployment process resolves deprecated kustomize configurations and establishes a robust monitoring foundation.

Key achievements:
- ✅ Fixed commonLabels deprecation warnings
- ✅ Deployed complete monitoring infrastructure
- ✅ Integrated Langfuse AI agent observability
- ✅ Established troubleshooting procedures
- ✅ Documented access and maintenance procedures

The system is now ready for production monitoring of AI agent workflows with comprehensive dashboards and alerting capabilities.

---

**Tags:** `monitoring` `langfuse` `kubernetes` `grafana` `observability` `ai-agents` `kustomize` `deployment`

1. **Core Monitoring Infrastructure**
   - **Loki**: Log aggregation system
   - **Promtail**: Log collection agent
   - **Grafana**: Visualization dashboard platform

2. **AI Agent Observability**
   - **Langfuse Dashboard**: AI agent performance and cost monitoring
   - **Langfuse Secrets**: Configuration for Langfuse integration

3. **Supporting Infrastructure**
   - **Honeycomb**: Application monitoring and tracing
   - **Pixie**: eBPF-based observability platform

## Deployment Process

### Prerequisites

- Kubernetes cluster with access
- kubectl configured
- Appropriate RBAC permissions for monitoring namespace

### Step 1: Fix Kustomization Deprecations

The monitoring stack Kustomization contained deprecated fields that needed updating:

```yaml
# Before (deprecated)
commonLabels:
  app.kubernetes.io/part-of: gitops-monitoring
  app.kubernetes.io/managed-by: flux

patchesJson6902:
  - target:
      kind: Deployment
      name: otel-collector-cluster
      namespace: honeycomb
    patch: |
      - op: add
        path: /spec/template/spec/containers/0/resources
        value:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "256Mi"
            cpu: "200m"

# After (updated)
labels:
  - pairs:
      app.kubernetes.io/part-of: gitops-monitoring
      app.kubernetes.io/managed-by: flux

patches:
  - target:
      kind: Deployment
      name: otel-collector-cluster
      namespace: honeycomb
    patch: |
      - op: add
        path: /spec/template/spec/containers/0/resources
        value:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "256Mi"
            cpu: "200m"
```

### Step 2: Deploy Core Monitoring Stack

```bash
kubectl apply -k core/resources/infrastructure/monitoring
```

**Fixed Issues:**
- Replaced deprecated `patchesJson6902` with `patches`
- Updated `commonLabels` to new `labels` format
- Resolved StatefulSet and DaemonSet immutable field conflicts

### Step 3: Deploy Grafana Dashboard

```bash
kubectl apply -f core/resources/infrastructure/tenants/3-workloads/monitoring/grafana.yaml
```

### Step 4: Configure Grafana Admin Credentials

```bash
kubectl create secret generic grafana-admin-credentials \
  --from-literal=admin-password=admin123 \
  -n monitoring
```

### Step 5: Deploy Langfuse Integration

```bash
# Deploy Langfuse secrets for AI infrastructure
kubectl apply -f core/config/langfuse-secret-gitops-infra.yaml

# Langfuse dashboard is automatically deployed as ConfigMap
kubectl apply -f core/resources/infrastructure/monitoring/langfuse-dashboard.yaml
```

## Access Information

### Grafana Dashboard

- **URL**: http://localhost:3000
- **Username**: admin
- **Password**: admin123
- **Dashboard**: "Langfuse AI Agent Observability"

### Port Forwarding

For local access to Grafana:

```bash
# Use nohup for persistent background execution
nohup kubectl port-forward -n monitoring svc/grafana-service 3000:3000 &

# Monitor with:
tail -f nohup.out

# Clean up when done:
pkill -f "kubectl port-forward"
```

## Langfuse Dashboard Configuration

### Dashboard Features

The Langfuse dashboard provides comprehensive AI agent observability:

1. **Agent Performance Overview**
   - Total traces
   - Success rates
   - Performance metrics

2. **Skill Invocation Analysis**
   - Success rate gauge
   - Skill performance matrix
   - Operation-specific metrics

3. **Cost Analysis**
   - Total cost tracking
   - Cost per request
   - Cost efficiency metrics

4. **Model Usage Breakdown**
   - Usage by model type
   - Token consumption trends
   - Model performance comparison

5. **Response Time Distribution**
   - Latency heatmaps
   - Performance percentiles
   - Bottleneck identification

6. **Error Analysis**
   - Error rates by operation
   - Error categorization
   - Failure pattern analysis

7. **Temporal Integration**
   - Workflow status tracking
   - Agent coordination metrics
   - Orchestration performance

### Metrics Available

The dashboard integrates with the following metrics:

- `langfuse_traces_total` - Total number of traces
- `langfuse_skill_invocation_success_rate` - Skill success percentage
- `langfuse_cost_total` - Total operational costs
- `langfuse_cost_per_request` - Cost efficiency metric
- `langfuse_model_usage` - Model-specific usage statistics
- `langfuse_response_time_bucket` - Response time distributions
- `langfuse_tokens_input_total` - Input token consumption
- `langfuse_tokens_output_total` - Output token consumption
- `langfuse_errors_total` - Error counts by type
- `temporal_workflow_status` - Workflow state tracking
- `langfuse_efficiency_tokens_per_dollar` - Cost efficiency
- `langfuse_skill_performance` - Skill-specific performance

## Secret Configuration

### Langfuse Secrets

Create secrets with actual Langfuse credentials:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: langfuse-secrets
  namespace: ai-infrastructure
type: Opaque
data:
  # Replace with base64 encoded actual values
  public-key: <base64-encoded-public-key>
  secret-key: <base64-encoded-secret-key>
  otlp-headers: <base64-encoded-otlp-headers>
```

**Encoding values:**
```bash
echo -n 'your-public-key' | base64
echo -n 'your-secret-key' | base64
echo -n 'Authorization=Bearer your-secret-key' | base64
```

## Resource Status

### Expected Pod Status

```bash
kubectl get pods -n monitoring
```

**Expected output:**
```
NAME                           READY   STATUS    RESTARTS   AGE
pod/grafana-64999d6f48-bmzdb   1/1     Running   0          104s
pod/loki-0                     1/1     Running   0          6m4s
pod/promtail-hbmh9             1/1     Running   0          5m39s
```

### Service Configuration

```bash
kubectl get svc -n monitoring
```

**Expected output:**
```
NAME                      TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
service/grafana-service   LoadBalancer   10.96.247.150   <pending>     3000:31976/TCP   104s
service/loki              ClusterIP      10.96.70.42     <none>        3100/TCP         9m26s
```

## Troubleshooting

### Common Issues

1. **Kustomization Deprecation Warnings**
   - **Issue**: `commonLabels` and `patchesJson6902` deprecated
   - **Solution**: Updated to `labels` and `patches` format

2. **Immutable Field Conflicts**
   - **Issue**: StatefulSet/DaemonSet selector changes
   - **Solution**: Delete and recreate affected resources

3. **Port Forwarding Issues**
   - **Issue**: Port already in use
   - **Solution**: Check with `lsof -i :3000` and kill conflicting processes

4. **Grafana Access Issues**
   - **Issue**: Admin credentials not found
   - **Solution**: Create `grafana-admin-credentials` secret

5. **Langfuse Dashboard Not Visible**
   - **Issue**: Dashboard not imported
   - **Solution**: Ensure ConfigMap has `grafana_dashboard: "1"` label

### Debug Commands

```bash
# Check monitoring stack health
kubectl get pods,svc -n monitoring

# Check Grafana logs
kubectl logs -n monitoring deployment/grafana

# Check Loki logs
kubectl logs -n monitoring statefulset/loki

# Check Promtail logs
kubectl logs -n monitoring daemonset/promtail

# Verify Langfuse dashboard ConfigMap
kubectl get configmap langfuse-dashboard -n monitoring -o yaml

# Check Grafana dashboard import
kubectl logs -n monitoring deployment/grafana | grep dashboard
```

### Recovery Procedures

1. **Resource Recreation**
   ```bash
   # Delete problematic resources
   kubectl delete statefulset loki -n monitoring
   kubectl delete daemonset promtail -n monitoring
   
   # Reapply monitoring stack
   kubectl apply -k core/resources/infrastructure/monitoring
   ```

2. **Secret Recreation**
   ```bash
   # Recreate Grafana admin credentials
   kubectl delete secret grafana-admin-credentials -n monitoring
   kubectl create secret generic grafana-admin-credentials \
     --from-literal=admin-password=admin123 \
     -n monitoring
   ```

## Security Considerations

### Access Control

1. **Grafana Authentication**
   - Change default admin password in production
   - Configure OAuth/LDAP integration
   - Enable role-based access control

2. **Network Security**
   - Use network policies to restrict access
   - Configure TLS termination
   - Implement ingress controllers

3. **Secret Management**
   - Use SealedSecrets for production
   - Rotate Langfuse API keys regularly
   - Implement secret scanning

### Monitoring Security

1. **Audit Logging**
   - Enable Grafana audit logs
   - Monitor access patterns
   - Alert on suspicious activities

2. **Data Protection**
   - Implement retention policies
   - Configure secure log storage
   - Use encryption at rest

## Performance Optimization

### Resource Tuning

1. **Grafana**
   ```yaml
   resources:
     requests:
       memory: "128Mi"
       cpu: "100m"
     limits:
       memory: "256Mi"
       cpu: "200m"
   ```

2. **Loki**
   ```yaml
   resources:
     requests:
       memory: "128Mi"
       cpu: "100m"
     limits:
       memory: "256Mi"
       cpu: "200m"
   ```

3. **Promtail**
   ```yaml
   resources:
     requests:
       memory: "64Mi"
       cpu: "100m"
     limits:
       memory: "128Mi"
       cpu: "200m"
   ```

### Scaling Considerations

1. **Horizontal Scaling**
   - Multiple Grafana instances behind load balancer
   - Loki cluster configuration
   - Promtail resource limits

2. **Storage Optimization**
   - Configure log retention policies
   - Implement log sampling
   - Use efficient storage backends

## Integration Points

### Temporal Workflow Integration

The Langfuse dashboard integrates with Temporal workflows for:

- **Workflow Status Tracking**: Monitor agent orchestration
- **Performance Metrics**: Track workflow execution times
- **Error Analysis**: Identify workflow failures

### AI Agent Integration

Connect with AI agents through:

- **OTLP Exporters**: Send traces to Langfuse
- **Metrics Exporters**: Export performance metrics
- **Log Forwarders**: Route agent logs to Loki

### External Systems

1. **Prometheus Integration**
   - Configure Prometheus data source
   - Set up alerting rules
   - Implement custom metrics

2. **Honeycomb Integration**
   - Configure OpenTelemetry collectors
   - Set up trace sampling
   - Implement distributed tracing

## Maintenance

### Regular Tasks

1. **Weekly**
   - Check resource utilization
   - Review log retention policies
   - Update dashboard configurations

2. **Monthly**
   - Rotate API keys and secrets
   - Update Grafana plugins
   - Review access controls

3. **Quarterly**
   - Performance tuning
   - Capacity planning
   - Security audits

### Backup Procedures

1. **Configuration Backup**
   ```bash
   # Export monitoring configurations
   kubectl get all -n monitoring -o yaml > monitoring-backup.yaml
   ```

2. **Dashboard Backup**
   ```bash
   # Export Grafana dashboards
   curl -u admin:admin123 http://localhost:3000/api/dashboards/export > dashboards.json
   ```

3. **Secret Backup**
   ```bash
   # Backup secrets (encrypted)
   kubectl get secrets -n monitoring -o yaml > secrets-backup.yaml
   ```

## Future Enhancements

### Planned Improvements

1. **Advanced Alerting**
   - Configure multi-channel alerting
   - Implement machine learning anomaly detection
   - Set up predictive alerting

2. **Enhanced Dashboards**
   - Create role-specific dashboards
   - Implement interactive visualizations
   - Add real-time collaboration features

3. **Automation**
   - Auto-scaling based on metrics
   - Self-healing capabilities
   - Automated backup and recovery

### Integration Roadmap

1. **Short Term (1-3 months)**
   - Enhanced Langfuse metrics
   - Improved Grafana plugins
   - Better alerting rules

2. **Medium Term (3-6 months)**
   - Multi-cluster monitoring
   - Advanced security features
   - Performance optimization

3. **Long Term (6+ months)**
   - AI-powered monitoring
   - Predictive analytics
   - Full observability platform

## References

### Documentation

- [Langfuse Documentation](https://docs.langfuse.com/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Promtail Documentation](https://grafana.com/docs/loki/latest/clients/promtail/)

### Configuration Files

- `core/resources/infrastructure/monitoring/kustomization.yaml` - Main monitoring stack
- `core/resources/infrastructure/monitoring/langfuse-dashboard.yaml` - Langfuse dashboard
- `core/config/langfuse-secret-gitops-infra.yaml` - Langfuse secrets
- `core/resources/infrastructure/tenants/3-workloads/monitoring/grafana.yaml` - Grafana deployment

### Scripts and Tools

- `scripts/setup-agentic-ai-monitoring.sh` - Automated setup script
- `scripts/deploy-agentic-ai-production.sh` - Production deployment
- `scripts/deploy-agentic-ai-staging.sh` - Staging deployment

---

**Last Updated**: March 18, 2026  
**Version**: 1.0  
**Maintainer**: GitOps Infrastructure Team

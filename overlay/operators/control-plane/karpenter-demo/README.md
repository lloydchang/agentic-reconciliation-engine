# Karpenter Demo: Just-in-Time Node Scaling

## Overview

This example demonstrates Karpenter integration with the GitOps Infra Control Plane for dynamic node provisioning across multiple cloud providers.

## Architecture

```
Hub Cluster (Flux Control Plane)
    ↓
Spoke Clusters with Karpenter
    ├── AWS EKS + Karpenter
    ├── Azure AKS + Karpenter
    └── GCP GKE + Karpenter
```

## Features Demonstrated

- **Multi-Cloud Node Scaling**: Karpenter configurations for AWS, Azure, and GCP
- **Just-in-Time Provisioning**: Nodes created only when needed
- **Cost Optimization**: Automatic consolidation and right-sizing
- **GitOps Management**: All Karpenter resources managed through Flux
- **Monitoring Integration**: Prometheus metrics and Grafana dashboards

## Deployment Steps

### 1. Deploy Hub Cluster with Flux

```bash
# Deploy the hub cluster with Flux control plane
kubectl apply -f ../../core/resources/flux/

# Deploy spoke clusters with Karpenter
kubectl apply -f ../../core/resources/tenants/2-clusters/
```

### 2. Configure Cloud Provider Credentials

```bash
# AWS - Update IRSA role
kubectl annotate serviceaccount karpenter -n karpenter \
  iam.amazonaws.com/role="KarpenterControllerRole-my-eks-cluster"

# Azure - Update workload identity
kubectl annotate serviceaccount karpenter -n karpenter \
  azure.workload.identity/client-id="your-client-id"

# GCP - Update workload identity
kubectl annotate serviceaccount karpenter -n karpenter \
  iam.gke.io/gcp-service-account="your-gcp-sa@project.iam.gserviceaccount.com"
```

### 3. Deploy Test Workloads

```bash
# Deploy sample workloads to trigger node provisioning
kubectl apply -f workloads/

# Monitor node provisioning
kubectl get nodes -w
```

## Files Structure

```
karpenter-demo/
├── README.md                    # This file
├── workloads/                   # Sample workloads for testing
│   ├── cpu-intensive.yaml       # CPU-intensive deployment
│   ├── memory-intensive.yaml    # Memory-intensive deployment
│   └── burst-workload.yaml     # Burst workload simulation
├── monitoring/                  # Monitoring configurations
│   ├── prometheus-rules.yaml   # Alerting rules
│   ├── grafana-dashboard.json  # Karpenter dashboard
│   └── service-monitor.yaml    # ServiceMonitor for Karpenter
└── patches/                    # Customization patches
    ├── aws-optimization.yaml   # AWS-specific optimizations
    ├── azure-optimization.yaml # Azure-specific optimizations
    └── gcp-optimization.yaml   # GCP-specific optimizations
```

## Test Scenarios

### Scenario 1: Gradual Scale-Up

Deploy workloads gradually to observe Karpenter's node provisioning behavior:

```bash
# Deploy initial workload
kubectl apply -f workloads/cpu-intensive.yaml

# Scale up gradually
kubectl scale deployment cpu-intensive --replicas=10
kubectl scale deployment cpu-intensive --replicas=50
kubectl scale deployment cpu-intensive --replicas=100
```

### Scenario 2: Burst Workload

Simulate sudden workload spikes:

```bash
# Deploy burst workload
kubectl apply -f workloads/burst-workload.yaml

# Monitor rapid node provisioning
kubectl get nodeclaims -A -w
```

### Scenario 3: Consolidation Test

Test Karpenter's consolidation capabilities:

```bash
# Deploy workloads
kubectl apply -f workloads/memory-intensive.yaml

# Scale down to trigger consolidation
kubectl scale deployment memory-intensive --replicas=1

# Observe node termination and consolidation
kubectl get nodes -w
```

## Monitoring

### Key Metrics to Watch

1. **Node Provisioning Rate**: How quickly nodes are created
2. **Node Consolidation**: Efficiency of node consolidation
3. **Cost per Node**: Cost optimization effectiveness
4. **Pod Scheduling Delay**: Time from pod creation to scheduling
5. **Resource Utilization**: Cluster utilization patterns

### Grafana Dashboard

Import the provided Grafana dashboard to visualize Karpenter metrics:

```bash
# Import dashboard
kubectl apply -f monitoring/grafana-dashboard.json
```

Dashboard panels include:
- Node provisioning timeline
- Instance type distribution
- Cost optimization metrics
- Consolidation effectiveness
- Resource utilization trends

## Cost Analysis

### Before Karpenter

- **Static Node Pools**: Fixed number of nodes provisioned 24/7
- **Over-provisioning**: 30-50% unused capacity for peak loads
- **Manual Scaling**: Requires manual intervention for scale changes

### After Karpenter

- **Dynamic Provisioning**: Nodes created only when needed
- **Right-Sizing**: Appropriate instance types for workloads
- **Automatic Consolidation**: Unused nodes terminated automatically

### Expected Savings

- **Compute Costs**: 20-40% reduction through right-sizing
- **Operational Overhead**: 90% reduction in manual scaling tasks
- **Resource Efficiency**: 60-80% improvement in utilization

## Troubleshooting

### Common Issues

1. **Nodes Not Provisioning**
   ```bash
   # Check Karpenter logs
   kubectl logs -f deployment/karpenter -n karpenter
   
   # Verify IAM permissions
   aws sts get-caller-identity
   ```

2. **Pods Stuck in Pending**
   ```bash
   # Check NodePool constraints
   kubectl describe nodepool default -n karpenter
   
   # Verify instance availability
   aws ec2 describe-instance-type-offerings
   ```

3. **Excessive Node Termination**
   ```bash
   # Check consolidation settings
   kubectl get nodepool default -n karpenter -o yaml
   
   # Review disruption budgets
   kubectl describe disruptionbudget
   ```

## Cleanup

```bash
# Remove test workloads
kubectl delete -f workloads/

# Remove Karpenter (if needed)
kubectl delete -f ../../core/resources/tenants/2-clusters/karpenter-*.yaml
```

## Next Steps

1. **Production Deployment**: Adapt configurations for production workloads
2. **Cost Monitoring**: Set up detailed cost tracking and alerts
3. **Performance Tuning**: Optimize instance types and configurations
4. **Automation**: Integrate with CI/CD pipelines for automated testing
5. **Multi-Region**: Extend Karpenter to multiple cloud regions

## Integration with Control Plane

This demo shows how Karpenter complements the GitOps Infra Control Plane:

- **Declarative Management**: Karpenter resources managed through Git
- **Automated Deployment**: Flux handles installation and configuration
- **Dependency Coordination**: Karpenter depends on cluster infrastructure
- **Multi-Cloud Consistency**: Unified approach across cloud providers
- **Observability**: Integrated with existing monitoring stack

The combination provides dynamic scaling while maintaining GitOps principles of infrastructure as code and automated deployment.

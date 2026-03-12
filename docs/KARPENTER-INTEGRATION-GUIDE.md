# Karpenter Integration Guide

## Overview

This guide explains how to integrate Karpenter for just-in-time node scaling with the GitOps Infrastructure Control Plane. Karpenter complements the control plane by providing dynamic node provisioning that works alongside Flux-based GitOps workflows.

## Architecture

```
Git Repository (Flux manifests)
    ↓
Flux Controller
    ↓
Karpenter HelmRelease + NodePool resources
    ↓
Karpenter Controller
    ↓
Cloud Provider APIs (AWS/Azure/GCP)
    ↓
Dynamic Node Provisioning
```

## Integration Components

### 1. Core Karpenter Resources

**karpenter-namespace.yaml**
- Creates dedicated namespace for Karpenter components
- Applies consistent labels for GitOps management

**karpenter-rbac.yaml**
- Service account with cloud provider IAM integration
- ClusterRole and ClusterRoleBinding for Karpenter permissions
- Multi-cloud RBAC support

**karpenter-helmrepo.yaml**
- Helm repository configuration for Karpenter charts
- Managed by Flux for automated updates

**karpenter-helmrelease.yaml**
- HelmRelease for Karpenter controller deployment
- Configurable values for different cloud providers
- Dependency management with Flux system

### 2. Cloud-Specific Configurations

**karpenter.yaml** (AWS)
- EC2NodeClass for AWS instance types
- NodePool with AWS-specific requirements
- Subnet and security group selectors

**karpenter-azure.yaml** (Azure)
- AKSNodeClass for Azure VM families
- NodePool with Azure-specific requirements
- Location and subnet configuration

**karpenter-gcp.yaml** (GCP)
- GCPNodeClass for Google Cloud machine families
- NodePool with GCP-specific requirements
- Project and location settings

## Deployment Scenarios

### Scenario 1: AWS EKS with Karpenter

```yaml
# Enable Karpenter for AWS clusters
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - karpenter-namespace.yaml
  - karpenter-rbac.yaml
  - karpenter-helmrepo.yaml
  - karpenter-helmrelease.yaml
  - karpenter.yaml
patchesStrategicMerge:
  - patches/aws-cluster-name.yaml
```

### Scenario 2: Azure AKS with Karpenter

```yaml
# Enable Karpenter for Azure clusters
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - karpenter-namespace.yaml
  - karpenter-rbac.yaml
  - karpenter-helmrepo.yaml
  - karpenter-helmrelease.yaml
  - karpenter-azure.yaml
patchesStrategicMerge:
  - patches/azure-cluster-name.yaml
```

### Scenario 3: Multi-Cloud Deployment

```yaml
# Enable Karpenter across all cloud providers
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - karpenter-namespace.yaml
  - karpenter-rbac.yaml
  - karpenter-helmrepo.yaml
  - karpenter-helmrelease.yaml
  - karpenter.yaml      # AWS
  - karpenter-azure.yaml  # Azure
  - karpenter-gcp.yaml    # GCP
```

## Configuration Customization

### Cluster-Specific Patches

Create patches for each cluster to customize Karpenter settings:

**patches/aws-cluster-name.yaml**
```yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: default
spec:
  template:
    spec:
      nodeClassRef:
        name: default
      requirements:
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m", "r"]
        - key: topology.kubernetes.io/zone
          operator: In
          values: ["us-west-2a", "us-west-2b", "us-west-2c"]
---
apiVersion: karpenter.k8s.aws/v1beta1
kind: EC2NodeClass
metadata:
  name: default
spec:
  subnetSelectorTerms:
  - tags:
      karpenter.sh/instancepool: "true"
      kubernetes.io/cluster: "my-eks-cluster"
  securityGroupSelectorTerms:
  - tags:
      karpenter.sh/instancepool: "true"
      kubernetes.io/cluster: "my-eks-cluster"
```

### Instance Type Optimization

Customize instance families based on workload requirements:

**Compute-Optimized**
```yaml
requirements:
  - key: karpenter.k8s.aws/instance-category
    operator: In
    values: ["c"]  # Compute optimized
instanceTypes:
  - "c5.large"
  - "c5.xlarge"
  - "c5.2xlarge"
```

**Memory-Optimized**
```yaml
requirements:
  - key: karpenter.k8s.aws/instance-category
    operator: In
    values: ["r"]  # Memory optimized
instanceTypes:
  - "r5.large"
  - "r5.xlarge"
  - "r5.2xlarge"
```

**General Purpose**
```yaml
requirements:
  - key: karpenter.k8s.aws/instance-category
    operator: In
    values: ["m"]  # General purpose
instanceTypes:
  - "m5.large"
  - "m5.xlarge"
  - "m5.2xlarge"
```

## Monitoring and Observability

### Karpenter Metrics

Monitor Karpenter operations with Prometheus:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: karpenter-metrics-config
  namespace: karpenter
data:
  config.yaml: |
    metrics:
      - name: karpenter_nodes_created
        help: Number of nodes created by Karpenter
      - name: karpenter_nodes_terminated
        help: Number of nodes terminated by Karpenter
      - name: karpenter_nodeclaims_created
        help: Number of NodeClaims created
      - name: karpenter_nodeclaims_bound
        help: Number of NodeClaims bound to nodes
```

### Grafana Dashboard

Create Grafana dashboard for Karpenter monitoring:

- Node provisioning rate
- Node termination events
- Cost optimization metrics
- Instance type distribution
- Cluster utilization trends

## Security Considerations

### IAM Permissions

Ensure proper IAM permissions for Karpenter:

**AWS IAM Policy**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateLaunchTemplate",
        "ec2:CreateFleet",
        "ec2:RunInstances",
        "ec2:CreateTags",
        "ec2:TerminateInstances",
        "ec2:DeleteLaunchTemplate",
        "ec2:DescribeLaunchTemplates",
        "ec2:DescribeInstances",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeImages",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeInstanceTypeOfferings",
        "ec2:DescribeAvailabilityZones",
        "ssm:GetParameter",
        "iam:PassRole"
      ],
      "Resource": "*"
    }
  ]
}
```

### Network Security

- Use VPC endpoints for private connectivity
- Apply network policies to restrict Karpenter traffic
- Enable encryption for node communications

## Cost Optimization

### Right-Sizing Strategies

1. **Workload Analysis**: Monitor resource usage patterns
2. **Instance Selection**: Choose appropriate instance families
3. **Spot Instances**: Use spot instances for non-critical workloads
4. **Consolidation**: Enable node consolidation for better utilization

### Budget Controls

Set limits to prevent cost overruns:

```yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: default
spec:
  limits:
    cpu: "1000"      # Maximum CPU cores
    memory: 1000Gi    # Maximum memory
  disruption:
    budgets:
    - nodes: "10"      # Maximum concurrent node changes
```

## Troubleshooting

### Common Issues

1. **Node Provisioning Failures**
   - Check IAM permissions
   - Verify subnet and security group configurations
   - Review instance type availability

2. **Pod Scheduling Issues**
   - Verify node pool requirements
   - Check taints and tolerations
   - Review resource requests and limits

3. **Cost Overruns**
   - Monitor node provisioning frequency
   - Review consolidation settings
   - Check for abandoned nodes

### Debug Commands

```bash
# Check Karpenter logs
kubectl logs -f deployment/karpenter -n karpenter

# List NodePools
kubectl get nodepools -A

# List NodeClaims
kubectl get nodeclaims -A

# Describe NodePool
kubectl describe nodepool default -n karpenter

# Check events
kubectl get events -n karpenter --sort-by='.lastTimestamp'
```

## Best Practices

1. **Start Conservative**: Begin with conservative limits and expand as needed
2. **Monitor Closely**: Set up comprehensive monitoring and alerting
3. **Test Thoroughly**: Validate configurations in non-production environments
4. **Document Changes**: Keep track of configuration changes and their impact
5. **Regular Reviews**: Periodically review and optimize configurations

## Integration with GitOps Workflows

Karpenter integrates seamlessly with GitOps Infrastructure Control Plane:

- **Declarative Configuration**: All Karpenter resources managed through Git
- **Automated Deployment**: Flux handles installation and updates
- **Dependency Management**: Karpenter depends on cluster infrastructure
- **Multi-Cloud Support**: Consistent patterns across cloud providers
- **Version Control**: Track all configuration changes in Git

This integration provides dynamic node scaling while maintaining the GitOps principles of declarative infrastructure management and automated deployment.

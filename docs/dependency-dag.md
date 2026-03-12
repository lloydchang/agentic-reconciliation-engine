# Infrastructure Dependency DAG

## Kustomization Level Dependencies
```
network-infra (1-network/)
    ↓ dependsOn
cluster-infra (2-clusters/)
    ↓ dependsOn
workload-infra (3-workloads/)
    ↓ dependsOn
karmada-infra (karmada/)
```

## Resource Level Dependencies

### AWS Dependencies
```
VPC (gitops-vpc) [order: 1]
    ↓ dependsOn
InternetGateway (gitops-igw) [order: 2]
    ↓ dependsOn
Subnets (gitops-*-subnet) [order: 3]
    ↓ dependsOn
RouteTable (gitops-public-rt) [order: 4]
    ↓ dependsOn
RouteTableAssociations (gitops-public-rta-*) [order: 5]

IAM Role (eks-cluster-role) [order: 1]
    ↓ dependsOn
IAM Policy (eks-cluster-policy) [order: 2]
    ↓ dependsOn
RolePolicyAttachment (eks-cluster-service-policy) [order: 3]
    ↓ dependsOn
EKS Cluster (gitops-eks-cluster) [order: 4]
    ↓ dependsOn
EKS Nodegroup (gitops-eks-nodegroup) [order: 5]
```

### Azure Dependencies
```
ResourceGroup (gitops-resource-group) [order: 1]
    ↓ dependsOn
VirtualNetwork (gitops-vnet) [order: 2]
    ↓ dependsOn
UserAssignedIdentity (gitops-aks-identity) [order: 1]
    ↓ dependsOn
AKS Cluster (gitops-aks-cluster) [order: 2]
```

### GCP Dependencies
```
ComputeNetwork (gitops-network) [order: 1]
    ↓ dependsOn
ComputeSubnets (gitops-subnet-*) [order: 2]
    ↓ dependsOn
IAMServiceAccount (gke-node-sa) [order: 1]
    ↓ dependsOn
GKE Cluster (gitops-gke-cluster) [order: 2]
    ↓ dependsOn
GKE NodePool (gitops-gke-nodepool) [order: 3]
```

## Benefits
- ✅ Explicit resource ordering
- ✅ Parallel execution where possible
- ✅ Failure isolation
- ✅ Clear dependency visualization
- ✅ Reliable infrastructure deployment

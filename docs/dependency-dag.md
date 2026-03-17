# Infrastructure Dependency DAG

## Complete DAG Overview

### Root Level Dependencies

```
gitops-infra-control-plane-root
├── core/operators/ (gitops-infra-control-plane)
│   ├── flux/ (flux-system) [ROOT]
│   ├── controllers/ [dependsOn: flux]
│   ├── karmada/ [dependsOn: flux]
│   ├── monitoring/ [dependsOn: flux]
│   └── consensus/ [dependsOn: flux]
└── core/resources/
    ├── flux/ [dependsOn: flux]
    ├── monitoring/ [dependsOn: flux]
    └── tenants/
        ├── 1-network/ (network-infra) [ROOT]
        ├── 2-clusters/ (cluster-infra) [dependsOn: network-infra]
        └── 3-workloads/ (workload-infra) [dependsOn: cluster-infra]
```

### Kustomization Level Dependencies

```
flux-system [ROOT]
    ↓ dependsOn
network-infra (1-network/) [ROOT]
    ↓ dependsOn
cluster-infra (2-clusters/)
    ↓ dependsOn
workload-infra (3-workloads/)
    ↓ dependsOn
gitops-infra-control-plane
    ↓ dependsOn
karmada-infra (karmada/)
```

### Example Variant Dependencies

```
complete-hub-spoke-with-consensus-ai
    ↓ dependsOn
gitops-infra-control-plane
    ↓ dependsOn
flux-system

template-multi-cloud-ai
    ↓ dependsOn
controllers
    ↓ dependsOn
tenants
    ↓ dependsOn
flux-system
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

- ✅ Explicit resource ordering through Flux dependsOn
- ✅ Parallel execution where possible for independent components
- ✅ Failure isolation through modular boundaries
- ✅ Clear dependency visualization and documentation
- ✅ Reliable infrastructure deployment with DAG guarantees
- ✅ Variant swapping support (opensource/small-business/enterprise)
- ✅ Multi-ecosystem modularity (rust, go, python, typescript, c#, java, bash)
- ✅ Component reusability across different deployment patterns

## Variant Support Matrix

### Open Source Variant

- Basic Flux controllers
- Core monitoring (Prometheus/Grafana)
- Standard networking
- Community tools
- **Labels:** `variant: opensource`

### Small Business Variant

- Enhanced monitoring
- Backup solutions
- Security scanning
- Cost optimization
- **Labels:** `variant: small-business`

### Enterprise Variant

- Full AI integration
- Advanced security
- Multi-cloud controllers
- Consensus orchestration
- **Labels:** `variant: enterprise`

## Ecosystem Modularity

### Rust Ecosystem

```
workload-infra/
├── rust/
│   ├── cargo-workloads/
│   ├── tokio-services/
│   └── actix-web-apps/
```

### Go Ecosystem

```
workload-infra/
├── go/
│   ├── gin-services/
│   ├── kubernetes-operators/
│   └── grpc-services/
```

### Python/uv Ecosystem

```
workload-infra/
├── python/
│   ├── fastapi-apps/
│   ├── apache-airflow/
│   ├── jupyter-notebooks/
│   └── poetry-workloads/
```

### TypeScript/Node.js Ecosystem

```
workload-infra/
├── typescript/
│   ├── nextjs-apps/
│   ├── nestjs-services/
│   ├── express-apis/
│   └── react-frontends/
```

### C#/.NET Ecosystem

```
workload-infra/
├── dotnet/
│   ├── aspnet-core-apps/
│   ├── blazor-apps/
│   └── entity-framework/
```

### Java/JVM Ecosystem

```
workload-infra/
├── java/
│   ├── spring-boot-apps/
│   ├── quarkus-services/
│   └── maven-gradle/
```

### Shell/Bash Ecosystem

```
workload-infra/
├── shell/
│   ├── cron-jobs/
│   ├── bash-core/core/automation/ci-cd/scripts/
│   └── system-core/automation/ci-cd/
```

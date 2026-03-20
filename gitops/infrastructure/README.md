# Infrastructure GitOps Repository

This directory contains Kubernetes-native infrastructure definitions managed by Crossplane and deployed via GitOps (Flux or ArgoCD).

## Structure

```
gitops/infrastructure/
├── base/
│   └── crossplane/
│       ├── providerconfigs/     # Cloud provider credentials & RBAC
│       ├── compositions/        # Compositions (templates) for each resource type
│       │   ├── eks-cluster/     # AWS EKS
│       │   ├── gke-cluster/     # GCP GKE
│       │   ├── aks-cluster/     # Azure AKS
│       │   ├── postgresql/      # PostgreSQL (RDS/CloudSQL/Flexible)
│       │   ├── redis/           # Redis (ElastiCache/Memorystore/Cache)
│       │   ├── backup-storage/  # Cross-cloud backup storage
│       │   └── load-balancer/   # Load balancers (ALB/CloudLB/AppGateway)
│       ├── claims/              # Example claims (requests)
│       └── kustomization.yaml   # Kustomize base configuration
├── overlays/
│   ├── prod/                    # Production overrides
│   ├── staging/                 # Staging overrides
│   └── dev/                     # Development overrides
└── README.md                    # This file
```

## Concepts

- **ProviderConfig**: Defines how Crossplane authenticates to cloud providers (AWS, GCP, Azure). Stored in `crossplane-system` namespace. Supports IRSA/Workload Identity (production) or secrets (dev).
- **XRDs (Compositition Resource Definitions)**: Define the custom resource kinds (e.g., `XEKSCluster`) that users will create. They define the schema (spec/status) of the resource.
- **Compositions**: Templates that map the abstract resource request (XR) to concrete cloud provider resources. Compositions use patches (`patch` and `toCompositeFieldPath`) to wire dependencies.
- **Claims (XClients)**: Simplified resource requests. Teams submit Claims (e.g., `EKSClusterClaim`) instead of dealing with XRs directly. Claims auto-generate the corresponding XR.

## Workflow

1. **Install Crossplane** in management cluster
2. **Configure ProviderConfigs** with cloud credentials
3. **Define XRD + Composition** for each resource type
4. **Create Claims** to request infrastructure
5. **Crossplane reconciles**: Claim → XR → Cloud resources
6. **GitOps**: All YAML committed to git → Flux/ArgoCD applies → Crossplane provisions

## Example Request Flow

```yaml
# Team submits a Claim (simplified)
apiVersion: example.crossplane.io/v1alpha1
kind: EKSClusterClaim
metadata:
  name: ai-infrastructure-prod
  namespace: production
spec:
  compositionRef:
    name: eks-cluster-composition
  parameters:
    region: us-west-2
    nodeGroups:
      - name: general
        instanceTypes: [t3.medium, t3.large]
        minSize: 3
        maxSize: 10
        diskSize: 100
```

Crossplane:
1. Creates `XEKSCluster` resource (XR)
2. Composition patches create:
   - `VPC` (networking)
   - `EKSCluster` + `NodeGroup` + `FargateProfile` (compute)
   - `SecurityGroup` rules
   - `StorageClass` for dynamic provisioning
3. All resources tagged with same Crossplane identity
4. Connection details (kubeconfig, endpoint) written back to XR status

## Isolation

Isolation is achieved through **ProviderConfig `allowedNamespaces`** and **Kubernetes RBAC**:

- `ProviderConfig.spec.allowedNamespaces`: List of namespaces that can use this provider config
- `RoleBinding` grants `use` verb on ProviderConfig to specific service accounts/namespaces
- Teams only see resources in their namespace
- Single Crossplane instance serves all teams (simpler ops)

## Multi-Cloud Support

- Cloud-agnostic Claims: Teams can specify `provider: aws|gcp|azure` and the appropriate Composition handles provider-specific details
- Compositions may differ per cloud (e.g., EKS vs AKS vs GKE have different parameters)
- Crossplane handles provider-specific resource naming, dependencies, and connection details

## Migration from Terraform

Phase 0: Install Crossplane + ProviderConfigs
Phase 1: Create Compositions equivalent to existing Terraform resources
Phase 2: Add GCP/Azure compositions
Phase 3: Migrate multi-cloud orchestrator scripts to use Crossplane
Phase 4: Integrate with GitOps
Phase 5: Decommission Terraform

See `docs/CROSSPLANE-MIGRATION-PLAN.md` for full migration plan.

## References

- Crossplane Docs: https://docs.crossplane.io/
- Provider AWS: https://github.com/crossplane-contrib/provider-aws
- Provider GCP: https://github.com/crossplane-contrib/provider-gcp
- Provider Azure: https://github.com/crossplane/provider-azure
- GitOps with Flux: https://fluxcd.io/flux/
- GitOps with ArgoCD: https://argo-cd.readthedocs.io/

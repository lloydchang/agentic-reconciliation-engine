# Legacy IaC Migration Strategy

## Overview

This document outlines the strategy for migrating existing workloads from Terraform, Blueprints, CDK, CloudFormation, Bicep, and ARM to the GitOps Infrastructure Control Plane. The approach uses a hybrid strategy: industry-standard CLIs for initial cluster bootstrap, then transitions to continuous reconciliation for ongoing infrastructure management.

## Migration Philosophy

### No Big-Bang Migration Required
The GitOps Infrastructure Control Plane is designed to **coexist with existing infrastructure**. Organizations can maintain their current IaC tools while gradually adopting the new GitOps approach.

### Three-Tier Migration Approach

#### 1. Keep Existing Infrastructure (Recommended)
- Existing Terraform/CloudFormation resources continue running unchanged
- New resources are provisioned through the GitOps control plane
- Migration occurs naturally when resources require updates or replacement

#### 2. Hybrid Transition Period
```yaml
# Example: Existing VPC (Terraform) + New EKS (GitOps)
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: new-eks-cluster
spec:
  dependsOn:
  - name: existing-vpc-terraform  # Reference existing resource
    namespace: legacy-infrastructure
```

#### 3. Full GitOps Adoption
- All infrastructure managed through Flux
- Legacy IaC tools deprecated
- Single source of truth achieved

## Fallback Strategy for Non-Native Resources

From `infrastructure/fallback/README.md`, the control plane provides a hierarchical fallback strategy:

### 1. Official Kubernetes Operator (Preferred)
Use official operators when native cloud controller support is unavailable.

**Examples:**
- `cert-manager` for TLS certificates
- `ingress-nginx` for ingress controllers  
- `external-dns` for DNS management
- `prometheus-operator` for monitoring

### 2. Flux-Managed Kubernetes Job
For one-off or complex deployments, use Flux-managed Jobs to run legacy IaC commands.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: terraform-apply
  namespace: flux-system
spec:
  template:
    spec:
      containers:
      - name: terraform
        image: hashicorp/terraform:latest
        command: ["terraform", "apply", "-auto-approve"]
        workingDir: /workspace
        volumeMounts:
        - name: tf-config
          mountPath: /workspace
      volumes:
      - name: tf-config
        configMap:
          name: terraform-config
      restartPolicy: OnFailure
```

### 3. Targeted Crossplane Provider (Last Resort)
Only use Crossplane providers when absolutely necessary and no other options exist. This should be avoided to maintain the no-abstraction principle.

## Conversion Tools and Techniques

### AI-Assisted Conversion
AI coding agents can convert existing IaC to Kubernetes CRs:

```bash
# Convert Terraform to AWS ACK CRs
terraform show -json | ai-convert-to-ack-crds > aws-resources.yaml

# Convert CloudFormation to Azure ASO CRs  
aws cloudformation get-template --stack-name my-stack | ai-convert-to-aso-crds > azure-resources.yaml

# Convert Bicep/ARM to Azure ASO CRs
az deployment group show --resource-group my-rg --name my-deployment | ai-convert-to-aso-crds > azure-resources.yaml
```

### Native Controller Mapping

| Legacy IaC | Target Controller | Example Conversion |
|------------|------------------|-------------------|
| Terraform AWS resources | AWS ACK | `aws_instance` → `ec2.services.k8s.aws/Instance` |
| CloudFormation | Azure ASO | `AWS::EC2::Instance` → `compute.azure.com/VirtualMachine` |
| Bicep/ARM | Azure ASO | `Microsoft.Compute/virtualMachines` → `compute.azure.com/VirtualMachine` |
| CDK | Native cloud controllers | CDK constructs → corresponding ACK/ASO/KCC CRs |

## Recommended Migration Phases

### Phase 1: Parallel Operation (Weeks 1-4)
1. **Deploy GitOps control plane** alongside existing infrastructure
2. **Start with greenfield projects** using the new approach
3. **Document dependencies** between existing and new resources
4. **Establish communication patterns** between legacy and GitOps systems

**Actions:**
```bash
# Deploy control plane
./scripts/deploy-gitops-infrastructure.sh

# Create dependency mapping
kubectl create namespace legacy-infrastructure
kubectl apply -f legacy-resource-dependencies.yaml
```

### Phase 2: Gradual Migration (Weeks 5-12)
1. **Convert resources** when they need major updates
2. **Use AI-assisted conversion** for complex resources
3. **Maintain both systems** during transition
4. **Validate equivalence** between legacy and new resources

**Actions:**
```bash
# Convert specific resources
ai-convert-terraform-to-ack --state-file terraform.tfstate --output aws-resources.yaml

# Validate equivalence
./scripts/validate-migration.sh --legacy terraform --new gitops --resource-type vpc
```

### Phase 3: Full GitOps (Weeks 13-16)
1. **Migrate remaining critical resources**
2. **Decommission legacy IaC tools**
3. **Establish single source of truth**
4. **Optimize dependency chains**

**Actions:**
```bash
# Final migration sweep
./scripts/migrate-remaining-resources.sh

# Cleanup legacy tools
./scripts/decommission-legacy-iac.sh
```

## Dependency Management During Migration

### Cross-System Dependencies
Use Flux `dependsOn` to create dependencies between legacy and GitOps-managed resources:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: new-application
  namespace: flux-system
spec:
  dependsOn:
  - name: existing-database-terraform
    namespace: legacy-infrastructure
  - name: existing-network-cloudformation
    namespace: legacy-infrastructure
  interval: 5m
  path: ./infrastructure/tenants/3-workloads/new-app
```

### Resource Discovery
Automatically discover existing resources and create dependency mappings:

```bash
# Generate dependency mapping
./scripts/generate-migration-dependencies.sh --legacy-state terraform.tfstate --output dependencies.yaml
```

## Risk Mitigation

### Migration Risks
1. **Resource drift** between legacy and GitOps systems
2. **Dependency conflicts** during transition
3. **Team skill gaps** with new tools
4. **Operational complexity** of running two systems

### Mitigation Strategies
1. **Comprehensive testing** before each migration phase
2. **Rollback procedures** for each migration step
3. **Team training** and documentation
4. **Monitoring and alerting** for both systems

### Validation Framework
```bash
# Pre-migration validation
./scripts/validate-migration-readiness.sh

# Post-migration verification  
./scripts/verify-migration-success.sh

# Drift detection
./scripts/detect-migration-drift.sh
```

## Team Considerations

### Skill Development
- **Flux CD** training for operations teams
- **Kubernetes CRD** knowledge for infrastructure teams
- **Cloud controller** specific training (ACK/ASO/KCC)

### Process Changes
- **Git workflow** adoption for infrastructure changes
- **Pull request reviews** for infrastructure modifications
- **Automated testing** for infrastructure deployments

### Tool Transition
- **IDE plugins** for Kubernetes CR development
- **CI/CD integration** for infrastructure validation
- **Monitoring dashboards** for GitOps operations

## Success Metrics

### Technical Metrics
- **Migration completion rate**: % of resources converted
- **Deployment frequency**: Infrastructure change rate
- **Lead time**: Time from change to production
- **Change failure rate**: % of failed deployments

### Operational Metrics  
- **System reliability**: Uptime during migration
- **Team productivity**: Resources managed per engineer
- **Cost efficiency**: Infrastructure cost optimization
- **Compliance adherence**: Policy compliance rate

## Troubleshooting

### Common Issues

#### Resource Conflicts
```bash
# Identify conflicting resources
kubectl get crd | grep -E "(ec2|compute|network)"
kubectl describe <resource-type> <resource-name>
```

#### Dependency Issues
```bash
# Validate dependency chains
./scripts/generate-dag-visualization.sh --validate-only
```

#### Conversion Errors
```bash
# Debug AI conversion
ai-convert-terraform-to-ack --debug --input terraform.tfstate --output debug.yaml
```

### Emergency Rollback
```bash
# Emergency rollback to legacy IaC
./scripts/emergency-rollback.sh --to terraform --resources vpc,subnet,security-group
```

## Conclusion

The GitOps Infrastructure Control Plane provides a flexible, low-risk migration path from legacy IaC tools. By following the gradual migration approach, organizations can:

- **Minimize disruption** to existing operations
- **Build confidence** in the new system gradually
- **Maintain business continuity** throughout the transition
- **Achieve full GitOps** adoption at their own pace

The key is to start small, validate thoroughly, and expand incrementally rather than attempting a risky big-bang migration.

## See Also

- **Flux Documentation**: [Flux CD Getting Started](https://fluxcd.io/docs/get-started/)
- **AWS ACK**: [AWS Controllers for Kubernetes](https://aws.github.io/aws-controllers-k8s/)
- **Azure ASO**: [Azure Service Operator](https://github.com/Azure/azure-service-operator)
- **GCP KCC**: [Kubernetes Config Connector](https://cloud.google.com/config-connector/docs)
- **Fallback Strategy**: `infrastructure/fallback/README.md`
- **Dependency Management**: `scripts/generate-dag-visualization.sh`

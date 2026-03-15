# Migration Guide: Converting Existing IaC to GitOps Control Plane

## Overview

This guide documents the approach for handling existing workloads built with push-based Infrastructure as Code (IaC) tools such as Terraform, AWS CloudFormation/CDK, Azure Blueprints/ARM/Bicep, and GCP Deployment Manager when adopting the GitOps Infra Control Plane using Flux + Crossplane + CAPI.

## Core Philosophy

The GitOps approach employs a hybrid strategy: push-based tools for initial cluster bootstrap, transitioning to continuous reconciliation for ongoing infrastructure management.

- **Phased Migration**: Use industry-standard CLIs (eksctl, az, gcloud) for initial Hub cluster creation, then leverage Crossplane + CAPI for declarative, self-healing infrastructure management.
- **Push-Based IaC (Terraform, CDK, etc.)**: Execute once, create state files, require external orchestration for dependencies - used only for initial bootstrap.
- **GitOps Control Plane**: Continuous reconciliation using Crossplane + CAPI, no state files, Flux `dependsOn` for DAG dependencies - used for ongoing management.

**Key Advantage**: Self-healing infrastructure that automatically maintains desired state without human intervention.

## Migration Requirements

### Continuous Reconciliation Advantage

Existing IaC workloads can be enhanced with continuous reconciliation capabilities. The repository uses industry-standard CLIs for initial Hub cluster setup, then provides 24/7 automated drift detection and repair for ongoing operations - something traditional IaC cannot achieve without complex external orchestration.

### No Built-in Conversion Tools

The repository does not contain automated migration utilities. Conversion must be performed manually or with external assistance.

### Manual Migration Required

All workloads must be rewritten into:

- Flux-compatible Kustomization.yaml manifests
- Crossplane XRDs/Compositions and CAPI resources for cloud resources
- Proper Flux `dependsOn` relationships for dependency sequencing

## Conversion Process

### Step 1: Resource Inventory

Analyze existing IaC to identify core components:

- Network infrastructure
- Compute clusters
- Storage resources
- Security configurations
- Application workloads

### Step 2: Map to Controller Resources

Translate each IaC resource to Crossplane XRDs and CAPI resources:

**AWS Resources:**

- VPCs, subnets → XNetwork
- EKS clusters → XCluster (CAPI)
- IAM roles/policies → Crossplane-managed IAM or external IAM pipelines

**Azure Resources:**

- VNets, subnets → XNetwork
- AKS clusters → XCluster (CAPI)
- RBAC → platform IAM workflows

**GCP Resources:**

- VPCs, subnets → XNetwork
- GKE clusters → XCluster (CAPI)
- IAM → platform IAM workflows

### Step 3: Define Dependencies

Use Flux `dependsOn` to establish proper sequencing:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: aws-network
dependsOn:
- name: azure-identity-setup  # Cross-cloud dependency
```

### Step 4: Testing and Validation

- Deploy to staging environment
- Validate resource creation via cloud APIs
- Test dependency chains with DAG visualization scripts
- Verify reconciliation behavior

## AI-Assisted Conversion

While no built-in tools exist, an AI coding agent can assist with conversion by:

- Analyzing source IaC syntax and parameters
- Generating equivalent Crossplane XRD claims
- Mapping resource dependencies

**Requirements for AI Conversion:**

- Access to original IaC source files
- Understanding of target cloud provider APIs
- Manual review and testing of generated manifests

**Limitations:**

- AI generation requires human validation
- Complex dependencies may need manual refinement
- One-way conversion (no reversion capability)

## Key Considerations

### State Management

- No Terraform state files to migrate
- Cloud APIs serve as the source of truth
- Reconciliation handles configuration drift automatically

### Dependency Orchestration

- Replace pipeline-based dependency management with Flux DAGs
- Ensure cross-cloud relationships are properly sequenced

### Security and Secrets

- Use SealedSecrets or external secret management
- Avoid hardcoded credentials in manifests

## Validation

The repository includes testing frameworks for validating migrated workloads:

- Permutation testing for dependency scenarios
- DAG visualization scripts (`generate-dag-visualization.sh`)
- Integration tests for cross-cloud resource relationships

## Summary

Migration from push-based IaC to GitOps control plane requires manual conversion to declarative manifests. While AI assistance can accelerate the process, all generated code must be thoroughly tested and validated. The result is infrastructure that self-heals and maintains proper dependency ordering without external orchestration.

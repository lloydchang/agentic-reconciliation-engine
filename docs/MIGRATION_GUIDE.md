# Migration Guide: Converting Existing IaC to GitOps Control Plane

## Overview

This guide documents the approach for handling existing workloads built with push-based Infrastructure as Code (IaC) tools such as Terraform, AWS CloudFormation/CDK, Azure Blueprints/ARM/Bicep, and GCP Deployment Manager when adopting the GitOps Infrastructure Control Plane using Flux + Cloud Controllers (ACK/ASO/KCC).

## Core Philosophy

The GitOps approach fundamentally differs from push-based IaC tools:

- **Push-Based IaC (Terraform, CDK, etc.)**: Execute once, create state files, require external orchestration for dependencies.
- **GitOps Control Plane**: Continuous reconciliation using native Kubernetes controllers (ACK/ASO/KCC), no state files, Flux `dependsOn` for DAG dependencies.

## Migration Requirements

### Hybrid Compatibility
Existing IaC workloads can be gradually migrated to this GitOps framework. The repository uses industry-standard CLIs for initial cluster bootstrap, then transitions to declarative, controller-managed infrastructure for ongoing operations.

### No Built-in Conversion Tools
The repository does not contain automated migration utilities. Conversion must be performed manually or with external assistance.

### Manual Migration Required
All workloads must be rewritten into:
- Flux-compatible Kustomization.yaml manifests
- ACK/ASO/KCC Custom Resource Definitions (CRDs) for cloud resources
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
Translate each IaC resource to equivalent ACK/ASO/KCC custom resources:

**AWS Resources:**
- VPCs, subnets → ACK EC2 custom resources
- EKS clusters → ACK EKS custom resources
- IAM roles/policies → ACK IAM custom resources

**Azure Resources:**
- VNets, subnets → ASO Network custom resources
- AKS clusters → ASO ContainerService custom resources
- RBAC → ASO Authorization custom resources

**GCP Resources:**
- VPCs, subnets → KCC Compute custom resources
- GKE clusters → KCC Container custom resources
- IAM → KCC IAM custom resources

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
- Generating equivalent ACK/ASO/KCC YAML manifests
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

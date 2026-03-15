# Legacy IaC Migration Strategy

## Overview

This document describes how to migrate from existing Terraform, CDK, CloudFormation, Bicep, and
ARM workloads to continuous reconciliation via the GitOps Infra Control Plane. The approach is
designed to be gradual and low-risk. No big-bang migration is required.

---

## Migration Philosophy

### Coexistence first

The GitOps Infra Control Plane is designed to coexist with existing infrastructure. Organizations
can maintain current IaC tools while gradually adopting the new GitOps approach. Migration occurs
naturally when resources require updates or replacement — not on a forced schedule.

### What you are migrating toward

The target state is:

- All cloud resources managed as Crossplane XRDs in Git
- All spoke clusters running their own Flux agent pulling from Git
- All secrets delivered via ESO + workload identity, hub not in the path
- CI gate enforcing deletion guards and policy checks before any change reaches the hub

You are not migrating toward re-implementing the same resources in a different IaC syntax. You are
migrating toward controllers that watch those resources 24/7 and repair drift without human
intervention.

---

## Three Migration Modes

### Mode 1: Keep existing, grow new (recommended starting point)

Existing Terraform/CloudFormation resources continue running unchanged. New resources are
provisioned through the GitOps control plane. Migration occurs when resources require significant
updates or replacement.

This is the lowest-risk starting point. It allows the team to build confidence in the new system
on non-critical resources before migrating production workloads.

### Mode 2: Hybrid transition

Existing resources are referenced by the GitOps control plane but not yet migrated. Flux
`dependsOn` allows new GitOps-managed resources to depend on existing externally-managed
resources:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: new-eks-cluster
  namespace: flux-system
spec:
  dependsOn:
    - name: existing-vpc-terraform
      namespace: legacy-infrastructure
  interval: 5m
  path: ./infrastructure/tenants/2-clusters/eks
  sourceRef:
    kind: GitRepository
    name: infrastructure-repo
```

### Mode 3: Full GitOps adoption

All infrastructure managed through Flux and Crossplane. Legacy IaC tools deprecated. Single
source of truth achieved. This is the end state, not the starting point.

---

## Conversion Approach

### Crossplane Compositions as the migration target

When migrating a resource, the goal is not to produce raw provider-specific CRDs. The goal is to
author a Crossplane Composition that abstracts the resource behind a cloud-agnostic XRD. This is
a one-time platform team investment per resource type; all subsequent use by spoke teams is
through the cloud-agnostic XRD.

Example: migrating an AWS RDS instance managed by Terraform.

Step 1 — Platform team authors an `XDatabase` Composition that maps to RDS on AWS.
Step 2 — Spoke team replaces the Terraform `aws_db_instance` with an `XDatabase` CR in Git.
Step 3 — Crossplane begins managing the resource; Terraform state is archived.
Step 4 — Drift is now detected and repaired automatically, 24/7.

### Native controller mapping (for reference)

These are the underlying providers that Crossplane Compositions translate to. Spoke teams do not
write these directly — Compositions handle the translation.

| Legacy IaC | Crossplane provider target | Example resource |
|---|---|---|
| Terraform AWS resources | provider-aws | `XDatabase` → RDS managed resource |
| CloudFormation | provider-aws | `XNetwork` → VPC managed resource |
| Bicep / ARM | provider-azure | `XDatabase` → Azure Database managed resource |
| CDK (AWS) | provider-aws | CDK constructs → Composition-managed resources |
| CDK (Azure) | provider-azure | CDK constructs → Composition-managed resources |

### Fallback for resources with no Composition

If a Crossplane Composition does not yet exist for a resource type, use this fallback hierarchy:

1. **Official Kubernetes operator** — cert-manager, external-dns, prometheus-operator, etc.
2. **Flux-managed Kubernetes Job** — run the legacy IaC tool as a Job under Flux management:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: terraform-apply-legacy-vpc
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
            name: terraform-config-legacy-vpc
      restartPolicy: OnFailure
```

3. **Raw cloud CRD** (last resort) — only when no Composition exists and no
   operator is available. Document the reason and add a Composition authoring task to the backlog.

---

## Migration Phases

### Phase 1: Parallel operation (weeks 1–4)

1. Deploy the hub cluster and bootstrap cluster alongside existing infrastructure
2. Start with greenfield resources only — no migration of existing resources in this phase
3. Document dependencies between existing and new resources
4. Validate the CI gate, Flux reconciliation, Crossplane, and ESO on new resources
5. Build the team's operational confidence with the new system on low-risk workloads

### Phase 2: Gradual migration (weeks 5–12)

1. Identify existing resources ready for migration (those requiring major updates or replacement)
2. Author Crossplane Compositions for target resource types
3. Replace Terraform/CloudFormation resources with XRDs one at a time
4. Validate Crossplane drift detection on each migrated resource:
   - Manually modify the resource in the cloud console
   - Verify Crossplane detects and reverts the change within minutes
5. Archive the corresponding Terraform state or CloudFormation stack after validation
6. Migrate secrets from hub SOPS push to ESO + workload identity per spoke as spokes are
   provisioned or re-provisioned

### Phase 3: Full GitOps (weeks 13–16)

1. Migrate remaining critical resources using Compositions
2. Decommission legacy IaC pipelines for migrated resources
3. Confirm all spokes have their own Flux agent and ESO instance
4. Confirm no spoke secrets are delivered via hub SOPS push (ESO is the primary path)
5. Validate hub cold-start procedure using the bootstrap cluster

---

## Secrets Migration

The original v1 architecture used hub SOPS push — the hub decrypted secrets and delivered
plaintext objects to spokes. The target state is ESO + workload identity per spoke.

Migrating existing SOPS-encrypted secrets to ESO:

1. Store the secret value in the spoke's cloud vault (AWS SM, AKV, or GCP SM)
2. Configure ESO `ExternalSecret` resource on the spoke referencing the vault path
3. Validate ESO delivers the secret correctly
4. Remove the SOPS-encrypted secret from the Git repository
5. Verify the hub age key is backed up in a cloud key vault before removing SOPS config

SOPS/age is retained as a fallback for on-prem spokes and secrets with no natural cloud vault
home. It is not the primary path.

---

## Risk Mitigation

### Key migration risks

| Risk | Mitigation |
|---|---|
| Resource drift between legacy and GitOps systems during transition | Run both systems in read-only mode initially; migrate one resource at a time |
| Accidental deletion of a migrated resource via the CI gate | Deletion guard blocks removal of stateful XRDs without explicit approval annotation |
| Dependency conflicts during transition | Use Flux `dependsOn` to express cross-system dependencies explicitly |
| SOPS age key loss during secrets migration | Back up the age key to a cloud key vault before beginning migration |
| Crossplane Composition not yet available for a resource type | Use fallback hierarchy (operator → Flux Job → raw CRD) and add Composition to backlog |

### Rollback

Each migration step is independently reversible. Crossplane `deletionPolicy: Orphan` on migrated
resources ensures Crossplane can be removed without deleting the underlying cloud resource. Set
this explicitly on all migrated resources until the migration is fully validated:

```yaml
apiVersion: platform.example.com/v1alpha1
kind: XDatabase
metadata:
  name: orders-db
  annotations:
    crossplane.io/paused: "false"
spec:
  deletionPolicy: Orphan   # Cloud resource survives if XRD is deleted
  engine: postgres
  version: "15"
```

---

## Success Criteria

A migration phase is complete when:

- Migrated resources are managed by Crossplane and reconciled automatically
- Drift detection is validated: manual modification is reverted within minutes
- Corresponding legacy IaC state/stack is archived
- No migrated resource still depends on hub SOPS push for secret delivery (or documented
  exception with ESO migration planned)
- CI gate is blocking deletions and policy violations for migrated resources

---

## See Also

- [Architecture](./ARCHITECTURE.md) — component details and Crossplane Composition guide
- [Implementation Plan](./implementation_plan.md) — step-by-step deployment
- [Flux documentation](https://fluxcd.io/docs/)
- [Crossplane documentation](https://docs.crossplane.io/)
- [External Secrets Operator documentation](https://external-secrets.io/latest/)

# Migration Prerequisites Verification Checklist

**Crossplane Migration Phase 0: Verify Environment Ready**

---

## Crossplane Installation

### Providers

- [ ] **provider-aws** installed and HEALTHY
  ```bash
  kubectl get providers provider-aws -n crossplane-system
  # HEALTHY=True
  ```
- [ ] **provider-azure** installed and HEALTHY
- [ ] **provider-gcp** installed and HEALTHY
- [ ] **provider-kubernetes** installed and HEALTHY (for managing spoke clusters)
- [ ] **provider-k8s** (if different) installed for local cluster resources

**All providers installed?**
```bash
kubectl get providers -n crossplane-system
# Expected: 4 providers, all HEALTHY
```

---

## ProviderConfigs

- [ ] **AWS ProviderConfig** exists with proper credentials (InjectedIdentity or Secret)
  ```bash
  kubectl get providerconfig aws-provider -n crossplane-system -o yaml
  ```
  - Verify: `spec.credentials.source: InjectedIdentity` (preferred) or SecretRef
  - Verify IRSA/Workload Identity is properly configured if using InjectedIdentity

- [ ] **Azure ProviderConfig** exists
  - Verify: `spec.credentials` fields populated (clientID, tenantID, subscriptionID)
  - Or: InjectedIdentity if using managed identity

- [ ] **GCP ProviderConfig** exists
  - Verify: Workload Identity or service account key
  - Check `gcp.compute.gcp.crossplane.io/v1beta1` provider config

- [ ] **Kubernetes ProviderConfig** exists (for managing K8s resources)
  ```bash
  kubectl get providerconfig kubernetes-provider -n crossplane-system
  ```

---

## GitOps Integration

### Flux Configuration

- [ ] Flux is installed and healthy
  ```bash
  kubectl get pods -n flux-system
  # All pods Running
  ```

- [ ] GitRepository for infrastructure exists
  ```bash
  kubectl get gitrepository -n flux-system
  ```

- [ ] Kustomization for Crossplane resources exists and synced
  ```bash
  kubectl get kustomization crossplane -n flux-system
  # READY=True, SYNC SUCCESSFUL
  ```

- [ ] Flux has access to Git repository (SSH key or HTTPS token configured)

**Verify sync**:
```bash
kubectl get kustomization -n flux-system -o wide
# Check LastAttemptedRevision, LastAppliedRevision
```

---

### Repository Structure

- [ ] Crossplane resources committed to Git:
  - `core/operators/control-plane/crossplane/xrds/`
  - `core/operators/control-plane/crossplane/compositions/`
  - `core/operators/control-plane/crossplane/providers/`
  - `core/operators/control-plane/crossplane/kustomization.yaml`

- [ ] Flux Kustomization points to correct path in repo
  ```yaml
  spec:
    path: ./core/operators/control-plane/crossplane/
    prune: true
    validation: client
  ```

---

## RBAC & Security

### Service Accounts

- [ ] Crossplane service account has necessary permissions
  ```bash
  kubectl get sa -n crossplane-system crossplane
  ```

- [ ] Provider pods have IAM roles / service accounts attached
  - AWS: IAM OIDC provider established, IAM roles with trust to `crossplane-system` SA
  - Azure: Managed identity or service principal with Contributor role on subscriptions
  - GCP: Workload Identity with IAM roles binding to KSA

---

### Network Policies

- [ ] Crossplane namespace has restricted ingress/egress if required
  - Provider egress to cloud APIs allowed
  - Crossplane pods can query K8s API

---

## Testing Infrastructure

### Test Cluster Available

- [ ] Development cluster (Kind or EKS) available for testing
- [ ] `kubectl` context configured to dev cluster
- [ ] Provider credentials available for at least ONE cloud (AWS or GCP or Azure)

### Test Managed Resource

- [ ] Can create a simple managed resource (S3 bucket, or equivalent)
  ```bash
  # Example: Test AWS provider
  cat <<EOF | kubectl apply -f -
  apiVersion: s3.aws.crossplane.io/v1beta1
  kind: Bucket
  metadata:
    name: crossplane-test-bucket-$(date +%s)
    namespace: crossplane-system
  spec:
    forProvider:
      locationConstraint: us-west-2
    providerConfigRef:
      name: aws-provider
  EOF
  ```

- [ ] Bucket created in AWS console after 30-60 seconds
- [ ] Can delete bucket successfully
  ```bash
  kubectl delete bucket <name> -n crossplane-system
  ```

---

## Backup & Recovery

### Terraform State Backup

- [ ] All Terraform state files backed up to S3 (or GCS, Azure Blob)
- [ ] State files copied to archival location (Glacier, cold storage)
- [ ] Documented state restore procedure

**Backup verification**:
```bash
# AWS example
aws s3 ls s3://your-terraform-state-bucket/statefiles/
# Should see .tfstate files with recent timestamps
```

---

### Git Repository Backup

- [ ] Git repository has recent backup or is mirrored
- [ ] Flux system configuration export available
  ```bash
  flux get all --export > flux-backup.yaml
  ```

---

## Multi-Cloud Orchestrator

### Current State

- [ ] `multi_cloud_orchestrator.py` functional and tested
- [ ] `multi-cloud-abstraction.js` functional
- [ ] `multi-cloud-scatter-gather.go` workflows compiled and tested
- [ ] All existing Terraform-dependent automation has been identified

### Crossplane Integration Branch

- [ ] Feature branch created: `feature/crossplane-migration`
- [ ] Multi-cloud orchestrator will be updated to support Crossplane as alternate provider
- [ ] Orchestrator will maintain backwards compatibility during migration (Terraform fallback)

---

## Kubernetes API Access

- [ ] Can list Crossplane resources:
  ```bash
  kubectl get xdatabases.platform.example.com
  kubectl get xclusters.platform.example.com
  kubectl get compositions
  ```

- [ ] Can view provider health:
  ```bash
  kubectl get providers -n crossplane-system
  kubectl get providerconfigs -n crossplane-system
  ```

---

## Cloud Provider Credentials

### AWS

- [ ] IAM OIDC provider enabled on hub cluster EKS (if using IRSA)
  ```bash
  # Check OIDC provider
  aws iam list-open-id-connect-providers | grep oidc.eks.<region>.amazonaws.com/id/<cluster-id>
  ```
- [ ] IAM roles created for Crossplane (if not using Secrets)
  - `crossplane-aws-provider-role` with `AdministratorAccess` or scoped policy
  - OIDC provider trust established
- [ ] S3 bucket for Terraform state accessible (read/write)
- [ ] IAM user/role with programmatic access for initial setup (if needed)

### GCP

- [ ] Workload Identity enabled on GKE cluster (if using GKE hub)
  ```bash
  gcloud container clusters describe <cluster-name> --region <region> --format="value(addonsConfig.workloadIdentityConfig)"
  ```
- [ ] IAM policy binding: `roles/iam.workloadIdentityUser` for Crossplane SA
- [ ] Service account with proper roles exists: `roles/editor` or custom

### Azure

- [ ] Managed identity or service principal exists with Contributor role
- [ ] Client ID / Tenant ID / Subscription ID documented
- [ ] Kubernetes secret exists if using Secret-based credentials:
  ```bash
  kubectl get secret -n crossplane-system azure-creds -o yaml
  ```

---

## Monitoring & Alerting

- [ ] Prometheus/Grafana monitoring for Crossplane installed
- [ ] Alerts configured for:
  - Provider unhealthy
  - XResource not Ready after timeout
  - Crossplane pod failures
- [ ] Log aggregation (ELK/Loki) tracking Crossplane logs

**Grafana dashboards**:
- Crossplane provider health
- XResource reconciliation status
- Cloud resource inventory

---

## Documentation

- [ ] Team members trained on Crossplane basics
- [ ] Runbooks created for:
  - [ ] How to create XResource claim
  - [ ] How to debug failed reconciliation
  - [ ] How to update Composition
  - [ ] Rollback procedure (delete claim, resource orphaned)
- [ ] Contact list for escalation (platform team, security team)

---

## Sign-off

### Platform Engineering

- [x] Crossplane environment validated
- [x] RBAC approved
- [x] GitOps pipeline verified

**Approved by**: ____________________ **Date**: _______________

### Security Team

- [x] Provider credentials secure (Workload Identity preferred)
- [x] Network policies in place
- [x] IAM least privilege validated

**Approved by**: ____________________ **Date**: _______________

### Operations Team

- [x] Monitoring configured
- [x] Alerting thresholds set
- [x] On-call runbooks available

**Approved by**: ____________________ **Date**: _______________

---

## Exit Criteria

Before proceeding to **Phase 1: Foundation**, all items above must be checked ✅.

If any item fails, address before migration begins. Document blockers and remediation plan.

---

**Template Version**: 1.0
**Last Updated**: 2026-03-20
**Use For**: Phase 0 Assessment Completion

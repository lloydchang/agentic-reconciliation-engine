---
name: gitops-workflow
description: >
  Use this skill to implement, operate, and troubleshoot GitOps workflows using
  ArgoCD and Flux. Triggers: any request to set up GitOps for a new cluster or
  tenant, configure app-of-apps patterns, investigate a sync failure, enforce
  drift detection, promote releases across environments, manage ArgoCD
  ApplicationSets, configure Flux kustomizations, or audit what version is
  running where across the fleet.
tools:
  - bash
  - computer
---

# GitOps Workflow Skill

Implement and operate production GitOps pipelines using ArgoCD and Flux:
declarative continuous delivery, drift detection, multi-environment promotion,
and fleet-wide application management.

---

## Tooling

| Tool     | Use case                                | Config format       |
|----------|-----------------------------------------|---------------------|
| ArgoCD   | App-centric GitOps, UI, RBAC            | Application/AppSet  |
| Flux     | Cluster-centric, Helm + Kustomize       | HelmRelease/Kustomization |
| Kustomize| Environment overlays                    | kustomization.yaml  |
| Helm     | Parameterised chart packaging           | values.yaml         |

---

## ArgoCD Setup

### Install ArgoCD
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f \
  https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Patch to use SSO (Azure AD)
kubectl patch cm argocd-cm -n argocd --patch-file argocd/config/sso-patch.yaml
kubectl patch cm argocd-rbac-cm -n argocd --patch-file argocd/config/rbac-patch.yaml
```

### App-of-Apps Pattern (per cluster)
```yaml
# root-app.yaml — one app per cluster that manages all other apps
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: root-${CLUSTER_NAME}
  namespace: argocd
spec:
  project: platform
  source:
    repoURL: https://github.com/org/platform-gitops.git
    targetRevision: main
    path: clusters/${CLUSTER_NAME}/apps
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
```

### ApplicationSet (deploy to all tenant namespaces)
```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: tenant-apps
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - tenant: t-acme-prod
            env: prod
            values_file: values-enterprise.yaml
          - tenant: t-widgets-prod
            env: prod
            values_file: values-business.yaml
  template:
    metadata:
      name: '{{tenant}}-app'
    spec:
      project: tenants
      source:
        repoURL: https://github.com/org/tenant-app-chart.git
        targetRevision: '{{env}}'
        helm:
          valueFiles:
            - environments/{{env}}/{{values_file}}
          parameters:
            - name: tenant.id
              value: '{{tenant}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{tenant}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
```

---

## Flux Setup

### Bootstrap Flux on a New Cluster
```bash
flux bootstrap github \
  --owner "$GITHUB_ORG" \
  --repository "platform-gitops" \
  --branch main \
  --path "clusters/${CLUSTER_NAME}" \
  --personal false \
  --components-extra image-reflector-controller,image-automation-controller
```

### HelmRelease with Auto-Upgrade
```yaml
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: tenant-app
  namespace: ${TENANT_ID}
spec:
  interval: 5m
  chart:
    spec:
      chart: tenant-app
      version: '>=1.0.0 <2.0.0'
      sourceRef:
        kind: HelmRepository
        name: internal-charts
  values:
    tenantId: ${TENANT_ID}
    image:
      tag: ${IMAGE_TAG}
  upgrade:
    remediation:
      retries: 3
  rollback:
    cleanupOnFail: true
```

---

## Environment Promotion Pipeline

```
feature/* branch
      ↓ PR merged
    dev environment  (auto-sync, any commit)
      ↓ integration tests pass
  staging environment  (auto-promote after tests)
      ↓ manual approval gate
  prod environment  (sync on tag only)
```

```bash
promote_to_env() {
  local chart=$1
  local version=$2
  local target_env=$3

  # Update image tag in GitOps repo
  cd platform-gitops
  yq e ".image.tag = \"${version}\"" \
    -i "environments/${target_env}/${chart}/values.yaml"

  git add "environments/${target_env}/${chart}/values.yaml"
  git commit -m "promote(${target_env}): ${chart}@${version} [automated]"
  git push origin main

  # Wait for ArgoCD sync
  argocd app wait "${chart}-${target_env}" \
    --sync --health --timeout 300
}
```

---

## Drift Detection & Self-Healing

```bash
# Check all apps for drift (out-of-sync)
argocd app list -o json | \
  jq -r '.[] | select(.status.sync.status != "Synced") |
    "\(.metadata.name): \(.status.sync.status) — \(.status.health.status)"'

# Force sync for a specific app
argocd app sync "${APP_NAME}" --force --prune

# Get diff between live and desired state
argocd app diff "${APP_NAME}"
```

### Auto-Remediation Policy
```yaml
syncPolicy:
  automated:
    prune: true       # Remove resources deleted from Git
    selfHeal: true    # Re-sync if live state drifts from Git
  retry:
    limit: 5
    backoff:
      duration: 5s
      factor: 2
      maxDuration: 3m
```

---

## GitOps Repository Structure

```
platform-gitops/
  clusters/
    aks-prod-eastus/
      apps/                    # root app-of-apps
        kustomization.yaml
      infrastructure/          # base infra: cert-manager, monitoring, etc.
      tenants/                 # per-tenant Application resources
    aks-staging-eastus/
    ...
  environments/
    dev/
      tenant-app/values.yaml
    staging/
      tenant-app/values.yaml
    prod/
      tenant-app/values.yaml
  charts/
    tenant-app/               # Helm chart
  policies/                   # OPA/Kyverno policies deployed via GitOps
```

---

## Fleet Version Audit

```bash
# What version is running where?
argocd app list -o json | \
  jq -r '.[] |
    "\(.metadata.name)\t\(.spec.source.targetRevision)\t\(.status.sync.status)\t\(.status.health.status)"' | \
  sort | column -t

# Find any app running a non-approved version
argocd app list -o json | \
  jq -r '.[] | select(.spec.source.targetRevision != "main" and
    (.spec.source.targetRevision | test("^v[0-9]+\\.[0-9]+\\.[0-9]+$") | not)) |
    "\(.metadata.name): \(.spec.source.targetRevision)"'
```

---

## ArgoCD RBAC

```yaml
# argocd-rbac-cm.yaml
policy.csv: |
  # Platform engineers — full access
  p, role:platform-engineer, applications, *, */*, allow
  p, role:platform-engineer, clusters, get, *, allow

  # Tenant developers — read own namespace only
  p, role:tenant-dev, applications, get, */{{tenant}}-*, allow
  p, role:tenant-dev, applications, sync, */{{tenant}}-*, allow

  # Read-only for auditors
  p, role:auditor, applications, get, *, allow
  p, role:auditor, repositories, get, *, allow
```

---

## Examples

- "Set up ArgoCD app-of-apps for the new production cluster in East US"
- "Why is the payments-api out of sync in prod? Show me the diff"
- "Promote tenant-app v2.3.1 from staging to prod"
- "Show me every service running a non-prod image tag in production"
- "Set up Flux bootstrapping for the new DR cluster in West Europe"
- "Create an ApplicationSet to deploy the tenant-app to all 42 tenant namespaces"

---

## Output Format

```json
{
  "tool": "argocd|flux",
  "operation": "sync|promote|audit|diff|setup|appset",
  "app_name": "string",
  "target_revision": "string",
  "sync_status": "Synced|OutOfSync|Unknown",
  "health_status": "Healthy|Degraded|Progressing|Missing",
  "drift_detected": false,
  "environments": [],
  "status": "success|failure"
}
```

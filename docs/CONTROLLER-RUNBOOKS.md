# Controller Runbooks

Per-controller failure playbooks for Flux, Crossplane, Cluster API, and ESO. Use this document
when a controller is stuck, erroring, or producing unexpected reconciliation behaviour.

---

## General Diagnosis Pattern

Before opening a controller-specific section, run this triage sequence:

```bash
# 1. Is the controller running?
kubectl get pods -n <controller-namespace>

# 2. Is it logging errors?
kubectl logs -n <controller-namespace> deploy/<controller-name> --tail=50

# 3. What is the resource status?
kubectl describe <resource-kind> <resource-name> -n <namespace>
# Focus on: Status.Conditions, Events

# 4. Is there a recent reconciliation attempt?
kubectl get events -n <namespace> --sort-by='.lastTimestamp' | tail -20
```

---

## Flux

### Namespace: `flux-system`

### Flux reconciliation stuck or stalled

**Symptoms**: `flux get kustomizations` shows `False` under Ready; Last Applied timestamp is old.

```bash
# Check kustomization status
flux get kustomizations -A

# Get detailed status for a specific kustomization
flux describe kustomization flux-system

# Check for source fetch errors (Git unreachable, auth failure)
flux get sources git -A
kubectl describe gitrepository infrastructure-repo -n flux-system

# Force a reconciliation
flux reconcile kustomization flux-system --with-source

# Check controller logs for errors
kubectl logs -n flux-system deploy/kustomize-controller --tail=100
kubectl logs -n flux-system deploy/source-controller --tail=100
```

**Common causes and fixes:**

| Cause | Fix |
|---|---|
| Git credentials expired | Update the `flux-system/flux-git-credentials` Secret |
| Manifest apply error (CRD not found) | Check that the dependency CRD is applied before this kustomization; review `dependsOn` |
| OOM-killed controller | Increase memory limit on the controller Deployment |
| Hub API server unreachable | Wait for managed control plane to recover; check cloud provider status |

### Flux self-management circular dependency

Flux manages the hub cluster it runs on. If Flux itself is broken:

```bash
# Check if Flux controllers are running at all
kubectl get pods -n flux-system

# If controllers are not running, reinstall Flux manually (no bootstrap cluster needed
# for a controller restart — just re-apply the components)
kubectl apply -f https://github.com/fluxcd/flux2/releases/latest/download/install.yaml

# If that fails, use the bootstrap cluster procedure:
# See HUB-HA-RECOVERY.md
```

### Flux SOPS decryption failure

**Symptoms**: Kustomization shows error: `decryption failed: failed to get age identity`.

```bash
# Verify the SOPS age key Secret exists
kubectl get secret sops-age -n flux-system

# Verify the key matches the public key in .sops.yaml
kubectl get secret sops-age -n flux-system -o jsonpath='{.data.age\.agekey}' | base64 -d

# If the Secret is missing, restore from cloud key vault backup
aws secretsmanager get-secret-value \
  --secret-id gitops/sops-age-private-key \
  --query SecretString --output text > /tmp/age-key.txt

kubectl create secret generic sops-age \
  --from-file=age.agekey=/tmp/age-key.txt \
  -n flux-system

rm /tmp/age-key.txt
```

---

## Crossplane

### Namespace: `crossplane-system`

### Managed resource stuck in `Synced=False`

**Symptoms**: `kubectl get managed -A` shows `SYNCED=False` for a resource.

```bash
# Get the error
kubectl describe <resource-kind> <resource-name>
# Look at: Status.Conditions[type=Synced], Events

# Common: ProviderConfig not found or not ready
kubectl get providerconfigs -A
kubectl describe providerconfig aws-provider

# Common: provider credentials error (workload identity not configured)
kubectl logs -n crossplane-system \
  $(kubectl get pods -n crossplane-system -l pkg.crossplane.io/revision \
    -o jsonpath='{.items[0].metadata.name}') --tail=50

# Force a reconciliation by adding/removing an annotation
kubectl annotate <resource-kind> <resource-name> reconcile-trigger=$(date +%s) --overwrite
```

**Common causes and fixes:**

| Cause | Fix |
|---|---|
| Provider not healthy | `kubectl describe provider provider-aws` — check health condition |
| IRSA / workload identity misconfigured | Verify service account annotation; check IAM role trust policy |
| Cloud API quota exceeded | Check cloud console quota page; request increase |
| Cloud API throttling | Transient; wait and the controller retries automatically |
| Resource already exists in cloud, not managed | Import using `crossplane beta trace` or delete and let Crossplane recreate |

### Crossplane provider unhealthy

```bash
kubectl get providers -A
kubectl describe provider provider-aws
# Look at: Status.Conditions[type=Healthy]

# Restart the provider
kubectl rollout restart deployment \
  $(kubectl get pods -n crossplane-system -l pkg.crossplane.io/revision \
    --no-headers -o custom-columns=':metadata.name' | head -1 | xargs -I{} \
    kubectl get pod {} -n crossplane-system -o jsonpath='{.metadata.labels.pkg\.crossplane\.io/revision}') \
  -n crossplane-system
```

### Deletion blocked by finalizer

A resource is stuck in `Terminating` state:

```bash
kubectl get <resource-kind> <resource-name> -o jsonpath='{.metadata.finalizers}'

# Crossplane finalizer: crossplane.io/finalizer
# Only remove finalizer after confirming the cloud resource is actually gone
# Check cloud console first

# If cloud resource is confirmed deleted:
kubectl patch <resource-kind> <resource-name> \
  --type=json \
  -p='[{"op":"remove","path":"/metadata/finalizers"}]'
```

---

## Cluster API

### Namespace: `capi-system` (core); `caip-system` / `capz-system` / `capg-system` (infra providers)

### Spoke cluster stuck in `Provisioning`

```bash
# Check cluster phase
kubectl get cluster <cluster-name> -n <namespace> -o wide

# Get provisioning events
kubectl describe cluster <cluster-name> -n <namespace>
kubectl describe kubeadmcontrolplane <kcp-name> -n <namespace>

# Check machine status
kubectl get machines -n <namespace> -l cluster.x-k8s.io/cluster-name=<cluster-name>
kubectl describe machine <machine-name> -n <namespace>

# Check infrastructure provider logs
kubectl logs -n caip-system deploy/capa-controller-manager --tail=100  # AWS
kubectl logs -n capz-system deploy/capz-controller-manager --tail=100  # Azure
kubectl logs -n capg-system deploy/capg-controller-manager --tail=100  # GCP
```

**Common causes:**

| Cause | Fix |
|---|---|
| Cloud quota exhausted | Check quota in cloud console; request increase |
| Bootstrap token expired | Delete and recreate the KubeadmControlPlane; CAPI will reprovision |
| Infrastructure provider credentials | Verify workload identity on the hub for the infra provider |
| Network not ready | Ensure XNetwork Composition completed before XCluster; check `dependsOn` |

### Spoke cluster unreachable from hub

CAPI needs to reach spoke API servers for health checks during provisioning:

```bash
# Check that the spoke kubeconfig Secret was created
kubectl get secret <cluster-name>-kubeconfig -n <namespace>

# Extract and test connectivity
kubectl get secret <cluster-name>-kubeconfig -n <namespace> \
  -o jsonpath='{.data.value}' | base64 -d > /tmp/spoke-kubeconfig
KUBECONFIG=/tmp/spoke-kubeconfig kubectl get nodes
rm /tmp/spoke-kubeconfig

# If unreachable: check network security groups / firewall rules
# between hub and spoke control plane endpoint
```

---

## ESO (External Secrets Operator)

### Namespace: `external-secrets` (on each spoke)

### ExternalSecret not syncing

```bash
# Check status
kubectl get externalsecrets -A
# STATUS column: SecretSynced | SecretSyncedError | NotReady

# Get error detail
kubectl describe externalsecret <name> -n <namespace>
# Look at: Status.Conditions, Events

# Check ClusterSecretStore is ready
kubectl get clustersecretstore
kubectl describe clustersecretstore <name>
```

**Common causes:**

| Cause | Fix |
|---|---|
| Workload identity annotation missing | Annotate ESO service account; restart ESO pod |
| IAM role trust policy wrong OIDC issuer | Update trust policy with correct OIDC provider URL |
| Secret path not found in vault | Verify path exists in AWS SM / AKV / GCP SM |
| Secret version `latest` resolves to deleted version | Restore secret or pin to a specific version |
| Vault token expired | ESO renews automatically; if not, check ESO controller logs |

### ESO pod CrashLoopBackOff

```bash
kubectl logs -n external-secrets deploy/external-secrets --previous

# Common: webhook TLS certificate expired
kubectl get certificate -n external-secrets
# If expired: delete the certificate and cert-manager will reissue
kubectl delete certificate external-secrets-webhook -n external-secrets

# Wait for cert-manager to reissue, then restart ESO
kubectl rollout restart deploy/external-secrets -n external-secrets
kubectl rollout restart deploy/external-secrets-webhook -n external-secrets
```

### Secret not updated after rotation in vault

ESO syncs on a `refreshInterval`. If a secret was rotated in the vault and the interval has not
elapsed:

```bash
# Force immediate re-sync by annotating the ExternalSecret
kubectl annotate externalsecret <name> -n <namespace> \
  force-sync=$(date +%s) --overwrite

# Or reduce refreshInterval temporarily (change in Git, let Flux apply)
```

---

## Escalation

If a controller failure cannot be resolved with the above steps:

1. Collect full controller logs: `kubectl logs -n <ns> deploy/<controller> > /tmp/controller-logs.txt`
2. Collect affected resource manifests: `kubectl get <kind> <name> -o yaml > /tmp/resource.yaml`
3. Collect recent events: `kubectl get events -n <ns> --sort-by='.lastTimestamp' > /tmp/events.txt`
4. Open an issue in the upstream project repository (Flux, Crossplane, CAPI, ESO) with the above
5. Tag the on-call platform team in the incident channel with the issue link

# Bootstrap Cluster

## Purpose

The bootstrap cluster solves two specific problems:

1. **Circular dependency**: Flux manages the hub cluster it runs on. If the hub suffers a total
   loss, the tool required to recover it (Flux) is not running. The bootstrap cluster holds the
   hub's bootstrap configuration and provides an external starting point for hub recovery without
   requiring Flux to already be running.

2. **etcd backup scheduling**: The hub etcd backup CronJob runs on the hub — which means it
   stops during a hub outage. The bootstrap cluster runs an independent backup schedule that does
   not depend on hub availability.

The bootstrap cluster does **not**:

- Reconcile spokes (spokes pull from Git directly)
- Manage cloud resources (Crossplane runs on the hub, not here)
- Participate in the data path for application workloads
- Hold cloud credentials for spoke cloud providers

It is a recovery anchor only. In steady state it idles.

---

## Sizing

The bootstrap cluster is intentionally minimal. It runs two workloads: a Flux instance watching
the bootstrap configuration in Git, and a CronJob for hub state backup.

| Option | Sizing | When to use |
|---|---|---|
| k3s (self-hosted) | 1–3 nodes, 2 vCPU / 4 GB RAM each | Cost-sensitive; on-prem is available |
| Managed (EKS/AKS/GKE) | Smallest available node type, 1–3 nodes | No on-prem; want managed control plane |

A single-node k3s cluster is sufficient. Use 3 nodes if the bootstrap cluster itself needs to
survive a node failure (recommended for production environments).

---

## What the Bootstrap Cluster Holds

### Hub bootstrap Flux configuration

The complete set of manifests needed to bootstrap Flux onto a fresh hub cluster and bring the
full hub control plane to a healthy state:

```
control-plane/
  flux/
    gotk-components.yaml        # Flux CRDs and controllers
    gotk-sync.yaml              # GitRepository + Kustomization pointing at Git
  crossplane/
    providers.yaml              # provider-aws, provider-azure, provider-gcp
    provider-configs.yaml       # ProviderConfig per cloud
  capi/
    infrastructure-providers.yaml
  bootstrap/
    hub-cluster-config.yaml     # eksctl / az / gcloud config for hub reprovisioning
    recovery-procedure.md       # Step-by-step cold-start instructions (offline copy)
```

### Hub state backup CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: hub-state-backup
  namespace: bootstrap-system
spec:
  schedule: "0 * * * *"
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: hub-backup-sa
          containers:
            - name: backup
              image: bitnami/kubectl:latest
              env:
                - name: HUB_KUBECONFIG
                  valueFrom:
                    secretKeyRef:
                      name: hub-kubeconfig
                      key: kubeconfig
                - name: BACKUP_BUCKET
                  value: "s3://hub-backups"
              command:
                - /bin/sh
                - -c
                - |
                  export KUBECONFIG=/tmp/hub-kubeconfig
                  echo "$HUB_KUBECONFIG" > $KUBECONFIG

                  # Check hub reachability first
                  if ! kubectl cluster-info > /dev/null 2>&1; then
                    echo "Hub unreachable — skipping backup, alerting"
                    exit 1
                  fi

                  TIMESTAMP=$(date +%Y%m%d-%H%M%S)
                  kubectl get managed -A -o yaml > /tmp/managed.yaml
                  kubectl get kustomizations,gitrepositories -A -o yaml > /tmp/flux.yaml
                  kubectl get clusters,machinedeployments -A -o yaml > /tmp/capi.yaml
                  kubectl get xrds,compositions -A -o yaml > /tmp/crossplane-apis.yaml

                  aws s3 cp /tmp/ ${BACKUP_BUCKET}/${TIMESTAMP}/ --recursive
                  echo "Backup complete: ${BACKUP_BUCKET}/${TIMESTAMP}/"
          restartPolicy: OnFailure
```

The CronJob requires a `hub-kubeconfig` Secret with read access to the hub API server. Rotate
this kubeconfig when hub credentials are rotated.

---

## Setup Procedure

### 1. Provision the bootstrap cluster

**Option A: k3s**

```bash
# On the bootstrap node
curl -sfL https://get.k3s.io | sh -

# Export kubeconfig
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# Verify
kubectl get nodes
```

**Option B: Managed cluster (EKS example)**

```bash
eksctl create cluster \
  --name bootstrap-cluster \
  --region us-east-1 \
  --nodegroup-name bootstrap-ng \
  --node-type t3.small \
  --nodes 1 \
  --nodes-min 1 \
  --nodes-max 3
```

### 2. Bootstrap Flux on the bootstrap cluster

```bash
flux bootstrap github \
  --owner=org \
  --repository=gitops-infra-control-plane \
  --branch=main \
  --path=control-plane/bootstrap \
  --personal
```

Flux on the bootstrap cluster watches `control-plane/bootstrap/` only — not the full hub
configuration. This keeps the bootstrap cluster scope minimal.

### 3. Create the hub kubeconfig Secret

```bash
# After hub is provisioned and healthy
kubectl create secret generic hub-kubeconfig \
  --from-file=kubeconfig=$HOME/.kube/hub-kubeconfig \
  -n bootstrap-system
```

### 4. Verify the backup CronJob

```bash
# Trigger a manual run
kubectl create job --from=cronjob/hub-state-backup manual-test -n bootstrap-system

# Check output
kubectl logs -n bootstrap-system -l job-name=manual-test
```

Verify that backup objects appear in the target S3/GCS/blob storage bucket.

### 5. Rotate backup credentials

The backup CronJob service account needs cloud storage write permissions. Set up workload
identity on the bootstrap cluster the same way you would on a spoke:

```bash
# EKS bootstrap: annotate the service account for IRSA
kubectl annotate serviceaccount hub-backup-sa \
  -n bootstrap-system \
  eks.amazonaws.com/role-arn=arn:aws:iam::ACCOUNT:role/hub-backup-role
```

---

## Hub Cold-Start Recovery

When the hub cluster suffers a total loss:

### Step 1: Provision a replacement hub cluster

Use the hub cluster config stored in `control-plane/bootstrap/hub-cluster-config.yaml`:

```bash
# EKS
eksctl create cluster -f control-plane/bootstrap/hub-cluster-config.yaml

# AKS
az deployment group create \
  --resource-group hub-rg \
  --template-file control-plane/bootstrap/hub-arm-template.json

# GKE
gcloud container clusters create hub-cluster \
  --config-file control-plane/bootstrap/hub-gke-config.yaml
```

### Step 2: Bootstrap Flux on the replacement hub

```bash
export KUBECONFIG=$HOME/.kube/new-hub-kubeconfig

flux bootstrap github \
  --owner=org \
  --repository=gitops-infra-control-plane \
  --branch=main \
  --path=control-plane/flux
```

Flux will reconcile Crossplane, CAPI, and all hub controllers from Git.

### Step 3: Wait for controllers to become healthy

```bash
# Monitor Crossplane provider health
kubectl get providers -A -w

# Monitor CAPI controllers
kubectl get deployments -n capi-system -w

# All should reach Available=True
```

### Step 4: Verify managed resource reconciliation

```bash
kubectl get managed -A
# Expected: Synced=True, Ready=True for all resources
# If a resource is Synced=False, describe it for the error:
kubectl describe <resource-type> <resource-name>
```

Resources that drifted during the hub outage are corrected in the first reconciliation cycle.

### Step 5: Verify CAPI picks up existing spokes

```bash
kubectl get clusters -A -o wide
# Existing spoke clusters should appear and show Phase=Provisioned
```

CAPI re-adopts existing clusters automatically by matching cluster names in the CAPI manifests
against live cloud resources.

### Step 6: Verify spokes are healthy (they should never have stopped)

Run on each spoke:

```bash
flux get all -A
kubectl get externalsecrets -A
kubectl get nodes
```

Spoke Flux agents and ESO continued pulling from Git and cloud vaults throughout the hub outage.
No spoke workloads should require restart.

### Step 7: Update the bootstrap cluster's hub kubeconfig

```bash
# Replace the hub kubeconfig Secret with credentials for the new hub
kubectl create secret generic hub-kubeconfig \
  --from-file=kubeconfig=$HOME/.kube/new-hub-kubeconfig \
  -n bootstrap-system \
  --dry-run=client -o yaml | kubectl apply -f -
```

---

## Quarterly Recovery Drill

Test the cold-start procedure quarterly on a non-production copy of the hub:

```bash
# 1. Provision a test hub cluster
# 2. Run flux bootstrap pointing at the test path
# 3. Verify controllers come up
# 4. Verify managed resources reconcile
# 5. Document RTO: time from cluster provisioned to all controllers Healthy
# 6. Tear down test hub
```

Record the measured RTO. If it exceeds your target, identify and fix the bottleneck before the
next drill.

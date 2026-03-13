# Hub HA and Recovery

The hub cluster is the single coordination point for spoke provisioning and Crossplane resource
reconciliation. Hub failure pauses those operations. Spoke Flux agents and ESO instances continue
running independently — they pull from Git and from cloud vaults directly, so application
workloads are unaffected by hub downtime.

This document covers hub HA configuration, failure modes, and the cold-start recovery procedure.

---

## Hub HA Configuration

### Managed control plane (recommended)

Run the hub on a managed Kubernetes control plane (EKS, AKS, or GKE). The cloud provider
operates the control plane nodes, etcd, and the API server; you operate the workloads running on
them. This eliminates the operational burden of managing control plane nodes directly.

Minimum configuration:

| Setting | Value |
|---|---|
| Control plane nodes | Managed (cloud provider) |
| Worker node pools | 3+ nodes across 3 availability zones |
| Crossplane node pool | Dedicated, not shared with application workloads |
| CAPI node pool | Dedicated, not shared with Crossplane |
| etcd | Managed by cloud provider; configure backup separately |

### Node pool configuration

```yaml
# Example: dedicated node pool for Crossplane controllers (EKS NodeGroup)
apiVersion: eks.services.k8s.aws/v1alpha1
kind: Nodegroup
metadata:
  name: crossplane-controllers
  namespace: crossplane-system
spec:
  clusterName: hub-cluster
  nodeRole: arn:aws:iam::ACCOUNT:role/hub-crossplane-node-role
  scalingConfig:
    desiredSize: 3
    minSize: 3
    maxSize: 6
  subnets:
    - subnet-az1
    - subnet-az2
    - subnet-az3
  labels:
    dedicated: crossplane
  taints:
    - effect: NO_SCHEDULE
      key: dedicated
      value: crossplane
```

Apply matching tolerations on Crossplane:

```yaml
# values override for Crossplane Helm chart
tolerations:
  - key: dedicated
    operator: Equal
    value: crossplane
    effect: NoSchedule
nodeSelector:
  dedicated: crossplane
```

### etcd backup

Configure scheduled etcd backups to object storage. On managed control planes, back up the
relevant cluster state rather than etcd directly, as cloud providers do not expose etcd for
managed clusters.

```yaml
# Flux-managed CronJob: back up cluster state to S3
apiVersion: batch/v1
kind: CronJob
metadata:
  name: hub-state-backup
  namespace: flux-system
spec:
  schedule: "0 * * * *"   # hourly
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: hub-backup-sa  # IRSA with s3:PutObject
          containers:
            - name: backup
              image: bitnami/kubectl:latest
              command:
                - /bin/sh
                - -c
                - |
                  # Export all Crossplane managed resources and Flux objects
                  kubectl get managed -A -o yaml > /tmp/managed-resources.yaml
                  kubectl get kustomizations,gitrepositories,helmreleases -A -o yaml > /tmp/flux-objects.yaml
                  kubectl get clusters,machines -A -o yaml > /tmp/capi-objects.yaml
                  # Upload to S3
                  aws s3 cp /tmp/ s3://hub-backups/$(date +%Y%m%d-%H%M%S)/ --recursive
          restartPolicy: OnFailure
```

Verify restores quarterly. A backup that has never been tested is not a backup.

---

## Failure Modes

### Mode 1: Hub worker node failure

**Symptoms**: Controllers restart; reconciliation delays; pending Crossplane claims.

**Spoke impact**: None — spoke Flux agents and ESO continue pulling from Git and cloud vaults.

**Resolution**: Kubernetes reschedules controllers on healthy nodes automatically. If all nodes
in a zone fail, CAPI and Crossplane controllers reschedule to surviving zones. No manual
intervention required if 3+ nodes across 3 AZs are healthy.

**Diagnosis**:
```bash
kubectl get nodes -o wide
kubectl get pods -n crossplane-system
kubectl get pods -n capi-system
kubectl get pods -n flux-system
```

### Mode 2: Hub API server unreachable (transient)

**Symptoms**: `kubectl` commands time out; Flux on the hub cannot reconcile.

**Spoke impact**: None — spokes pull from Git directly.

**Resolution**: Wait for the managed control plane to recover. Cloud provider SLAs apply. Monitor
via cloud provider dashboards rather than `kubectl`.

### Mode 3: Hub total loss (data loss or permanent failure)

**Symptoms**: Hub cluster does not exist or cannot be recovered. Managed resources may be
orphaned (Crossplane no longer reconciling them). No new spoke provisioning possible.

**Spoke impact**: Spokes continue running on last-applied state. Flux agents pull from Git. ESO
delivers secrets. No spoke workload interruption.

**Resolution**: Cold-start recovery using the bootstrap cluster. See below.

---

## Cold-Start Recovery Procedure

The bootstrap cluster holds the hub's bootstrap Flux configuration and cluster manifests. It
provides the external anchor needed to recover the hub without Flux (since Flux runs on the hub
it is supposed to recover).

Full procedure is in [BOOTSTRAP-CLUSTER.md](./BOOTSTRAP-CLUSTER.md). Summary:

```
1. Bootstrap cluster confirms hub is unreachable

2. Operator provisions a replacement hub cluster (eksctl / az / gcloud CLI)
   $ eksctl create cluster -f hub-cluster-config.yaml

3. Operator installs Flux on the replacement hub, pointing at the Git repository
   $ flux bootstrap github \
       --owner=org \
       --repository=gitops-infra-control-plane \
       --branch=main \
       --path=control-plane/flux

4. Flux reconciles Crossplane, CAPI, and ESO onto the hub
   Wait for: kubectl get providers -A  (all Healthy)
             kubectl get clusters -A   (CAPI picks up existing spoke records)

5. Verify Crossplane managed resource reconciliation resumes
   $ kubectl get managed -A
   All resources should reach Synced=True, Ready=True

6. Verify spoke clusters are recognised by CAPI
   $ kubectl get clusters -A -o wide

7. Verify spoke Flux and ESO are still running (they never stopped)
   Run on each spoke:
   $ flux get all -A
   $ kubectl get externalsecrets -A

8. Resume normal operations
```

**Spoke state during recovery**: Spokes run on last-applied Git state throughout. Secret delivery
via ESO continues. No spoke workload restarts are caused by hub recovery.

**Crossplane resource reconciliation after recovery**: Crossplane re-adopts existing managed
resources automatically. Resources that drifted during the hub outage are corrected within one
reconciliation cycle after the hub comes back.

---

## Circular Dependency Note

Flux manages the hub cluster it runs on. This is intentional — Flux is a cluster extension, and
hub self-management is a feature not a flaw. The implication is that Flux cannot recover itself
from a total hub loss. The bootstrap cluster exists specifically to break this circular dependency
by providing an external recovery anchor that does not depend on the hub being operational.

See [BOOTSTRAP-CLUSTER.md](./BOOTSTRAP-CLUSTER.md) for bootstrap cluster setup and configuration.

---

## Runbook References

- Flux reconciliation failure: [CONTROLLER-RUNBOOKS.md — Flux](./CONTROLLER-RUNBOOKS.md#flux)
- Crossplane provider stuck: [CONTROLLER-RUNBOOKS.md — Crossplane](./CONTROLLER-RUNBOOKS.md#crossplane)
- CAPI cluster stuck provisioning: [CONTROLLER-RUNBOOKS.md — CAPI](./CONTROLLER-RUNBOOKS.md#cluster-api)

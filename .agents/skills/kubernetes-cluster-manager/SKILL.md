---
name: kubernetes-cluster-manager
description: >
  Use this skill to manage the full Kubernetes cluster lifecycle across Azure
  AKS, AWS EKS, and GCP GKE. Triggers: any request to provision, upgrade,
  scale, harden, or decommission a Kubernetes cluster; manage node pools;
  configure RBAC or network policies; perform version upgrades with zero
  downtime; diagnose cluster health; or enforce Kubernetes operational
  standards across a multi-cloud fleet.
tools:
  - bash
  - computer
---

# Kubernetes Cluster Manager Skill

Manage every dimension of Kubernetes cluster operations: provisioning,
day-2 operations, version lifecycle, node pool scaling, security hardening,
and fleet-wide policy enforcement — across AKS, EKS, and GKE.

---

## Supported Platforms

| Platform | CLI        | Auth env var               | Managed service feature |
|----------|------------|----------------------------|-------------------------|
| AKS      | `az aks`   | `AZURE_SUBSCRIPTION_ID`    | Azure CNI, AGIC, AAD    |
| EKS      | `eksctl`   | `AWS_PROFILE`              | EKS Managed Node Groups |
| GKE      | `gcloud`   | `GOOGLE_APPLICATION_CREDENTIALS` | Autopilot, Workload Identity |

---

## Cluster Provisioning

### AKS (standard pattern)
```bash
az aks create \
  --resource-group "rg-${TENANT_ID}" \
  --name "aks-${CLUSTER_NAME}" \
  --kubernetes-version "$K8S_VERSION" \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --network-plugin azure \
  --network-policy calico \
  --enable-aad \
  --enable-azure-rbac \
  --enable-managed-identity \
  --enable-addons monitoring \
  --workspace-resource-id "$LOG_ANALYTICS_ID" \
  --enable-cluster-autoscaler \
  --min-count 2 \
  --max-count 10 \
  --zones 1 2 3 \
  --tags "managed_by=cluster-manager" "tenant=$TENANT_ID" "env=$ENV"
```

### Post-Provision Hardening (all platforms)
```bash
# Apply baseline network policies (deny-all default)
kubectl apply -f policies/network/deny-all-default.yaml

# Apply Pod Security Standards
kubectl label namespace $NS \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/warn=restricted

# Install cert-manager
helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set installCRDs=true

# Install Prometheus stack
helm upgrade --install kube-prometheus-stack \
  prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  -f values/prometheus-stack.yaml
```

---

## Node Pool Management

### Add a node pool
```bash
az aks nodepool add \
  --cluster-name "aks-${CLUSTER_NAME}" \
  --resource-group "rg-${TENANT_ID}" \
  --name "$POOL_NAME" \
  --node-count $COUNT \
  --node-vm-size $VM_SIZE \
  --node-taints "$TAINT" \
  --labels "workload=$WORKLOAD_TYPE" \
  --enable-cluster-autoscaler \
  --min-count $MIN --max-count $MAX \
  --zones 1 2 3
```

### Drain and delete a node pool
```bash
# Cordon all nodes in pool first
for node in $(kubectl get nodes -l "agentpool=$POOL_NAME" -o name); do
  kubectl cordon "$node"
  kubectl drain "$node" --ignore-daemonsets --delete-emptydir-data --timeout=5m
done
az aks nodepool delete \
  --cluster-name "aks-${CLUSTER_NAME}" \
  --resource-group "rg-${TENANT_ID}" \
  --name "$POOL_NAME"
```

---

## Zero-Downtime Version Upgrades

```bash
# Step 1: Upgrade control plane first
az aks upgrade \
  --resource-group "rg-${TENANT_ID}" \
  --name "aks-${CLUSTER_NAME}" \
  --kubernetes-version "$NEW_K8S_VERSION" \
  --control-plane-only

# Step 2: Validate control plane
kubectl version
kubectl get nodes

# Step 3: Upgrade node pools one at a time
for POOL in $(az aks nodepool list --cluster-name "aks-${CLUSTER_NAME}" \
  -g "rg-${TENANT_ID}" --query "[].name" -o tsv); do
  echo "Upgrading pool: $POOL"
  az aks nodepool upgrade \
    --cluster-name "aks-${CLUSTER_NAME}" \
    --resource-group "rg-${TENANT_ID}" \
    --name "$POOL" \
    --kubernetes-version "$NEW_K8S_VERSION" \
    --no-wait
  # Wait and validate between pools
  az aks nodepool wait \
    --cluster-name "aks-${CLUSTER_NAME}" \
    -g "rg-${TENANT_ID}" \
    --name "$POOL" \
    --updated
  kubectl get nodes -l "agentpool=$POOL"
done

# Step 4: Post-upgrade validation
kubectl get pods -A | grep -v Running | grep -v Completed
kubectl get events --sort-by='.lastTimestamp' | tail -20
```

### Version Lifecycle Policy
- Stay within N-1 of latest stable minor version
- Begin upgrade planning 60 days before a minor version reaches end-of-life
- Test upgrades in dev → staging → prod with 3-day soak periods

---

## RBAC Management

```bash
# Create namespace-scoped developer role
kubectl apply -f - <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: $NAMESPACE
  name: developer
rules:
- apiGroups: ["", "apps", "batch"]
  resources: ["pods", "deployments", "jobs", "configmaps"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
- apiGroups: [""]
  resources: ["pods/log", "pods/exec"]
  verbs: ["get", "create"]
EOF

# Bind a user (Azure AD group)
kubectl create rolebinding developer-binding \
  --role=developer \
  --group="$AAD_GROUP_ID" \
  --namespace=$NAMESPACE
```

### RBAC Audit
```bash
# Find all cluster-admin bindings
kubectl get clusterrolebindings -o json | \
  jq -r '.items[] | select(.roleRef.name=="cluster-admin") |
    "\(.metadata.name): \(.subjects[]?.name // "unknown")"'

# Check what a user can do
kubectl auth can-i --list --as="$USER" --namespace=$NAMESPACE
```

---

## Cluster Health Diagnostics

```bash
# Full cluster health snapshot
echo "=== Node Status ===" && kubectl get nodes -o wide
echo "=== Component Status ===" && kubectl get componentstatuses
echo "=== System Pods ===" && kubectl get pods -n kube-system
echo "=== Resource Pressure ===" && kubectl top nodes
echo "=== Recent Events ===" && kubectl get events -A \
  --sort-by='.lastTimestamp' | grep -E "Warning|Error" | tail -30
echo "=== PVC Status ===" && kubectl get pvc -A | grep -v Bound
echo "=== Failed Pods ===" && kubectl get pods -A | grep -vE "Running|Completed"
```

### Automated Health Checks (scheduled every 5 min)
| Check | Healthy threshold |
|-------|------------------|
| Node ready ratio | ≥ 100% |
| System pod running ratio | ≥ 95% |
| etcd latency p99 | < 10 ms |
| API server request errors | < 1% |
| Node memory pressure | 0 nodes |
| PVC unbound | 0 |

---

## Security Hardening Checklist

```bash
# 1. Enforce Pod Security Standards
# 2. Enable Calico network policies (deny-all default)
# 3. Disable dashboard if not needed
# 4. Enable audit logging to Log Analytics / CloudWatch
# 5. Restrict kubelet read-only port
# 6. Enable Workload Identity / IRSA (no static credentials)
# 7. Scan all running images via trivy operator
# 8. Enable Azure Defender / GKE Security Posture
# 9. Rotate kubeconfig credentials every 90 days
# 10. Verify no containers run as root (enforce via OPA)
```

---

## Fleet Summary Report

```
Cluster Fleet Status — [DATE]
──────────────────────────────
Total clusters:  12  (AKS: 7 | EKS: 3 | GKE: 2)
Healthy:         11  ✅
Degraded:        1   ⚠️  (aks-tenant-42-prod — node memory pressure)

Version compliance:
  Up to date (K8s 1.30): 9/12
  One minor behind:       2/12
  EOL risk:               1/12  ← upgrade required within 30 days

Total node count:        214
Autoscaler utilisation:  68% avg CPU | 72% avg memory
```

---

## Examples

- "Provision a new AKS cluster for tenant-42 in East US with 3-node enterprise config"
- "Upgrade all dev clusters to Kubernetes 1.30"
- "Show me any clusters running an EOL version"
- "Add a GPU node pool to the ml-workloads cluster"
- "Audit all cluster-admin bindings across the fleet"
- "Run a full health check on aks-tenant-42-prod"

---

## Output Format

```json
{
  "cluster_name": "string",
  "platform": "aks|eks|gke",
  "k8s_version": "string",
  "node_count": 0,
  "node_pools": [],
  "health_status": "healthy|degraded|critical",
  "security_score": 0,
  "upgrade_required": false,
  "operation": "provision|upgrade|scale|delete|health_check",
  "status": "success|failure|in_progress"
}
```

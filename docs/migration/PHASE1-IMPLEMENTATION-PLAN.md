# Phase 1: Foundation & Provider Validation - Implementation Plan

**Crossplane Migration - Phase 1 Execution**

---

## Current State Assessment

**Environment**:
- **Cluster**: Kind (local development) - `kind-agentic-test-control-plane`
- **Crossplane**: Installed (core only)
- **Providers**: NOT installed (0 providers)
- **GitOps**: NOT installed (no Flux/ArgoCD)
- **Repository**: Contains provider definitions and compositions ready to deploy

---

## Phase 1 Objectives

✅ Install and configure all Crossplane providers (AWS, Azure, GCP, Kubernetes)
✅ Validate ProviderConfigs and credentials
✅ Verify GitOps pipeline (or document manual apply path for dev)
✅ Test basic managed resource provisioning
✅ Begin multi-cloud orchestrator Crossplane integration

---

## Implementation Steps

### 1. Install Crossplane Providers

Since GitOps is not yet deployed, we'll apply providers directly using `kubectl apply -k`.

**Target**: Install `provider-aws`, `provider-azure`, `provider-gcp`, `provider-kubernetes`

```bash
# Apply provider definitions and configs from repository
kubectl apply -k core/operators/control-plane/crossplane/providers/

# Wait for providers to install and become HEALTHY
kubectl wait --for=condition=Healthy providers -n crossplane-system --all --timeout=300s
```

**Expected output**:
```
provider.aws.crossplane.io/provider-aws created
provider.azure.crossplane.io/provider-azure created
provider.gcp.crossplane.io/provider-gcp created
provider.kubernetes.crossplane.io/provider-kubernetes created
providerconfig.aws.crossplane.io/aws-provider created
providerconfig.azure.crossplane.io/azure-provider created
providerconfig.gcp.crossplane.io/gcp-provider created
providerconfig.kubernetes.crossplane.io/kubernetes-provider created
```

**Verification**:
```bash
kubectl get providers -n crossplane-system
# Should show all 4 providers with HEALTHY=True

kubectl get providerconfigs -n crossplane-system
# Should show all 4 ProviderConfigs
```

#### Credentials Configuration (Dev/Test)

The ProviderConfigs use `source: InjectedIdentity` which requires Workload Identity (GCP) or IRSA (AWS) or Azure Managed Identity. On a local Kind cluster, this won't work because there's no cloud provider metadata service.

**For local development**, we need to create a Secret-based ProviderConfig:

```bash
# Create AWS provider config with credentials from environment
kubectl create secret generic aws-creds \
  --from-literal='key=YOUR_AWS_ACCESS_KEY_ID' \
  --from-literal='secret=YOUR_AWS_SECRET_ACCESS_KEY' \
  --namespace crossplane-system

# Patch ProviderConfig to use Secret source
kubectl patch providerconfig aws-provider -n crossplane-system \
  --type merge \
  -p '{"spec":{"credentials":{"source":"Secret","secretRef":{"name":"aws-creds","key":"key","namespace":"crossplane-system"}}}}'
# Actually need separate key and secret refs - adjust as needed
```

But for initial testing we can skip real credentials and just verify installation structure.

---

### 2. Verify Provider Installation

```bash
# Check all providers
echo "Checking providers..."
kubectl get providers -n crossplane-system -o wide

# Check provider-specific CRDs are registered
echo "Checking provider CRDs..."
kubectl get crd | grep -E "(rds\.aws|eks\.aws|container\.gcp|azure)" | head -20

# Check provider health
for p in aws azure gcp kubernetes; do
  echo "Provider: $p"
  kubectl get provider provider-$p -n crossplane-system -o jsonpath='{.status.health}'
  echo ""
done
```

---

### 3. Test Managed Resource Creation (AWS S3 Example)

We'll create a simple S3 bucket to verify the provider works. This requires AWS credentials in the ProviderConfig.

```bash
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

# Monitor creation
kubectl get bucket -n crossplane-system -w

# When Ready=True, verify in AWS console or CLI
# Cleanup
# kubectl delete bucket <name> -n crossplane-system
```

**If credentials are not set**: The bucket resource will show `Syncing=False` and an error in events. That's expected; we can still validate the control plane flow.

---

### 4. Create Missing XRD Definitions

Based on gap analysis, we need to create these XRDs:

- **XSecurityGroup** (unified security groups)
- **XRedis** (Redis instances)
- **XCertificate** (SSL certificates)
- **XWAF** (Web Application Firewall)
- **XStorageBucket** (object storage)
- **XLoadBalancer** (load balancers)
- **XDNS** (DNS zones/records)

**Workflow**:
1. Create XRD YAML in `core/operators/control-plane/crossplane/xrds/`
2. Apply XRD: `kubectl apply -f xrds/<xrd>.yaml`
3. Create corresponding Composition(s) for each cloud provider
4. Apply Composition: `kubectl apply -f compositions/<composition>-aws.yaml`

**Priority for migration**: XNetwork extensions already partially exist; extend those first. XDatabase, XCluster also need extensions before migration.

For Phase 1, we only need to verify the existing XRDs work. We'll create the new XRDs in later phases as we migrate those resource types.

---

### 5. Extend Existing XRDs (Gap Analysis)

The gap analysis identified missing fields in existing XRDs. We'll create patches to extend:

**XNetwork Extensions** (`xrds/xnetwork.yaml`):
- Add NAT gateway, IGW, route tables, security groups
- Add DNS, flow logs, VPC peering

**XCluster Extensions** (`xrds/xcluster.yaml`):
- Multiple node pools with autoscaling
- Add-ons, endpoint access, OIDC/IAM
- Logging, monitoring, maintenance windows

**XDatabase Extensions** (`xrds/xdatabase.yaml`):
- Backups, HA, maintenance
- Encryption, parameter groups
- Networking connectivity, storage configuration

We'll create new versions of these XRDs (v1alpha2 or v1beta1) and update Compositions accordingly. This is **Phase 2+ work**, not Phase 1.

---

### 6. GitOps Setup (Optional for Dev, Required for Prod)

We'll set up Flux CD for GitOps automation:

```bash
# Install Flux CLI
flux install

# Create GitRepository pointing to this repo
cat <<EOF | kubectl apply -f -
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: crossplane-infra
  namespace: flux-system
spec:
  interval: 5m
  url: https://github.com/lloydchang/agentic-reconciliation-engine
  ref:
    branch: main
  secretRef:
    name: github-pat  # If private repo
EOF

# Create Kustomization for Crossplane resources
cat <<EOF | kubectl apply -f -
apiVersion: kustomize.toolkit.fluxcd.io/v1beta1
kind: Kustomization
metadata:
  name: crossplane
  namespace: flux-system
spec:
  interval: 10m
  path: ./core/operators/control-plane/crossplane
  prune: true
  sourceRef:
    kind: GitRepository
    name: crossplane-infra
  validation: client
  wait: true
EOF

# Watch sync
kubectl get kustomization -n flux-system -w
```

**Note**: GitOps setup can be deferred to Phase 2 if we're doing manual validation first.

---

### 7. Multi-Cloud Orchestrator Crossplane Integration

Current orchestrators talk directly to cloud SDKs. We'll add Crossplane as an abstraction layer.

**Files to update**:

1. `core/ai/skills/provision-infrastructure/scripts/multi_cloud_orchestrator.py`
   - Add `CrossplaneProvider` class
   - Fallback logic: Try Crossplane first, then legacy SDK if Crossplane not available
   - Methods: `list_vms`, `create_vm`, `list_clusters`, `get_db_endpoint`, etc. that read Crossplane XResources

2. `overlay/ai/skills/complete-hub-spoke-temporal/workflows/multi-cloud-scatter-gather.go`
   - Add activity to query Crossplane XResources via Kubernetes API
   - Update consensus algorithm to include Crossplane resource status

3. `core/multi-cloud-abstraction.js`
   - Add Crossplane REST API client (kubectl proxy or direct K8s API)
   - Implement same interface as existing cloud SDK providers

**Implementation approach**:

```python
# multi_cloud_orchestrator.py
class CrossplaneProvider:
    def __init__(self, k8s_client):
        self.k8s = k8s_client

    def list_clusters(self):
        # Query XCluster resources
        clusters = self.k8s.list_cluster_claims()
        return [{
            'name': c.metadata.name,
            'provider': c.spec.compositionSelector.matchLabels['provider'],
            'endpoint': c.status.endpoint,
            'status': c.status.conditions[-1].type
        } for c in clusters]

    def get_database_connection(self, name, namespace):
        # Get XDatabase resource and return connection secret
        xdb = self.k8s.get_xdatabase(name, namespace)
        secret_name = xdb.spec.writeConnectionSecretToRef.name
        secret = self.k8s.get_secret(secret_name, namespace)
        return {
            'host': secret.data['host'],
            'port': secret.data['port'],
            'username': secret.data['username'],
            'password': secret.data['password']
        }

# Update MultiCloudAbstractionLayer to use CrossplaneProvider
```

This is a significant task; allocate time in Phase 3-4.

---

## Success Criteria for Phase 1

- [ ] All 4 providers installed and show `HEALTHY=True`
- [ ] ProviderConfigs exist for each cloud
- [ ] At least one managed resource successfully provisioned (test S3 bucket or equivalent)
- [ ] XRDs for core types (XNetwork, XCluster, XDatabase) are recognized by the API server
- [ ] GitOps pipeline (Flux/ArgoCD) configured to sync Crossplane resources from Git (OR manual apply documented)
- [ ] Multi-cloud orchestrator updated to detect Crossplane resources

---

## Rollback Plan

If providers fail to install or become healthy:
- Check provider logs: `kubectl logs -n crossplane-system deployment/provider-aws -c provider`
- Verify provider package image is accessible (xpkg.upbound.io)
- Check ProviderConfig credentials (if using secrets)
- Ensure cluster has outbound internet access to download provider packages

If managed resource creation fails:
- Check XResource status: `kubectl describe <resource> -n crossplane-system`
- Check managed resource status: `kubectl get <managed-resource> -n crossplane-system`
- Review provider logs for errors

---

## Deliverables

By end of Phase 1, we should have:

1. **Functional Crossplane control plane** with all cloud providers installed
2. **ProviderConfigs** properly configured (or documented for production setup)
3. **Test resource** (S3 bucket or equivalent) successfully created
4. **Validation logs** showing all checks passed
5. **Updated orchestrator** with Crossplane detection (in progress)

---

## Timeline

- **Day 1-2**: Install providers, configure credentials, verify health
- **Day 3**: Test managed resource creation, document issues
- **Day 4**: GitOps setup (if chosen)
- **Day 5**: Begin orchestrator Crossplane integration

---

**Next**: After Phase 1 complete, move to **Phase 2: Network Migration** - extend XNetwork XRD and migrate first VPCs.

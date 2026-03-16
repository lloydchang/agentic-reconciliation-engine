#!/usr/bin/env bash

set -euo pipefail
set -x   # optional, only if you want debug output

# 1. Create target directories
mkdir -p docs
mkdir -p examples/crossplane-compositions/{xdatabase,xnetwork,xcluster}
mkdir -p examples/eso-workload-identity/{eks,aks,gke,on-prem}

# 2. Docs
mv HUB-HA-RECOVERY.md BOOTSTRAP-CLUSTER.md CROSSPLANE-COMPOSITIONS.md \
   ESO-WORKLOAD-IDENTITY.md CI-POLICY-GATE.md CONTROLLER-RUNBOOKS.md docs/

# 3. Crossplane — flat files (these are all xdatabase + xcluster eks)
mv CROSSPLANE-README.md          examples/crossplane-compositions/README.md
mv xrd.yaml                      examples/crossplane-compositions/xdatabase/xrd.yaml
mv composition-aws.yaml          examples/crossplane-compositions/xdatabase/composition-aws.yaml
mv composition-azure.yaml        examples/crossplane-compositions/xdatabase/composition-azure.yaml
mv composition-gcp.yaml          examples/crossplane-compositions/xdatabase/composition-gcp.yaml
mv claim-example.yaml            examples/crossplane-compositions/xdatabase/claim-example.yaml
mv composition-eks.yaml          examples/crossplane-compositions/xcluster/composition-eks.yaml

# 4. ESO — flat files (these are all eks)
mv helmrelease-patch.yaml        examples/eso-workload-identity/eks/helmrelease-patch.yaml
mv cluster-secret-store.yaml     examples/eso-workload-identity/eks/cluster-secret-store.yaml
mv external-secret-example.yaml  examples/eso-workload-identity/eks/external-secret-example.yaml
mv helmrelease.yaml              examples/eso-workload-identity/on-prem/helmrelease.yaml

# 5. Crossplane — pull out of mnt/
MNT=mnt/user-data/outputs/examples
mv $MNT/crossplane-compositions/xnetwork/xrd.yaml          examples/crossplane-compositions/xnetwork/xrd.yaml
mv $MNT/crossplane-compositions/xnetwork/composition-aws.yaml examples/crossplane-compositions/xnetwork/composition-aws.yaml
mv $MNT/crossplane-compositions/xnetwork/claim-example.yaml   examples/crossplane-compositions/xnetwork/claim-example.yaml
mv $MNT/crossplane-compositions/xcluster/xrd.yaml          examples/crossplane-compositions/xcluster/xrd.yaml
mv $MNT/crossplane-compositions/xcluster/claim-example.yaml   examples/crossplane-compositions/xcluster/claim-example.yaml

# 6. ESO — pull out of mnt/
mv $MNT/eso-workload-identity/README.md                        examples/eso-workload-identity/README.md
mv $MNT/eso-workload-identity/aks/helmrelease-patch.yaml       examples/eso-workload-identity/aks/helmrelease-patch.yaml
mv $MNT/eso-workload-identity/aks/cluster-secret-store.yaml    examples/eso-workload-identity/aks/cluster-secret-store.yaml
mv $MNT/eso-workload-identity/aks/external-secret-example.yaml examples/eso-workload-identity/aks/external-secret-example.yaml
mv $MNT/eso-workload-identity/gke/helmrelease-patch.yaml       examples/eso-workload-identity/gke/helmrelease-patch.yaml
mv $MNT/eso-workload-identity/gke/cluster-secret-store.yaml    examples/eso-workload-identity/gke/cluster-secret-store.yaml
mv $MNT/eso-workload-identity/gke/external-secret-example.yaml examples/eso-workload-identity/gke/external-secret-example.yaml
mv $MNT/eso-workload-identity/on-prem/cluster-secret-store.yaml    examples/eso-workload-identity/on-prem/cluster-secret-store.yaml
mv $MNT/eso-workload-identity/on-prem/external-secret-example.yaml examples/eso-workload-identity/on-prem/external-secret-example.yaml

# 7. Delete the mnt/ tree
rm -rf mnt/

# 8. Verify — should show clean tree, nothing leftover
find docs examples -type f | sort
ls *.md *.yaml 2>/dev/null && echo "WARNING: flat files remain" || echo "Clean"
```

The expected `find` output is:
```
docs/BOOTSTRAP-CLUSTER.md
docs/CI-POLICY-GATE.md
docs/CONTROLLER-RUNBOOKS.md
docs/CROSSPLANE-COMPOSITIONS.md
docs/ESO-WORKLOAD-IDENTITY.md
docs/HUB-HA-RECOVERY.md
examples/crossplane-compositions/README.md
examples/crossplane-compositions/xcluster/claim-example.yaml
examples/crossplane-compositions/xcluster/composition-eks.yaml
examples/crossplane-compositions/xcluster/xrd.yaml
examples/crossplane-compositions/xdatabase/claim-example.yaml
examples/crossplane-compositions/xdatabase/composition-aws.yaml
examples/crossplane-compositions/xdatabase/composition-azure.yaml
examples/crossplane-compositions/xdatabase/composition-gcp.yaml
examples/crossplane-compositions/xdatabase/xrd.yaml
examples/crossplane-compositions/xnetwork/claim-example.yaml
examples/crossplane-compositions/xnetwork/composition-aws.yaml
examples/crossplane-compositions/xnetwork/xrd.yaml
examples/eso-workload-identity/README.md
examples/eso-workload-identity/aks/cluster-secret-store.yaml
examples/eso-workload-identity/aks/external-secret-example.yaml
examples/eso-workload-identity/aks/helmrelease-patch.yaml
examples/eso-workload-identity/eks/cluster-secret-store.yaml
examples/eso-workload-identity/eks/external-secret-example.yaml
examples/eso-workload-identity/eks/helmrelease-patch.yaml
examples/eso-workload-identity/gke/cluster-secret-store.yaml
examples/eso-workload-identity/gke/external-secret-example.yaml
examples/eso-workload-identity/gke/helmrelease-patch.yaml
examples/eso-workload-identity/on-prem/cluster-secret-store.yaml
examples/eso-workload-identity/on-prem/external-secret-example.yaml
examples/eso-workload-identity/on-prem/helmrelease.yaml

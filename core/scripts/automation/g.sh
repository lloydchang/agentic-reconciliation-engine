#!/usr/bin/env bash

set -euo pipefail
set -x   # optional, only if you want debug output

git add docs/ overlay/examples/crossplane-compositions/ overlay/examples/eso-workload-identity/
git status   # review what's staged
git commit -m "docs: add v2 operational docs and examples

- HUB-HA-RECOVERY, BOOTSTRAP-CLUSTER, CROSSPLANE-COMPOSITIONS,
  ESO-WORKLOAD-IDENTITY, CI-POLICY-GATE, CONTROLLER-RUNBOOKS
- overlay/examples/crossplane-compositions: XDatabase/XNetwork/XCluster XRDs,
  Compositions (AWS/Azure/GCP), and claim examples
- overlay/examples/eso-workload-identity: per-spoke ESO setup for EKS/AKS/GKE/on-prem"
git push

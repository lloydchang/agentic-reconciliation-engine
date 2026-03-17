# Hub Cold-Start Recovery (Offline Copy)

This file is stored in the bootstrap cluster path so recovery steps are available
even when the hub is unavailable.

1. Provision replacement hub cluster using `hub-cluster-config.yaml`
2. Bootstrap Flux on the replacement hub:
   `flux bootstrap github --owner=org --repository=gitops-infra-control-plane --branch=main --path=core/operators/flux`
3. Wait for Crossplane and CAPI providers to become Healthy
4. Verify managed resource reconciliation:
   `kubectl get managed -A`
5. Verify CAPI re-adopts spokes:
   `kubectl get clusters -A -o wide`
6. Verify spokes:
   `flux get all -A` on each spoke
7. Update bootstrap cluster hub kubeconfig Secret

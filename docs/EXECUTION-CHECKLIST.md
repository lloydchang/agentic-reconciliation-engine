# Execution Checklist

Apply in order:

1. Operator inputs
   - Review [docs/operator-inputs.md](docs/operator-inputs.md)
   - Update workload identity annotations
   - Update ClusterClass values (region/project/subscription)
   - Configure `control-plane/identity/*`

2. Bootstrap hub
   - Apply `control-plane/flux/`
   - Ensure `control-plane/crossplane/` and `control-plane/capi/` reconcile

3. Verify control plane
   - `kubectl get providers -A`
   - `kubectl get deployments -n capi-system`

4. Apply tenant layers
   - `infrastructure/tenants/1-network/`
   - `infrastructure/tenants/2-clusters/`
   - `infrastructure/tenants/3-workloads/`

5. Validate drift repair
   - Delete a managed resource in cloud console, confirm Crossplane re‑creates it
   - Delete a synced secret in a spoke, confirm ESO re‑creates it

6. Hub outage drill (non‑prod)
   - Follow [control-plane/bootstrap/recovery-procedure.md](control-plane/bootstrap/recovery-procedure.md)

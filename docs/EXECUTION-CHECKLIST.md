# Execution Checklist

Apply in order:

1. Operator inputs
   - Review [docs/operator-inputs.md](docs/operator-inputs.md)
   - Update workload identity annotations
   - Update ClusterClass values (region/project/subscription)
   - Configure `core/operators/identity/*`

2. Bootstrap hub
   - Apply `core/operators/flux/`
   - Ensure `core/operators/crossplane/` and `core/operators/capi/` reconcile

3. Verify control plane
   - `kubectl get providers -A`
   - `kubectl get deployments -n capi-system`

4. Apply tenant layers
   - `core/resources/tenants/1-network/`
   - `core/resources/tenants/2-clusters/`
   - `core/resources/tenants/3-workloads/`

5. Validate drift repair
   - Delete a managed resource in cloud console, confirm Crossplane re‑creates it
   - Delete a synced secret in a spoke, confirm ESO re‑creates it

6. Hub outage drill (non‑prod)
   - Follow [core/operators/bootstrap/recovery-procedure.md](core/operators/bootstrap/recovery-procedure.md)

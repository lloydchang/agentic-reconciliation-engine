# Crossplane Compositions — Examples

Working examples for each XRD type. Each subdirectory contains:

- `xrd.yaml` — CompositeResourceDefinition (platform team applies once to hub)
- `composition-<cloud>.yaml` — Composition per cloud provider (platform team)
- `claim-example.yaml` — Example claim (spoke team writes this)

## Directory Layout

```
xdatabase/
  xrd.yaml
  composition-aws.yaml
  composition-azure.yaml
  composition-gcp.yaml
  claim-example.yaml

xnetwork/
  xrd.yaml
  composition-aws.yaml
  composition-azure.yaml
  composition-gcp.yaml
  claim-example.yaml

xcluster/
  xrd.yaml
  composition-eks.yaml
  composition-aks.yaml
  composition-gke.yaml
  claim-example.yaml
```

## Quick Start

```bash
# Apply XRDs and Compositions to the hub (platform team, once)
kubectl apply -f xdatabase/xrd.yaml
kubectl apply -f xdatabase/composition-aws.yaml

# Apply a claim (spoke team, per resource)
kubectl apply -f xdatabase/claim-example.yaml

# Monitor claim reconciliation
kubectl describe database my-db -n my-team
```

See [CROSSPLANE-COMPOSITIONS.md](../../docs/CROSSPLANE-COMPOSITIONS.md) for full authoring guide.

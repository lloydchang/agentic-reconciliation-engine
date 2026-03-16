# Implementation Summary (Crossplane + CAPI + ESO)

This repository now implements the GitOps Infra Control Plane as described in the
implementation plan:

## Core Architecture

- **Flux** for GitOps reconciliation (hub + spokes).
- **Crossplane** XRDs/Compositions for cloud resources.
- **CAPI** for spoke cluster lifecycle.
- **ESO + workload identity** for per‑spoke secret delivery.

## Repository Structure (Active)

```
control-plane/
  flux/
  crossplane/          # XRDs, compositions, provider configs
  capi/                # CAPI providers + ClusterClasses
  bootstrap/           # bootstrap cluster + hub backup CronJob
  ci/                  # policy gate scripts + rego

infrastructure/tenants/
  1-network/           # XNetwork claims
  2-clusters/          # XCluster claims
  3-workloads/         # XDatabase/XQueue + ESO
```

## Fallbacks

Deprecated raw provider manifests and SOPS kustomizations moved under:

```
infrastructure/fallback/
  raw-controllers/
  capi-direct/
  sops/
```

## Operator Inputs

See:

- [control-plane/crossplane/README.md](control-plane/crossplane/README.md)
- [control-plane/capi/README.md](control-plane/capi/README.md)
- [docs/SETUP.md](docs/SETUP.md)

## CI Policy Gate

GitHub Actions workflow added in `.github/workflows/ci-policy-gate.yaml` with
deletion guard, schema validation, OPA policies, and Flux dry‑run.

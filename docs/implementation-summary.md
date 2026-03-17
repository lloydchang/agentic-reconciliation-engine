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
core/operators/
  flux/
  crossplane/          # XRDs, compositions, provider configs
  capi/                # CAPI providers + ClusterClasses
  bootstrap/           # bootstrap cluster + hub backup CronJob
  ci/                  # policy gate scripts + rego

core/resources/tenants/
  1-network/           # XNetwork claims
  2-clusters/          # XCluster claims
  3-workloads/         # XDatabase/XQueue + ESO
```

## Fallbacks

Deprecated raw provider manifests and SOPS kustomizations moved under:

```
core/resources/fallback/
  raw-controllers/
  capi-direct/
  sops/
```

## Operator Inputs

See:

- [core/operators/crossplane/README.md](core/operators/crossplane/README.md)
- [core/operators/capi/README.md](core/operators/capi/README.md)
- [docs/SETUP.md](docs/SETUP.md)

## CI Policy Gate

GitHub Actions workflow added in `.github/workflows/ci-policy-gate.yaml` with
deletion guard, schema validation, OPA policies, and Flux dry‑run.

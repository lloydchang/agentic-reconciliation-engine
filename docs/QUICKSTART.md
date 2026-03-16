# Quickstart - MVP GitOps Infrastructure

Get a working GitOps control plane running locally in minutes.

## Prerequisites

- `kubectl`, `helm`, `kind` (for local clusters)
- POSIX shell (bash, WSL, Git Bash)

## MVP Setup (One Command)

```bash
# One-command MVP setup
./scripts/setup-mvp.sh
```

Or run steps manually:

```bash
# 1. Validate your environment
./scripts/prerequisites.sh

# 2. Setup GitOps configuration
./scripts/setup-gitops-config.sh

# 3. Create bootstrap cluster (local recovery anchor)
./scripts/create-bootstrap-cluster.sh

# 4. Create hub cluster (local for MVP)
./scripts/create-hub-cluster.sh --provider local

# 5. Create spoke cluster (MVP - local emulation)
./scripts/create-spoke-clusters.sh
```

## MVP Options

```bash
# Full MVP setup
./scripts/setup-mvp.sh

# Preview commands without running
./scripts/setup-mvp.sh --dry-run

# Skip specific steps (useful for re-running)
./scripts/setup-mvp.sh --skip-spoke    # Setup bootstrap + hub only
./scripts/setup-mvp.sh --skip-hub       # Setup bootstrap + spokes only
```

## What You Get

✅ **Bootstrap Cluster** - Recovery anchor for hub cluster  
✅ **Hub Cluster** - Runs Flux, Crossplane, Cluster API  
✅ **Spoke Cluster** - Local kind cluster for workloads  
✅ **GitOps Workflow** - Full continuous reconciliation  
✅ **Zero Cloud Costs** - Everything runs locally  

## Verify Your MVP

```bash
# Check all clusters
kubectl get clusters -n gitops-system

# Check Flux status
kubectl get pods -n flux-system

# Check Crossplane
kubectl get providers -n crossplane-system
```

## Next Steps

- **Add Real Cloud**: `./scripts/create-spoke-clusters.sh --providers azure`
- **Multi-Cloud**: `./scripts/create-spoke-clusters.sh --providers azure,aws,gcp`
- **Production**: Use real cloud providers for hub cluster

## Architecture

```
Bootstrap Cluster (local) → Hub Cluster (local) → Spoke Cluster (local)
        ↓                           ↓                      ↓
   Recovery Config         Flux + Crossplane      Workloads + Apps
```

---

**MVP Benefits**: No cloud costs, no credentials, full GitOps validation.  

**For production deployment**, see `docs/OVERVIEW.md`.

---
name: phase1-crossplane-setup
description: Automates Crossplane provider installation, validation, and initial setup for Phase 1 migration. Use when setting up a new Crossplane control plane or validating provider health. Handles provider installation, health checks, XRD validation, test resource creation, GitOps integration, and orchestrator preparation.
license: AGPLv3
metadata:
  author: agentic-reconciliation-engine
  version: "1.0"
  category: crossplane
  risk_level: medium
  autonomy: conditional
  layer: gitops
  human_gate: Requires PR approval for provider installation in production clusters
compatibility: Requires Python 3.8+, kubectl configured with cluster admin access, and Kubernetes cluster with Crossplane not yet installed OR needing validation. Flux CLI optional for GitOps setup.
allowed-tools: Bash Read Write Grep

---

# Phase 1 Crossplane Setup Skill

This skill automates the complete Phase 1 Crossplane migration implementation as documented in `docs/migration/PHASE1-IMPLEMENTATION-PLAN.md`.

## When to Use

Use this skill when:

- Setting up Crossplane for the first time on a new cluster
- Validating that all providers (AWS, Azure, GCP, Kubernetes) are installed and healthy
- Needing to create test managed resources to verify provider functionality
- Setting up GitOps (Flux CD) to manage Crossplane configurations
- Preparing the environment for Phase 2+ migrations

## What It Does

The automation script (`core/ai/skills/phase1-crossplane-setup/scripts/phase1_setup.py`) performs:

1. **Prerequisites Check**: Validates kubectl availability and cluster connectivity
2. **Provider Installation**: Applies provider definitions from `core/operators/control-plane/crossplane/providers/`
3. **Health Validation**: Waits for all providers to reach Healthy status
4. **ProviderConfig Verification**: Confirms credentials/configs are properly set
5. **XRD Validation**: Checks that core XRDs (XNetwork, XCluster, XDatabase) are registered
6. **Test Resource Creation** (optional): Creates an S3 bucket to verify AWS provider
7. **GitOps Setup** (optional): Installs Flux and configures GitRepository/Kustomization
8. **Orchestrator Check**: Verifies CrossplaneProvider integration status

## Usage

### Via Agent

```bash
# Full automated setup with all features
/phase1-crossplane-setup

# Dry run to see what would happen
/phase1-crossplane-setup --dry-run

# Skip provider installation (assume already installed)
/phase1-crossplane-setup --skip-providers

# Skip GitOps setup
/phase1-crossplane-setup --skip-gitops

# Include test resource creation
/phase1-crossplane-setup --test-resource
```

### Manual Execution

```bash
cd core/ai/skills/phase1-crossplane-setup/scripts
python3 phase1_setup.py [options]
```

## Required Permissions

The skill requires:

- K8s cluster-admin role to install providers and create resources
- Flux CLI installed if using GitOps feature
- Internet access to download provider packages from xpkg.upbound.io
- AWS credentials configured if creating test S3 bucket

## Success Criteria

- [ ] All 4 providers (AWS, Azure, GCP, Kubernetes) show `HEALTHY=True`
- [ ] ProviderConfigs exist for each provider in `crossplane-system` namespace
- [ ] Provider-specific CRDs are registered (can verify with `kubectl get crd | grep aws`)
- [ ] Test resource (S3 bucket) reaches `Ready=True` condition (if `--test-resource` used)
- [ ] Core XRDs are recognized by the API server
- [ ] Flux installed and GitRepository/Kustomization created (if `--skip-gitops` not used)
- [ ] CrossplaneProvider class exists in orchestrator (manual check)

## Rollback

If installation fails:

1. **Provider failures**: Check logs with `kubectl logs -n crossplane-system deployment/provider-aws -c provider`
2. **Credential issues**: Verify ProviderConfig has correct secret references
3. **Network issues**: Ensure cluster has outbound internet access for xpkg downloads
4. **Cleanup**: `kubectl delete -k core/operators/control-plane/crossplane/providers`

## Risk Mitigation

- **Medium risk**: Installations modify cluster state but are reversible
- **Always use `--dry-run` first** in non-production environments
- **Requires PR approval** for production clusters (set via `human_gate`)
- **Monitor costs**: Test resources incur cloud provider charges
- **Keep credentials secure**: Do not commit ProviderConfig secrets; use external secrets operator

## References

- Implementation plan: `docs/migration/PHASE1-IMPLEMENTATION-PLAN.md`
- Crossplane documentation: https://docs.crossplane.io/
- Provider packages: https://xpkg.upbound.io/
- Repository structure: `core/operators/control-plane/crossplane/`

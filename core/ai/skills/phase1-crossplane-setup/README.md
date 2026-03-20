# Phase 1 Crossplane Setup Skill

This skill automates the initial Crossplane foundation setup and provider validation as per the [Phase 1 Implementation Plan](../../docs/migration/PHASE1-IMPLEMENTATION-PLAN.md).

## Quick Start

```bash
# In the agent system, invoke:
/phase1-crossplane-setup --test-resource

# Or run the script directly:
cd core/operators/control-plane/crossplane/scripts
python3 phase1_setup.py --test-resource
```

## What Gets Automated

1. ✅ Prerequisites check (kubectl, cluster connectivity, Crossplane)
2. ✅ Install 4 providers (AWS, Azure, GCP, Kubernetes)
3. ✅ Wait for HEALTHY status on all providers
4. ✅ Verify ProviderConfigs and CRD registration
5. ✅ Validate core XRD definitions
6. ✅ Create test S3 bucket (optional)
7. ✅ Setup Flux GitOps (optional)
8. ✅ Check orchestrator integration status

## Files

- `SKILL.md` - Skill definition (agentskills.io compliant)
- `scripts/phase1_setup.py` - Main automation script (also in `core/operators/...`)
- `examples/simple_setup.sh` - Run full setup with test resource
- `examples/validate_only.sh` - Validate existing installation

## Integration

When invoked through the agent system, this skill:

1. Loads the Python script from the repository
2. Executes with appropriate permissions (cluster-admin assumed)
3. Logs all output to Temporal/GitOps for audit trail
4. Creates PRs if `autonomy: conditional` (medium risk operations)
5. Updates memory with verification results

## Success Criteria

Refer to `docs/migration/PHASE1-IMPLEMENTATION-PLAN.md` for complete success criteria and rollback procedures.

## Support

See the main [Implementation Plan](../../docs/migration/PHASE1-IMPLEMENTATION-PLAN.md) for detailed documentation.

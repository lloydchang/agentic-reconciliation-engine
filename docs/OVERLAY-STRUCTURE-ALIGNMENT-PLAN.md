# Overlay Structure Alignment Plan

## Overview

This document outlines the plan to align the overlay directory structure with the core directory structure, ensuring that overlays mirror the core hierarchy as intended by the architecture.

## Current State Analysis

### Issue Identified

The overlay system has a structural mismatch:

**Current Reality:**
```
gitops-infra-control-plane/
├── core/                           # Base components
│   ├── ai/
│   ├── automation/
│   ├── config/
│   ├── deployment/
│   ├── governance/
│   ├── operators/
│   ├── resources/
│   └── workspace/
└── overlay/                        # Overlay extensions (MISMATCHED)
    ├── editions/
    │   └── editions/
    └── examples/
        └── examples/
```

**Documented Architecture:**
```
gitops-infra-control-plane/
├── core/                           # Base components
│   ├── ai/
│   ├── automation/
│   ├── config/
│   ├── deployment/
│   ├── governance/
│   ├── operators/
│   ├── resources/
│   └── workspace/
└── overlay/                        # Overlay extensions (ALIGNED)
    ├── ai/                         # Mirror core/ai/
    ├── automation/                 # Mirror core/automation/
    ├── config/                     # Mirror core/config/
    ├── deployment/                 # Mirror core/deployment/
    ├── governance/                 # Mirror core/governance/
    ├── operators/                  # Mirror core/operators/
    ├── resources/                  # Mirror core/resources/
    └── workspace/                  # Mirror core/workspace/
```

### Problems with Current Structure

1. **Non-mirrored hierarchy**: Overlay doesn't mirror core structure
2. **Nested redundancy**: `overlay/editions/editions/` and `overlay/examples/examples/`
3. **Documentation mismatch**: Docs reference `core/deployment/overlays/` but overlays are at root level
4. **Confusing organization**: Content is not logically mapped to core components

## Target Structure

### Proposed Overlay Directory Structure

```
overlay/
├── ai/                              # Mirror core/ai/
│   ├── skills/                      # Overlay extensions for AI skills
│   │   ├── debug-enhanced/
│   │   ├── ml-optimized/
│   │   └── custom-skills/
│   └── runtime/                     # Overlay extensions for AI runtime
│       ├── dashboard-themes/
│       ├── custom-widgets/
│       └── integrations/
├── automation/                      # Mirror core/automation/
│   ├── ci-cd/                       # CI/CD pipeline overlays
│   │   ├── enhanced-pipelines/
│   │   └── custom-jenkins/
│   ├── scripts/                     # Script overlays
│   └── testing/                     # Testing framework overlays
├── config/                          # Mirror core/config/
│   ├── kind/                        # Kind cluster overlays
│   ├── kubeconfigs/                 # Kubeconfig overlays
│   ├── sops/                        # SOPS overlays
│   └── scripts/                    # Configuration script overlays
├── deployment/                      # Mirror core/deployment/
│   ├── overlays/                    # Kustomize overlays
│   │   ├── development/
│   │   ├── staging/
│   │   └── production/
│   └── templates/                   # Deployment templates
├── governance/                      # Mirror core/governance/
│   ├── policies/                    # Policy overlays
│   │   ├── enhanced-security/
│   │   └── custom-compliance/
│   └── scripts/                     # Governance script overlays
├── operators/                       # Mirror core/operators/
│   ├── control-plane/               # Control plane overlays
│   │   ├── flux-enhanced/
│   │   ├── monitoring-extended/
│   │   └── custom-controllers/
│   └── crossplane/                  # Crossplane overlays
├── resources/                       # Mirror core/resources/
│   ├── infrastructure/              # Infrastructure overlays
│   ├── applications/                # Application overlays
│   └── monitoring/                  # Monitoring resource overlays
├── workspace/                       # Mirror core/workspace/
│   ├── workspace/                   # Workspace configuration overlays
│   └── templates/                   # Workspace templates
├── editions/                        # Special overlay collections
│   ├── enterprise/                  # Enterprise edition overlays
│   ├── opensource/                  # Open source edition overlays
│   └── languages/                   # Language-specific overlays
│       ├── csharp/
│       ├── go/
│       ├── java/
│       ├── python/
│       ├── rust/
│       └── typescript/
└── examples/                        # Complete example overlays
    ├── complete-hub-spoke/
    ├── complete-hub-spoke-consensus/
    ├── complete-hub-spoke-kagent/
    ├── complete-hub-spoke-temporal/
    └── template-multi-cloud/
```

## Migration Plan

### Phase 1: Documentation Updates

1. **Update Architecture Documentation**
   - Fix `OVERLAY-ARCHITECTURE.md` to reflect actual structure
   - Update all overlay documentation to use correct paths
   - Update examples and code snippets

2. **Update Developer Guide**
   - Fix `OVERLAY-DEVELOPER-GUIDE.md` paths
   - Update CLI tool documentation
   - Fix template paths and examples

3. **Update All Overlay Documentation**
   - Fix path references in all overlay-related docs
   - Update quick start guides
   - Fix cheat sheets and FAQs

### Phase 2: Content Migration

1. **Create New Directory Structure**
   ```bash
   # Create new overlay directories mirroring core
   mkdir -p overlay/ai/skills
   mkdir -p overlay/ai/runtime
   mkdir -p overlay/automation/ci-cd
   mkdir -p overlay/automation/scripts
   mkdir -p overlay/automation/testing
   mkdir -p overlay/config/kind
   mkdir -p overlay/config/kubeconfigs
   mkdir -p overlay/config/sops
   mkdir -p overlay/config/scripts
   mkdir -p overlay/deployment/overlays
   mkdir -p overlay/deployment/templates
   mkdir -p overlay/governance/policies
   mkdir -p overlay/governance/scripts
   mkdir -p overlay/operators/control-plane
   mkdir -p overlay/operators/crossplane
   mkdir -p overlay/resources/infrastructure
   mkdir -p overlay/resources/applications
   mkdir -p overlay/resources/monitoring
   mkdir -p overlay/workspace/workspace
   mkdir -p overlay/workspace/templates
   ```

2. **Migrate Existing Content**
   - Move content from `overlay/editions/editions/` to `overlay/editions/`
   - Move content from `overlay/examples/examples/` to `overlay/examples/`
   - Organize content by appropriate core component mapping
   - Preserve all existing functionality

3. **Update References**
   - Update all kustomization.yaml files
   - Fix relative paths in overlays
   - Update import statements and references

### Phase 3: Tool Updates

1. **Update CLI Tools**
   - Fix overlay CLI to use new structure
   - Update validation scripts
   - Fix registry tools

2. **Update Templates**
   - Fix overlay templates
   - Update scaffold generators
   - Fix example templates

3. **Update Tests**
   - Fix test paths
   - Update integration tests
   - Fix validation tests

### Phase 4: Validation

1. **Structure Validation**
   - Validate all overlays follow new structure
   - Test overlay composition
   - Verify kustomize builds work

2. **Functionality Testing**
   - Test overlay deployment
   - Validate overlay registry
   - Test CLI tools

3. **Documentation Validation**
   - Verify all documentation is accurate
   - Test all examples
   - Validate quick start guides

## Detailed Migration Steps

### Step 1: Backup Current Structure
```bash
# Create backup
cp -r overlay overlay-backup-$(date +%Y%m%d)
```

### Step 2: Create New Structure
```bash
# Create base directories
mkdir -p overlay/{ai,automation,config,deployment,governance,operators,resources,workspace}

# Create subdirectories mirroring core
mkdir -p overlay/ai/{skills,runtime}
mkdir -p overlay/automation/{ci-cd,scripts,testing}
mkdir -p overlay/config/{kind,kubeconfigs,sops,scripts}
mkdir -p overlay/deployment/{overlays,templates}
mkdir -p overlay/governance/{policies,scripts}
mkdir -p overlay/operators/{control-plane,crossplane}
mkdir -p overlay/resources/{infrastructure,applications,monitoring}
mkdir -p overlay/workspace/{workspace,templates}

# Keep special directories
mkdir -p overlay/editions
mkdir -p overlay/examples
```

### Step 3: Migrate Content

#### Migrate Editions
```bash
# Fix nested editions structure
mv overlay/editions/editions/* overlay/editions/
rmdir overlay/editions/editions
```

#### Migrate Examples
```bash
# Fix nested examples structure
mv overlay/examples/examples/* overlay/examples/
rmdir overlay/examples/examples
```

#### Organize Examples by Core Component
```bash
# Move examples to appropriate locations
# For example, AI-related examples
mkdir -p overlay/ai/skills/examples
mv overlay/examples/complete-hub-spoke/agent-workflows overlay/ai/skills/examples/

# Infrastructure examples
mkdir -p overlay/operators/control-plane/examples
mv overlay/examples/complete-hub-spoke/ai-cronjobs overlay/operators/control-plane/examples/
```

### Step 4: Update All References

#### Update Kustomization Files
```bash
# Find all kustomization.yaml files and update paths
find overlay -name "kustomization.yaml" -exec sed -i '' 's|../examples/|../../examples/|g' {} \;
```

#### Update Documentation
```bash
# Fix documentation references
find docs -name "*.md" -exec sed -i '' 's|core/deployment/overlays/|overlay/|g' {} \;
```

## Implementation Timeline

| Phase | Duration | Owner | Status |
|-------|----------|-------|--------|
| Phase 1: Documentation Updates | 2 days | Documentation Team | Not Started |
| Phase 2: Content Migration | 3 days | Development Team | Not Started |
| Phase 3: Tool Updates | 2 days | Tools Team | Not Started |
| Phase 4: Validation | 1 day | QA Team | Not Started |

## Success Criteria

1. **Structure Alignment**: Overlay directory structure mirrors core structure
2. **Documentation Accuracy**: All documentation reflects actual structure
3. **Functionality Preservation**: All existing overlays continue to work
4. **Tool Compatibility**: All CLI tools work with new structure
5. **Test Coverage**: All tests pass with new structure

## Risk Mitigation

### Risks

1. **Breaking Changes**: Existing overlays may break
2. **Tool Incompatibility**: CLI tools may not work
3. **Documentation Confusion**: Mixed documentation during transition
4. **Content Loss**: Content may be lost during migration

### Mitigation Strategies

1. **Backup Strategy**: Complete backup before migration
2. **Incremental Migration**: Migrate gradually to minimize disruption
3. **Validation Testing**: Test thoroughly at each step
4. **Rollback Plan**: Clear rollback procedure if issues arise

## Rollback Plan

If migration fails:

1. **Stop Migration**: Halt at current point
2. **Restore Backup**: Restore from backup
3. **Assess Issues**: Identify what went wrong
4. **Plan Fix**: Address issues before retry

## Post-Migration Tasks

1. **Update Training Materials**: Update any training or onboarding materials
2. **Communicate Changes**: Notify team of new structure
3. **Archive Old Documentation**: Archive outdated documentation
4. **Update CI/CD**: Update any automated processes

## Conclusion

This migration will align the overlay structure with the core architecture, making the system more intuitive and maintainable. The mirror structure will make it easier for developers to understand where overlays should be placed and how they relate to base components.

The phased approach minimizes risk while ensuring thorough validation at each step. The result will be a cleaner, more logical overlay system that matches the documented architecture.

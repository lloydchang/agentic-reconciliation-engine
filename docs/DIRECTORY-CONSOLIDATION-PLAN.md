# Directory Consolidation Plan

## Overview

This document outlines the plan to consolidate the current 15+ root-level directories into a clean structure with only 2 main directories: `core/` and `overlay/`.

## Current Root Structure

```
core/ai/skills/ (4 items)        → core/ai/skills/
.claude (7 bytes)         → KEEP (IDE-specific)
.codex (7 bytes)          → KEEP (IDE-specific)
.cursor (7 bytes)         → KEEP (IDE-specific)
.git/ (0 items)           → KEEP (Git metadata)
.github/ (11 items)       → KEEP (GitHub workflows)
.gitignore (10181 bytes)  → KEEP (Git ignore)
.windsurf (7 bytes)       → KEEP (IDE-specific)
AGENTS.md (10773 bytes)   → KEEP (Agent documentation)
CLAUDE.md (9 bytes)       → KEEP (IDE-specific)
CONTRIBUTING.md (3210 bytes) → KEEP (Contributing guide)
GEMINI.md (9 bytes)       → KEEP (IDE-specific)
LICENSE (34523 bytes)     → KEEP (License)
README.md (2959 bytes)    → KEEP (Repository README)
core/ai/runtime/ (107 items)       → core/ai/runtime/
core/automation/ci-cd/ (4 items)     → core/core/automation/ci-cd/ci-cd/
bootstrap-kubeconfig (5675 bytes) → core/config/kubeconfigs/
core/operators/ (166 items) → core/operators/
docs/ (224 items)         → KEEP (Documentation)
overlay/editions/ (8 items)       → overlay/overlay/editions/
overlay/examples/ (92 items)      → overlay/overlay/examples/
fix_workspace_skills.sh (3929 bytes) → core/config/core/core/automation/ci-cd/scripts/
core/config/go.mod (103 bytes)        → KEEP (Go module)
hub-kubeconfig (5639 bytes) → core/config/kubeconfigs/
core/resources/ (365 items) → core/resources/
kind-config.yaml (689 bytes) → core/config/kind/
logs/ (0 items)           → DELETE (Ephemeral logs)
core/deployment/overlays/ (0 items)       → core/deployment/core/deployment/overlays/
core/governance/ (6 items)       → core/governance/
core/core/automation/ci-cd/scripts/ (135 items)      → core/core/automation/ci-cd/core/core/automation/ci-cd/scripts/
core/automation/testing/ (22 items)         → core/core/automation/ci-cd/testing/
tmp/ (0 items)            → DELETE (Temporary files)
core/workspace/ (956 items)    → core/core/workspace/
```

## Target Structure

```
core/                    # Complete GitOps infrastructure system
├── operators/          # core/operators/ → operators/
├── resources/          # core/resources/ → resources/
├── governance/         # core/governance/ → governance/
├── core/automation/ci-cd/         # core/core/automation/ci-cd/scripts/ + core/automation/ci-cd/ → core/automation/ci-cd/
│   ├── ci-cd/         # core/automation/ci-cd/ (Jenkins, Azure Pipelines)
│   ├── core/core/automation/ci-cd/scripts/       # core/core/automation/ci-cd/scripts/ (135+ automation scripts)
│   └── testing/       # core/automation/testing/ (test suites)
├── ai/                # core/ai/skills/ + core/ai/runtime/ → ai/
│   ├── skills/       # core/ai/skills/ (72+ AI skills)
│   └── runtime/      # core/ai/runtime/ (Temporal runtime + dashboard)
├── deployment/        # core/deployment/overlays/ + deployment configs
│   └── core/deployment/overlays/     # core/deployment/overlays/ (overlay configurations)
├── config/            # Configuration files
│   ├── sops/         # .sops.pub.age + .sops.yaml
│   ├── kubeconfigs/  # bootstrap-kubeconfig + hub-kubeconfig
│   ├── kind/         # kind-config.yaml
│   └── core/core/automation/ci-cd/scripts/      # fix_workspace_skills.sh
└── core/workspace/         # core/workspace/ (working environment)

overlay/                 # Variants and configurations
├── overlay/editions/          # overlay/editions/ (enterprise/opensource)
└── overlay/examples/          # overlay/examples/ (reference implementations)
```

## Top-Level Directory Contents

The only directories/files that remain at root level are:

- `.agents` (hidden) → will be moved
- `.claude` (IDE-specific)
- `.codex` (IDE-specific)
- `.cursor` (IDE-specific)
- `.git/` (Git metadata)
- `.github/` (GitHub workflows)
- `.gitignore` (Git ignore rules)
- `.windsurf` (IDE-specific)
- [AGENTS.md](AGENTS.md) (Agent documentation)
- [CLAUDE.md](CLAUDE.md) (IDE-specific)
- [CONTRIBUTING.md](CONTRIBUTING.md) (Contributing guide)
- `core/` (new consolidated directory)
- `docs/` (documentation)
- [GEMINI.md](GEMINI.md) (IDE-specific)
- `LICENSE` (license)
- `overlay/` (new consolidated directory)
- [README.md](README.md) (repository README)

Everything else moves into `core/` by default, unless it belongs in `overlay/` as a variant/configuration.

## Implementation Plan

### Phase 1: Create New Structure
```bash
# Create new directories
mkdir -p core/{operators,resources,governance,core/automation/ci-cd/{ci-cd,scripts,testing},ai/{skills,runtime},deployment/overlays,config/{sops,kubeconfigs,kind,scripts},workspace}
mkdir -p overlay/{editions,examples}

# Move directories
mv control-plane core/operators/
mv infrastructure core/resources/
mv policies core/governance/
mv automation core/core/automation/ci-cd/ci-cd/
mv scripts core/core/automation/ci-cd/core/core/automation/ci-cd/scripts/
mv tests core/core/automation/ci-cd/testing/
mv .agents core/ai/skills/
mv agents core/ai/runtime/
mv overlays core/deployment/core/deployment/overlays/
mv editions overlay/overlay/editions/
mv examples overlay/overlay/examples/
mv workspace core/core/workspace/

# Move config files
mv .sops.pub.age core/config/sops/
mv .sops.yaml core/config/sops/
mv bootstrap-kubeconfig core/config/kubeconfigs/
mv hub-kubeconfig core/config/kubeconfigs/
mv kind-config.yaml core/config/kind/
mv fix_workspace_skills.sh core/config/core/core/automation/ci-cd/scripts/
```

### Phase 2: Update References
- Update all import paths and relative references
- Update CI/CD pipeline configurations
- Update documentation links
- Update script paths

### Phase 3: Clean Up
- Remove empty directories
- Delete ephemeral files (logs/, tmp/)
- Update .gitignore if needed

### Phase 4: Testing
- Run existing automation scripts
- Verify CI/CD pipelines
- Test documentation links
- Validate all imports

## Benefits

1. **Reduced Complexity**: From 15+ root directories to 2 main directories
2. **Clear Organization**: Core infrastructure vs configuration variants
3. **Better Discoverability**: Related functionality grouped together
4. **Scalable Structure**: Easy to add new components within logical domains
5. **Clean Root**: Only essential files and IDE-specific configs remain

## Impact Assessment

### Files to Move
- 15+ directories consolidated into 2
- 1000+ files reorganized
- No functional changes to code

### Breaking Changes
- All relative paths need updating
- Documentation links need updating
- CI/CD configurations need updating

### Risk Mitigation
- Create backup branch before changes
- Update references systematically
- Test incrementally after each phase

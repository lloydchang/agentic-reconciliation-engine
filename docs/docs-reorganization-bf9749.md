# Documentation Reorganization Plan

Create a hierarchical docs/ directory structure to improve documentation organization and reduce overlap.

## Implementation Steps

### Phase 1: Create Directory Structure
- Create `docs/` directory with subdirectories: `user-guide/`, `developer-guide/`, `reference/`
- Move existing docs files to appropriate locations

### Phase 2: Consolidate User-Facing Content
- **docs/README.md**: Create main docs landing page with navigation
- **docs/user-guide/getting-started.md**: Quick start and prerequisites (from current README)
- **docs/user-guide/skills-reference.md**: Consolidate QUICK-REFERENCE.md + Cloud-AI-Agent-README.md skill content
- **docs/user-guide/workflows.md**: Composite workflows documentation
- **docs/user-guide/troubleshooting.md**: Troubleshooting guide from current README

### Phase 3: Reorganize Developer Content
- **docs/developer-guide/agent-behavior.md**: Agent rules and behavior (split from AGENTS.md)
- **docs/developer-guide/operational-procedures.md**: Workflow execution and operations (split from AGENTS.md)
- **docs/developer-guide/skills-api.md**: Technical API specs (SKILL.md content)
- **docs/developer-guide/implementation.md**: Technical implementation details (IMPLEMENTATION_SUMMARY.md)
- **docs/developer-guide/extending.md**: Contributing and extension guide

### Phase 4: Create Reference Documentation
- **docs/reference/cli-commands.md**: CLI command reference
- **docs/reference/api-reference.md**: API endpoint documentation
- **docs/reference/configuration.md**: Configuration and environment variables

### Phase 5: Update Main README
- Simplify main README.md to focus on overview, quick start, and navigation to docs/
- Remove duplicate content now in docs/
- Update all cross-references to point to new locations

### Phase 6: Clean Up and Validation
- Remove obsolete files (Cloud-AI-Agent-README.md, IMPLEMENTATION_SUMMARY.md)
- Update gitignore if needed
- Validate all links and references work
- Test documentation navigation

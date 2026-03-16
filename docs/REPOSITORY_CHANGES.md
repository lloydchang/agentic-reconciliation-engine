# Repository Organization Changes

## Overview

This document outlines the comprehensive repository reorganization completed to achieve full compliance with `agentskills.io` specifications and AI coding tool conventions (as of 2025). All changes were made to improve maintainability, tool compatibility, and adherence to emerging standards.

## Changes Summary

### 1. Agent Skills System Compliance (`agentskills.io`)

**Changes Made:**

- Moved root [SKILL.md](SKILL.md) → [docs/system-interface.md](docs/system-interface.md)
- Created 40 individual [SKILL.md](SKILL.md) files in `.agents/skills/*/SKILL.md` directories
- Each skill file follows proper YAML frontmatter format with `name`, `description`, `tools` fields

**Justification:**

- `agentskills.io` specification requires individual skills to be in their own directories with [SKILL.md](SKILL.md) files
- Root-level [SKILL.md](SKILL.md) violated the specification which states: "A skill is a folder containing a SKILL.md file"
- Citation: `agentskills.io/specification` - "Directory structure" section

**Reasoning:**

- Ensures compatibility with tools that follow `agentskills.io` standards
- Allows for modular skill development and discovery
- Separates system documentation from individual skill definitions

### 2. AI Coding Tool Conventions (AGENTS.md)

**Changes Made:**

- Maintained [AGENTS.md](AGENTS.md) in repository root
- Created [CLAUDE.md](CLAUDE.md) as symlink to [AGENTS.md](AGENTS.md)
- Moved legacy [CLAUDE.md](CLAUDE.md) and [GEMINI.md](GEMINI.md) to `docs/legacy-configs/`

**Existing Symlinks (Pre-existing):**

- `.claude` → `.agents` (Claude tool configuration)
- `.codex` → `.agents` (GitHub Copilot/Codex configuration)  
- `.cursor` → `.agents` (Cursor IDE configuration)
- `.windsurf` → `.agents` (Windsurf IDE configuration)

**Justification:**

- 2025 community convention established [AGENTS.md](AGENTS.md) as unified configuration for AI coding tools
- Eliminates need for tool-specific config files (CLAUDE.md, GEMINI.md, .cursorrules)
- Citation: Cobus Greyling Substack - "In mid-2025 the community converged on one convention… A single plain-Markdown file called AGENTS.md"

**Reasoning for Symlinks:**

- **Tool-specific dotfiles** (`.claude`, `.cursor`, etc.) are IDE/tool conventions for configuration discovery
- **Pointing to `.agents/`** allows tools to access the skill system while maintaining their expected configuration paths
- **Prevents conflicts** between tool-specific expectations and the unified agentskills.io structure
- **Maintains compatibility** with tools that look for their branded configuration directories

**Reasoning:**

- Single source of truth for coding standards and project rules
- Automatic recognition by Cursor, GitHub Copilot, Windsurf, Continue.dev, Aider, OpenHands
- Symlink solution for Claude Code due to documented `@AGENTS.md` reference unreliability (GitHub issue #6235 with 2.1K+ upvotes)

### 3. Repository Structure Organization

**Changes Made:**

- **Root directory cleanup:** Removed all non-essential files from root
- **File relocations:**
  - Binaries: `ai-agent` → `tools/`
  - Go modules: `go.mod`, `go.sum` → `infrastructure/`
  - Kubernetes manifests: `*.yaml` → `infrastructure/`
  - Shell scripts: `*.sh`, `*.js` → `scripts/`
  - Documentation: `LICENSE`, [README.md](README.md), diagrams → `docs/`
  - Sample data: `agent-data.json` → `examples/`

**Justification:**

- Industry best practices require clean repository roots
- Separates concerns by file type and purpose
- SOPS configuration (`sops.yaml`, `.sops.pub.age`) must remain in root per SOPS conventions

**Reasoning:**

- Improves discoverability and reduces clutter
- Follows standard project layouts (tools/, scripts/, docs/, examples/)
- Maintains tool compatibility (Git, SOPS, AI assistants)

### 4. Cross-Reference Documentation

**Changes Made:**

- Added implementation references in [docs/system-interface.md](docs/system-interface.md)
- Updated [ai-agents/README.md](ai-agents/README.md) and [ai-agents/docs/README.md](ai-agents/docs/README.md) with links to system docs
- Modified [AGENTS.md](AGENTS.md) repository structure diagram to reflect new layout

**Justification:**

- Ensures seamless navigation between interface specifications and implementation
- Prevents documentation drift between API docs and code

**Reasoning:**

- Developers can easily move between high-level API docs and actual implementation
- Maintains single source of truth while providing multiple entry points

## Impact Assessment

### Positive Impacts

- ✅ **agentskills.io compliant** - Skills properly structured for tool discovery
- ✅ **AI tool compatible** - Supports Claude Code, Gemini CLI, Cursor, Windsurf, etc.
- ✅ **Organized codebase** - Clean directory structure following industry standards
- ✅ **Maintainable** - Single AGENTS.md source with automatic updates via symlink
- ✅ **Discoverable** - Proper file placement per conventions

### Tool Compatibility Matrix

| Tool | Compatibility | Method |
|------|---------------|--------|
| Claude Code | ✅ Compatible | Symlink to AGENTS.md |
| Gemini CLI | ✅ Compatible | Native AGENTS.md support |
| Cursor | ✅ Compatible | Native AGENTS.md support |
| Windsurf | ✅ Compatible | Native AGENTS.md support |
| GitHub Copilot | ✅ Compatible | Native AGENTS.md support |

## Citations and References

1. **agentskills.io Specification:** "Directory structure" - requires SKILL.md in individual skill directories
2. **Cobus Greyling (2025):** "What is AGENTS.md?" - community convergence on AGENTS.md standard
3. **AI Engineer Guide (2025):** "How to use AGENTS.md in Claude Code" - documents @AGENTS.md workaround
4. **GitHub Issue #6235:** Anthropic/claude-code - 2.1K+ upvotes requesting native AGENTS.md support
5. **Medium Article (2025):** "Complete Guide to AI Agent Memory Files" - tool support matrix

## Future Considerations

- Monitor Claude Code for native AGENTS.md support (tracked in GitHub issue #6235)
- Consider removing CLAUDE.md symlink if native support is added
- Regular review of AI tool conventions as standards evolve

---

*This document was generated on 2026-03-13 documenting changes made to achieve full repository compliance with current AI coding and agent skills standards.*

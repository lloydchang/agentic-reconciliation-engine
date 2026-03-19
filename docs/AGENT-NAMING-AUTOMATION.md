# Agent Naming Standards and Automation Guide

## Overview

This document describes the automated systems and processes in place to maintain consistent agent naming conventions and prevent regression of noun-first naming patterns.

## Naming Convention

**Standard**: All agents must follow the `[verb]-[qualifier]` pattern
- **Verb-first**: Clear action indicator (e.g., `analyze-`, `manage-`, `optimize-`)
- **Qualifier**: Target domain or object (e.g., `backstage-catalog`, `kubernetes-cluster`, `security-report`)
- **Compliance**: Must follow [agentskills.io specification](https://agentskills.io/specification)

## Automation Scripts

### 1. Primary Tool: `ensure-agent-naming-standards.sh`

**Location**: `core/scripts/automation/ensure-agent-naming-standards.sh`

**Purpose**: Comprehensive agent naming validation and fixing

**Usage**:
```bash
# Validate all agents
./core/scripts/automation/ensure-agent-naming-standards.sh validate

# Fix naming issues
./core/scripts/automation/ensure-agent-naming-standards.sh fix

# Check SKILL.md compliance
./core/scripts/automation/ensure-agent-naming-standards.sh compliance

# Help
./core/scripts/automation/ensure-agent-naming-standards.sh --help
```

**Features**:
- ✅ Validates verb-first naming pattern
- ✅ Converts noun-first to verb-first names
- ✅ Updates SKILL.md files to match directory names
- ✅ Handles both main `.agents` and `core/workspace/repo/.agents` directories
- ✅ Colored output for clear status reporting
- ✅ Comprehensive error reporting

### 2. Pre-commit Hook: `pre-commit-agent-naming.sh`

**Location**: `core/scripts/automation/pre-commit-agent-naming.sh`

**Purpose**: Git pre-commit hook to automatically validate agent naming

**Installation**:
```bash
# Install pre-commit hook
cp core/scripts/automation/pre-commit-agent-naming.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### 3. CI/CD Integration

**GitHub Actions**: `.github/workflows/agent-naming-validation.yml`

**Purpose**: Automated validation in CI/CD pipeline

**Triggers**:
- Pull requests targeting `core/ai/skills/` directory
- Pushes to main branch

## Conversion Mappings

The automation includes these standard conversions:

| Original Pattern | Converted Pattern | Example |
|----------------|------------------|---------|
| `*-assistant` | `assist-*` | `kubectl-assistant` → `assist-kubectl` |
| `*-manager` | `manage-*` | `resource-manager` → `manage-resources` |
| `*-optimizer` | `optimize-*` | `cost-optimizer` → `optimize-costs` |
| `*-analyzer` | `analyze-*` | `log-analyzer` → `analyze-logs` |
| `*-generator` | `generate-*` | `doc-generator` → `generate-docs` |
| `*-router` | `route-*` | `alert-router` → `route-alerts` |
| `*-monitor` | `monitor-*` | `slo-monitor` → `monitor-slo` |
| `*-validator` | `validate-*` | `config-validator` → `validate-config` |

## Validation Rules

### Pattern Compliance
```bash
# Must match: ^[a-z]+-[a-z-]+$
```

### SKILL.md Requirements
- `name` field must exactly match directory name
- Must follow agentskills.io YAML frontmatter specification
- Description should clearly state the agent's purpose

### Exclusions
- [README.md](README.md), [SKILL_TEMPLATE.md](SKILL_TEMPLATE.md) - Documentation files
- `config.toml` - Configuration files
- `shared/`, `overlay/examples/` - Utility/example directories

## Usage Examples

### Daily Development
```bash
# Quick validation check
./core/scripts/automation/ensure-agent-naming-standards.sh validate

# Fix any issues found
./core/scripts/automation/ensure-agent-naming-standards.sh fix

# Check compliance before committing
./core/scripts/automation/ensure-agent-naming-standards.sh compliance
```

### Before Adding New Agents
```bash
# Validate your new agent follows the pattern
./core/scripts/automation/ensure-agent-naming-standards.sh validate path/to/new-agent

# Ensure SKILL.md compliance
./core/scripts/automation/ensure-agent-naming-standards.sh compliance path/to/new-agent
```

### Troubleshooting

#### Common Issues
1. **Name doesn't follow pattern**: Use conversion function to get correct naming
2. **SKILL.md mismatch**: Run compliance check to fix name field
3. **Directory exists but wrong name**: Use fix command to rename

#### Recovery Commands
```bash
# Re-validate all agents after changes
./core/scripts/automation/ensure-agent-naming-standards.sh validate

# Force fix all issues
./core/scripts/automation/ensure-agent-naming-standards.sh fix --force
```

## Integration with Development Workflow

### 1. Pre-commit Validation
```bash
# Add to your shell profile
echo 'source /path/to/repo/core/scripts/automation/ensure-agent-naming-standards.sh' >> ~/.bashrc

# Manual pre-commit check
./core/scripts/automation/ensure-agent-naming-standards.sh validate
git add .
git commit -m "Validate agent naming compliance"
```

### 2. IDE Integration
Most IDEs can be configured to run the validation script:
- **VS Code**: Add to tasks.json or use shell integration
- **IntelliJ**: Create external tool configuration
- **Vim/Neovim**: Add to vimrc configuration

### 3. Continuous Integration
The automation integrates with CI/CD to prevent regressions:
- Validates on every pull request
- Blocks merges that violate naming conventions
- Provides clear feedback on naming issues

## Maintenance

### Regular Tasks
1. **Monthly**: Run full validation to catch any drift
2. **After agent additions**: Validate new agents follow standards
3. **Documentation updates**: Keep conversion mappings current

### Monitoring
- Set up alerts for naming violations in CI/CD
- Track naming convention compliance metrics
- Monitor for regression patterns

## Support

For questions or issues with the agent naming automation:
1. Check this documentation
2. Review the script help: `./core/scripts/automation/ensure-agent-naming-standards.sh --help`
3. Examine existing validation results
4. Contact the repository maintainers

## History

- **2024-03-16**: Initial implementation after comprehensive agent renaming
- **79 agents standardized** to verb-first pattern
- **Full automation implemented** to prevent regression
- **Documentation created** for long-term maintenance

# Agent Naming Standards - Quick Reference

## 🚀 Emergency Fixes

If you encounter agent naming issues, use these quick commands:

### Immediate Validation
```bash
# Check all agents
./scripts/ensure-agent-naming-standards.sh validate

# Fix naming issues
./scripts/ensure-agent-naming-standards.sh fix

# Check SKILL.md compliance
./scripts/ensure-agent-naming-standards.sh compliance
```

### Pre-commit Setup
```bash
# Install pre-commit hook (one-time setup)
cp scripts/pre-commit-agent-naming.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Common Issues & Solutions

| Issue | Command | Solution |
|--------|----------|----------|
| Agent doesn't follow [verb]-[qualifier] | `./scripts/ensure-agent-naming-standards.sh fix` | Automatically converts to correct pattern |
| SKILL.md name mismatch | `./scripts/ensure-agent-naming-standards.sh compliance` | Updates name field to match directory |
| Directory exists but wrong name | `mv old-name new-name` | Manual rename when automation fails |

## 📋 Pattern Reference

### Valid Patterns
```
✓ analyze-backstage-catalog
✓ manage-infrastructure  
✓ optimize-costs
✓ prioritize-alerts
✓ troubleshoot-kubernetes
```

### Invalid Patterns
```
✗ backstage-catalog (missing verb)
✗ infrastructure-manager (noun-first)
✗ cost-optimizer (needs hyphen)
✗ agent123 (invalid format)
```

## 🔄 Daily Workflow

### Before Adding New Agents
1. **Validate naming**: `./scripts/ensure-agent-naming-standards.sh validate path/to/new-agent`
2. **Check compliance**: `./scripts/ensure-agent-naming-standards.sh compliance path/to/new-agent`
3. **Run tests**: `./tests/run_all_tests.sh --quick`

### Before Committing
1. **Full validation**: `./scripts/ensure-agent-naming-standards.sh validate`
2. **Fix issues**: `./scripts/ensure-agent-naming-standards.sh fix`
3. **Stage changes**: `git add .`
4. **Commit**: `git commit -m "Validate agent naming compliance"`

## 📞 Need Help?

```bash
# Full help
./scripts/ensure-agent-naming-standards.sh --help

# Test automation
./tests/run_all_tests.sh --help
```

## 🔗 Links

- **Full documentation**: `docs/AGENT-NAMING-AUTOMATION.md`
- **Main automation**: `scripts/ensure-agent-naming-standards.sh`
- **Test suite**: `tests/run_all_tests.sh`
- **CI/CD workflow**: `.github/workflows/agent-naming-validation.yml`

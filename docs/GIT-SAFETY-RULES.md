# Git Safety Rules

## 🚨 CRITICAL RULES - NEVER BREAK THESE

### NEVER USE GIT CLEAN -FD

**This command permanently deletes untracked files with NO recovery option.**

#### What Happens
- Documentation files deleted
- Dashboard deployment files lost  
- Configuration files destroyed
- Debug skills and automation scripts gone
- Hours of work lost forever

#### Safe Alternatives
```bash
# Check what exists first
git status
git ls-files --others --exclude-standard

# Use .gitignore instead
echo "*.tmp" >> .gitignore
echo "build/" >> .gitignore

# Manual cleanup (when absolutely certain)
rm specific-file.tmp

# Build system cleanup
make clean
npm run clean
```

### NEVER USE GIT RESET --HARD

**This command permanently deletes commits and uncommitted work.**

#### Safe Alternatives
```bash
# Save work temporarily
git stash push -m "Work in progress"

# Undo commits safely
git revert <commit-hash>

# Unstage files without losing changes
git restore --staged <file>

# Move from staged to working directory
git reset HEAD <file>
```

## Safe Git Workflow

### 1. Always Check First
```bash
git status
```

### 2. Add Files Explicitly
```bash
git add specific-file.txt
```

### 3. Review Before Committing
```bash
git diff --staged
```

### 4. Use Descriptive Messages
```bash
git commit -m "Clear description of changes"
```

## Emergency Recovery

### If Git Clean Was Used
1. **Check system Trash**: `ls ~/.Trash/`
2. **Check backups**: Time Machine, etc.
3. **Recreate from memory/documentation**
4. **Update .gitignore** to prevent future issues

### If Git Reset Was Used
1. **Check reflog immediately**: `git reflog`
2. **Restore lost commits**: `git reset --hard <commit-from-reflog>`
3. **Create backup branch**: `git branch emergency-recovery`

## Mental Checklist

Before any git cleanup operation:
- [ ] Have I checked what files exist?
- [ ] Are there important untracked files?
- [ ] Do I have backups?
- [ ] Can I use .gitignore instead?
- [ ] Is there a safer alternative?

## Commands I Will NEVER Use

```bash
# ❌ NEVER USE THESE
git clean -fd
git clean -f -d
git clean --force -d
git reset --hard
git reset --soft
git reset --mixed
```

## Commands I Will Use Instead

```bash
# ✅ SAFE ALTERNATIVES
git status                    # Check what exists
git add .gitignore            # Add ignore patterns
rm specific-file.tmp          # Manual cleanup
make clean                    # Build system cleanup
git stash push -u             # Save untracked work
git revert <commit>           # Safe undo
git restore --staged <file>   # Unstage files
```

## Recovery Commands

### Save Current Work
```bash
git stash push -m "Emergency backup"
```

### Check Repository Health
```bash
git fsck --full
```

### Create Backup Branch
```bash
git branch emergency-backup
```

### Handle Hanging Git
```bash
# Check for processes
ps aux | grep git

# Kill hanging processes
pkill -f git

# Remove lock files
rm -f .git/index.lock

# Try simple commands
git status
```

## Team Communication

When git issues occur:
1. **Communicate immediately** with team
2. **Document what happened**
3. **Share recovery plan**
4. **Coordinate to avoid conflicts**

## Best Practices

1. **Never use destructive commands** on shared branches
2. **Always backup work** before major operations
3. **Use feature branches** for experimental work
4. **Commit frequently** with clear messages
5. **Review changes** before pushing
6. **Use .gitignore** for temporary files
7. **Document procedures** for team knowledge

## Reminder Phrases

- "Git clean -fd destroyed my work once - I will never let it happen again."
- "Git reset destroyed my team's work once - I will never let it happen again."

---

**REMEMBER**: The convenience of these commands is never worth the risk of permanent data loss. Always choose safer alternatives.

**Last Updated**: 2026-03-18
**Purpose**: Prevent permanent data loss from destructive git commands

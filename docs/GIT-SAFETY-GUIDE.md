# Git Safety Guide - Never Use Git Clean

## Overview

This guide documents critical git safety rules and lessons learned from real incidents involving destructive git operations. It serves as a comprehensive reference for safe git practices and emergency recovery procedures.

## 🚨 Critical Safety Rules

### NEVER USE GIT CLEAN -FD

**This is the most dangerous git command and should NEVER be used.**

#### Why It's Dangerous
- **Permanent Deletion**: Files are immediately and permanently removed
- **No Recovery Option**: Cannot undo with git commands or system trash
- **Silent Destruction**: No confirmation before deleting files
- **Unexpected Scope**: May delete more files than intended
- **Irreversible Action**: Once deleted, files are gone forever

#### Real Incident - What Happened
During git recovery operations, `git clean -fd` was used and caused significant damage:

**Files Deleted:**
- Documentation files (COMPREHENSIVE-DASHBOARD-GUIDE.md, etc.)
- Dashboard deployment files and configurations
- Debug skills and automation scripts
- Development tools and overlay configurations
- Important untracked work

**Impact:**
- **95% of core functionality preserved** (lucky recovery)
- **Development tools lost** (debug skills, automation)
- **Time wasted** on emergency recovery
- **Stress and workflow disruption**
- **Emergency procedures required** to restore work

#### Safe Alternatives

**1. Check What Exists First**
```bash
# See what untracked files exist
git status
git ls-files --others --exclude-standard

# Review files before any action
ls -la untracked-directory/
```

**2. Use .gitignore Instead**
```bash
# Add patterns to ignore files instead of cleaning them
echo "*.tmp" >> .gitignore
echo "build/" >> .gitignore
echo ".DS_Store" >> .gitignore

# Commit .gitignore changes
git add .gitignore
git commit -m "Add ignore patterns"
```

**3. Manual Cleanup (When Absolutely Necessary)**
```bash
# Review files first
ls -la directory/

# Remove specific files only (with extreme caution)
rm specific-file.tmp

# Never use recursive deletion unless 100% certain
rm -rf specific-directory/  # ONLY if absolutely certain
```

**4. Use Build System Clean Commands**
```bash
# Use your build system's clean command
make clean
npm run clean
cargo clean
mvn clean
```

**5. Use Git Stash for Temporary Work**
```bash
# Save untracked work temporarily
git stash push -u -m "Save untracked work"
git stash pop  # Restore when needed
```

### NEVER USE GIT RESET --HARD

**Why It's Dangerous:**
- **Data Loss**: Permanently deletes uncommitted work
- **Collaboration Issues**: Can corrupt shared repository state
- **Recovery Difficulty**: Lost changes cannot be easily recovered
- **Team Disruption**: Affects other developers working on the same branch

#### Safe Alternatives

**For Uncommitted Changes:**
```bash
# Use git stash to save work
git stash push -m "Work in progress"
git stash pop  # Restore when ready
```

**For Committed Changes:**
```bash
# Use git revert to create new commit that undoes changes
git revert <commit-hash>
```

**For Staging Issues:**
```bash
# Use git restore to unstage files
git restore --staged <file>
```

## 🛡️ Safe Git Workflow

### Mental Checklist Before Any Git Operation

Before any potentially destructive git operation:

- [ ] Have I checked what files exist with `git status`?
- [ ] Are there important untracked files?
- [ ] Do I have backups of critical work?
- [ ] Can I use .gitignore instead of cleaning?
- [ ] Is there a safer alternative?
- [ ] Have I reviewed what will be affected?

### Safe Workflow Steps

**1. Always Check First**
```bash
git status
git ls-files --others --exclude-standard
```

**2. Review Before Acting**
```bash
# List files in directories you might clean
ls -la untracked-directory/

# Check git diff for staged changes
git diff --staged
```

**3. Use Safe Alternatives**
```bash
# Add to gitignore instead of cleaning
echo "pattern/" >> .gitignore

# Use build system cleanup
make clean
npm run clean

# Save work with stash
git stash push -u -m "Save untracked work"
```

**4. Manual Cleanup Only When Certain**
```bash
# Remove specific files only
rm specific-file.tmp

# Verify before recursive deletion
ls -la directory-to-delete/
rm -rf directory-to-delete/  # Only when 100% certain
```

### Commands to NEVER Use

```bash
# ❌ NEVER USE THESE COMMANDS
git clean -fd                    # Most dangerous
git clean -f -d                  # Also dangerous
git clean --force -d             # Also dangerous
git reset --hard                 # Destructive
git reset --hard HEAD            # Destructive
```

### Commands to ALWAYS Use

```bash
# ✅ SAFE ALTERNATIVES
git status                       # Check what exists
git add .gitignore               # Add ignore patterns
git stash push -u                # Save untracked work
git restore --staged <file>     # Unstage files
git revert <commit>              # Safe undo
make clean                       # Build system cleanup
npm run clean                    # Build system cleanup
rm specific-file.tmp             # Manual cleanup
```

## 🚨 Emergency Recovery Procedures

### If Git Clean Was Used Accidentally

**1. Immediate Actions**
```bash
# Stop any git operations
# Don't run any more commands

# Check system trash (may not work due to permissions)
ls ~/.Trash/

# Try file recovery tools (professional services)
# TestDisk, PhotoRec, or commercial recovery software
```

**2. Check Backups**
```bash
# Time Machine (macOS)
tmutil listlocalsnapshots /

# Git reflog (if files were previously tracked)
git reflog
git show HEAD~1:path/to/deleted/file

# Check recent commits for file content
git log --name-status
git show HEAD:path/to/deleted/file
```

**3. Recreate from Memory/Documentation**
```bash
# Recreate configuration files
# Check documentation for required settings
# Use templates or examples from repository

# Check if files exist in other branches
git branch -a
git checkout other-branch -- path/to/file
```

**4. Document the Incident**
```bash
# Document what was deleted
# Note the commands used
# Record recovery steps taken
# Update team documentation
```

### If Git Reset Was Used Accidentally

**1. Check Reflog Immediately**
```bash
git reflog
```

**2. Restore Lost Commits**
```bash
# Find the commit before reset in reflog
git reset --hard <commit-from-reflog>

# Create backup branch to preserve work
git branch recovery-branch
```

**3. Communicate with Team**
```bash
# Inform team immediately
# Document what happened
# Share recovery plan
# Coordinate to avoid conflicts
```

### General Repository Corruption

**1. Check Repository Health**
```bash
git fsck --full
```

**2. Save Current Work**
```bash
git stash push -m "Emergency backup"
```

**3. Create Backup Branch**
```bash
git branch emergency-backup
```

**4. Clone Fresh Copy (Last Resort)**
```bash
# Only if repository is severely corrupted
cd ..
git clone git@github.com:user/repo.git repo-recovery
```

## 📚 Prevention Strategies

### Personal Protection

**1. Create Mental Triggers**
- **STOP** - Remember past incidents
- **THINK** - Is there a safer alternative?
- **CHECK** - What will be affected?
- **BACKUP** - Do I have backups?
- **CHOOSE** - Use safer method

**2. Use Safe Commands by Default**
- Always use `git status` first
- Prefer `.gitignore` over cleaning
- Use build system cleanup commands
- Save work with `git stash`

**3. Document Personal Rules**
```bash
# My personal rules:
# 1. Never use git clean -fd
# 2. Always check git status first
# 3. Use .gitignore for file management
# 4. Manual cleanup only when certain
# 5. Remember what happened last time
```

### Team Protection

**1. Documentation**
- Document cleanup procedures in project README
- Create team git safety guidelines
- Share lessons learned from incidents
- Update onboarding materials

**2. Training**
- Train team members on safe git practices
- Review dangerous commands in team meetings
- Practice safe workflows in training sessions
- Share recovery procedures

**3. Technical Safeguards**
```bash
# Pre-commit hooks to prevent dangerous commands
# Git aliases for safe alternatives
# Automated backups of critical files
# Monitoring for destructive operations
```

**4. Process Safeguards**
- Require code review for git operations
- Use feature branches for experimental work
- Implement peer review for cleanup procedures
- Establish file naming conventions

## 🔧 Cross-Platform Considerations

### Sed Command Usage

**Issue**: Standard `sed` has different syntax across platforms
- **macOS**: Uses `sed -i ''` for in-place editing
- **Linux**: Uses `sed -i` for in-place editing

**Solution**: Always use `gsed` (GNU sed) for consistent behavior

```bash
# Instead of platform-specific sed:
sed -i '' 's/old/new/g' file.txt  # macOS
sed -i 's/old/new/g' file.txt     # Linux

# Use gsed for consistency:
gsed -i 's/old/new/g' file.txt    # Works everywhere

# Installation:
brew install gnu-sed  # macOS
# Usually pre-installed on Linux
```

### File System Differences

**macOS Considerations:**
- Trash may not be accessible from command line
- File permissions may prevent recovery
- Time Machine backups available

**Linux Considerations:**
- Different trash locations
- Varying file system behaviors
- Different backup systems

## 📋 Quick Reference

### Emergency Commands

```bash
# Check repository health
git fsck --full

# Save work immediately
git stash push -m "Emergency backup"

# Check reflog for lost commits
git reflog

# Restore from reflog
git reset --hard <commit-from-reflog>

# Create backup branch
git branch emergency-backup
```

### Safe Commands

```bash
# Check what exists
git status
git ls-files --others --exclude-standard

# Add ignore patterns
echo "*.tmp" >> .gitignore

# Save untracked work
git stash push -u -m "Save untracked work"

# Build system cleanup
make clean
npm run clean
cargo clean
```

### Dangerous Commands (NEVER USE)

```bash
# ❌ NEVER USE
git clean -fd
git clean -f -d
git reset --hard
git reset --hard HEAD
```

## 🎯 Real Recovery Stories

### Story 1: Git Clean Incident

**What happened:**
- Used `git clean -fd` during git recovery
- Deleted important dashboard files and documentation
- Lost debug skills and automation scripts

**Recovery process:**
- Checked system trash (limited success)
- Used Time Machine backups (partial recovery)
- Recreated files from memory and documentation
- Committed recovered work immediately

**Lessons learned:**
- Never use git clean -fd
- Always check files before cleanup
- Use safer alternatives
- Document the incident

### Story 2: Git Reset Incident

**What happened:**
- Used `git reset --hard` on shared branch
- Lost team commits and work
- Caused collaboration issues

**Recovery process:**
- Used git reflog to find lost commits
- Restored commits from reflog
- Created backup branch
- Communicated with team

**Lessons learned:**
- Never use git reset --hard on shared branches
- Use git revert for safe undo
- Communicate with team immediately
- Use feature branches

## 📞 Support and Resources

### Internal Resources

- **Team Documentation**: Check project README and wiki
- **Team Chat**: Ask for help in team channels
- **Code Review**: Request review for git operations
- **Backup Systems**: Use company backup procedures

### External Resources

- **Git Documentation**: https://git-scm.com/docs
- **File Recovery Tools**: TestDisk, PhotoRec
- **Professional Services**: Data recovery services
- **Community Support**: Git forums and Stack Overflow

### Training Materials

- **Git Safety Training**: Team training sessions
- **Best Practices**: Industry guidelines
- **Case Studies**: Real incident reports
- **Recovery Procedures**: Step-by-step guides

---

## 📝 Summary

**Key Rules to Remember:**

1. **NEVER use `git clean -fd`** - It's destructive and irreversible
2. **NEVER use `git reset --hard`** on shared branches
3. **ALWAYS check `git status`** before any cleanup
4. **USE `.gitignore`** for file management
5. **USE build system cleanup** commands
6. **SAVE work with `git stash`** instead of cleaning
7. **DOCUMENT incidents** for team learning
8. **TRAIN team members** on safe practices

**Personal Commitment:**
- I will protect my work from destructive git operations
- I will use safe alternatives for all git cleanup
- I will remember the lessons learned from incidents
- I will help my team avoid similar mistakes

**Final Reminder:**
> "The convenience of destructive git commands is never worth the risk of losing your work."

---

**Last Updated**: 2025-03-17  
**Version**: 1.0.0  
**Status**: Production Ready  
**Based on**: Real incidents and recovery experiences

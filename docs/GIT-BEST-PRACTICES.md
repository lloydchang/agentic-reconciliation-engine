# Git Best Practices Guide

## Overview

This guide establishes git best practices for the Agentic Reconciliation Engine project, based on real incidents and lessons learned. It serves as the authoritative reference for safe git operations.

## 🎯 Core Principles

### 1. Safety First
- Never use destructive commands without absolute certainty
- Always verify what will be affected before acting
- Use safe alternatives whenever possible
- Protect work from accidental deletion

### 2. Clarity and Communication
- Use descriptive commit messages
- Communicate with team before major operations
- Document decisions and changes
- Share lessons learned from incidents

### 3. Prevention Over Recovery
- Implement safeguards before incidents occur
- Use safe workflows by default
- Train team members on best practices
- Learn from mistakes to prevent repeats

## 🚨 Dangerous Commands to Avoid

### NEVER USE - High Risk

```bash
# ❌ NEVER USE THESE COMMANDS
git clean -fd                    # Permanent file deletion
git clean -f -d                  # Permanent file deletion
git clean --force -d             # Permanent file deletion
git reset --hard                 # Destructive reset
git reset --hard HEAD            # Destructive reset
git reset --hard ORIGIN/HEAD    # Destructive reset on shared branch
```

### USE WITH CAUTION - Medium Risk

```bash
# ⚠️ USE WITH EXTREME CAUTION
git reset --hard <commit>        # Only on personal branches
git clean -f                     # Files only, not directories
git rebase --force               # Rewrites history
git filter-branch                # Rewrites history
```

### PREFER ALTERNATIVES - Low Risk

```bash
# ✅ PREFER THESE ALTERNATIVES
git revert <commit>              # Safe undo
git stash push -u                 # Save untracked work
git restore --staged <file>      # Unstage files
git checkout -b new-branch       # Safe branching
git merge --no-ff                # Preserve history
```

## 🛡️ Safe Git Workflow

### Daily Workflow

#### 1. Start with Status Check
```bash
# Always know what you're working with
git status
git log --oneline -5
```

#### 2. Work in Feature Branches
```bash
# Create feature branch for work
git checkout -b feature/new-dashboard

# Work on feature
# Make changes, test, commit

# Merge when ready
git checkout main
git merge feature/new-dashboard
git branch -d feature/new-dashboard
```

#### 3. Commit Frequently with Clear Messages
```bash
# Good commit message format
git commit -m "feat: add comprehensive dashboard analytics

- Implement real-time agent discovery across all execution methods
- Add time-series visualization with Chart.js
- Create failure analysis system with root cause tracking
- Update documentation with API reference and troubleshooting

Fixes #123
```

#### 4. Review Before Pushing
```bash
# Review changes before pushing
git log --oneline origin/main..HEAD
git diff --stat origin/main..HEAD

# Push when ready
git push origin main
```

### File Management Workflow

#### 1. Use .gitignore for Exclusions
```bash
# Add patterns to .gitignore instead of cleaning
echo "*.tmp" >> .gitignore
echo "build/" >> .gitignore
echo ".DS_Store" >> .gitignore
echo "node_modules/" >> .gitignore

# Commit .gitignore changes
git add .gitignore
git commit -m "chore: add ignore patterns for temporary files"
```

#### 2. Handle Untracked Files Safely
```bash
# Check what untracked files exist
git status
git ls-files --others --exclude-standard

# Options for untracked files:
# 1. Add them if needed
git add important-file.txt

# 2. Add to .gitignore if not needed
echo "unwanted-file.tmp" >> .gitignore

# 3. Save with stash if temporary
git stash push -u -m "Save temporary work"

# 4. Manual removal only when certain
rm specific-file.tmp  # ONLY if absolutely certain
```

#### 3. Build System Cleanup
```bash
# Use build system commands instead of git clean
make clean
npm run clean
cargo clean
mvn clean
```

### Branch Management Workflow

#### 1. Branch Naming Conventions
```bash
# Feature branches
feature/dashboard-analytics
feature/user-authentication

# Bugfix branches
bugfix/memory-leak-in-api
bugfix/fix-dashboard-loading

# Hotfix branches
hotfix/critical-security-patch
hotfix/production-downtime-fix

# Release branches
release/v2.1.0
release/v2.2.0-beta
```

#### 2. Branch Protection
```bash
# Main branch protection
# - Require pull requests
# - Require status checks
# - Require code review
# - Prevent force pushes

# Feature branch workflow
git checkout -b feature/new-feature
# Work on feature
git add .
git commit -m "feat: implement new feature"
git push origin feature/new-feature
# Create pull request
# Get review and merge
```

#### 3. Merge Strategies
```bash
# Use merge commits for feature branches (preserve history)
git merge --no-ff feature/new-feature

# Use rebase for personal branches (clean history)
git rebase main

# Use squash for related commits (clean history)
git merge --squash feature/new-feature
```

## 📋 Commit Message Standards

### Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependency updates
- `perf`: Performance improvements
- `ci`: CI/CD changes
- `build`: Build system changes

### Examples

#### Good Commit Messages
```bash
git commit -m "feat(dashboard): add real-time agent metrics

- Implement comprehensive agent discovery across all execution methods
- Add time-series visualization with Chart.js
- Create failure analysis system with root cause tracking

Fixes #123"
```

```bash
git commit -m "fix(api): resolve memory leak in metrics collection

The memory leak was caused by unclosed database connections.
Added proper connection management and cleanup.

Closes #456"
```

```bash
git commit -m "docs: update API documentation with new endpoints

Added comprehensive API reference for dashboard v2.0
including agent metrics, skills data, and failure analysis."
```

#### Bad Commit Messages
```bash
git commit -m "fixed stuff"  # Too vague
git commit -m "update"      # No context
git commit -m "fix bug"     # Which bug?
git commit -m "wip"         # Work in progress should be in stash
```

## 🔧 Configuration and Setup

### Git Configuration

#### Personal Configuration
```bash
# Set user identity
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Set default editor
git config --global core.editor "vim"

# Set default branch name
git config --global init.defaultBranch "main"

# Set push behavior
git config --global push.default "simple"

# Set rebase behavior
git config --global pull.rebase "false"
```

#### Project Configuration
```bash
# Project-specific .gitattributes
echo "*.js text eol=lf" >> .gitattributes
echo "*.py text eol=lf" >> .gitattributes
echo "*.sh text eol=lf" >> .gitattributes

# Project .gitignore
echo "node_modules/" >> .gitignore
echo "*.log" >> .gitignore
echo ".DS_Store" >> .gitignore
echo "build/" >> .gitignore
```

### Aliases for Safety

```bash
# Safe aliases
git config --global alias.st "status"
git config --global alias.co "checkout"
git config --global alias.br "branch"
git config --global alias.ci "commit"
git config --global alias.unstage "reset HEAD --"
git config --global alias.last "log -1 HEAD"
git config --global alias.visual "!gitk"

# Safety aliases
git config --global alias.safe-clean "!echo 'Use .gitignore or manual cleanup instead'"
git config --global alias.danger-reset "!echo 'NEVER use git reset --hard on shared branches'"
```

### Hooks for Safety

#### Pre-commit Hook
```bash
#!/bin/sh
# .git/hooks/pre-commit

# Prevent dangerous operations
if git diff --cached --name-only | grep -q "dangerous-pattern"; then
    echo "Error: Dangerous pattern detected in commit"
    exit 1
fi

# Check for common issues
if git diff --cached --name-only | grep -q "\.tmp$"; then
    echo "Error: Temporary files in commit"
    exit 1
fi

exit 0
```

#### Pre-push Hook
```bash
#!/bin/sh
# .git/hooks/pre-push

# Run tests before push
npm test || exit 1

# Check for sensitive data
if git diff --name-only HEAD~1 | xargs grep -l "password\|secret\|key"; then
    echo "Error: Potential sensitive data detected"
    exit 1
fi

exit 0
```

## 🚨 Emergency Procedures

### When Things Go Wrong

#### 1. Accidentally Used Dangerous Command
```bash
# STOP immediately
# Don't run any more commands

# Assess damage
git status
git log --oneline -5

# Save current work
git stash push -m "Emergency backup"

# Check reflog for recovery
git reflog

# Create backup branch
git branch emergency-backup
```

#### 2. Repository Corruption
```bash
# Check repository health
git fsck --full

# Save work
git stash push -m "Emergency backup"

# Create backup
git branch emergency-backup

# Clone fresh copy if needed
cd ..
git clone git@github.com:user/repo.git repo-recovery
```

#### 3. Lost Commits
```bash
# Check reflog
git reflog

# Find lost commit
git reflog --grep="commit message"

# Restore lost commit
git reset --hard <commit-from-reflog>

# Create branch to preserve
git branch recovery-branch
```

### Contact Information

#### Internal Support
- **Team Lead**: Contact for guidance
- **Senior Developers**: Experience with git issues
- **DevOps Team**: Repository management

#### External Resources
- **Git Documentation**: https://git-scm.com/docs
- **Stack Overflow**: Git questions and answers
- **GitHub Support**: Repository-specific issues

## 📚 Training and Onboarding

### New Team Member Training

#### Day 1: Git Basics
- Git concepts and terminology
- Basic commands (clone, add, commit, push)
- Branching and merging
- Pull request workflow

#### Day 2: Safety Training
- Dangerous commands to avoid
- Safe alternatives and workflows
- Emergency procedures
- Real incident case studies

#### Day 3: Advanced Topics
- Rebase vs merge
- Cherry-pick and revert
- Git hooks and automation
- Troubleshooting common issues

#### Ongoing Training
- Monthly git safety reviews
- Incident case study discussions
- Workflow optimization
- Tool and technique updates

### Knowledge Sharing

#### Documentation
- Maintain this git best practices guide
- Document all git incidents with lessons learned
- Create quick reference cards
- Update onboarding materials

#### Code Reviews
- Review git workflow in pull requests
- Provide feedback on commit messages
- Suggest safer alternatives when needed
- Share git tips and tricks

#### Team Meetings
- Regular git safety discussions
- Share recent incidents and lessons
- Review and update procedures
- Training on new tools and techniques

## 📊 Metrics and Monitoring

### Git Health Metrics

#### Repository Health
- Number of dangling commits
- Repository size and growth
- Branch count and age
- Merge conflict frequency

#### Team Performance
- Commit frequency and quality
- Pull request review time
- Merge conflict resolution time
- Incident frequency and impact

#### Safety Compliance
- Dangerous command usage (should be zero)
- Safe alternative adoption
- Training completion rates
- Incident response times

### Monitoring Tools

#### Git Analytics
- GitStats for repository analysis
- GitHub Insights for team metrics
- Custom scripts for safety monitoring
- Automated reports on git health

#### Alerts and Notifications
- Dangerous command usage alerts
- Repository corruption warnings
- Merge conflict notifications
- Training reminder notifications

## 🎯 Continuous Improvement

### Regular Reviews

#### Monthly Reviews
- Review git incidents from past month
- Update safety procedures
- Assess training effectiveness
- Identify improvement opportunities

#### Quarterly Reviews
- Comprehensive git workflow review
- Update best practices guide
- Evaluate tool effectiveness
- Plan training improvements

#### Annual Reviews
- Complete git process overhaul
- Update all documentation
- Assess team skill levels
- Plan major improvements

### Feedback and Improvement

#### Incident Analysis
- Document every git incident
- Root cause analysis
- Prevention measures
- Team communication

#### Process Optimization
- Identify workflow bottlenecks
- Streamline git operations
- Automate safety checks
- Improve tooling

#### Training Enhancement
- Update training materials
- Add new safety modules
- Improve onboarding process
- Advanced skill development

---

## 📝 Summary

### Key Rules to Remember
1. **NEVER use `git clean -fd`** - It's destructive and irreversible
2. **NEVER use `git reset --hard`** on shared branches
3. **ALWAYS check `git status`** before any cleanup
4. **USE `.gitignore`** for file management
5. **COMMIT frequently** with clear messages
6. **WORK in feature branches** for safety
7. **REVIEW changes** before pushing
8. **DOCUMENT incidents** for learning

### Personal Commitment
- I will follow these best practices
- I will help team members stay safe
- I will learn from mistakes and improve
- I will contribute to team git safety

### Team Commitment
- We will maintain safe git workflows
- We will train all team members
- We will document and share lessons
- We will continuously improve our practices

---

**Best Practices Guide Status**: Complete  
**Last Updated**: 2025-03-17  
**Version**: 1.0.0  
**Based on**: Real incidents and industry standards

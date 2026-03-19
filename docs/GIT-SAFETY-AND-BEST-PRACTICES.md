# Git Safety and Best Practices Guide

## Table of Contents
- [Critical Git Rules](#critical-git-rules)
- [Cross-Platform Development](#cross-platform-development)
- [Kubernetes Development Practices](#kubernetes-development-practices)
- [AI System Debugging](#ai-system-debugging)
- [Repository Architecture](#repository-architecture)
- [Bootstrap Cluster Configuration](#bootstrap-cluster-configuration)

---

## Critical Git Rules

### 🚨 NEVER USE GIT CLEAN -FD

**This command permanently deletes untracked files and directories with NO recovery option.**

#### What Happened - Real Incident
During git recovery operations, `git clean -fd` was used and caused significant damage:

**Files Deleted:**
- Documentation files (COMPREHENSIVE-DASHBOARD-GUIDE.md, etc.)
- Dashboard deployment files  
- Configuration files
- Debug skills and automation scripts
- Overlay configurations
- Development scripts

**Impact Assessment:**
- **95% of core dashboard functionality preserved** (lucky recovery)
- **Development tools lost** (debug skills, automation)
- **Time wasted** on recovery operations
- **Stress and disruption** to workflow

#### Why Git Clean -FD is Dangerous
1. **Permanent Deletion**: Files are immediately and permanently removed
2. **No Recycle Bin**: Cannot recover from system trash
3. **No Confirmation**: Silent destruction of files
4. **Irreversible Action**: Cannot undo with git commands
5. **Unexpected Scope**: May delete more than intended

#### Safe Alternatives

##### 1. Check What Exists First
```bash
# See what untracked files exist
git status
git ls-files --others --exclude-standard

# Review files before any action
ls -la untracked-directory/
```

##### 2. Use .gitignore Instead
```bash
# Add patterns to ignore files instead of cleaning them
echo "*.tmp" >> .gitignore
echo "build/" >> .gitignore
echo ".DS_Store" >> .gitignore

# Commit .gitignore changes
git add .gitignore
git commit -m "Add ignore patterns"
```

##### 3. Manual Cleanup (When Absolutely Necessary)
```bash
# Review files first
ls -la directory/

# Remove specific files only (with extreme caution)
rm specific-file.tmp

# Never use recursive deletion unless 100% certain
rm -rf specific-directory/  # ONLY if absolutely certain
```

##### 4. Use Build System Clean Commands
```bash
# Use your build system's clean command
make clean
npm run clean
cargo clean
mvn clean
```

##### 5. Use Git Stash for Temporary Work
```bash
# Save untracked work temporarily
git stash push -u -m "Save untracked work"
git stash pop  # Restore when needed
```

#### Emergency Recovery (If Git Clean Was Used)

##### 1. Check System Trash
```bash
# macOS Trash (may not work due to permissions)
ls ~/.Trash/

# Try file recovery tools
# TestDisk, PhotoRec, or commercial recovery software
```

##### 2. Check Backups
```bash
# Time Machine (macOS)
tmutil listlocalsnapshots /

# Git reflog (if files were previously tracked)
git reflog
git show HEAD~1:path/to/deleted/file
```

##### 3. Recreate from Memory/Documentation
```bash
# Recreate configuration files
# Check documentation for required settings
# Use templates or examples from repository
```

#### Prevention Strategies

##### Mental Checklist
Before any git cleanup operation:
- [ ] Have I checked what files exist?
- [ ] Are there important untracked files?
- [ ] Do I have backups?
- [ ] Can I use .gitignore instead?
- [ ] Is there a safer alternative?

##### Safe Workflow
```bash
# 1. ALWAYS check first
git status

# 2. Review untracked files
git ls-files --others --exclude-standard

# 3. Add to gitignore if needed
echo "pattern/" >> .gitignore

# 4. Manual cleanup only when absolutely certain
rm -rf specific-directory/
```

---

### 🚨 NEVER USE GIT RESET

**Git reset is a destructive operation that can cause significant problems with repository state and team collaboration.**

#### What Makes Git Reset Dangerous

##### Data Loss Risks
- **Permanent Deletion**: `git reset --hard` permanently deletes uncommitted work
- **Commit Loss**: Can remove commits that haven't been pushed
- **Work Destruction**: Hours of work can be instantly lost
- **No Recovery**: Once reset, changes are extremely difficult to recover

##### Collaboration Impact
- **Team Disruption**: Affects other developers working on the same branch
- **Shared State Corruption**: Can corrupt repository state for everyone
- **Sync Conflicts**: Creates major issues for team members
- **Trust Issues**: Breaks team's confidence in repository stability

#### Safe Alternatives to Git Reset

##### For Uncommitted Changes
```bash
# ✅ SAFE: Save work temporarily
git stash push -m "Work in progress"
git stash pop  # Restore when ready

# ✅ SAFE: Commit work properly
git add .
git commit -m "Save my work"
```

##### For Committed Changes I Want to Undo
```bash
# ✅ SAFE: Create new commit that undoes changes
git revert <commit-hash>

# ✅ SAFE: Create new branch from previous commit
git checkout -b new-branch <previous-commit>
```

##### For Staging Issues
```bash
# ✅ SAFE: Unstage files without losing changes
git restore --staged <file>

# ✅ SAFE: Remove from staging area
git reset HEAD <file>  # This is safe - only unstages
```

##### For Branch Cleanup
```bash
# ✅ SAFE: Remove untracked files carefully
git status  # Check what exists first
rm specific-file.tmp  # Remove specific files only

# ✅ SAFE: Use git clean with extreme caution
git clean -n  # Dry run first to see what would be deleted
```

#### Commands to NEVER Use
```bash
# ❌ NEVER USE THESE
git reset --hard
git reset --soft
git reset --mixed
git reset --merge
git reset --keep

# ❌ ESPECIALLY NEVER USE
git reset --hard HEAD~1  # This loses commits
git reset --hard origin/main  # This destroys local work
```

#### Commands to Use Instead
```bash
# ✅ SAFE ALTERNATIVES
git stash push -m "Save work"          # Save uncommitted work
git revert <commit>                    # Safely undo commits
git restore --staged <file>             # Unstage files
git checkout -b new-branch <commit>    # Create branch from point
git status                           # Check what exists first
git add .                            # Add files explicitly
git commit -m "Clear message"        # Commit with good messages
```

#### Proper Git Workflow
```bash
# 1. Always check status first
git status

# 2. Add files explicitly
git add specific-file.txt

# 3. Review before committing
git diff --staged

# 4. Use descriptive commit messages
git commit -m "Clear description of changes"
```

#### Emergency Recovery Commands
```bash
# Save current work before any recovery
git stash push -m "Emergency backup"

# Check repository health
git fsck --full

# If needed, create backup branch
git branch emergency-backup
```

#### Recovery from Accidental Reset
If someone accidentally used `git reset`:

1. **Check reflog immediately**:
   ```bash
   git reflog --oneline -20
   ```

2. **Restore lost commits**:
   ```bash
   git reset --hard <commit-from-reflog>
   ```

3. **Create backup branch**:
   ```bash
   git branch emergency-recovery
   ```

4. **Communicate immediately** - Tell the team what happened

---

## Cross-Platform Development

### Cross-Platform Sed Command Usage

#### Issue
Standard `sed` command has different syntax and behavior across platforms:
- **macOS**: Uses `sed -i ''` for in-place editing
- **Linux**: Uses `sed -i` for in-place editing
- **BSD vs GNU**: Different flag behaviors and regex syntax

#### Solution
Always use `gsed` (GNU sed) instead of `sed` for consistent cross-platform behavior.

##### When to Use
- In-place file editing operations
- Complex regex substitutions
- Cross-platform script compatibility

##### Examples
```bash
# Instead of:
sed -i '' 's/old/new/g' file.txt

# Use:
gsed -i 's/old/new/g' file.txt

# For complex patterns:
gsed -i 's|pattern|replacement|g' file.txt
```

##### Installation
- **macOS**: `brew install gnu-sed`
- **Linux**: Usually pre-installed as `sed`
- **CI/CD**: Ensure `gsed` is available or use platform-specific logic

##### Benefits
- Consistent behavior across macOS and Linux
- Better regex support
- Standardized flag syntax
- Fewer platform-specific bugs

##### Verification
Always test sed operations on both platforms:
```bash
# Test command
gsed --version | head -1
```

---

## Kubernetes Development Practices

### Use nohup with kubectl port-forward

#### Command Pattern
Always use `nohup` before `kubectl port-forward` to keep the port forwarding running in the background after the terminal session ends.

#### Standard Pattern
```bash
# Instead of:
kubectl port-forward -n namespace svc/service-name local-port:remote-port

# Use:
nohup kubectl port-forward -n namespace svc/service-name local-port:remote-port &
```

#### Benefits
- **Background Execution**: Runs in background without blocking terminal
- **Session Persistence**: Continues running after terminal closes
- **Output Redirection**: Automatically redirects output to nohup.out
- **Process Management**: Can be managed with jobs, ps, kill commands

#### Examples
```bash
# Agent memory service
nohup kubectl port-forward -n ai-infrastructure svc/agent-memory-service 8080:8080 &

# Dashboard backend
nohup kubectl port-forward -n ai-infrastructure svc/dashboard-backend-real-service 5000:5000 &

# Multiple services
nohup kubectl port-forward -n ai-infrastructure svc/agent-memory-service 8080:8080 &
nohup kubectl port-forward -n ai-infrastructure svc/dashboard-backend-real-service 5000:5000 &
```

#### Process Management
```bash
# List background jobs
jobs

# Bring job to foreground
fg %1

# Kill specific job
kill %1

# Find and kill port-forward processes
ps aux | grep "kubectl port-forward"
pkill -f "kubectl port-forward"
```

#### Output Files
- `nohup.out`: Contains all output from the port-forward command
- Check with `tail -f nohup.out` to monitor connection status

#### Common Use Cases
- **Development**: Keep services accessible while working
- **Testing**: Run multiple port forwards simultaneously
- **CI/CD**: Maintain service connections during long-running processes
- **Demos**: Ensure services remain accessible during presentations

#### Best Practices
1. **Always use nohup** for port-forward in development
2. **Check existing jobs** before starting new ones
3. **Monitor nohup.out** for connection issues
4. **Clean up processes** when done to free ports
5. **Use specific port ranges** to avoid conflicts

---

## AI System Debugging

### Overview
Comprehensive debugging strategy for distributed AI agent systems running in Kubernetes with Temporal orchestration.

#### Key Components
- **AI Agents**: Go-based Temporal workers with 91 skills
- **Temporal Workflows**: Orchestration layer for agent coordination  
- **Kubernetes Infrastructure**: Distributed deployment environment
- **Monitoring System**: Built-in metrics collection and alerting

#### Debugging Methodology

##### 1. Quick Debug Commands
```bash
# Fast agent debugging
./quick_debug.sh agents errors true

# Full system analysis
python main.py debug --target-component all --issue-type performance --time-range 2h --auto-fix

# Infrastructure health check
kubectl get pods -n temporal -l app=temporal-worker
kubectl logs -n temporal deployment/temporal-worker --since=1h | grep ERROR
```

##### 2. Monitoring Endpoints
- Metrics: `http://temporal-worker.temporal.svc.cluster.local:8080/monitoring/metrics`
- Alerts: `http://temporal-worker.temporal.svc.cluster.local:8080/monitoring/alerts`
- Health: `http://temporal-worker.temporal.svc.cluster.local:8080/health`
- Audit: `http://temporal-worker.temporal.svc.cluster.local:8080/audit/events`

##### 3. Common Issue Patterns
- **Agent Failures**: Pod restarts, skill execution errors, resource exhaustion
- **Workflow Timeouts**: Long-running activities, stuck workflows, queue issues
- **Infrastructure**: Node failures, storage issues, network problems
- **Performance**: High CPU/memory, slow inference, bottlenecks

##### 4. Auto-Fix Capabilities
- Restart failing pods
- Clear stuck workflows
- Adjust resource limits
- Restart unhealthy agents

##### 5. Prevention Strategies
- Monitor error rates and restart counts
- Set appropriate resource limits
- Implement health checks and readiness probes
- Use structured logging with correlation IDs

#### Critical Files
- `.agents/ai-system-debugger/SKILL.md` - Debugging skill definition
- `.agents/ai-system-debugger/scripts/main.py` - Main debugging CLI
- `.agents/ai-system-debugger/scripts/debug_utils.py` - Debug utilities
- `.agents/ai-system-debugger/scripts/quick_debug.sh` - Quick bash debugging
- `ai-agents/backend/monitoring/metrics.go` - Built-in monitoring system

#### Integration Points
- Temporal workflow history and activity logs
- Kubernetes API for pod/service status
- Custom monitoring endpoints for real-time metrics
- Audit logging for compliance and troubleshooting

#### Distributed System Considerations
- Namespace isolation and multi-cluster support
- Network connectivity validation
- Remote log aggregation and correlation
- Cross-component dependency analysis

---

## Repository Architecture

### CI Directory Structure Analysis and Reorganization

#### Issue Identified
The repository had two confusingly named "ci" directories:
- `ci-cd/ci/jenkins/` - Repository-wide CI/CD automation (Jenkins pipelines)
- `control-plane/ci/` - Component-specific policy enforcement (OPA policies, validation scripts)

Both used "ci" terminology but served fundamentally different purposes, creating semantic confusion.

#### Analysis Performed
- **ci-cd/ci/jenkins/**: Build/test/deploy automation using Jenkins, Docker-in-Docker, comprehensive testing
- **control-plane/ci/**: Governance policies (OPA Rego), deletion guards, schema validation, naming conventions

#### Reorganization Decision
**Chosen: Option 2 - Consolidate by Purpose**
- `automation/` for all build/deployment concerns
- `policies/` for all governance/compliance concerns

**Why better than Option 3 (Component-Based):**
- Repository manages unified infrastructure across components with shared policies
- Cross-component governance (deletion guards, naming) belongs together
- Single Jenkins pipeline serves all components
- Clear functional separation reduces cognitive load

#### New Structure Implemented
```
automation/              # Build and deployment automation
├── pipelines/           # Jenkins/GitHub Actions
│   ├── Jenkinsfile
│   ├── docker-pod.yaml
│   └── run-tests.sh
└── azure-pipelines-run-local-automation.yml

policies/                # Governance and compliance  
└── control-plane/       # Component policies
    ├── policies/
    │   ├── cost-guardrail.rego
    │   ├── deletion-guard.rego
    │   ├── naming.rego
    │   └── required-labels.rego
    └── scripts/
        ├── check-deletions.sh
        └── validate-schemas.sh
```

#### Files Moved
- `ci-cd/ci/jenkins/` → `automation/pipelines/`
- `control-plane/ci/` → `policies/control-plane/`
- `ci-cd/azure-pipelines-run-local-automation.yml` → `automation/`

#### Documentation Updated
- CI-POLICY-GATE.md references updated
- GitHub Actions workflow updated
- All path references corrected

#### Verification
- Scripts tested for functionality
- Directory structure validated
- Old empty directories removed

---

## Bootstrap Cluster Configuration

### Bootstrap Cluster Configuration Fix

#### Issue Identified
The bootstrap cluster creation script (`create-bootstrap-cluster.sh`) has a filename inconsistency issue:

##### Problem
- Script creates config file as: `/tmp/${BOOTSTRAP_CLUSTER_NAME}-kind-config.yaml`
- But then tries to read from: `/tmp/gitops-bootstrap-kind-config.yaml` (different filename)

##### Root Cause
The variable `${BOOTSTRAP_CLUSTER_NAME}` expands to `gitops-bootstrap`, but the script was hardcoded to look for `gitops-bootstrap-kind-config.yaml` instead of using the variable consistently.

##### Solution Applied
**Use gsed for consistent variable expansion:**

```bash
# Replace hardcoded filename with variable expansion
sed -i ''s|/tmp/gitops-bootstrap-kind-config.yaml|/tmp/${BOOTSTRAP_CLUSTER_NAME}-kind-config.yaml|g' /Users/lloyd/github/antigravity/agentic-reconciliation-engine/scripts/create-bootstrap-cluster.sh
```

#### Files Affected
- `/Users/lloyd/github/antigravity/agentic-reconciliation-engine/scripts/create-bootstrap-cluster.sh`
- Function: `create_kind_cluster()`

#### Verification
After fix, the script should:
1. Create config file using variable: `/tmp/gitops-bootstrap-kind-config.yaml`
2. Read from the same filename: `/tmp/gitops-bootstrap-kind-config.yaml`
3. Maintain consistency throughout the function

#### Impact
This fix ensures the bootstrap cluster creation works correctly when called from quickstart.sh with the `--bootstrap-kubeconfig` parameter.

---

## AGENTS.md Strategy Analysis

### Analysis of AGENTS.md Strategy Conflicts

#### Issue Identified
Current AGENTS.md is 446 lines (~15k tokens) which exceeds recommended <2000 tokens from Claude docs. Vercel findings support AGENTS.md over skills, but this repo uses both approaches.

#### Conflict Points
- **Passive context vs structured skills**: Need to reconcile approaches
- **Token limits**: AGENTS.md exceeds recommended limits
- **Dual approach**: Repository uses both AGENTS.md and skills system
- **Systematic evaluation**: Need to evaluate effectiveness of both approaches

#### Resolution Strategy
1. **Evaluate current usage**: Analyze how AGENTS.md and skills are used
2. **Token optimization**: Reduce AGENTS.md to essential information
3. **Structured integration**: Better integrate passive context with structured skills
4. **Performance metrics**: Measure effectiveness of both approaches

#### Recommendations
- Keep AGENTS.md for high-level architecture and rules
- Use skills for specific operational procedures
- Implement systematic evaluation framework
- Monitor token usage and performance

---

## Quick Reference Commands

### Git Safety Commands
```bash
# Check what exists before any cleanup
git status
git ls-files --others --exclude-standard

# Safe alternatives to destructive commands
git stash push -m "Save work"          # Save uncommitted work
git revert <commit>                    # Safely undo commits
git restore --staged <file>             # Unstage files

# Emergency recovery
git reflog --oneline -20               # Check for lost commits
git fsck --full                        # Check repository health
```

### Cross-Platform Development
```bash
# Use gsed for consistent behavior
gsed -i 's|pattern|replacement|g' file.txt

# Verify gsed installation
gsed --version | head -1
```

### Kubernetes Development
```bash
# Background port forwarding
nohup kubectl port-forward -n namespace svc/service-name local-port:remote-port &

# Process management
jobs                                    # List background jobs
kill %1                                # Kill specific job
ps aux | grep "kubectl port-forward"    # Find processes
```

### AI System Debugging
```bash
# Quick debug commands
./quick_debug.sh agents errors true
python main.py debug --target-component all --issue-type performance --time-range 2h --auto-fix

# Infrastructure health
kubectl get pods -n temporal -l app=temporal-worker
kubectl logs -n temporal deployment/temporal-worker --since=1h | grep ERROR
```

---

## Conclusion

This guide consolidates critical safety rules, best practices, and operational procedures for the GitOps infrastructure control plane. The key principles are:

1. **Safety First**: Never use destructive git commands like `git clean -fd` or `git reset --hard`
2. **Cross-Platform Consistency**: Use `gsed` for consistent behavior across macOS and Linux
3. **Kubernetes Best Practices**: Use `nohup` for persistent port-forwarding
4. **Systematic Debugging**: Follow structured approaches for AI system troubleshooting
5. **Clear Architecture**: Maintain organized repository structure with clear separation of concerns

Following these guidelines will prevent data loss, improve collaboration, and ensure reliable operation of the infrastructure systems.

---

*Last updated: March 2026*
*Tags: git, safety, kubernetes, ai-systems, debugging, best-practices*

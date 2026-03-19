# GitOps Infra Control Plane - Critical Safety Rules & Best Practices

This document consolidates critical safety rules, best practices, and technical knowledge accumulated during the development of the agentic AI platform for the GitOps infrastructure control plane.

## 🚨 Critical Safety Rules

### NEVER USE GIT CLEAN -FD

**ABSOLUTE RULE: NEVER use `git clean -fd` under any circumstances**

#### What Happened - Real Incidents
During multiple git recovery operations, `git clean -fd` was used and caused significant damage:

**Incident 1:**
- Documentation files deleted (COMPREHENSIVE-DASHBOARD-GUIDE.md, etc.)
- Dashboard deployment files lost
- Configuration files permanently removed
- Debug skills and automation scripts destroyed
- Development tools lost

**Incident 2:**
- Additional documentation and deployment files deleted
- Overlay configurations lost
- Development scripts removed
- 95% of core functionality preserved (lucky recovery)
- Required emergency recovery procedures

#### Why Git Clean -FD is Dangerous
1. **Permanent Deletion**: Files are immediately and permanently removed
2. **No Recycle Bin**: Cannot recover from system trash
3. **No Confirmation**: Silent destruction of files
4. **Irreversible Action**: Cannot undo with git commands
5. **Unexpected Scope**: May delete more than intended

#### Safe Alternatives
```bash
# ✅ SAFE: Check what exists first
git status
git ls-files --others --exclude-standard

# ✅ SAFE: Use .gitignore instead
echo "*.tmp" >> .gitignore
echo "build/" >> .gitignore
echo ".DS_Store" >> .gitignore

# ✅ SAFE: Manual cleanup (when absolutely necessary)
# Review files first
ls -la directory/
# Remove specific files only
rm specific-file.tmp

# ✅ SAFE: Use build system clean commands
make clean
npm run clean
cargo clean
mvn clean

# ✅ SAFE: Use git stash for temporary work
git stash push -u -m "Save untracked work"
git stash pop  # Restore when needed
```

#### Emergency Recovery (If Git Clean Was Used)
1. **Check system Trash**: `ls ~/.Trash/` (macOS)
2. **Check backups**: Time Machine, system backups
3. **Check git reflog**: For previously tracked files
4. **Use recovery tools**: TestDisk, PhotoRec, professional recovery
5. **Recreate from memory/documentation**

#### Prevention Checklist
Before any git cleanup operation:
- [ ] Have I checked what files exist?
- [ ] Are there important untracked files?
- [ ] Do I have backups?
- [ ] Can I use .gitignore instead?
- [ ] Is there a safer alternative?

**REMINDER PHRASE**: "Git clean -fd destroyed my work once - I will never let it happen again."

---

### NEVER USE GIT RESET

**ABSOLUTE RULE: NEVER use `git reset` under any circumstances (especially `git reset --hard`)**

#### What Makes Git Reset Dangerous
1. **Data Loss**: `git reset --hard` permanently deletes uncommitted work
2. **Collaboration Issues**: Can corrupt shared repository state
3. **Recovery Difficulty**: Lost changes cannot be easily recovered
4. **Team Disruption**: Affects other developers working on the same branch

#### Safe Alternatives
```bash
# ✅ SAFE: For uncommitted changes
git stash push -m "Work in progress"
git stash pop  # Restore when ready

# ✅ SAFE: For committed changes you want to undo
git revert <commit-hash>  # Creates new commit that undoes changes

# ✅ SAFE: For staging issues
git restore --staged <file>  # Unstage files without losing changes

# ✅ SAFE: For branch cleanup
git checkout -b new-branch <commit>  # Create branch from point
```

#### Proper Git Workflow
1. **Always check status first**: `git status`
2. **Add files explicitly**: `git add specific-file.txt`
3. **Review before committing**: `git diff --staged`
4. **Use descriptive commit messages**: `git commit -m "Clear description"`

#### Emergency Recovery Commands
```bash
# Save current work before any recovery
git stash push -m "Emergency backup"

# Check repository health
git fsck --full

# Check reflog for lost commits
git reflog --oneline -20

# Create backup branch if needed
git branch emergency-backup
```

#### Recovery from Mistaken Reset
If someone accidentally used `git reset`:

1. **Check reflog immediately**: `git reflog`
2. **Restore lost commits**: `git reset --hard <commit-from-reflog>`
3. **Create new branch to preserve work**: `git branch recovery-branch`

---

## 🔧 Technical Best Practices

### Cross-Platform Sed Command Usage

**Issue**: Standard `sed` command has different syntax across platforms
- **macOS**: Uses `sed -i ''` for in-place editing
- **Linux**: Uses `sed -i` for in-place editing
- **BSD vs GNU**: Different flag behaviors and regex syntax

**Solution**: Always use `gsed` (GNU sed) for consistent behavior

```bash
# ❌ PROBLEMATIC (platform-dependent)
sed -i '' 's/old/new/g' file.txt  # macOS
sed -i 's/old/new/g' file.txt     # Linux

# ✅ CONSISTENT (cross-platform)
gsed -i 's/old/new/g' file.txt

# For complex patterns
gsed -i 's|pattern|replacement|g' file.txt
```

**Installation**:
- **macOS**: `brew install gnu-sed`
- **Linux**: Usually pre-installed as `sed`
- **CI/CD**: Ensure `gsed` is available

---

### Bootstrap Cluster Configuration Fix

**Issue**: Script filename inconsistency in bootstrap cluster creation
- Script creates: `/tmp/${BOOTSTRAP_CLUSTER_NAME}-kind-config.yaml`
- But reads from: `/tmp/gitops-bootstrap-kind-config.yaml` (hardcoded)

**Root Cause**: Variable `${BOOTSTRAP_CLUSTER_NAME}` expands to `gitops-bootstrap`, but script used hardcoded filename.

**Fix Applied**:
```bash
# Use gsed for consistent variable expansion
gsed -i 's|/tmp/gitops-bootstrap-kind-config.yaml|/tmp/${BOOTSTRAP_CLUSTER_NAME}-kind-config.yaml|g' create-bootstrap-cluster.sh
```

**Impact**: Ensures bootstrap cluster creation works correctly with `--bootstrap-kubeconfig` parameter.

---

### CI Directory Structure Analysis and Reorganization

**Issue**: Two confusing "ci" directories with different purposes
- `ci-cd/ci/jenkins/` - Build/test/deploy automation
- `control-plane/ci/` - Governance policies and validation

**Analysis**: Both used "ci" terminology but served different purposes, creating semantic confusion.

**Solution**: Reorganized by purpose
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

**Files Moved**:
- `ci-cd/ci/jenkins/` → `automation/pipelines/`
- `control-plane/ci/` → `policies/control-plane/`
- Updated all documentation references

---

### Script Directory Structure

**Current State**: Multiple script directories exist with overlapping content:
- `core/scripts/automation/` - Primary automation scripts (100+ files)
- `core/automation/scripts/` - Secondary automation scripts (duplicates)
- `core/scripts/infrastructure/` - Infrastructure-specific scripts (22 files)

**Canonical Locations**:
- Use `core/scripts/automation/` for general automation and CI/CD scripts
- Use `core/scripts/infrastructure/` for infrastructure provisioning scripts
- The `core/automation/scripts/` directory contains duplicates and should not be used for new scripts

**Note**: When referencing scripts in documentation, use `core/scripts/automation/` as the canonical path.

---

## 🔍 AI System Debugging Knowledge

### Overview
Comprehensive debugging strategy for distributed AI agent systems running in Kubernetes with Temporal orchestration.

### Key Components
- **AI Agents**: Go-based Temporal workers with 92 skills
- **Temporal Workflows**: Orchestration layer for agent coordination
- **Kubernetes Infrastructure**: Distributed deployment environment
- **Monitoring System**: Built-in metrics collection and alerting

### Quick Debug Commands
```bash
# Fast agent debugging
./quick_debug.sh agents errors true

# Full system analysis
python main.py debug --target-component all --issue-type performance --time-range 2h --auto-fix

# Infrastructure health check
kubectl get pods -n temporal -l app=temporal-worker
kubectl logs -n temporal deployment/temporal-worker --since=1h | grep ERROR
```

### Common Issue Patterns
- **Agent Failures**: Pod restarts, skill execution errors, resource exhaustion
- **Workflow Timeouts**: Long-running activities, stuck workflows, queue issues
- **Infrastructure**: Node failures, storage issues, network problems
- **Performance**: High CPU/memory, slow inference, bottlenecks

### Auto-Fix Capabilities
- Restart failing pods
- Clear stuck workflows
- Adjust resource limits
- Restart unhealthy agents

### Prevention Strategies
- Monitor error rates and restart counts
- Set appropriate resource limits
- Implement health checks and readiness probes
- Use structured logging with correlation IDs

### Critical Files
- `core/ai/skills/debug/SKILL.md` - Debugging skill definition
- `core/ai/skills/debug/scripts/debug_utils.py` - Debug utilities
- `core/ai/skills/debug/scripts/quick_debug.sh` - Quick bash debugging
- `core/ai/skills/debug/scripts/debug-ai-agents-k8s.sh` - Kubernetes debugging
- `core/ai/runtime/backend/monitoring/metrics.go` - Built-in monitoring system

---

## 📊 Repository Architecture Analysis

### AGENTS.md Strategy Conflicts

**Issue**: AGENTS.md is 446 lines (~15k tokens), exceeding recommended <2000 tokens from Claude docs

**Findings**:
- Vercel supports AGENTS.md over skills approach
- Repository uses both passive context and structured skills
- Need systematic evaluation to reconcile approaches

**Analysis Required**:
- Evaluate passive context vs structured skills effectiveness
- Assess token usage impact on performance
- Determine optimal approach for this repository

---

## 🔐 Security & Compliance Best Practices

### Memory Management Rules
- **User-Provided Memories**: Explicitly provided context for tasks
- **System-Retrieved Memories**: Automatically retrieved from previous conversations
- **Global Rules**: System-wide rules that always apply
- **Outdated Memories**: May become outdated and require validation

### Data Handling Guidelines
- **Privacy First**: No external API calls for inference - all local
- **Secure Storage**: Use appropriate secret management systems
- **Audit Trails**: Comprehensive logging for compliance
- **Access Controls**: Role-based access with principle of least privilege

---

## 🚀 Deployment & Operations

### Infrastructure Requirements
- **Kubernetes Cluster**: 3+ nodes for agent workloads
- **Redis/Cassandra**: Task queuing and state management
- **PostgreSQL**: Metadata storage and configuration
- **Prometheus/Grafana**: Monitoring and alerting
- **Jaeger**: Distributed tracing
- **Slack Integration**: Notification and alerting

### Resource Allocation Guidelines
- **Team Composition**: 2-3 Go developers, 2-3 frontend developers, 2 DevOps engineers, 1-2 ML engineers, 1 Product manager
- **Infrastructure Budget**: Additional compute resources for agents
- **AI Model Costs**: Token usage and API calls
- **Training Programs**: Developer enablement and adoption

### Success Metrics
- **Technical**: 70% toil automation, 95%+ success rate, 30% cost reduction
- **Business**: 40% productivity increase, 2x deployment speed, 25% infrastructure cost reduction
- **Adoption**: 70% developer usage, >4.5/5 satisfaction score

---

## 📝 Documentation Standards

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes
- **refactor**: Code refactoring
- **test**: Testing changes
- **chore**: Maintenance tasks

### Examples
```
feat: add certificate rotation skill

Implement automated TLS certificate lifecycle management
with expiry monitoring and renewal capabilities.

Closes #123
```

---

## 🔄 Continuous Improvement

### Feedback Loops
- **Success Stories**: Share peer success stories vs. mandates
- **Adoption Metrics**: Track usage patterns and satisfaction
- **Performance Monitoring**: Regular benchmarking and optimization
- **Technology Updates**: Stay current with emerging AI capabilities

### Risk Mitigation
- **Technical Risks**: Model performance testing and fallback mechanisms
- **Operational Risks**: Gradual rollout with demonstrated value
- **Business Risks**: Clear ROI metrics and regular reporting
- **Security Risks**: Sandboxed execution and comprehensive audit trails

---

## 🎯 Key Takeaways

1. **Safety First**: Never use destructive git commands - they cause irreversible damage
2. **Consistency Matters**: Use cross-platform tools like `gsed` for reliable operations
3. **Prevention Over Cure**: Implement proper .gitignore patterns and backup strategies
4. **Structured Approaches**: Clear separation of concerns in directory structures
5. **Monitoring & Debugging**: Comprehensive observability for distributed systems
6. **Security & Compliance**: Built-in audit trails and access controls
7. **Continuous Learning**: Regular evaluation and improvement of processes

This document serves as the definitive reference for safe, effective development practices in the GitOps infrastructure control plane project. All team members should familiarize themselves with these critical rules and best practices to ensure reliable, secure development workflows.

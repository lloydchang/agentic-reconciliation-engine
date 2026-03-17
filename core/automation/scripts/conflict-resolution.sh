#!/bin/bash

# Git Conflict Resolution Script
# Handles merge conflicts during bidirectional synchronization

set -euo pipefail

MIRROR_DIR="/tmp/git-mirror/gitops-infra-control-plane.git"
CONFLICT_LOG="/var/log/git-conflicts.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$CONFLICT_LOG"
}

resolve_conflicts() {
    local branch=$1
    log "Resolving conflicts for branch: $branch"
    
    cd "$MIRROR_DIR"
    git checkout "$branch" 2>/dev/null || git checkout -b "$branch" "origin/$branch"
    
    # Try to merge from secondary
    if git merge secondary/"$branch" --no-commit 2>/dev/null; then
        log "✅ Successfully merged secondary/$branch"
    else
        log "⚠️ Conflict detected with secondary/$branch"
        # Use ours strategy for infrastructure files
        if [ -f "core/resources/tenants/1-network/kustomization.yaml" ]; then
            git checkout --ours core/resources/
            git add core/resources/
            git commit -m "Auto-resolve conflicts: prefer primary for infrastructure"
            log "🔧 Resolved conflicts: prefer primary infrastructure"
        fi
    fi
    
    # Try to merge from tertiary
    if git merge tertiary/"$branch" --no-commit 2>/dev/null; then
        log "✅ Successfully merged tertiary/$branch"
    else
        log "⚠️ Conflict detected with tertiary/$branch"
        # Use ours strategy for critical files
        if [ -f "core/operators/flux/kustomization.yaml" ]; then
            git checkout --ours core/operators/
            git add core/operators/
            git commit -m "Auto-resolve conflicts: prefer primary for control-plane"
            log "🔧 Resolved conflicts: prefer primary control-plane"
        fi
    fi
}

# Main conflict resolution
log "Starting conflict resolution..."

# Get all branches
cd "$MIRROR_DIR"
git fetch --all

# Resolve conflicts for main branches
for branch in main master develop; do
    if git rev-parse --verify "origin/$branch" >/dev/null 2>&1; then
        resolve_conflicts "$branch"
    fi
done

log "Conflict resolution completed"

# Push resolved changes
git push origin --all
git push secondary --all
git push tertiary --all

log "Resolved changes pushed to all remotes"

#!/bin/bash

# Git Repository Mirroring Setup Script
# Sets up bidirectional synchronization between GitHub, GitLab, and Gitea

set -euo pipefail

# Configuration
PRIMARY_REPO="git@github.com:antigravity/gitops-infra-control-plane.git"
SECONDARY_REPO="git@gitlab.com:antigravity/gitops-infra-control-plane.git"
TERTIARY_REPO="git@gitea.internal:antigravity/gitops-infra-control-plane.git"
MIRROR_DIR="/tmp/git-mirror"

echo "🔄 Setting up Git Repository Mirroring..."

# Create mirror directory
mkdir -p "$MIRROR_DIR"
cd "$MIRROR_DIR"

# Clone primary repository as bare mirror
if [ ! -d "gitops-infra-control-plane.git" ]; then
    echo "📥 Cloning primary repository as bare mirror..."
    git clone --mirror "$PRIMARY_REPO"
fi

cd gitops-infra-control-plane.git

# Add remote repositories
echo "🔗 Adding remote repositories..."
git remote add secondary "$SECONDARY_REPO" || echo "Secondary remote already exists"
git remote add tertiary "$TERTIARY_REPO" || echo "Tertiary remote already exists"

# Fetch from all remotes
echo "📥 Fetching from all remotes..."
git fetch --all
git fetch secondary --all
git fetch tertiary --all

# Set up synchronization script
cat > /usr/local/bin/git-sync.sh << 'EOF'
#!/bin/bash

# Git Repository Synchronization Script
# Runs bidirectional sync between all repositories

set -euo pipefail

MIRROR_DIR="/tmp/git-mirror/gitops-infra-control-plane.git"
LOG_FILE="/var/log/git-sync.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

cd "$MIRROR_DIR"

log "Starting synchronization..."

# Fetch from all remotes
log "Fetching from primary..."
git fetch origin || log "❌ Failed to fetch from primary"

log "Fetching from secondary..."
git fetch secondary || log "❌ Failed to fetch from secondary"

log "Fetching from tertiary..."
git fetch tertiary || log "❌ Failed to fetch from tertiary"

# Push to all remotes
log "Pushing to primary..."
git push --mirror origin || log "❌ Failed to push to primary"

log "Pushing to secondary..."
git push --mirror secondary || log "❌ Failed to push to secondary"

log "Pushing to tertiary..."
git push --mirror tertiary || log "❌ Failed to push to tertiary"

log "Synchronization completed"
EOF

chmod +x /usr/local/bin/git-sync.sh

# Set up cron job for automatic synchronization
echo "⏰ Setting up automatic synchronization..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/git-sync.sh") | crontab -

echo "✅ Git repository mirroring setup completed!"
echo "📍 Mirror directory: $MIRROR_DIR"
echo "🔄 Sync runs every 5 minutes"
echo "📝 Logs: /var/log/git-sync.log"

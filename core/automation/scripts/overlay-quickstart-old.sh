#!/usr/bin/env bash
# =============================================================================
# Overlay Quickstart - True Overlay Pattern Implementation
# This script OVERLAYS additional functionality on top of quickstart.sh
# =============================================================================
set -euo pipefail

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

pass() { echo -e "  ${GREEN}✓${RESET} $*"; }
fail() { echo -e "  ${RED}✗${RESET} $*"; exit 1; }
warn() { echo -e "  ${YELLOW}!${RESET} $*"; }
info() { echo -e "  ${CYAN}→${RESET} $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OVERLAY_DIR="${OVERLAY_DIR:-overlays}"

# =============================================================================
# OVERLAY CONFIGURATION - These are the overlay customizations
# =============================================================================

# Overlay-specific environment variables that quickstart.sh will pick up
export QUICKSTART_OVERLAY_MODE="true"
export OVERLAY_FEATURES="${OVERLAY_FEATURES:-debug,dashboard,enhanced}"
export OVERLAY_NAMESPACE="${OVERLAY_NAMESPACE:-overlay-system}"
export OVERLAY_LOG_DIR="${SCRIPT_DIR}/../logs/overlay-quickstart"

# Hook directories for overlay injection
export HOOKS_DIR="${OVERLAY_DIR}/hooks"
export PATCHES_DIR="${OVERLAY_DIR}/patches"

# =============================================================================
# HOOK SETUP - Create hooks that quickstart.sh will call if they exist
# =============================================================================

setup_overlay_hooks() {
    echo -e "${BOLD}Setting up overlay hooks...${RESET}"
    
    mkdir -p "$HOOKS_DIR" "$PATCHES_DIR"
    
    # Pre-quickstart hook - runs before base quickstart
    cat > "$HOOKS_DIR/pre-quickstart.sh" << 'EOF'
#!/usr/bin/env bash
# Pre-quickstart overlay hook
echo "🔧 Overlay: Pre-quickstart setup"

# Set overlay-specific environment
export OVERLAY_MODE=true
export ENHANCED_LOGGING=true
export DEBUG_DASHBOARD=true

# Create overlay directories
mkdir -p "${OVERLAY_LOG_DIR}"
mkdir -p "${OVERLAY_DIR}/config"

echo "✓ Overlay pre-setup complete"
EOF

    # Post-quickstart hook - runs after base quickstart  
    cat > "$HOOKS_DIR/post-quickstart.sh" << 'EOF'
#!/usr/bin/env bash
# Post-quickstart overlay hook
echo "🚀 Overlay: Post-quickstart enhancements"

# Deploy overlay-specific resources
if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null; then
    echo "Deploying overlay enhancements..."
    
    # Create overlay namespace
    kubectl create namespace overlay-system --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy enhanced debug dashboard
    if [[ -f "${OVERLAY_DIR}/debug-dashboard.yaml" ]]; then
        kubectl apply -f "${OVERLAY_DIR}/debug-dashboard.yaml"
    fi
    
    echo "✓ Overlay enhancements deployed"
else
    echo "⚠️  Cluster not accessible - skipping overlay deployment"
fi

echo "✓ Overlay post-setup complete"
EOF

    chmod +x "$HOOKS_DIR"/pre-quickstart.sh "$HOOKS_DIR"/post-quickstart.sh
    pass "Overlay hooks created"
}

# =============================================================================
# QUICKSTART.SH MODIFICATION CHECK
# Check if quickstart.sh supports overlay hooks
# =============================================================================

check_quickstart_overlay_support() {
    local quickstart_path="${SCRIPT_DIR}/quickstart.sh"
    
    if [[ ! -f "$quickstart_path" ]]; then
        fail "quickstart.sh not found at $quickstart_path"
    fi
    
    # Check if quickstart.sh has hook support
    if grep -q "pre-quickstart.sh" "$quickstart_path"; then
        pass "quickstart.sh has overlay hook support"
        return 0
    else
        warn "quickstart.sh needs overlay hook support added"
        add_overlay_support_to_quickstart "$quickstart_path"
        return 1
    fi
}

# =============================================================================
# ONE-TIME QUICKSTART.SH ENHANCEMENT  
# Add hook support to quickstart.sh (this is the only modification needed)
# =============================================================================

add_overlay_support_to_quickstart() {
    local quickstart_path="$1"
    
    echo -e "${BOLD}Adding overlay hook support to quickstart.sh...${RESET}"
    
    # Create backup
    cp "$quickstart_path" "${quickstart_path}.backup.$(date +%s)"
    
    # Add hook calls at strategic points
    # This is a minimal, safe modification
    
    # Add pre-hook after argument parsing
    sed -i '' '/^done$/a\
\
# Overlay: Allow pre-quickstart hook\
[ -f "./core/hooks/pre-quickstart.sh" ] && source ./core/hooks/pre-quickstart.sh' "$quickstart_path"
    
    # Add post-hook before final summary
    sed -i '' '/# Summary/i\
\
# Overlay: Allow post-quickstart hook\
[ -f "./core/hooks/post-quickstart.sh" ] && source ./core/hooks/post-quickstart.sh' "$quickstart_path"
    
    pass "Overlay hook support added to quickstart.sh"
    warn "Note: This is a one-time modification to enable overlay pattern"
}

# =============================================================================
# OVERLAY RESOURCES CREATION
# Create additional resources that the overlay will deploy
# =============================================================================

create_overlay_resources() {
    echo -e "${BOLD}Creating overlay resources...${RESET}"
    
    # Enhanced debug dashboard
    cat > "${OVERLAY_DIR}/debug-dashboard.yaml" << 'EOF'
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: debug-dashboard-config
  namespace: overlay-system
data:
  dashboard.yaml: |
    title: "Enhanced Debug Dashboard"
    features:
      - real-time-logs
      - metrics-visualization  
      - agent-status
      - overlay-management
    overlay_mode: "true"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: debug-dashboard
  namespace: overlay-system
  labels:
    app: debug-dashboard
    overlay: "true"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: debug-dashboard
  template:
    metadata:
      labels:
        app: debug-dashboard
        overlay: "true"
    spec:
      containers:
      - name: dashboard
        image: nginx:alpine
        ports:
        - containerPort: 80
        volumeMounts:
        - name: config
          mountPath: /usr/share/nginx/html/dashboard.yaml
          subPath: dashboard.yaml
      volumes:
      - name: config
        configMap:
          name: debug-dashboard-config
EOF

    pass "Overlay resources created"
}

# =============================================================================
# MAIN OVERLAY EXECUTION
# This is where we run the base quickstart with overlay enhancements
# =============================================================================

main() {
    echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}║   GitOps Infra Control Plane — Overlay Quickstart         ║${RESET}"
    echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${RESET}"
    echo
    echo "Overlay Mode: ${OVERLAY_FEATURES}"
    echo "Overlay Directory: $OVERLAY_DIR"
    echo
    
    # Step 1: Setup overlay infrastructure
    setup_overlay_hooks
    
    # Step 2: Ensure quickstart.sh supports overlay pattern
    check_quickstart_overlay_support
    
    # Step 3: Create overlay resources
    create_overlay_resources
    
    # Step 4: RUN THE BASE QUICKSTART with overlay context
    echo
    echo -e "${BOLD}🚀 Running base quickstart.sh with overlay enhancements...${RESET}"
    echo
    
    # Source quickstart.sh - this will pick up our env vars and call our hooks
    source "${SCRIPT_DIR}/quickstart.sh" "$@"
    
    # Step 5: Overlay completion
    echo
    echo -e "${BOLD}Overlay Quickstart Complete!${RESET}"
    echo "=========================="
    echo
    echo "Your Agentic Reconciliation Engine includes overlay enhancements:"
    echo "  • Enhanced debug dashboard"
    echo "  • Overlay-specific logging"
    echo "  • Hook-based extensibility"
    echo
    echo "Overlay resources in: $OVERLAY_DIR"
    echo "Overlay logs in: $OVERLAY_LOG_DIR"
    echo
    echo -e "${GREEN}${BOLD}Overlay-enhanced Agentic Reconciliation Engine deployed!${RESET}"
}

# Parse arguments and pass through to quickstart.sh
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    cat <<EOF
Overlay Quickstart - True Overlay Pattern

USAGE: $0 [quickstart-options] [--overlay-features FEATURES]

This script OVERLAYS additional functionality on top of quickstart.sh.
The base quickstart.sh runs first, then overlay enhancements are applied.

OVERLAY OPTIONS:
  --overlay-features FEATURES    Comma-separated overlay features (default: debug,dashboard,enhanced)
  --overlay-dir DIR             Overlay directory (default: overlays)  

QUICKSTART OPTIONS:
  All quickstart.sh options are supported and passed through:
  --dry-run, --skip-bootstrap, --skip-hub, --skip-spoke, etc.

EXAMPLES:
  $0                              # Full quickstart with overlay enhancements
  $0 --dry-run                    # Preview with overlay enhancements  
  $0 --skip-spoke                 # Quickstart without spoke clusters + overlays
  $0 --overlay-features debug     # Quickstart with only debug overlay features

OVERLAY PATTERN:
  This script uses the true overlay pattern:
  1. Sets overlay environment variables
  2. Creates hook files that quickstart.sh calls
  3. Runs the base quickstart.sh (unchanged except for hook support)
  4. Deploys overlay-specific resources

For base quickstart functionality, use quickstart.sh directly.
EOF
    exit 0
fi

# Handle overlay-specific arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --overlay-features)
            export OVERLAY_FEATURES="$2"
            shift 2
            ;;
        --overlay-dir)
            export OVERLAY_DIR="$2"
            shift 2
            ;;
        *)
            # Pass through to quickstart.sh
            break
            ;;
    esac
done

# Run main overlay function
main "$@"

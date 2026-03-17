#!/bin/bash

# Git Hooks Installation Script
# This script installs SOPS validation git hooks

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the repository root
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "$(pwd)")

echo -e "${GREEN}🔧 Installing SOPS Git Hooks${NC}"
echo "This script installs git hooks for SOPS validation."
echo

# Check if we're in a git repository
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo -e "${RED}❌ Not in a Git repository${NC}"
    echo "This script must be run from within a Git repository."
    exit 1
fi

# Git hooks directory
HOOKS_DIR="${REPO_ROOT}/.git/hooks"
SCRIPTS_DIR="${REPO_ROOT}/scripts"

# Check if hooks directory exists
if [[ ! -d "$HOOKS_DIR" ]]; then
    echo -e "${RED}❌ Git hooks directory not found: $HOOKS_DIR${NC}"
    exit 1
fi

# Function to install a hook
install_hook() {
    local hook_name="$1"
    local source_file="${SCRIPTS_DIR}/git-hooks/${hook_name}"
    local target_file="${HOOKS_DIR}/${hook_name}"
    
    echo "Installing $hook_name hook..."
    
    # Copy the hook file
    if [[ -f "$source_file" ]]; then
        cp "$source_file" "$target_file"
        chmod +x "$target_file"
        echo -e "${GREEN}✅ $hook_name hook installed${NC}"
    else
        echo -e "${YELLOW}⚠️  $hook_name hook source not found, skipping${NC}"
    fi
}

# Create git-hooks directory in scripts if it doesn't exist
mkdir -p "${SCRIPTS_DIR}/git-hooks"

# Move existing hooks to git-hooks directory for backup
echo "Backing up existing hooks..."
for hook in pre-commit pre-push; do
    if [[ -f "${HOOKS_DIR}/${hook}" ]]; then
        # Check if it's our SOPS hook (has our signature)
        if grep -q "SOPS.*validation" "${HOOKS_DIR}/${hook}" 2>/dev/null; then
            echo "Existing SOPS $hook found, will be replaced"
        else
            # Backup existing hook
            cp "${HOOKS_DIR}/${hook}" "${SCRIPTS_DIR}/git-hooks/${hook}.backup.$(date +%Y%m%d-%H%M%S)"
            echo -e "${YELLOW}⚠️  Backed up existing $hook hook${NC}"
        fi
    fi
done

# Copy current hooks to git-hooks directory for version control
echo "Copying hooks to scripts directory for version control..."
cp "${HOOKS_DIR}/pre-commit" "${SCRIPTS_DIR}/git-hooks/pre-commit" 2>/dev/null || true
cp "${HOOKS_DIR}/pre-push" "${SCRIPTS_DIR}/git-hooks/pre-push" 2>/dev/null || true

# Install hooks
echo "Installing SOPS validation hooks..."
install_hook "pre-commit"
install_hook "pre-push"

# Create additional utility hooks
echo "Creating additional utility hooks..."

# Post-commit hook (optional - for notifications)
cat > "${HOOKS_DIR}/post-commit" << 'EOF'
#!/bin/bash

# Post-commit hook for SOPS notifications
# This hook provides notifications after successful commits

# Check if any .secret.yaml files were committed
if git diff --name-only HEAD~1 HEAD | grep -q "\.secret\.yaml$"; then
    echo "🔒 SOPS secrets were committed in this change"
    echo "   Remember to rotate keys regularly and monitor access"
fi

# Check if .sops.yaml was modified
if git diff --name-only HEAD~1 HEAD | grep -q "\.sops\.yaml$"; then
    echo "⚙️  SOPS configuration was updated"
    echo "   Ensure all team members have the latest configuration"
fi
EOF

chmod +x "${HOOKS_DIR}/post-commit"

# Create a simple git hooks management script
cat > "${SCRIPTS_DIR}/manage-git-hooks.sh" << 'EOF'
#!/bin/bash

# Git Hooks Management Script
# This script helps manage SOPS git hooks

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the repository root
REPO_ROOT=$(git rev-parse --show-toplevel)
HOOKS_DIR="${REPO_ROOT}/.git/hooks"

case "${1:-}" in
    "install")
        echo "Installing SOPS git hooks..."
        bash "${REPO_ROOT}/core/core/automation/ci-cd/scripts/install-git-hooks.sh"
        ;;
    "uninstall")
        echo "Uninstalling SOPS git hooks..."
        for hook in pre-commit pre-push post-commit; do
            if [[ -f "${HOOKS_DIR}/${hook}" ]]; then
                if grep -q "SOPS.*validation" "${HOOKS_DIR}/${hook}" 2>/dev/null; then
                    rm "${HOOKS_DIR}/${hook}"
                    echo "Removed $hook hook"
                fi
            fi
        done
        echo -e "${GREEN}✅ SOPS git hooks uninstalled${NC}"
        ;;
    "status")
        echo "SOPS Git Hooks Status:"
        echo
        for hook in pre-commit pre-push post-commit; do
            if [[ -f "${HOOKS_DIR}/${hook}" ]]; then
                if [[ -x "${HOOKS_DIR}/${hook}" ]]; then
                    echo -e "${GREEN}✅ $hook: Installed and executable${NC}"
                else
                    echo -e "${YELLOW}⚠️  $hook: Installed but not executable${NC}"
                fi
                if grep -q "SOPS.*validation" "${HOOKS_DIR}/${hook}" 2>/dev/null; then
                    echo "   (SOPS validation hook)"
                else
                    echo "   (Custom hook)"
                fi
            else
                echo -e "${RED}❌ $hook: Not installed${NC}"
            fi
            echo
        done
        ;;
    "test")
        echo "Testing SOPS git hooks..."
        echo "Creating test files..."
        
        # Create a test secret file
        echo "apiVersion: v1
kind: Secret
metadata:
  name: test-secret
type: Opaque
data:
  key: dGVzdA==" > test-secret.yaml
        
        echo "Testing pre-commit hook..."
        if git add test-secret.yaml 2>/dev/null; then
            if git commit -m "Test commit" 2>/dev/null; then
                echo -e "${GREEN}✅ Pre-commit hook passed${NC}"
            else
                echo -e "${YELLOW}⚠️  Pre-commit hook blocked commit (expected for unencrypted secret)${NC}"
            fi
            git reset HEAD test-secret.yaml 2>/dev/null || true
        fi
        
        # Clean up
        rm -f test-secret.yaml
        echo "Test completed"
        ;;
    *)
        echo "Usage: $0 {install|uninstall|status|test}"
        echo
        echo "Commands:"
        echo "  install   - Install SOPS git hooks"
        echo "  uninstall - Uninstall SOPS git hooks"
        echo "  status    - Show hook installation status"
        echo "  test      - Test hook functionality"
        ;;
esac
EOF

chmod +x "${SCRIPTS_DIR}/manage-git-hooks.sh"

echo
echo -e "${GREEN}🎉 Git hooks installation complete!${NC}"
echo
echo -e "${YELLOW}📋 Installed hooks:${NC}"
echo "  • pre-commit  - Validates SOPS configuration and encrypted secrets"
echo "  • pre-push   - Additional validation before pushing to remote"
echo "  • post-commit - Notifications after successful commits"
echo
echo -e "${YELLOW}🔧 Management commands:${NC}"
echo "  ./core/core/automation/ci-cd/scripts/manage-git-hooks.sh status  - Check hook status"
echo "  ./core/core/automation/ci-cd/scripts/manage-git-hooks.sh test    - Test hook functionality"
echo "  ./core/core/automation/ci-cd/scripts/manage-git-hooks.sh uninstall - Remove hooks"
echo
echo -e "${YELLOW}⚠️  Important notes:${NC}"
echo "  • Hooks will run automatically on git operations"
echo "  • You can bypass hooks with --no-verify (not recommended)"
echo "  • Hooks are version controlled in core/core/automation/ci-cd/scripts/git-hooks/"
echo "  • Team members should run this script after cloning"
echo
echo -e "${GREEN}✅ Your SOPS workflow is now protected by git hooks!${NC}"

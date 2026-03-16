#!/bin/bash
# GitOps Infrastructure Control Plane - Quick Start Script
# Repository setup and initial onboarding - supports overlay extensions

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script information
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Hook support - allows overlays to extend quickstart without modification
run_hooks() {
    local hook_name="$1"
    local hook_file="hooks/${hook_name}.sh"
    
    if [[ -f "$hook_file" ]]; then
        print_info "Running $hook_name hook..."
        if bash "$hook_file"; then
            print_success "$hook_name hook completed"
        else
            print_error "$hook_name hook failed"
            return 1
        fi
    else
        print_info "No $hook_name hook found - skipping"
    fi
}

# Main quick start function
main() {
    print_header "GitOps Infrastructure Quick Start"
    
    echo -e "${BLUE}Welcome to GitOps Infrastructure Control Plane!${NC}"
    echo ""
    
    # Check if we're in overlay mode
    if [[ "${OVERLAY_MODE:-false}" == "true" ]]; then
        echo -e "${YELLOW}Running in overlay mode${NC}"
    else
        echo -e "${YELLOW}This script sets up your development environment.${NC}"
    fi
    echo ""
    
    # Check if we're in the right directory
    if [[ ! -f "$REPO_ROOT/README.md" ]]; then
        print_error "Not in repository root. Please run from repository root."
        exit 1
    fi
    
    # Run pre-quickstart hook (overlay extension point)
    run_hooks "pre-quickstart" || return 1
    
    print_info "Checking prerequisites..."
    
    # Check for required tools
    local missing_tools=()
    
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    if ! command -v kustomize &> /dev/null; then
        missing_tools+=("kustomize")
    fi
    
    if ! command -v python3 &> /dev/null; then
        missing_tools+=("python3")
    fi
    
    if ! command -v git &> /dev/null; then
        missing_tools+=("git")
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        echo -e "${YELLOW}Please install missing tools and try again.${NC}"
        exit 1
    fi
    
    print_success "All prerequisites satisfied"
    
    # Setup basic configuration
    print_info "Setting up development environment..."
    
    # Create basic directories if they don't exist
    mkdir -p logs/
    mkdir -p tmp/
    
    # Make scripts executable
    find "$SCRIPT_DIR" -name "*.sh" -exec chmod +x {} \;
    find "$SCRIPT_DIR" -name "*.py" -exec chmod +x {} \;
    
    print_success "Development environment ready"
    
    # Skip examples if in overlay mode and requested
    if [[ "${OVERLAY_MODE:-false}" == "true" && "${QUICKSTART_SKIP_EXAMPLES:-false}" == "true" ]]; then
        print_info "Skipping example creation (overlay mode)"
    else
        # Create basic examples for non-overlay mode
        echo -e "${BLUE}Creating basic examples...${NC}"
        mkdir -p examples/basic/
        cat > examples/basic/README.md << 'EOF'
# Basic Examples

This directory contains basic examples for getting started with the GitOps Infrastructure Control Plane.

## Quick Start Examples

1. **Basic Setup**: Run `./quickstart.sh` to get started
2. **Overlay Mode**: Run `./overlay-quickstart.sh` for overlay-based setup
3. **Advanced**: See `examples/` directory for comprehensive examples

## Next Steps

1. Read the documentation in `docs/`
2. Check the examples in `examples/`
3. Use the scripts in `scripts/` for automation
EOF
        print_success "Basic examples created"
    fi
    
    # Run post-quickstart hook (overlay extension point)
    run_hooks "post-quickstart" || return 1
    
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    
    if [[ "${OVERLAY_MODE:-false}" == "true" ]]; then
        echo "1. Use overlay-manager.sh to manage overlays"
        echo "2. Create custom overlays with overlay-cli.py"
        echo "3. Deploy overlays to your cluster"
        echo "4. Monitor overlay status and logs"
        echo ""
        echo -e "${GREEN}🚀 Overlay system is ready!${NC}"
    else
        echo "1. Use overlay-quickstart.sh to create and manage overlays"
        echo "2. Read docs/OVERLAY-QUICK-START.md for detailed guidance"
        echo "3. Check examples/ directory for sample configurations"
        echo ""
        echo -e "${GREEN}🚀 Ready to start working with overlays!${NC}"
    fi
}

# Help function
show_help() {
    echo "GitOps Infrastructure Control Plane - Quick Start"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up development environment for GitOps Infrastructure Control Plane."
    echo "  This includes tool verification, directory setup, and basic configuration."
    echo ""
    echo "  This script supports overlay extensions through hooks:"
    echo "  - hooks/pre-quickstart.sh: Runs before main quickstart logic"
    echo "  - hooks/post-quickstart.sh: Runs after main quickstart logic"
    echo ""
    echo "  Overlay mode is activated when OVERLAY_MODE=true is set."
    echo "  In overlay mode, the script adapts behavior for overlay workflows."
    echo ""
    echo "  For overlay-specific operations, use: overlay-quickstart.sh"
    echo "  For overlay lifecycle management, use: overlay-manager.sh"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                    # Standard repository setup"
    echo "  OVERLAY_MODE=true $0   # Setup with overlay extensions"
    echo ""
    echo "  # With overlay-quickstart.sh (recommended for overlay workflows)"
    echo "  overlay-quickstart.sh --all"
    echo ""
    echo "HOOKS:"
    echo "  To extend quickstart.sh without modifying it:"
    echo "  1. Create hooks/ directory"
    echo "  2. Add hooks/pre-quickstart.sh (runs before main logic)"
    echo "  3. Add hooks/post-quickstart.sh (runs after main logic)"
    echo "  4. Set OVERLAY_MODE=true when running"
    echo ""
    echo "  The hooks will be automatically sourced and executed."
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac

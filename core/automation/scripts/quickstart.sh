#!/bin/bash
# Agentic Reconciliation Engine - Quick Start Script
# Repository setup and initial onboarding - supports overlay extensions

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source common functions
if [[ -f "$SCRIPT_DIR/quickstart-common.sh" ]]; then
    source "$SCRIPT_DIR/quickstart-common.sh"
else
    echo "Error: quickstart-common.sh not found at $SCRIPT_DIR/quickstart-common.sh"
    exit 1
fi

# Main quick start function
main() {
    common_main "General"
}

# Help function
show_help() {
    echo "Agentic Reconciliation Engine - Quick Start"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up development environment for Agentic Reconciliation Engine."
    echo "  This includes tool verification, directory setup, basic configuration,"
    echo "  and deployment of AI agents dashboard with running agents."
    echo ""
    echo "  For environment-specific setups, use:"
    echo "  - quickstart-local-kind.sh"
    echo "  - quickstart-local-docker-desktop.sh"
    echo "  - quickstart-local-minikube.sh"
    echo "  - quickstart-remote-aws.sh"
    echo "  - quickstart-remote-azure.sh"
    echo "  - quickstart-remote-gcp.sh"
    echo "  - And more environment-specific scripts"
    echo ""
    echo "  This script supports overlay extensions through hooks:"
    echo "  - core/hooks/pre-quickstart.sh: Runs before main quickstart logic"
    echo "  - core/hooks/post-quickstart.sh: Runs after main quickstart logic"
    echo ""
    echo "  Overlay mode is activated when OVERLAY_MODE=true is set."
    echo "  In overlay mode, the script adapts behavior for overlay workflows."
    echo ""
    echo "  For overlay-specific operations, use: overlay-quickstart.sh"
    echo "  For overlay lifecycle management, use: overlay-manager.sh"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                    # Standard repository setup with AI agents dashboard"
    echo "  OVERLAY_MODE=true $0   # Setup with overlay extensions and AI agents dashboard"
    echo ""
    echo "  # With overlay-quickstart.sh (recommended for overlay workflows)"
    echo "  overlay-quickstart.sh --all"
    echo ""
    echo "HOOKS:"
    echo "  To extend quickstart.sh without modifying it:"
    echo "  1. Create core/hooks/ directory"
    echo "  2. Add core/hooks/pre-quickstart.sh (runs before main logic)"
    echo "  3. Add core/hooks/post-quickstart.sh (runs after main logic)"
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

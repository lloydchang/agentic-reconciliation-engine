#!/bin/bash
# Agentic Reconciliation Engine - Quick Start Script (Local Docker Desktop)
# Environment-specific quickstart for local Docker Desktop Kubernetes

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

# Help function
show_help() {
    echo "Agentic Reconciliation Engine - Quick Start (Local Docker Desktop)"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up development environment for Agentic Reconciliation Engine"
    echo "  using local Docker Desktop Kubernetes cluster."
    echo ""
    echo "  This includes:"
    echo "  - Docker Desktop verification and Kubernetes setup check"
    echo "  - Tool verification and prerequisites checking"
    echo "  - Directory setup and basic configuration"
    echo "  - Deployment of AI agents dashboard with running agents"
    echo "  - AI Agent Skills deployment and configuration"
    echo ""
    echo "  This script supports overlay extensions through hooks:"
    echo "  - core/hooks/pre-quickstart.sh: Runs before main quickstart logic"
    echo "  - core/hooks/post-quickstart.sh: Runs after main quickstart logic"
    echo ""
    echo "  Overlay mode is activated when OVERLAY_MODE=true is set."
    echo "  In overlay mode, the script adapts behavior for overlay workflows."
    echo ""
    echo "EXAMPLES:"
    echo "  $0                                    # Standard Docker Desktop setup with AI agents dashboard"
    echo "  OVERLAY_MODE=true $0                   # Setup with overlay extensions and AI agents dashboard"
    echo ""
    echo "REQUIREMENTS:"
    echo "  - Docker Desktop installed and running"
    echo "  - Kubernetes enabled in Docker Desktop preferences"
    echo "  - kubectl, kustomize, python3, git"
    echo ""
    echo "DOCKER DESKTOP CONFIGURATION:"
    echo "  - Uses existing Docker Desktop Kubernetes cluster"
    echo "  - No cluster creation required (uses built-in)"
    echo "  - Automatic context detection and setup"
    echo "  - Verifies Kubernetes is enabled and accessible"
    echo ""
    echo "OVERLAY USAGE:"
    echo "  For overlay-specific operations, use: overlay-quickstart-local-docker-desktop.sh"
    echo "  For overlay lifecycle management, use: overlay-manager.sh"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                                    # Standard Docker Desktop setup with AI agents dashboard"
    echo "  OVERLAY_MODE=true $0                   # Setup with overlay extensions and AI agents dashboard"
    echo ""
}

# Main function
main() {
    common_main "Docker Desktop"
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

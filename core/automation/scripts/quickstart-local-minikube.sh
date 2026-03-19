#!/bin/bash
# Agentic Reconciliation Engine - Quick Start Script (Local Minikube)
# Environment-specific quickstart for local Minikube clusters

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
    echo "Agentic Reconciliation Engine - Quick Start (Local Minikube)"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up development environment for Agentic Reconciliation Engine"
    echo "  using local Minikube Kubernetes cluster."
    echo ""
    echo "  This includes:"
    echo "  - Minikube cluster startup and configuration"
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
    echo "  $0                                    # Standard Minikube setup with AI agents dashboard"
    echo "  OVERLAY_MODE=true $0                   # Setup with overlay extensions and AI agents dashboard"
    echo ""
    echo "REQUIREMENTS:"
    echo "  - Minikube installed and available"
    echo "  - kubectl, kustomize, python3, git"
    echo "  - Virtualization support (for Minikube driver)"
    echo ""
    echo "MINIKUBE CONFIGURATION:"
    echo "  - Uses default Minikube cluster"
    echo "  - Automatic startup if not running"
    echo "  - Context automatically set to minikube"
    echo "  - Supports various Minikube drivers (docker, kvm2, etc.)"
    echo ""
    echo "OVERLAY USAGE:"
    echo "  For overlay-specific operations, use: overlay-quickstart-local-minikube.sh"
    echo "  For overlay lifecycle management, use: overlay-manager.sh"
}

# Main function
main() {
    common_main "Minikube"
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

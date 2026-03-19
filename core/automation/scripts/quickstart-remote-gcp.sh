#!/bin/bash
# Agentic Reconciliation Engine - Quick Start Script (Remote GCP)
# Environment-specific quickstart for remote Google Cloud GKE clusters

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
    echo "Agentic Reconciliation Engine - Quick Start (Remote GCP)"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up development environment for Agentic Reconciliation Engine"
    echo "  using remote Google Cloud GKE clusters."
    echo ""
    echo "  This includes:"
    echo "  - Google Cloud SDK authentication and verification"
    echo "  - GKE cluster connection and configuration"
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
    echo "  $0                                    # Standard GCP GKE setup with AI agents dashboard"
    echo "  OVERLAY_MODE=true $0                   # Setup with overlay extensions and AI agents dashboard"
    echo ""
    echo "REQUIREMENTS:"
    echo "  - Google Cloud SDK installed and authenticated"
    echo "  - Access to Google Cloud GKE cluster"
    echo "  - kubectl, kustomize, python3, git"
    echo "  - Appropriate GCP permissions"
    echo ""
    echo "GCP CONFIGURATION:"
    echo "  - Uses existing GCP project and GKE cluster"
    echo "  - Automatic kubeconfig setup for GKE"
    echo "  - Verifies cluster access and permissions"
    echo "  - Supports multiple GKE clusters (selectable via context)"
    echo ""
    echo "OVERLAY USAGE:"
    echo "  For overlay-specific operations, use: overlay-quickstart-remote-gcp.sh"
    echo "  For overlay lifecycle management, use: overlay-manager.sh"
}

# Main function
main() {
    common_main "GCP"
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

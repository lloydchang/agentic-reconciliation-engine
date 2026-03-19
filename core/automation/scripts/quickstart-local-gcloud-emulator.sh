#!/bin/bash
# Agentic Reconciliation Engine - Quick Start Script (Local Google Cloud Emulator)
# Environment-specific quickstart for local Google Cloud services emulation

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
    echo "Agentic Reconciliation Engine - Quick Start (Local Google Cloud Emulator)"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up development environment for Agentic Reconciliation Engine"
    echo "  using local Google Cloud services emulation."
    echo ""
    echo "  This includes:"
    echo "  - Google Cloud SDK setup and emulator startup"
    echo "  - Cloud Datastore emulator configuration"
    echo "  - Cloud Pub/Sub emulator configuration"
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
    echo "  $0                                    # Standard GCP emulation setup with AI agents dashboard"
    echo "  OVERLAY_MODE=true $0                   # Setup with overlay extensions and AI agents dashboard"
    echo ""
    echo "REQUIREMENTS:"
    echo "  - Google Cloud SDK installed and configured"
    echo "  - Docker installed and running"
    echo "  - kubectl, kustomize, python3, git"
    echo ""
    echo "GCP EMULATOR CONFIGURATION:"
    echo "  - Cloud Datastore: localhost:8081"
    echo "  - Cloud Pub/Sub: localhost:8085"
    echo "  - Consistency level: 1.0 (strong)"
    echo "  - Environment variables auto-configured"
    echo "  - Cleanup on script exit"
}

# Cleanup function
cleanup_gcloud_emulators() {
    print_info "Cleaning up Google Cloud emulators..."
    
    # Kill emulator processes
    if [[ -f /tmp/gcloud-datastore-emulator.pid ]]; then
        local datastore_pid=$(cat /tmp/gcloud-datastore-emulator.pid)
        if kill -0 "$datastore_pid" 2>/dev/null; then
            kill "$datastore_pid"
            print_success "Cloud Datastore emulator stopped"
        fi
        rm -f /tmp/gcloud-datastore-emulator.pid
    fi
    
    if [[ -f /tmp/gcloud-pubsub-emulator.pid ]]; then
        local pubsub_pid=$(cat /tmp/gcloud-pubsub-emulator.pid)
        if kill -0 "$pubsub_pid" 2>/dev/null; then
            kill "$pubsub_pid"
            print_success "Cloud Pub/Sub emulator stopped"
        fi
        rm -f /tmp/gcloud-pubsub-emulator.pid
    fi
    
    # Clean up environment variables
    unset DATASTORE_EMULATOR_HOST PUBSUB_EMULATOR_HOST 2>/dev/null
}

# Main function
main() {
    # Set trap for cleanup on script exit
    trap cleanup_gcloud_emulators EXIT
    
    common_main "Google Cloud Emulator"
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

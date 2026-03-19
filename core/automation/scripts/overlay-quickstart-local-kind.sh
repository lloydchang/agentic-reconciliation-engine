#!/bin/bash
# Agentic Reconciliation Engine - Overlay Quick Start Script (Local Kind)
# Environment-specific overlay quickstart for local Kind clusters

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source common overlay functions
if [[ -f "$SCRIPT_DIR/overlay-quickstart-common.sh" ]]; then
    source "$SCRIPT_DIR/overlay-quickstart-common.sh"
else
    echo "Error: overlay-quickstart-common.sh not found at $SCRIPT_DIR/overlay-quickstart-common.sh"
    exit 1
fi

# Help function
show_help() {
    echo "Agentic Reconciliation Engine - Overlay Quick Start (Local Kind)"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help        Show this help message"
    echo "  -e, --examples     Create example overlays only"
    echo "  -t, --test         Test overlay system only"
    echo "  -d, --deploy       Deploy example overlay only"
    echo "  -a, --all          Run complete overlay quick start"
    echo ""
    echo "DESCRIPTION:"
    echo "  Overlay quick start for Agentic Reconciliation Engine on Kind clusters."
    echo "  Demonstrates overlay pattern where base script (quickstart-local-kind.sh) is"
    echo "  extended without modification through environment variables and hooks."
    echo ""
    echo "  This includes:"
    echo "  - Kind cluster setup and configuration"
    echo "  - Overlay environment setup and hooks creation"
    echo "  - Base quickstart execution with overlay extensions"
    echo "  - Example overlay creation and deployment"
    echo "  - AI Agent Skills deployment and configuration"
    echo ""
    echo "EXAMPLES:"
    echo "  $0 --all              # Complete Kind overlay quick start"
    echo "  $0 --examples          # Create example overlays only"
    echo "  $0 --test              # Test overlay system only"
    echo "  $0 --deploy            # Deploy example overlay only"
    echo ""
    echo "REQUIREMENTS:"
    echo "  - Kind installed and available"
    echo "  - kubectl, kustomize, python3, git"
    echo "  - Docker running (Kind uses Docker containers)"
    echo ""
    echo "KIND CONFIGURATION:"
    echo "  - Cluster name: agentic-reconciliation"
    echo "  - Config file: core/config/kind/cluster-config.yaml (if exists)"
    echo "  - Default config used if custom config not found"
    echo ""
    echo "OVERLAY CONCEPT:"
    echo "  1. Sets up overlay environment variables"
    echo "  2. Creates hook files that base quickstart will source"
    echo "  3. Runs base quickstart-local-kind.sh (never modifying it)"
    echo "  4. Base quickstart automatically picks up overlay extensions"
    echo "  5. No need to ever modify base quickstart scripts again"
    echo ""
    echo "ENVIRONMENT VARIABLES:"
    echo "  OVERLAY_DIR            Overlay directory (default: overlay)"
    echo "  QUICKSTART_SKIP_EXAMPLES  Skip example creation (default: false)"
    echo "  QUICKSTART_ENABLE_OVERLAYS Enable overlay features (default: true)"
}

# Complete overlay quick start
complete_overlay_quickstart() {
    common_overlay_main "Kind"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -e|--examples)
        setup_overlay_environment
        create_overlay_hooks
        create_overlay_examples
        deploy_ai_agent_skills
        ;;
    -t|--test)
        setup_overlay_environment
        create_overlay_hooks
        test_overlay_system
        ;;
    -d|--deploy)
        setup_overlay_environment
        create_overlay_hooks
        deploy_example_overlay
        deploy_ai_agent_skills
        ;;
    -a|--all)
        complete_overlay_quickstart
        ;;
    "")
        complete_overlay_quickstart
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac

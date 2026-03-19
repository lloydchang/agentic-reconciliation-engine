#!/bin/bash
# Agentic Reconciliation Engine - Quick Start Script (Local LocalStack AWS)
# Environment-specific quickstart for local LocalStack AWS emulation

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
    echo "Agentic Reconciliation Engine - Quick Start (Local LocalStack AWS)"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up development environment for Agentic Reconciliation Engine"
    echo "  using local LocalStack AWS services emulation."
    echo ""
    echo "  This includes:"
    echo "  - LocalStack container startup and configuration"
    echo "  - AWS CLI configuration for LocalStack endpoint"
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
    echo "  $0                                    # Standard LocalStack setup with AI agents dashboard"
    echo "  OVERLAY_MODE=true $0                   # Setup with overlay extensions and AI agents dashboard"
    echo ""
    echo "REQUIREMENTS:"
    echo "  - Docker installed and running"
    echo "  - LocalStack Docker image (auto-pulled if needed)"
    echo "  - kubectl, kustomize, python3, git"
    echo "  - AWS CLI (recommended for testing)"
    echo ""
    echo "LOCALSTACK CONFIGURATION:"
    echo "  - Container name: localstack"
    echo "  - Ports: 4566 (main endpoint), 4571 (web UI)"
    echo "  - AWS credentials: test/test (auto-configured)"
    echo "  - Region: us-east-1 (auto-configured)"
    echo "  - Endpoint: http://localhost:4566 (auto-configured)"
}

# Cleanup function
cleanup_localstack() {
    print_info "Cleaning up LocalStack resources..."
    if docker ps | grep -q "localstack"; then
        docker stop localstack
        docker rm localstack
        print_success "LocalStack container stopped and removed"
    fi
}

# Main function
main() {
    # Set trap for cleanup on script exit
    trap cleanup_localstack EXIT
    
    common_main "LocalStack AWS"
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

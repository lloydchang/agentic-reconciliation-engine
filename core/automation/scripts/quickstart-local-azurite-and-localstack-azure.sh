#!/bin/bash
# Agentic Reconciliation Engine - Quick Start Script (Local Azurite and LocalStack Azure)
# Environment-specific quickstart for local Azure emulation with Azurite and LocalStack

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
    echo "Agentic Reconciliation Engine - Quick Start (Local Azurite and LocalStack Azure)"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up development environment for Agentic Reconciliation Engine"
    echo "  using local Azure services emulation with Azurite and LocalStack."
    echo ""
    echo "  This includes:"
    echo "  - Azurite container startup for Azure Storage emulation"
    echo "  - LocalStack container startup for Azure services emulation"
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
    echo "  $0                                    # Standard Azure emulation setup with AI agents dashboard"
    echo "  OVERLAY_MODE=true $0                   # Setup with overlay extensions and AI agents dashboard"
    echo ""
    echo "REQUIREMENTS:"
    echo "  - Docker installed and running"
    echo "  - Azurite Docker image (auto-pulled if needed)"
    echo "  - LocalStack Docker image (auto-pulled if needed)"
    echo "  - kubectl, kustomize, python3, git"
    echo "  - Azure CLI (recommended for testing)"
    echo ""
    echo "AZURITE CONFIGURATION:"
    echo "  - Container name: azurite"
    echo "  - Ports: 10000 (Blob), 10001 (Queue), 10002 (Table)"
    echo ""
    echo "LOCALSTACK AZURE CONFIGURATION:"
    echo "  - Container name: localstack-azure"
    echo "  - Ports: 4566 (main endpoint), 4571 (web UI)"
    echo "  - Azure credentials and endpoints auto-configured"
}

# Cleanup function
cleanup_azure_emulators() {
    print_info "Cleaning up Azure emulator resources..."
    
    if docker ps | grep -q "azurite"; then
        docker stop azurite
        docker rm azurite
        print_success "Azurite container stopped and removed"
    fi
    
    if docker ps | grep -q "localstack-azure"; then
        docker stop localstack-azure
        docker rm localstack-azure
        print_success "LocalStack Azure container stopped and removed"
    fi
}

# Setup Azure-specific environment
setup_azure_emulators_environment() {
    print_info "Setting up Azure emulators environment..."
    
    # Setup Azurite
    setup_azurite_azure_environment || return 1
    
    # Setup LocalStack for Azure services
    print_info "Setting up LocalStack for Azure services..."
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker."
        return 1
    fi
    
    # Check if LocalStack is installed
    if ! docker images | grep -q "localstack"; then
        print_info "Pulling LocalStack Docker image..."
        docker pull localstack/localstack
    fi
    
    # Start LocalStack for Azure if not running
    if ! docker ps | grep -q "localstack-azure"; then
        print_info "Starting LocalStack for Azure..."
        docker run -d -p 4566:4566 -p 4571:4571 --name localstack-azure -e PROVIDER=azure localstack/localstack || {
            print_warning "Failed to start new LocalStack Azure container, checking if existing..."
            docker start localstack-azure 2>/dev/null || {
                print_error "Failed to start LocalStack for Azure"
                return 1
            }
        }
    else
        print_info "LocalStack for Azure is already running"
    fi
    
    print_success "Azure emulators environment ready"
}

# Main function
main() {
    # Set trap for cleanup on script exit
    trap cleanup_azure_emulators EXIT
    
    # Override the environment setup function
    setup_azure_emulators_environment || return 1
    
    # Run common main with custom environment
    print_header "Agentic Reconciliation Engine Quick Start - Azurite and LocalStack Azure"
    
    echo -e "${BLUE}Welcome to Agentic Reconciliation Engine!${NC}"
    echo ""
    
    # Check if we're in overlay mode
    if [[ "${OVERLAY_MODE:-false}" == "true" ]]; then
        echo -e "${YELLOW}Running in overlay mode${NC}"
    else
        echo -e "${YELLOW}This script sets up your Azure emulation development environment.${NC}"
    fi
    echo ""
    
    # Check if we're in the right directory
    if [[ ! -f "$REPO_ROOT/README.md" ]]; then
        print_error "Not in repository root. Please run from repository root."
        exit 1
    fi
    
    # Run pre-quickstart hook (overlay extension point)
    run_hooks "pre-quickstart" || return 1
    
    # Check prerequisites
    check_prerequisites
    
    # Setup basic configuration
    setup_basic_config
    
    # Skip examples if in overlay mode and requested
    if [[ "${OVERLAY_MODE:-false}" == "true" && "${QUICKSTART_SKIP_EXAMPLES:-false}" == "true" ]]; then
        print_info "Skipping example creation (overlay mode)"
    else
        # Create basic examples for non-overlay mode
        create_basic_examples
    fi
    
    # Run post-quickstart hook (overlay extension point)
    run_hooks "post-quickstart" || return 1
    
    # Deploy AI agents dashboard
    deploy_ai_agents_dashboard || return 1
    
    # Deploy AI Agent Skills and MCP servers
    deploy_ai_agent_skills || return 1
    
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    
    if [[ "${OVERLAY_MODE:-false}" == "true" ]]; then
        echo "1. Use overlay-manager.sh to manage overlays"
        echo "2. Create custom overlays with overlay-cli.py"
        echo "3. Deploy overlays to your cluster"
        echo "4. Monitor overlay status and logs"
        echo "5. Access your AI agents dashboard at http://localhost:8080"
        echo "6. Configure Claude Desktop with AI Agent Skills"
        echo ""
        echo -e "${GREEN}🚀 Overlay system and AI agents are ready on Azure emulation!${NC}"
    else
        echo "1. Use overlay-quickstart.sh to create and manage overlays"
        echo "2. Read docs/OVERLAY-QUICK-START.md for detailed guidance"
        echo "3. Check overlay/examples/ directory for sample configurations"
        echo "4. Access your AI agents dashboard at http://localhost:8080"
        echo "5. Configure Claude Desktop with AI Agent Skills (auto-configured)"
        echo ""
        echo -e "${GREEN}🚀 Azure emulation environment and AI agents are ready!${NC}"
        echo -e "${YELLOW}✨ AI Agent Skills are fully operational and ready for use!${NC}"
    fi
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

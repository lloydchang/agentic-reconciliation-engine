#!/bin/bash
# Agentic Reconciliation Engine - Overlay Quick Start Script (Local Minikube)
# Environment-specific overlay quickstart for local Minikube clusters

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
    echo "Agentic Reconciliation Engine - Overlay Quick Start (Local Minikube)"
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
    echo "  Overlay quick start for Agentic Reconciliation Engine on Minikube."
    echo "  Demonstrates overlay pattern where base script (quickstart-local-minikube.sh) is"
    echo "  extended without modification through environment variables and hooks."
    echo ""
    echo "  This includes:"
    echo "  - Minikube cluster startup and configuration"
    echo "  - Overlay environment setup and hooks creation"
    echo "  - Base quickstart execution with overlay extensions"
    echo "  - Example overlay creation and deployment"
    echo "  - AI Agent Skills deployment and configuration"
    echo ""
    echo "EXAMPLES:"
    echo "  $0 --all              # Complete Minikube overlay quick start"
    echo "  $0 --examples          # Create example overlays only"
    echo "  $0 --test              # Test overlay system only"
    echo "  $0 --deploy            # Deploy example overlay only"
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
    echo ""
    echo "OVERLAY CONCEPT:"
    echo "  1. Sets up overlay environment variables"
    echo "  2. Creates hook files that base quickstart will source"
    echo "  3. Runs base quickstart-local-minikube.sh (never modifying it)"
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
    print_header "Complete Overlay Quick Start - Minikube"
    
    # Setup overlay environment
    setup_overlay_environment || return 1
    
    # Create overlay hooks
    create_overlay_hooks || return 1
    
    # Run base quickstart with overlay extensions
    run_overlay_quickstart || return 1
    
    # Create overlay examples
    create_overlay_examples || return 1
    
    # Test overlay system
    test_overlay_system || return 1
    
    # Deploy example overlay
    deploy_example_overlay || return 1
    
    # Deploy AI Agent Skills and MCP servers
    deploy_ai_agent_skills || return 1
    
    print_success "Overlay quick start completed successfully!"
    echo ""
    echo -e "${BLUE}🎉 Overlay system is ready on Minikube!${NC}"
    echo -e "${YELLOW}📊 Your enhanced debug dashboard is running!${NC}"
    echo -e "${GREEN}🚀 Access it at: http://localhost:8080/dashboard${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Use overlay-manager.sh to manage overlays"
    echo "2. Create custom overlays with overlay-cli.py"
    echo "3. Deploy overlays to your cluster"
    echo "4. Monitor overlay status and logs"
    echo "5. Access your AI agents dashboard at http://localhost:8080"
    echo "6. Configure Claude Desktop with AI Agent Skills (auto-configured)"
    echo ""
    echo -e "${GREEN}🎉 Overlay system and AI agents are ready on Minikube!${NC}"
    echo -e "${YELLOW}📊 Your enhanced debug dashboard is running!${NC}"
    echo -e "${GREEN}🚀 Access it at: http://localhost:8080/dashboard${NC}"
    echo -e "${YELLOW}✨ AI Agent Skills are fully operational and ready for use!${NC}"
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

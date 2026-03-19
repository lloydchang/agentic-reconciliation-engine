#!/bin/bash
# Agentic Reconciliation Engine - Overlay Quick Start Script (Remote On-Premises)
# Environment-specific overlay quickstart for remote on-premises Kubernetes clusters

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
    echo "Agentic Reconciliation Engine - Overlay Quick Start (Remote On-Premises)"
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
    echo "  Overlay quick start for Agentic Reconciliation Engine on on-premises clusters."
    echo "  Demonstrates overlay pattern where base script (quickstart-remote-on-prem.sh) is"
    echo "  extended without modification through environment variables and hooks."
    echo ""
    echo "  This includes:"
    echo "  - On-premises cluster connection verification"
    echo "  - Overlay environment setup and hooks creation"
    echo "  - Base quickstart execution with overlay extensions"
    echo "  - Example overlay creation and deployment"
    echo "  - AI Agent Skills deployment and configuration"
    echo ""
    echo "EXAMPLES:"
    echo "  $0 --all              # Complete on-premises overlay quick start"
    echo "  $0 --examples          # Create example overlays only"
    echo "  $0 --test              # Test overlay system only"
    echo "  $0 --deploy            # Deploy example overlay only"
    echo ""
    echo "REQUIREMENTS:"
    echo "  - kubectl configured for on-premises cluster"
    echo "  - Network access to on-premises Kubernetes API"
    echo "  - kustomize, python3, git"
    echo "  - Appropriate cluster permissions"
    echo ""
    echo "ON-PREMISES CONFIGURATION:"
    echo "  - Uses existing kubeconfig configuration"
    echo "  - Verifies cluster accessibility"
    echo "  - Supports any on-premises Kubernetes distribution"
    echo "  - Works with custom certificate authorities"
    echo ""
    echo "OVERLAY CONCEPT:"
    echo "  1. Sets up overlay environment variables"
    echo "  2. Creates hook files that base quickstart will source"
    echo "  3. Runs base quickstart-remote-on-prem.sh (never modifying it)"
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
    print_header "Complete Overlay Quick Start - On-Premises"
    
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
    echo -e "${BLUE}🎉 Overlay system is ready on On-Premises!${NC}"
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
    echo -e "${GREEN}🎉 Overlay system and AI agents are ready on On-Premises!${NC}"
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

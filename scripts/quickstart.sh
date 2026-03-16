#!/bin/bash
# GitOps Infrastructure Control Plane - Quick Start Script
# Repository setup and initial onboarding

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script information
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Main quick start function
main() {
    print_header "GitOps Infrastructure Quick Start"
    
    echo -e "${BLUE}Welcome to GitOps Infrastructure Control Plane!${NC}"
    echo ""
    echo -e "${YELLOW}This script sets up your development environment.${NC}"
    echo ""
    
    # Check if we're in the right directory
    if [[ ! -f "$REPO_ROOT/README.md" ]]; then
        print_error "Not in repository root. Please run from repository root."
        exit 1
    fi
    
    print_info "Checking prerequisites..."
    
    # Check for required tools
    local missing_tools=()
    
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    if ! command -v kustomize &> /dev/null; then
        missing_tools+=("kustomize")
    fi
    
    if ! command -v python3 &> /dev/null; then
        missing_tools+=("python3")
    fi
    
    if ! command -v git &> /dev/null; then
        missing_tools+=("git")
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        echo -e "${YELLOW}Please install missing tools and try again.${NC}"
        exit 1
    fi
    
    print_success "All prerequisites satisfied"
    
    # Setup basic configuration
    print_info "Setting up development environment..."
    
    # Create basic directories if they don't exist
    mkdir -p logs/
    mkdir -p tmp/
    
    # Make scripts executable
    find "$SCRIPT_DIR" -name "*.sh" -exec chmod +x {} \;
    find "$SCRIPT_DIR" -name "*.py" -exec chmod +x {} \;
    
    print_success "Development environment ready"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Use overlay-quickstart.sh to create and manage overlays"
    echo "2. Read docs/OVERLAY-QUICK-START.md for detailed guidance"
    echo "3. Check examples/ directory for sample configurations"
    echo ""
    echo -e "${GREEN}🚀 Ready to start working with overlays!${NC}"
}

# Help function
show_help() {
    echo "GitOps Infrastructure Control Plane - Quick Start"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up the development environment for GitOps Infrastructure Control Plane."
    echo "  This includes tool verification, directory setup, and basic configuration."
    echo ""
    echo "  For overlay-specific operations, use: overlay-quickstart.sh"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                    # Setup development environment"
    echo "  overlay-quickstart.sh --help  # Get overlay management help"
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

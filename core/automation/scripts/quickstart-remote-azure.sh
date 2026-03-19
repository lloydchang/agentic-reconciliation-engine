#!/bin/bash
# Agentic Reconciliation Engine - Quick Start Script (Remote Azure)
# Environment-specific quickstart for remote Azure AKS clusters

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
    echo "Agentic Reconciliation Engine - Quick Start (Remote Azure)"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up development environment for Agentic Reconciliation Engine"
    echo "  using remote Azure AKS Kubernetes cluster."
    echo ""
    echo "  This includes:"
    echo "  - Azure CLI verification and authentication check"
    echo "  - AKS cluster access and configuration"
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
    echo "  $0                                    # Standard Azure setup with AI agents dashboard"
    echo "  OVERLAY_MODE=true $0                   # Setup with overlay extensions and AI agents dashboard"
    echo ""
    echo "REQUIREMENTS:"
    echo "  - Azure CLI installed and authenticated"
    echo "  - Valid Azure subscription with AKS access"
    echo "  - kubectl, kustomize, python3, git"
    echo "  - AKS cluster access (RBAC permissions)"
    echo ""
    echo "AZURE CONFIGURATION:"
    echo "  - Uses existing AKS cluster"
    echo "  - Automatic kubeconfig update recommended"
    echo "  - Subscription and resource group verification"
    echo ""
    echo "SETUP COMMANDS (if needed):"
    echo "  az login                                         # Authenticate to Azure"
    echo "  az account set --subscription <subscription-id>"
    echo "  az aks get-credentials --resource-group <group> --name <cluster>"
}

# Enhanced Azure setup with cluster information
setup_azure_environment() {
    print_info "Setting up Azure environment..."
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install Azure CLI first."
        print_info "Installation: brew install azure-cli"
        return 1
    fi
    
    # Check Azure login
    if ! az account show &> /dev/null; then
        print_error "Not logged into Azure. Please run 'az login'."
        return 1
    fi
    
    # Show Azure account information
    local azure_subscription=$(az account show --query 'name' -o tsv 2>/dev/null)
    local azure_tenant=$(az account show --query 'tenantId' -o tsv 2>/dev/null)
    print_success "Azure account verified: Subscription '$azure_subscription', Tenant $azure_tenant"
    
    # Check if kubectl is configured for AKS
    if ! kubectl cluster-info &> /dev/null; then
        print_warning "kubectl not configured for AKS cluster"
        print_info "Please update your kubeconfig:"
        echo "  az aks get-credentials --resource-group <resource-group> --name <cluster-name>"
        print_info "Or set KUBECONFIG environment variable to your AKS cluster"
    else
        # Show cluster information
        local cluster_context=$(kubectl config current-context 2>/dev/null)
        local cluster_info=$(kubectl cluster-info 2>/dev/null | head -1)
        print_success "Connected to cluster: $cluster_context"
        print_info "$cluster_info"
        
        # Try to get AKS cluster details if context suggests AKS
        if [[ "$cluster_context" == *"aks"* ]]; then
            local resource_group=$(az aks list --query "[?contains(name, '$(echo $cluster_context | cut -d'-' -f1)')].resourceGroup" -o tsv 2>/dev/null | head -1)
            if [[ -n "$resource_group" ]]; then
                local cluster_name=$(az aks list --query "[?contains(name, '$(echo $cluster_context | cut -d'-' -f1)')].name" -o tsv 2>/dev/null | head -1)
                if [[ -n "$cluster_name" ]]; then
                    print_info "AKS Cluster: $cluster_name (Resource Group: $resource_group)"
                fi
            fi
        fi
    fi
    
    print_success "Azure environment ready"
}

# Main function
main() {
    common_main "Azure"
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

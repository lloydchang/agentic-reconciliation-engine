#!/bin/bash
# Agentic Reconciliation Engine - Quick Start Script (Remote AWS)
# Environment-specific quickstart for remote AWS EKS clusters

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
    echo "Agentic Reconciliation Engine - Quick Start (Remote AWS)"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up development environment for Agentic Reconciliation Engine"
    echo "  using remote AWS EKS Kubernetes cluster."
    echo ""
    echo "  This includes:"
    echo "  - AWS CLI verification and credential checking"
    echo "  - EKS cluster access and configuration"
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
    echo "  $0                                    # Standard AWS setup with AI agents dashboard"
    echo "  OVERLAY_MODE=true $0                   # Setup with overlay extensions and AI agents dashboard"
    echo ""
    echo "REQUIREMENTS:"
    echo "  - AWS CLI installed and configured"
    echo "  - Valid AWS credentials with EKS access"
    echo "  - kubectl, kustomize, python3, git"
    echo "  - EKS cluster access (IAM permissions)"
    echo ""
    echo "AWS CONFIGURATION:"
    echo "  - Uses existing EKS cluster"
    echo "  - Automatic kubeconfig update recommended"
    echo "  - IAM role/permissions verification"
    echo ""
    echo "SETUP COMMANDS (if needed):"
    echo "  aws configure                                    # Set up AWS credentials"
    echo "  aws eks update-kubeconfig --region <region> --name <cluster>"
}

# Enhanced AWS setup with cluster information
setup_aws_environment() {
    print_info "Setting up AWS environment..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install AWS CLI first."
        print_info "Installation: brew install awscli"
        return 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure'."
        return 1
    fi
    
    # Show AWS identity information
    local aws_identity=$(aws sts get-caller-identity --query 'Account' --output text 2>/dev/null)
    local aws_region=$(aws configure get region 2>/dev/null || echo "us-east-1")
    print_success "AWS identity verified: Account $aws_identity, Region $aws_region"
    
    # Check if kubectl is configured for EKS
    if ! kubectl cluster-info &> /dev/null; then
        print_warning "kubectl not configured for EKS cluster"
        print_info "Please update your kubeconfig:"
        echo "  aws eks update-kubeconfig --region <region> --name <cluster-name>"
        print_info "Or set KUBECONFIG environment variable to your EKS cluster"
    else
        # Show cluster information
        local cluster_context=$(kubectl config current-context 2>/dev/null)
        local cluster_info=$(kubectl cluster-info 2>/dev/null | head -1)
        print_success "Connected to cluster: $cluster_context"
        print_info "$cluster_info"
    fi
    
    print_success "AWS environment ready"
}

# Main function
main() {
    common_main "AWS"
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

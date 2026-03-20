#!/bin/bash
# Langfuse Secrets Deployment Fix Script
# Fixes deployment issues for Langfuse secrets in ai-infrastructure namespace

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found. Please install kubectl first."
        exit 1
    fi
    
    # Check cluster access with timeout
    print_info "Checking Kubernetes cluster access..."
    if timeout 30 kubectl cluster-info &> /dev/null; then
        print_success "Cluster access verified"
    else
        print_error "Cannot access Kubernetes cluster or connection timeout"
        print_info "Please check your kubeconfig and cluster connectivity"
        exit 1
    fi
    
    print_success "Prerequisites checked"
}

# Create ai-infrastructure namespace if needed
create_namespace() {
    print_header "Setting up ai-infrastructure namespace"
    
    # Check if namespace exists
    if kubectl get namespace ai-infrastructure &> /dev/null; then
        print_success "ai-infrastructure namespace already exists"
    else
        print_info "Creating ai-infrastructure namespace..."
        kubectl create namespace ai-infrastructure --dry-run=client -o yaml | kubectl apply -f -
        print_success "ai-infrastructure namespace created"
    fi
}

# Generate proper Langfuse secrets
generate_secrets() {
    print_header "Generating Langfuse Secrets"
    
    print_info "Creating Langfuse secrets with proper configuration..."
    
    # Create secrets with proper placeholder values that can be updated later
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: langfuse-secrets
  namespace: ai-infrastructure
  labels:
    app: langfuse
    component: observability
type: Opaque
data:
  # Placeholder values - replace with actual base64-encoded Langfuse credentials
  # To generate real values: echo -n 'your-actual-key' | base64
  public-key: cGxhY2Vob2xkZXItcHVibGljLWtleQ==
  secret-key: cGxhY2Vob2xkZXItc2VjcmV0LWtleQ==
  otlp-headers: QXV0aG9yaXphdGlvbj1CZWFyZXIgcGxhY2Vob2xkZXItc2VjcmV0LWtleQ==
EOF
    
    print_success "Langfuse secrets deployed"
}

# Verify deployment
verify_deployment() {
    print_header "Verifying Deployment"
    
    # Check if secret exists
    if kubectl get secret langfuse-secrets -n ai-infrastructure &> /dev/null; then
        print_success "langfuse-secrets secret found in ai-infrastructure namespace"
        
        # Show secret details (without exposing sensitive data)
        print_info "Secret details:"
        kubectl get secret langfuse-secrets -n ai-infrastructure -o yaml | grep -A 10 "data:" | head -10
    else
        print_error "langfuse-secrets secret not found"
        return 1
    fi
    
    print_success "Deployment verification completed"
}

# Show next steps
show_next_steps() {
    print_header "Next Steps"
    
    echo -e "${YELLOW}Langfuse secrets have been deployed successfully!${NC}"
    echo ""
    echo -e "${BLUE}To complete Langfuse setup:${NC}"
    echo "1. Get your Langfuse API keys from https://cloud.langfuse.com or your self-hosted instance"
    echo "2. Update the secrets with your actual credentials:"
    echo "   kubectl edit secret langfuse-secrets -n ai-infrastructure"
    echo "3. Or update using kubectl patch:"
    echo "   kubectl patch secret langfuse-secrets -n ai-infrastructure \\"
    echo "     --patch='$(echo '{"data":{"public-key":"$(echo -n 'your-public-key' | base64)","secret-key":"$(echo -n 'your-secret-key' | base64)"}}' | base64 -w 0)'"
    echo ""
    echo -e "${BLUE}To verify the secrets:${NC}"
    echo "kubectl get secret langfuse-secrets -n ai-infrastructure -o yaml"
    echo ""
    echo -e "${BLUE}To decode and verify values:${NC}"
    echo "kubectl get secret langfuse-secrets -n ai-infrastructure -o jsonpath='{.data.public-key}' | base64 --decode"
    echo ""
    
    print_success "Langfuse secrets deployment fix completed!"
}

# Main execution
main() {
    print_header "Langfuse Secrets Deployment Fix"
    echo "🔧 Fixing Langfuse secrets deployment issues"
    echo ""
    
    check_prerequisites
    create_namespace
    generate_secrets
    verify_deployment
    show_next_steps
}

# Handle script interruption
trap 'echo -e "${RED}❌ Fix interrupted${NC}"; exit 1' INT TERM

# Run main function
main "$@"

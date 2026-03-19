#!/bin/bash

# Flux Auto Setup Script
# Automated setup of Flux CD with Qwen LLM and K8sGPT integration

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default configuration
DEFAULT_PROVIDER="github"
DEFAULT_REPOSITORY="agentic-reconciliation-engine"
DEFAULT_OWNER="lloydchang"
DEFAULT_BRANCH="main"
DEFAULT_PATH="./clusters/production"
DEFAULT_NAMESPACE="flux-system"
DEFAULT_ENVIRONMENT="development"

# Script configuration
PROVIDER="${PROVIDER:-$DEFAULT_PROVIDER}"
REPOSITORY="${REPOSITORY:-$DEFAULT_REPOSITORY}"
OWNER="${OWNER:-$DEFAULT_OWNER}"
BRANCH="${BRANCH:-$DEFAULT_BRANCH}"
PATH="${PATH:-$DEFAULT_PATH}"
NAMESPACE="${NAMESPACE:-$DEFAULT_NAMESPACE}"
ENVIRONMENT="${ENVIRONMENT:-$DEFAULT_ENVIRONMENT}"
WITH_QWEN="${WITH_QWEN:-true}"
WITH_MONITORING="${WITH_MONITORING:-true}"
WITH_SECRETS="${WITH_SECRETS:-true}"
AUTO_APPROVE="${AUTO_APPROVE:-false}"
DRY_RUN="${DRY_RUN:-false}"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Show banner
show_banner() {
    echo -e "${CYAN}"
    echo "=================================================="
    echo "    Flux CD Auto Setup with Qwen Integration"
    echo "=================================================="
    echo -e "${NC}"
    echo "This script will automatically set up Flux CD with:"
    echo "• Qwen LLM integration for intelligent analysis"
    echo "• K8sGPT for automated Kubernetes operations"
    echo "• Comprehensive monitoring and observability"
    echo "• Multi-environment support"
    echo "• Automated testing and validation"
    echo ""
}

# Show help
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

OPTIONS:
    --provider PROVIDER        Git provider (github, gitlab, bitbucket) [default: github]
    --repository REPO          Repository name [default: agentic-reconciliation-engine]
    --owner OWNER              Repository owner/organization [default: lloydchang]
    --branch BRANCH            Git branch [default: main]
    --path PATH                Path in repository for Flux manifests [default: ./clusters/production]
    --namespace NAMESPACE      Kubernetes namespace for Flux [default: flux-system]
    --environment ENV          Target environment (development, staging, production) [default: development]
    --with-qwen                Enable Qwen LLM integration [default: true]
    --with-monitoring          Enable monitoring stack [default: true]
    --with-secrets             Enable secret management [default: true]
    --auto-approve            Auto-approve all prompts [default: false]
    --dry-run                 Show what would be done without executing [default: false]
    --help                    Show this help message

EXAMPLES:
    $0 --provider github --owner myorg --repository my-infra --environment production
    $0 --with-qwen --with-monitoring --auto-approve
    $0 --dry-run --environment staging

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --provider)
                PROVIDER="$2"
                shift 2
                ;;
            --repository)
                REPOSITORY="$2"
                shift 2
                ;;
            --owner)
                OWNER="$2"
                shift 2
                ;;
            --branch)
                BRANCH="$2"
                shift 2
                ;;
            --path)
                PATH="$2"
                shift 2
                ;;
            --namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --with-qwen)
                WITH_QWEN="$2"
                shift 2
                ;;
            --with-monitoring)
                WITH_MONITORING="$2"
                shift 2
                ;;
            --with-secrets)
                WITH_SECRETS="$2"
                shift 2
                ;;
            --auto-approve)
                AUTO_APPROVE="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN="$2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check for required tools
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    if ! command -v flux &> /dev/null; then
        missing_tools+=("flux")
    fi
    
    if ! command -v git &> /dev/null; then
        missing_tools+=("git")
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install the missing tools and try again."
        exit 1
    fi
    
    # Check Kubernetes connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        log_info "Please check your kubeconfig and try again."
        exit 1
    fi
    
    # Check cluster permissions
    if ! kubectl auth can-i create namespaces &> /dev/null; then
        log_error "Insufficient permissions to create namespaces"
        log_info "Please ensure you have cluster-admin permissions."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Install Flux CLI if not present
install_flux_cli() {
    if ! command -v flux &> /dev/null; then
        log_step "Installing Flux CLI..."
        
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would install Flux CLI"
            return
        fi
        
        curl -sSL https://fluxcd.io/install.sh | sudo bash
        export PATH=$PATH:/usr/local/bin
        
        if command -v flux &> /dev/null; then
            log_success "Flux CLI installed successfully"
        else
            log_error "Failed to install Flux CLI"
            exit 1
        fi
    else
        log_info "Flux CLI already installed"
    fi
}

# Setup repository structure
setup_repository_structure() {
    log_step "Setting up repository structure..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create repository structure"
        return
    fi
    
    # Create necessary directories
    mkdir -p "clusters/$ENVIRONMENT/flux-system"
    mkdir -p "core/gitops/flux-system"
    mkdir -p "overlays/flux-system/$ENVIRONMENT"
    mkdir -p "core/resources/tenants/{1-network,2-clusters,3-workloads}"
    mkdir -p "core/operators"
    mkdir -p "core/ai/{skills,runtime}"
    mkdir -p "tests"
    mkdir -p "scripts"
    
    log_success "Repository structure created"
}

# Bootstrap Flux
bootstrap_flux() {
    log_step "Bootstrapping Flux..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would bootstrap Flux with:"
        log_info "  Provider: $PROVIDER"
        log_info "  Repository: $OWNER/$REPOSITORY"
        log_info "  Branch: $BRANCH"
        log_info "  Path: $PATH"
        log_info "  Namespace: $NAMESPACE"
        return
    fi
    
    local bootstrap_cmd="flux bootstrap $PROVIDER"
    bootstrap_cmd+=" --owner=$OWNER"
    bootstrap_cmd+=" --repository=$REPOSITORY"
    bootstrap_cmd+=" --branch=$BRANCH"
    bootstrap_cmd+=" --path=$PATH"
    bootstrap_cmd+=" --namespace=$NAMESPACE"
    
    # Add provider-specific options
    case $PROVIDER in
        github)
            bootstrap_cmd+=" --personal"
            bootstrap_cmd+=" --ssh-key-algorithm=ed25519"
            ;;
        gitlab)
            bootstrap_cmd+=" --token-auth"
            ;;
        bitbucket)
            bootstrap_cmd+=" --ssh-key-algorithm=ed25519"
            ;;
    esac
    
    if [[ "$AUTO_APPROVE" == "true" ]]; then
        bootstrap_cmd+=" --silent"
    fi
    
    log_info "Running: $bootstrap_cmd"
    
    if eval "$bootstrap_cmd"; then
        log_success "Flux bootstrap completed"
    else
        log_error "Flux bootstrap failed"
        exit 1
    fi
}

# Setup Qwen LLM integration
setup_qwen_integration() {
    if [[ "$WITH_QWEN" != "true" ]]; then
        log_info "Skipping Qwen integration"
        return
    fi
    
    log_step "Setting up Qwen LLM integration..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would setup Qwen LLM integration"
        return
    fi
    
    # Apply Qwen manifests
    if kubectl apply -f core/gitops/flux-system/qwen-integration.yaml; then
        log_success "Qwen LLM integration manifests applied"
    else
        log_error "Failed to apply Qwen manifests"
        exit 1
    fi
    
    # Wait for Qwen deployment
    log_info "Waiting for Qwen LLM deployment to be ready..."
    if kubectl wait --for=condition=available deployment/qwen-llm -n qwen-system --timeout=300s; then
        log_success "Qwen LLM deployment is ready"
    else
        log_warning "Qwen LLM deployment not ready within timeout"
    fi
}

# Setup K8sGPT
setup_k8sgpt() {
    if [[ "$WITH_QWEN" != "true" ]]; then
        log_info "Skipping K8sGPT setup (requires Qwen)"
        return
    fi
    
    log_step "Setting up K8sGPT..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would setup K8sGPT"
        return
    fi
    
    # Apply K8sGPT manifests
    if kubectl apply -f core/gitops/flux-system/k8sgpt-qwen.yaml; then
        log_success "K8sGPT manifests applied"
    else
        log_error "Failed to apply K8sGPT manifests"
        exit 1
    fi
    
    # Wait for K8sGPT deployment
    log_info "Waiting for K8sGPT deployment to be ready..."
    if kubectl wait --for=condition=available deployment/k8sgpt -n flux-system --timeout=300s; then
        log_success "K8sGPT deployment is ready"
    else
        log_warning "K8sGPT deployment not ready within timeout"
    fi
}

# Setup monitoring
setup_monitoring() {
    if [[ "$WITH_MONITORING" != "true" ]]; then
        log_info "Skipping monitoring setup"
        return
    fi
    
    log_step "Setting up monitoring..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would setup monitoring"
        return
    fi
    
    # Apply monitoring manifests
    if kubectl apply -f core/gitops/flux-system/monitoring.yaml; then
        log_success "Monitoring manifests applied"
    else
        log_error "Failed to apply monitoring manifests"
        exit 1
    fi
    
    log_success "Monitoring setup completed"
}

# Setup secret management
setup_secrets() {
    if [[ "$WITH_SECRETS" != "true" ]]; then
        log_info "Skipping secret management setup"
        return
    fi
    
    log_step "Setting up secret management..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would setup secret management"
        return
    fi
    
    # Check if SOPS is installed
    if ! command -v sops &> /dev/null; then
        log_warning "SOPS not found, installing..."
        if command -v brew &> /dev/null; then
            brew install sops
        elif command -v go &> /dev/null; then
            go install github.com/getsops/sops/v3/cmd/sops@latest
        else
            log_warning "Cannot install SOPS automatically, please install it manually"
            return
        fi
    fi
    
    # Generate age key for encryption
    if ! command -v age &> /dev/null; then
        log_warning "age not found, installing..."
        if command -v brew &> /dev/null; then
            brew install age
        elif command -v go &> /dev/null; then
            go install filippo.io/age/cmd/age@latest
        else
            log_warning "Cannot install age automatically, please install it manually"
            return
        fi
    fi
    
    # Generate key if not exists
    if [[ ! -f "age.key" ]]; then
        age-keygen -o age.key
        log_success "Age key generated"
    fi
    
    log_success "Secret management setup completed"
}

# Configure environment-specific settings
configure_environment() {
    log_step "Configuring environment: $ENVIRONMENT"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would configure $ENVIRONMENT environment"
        return
    fi
    
    # Apply environment-specific overlay
    if [[ -d "overlays/flux-system/$ENVIRONMENT" ]]; then
        if kubectl apply -k "overlays/flux-system/$ENVIRONMENT"; then
            log_success "Environment $ENVIRONMENT configured"
        else
            log_error "Failed to configure environment $ENVIRONMENT"
            exit 1
        fi
    else
        log_warning "Environment overlay not found: overlays/flux-system/$ENVIRONMENT"
    fi
}

# Verify installation
verify_installation() {
    log_step "Verifying installation..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would verify installation"
        return
    fi
    
    # Run Flux check
    if flux check --namespace "$NAMESPACE"; then
        log_success "Flux verification passed"
    else
        log_error "Flux verification failed"
        return 1
    fi
    
    # Check deployments
    local deployments=("source-controller" "kustomize-controller" "helm-controller" "notification-controller")
    local all_healthy=true
    
    for deployment in "${deployments[@]}"; do
        if kubectl get deployment "$deployment" -n "$NAMESPACE" --no-headers | grep -q "Running"; then
            log_success "$deployment is healthy"
        else
            log_error "$deployment is not healthy"
            all_healthy=false
        fi
    done
    
    if [[ "$WITH_QWEN" == "true" ]]; then
        if kubectl get deployment qwen-llm -n qwen-system --no-headers | grep -q "Running"; then
            log_success "Qwen LLM is healthy"
        else
            log_warning "Qwen LLM is not healthy"
        fi
    fi
    
    if [[ "$all_healthy" == "true" ]]; then
        log_success "All components are healthy"
    else
        log_warning "Some components are not healthy"
    fi
}

# Run tests
run_tests() {
    log_step "Running integration tests..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would run integration tests"
        return
    fi
    
    # Run Flux tests
    if ./tests/flux-comprehensive-test.sh; then
        log_success "Flux tests passed"
    else
        log_warning "Some Flux tests failed"
    fi
    
    # Run Qwen tests if enabled
    if [[ "$WITH_QWEN" == "true" ]]; then
        if ./tests/qwen-integration-test.sh; then
            log_success "Qwen integration tests passed"
        else
            log_warning "Some Qwen integration tests failed"
        fi
    fi
}

# Show summary
show_summary() {
    log_step "Setup Summary"
    echo ""
    echo "Flux CD has been successfully set up with the following configuration:"
    echo "• Provider: $PROVIDER"
    echo "• Repository: $OWNER/$REPOSITORY"
    echo "• Branch: $BRANCH"
    echo "• Path: $PATH"
    echo "• Namespace: $NAMESPACE"
    echo "• Environment: $ENVIRONMENT"
    echo "• Qwen Integration: $WITH_QWEN"
    echo "• Monitoring: $WITH_MONITORING"
    echo "• Secret Management: $WITH_SECRETS"
    echo ""
    echo "Next steps:"
    echo "1. Check Flux status: flux get all"
    echo "2. Verify deployments: kubectl get deployments -n $NAMESPACE"
    echo "3. Access monitoring: kubectl port-forward svc/grafana 3000:3000 -n monitoring"
    echo "4. Run tests: ./tests/flux-comprehensive-test.sh"
    echo ""
    
    if [[ "$WITH_QWEN" == "true" ]]; then
        echo "Qwen-specific next steps:"
        echo "1. Test Qwen API: kubectl port-forward svc/qwen-llm 8000:8000 -n qwen-system"
        echo "2. Check K8sGPT: kubectl logs -n $NAMESPACE deployment/k8sgpt"
        echo "3. Run Qwen tests: ./tests/qwen-integration-test.sh"
        echo ""
    fi
    
    echo "Documentation:"
    echo "• Flux Guide: docs/FLUX-COMPLETE-GUIDE.md"
    echo "• Qwen Integration: docs/QWEN-INTEGRATION.md"
    echo "• Troubleshooting: docs/TROUBLESHOOTING.md"
    echo ""
}

# Main execution
main() {
    show_banner
    
    # Parse arguments
    parse_args "$@"
    
    # Show configuration
    log_info "Configuration:"
    log_info "  Provider: $PROVIDER"
    log_info "  Repository: $OWNER/$REPOSITORY"
    log_info "  Branch: $BRANCH"
    log_info "  Path: $PATH"
    log_info "  Namespace: $NAMESPACE"
    log_info "  Environment: $ENVIRONMENT"
    log_info "  Qwen Integration: $WITH_QWEN"
    log_info "  Monitoring: $WITH_MONITORING"
    log_info "  Secret Management: $WITH_SECRETS"
    log_info "  Auto Approve: $AUTO_APPROVE"
    log_info "  Dry Run: $DRY_RUN"
    echo ""
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "Running in dry-run mode - no changes will be made"
        echo ""
    fi
    
    # Confirmation prompt
    if [[ "$AUTO_APPROVE" != "true" && "$DRY_RUN" != "true" ]]; then
        echo -e "${YELLOW}This will set up Flux CD with the above configuration.${NC}"
        read -p "Do you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Setup cancelled by user"
            exit 0
        fi
    fi
    
    # Execute setup steps
    check_prerequisites
    install_flux_cli
    setup_repository_structure
    bootstrap_flux
    setup_qwen_integration
    setup_k8sgpt
    setup_monitoring
    setup_secrets
    configure_environment
    verify_installation
    run_tests
    show_summary
    
    log_success "Flux CD setup with Qwen integration completed! 🎉"
}

# Run main function
main "$@"

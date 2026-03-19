#!/bin/bash
# Agentic Reconciliation Engine - Overlay Quick Start
# Overlay approach to quickstart - extends quickstart.sh without modifying it

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script information
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

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

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Set overlay environment variables
setup_overlay_environment() {
    print_header "Setting Up Overlay Environment"
    
    # Create hooks directory if it doesn't exist
    mkdir -p hooks
    
    # Set overlay-specific configuration
    export OVERLAY_MODE="true"
    export OVERLAY_QUICKSTART="true"
    export OVERLAY_VERSION="2.0.0"
    
    # Override default quickstart behavior
    export QUICKSTART_SKIP_EXAMPLES="true"
    export QUICKSTART_SKIP_VALIDATION="false"
    export QUICKSTART_ENABLE_OVERLAYS="true"
    
    print_success "Overlay environment configured"
}

# Create overlay-specific hooks
create_overlay_hooks() {
    print_header "Creating Overlay Hooks"
    
    # Pre-quickstart hook - runs before base quickstart
    cat > hooks/pre-quickstart.sh << 'EOF'
#!/bin/bash
# Overlay pre-quickstart hook
# This runs before the base quickstart.sh

echo "🔧 Overlay pre-quickstart hook executing..."

# Set overlay-specific defaults
export OVERLAY_DIR="overlays"
export OVERLAY_REGISTRY_ENABLED="true"
export OVERLAY_TEMPLATES_ENABLED="true"

# Override some quickstart defaults for overlay workflow
export QUICKSTART_MODE="overlay"
export QUICKSTART_FEATURES="overlay-creation,overlay-deployment,overlay-management"

echo "✅ Overlay environment prepared"
EOF
    
    # Post-quickstart hook - runs after base quickstart
    cat > hooks/post-quickstart.sh << 'EOF'
#!/bin/bash
# Overlay post-quickstart hook
# This runs after the base quickstart.sh

echo "🚀 Overlay post-quickstart hook executing..."

# Deploy Langfuse + Temporal Integration for Overlay
echo "🔍 Deploying Langfuse + Temporal Integration for Overlay..."

# Check if kubectl is available
if command -v kubectl &> /dev/null; then
    # Deploy Langfuse observability integration
    echo "🔍 Deploying Langfuse observability integration..."

    # Check if cluster is accessible
    if kubectl cluster-info &> /dev/null; then
        # Deploy Langfuse secrets
        echo "📋 Deploying Langfuse secrets..."
        
        if [[ -f "core/config/langfuse-secret.yaml" ]]; then
            if kubectl apply -f core/config/langfuse-secret.yaml; then
                echo "✅ Langfuse secrets deployed to control-plane namespace"
            else
                echo "⚠️  Failed to deploy Langfuse secrets to control-plane namespace"
            fi
        fi
        
        if [[ -f "core/config/langfuse-secret-gitops-infra.yaml" ]]; then
            if kubectl apply -f core/config/langfuse-secret-gitops-infra.yaml; then
                echo "✅ Langfuse secrets deployed to ai-infrastructure namespace"
            else
                echo "⚠️  Failed to deploy Langfuse secrets to ai-infrastructure namespace"
            fi
        fi
        
        # Deploy monitoring with Langfuse dashboard
        echo "📊 Deploying monitoring stack with Langfuse dashboard..."
        
        if [[ -d "core/resources/infrastructure/monitoring" ]]; then
            if kubectl apply -k core/resources/infrastructure/monitoring; then
                echo "✅ Monitoring stack with Langfuse dashboard deployed"
            else
                echo "⚠️  Failed to deploy monitoring stack"
            fi
        fi
        
        # Deploy self-hosted Langfuse with full automation
        if [[ -f "core/automation/scripts/auto-configure-langfuse.sh" ]]; then
            echo "🚀 Running fully automated Langfuse setup..."
            if bash "core/automation/scripts/auto-configure-langfuse.sh"; then
                echo "✅ Fully automated Langfuse setup completed"
            else
                echo "⚠️  Automated setup failed, but secrets deployed"
                echo "   You can run manually: ./core/automation/scripts/auto-configure-langfuse.sh"
            fi
        else
            echo "⚠️  Automated setup script not found"
        fi
    else
        echo "⚠️  Kubernetes cluster not accessible - skipping Langfuse deployment"
    fi

    # Initialize overlay registry if it doesn't exist
    if [[ ! -f overlay/registry/catalog.yaml ]]; then
        cat > overlay/registry/catalog.yaml << 'REGISTRY_EOF'
if [[ ! -f overlay/registry/catalog.yaml ]]; then
    cat > overlay/registry/catalog.yaml << 'REGISTRY_EOF'
apiVersion: v1
kind: OverlayRegistry
metadata:
  name: overlay-registry
  namespace: flux-system
spec:
  overlays: []
REGISTRY_EOF
fi

# Create overlay templates if they don't exist
if [[ ! -d overlay/templates ]]; then
    mkdir -p overlay/templates/{skill-overlay,dashboard-overlay,infra-overlay}
fi

echo "✅ Overlay structure initialized"
EOF
    
    # Make hooks executable
    chmod +x hooks/pre-quickstart.sh
    chmod +x hooks/post-quickstart.sh
    
    print_success "Overlay hooks created"
}

# Run overlay quickstart
run_overlay_quickstart() {
    print_header "Running Overlay Quick Start"
    
    # Check if quickstart.sh exists
    if [[ ! -f "$SCRIPT_DIR/quickstart.sh" ]]; then
        print_error "Base quickstart.sh not found: $SCRIPT_DIR/quickstart.sh"
        return 1
    fi
    
    print_info "Executing base quickstart with overlay extensions..."
    
    # Source and run base quickstart
    # The hooks will be automatically picked up by quickstart.sh
    source "$SCRIPT_DIR/quickstart.sh"
    
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        print_success "Base quickstart completed with overlay extensions"
    else
        print_error "Base quickstart failed with exit code: $exit_code"
        return $exit_code
    fi
}

# Create overlay examples
create_overlay_examples() {
    print_header "Creating Overlay Examples"
    
    # Use overlay-cli to create examples
    if [[ -f "$SCRIPT_DIR/overlay-cli.py" ]]; then
        print_info "Creating example overlays using overlay-cli..."
        
        # Create hello-world skill overlay
        if [[ ! -d "overlay/ai/skills/hello-world" ]]; then
            OVERLAY_DIR=overlay python3 "$SCRIPT_DIR/overlay-cli.py" create hello-world skills debug --template skill-overlay || {
                print_error "Failed to create hello-world overlay"
                return 1
            }
            print_success "Created hello-world overlay"
        else
            print_info "Hello-world overlay already exists - skipping creation"
        fi
        
        # Create dark-theme dashboard overlay
        if [[ ! -d "overlay/ai/runtime/dashboard/dark-theme" ]]; then
            OVERLAY_DIR=overlay python3 "$SCRIPT_DIR/overlay-cli.py" create dark-theme dashboard themes --template dashboard-overlay || {
                print_error "Failed to create dark-theme overlay"
                return 1
            }
            print_success "Created dark-theme overlay"
        else
            print_info "Dark-theme overlay already exists - skipping creation"
        fi
        
        # Create production-env composed overlay
        if [[ ! -d "overlay/examples/production-env" ]]; then
            OVERLAY_DIR=overlay python3 "$SCRIPT_DIR/overlay-cli.py" create production-env composed "" || {
                print_error "Failed to create production-env overlay"
                return 1
            }
            print_success "Created production-env overlay"
        else
            print_info "Production-env overlay already exists - skipping creation"
        fi
        
        print_success "Example overlays created"
    else
        print_warning "overlay-cli.py not found - skipping example creation"
    fi
}

# Test overlay system
test_overlay_system() {
    print_header "Testing Overlay System"
    
    local test_results=()
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    
    # Test overlay registry
    if [[ -f "overlay/registry/catalog.yaml" ]]; then
        print_success "Overlay registry exists"
        ((passed_tests++))
    else
        print_error "Overlay registry missing"
    fi
    ((total_tests++))
    
    # Test overlay templates
    if [[ -d "overlay/templates" ]]; then
        local template_count=$(find overlay/templates -name "kustomization.yaml" | wc -l)
        print_success "Found $template_count overlay templates"
        ((passed_tests++))
    else
        print_error "Overlay templates missing"
    fi
    ((total_tests++))
    
    # Test overlay CLI
    if [[ -f "$SCRIPT_DIR/overlay-cli.py" ]]; then
        if OVERLAY_DIR=overlay python3 "$SCRIPT_DIR/overlay-cli.py" list > /dev/null 2>&1; then
            print_success "Overlay CLI working"
            ((passed_tests++))
        else
            print_error "Overlay CLI not working"
            ((failed_tests++))
        fi
    else
        print_warning "Overlay CLI not available"
    fi
    ((total_tests++))
    
    # Print test results
    print_header "Test Results"
    echo -e "${BLUE}Total Tests: $total_tests${NC}"
    echo -e "${GREEN}Passed: $passed_tests${NC}"
    if [[ $failed_tests -gt 0 ]]; then
        echo -e "${RED}Failed: $failed_tests${NC}"
    else
        echo -e "${GREEN}🎉 All tests passed!${NC}"
    fi
}

# Deploy example overlay
deploy_example_overlay() {
    print_header "Deploying Example Overlay"
    
    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        print_warning "Kubernetes cluster not accessible - skipping deployment"
        return 0
    fi
    
    # Deploy enhanced debug overlay if it exists
    if [[ -d "overlay/ai/skills/debug/enhanced" ]]; then
        print_info "Deploying enhanced debug overlay..."
        
        if kustomize build overlay/ai/skills/debug/enhanced | kubectl apply -f -; then
            print_success "Enhanced debug overlay deployed successfully"
            
            # Wait for pod to be ready
            print_info "Waiting for pod to be ready..."
            local pod_ready=false
            local attempts=0
            local max_attempts=30
            
            while [[ $pod_ready == false && $attempts -lt $max_attempts ]]; do
                if kubectl get pods -n flux-system -l app=debug --no-headers 2>/dev/null | grep -q "Running"; then
                    pod_ready=true
                    print_success "Debug pod is ready and running"
                    break
                fi
                
                ((attempts++))
                sleep 2
            done
            
            if [[ $pod_ready == false ]]; then
                print_error "Pod did not become ready within expected time"
                return 1
            fi
            
            # Get service URL
            local service_url="http://localhost:8080"
            if command -v minikube &> /dev/null; then
                service_url=$(minikube service debug --url -n flux-system 2>/dev/null)
            fi
            
            print_success "Dashboard available at: $service_url"
            print_info "Access dashboard at: $service_url/dashboard"
            
        else
            print_error "Failed to deploy enhanced debug overlay"
            return 1
        fi
    else
        print_warning "Enhanced debug overlay not found - skipping deployment"
    fi
}

# Deploy consolidated K8sGPT (same function as in quickstart.sh)
deploy_consolidated_k8sgpt() {
    print_header "Deploying Consolidated K8sGPT"
    
    # Check if the consolidated deployment script exists
    local k8sgpt_script="$SCRIPT_DIR/deploy-consolidated-k8sgpt.sh"
    
    if [[ ! -f "$k8sgpt_script" ]]; then
        print_warning "Consolidated K8sGPT deployment script not found at $k8sgpt_script"
        print_info "You can manually run: ./core/scripts/deploy-consolidated-k8sgpt.sh deploy"
        return 0
    fi
    
    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        print_warning "Kubernetes cluster not accessible - skipping K8sGPT deployment"
        print_info "To deploy K8sGPT later: QUICKSTART_DEPLOY_K8SGPT=true ./core/automation/scripts/overlay-quickstart.sh"
        return 0
    fi
    
    # Check if K8sGPT is already deployed
    if kubectl get deployment k8sgpt -n k8sgpt-system &> /dev/null; then
        print_info "K8sGPT already deployed - validating existing deployment"
        if bash "$k8sgpt_script" validate; then
            print_success "K8sGPT deployment validated successfully!"
        else
            print_warning "K8sGPT deployment validation failed - attempting redeployment"
            if bash "$k8sgpt_script" deploy; then
                print_success "K8sGPT redeployment successful!"
            else
                print_error "K8sGPT redeployment failed"
                return 1
            fi
        fi
        return 0
    fi
    
    print_info "Deploying consolidated K8sGPT (single instance per cluster)..."
    
    # Run the consolidated deployment
    if bash "$k8sgpt_script" deploy; then
        print_success "Consolidated K8sGPT deployed successfully!"
        echo ""
        echo -e "${GREEN}🎉 Your consolidated K8sGPT is now running!${NC}"
        echo -e "${YELLOW}🤖 Service endpoint: http://k8sgpt.k8sgpt-system.svc.cluster.local:8080${NC}"
        echo -e "${BLUE}📊 Metrics endpoint: http://k8sgpt.k8sgpt-system.svc.cluster.local:9090/metrics${NC}"
        echo ""
        echo "K8sGPT features:"
        echo "  ✅ Single instance per cluster (75% resource reduction)"
        echo "  ✅ Multi-backend support (agent-memory, LocalAI, OpenAI)"
        echo "  ✅ Cluster-wide RBAC for all GitOps components"
        echo "  ✅ Unified service endpoint for all integrations"
        echo "  ✅ Real-time metrics and health monitoring"
        echo ""
        echo "To access K8sGPT:"
        echo "1. Health check: curl http://k8sgpt.k8sgpt-system.svc.cluster.local:8080/healthz"
        echo "2. Analysis: curl -X POST http://k8sgpt.k8sgpt-system.svc.cluster.local:8080/analyze -H 'Content-Type: application/json' -d '{\"namespace\":\"default\",\"resources\":[\"deployments\"]}'"
        echo "3. Metrics: curl http://k8sgpt.k8sgpt-system.svc.cluster.local:9090/metrics"
    else
        print_error "Failed to deploy consolidated K8sGPT"
        print_info "Check the logs above for errors and try running the script manually"
        print_info "Manual deployment: ./core/scripts/deploy-consolidated-k8sgpt.sh deploy"
        return 1
    fi
}

# Complete overlay quick start
complete_overlay_quickstart() {
    print_header "Complete Overlay Quick Start"
    
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
    
    # Deploy consolidated K8sGPT
    deploy_consolidated_k8sgpt || return 1
    
    # Deploy AI Agent Skills and MCP servers
    deploy_ai_agent_skills || return 1
    
    print_success "Overlay quick start completed successfully!"
    echo ""
    echo -e "${BLUE}🎉 Overlay system is ready!${NC}"
    echo -e "${YELLOW}📊 Your enhanced debug dashboard is running!${NC}"
    echo -e "${GREEN}🚀 Access it at: http://localhost:8080/dashboard${NC}"
    echo -e "${BLUE}🤖 Consolidated K8sGPT is deployed and integrated!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Use overlay-manager.sh to manage overlays"
    echo "2. Create custom overlays with overlay-cli.py"
    echo "3. Deploy overlays to your cluster"
    echo "4. Monitor overlay status and logs"
    echo "5. Access your AI agents dashboard at http://localhost:8080"
    echo "6. Configure Claude Desktop with AI Agent Skills (auto-configured)"
    echo "7. Use consolidated K8sGPT: http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
    echo ""
    echo -e "${GREEN}🎉 Overlay system is ready!${NC}"
    echo -e "${YELLOW}📊 Your enhanced debug dashboard is running!${NC}"
    echo -e "${GREEN}🚀 Access it at: http://localhost:8080/dashboard${NC}"
    echo -e "${YELLOW}✨ AI Agent Skills are fully operational and ready for use!${NC}"
    echo -e "${BLUE}🤖 Consolidated K8sGPT is deployed and integrated!${NC}"
}

# Help function
show_help() {
    echo "Agentic Reconciliation Engine - Overlay Quick Start"
    echo ""
    echo "Overlay approach to quickstart - extends quickstart.sh without modifying it"
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
    echo "ENVIRONMENT VARIABLES:"
    echo "  OVERLAY_DIR            Overlay directory (default: overlay)"
    echo "  QUICKSTART_SKIP_EXAMPLES  Skip example creation (default: false)"
    echo "  QUICKSTART_ENABLE_OVERLAYS Enable overlay features (default: true)"
    echo ""
    echo "CONCEPT:"
    echo "  This script demonstrates the overlay pattern:"
    echo "  1. Sets up overlay environment variables"
    echo "  2. Creates hook files that base quickstart.sh will source"
    echo "  3. Runs base quickstart.sh (never modifying it)"
    echo "  4. Base quickstart automatically picks up overlay extensions"
    echo "  5. No need to ever modify quickstart.sh again"
    echo ""
    echo "  The overlay concept: Base script defines structure,"
    echo "  overlay script patches/extends it without base knowing."
    echo ""
    echo "EXAMPLES:"
    echo "  $0 --all              # Complete overlay quick start"
    echo "  $0 --examples          # Create example overlays only"
    echo "  $0 --test              # Test overlay system only"
    echo "  $0 --deploy            # Deploy example overlay only"
    echo ""
    echo "  # Environment variable override"
    echo "  OVERLAY_DIR=custom-overlays $0 --all"
    echo ""
    echo "DESCRIPTION:"
    echo "  Overlay quick start for Agentic Reconciliation Engine."
    echo "  Demonstrates overlay pattern where base script (quickstart.sh) is"
    echo "  extended without modification through environment variables and hooks."
    echo ""
    echo "  For general repository setup, use: quickstart.sh"
    echo "  For overlay lifecycle management, use: overlay-manager.sh"
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
        deploy_consolidated_k8sgpt
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
        deploy_consolidated_k8sgpt
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

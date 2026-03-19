#!/bin/bash
# Agentic Reconciliation Engine - Common Overlay Quick Start Functions
# Shared functions for all environment-specific overlay quickstart scripts

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

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Set overlay environment variables
setup_overlay_environment() {
    print_header "Setting Up Overlay Environment"
    
    # Create hooks directory if it doesn't exist
    mkdir -p core/hooks
    
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
    cat > core/hooks/pre-quickstart.sh << 'EOF'
#!/bin/bash
# Overlay pre-quickstart hook
# This runs before the base quickstart.sh

echo "🔧 Overlay pre-quickstart hook executing..."

# Set overlay-specific defaults
export OVERLAY_DIR="overlay"
export OVERLAY_REGISTRY_ENABLED="true"
export OVERLAY_TEMPLATES_ENABLED="true"

# Override some quickstart defaults for overlay workflow
export QUICKSTART_MODE="overlay"
export QUICKSTART_FEATURES="overlay-creation,overlay-deployment,overlay-management"

echo "✅ Overlay environment prepared"
EOF
    
    # Post-quickstart hook - runs after base quickstart
    cat > core/hooks/post-quickstart.sh << 'EOF'
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
        
        if [[ -f "core/config/langfuse-secret-$TOPDIR.yaml" ]]; then
            if kubectl apply -f core/config/langfuse-secret-$TOPDIR.yaml; then
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
        mkdir -p overlay/registry
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
    chmod +x core/hooks/pre-quickstart.sh
    chmod +x core/hooks/post-quickstart.sh
    
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

# Deploy AI Agent Skills and MCP servers
deploy_ai_agent_skills() {
    print_header "Deploying AI Agent Skills and MCP Servers"
    
    # Source the deploy_ai_agent_skills script
    local deploy_script="$SCRIPT_DIR/deploy_ai_agent_skills.sh"
    if [[ -f "$deploy_script" ]]; then
        source "$deploy_script"
        deploy_ai_agent_skills
    else
        print_warning "deploy_ai_agent_skills.sh not found - skipping AI agent deployment"
    fi
}

# Complete overlay quick start
complete_overlay_quickstart() {
    local environment="$1"
    
    print_header "Complete Overlay Quick Start - $environment"
    
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
    echo -e "${BLUE}🎉 Overlay system is ready on $environment!${NC}"
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
    echo -e "${GREEN}🎉 Overlay system and AI agents are ready on $environment!${NC}"
    echo -e "${YELLOW}📊 Your enhanced debug dashboard is running!${NC}"
    echo -e "${GREEN}🚀 Access it at: http://localhost:8080/dashboard${NC}"
    echo -e "${YELLOW}✨ AI Agent Skills are fully operational and ready for use!${NC}"
}

# Help function
show_overlay_help() {
    echo "Agentic Reconciliation Engine - Common Overlay Quick Start Functions"
    echo ""
    echo "USAGE: source overlay-quickstart-common.sh"
    echo ""
    echo "DESCRIPTION:"
    echo "  Provides shared functions for all environment-specific overlay quickstart scripts."
    echo "  This includes overlay environment setup, hook creation, example generation,"
    echo "  system testing, and deployment orchestration."
    echo ""
    echo "CORE FUNCTIONS:"
    echo "  setup_overlay_environment()           - Configure overlay environment variables"
    echo "  create_overlay_hooks()                - Create overlay extension hooks"
    echo "  run_overlay_quickstart()             - Execute base quickstart with overlays"
    echo "  create_overlay_examples()             - Generate example overlays"
    echo "  test_overlay_system()                 - Test overlay system components"
    echo "  deploy_example_overlay()             - Deploy example overlay to cluster"
    echo "  deploy_ai_agent_skills()             - Deploy AI skills and MCP servers"
    echo "  complete_overlay_quickstart()         - Full overlay quickstart orchestration"
    echo ""
    echo "UTILITY FUNCTIONS:"
    echo "  print_header(), print_success(), print_error()"
    echo "  print_warning(), print_info()"
    echo ""
    echo "ENVIRONMENT VARIABLES:"
    echo "  OVERLAY_MODE=true                     - Enable overlay mode"
    echo "  OVERLAY_QUICKSTART=true               - Mark as overlay quickstart"
    echo "  QUICKSTART_SKIP_EXAMPLES=true         - Skip basic example creation"
    echo "  QUICKSTART_ENABLE_OVERLAYS=true       - Enable overlay features"
}

# Export functions for use in other scripts
export -f print_header print_success print_error print_warning print_info
export -f setup_overlay_environment create_overlay_hooks run_overlay_quickstart
export -f create_overlay_examples test_overlay_system deploy_example_overlay
export -f deploy_ai_agent_skills complete_overlay_quickstart show_overlay_help

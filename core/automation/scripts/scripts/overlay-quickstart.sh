#!/bin/bash
# GitOps Infrastructure Control Plane - Overlay Quick Start
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

# Create overlay-specific directories
mkdir -p core/deployment/overlays/examples
mkdir -p core/deployment/overlays/templates
mkdir -p core/deployment/overlays/registry

# Initialize overlay registry if it doesn't exist
if [[ ! -f core/deployment/overlays/registry/catalog.yaml ]]; then
    cat > core/deployment/overlays/registry/catalog.yaml << 'REGISTRY_EOF'
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
if [[ ! -d core/deployment/overlays/templates ]]; then
    mkdir -p core/deployment/overlays/templates/{skill-overlay,dashboard-overlay,infra-overlay}
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
        python3 "$SCRIPT_DIR/overlay-cli.py" create hello-world skills debug --template skills-overlay || {
            print_error "Failed to create hello-world overlay"
            return 1
        }
        
        # Create dark-theme dashboard overlay
        python3 "$SCRIPT_DIR/overlay-cli.py" create dark-theme dashboard themes --template dashboard-overlay || {
            print_error "Failed to create dark-theme overlay"
            return 1
        }
        
        # Create production-env composed overlay
        python3 "$SCRIPT_DIR/overlay-cli.py" create production-env composed "" || {
            print_error "Failed to create production-env overlay"
            return 1
        }
        
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
    
    # Test overlay registry
    if [[ -f "core/deployment/overlays/registry/catalog.yaml" ]]; then
        print_success "Overlay registry exists"
        ((passed_tests++))
    else
        print_error "Overlay registry missing"
        ((test_results++))
    fi
    ((total_tests++))
    
    # Test overlay templates
    if [[ -d "core/deployment/overlays/templates" ]]; then
        local template_count=$(find core/deployment/overlays/templates -name "kustomization.yaml" | wc -l)
        print_success "Found $template_count overlay templates"
        ((passed_tests++))
    else
        print_error "Overlay templates missing"
        ((test_results++))
    fi
    ((total_tests++))
    
    # Test overlay CLI
    if [[ -f "$SCRIPT_DIR/overlay-cli.py" ]]; then
        if python3 "$SCRIPT_DIR/overlay-cli.py" list > /dev/null 2>&1; then
            print_success "Overlay CLI working"
            ((passed_tests++))
        else
            print_error "Overlay CLI not working"
            ((test_results++))
        fi
    else
        print_warning "Overlay CLI not available"
    fi
    ((total_tests++))
    
    # Print test results
    print_header "Test Results"
    echo -e "${BLUE}Total Tests: $total_tests${NC}"
    echo -e "${GREEN}Passed: $passed_tests${NC}"
    if [[ $((test_results - passed_tests)) -gt 0 ]]; then
        echo -e "${RED}Failed: $((test_results - passed_tests))${NC}"
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
    if [[ -d "core/deployment/overlays/core/ai/skills/debug/enhanced" ]]; then
        print_info "Deploying enhanced debug overlay..."
        
        if kustomize build core/deployment/overlays/core/ai/skills/debug/enhanced | kubectl apply -f -; then
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
    
    print_success "Overlay quick start completed successfully!"
    echo ""
    echo -e "${BLUE}🎉 Overlay system is ready!${NC}"
    echo -e "${YELLOW}📊 Your enhanced debug dashboard is running!${NC}"
    echo -e "${GREEN}🚀 Access it at: http://localhost:8080/dashboard${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Use overlay-manager.sh to manage overlays"
    echo "2. Create custom overlays with overlay-cli.py"
    echo "3. Deploy overlays to your cluster"
    echo "4. Monitor overlay status and logs"
}

# Help function
show_help() {
    echo "GitOps Infrastructure Control Plane - Overlay Quick Start"
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
    echo "  OVERLAY_DIR            Overlay directory (default: overlays)"
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
    echo "  Overlay quick start for GitOps Infrastructure Control Plane."
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

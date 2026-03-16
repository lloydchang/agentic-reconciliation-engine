#!/bin/bash
# GitOps Infrastructure Control Plane - Overlay Quick Start Script
# Overlay creation, testing, deployment, and management

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
OVERLAY_DIR="${OVERLAY_DIR:-overlays}"

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

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
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
    
    # Check cluster access
    if kubectl cluster-info &> /dev/null; then
        print_success "Kubernetes cluster accessible"
    else
        print_info "Kubernetes cluster not accessible (will skip deployment tests)"
    fi
    
    print_success "All prerequisites satisfied"
}

# Create example overlays
create_examples() {
    print_header "Creating Example Overlays"
    
    # Create examples directory
    local examples_dir="${OVERLAY_DIR}/examples"
    mkdir -p "$examples_dir"
    
    # 1. Hello World Skill Overlay
    print_info "Creating hello-world skill overlay..."
    python3 "${SCRIPT_DIR}/overlay-cli.py" create hello-world skills debug --template skills-overlay || {
        print_error "Failed to create hello-world overlay"
        return 1
    }
    
    # Add custom content to hello-world
    mkdir -p "${OVERLAY_DIR}/.agents/debug/hello-world/patches"
    cat > "${OVERLAY_DIR}/.agents/debug/hello-world/patches/hello-world.yaml" << 'EOF'
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: hello-world-config
data:
  message: "Hello, World!"
  overlay_enabled: "true"
  feature_x: "enabled"
EOF
    
    # 2. Dark Theme Dashboard Overlay
    print_info "Creating dark-theme dashboard overlay..."
    python3 "${SCRIPT_DIR}/overlay-cli.py" create dark-theme dashboard themes --template dashboard-overlay || {
        print_error "Failed to create dark-theme overlay"
        return 1
    }
    
    # Add dark theme CSS
    mkdir -p "${OVERLAY_DIR}/agents/dashboard/themes/dark-theme/theme"
    cat > "${OVERLAY_DIR}/agents/dashboard/themes/dark-theme/theme/dark.css" << 'EOF'
:root {
  --primary-color: #1e88e5;
  --secondary-color: #43a047;
  --background-color: #0d1117;
  --surface-color: #21262d;
  --text-color: #c9d1d9;
  --border-color: #30363d;
}

.dashboard-container {
  background: var(--surface-color);
  color: var(--text-color);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.header {
  background: var(--primary-color);
  color: white;
  padding: 15px;
  border-radius: 6px 6px 0 6px;
  margin-bottom: 20px;
}

.metric-card {
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 15px;
}
EOF
    
    # 3. Production Environment Composed Overlay
    print_info "Creating production-environment composed overlay..."
    python3 "${SCRIPT_DIR}/overlay-cli.py" create production-env composed "" || {
        print_error "Failed to create production-environment overlay"
        return 1
    }
    
    cat > "${OVERLAY_DIR}/composed/production-env/kustomization.yaml" << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: production-environment
  namespace: production
resources:
  - ../../../../control-plane
  - ../../../../.agents
  - ../../../../agents
commonLabels:
  overlay: "production-environment"
  overlay-type: "composed"
  managed-by: "kustomize"
EOF
    
    # 4. Multi-Cloud Infrastructure Overlay
    print_info "Creating multi-cloud infrastructure overlay..."
    python3 "${SCRIPT_DIR}/overlay-cli.py" create multi-cloud infrastructure flux --template infra-overlay || {
        print_error "Failed to create multi-cloud overlay"
        return 1
    }
    
    # Add cloud configurations
    mkdir -p "${OVERLAY_DIR}/control-plane/multi-cloud/configs"
    
    # AWS configuration
    cat > "${OVERLAY_DIR}/control-plane/multi-cloud/configs/aws.yaml" << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-config
data:
  cloud_provider: "aws"
  region: "us-east-1"
  availability_zone: "us-east-1a"
  cluster_type: "eks"
  storage_class: "gp2"
  vpc_cidr: "10.0.0.0/16"
  subnet_cidrs: "10.0.1.0/24,10.0.2.0/24"
EOF
    
    # Azure configuration
    cat > "${OVERLAY_DIR}/control-plane/multi-cloud/configs/azure.yaml" << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: azure-config
data:
  cloud_provider: "azure"
  region: "eastus"
  availability_zone: "1"
  cluster_type: "aks"
  storage_class: "managed-premium"
  resource_group: "my-resource-group"
EOF
    
    # GCP configuration
    cat > "${OVERLAY_DIR}/control-plane/multi-cloud/configs/gcp.yaml" << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: gcp-config
data:
  cloud_provider: "gcp"
  region: "us-central1"
  availability_zone: "us-central1-a"
  cluster_type: "gke"
  storage_class: "standard"
EOF
    
    print_success "Example overlays created"
}

# Test overlay system
test_overlays() {
    print_header "Testing Overlay System"
    
    local test_results=()
    local total_tests=0
    local passed_tests=0
    
    # Test overlay listing
    print_info "Testing overlay listing..."
    if python3 "${SCRIPT_DIR}/overlay-cli.py" list; then
        print_success "Overlay listing works"
        ((passed_tests++))
    else
        print_error "Overlay listing failed"
        ((test_results++))
    fi
    ((total_tests++))
    
    # Test overlay validation
    print_info "Testing overlay validation..."
    if python3 "${SCRIPT_DIR}/validate-overlays.py" "${OVERLAY_DIR}/.agents/debug/enhanced" --verbose; then
        print_success "Overlay validation works"
        ((passed_tests++))
    else
        print_error "Overlay validation failed"
        ((test_results++))
    fi
    ((total_tests++))
    
    # Test overlay building
    print_info "Testing overlay building..."
    if kustomize build "${OVERLAY_DIR}/.agents/debug/enhanced" > /tmp/test-build.yaml; then
        print_success "Overlay building works"
        ((passed_tests++))
    else
        print_error "Overlay building failed"
        ((test_results++))
    fi
    ((total_tests++))
    
    # Test overlay registry
    print_info "Testing overlay registry..."
    if python3 "${SCRIPT_DIR}/overlay-registry.py" list; then
        print_success "Overlay registry works"
        ((passed_tests++))
    else
        print_error "Overlay registry failed"
        ((test_results++))
    fi
    ((total_tests++))
    
    # Test overlay search
    print_info "Testing overlay search..."
    if python3 "${SCRIPT_DIR}/overlay-cli.py" search debug; then
        print_success "Overlay search works"
        ((passed_tests++))
    else
        print_error "Overlay search failed"
        ((test_results++))
    fi
    ((total_tests++))
    
    # Print test results
    print_header "Test Results"
    echo -e "${BLUE}Total Tests: $total_tests${NC}"
    echo -e "${GREEN}Passed: $passed_tests${NC}"
    if [[ $((test_results - passed_tests)) -gt 0 ]]; then
        echo -e "${RED}Failed: $((test_results - passed_tests))${NC}"
        echo -e "${RED}❌ Failed tests: $(python3 "${SCRIPT_DIR}/overlay-cli.py" list 2>/dev/null | grep -E "overlay-(validation|build|registry)" | tr '\n' ' ' | head -10)${NC}"
    else
        echo -e "${GREEN}🎉 All tests passed!${NC}"
    fi
}

# Deploy overlays
deploy_overlays() {
    print_header "Deploying Overlays"
    
    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        print_info "Kubernetes cluster not accessible - skipping deployment"
        return 0
    fi
    
    print_info "Deploying enhanced debug overlay..."
    
    # Build and deploy the enhanced debug overlay
    if kustomize build "${OVERLAY_DIR}/.agents/debug/enhanced" | kubectl apply -f -; then
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
        local service_url
        if command -v minikube &> /dev/null; then
            service_url=$(minikube service debug --url -n flux-system)
        else
            # For other clusters, try port-forward
            service_url="http://localhost:8080"
        fi
        
        print_success "Dashboard available at: $service_url"
        print_info "Access the dashboard at: $service_url/dashboard"
        
    else
        print_error "Failed to deploy enhanced debug overlay"
        return 1
    fi
}

# Complete quick start
complete_quickstart() {
    print_header "Complete Overlay Quick Start"
    
    # Run all steps
    check_prerequisites || return 1
    create_examples || return 1
    test_overlays || return 1
    deploy_overlays || return 1
    
    print_success "Overlay quick start completed successfully!"
    echo ""
    echo -e "${BLUE}📊 Your enhanced debug dashboard is now running!${NC}"
    echo -e "${YELLOW}Access it at: http://localhost:8080/dashboard${NC}"
    echo ""
    echo -e "${GREEN}🎉 Overlay system is ready for use!${NC}"
}

# Help function
show_help() {
    echo "GitOps Infrastructure Control Plane - Overlay Quick Start"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help        Show this help message"
    echo "  -i, --install      Install prerequisites only"
    echo "  -e, --example      Create example overlays only"
    echo "  -t, --test         Test overlay system only"
    echo "  -d, --deploy       Deploy overlays only"
    echo "  -a, --all          Run complete quick start (install + examples + test + deploy)"
    echo ""
    echo "ENVIRONMENT VARIABLES:"
    echo "  NAMESPACE              Target namespace (default: flux-system)"
    echo "  OVERLAY_DIR            Overlay directory (default: overlays)"
    echo ""
    echo "EXAMPLES:"
    echo "  $0 --all              # Complete quick start"
    echo "  $0 --example           # Create examples only"
    echo "  $0 --test              # Test system only"
    echo "  $0 --deploy            # Deploy to cluster"
    echo ""
    echo "DESCRIPTION:"
    echo "  Complete overlay quick start for GitOps Infrastructure Control Plane."
    echo "  Creates, tests, and deploys overlays with enhanced debugging capabilities."
    echo ""
    echo "  For general repository setup, use: quickstart.sh"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -i|--install)
        check_prerequisites
        ;;
    -e|--example)
        create_examples
        ;;
    -t|--test)
        test_overlays
        ;;
    -d|--deploy)
        deploy_overlays
        ;;
    -a|--all)
        complete_quickstart
        ;;
    "")
        complete_quickstart
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac

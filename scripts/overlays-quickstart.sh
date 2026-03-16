#!/bin/bash

# Overlays Quick Start Script
# GitOps Infrastructure Control Plane - Quick Start Guide
# 
# This script provides a complete quick start experience for the overlays system
#
# Usage: ./overlays-quickstart.sh [option]
# Options:
#   -h, --help     Show this help message
#   -i, --install   Install prerequisites
#   -e, --example   Create example overlays
#   -t, --test      Test overlay system
#   -d, --deploy    Deploy overlays to cluster
#   -a, --all       Run complete quick start (install + examples + test + deploy)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="flux-system"
OVERLAY_DIR="overlays"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Helper functions
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
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Show help
show_help() {
    cat << EOF
${BLUE}Overlays Quick Start Script${NC}

${YELLOW}USAGE:${NC}
    $0 [OPTIONS]

${YELLOW}OPTIONS:${NC}
    -h, --help        Show this help message
    -i, --install      Install prerequisites
    -e, --example      Create example overlays
    -t, --test         Test overlay system
    -d, --deploy       Deploy overlays to cluster
    -a, --all          Run complete quick start (install + examples + test + deploy)

${YELLOW}EXAMPLES:${NC}
    $0 --all              # Complete quick start
    $0 --install          # Install prerequisites only
    $0 --example           # Create example overlays only
    $0 --test             # Test system only
    $0 --deploy            # Deploy to cluster only

${YELLOW}ENVIRONMENT VARIABLES:${NC}
    NAMESPACE              Target namespace (default: flux-system)
    OVERLAY_DIR            Overlays directory (default: overlays)
    
EOF
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local missing_tools=()
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    else
        print_success "kubectl found: $(kubectl version --client --short 2>/dev/null || echo 'unknown')"
    fi
    
    # Check kustomize
    if ! command -v kustomize &> /dev/null; then
        missing_tools+=("kustomize")
    else
        print_success "kustomize found: $(kustomize version | cut -d' ' -f1 | cut -d'/' -f1)"
    fi
    
    # Check python3
    if ! command -v python3 &> /dev/null; then
        missing_tools+=("python3")
    else
        print_success "python3 found: $(python3 --version | cut -d' ' -f2)"
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        missing_tools+=("git")
    else
        print_success "git found: $(git --version | cut -d' ' -f3)"
    fi
    
    # Check if cluster is accessible
    if kubectl cluster-info &> /dev/null; then
        print_success "Kubernetes cluster accessible"
        local cluster_info=$(kubectl cluster-info | grep "Kubernetes master" | cut -d':' -f2 | tr -d ' ')
        print_info "Cluster: $cluster_info"
    else
        print_warning "Kubernetes cluster not accessible (will skip deployment tests)"
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        print_error "Missing tools: ${missing_tools[*]}"
        print_info "Please install missing tools and try again"
        return 1
    fi
    
    print_success "All prerequisites satisfied"
    return 0
}

# Install prerequisites
install_prerequisites() {
    print_header "Installing Prerequisites"
    
    # Install Python dependencies
    if [ -f "${SCRIPT_DIR}/../requirements.txt" ]; then
        print_info "Installing Python dependencies..."
        pip3 install -r "${SCRIPT_DIR}/../requirements.txt" || {
            print_error "Failed to install Python dependencies"
            return 1
        }
        print_success "Python dependencies installed"
    fi
    
    # Make scripts executable
    print_info "Making overlay scripts executable..."
    chmod +x "${SCRIPT_DIR}"/overlay-*.py || {
        print_error "Failed to make scripts executable"
        return 1
    }
    print_success "Scripts made executable"
    
    # Add scripts to PATH
    if [[ ":$PATH:" != *":${SCRIPT_DIR}:"* ]]; then
        export PATH="${SCRIPT_DIR}:$PATH"
        print_info "Added scripts to PATH"
    fi
    
    print_success "Prerequisites installation complete"
}

# Create example overlays
create_examples() {
    print_header "Creating Example Overlays"
    
    # Create examples directory
    local examples_dir="${OVERLAY_DIR}/examples"
    mkdir -p "$examples_dir"
    
    # 1. Hello World Skill Overlay
    print_info "Creating hello-world skill overlay..."
    python3 "${SCRIPT_DIR}/overlay-cli.py" create hello-world skills debug --template skill-overlay || {
        print_error "Failed to create hello-world overlay"
        return 1
    }
    
    # Add custom content to hello-world
    cat > "$examples_dir/.agents/hello-world/patches/hello-world.yaml" << 'EOF'
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
    
    cat > "$examples_dir/.agents/hello-world/kustomization.yaml" << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: hello-world
  namespace: flux-system
resources:
  - ../../../../.agents/debug
patchesStrategicMerge:
  - patches/hello-world.yaml
configMapGenerator:
  - name: hello-world-config
    literals:
      - OVERLAY_ENABLED=true
      - HELLO_WORLD=true
commonLabels:
  overlay: "hello-world"
  overlay-type: "skill"
  managed-by: "kustomize"
EOF
    
    cat > "$examples_dir/.agents/hello-world/overlay-metadata.yaml" << 'EOF'
---
name: hello-world
version: "1.0.0"
description: "Simple hello world overlay for getting started"
category: skills
base_path: ".agents/debug"
license: "AGPLv3"
risk_level: low
autonomy: fully_auto

maintainer:
  name: "Community"
  email: "community@example.com"

tags:
  - skills
  - example
  - hello-world

compatibility:
  min_base: "1.0.0"
  kubernetes: ">=1.20"

examples:
  - name: "Hello World"
    description: "Run hello world example"
    command: "echo 'Hello, World!'"
    expected_output: "Hello, World!"
EOF
    
    print_success "Created hello-world skill overlay"
    
    # 2. Dark Theme Dashboard Overlay
    print_info "Creating dark-theme dashboard overlay..."
    python3 "${SCRIPT_DIR}/overlay-cli.py" create dark-theme dashboard themes --template dashboard-overlay || {
        print_error "Failed to create dark-theme overlay"
        return 1
    }
    
    # Add dark theme CSS
    mkdir -p "$examples_dir/agents/dashboard/themes/dark-theme/theme"
    cat > "$examples_dir/agents/dashboard/themes/dark-theme/theme/dark.css" << 'EOF'
:root {
  --primary-color: #1e88e5;
  --secondary-color: #43a047;
  --background-color: #0d1117;
  --surface-color: #21262d;
  --text-color: #c9d1d9;
  --border-color: #30363d;
}

.dashboard-container {
  background: var(--background-color);
  color: var(--text-color);
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

.card {
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.4);
  padding: 1rem;
}

.button-primary {
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.button-primary:hover {
  background: #1976d2;
  transform: translateY(-1px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
}
EOF
    
    cat > "$examples_dir/agents/dashboard/themes/dark-theme/kustomization.yaml" << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: dark-theme
  namespace: flux-system
resources:
  - ../../../../../agents/dashboard
patchesStrategicMerge:
  - patches/theme-patches.yaml
configMapGenerator:
  - name: dark-theme-config
    files:
      - theme/dark.css
    literals:
      - THEME_MODE=dark
      - THEME_VARIANT=pro
      - CUSTOM_ANIMATIONS=true
commonLabels:
  overlay: "dark-theme"
  overlay-type: "dashboard"
  managed-by: "kustomize"
EOF
    
    print_success "Created dark-theme dashboard overlay"
    
    # 3. Production Environment Composed Overlay
    print_info "Creating production-environment composed overlay..."
    python3 "${SCRIPT_DIR}/overlay-cli.py" create production-env composed "" || {
        print_error "Failed to create production-environment overlay"
        return 1
    }
    
    cat > "$examples_dir/composed/production-env/kustomization.yaml" << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: production-environment
  namespace: production
resources:
  - ../../../../control-plane
  - ../../../../.agents
  - ../../../../agents
  
  # Production enhancements
  - ../.agents/debug/enhanced
  - ../agents/dashboard/themes/dark-pro

# Production configuration
configMapGenerator:
  - name: production-env-config
    literals:
      - ENVIRONMENT=production
      - SECURITY_LEVEL=high
      - MONITORING_LEVEL=comprehensive
      - BACKUP_ENABLED=true
      - AUDIT_LOGGING=true
      - MULTI_REGION=true

# Production resource requirements
patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/resources
        value:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"
commonLabels:
  environment: production
  security-level: high
  monitoring: comprehensive
  backup: enabled
EOF
    
    print_success "Created production-environment composed overlay"
    
    # 4. Multi-Cloud Infrastructure Overlay
    print_info "Creating multi-cloud infrastructure overlay..."
    python3 "${SCRIPT_DIR}/overlay-cli.py" create multi-cloud infrastructure flux --template infra-overlay || {
        print_error "Failed to create multi-cloud overlay"
        return 1
    }
    
    # Add cloud configurations
    mkdir -p "$examples_dir/control-plane/multi-cloud/configs"
    
    # AWS configuration
    cat > "$examples_dir/control-plane/multi-cloud/configs/aws.yaml" << 'EOF'
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
    cat > "$examples_dir/control-plane/multi-cloud/configs/azure.yaml" << 'EOF'
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
    cat > "$examples_dir/control-plane/multi-cloud/configs/gcp.yaml" << 'EOF'
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
  project_id: "my-project"
EOF
    
    cat > "$examples_dir/control-plane/multi-cloud/kustomization.yaml" << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: multi-cloud
  namespace: flux-system
resources:
  - ../../../../control-plane
  - configs/aws/
  - configs/azure/
  - configs/gcp/

configMapGenerator:
  - name: multi-cloud-config
    literals:
      - MULTI_CLOUD_ENABLED=true
      - CLOUD_FAILOVER=true
      - CROSS_CLOUD_NETWORKING=true
      - DISASTER_RECOVERY=true

# Cloud-specific configurations
configurations:
  - configs/\${CLOUD_PROVIDER:-aws}/
EOF
    
    print_success "Created multi-cloud infrastructure overlay"
    
    print_success "All example overlays created successfully"
    print_info "Example overlays location: $examples_dir"
    
    # List created examples
    echo
    print_info "Created overlays:"
    find "$examples_dir" -name "kustomization.yaml" -exec dirname {} \; | sort
}

# Test overlay system
test_system() {
    print_header "Testing Overlay System"
    
    local test_results=()
    local total_tests=0
    local passed_tests=0
    
    # Test 1: List overlays
    print_info "Testing overlay listing..."
    if python3 "${SCRIPT_DIR}/overlay-cli.py" list &> /dev/null; then
        print_success "Overlay listing works"
        ((passed_tests++))
    else
        print_error "Overlay listing failed"
        test_results+=("overlay-list")
    fi
    ((total_tests++))
    
    # Test 2: Validate existing overlays
    print_info "Testing overlay validation..."
    if [ -d "${OVERLAY_DIR}/.agents/debug/enhanced" ]; then
        if python3 "${SCRIPT_DIR}/validate-overlays.py" "${OVERLAY_DIR}/.agents/debug/enhanced" &> /dev/null; then
            print_success "Overlay validation works"
            ((passed_tests++))
        else
            print_error "Overlay validation failed"
            test_results+=("overlay-validation")
        fi
    else
        print_warning "Debug enhanced overlay not found, skipping validation test"
    fi
    ((total_tests++))
    
    # Test 3: Build overlay
    print_info "Testing overlay building..."
    if [ -d "${OVERLAY_DIR}/.agents/debug/enhanced" ]; then
        if python3 "${SCRIPT_DIR}/overlay-cli.py" build "${OVERLAY_DIR}/.agents/debug/enhanced" --output /tmp/test-build.yaml &> /dev/null; then
            print_success "Overlay building works"
            ((passed_tests++))
            rm -f /tmp/test-build.yaml
        else
            print_error "Overlay building failed"
            test_results+=("overlay-build")
        fi
    else
        print_warning "Debug enhanced overlay not found, skipping build test"
    fi
    ((total_tests++))
    
    # Test 4: Registry operations
    print_info "Testing overlay registry..."
    if python3 "${SCRIPT_DIR}/overlay-registry.py" list &> /dev/null; then
        print_success "Overlay registry works"
        ((passed_tests++))
    else
        print_error "Overlay registry failed"
        test_results+=("overlay-registry")
    fi
    ((total_tests++))
    
    # Test 5: Search functionality
    print_info "Testing overlay search..."
    if python3 "${SCRIPT_DIR}/overlay-cli.py" search "debug" &> /dev/null; then
        print_success "Overlay search works"
        ((passed_tests++))
    else
        print_error "Overlay search failed"
        test_results+=("overlay-search")
    fi
    ((total_tests++))
    
    # Show test results
    echo
    print_header "Test Results"
    echo -e "${BLUE}Total Tests: $total_tests${NC}"
    echo -e "${GREEN}Passed: $passed_tests${NC}"
    echo -e "${RED}Failed: $((total_tests - passed_tests))${NC}"
    
    if [ ${#test_results[@]} -gt 0 ]; then
        echo
        print_error "Failed tests: ${test_results[*]}"
        return 1
    fi
    
    print_success "All tests passed! Overlay system is working correctly."
    return 0
}

# Deploy overlays
deploy_overlays() {
    print_header "Deploying Overlays to Cluster"
    
    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Kubernetes cluster not accessible"
        print_info "Please configure kubectl and try again"
        return 1
    fi
    
    # Create namespace if it doesn't exist
    print_info "Creating namespace: $NAMESPACE"
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f - || {
        print_warning "Namespace $NAMESPACE may already exist"
    }
    
    # Deploy debug enhanced overlay
    if [ -d "${OVERLAY_DIR}/.agents/debug/enhanced" ]; then
        print_info "Deploying debug enhanced overlay..."
        if python3 "${SCRIPT_DIR}/overlay-cli.py" apply "${OVERLAY_DIR}/.agents/debug/enhanced" --dry-run; then
            print_info "Dry run successful, applying to cluster..."
            if python3 "${SCRIPT_DIR}/overlay-cli.py" apply "${OVERLAY_DIR}/.agents/debug/enhanced"; then
                print_success "Debug enhanced overlay deployed successfully"
            else
                print_error "Failed to deploy debug enhanced overlay"
                return 1
            fi
        else
            print_error "Dry run failed for debug enhanced overlay"
            return 1
        fi
    else
        print_warning "Debug enhanced overlay not found"
    fi
    
    # Deploy production environment overlay (if created)
    if [ -d "${OVERLAY_DIR}/examples/composed/production-env" ]; then
        print_info "Deploying production environment overlay..."
        if python3 "${SCRIPT_DIR}/overlay-cli.py" apply "${OVERLAY_DIR}/examples/composed/production-env" --namespace production; then
            print_success "Production environment overlay deployed successfully"
        else
            print_error "Failed to deploy production environment overlay"
            return 1
        fi
    else
        print_warning "Production environment overlay not found"
    fi
    
    # Show deployment status
    print_info "Checking deployment status..."
    kubectl get pods -n "$NAMESPACE" -l overlay=debug-enhanced
    kubectl get deployments -n "$NAMESPACE" -l overlay=debug-enhanced
    
    print_success "Overlay deployment complete"
}

# Complete quick start
run_complete_quickstart() {
    print_header "Complete Quick Start"
    
    print_info "Starting complete quick start process..."
    echo
    
    # Step 1: Install prerequisites
    if ! install_prerequisites; then
        print_error "Prerequisites installation failed"
        return 1
    fi
    echo
    
    # Step 2: Create examples
    if ! create_examples; then
        print_error "Example creation failed"
        return 1
    fi
    echo
    
    # Step 3: Test system
    if ! test_system; then
        print_error "System testing failed"
        return 1
    fi
    echo
    
    # Step 4: Deploy overlays
    if ! deploy_overlays; then
        print_error "Overlay deployment failed"
        return 1
    fi
    echo
    
    print_success "🎉 Complete quick start finished successfully!"
    echo
    print_info "What you can do next:"
    echo -e "${BLUE}  1. Explore created overlays:${NC}"
    echo -e "     ls -la ${OVERLAY_DIR}/examples/"
    echo
    echo -e "${BLUE}  2. Test individual overlays:${NC}"
    echo -e "     python3 ${SCRIPT_DIR}/overlay-cli.py validate ${OVERLAY_DIR}/examples/.agents/hello-world"
    echo
    echo -e "${BLUE}  3. Create custom overlays:${NC}"
    echo -e "     python3 ${SCRIPT_DIR}/overlay-cli.py create my-overlay skills debug --template skill-overlay"
    echo
    echo -e "${BLUE}  4. Deploy to different environments:${NC}"
    echo -e "     python3 ${SCRIPT_DIR}/overlay-cli.py apply ${OVERLAY_DIR}/examples/composed/production-env --namespace staging"
    echo
    echo -e "${BLUE}  5. Learn more:${NC}"
    echo -e "     Read the documentation: docs/OVERLAYS-QUICK-START.md"
    echo -e "     Check examples: docs/OVERLAYS-EXAMPLES.md"
    echo -e "     Join community: https://github.com/gitops-infra-control-plane/discussions"
    
    return 0
}

# Main script logic
main() {
    # Parse command line arguments
    case "${1:-}" in
        -h|--help)
            show_help
            exit 0
            ;;
        -i|--install)
            check_prerequisites
            install_prerequisites
            ;;
        -e|--example)
            check_prerequisites
            create_examples
            ;;
        -t|--test)
            check_prerequisites
            test_system
            ;;
        -d|--deploy)
            check_prerequisites
            deploy_overlays
            ;;
        -a|--all)
            run_complete_quickstart
            ;;
        "")
            print_error "No option provided"
            echo
            show_help
            exit 1
            ;;
        *)
            print_error "Unknown option: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Script is being executed directly
    main "$@"
else
    # Script is being sourced
    :
fi

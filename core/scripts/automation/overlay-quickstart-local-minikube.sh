#!/bin/bash
# Agentic Reconciliation Engine - Overlay Quick Start for Minikube
# Overlay approach to quickstart - extends quickstart-local-minikube.sh without modifying it

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'
RESET='\033[0m'

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
    print_header "Setting Up Overlay Environment for Minikube"

    # Create hooks directory if it doesn't exist
    mkdir -p core/hooks

    # Set overlay-specific configuration
    export OVERLAY_MODE="true"
    export OVERLAY_QUICKSTART="true"
    export OVERLAY_VERSION="2.0.0"
    export OVERLAY_TARGET_ENVIRONMENT="local-minikube"

    # Override default quickstart behavior
    export QUICKSTART_SKIP_EXAMPLES="true"
    export QUICKSTART_SKIP_VALIDATION="false"
    export QUICKSTART_ENABLE_OVERLAYS="true"

    # Minikube-specific overlay settings
    export MINIKUBE_OVERLAY_ENABLED="true"
    export MINIKUBE_ADDONS_OVERLAY="ingress,dashboard,metrics-server"

    print_success "Overlay environment configured for Minikube"
}

# Create overlay-specific hooks
create_overlay_hooks() {
    print_header "Creating Overlay Hooks for Minikube"

    # Pre-quickstart hook - runs before base quickstart
    cat > core/hooks/pre-quickstart.sh << 'EOF'
#!/bin/bash
# Overlay pre-quickstart hook for Minikube
# This runs before the base quickstart-local-minikube.sh

echo "🔧 Overlay pre-quickstart hook executing for Minikube..."

# Set overlay-specific defaults for Minikube
export OVERLAY_DIR="overlays/minikube"
export OVERLAY_REGISTRY_ENABLED="true"
export OVERLAY_TEMPLATES_ENABLED="true"

# Override some quickstart defaults for overlay workflow
export QUICKSTART_MODE="overlay"
export QUICKSTART_FEATURES="overlay-creation,overlay-deployment,overlay-management,minikube-cluster"

# Minikube-specific overlay configuration
export MINIKUBE_PROFILE="${MINIKUBE_PROFILE:-agentic-overlay}"
export MINIKUBE_DRIVER="${MINIKUBE_DRIVER:-docker}"
export MINIKUBE_MEMORY="${MINIKUBE_MEMORY:-4096}"
export MINIKUBE_CPUS="${MINIKUBE_CPUS:-2}"

echo "✅ Overlay environment prepared for Minikube"
EOF

    # Post-quickstart hook - runs after base quickstart
    cat > core/hooks/post-quickstart.sh << 'EOF'
#!/bin/bash
# Overlay post-quickstart hook for Minikube
# This runs after the base quickstart-local-minikube.sh

echo "🚀 Overlay post-quickstart hook executing for Minikube..."

# Deploy additional overlay services for Minikube
echo "🔧 Deploying overlay services for Minikube..."

# Check if kubectl is available and cluster is accessible
if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null; then

    # Deploy overlay-specific services
    echo "🔧 Deploying overlay dashboard extensions..."

    # Create overlay namespace
    kubectl create namespace overlay-services --dry-run=client -o yaml | kubectl apply -f -

    # Deploy overlay monitoring stack
    cat << 'MONITORING_EOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: overlay-monitoring-config
  namespace: overlay-services
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
      - job_name: 'overlay-services'
        static_configs:
          - targets: ['localhost:9090']
MONITORING_EOF

    echo "✅ Overlay services deployed for Minikube"

    # Deploy Langfuse + Temporal Integration for Overlay
    echo "🔍 Deploying Langfuse + Temporal Integration for Minikube Overlay..."

    # Deploy Langfuse secrets if needed
    if ! kubectl get secret langfuse-secret -n langfuse &>/dev/null; then
        echo "🔐 Creating Langfuse secrets..."
        # Note: In production, use proper secret management
        kubectl create secret generic langfuse-secret \
            --from-literal=database-url="postgresql://user:password@langfuse-postgres:5432/langfuse" \
            --from-literal=nextauth-secret="your-nextauth-secret-here" \
            --from-literal=nextauth-url="http://localhost:3000" \
            --namespace langfuse --dry-run=client -o yaml | kubectl apply -f -
    fi

    echo "✅ Langfuse integration configured for Minikube"

else
    echo "⚠️  kubectl not available or cluster not accessible - skipping overlay services deployment"
fi

echo "🎉 Minikube overlay deployment completed!"
EOF

    # Make hooks executable
    chmod +x core/hooks/pre-quickstart.sh
    chmod +x core/hooks/post-quickstart.sh

    print_success "Overlay hooks created for Minikube"
}

# Main overlay function
main() {
    print_header "Agentic Reconciliation Engine - Minikube Overlay Quick Start"

    echo -e "${BLUE}Welcome to Agentic Reconciliation Engine - Minikube Overlay Deployment!${NC}"
    echo ""
    echo -e "${YELLOW}This overlay extends quickstart-local-minikube.sh with additional features:${NC}"
    echo "  • Enhanced monitoring and observability"
    echo "  • Langfuse + Temporal integration"
    echo "  • Overlay-specific service deployment"
    echo "  • Custom Minikube cluster configuration"
    echo ""

    # Check if base script exists
    local base_script="$SCRIPT_DIR/quickstart-local-minikube.sh"
    if [[ ! -f "$base_script" ]]; then
        print_error "Base script not found: $base_script"
        print_info "Please ensure quickstart-local-minikube.sh exists before running overlay"
        exit 1
    fi

    # Setup overlay environment
    setup_overlay_environment

    # Create overlay hooks
    create_overlay_hooks

    # Source the base quickstart script
    print_info "Sourcing base Minikube quickstart script..."
    source "$base_script"
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi

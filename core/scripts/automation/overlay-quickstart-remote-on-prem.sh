#!/bin/bash
# Agentic Reconciliation Engine - Overlay Quick Start for Remote On-Premises
# Overlay approach to quickstart - extends quickstart-remote-on-prem.sh without modifying it

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
    print_header "Setting Up Overlay Environment for Remote On-Premises"

    # Create hooks directory if it doesn't exist
    mkdir -p core/hooks

    # Set overlay-specific configuration
    export OVERLAY_MODE="true"
    export OVERLAY_QUICKSTART="true"
    export OVERLAY_VERSION="2.0.0"
    export OVERLAY_TARGET_ENVIRONMENT="remote-on-prem"

    # Override default quickstart behavior
    export QUICKSTART_SKIP_EXAMPLES="true"
    export QUICKSTART_SKIP_VALIDATION="false"
    export QUICKSTART_ENABLE_OVERLAYS="true"

    # On-premises-specific overlay settings
    export ONPREM_OVERLAY_ENABLED="true"
    export INGRESS_OVERLAY_ENABLED="true"

    print_success "Overlay environment configured for Remote On-Premises"
}

# Create overlay-specific hooks
create_overlay_hooks() {
    print_header "Creating Overlay Hooks for Remote On-Premises"

    # Pre-quickstart hook - runs before base quickstart
    cat > core/hooks/pre-quickstart.sh << 'EOF'
#!/bin/bash
# Overlay pre-quickstart hook for Remote On-Premises
# This runs before the base quickstart-remote-on-prem.sh

echo "🔧 Overlay pre-quickstart hook executing for Remote On-Premises..."

# Set overlay-specific defaults for On-Premises
export OVERLAY_DIR="overlays/remote-on-prem"
export OVERLAY_REGISTRY_ENABLED="true"
export OVERLAY_TEMPLATES_ENABLED="true"

# Override some quickstart defaults for overlay workflow
export QUICKSTART_MODE="overlay"
export QUICKSTART_FEATURES="overlay-creation,overlay-deployment,overlay-management,on-prem-k8s"

# On-premises-specific overlay configuration
export INGRESS_CLASS="nginx"
export STORAGE_CLASS="${STORAGE_CLASS:-}"
export LOAD_BALANCER_TYPE="${LOAD_BALANCER_TYPE:-}"

echo "✅ Overlay environment prepared for Remote On-Premises"
EOF

    # Post-quickstart hook - runs after base quickstart
    cat > core/hooks/post-quickstart.sh << 'EOF'
#!/bin/bash
# Overlay post-quickstart hook for Remote On-Premises
# This runs after the base quickstart-remote-on-prem.sh

echo "🚀 Overlay post-quickstart hook executing for Remote On-Premises..."

# Deploy additional overlay services for On-Premises
echo "🔧 Deploying overlay services for On-Premises..."

# Check if kubectl is available and cluster is accessible
if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null; then

    # Deploy overlay-specific services
    echo "🔧 Deploying overlay dashboard extensions..."

    # Create overlay namespace
    kubectl create namespace overlay-services --dry-run=client -o yaml | kubectl apply -f -

    # Deploy overlay monitoring stack (on-premises-specific)
    cat << 'MONITORING_EOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: overlay-onprem-monitoring-config
  namespace: overlay-services
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
      - job_name: 'overlay-onprem-services'
        static_configs:
          - targets: ['localhost:9090']
MONITORING_EOF

    # Deploy on-premises-specific services
    echo "🏢 Deploying on-premises-specific overlay services..."

    # Create overlay persistent volumes if storage class exists
    if kubectl get storageclass --no-headers 2>/dev/null | grep -q .; then
        echo "💾 Creating overlay persistent volumes..."

        # Create overlay PVC
        cat << 'PVC_EOF' | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: overlay-storage
  namespace: overlay-services
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
EOF
    fi

    echo "✅ Overlay on-premises services deployed"

    # Deploy Langfuse + Temporal Integration for Overlay
    echo "🔍 Deploying Langfuse + Temporal Integration for On-Premises Overlay..."

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

    echo "✅ Langfuse integration configured for On-Premises"

else
    echo "⚠️  kubectl not available or cluster not accessible - skipping overlay services deployment"
fi

echo "🎉 Remote On-Premises overlay deployment completed!"
EOF

    # Make hooks executable
    chmod +x core/hooks/pre-quickstart.sh
    chmod +x core/hooks/post-quickstart.sh

    print_success "Overlay hooks created for Remote On-Premises"
}

# Main overlay function
main() {
    print_header "Agentic Reconciliation Engine - Remote On-Premises Overlay Quick Start"

    echo -e "${BLUE}Welcome to Agentic Reconciliation Engine - Remote On-Premises Overlay Deployment!${NC}"
    echo ""
    echo -e "${YELLOW}This overlay extends quickstart-remote-on-prem.sh with additional features:${NC}"
    echo "  • Enhanced on-premises resource provisioning"
    echo "  • Overlay-specific persistent volumes"
    echo "  • On-premises-specific service integrations"
    echo "  • Custom Kubernetes cluster configuration"
    echo ""

    # Check if base script exists
    local base_script="$SCRIPT_DIR/quickstart-remote-on-prem.sh"
    if [[ ! -f "$base_script" ]]; then
        print_error "Base script not found: $base_script"
        print_info "Please ensure quickstart-remote-on-prem.sh exists before running overlay"
        exit 1
    fi

    # Setup overlay environment
    setup_overlay_environment

    # Create overlay hooks
    create_overlay_hooks

    # Source the base quickstart script
    print_info "Sourcing base Remote On-Premises quickstart script..."
    source "$base_script"
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi

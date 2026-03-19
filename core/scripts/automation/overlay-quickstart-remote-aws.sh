#!/bin/bash
# Agentic Reconciliation Engine - Overlay Quick Start for Remote AWS
# Overlay approach to quickstart - extends quickstart-remote-aws.sh without modifying it

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
    print_header "Setting Up Overlay Environment for Remote AWS"

    # Create hooks directory if it doesn't exist
    mkdir -p core/hooks

    # Set overlay-specific configuration
    export OVERLAY_MODE="true"
    export OVERLAY_QUICKSTART="true"
    export OVERLAY_VERSION="2.0.0"
    export OVERLAY_TARGET_ENVIRONMENT="remote-aws"

    # Override default quickstart behavior
    export QUICKSTART_SKIP_EXAMPLES="true"
    export QUICKSTART_SKIP_VALIDATION="false"
    export QUICKSTART_ENABLE_OVERLAYS="true"

    # AWS-specific overlay settings
    export AWS_OVERLAY_ENABLED="true"
    export AWS_REGION_OVERLAY="${AWS_DEFAULT_REGION}"

    print_success "Overlay environment configured for Remote AWS"
}

# Create overlay-specific hooks
create_overlay_hooks() {
    print_header "Creating Overlay Hooks for Remote AWS"

    # Pre-quickstart hook - runs before base quickstart
    cat > core/hooks/pre-quickstart.sh << 'EOF'
#!/bin/bash
# Overlay pre-quickstart hook for Remote AWS
# This runs before the base quickstart-remote-aws.sh

echo "🔧 Overlay pre-quickstart hook executing for Remote AWS..."

# Set overlay-specific defaults for Remote AWS
export OVERLAY_DIR="overlays/remote-aws"
export OVERLAY_REGISTRY_ENABLED="true"
export OVERLAY_TEMPLATES_ENABLED="true"

# Override some quickstart defaults for overlay workflow
export QUICKSTART_MODE="overlay"
export QUICKSTART_FEATURES="overlay-creation,overlay-deployment,overlay-management,aws-eks"

# AWS-specific overlay configuration
export EKS_CLUSTER_NAME="${EKS_CLUSTER_NAME:-agentic-overlay-cluster}"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
export VPC_ID="${VPC_ID:-}"
export SUBNET_IDS="${SUBNET_IDS:-}"

echo "✅ Overlay environment prepared for Remote AWS"
EOF

    # Post-quickstart hook - runs after base quickstart
    cat > core/hooks/post-quickstart.sh << 'EOF'
#!/bin/bash
# Overlay post-quickstart hook for Remote AWS
# This runs after the base quickstart-remote-aws.sh

echo "🚀 Overlay post-quickstart hook executing for Remote AWS..."

# Deploy additional overlay services for AWS
echo "🔧 Deploying overlay services for AWS..."

# Check if kubectl is available and cluster is accessible
if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null; then

    # Deploy overlay-specific services
    echo "🔧 Deploying overlay dashboard extensions..."

    # Create overlay namespace
    kubectl create namespace overlay-services --dry-run=client -o yaml | kubectl apply -f -

    # Deploy overlay monitoring stack (AWS-specific)
    cat << 'MONITORING_EOF' | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: overlay-aws-monitoring-config
  namespace: overlay-services
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
      - job_name: 'overlay-aws-services'
        static_configs:
          - targets: ['localhost:9090']
      - job_name: 'aws-metadata'
        ec2_sd_configs:
          - region: us-east-1
            port: 80
MONITORING_EOF

    # Deploy AWS-specific services
    echo "☁️  Deploying AWS-specific overlay services..."

    # Create overlay S3 bucket via AWS CLI (if available)
    if command -v aws &> /dev/null && aws sts get-caller-identity &>/dev/null; then
        overlay_bucket="agentic-overlay-${AWS_DEFAULT_REGION}-$(date +%s)"
        aws s3 mb "s3://${overlay_bucket}" --region "${AWS_DEFAULT_REGION}" || true
        echo "📦 Created overlay S3 bucket: ${overlay_bucket}"
    fi

    echo "✅ Overlay AWS services deployed"

    # Deploy Langfuse + Temporal Integration for Overlay
    echo "🔍 Deploying Langfuse + Temporal Integration for AWS Overlay..."

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

    echo "✅ Langfuse integration configured for AWS"

else
    echo "⚠️  kubectl not available or cluster not accessible - skipping overlay services deployment"
fi

echo "🎉 Remote AWS overlay deployment completed!"
EOF

    # Make hooks executable
    chmod +x core/hooks/pre-quickstart.sh
    chmod +x core/hooks/post-quickstart.sh

    print_success "Overlay hooks created for Remote AWS"
}

# Main overlay function
main() {
    print_header "Agentic Reconciliation Engine - Remote AWS Overlay Quick Start"

    echo -e "${BLUE}Welcome to Agentic Reconciliation Engine - Remote AWS Overlay Deployment!${NC}"
    echo ""
    echo -e "${YELLOW}This overlay extends quickstart-remote-aws.sh with additional features:${NC}"
    echo "  • Enhanced AWS resource provisioning"
    echo "  • Overlay-specific S3 buckets and monitoring"
    echo "  • AWS-specific service integrations"
    echo "  • Custom EKS cluster configuration"
    echo ""

    # Check if base script exists
    local base_script="$SCRIPT_DIR/quickstart-remote-aws.sh"
    if [[ ! -f "$base_script" ]]; then
        print_error "Base script not found: $base_script"
        print_info "Please ensure quickstart-remote-aws.sh exists before running overlay"
        exit 1
    fi

    # Setup overlay environment
    setup_overlay_environment

    # Create overlay hooks
    create_overlay_hooks

    # Source the base quickstart script
    print_info "Sourcing base Remote AWS quickstart script..."
    source "$base_script"
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi

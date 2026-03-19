#!/bin/bash
# Agentic Reconciliation Engine - Overlay Quick Start for Azurite + LocalStack Azure
# Overlay approach to quickstart - extends quickstart-local-azurite-and-localstack-azure.sh without modifying it

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
    print_header "Setting Up Overlay Environment for Azurite + LocalStack Azure"

    # Create hooks directory if it doesn't exist
    mkdir -p core/hooks

    # Set overlay-specific configuration
    export OVERLAY_MODE="true"
    export OVERLAY_QUICKSTART="true"
    export OVERLAY_VERSION="2.0.0"
    export OVERLAY_TARGET_ENVIRONMENT="local-azurite-azure"

    # Override default quickstart behavior
    export QUICKSTART_SKIP_EXAMPLES="true"
    export QUICKSTART_SKIP_VALIDATION="false"
    export QUICKSTART_ENABLE_OVERLAYS="true"

    # Azure-specific overlay settings
    export AZURE_OVERLAY_ENABLED="true"
    export AZURITE_OVERLAY_ENABLED="true"
    export AZURE_STORAGE_OVERLAY="true"

    print_success "Overlay environment configured for Azurite + LocalStack Azure"
}

# Create overlay-specific hooks
create_overlay_hooks() {
    print_header "Creating Overlay Hooks for Azurite + LocalStack Azure"

    # Pre-quickstart hook - runs before base quickstart
    cat > core/hooks/pre-quickstart.sh << 'EOF'
#!/bin/bash
# Overlay pre-quickstart hook for Azurite + LocalStack Azure
# This runs before the base quickstart-local-azurite-and-localstack-azure.sh

echo "🔧 Overlay pre-quickstart hook executing for Azurite + LocalStack Azure..."

# Set overlay-specific defaults for Azure
export OVERLAY_DIR="overlays/azurite-azure"
export OVERLAY_REGISTRY_ENABLED="true"
export OVERLAY_TEMPLATES_ENABLED="true"

# Override some quickstart defaults for overlay workflow
export QUICKSTART_MODE="overlay"
export QUICKSTART_FEATURES="overlay-creation,overlay-deployment,overlay-management,azurite-azure"

# Azure-specific overlay configuration
export AZURE_STORAGE_ACCOUNT="${AZURE_STORAGE_ACCOUNT:-devstoreaccount1}"
export AZURE_STORAGE_KEY="${AZURE_STORAGE_KEY:-Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==}"
export AZURE_SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID:-00000000-0000-0000-0000-000000000000}"
export AZURE_TENANT_ID="${AZURE_TENANT_ID:-00000000-0000-0000-0000-000000000000}"

echo "✅ Overlay environment prepared for Azurite + LocalStack Azure"
EOF

    # Post-quickstart hook - runs after base quickstart
    cat > core/hooks/post-quickstart.sh << 'EOF'
#!/bin/bash
# Overlay post-quickstart hook for Azurite + LocalStack Azure
# This runs after the base quickstart-local-azurite-and-localstack-azure.sh

echo "🚀 Overlay post-quickstart hook executing for Azurite + LocalStack Azure..."

# Deploy additional overlay services for Azure
echo "🔧 Deploying overlay services for Azurite + LocalStack Azure..."

# Check if Azurite is running
if curl -s http://localhost:10000/devstoreaccount1 &>/dev/null; then

    # Deploy overlay-specific Azure resources
    echo "🔧 Deploying overlay Azure resources..."

    # Create overlay storage containers
    echo "📦 Creating overlay Azure storage containers..."
    curl -X PUT "http://localhost:10000/devstoreaccount1/overlay-container?restype=container" \
         -H "Authorization: SharedKey devstoreaccount1:Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==" \
         -H "Content-Length: 0" || true

    curl -X PUT "http://localhost:10000/devstoreaccount1/agentic-data-container?restype=container" \
         -H "Authorization: SharedKey devstoreaccount1:Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==" \
         -H "Content-Length: 0" || true

    # Upload sample data to overlay container
    echo "📤 Uploading sample data to overlay container..."
    echo "Sample overlay data for Azure Storage" | curl -X PUT "http://localhost:10000/devstoreaccount1/overlay-container/sample.txt" \
         -H "Authorization: SharedKey devstoreaccount1:Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==" \
         -H "Content-Type: text/plain" \
         -H "x-ms-blob-type: BlockBlob" \
         --data-binary @- || true

    echo "✅ Overlay Azure storage resources deployed"

else
    echo "⚠️  Azurite not running - skipping overlay Azure storage resource deployment"
fi

# Check if LocalStack Azure is running
if curl -s http://localhost:4566/_localstack/health | grep -q "running"; then

    # Deploy overlay-specific LocalStack Azure resources
    echo "🔧 Deploying overlay LocalStack Azure resources..."

    # Set AWS CLI to use LocalStack (for Azure services)
    export AWS_ACCESS_KEY_ID=test
    export AWS_SECRET_ACCESS_KEY=test
    export AWS_DEFAULT_REGION=us-east-1
    export AWS_ENDPOINT_URL=http://localhost:4566

    # Create overlay Azure resources via LocalStack
    echo "📊 Creating overlay Azure service resources..."

    # Create overlay storage account (simulated)
    aws s3 mb s3://overlay-azure-storage --endpoint-url=http://localhost:4566 || true

    # Create overlay service bus namespace
    aws sqs create-queue --queue-name overlay-servicebus --endpoint-url=http://localhost:4566 || true

    # Create overlay key vault (simulated via DynamoDB)
    aws dynamodb create-table \
        --table-name overlay-keyvault \
        --attribute-definitions AttributeName=id,AttributeType=S \
        --key-schema AttributeName=id,KeyType=HASH \
        --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
        --endpoint-url=http://localhost:4566 || true

    echo "✅ Overlay LocalStack Azure resources deployed"

else
    echo "⚠️  LocalStack not running - skipping overlay LocalStack Azure resource deployment"
fi

echo "🎉 Azurite + LocalStack Azure overlay deployment completed!"
EOF

    # Make hooks executable
    chmod +x core/hooks/pre-quickstart.sh
    chmod +x core/hooks/post-quickstart.sh

    print_success "Overlay hooks created for Azurite + LocalStack Azure"
}

# Main overlay function
main() {
    print_header "Agentic Reconciliation Engine - Azurite + LocalStack Azure Overlay Quick Start"

    echo -e "${BLUE}Welcome to Agentic Reconciliation Engine - Azurite + LocalStack Azure Overlay Deployment!${NC}"
    echo ""
    echo -e "${YELLOW}This overlay extends quickstart-local-azurite-and-localstack-azure.sh with additional features:${NC}"
    echo "  • Enhanced Azure storage provisioning"
    echo "  • Overlay-specific containers and blobs"
    echo "  • Azure service integrations"
    echo "  • Sample data for testing"
    echo ""

    # Check if base script exists
    local base_script="$SCRIPT_DIR/quickstart-local-azurite-and-localstack-azure.sh"
    if [[ ! -f "$base_script" ]]; then
        print_error "Base script not found: $base_script"
        print_info "Please ensure quickstart-local-azurite-and-localstack-azure.sh exists before running overlay"
        exit 1
    fi

    # Setup overlay environment
    setup_overlay_environment

    # Create overlay hooks
    create_overlay_hooks

    # Source the base quickstart script
    print_info "Sourcing base Azurite + LocalStack Azure quickstart script..."
    source "$base_script"
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi

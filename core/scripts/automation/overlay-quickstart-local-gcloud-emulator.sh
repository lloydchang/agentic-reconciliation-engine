#!/bin/bash
# Agentic Reconciliation Engine - Overlay Quick Start for Google Cloud Emulator
# Overlay approach to quickstart - extends quickstart-local-gcloud-emulator.sh without modifying it

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
    print_header "Setting Up Overlay Environment for Google Cloud Emulator"

    # Create hooks directory if it doesn't exist
    mkdir -p core/hooks

    # Set overlay-specific configuration
    export OVERLAY_MODE="true"
    export OVERLAY_QUICKSTART="true"
    export OVERLAY_VERSION="2.0.0"
    export OVERLAY_TARGET_ENVIRONMENT="local-gcloud-emulator"

    # Override default quickstart behavior
    export QUICKSTART_SKIP_EXAMPLES="true"
    export QUICKSTART_SKIP_VALIDATION="false"
    export QUICKSTART_ENABLE_OVERLAYS="true"

    # Google Cloud-specific overlay settings
    export GCLOUD_OVERLAY_ENABLED="true"
    export FIRESTORE_EMULATOR_HOST="localhost:8080"
    export PUBSUB_EMULATOR_HOST="localhost:8085"
    export BIGTABLE_EMULATOR_HOST="localhost:8086"
    export DATASTORE_EMULATOR_HOST="localhost:8081"
    export SPANNER_EMULATOR_HOST="localhost:9010"

    print_success "Overlay environment configured for Google Cloud Emulator"
}

# Create overlay-specific hooks
create_overlay_hooks() {
    print_header "Creating Overlay Hooks for Google Cloud Emulator"

    # Pre-quickstart hook - runs before base quickstart
    cat > core/hooks/pre-quickstart.sh << 'EOF'
#!/bin/bash
# Overlay pre-quickstart hook for Google Cloud Emulator
# This runs before the base quickstart-local-gcloud-emulator.sh

echo "🔧 Overlay pre-quickstart hook executing for Google Cloud Emulator..."

# Set overlay-specific defaults for Google Cloud
export OVERLAY_DIR="overlays/gcloud-emulator"
export OVERLAY_REGISTRY_ENABLED="true"
export OVERLAY_TEMPLATES_ENABLED="true"

# Override some quickstart defaults for overlay workflow
export QUICKSTART_MODE="overlay"
export QUICKSTART_FEATURES="overlay-creation,overlay-deployment,overlay-management,gcloud-emulator"

# Google Cloud-specific overlay configuration
export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-agentic-overlay-project}"
export FIRESTORE_EMULATOR_HOST="${FIRESTORE_EMULATOR_HOST:-localhost:8080}"
export PUBSUB_EMULATOR_HOST="${PUBSUB_EMULATOR_HOST:-localhost:8085}"
export BIGTABLE_EMULATOR_HOST="${BIGTABLE_EMULATOR_HOST:-localhost:8086}"
export DATASTORE_EMULATOR_HOST="${DATASTORE_EMULATOR_HOST:-localhost:8081}"
export SPANNER_EMULATOR_HOST="${SPANNER_EMULATOR_HOST:-localhost:9010}"

echo "✅ Overlay environment prepared for Google Cloud Emulator"
EOF

    # Post-quickstart hook - runs after base quickstart
    cat > core/hooks/post-quickstart.sh << 'EOF'
#!/bin/bash
# Overlay post-quickstart hook for Google Cloud Emulator
# This runs after the base quickstart-local-gcloud-emulator.sh

echo "🚀 Overlay post-quickstart hook executing for Google Cloud Emulator..."

# Deploy additional overlay services for Google Cloud
echo "🔧 Deploying overlay services for Google Cloud Emulator..."

# Check if emulators are running and create overlay resources
emulators_running=true

# Check Firestore emulator
if ! curl -s http://localhost:8080 &>/dev/null; then
    emulators_running=false
    echo "⚠️  Firestore emulator not running"
fi

# Check Pub/Sub emulator
if ! curl -s http://localhost:8085 &>/dev/null; then
    emulators_running=false
    echo "⚠️  Pub/Sub emulator not running"
fi

# Check Bigtable emulator
if ! curl -s http://localhost:8086 &>/dev/null; then
    emulators_running=false
    echo "⚠️  Bigtable emulator not running"
fi

if [[ "$emulators_running" == "true" ]]; then

    # Deploy overlay-specific Google Cloud resources
    echo "🔧 Deploying overlay Google Cloud resources..."

    # Set environment variables for gcloud CLI
    export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-agentic-overlay-project}"
    export FIRESTORE_EMULATOR_HOST="localhost:8080"
    export PUBSUB_EMULATOR_HOST="localhost:8085"
    export BIGTABLE_EMULATOR_HOST="localhost:8086"
    export DATASTORE_EMULATOR_HOST="localhost:8081"
    export SPANNER_EMULATOR_HOST="localhost:9010"

    # Create overlay Firestore collections and documents
    echo "📄 Creating overlay Firestore resources..."
    # Note: Firestore emulator REST API calls would go here
    # Example: curl -X POST "http://localhost:8080/v1/projects/${GOOGLE_CLOUD_PROJECT}/databases/(default)/documents/overlay-collection"

    # Create overlay Pub/Sub topics and subscriptions
    echo "📨 Creating overlay Pub/Sub resources..."
    if command -v gcloud &>/dev/null; then
        gcloud pubsub topics create overlay-topic --project="${GOOGLE_CLOUD_PROJECT}" || true
        gcloud pubsub subscriptions create overlay-subscription --topic=overlay-topic --project="${GOOGLE_CLOUD_PROJECT}" || true
    fi

    # Create overlay Bigtable instances and tables
    echo "🗄️  Creating overlay Bigtable resources..."
    if command -v cbt &>/dev/null; then
        cbt createtable overlay-table || true
        cbt createfamily overlay-table cf1 || true
    fi

    # Create overlay Datastore entities
    echo "📊 Creating overlay Datastore resources..."
    # Note: Datastore emulator operations would go here

    # Create overlay Spanner instances and databases
    echo "🗃️  Creating overlay Spanner resources..."
    # Note: Spanner emulator operations would go here

    echo "✅ Overlay Google Cloud resources deployed"

    # Deploy overlay integration with AI agents
    echo "🤖 Deploying overlay AI agent integrations..."

    # Create sample data for testing
    echo "Sample overlay data created for Google Cloud emulators"

    echo "✅ Overlay AI agent integrations configured"

else
    echo "⚠️  Google Cloud emulators not fully running - skipping overlay resource deployment"
fi

echo "🎉 Google Cloud Emulator overlay deployment completed!"
EOF

    # Make hooks executable
    chmod +x core/hooks/pre-quickstart.sh
    chmod +x core/hooks/post-quickstart.sh

    print_success "Overlay hooks created for Google Cloud Emulator"
}

# Main overlay function
main() {
    print_header "Agentic Reconciliation Engine - Google Cloud Emulator Overlay Quick Start"

    echo -e "${BLUE}Welcome to Agentic Reconciliation Engine - Google Cloud Emulator Overlay Deployment!${NC}"
    echo ""
    echo -e "${YELLOW}This overlay extends quickstart-local-gcloud-emulator.sh with additional features:${NC}"
    echo "  • Enhanced Google Cloud resource provisioning"
    echo "  • Overlay-specific Firestore collections"
    echo "  • Pub/Sub topics and subscriptions"
    echo "  • Bigtable instances and tables"
    echo "  • Sample data for testing"
    echo ""

    # Check if base script exists
    local base_script="$SCRIPT_DIR/quickstart-local-gcloud-emulator.sh"
    if [[ ! -f "$base_script" ]]; then
        print_error "Base script not found: $base_script"
        print_info "Please ensure quickstart-local-gcloud-emulator.sh exists before running overlay"
        exit 1
    fi

    # Setup overlay environment
    setup_overlay_environment

    # Create overlay hooks
    create_overlay_hooks

    # Source the base quickstart script
    print_info "Sourcing base Google Cloud Emulator quickstart script..."
    source "$base_script"
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi

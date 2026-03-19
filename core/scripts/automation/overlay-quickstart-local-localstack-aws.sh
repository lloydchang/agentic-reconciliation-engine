#!/bin/bash
# Agentic Reconciliation Engine - Overlay Quick Start for LocalStack AWS
# Overlay approach to quickstart - extends quickstart-local-localstack-aws.sh without modifying it

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
    print_header "Setting Up Overlay Environment for LocalStack AWS"

    # Create hooks directory if it doesn't exist
    mkdir -p core/hooks

    # Set overlay-specific configuration
    export OVERLAY_MODE="true"
    export OVERLAY_QUICKSTART="true"
    export OVERLAY_VERSION="2.0.0"
    export OVERLAY_TARGET_ENVIRONMENT="local-localstack-aws"

    # Override default quickstart behavior
    export QUICKSTART_SKIP_EXAMPLES="true"
    export QUICKSTART_SKIP_VALIDATION="false"
    export QUICKSTART_ENABLE_OVERLAYS="true"

    # LocalStack AWS-specific overlay settings
    export LOCALSTACK_OVERLAY_ENABLED="true"
    export LOCALSTACK_SERVICES_OVERLAY="s3,dynamodb,sns,sqs,lambda,iam"

    print_success "Overlay environment configured for LocalStack AWS"
}

# Create overlay-specific hooks
create_overlay_hooks() {
    print_header "Creating Overlay Hooks for LocalStack AWS"

    # Pre-quickstart hook - runs before base quickstart
    cat > core/hooks/pre-quickstart.sh << 'EOF'
#!/bin/bash
# Overlay pre-quickstart hook for LocalStack AWS
# This runs before the base quickstart-local-localstack-aws.sh

echo "🔧 Overlay pre-quickstart hook executing for LocalStack AWS..."

# Set overlay-specific defaults for LocalStack AWS
export OVERLAY_DIR="overlays/localstack-aws"
export OVERLAY_REGISTRY_ENABLED="true"
export OVERLAY_TEMPLATES_ENABLED="true"

# Override some quickstart defaults for overlay workflow
export QUICKSTART_MODE="overlay"
export QUICKSTART_FEATURES="overlay-creation,overlay-deployment,overlay-management,localstack-aws"

# LocalStack AWS-specific overlay configuration
export LOCALSTACK_API_KEY="${LOCALSTACK_API_KEY:-}"
export SERVICES="${SERVICES:-s3,dynamodb,sns,sqs,lambda,iam,cloudformation}"
export LOCALSTACK_WEB_UI="true"
export DEBUG="${DEBUG:-1}"

echo "✅ Overlay environment prepared for LocalStack AWS"
EOF

    # Post-quickstart hook - runs after base quickstart
    cat > core/hooks/post-quickstart.sh << 'EOF'
#!/bin/bash
# Overlay post-quickstart hook for LocalStack AWS
# This runs after the base quickstart-local-localstack-aws.sh

echo "🚀 Overlay post-quickstart hook executing for LocalStack AWS..."

# Deploy additional overlay services for LocalStack AWS
echo "🔧 Deploying overlay services for LocalStack AWS..."

# Check if LocalStack is running
if curl -s http://localhost:4566/_localstack/health | grep -q "running"; then

    # Deploy overlay-specific AWS resources
    echo "🔧 Deploying overlay AWS resources..."

    # Set AWS CLI to use LocalStack
    export AWS_ACCESS_KEY_ID=test
    export AWS_SECRET_ACCESS_KEY=test
    export AWS_DEFAULT_REGION=us-east-1
    export AWS_ENDPOINT_URL=http://localhost:4566

    # Create overlay S3 buckets
    echo "📦 Creating overlay S3 buckets..."
    aws s3 mb s3://overlay-bucket --endpoint-url=http://localhost:4566 || true
    aws s3 mb s3://agentic-data-bucket --endpoint-url=http://localhost:4566 || true

    # Create overlay DynamoDB tables
    echo "🗄️  Creating overlay DynamoDB tables..."
    aws dynamodb create-table \
        --table-name overlay-table \
        --attribute-definitions AttributeName=id,AttributeType=S \
        --key-schema AttributeName=id,KeyType=HASH \
        --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
        --endpoint-url=http://localhost:4566 || true

    # Create overlay SNS topics and SQS queues
    echo "📨 Creating overlay SNS topics and SQS queues..."
    aws sns create-topic --name overlay-topic --endpoint-url=http://localhost:4566 || true
    aws sqs create-queue --queue-name overlay-queue --endpoint-url=http://localhost:4566 || true

    # Create overlay IAM roles and policies
    echo "🔐 Creating overlay IAM resources..."
    cat > /tmp/overlay-iam-policy.json << 'IAM_EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "sns:Publish",
                "sqs:SendMessage"
            ],
            "Resource": "*"
        }
    ]
}
IAM_EOF

    aws iam create-policy --policy-name overlay-policy --policy-document file:///tmp/overlay-iam-policy.json --endpoint-url=http://localhost:4566 || true
    aws iam create-role --role-name overlay-role --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' --endpoint-url=http://localhost:4566 || true

    rm -f /tmp/overlay-iam-policy.json

    echo "✅ Overlay AWS resources deployed for LocalStack"

    # Deploy overlay integration with AI agents
    echo "🤖 Deploying overlay AI agent integrations..."

    # Create sample data for testing
    echo "Sample data for overlay bucket" | aws s3 cp - s3://overlay-bucket/sample.txt --endpoint-url=http://localhost:4566 || true

    aws dynamodb put-item \
        --table-name overlay-table \
        --item '{"id":{"S":"sample-id"},"data":{"S":"sample overlay data"}}' \
        --endpoint-url=http://localhost:4566 || true

    echo "✅ Overlay AI agent integrations configured"

else
    echo "⚠️  LocalStack not running - skipping overlay AWS resource deployment"
fi

echo "🎉 LocalStack AWS overlay deployment completed!"
EOF

    # Make hooks executable
    chmod +x core/hooks/pre-quickstart.sh
    chmod +x core/hooks/post-quickstart.sh

    print_success "Overlay hooks created for LocalStack AWS"
}

# Main overlay function
main() {
    print_header "Agentic Reconciliation Engine - LocalStack AWS Overlay Quick Start"

    echo -e "${BLUE}Welcome to Agentic Reconciliation Engine - LocalStack AWS Overlay Deployment!${NC}"
    echo ""
    echo -e "${YELLOW}This overlay extends quickstart-local-localstack-aws.sh with additional features:${NC}"
    echo "  • Enhanced AWS resource provisioning"
    echo "  • Overlay-specific S3 buckets and DynamoDB tables"
    echo "  • SNS/SQS messaging infrastructure"
    echo "  • IAM roles and policies for AI agents"
    echo "  • Sample data for testing"
    echo ""

    # Check if base script exists
    local base_script="$SCRIPT_DIR/quickstart-local-localstack-aws.sh"
    if [[ ! -f "$base_script" ]]; then
        print_error "Base script not found: $base_script"
        print_info "Please ensure quickstart-local-localstack-aws.sh exists before running overlay"
        exit 1
    fi

    # Setup overlay environment
    setup_overlay_environment

    # Create overlay hooks
    create_overlay_hooks

    # Source the base quickstart script
    print_info "Sourcing base LocalStack AWS quickstart script..."
    source "$base_script"
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi

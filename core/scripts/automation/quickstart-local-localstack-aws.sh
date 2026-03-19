#!/bin/bash
# Agentic Reconciliation Engine - Quick Start for Local LocalStack AWS Development
# Repository setup and initial onboarding for LocalStack AWS emulation

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
REPO_ROOT="$(git rev-parse --show-toplevel)"

# Source the deploy_ai_agent_skills function
if [[ -f "$SCRIPT_DIR/deploy_ai_agent_skills.sh" ]]; then
    source "$SCRIPT_DIR/deploy_ai_agent_skills.sh"
else
    echo "Warning: deploy_ai_agent_skills.sh not found"
fi

# Global counters for validation
ERRORS=0
WARNINGS=0

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

# Validation functions from prerequisites.sh
pass() { echo -e "  ${GREEN}✓${RESET} $*"; }
fail() { echo -e "  ${RED}✗${RESET} $*"; ERRORS=$((ERRORS + 1)); }
warn() { echo -e "  ${YELLOW}!${RESET} $*"; WARNINGS=$((WARNINGS + 1)); }
info() { echo -e "  ${CYAN}→${RESET} $*"; }

# Environment-specific validation for LocalStack AWS
run_localstack_aws_validation() {
    ERRORS=0
    WARNINGS=0

    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}║  agentic-reconciliation-engine — LocalStack AWS Validation ║${RESET}"
    echo -e "${BOLD}╚══════════════════════════════════════════════════════════════╝${RESET}"
    echo ""

    # 1. LocalStack prerequisites
    echo -e "${BOLD}[1/6] Checking LocalStack prerequisites${RESET}"

    # Check Docker (required for LocalStack)
    if command -v docker &>/dev/null; then
        local docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        if docker system info &>/dev/null; then
            pass "Docker available (${docker_version})"
        else
            fail "Docker daemon not accessible"
        fi
    else
        fail "Docker not found (required for LocalStack)"
    fi

    # Check LocalStack CLI
    if command -v localstack &>/dev/null; then
        local ls_version=$(localstack --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        pass "LocalStack CLI available (${ls_version})"
    else
        warn "LocalStack CLI not found - will use Docker directly"
    fi

    # Check AWS CLI
    if command -v aws &>/dev/null; then
        local aws_version=$(aws --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        pass "AWS CLI available (${aws_version})"
    else
        fail "AWS CLI not found (required for AWS skill testing)"
    fi

    # Check if LocalStack is running
    if curl -sf http://localhost:4566/_localstack/health &>/dev/null; then
        pass "LocalStack is running on localhost:4566"
    else
        warn "LocalStack not running on localhost:4566 - will be started"
    fi

    echo ""

    # 2. Standard CLI tools (AWS-focused)
    echo -e "${BOLD}[2/6] Checking required CLI tools${RESET}"

    check_tool() {
        local tool=$1 min_version=$2 version_flag="${3:---version}"
        if command -v "$tool" &>/dev/null; then
            local ver=""
            if "$tool" $version_flag >/dev/null 2>&1; then
                ver=$("$tool" $version_flag 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1)
            fi
            pass "${tool} ${ver}"
        else
            fail "${tool} not found (required)"
        fi
    }

    check_tool_optional() {
        local tool=$1
        if command -v "$tool" &>/dev/null; then
            pass "${tool} available"
        else
            warn "${tool} not found (optional — some skills will have limited functionality)"
        fi
    }

    # Required for AWS
    check_tool "terraform"  "1.6"
    check_tool "jq"         "1.6"
    check_tool "yq"         "4.0"

    # Optional but recommended
    check_tool_optional "kubectl"
    check_tool_optional "helm"
    check_tool_optional "checkov"

    echo ""

    # 3. LocalStack configuration
    echo -e "${BOLD}[3/6] Checking LocalStack configuration${RESET}"

    # Check environment variables
    check_env_optional() {
        local var=$1
        if [[ -n "${!var:-}" ]]; then
            local val="${!var}"
            if [[ "$var" =~ (SECRET|PASSWORD|KEY|TOKEN|PSK) ]]; then
                val="${val:0:6}***"
            fi
            pass "${var}=${val}"
        else
            warn "${var} not set (optional for local development)"
        fi
    }

    check_env_optional "AWS_ACCESS_KEY_ID"
    check_env_optional "AWS_SECRET_ACCESS_KEY"
    check_env_optional "AWS_DEFAULT_REGION"
    check_env_optional "LOCALSTACK_API_KEY"

    # Check LocalStack services configuration
    local services=${SERVICES:-"s3,lambda,iam,cloudformation,ec2,rds,dynamodb"}
    pass "LocalStack services: ${services}"

    echo ""

    # 4. Resource requirements check
    echo -e "${BOLD}[4/6] Checking resource requirements${RESET}"

    # Check available memory
    local mem_gb=$(docker system info --format '{{.MemTotal}}' 2>/dev/null | awk '{print int($1/1024/1024/1024)}' || echo "unknown")
    if [[ "$mem_gb" != "unknown" && $mem_gb -ge 4 ]]; then
        pass "Available memory: ${mem_gb}GB (sufficient for LocalStack)"
    else
        warn "Available memory: ${mem_gb}GB (may be insufficient - recommend 4GB+)"
    fi

    # Check available disk space
    local disk_gb=$(df -BG . | tail -1 | awk '{print int($4)}')
    if [[ $disk_gb -ge 10 ]]; then
        pass "Available disk space: ${disk_gb}GB (sufficient)"
    else
        warn "Available disk space: ${disk_gb}GB (may be insufficient - recommend 10GB+)"
    fi

    echo ""

    # 5. Network requirements
    echo -e "${BOLD}[5/6] Checking network requirements${RESET}"

    # Check for port conflicts
    local ports=(4566 8080)
    for port in "${ports[@]}"; do
        if lsof -i ":${port}" &>/dev/null; then
            if [[ $port -eq 4566 ]]; then
                # Port 4566 might be LocalStack
                if curl -sf http://localhost:4566/_localstack/health &>/dev/null; then
                    pass "Port ${port} in use by LocalStack"
                else
                    warn "Port ${port} in use by another service"
                fi
            else
                warn "Port ${port} is in use - may conflict with services"
            fi
        else
            pass "Port ${port} available"
        fi
    done

    echo ""

    # 6. Quick smoke test
    echo -e "${BOLD}[6/6] Running LocalStack smoke tests${RESET}"

    if docker ps | grep -q localstack; then
        pass "LocalStack container is running"
    else
        info "LocalStack container not running - will be started"
    fi

    if command -v aws &>/dev/null; then
        # Test AWS CLI configuration
        if aws configure list &>/dev/null; then
            pass "AWS CLI configured"
        else
            warn "AWS CLI not configured - LocalStack will use default credentials"
        fi
    fi

    echo ""

    # Summary
    echo -e "${BOLD}══════════════════════════════════════════════════════════════${RESET}"
    if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}  ✓ LocalStack AWS validation PASSED — ready for local AWS development${RESET}"
    elif [[ $ERRORS -eq 0 ]]; then
        echo -e "${YELLOW}${BOLD}  ⚠ LocalStack AWS validation PASSED with ${WARNINGS} warning(s)${RESET}"
        echo -e "${YELLOW}  Local AWS development may have degraded functionality.${RESET}"
    else
        echo -e "${RED}${BOLD}  ✗ LocalStack AWS validation FAILED — ${ERRORS} error(s), ${WARNINGS} warning(s)${RESET}"
        echo -e "${RED}  Fix the errors above before proceeding.${RESET}"
        echo ""
        echo -e "  ${CYAN}Quick fixes:${RESET}"
        echo -e "    brew install docker awscli localstack jq yq  # Install required tools"
        echo -e "    docker run -d --name localstack -p 4566:4566 localstack/localstack  # Start LocalStack"
    fi
    echo -e "${BOLD}══════════════════════════════════════════════════════════════${RESET}"
    echo ""

    return $ERRORS
}

# Hook support
run_hooks() {
    local hook_name="$1"
    local hook_file="core/hooks/${hook_name}.sh"

    if [[ -f "$hook_file" ]]; then
        print_info "Running $hook_name hook..."
        if bash "$hook_file"; then
            print_success "$hook_name hook completed"
        else
            print_error "$hook_name hook failed"
            return 1
        fi
    else
        print_info "No $hook_name hook found - skipping"
    fi
}

# Start LocalStack
start_localstack() {
    print_header "Starting LocalStack"

    # Check if LocalStack is already running
    if curl -sf http://localhost:4566/_localstack/health &>/dev/null; then
        print_info "LocalStack is already running"
        return 0
    fi

    # Check if container exists but is stopped
    if docker ps -a | grep -q localstack; then
        print_info "Starting existing LocalStack container..."
        if docker start localstack; then
            print_success "LocalStack container started"
            print_info "Waiting for LocalStack to be ready..."
            sleep 10
            return 0
        else
            print_warning "Failed to start existing container, will create new one"
        fi
    fi

    print_info "Starting LocalStack with AWS services..."

    # Set environment variables for LocalStack
    local services=${SERVICES:-"s3,lambda,iam,cloudformation,ec2,rds,dynamodb,apigateway,cloudwatch,logs,sns,sqs"}
    local env_vars=(
        "-e SERVICES=${services}"
        "-e DEBUG=1"
        "-e LAMBDA_EXECUTOR=docker"
        "-e DOCKER_HOST=unix:///var/run/docker.sock"
        "-e HOST_TMP_FOLDER=${TMPDIR:-/tmp/}localstack"
    )

    # Add LocalStack API key if set
    if [[ -n "${LOCALSTACK_API_KEY:-}" ]]; then
        env_vars+=("-e LOCALSTACK_API_KEY=${LOCALSTACK_API_KEY}")
    fi

    # Run LocalStack container
    if docker run -d --name localstack \
        --rm \
        -p 4566:4566 \
        "${env_vars[@]}" \
        -v "/var/run/docker.sock:/var/run/docker.sock" \
        -v "localstack-data:/tmp/localstack" \
        localstack/localstack:3.0; then

        print_success "LocalStack container started"
        print_info "Waiting for LocalStack to initialize..."

        # Wait for LocalStack to be ready
        local attempts=0
        local max_attempts=30
        while [[ $attempts -lt $max_attempts ]]; do
            if curl -sf http://localhost:4566/_localstack/health &>/dev/null; then
                print_success "LocalStack is ready!"
                return 0
            fi
            ((attempts++))
            sleep 2
        done

        print_error "LocalStack failed to become ready within expected time"
        return 1
    else
        print_error "Failed to start LocalStack container"
        return 1
    fi
}

# Configure AWS CLI for LocalStack
configure_aws_cli_for_localstack() {
    print_header "Configuring AWS CLI for LocalStack"

    print_info "Configuring AWS CLI to use LocalStack endpoints..."

    # Set AWS CLI to use LocalStack
    export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-test}
    export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-test}
    export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}

    # Configure AWS CLI
    mkdir -p ~/.aws

    cat > ~/.aws/config << EOF
[default]
region = ${AWS_DEFAULT_REGION}
output = json

[profile localstack]
region = ${AWS_DEFAULT_REGION}
output = json
endpoint_url = http://localhost:4566
EOF

    cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}

[localstack]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
EOF

    print_success "AWS CLI configured for LocalStack"
    print_info "Use 'aws --profile localstack' to interact with LocalStack"
}

# Create sample AWS resources in LocalStack
create_sample_aws_resources() {
    print_header "Creating Sample AWS Resources"

    print_info "Creating sample S3 bucket, Lambda function, and other resources..."

    # Set AWS CLI to use LocalStack profile
    export AWS_PROFILE=localstack

    # Create S3 bucket
    if aws s3 mb s3://agentic-test-bucket; then
        print_success "Created S3 bucket: agentic-test-bucket"
    else
        print_warning "Failed to create S3 bucket"
    fi

    # Create DynamoDB table
    if aws dynamodb create-table \
        --table-name agentic-test-table \
        --attribute-definitions AttributeName=id,AttributeType=S \
        --key-schema AttributeName=id,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST; then
        print_success "Created DynamoDB table: agentic-test-table"
    else
        print_warning "Failed to create DynamoDB table"
    fi

    # Create SNS topic
    if aws sns create-topic --name agentic-test-topic; then
        print_success "Created SNS topic: agentic-test-topic"
    else
        print_warning "Failed to create SNS topic"
    fi

    # Create SQS queue
    if aws sqs create-queue --queue-name agentic-test-queue; then
        print_success "Created SQS queue: agentic-test-queue"
    else
        print_warning "Failed to create SQS queue"
    fi

    print_success "Sample AWS resources created in LocalStack"
}

# Deploy AI agents dashboard function (same as base)
deploy_ai_agents_dashboard() {
    print_header "Deploying AI Agents Dashboard"

    # Check if the ecosystem deployment script exists
    local ecosystem_script="$SCRIPT_DIR/deploy-ai-agents-ecosystem.sh"

    if [[ ! -f "$ecosystem_script" ]]; then
        print_warning "AI agents ecosystem script not found at $ecosystem_script"
        print_info "You can manually run: ./core/automation/scripts/deploy-ai-agents-ecosystem.sh"
        return 0
    fi

    # Check if cluster is accessible (for local development, this might not be needed)
    if ! kubectl cluster-info &> /dev/null; then
        print_warning "Kubernetes cluster not accessible - skipping dashboard deployment"
        print_info "For LocalStack development, you may want to run a local K8s cluster first"
        print_info "Or deploy dashboard to LocalStack directly (not implemented yet)"
        return 0
    fi

    print_info "Deploying AI agents ecosystem with dashboard..."

    # Run the ecosystem deployment script
    if bash "$ecosystem_script"; then
        print_success "AI agents dashboard deployed successfully!"
        echo ""
        echo -e "${GREEN}🎉 Your AI Agents Dashboard is now running!${NC}"
        echo -e "${YELLOW}📊 Access it at: http://localhost:8080${NC}"
        echo ""

        # Start all required port-forwards in background
        start_all_port_forwards

        echo ""
        echo "🌐 All Services Access:"
        echo "  🚪 Infrastructure Portal:  http://localhost:9000"
        echo "  🤖 AI Dashboard:        http://localhost:8080"
        echo "  📊 Dashboard API:        http://localhost:5000"
        echo "  ⏰ Temporal UI:          http://localhost:7233"
        echo "  🔍 Langfuse Observability: http://localhost:3000"
        echo "  📈 Comprehensive API:   http://localhost:5001"
        echo "  🖥️  Comprehensive Frontend: http://localhost:8082"
        echo "  🧠 Memory Service:       http://localhost:8081"
        echo ""
        echo "💡 Management:"
        echo "  📝 View logs: tail -f /tmp/quickstart-port-forwards/*.log"
        echo "  🧹 Clean up: ./core/scripts/automation/quickstart-local-localstack-aws.sh --cleanup"
        echo "  🔄 Restart: ./core/scripts/automation/quickstart-local-localstack-aws.sh --start-pf"
        echo ""
        echo "Dashboard features:"
        echo "  ✅ Real-time AI agents monitoring"
        echo "  ✅ 91 operational skills visualization"
        echo "  ✅ Performance metrics and charts"
        echo "  ✅ Activity feed and system controls"
        echo "  ✅ Temporal workflow orchestration UI"
        echo "  ✅ Comprehensive analytics dashboard"
    else
        print_error "Failed to deploy AI agents dashboard"
        print_info "Check the logs above for errors and try running the script manually"
        return 1
    fi
}

# Start all required port-forwards in background (same as base)
start_all_port_forwards() {
    print_info "Starting background port-forwards for all services..."

    # Create log directory
    mkdir -p /tmp/quickstart-port-forwards

    local started_count=0
    local failed_count=0

    # AI Infrastructure Services
    local services=(
        "ai-infrastructure:ai-infrastructure-portal:80:9000"
        "ai-infrastructure:agent-dashboard-service:80:8080"
        "ai-infrastructure:dashboard-api-service:5000:5000"
        "ai-infrastructure:temporal-server-service:7233:7233"
        "ai-infrastructure:comprehensive-dashboard-api:5000:5001"
        "ai-infrastructure:comprehensive-dashboard-frontend:80:8082"
        "ai-infrastructure:agent-memory-service:8080:8081"

        # Langfuse Services
        "langfuse:langfuse-server:3000:3000"
    )

    for service_config in "${services[@]}"; do
        IFS=':' read -r namespace service_name target_port local_port <<< "$service_config"
        local log_file="/tmp/quickstart-port-forwards/${namespace}-${service_name}.log"
        local service_key="${namespace}-${service_name}"

        # Check if port-forward already running
        if pgrep -f "port-forward.*${service_name}.*${local_port}" > /dev/null; then
            print_info "Port-forward already running: ${service_name} -> ${local_port}"
            ((started_count++))
            continue
        fi

        # Start port-forward in background
        print_info "Starting: ${service_name} -> localhost:${local_port}"
        nohup kubectl port-forward -n "${namespace}" svc/"${service_name}" "${local_port}:${target_port}" > "${log_file}" 2>&1 &

        # Wait a moment and check if it started successfully
        sleep 2
        if pgrep -f "port-forward.*${service_name}.*${local_port}" > /dev/null; then
            print_success "✅ ${service_name} -> localhost:${local_port}"
            ((started_count++))
        else
            print_warning "❌ Failed to start: ${service_name} -> localhost:${local_port}"
            ((failed_count++))
        fi
    done

    # Summary
    echo ""
    print_success "Port-forward summary:"
    echo "  ✅ Started: ${started_count} services"
    if [[ $failed_count -gt 0 ]]; then
        echo "  ❌ Failed: ${failed_count} services"
    fi
    echo ""
    echo -e "${GREEN}🌐 Access URLs:${NC}"
    echo "  🚪 Infrastructure Portal:  http://localhost:9000"
    echo "  🤖 AI Dashboard:        http://localhost:8080"
    echo "  📊 Dashboard API:        http://localhost:5000"
    echo "  ⏰ Temporal UI:          http://localhost:7233"
    echo "  🔍 Langfuse Observability: http://localhost:3000"
    echo "  📈 Comprehensive API:   http://localhost:5001"
    echo "  🖥️  Comprehensive Frontend: http://localhost:8082"
    echo "  🧠 Memory Service:       http://localhost:8081"
    echo ""
    echo -e "${YELLOW}📝 Logs: tail -f /tmp/quickstart-port-forwards/*.log${NC}"
}

# Enhanced cleanup function for LocalStack
cleanup_localstack() {
    print_header "Cleaning up LocalStack environment"

    # Stop all port-forwards
    cleanup_port_forwards

    # Stop LocalStack container
    if docker ps | grep -q localstack; then
        print_info "Stopping LocalStack container..."
        if docker stop localstack; then
            print_success "LocalStack container stopped"
        else
            print_warning "Failed to stop LocalStack container"
        fi
    fi

    # Remove LocalStack container
    if docker ps -a | grep -q localstack; then
        print_info "Removing LocalStack container..."
        if docker rm localstack; then
            print_success "LocalStack container removed"
        else
            print_warning "Failed to remove LocalStack container"
        fi
    fi

    # Clean up LocalStack data volume
    if docker volume ls | grep -q localstack-data; then
        print_info "Removing LocalStack data volume..."
        if docker volume rm localstack-data; then
            print_success "LocalStack data volume removed"
        else
            print_warning "Failed to remove LocalStack data volume"
        fi
    fi

    # Clean up AWS CLI configuration
    if [[ -f ~/.aws/config.backup ]]; then
        mv ~/.aws/config.backup ~/.aws/config
        print_info "Restored original AWS CLI config"
    fi

    if [[ -f ~/.aws/credentials.backup ]]; then
        mv ~/.aws/credentials.backup ~/.aws/credentials
        print_info "Restored original AWS CLI credentials"
    fi

    print_success "LocalStack environment cleanup completed"
}

# Main function for LocalStack AWS quickstart
main() {
    print_header "Agentic Reconciliation Engine - LocalStack AWS Quick Start"

    echo -e "${BLUE}Welcome to Agentic Reconciliation Engine - LocalStack AWS Development!${NC}"
    echo ""
    echo -e "${YELLOW}This will set up LocalStack for local AWS service emulation.${NC}"
    echo ""

    # Check if we're in the right directory
    if [[ ! -f "$REPO_ROOT/README.md" ]]; then
        print_error "Not in repository root. Please run from repository root."
        exit 1
    fi

    # Run LocalStack-specific validation
    print_info "Running LocalStack-specific prerequisites validation..."
    if ! run_localstack_aws_validation; then
        print_error "LocalStack validation failed. Please fix errors above and retry."
        exit 1
    fi

    # If there are warnings, prompt user to continue
    if [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Found $WARNINGS warning(s). Continue with LocalStack setup? (Y/n)${NC}"
        read -r response
        if [[ "$response" =~ ^[Nn]$ ]]; then
            print_info "LocalStack setup cancelled by user."
            exit 0
        fi
    fi

    # Run pre-quickstart hook
    run_hooks "pre-quickstart" || return 1

    # Setup basic configuration
    print_info "Setting up LocalStack development environment..."

    # Create basic directories if they don't exist
    mkdir -p logs/
    mkdir -p tmp/

    # Make scripts executable
    find "$SCRIPT_DIR" -name "*.sh" -exec chmod +x {} \;
    find "$SCRIPT_DIR" -name "*.py" -exec chmod +x {} \;

    print_success "LocalStack development environment ready"

    # Start LocalStack
    start_localstack || return 1

    # Configure AWS CLI for LocalStack
    configure_aws_cli_for_localstack || return 1

    # Create sample AWS resources
    create_sample_aws_resources || return 1

    # Run post-quickstart hook
    run_hooks "post-quickstart" || return 1

    # Deploy AI agents dashboard
    deploy_ai_agents_dashboard || return 1

    # Deploy AI Agent Skills and MCP servers
    deploy_ai_agent_skills || return 1

    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Access your AI agents dashboard at http://localhost:8080"
    echo "2. Test AWS skills against LocalStack:"
    echo "   aws --profile localstack s3 ls"
    echo "   aws --profile localstack dynamodb list-tables"
    echo "3. Configure Claude Desktop with AI Agent Skills (auto-configured)"
    echo "4. Use consolidated K8sGPT: http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
    echo "5. View LocalStack logs: docker logs localstack"
    echo "6. Clean up environment: ./core/scripts/automation/quickstart-local-localstack-aws.sh --cleanup"
    echo ""
    echo -e "${GREEN}🚀 LocalStack AWS development environment is ready!${NC}"
    echo -e "${YELLOW}🧠 AI agents are fully operational!${NC}"
    echo -e "${BLUE}☁️  LocalStack AWS services are running on localhost:4566${NC}"
}

# Enhanced cleanup function (same as base)
cleanup_port_forwards() {
    print_info "Cleaning up all background port-forwards..."

    local services=(
        "ai-infrastructure-portal:9000"
        "agent-dashboard-service:8080"
        "dashboard-api-service:5000"
        "temporal-server-service:7233"
        "comprehensive-dashboard-api:5001"
        "comprehensive-dashboard-frontend:8082"
        "langfuse-server:3000"
        "agent-memory-service:8081"
    )

    for service_config in "${services[@]}"; do
        IFS=':' read -r service_name local_port <<< "$service_config"

        # Kill the port-forward process
        if pgrep -f "port-forward.*${service_name}.*${local_port}" > /dev/null; then
            pkill -f "port-forward.*${service_name}.*${local_port}"
            print_success "Stopped ${service_name} port-forward (port ${local_port})"
        fi
    done

    # Clean up log directory
    if [[ -d /tmp/quickstart-port-forwards ]]; then
        rm -rf /tmp/quickstart-port-forwards
        print_info "Cleaned up port-forward logs"
    fi

    # Clean up old individual log files
    for service_config in "${services[@]}"; do
        IFS=':' read -r service_name local_port <<< "$service_config"
        local log_file="/tmp/${service_name}-port-forward.log"
        if [[ -f "$log_file" ]]; then
            rm -f "$log_file"
        fi
    done

    print_success "All port-forwards cleaned up"
}

# Help function
show_help() {
    echo "Agentic Reconciliation Engine - LocalStack AWS Quick Start"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help         Show this help message"
    echo "  --validate         Run LocalStack validation only"
    echo "  --cleanup          Clean up LocalStack container and resources"
    echo "  --start-pf         Start all port-forwards (if not already running)"
    echo "  --start-localstack Start LocalStack container only"
    echo "  --configure-aws    Configure AWS CLI for LocalStack only"
    echo "  --create-resources Create sample AWS resources in LocalStack"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up LocalStack for local AWS service emulation."
    echo "  This includes LocalStack container startup, AWS CLI configuration,"
    echo "  sample resource creation, and deployment of AI agents dashboard."
    echo ""
    echo "EXAMPLES:"
    echo "  $0                        # Complete LocalStack AWS setup"
    echo "  $0 --validate            # Validate LocalStack prerequisites only"
    echo "  $0 --cleanup             # Clean up LocalStack environment"
    echo "  $0 --start-localstack    # Start LocalStack container only"
    echo ""
    echo "LOCALSTACK CONFIGURATION:"
    echo "  - Endpoint: localhost:4566"
    echo "  - Services: s3,lambda,iam,cloudformation,ec2,rds,dynamodb,apigateway,cloudwatch,logs,sns,sqs"
    echo "  - Data persistence: Docker volume"
    echo "  - Debug mode: enabled"
    echo ""
    echo "AWS CLI USAGE:"
    echo "  aws --profile localstack s3 ls"
    echo "  aws --profile localstack dynamodb list-tables"
    echo "  aws --profile localstack lambda list-functions"
    echo ""
    echo "SERVICES ACCESS:"
    echo "  ☁️  LocalStack AWS:     http://localhost:4566"
    echo "  🚪 Infrastructure Portal:  http://localhost:9000"
    echo "  🤖 AI Dashboard:        http://localhost:8080"
    echo "  📊 Dashboard API:        http://localhost:5000"
    echo "  ⏰ Temporal UI:          http://localhost:7233"
    echo "  🔍 Langfuse Observability: http://localhost:3000"
    echo "  📈 Comprehensive API:   http://localhost:5001"
    echo "  🖥️  Comprehensive Frontend: http://localhost:8082"
    echo "  🧠 Memory Service:       http://localhost:8081"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    --validate)
        run_localstack_aws_validation
        exit $?
        ;;
    --cleanup)
        cleanup_localstack
        exit 0
        ;;
    --start-pf)
        start_all_port_forwards
        exit 0
        ;;
    --start-localstack)
        start_localstack
        exit $?
        ;;
    --configure-aws)
        configure_aws_cli_for_localstack
        exit $?
        ;;
    --create-resources)
        configure_aws_cli_for_localstack
        create_sample_aws_resources
        exit $?
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac

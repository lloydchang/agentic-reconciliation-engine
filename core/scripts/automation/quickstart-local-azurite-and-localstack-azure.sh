#!/bin/bash
# Agentic Reconciliation Engine - Quick Start for Local Azurite + LocalStack Azure Development
# Repository setup and initial onboarding for Azurite (Azure Storage) + LocalStack (Azure services) emulation

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

# Environment-specific validation for Azurite + LocalStack Azure
run_azurite_azure_validation() {
    ERRORS=0
    WARNINGS=0

    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}║  agentic-reconciliation-engine — Azurite + LocalStack Azure Validation ║${RESET}"
    echo -e "${BOLD}╚══════════════════════════════════════════════════════════════════╝${RESET}"
    echo ""

    # 1. Azurite and LocalStack prerequisites
    echo -e "${BOLD}[1/7] Checking Azurite and LocalStack prerequisites${RESET}"

    # Check Docker (required for both Azurite and LocalStack)
    if command -v docker &>/dev/null; then
        local docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        if docker system info &>/dev/null; then
            pass "Docker available (${docker_version})"
        else
            fail "Docker daemon not accessible"
        fi
    else
        fail "Docker not found (required for Azurite and LocalStack)"
    fi

    # Check Azure CLI
    if command -v az &>/dev/null; then
        local az_version=$(az version --query '"azure-cli"' -o tsv 2>/dev/null || echo "unknown")
        pass "Azure CLI available (${az_version})"
    else
        fail "Azure CLI not found (required for Azure skill testing)"
    fi

    # Check if Azurite is running
    if curl -sf http://localhost:10000 &>/dev/null || curl -sf http://localhost:10001 &>/dev/null; then
        pass "Azurite is running on localhost:10000/10001"
    else
        warn "Azurite not running on localhost:10000/10001 - will be started"
    fi

    # Check if LocalStack Azure services are running
    if curl -sf http://localhost:4566/_localstack/health &>/dev/null; then
        pass "LocalStack is running on localhost:4566"
    else
        warn "LocalStack not running on localhost:4566 - will be started"
    fi

    echo ""

    # 2. Standard CLI tools (Azure-focused)
    echo -e "${BOLD}[2/7] Checking required CLI tools${RESET}"

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

    # Required for Azure
    check_tool "terraform"  "1.6"
    check_tool "jq"         "1.6"
    check_tool "yq"         "4.0"

    # Optional but recommended
    check_tool_optional "kubectl"
    check_tool_optional "helm"
    check_tool_optional "checkov"

    echo ""

    # 3. Azure configuration
    echo -e "${BOLD}[3/7] Checking Azure configuration${RESET}"

    # Check Azure CLI login status
    if az account show &>/dev/null; then
        pass "Azure CLI logged in"
        local sub_name=$(az account show --query name -o tsv 2>/dev/null)
        info "Azure subscription: ${sub_name}"
    else
        warn "Azure CLI not logged in - LocalStack will use default credentials"
    fi

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

    check_env_optional "AZURE_STORAGE_ACCOUNT"
    check_env_optional "AZURE_STORAGE_KEY"
    check_env_optional "AZURE_SUBSCRIPTION_ID"
    check_env_optional "AZURE_TENANT_ID"
    check_env_optional "LOCALSTACK_API_KEY"

    # Check LocalStack Azure services configuration
    local services=${SERVICES:-"s3,lambda,iam,cloudformation,ec2,rds,dynamodb,apigateway,cloudwatch,logs"}
    pass "LocalStack services: ${services}"

    echo ""

    # 4. Resource requirements check
    echo -e "${BOLD}[4/7] Checking resource requirements${RESET}"

    # Check available memory
    local mem_gb=$(docker system info --format '{{.MemTotal}}' 2>/dev/null | awk '{print int($1/1024/1024/1024)}' || echo "unknown")
    if [[ "$mem_gb" != "unknown" && $mem_gb -ge 6 ]]; then
        pass "Available memory: ${mem_gb}GB (sufficient for Azurite + LocalStack)"
    else
        warn "Available memory: ${mem_gb}GB (may be insufficient - recommend 6GB+)"
    fi

    # Check available disk space
    local disk_gb=$(df -BG . | tail -1 | awk '{print int($4)}')
    if [[ $disk_gb -ge 15 ]]; then
        pass "Available disk space: ${disk_gb}GB (sufficient)"
    else
        warn "Available disk space: ${disk_gb}GB (may be insufficient - recommend 15GB+)"
    fi

    echo ""

    # 5. Network requirements
    echo -e "${BOLD}[5/7] Checking network requirements${RESET}"

    # Check for port conflicts
    local ports=(10000 10001 10002 4566 8080)
    for port in "${ports[@]}"; do
        if lsof -i ":${port}" &>/dev/null; then
            if [[ $port -eq 4566 ]]; then
                # Port 4566 might be LocalStack
                if curl -sf http://localhost:4566/_localstack/health &>/dev/null; then
                    pass "Port ${port} in use by LocalStack"
                else
                    warn "Port ${port} in use by another service"
                fi
            elif [[ $port -ge 10000 && $port -le 10002 ]]; then
                # Ports 10000-10002 might be Azurite
                if curl -sf http://localhost:${port} &>/dev/null; then
                    pass "Port ${port} in use by Azurite"
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
    echo -e "${BOLD}[6/7] Running Azurite + LocalStack smoke tests${RESET}"

    if docker ps | grep -q azurite; then
        pass "Azurite container is running"
    else
        info "Azurite container not running - will be started"
    fi

    if docker ps | grep -q localstack; then
        pass "LocalStack container is running"
    else
        info "LocalStack container not running - will be started"
    fi

    if command -v az &>/dev/null; then
        # Test Azure CLI configuration
        if az configure --list-defaults &>/dev/null; then
            pass "Azure CLI configured"
        else
            warn "Azure CLI not fully configured - LocalStack will use default settings"
        fi
    fi

    echo ""

    # 7. Azure Storage emulator test
    echo -e "${BOLD}[7/7] Testing Azure Storage emulator${RESET}"

    # Test Azurite blob storage
    if curl -sf http://localhost:10000/devstoreaccount1 &>/dev/null; then
        pass "Azurite blob storage accessible"
    else
        info "Azurite blob storage not accessible - will be started"
    fi

    # Test Azurite queue storage
    if curl -sf http://localhost:10001/devstoreaccount1 &>/dev/null; then
        pass "Azurite queue storage accessible"
    else
        info "Azurite queue storage not accessible - will be started"
    fi

    # Test Azurite table storage
    if curl -sf http://localhost:10002/devstoreaccount1 &>/dev/null; then
        pass "Azurite table storage accessible"
    else
        info "Azurite table storage not accessible - will be started"
    fi

    echo ""

    # Summary
    echo -e "${BOLD}══════════════════════════════════════════════════════════════════${RESET}"
    if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}  ✓ Azurite + LocalStack Azure validation PASSED — ready for local Azure development${RESET}"
    elif [[ $ERRORS -eq 0 ]]; then
        echo -e "${YELLOW}${BOLD}  ⚠ Azurite + LocalStack Azure validation PASSED with ${WARNINGS} warning(s)${RESET}"
        echo -e "${YELLOW}  Local Azure development may have degraded functionality.${RESET}"
    else
        echo -e "${RED}${BOLD}  ✗ Azurite + LocalStack Azure validation FAILED — ${ERRORS} error(s), ${WARNINGS} warning(s)${RESET}"
        echo -e "${RED}  Fix the errors above before proceeding.${RESET}"
        echo ""
        echo -e "  ${CYAN}Quick fixes:${RESET}"
        echo -e "    brew install docker azure-cli jq yq  # Install required tools"
        echo -e "    docker run -d --name azurite -p 10000-10002:10000-10002 mcr.microsoft.com/azure-storage/azurite  # Start Azurite"
        echo -e "    docker run -d --name localstack -p 4566:4566 localstack/localstack:3.0  # Start LocalStack"
    fi
    echo -e "${BOLD}══════════════════════════════════════════════════════════════════${RESET}"
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

# Start Azurite (Azure Storage Emulator)
start_azurite() {
    print_header "Starting Azurite (Azure Storage Emulator)"

    # Check if Azurite is already running
    if curl -sf http://localhost:10000/devstoreaccount1 &>/dev/null && \
       curl -sf http://localhost:10001/devstoreaccount1 &>/dev/null && \
       curl -sf http://localhost:10002/devstoreaccount1 &>/dev/null; then
        print_info "Azurite is already running"
        return 0
    fi

    # Check if container exists but is stopped
    if docker ps -a | grep -q azurite; then
        print_info "Starting existing Azurite container..."
        if docker start azurite; then
            print_success "Azurite container started"
            print_info "Waiting for Azurite to be ready..."
            sleep 5
            return 0
        else
            print_warning "Failed to start existing container, will create new one"
        fi
    fi

    print_info "Starting Azurite with Azure Storage emulation..."

    # Run Azurite container
    if docker run -d --name azurite \
        --rm \
        -p 10000:10000 \
        -p 10001:10001 \
        -p 10002:10002 \
        -v azurite-data:/data \
        mcr.microsoft.com/azure-storage/azurite; then

        print_success "Azurite container started"
        print_info "Waiting for Azurite to initialize..."

        # Wait for Azurite to be ready
        local attempts=0
        local max_attempts=20
        while [[ $attempts -lt $max_attempts ]]; do
            if curl -sf http://localhost:10000/devstoreaccount1 &>/dev/null; then
                print_success "Azurite is ready!"
                print_info "Blob storage: http://localhost:10000/devstoreaccount1"
                print_info "Queue storage: http://localhost:10001/devstoreaccount1"
                print_info "Table storage: http://localhost:10002/devstoreaccount1"
                return 0
            fi
            ((attempts++))
            sleep 2
        done

        print_error "Azurite failed to become ready within expected time"
        return 1
    else
        print_error "Failed to start Azurite container"
        return 1
    fi
}

# Start LocalStack with Azure services
start_localstack_azure() {
    print_header "Starting LocalStack (Azure Services)"

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

    print_info "Starting LocalStack with Azure services..."

    # Set environment variables for LocalStack Azure
    local env_vars=(
        "-e SERVICES=s3,lambda,iam,cloudformation,ec2,rds,dynamodb,apigateway,cloudwatch,logs"
        "-e DEBUG=1"
        "-e LAMBDA_EXECUTOR=docker"
        "-e DOCKER_HOST=unix:///var/run/docker.sock"
        "-e HOST_TMP_FOLDER=${TMPDIR:-/tmp/}localstack"
        "-e PERSISTENCE=1"
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
        -v "localstack-azure-data:/tmp/localstack" \
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

# Configure Azure CLI for local development
configure_azure_cli_for_local() {
    print_header "Configuring Azure CLI for Local Development"

    print_info "Configuring Azure CLI to use Azurite and LocalStack endpoints..."

    # Set Azure CLI to use local endpoints
    export AZURE_STORAGE_ACCOUNT=${AZURE_STORAGE_ACCOUNT:-devstoreaccount1}
    export AZURE_STORAGE_KEY=${AZURE_STORAGE_KEY:-Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==}
    export AZURE_SUBSCRIPTION_ID=${AZURE_SUBSCRIPTION_ID:-00000000-0000-0000-0000-000000000000}
    export AZURE_TENANT_ID=${AZURE_TENANT_ID:-00000000-0000-0000-0000-000000000000}

    print_success "Azure CLI configured for local development"
    print_info "Storage Account: ${AZURE_STORAGE_ACCOUNT}"
    print_info "Storage Key: ${AZURE_STORAGE_KEY:0:10}..."
}

# Create sample Azure resources
create_sample_azure_resources() {
    print_header "Creating Sample Azure Resources"

    print_info "Creating sample Azure resources in Azurite and LocalStack..."

    # Create Azure Storage containers (Azurite)
    print_info "Creating Azure Storage containers..."

    # Note: Using curl to create containers since az storage commands might not work with Azurite
    # Blob container
    if curl -sf -X PUT "http://localhost:10000/devstoreaccount1/test-container?restype=container" \
        -H "Authorization: SharedKey devstoreaccount1:Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="; then
        print_success "Created blob container: test-container"
    else
        print_warning "Failed to create blob container"
    fi

    # Create Azure resources in LocalStack (mapped to AWS services)
    print_info "Creating Azure-mapped resources in LocalStack..."

    # Set AWS CLI to use LocalStack (for Azure services)
    export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-test}
    export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-test}
    export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-eastus}

    # Create S3 bucket (maps to Azure Blob Storage)
    if aws s3 mb s3://agentic-test-blob --endpoint-url=http://localhost:4566; then
        print_success "Created S3 bucket (Azure Blob): agentic-test-blob"
    else
        print_warning "Failed to create S3 bucket"
    fi

    # Create DynamoDB table (maps to Azure Table Storage)
    if aws dynamodb create-table \
        --table-name agentic-test-table \
        --attribute-definitions AttributeName=PartitionKey,AttributeType=S \
        --key-schema AttributeName=PartitionKey,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --endpoint-url=http://localhost:4566; then
        print_success "Created DynamoDB table (Azure Table): agentic-test-table"
    else
        print_warning "Failed to create DynamoDB table"
    fi

    print_success "Sample Azure resources created"
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
        print_info "For Azure development, you may want to run a local K8s cluster first"
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
        echo "  🧹 Clean up: ./core/scripts/automation/quickstart-local-azurite-and-localstack-azure.sh --cleanup"
        echo "  🔄 Restart: ./core/scripts/automation/quickstart-local-azurite-and-localstack-azure.sh --start-pf"
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

# Enhanced cleanup function for Azurite + LocalStack
cleanup_azurite_azure() {
    print_header "Cleaning up Azurite + LocalStack Azure environment"

    # Stop all port-forwards
    cleanup_port_forwards

    # Stop Azurite container
    if docker ps | grep -q azurite; then
        print_info "Stopping Azurite container..."
        if docker stop azurite; then
            print_success "Azurite container stopped"
        else
            print_warning "Failed to stop Azurite container"
        fi
    fi

    # Remove Azurite container
    if docker ps -a | grep -q azurite; then
        print_info "Removing Azurite container..."
        if docker rm azurite; then
            print_success "Azurite container removed"
        else
            print_warning "Failed to remove Azurite container"
        fi
    fi

    # Remove Azurite data volume
    if docker volume ls | grep -q azurite-data; then
        print_info "Removing Azurite data volume..."
        if docker volume rm azurite-data; then
            print_success "Azurite data volume removed"
        else
            print_warning "Failed to remove Azurite data volume"
        fi
    fi

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

    # Remove LocalStack data volume
    if docker volume ls | grep -q localstack-azure-data; then
        print_info "Removing LocalStack data volume..."
        if docker volume rm localstack-azure-data; then
            print_success "LocalStack data volume removed"
        else
            print_warning "Failed to remove LocalStack data volume"
        fi
    fi

    print_success "Azurite + LocalStack Azure environment cleanup completed"
}

# Main function for Azurite + LocalStack Azure quickstart
main() {
    print_header "Agentic Reconciliation Engine - Azurite + LocalStack Azure Quick Start"

    echo -e "${BLUE}Welcome to Agentic Reconciliation Engine - Azurite + LocalStack Azure Development!${NC}"
    echo ""
    echo -e "${YELLOW}This will set up Azurite (Azure Storage) and LocalStack (Azure services) for local Azure emulation.${NC}"
    echo ""

    # Check if we're in the right directory
    if [[ ! -f "$REPO_ROOT/README.md" ]]; then
        print_error "Not in repository root. Please run from repository root."
        exit 1
    fi

    # Run Azurite + LocalStack Azure-specific validation
    print_info "Running Azurite + LocalStack Azure-specific prerequisites validation..."
    if ! run_azurite_azure_validation; then
        print_error "Azurite + LocalStack Azure validation failed. Please fix errors above and retry."
        exit 1
    fi

    # If there are warnings, prompt user to continue
    if [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Found $WARNINGS warning(s). Continue with Azurite + LocalStack Azure setup? (Y/n)${NC}"
        read -r response
        if [[ "$response" =~ ^[Nn]$ ]]; then
            print_info "Azurite + LocalStack Azure setup cancelled by user."
            exit 0
        fi
    fi

    # Run pre-quickstart hook
    run_hooks "pre-quickstart" || return 1

    # Setup basic configuration
    print_info "Setting up Azurite + LocalStack Azure development environment..."

    # Create basic directories if they don't exist
    mkdir -p logs/
    mkdir -p tmp/

    # Make scripts executable
    find "$SCRIPT_DIR" -name "*.sh" -exec chmod +x {} \;
    find "$SCRIPT_DIR" -name "*.py" -exec chmod +x {} \;

    print_success "Azurite + LocalStack Azure development environment ready"

    # Start Azurite
    start_azurite || return 1

    # Start LocalStack Azure
    start_localstack_azure || return 1

    # Configure Azure CLI for local development
    configure_azure_cli_for_local || return 1

    # Create sample Azure resources
    create_sample_azure_resources || return 1

    # Run post-quickstart hook
    run_hooks "post-quickstart" || return 1

    # Deploy AI agents dashboard
    deploy_ai_agents_dashboard || return 1

    # Deploy AI Agent Skills and MCP servers
    deploy_ai_agent_skills || return 1

    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Access your AI agents dashboard at http://localhost:8080"
    echo "2. Test Azure skills against Azurite and LocalStack:"
    echo "   Azure Storage: Use connection string with Azurite endpoints"
    echo "   Azure services: Use LocalStack endpoints"
    echo "3. Configure Claude Desktop with AI Agent Skills (auto-configured)"
    echo "4. Use consolidated K8sGPT: http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
    echo "5. View Azurite logs: docker logs azurite"
    echo "6. View LocalStack logs: docker logs localstack"
    echo "7. Clean up environment: ./core/scripts/automation/quickstart-local-azurite-and-localstack-azure.sh --cleanup"
    echo ""
    echo -e "${GREEN}🚀 Azurite + LocalStack Azure development environment is ready!${NC}"
    echo -e "${YELLOW}🧠 AI agents are fully operational!${NC}"
    echo -e "${BLUE}☁️  Azure Storage emulator (Azurite) is running on localhost:10000-10002${NC}"
    echo -e "${CYAN}☁️  Azure services (LocalStack) are running on localhost:4566${NC}"
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
    echo "Agentic Reconciliation Engine - Azurite + LocalStack Azure Quick Start"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help         Show this help message"
    echo "  --validate         Run Azurite + LocalStack Azure validation only"
    echo "  --cleanup          Clean up Azurite and LocalStack containers and resources"
    echo "  --start-pf         Start all port-forwards (if not already running)"
    echo "  --start-azurite    Start Azurite container only"
    echo "  --start-localstack Start LocalStack container only"
    echo "  --configure-azure  Configure Azure CLI for local development only"
    echo "  --create-resources Create sample Azure resources in Azurite and LocalStack"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up Azurite (Azure Storage emulator) and LocalStack (Azure services)"
    echo "  for local Azure service emulation and deployment of AI agents dashboard."
    echo ""
    echo "EXAMPLES:"
    echo "  $0                           # Complete Azurite + LocalStack Azure setup"
    echo "  $0 --validate               # Validate Azurite + LocalStack Azure prerequisites only"
    echo "  $0 --cleanup                # Clean up Azurite + LocalStack Azure environment"
    echo "  $0 --start-azurite          # Start Azurite container only"
    echo "  $0 --start-localstack       # Start LocalStack container only"
    echo ""
    echo "AZURITE CONFIGURATION:"
    echo "  - Blob Storage: localhost:10000"
    echo "  - Queue Storage: localhost:10001"
    echo "  - Table Storage: localhost:10002"
    echo "  - Account: devstoreaccount1"
    echo "  - Key: Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="
    echo ""
    echo "LOCALSTACK CONFIGURATION:"
    echo "  - Endpoint: localhost:4566"
    echo "  - Services: s3,lambda,iam,cloudformation,ec2,rds,dynamodb,apigateway,cloudwatch,logs"
    echo "  - Persistence: enabled"
    echo ""
    echo "SERVICES ACCESS:"
    echo "  ☁️  Azurite Blob:       http://localhost:10000"
    echo "  ☁️  Azurite Queue:      http://localhost:10001"
    echo "  ☁️  Azurite Table:      http://localhost:10002"
    echo "  ☁️  LocalStack Azure:   http://localhost:4566"
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
        run_azurite_azure_validation
        exit $?
        ;;
    --cleanup)
        cleanup_azurite_azure
        exit 0
        ;;
    --start-pf)
        start_all_port_forwards
        exit 0
        ;;
    --start-azurite)
        start_azurite
        exit $?
        ;;
    --start-localstack)
        start_localstack_azure
        exit $?
        ;;
    --configure-azure)
        configure_azure_cli_for_local
        exit $?
        ;;
    --create-resources)
        configure_azure_cli_for_local
        create_sample_azure_resources
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

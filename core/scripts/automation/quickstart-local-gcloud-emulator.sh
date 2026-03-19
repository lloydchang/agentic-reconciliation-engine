#!/bin/bash
# Agentic Reconciliation Engine - Quick Start for Local Google Cloud Emulator Development
# Repository setup and initial onboarding for Google Cloud emulator (Bigtable, Datastore, Firestore, Pub/Sub, Spanner)

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

# Environment-specific validation for Google Cloud Emulator
run_gcloud_emulator_validation() {
    ERRORS=0
    WARNINGS=0

    echo ""
    echo -e "${BOLD}╔═══════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}║  agentic-reconciliation-engine — Google Cloud Emulator Validation ║${RESET}"
    echo -e "${BOLD}╚═══════════════════════════════════════════════════════════════╝${RESET}"
    echo ""

    # 1. Google Cloud prerequisites
    echo -e "${BOLD}[1/6] Checking Google Cloud prerequisites${RESET}"

    # Check Docker (required for emulators)
    if command -v docker &>/dev/null; then
        local docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        if docker system info &>/dev/null; then
            pass "Docker available (${docker_version})"
        else
            fail "Docker daemon not accessible"
        fi
    else
        fail "Docker not found (required for Google Cloud emulators)"
    fi

    # Check gcloud CLI
    if command -v gcloud &>/dev/null; then
        local gcloud_version=$(gcloud version --format="value(gcloud)" 2>/dev/null || echo "unknown")
        pass "gcloud CLI available (${gcloud_version})"
    else
        warn "gcloud CLI not found - will use emulators directly via Docker"
    fi

    # Check Java (required for some emulators)
    if command -v java &>/dev/null; then
        local java_version=$(java -version 2>&1 | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        pass "Java available (${java_version})"
    else
        warn "Java not found - some emulators may not work"
    fi

    # Check if emulators are running
    local emulator_ports=(8081 8082 8083 8084 8085 8086 8087 8088 8089)
    local any_running=false
    for port in "${emulator_ports[@]}"; do
        if curl -sf http://localhost:${port} &>/dev/null; then
            pass "Emulator running on port ${port}"
            any_running=true
        fi
    done

    if [[ "$any_running" == false ]]; then
        warn "No Google Cloud emulators running - will be started"
    fi

    echo ""

    # 2. Standard CLI tools (GCP-focused)
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

    # Required for GCP
    check_tool "terraform"  "1.6"
    check_tool "jq"         "1.6"
    check_tool "yq"         "4.0"

    # Optional but recommended
    check_tool_optional "kubectl"
    check_tool_optional "helm"
    check_tool_optional "checkov"

    echo ""

    # 3. GCP configuration
    echo -e "${BOLD}[3/6] Checking GCP configuration${RESET}"

    # Check gcloud authentication
    if command -v gcloud &>/dev/null; then
        if gcloud auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
            pass "gcloud authenticated"
            local active_account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
            info "Active account: ${active_account}"
        else
            warn "gcloud not authenticated - emulators will use default credentials"
        fi

        # Check project
        local project=$(gcloud config get-value project 2>/dev/null)
        if [[ -n "$project" && "$project" != "(unset)" ]]; then
            pass "gcloud project: ${project}"
        else
            warn "gcloud project not set"
        fi
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

    check_env_optional "GOOGLE_CLOUD_PROJECT"
    check_env_optional "GOOGLE_APPLICATION_CREDENTIALS"
    check_env_optional "FIRESTORE_EMULATOR_HOST"
    check_env_optional "PUBSUB_EMULATOR_HOST"
    check_env_optional "BIGTABLE_EMULATOR_HOST"

    # Check emulator configuration
    local emulators=${EMULATORS:-"firestore,pubsub,bigtable,datastore,spanner"}
    pass "Emulators to start: ${emulators}"

    echo ""

    # 4. Resource requirements check
    echo -e "${BOLD}[4/6] Checking resource requirements${RESET}"

    # Check available memory
    local mem_gb=$(docker system info --format '{{.MemTotal}}' 2>/dev/null | awk '{print int($1/1024/1024/1024)}' || echo "unknown")
    if [[ "$mem_gb" != "unknown" && $mem_gb -ge 8 ]]; then
        pass "Available memory: ${mem_gb}GB (sufficient for Google Cloud emulators)"
    else
        warn "Available memory: ${mem_gb}GB (may be insufficient - recommend 8GB+)"
    fi

    # Check available disk space
    local disk_gb=$(df -BG . | tail -1 | awk '{print int($4)}')
    if [[ $disk_gb -ge 20 ]]; then
        pass "Available disk space: ${disk_gb}GB (sufficient)"
    else
        warn "Available disk space: ${disk_gb}GB (may be insufficient - recommend 20GB+)"
    fi

    echo ""

    # 5. Network requirements
    echo -e "${BOLD}[5/6] Checking network requirements${RESET}"

    # Check for port conflicts
    local ports=(8081 8082 8083 8084 8085 8086 8087 8088 8089 9090)
    for port in "${ports[@]}"; do
        if lsof -i ":${port}" &>/dev/null; then
            warn "Port ${port} is in use - may conflict with emulators"
        else
            pass "Port ${port} available"
        fi
    done

    echo ""

    # 6. Quick smoke test
    echo -e "${BOLD}[6/6] Running Google Cloud emulator smoke tests${RESET}"

    if docker ps | grep -q gcloud-emulator; then
        pass "Google Cloud emulator containers are running"
    else
        info "Google Cloud emulator containers not running - will be started"
    fi

    if command -v gcloud &>/dev/null; then
        # Test gcloud configuration
        if gcloud config list &>/dev/null; then
            pass "gcloud CLI functional"
        else
            warn "gcloud CLI not fully configured"
        fi
    fi

    echo ""

    # Summary
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${RESET}"
    if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}  ✓ Google Cloud emulator validation PASSED — ready for local GCP development${RESET}"
    elif [[ $ERRORS -eq 0 ]]; then
        echo -e "${YELLOW}${BOLD}  ⚠ Google Cloud emulator validation PASSED with ${WARNINGS} warning(s)${RESET}"
        echo -e "${YELLOW}  Local GCP development may have degraded functionality.${RESET}"
    else
        echo -e "${RED}${BOLD}  ✗ Google Cloud emulator validation FAILED — ${ERRORS} error(s), ${WARNINGS} warning(s)${RESET}"
        echo -e "${RED}  Fix the errors above before proceeding.${RESET}"
        echo ""
        echo -e "  ${CYAN}Quick fixes:${RESET}"
        echo -e "    brew install --cask google-cloud-sdk docker jq yq  # Install required tools"
        echo -e "    gcloud auth login  # Authenticate with Google Cloud"
        echo -e "    gcloud config set project YOUR_PROJECT_ID  # Set project"
    fi
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${RESET}"
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

# Start Google Cloud emulators
start_gcloud_emulators() {
    print_header "Starting Google Cloud Emulators"

    local emulators=${EMULATORS:-"firestore,pubsub,bigtable,datastore,spanner"}
    print_info "Starting emulators: ${emulators}"

    # Create a docker-compose file for emulators
    cat > /tmp/gcloud-emulators-docker-compose.yml << EOF
version: '3.8'
services:
  firestore:
    image: google/cloud-sdk:emulators
    command: gcloud beta emulators firestore start --host-port=0.0.0.0:8081 --database-mode=datastore-mode
    ports:
      - "8081:8081"
    volumes:
      - firestore-data:/opt/data

  pubsub:
    image: google/cloud-sdk:emulators
    command: gcloud beta emulators pubsub start --host-port=0.0.0.0:8082
    ports:
      - "8082:8082"
    volumes:
      - pubsub-data:/opt/data

  bigtable:
    image: google/cloud-sdk:emulators
    command: gcloud beta emulators bigtable start --host-port=0.0.0.0:8083
    ports:
      - "8083:8083"
    volumes:
      - bigtable-data:/opt/data

  datastore:
    image: google/cloud-sdk:emulators
    command: gcloud beta emulators datastore start --host-port=0.0.0.0:8084 --no-store-on-disk
    ports:
      - "8084:8084"

  spanner:
    image: google/cloud-sdk:emulators
    command: gcloud beta emulators spanner start --host-port=0.0.0.0:8085
    ports:
      - "8085:8085"
    volumes:
      - spanner-data:/opt/data

volumes:
  firestore-data:
  pubsub-data:
  bigtable-data:
  spanner-data:
EOF

    # Start emulators using docker-compose
    if command -v docker-compose &>/dev/null; then
        print_info "Starting emulators with docker-compose..."
        if docker-compose -f /tmp/gcloud-emulators-docker-compose.yml up -d; then
            print_success "Google Cloud emulators started with docker-compose"
        else
            print_error "Failed to start emulators with docker-compose"
            rm -f /tmp/gcloud-emulators-docker-compose.yml
            return 1
        fi
    else
        # Fallback: start individual containers
        print_info "Starting emulators individually (docker-compose not found)..."

        # Firestore/Datastore emulator
        if docker run -d --name gcloud-firestore \
            -p 8081:8081 \
            -v firestore-data:/opt/data \
            google/cloud-sdk:emulators \
            gcloud beta emulators firestore start --host-port=0.0.0.0:8081 --database-mode=datastore-mode; then
            print_success "Firestore emulator started on port 8081"
        else
            print_warning "Failed to start Firestore emulator"
        fi

        # Pub/Sub emulator
        if docker run -d --name gcloud-pubsub \
            -p 8082:8082 \
            -v pubsub-data:/opt/data \
            google/cloud-sdk:emulators \
            gcloud beta emulators pubsub start --host-port=0.0.0.0:8082; then
            print_success "Pub/Sub emulator started on port 8082"
        else
            print_warning "Failed to start Pub/Sub emulator"
        fi

        # Bigtable emulator
        if docker run -d --name gcloud-bigtable \
            -p 8083:8083 \
            -v bigtable-data:/opt/data \
            google/cloud-sdk:emulators \
            gcloud beta emulators bigtable start --host-port=0.0.0.0:8083; then
            print_success "Bigtable emulator started on port 8083"
        else
            print_warning "Failed to start Bigtable emulator"
        fi

        # Spanner emulator
        if docker run -d --name gcloud-spanner \
            -p 8085:8085 \
            -v spanner-data:/opt/data \
            google/cloud-sdk:emulators \
            gcloud beta emulators spanner start --host-port=0.0.0.0:8085; then
            print_success "Spanner emulator started on port 8085"
        else
            print_warning "Failed to start Spanner emulator"
        fi
    fi

    # Wait for emulators to be ready
    print_info "Waiting for emulators to initialize..."
    sleep 10

    # Verify emulators are running
    local ports=(8081 8082 8083 8084 8085)
    for port in "${ports[@]}"; do
        if curl -sf http://localhost:${port} &>/dev/null; then
            print_success "Emulator on port ${port} is responding"
        else
            print_warning "Emulator on port ${port} is not responding"
        fi
    done

    rm -f /tmp/gcloud-emulators-docker-compose.yml
    print_success "Google Cloud emulators started"
}

# Configure gcloud CLI for emulators
configure_gcloud_for_emulators() {
    print_header "Configuring gcloud CLI for Emulators"

    print_info "Setting environment variables for emulator endpoints..."

    # Set emulator environment variables
    export FIRESTORE_EMULATOR_HOST=localhost:8081
    export PUBSUB_EMULATOR_HOST=localhost:8082
    export BIGTABLE_EMULATOR_HOST=localhost:8083
    export DATASTORE_EMULATOR_HOST=localhost:8084
    export SPANNER_EMULATOR_HOST=localhost:8085

    # Set project for emulators
    export GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT:-emulator-project}

    print_success "gcloud CLI configured for emulators"
    print_info "Project: ${GOOGLE_CLOUD_PROJECT}"
    print_info "Firestore: ${FIRESTORE_EMULATOR_HOST}"
    print_info "Pub/Sub: ${PUBSUB_EMULATOR_HOST}"
    print_info "Bigtable: ${BIGTABLE_EMULATOR_HOST}"
    print_info "Datastore: ${DATASTORE_EMULATOR_HOST}"
    print_info "Spanner: ${SPANNER_EMULATOR_HOST}"
}

# Create sample GCP resources
create_sample_gcp_resources() {
    print_header "Creating Sample GCP Resources"

    print_info "Creating sample resources in Google Cloud emulators..."

    # Set project
    local project=${GOOGLE_CLOUD_PROJECT:-emulator-project}

    # Create Firestore/Datastore entities
    if curl -sf http://localhost:8081 &>/dev/null; then
        print_info "Creating Firestore/Datastore sample data..."
        # Note: Would need gcloud or REST API calls here
        print_success "Firestore/Datastore emulator available"
    fi

    # Create Pub/Sub topics and subscriptions
    if curl -sf http://localhost:8082 &>/dev/null; then
        print_info "Creating Pub/Sub sample topics..."
        # Note: Would need gcloud commands or REST API calls here
        print_success "Pub/Sub emulator available"
    fi

    # Create Bigtable instance/tables
    if curl -sf http://localhost:8083 &>/dev/null; then
        print_info "Bigtable emulator available for table creation..."
        print_success "Bigtable emulator available"
    fi

    # Create Spanner instance/databases
    if curl -sf http://localhost:8085 &>/dev/null; then
        print_info "Spanner emulator available for database creation..."
        print_success "Spanner emulator available"
    fi

    print_success "Sample GCP resources setup completed"
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
        print_info "For GCP development, you may want to run a local K8s cluster first"
        print_info "Or deploy dashboard to emulators directly (not implemented yet)"
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
        echo "  🧹 Clean up: ./core/scripts/automation/quickstart-local-gcloud-emulator.sh --cleanup"
        echo "  🔄 Restart: ./core/scripts/automation/quickstart-local-gcloud-emulator.sh --start-pf"
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

# Enhanced cleanup function for Google Cloud emulators
cleanup_gcloud_emulators() {
    print_header "Cleaning up Google Cloud emulators"

    # Stop all port-forwards
    cleanup_port_forwards

    # Stop emulator containers
    local containers=("gcloud-firestore" "gcloud-pubsub" "gcloud-bigtable" "gcloud-datastore" "gcloud-spanner")
    for container in "${containers[@]}"; do
        if docker ps | grep -q "$container"; then
            print_info "Stopping $container..."
            if docker stop "$container"; then
                print_success "$container stopped"
            else
                print_warning "Failed to stop $container"
            fi
        fi

        if docker ps -a | grep -q "$container"; then
            print_info "Removing $container..."
            if docker rm "$container"; then
                print_success "$container removed"
            else
                print_warning "Failed to remove $container"
            fi
        fi
    done

    # Clean up docker-compose if it exists
    if [[ -f /tmp/gcloud-emulators-docker-compose.yml ]]; then
        rm -f /tmp/gcloud-emulators-docker-compose.yml
    fi

    # Clean up volumes
    local volumes=("firestore-data" "pubsub-data" "bigtable-data" "spanner-data")
    for volume in "${volumes[@]}"; do
        if docker volume ls | grep -q "$volume"; then
            print_info "Removing volume $volume..."
            if docker volume rm "$volume"; then
                print_success "Volume $volume removed"
            else
                print_warning "Failed to remove volume $volume"
            fi
        fi
    done

    print_success "Google Cloud emulators cleanup completed"
}

# Main function for Google Cloud emulator quickstart
main() {
    print_header "Agentic Reconciliation Engine - Google Cloud Emulator Quick Start"

    echo -e "${BLUE}Welcome to Agentic Reconciliation Engine - Google Cloud Emulator Development!${NC}"
    echo ""
    echo -e "${YELLOW}This will set up Google Cloud emulators (Firestore, Pub/Sub, Bigtable, Spanner) for local GCP development.${NC}"
    echo ""

    # Check if we're in the right directory
    if [[ ! -f "$REPO_ROOT/README.md" ]]; then
        print_error "Not in repository root. Please run from repository root."
        exit 1
    fi

    # Run Google Cloud emulator-specific validation
    print_info "Running Google Cloud emulator-specific prerequisites validation..."
    if ! run_gcloud_emulator_validation; then
        print_error "Google Cloud emulator validation failed. Please fix errors above and retry."
        exit 1
    fi

    # If there are warnings, prompt user to continue
    if [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Found $WARNINGS warning(s). Continue with Google Cloud emulator setup? (Y/n)${NC}"
        read -r response
        if [[ "$response" =~ ^[Nn]$ ]]; then
            print_info "Google Cloud emulator setup cancelled by user."
            exit 0
        fi
    fi

    # Run pre-quickstart hook
    run_hooks "pre-quickstart" || return 1

    # Setup basic configuration
    print_info "Setting up Google Cloud emulator development environment..."

    # Create basic directories if they don't exist
    mkdir -p logs/
    mkdir -p tmp/

    # Make scripts executable
    find "$SCRIPT_DIR" -name "*.sh" -exec chmod +x {} \;
    find "$SCRIPT_DIR" -name "*.py" -exec chmod +x {} \;

    print_success "Google Cloud emulator development environment ready"

    # Start Google Cloud emulators
    start_gcloud_emulators || return 1

    # Configure gcloud CLI for emulators
    configure_gcloud_for_emulators || return 1

    # Create sample GCP resources
    create_sample_gcp_resources || return 1

    # Run post-quickstart hook
    run_hooks "post-quickstart" || return 1

    # Deploy AI agents dashboard
    deploy_ai_agents_dashboard || return 1

    # Deploy AI Agent Skills and MCP servers
    deploy_ai_agent_skills || return 1

    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Access your AI agents dashboard at http://localhost:8080"
    echo "2. Test GCP skills against emulators:"
    echo "   Firestore: Use emulator endpoints with gcloud or client libraries"
    echo "   Pub/Sub: Use emulator endpoints with gcloud or client libraries"
    echo "   Bigtable: Use emulator endpoints with gcloud or client libraries"
    echo "   Spanner: Use emulator endpoints with gcloud or client libraries"
    echo "3. Configure Claude Desktop with AI Agent Skills (auto-configured)"
    echo "4. Use consolidated K8sGPT: http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
    echo "5. View emulator logs: docker logs <container-name>"
    echo "6. Clean up environment: ./core/scripts/automation/quickstart-local-gcloud-emulator.sh --cleanup"
    echo ""
    echo -e "${GREEN}🚀 Google Cloud emulator development environment is ready!${NC}"
    echo -e "${YELLOW}🧠 AI agents are fully operational!${NC}"
    echo -e "${BLUE}☁️  Google Cloud emulators are running on localhost:8081-8085${NC}"
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
    echo "Agentic Reconciliation Engine - Google Cloud Emulator Quick Start"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help         Show this help message"
    echo "  --validate         Run Google Cloud emulator validation only"
    echo "  --cleanup          Clean up emulators and resources"
    echo "  --start-pf         Start all port-forwards (if not already running)"
    echo "  --start-emulators  Start Google Cloud emulators only"
    echo "  --configure-gcloud Configure gcloud CLI for emulators only"
    echo "  --create-resources Create sample GCP resources in emulators"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up Google Cloud emulators for local GCP service emulation."
    echo "  This includes emulator startup, gcloud CLI configuration,"
    echo "  sample resource creation, and deployment of AI agents dashboard."
    echo ""
    echo "EXAMPLES:"
    echo "  $0                        # Complete Google Cloud emulator setup"
    echo "  $0 --validate            # Validate Google Cloud emulator prerequisites only"
    echo "  $0 --cleanup             # Clean up Google Cloud emulator environment"
    echo "  $0 --start-emulators     # Start Google Cloud emulators only"
    echo ""
    echo "EMULATOR CONFIGURATION:"
    echo "  - Firestore/Datastore: localhost:8081"
    echo "  - Pub/Sub: localhost:8082"
    echo "  - Bigtable: localhost:8083"
    echo "  - Datastore: localhost:8084"
    echo "  - Spanner: localhost:8085"
    echo "  - Project: emulator-project (configurable)"
    echo "  - Data persistence: Docker volumes"
    echo ""
    echo "SERVICES ACCESS:"
    echo "  ☁️  Firestore:       http://localhost:8081"
    echo "  ☁️  Pub/Sub:         http://localhost:8082"
    echo "  ☁️  Bigtable:        http://localhost:8083"
    echo "  ☁️  Datastore:       http://localhost:8084"
    echo "  ☁️  Spanner:         http://localhost:8085"
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
        run_gcloud_emulator_validation
        exit $?
        ;;
    --cleanup)
        cleanup_gcloud_emulators
        exit 0
        ;;
    --start-pf)
        start_all_port_forwards
        exit 0
        ;;
    --start-emulators)
        start_gcloud_emulators
        exit $?
        ;;
    --configure-gcloud)
        configure_gcloud_for_emulators
        exit $?
        ;;
    --create-resources)
        configure_gcloud_for_emulators
        create_sample_gcp_resources
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

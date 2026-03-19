#!/bin/bash
# Agentic Reconciliation Engine - Quick Start for Local Docker Desktop Development
# Repository setup and initial onboarding for Docker Desktop local development

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

# Environment-specific validation for Docker Desktop
run_docker_desktop_validation() {
    ERRORS=0
    WARNINGS=0

    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}║  agentic-reconciliation-engine — Docker Desktop Validation ║${RESET}"
    echo -e "${BOLD}╚══════════════════════════════════════════════════════════════╝${RESET}"
    echo ""

    # 1. Docker Desktop prerequisites
    echo -e "${BOLD}[1/6] Checking Docker Desktop prerequisites${RESET}"

    # Check Docker Desktop
    if command -v docker &>/dev/null; then
        local docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        pass "Docker available (${docker_version})"

        # Check if Docker Desktop is running
        if docker system info &>/dev/null; then
            pass "Docker daemon accessible"
        else
            fail "Docker daemon not accessible - start Docker Desktop"
        fi
    else
        fail "Docker not found - install Docker Desktop"
    fi

    # Check kubectl (comes with Docker Desktop)
    if command -v kubectl &>/dev/null; then
        local kube_version=$(kubectl version --client --short 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        pass "kubectl available (${kube_version})"
    else
        fail "kubectl not found - should come with Docker Desktop"
    fi

    # Check Docker Desktop Kubernetes
    if kubectl cluster-info &>/dev/null; then
        pass "Docker Desktop Kubernetes cluster accessible"
        local context=$(kubectl config current-context 2>/dev/null)
        if [[ "$context" == "docker-desktop" || "$context" == "docker-for-desktop" ]]; then
            pass "Using Docker Desktop Kubernetes context: ${context}"
        else
            warn "Current kubectl context is not Docker Desktop: ${context}"
        fi
    else
        fail "Docker Desktop Kubernetes cluster not accessible"
    fi

    echo ""

    # 2. Standard CLI tools (same as base validation)
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

    # Required
    check_tool "helm"       "3.12"
    check_tool "terraform"  "1.6"
    check_tool "jq"         "1.6"
    check_tool "yq"         "4.0"

    # Optional but recommended
    check_tool_optional "argocd"
    check_tool_optional "flux"
    check_tool_optional "istioctl"
    check_tool_optional "notation"
    check_tool_optional "trivy"
    check_tool_optional "k6"
    check_tool_optional "linkerd"
    check_tool_optional "checkov"

    echo ""

    # 3. Docker Desktop specific checks
    echo -e "${BOLD}[3/6] Checking Docker Desktop configuration${RESET}"

    # Check Docker Desktop resources
    if docker system info &>/dev/null; then
        local mem_gb=$(docker system info --format '{{.MemTotal}}' 2>/dev/null | awk '{print int($1/1024/1024/1024)}' || echo "unknown")
        if [[ "$mem_gb" != "unknown" ]]; then
            if [[ $mem_gb -ge 4 ]]; then
                pass "Docker Desktop memory: ${mem_gb}GB (sufficient)"
            else
                warn "Docker Desktop memory: ${mem_gb}GB (may be insufficient - increase in Docker Desktop settings)"
            fi
        fi

        local cpus=$(docker system info --format '{{.NCPU}}' 2>/dev/null || echo "unknown")
        if [[ "$cpus" != "unknown" && $cpus -ge 2 ]]; then
            pass "Docker Desktop CPUs: ${cpus} (sufficient)"
        else
            warn "Docker Desktop CPUs: ${cpus} (may be insufficient - increase in Docker Desktop settings)"
        fi
    fi

    # Check if Kubernetes is enabled in Docker Desktop
    if kubectl cluster-info &>/dev/null; then
        local node_count=$(kubectl get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')
        info "Kubernetes nodes available: ${node_count}"
    fi

    echo ""

    # 4. Local cluster state
    echo -e "${BOLD}[4/6] Checking local cluster state${RESET}"

    if kubectl cluster-info &>/dev/null; then
        pass "Docker Desktop Kubernetes cluster is running"
        if kubectl auth can-i get pods -n kube-system &>/dev/null; then
            pass "Cluster API accessible with permissions"
        else
            warn "Limited cluster API permissions"
        fi
    else
        warn "Docker Desktop Kubernetes cluster not running"
    fi

    echo ""

    # 5. Network requirements
    echo -e "${BOLD}[5/6] Checking network requirements${RESET}"

    # Check for port conflicts
    local ports=(80 443 3000 5000 5001 7233 8080 8081 8082 9000)
    for port in "${ports[@]}"; do
        if lsof -i ":${port}" &>/dev/null; then
            warn "Port ${port} is in use - may conflict with services"
        else
            pass "Port ${port} available"
        fi
    done

    echo ""

    # 6. Quick smoke test
    echo -e "${BOLD}[6/6] Running Docker Desktop smoke tests${RESET}"

    if docker run --rm hello-world &>/dev/null; then
        pass "Docker container execution functional"
    else
        warn "Docker container execution failed"
    fi

    if kubectl get nodes &>/dev/null; then
        pass "Kubernetes API functional"
    fi

    echo ""

    # Summary
    echo -e "${BOLD}══════════════════════════════════════════════════════════════${RESET}"
    if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}  ✓ Docker Desktop validation PASSED — ready for local development${RESET}"
    elif [[ $ERRORS -eq 0 ]]; then
        echo -e "${YELLOW}${BOLD}  ⚠ Docker Desktop validation PASSED with ${WARNINGS} warning(s)${RESET}"
        echo -e "${YELLOW}  Local development may have degraded performance.${RESET}"
    else
        echo -e "${RED}${BOLD}  ✗ Docker Desktop validation FAILED — ${ERRORS} error(s), ${WARNINGS} warning(s)${RESET}"
        echo -e "${RED}  Fix the errors above before proceeding.${RESET}"
        echo ""
        echo -e "  ${CYAN}Quick fixes:${RESET}"
        echo -e "    # Start Docker Desktop and enable Kubernetes"
        echo -e "    brew install helm terraform jq yq  # Install required tools"
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

# Setup Docker Desktop environment
setup_docker_desktop_environment() {
    print_header "Setting up Docker Desktop Environment"

    # Check if Docker Desktop Kubernetes is enabled
    if ! kubectl cluster-info &>/dev/null; then
        print_error "Docker Desktop Kubernetes is not running"
        print_info "Please start Docker Desktop and enable Kubernetes in settings"
        return 1
    fi

    # Switch to docker-desktop context if available
    if kubectl config get-contexts docker-desktop &>/dev/null; then
        kubectl config use-context docker-desktop
        print_success "Switched to docker-desktop context"
    elif kubectl config get-contexts docker-for-desktop &>/dev/null; then
        kubectl config use-context docker-for-desktop
        print_success "Switched to docker-for-desktop context"
    fi

    print_success "Docker Desktop environment ready"
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

    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        print_warning "Kubernetes cluster not accessible - skipping dashboard deployment"
        print_info "To deploy dashboard later: QUICKSTART_DEPLOY_DASHBOARD=true ./core/scripts/automation/quickstart-local-docker-desktop.sh"
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
        echo "  🧹 Clean up: ./core/scripts/automation/quickstart-local-docker-desktop.sh --cleanup"
        echo "  🔄 Restart: ./core/scripts/automation/quickstart-local-docker-desktop.sh --start-pf"
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

# Enhanced cleanup function for Docker Desktop
cleanup_docker_desktop() {
    print_header "Cleaning up Docker Desktop environment"

    # Stop all port-forwards
    cleanup_port_forwards

    # Note: We don't delete the Docker Desktop cluster as it's managed by Docker Desktop
    print_info "Docker Desktop Kubernetes cluster is managed by Docker Desktop"
    print_info "To reset the cluster, use Docker Desktop > Settings > Kubernetes > Reset Kubernetes Cluster"

    print_success "Docker Desktop environment cleanup completed"
}

# Main function for Docker Desktop quickstart
main() {
    print_header "Agentic Reconciliation Engine - Docker Desktop Local Quick Start"

    echo -e "${BLUE}Welcome to Agentic Reconciliation Engine - Docker Desktop Local Development!${NC}"
    echo ""
    echo -e "${YELLOW}This will set up a complete local development environment using Docker Desktop.${NC}"
    echo ""

    # Check if we're in the right directory
    if [[ ! -f "$REPO_ROOT/README.md" ]]; then
        print_error "Not in repository root. Please run from repository root."
        exit 1
    fi

    # Run Docker Desktop-specific validation
    print_info "Running Docker Desktop-specific prerequisites validation..."
    if ! run_docker_desktop_validation; then
        print_error "Docker Desktop validation failed. Please fix errors above and retry."
        exit 1
    fi

    # If there are warnings, prompt user to continue
    if [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Found $WARNINGS warning(s). Continue with Docker Desktop setup? (Y/n)${NC}"
        read -r response
        if [[ "$response" =~ ^[Nn]$ ]]; then
            print_info "Docker Desktop setup cancelled by user."
            exit 0
        fi
    fi

    # Run pre-quickstart hook
    run_hooks "pre-quickstart" || return 1

    # Setup basic configuration
    print_info "Setting up Docker Desktop development environment..."

    # Create basic directories if they don't exist
    mkdir -p logs/
    mkdir -p tmp/

    # Make scripts executable
    find "$SCRIPT_DIR" -name "*.sh" -exec chmod +x {} \;
    find "$SCRIPT_DIR" -name "*.py" -exec chmod +x {} \;

    print_success "Docker Desktop development environment ready"

    # Setup Docker Desktop environment
    setup_docker_desktop_environment || return 1

    # Run post-quickstart hook
    run_hooks "post-quickstart" || return 1

    # Deploy AI agents dashboard
    deploy_ai_agents_dashboard || return 1

    # Deploy AI Agent Skills and MCP servers
    deploy_ai_agent_skills || return 1

    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Access your AI agents dashboard at http://localhost:8080"
    echo "2. Configure Claude Desktop with AI Agent Skills (auto-configured)"
    echo "3. Use consolidated K8sGPT: http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
    echo "4. View port-forward logs: tail -f /tmp/quickstart-port-forwards/*.log"
    echo "5. Clean up environment: ./core/scripts/automation/quickstart-local-docker-desktop.sh --cleanup"
    echo ""
    echo -e "${GREEN}🚀 Docker Desktop local development environment is ready!${NC}"
    echo -e "${YELLOW}🧠 AI agents are fully operational!${NC}"
    echo -e "${BLUE}🤖 Consolidated K8sGPT is deployed and integrated!${NC}"
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
    echo "Agentic Reconciliation Engine - Docker Desktop Local Quick Start"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help         Show this help message"
    echo "  --validate         Run Docker Desktop validation only"
    echo "  --cleanup          Clean up port-forwards and reset environment"
    echo "  --start-pf         Start all port-forwards (if not already running)"
    echo "  --setup-env        Setup Docker Desktop environment only"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up a complete local development environment using Docker Desktop."
    echo "  This includes Docker Desktop Kubernetes validation, environment setup,"
    echo "  and deployment of AI agents dashboard with running agents."
    echo ""
    echo "  Docker Desktop must be running with Kubernetes enabled."
    echo ""
    echo "EXAMPLES:"
    echo "  $0                    # Complete Docker Desktop local setup"
    echo "  $0 --validate         # Validate Docker Desktop prerequisites only"
    echo "  $0 --cleanup          # Clean up environment"
    echo "  $0 --setup-env        # Setup environment only"
    echo ""
    echo "DOCKER DESKTOP REQUIREMENTS:"
    echo "  - Docker Desktop installed and running"
    echo "  - Kubernetes enabled in Docker Desktop settings"
    echo "  - Sufficient resources allocated (4GB RAM, 2+ CPUs recommended)"
    echo ""
    echo "SERVICES ACCESS:"
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
        run_docker_desktop_validation
        exit $?
        ;;
    --cleanup)
        cleanup_docker_desktop
        exit 0
        ;;
    --start-pf)
        start_all_port_forwards
        exit 0
        ;;
    --setup-env)
        setup_docker_desktop_environment
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

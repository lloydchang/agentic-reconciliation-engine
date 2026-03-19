#!/bin/bash
# Agentic Reconciliation Engine - Quick Start for Local Kind Development
# Repository setup and initial onboarding for Kind-based local development

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

# Environment-specific validation for Kind
run_kind_validation() {
    ERRORS=0
    WARNINGS=0

    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}║  agentic-reconciliation-engine — Kind Local Validation ║${RESET}"
    echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${RESET}"
    echo ""

    # 1. Kind-specific prerequisites
    echo -e "${BOLD}[1/7] Checking Kind prerequisites${RESET}"

    # Check Docker
    if command -v docker &>/dev/null; then
        local docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        pass "Docker available (${docker_version})"
    else
        fail "Docker not found (required for Kind)"
    fi

    # Check Kind
    if command -v kind &>/dev/null; then
        local kind_version=$(kind version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        pass "Kind available (${kind_version})"
    else
        fail "Kind not found - install with: brew install kind"
    fi

    # Check kubectl
    if command -v kubectl &>/dev/null; then
        local kube_version=$(kubectl version --client --short 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        pass "kubectl available (${kube_version})"
    else
        fail "kubectl not found (required for Kind)"
    fi

    # Check if Kind cluster exists
    if kind get clusters 2>/dev/null | grep -q "agentic-cluster"; then
        pass "Kind cluster 'agentic-cluster' exists"
    else
        warn "Kind cluster 'agentic-cluster' not found - will be created"
    fi

    echo ""

    # 2. Standard CLI tools (same as base validation)
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

    # 3. Environment Variables (Kind-specific)
    echo -e "${BOLD}[3/7] Checking Kind environment configuration${RESET}"

    # Local development specific env vars
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

    check_env_optional "DOCKER_REGISTRY"
    check_env_optional "LOCAL_REGISTRY_PORT"

    echo ""

    # 4. Local cluster state
    echo -e "${BOLD}[4/7] Checking local cluster state${RESET}"

    if kind get clusters 2>/dev/null | grep -q "agentic-cluster"; then
        pass "Kind cluster 'agentic-cluster' is running"
        if kubectl cluster-info --context kind-agentic-cluster &>/dev/null; then
            pass "Cluster API accessible"
            local node_count=$(kubectl get nodes --context kind-agentic-cluster --no-headers 2>/dev/null | wc -l | tr -d ' ')
            info "Nodes in cluster: ${node_count}"
        else
            warn "Cannot access cluster API"
        fi
    else
        info "Kind cluster 'agentic-cluster' not running - will be created"
    fi

    echo ""

    # 5. Resource requirements check
    echo -e "${BOLD}[5/7] Checking resource requirements${RESET}"

    # Check available memory
    if command -v docker &>/dev/null && docker system info &>/dev/null; then
        local mem_gb=$(docker system info --format '{{.MemTotal}}' 2>/dev/null | awk '{print int($1/1024/1024/1024)}' || echo "unknown")
        if [[ "$mem_gb" != "unknown" && "$mem_gb" -ge 4 ]]; then
            pass "Available memory: ${mem_gb}GB (sufficient for Kind)"
        else
            warn "Available memory: ${mem_gb}GB (may be insufficient - recommend 8GB+)"
        fi
    else
        warn "Cannot determine available memory"
    fi

    # Check available disk space
    local disk_gb=$(df -BG . | tail -1 | awk '{print int($4)}')
    if [[ $disk_gb -ge 10 ]]; then
        pass "Available disk space: ${disk_gb}GB (sufficient)"
    else
        warn "Available disk space: ${disk_gb}GB (may be insufficient - recommend 20GB+)"
    fi

    echo ""

    # 6. Network requirements
    echo -e "${BOLD}[6/7] Checking network requirements${RESET}"

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

    # 7. Quick smoke test
    echo -e "${BOLD}[7/7] Running Kind smoke tests${RESET}"

    if command -v docker &>/dev/null; then
        if docker ps &>/dev/null; then
            pass "Docker daemon accessible"
        else
            warn "Docker daemon not accessible"
        fi
    fi

    if command -v kind &>/dev/null; then
        if kind version &>/dev/null; then
            pass "Kind CLI functional"
        fi
    fi

    echo ""

    # Summary
    echo -e "${BOLD}══════════════════════════════════════════════════════════${RESET}"
    if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}  ✓ Kind validation PASSED — ready for local development${RESET}"
    elif [[ $ERRORS -eq 0 ]]; then
        echo -e "${YELLOW}${BOLD}  ⚠ Kind validation PASSED with ${WARNINGS} warning(s)${RESET}"
        echo -e "${YELLOW}  Local development may have degraded performance.${RESET}"
    else
        echo -e "${RED}${BOLD}  ✗ Kind validation FAILED — ${ERRORS} error(s), ${WARNINGS} warning(s)${RESET}"
        echo -e "${RED}  Fix the errors above before proceeding.${RESET}"
        echo ""
        echo -e "  ${CYAN}Quick fixes:${RESET}"
        echo -e "    brew install kind docker kubectl helm  # Install required tools"
        echo -e "    kind create cluster --name agentic-cluster  # Create Kind cluster"
    fi
    echo -e "${BOLD}══════════════════════════════════════════════════════════${RESET}"
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

# Create Kind cluster
create_kind_cluster() {
    print_header "Creating Kind Cluster"

    if kind get clusters 2>/dev/null | grep -q "agentic-cluster"; then
        print_info "Kind cluster 'agentic-cluster' already exists"
        return 0
    fi

    print_info "Creating Kind cluster 'agentic-cluster'..."

    # Create kind config
    cat > /tmp/kind-config.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: agentic-cluster
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
  - containerPort: 3000
    hostPort: 3000
    protocol: TCP
  - containerPort: 5000
    hostPort: 5000
    protocol: TCP
  - containerPort: 5001
    hostPort: 5001
    protocol: TCP
  - containerPort: 7233
    hostPort: 7233
    protocol: TCP
  - containerPort: 8080
    hostPort: 8080
    protocol: TCP
  - containerPort: 8081
    hostPort: 8081
    protocol: TCP
  - containerPort: 8082
    hostPort: 8082
    protocol: TCP
  - containerPort: 9000
    hostPort: 9000
    protocol: TCP
EOF

    if kind create cluster --config /tmp/kind-config.yaml --wait 5m; then
        print_success "Kind cluster 'agentic-cluster' created successfully"
        rm -f /tmp/kind-config.yaml
    else
        print_error "Failed to create Kind cluster"
        rm -f /tmp/kind-config.yaml
        return 1
    fi
}

# Deploy NGINX Ingress Controller for Kind
deploy_kind_ingress() {
    print_header "Deploying NGINX Ingress Controller"

    if kubectl get deployment ingress-nginx-controller -n ingress-nginx &>/dev/null; then
        print_info "NGINX Ingress Controller already deployed"
        return 0
    fi

    print_info "Deploying NGINX Ingress Controller for Kind..."

    if kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/kind/deploy.yaml; then
        print_success "NGINX Ingress Controller deployed"
        print_info "Waiting for ingress controller to be ready..."
        kubectl wait --namespace ingress-nginx \
            --for=condition=ready pod \
            --selector=app.kubernetes.io/component=controller \
            --timeout=300s
    else
        print_error "Failed to deploy NGINX Ingress Controller"
        return 1
    fi
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
        print_info "To deploy dashboard later: QUICKSTART_DEPLOY_DASHBOARD=true ./core/scripts/automation/quickstart-local-kind.sh"
        return 0
    fi

    print_info "Deploying AI agents ecosystem with dashboard..."

    # Run the ecosystem deployment script
    if bash "$ecosystem_script"; then
        print_success "AI agents dashboard deployed successfully!"
        echo ""
        echo -e "${GREEN}🎉 Your AI Agents Dashboard is now running!${NC}"
        echo -e "${YELLOW}📊 Access it at: http://localhost:8080${NC}"
        echo -e "${BLUE}🔄 Or via ingress: http://dashboard.local${NC}"
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
        echo "  🧹 Clean up: ./core/scripts/automation/quickstart-local-kind.sh --cleanup"
        echo "  🔄 Restart: ./core/scripts/automation/quickstart-local-kind.sh --start-pf"
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

# Enhanced cleanup function for Kind
cleanup_kind() {
    print_header "Cleaning up Kind environment"

    # Stop all port-forwards
    cleanup_port_forwards

    # Delete Kind cluster if it exists
    if kind get clusters 2>/dev/null | grep -q "agentic-cluster"; then
        print_info "Deleting Kind cluster 'agentic-cluster'..."
        if kind delete cluster --name agentic-cluster; then
            print_success "Kind cluster deleted successfully"
        else
            print_warning "Failed to delete Kind cluster"
        fi
    else
        print_info "No Kind cluster 'agentic-cluster' found"
    fi

    # Clean up temporary files
    rm -f /tmp/kind-config.yaml

    print_success "Kind environment cleanup completed"
}

# Main function for Kind quickstart
main() {
    print_header "Agentic Reconciliation Engine - Kind Local Quick Start"

    echo -e "${BLUE}Welcome to Agentic Reconciliation Engine - Kind Local Development!${NC}"
    echo ""
    echo -e "${YELLOW}This will set up a complete local development environment using Kind.${NC}"
    echo ""

    # Check if we're in the right directory
    if [[ ! -f "$REPO_ROOT/README.md" ]]; then
        print_error "Not in repository root. Please run from repository root."
        exit 1
    fi

    # Run Kind-specific validation
    print_info "Running Kind-specific prerequisites validation..."
    if ! run_kind_validation; then
        print_error "Kind validation failed. Please fix errors above and retry."
        exit 1
    fi

    # If there are warnings, prompt user to continue
    if [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Found $WARNINGS warning(s). Continue with Kind setup? (Y/n)${NC}"
        read -r response
        if [[ "$response" =~ ^[Nn]$ ]]; then
            print_info "Kind setup cancelled by user."
            exit 0
        fi
    fi

    # Run pre-quickstart hook
    run_hooks "pre-quickstart" || return 1

    # Setup basic configuration
    print_info "Setting up Kind development environment..."

    # Create basic directories if they don't exist
    mkdir -p logs/
    mkdir -p tmp/

    # Make scripts executable
    find "$SCRIPT_DIR" -name "*.sh" -exec chmod +x {} \;
    find "$SCRIPT_DIR" -name "*.py" -exec chmod +x {} \;

    print_success "Kind development environment ready"

    # Create Kind cluster
    create_kind_cluster || return 1

    # Deploy NGINX Ingress Controller
    deploy_kind_ingress || return 1

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
    echo "5. Clean up environment: ./core/scripts/automation/quickstart-local-kind.sh --cleanup"
    echo ""
    echo -e "${GREEN}🚀 Kind local development environment is ready!${NC}"
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
    echo "Agentic Reconciliation Engine - Kind Local Quick Start"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help         Show this help message"
    echo "  --validate         Run Kind-specific validation only"
    echo "  --cleanup          Clean up Kind cluster and port-forwards"
    echo "  --start-pf         Start all port-forwards (if not already running)"
    echo "  --create-cluster   Create Kind cluster only"
    echo "  --deploy-ingress   Deploy NGINX ingress controller only"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up a complete local development environment using Kind."
    echo "  This includes Kind cluster creation, ingress controller deployment,"
    echo "  comprehensive prerequisites validation, and deployment of AI agents dashboard."
    echo ""
    echo "EXAMPLES:"
    echo "  $0                    # Complete Kind local setup"
    echo "  $0 --validate         # Validate Kind prerequisites only"
    echo "  $0 --cleanup          # Clean up Kind environment"
    echo "  $0 --create-cluster   # Create Kind cluster only"
    echo ""
    echo "KIND ENVIRONMENT:"
    echo "  - Cluster name: agentic-cluster"
    echo "  - Ports exposed: 80, 443, 3000, 5000, 5001, 7233, 8080, 8081, 8082, 9000"
    echo "  - Ingress controller: NGINX (kind provider)"
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
        run_kind_validation
        exit $?
        ;;
    --cleanup)
        cleanup_kind
        exit 0
        ;;
    --start-pf)
        start_all_port_forwards
        exit 0
        ;;
    --create-cluster)
        create_kind_cluster
        exit $?
        ;;
    --deploy-ingress)
        deploy_kind_ingress
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

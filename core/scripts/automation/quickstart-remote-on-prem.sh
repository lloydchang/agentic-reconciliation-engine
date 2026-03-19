#!/bin/bash
# Agentic Reconciliation Engine - Quick Start for Remote On-Premises
# Repository setup and initial onboarding for on-premises Kubernetes deployments

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

# Environment-specific validation for On-Premises
run_onprem_validation() {
    ERRORS=0
    WARNINGS=0

    echo ""
    echo -e "${BOLD}╔════════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}║  agentic-reconciliation-engine — On-Premises Validation     ║${RESET}"
    echo -e "${BOLD}╚════════════════════════════════════════════════════════════════╝${RESET}"
    echo ""

    # 1. Kubernetes prerequisites
    echo -e "${BOLD}[1/7] Checking Kubernetes prerequisites${RESET}"

    # Check kubectl
    if command -v kubectl &>/dev/null; then
        local kube_version=$(kubectl version --client --short 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        pass "kubectl available (${kube_version})"
    else
        fail "kubectl not found (required for Kubernetes operations)"
    fi

    # Check kubectl connectivity
    if kubectl cluster-info &>/dev/null; then
        local cluster_info=$(kubectl cluster-info 2>/dev/null | head -1)
        pass "kubectl connected to cluster: ${cluster_info}"
    else
        fail "kubectl cannot connect to cluster - check kubeconfig"
    fi

    # Check cluster version
    local server_version=$(kubectl version --short 2>/dev/null | grep Server | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")
    if [[ "$server_version" != "unknown" ]]; then
        # Extract major and minor versions
        local major_version=$(echo "$server_version" | cut -d. -f1)
        local minor_version=$(echo "$server_version" | cut -d. -f2)

        if [[ $major_version -eq 1 && $minor_version -ge 24 ]]; then
            pass "Kubernetes server version: ${server_version} (supported)"
        elif [[ $major_version -eq 1 && $minor_version -ge 20 ]]; then
            warn "Kubernetes server version: ${server_version} (minimum supported, consider upgrading)"
        else
            fail "Kubernetes server version: ${server_version} (unsupported - requires v1.20+)"
        fi
    else
        warn "Could not determine Kubernetes server version"
    fi

    echo ""

    # 2. Standard CLI tools
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

    # Required for on-premises
    check_tool "helm"       "3.12"
    check_tool "jq"         "1.6"
    check_tool "yq"         "4.0"

    # Optional but recommended
    check_tool_optional "kubectx"
    check_tool_optional "kubens"
    check_tool_optional "kustomize"
    check_tool_optional "skaffold"

    echo ""

    # 3. Cluster capabilities
    echo -e "${BOLD}[3/7] Checking cluster capabilities${RESET}"

    # Check cluster nodes
    local node_count=$(kubectl get nodes --no-headers 2>/dev/null | wc -l)
    if [[ $node_count -gt 0 ]]; then
        pass "${node_count} node(s) available"

        # Check node resources
        local total_cpu=$(kubectl get nodes -o jsonpath='{.items[*].status.capacity.cpu}' 2>/dev/null | sed 's/ //g' | paste -sd+ - | bc 2>/dev/null || echo "unknown")
        local total_memory=$(kubectl get nodes -o jsonpath='{.items[*].status.capacity.memory}' 2>/dev/null | sed 's/Ki//g' | sed 's/ //g' | paste -sd+ - | bc 2>/dev/null || echo "unknown")

        if [[ "$total_cpu" != "unknown" ]]; then
            # Convert memory from Ki to Gi
            local total_memory_gb=$((total_memory / 1024 / 1024))
            pass "Total cluster resources: ${total_cpu} CPU cores, ${total_memory_gb}GB memory"
        fi
    else
        fail "No nodes found in cluster"
    fi

    # Check storage classes
    local storage_classes=$(kubectl get storageclass --no-headers 2>/dev/null | wc -l)
    if [[ $storage_classes -gt 0 ]]; then
        pass "${storage_classes} storage class(es) available"

        # Check for default storage class
        local default_sc=$(kubectl get storageclass --no-headers 2>/dev/null | grep -c "(default)" || echo "0")
        if [[ $default_sc -gt 0 ]]; then
            pass "Default storage class configured"
        else
            warn "No default storage class - some components may need manual configuration"
        fi
    else
        warn "No storage classes found - persistent volumes may not work"
    fi

    # Check ingress controllers
    local ingress_classes=$(kubectl get ingressclass --no-headers 2>/dev/null | wc -l)
    if [[ $ingress_classes -gt 0 ]]; then
        pass "${ingress_classes} ingress class(es) available"
    else
        warn "No ingress controllers found - services will not be externally accessible"
        info "Consider installing: NGINX Ingress Controller, Traefik, or HAProxy Ingress"
    fi

    echo ""

    # 4. Network and security
    echo -e "${BOLD}[4/7] Checking network and security${RESET}"

    # Check namespaces
    local namespaces=$(kubectl get namespaces --no-headers 2>/dev/null | wc -l)
    if [[ $namespaces -gt 0 ]]; then
        pass "${namespaces} namespace(s) available"
    fi

    # Check network policies support
    local network_policies=$(kubectl get networkpolicy --all-namespaces --no-headers 2>/dev/null | wc -l)
    if [[ $network_policies -gt 0 ]]; then
        pass "Network policies configured (${network_policies} policies)"
    else
        info "No network policies found - consider implementing network segmentation"
    fi

    # Check RBAC
    if kubectl auth can-i list pods --all-namespaces &>/dev/null; then
        pass "RBAC permissions sufficient for deployment"
    else
        fail "Insufficient RBAC permissions for deployment"
    fi

    echo ""

    # 5. Load balancer and ingress
    echo -e "${BOLD}[5/7] Checking load balancer and ingress${RESET}"

    # Check for LoadBalancer services capability
    local lb_services=$(kubectl get services --all-namespaces --no-headers 2>/dev/null | grep LoadBalancer | wc -l)
    if [[ $lb_services -gt 0 ]]; then
        pass "LoadBalancer services supported (${lb_services} existing)"
    else
        info "No LoadBalancer services found - check if cloud provider integration is needed"
    fi

    # Check ingress resources
    local ingress_count=$(kubectl get ingress --all-namespaces --no-headers 2>/dev/null | wc -l)
    if [[ $ingress_count -gt 0 ]]; then
        pass "${ingress_count} ingress resource(s) configured"
    else
        info "No ingress resources found - will create ingress for services"
    fi

    echo ""

    # 6. Resource estimation
    echo -e "${BOLD}[6/7] Estimating resource requirements${RESET}"

    # Estimated resource requirements
    info "Estimated resource requirements for AI agents ecosystem:"
    info "  - CPU: ~2-4 cores minimum, 8+ cores recommended"
    info "  - Memory: ~4GB minimum, 16GB+ recommended"
    info "  - Storage: ~50GB minimum for logs and data"
    info "  - Network: External access for dashboard and APIs"
    info ""
    info "Components will be deployed with resource limits and requests"

    echo ""

    # 7. Final confirmation
    echo -e "${BOLD}[7/7] Deployment confirmation${RESET}"

    local cluster_name=$(kubectl config current-context 2>/dev/null || echo "unknown")
    local server_version=$(kubectl version --short 2>/dev/null | grep Server | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")

    echo -e "${YELLOW}Target cluster: ${cluster_name}${NC}"
    echo -e "${YELLOW}Kubernetes version: ${server_version}${NC}"
    echo -e "${YELLOW}Estimated cost: $0 (on-premises infrastructure)${NC}"
    echo ""

    # Summary
    echo -e "${BOLD}════════════════════════════════════════════════════════════════${RESET}"
    if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}  ✓ On-premises validation PASSED — ready for deployment${RESET}"
    elif [[ $ERRORS -eq 0 ]]; then
        echo -e "${YELLOW}${BOLD}  ⚠ On-premises validation PASSED with ${WARNINGS} warning(s)${RESET}"
        echo -e "${YELLOW}  Review warnings above before proceeding with deployment.${RESET}"
    else
        echo -e "${RED}${BOLD}  ✗ On-premises validation FAILED — ${ERRORS} error(s), ${WARNINGS} warning(s)${RESET}"
        echo -e "${RED}  Fix the errors above before proceeding.${RESET}"
        echo ""
        echo -e "  ${CYAN}Quick fixes:${RESET}"
        echo -e "    kubectl config use-context <context>  # Switch to correct cluster"
        echo -e "    # Install ingress controller if needed"
        echo -e "    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml"
    fi
    echo -e "${BOLD}════════════════════════════════════════════════════════════════${RESET}"
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

# Deploy NGINX Ingress Controller for on-premises
deploy_nginx_ingress() {
    print_header "Deploying NGINX Ingress Controller"

    if kubectl get deployment ingress-nginx-controller -n ingress-nginx &>/dev/null; then
        print_info "NGINX Ingress Controller already deployed"
        return 0
    fi

    print_info "Deploying NGINX Ingress Controller for on-premises..."

    # Create ingress-nginx namespace
    kubectl create namespace ingress-nginx --dry-run=client -o yaml | kubectl apply -f -

    # Deploy NGINX Ingress Controller
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/baremetal/deploy.yaml

    # Wait for deployment
    kubectl wait --for=condition=available --timeout=300s deployment/ingress-nginx-controller -n ingress-nginx

    print_success "NGINX Ingress Controller deployed"
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
        print_info "To deploy dashboard later: QUICKSTART_DEPLOY_DASHBOARD=true ./core/scripts/automation/quickstart-remote-on-prem.sh"
        return 0
    fi

    print_info "Deploying AI agents ecosystem with dashboard..."

    # Run the ecosystem deployment script
    if bash "$ecosystem_script"; then
        print_success "AI agents dashboard deployed successfully!"
        echo ""
        echo -e "${GREEN}🎉 Your AI Agents Dashboard is now running!${NC}"
        echo -e "${YELLOW}📊 Access it via NGINX Ingress (check kubectl get ingress -n ai-infrastructure)${NC}"
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
        echo "  🧹 Clean up: ./core/scripts/automation/quickstart-remote-on-prem.sh --cleanup"
        echo "  🔄 Restart: ./core/scripts/automation/quickstart-remote-on-prem.sh --start-pf"
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

# Enhanced cleanup function for On-Premises
cleanup_onprem() {
    print_header "Cleaning up on-premises environment"

    # Stop all port-forwards
    cleanup_port_forwards

    # Ask for confirmation before cleanup
    echo -e "${RED}⚠️  This will remove the AI agents ecosystem from your cluster!${NC}"
    echo -e "${RED}This includes all namespaces, deployments, and data!${NC}"
    echo -e "${YELLOW}This action cannot be undone. Are you sure? (yes/NO)${NC}"
    read -r response

    if [[ "$response" != "yes" ]]; then
        print_info "Cleanup cancelled by user"
        return 0
    fi

    # Clean up AI infrastructure
    local namespaces=(
        "ai-infrastructure"
        "langfuse"
        "k8sgpt-system"
        "temporal-system"
        "ingress-nginx"
    )

    for namespace in "${namespaces[@]}"; do
        if kubectl get namespace "$namespace" &>/dev/null; then
            print_info "Deleting namespace: $namespace"
            kubectl delete namespace "$namespace" --timeout=300s || {
                print_warning "Failed to delete namespace $namespace - may need manual cleanup"
            }
        else
            print_info "Namespace $namespace not found"
        fi
    done

    # Clean up cluster-level resources
    print_info "Cleaning up cluster-level resources..."

    # Remove CRDs
    kubectl delete crd $(kubectl get crd | grep -E '(temporal|k8sgpt|ai-infrastructure)' | awk '{print $1}') --ignore-not-found=true || true

    # Clean up helm releases
    if command -v helm &>/dev/null; then
        helm list --all-namespaces | grep -E '(temporal|k8sgpt|ingress-nginx)' | awk '{print $1, $2}' | while read -r release namespace; do
            print_info "Uninstalling helm release: $release in $namespace"
            helm uninstall "$release" -n "$namespace" --ignore-not-found || true
        done
    fi

    print_success "On-premises environment cleanup completed"
}

# Main function for on-premises quickstart
main() {
    print_header "Agentic Reconciliation Engine - On-Premises Quick Start"

    echo -e "${BLUE}Welcome to Agentic Reconciliation Engine - On-Premises Deployment!${NC}"
    echo ""
    echo -e "${YELLOW}This will deploy the complete AI agents ecosystem to your existing Kubernetes cluster.${NC}"
    echo -e "${GREEN}✅ No cloud costs - runs on your own infrastructure!${NC}"
    echo ""

    # Check if we're in the right directory
    if [[ ! -f "$REPO_ROOT/README.md" ]]; then
        print_error "Not in repository root. Please run from repository root."
        exit 1
    fi

    # Run on-premises validation
    print_info "Running on-premises prerequisites validation..."
    if ! run_onprem_validation; then
        print_error "On-premises validation failed. Please fix errors above and retry."
        exit 1
    fi

    # If there are warnings, prompt user to continue
    if [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Found $WARNINGS warning(s). Continue with on-premises deployment? (Y/n)${NC}"
        read -r response
        if [[ "$response" =~ ^[Nn]$ ]]; then
            print_info "On-premises deployment cancelled by user."
            exit 0
        fi
    fi

    # Final confirmation
    echo -e "${GREEN}✅ DEPLOYMENT COST: $0${NC}"
    echo -e "${YELLOW}This deployment uses your existing on-premises infrastructure.${NC}"
    echo -e "${YELLOW}Ensure your cluster has sufficient resources (8+ CPU cores, 16GB+ RAM recommended).${NC}"
    echo -e "${YELLOW}Do you want to proceed with deployment? (yes/NO)${NC}"
    read -r response
    if [[ "$response" != "yes" ]]; then
        print_info "On-premises deployment cancelled by user."
        exit 0
    fi

    # Run pre-quickstart hook
    run_hooks "pre-quickstart" || return 1

    # Setup basic configuration
    print_info "Setting up on-premises environment..."

    # Create basic directories if they don't exist
    mkdir -p logs/
    mkdir -p tmp/

    # Make scripts executable
    find "$SCRIPT_DIR" -name "*.sh" -exec chmod +x {} \;
    find "$SCRIPT_DIR" -name "*.py" -exec chmod +x {} \;

    print_success "On-premises environment ready"

    # Deploy NGINX Ingress Controller
    deploy_nginx_ingress || return 1

    # Run post-quickstart hook
    run_hooks "post-quickstart" || return 1

    # Deploy AI agents dashboard
    deploy_ai_agents_dashboard || return 1

    # Deploy AI Agent Skills and MCP servers
    deploy_ai_agent_skills || return 1

    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Access your AI agents dashboard via NGINX Ingress"
    echo "2. Check service endpoints: kubectl get ingress -n ai-infrastructure"
    echo "3. Configure DNS for ingress if needed (external access)"
    echo "4. Configure Claude Desktop with AI Agent Skills (auto-configured)"
    echo "5. Use consolidated K8sGPT: http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
    echo "6. Monitor cluster resources: kubectl top nodes"
    echo "7. View port-forward logs: tail -f /tmp/quickstart-port-forwards/*.log"
    echo "8. Clean up environment: ./core/scripts/automation/quickstart-remote-on-prem.sh --cleanup"
    echo ""
    echo -e "${GREEN}🚀 On-premises environment is ready!${NC}"
    echo -e "${YELLOW}🧠 AI agents are fully operational!${NC}"
    echo -e "${BLUE}🏢 Running on your Kubernetes cluster!${NC}"
    echo ""
    echo -e "${GREEN}💰 No cloud costs - all on your infrastructure!${NC}"
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
    echo "Agentic Reconciliation Engine - On-Premises Quick Start"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help         Show this help message"
    echo "  --validate         Run on-premises validation only"
    echo "  --cleanup          Clean up AI agents ecosystem from cluster"
    echo "  --start-pf         Start all port-forwards (if not already running)"
    echo "  --deploy-ingress   Deploy NGINX Ingress Controller only"
    echo ""
    echo "DESCRIPTION:"
    echo "  Deploys the complete AI agents ecosystem to your existing Kubernetes cluster."
    echo "  This assumes you have a working Kubernetes cluster with kubectl access."
    echo "  Includes NGINX Ingress Controller deployment and comprehensive validation."
    echo ""
    echo "  ✅ No cloud costs - runs entirely on your infrastructure!"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                        # Complete on-premises deployment"
    echo "  $0 --validate            # Validate cluster prerequisites only"
    echo "  $0 --cleanup             # Clean up AI agents ecosystem (destructive!)"
    echo "  $0 --deploy-ingress      # Deploy NGINX Ingress Controller only"
    echo ""
    echo "REQUIREMENTS:"
    echo "  - Existing Kubernetes cluster (v1.20+)"
    echo "  - kubectl configured and connected"
    echo "  - Sufficient cluster resources (8+ CPU cores, 16GB+ RAM recommended)"
    echo "  - Storage class configured (for persistent volumes)"
    echo ""
    echo "OPTIONAL BUT RECOMMENDED:"
    echo "  - Ingress controller (automatically deployed if missing)"
    echo "  - LoadBalancer service support (for cloud integrations)"
    echo "  - Network policies enabled"
    echo ""
    echo "SERVICES ACCESS:"
    echo "  🚪 Infrastructure Portal:  NGINX Ingress"
    echo "  🤖 AI Dashboard:        NGINX Ingress"
    echo "  📊 Dashboard API:        NGINX Ingress"
    echo "  ⏰ Temporal UI:          NGINX Ingress"
    echo "  🔍 Langfuse Observability: NGINX Ingress"
    echo "  📈 Comprehensive API:   NGINX Ingress"
    echo "  🖥️  Comprehensive Frontend: NGINX Ingress"
    echo "  🧠 Memory Service:       NGINX Ingress"
    echo ""
    echo "RESOURCE REQUIREMENTS:"
    echo "  - CPU: 2-4 cores minimum, 8+ cores recommended"
    echo "  - Memory: 4GB minimum, 16GB+ recommended"
    echo "  - Storage: 50GB+ for logs and data"
    echo "  - Network: External access for dashboard and APIs"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    --validate)
        run_onprem_validation
        exit $?
        ;;
    --cleanup)
        cleanup_onprem
        exit 0
        ;;
    --start-pf)
        start_all_port_forwards
        exit 0
        ;;
    --deploy-ingress)
        deploy_nginx_ingress
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

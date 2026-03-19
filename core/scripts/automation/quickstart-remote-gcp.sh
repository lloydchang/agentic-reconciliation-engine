#!/bin/bash
# Agentic Reconciliation Engine - Quick Start for Remote GCP Production
# Repository setup and initial onboarding for Google Cloud GKE production deployments

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

# Environment-specific validation for Remote GCP
run_gcp_production_validation() {
    ERRORS=0
    WARNINGS=0

    echo ""
    echo -e "${BOLD}╔═══════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}║  agentic-reconciliation-engine — GCP Production Validation ║${RESET}"
    echo -e "${BOLD}╚═══════════════════════════════════════════════════════════════╝${RESET}"
    echo ""

    # 1. GCP prerequisites
    echo -e "${BOLD}[1/8] Checking GCP prerequisites${RESET}"

    # Check gcloud CLI
    if command -v gcloud &>/dev/null; then
        local gcloud_version=$(gcloud version --format="value(gcloud)" 2>/dev/null || echo "unknown")
        pass "gcloud CLI available (${gcloud_version})"
    else
        fail "gcloud CLI not found (required for GCP operations)"
    fi

    # Check kubectl
    if command -v kubectl &>/dev/null; then
        local kube_version=$(kubectl version --client --short 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        pass "kubectl available (${kube_version})"
    else
        fail "kubectl not found (required for GKE)"
    fi

    # Check GCP authentication
    if gcloud auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
        local active_account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
        pass "GCP authenticated - Account: ${active_account}"
    else
        fail "GCP authentication failed - run: gcloud auth login"
    fi

    # Check if GKE cluster exists
    local cluster_name=${GKE_CLUSTER_NAME:-agentic-cluster}
    local region=${GCP_REGION:-us-central1}
    if gcloud container clusters describe "$cluster_name" --region="$region" &>/dev/null; then
        pass "GKE cluster '$cluster_name' exists"
    else
        warn "GKE cluster '$cluster_name' not found - will be created"
    fi

    echo ""

    # 2. Standard CLI tools
    echo -e "${BOLD}[2/8] Checking required CLI tools${RESET}"

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
    check_tool "helm"       "3.12"
    check_tool "terraform"  "1.6"
    check_tool "jq"         "1.6"
    check_tool "yq"         "4.0"

    # Optional but recommended
    check_tool_optional "kubectx"
    check_tool_optional "kubens"
    check_tool_optional "skaffold"

    echo ""

    # 3. GCP region and environment
    echo -e "${BOLD}[3/8] Checking GCP region and environment${RESET}"

    # Check GCP region
    local region=${GCP_REGION:-$(gcloud config get-value compute/region 2>/dev/null || echo "us-central1")}
    if [[ -n "$region" ]]; then
        pass "GCP region: ${region}"

        # Check region availability (basic check)
        if gcloud compute regions describe "$region" &>/dev/null; then
            pass "Region ${region} is available"
        else
            warn "Region ${region} may not be available"
        fi
    else
        fail "GCP region not set"
    fi

    # Check required environment variables
    check_env_var() {
        local var=$1 required=${2:-true}
        if [[ -n "${!var:-}" ]]; then
            pass "${var} set"
        elif [[ "$required" == "true" ]]; then
            fail "${var} not set (required)"
        else
            warn "${var} not set (optional)"
        fi
    }

    check_env_var "GCP_REGION" "false"
    check_env_var "GKE_CLUSTER_NAME" "false"
    check_env_var "GOOGLE_CLOUD_PROJECT" "false"
    check_env_var "GCP_NETWORK" "false"

    echo ""

    # 4. GCP resource availability
    echo -e "${BOLD}[4/8] Checking GCP resource availability${RESET}"

    # Check project
    local project=${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null)}
    if [[ -n "$project" ]]; then
        if gcloud projects describe "$project" &>/dev/null; then
            pass "GCP project '$project' exists"
        else
            fail "GCP project '$project' not found"
        fi
    else
        fail "GCP project not set - run: gcloud config set project PROJECT_ID"
    fi

    # Check VPC network
    local network=${GCP_NETWORK:-default}
    if gcloud compute networks describe "$network" --project="$project" &>/dev/null; then
        pass "VPC network '$network' exists"
    else
        info "VPC network '$network' not found - will be created"
    fi

    # Check GKE cluster quota
    local gke_count=$(gcloud container clusters list --project="$project" --format="value(name)" 2>/dev/null | wc -l)
    if [[ $gke_count -lt 95 ]]; then
        pass "GKE clusters: ${gke_count}/100 (sufficient)"
    else
        warn "High GKE cluster usage: ${gke_count}/100"
    fi

    # Check Compute Engine quota
    local region=${GCP_REGION:-us-central1}
    local cpu_quota=$(gcloud compute project-info describe --project="$project" --format="value(quotas[metric=CPUS].limit)" 2>/dev/null || echo "unknown")
    if [[ "$cpu_quota" != "unknown" && $cpu_quota -gt 24 ]]; then
        pass "Compute Engine CPU quota: ${cpu_quota} available"
    else
        warn "Low Compute Engine CPU quota: ${cpu_quota} available - may need quota increase"
    fi

    echo ""

    # 5. Network and security
    echo -e "${BOLD}[5/8] Checking network and security${RESET}"

    # Check if VPC exists
    if [[ -n "${GCP_NETWORK:-}" ]]; then
        if gcloud compute networks describe "$GCP_NETWORK" --project="$project" &>/dev/null; then
            pass "VPC network '$GCP_NETWORK' exists"
        else
            fail "VPC network '$GCP_NETWORK' not found"
        fi
    else
        info "GCP_NETWORK not set - will use default network"
    fi

    echo ""

    # 6. Kubernetes context
    echo -e "${BOLD}[6/8] Checking Kubernetes context${RESET}"

    if kubectl cluster-info &>/dev/null; then
        local context=$(kubectl config current-context 2>/dev/null)
        if [[ "$context" == gke_* ]]; then
            pass "kubectl context set to GKE cluster: ${context}"
        else
            warn "kubectl context (${context}) does not match expected GKE cluster"
        fi
    else
        info "kubectl not connected to cluster - will connect after GKE creation"
    fi

    echo ""

    # 7. Cost and resource estimation
    echo -e "${BOLD}[7/8] Estimating costs and resources${RESET}"

    # Rough cost estimation for GKE
    info "Estimated monthly costs for GKE cluster:"
    info "  - GKE control plane: ~$70/month"
    info "  - 3 e2-standard-4 nodes: ~$150/month"
    info "  - Load balancer: ~$20/month"
    info "  - Persistent disks: ~$10/month"
    info "  - Total estimate: ~$250+/month"
    info ""
    info "Note: Costs vary by region and exact node types"

    echo ""

    # 8. Final confirmation
    echo -e "${BOLD}[8/8] Deployment confirmation${RESET}"

    local cluster_name=${GKE_CLUSTER_NAME:-agentic-cluster}
    local region=${GCP_REGION:-us-central1}
    local project=${GOOGLE_CLOUD_PROJECT}

    echo -e "${YELLOW}This will deploy to GCP region: ${region}${NC}"
    echo -e "${YELLOW}GKE cluster name: ${cluster_name}${NC}"
    echo -e "${YELLOW}GCP project: ${project}${NC}"
    echo -e "${YELLOW}Estimated monthly cost: ~$250+${NC}"
    echo ""

    # Summary
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${RESET}"
    if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}  ✓ GCP production validation PASSED — ready for deployment${RESET}"
    elif [[ $ERRORS -eq 0 ]]; then
        echo -e "${YELLOW}${BOLD}  ⚠ GCP production validation PASSED with ${WARNINGS} warning(s)${RESET}"
        echo -e "${YELLOW}  Review warnings above before proceeding with deployment.${RESET}"
    else
        echo -e "${RED}${BOLD}  ✗ GCP production validation FAILED — ${ERRORS} error(s), ${WARNINGS} warning(s)${RESET}"
        echo -e "${RED}  Fix the errors above before proceeding.${RESET}"
        echo ""
        echo -e "  ${CYAN}Quick fixes:${RESET}"
        echo -e "    gcloud auth login                      # Authenticate with GCP"
        echo -e "    gcloud config set project PROJECT_ID   # Set GCP project"
        echo -e "    export GCP_REGION=us-central1           # Set GCP region"
        echo -e "    export GKE_CLUSTER_NAME=my-cluster      # Set cluster name"
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

# Create GKE cluster
create_gke_cluster() {
    print_header "Creating GKE Cluster"

    local cluster_name=${GKE_CLUSTER_NAME:-agentic-cluster}
    local region=${GCP_REGION:-us-central1}
    local project=${GOOGLE_CLOUD_PROJECT}

    if gcloud container clusters describe "$cluster_name" --region="$region" --project="$project" &>/dev/null; then
        print_info "GKE cluster '$cluster_name' already exists"
        return 0
    fi

    print_info "Creating GKE cluster '$cluster_name' in region '$region'..."

    # Create GKE cluster with standard configuration
    if gcloud container clusters create "$cluster_name" \
        --region="$region" \
        --project="$project" \
        --num-nodes=3 \
        --machine-type=e2-standard-4 \
        --enable-autoscaling \
        --min-nodes=1 \
        --max-nodes=5 \
        --enable-ip-alias \
        --enable-stackdriver-kubernetes \
        --enable-network-policy; then

        print_success "GKE cluster '$cluster_name' created successfully"
    else
        print_error "Failed to create GKE cluster"
        return 1
    fi

    # Get cluster credentials
    print_info "Getting GKE cluster credentials..."
    gcloud container clusters get-credentials "$cluster_name" --region="$region" --project="$project"

    print_success "GKE cluster setup complete"
}

# Deploy GCP Load Balancer Controller
deploy_gcp_load_balancer_controller() {
    print_header "Deploying GCP Load Balancer Controller"

    if kubectl get deployment glbc -n kube-system &>/dev/null; then
        print_info "GCP Load Balancer Controller already deployed"
        return 0
    fi

    print_info "Deploying GCP Load Balancer Controller..."

    # Enable required GCP APIs
    local project=${GOOGLE_CLOUD_PROJECT}
    gcloud services enable compute.googleapis.com --project="$project"
    gcloud services enable container.googleapis.com --project="$project"

    # Deploy the GCP Load Balancer Controller
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-gce/master/deploy/controller.yaml

    # Wait for deployment
    kubectl wait --for=condition=available --timeout=300s deployment/glbc -n kube-system

    print_success "GCP Load Balancer Controller deployed"
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
        print_info "To deploy dashboard later: QUICKSTART_DEPLOY_DASHBOARD=true ./core/scripts/automation/quickstart-remote-gcp.sh"
        return 0
    fi

    print_info "Deploying AI agents ecosystem with dashboard..."

    # Run the ecosystem deployment script
    if bash "$ecosystem_script"; then
        print_success "AI agents dashboard deployed successfully!"
        echo ""
        echo -e "${GREEN}🎉 Your AI Agents Dashboard is now running!${NC}"
        echo -e "${YELLOW}📊 Access it via GCP Load Balancer (check kubectl get ingress -n ai-infrastructure)${NC}"
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
        echo "  🧹 Clean up: ./core/scripts/automation/quickstart-remote-gcp.sh --cleanup"
        echo "  🔄 Restart: ./core/scripts/automation/quickstart-remote-gcp.sh --start-pf"
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

# Enhanced cleanup function for GCP
cleanup_gcp() {
    print_header "Cleaning up GCP environment"

    # Stop all port-forwards
    cleanup_port_forwards

    local cluster_name=${GKE_CLUSTER_NAME:-agentic-cluster}
    local region=${GCP_REGION:-us-central1}
    local project=${GOOGLE_CLOUD_PROJECT}

    # Ask for confirmation before destroying cluster
    echo -e "${RED}⚠️  This will destroy the GKE cluster and all associated resources!${NC}"
    echo -e "${RED}Cluster: ${cluster_name}${NC}"
    echo -e "${RED}Region: ${region}${NC}"
    echo -e "${RED}Project: ${project}${NC}"
    echo -e "${YELLOW}This action cannot be undone. Are you sure? (yes/NO)${NC}"
    read -r response

    if [[ "$response" != "yes" ]]; then
        print_info "Cleanup cancelled by user"
        return 0
    fi

    # Delete GKE cluster
    if gcloud container clusters describe "$cluster_name" --region="$region" --project="$project" &>/dev/null; then
        print_info "Deleting GKE cluster '$cluster_name'..."

        if gcloud container clusters delete "$cluster_name" --region="$region" --project="$project" --quiet; then
            print_success "GKE cluster deleted successfully"
        else
            print_error "Failed to delete GKE cluster"
        fi
    else
        print_info "GKE cluster '$cluster_name' not found"
    fi

    print_success "GCP environment cleanup completed"
}

# Main function for GCP production quickstart
main() {
    print_header "Agentic Reconciliation Engine - GCP Production Quick Start"

    echo -e "${BLUE}Welcome to Agentic Reconciliation Engine - GCP Production Deployment!${NC}"
    echo ""
    echo -e "${YELLOW}This will deploy a complete production environment on Google Cloud GKE.${NC}"
    echo -e "${RED}⚠️  This will create billable GCP resources!${NC}"
    echo ""

    # Check if we're in the right directory
    if [[ ! -f "$REPO_ROOT/README.md" ]]; then
        print_error "Not in repository root. Please run from repository root."
        exit 1
    fi

    # Run GCP production-specific validation
    print_info "Running GCP production prerequisites validation..."
    if ! run_gcp_production_validation; then
        print_error "GCP production validation failed. Please fix errors above and retry."
        exit 1
    fi

    # If there are warnings, prompt user to continue
    if [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Found $WARNINGS warning(s). Continue with GCP deployment? (Y/n)${NC}"
        read -r response
        if [[ "$response" =~ ^[Nn]$ ]]; then
            print_info "GCP deployment cancelled by user."
            exit 0
        fi
    fi

    # Final cost confirmation
    echo -e "${RED}⚠️  DEPLOYMENT COST WARNING${NC}"
    echo -e "${YELLOW}This deployment will create billable GCP resources with estimated monthly costs of ~$250+${NC}"
    echo -e "${YELLOW}Resources include: GKE cluster, Compute Engine VMs, Load Balancer, Persistent Disks${NC}"
    echo -e "${YELLOW}Do you want to proceed with deployment? (yes/NO)${NC}"
    read -r response
    if [[ "$response" != "yes" ]]; then
        print_info "GCP deployment cancelled by user."
        exit 0
    fi

    # Run pre-quickstart hook
    run_hooks "pre-quickstart" || return 1

    # Setup basic configuration
    print_info "Setting up GCP production environment..."

    # Create basic directories if they don't exist
    mkdir -p logs/
    mkdir -p tmp/

    # Make scripts executable
    find "$SCRIPT_DIR" -name "*.sh" -exec chmod +x {} \;
    find "$SCRIPT_DIR" -name "*.py" -exec chmod +x {} \;

    print_success "GCP production environment ready"

    # Create GKE cluster
    create_gke_cluster || return 1

    # Deploy GCP Load Balancer Controller
    deploy_gcp_load_balancer_controller || return 1

    # Run post-quickstart hook
    run_hooks "post-quickstart" || return 1

    # Deploy AI agents dashboard
    deploy_ai_agents_dashboard || return 1

    # Deploy AI Agent Skills and MCP servers
    deploy_ai_agent_skills || return 1

    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Access your AI agents dashboard via GCP Load Balancer"
    echo "2. Check service endpoints: kubectl get ingress -n ai-infrastructure"
    echo "3. Configure DNS for LoadBalancer services if needed"
    echo "4. Configure Claude Desktop with AI Agent Skills (auto-configured)"
    echo "5. Use consolidated K8sGPT: http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
    echo "6. Monitor GCP costs in Google Cloud Console Billing"
    echo "7. View port-forward logs: tail -f /tmp/quickstart-port-forwards/*.log"
    echo "8. Clean up environment: ./core/scripts/automation/quickstart-remote-gcp.sh --cleanup"
    echo ""
    echo -e "${GREEN}🚀 GCP production environment is ready!${NC}"
    echo -e "${YELLOW}🧠 AI agents are fully operational!${NC}"
    echo -e "${BLUE}☁️  GKE cluster is running in ${GCP_REGION}!${NC}"
    echo ""
    echo -e "${RED}💰 Remember to monitor your GCP costs!${NC}"
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
    echo "Agentic Reconciliation Engine - GCP Production Quick Start"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help         Show this help message"
    echo "  --validate         Run GCP production validation only"
    echo "  --cleanup          Clean up GKE cluster and resources"
    echo "  --start-pf         Start all port-forwards (if not already running)"
    echo "  --create-cluster   Create GKE cluster only"
    echo "  --deploy-lb        Deploy GCP Load Balancer Controller only"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up a complete production environment on Google Cloud GKE."
    echo "  This includes GKE cluster creation, GCP Load Balancer Controller,"
    echo "  comprehensive prerequisites validation, and deployment of AI agents dashboard."
    echo ""
    echo "  ⚠️  This creates billable GCP resources! Monitor costs carefully."
    echo ""
    echo "EXAMPLES:"
    echo "  $0                        # Complete GCP production setup"
    echo "  $0 --validate            # Validate GCP prerequisites only"
    echo "  $0 --cleanup             # Clean up GCP environment (destructive!)"
    echo "  $0 --create-cluster      # Create GKE cluster only"
    echo ""
    echo "GCP REQUIREMENTS:"
    echo "  - gcloud CLI logged in with appropriate permissions"
    echo "  - Sufficient GCP quota for GKE, Compute Engine, Load Balancing"
    echo "  - Budget for ~$250+/month in costs"
    echo ""
    echo "REQUIRED PERMISSIONS:"
    echo "  - container.* (GKE operations)"
    echo "  - compute.* (VMs, networks, load balancers)"
    echo "  - storage.* (if using GCS)"
    echo "  - monitoring.* (Stackdriver)"
    echo ""
    echo "SERVICES ACCESS:"
    echo "  🚪 Infrastructure Portal:  GCP Load Balancer"
    echo "  🤖 AI Dashboard:        GCP Load Balancer"
    echo "  📊 Dashboard API:        GCP Load Balancer"
    echo "  ⏰ Temporal UI:          GCP Load Balancer"
    echo "  🔍 Langfuse Observability: GCP Load Balancer"
    echo "  📈 Comprehensive API:   GCP Load Balancer"
    echo "  🖥️  Comprehensive Frontend: GCP Load Balancer"
    echo "  🧠 Memory Service:       GCP Load Balancer"
    echo ""
    echo "COST ESTIMATION:"
    echo "  - GKE control plane: ~$70/month"
    echo "  - 3 e2-standard-4 nodes: ~$150/month"
    echo "  - Load balancer: ~$20/month"
    echo "  - Persistent disks: ~$10/month"
    echo "  - Total: ~$250/month (varies by region and usage)"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    --validate)
        run_gcp_production_validation
        exit $?
        ;;
    --cleanup)
        cleanup_gcp
        exit 0
        ;;
    --start-pf)
        start_all_port_forwards
        exit 0
        ;;
    --create-cluster)
        create_gke_cluster
        exit $?
        ;;
    --deploy-lb)
        deploy_gcp_load_balancer_controller
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

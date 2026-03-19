#!/bin/bash
# Agentic Reconciliation Engine - Quick Start for Remote Azure Production
# Repository setup and initial onboarding for Azure AKS production deployments

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

# Environment-specific validation for Remote Azure
run_azure_production_validation() {
    ERRORS=0
    WARNINGS=0

    echo ""
    echo -e "${BOLD}╔═══════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}║  agentic-reconciliation-engine — Azure Production Validation ║${RESET}"
    echo -e "${BOLD}╚═══════════════════════════════════════════════════════════════╝${RESET}"
    echo ""

    # 1. Azure prerequisites
    echo -e "${BOLD}[1/8] Checking Azure prerequisites${RESET}"

    # Check Azure CLI
    if command -v az &>/dev/null; then
        local az_version=$(az version --query '"azure-cli"' -o tsv 2>/dev/null || echo "unknown")
        pass "Azure CLI available (${az_version})"
    else
        fail "Azure CLI not found (required for Azure operations)"
    fi

    # Check kubectl
    if command -v kubectl &>/dev/null; then
        local kube_version=$(kubectl version --client --short 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        pass "kubectl available (${kube_version})"
    else
        fail "kubectl not found (required for AKS)"
    fi

    # Check Azure authentication
    if az account show &>/dev/null; then
        local sub_name=$(az account show --query name -o tsv 2>/dev/null)
        local sub_id=$(az account show --query id -o tsv 2>/dev/null)
        local user=$(az account show --query user.name -o tsv 2>/dev/null)
        pass "Azure authenticated - Subscription: ${sub_name} (${sub_id}), User: ${user}"
    else
        fail "Azure authentication failed - run: az login"
    fi

    # Check if AKS cluster exists
    local cluster_name=${AKS_CLUSTER_NAME:-agentic-cluster}
    local rg_name=${AZURE_RESOURCE_GROUP:-agentic-rg}
    if az aks show --name "$cluster_name" --resource-group "$rg_name" &>/dev/null; then
        pass "AKS cluster '$cluster_name' exists"
    else
        warn "AKS cluster '$cluster_name' not found - will be created"
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

    # Required for Azure
    check_tool "helm"       "3.12"
    check_tool "terraform"  "1.6"
    check_tool "jq"         "1.6"
    check_tool "yq"         "4.0"

    # Optional but recommended
    check_tool_optional "kubectx"
    check_tool_optional "kubens"
    check_tool_optional "kustomize"

    echo ""

    # 3. Azure region and environment
    echo -e "${BOLD}[3/8] Checking Azure region and environment${RESET}"

    # Check Azure region
    local location=${AZURE_LOCATION:-$(az configure --list-defaults | grep location | awk '{print $2}' || echo "eastus")}
    if [[ -n "$location" ]]; then
        pass "Azure location: ${location}"

        # Check region availability (basic check)
        if az account list-locations --query "[?name=='${location}']" &>/dev/null; then
            pass "Location ${location} is available"
        else
            warn "Location ${location} may not be available"
        fi
    else
        fail "Azure location not set"
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

    check_env_var "AZURE_LOCATION" "false"
    check_env_var "AKS_CLUSTER_NAME" "false"
    check_env_var "AZURE_RESOURCE_GROUP" "false"
    check_env_var "AZURE_SUBSCRIPTION_ID" "false"

    echo ""

    # 4. Azure resource availability
    echo -e "${BOLD}[4/8] Checking Azure resource availability${RESET}"

    # Check resource group
    local rg_name=${AZURE_RESOURCE_GROUP:-agentic-rg}
    if az group show --name "$rg_name" &>/dev/null; then
        pass "Resource group '$rg_name' exists"
    else
        info "Resource group '$rg_name' not found - will be created"
    fi

    # Check AKS cluster quota
    local aks_count=$(az aks list --query "length(@)" -o tsv 2>/dev/null || echo "unknown")
    if [[ "$aks_count" != "unknown" && $aks_count -lt 95 ]]; then
        pass "AKS clusters: ${aks_count}/100 (sufficient)"
    else
        warn "High AKS cluster usage: ${aks_count}/100"
    fi

    # Check VM quota
    local location=${AZURE_LOCATION:-eastus}
    local vm_quota=$(az vm list-usage --location "$location" --query "[?name.localizedValue=='Total Regional vCPUs']" -o tsv 2>/dev/null | awk '{print $1}' || echo "unknown")
    if [[ "$vm_quota" != "unknown" && $vm_quota -gt 10 ]]; then
        pass "VM vCPU quota: ${vm_quota} available"
    else
        warn "Low VM vCPU quota: ${vm_quota} available - may need quota increase"
    fi

    echo ""

    # 5. Network and security
    echo -e "${BOLD}[5/8] Checking network and security${RESET}"

    # Check VNet
    local vnet_name=${AZURE_VNET_NAME:-agentic-vnet}
    local rg_name=${AZURE_RESOURCE_GROUP:-agentic-rg}
    if az network vnet show --name "$vnet_name" --resource-group "$rg_name" &>/dev/null; then
        pass "Virtual network '$vnet_name' exists"
    else
        info "Virtual network '$vnet_name' not found - will be created"
    fi

    echo ""

    # 6. Kubernetes context
    echo -e "${BOLD}[6/8] Checking Kubernetes context${RESET}"

    if kubectl cluster-info &>/dev/null; then
        local context=$(kubectl config current-context 2>/dev/null)
        if [[ "$context" == *aks* ]]; then
            pass "kubectl context set to AKS cluster: ${context}"
        else
            warn "kubectl context (${context}) does not match expected AKS cluster"
        fi
    else
        info "kubectl not connected to cluster - will connect after AKS creation"
    fi

    echo ""

    # 7. Cost and resource estimation
    echo -e "${BOLD}[7/8] Estimating costs and resources${RESET}"

    # Rough cost estimation for AKS
    info "Estimated monthly costs for AKS cluster:"
    info "  - AKS control plane: ~$70/month"
    info "  - 3 Standard_D2_v3 nodes: ~$150/month"
    info "  - Azure Load Balancer: ~$20/month"
    info "  - Azure Disk storage: ~$10/month"
    info "  - Total estimate: ~$250+/month"
    info ""
    info "Note: Costs vary by region and exact VM sizes"

    echo ""

    # 8. Final confirmation
    echo -e "${BOLD}[8/8] Deployment confirmation${RESET}"

    local cluster_name=${AKS_CLUSTER_NAME:-agentic-cluster}
    local rg_name=${AZURE_RESOURCE_GROUP:-agentic-rg}
    local location=${AZURE_LOCATION:-eastus}

    echo -e "${YELLOW}This will deploy to Azure region: ${location}${NC}"
    echo -e "${YELLOW}AKS cluster name: ${cluster_name}${NC}"
    echo -e "${YELLOW}Resource group: ${rg_name}${NC}"
    echo -e "${YELLOW}Estimated monthly cost: ~$250+${NC}"
    echo ""

    # Summary
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${RESET}"
    if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}  ✓ Azure production validation PASSED — ready for deployment${RESET}"
    elif [[ $ERRORS -eq 0 ]]; then
        echo -e "${YELLOW}${BOLD}  ⚠ Azure production validation PASSED with ${WARNINGS} warning(s)${RESET}"
        echo -e "${YELLOW}  Review warnings above before proceeding with deployment.${RESET}"
    else
        echo -e "${RED}${BOLD}  ✗ Azure production validation FAILED — ${ERRORS} error(s), ${WARNINGS} warning(s)${RESET}"
        echo -e "${RED}  Fix the errors above before proceeding.${RESET}"
        echo ""
        echo -e "  ${CYAN}Quick fixes:${RESET}"
        echo -e "    az login                              # Authenticate with Azure"
        echo -e "    export AZURE_LOCATION=eastus          # Set Azure region"
        echo -e "    export AKS_CLUSTER_NAME=my-cluster    # Set cluster name"
        echo -e "    export AZURE_RESOURCE_GROUP=my-rg     # Set resource group"
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

# Create AKS cluster
create_aks_cluster() {
    print_header "Creating AKS Cluster"

    local cluster_name=${AKS_CLUSTER_NAME:-agentic-cluster}
    local rg_name=${AZURE_RESOURCE_GROUP:-agentic-rg}
    local location=${AZURE_LOCATION:-eastus}

    if az aks show --name "$cluster_name" --resource-group "$rg_name" &>/dev/null; then
        print_info "AKS cluster '$cluster_name' already exists"
        return 0
    fi

    print_info "Creating AKS cluster '$cluster_name' in resource group '$rg_name'..."

    # Create resource group if it doesn't exist
    if ! az group show --name "$rg_name" &>/dev/null; then
        print_info "Creating resource group '$rg_name'..."
        az group create --name "$rg_name" --location "$location"
    fi

    # Create AKS cluster
    if az aks create \
        --resource-group "$rg_name" \
        --name "$cluster_name" \
        --node-count 3 \
        --node-vm-size Standard_D2_v3 \
        --enable-managed-identity \
        --generate-ssh-keys \
        --enable-addons monitoring \
        --enable-msi-auth-for-monitoring \
        --enable-cluster-autoscaler \
        --min-count 1 \
        --max-count 5; then

        print_success "AKS cluster '$cluster_name' created successfully"
    else
        print_error "Failed to create AKS cluster"
        return 1
    fi

    # Get AKS credentials
    print_info "Getting AKS credentials..."
    az aks get-credentials --resource-group "$rg_name" --name "$cluster_name" --overwrite-existing

    print_success "AKS cluster setup complete"
}

# Deploy Azure Application Gateway Ingress Controller
deploy_azure_ingress_controller() {
    print_header "Deploying Azure Application Gateway Ingress Controller"

    local rg_name=${AZURE_RESOURCE_GROUP:-agentic-rg}
    local location=${AZURE_LOCATION:-eastus}
    local cluster_name=${AKS_CLUSTER_NAME:-agentic-cluster}

    if kubectl get deployment ingress-appgw-deployment -n kube-system &>/dev/null; then
        print_info "Azure Application Gateway Ingress Controller already deployed"
        return 0
    fi

    print_info "Deploying Azure Application Gateway Ingress Controller..."

    # Create Application Gateway
    local ag_name="${cluster_name}-ag"
    if ! az network application-gateway show --name "$ag_name" --resource-group "$rg_name" &>/dev/null; then
        print_info "Creating Azure Application Gateway..."

        # Get AKS subnet
        local vnet_name=$(az aks show --resource-group "$rg_name" --name "$cluster_name" --query "agentPoolProfiles[0].vnetSubnetId" -o tsv | awk -F'/' '{print $(NF-2)}')
        local subnet_name=$(az aks show --resource-group "$rg_name" --name "$cluster_name" --query "agentPoolProfiles[0].vnetSubnetId" -o tsv | awk -F'/' '{print $NF}')

        # Create Application Gateway in AKS subnet
        az network application-gateway create \
            --name "$ag_name" \
            --resource-group "$rg_name" \
            --location "$location" \
            --sku Standard_v2 \
            --public-ip-address "$ag_name-pip" \
            --vnet-name "$vnet_name" \
            --subnet "$subnet_name" \
            --min-capacity 0 \
            --max-capacity 10
    fi

    # Install AGIC using Helm
    helm repo add application-gateway-kubernetes-ingress https://appgwingress.blob.core.windows.net/ingress-azure-helm-package/
    helm repo update

    helm install ingress-azure application-gateway-kubernetes-ingress/ingress-azure \
        --namespace kube-system \
        --set appgw.name="$ag_name" \
        --set appgw.resourceGroup="$rg_name" \
        --set appgw.subscriptionId="$AZURE_SUBSCRIPTION_ID" \
        --set appgw.usePrivateIP=false \
        --set appgw.shared=false \
        --set verbosityLevel=3 \
        --set kubernetes.watchNamespace="" \
        --set armAuth.type=msi \
        --set rbac.enabled=true

    # Wait for deployment
    kubectl wait --for=condition=available --timeout=600s deployment/ingress-appgw-deployment -n kube-system

    print_success "Azure Application Gateway Ingress Controller deployed"
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
        print_info "To deploy dashboard later: QUICKSTART_DEPLOY_DASHBOARD=true ./core/scripts/automation/quickstart-remote-azure.sh"
        return 0
    fi

    print_info "Deploying AI agents ecosystem with dashboard..."

    # Run the ecosystem deployment script
    if bash "$ecosystem_script"; then
        print_success "AI agents dashboard deployed successfully!"
        echo ""
        echo -e "${GREEN}🎉 Your AI Agents Dashboard is now running!${NC}"
        echo -e "${YELLOW}📊 Access it via Azure Application Gateway (check kubectl get ingress -n ai-infrastructure)${NC}"
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
        echo "  🧹 Clean up: ./core/scripts/automation/quickstart-remote-azure.sh --cleanup"
        echo "  🔄 Restart: ./core/scripts/automation/quickstart-remote-azure.sh --start-pf"
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

# Enhanced cleanup function for Azure
cleanup_azure() {
    print_header "Cleaning up Azure environment"

    # Stop all port-forwards
    cleanup_port_forwards

    local cluster_name=${AKS_CLUSTER_NAME:-agentic-cluster}
    local rg_name=${AZURE_RESOURCE_GROUP:-agentic-rg}

    # Ask for confirmation before destroying cluster
    echo -e "${RED}⚠️  This will destroy the AKS cluster and all associated resources!${NC}"
    echo -e "${RED}Cluster: ${cluster_name}${NC}"
    echo -e "${RED}Resource Group: ${rg_name}${NC}"
    echo -e "${YELLOW}This action cannot be undone. Are you sure? (yes/NO)${NC}"
    read -r response

    if [[ "$response" != "yes" ]]; then
        print_info "Cleanup cancelled by user"
        return 0
    fi

    # Delete AKS cluster
    if az aks show --name "$cluster_name" --resource-group "$rg_name" &>/dev/null; then
        print_info "Deleting AKS cluster '$cluster_name'..."

        if az aks delete --name "$cluster_name" --resource-group "$rg_name" --yes; then
            print_success "AKS cluster deleted successfully"
        else
            print_error "Failed to delete AKS cluster"
        fi
    else
        print_info "AKS cluster '$cluster_name' not found"
    fi

    # Ask about deleting resource group
    echo -e "${RED}Delete resource group '${rg_name}' and all resources? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_info "Deleting resource group '$rg_name'..."
        if az group delete --name "$rg_name" --yes; then
            print_success "Resource group deleted successfully"
        else
            print_warning "Failed to delete resource group"
        fi
    fi

    print_success "Azure environment cleanup completed"
}

# Main function for Azure production quickstart
main() {
    print_header "Agentic Reconciliation Engine - Azure Production Quick Start"

    echo -e "${BLUE}Welcome to Agentic Reconciliation Engine - Azure Production Deployment!${NC}"
    echo ""
    echo -e "${YELLOW}This will deploy a complete production environment on Azure AKS.${NC}"
    echo -e "${RED}⚠️  This will create billable Azure resources!${NC}"
    echo ""

    # Check if we're in the right directory
    if [[ ! -f "$REPO_ROOT/README.md" ]]; then
        print_error "Not in repository root. Please run from repository root."
        exit 1
    fi

    # Run Azure production-specific validation
    print_info "Running Azure production prerequisites validation..."
    if ! run_azure_production_validation; then
        print_error "Azure production validation failed. Please fix errors above and retry."
        exit 1
    fi

    # If there are warnings, prompt user to continue
    if [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Found $WARNINGS warning(s). Continue with Azure deployment? (Y/n)${NC}"
        read -r response
        if [[ "$response" =~ ^[Nn]$ ]]; then
            print_info "Azure deployment cancelled by user."
            exit 0
        fi
    fi

    # Final cost confirmation
    echo -e "${RED}⚠️  DEPLOYMENT COST WARNING${NC}"
    echo -e "${YELLOW}This deployment will create billable Azure resources with estimated monthly costs of ~$250+${NC}"
    echo -e "${YELLOW}Resources include: AKS cluster, VMs, Application Gateway, managed disks${NC}"
    echo -e "${YELLOW}Do you want to proceed with deployment? (yes/NO)${NC}"
    read -r response
    if [[ "$response" != "yes" ]]; then
        print_info "Azure deployment cancelled by user."
        exit 0
    fi

    # Run pre-quickstart hook
    run_hooks "pre-quickstart" || return 1

    # Setup basic configuration
    print_info "Setting up Azure production environment..."

    # Create basic directories if they don't exist
    mkdir -p logs/
    mkdir -p tmp/

    # Make scripts executable
    find "$SCRIPT_DIR" -name "*.sh" -exec chmod +x {} \;
    find "$SCRIPT_DIR" -name "*.py" -exec chmod +x {} \;

    print_success "Azure production environment ready"

    # Create AKS cluster
    create_aks_cluster || return 1

    # Deploy Azure Application Gateway Ingress Controller
    deploy_azure_ingress_controller || return 1

    # Run post-quickstart hook
    run_hooks "post-quickstart" || return 1

    # Deploy AI agents dashboard
    deploy_ai_agents_dashboard || return 1

    # Deploy AI Agent Skills and MCP servers
    deploy_ai_agent_skills || return 1

    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Access your AI agents dashboard via Azure Application Gateway"
    echo "2. Check service endpoints: kubectl get ingress -n ai-infrastructure"
    echo "3. Configure DNS for Application Gateway public IP if needed"
    echo "4. Configure Claude Desktop with AI Agent Skills (auto-configured)"
    echo "5. Use consolidated K8sGPT: http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
    echo "6. Monitor Azure costs in Azure Cost Management"
    echo "7. View port-forward logs: tail -f /tmp/quickstart-port-forwards/*.log"
    echo "8. Clean up environment: ./core/scripts/automation/quickstart-remote-azure.sh --cleanup"
    echo ""
    echo -e "${GREEN}🚀 Azure production environment is ready!${NC}"
    echo -e "${YELLOW}🧠 AI agents are fully operational!${NC}"
    echo -e "${BLUE}☁️  Azure AKS cluster is running in ${AZURE_LOCATION}!${NC}"
    echo ""
    echo -e "${RED}💰 Remember to monitor your Azure costs!${NC}"
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
    echo "Agentic Reconciliation Engine - Azure Production Quick Start"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help         Show this help message"
    echo "  --validate         Run Azure production validation only"
    echo "  --cleanup          Clean up Azure AKS cluster and resources"
    echo "  --start-pf         Start all port-forwards (if not already running)"
    echo "  --create-cluster   Create AKS cluster only"
    echo "  --deploy-ag        Deploy Azure Application Gateway only"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up a complete production environment on Azure AKS."
    echo "  This includes AKS cluster creation, Application Gateway ingress,"
    echo "  comprehensive prerequisites validation, and deployment of AI agents dashboard."
    echo ""
    echo "  ⚠️  This creates billable Azure resources! Monitor costs carefully."
    echo ""
    echo "EXAMPLES:"
    echo "  $0                        # Complete Azure production setup"
    echo "  $0 --validate            # Validate Azure prerequisites only"
    echo "  $0 --cleanup             # Clean up Azure environment (destructive!)"
    echo "  $0 --create-cluster      # Create AKS cluster only"
    echo ""
    echo "AZURE REQUIREMENTS:"
    echo "  - Azure CLI logged in with appropriate permissions"
    echo "  - Sufficient Azure quota for AKS, VMs, Application Gateway"
    echo "  - Budget for ~$250+/month in costs"
    echo ""
    echo "REQUIRED PERMISSIONS:"
    echo "  - Microsoft.ContainerService/managedClusters/* (AKS)"
    echo "  - Microsoft.Network/* (VNet, Application Gateway)"
    echo "  - Microsoft.Storage/* (if using Azure Storage)"
    echo "  - Microsoft.KeyVault/* (if using Key Vault)"
    echo ""
    echo "SERVICES ACCESS:"
    echo "  🚪 Infrastructure Portal:  Azure Application Gateway"
    echo "  🤖 AI Dashboard:        Azure Application Gateway"
    echo "  📊 Dashboard API:        Azure Application Gateway"
    echo "  ⏰ Temporal UI:          Azure Application Gateway"
    echo "  🔍 Langfuse Observability: Azure Application Gateway"
    echo "  📈 Comprehensive API:   Azure Application Gateway"
    echo "  🖥️  Comprehensive Frontend: Azure Application Gateway"
    echo "  🧠 Memory Service:       Azure Application Gateway"
    echo ""
    echo "COST ESTIMATION:"
    echo "  - AKS control plane: ~$70/month"
    echo "  - 3 Standard_D2_v3 nodes: ~$150/month"
    echo "  - Application Gateway: ~$20/month"
    echo "  - Managed disks: ~$10/month"
    echo "  - Total: ~$250/month (varies by region and usage)"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    --validate)
        run_azure_production_validation
        exit $?
        ;;
    --cleanup)
        cleanup_azure
        exit 0
        ;;
    --start-pf)
        start_all_port_forwards
        exit 0
        ;;
    --create-cluster)
        create_aks_cluster
        exit $?
        ;;
    --deploy-ag)
        deploy_azure_ingress_controller
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

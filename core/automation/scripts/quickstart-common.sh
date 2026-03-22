#!/bin/bash
# Agentic Reconciliation Engine - Common Quick Start Functions
# Shared functions for all environment-specific quickstart scripts

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script information
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel)"

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

# Hook support - allows overlays to extend quickstart without modification
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

# Deploy AI Agent Skills and MCP servers
deploy_ai_agent_skills() {
    # Call the dedicated deployment script
    local deploy_script="$SCRIPT_DIR/deploy_ai_agent_skills.sh"
    
    if [[ -f "$deploy_script" ]]; then
        print_info "Running AI Agent Skills deployment..."
        if bash "$deploy_script"; then
            print_success "AI Agent Skills deployed successfully"
        else
            print_error "AI Agent Skills deployment failed"
            return 1
        fi
    else
        print_error "AI Agent Skills deployment script not found at $deploy_script"
        return 1
    fi
}

# Deploy AI agents dashboard function
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
        print_info "To deploy dashboard later: QUICKSTART_DEPLOY_DASHBOARD=true ./core/automation/scripts/quickstart.sh"
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
        echo "To access the dashboard:"
        echo "1. Port forward: kubectl port-forward -n ai-infrastructure svc/agent-dashboard-service 8080:80"
        echo "2. Open browser: http://localhost:8080"
        echo ""
        echo "Dashboard features:"
        echo "  ✅ Real-time AI agents monitoring"
        echo "  ✅ 91 operational skills visualization"
        echo "  ✅ Performance metrics and charts"
        echo "  ✅ Activity feed and system controls"
        echo "  ✅ Temporal workflow orchestration UI"
    else
        print_error "Failed to deploy AI agents dashboard"
        print_info "Check the logs above for errors and try running the script manually"
        return 1
    fi
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check for required tools
    local missing_tools=()
    
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    if ! command -v kustomize &> /dev/null; then
        missing_tools+=("kustomize")
    fi
    
    if ! command -v python3 &> /dev/null; then
        missing_tools+=("python3")
    fi
    
    if ! command -v git &> /dev/null; then
        missing_tools+=("git")
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        echo -e "${YELLOW}Please install missing tools and try again.${NC}"
        exit 1
    fi
    
    print_success "All prerequisites satisfied"
}

# Setup basic configuration
setup_basic_config() {
    print_info "Setting up development environment..."
    
    # Create basic directories if they don't exist
    mkdir -p logs/
    mkdir -p tmp/
    
    # Create overlay hooks if in overlay mode
    if [[ "${OVERLAY_MODE:-false}" == "true" ]]; then
        # Source overlay common functions if available
        if [[ -f "$SCRIPT_DIR/overlay-quickstart-common.sh" ]]; then
            source "$SCRIPT_DIR/overlay-quickstart-common.sh"
            create_overlay_hooks
        fi
    fi
    
    # Make scripts executable
    find "$SCRIPT_DIR" -name "*.sh" -exec chmod +x {} \;
    find "$SCRIPT_DIR" -name "*.py" -exec chmod +x {} \;
    
    print_success "Development environment ready"
}

# Environment-specific setup functions
setup_kind_environment() {
    print_info "Setting up Kind environment..."
    
    # Check if Kind is installed
    if ! command -v kind &> /dev/null; then
        print_error "Kind is not installed. Please install Kind first."
        print_info "Installation: brew install kind or curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-darwin-amd64"
        return 1
    fi
    
    # Check if cluster exists
    if ! kind get clusters | grep -q "agentic-reconciliation"; then
        print_info "Creating Kind cluster..."
        kind create cluster --name agentic-reconciliation --config "$SCRIPT_DIR/../config/kind/cluster-config.yaml" || {
            print_warning "Failed to create cluster with config, trying default config..."
            kind create cluster --name agentic-reconciliation
        }
    else
        print_info "Kind cluster already exists"
    fi
    
    # Set kubectl context
    kubectl cluster-info --context kind-agentic-reconciliation &> /dev/null || {
        print_error "Failed to set Kind cluster context"
        return 1
    }
    
    print_success "Kind environment ready"
}

setup_docker_desktop_environment() {
    print_info "Setting up Docker Desktop environment..."
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker Desktop is not running. Please start Docker Desktop."
        return 1
    fi
    
    # Check if Kubernetes is enabled in Docker Desktop
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Kubernetes is not enabled in Docker Desktop."
        print_info "Please enable Kubernetes in Docker Desktop preferences."
        return 1
    fi
    
    print_success "Docker Desktop environment ready"
}

setup_minikube_environment() {
    print_info "Setting up Minikube environment..."
    
    # Check if Minikube is installed
    if ! command -v minikube &> /dev/null; then
        print_error "Minikube is not installed. Please install Minikube first."
        print_info "Installation: brew install minikube"
        return 1
    fi
    
    # Check if Minikube is running
    if ! minikube status &> /dev/null; then
        print_info "Starting Minikube..."
        minikube start
    else
        print_info "Minikube is already running"
    fi
    
    # Set kubectl context
    kubectl config use-context minikube &> /dev/null || {
        print_error "Failed to set Minikube context"
        return 1
    }
    
    print_success "Minikube environment ready"
}

setup_localstack_aws_environment() {
    print_info "Setting up LocalStack AWS environment..."
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker."
        return 1
    fi
    
    # Check if LocalStack is installed
    if ! command -v localstack &> /dev/null && ! docker images | grep -q "localstack"; then
        print_info "Pulling LocalStack Docker image..."
        docker pull localstack/localstack
    fi
    
    # Start LocalStack if not running
    if ! docker ps | grep -q "localstack"; then
        print_info "Starting LocalStack..."
        docker run -d -p 4566:4566 -p 4571:4571 --name localstack localstack/localstack || {
            print_warning "Failed to start new LocalStack container, checking if existing..."
            docker start localstack 2>/dev/null || {
                print_error "Failed to start LocalStack"
                return 1
            }
        }
    else
        print_info "LocalStack is already running"
    fi
    
    # Configure AWS CLI for LocalStack
    export AWS_ACCESS_KEY_ID=test
    export AWS_SECRET_ACCESS_KEY=test
    export AWS_DEFAULT_REGION=us-east-1
    export AWS_ENDPOINT_URL=http://localhost:4566
    
    print_success "LocalStack AWS environment ready"
}

setup_azurite_azure_environment() {
    print_info "Setting up Azurite Azure environment..."
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker."
        return 1
    fi
    
    # Check if Azurite is installed
    if ! docker images | grep -q "azurite"; then
        print_info "Pulling Azurite Docker image..."
        docker pull mcr.microsoft.com/azure-storage/azurite
    fi
    
    # Start Azurite if not running
    if ! docker ps | grep -q "azurite"; then
        print_info "Starting Azurite..."
        docker run -d -p 10000:10000 -p 10001:10001 -p 10002:10002 --name azurite mcr.microsoft.com/azure-storage/azurite || {
            print_warning "Failed to start new Azurite container, checking if existing..."
            docker start azurite 2>/dev/null || {
                print_error "Failed to start Azurite"
                return 1
            }
        }
    else
        print_info "Azurite is already running"
    fi
    
    print_success "Azurite Azure environment ready"
}

setup_gcloud_emulator_environment() {
    print_info "Setting up Google Cloud emulator environment..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        print_error "Google Cloud SDK is not installed. Please install gcloud first."
        print_info "Installation: curl https://sdk.cloud.google.com | bash"
        return 1
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker."
        return 1
    fi
    
    # Start Cloud Datastore emulator
    print_info "Starting Cloud Datastore emulator..."
    gcloud emulators datastore start --host-port=localhost:8081 --consistency=1.0 &
    local datastore_pid=$!
    
    # Start Cloud Pub/Sub emulator
    print_info "Starting Cloud Pub/Sub emulator..."
    gcloud emulators pubsub start --host-port=localhost:8085 &
    local pubsub_pid=$!
    
    # Set environment variables
    export DATASTORE_EMULATOR_HOST=localhost:8081
    export PUBSUB_EMULATOR_HOST=localhost:8085
    
    # Store PIDs for cleanup
    echo "$datastore_pid" > /tmp/gcloud-datastore-emulator.pid
    echo "$pubsub_pid" > /tmp/gcloud-pubsub-emulator.pid
    
    print_success "Google Cloud emulator environment ready"
}

setup_aws_environment() {
    print_info "Setting up AWS environment..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install AWS CLI first."
        print_info "Installation: brew install awscli"
        return 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure'."
        return 1
    fi
    
    # Check if kubectl is configured for EKS
    if ! kubectl cluster-info &> /dev/null; then
        print_warning "kubectl not configured for EKS cluster"
        print_info "Please update your kubeconfig: aws eks update-kubeconfig --region <region> --name <cluster-name>"
    fi
    
    print_success "AWS environment ready"
}

setup_azure_environment() {
    print_info "Setting up Azure environment..."
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install Azure CLI first."
        print_info "Installation: brew install azure-cli"
        return 1
    fi
    
    # Check Azure login
    if ! az account show &> /dev/null; then
        print_error "Not logged into Azure. Please run 'az login'."
        return 1
    fi
    
    # Check if kubectl is configured for AKS
    if ! kubectl cluster-info &> /dev/null; then
        print_warning "kubectl not configured for AKS cluster"
        print_info "Please update your kubeconfig: az aks get-credentials --resource-group <group> --name <cluster>"
    fi
    
    print_success "Azure environment ready"
}

setup_gcp_environment() {
    print_info "Setting up GCP environment..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        print_error "Google Cloud SDK is not installed. Please install gcloud first."
        print_info "Installation: curl https://sdk.cloud.google.com | bash"
        return 1
    fi
    
    # Check GCP login
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 | grep -q "@"; then
        print_error "Not logged into GCP. Please run 'gcloud auth login'."
        return 1
    fi
    
    # Check if kubectl is configured for GKE
    if ! kubectl cluster-info &> /dev/null; then
        print_warning "kubectl not configured for GKE cluster"
        print_info "Please update your kubeconfig: gcloud container clusters get-credentials <cluster-name> --zone <zone>"
    fi
    
    print_success "GCP environment ready"
}

setup_on_prem_environment() {
    print_info "Setting up on-premises environment..."
    
    # Check if kubectl is configured
    if ! kubectl cluster-info &> /dev/null; then
        print_error "kubectl not configured for on-premises cluster"
        print_info "Please update your kubeconfig to point to your on-premises cluster"
        return 1
    fi
    
    print_success "On-premises environment ready"
}

# Create basic examples
create_basic_examples() {
    echo -e "${BLUE}Creating basic examples...${NC}"
    mkdir -p overlay/examples/basic/
    cat > overlay/examples/basic/README.md << 'EOF'
# Basic Examples

This directory contains basic examples for getting started with the Agentic Reconciliation Engine.

## Quick Start Examples

1. **Basic Setup**: Run the environment-specific quickstart script
2. **Overlay Mode**: Run the environment-specific overlay-quickstart script
3. **Advanced**: See `overlay/examples/` directory for comprehensive examples

## Next Steps

1. Read the documentation in `docs/`
2. Check the examples in `overlay/examples/`
3. Use the scripts in `core/automation/scripts/` for automation
EOF
    print_success "Basic examples created"
}

# Common main function
common_main() {
    local environment="$1"
    
    print_header "Agentic Reconciliation Engine Quick Start - $environment"
    
    echo -e "${BLUE}Welcome to Agentic Reconciliation Engine!${NC}"
    echo ""
    
    # Check if we're in overlay mode
    if [[ "${OVERLAY_MODE:-false}" == "true" ]]; then
        echo -e "${YELLOW}Running in overlay mode${NC}"
    else
        echo -e "${YELLOW}This script sets up your $environment development environment.${NC}"
    fi
    echo ""
    
    # Check if we're in the right directory
    if [[ ! -f "$REPO_ROOT/README.md" ]]; then
        print_error "Not in repository root. Please run from repository root."
        exit 1
    fi
    
    # Run pre-quickstart hook (overlay extension point)
    run_hooks "pre-quickstart" || return 1
    
    # Check prerequisites
    check_prerequisites
    
    # Setup environment-specific configuration
    case "$environment" in
        "Kind")
            setup_kind_environment || return 1
            ;;
        "Docker Desktop")
            setup_docker_desktop_environment || return 1
            ;;
        "Minikube")
            setup_minikube_environment || return 1
            ;;
        "LocalStack AWS")
            setup_localstack_aws_environment || return 1
            ;;
        "Azurite Azure")
            setup_azurite_azure_environment || return 1
            ;;
        "Google Cloud Emulator")
            setup_gcloud_emulator_environment || return 1
            ;;
        "AWS")
            setup_aws_environment || return 1
            ;;
        "Azure")
            setup_azure_environment || return 1
            ;;
        "GCP")
            setup_gcp_environment || return 1
            ;;
        "General")
            print_info "Setting up General development environment..."
            # General environment doesn't need specific cluster setup
            # Just check if kubectl is accessible for dashboard deployment
            if ! kubectl cluster-info &> /dev/null; then
                print_warning "Kubernetes cluster not accessible - dashboard deployment will be skipped"
                print_info "You can deploy the dashboard later by configuring kubectl and running: ./core/automation/scripts/deploy-ai-agents-ecosystem.sh"
            fi
            print_success "General environment ready"
            ;;
        "On-Premises")
            setup_on_prem_environment || return 1
            ;;
        *)
            print_error "Unknown environment: $environment"
            return 1
            ;;
    esac
    
    # Setup basic configuration
    setup_basic_config
    
    # Skip examples if in overlay mode and requested
    if [[ "${OVERLAY_MODE:-false}" == "true" && "${QUICKSTART_SKIP_EXAMPLES:-false}" == "true" ]]; then
        print_info "Skipping example creation (overlay mode)"
    else
        # Create basic examples for non-overlay mode
        create_basic_examples
    fi
    
    # Run post-quickstart hook (overlay extension point)
    run_hooks "post-quickstart" || return 1
    
    # Deploy AI agents dashboard
    deploy_ai_agents_dashboard || return 1
    
    # Deploy AI Agent Skills and MCP servers
    deploy_ai_agent_skills || return 1
    
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    
    if [[ "${OVERLAY_MODE:-false}" == "true" ]]; then
        echo "1. Use overlay-manager.sh to manage overlays"
        echo "2. Create custom overlays with overlay-cli.py"
        echo "3. Deploy overlays to your cluster"
        echo "4. Monitor overlay status and logs"
        echo "5. Access your AI agents dashboard at http://localhost:8080"
        echo "6. Configure Claude Desktop with AI Agent Skills"
        echo ""
        echo -e "${GREEN}🚀 Overlay system and AI agents are ready on $environment!${NC}"
    else
        echo "1. Use overlay-quickstart.sh to create and manage overlays"
        echo "2. Read docs/OVERLAY-QUICK-START.md for detailed guidance"
        echo "3. Check overlay/examples/ directory for sample configurations"
        echo "4. Access your AI agents dashboard at http://localhost:8080"
        echo "5. Configure Claude Desktop with AI Agent Skills (auto-configured)"
        echo ""
        echo -e "${GREEN}🚀 $environment environment and AI agents are ready!${NC}"
        echo -e "${YELLOW}✨ AI Agent Skills are fully operational and ready for use!${NC}"
    fi
}

# Help function
show_help() {
    echo "Agentic Reconciliation Engine - Common Quick Start Functions"
    echo ""
    echo "USAGE: source quickstart-common.sh"
    echo ""
    echo "DESCRIPTION:"
    echo "  Provides shared functions for all environment-specific quickstart scripts."
    echo "  This includes color output, hook support, dashboard deployment,"
    echo "  environment setup, and common quickstart logic."
    echo ""
    echo "ENVIRONMENT SETUP FUNCTIONS:"
    echo "  setup_kind_environment()              - Setup Kind Kubernetes cluster"
    echo "  setup_docker_desktop_environment()    - Setup Docker Desktop Kubernetes"
    echo "  setup_minikube_environment()          - Setup Minikube cluster"
    echo "  setup_localstack_aws_environment()    - Setup LocalStack AWS emulator"
    echo "  setup_azurite_azure_environment()     - Setup Azurite Azure emulator"
    echo "  setup_gcloud_emulator_environment()   - Setup Google Cloud emulators"
    echo "  setup_aws_environment()               - Setup AWS EKS environment"
    echo "  setup_azure_environment()             - Setup Azure AKS environment"
    echo "  setup_gcp_environment()               - Setup Google Cloud GKE environment"
    echo "  setup_on_prem_environment()           - Setup on-premises Kubernetes"
    echo ""
    echo "COMMON FUNCTIONS:"
    echo "  check_prerequisites()                 - Check required tools"
    echo "  setup_basic_config()                  - Setup basic directories"
    echo "  deploy_ai_agents_dashboard()          - Deploy AI dashboard"
    echo "  deploy_ai_agent_skills()              - Deploy AI skills"
    echo "  common_main()                         - Common main logic"
    echo ""
    echo "UTILITY FUNCTIONS:"
    echo "  print_header(), print_success(), print_error()"
    echo "  print_warning(), print_info()"
    echo "  run_hooks()                           - Execute overlay hooks"
}

# Export functions for use in other scripts
export -f print_header print_success print_error print_warning print_info
export -f run_hooks deploy_ai_agent_skills deploy_ai_agents_dashboard
export -f check_prerequisites setup_basic_config create_basic_examples
export -f setup_kind_environment setup_docker_desktop_environment setup_minikube_environment
export -f setup_localstack_aws_environment setup_azurite_azure_environment
export -f setup_gcloud_emulator_environment setup_aws_environment setup_azure_environment
export -f setup_gcp_environment setup_on_prem_environment common_main show_help

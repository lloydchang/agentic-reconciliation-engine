#!/bin/bash

# Zero-Touch Local AI Agents Development Setup
# Automatically installs prerequisites and deploys the full autonomous AI agents ecosystem

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
MINIKUBE_PROFILE="ai-agents-local"
MINIKUBE_MEMORY="4096"
MINIKUBE_CPUS="2"
NAMESPACE="ai-infrastructure"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

log_agent() {
    echo -e "${CYAN}[AGENT]${NC} $1"
}

# Check if running on macOS
check_os() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "This setup script is designed for macOS. For other platforms, please install prerequisites manually."
        exit 1
    fi
    log_success "macOS detected - proceeding with automated setup"
}

# Install Homebrew if not present
install_homebrew() {
    if ! command -v brew &> /dev/null; then
        log_step "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        eval "$(/opt/homebrew/bin/brew shellenv)"
        log_success "Homebrew installed"
    else
        log_success "Homebrew already installed"
    fi
}

# Install Docker Desktop
install_docker() {
    if ! command -v docker &> /dev/null; then
        log_step "Installing Docker Desktop..."
        brew install --cask docker
        log_warning "Docker Desktop installed. Please start Docker Desktop manually if not already running."
        log_info "Waiting 10 seconds for Docker to start..."
        sleep 10
        log_success "Docker installation complete"
    else
        log_success "Docker already installed"
    fi
}

# Install kubectl
install_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_step "Installing kubectl..."
        brew install kubectl
        log_success "kubectl installed"
    else
        log_success "kubectl already installed"
    fi
}

# Install Helm
install_helm() {
    if ! command -v helm &> /dev/null; then
        log_step "Installing Helm..."
        brew install helm
        log_success "Helm installed"
    else
        log_success "Helm already installed"
    fi
}

# Install Minikube
install_minikube() {
    if ! command -v minikube &> /dev/null; then
        log_step "Installing Minikube..."
        brew install minikube
        log_success "Minikube installed"
    else
        log_success "Minikube already installed"
    fi
}

# Start Minikube cluster
start_minikube() {
    log_step "Starting Minikube cluster..."

    # Delete existing cluster if it exists
    minikube delete -p $MINIKUBE_PROFILE 2>/dev/null || true

    # Start new cluster
    minikube start \
        -p $MINIKUBE_PROFILE \
        --memory=$MINIKUBE_MEMORY \
        --cpus=$MINIKUBE_CPUS \
        --driver=docker \
        --kubernetes-version=v1.27.0 \
        --addons=ingress \
        --addons=metrics-server

    # Enable required addons
    minikube addons enable ingress -p $MINIKUBE_PROFILE
    minikube addons enable metrics-server -p $MINIKUBE_PROFILE

    log_success "Minikube cluster started and configured"
}

# Build AI agent images
build_agent_images() {
    log_step "Building AI agent container images..."

    # Build Rust agent
    log_agent "Building Rust AI memory agent..."
    cd infrastructure/ai-inference/rust-agent
    docker build -t cloud-ai-agent-rust:latest .
    cd ../../../

    # Build Go agent
    log_agent "Building Go AI memory agent..."
    cd infrastructure/ai-inference/go-agent
    docker build -t cloud-ai-agent-go:latest .
    cd ../../../

    # Build Python agent
    log_agent "Building Python AI memory agent..."
    cd infrastructure/ai-inference/python-agent
    docker build -t cloud-ai-agent-python:latest .
    cd ../../../

    log_success "All AI agent images built"
}

# Deploy AI agents ecosystem
deploy_ecosystem() {
    log_step "Deploying autonomous AI agents ecosystem..."

    # Run the deployment script
    ./scripts/deploy-ai-agents-ecosystem.sh

    log_success "AI agents ecosystem deployed"
}

# Setup port forwarding for easy access
setup_port_forwarding() {
    log_step "Setting up port forwarding for local access..."

    # Kill any existing port forwards
    pkill -f "kubectl port-forward" || true

    # Port forward dashboard in background
    kubectl port-forward -n $NAMESPACE svc/agent-dashboard-service 8080:80 &
    echo $! > /tmp/dashboard-pf.pid

    # Port forward Temporal UI
    kubectl port-forward -n $NAMESPACE svc/temporal-frontend 8081:7233 &
    echo $! > /tmp/temporal-pf.pid

    log_success "Port forwarding established"
}

# Open dashboard in browser
open_dashboard() {
    log_step "Opening agent dashboard in web browser..."

    # Wait a moment for services to be ready
    sleep 5

    # Open dashboard
    if command -v open &> /dev/null; then
        open "http://localhost:8080"
    else
        log_info "Please open http://localhost:8080 in your web browser"
    fi

    log_success "Dashboard opened - AI agents are now running autonomously!"
}

# Display access information
show_access_info() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║           🚀 AUTONOMOUS AI AGENTS ECOSYSTEM READY           ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "🌐 Dashboard (Agent Activity):  http://localhost:8080"
    echo "🔄 Temporal Workflows:          http://localhost:8081"
    echo "📊 Cluster Status:              minikube dashboard -p $MINIKUBE_PROFILE"
    echo ""
    echo "🤖 AI Agents Status:"
    kubectl get pods -n $NAMESPACE --no-headers | while read line; do
        pod_name=$(echo $line | awk '{print $1}')
        status=$(echo $line | awk '{print $3}')
        if [[ $status == "Running" ]]; then
            echo "   ✅ $pod_name"
        else
            echo "   ⏳ $pod_name ($status)"
        fi
    done
    echo ""
    echo "📈 What the agents are doing:"
    echo "   • AI Memory Agents: Processing inference requests with Qwen2.5"
    echo "   • Skills Framework: Executing autonomous operational workflows"
    echo "   • Storage Management: Auto-resizing PVCs and pruning old data"
    echo "   • Monitoring: Collecting metrics and sending alerts"
    echo ""
    echo "🛑 To stop: ./scripts/stop-local-setup.sh"
    echo "🧹 To cleanup: minikube delete -p $MINIKUBE_PROFILE"
    echo ""
}

# Main setup function
main() {
    log_info "🚀 Starting Zero-Touch AI Agents Local Development Setup"
    echo ""

    check_os
    install_homebrew
    install_docker
    install_kubectl
    install_helm
    install_minikube
    start_minikube
    build_agent_images
    deploy_ecosystem
    setup_port_forwarding
    open_dashboard
    show_access_info

    log_success "🎉 Setup complete! Your autonomous AI agents are now running locally."
    log_info "The dashboard shows real-time agent activity - watch them make autonomous decisions!"
}

# Cleanup function
cleanup() {
    log_warning "Cleaning up port forwarding..."
    if [[ -f /tmp/dashboard-pf.pid ]]; then
        kill $(cat /tmp/dashboard-pf.pid) 2>/dev/null || true
        rm /tmp/dashboard-pf.pid
    fi
    if [[ -f /tmp/temporal-pf.pid ]]; then
        kill $(cat /tmp/temporal-pf.pid) 2>/dev/null || true
        rm /tmp/temporal-pf.pid
    fi
}

# Trap cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"

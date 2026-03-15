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

# Detect operating system and set package manager
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PACKAGE_MANAGER="brew"
        log_success "macOS detected - using Homebrew"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
        PACKAGE_MANAGER="choco"
        log_success "Windows detected - using Chocolatey"
    elif [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS="linux"
        if command -v apt &> /dev/null; then
            PACKAGE_MANAGER="apt"
            log_success "Linux (Debian/Ubuntu) detected - using apt"
        elif command -v yum &> /dev/null; then
            PACKAGE_MANAGER="yum"
            log_success "Linux (RedHat/CentOS) detected - using yum"
        elif command -v dnf &> /dev/null; then
            PACKAGE_MANAGER="dnf"
            log_success "Linux (Fedora) detected - using dnf"
        else
            log_error "Unsupported Linux distribution. Please install prerequisites manually."
            exit 1
        fi
    else
        log_error "Unsupported operating system. This script supports macOS, Windows, and Linux."
        exit 1
    fi
}

# Install package manager (Chocolatey for Windows, etc.)
install_package_manager() {
    case $OS in
        macos)
            install_homebrew
            ;;
        windows)
            install_chocolatey
            ;;
        linux)
            log_success "Using system package manager: $PACKAGE_MANAGER"
            ;;
    esac
}

# Install Chocolatey for Windows
install_chocolatey() {
    if ! command -v choco &> /dev/null; then
        log_step "Installing Chocolatey..."
        powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
        export PATH="$PATH:/c/ProgramData/chocolatey/bin"
        log_success "Chocolatey installed"
    else
        log_success "Chocolatey already installed"
    fi
}

# Install Docker Desktop
install_docker() {
    if ! command -v docker &> /dev/null; then
        log_step "Installing Docker Desktop..."
        case $OS in
            macos)
                brew install --cask docker
                ;;
            windows)
                choco install docker-desktop
                ;;
            linux)
                # Install Docker Engine for Linux
                case $PACKAGE_MANAGER in
                    apt)
                        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
                        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
                        sudo apt update
                        sudo apt install -y docker-ce docker-ce-cli containerd.io
                        sudo usermod -aG docker $USER
                        ;;
                    yum|dnf)
                        sudo $PACKAGE_MANAGER config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
                        sudo $PACKAGE_MANAGER install -y docker-ce docker-ce-cli containerd.io
                        sudo systemctl start docker
                        sudo systemctl enable docker
                        sudo usermod -aG docker $USER
                        ;;
                esac
                ;;
        esac
        log_warning "Docker installed. You may need to restart your terminal and start Docker Desktop (if applicable)."
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
        case $OS in
            macos)
                brew install helm
                ;;
            windows)
                choco install kubernetes-helm
                ;;
            linux)
                curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
                ;;
        esac
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

    # Open dashboard based on OS
    case $OS in
        macos)
            if command -v open &> /dev/null; then
                open "http://localhost:8080"
            fi
            ;;
        windows)
            if command -v start &> /dev/null; then
                start "http://localhost:8080"
            fi
            ;;
        linux)
            if command -v xdg-open &> /dev/null; then
                xdg-open "http://localhost:8080"
            elif command -v firefox &> /dev/null; then
                firefox "http://localhost:8080" &
            fi
            ;;
    esac

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

    detect_os
    install_package_manager
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

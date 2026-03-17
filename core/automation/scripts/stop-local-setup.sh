#!/bin/bash

# Stop Local AI Agents Setup
# Cleans up port forwarding and stops local services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Stop port forwarding
stop_port_forwarding() {
    log_info "Stopping port forwarding..."

    # Kill dashboard port forward
    if [[ -f /tmp/dashboard-pf.pid ]]; then
        if kill $(cat /tmp/dashboard-pf.pid) 2>/dev/null; then
            log_info "Stopped dashboard port forwarding"
        fi
        rm /tmp/dashboard-pf.pid
    fi

    # Kill temporal port forward
    if [[ -f /tmp/temporal-pf.pid ]]; then
        if kill $(cat /tmp/temporal-pf.pid) 2>/dev/null; then
            log_info "Stopped Temporal port forwarding"
        fi
        rm /tmp/temporal-pf.pid
    fi

    # Kill any remaining kubectl port forwards
    pkill -f "kubectl port-forward" || true

    log_success "Port forwarding stopped"
}

# Check if Minikube cluster exists
cluster_exists() {
    minikube status -p ai-agents-local >/dev/null 2>&1
}

# Stop Minikube cluster (optional)
stop_minikube() {
    if cluster_exists; then
        read -p "Stop Minikube cluster as well? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Stopping Minikube cluster..."
            minikube stop -p ai-agents-local
            log_success "Minikube cluster stopped"
        fi
    else
        log_info "Minikube cluster not running"
    fi
}

# Main cleanup function
main() {
    log_info "🛑 Stopping Local AI Agents Setup"

    stop_port_forwarding
    stop_minikube

    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🧹 CLEANUP COMPLETE                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Port forwarding stopped. Dashboard no longer accessible."
    echo ""
    echo "To restart: ./core/core/automation/ci-cd/scripts/setup-local-ai-agents.sh"
    echo "To delete cluster: minikube delete -p ai-agents-local"
    echo ""
}

# Run main function
main "$@"

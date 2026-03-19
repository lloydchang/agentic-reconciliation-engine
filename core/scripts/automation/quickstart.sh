#!/bin/bash
# GitOps Infrastructure Control Plane - Quick Start Script
# Repository setup and initial onboarding - supports overlay extensions

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

# Deploy consolidated K8sGPT
deploy_consolidated_k8sgpt() {
    print_header "Deploying Consolidated K8sGPT"
    
    # Check if the consolidated deployment script exists
    local k8sgpt_script="$SCRIPT_DIR/deploy-consolidated-k8sgpt.sh"
    
    if [[ ! -f "$k8sgpt_script" ]]; then
        print_warning "Consolidated K8sGPT deployment script not found at $k8sgpt_script"
        print_info "You can manually run: ./core/scripts/deploy-consolidated-k8sgpt.sh deploy"
        return 0
    fi
    
    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        print_warning "Kubernetes cluster not accessible - skipping K8sGPT deployment"
        print_info "To deploy K8sGPT later: QUICKSTART_DEPLOY_K8SGPT=true ./core/automation/scripts/quickstart.sh"
        return 0
    fi
    
    # Check if K8sGPT is already deployed
    if kubectl get deployment k8sgpt -n k8sgpt-system &> /dev/null; then
        print_info "K8sGPT already deployed - validating existing deployment"
        if bash "$k8sgpt_script" validate; then
            print_success "K8sGPT deployment validated successfully!"
        else
            print_warning "K8sGPT deployment validation failed - attempting redeployment"
            if bash "$k8sgpt_script" deploy; then
                print_success "K8sGPT redeployment successful!"
            else
                print_error "K8sGPT redeployment failed"
                return 1
            fi
        fi
        return 0
    fi
    
    print_info "Deploying consolidated K8sGPT (single instance per cluster)..."
    
    # Run the consolidated deployment
    if bash "$k8sgpt_script" deploy; then
        print_success "Consolidated K8sGPT deployed successfully!"
        echo ""
        echo -e "${GREEN}🎉 Your consolidated K8sGPT is now running!${NC}"
        echo -e "${YELLOW}🤖 Service endpoint: http://k8sgpt.k8sgpt-system.svc.cluster.local:8080${NC}"
        echo -e "${BLUE}📊 Metrics endpoint: http://k8sgpt.k8sgpt-system.svc.cluster.local:9090/metrics${NC}"
        echo ""
        echo "K8sGPT features:"
        echo "  ✅ Single instance per cluster (75% resource reduction)"
        echo "  ✅ Multi-backend support (agent-memory, LocalAI, OpenAI)"
        echo "  ✅ Cluster-wide RBAC for all GitOps components"
        echo "  ✅ Unified service endpoint for all integrations"
        echo "  ✅ Real-time metrics and health monitoring"
        echo ""
        echo "To access K8sGPT:"
        echo "1. Health check: curl http://k8sgpt.k8sgpt-system.svc.cluster.local:8080/healthz"
        echo "2. Analysis: curl -X POST http://k8sgpt.k8sgpt-system.svc.cluster.local:8080/analyze -H 'Content-Type: application/json' -d '{\"namespace\":\"default\",\"resources\":[\"deployments\"]}'"
        echo "3. Metrics: curl http://k8sgpt.k8sgpt-system.svc.cluster.local:9090/metrics"
    else
        print_error "Failed to deploy consolidated K8sGPT"
        print_info "Check the logs above for errors and try running the script manually"
        print_info "Manual deployment: ./core/scripts/deploy-consolidated-k8sgpt.sh deploy"
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
        echo "  🧹 Clean up: ./core/scripts/automation/quickstart.sh --cleanup"
        echo "  🔄 Restart: ./core/scripts/automation/quickstart.sh --start-pf"
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

# Start all required port-forwards in background
start_all_port_forwards() {
    print_info "Starting all required port-forwards in background..."
    
    # Define port-forward configurations
    declare -A PORT_FORWARDS=(
        ["agent-dashboard"]="svc/agent-dashboard-service 8080:80"
        ["comprehensive-dashboard-frontend"]="svc/comprehensive-dashboard-frontend 8083:80"
        ["comprehensive-dashboard-api"]="svc/comprehensive-dashboard-api 5001:5000"
    )
    
    # Check if port-forwards are already running and start them if not
    for service_name in "${!PORT_FORWARDS[@]}"; do
        local port_config="${PORT_FORWARDS[$service_name]}"
        local local_port=$(echo "$port_config" | cut -d' ' -f2 | cut -d':' -f1)
        
        # Check if this specific port-forward is already running
        if pgrep -f "port-forward.*$service_name.*$local_port" > /dev/null; then
            print_info "Port-forward for $service_name (port $local_port) already running"
        else
            # Start port-forward in background with logging
            local log_file="/tmp/${service_name}-port-forward.log"
            nohup kubectl port-forward -n ai-infrastructure $port_config > "$log_file" 2>&1 &
            local pid=$!
            
            # Give it a moment to start
            sleep 2
            
            # Verify it started successfully
            if pgrep -f "port-forward.*$service_name.*$local_port" > /dev/null; then
                print_success "Background port-forward started for $service_name (port $local_port)"
                echo -e "${GREEN}🌐 Access: http://localhost:$local_port${NC}"
                echo -e "${YELLOW}📝 Logs: tail -f $log_file${NC}"
            else
                print_warning "Port-forward failed to start for $service_name (port $local_port)"
                echo "Check logs: cat $log_file"
            fi
        fi
        echo ""
    done
    
    # Show summary of all running port-forwards
    print_info "Current port-forward status:"
    for service_name in "${!PORT_FORWARDS[@]}"; do
        local port_config="${PORT_FORWARDS[$service_name]}"
        local local_port=$(echo "$port_config" | cut -d' ' -f2 | cut -d':' -f1)
        
        if pgrep -f "port-forward.*$service_name.*$local_port" > /dev/null; then
            echo -e "  ✅ $service_name: http://localhost:$local_port"
        else
            echo -e "  ❌ $service_name: Not running"
        fi
    done
}

# Main quick start function
main() {
    print_header "GitOps Infrastructure Quick Start"
    
    echo -e "${BLUE}Welcome to GitOps Infrastructure Control Plane!${NC}"
    echo ""
    
    # Check if we're in overlay mode
    if [[ "${OVERLAY_MODE:-false}" == "true" ]]; then
        echo -e "${YELLOW}Running in overlay mode${NC}"
    else
        echo -e "${YELLOW}This script sets up your development environment.${NC}"
    fi
    echo ""
    
    # Check if we're in the right directory
    if [[ ! -f "$REPO_ROOT/README.md" ]]; then
        print_error "Not in repository root. Please run from repository root."
        exit 1
    fi
    
    # Run pre-quickstart hook (overlay extension point)
    run_hooks "pre-quickstart" || return 1
    
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
    
    # Setup basic configuration
    print_info "Setting up development environment..."
    
    # Create basic directories if they don't exist
    mkdir -p logs/
    mkdir -p tmp/
    
    # Make scripts executable
    find "$SCRIPT_DIR" -name "*.sh" -exec chmod +x {} \;
    find "$SCRIPT_DIR" -name "*.py" -exec chmod +x {} \;
    
    print_success "Development environment ready"
    
    # Skip examples if in overlay mode and requested
    if [[ "${OVERLAY_MODE:-false}" == "true" && "${QUICKSTART_SKIP_EXAMPLES:-false}" == "true" ]]; then
        print_info "Skipping example creation (overlay mode)"
    else
        # Create basic examples for non-overlay mode
        echo -e "${BLUE}Creating basic examples...${NC}"
        mkdir -p overlay/examples/basic/
        cat > overlay/examples/basic/README.md << 'EOF'
# Basic Examples

This directory contains basic examples for getting started with the GitOps Infrastructure Control Plane.

## Quick Start Examples

1. **Basic Setup**: Run `./quickstart.sh` to get started
2. **Overlay Mode**: Run `./overlay-quickstart.sh` for overlay-based setup
3. **Advanced**: See `overlay/examples/` directory for comprehensive examples

## Next Steps

1. Read the documentation in `docs/`
2. Check the examples in `overlay/examples/`
3. Use the scripts in `core/automation/scripts/` for automation
EOF
        print_success "Basic examples created"
    fi
    
    # Run post-quickstart hook (overlay extension point)
    run_hooks "post-quickstart" || return 1
    
    # Deploy AI agents dashboard
    deploy_ai_agents_dashboard || return 1
    
    # Deploy consolidated K8sGPT
    deploy_consolidated_k8sgpt || return 1
    
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
        echo "7. Use consolidated K8sGPT: http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
        echo ""
        echo -e "${GREEN}🚀 Overlay system and AI agents are ready!${NC}"
        echo -e "${YELLOW}🤖 Consolidated K8sGPT is deployed and integrated!${NC}"
    else
        echo "1. Use overlay-quickstart.sh to create and manage overlays"
        echo "2. Read docs/OVERLAY-QUICK-START.md for detailed guidance"
        echo "3. Check overlay/examples/ directory for sample configurations"
        echo "4. Access your AI agents dashboard at http://localhost:8080"
        echo "5. Configure Claude Desktop with AI Agent Skills (auto-configured)"
        echo "6. Use consolidated K8sGPT: http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
        echo ""
        echo -e "${GREEN}🚀 Overlay system and AI agents are ready!${NC}"
        echo -e "${YELLOW}✨ AI Agent Skills are fully operational and ready for use!${NC}"
        echo -e "${BLUE}🤖 Consolidated K8sGPT is deployed and integrated!${NC}"
    fi
}

# Comprehensive port-forward manager
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

# Enhanced cleanup function
cleanup_port_forwards() {
    print_info "Cleaning up all background port-forwards..."
    
    # Define all services for cleanup
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
    echo "GitOps Infrastructure Control Plane - Quick Start"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help     Show this help message"
    echo "  --cleanup      Clean up all background port-forwards"
    echo "  --start-pf     Start all port-forwards (if not already running)"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up development environment for GitOps Infrastructure Control Plane."
    echo "  This includes tool verification, directory setup, basic configuration,"
    echo "  and deployment of AI agents dashboard with running agents."
    echo ""
    echo "  This script supports overlay extensions through hooks:"
    echo "  - hooks/pre-quickstart.sh: Runs before main quickstart logic"
    echo "  - hooks/post-quickstart.sh: Runs after main quickstart logic"
    echo ""
    echo "  Overlay mode is activated when OVERLAY_MODE=true is set."
    echo "  In overlay mode, the script adapts behavior for overlay workflows."
    echo ""
    echo "  For overlay-specific operations, use: overlay-quickstart.sh"
    echo "  For overlay lifecycle management, use: overlay-manager.sh"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                    # Standard repository setup with AI agents dashboard"
    echo "  OVERLAY_MODE=true $0   # Setup with overlay extensions and AI agents dashboard"
    echo ""
    echo "  # With overlay-quickstart.sh (recommended for overlay workflows)"
    echo "  overlay-quickstart.sh --all"
    echo ""
    echo "HOOKS:"
    echo "  To extend quickstart.sh without modifying it:"
    echo "  1. Create hooks/ directory"
    echo "  2. Add hooks/pre-quickstart.sh (runs before main logic)"
    echo "  3. Add hooks/post-quickstart.sh (runs after main logic)"
    echo "  4. Set OVERLAY_MODE=true when running"
    echo ""
    echo "  The hooks will be automatically sourced and executed."
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    --cleanup)
        cleanup_port_forwards
        exit 0
        ;;
    --start-pf)
        start_all_port_forwards
        exit 0
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

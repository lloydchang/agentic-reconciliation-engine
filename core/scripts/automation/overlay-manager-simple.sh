#!/bin/bash
# Agentic Reconciliation Engine - Simple Overlay Manager
# Complete overlay lifecycle: create, deploy, remove, uninstall

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script information
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
OVERLAY_DIR="${OVERLAY_DIR:-overlays}"

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# List overlays
list_overlays() {
    print_header "Available Overlays"
    
    if [[ ! -d "$OVERLAY_DIR" ]]; then
        print_error "Overlay directory not found: $OVERLAY_DIR"
        return 1
    fi
    
    echo -e "${BLUE}Available overlays:${NC}"
    
    local overlay_count=0
    for overlay_dir in "$OVERLAY_DIR"/*; do
        if [[ -d "$overlay_dir" && -f "$overlay_dir/kustomization.yaml" ]]; then
            ((overlay_count++))
            local overlay_name=$(basename "$overlay_dir")
            local overlay_type="unknown"
            local status="unknown"
            
            # Determine overlay type
            if [[ "$overlay_dir" == *"core/ai/skills/"* ]]; then
                overlay_type="skill"
            elif [[ "$overlay_dir" == *"core/ai/skills/dashboard"* ]]; then
                overlay_type="dashboard"
            elif [[ "$overlay_dir" == *"core/operators/"* ]]; then
                overlay_type="infrastructure"
            elif [[ "$overlay_dir" == *"composed/"* ]]; then
                overlay_type="composed"
            fi
            
            # Check deployment status
            if kubectl get pods -n flux-system -l overlay="$overlay_name" --no-headers 2>/dev/null | grep -q "Running"; then
                status="🟢 Running"
            elif kubectl get pods -n flux-system -l overlay="$overlay_name" --no-headers 2>/dev/null | grep -q "Succeeded\|Completed"; then
                status="🟡 Deployed"
            else
                status="⚪ Stopped"
            fi
            
            printf "  ${BLUE}%3d. %-20s${NC} ${YELLOW}%-12s${NC} ${GREEN}%-10s${NC} %s\n" \
                "$overlay_count" "$overlay_name" "$overlay_type" "$status"
        fi
    done
    
    if [[ $overlay_count -eq 0 ]]; then
        echo -e "${YELLOW}No overlays found in $OVERLAY_DIR${NC}"
        echo -e "${BLUE}Use 'overlay-manager-simple.sh --create' to create your first overlay.${NC}"
    else
        echo -e "${BLUE}Total: $overlay_count overlays found${NC}"
    fi
}

# Deploy overlay
deploy_overlay() {
    local overlay_name="$1"
    
    print_header "Deploying Overlay: $overlay_name"
    
    # Find overlay directory
    local overlay_dir="$OVERLAY_DIR/$overlay_name"
    if [[ ! -d "$overlay_dir" ]]; then
        print_error "Overlay not found: $overlay_name"
        return 1
    fi
    
    # Check cluster access
    if ! kubectl cluster-info &> /dev/null; then
        print_warning "Kubernetes cluster not accessible - cannot deploy"
        return 1
    fi
    
    # Build and deploy
    print_info "Building and deploying overlay..."
    if kustomize build "$overlay_dir" | kubectl apply -f -; then
        print_success "Overlay '$overlay_name' deployed successfully"
        
        # Get service URL
        local service_url="http://localhost:8080"
        if command -v minikube &> /dev/null; then
            service_url=$(minikube service "$overlay_name" --url -n flux-system 2>/dev/null)
        fi
        
        print_success "Service available at: $service_url"
        print_info "Use 'overlay-manager-simple.sh --status $overlay_name' to check status"
        
    else
        print_error "Failed to deploy overlay '$overlay_name'"
        return 1
    fi
}

# Remove overlay
remove_overlay() {
    local overlay_name="$1"
    local force="$2"
    
    print_header "Removing Overlay: $overlay_name"
    
    # Find overlay directory
    local overlay_dir="$OVERLAY_DIR/$overlay_name"
    if [[ ! -d "$overlay_dir" ]]; then
        print_error "Overlay not found: $overlay_name"
        return 1
    fi
    
    # Check if overlay is deployed
    local deployed=false
    if kubectl get pods -n flux-system -l overlay="$overlay_name" --no-headers 2>/dev/null | grep -q "Running"; then
        deployed=true
    fi
    
    # Remove deployment
    if [[ "$deployed" == "true" ]] || [[ "$force" == "true" ]]; then
        print_info "Removing deployment..."
        if kustomize build "$overlay_dir" | kubectl delete -f -; then
            print_success "Overlay '$overlay_name' deployment removed"
        else
            print_error "Failed to remove overlay '$overlay_name' deployment"
            return 1
        fi
    else
        print_warning "Overlay '$overlay_name' is not deployed (use --force to remove anyway)"
    fi
    
    # Remove overlay directory
    if [[ "$force" == "true" ]] || [[ "$deployed" != "true" ]]; then
        print_info "Removing overlay directory..."
        rm -rf "$overlay_dir"
        print_success "Overlay '$overlay_name' directory removed"
    else
        print_warning "Overlay directory preserved (overlay is deployed)"
    fi
}

# Uninstall overlay
uninstall_overlay() {
    local overlay_name="$1"
    local force="$2"
    
    print_header "Uninstalling Overlay: $overlay_name"
    
    # Complete removal - same as remove with force
    remove_overlay "$overlay_name" "true"
    
    print_success "Overlay '$overlay_name' uninstalled completely"
}

# Show overlay status
show_status() {
    local overlay_name="$1"
    
    print_header "Overlay Status: $overlay_name"
    
    # Find overlay directory
    local overlay_dir="$OVERLAY_DIR/$overlay_name"
    if [[ ! -d "$overlay_dir" ]]; then
        print_error "Overlay not found: $overlay_name"
        return 1
    fi
    
    # Check deployment status
    local pod_status="⚪ Unknown"
    if kubectl get pods -n flux-system -l overlay="$overlay_name" --no-headers 2>/dev/null | grep -q "Running"; then
        pod_status="🟢 Running"
    elif kubectl get pods -n flux-system -l overlay="$overlay_name" --no-headers 2>/dev/null | grep -q "Succeeded\|Completed"; then
        pod_status="🟡 Deployed"
    elif kubectl get pods -n flux-system -l overlay="$overlay_name" --no-headers 2>/dev/null | grep -q "Terminated\|Error\|CrashLoopBackOff\|ImagePullBackOff\|OOMKilled"; then
        pod_status="⚪ Stopped"
    fi
    
    local service_info=$(kubectl get svc -n flux-system -l overlay="$overlay_name" --no-headers 2>/dev/null)
    
    echo -e "${BLUE}Overlay Information:${NC}"
    echo -e "  Name: $overlay_name"
    echo -e "  Status: $pod_status"
    
    if [[ -n "$service_info" ]]; then
        echo -e "  Service:"
        echo "$service_info" | sed 's/^/    /  /'
    fi
    
    # Show resources
    echo -e "${BLUE}Resources:${NC}"
    kubectl get all -n flux-system -l overlay="$overlay_name" --no-headers 2>/dev/null
}

# Show overlay logs
show_logs() {
    local overlay_name="$1"
    local lines="${2:-50}"
    
    print_header "Overlay Logs: $overlay_name"
    
    # Find overlay directory
    local overlay_dir="$OVERLAY_DIR/$overlay_name"
    if [[ ! -d "$overlay_dir" ]]; then
        print_error "Overlay not found: $overlay_name"
        return 1
    fi
    
    # Get pod name
    local pod_name=$(kubectl get pods -n flux-system -l overlay="$overlay_name" --no-headers 2>/dev/null | awk '/Running/{print $1; exit} {print ""}' | head -1)
    
    if [[ -z "$pod_name" ]]; then
        print_error "No running pod found for overlay: $overlay_name"
        return 1
    fi
    
    # Show logs
    kubectl logs -n flux-system "$pod_name" --tail="$lines"
}

# Help function
show_help() {
    echo "Agentic Reconciliation Engine - Simple Overlay Manager"
    echo ""
    echo "Complete overlay lifecycle management for Agentic Reconciliation Engine."
    echo ""
    echo "USAGE: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "COMMANDS:"
    echo "  list                                  List all available overlays"
    echo "  deploy <name>                        Deploy an overlay"
    echo "  remove <name> [--force]              Remove an overlay (undeploy if running)"
    echo "  uninstall <name> [--force]           Completely remove an overlay"
    echo "  status <name>                        Show overlay status and information"
    echo "  logs <name> [lines]                   Show overlay logs"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help        Show this help message"
    echo "  -v, --verbose      Enable verbose output"
    echo ""
    echo "EXAMPLES:"
    echo "  # List all overlays"
    echo "  overlay-manager-simple.sh list"
    echo ""
    echo "  # Deploy an overlay"
    echo "  overlay-manager-simple.sh deploy debug"
    echo ""
    echo "  # Remove an overlay"
    echo "  overlay-manager-simple.sh remove my-overlay --force"
    echo ""
    echo "  # Show overlay status"
    echo "  overlay-manager-simple.sh status my-overlay"
    echo ""
    echo "  # Show overlay logs"
    echo "  overlay-manager-simple.sh logs my-overlay"
    echo ""
    echo "ENVIRONMENT VARIABLES:"
    echo "  OVERLAY_DIR            Overlay directory (default: overlays)"
}

# Main function
main() {
    local command=""
    local overlay_name=""
    local force="false"
    local lines=""
    local verbose=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            list)
                shift
                ;;
            deploy)
                shift
                overlay_name="$1"
                shift
                ;;
            remove)
                overlay_name="$2"
                if [[ "$3" == "--force" ]]; then
                    force="true"
                    shift
                fi
                shift 2
                ;;
            uninstall)
                overlay_name="$2"
                if [[ "$3" == "--force" ]]; then
                    force="true"
                    shift
                fi
                shift 2
                ;;
            status)
                shift
                overlay_name="$1"
                shift
                ;;
            logs)
                shift
                overlay_name="$1"
                lines="$2"
                shift 2
                ;;
            *)
                print_error "Unknown command: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Execute command
    echo "DEBUG: All args: $@"
    echo "DEBUG: command='$command', overlay_name='$overlay_name', force='$force'"
    case "$command" in
        list)
            list_overlays
            ;;
        deploy)
            deploy_overlay "$overlay_name"
            ;;
        remove)
            remove_overlay "$overlay_name" "$force"
            ;;
        uninstall)
            uninstall_overlay "$overlay_name" "$force"
            ;;
        status)
            show_status "$overlay_name"
            ;;
        logs)
            show_logs "$overlay_name" "$lines"
            ;;
        "")
            print_error "Command is required"
            show_help
            exit 1
            ;;
    esac
}

# Check if script is being sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
else
    echo "This script should be executed directly, not sourced."
    exit 1
fi

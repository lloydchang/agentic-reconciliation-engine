#!/bin/bash
# GitOps Infrastructure Control Plane - Overlay Manager
# Complete overlay lifecycle management: create, test, deploy, remove, uninstall

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

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
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
    
    # Check cluster access
    if kubectl cluster-info &> /dev/null; then
        print_success "Kubernetes cluster accessible"
    else
        print_warning "Kubernetes cluster not accessible (some operations will be limited)"
    fi
    
    print_success "All prerequisites satisfied"
}

# List overlays
list_overlays() {
    print_header "Listing Available Overlays"
    
    if [[ ! -d "$OVERLAY_DIR" ]]; then
        print_error "Overlay directory not found: $OVERLAY_DIR"
        return 1
    fi
    
    echo -e "${BLUE}Available overlays:${NC}"
    
    # Find all kustomization.yaml files
    local overlay_count=0
    while IFS= read -r -d '' overlay; do
        if [[ -f "$overlay/kustomization.yaml" ]]; then
            ((overlay_count++))
            local overlay_name=$(basename "$(dirname "$overlay")")
            local overlay_type="unknown"
            local status="unknown"
            
            # Determine overlay type
            if [[ "$overlay_name" == *"core/ai/skills/"* ]]; then
                overlay_type="skill"
            elif [[ "$overlay_name" == *"core/ai/skills/dashboard"* ]]; then
                overlay_type="dashboard"
            elif [[ "$overlay_name" == *"core/operators/"* ]]; then
                overlay_type="infrastructure"
            elif [[ "$overlay_name" == *"composed/"* ]]; then
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
    done <<< "$(find "$OVERLAY_DIR" -name "kustomization.yaml" -type f)"
    
    if [[ $overlay_count -eq 0 ]]; then
        echo -e "${YELLOW}No overlays found in $OVERLAY_DIR${NC}"
        echo -e "${BLUE}Use 'overlay-manager.sh --create' to create your first overlay.${NC}"
    else
        echo -e "${BLUE}Total: $overlay_count overlays found${NC}"
    fi
}

# Create overlay
create_overlay() {
    local overlay_name="$1"
    local overlay_type="$2"
    local base_path="$3"
    
    print_header "Creating Overlay: $overlay_name"
    
    # Validate inputs
    if [[ -z "$overlay_name" ]]; then
        print_error "Overlay name is required"
        return 1
    fi
    
    if [[ -z "$overlay_type" ]]; then
        print_error "Overlay type is required"
        return 1
    fi
    
    # Determine target directory
    local target_dir="$OVERLAY_DIR"
    case "$overlay_type" in
        "skill")
            target_dir="$OVERLAY_DIR/core/ai/skills/$base_path"
            ;;
        "dashboard")
            target_dir="$OVERLAY_DIR/core/ai/runtime/dashboard/$base_path"
            ;;
        "infrastructure")
            target_dir="$OVERLAY_DIR/core/operators/$base_path"
            ;;
        "composed")
            target_dir="$OVERLAY_DIR/composed/$overlay_name"
            ;;
        *)
            print_error "Unknown overlay type: $overlay_type"
            return 1
            ;;
    esac
    
    # Check if overlay already exists
    if [[ -d "$target_dir" ]]; then
        print_error "Overlay already exists: $target_dir"
        return 1
    fi
    
    # Create overlay directory structure
    mkdir -p "$target_dir"
    
    # Create kustomization.yaml
    cat > "$target_dir/kustomization.yaml" << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: $overlay_name
  namespace: flux-system
  labels:
    overlay: "$overlay_name"
    overlay-type: "$overlay_type"
    managed-by: "kustomize"
resources:
  - $(get_base_resources "$overlay_type" "$base_path")
commonLabels:
  overlay: "$overlay_name"
  overlay-type: "$overlay_type"
EOF
    
    # Create overlay metadata
    cat > "$target_dir/overlay-metadata.yaml" << EOF
name: "$overlay_name"
version: "1.0.0"
description: "Auto-generated $overlay_type overlay"
category: "$overlay_type"
license: "Apache-2.0"
risk_level: "low"
autonomy: "fully_auto"
maintainer: "overlay-manager"
tags:
  - auto-generated
  - "$overlay_type"
compatibility: "1.0.0+"
base_path: "$base_path"
inputs:
  - name: overlay_name
    description: "Overlay name"
    required: true
    type: string
  - name: overlay_type
    description: "Overlay type"
    required: true
    type: string
    - name: base_path
    description: "Base path for overlay"
    required: true
    type: string
outputs:
  - name: kustomization_path
    description: "Path to generated kustomization.yaml"
    type: string
    value: "$target_dir/kustomization.yaml"
examples:
  - name: "Create and deploy"
    description: "Create the overlay and deploy to cluster"
    commands:
      - "./overlay-manager.sh --create $overlay_name $overlay_type $base_path"
      - "./overlay-manager.sh --deploy $overlay_name"
EOF
    
    # Create README
    cat > "$target_dir/README.md" << EOF
# $overlay_name Overlay

$overlay_type overlay for GitOps Infrastructure Control Plane.

## Overview

This overlay was created using the overlay manager.

## Quick Start

\`\`\`bash
# Create the overlay
./overlay-manager.sh --create $overlay_name $overlay_type $base_path

# Deploy the overlay
./overlay-manager.sh --deploy $overlay_name

\`\`\`

## Structure

\`\`\`
$target_dir/
├── kustomization.yaml
├── overlay-metadata.yaml
└── README.md
\`\`\`

## Generated Files

- **kustomization.yaml**: Kustomize configuration
- **overlay-metadata.yaml**: Overlay metadata and inputs/outputs
- **README.md**: Documentation and usage examples
EOF
    
    print_success "Overlay '$overlay_name' created successfully in $target_dir"
    print_info "Use './overlay-manager.sh --deploy $overlay_name' to deploy"
}

# Get base resources function
get_base_resources() {
    local overlay_type="$1"
    local base_path="$2"
    
    case "$overlay_type" in
        "skill")
            echo "../../core/ai/skills/$base_path"
            ;;
        "dashboard")
            echo "../../core/ai/skills/dashboard/$base_path"
            ;;
        "infrastructure")
            echo "../../core/operators/$base_path"
            ;;
        "composed")
            echo ""
            ;;
        *)
            echo ""
            ;;
    esac
}

# Test overlay
test_overlay() {
    local overlay_name="$1"
    
    print_header "Testing Overlay: $overlay_name"
    
    # Find overlay directory
    local overlay_dir="$OVERLAY_DIR/$overlay_name"
    if [[ ! -d "$overlay_dir" ]]; then
        print_error "Overlay not found: $overlay_name"
        return 1
    fi
    
    # Validate kustomization
    if [[ ! -f "$overlay_dir/kustomization.yaml" ]]; then
        print_error "kustomization.yaml not found in $overlay_dir"
        return 1
    fi
    
    # Build overlay
    print_info "Building overlay..."
    if kustomize build "$overlay_dir" > /tmp/test-build.yaml; then
        print_success "Overlay builds successfully"
        rm -f /tmp/test-build.yaml
    else
        print_error "Failed to build overlay"
        return 1
    fi
    
    # Validate deployment (if cluster accessible)
    if kubectl cluster-info &> /dev/null; then
        print_info "Testing deployment..."
        if kubectl build "$overlay_dir" | kubectl apply --dry-run -f -; then
            print_success "Overlay deployment validation passed"
        else
            print_warning "Overlay deployment validation failed (check cluster access)"
        fi
    else
        print_warning "Skipping deployment tests (cluster not accessible)"
    fi
    
    print_success "Overlay '$overlay_name' test completed"
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
        
        # Get service URL if possible
        local service_url=""
        if command -v minikube &> /dev/null; then
            service_url=$(minikube service "$overlay_name" --url -n flux-system 2>/dev/null)
        else
            # Try port-forward for local clusters
            service_url="http://localhost:8080"
        fi
        
        print_success "Service available at: $service_url"
        print_info "Use 'kubectl get pods -n flux-system -l overlay=$overlay_name' to check status"
        
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
    local pod_status=$(kubectl get pods -n flux-system -l overlay="$overlay_name" --no-headers 2>/dev/null | awk '/Running/{print "🟢 Running"; /Succeeded|Completed/{print "🟡 Deployed"}; /Terminated|Error|CrashLoopBackOff|ImagePullBackOff|OOMKilled/{print "⚪ Stopped"}; {print "⚪ Unknown"}}')
    local service_info=$(kubectl get svc -n flux-system -l overlay="$overlay_name" --no-headers 2>/dev/null)
    
    echo -e "${BLUE}Overlay Information:${NC}"
    echo -e "  Name: $overlay_name"
    echo -e "  Type: $(cat "$overlay_dir/overlay-metadata.yaml" | grep 'category:' | cut -d':' -f2 | tr -d ' ')"
    echo -e "  Version: $(cat "$overlay_dir/overlay-metadata.yaml" | grep 'version:' | cut -d':' -f2 | tr -d ' ')"
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
    local lines="$2"
    
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
    local lines="${lines:-50}"
    kubectl logs -n flux-system "$pod_name" --tail="$lines"
}

# Update overlay
update_overlay() {
    local overlay_name="$1"
    local new_version="$2"
    
    print_header "Updating Overlay: $overlay_name"
    
    # Find overlay directory
    local overlay_dir="$OVERLAY_DIR/$overlay_name"
    if [[ ! -d "$overlay_dir" ]]; then
        print_error "Overlay not found: $overlay_name"
        return 1
    fi
    
    # Update metadata
    if [[ -n "$new_version" ]]; then
        sed -i ''s/version: ".*"/version: "$new_version"/' "$overlay_dir/overlay-metadata.yaml"
        print_success "Overlay '$overlay_name' updated to version $new_version"
    else
        print_error "Version is required for update"
        return 1
    fi
}

# Backup overlay
backup_overlay() {
    local overlay_name="$1"
    local backup_dir="$2"
    
    print_header "Backing Up Overlay: $overlay_name"
    
    # Find overlay directory
    local overlay_dir="$OVERLAY_DIR/$overlay_name"
    if [[ ! -d "$overlay_dir" ]]; then
        print_error "Overlay not found: $overlay_name"
        return 1
    fi
    
    # Create backup
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_name="${overlay_name}_backup_${timestamp}"
    local backup_path="${backup_dir:-$OVERLAY_DIR-backups}/$backup_name"
    
    mkdir -p "$backup_path"
    cp -r "$overlay_dir" "$backup_path"
    
    print_success "Overlay '$overlay_name' backed up to: $backup_path"
}

# Restore overlay
restore_overlay() {
    local backup_name="$1"
    local overlay_name="$2"
    local backup_dir="$3"
    
    print_header "Restoring Overlay: $overlay_name"
    
    # Find backup
    local backup_path="${backup_dir:-$OVERLAY_DIR-backups}/$backup_name"
    if [[ ! -d "$backup_path" ]]; then
        print_error "Backup not found: $backup_name"
        return 1
    fi
    
    # Find overlay directory
    local overlay_dir="$OVERLAY_DIR/$overlay_name"
    if [[ -d "$overlay_dir" ]]; then
        print_warning "Overlay directory exists - will be overwritten"
        rm -rf "$overlay_dir"
    fi
    
    # Restore backup
    cp -r "$backup_path" "$overlay_dir"
    
    print_success "Overlay '$overlay_name' restored from backup"
}

# Help function
show_help() {
    echo "GitOps Infrastructure Control Plane - Overlay Manager"
    echo ""
    echo "Complete overlay lifecycle management for GitOps Infrastructure Control Plane."
    echo ""
    echo "USAGE: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "COMMANDS:"
    echo "  create <name> <type> <base_path>     Create a new overlay"
    echo "  list                                  List all available overlays"
    echo "  test <name>                          Test an overlay"
    echo "  deploy <name>                        Deploy an overlay"
    echo "  remove <name> [--force]              Remove an overlay (undeploy if running)"
    echo "  uninstall <name> [--force]           Completely remove an overlay"
    echo "  status <name>                        Show overlay status and information"
    echo "  logs <name> [lines]                   Show overlay logs"
    echo "  update <name> <version>             Update overlay version"
    echo "  backup <name> [backup_dir]           Backup overlay"
    echo "  restore <backup_name> <name> [backup_dir] Restore overlay from backup"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help        Show this help message"
    echo "  -v, --verbose      Enable verbose output"
    echo ""
    echo "OVERLAY TYPES:"
    echo "  skill        - Skill-based overlays (agents)"
    echo "  dashboard     - Dashboard overlays (UI/themes)"
    echo "  infrastructure - Infrastructure overlays (control-plane)"
    echo "  composed      - Composed overlays (multiple overlays combined)"
    echo ""
    echo "EXAMPLES:"
    echo "  # Create a skill overlay"
    echo "  overlay-manager.sh create my-skill skill debug"
    echo ""
    echo "  # Deploy a dashboard overlay"
    echo "  overlay-manager.sh deploy my-theme dashboard"
    echo ""
    echo "  # Remove an overlay"
    echo "  overlay-manager.sh remove my-overlay --force"
    echo ""
    echo "  # Show overlay status"
    echo "  overlay-manager.sh status my-overlay"
    echo ""
    echo "  # Create backup"
    echo "  overlay-manager.sh backup my-overlay"
    echo ""
    echo "  # Update overlay version"
    echo "  overlay-manager.sh update my-overlay 2.0.0"
    echo ""
    echo "ENVIRONMENT VARIABLES:"
    echo "  OVERLAY_DIR            Overlay directory (default: overlays)"
    echo "  BACKUP_DIR            Backup directory (default: overlays-backups)"
}

# Main function
main() {
    local command="${1:-}"
    local overlay_name="${2:-}"
    local overlay_type="${3:-}"
    local base_path="${4:-}"
    local force="${5:-false}"
    local version="${6:-}"
    local backup_name="${7:-}"
    local backup_dir="${8:-}"
    local lines="${9:-}"
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
            create)
                shift
                overlay_name="$1"
                overlay_type="$2"
                base_path="$3"
                shift 3
                ;;
            list)
                shift
                ;;
            test)
                shift
                overlay_name="$1"
                shift
                ;;
            deploy)
                shift
                overlay_name="$1"
                shift
                ;;
            remove)
                shift
                overlay_name="$1"
                force="$2"
                shift 2
                ;;
            uninstall)
                shift
                overlay_name="$1"
                force="$2"
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
            update)
                shift
                overlay_name="$1"
                version="$2"
                shift 2
                ;;
            backup)
                shift
                overlay_name="$1"
                backup_dir="$2"
                shift 2
                ;;
            restore)
                shift
                backup_name="$1"
                overlay_name="$2"
                backup_dir="$3"
                shift 3
                ;;
            *)
                print_error "Unknown command: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Execute command
    case $command in
        create)
            create_overlay "$overlay_name" "$overlay_type" "$base_path"
            ;;
        list)
            list_overlays
            ;;
        test)
            test_overlay "$overlay_name"
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
        update)
            update_overlay "$overlay_name" "$version"
            ;;
        backup)
            backup_overlay "$overlay_name" "$backup_dir"
            ;;
        restore)
            restore_overlay "$backup_name" "$overlay_name" "$backup_dir"
            ;;
        "")
            print_error "Command is required"
            show_help
            exit 1
            ;;
    esac
}

# Check if script is being sourced
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    main "$@"
else
    echo "This script should be executed directly, not sourced."
    exit 1
fi

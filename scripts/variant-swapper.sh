#!/bin/bash
# Variant Swapping Tool for GitOps Infra Control Plane
# Allows switching between different deployment variants

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VARIANTS_DIR="$REPO_ROOT/variants"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    local color=$1
    shift
    echo -e "${color}$*${NC}"
}

# Function to show usage
show_usage() {
    cat << EOF
GitOps Infra Control Plane - Variant Swapper

Usage: $0 [OPTIONS] <variant-type> <variant-name>

Variant Types:
  opensource    - Open source deployment variant
  enterprise    - Enterprise deployment variant
  languages     - Language ecosystem variants

Language Variants:
  python        - Python/ML ecosystem (uv, PyTorch, FastAPI)
  go            - Go/Cloud Native ecosystem (Operators, Istio)
  rust          - Rust/WasmCloud ecosystem (Actors, Providers)
  typescript    - TypeScript/Node.js ecosystem (Express, Next.js)
  csharp        - C#/.NET ecosystem (ASP.NET Core, Entity Framework)
  java          - Java/JVM ecosystem (Spring Boot, Quarkus)

Options:
  -h, --help              Show this help message
  -d, --dry-run           Show what would be deployed without applying
  -v, --verbose           Enable verbose output
  -f, --force             Force deployment even if validation fails
  -c, --context CONTEXT   Kubernetes context to use (default: current)
  -n, --namespace NAMESPACE Kubernetes namespace (default: flux-system)

Examples:
  $0 opensource
  $0 enterprise
  $0 languages python
  $0 languages go --dry-run
  $0 languages rust --context dev-cluster

EOF
}

# Function to validate variant exists
validate_variant() {
    local variant_type=$1
    local variant_name=$2
    
    if [[ "$variant_type" == "languages" ]]; then
        if [[ -z "$variant_name" ]]; then
            print_color "$RED" "Error: Language variant name required when using 'languages' type"
            exit 1
        fi
        local variant_path="$VARIANTS_DIR/languages/$variant_name/kustomization.yaml"
    else
        local variant_path="$VARIANTS_DIR/$variant_type/kustomization.yaml"
    fi
    
    if [[ ! -f "$variant_path" ]]; then
        print_color "$RED" "Error: Variant not found at $variant_path"
        exit 1
    fi
    
    echo "$variant_path"
}

# Function to validate dependencies
validate_dependencies() {
    local variant_path=$1
    
    print_color "$BLUE" "Validating variant dependencies..."
    
    # Check if kustomize is available
    if ! command -v kustomize &> /dev/null; then
        print_color "$RED" "Error: kustomize is required but not installed"
        exit 1
    fi
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        print_color "$RED" "Error: kubectl is required but not installed"
        exit 1
    fi
    
    # Validate kustomization
    if ! kustomize build "$(dirname "$variant_path")" &> /dev/null; then
        print_color "$RED" "Error: Invalid kustomization in $variant_path"
        exit 1
    fi
    
    print_color "$GREEN" "✓ Dependencies validated"
}

# Function to generate DAG visualization
generate_dag() {
    local variant_path=$1
    local output_dir="$REPO_ROOT/docs/diagrams"
    
    print_color "$BLUE" "Generating DAG visualization..."
    
    mkdir -p "$output_dir"
    
    # Use the DAG visualizer
    if [[ -f "$REPO_ROOT/scripts/dag-visualizer.py" ]]; then
        python3 "$REPO_ROOT/scripts/dag-visualizer.py" \
            "$REPO_ROOT" \
            --format mermaid \
            --output "$output_dir/current-variant-dag.md"
        
        print_color "$GREEN" "✓ DAG visualization generated at $output_dir/current-variant-dag.md"
    else
        print_color "$YELLOW" "Warning: DAG visualizer not found, skipping visualization"
    fi
}

# Function to deploy variant
deploy_variant() {
    local variant_path=$1
    local dry_run=$2
    local context=${3:-}
    local namespace=${4:-flux-system}
    
    local variant_dir="$(dirname "$variant_path")"
    local variant_name="$(basename "$(dirname "$variant_dir")")"
    
    if [[ "$(basename "$variant_dir")" == "languages" ]]; then
        variant_name="$(basename "$variant_dir")"
    fi
    
    print_color "$BLUE" "Deploying variant: $variant_name"
    print_color "$BLUE" "Source: $variant_dir"
    
    local kustomize_cmd="kustomize build \"$variant_dir\""
    
    if [[ "$dry_run" == "true" ]]; then
        print_color "$YELLOW" "DRY RUN: The following would be deployed:"
        eval "$kustomize_cmd"
        return 0
    fi
    
    # Build and apply
    local manifest
    manifest=$(eval "$kustomize_cmd")
    
    # Add context if specified
    local kubectl_cmd="kubectl apply -f -"
    if [[ -n "$context" ]]; then
        kubectl_cmd="kubectl --context \"$context\" apply -f -"
    fi
    
    if [[ "$namespace" != "flux-system" ]]; then
        kubectl_cmd="kubectl apply --namespace \"$namespace\" -f -"
    fi
    
    echo "$manifest" | eval "$kubectl_cmd"
    
    print_color "$GREEN" "✓ Variant $variant_name deployed successfully"
}

# Function to show variant info
show_variant_info() {
    local variant_path=$1
    
    print_color "$BLUE" "Variant Information:"
    echo "Path: $variant_path"
    
    # Extract variant metadata
    if command -v yq &> /dev/null; then
        local name
        name=$(yq eval '.metadata.name' "$variant_path")
        local namespace
        namespace=$(yq eval '.metadata.namespace' "$variant_path")
        
        echo "Name: $name"
        echo "Namespace: $namespace"
        
        # Show annotations
        print_color "$BLUE" "Annotations:"
        yq eval '.metadata.annotations' "$variant_path" 2>/dev/null || echo "No annotations found"
    fi
}

# Main execution
main() {
    local dry_run=false
    local verbose=false
    local force=false
    local context=""
    local namespace="flux-system"
    local variant_type=""
    local variant_name=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -d|--dry-run)
                dry_run=true
                shift
                ;;
            -v|--verbose)
                verbose=true
                set -x
                shift
                ;;
            -f|--force)
                force=true
                shift
                ;;
            -c|--context)
                context="$2"
                shift 2
                ;;
            -n|--namespace)
                namespace="$2"
                shift 2
                ;;
            opensource|enterprise)
                variant_type="$1"
                shift
                ;;
            languages)
                variant_type="$1"
                variant_name="$2"
                shift 2
                ;;
            *)
                print_color "$RED" "Error: Unknown option $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Validate arguments
    if [[ -z "$variant_type" ]]; then
        print_color "$RED" "Error: Variant type required"
        show_usage
        exit 1
    fi
    
    # Validate variant exists
    local variant_path
    variant_path=$(validate_variant "$variant_type" "$variant_name")
    
    # Show variant info
    show_variant_info "$variant_path"
    
    # Validate dependencies
    if [[ "$force" != "true" ]]; then
        validate_dependencies "$variant_path"
    fi
    
    # Generate DAG
    generate_dag "$variant_path"
    
    # Deploy variant
    deploy_variant "$variant_path" "$dry_run" "$context" "$namespace"
    
    print_color "$GREEN" "Variant deployment completed successfully!"
}

# Run main function with all arguments
main "$@"

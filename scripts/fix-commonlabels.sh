#!/bin/bash
# Fix commonLabels to labels in all Kustomization files
# Resolves deprecated kustomize warning

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Function to fix commonLabels in a single file
fix_commonlabels() {
    local file="$1"
    
    if [[ ! -f "$file" ]]; then
        print_error "File not found: $file"
        return 1
    fi
    
    print_info "Fixing $file..."
    
    # Check if file contains commonLabels
    if grep -q "commonLabels:" "$file"; then
        # Create backup
        cp "$file" "$file.backup"
        
        # Use gsed for consistent cross-platform behavior
        if command -v gsed &> /dev/null; then
            SED_CMD="gsed"
        else
            SED_CMD="sed"
        fi
        
        # Fix commonLabels to labels with proper structure
        $SED_CMD -i '/^[[:space:]]*commonLabels:/,/^$/{
            s/^[[:space:]]*commonLabels:/labels:/
            s/^[[:space:]]*\([^[:space:]]\{1,\}\):[[:space:]]*\(.*\)/  - pairs:\n      \1: \2/
        }' "$file"
        
        # Clean up any malformed entries
        $SED_CMD -i '/^[[:space:]]*-[[:space:]]*pairs:/{
            N
            s/^[[:space:]]*-\s*pairs:\n[[:space:]]*\([^:]*\):[[:space:]]*\(.*\)/  - pairs:\n      \1: \2/
        }' "$file"
        
        print_success "Fixed $file"
        return 0
    else
        print_info "No commonLabels found in $file"
        return 0
    fi
}

# Main execution
main() {
    print_header "Fixing commonLabels to labels"
    echo "🔧 Resolving deprecated kustomize warning"
    echo ""
    
    # Find all kustomization files with commonLabels
    print_info "Searching for kustomization files with commonLabels..."
    
    # Use find with grep to locate files
    mapfile -t files < <(find $TOPDIR/agentic-reconciliation-engine -name "kustomization.yaml" -exec grep -l "commonLabels" {} \; 2>/dev/null || true)
    
    if [[ ${#files[@]} -eq 0 ]]; then
        print_success "No files with commonLabels found"
        exit 0
    fi
    
    print_info "Found ${#files[@]} files to fix"
    echo ""
    
    # Fix each file
    local fixed_count=0
    local failed_count=0
    
    for file in "${files[@]}"; do
        if fix_commonlabels "$file"; then
            ((fixed_count++))
        else
            ((failed_count++))
        fi
    done
    
    echo ""
    print_header "Summary"
    echo "Files processed: ${#files[@]}"
    echo "Successfully fixed: $fixed_count"
    echo "Failed: $failed_count"
    
    if [[ $failed_count -gt 0 ]]; then
        print_error "Some files failed to fix"
        exit 1
    else
        print_success "All commonLabels fixed successfully!"
        echo ""
        print_info "Next steps:"
        echo "1. Test the kustomization: kubectl kustomize <directory>"
        echo "2. Deploy monitoring stack: kubectl apply -k <directory>"
        echo "3. Verify deployment: kubectl get pods -n monitoring"
    fi
}

# Handle script interruption
trap 'echo -e "${RED}❌ Fix interrupted${NC}"; exit 1' INT TERM

# Run main function
main "$@"

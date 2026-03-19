#!/bin/bash

# Secret Rotation Script for Agentic Reconciliation Engine
# This script automates the rotation of sealed secrets

set -euxo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SECRETS_DIR="$PROJECT_ROOT/core/resources/tenants/3-workloads/helm-releases/monitoring"
LOG_FILE="$PROJECT_ROOT/logs/rotate-secrets.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    log "ERROR: $1"
    exit 1
}

# Success message
success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
    log "SUCCESS: $1"
}

# Warning message
warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
    log "WARNING: $1"
}

# Info message
info() {
    echo -e "${BLUE}INFO: $1${NC}"
    log "INFO: $1"
}

# Generate secure random password
generate_password() {
    local length=${1:-32}
    openssl rand -base64 "$length" | tr -d "=+/" | cut -c1-"$length"
}

# Generate secure random hex key
generate_hex_key() {
    local length=${1:-32}
    openssl rand -hex "$length"
}

# Check if required tools are installed
check_dependencies() {
    info "Checking dependencies..."
    
    command -v kubectl >/dev/null 2>&1 || error_exit "kubectl is not installed"
    command -v kubeseal >/dev/null 2>&1 || error_exit "kubeseal is not installed"
    command -v openssl >/dev/null 2>&1 || error_exit "openssl is not installed"
    
    success "All dependencies are available"
}

# Check cluster connectivity
check_cluster() {
    info "Checking cluster connectivity..."
    
    if ! kubectl cluster-info >/dev/null 2>&1; then
        error_exit "Cannot connect to Kubernetes cluster"
    fi
    
    success "Cluster connectivity verified"
}

# Backup current secrets
backup_secrets() {
    info "Creating backup of current secrets..."
    
    local backup_dir="$PROJECT_ROOT/backups/secrets-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    
    if [[ -f "$SECRETS_DIR/grafana-secrets.yaml" ]]; then
        cp "$SECRETS_DIR/grafana-secrets.yaml" "$backup_dir/"
        success "Backup created at $backup_dir"
    else
        warning "No existing secrets file found to backup"
    fi
}

# Rotate Grafana secrets
rotate_grafana_secrets() {
    info "Rotating Grafana secrets..."
    
    # Generate new secure values
    local admin_password=$(generate_password 24)
    local secret_key=$(generate_hex_key 32)
    local database_password=$(generate_password 32)
    local smtp_password=$(generate_password 32)
    
    info "Generated new secure passwords"
    
    # Create temporary secret manifest
    local temp_secret=$(mktemp)
    cat > "$temp_secret" << EOF
apiVersion: v1
kind: Secret
metadata:
  name: grafana-credentials
  namespace: monitoring
type: Opaque
stringData:
  GF_SECURITY_ADMIN_USER: "admin"
  GF_SECURITY_ADMIN_PASSWORD: "$admin_password"
  GF_SECURITY_SECRET_KEY: "$secret_key"
  GF_DATABASE_PASSWORD: "$database_password"
  GF_SMTP_PASSWORD: "$smtp_password"
EOF
    
    # Seal the secret
    info "Sealing the secret..."
    local sealed_secret="$SECRETS_DIR/grafana-secrets.yaml"
    
    if ! kubeseal --format yaml < "$temp_secret" > "$sealed_secret"; then
        rm -f "$temp_secret"
        error_exit "Failed to seal the secret"
    fi
    
    # Clean up
    rm -f "$temp_secret"
    
    success "Grafana secrets rotated and sealed"
    
    # Display the new values (for secure storage)
    warning "Please store these new values securely:"
    echo "Admin Password: $admin_password"
    echo "Secret Key: $secret_key"
    echo "Database Password: $database_password"
    echo "SMTP Password: $smtp_password"
}

# Validate sealed secret
validate_sealed_secret() {
    info "Validating sealed secret..."
    
    local sealed_file="$SECRETS_DIR/grafana-secrets.yaml"
    
    if [[ ! -f "$sealed_file" ]]; then
        error_exit "Sealed secret file not found: $sealed_file"
    fi
    
    # Check if it's a valid SealedSecret
    if ! grep -q "kind: SealedSecret" "$sealed_file"; then
        error_exit "Invalid SealedSecret format"
    fi
    
    # Check if namespace is correct
    if ! grep -q "namespace: monitoring" "$sealed_file"; then
        error_exit "Incorrect namespace in SealedSecret"
    fi
    
    success "Sealed secret validation passed"
}

# Commit changes
commit_changes() {
    info "Committing changes to Git..."
    
    cd "$PROJECT_ROOT"
    
    # Add the updated sealed secret
    git add "$SECRETS_DIR/grafana-secrets.yaml"
    
    # Check if there are changes to commit
    if git diff --cached --quiet; then
        warning "No changes to commit"
        return
    fi
    
    # Create commit
    local commit_message="chore(security): Rotate Grafana secrets - $(date '+%Y-%m-%d %H:%M:%S')"
    
    if ! git commit -m "$commit_message"; then
        error_exit "Failed to commit changes"
    fi
    
    success "Changes committed to Git"
    
    # Optionally push to remote
    if [[ "${1:-}" == "--push" ]]; then
        info "Pushing changes to remote..."
        if ! git push; then
            error_exit "Failed to push changes to remote"
        fi
        success "Changes pushed to remote"
    fi
}

# Main function
main() {
    info "Starting secret rotation process..."
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Parse command line arguments
    local push_to_remote=false
    while [[ $# -gt 0 ]]; do
        case $1 in
            --push)
                push_to_remote=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [--push] [--help]"
                echo "  --push    Push changes to remote Git repository"
                echo "  --help    Show this help message"
                exit 0
                ;;
            *)
                error_exit "Unknown argument: $1"
                ;;
        esac
    done
    
    # Execute rotation steps
    check_dependencies
    check_cluster
    backup_secrets
    rotate_grafana_secrets
    validate_sealed_secret
    
    if [[ "$push_to_remote" == true ]]; then
        commit_changes --push
    else
        commit_changes
    fi
    
    success "Secret rotation completed successfully!"
    info "Log file: $LOG_FILE"
}

# Execute main function with all arguments
main "$@"

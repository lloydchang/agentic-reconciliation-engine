#!/bin/bash

# Certificate Discovery Script
# Scans GitOps repositories for TLS certificates and builds inventory

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${OUTPUT_DIR:-$(mktemp -d)}"
INVENTORY_FILE="${OUTPUT_DIR}/certificates-inventory.json"
REPOS_DIR="${REPOS_DIR:-/tmp/gitops-repos}"
LOG_FILE="${OUTPUT_DIR}/discovery.log"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    command -v jq >/dev/null || error_exit "jq is required"
    command -v openssl >/dev/null || error_exit "openssl is required"
    command -v git >/dev/null || error_exit "git is required"
    
    log "Prerequisites check passed"
}

# Clone or update GitOps repositories
setup_repositories() {
    log "Setting up repositories..."
    
    if [[ ! -d "$REPOS_DIR" ]]; then
        mkdir -p "$REPOS_DIR"
    fi
    
    # Example repos - configure based on your environment
    local repos=(
        "gitops-manifests"
        "k8s-configs"
        "infrastructure-as-code"
    )
    
    for repo in "${repos[@]}"; do
        local repo_path="$REPOS_DIR/$repo"
        if [[ -d "$repo_path" ]]; then
            log "Updating repository: $repo"
            git -C "$repo_path" pull origin main
        else
            log "Cloning repository: $repo"
            git clone "git@github.com:company/$repo.git" "$repo_path"
        fi
    done
}

# Extract certificates from files
extract_certificates_from_file() {
    local file="$1"
    local temp_cert=$(mktemp)
    
    # Extract PEM certificates
    if grep -q "-----BEGIN CERTIFICATE-----" "$file"; then
        sed -n '/-----BEGIN CERTIFICATE-----/,/-----END CERTIFICATE-----/p' "$file" > "$temp_cert"
        
        if openssl x509 -in "$temp_cert" -noout -text >/dev/null 2>&1; then
            local cert_info=$(openssl x509 -in "$temp_cert" -noout -text -json 2>/dev/null || echo "{}")
            local subject=$(echo "$cert_info" | jq -r '.subject.common_name // "unknown"')
            local issuer=$(echo "$cert_info" | jq -r '.issuer.common_name // "unknown"')
            local not_after=$(echo "$cert_info" | jq -r '.not_after // ""')
            local san=$(echo "$cert_info" | jq -r '.extensions."subjectAltName" // ""')
            
            # Convert date to timestamp
            local expiry_timestamp=$(date -d "$not_after" +%s 2>/dev/null || echo "0")
            local days_until_expiry=$(( (expiry_timestamp - $(date +%s)) / 86400 ))
            
            jq -n \
                --arg file "$file" \
                --arg subject "$subject" \
                --arg issuer "$issuer" \
                --arg not_after "$not_after" \
                --arg days_until_expiry "$days_until_expiry" \
                --arg san "$san" \
                --arg type "pem" \
                '{
                    file: $file,
                    subject: $subject,
                    issuer: $issuer,
                    not_after: $not_after,
                    days_until_expiry: ($days_until_expiry | tonumber),
                    san: $san,
                    type: $type
                }'
        fi
    fi
    
    rm -f "$temp_cert"
}

# Extract certificates from Kubernetes secrets
extract_from_k8s_secrets() {
    local repo_path="$1"
    local results=()
    
    log "Scanning Kubernetes secrets in: $repo_path"
    
    while IFS= read -r -d '' secret_file; do
        if [[ -f "$secret_file" ]]; then
            # Check if it's a TLS secret
            if grep -q "type: kubernetes.io/tls" "$secret_file" 2>/dev/null; then
                local tls_cert=$(yq eval '.data."tls.crt"' "$secret_file" 2>/dev/null | base64 -d 2>/dev/null || echo "")
                if [[ -n "$tls_cert" ]]; then
                    local temp_cert=$(mktemp)
                    echo "$tls_cert" > "$temp_cert"
                    
                    if openssl x509 -in "$temp_cert" -noout -text >/dev/null 2>&1; then
                        local cert_info=$(openssl x509 -in "$temp_cert" -noout -text -json 2>/dev/null || echo "{}")
                        local subject=$(echo "$cert_info" | jq -r '.subject.common_name // "unknown"')
                        local issuer=$(echo "$cert_info" | jq -r '.issuer.common_name // "unknown"')
                        local not_after=$(echo "$cert_info" | jq -r '.not_after // ""')
                        local expiry_timestamp=$(date -d "$not_after" +%s 2>/dev/null || echo "0")
                        local days_until_expiry=$(( (expiry_timestamp - $(date +%s)) / 86400 ))
                        
                        results+=($(jq -n \
                            --arg file "$secret_file" \
                            --arg subject "$subject" \
                            --arg issuer "$issuer" \
                            --arg not_after "$not_after" \
                            --arg days_until_expiry "$days_until_expiry" \
                            --arg type "k8s-tls-secret" \
                            '{
                                file: $file,
                                subject: $subject,
                                issuer: $issuer,
                                not_after: $not_after,
                                days_until_expiry: ($days_until_expiry | tonumber),
                                type: $type
                            }'))
                    fi
                    
                    rm -f "$temp_cert"
                fi
            fi
        fi
    done < <(find "$repo_path" -name "*.yaml" -o -name "*.yml" -print0)
    
    printf '%s\n' "${results[@]}"
}

# Scan repositories for certificates
scan_repositories() {
    log "Scanning repositories for certificates..."
    
    local certificates=()
    
    while IFS= read -r -d '' repo_path; do
        if [[ -d "$repo_path" ]]; then
            log "Scanning repository: $(basename "$repo_path")"
            
            # Extract from Kubernetes secrets
            local k8s_certs=$(extract_from_k8s_secrets "$repo_path")
            certificates+=($k8s_certs)
            
            # Extract from PEM files
            while IFS= read -r -d '' pem_file; do
                if [[ -f "$pem_file" ]]; then
                    local cert=$(extract_certificates_from_file "$pem_file")
                    if [[ -n "$cert" ]]; then
                        certificates+=("$cert")
                    fi
                fi
            done < <(find "$repo_path" -name "*.pem" -o -name "*.crt" -o -name "*.cert" -print0)
        fi
    done < <(find "$REPOS_DIR" -maxdepth 1 -type d -not -path "$REPOS_DIR" -print0)
    
    # Combine results
    printf '%s\n' "${certificates[@]}" | jq -s '.' > "$INVENTORY_FILE"
    
    local total_certs=$(jq length "$INVENTORY_FILE")
    log "Discovered $total_certs certificates"
}

# Generate summary report
generate_summary() {
    log "Generating discovery summary..."
    
    local summary_file="${OUTPUT_DIR}/discovery-summary.json"
    
    jq -n \
        --arg total_certs "$(jq length "$INVENTORY_FILE")" \
        --arg expiring_soon "$(jq '[.[] | select(.days_until_expiry < 30)] | length' "$INVENTORY_FILE")" \
        --arg expired "$(jq '[.[] | select(.days_until_expiry < 0)] | length' "$INVENTORY_FILE")" \
        --arg scan_date "$(date -Iseconds)" \
        '{
            total_certificates: ($total_certs | tonumber),
            expiring_soon: ($expiring_soon | tonumber),
            expired: ($expired | tonumber),
            scan_date: $scan_date
        }' > "$summary_file"
    
    log "Discovery summary saved to: $summary_file"
}

# Main execution
main() {
    log "Starting certificate discovery..."
    
    check_prerequisites
    setup_repositories
    scan_repositories
    generate_summary
    
    log "Certificate discovery completed"
    log "Inventory saved to: $INVENTORY_FILE"
    log "Log file: $LOG_FILE"
}

# Execute main function
main "$@"

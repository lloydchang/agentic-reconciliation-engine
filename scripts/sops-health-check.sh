#!/bin/bash

# SOPS Health Check Script
# This script performs health checks on SOPS operations and provides status reporting

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_ROOT="${REPO_ROOT:-$(pwd)}"
NAMESPACE="${NAMESPACE:-flux-system}"
SECRET_NAME="${SECRET_NAME:-sops-age}"

echo -e "${BLUE}🏥 SOPS Health Check${NC}"
echo "This script performs comprehensive health checks for SOPS operations."
echo

# Health check results
HEALTHY=true
WARNINGS=0
ERRORS=0

# Function to log health check result
log_result() {
    local status="$1"
    local check="$2"
    local message="$3"
    local details="$4"
    
    case "$status" in
        "PASS")
            echo -e "${GREEN}✅ ${check}: ${message}${NC}"
            [[ -n "$details" ]] && echo "   ${details}"
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  ${check}: ${message}${NC}"
            [[ -n "$details" ]] && echo "   ${details}"
            ((WARNINGS++))
            ;;
        "FAIL")
            echo -e "${RED}❌ ${check}: ${message}${NC}"
            [[ -n "$details" ]] && echo "   ${details}"
            ((ERRORS++))
            HEALTHY=false
            ;;
    esac
    echo
}

# 1. Check SOPS tools
echo -e "${BLUE}1. Tool Health Check${NC}"
if command -v sops &> /dev/null; then
    SOPS_VERSION=$(sops --version 2>/dev/null | head -1 || echo "unknown")
    log_result "PASS" "SOPS CLI" "Available" "Version: ${SOPS_VERSION}"
else
    log_result "FAIL" "SOPS CLI" "Not found" "Install with: brew install sops"
fi

if command -v age &> /dev/null; then
    AGE_VERSION=$(age --version 2>/dev/null | head -1 || echo "unknown")
    log_result "PASS" "Age CLI" "Available" "Version: ${AGE_VERSION}"
else
    log_result "FAIL" "Age CLI" "Not found" "Install with: brew install age"
fi

# 2. Check configuration files
echo -e "${BLUE}2. Configuration Health Check${NC}"
if [[ -f "${REPO_ROOT}/.sops.yaml" ]]; then
    if python3 -c "import yaml; yaml.safe_load(open('${REPO_ROOT}/.sops.yaml'))" 2>/dev/null; then
        log_result "PASS" "SOPS Config" "Valid YAML" "Configuration file is syntactically correct"
    else
        log_result "FAIL" "SOPS Config" "Invalid YAML" "Configuration file has syntax errors"
    fi
    
    # Check for age keys
    AGE_KEYS=$(grep -c 'age1[a-z0-9]*' "${REPO_ROOT}/.sops.yaml" 2>/dev/null || echo "0")
    if [[ "$AGE_KEYS" -gt 0 ]]; then
        log_result "PASS" "Age Keys" "Found" "${AGE_KEYS} age key(s) in configuration"
    else
        log_result "FAIL" "Age Keys" "Missing" "No age keys found in SOPS configuration"
    fi
else
    log_result "FAIL" "SOPS Config" "Missing" "Configuration file not found"
fi

if [[ -f "${REPO_ROOT}/.sops.pub.age" ]]; then
    PUB_KEY=$(grep "^age1" "${REPO_ROOT}/.sops.pub.age" | head -1 || echo "")
    if [[ -n "$PUB_KEY" ]]; then
        log_result "PASS" "Public Key" "Available" "Public key file exists with valid key"
    else
        log_result "WARN" "Public Key" "Invalid" "Public key file exists but no valid key found"
    fi
else
    log_result "WARN" "Public Key" "Missing" "Public key file not found"
fi

if [[ -f "${REPO_ROOT}/.sops-keys/age.agekey" ]]; then
    if grep -q "AGE-SECRET-KEY-" "${REPO_ROOT}/.sops-keys/age.agekey"; then
        log_result "PASS" "Private Key" "Available" "Private key file exists"
    else
        log_result "FAIL" "Private Key" "Invalid" "Private key file format is invalid"
    fi
else
    log_result "WARN" "Private Key" "Missing" "Private key file not found"
fi

# 3. Cluster health check
echo -e "${BLUE}3. Cluster Health Check${NC}"
if kubectl cluster-info &>/dev/null; then
    log_result "PASS" "Cluster Access" "Connected" "Can access Kubernetes cluster"
    
    # Check flux-system namespace
    if kubectl get namespace "${NAMESPACE}" &>/dev/null; then
        log_result "PASS" "Flux Namespace" "Exists" "Namespace ${NAMESPACE} is present"
        
        # Check sops-age secret
        if kubectl get secret "${SECRET_NAME}" -n "${NAMESPACE}" &>/dev/null; then
            SECRET_AGE=$(kubectl get secret "${SECRET_NAME}" -n "${NAMESPACE}" -o jsonpath='{.metadata.creationTimestamp}' 2>/dev/null || echo "unknown")
            log_result "PASS" "SOPS Secret" "Exists" "Secret ${SECRET_NAME} created at ${SECRET_AGE}"
            
            # Check secret data
            if kubectl get secret "${SECRET_NAME}" -n "${NAMESPACE}" -o jsonpath='{.data.age\.agekey}' &>/dev/null; then
                log_result "PASS" "SOPS Secret Data" "Valid" "Secret contains age.agekey data"
            else
                log_result "FAIL" "SOPS Secret Data" "Missing" "Secret does not contain age.agekey data"
            fi
        else
            log_result "FAIL" "SOPS Secret" "Missing" "Secret ${SECRET_NAME} not found in ${NAMESPACE}"
        fi
        
        # Check kustomize-controller
        if kubectl get deployment kustomize-controller -n "${NAMESPACE}" &>/dev/null; then
            CONTROLLER_STATUS=$(kubectl get deployment kustomize-controller -n "${NAMESPACE}" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
            if [[ "$CONTROLLER_STATUS" -gt 0 ]]; then
                log_result "PASS" "Kustomize Controller" "Ready" "${CONTROLLER_STATUS} replicas ready"
            else
                log_result "FAIL" "Kustomize Controller" "Not Ready" "No ready replicas"
            fi
        else
            log_result "FAIL" "Kustomize Controller" "Missing" "Controller deployment not found"
        fi
    else
        log_result "FAIL" "Flux Namespace" "Missing" "Namespace ${NAMESPACE} not found"
    fi
else
    log_result "WARN" "Cluster Access" "Disconnected" "Cannot access Kubernetes cluster"
fi

# 4. Encrypted secrets health check
echo -e "${BLUE}4. Encrypted Secrets Health Check${NC}"
SECRET_FILES=$(find "${REPO_ROOT}" -name "*.secret.yaml" -type f 2>/dev/null || true)
if [[ -n "$SECRET_FILES" ]]; then
    SECRET_COUNT=$(echo "$SECRET_FILES" | wc -l)
    log_result "PASS" "Secret Files" "Found" "${SECRET_COUNT} .secret.yaml files"
    
    # Check encryption status
    ENCRYPTED_COUNT=0
    DECRYPTION_ERRORS=0
    
    for file in $SECRET_FILES; do
        if grep -q "ENC\[AES256_GCM" "$file" 2>/dev/null; then
            ((ENCRYPTED_COUNT++))
        fi
        
        # Test decryption (only if private key is available)
        if [[ -f "${REPO_ROOT}/.sops-keys/age.agekey" ]]; then
            if ! SOPS_AGE_KEY_FILE="${REPO_ROOT}/.sops-keys/age.agekey" sops --decrypt "$file" >/dev/null 2>&1; then
                ((DECRYPTION_ERRORS++))
            fi
        fi
    done
    
    if [[ "$ENCRYPTED_COUNT" -eq "$SECRET_COUNT" ]]; then
        log_result "PASS" "Secret Encryption" "Complete" "All ${SECRET_COUNT} secrets are encrypted"
    else
        log_result "WARN" "Secret Encryption" "Partial" "${ENCRYPTED_COUNT}/${SECRET_COUNT} secrets are encrypted"
    fi
    
    if [[ "$DECRYPTION_ERRORS" -gt 0 ]]; then
        log_result "FAIL" "Secret Decryption" "Errors" "${DECRYPTION_ERRORS} secrets have decryption errors"
    else
        log_result "PASS" "Secret Decryption" "Working" "All encrypted secrets can be decrypted"
    fi
else
    log_result "INFO" "Secret Files" "None" "No .secret.yaml files found"
fi

# 5. Flux reconciliation status
echo -e "${BLUE}5. Flux Reconciliation Health Check${NC}"
if kubectl cluster-info &>/dev/null && kubectl get namespace "${NAMESPACE}" &>/dev/null; then
    # Get kustomizations
    KUSTOMIZATIONS=$(kubectl get kustomizations -n "${NAMESPACE}" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    if [[ -n "$KUSTOMIZATIONS" ]]; then
        KUSTOMIZATION_COUNT=$(echo "$KUSTOMIZATIONS" | wc -w)
        log_result "PASS" "Kustomizations" "Found" "${KUSTOMIZATION_COUNT} kustomizations"
        
        # Check reconciliation status
        FAILED_COUNT=0
        for kustomization in $KUSTOMIZATIONS; do
            STATUS=$(kubectl get kustomization "$kustomization" -n "${NAMESPACE}" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "Unknown")
            if [[ "$STATUS" == "False" ]]; then
                ((FAILED_COUNT++))
            fi
        done
        
        if [[ "$FAILED_COUNT" -eq 0 ]]; then
            log_result "PASS" "Reconciliation" "Healthy" "All kustomizations are ready"
        else
            log_result "WARN" "Reconciliation" "Issues" "${FAILED_COUNT} kustomizations have issues"
        fi
    else
        log_result "INFO" "Kustomizations" "None" "No kustomizations found"
    fi
else
    log_result "INFO" "Flux Reconciliation" "Skipped" "Cluster access not available"
fi

# 6. Security health check
echo -e "${BLUE}6. Security Health Check${NC}"
if [[ -f ".gitignore" ]]; then
    if grep -q ".sops-keys" .gitignore || grep -q "age.agekey" .gitignore; then
        log_result "PASS" "Git Security" "Protected" "Private keys are excluded from Git"
    else
        log_result "WARN" "Git Security" "Unprotected" "Consider adding .sops-keys/ to .gitignore"
    fi
else
    log_result "WARN" "Git Security" "Unknown" "No .gitignore file found"
fi

# Check file permissions
if [[ -f "${REPO_ROOT}/.sops-keys/age.agekey" ]]; then
    PERMISSIONS=$(stat -f "%A" "${REPO_ROOT}/.sops-keys/age.agekey" 2>/dev/null || stat -c "%a" "${REPO_ROOT}/.sops-keys/age.agekey" 2>/dev/null || echo "unknown")
    if [[ "$PERMISSIONS" == "600" || "$PERMISSIONS" == "400" ]]; then
        log_result "PASS" "File Permissions" "Secure" "Private key has restricted permissions (${PERMISSIONS})"
    else
        log_result "WARN" "File Permissions" "Open" "Private key has open permissions (${PERMISSIONS})"
    fi
fi

# Summary
echo -e "${BLUE}📊 Health Check Summary${NC}"
echo "Errors: ${ERRORS}"
echo "Warnings: ${WARNINGS}"
echo

if [[ "$HEALTHY" == true ]]; then
    if [[ "$WARNINGS" -eq 0 ]]; then
        echo -e "${GREEN}🎉 SOPS setup is perfectly healthy!${NC}"
        echo "All systems are operational and secure."
    else
        echo -e "${YELLOW}⚠️  SOPS setup is healthy with ${WARNINGS} warnings.${NC}"
        echo "Consider addressing the warnings for optimal operation."
    fi
    exit 0
else
    echo -e "${RED}❌ SOPS setup has ${ERRORS} errors and ${WARNINGS} warnings.${NC}"
    echo "Please address the critical issues immediately."
    exit 1
fi

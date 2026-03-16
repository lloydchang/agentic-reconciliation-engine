#!/bin/bash

# SOPS Configuration Validation Script
# This script validates the SOPS setup and configuration

set -euo pipefail
cd $(dirname $0)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_ROOT="${REPO_ROOT:-$(pwd)}"
SOPS_CONFIG="${SOPS_CONFIG:-${REPO_ROOT}/.sops.yaml}"
PUBLIC_KEY_FILE="${PUBLIC_KEY_FILE:-${REPO_ROOT}/.sops.pub.age}"
PRIVATE_KEY_FILE="${PRIVATE_KEY_FILE:-${REPO_ROOT}/.sops-keys/age.agekey}"

echo -e "${BLUE}🔍 SOPS Configuration Validation${NC}"
echo "This script validates your SOPS setup and configuration."
echo

# Track validation results
VALIDATION_PASSED=true

# Function to print validation result
validate() {
    local test_name="$1"
    local result="$2"
    local details="$3"
    
    if [[ "$result" == "PASS" ]]; then
        echo -e "${GREEN}✅ ${test_name}: PASS${NC}"
        [[ -n "$details" ]] && echo "   ${details}"
    else
        echo -e "${RED}❌ ${test_name}: FAIL${NC}"
        [[ -n "$details" ]] && echo "   ${details}"
        VALIDATION_PASSED=false
    fi
    echo
}

# 1. Check if required tools are installed
echo -e "${BLUE}1. Tool Installation Check${NC}"
if command -v age &> /dev/null; then
    validate "age CLI" "PASS" "age CLI is installed"
else
    validate "age CLI" "FAIL" "age CLI is not installed. Install with: brew install age"
fi

if command -v sops &> /dev/null; then
    validate "sops CLI" "PASS" "sops CLI is installed"
else
    validate "sops CLI" "FAIL" "sops CLI is not installed. Install with: brew install sops"
fi

if command -v kubectl &> /dev/null; then
    validate "kubectl CLI" "PASS" "kubectl CLI is installed"
else
    validate "kubectl CLI" "WARN" "kubectl CLI is not installed. Required for cluster operations"
fi

# 2. Check SOPS configuration file
echo -e "${BLUE}2. SOPS Configuration File${NC}"
if [[ -f "${SOPS_CONFIG}" ]]; then
    validate "SOPS config file exists" "PASS" "Found ${SOPS_CONFIG}"
    
    # Check if config has valid YAML syntax
    if python3 -c "import yaml; yaml.safe_load(open('${SOPS_CONFIG}'))" 2>/dev/null; then
        validate "SOPS config YAML syntax" "PASS" "Valid YAML syntax"
    else
        validate "SOPS config YAML syntax" "FAIL" "Invalid YAML syntax"
    fi
    
    # Check for required sections
    if grep -q "creation_rules:" "${SOPS_CONFIG}"; then
        validate "creation_rules section" "PASS" "creation_rules found"
    else
        validate "creation_rules section" "FAIL" "creation_rules not found"
    fi
    
    # Extract and validate age keys
    AGE_KEYS=$(grep -o 'age1[a-z0-9]*' "${SOPS_CONFIG}" | head -5)
    if [[ -n "$AGE_KEYS" ]]; then
        validate "Age keys in config" "PASS" "Found age keys: ${AGE_KEYS}"
    else
        validate "Age keys in config" "FAIL" "No age keys found in configuration"
    fi
else
    validate "SOPS config file exists" "FAIL" "SOPS config file not found: ${SOPS_CONFIG}"
fi

# 3. Check public key file
echo -e "${BLUE}3. Public Key File${NC}"
if [[ -f "${PUBLIC_KEY_FILE}" ]]; then
    validate "Public key file exists" "PASS" "Found ${PUBLIC_KEY_FILE}"
    
    # Extract public key
    PUB_KEY=$(grep "^age1" "${PUBLIC_KEY_FILE}" | head -1)
    if [[ -n "$PUB_KEY" ]]; then
        validate "Public key format" "PASS" "Valid age public key: ${PUB_KEY}"
        
        # Check if public key matches config
        if grep -q "$PUB_KEY" "${SOPS_CONFIG}" 2>/dev/null; then
            validate "Public key consistency" "PASS" "Public key matches SOPS config"
        else
            validate "Public key consistency" "FAIL" "Public key does not match SOPS config"
        fi
    else
        validate "Public key format" "FAIL" "No valid age public key found"
    fi
else
    validate "Public key file exists" "FAIL" "Public key file not found: ${PUBLIC_KEY_FILE}"
fi

# 4. Check private key file
echo -e "${BLUE}4. Private Key File${NC}"
if [[ -f "${PRIVATE_KEY_FILE}" ]]; then
    validate "Private key file exists" "PASS" "Found ${PRIVATE_KEY_FILE}"
    
    # Check if private key is readable
    if grep -q "AGE-SECRET-KEY-" "${PRIVATE_KEY_FILE}"; then
        validate "Private key format" "PASS" "Valid age private key format"
    else
        validate "Private key format" "FAIL" "Invalid age private key format"
    fi
else
    validate "Private key file exists" "WARN" "Private key file not found: ${PRIVATE_KEY_FILE}"
fi

# 5. Test encryption/decryption
echo -e "${BLUE}5. Encryption/Decryption Test${NC}"
TEST_SECRET="/tmp/test-secret.yaml"
cat > "$TEST_SECRET" << EOF
apiVersion: v1
kind: Secret
metadata:
  name: test-secret
type: Opaque
data:
  test-key: dGVzdC12YWx1ZQ==
EOF

# Test encryption
if sops --encrypt --config "${SOPS_CONFIG}" --in-place "$TEST_SECRET" 2>/dev/null; then
    validate "Encryption test" "PASS" "Successfully encrypted test secret"
    
    # Test decryption
    if sops --decrypt --config "${SOPS_CONFIG}" "$TEST_SECRET" >/dev/null 2>&1; then
        validate "Decryption test" "PASS" "Successfully decrypted test secret"
    else
        validate "Decryption test" "FAIL" "Failed to decrypt test secret"
    fi
else
    validate "Encryption test" "FAIL" "Failed to encrypt test secret"
fi

# Clean up
rm -f "$TEST_SECRET"

# 6. Check existing encrypted secrets
echo -e "${BLUE}6. Existing Encrypted Secrets${NC}"
SECRET_FILES=$(find "${REPO_ROOT}" -name "*.secret.yaml" -type f 2>/dev/null || true)
if [[ -n "$SECRET_FILES" ]]; then
    SECRET_COUNT=$(echo "$SECRET_FILES" | wc -l)
    validate "Encrypted secrets found" "PASS" "Found ${SECRET_COUNT} .secret.yaml files"
    
    # Check if secrets are properly encrypted
    ENCRYPTED_COUNT=0
    for file in $SECRET_FILES; do
        if grep -q "ENC\[AES256_GCM" "$file" 2>/dev/null; then
            ((ENCRYPTED_COUNT++))
        fi
    done
    
    if [[ "$ENCRYPTED_COUNT" -eq "$SECRET_COUNT" ]]; then
        validate "Secret encryption status" "PASS" "All ${SECRET_COUNT} secrets are encrypted"
    else
        validate "Secret encryption status" "WARN" "${ENCRYPTED_COUNT}/${SECRET_COUNT} secrets are encrypted"
    fi
else
    validate "Encrypted secrets found" "INFO" "No .secret.yaml files found"
fi

# 7. Cluster connectivity (if kubectl is available)
echo -e "${BLUE}7. Cluster Connectivity${NC}"
if command -v kubectl &> /dev/null; then
    if kubectl cluster-info &>/dev/null; then
        validate "Cluster connectivity" "PASS" "Can connect to Kubernetes cluster"
        
        # Check if flux-system namespace exists
        if kubectl get namespace flux-system &>/dev/null; then
            validate "flux-system namespace" "PASS" "flux-system namespace exists"
            
            # Check if sops-age secret exists
            if kubectl get secret sops-age -n flux-system &>/dev/null; then
                validate "sops-age secret" "PASS" "sops-age secret exists in flux-system"
            else
                validate "sops-age secret" "WARN" "sops-age secret not found in flux-system"
            fi
        else
            validate "flux-system namespace" "WARN" "flux-system namespace not found"
        fi
    else
        validate "Cluster connectivity" "WARN" "Cannot connect to Kubernetes cluster"
    fi
fi

# 8. Git repository check
echo -e "${BLUE}8. Git Repository Check${NC}"
if git rev-parse --git-dir >/dev/null 2>&1; then
    validate "Git repository" "PASS" "Inside a Git repository"
    
    # Check if sensitive files are properly ignored
    if [[ -f ".gitignore" ]]; then
        if grep -q "age.agekey" .gitignore || grep -q ".sops-keys" .gitignore; then
            validate "Git ignore rules" "PASS" "Private keys are ignored"
        else
            validate "Git ignore rules" "WARN" "Consider adding .sops-keys/ to .gitignore"
        fi
    else
        validate "Git ignore rules" "WARN" "No .gitignore file found"
    fi
else
    validate "Git repository" "WARN" "Not inside a Git repository"
fi

# Summary
echo -e "${BLUE}📋 Validation Summary${NC}"
if [[ "$VALIDATION_PASSED" == true ]]; then
    echo -e "${GREEN}🎉 All critical validations passed!${NC}"
    echo "Your SOPS configuration is ready for use."
    exit 0
else
    echo -e "${RED}❌ Some validations failed.${NC}"
    echo "Please address the issues above before proceeding."
    exit 1
fi

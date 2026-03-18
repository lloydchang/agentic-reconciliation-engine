#!/bin/bash

# SOPS Secret Encryption Script
# This script encrypts all .secret.yaml files in the core/resources/tenants directory

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SECRETS_DIR="${SECRETS_DIR:-$(pwd)/core/resources/tenants}"
FLUX_SECRETS_DIR="${FLUX_SECRETS_DIR:-$(pwd)/core/operators/flux/secrets}"
AGE_KEY="${AGE_KEY:-}"
SOPS_CONFIG="${SOPS_CONFIG:-$(pwd)/.sops.yaml}"

echo -e "${GREEN}🔐 SOPS Secret Encryption${NC}"
echo "This script will encrypt all .secret.yaml and .sops.yaml files in the infrastructure and flux directories."
echo

# Check if SOPS is installed
if ! command -v sops &> /dev/null; then
    echo -e "${RED}❌ SOPS is not installed. Please install it first:${NC}"
    echo "brew install sops"
    exit 1
fi

# Check if age key is provided
if [[ -z "${AGE_KEY}" ]]; then
    echo -e "${YELLOW}⚠️  AGE_KEY not provided. Using key from .sops.yaml${NC}"
    # Extract age key from .sops.yaml
    if [[ -f "${SOPS_CONFIG}" ]]; then
        AGE_KEY=$(grep -o 'age1[a-z0-9]*' "${SOPS_CONFIG}" | head -1)
        if [[ -z "${AGE_KEY}" ]]; then
            echo -e "${RED}❌ No age key found in .sops.yaml${NC}"
            echo "Please set AGE_KEY environment variable or update .sops.yaml"
            exit 1
        fi
        echo "Using age key: ${AGE_KEY}"
    else
        echo -e "${RED}❌ .sops.yaml not found${NC}"
        exit 1
    fi
fi

# Check if secrets directory exists
if [[ ! -d "${SECRETS_DIR}" ]]; then
    echo -e "${RED}❌ Secrets directory not found: ${SECRETS_DIR}${NC}"
    exit 1
fi

# Find all .secret.yaml and .sops.yaml files
SECRET_FILES=$(find "${SECRETS_DIR}" -name "*.secret.yaml" -type f)
SOPS_FILES=$(find "${FLUX_SECRETS_DIR}" -name "*.sops.yaml" -type f)
ALL_FILES="${SECRET_FILES} ${SOPS_FILES}"

if [[ -z "${ALL_FILES}" ]]; then
    echo -e "${YELLOW}⚠️  No secret files found in ${SECRETS_DIR} or ${FLUX_SECRETS_DIR}${NC}"
    exit 0
fi

echo -e "${GREEN}📝 Found secret files to encrypt:${NC}"
echo "${ALL_FILES}"
echo

# Encrypt each secret file
for file in $ALL_FILES; do
    echo -e "${YELLOW}🔒 Encrypting: ${file}${NC}"
    
    # Check if file is already encrypted
    if grep -q "sops:" "${file}"; then
        echo -e "${YELLOW}⚠️  File ${file} appears to be already encrypted. Skipping...${NC}"
        continue
    fi
    
    # Encrypt the file
    sops --age="${AGE_KEY}" \
         --encrypted-regex='^(data|stringData)$' \
         --encrypt \
         --in-place "${file}"
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ Successfully encrypted: ${file}${NC}"
    else
        echo -e "${RED}❌ Failed to encrypt: ${file}${NC}"
        exit 1
    fi
done

echo
echo -e "${GREEN}🎉 Secret encryption complete!${NC}"
echo
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Review the encrypted files"
echo "2. Commit them to your Git repository"
echo "3. Ensure the age key is properly configured in your cluster"
echo "4. Verify Flux can decrypt the secrets"
echo
echo -e "${GREEN}🔍 Verification commands:${NC}"
echo "sops --decrypt ${SECRETS_DIR}/database-credentials.secret.yaml  # Test decryption"
echo "git status  # Check status of encrypted files"

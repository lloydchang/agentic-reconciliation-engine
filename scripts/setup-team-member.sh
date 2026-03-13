#!/bin/bash

# Team Member SOPS Setup Script
# This script helps team members set up SOPS for secret management

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REPO_ROOT="${REPO_ROOT:-$(pwd)}"
PUBLIC_KEY_FILE="${PUBLIC_KEY_FILE:-${REPO_ROOT}/.sops.pub.age}"

echo -e "${GREEN}👥 Team Member SOPS Setup${NC}"
echo "This script sets up SOPS for a team member to work with encrypted secrets."
echo

# Check if we're in the right directory
if [[ ! -f "${PUBLIC_KEY_FILE}" ]]; then
    echo -e "${RED}❌ Public key file not found: ${PUBLIC_KEY_FILE}${NC}"
    echo "Please ensure you're in the repository root and the public key file exists."
    exit 1
fi

# Check if age is installed
if ! command -v age &> /dev/null; then
    echo -e "${RED}❌ age is not installed. Please install it first:${NC}"
    echo "brew install age"
    exit 1
fi

# Check if sops is installed
if ! command -v sops &> /dev/null; then
    echo -e "${RED}❌ SOPS is not installed. Please install it first:${NC}"
    echo "brew install sops"
    exit 1
fi

echo -e "${GREEN}📋 Setting up SOPS for team member...${NC}"

# Extract public key from file
PUBLIC_KEY=$(grep "^age1" "${PUBLIC_KEY_FILE}" | head -1)

if [[ -z "${PUBLIC_KEY}" ]]; then
    echo -e "${RED}❌ No valid age public key found in ${PUBLIC_KEY_FILE}${NC}"
    exit 1
fi

echo "Public key found: ${PUBLIC_KEY}"

# Create team member's local SOPS config
cat > "${REPO_ROOT}/.sops.yaml" << EOF
# SOPS Configuration for GitOps Infrastructure Control Plane
# Team member configuration - uses shared public key

creation_rules:
  # Default rule for all YAML files - use age encryption
  - path_regex: .*.yaml$
    age: ${PUBLIC_KEY}
    encrypted_regex: '^(data|stringData)$'
  
  # Specific rules for secrets directories
  - path_regex: secrets/.*\.yaml$
    age: ${PUBLIC_KEY}
    encrypted_regex: '^(data|stringData)$'
  
  # Rules for infrastructure secrets
  - path_regex: infrastructure/.*\.secret\.yaml$
    age: ${PUBLIC_KEY}
    encrypted_regex: '^(data|stringData)$'
  
  # Rules for tenant-specific secrets
  - path_regex: infrastructure/tenants/.*/.*\.secret\.yaml$
    age: ${PUBLIC_KEY}
    encrypted_regex: '^(data|stringData)$'

# Key groups for team collaboration
key_groups:
  # Shared team key
  - age:
      - ${PUBLIC_KEY}
EOF

echo -e "${GREEN}✅ SOPS configuration updated with team public key${NC}"

# Test the setup
echo -e "${YELLOW}🧪 Testing SOPS configuration...${NC}"

# Create a test secret
TEST_SECRET_FILE="${REPO_ROOT}/test-secret.yaml"
cat > "${TEST_SECRET_FILE}" << EOF
apiVersion: v1
kind: Secret
metadata:
  name: test-secret
  namespace: default
type: Opaque
data:
  test-key: dGVzdC12YWx1ZQ==  # test-value
EOF

# Try to encrypt the test secret
if sops --age="${PUBLIC_KEY}" \
       --encrypted-regex='^(data|stringData)$' \
       --encrypt \
       --in-place "${TEST_SECRET_FILE}"; then
    echo -e "${GREEN}✅ SOPS encryption test successful${NC}"
    
    # Try to decrypt the test secret
    if sops --decrypt "${TEST_SECRET_FILE}" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ SOPS decryption test successful${NC}"
    else
        echo -e "${RED}❌ SOPS decryption test failed${NC}"
        rm -f "${TEST_SECRET_FILE}"
        exit 1
    fi
else
    echo -e "${RED}❌ SOPS encryption test failed${NC}"
    rm -f "${TEST_SECRET_FILE}"
    exit 1
fi

# Clean up test file
rm -f "${TEST_SECRET_FILE}"

echo
echo -e "${GREEN}🎉 Team member setup complete!${NC}"
echo
echo -e "${YELLOW}📋 Usage instructions:${NC}"
echo "1. Create new secrets: kubectl create secret generic my-secret --from-literal=key=value --dry-run=client -o yaml > my-secret.yaml"
echo "2. Encrypt secrets: sops --encrypt --in-place my-secret.yaml"
echo "3. Decrypt secrets (for editing): sops --decrypt my-secret.yaml > my-secret-decrypted.yaml"
echo "4. Edit secrets: sops my-secret.yaml"
echo
echo -e "${YELLOW}⚠️  Important reminders:${NC}"
echo "- Only encrypt the data/stringData fields"
echo "- Never commit unencrypted secrets to Git"
echo "- Use the repository's .sops.yaml configuration"
echo "- Contact the repository maintainer if you need to add new encryption keys"
echo
echo -e "${GREEN}🔐 You're ready to work with encrypted secrets!${NC}"

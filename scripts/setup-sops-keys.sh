#!/bin/bash

# SOPS Age Key Generation and Setup Script
# This script generates age keys and creates the necessary Kubernetes secrets for Flux SOPS decryption

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
KEY_DIR="${KEY_DIR:-$(pwd)/.sops-keys}"
CLUSTER_NAME="${CLUSTER_NAME:-gitops-infra-control-plane}"
NAMESPACE="${NAMESPACE:-flux-system}"
SECRET_NAME="${SECRET_NAME:-sops-age-key}"

echo -e "${GREEN}🔐 SOPS Age Key Generation and Setup${NC}"
echo "This script will generate age keys and create Kubernetes secrets for SOPS decryption."
echo

# Create key directory
mkdir -p "${KEY_DIR}"
cd "${KEY_DIR}"

# Generate age key if it doesn't exist
if [[ ! -f "age.agekey" ]]; then
    echo -e "${YELLOW}📝 Generating new age key...${NC}"
    age-keygen -o age.agekey
    
    # Extract public key
    PUBLIC_KEY=$(grep "Public key:" age.agekey | cut -d' ' -f3)
    echo -e "${GREEN}✅ Age key generated successfully${NC}"
    echo "Public key: ${PUBLIC_KEY}"
else
    echo -e "${YELLOW}⚠️  Age key already exists, using existing key${NC}"
    PUBLIC_KEY=$(grep "Public key:" age.agekey | cut -d' ' -f3)
    echo "Public key: ${PUBLIC_KEY}"
fi

# Backup the key file
cp age.agekey "age.agekey.backup.$(date +%Y%m%d-%H%M%S)"

echo
echo -e "${GREEN}🚀 Creating Kubernetes secret...${NC}"

# Check if cluster is accessible
if ! kubectl cluster-info &>/dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster. Please check your kubeconfig.${NC}"
    echo "You can create the secret manually with:"
    echo "cat ${KEY_DIR}/age.agekey | kubectl create secret generic ${SECRET_NAME} --namespace=${NAMESPACE} --from-file=age.agekey=/dev/stdin"
    exit 1
fi

# Create namespace if it doesn't exist
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# Create the secret
cat age.agekey | kubectl create secret generic "${SECRET_NAME}" \
    --namespace="${NAMESPACE}" \
    --from-file=age.agekey=/dev/stdin \
    --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✅ Kubernetes secret '${SECRET_NAME}' created in namespace '${NAMESPACE}'${NC}"

# Verify secret
if kubectl get secret "${SECRET_NAME}" -n "${NAMESPACE}" &>/dev/null; then
    echo -e "${GREEN}✅ Secret verification successful${NC}"
    kubectl get secret "${SECRET_NAME}" -n "${NAMESPACE}" -o jsonpath='{.data.age\.agekey}' | base64 -d | head -n 3
else
    echo -e "${RED}❌ Secret creation failed${NC}"
    exit 1
fi

echo
echo -e "${GREEN}📋 Setup Summary:${NC}"
echo "🔑 Age public key: ${PUBLIC_KEY}"
echo "📁 Key file location: ${KEY_DIR}/age.agekey"
echo "🔒 Kubernetes secret: ${SECRET_NAME} in ${NAMESPACE}"
echo
echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
echo "1. Backup the age.agekey file securely"
echo "2. Add the public key to your .sops.yaml configuration"
echo "3. Commit the .sops.yaml with the real public key"
echo "4. Never commit the private age.agekey file to Git"
echo
echo -e "${GREEN}🎉 SOPS key setup complete!${NC}"

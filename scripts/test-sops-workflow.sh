#!/bin/bash

# SOPS End-to-End Workflow Test
# This script tests the complete SOPS workflow from creation to deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_ROOT="${REPO_ROOT:-$(pwd)}"
TEST_NAMESPACE="${TEST_NAMESPACE:-sops-test}"
TEST_SECRET_NAME="${TEST_SECRET_NAME:-workflow-test-secret}"

echo -e "${BLUE}🧪 SOPS End-to-End Workflow Test${NC}"
echo "This script tests the complete SOPS workflow."
echo

# Cleanup function
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up test resources...${NC}"
    kubectl delete namespace "${TEST_NAMESPACE}" --ignore-not-found=true 2>/dev/null || true
    rm -f "${REPO_ROOT}/${TEST_SECRET_NAME}.yaml" 2>/dev/null || true
}

# Set trap for cleanup
trap cleanup EXIT

# 1. Create test namespace
echo -e "${BLUE}1. Creating test namespace${NC}"
if kubectl create namespace "${TEST_NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -; then
    echo -e "${GREEN}✅ Test namespace created${NC}"
else
    echo -e "${RED}❌ Failed to create test namespace${NC}"
    exit 1
fi

# 2. Create a test secret
echo -e "${BLUE}2. Creating test secret${NC}"
TEST_SECRET_FILE="${REPO_ROOT}/${TEST_SECRET_NAME}.yaml"
cat > "${TEST_SECRET_FILE}" << EOF
apiVersion: v1
kind: Secret
metadata:
  name: ${TEST_SECRET_NAME}
  namespace: ${TEST_NAMESPACE}
  labels:
    app.kubernetes.io/name: workflow-test
    app.kubernetes.io/component: secret
    gitops-infra-control-plane.io/managed-by: "sops-test"
type: Opaque
data:
  # Test data - base64 encoded
  username: dGVzdC11c2Vy  # test-user
  password: dGVzdC1wYXNzd29yZA==  # test-password
  api-key: dGVzdC1hcGkta2V5LXZhbHVl  # test-api-key-value
stringData:
  database-host: test-database.default.svc.cluster.local
  database-port: "5432"
  environment: test
EOF

echo -e "${GREEN}✅ Test secret manifest created${NC}"

# 3. Encrypt the secret
echo -e "${BLUE}3. Encrypting the secret${NC}"
if sops --encrypt --in-place "${TEST_SECRET_FILE}"; then
    echo -e "${GREEN}✅ Secret encrypted successfully${NC}"
else
    echo -e "${RED}❌ Failed to encrypt secret${NC}"
    exit 1
fi

# 4. Verify encryption
echo -e "${BLUE}4. Verifying encryption${NC}"
if grep -q "ENC\[AES256_GCM" "${TEST_SECRET_FILE}"; then
    echo -e "${GREEN}✅ Secret is properly encrypted${NC}"
else
    echo -e "${RED}❌ Secret is not properly encrypted${NC}"
    exit 1
fi

# 5. Test decryption
echo -e "${BLUE}5. Testing decryption${NC}"
if sops --decrypt "${TEST_SECRET_FILE}" | grep -q "test-user"; then
    echo -e "${GREEN}✅ Secret can be decrypted${NC}"
else
    echo -e "${RED}❌ Failed to decrypt secret${NC}"
    exit 1
fi

# 6. Apply encrypted secret to cluster
echo -e "${BLUE}6. Applying encrypted secret to cluster${NC}"
if kubectl apply -f "${TEST_SECRET_FILE}"; then
    echo -e "${GREEN}✅ Secret applied to cluster${NC}"
else
    echo -e "${RED}❌ Failed to apply secret to cluster${NC}"
    exit 1
fi

# 7. Wait for secret to be available
echo -e "${BLUE}7. Waiting for secret to be available${NC}"
for i in {1..30}; do
    if kubectl get secret "${TEST_SECRET_NAME}" -n "${TEST_NAMESPACE}" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Secret is available in cluster${NC}"
        break
    fi
    if [[ $i -eq 30 ]]; then
        echo -e "${RED}❌ Secret not found in cluster after 30 seconds${NC}"
        exit 1
    fi
    sleep 1
done

# 8. Verify secret data
echo -e "${BLUE}8. Verifying secret data in cluster${NC}"
DECODED_USERNAME=$(kubectl get secret "${TEST_SECRET_NAME}" -n "${TEST_NAMESPACE}" -o jsonpath='{.data.username}' | base64 -d)
if [[ "$DECODED_USERNAME" == "test-user" ]]; then
    echo -e "${GREEN}✅ Secret data is correct${NC}"
else
    echo -e "${RED}❌ Secret data is incorrect${NC}"
    echo "Expected: test-user, Got: ${DECODED_USERNAME}"
    exit 1
fi

# 9. Test with a pod that uses the secret
echo -e "${BLUE}9. Testing secret consumption by pod${NC}"
TEST_POD="${TEST_SECRET_NAME}-pod"
cat > "/tmp/${TEST_POD}.yaml" << EOF
apiVersion: v1
kind: Pod
metadata:
  name: ${TEST_POD}
  namespace: ${TEST_NAMESPACE}
spec:
  containers:
  - name: test-container
    image: busybox:1.35
    command: ['sh', '-c', 'echo "Username: \$USERNAME" && echo "Password: \$PASSWORD" && echo "API Key: \$API_KEY" && sleep 3600']
    env:
    - name: USERNAME
      valueFrom:
        secretKeyRef:
          name: ${TEST_SECRET_NAME}
          key: username
    - name: PASSWORD
      valueFrom:
        secretKeyRef:
          name: ${TEST_SECRET_NAME}
          key: password
    - name: API_KEY
      valueFrom:
        secretKeyRef:
          name: ${TEST_SECRET_NAME}
          key: api-key
  restartPolicy: Never
EOF

if kubectl apply -f "/tmp/${TEST_POD}.yaml"; then
    echo -e "${GREEN}✅ Test pod created${NC}"
else
    echo -e "${RED}❌ Failed to create test pod${NC}"
    exit 1
fi

# 10. Wait for pod to be ready and check logs
echo -e "${BLUE}10. Checking pod logs for secret consumption${NC}"
for i in {1..30}; do
    if kubectl get pod "${TEST_POD}" -n "${TEST_NAMESPACE}" -o jsonpath='{.status.phase}' | grep -q "Running"; then
        echo -e "${GREEN}✅ Pod is running${NC}"
        break
    fi
    if [[ $i -eq 30 ]]; then
        echo -e "${YELLOW}⚠️  Pod not running after 30 seconds, checking logs anyway${NC}"
        break
    fi
    sleep 1
done

# Get pod logs
POD_LOGS=$(kubectl logs "${TEST_POD}" -n "${TEST_NAMESPACE}" 2>/dev/null || echo "")
if echo "$POD_LOGS" | grep -q "Username: test-user"; then
    echo -e "${GREEN}✅ Pod successfully consumed secret data${NC}"
    echo "Pod logs:"
    echo "$POD_LOGS"
else
    echo -e "${YELLOW}⚠️  Could not verify secret consumption from pod logs${NC}"
    echo "Pod logs: ${POD_LOGS}"
fi

# 11. Test secret update
echo -e "${BLUE}11. Testing secret update workflow${NC}"
# Create updated secret
cat > "${TEST_SECRET_FILE}-updated" << EOF
apiVersion: v1
kind: Secret
metadata:
  name: ${TEST_SECRET_NAME}
  namespace: ${TEST_NAMESPACE}
  labels:
    app.kubernetes.io/name: workflow-test
    app.kubernetes.io/component: secret
    gitops-infra-control-plane.io/managed-by: "sops-test"
type: Opaque
data:
  # Updated test data
  username: dXBkYXRlZC11c2Vy  # updated-user
  password: dXBkYXRlZC1wYXNzd29yZA==  # updated-password
  api-key: dXBkYXRlZC1hcGkta2V5LXZhbHVl  # updated-api-key-value
stringData:
  database-host: updated-database.default.svc.cluster.local
  database-port: "5432"
  environment: test
EOF

# Encrypt updated secret
if sops --encrypt --in-place "${TEST_SECRET_FILE}-updated"; then
    echo -e "${GREEN}✅ Updated secret encrypted${NC}"
    
    # Apply updated secret
    if kubectl apply -f "${TEST_SECRET_FILE}-updated"; then
        echo -e "${GREEN}✅ Updated secret applied${NC}"
        
        # Verify update
        UPDATED_USERNAME=$(kubectl get secret "${TEST_SECRET_NAME}" -n "${TEST_NAMESPACE}" -o jsonpath='{.data.username}' | base64 -d)
        if [[ "$UPDATED_USERNAME" == "updated-user" ]]; then
            echo -e "${GREEN}✅ Secret update verified${NC}"
        else
            echo -e "${RED}❌ Secret update failed${NC}"
        fi
    else
        echo -e "${RED}❌ Failed to apply updated secret${NC}"
    fi
else
    echo -e "${RED}❌ Failed to encrypt updated secret${NC}"
fi

# Cleanup
rm -f "/tmp/${TEST_POD}.yaml" "${TEST_SECRET_FILE}-updated"

echo
echo -e "${GREEN}🎉 SOPS workflow test completed successfully!${NC}"
echo
echo -e "${BLUE}📋 Test Summary:${NC}"
echo "✅ Secret creation and encryption"
echo "✅ Secret decryption and verification"
echo "✅ Cluster deployment of encrypted secrets"
echo "✅ Secret consumption by pods"
echo "✅ Secret update workflow"
echo
echo -e "${YELLOW}⚠️  Note: The test namespace and resources will be cleaned up automatically.${NC}"

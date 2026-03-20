#!/bin/bash

# Crossplane Migration Prerequisites Validation Script
# Phase 0 → Phase 1: Verify environment ready for migration

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
LOG_FILE="${PROJECT_ROOT}/docs/migration/phase1-validation-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "=========================================="
echo "Crossplane Migration Prerequisites Validation"
echo "=========================================="
echo "Log: ${LOG_FILE}"
echo ""

# Track results
PASSED=0
FAILED=0
WARNINGS=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

check_warn() {
    echo -e "${YELLOW}!${NC} $1"
    ((WARNINGS++))
}

check_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# 1. Check kubectl connectivity
echo ""
echo "## 1. Kubernetes Cluster Connectivity"
echo "-----------------------------------"

if ! command -v kubectl &> /dev/null; then
    check_fail "kubectl not found"
    exit 1
fi

if ! kubectl cluster-info &> /dev/null; then
    check_fail "Cannot connect to Kubernetes cluster"
    exit 1
fi

CLUSTER_NAME=$(kubectl cluster-info | head -1 | sed 's/.*is running at //' | sed 's/https:\/\///' | cut -d: -f1)
check_pass "Connected to cluster: ${CLUSTER_NAME}"

# Check if we're on the hub cluster
if kubectl get namespace crossplane-system &> /dev/null; then
    check_pass "Crossplane system namespace exists"
else
    check_fail "Crossplane system namespace not found"
fi

# 2. Check Crossplane Core Installation
echo ""
echo "## 2. Crossplane Core Installation"
echo "-----------------------------------"

if kubectl get deployment crossplane -n crossplane-system &> /dev/null; then
    check_pass "Crossplane core deployment exists"
    READY_PODS=$(kubectl get deployment crossplane -n crossplane-system -o jsonpath='{.status.readyReplicas}')
    DESIRED_PODS=$(kubectl get deployment crossplane -n crossplane-system -o jsonpath='{.spec.replicas}')
    if [[ "${READY_PODS}" -eq "${DESIRED_PODS}" ]]; then
        check_pass "Crossplane pods ready: ${READY_PODS}/${DESIRED_PODS}"
    else
        check_fail "Crossplane pods not ready: ${READY_PODS}/${DESIRED_PODS}"
    fi
else
    check_fail "Crossplane core deployment not found"
fi

# Check Crossplane version
CP_VERSION=$(kubectl get deployment crossplane -n crossplane-system -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null | sed 's/.*:\(.*\)/\1/' || echo "unknown")
check_info "Crossplane version: ${CP_VERSION}"

# 3. Check Providers
echo ""
echo "## 3. Cloud Providers"
echo "--------------------"

PROVIDERS=("provider-aws" "provider-azure" "provider-gcp" "provider-kubernetes")
PROVIDER_STATUS=()

for provider in "${PROVIDERS[@]}"; do
    if kubectl get provider "${provider}" -n crossplane-system &> /dev/null; then
        HEALTHY=$(kubectl get provider "${provider}" -n crossplane-system -o jsonpath='{.status.health.lastHealthyTime}')
        if [[ -n "${HEALTHY}" ]]; then
            check_pass "Provider ${provider} is HEALTHY"
            PROVIDER_STATUS["${provider}"]="HEALTHY"
        else
            check_fail "Provider ${provider} exists but not healthy"
            PROVIDER_STATUS["${provider}"]="UNHEALTHY"
        fi
    else
        check_fail "Provider ${provider} not installed"
        PROVIDER_STATUS["${provider}"]="MISSING"
    fi
done

# 4. Check ProviderConfigs
echo ""
echo "## 4. ProviderConfigs"
echo "--------------------"

PROVIDER_CONFIGS=("aws-provider" "azure-provider" "gcp-provider" "kubernetes-provider")

for pc in "${PROVIDER_CONFIGS[@]}"; do
    if kubectl get providerconfig "${pc}" -n crossplane-system &> /dev/null; then
        check_pass "ProviderConfig ${pc} exists"

        # Check credential source
        CRED_SOURCE=$(kubectl get providerconfig "${pc}" -n crossplane-system -o jsonpath='{.spec.credentials.source}')
        if [[ "${CRED_SOURCE}" == "InjectedIdentity" ]]; then
            check_pass "  Credentials: InjectedIdentity (Workload Identity / IRSA)"
        elif [[ "${CRED_SOURCE}" == "Secret" ]]; then
            SECRET_NAME=$(kubectl get providerconfig "${pc}" -n crossplane-system -o jsonpath='{.spec.credentials.secretRef.name}')
            check_info "  Credentials: Secret (${SECRET_NAME})"
        else
            check_warn "  Unknown credential source: ${CRED_SOURCE}"
        fi
    else
        check_fail "ProviderConfig ${pc} missing"
    fi
done

# 5. Check CRDs (Crossplane Resource Definitions)
echo ""
echo "## 5. Crossplane CRDs"
echo "--------------------"

# Check for essential XRD types
XRDS=(
    "xdatabases.platform.example.com"
    "xclusters.platform.example.com"
    "xnetworks.platform.example.com"
    "xqueues.platform.example.com"
)

for xrd in "${XRDS[@]}"; do
    if kubectl get crd "${xrd}" &> /dev/null; then
        check_pass "CRD ${xrd} exists"
    else
        check_warn "CRD ${xrd} not found (may be created later)"
    fi
done

# Check for provider managed resources
echo ""
echo "## 6. Provider Managed Resource CRDs"
echo "------------------------------------"

ESSENTIAL_CRDS=(
    "dbinstances.rds.aws.crossplane.io"
    "clusters.eks.aws.crossplane.io"
    "buckets.s3.aws.crossplane.io"
    "clusters.container.gcp.crossplane.io"
    "instances.sqladmin.gcp.crossplane.io"
    "flexibleservers.database.azure.crossplane.io"
    "managedclusters.azure.crossplane.io"
)

for crd in "${ESSENTIAL_CRDS[@]}"; do
    if kubectl get crd "${crd}" &> /dev/null; then
        check_pass "CRD ${crd}"
    else
        check_warn "CRD ${crd} missing (check provider installation)"
    fi
done

# 6. GitOps (Flux) Validation
echo ""
echo "## 7. GitOps Pipeline (Flux)"
echo "---------------------------"

if kubectl get namespace flux-system &> /dev/null; then
    check_pass "Flux system namespace exists"

    if kubectl get gitrepository -A &> /dev/null; then
        GITREPO_COUNT=$(kubectl get gitrepository -A --no-headers | wc -l | tr -d ' ')
        check_pass "Found ${GITREPO_COUNT} GitRepository(s)"
    else
        check_warn "No GitRepository resources found"
    fi

    if kubectl get kustomization -A &> /dev/null; then
        KUSTOMIZATION_COUNT=$(kubectl get kustomization -A --no-headers | wc -l | tr -d ' ')
        check_pass "Found ${KUSTOMIZATION_COUNT} Kustomization(s)"

        # Check specifically for crossplane kustomization
        if kubectl get kustomization crossplane -n flux-system &> /dev/null; then
            check_pass "Crossplane Kustomization exists in flux-system"
            SYNC_STATUS=$(kubectl get kustomization crossplane -n flux-system -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
            if [[ "${SYNC_STATUS}" == "True" ]]; then
                check_pass "Crossplane Kustomization is Ready"
            else
                check_warn "Crossplane Kustomization not Ready"
            fi
        else
            check_warn "Crossplane Kustomization not found in flux-system"
        fi
    else
        check_warn "No Kustomization resources found"
    fi
else
    check_warn "Flux not installed (will need to install or use alternative GitOps)"
fi

# 7. Repository Structure Check
echo ""
echo "## 8. Repository Structure"
echo "--------------------------"

REPO_DIRS=(
    "core/operators/control-plane/crossplane/xrds"
    "core/operators/control-plane/crossplane/compositions"
    "core/operators/control-plane/crossplane/providers"
)

for dir in "${REPO_DIRS[@]}"; do
    if [[ -d "${PROJECT_ROOT}/${dir}" ]]; then
        check_pass "Directory exists: ${dir}"
    else
        check_fail "Directory missing: ${dir}"
    fi
done

# Check for essential files
ESSENTIAL_FILES=(
    "core/operators/control-plane/crossplane/xrds/xnetwork.yaml"
    "core/operators/control-plane/crossplane/xrds/xdatabase.yaml"
    "core/operators/control-plane/crossplane/xrds/xcluster.yaml"
    "core/operators/control-plane/crossplane/compositions/network-aws.yaml"
    "core/operators/control-plane/crossplane/compositions/database-aws.yaml"
    "core/operators/control-plane/crossplane/compositions/cluster-eks.yaml"
    "core/operators/control-plane/crossplane/providers/provider-aws.yaml"
)

for file in "${ESSENTIAL_FILES[@]}"; do
    if [[ -f "${PROJECT_ROOT}/${file}" ]]; then
        check_pass "File exists: ${file}"
    else
        check_fail "File missing: ${file}"
    fi
done

# 8. Test Managed Resource Creation
echo ""
echo "## 9. Test Managed Resource Creation"
echo "-------------------------------------"

check_info "This will create a test S3 bucket to verify provider connectivity"
read -p "Do you want to run the test? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    TEST_BUCKET="crossplane-test-$(date +%s)-$(openssl rand -hex 4)"

    cat <<EOF | kubectl apply -f -
apiVersion: s3.aws.crossplane.io/v1beta1
kind: Bucket
metadata:
  name: ${TEST_BUCKET}
  namespace: crossplane-system
  annotations:
    "crossplane.io/external-name": "${TEST_BUCKET}"
spec:
  forProvider:
    locationConstraint: us-west-2
  providerConfigRef:
    name: aws-provider
EOF

    check_info "Test bucket created, waiting for reconciliation (30s)..."
    sleep 30

    if kubectl get bucket "${TEST_BUCKET}" -n crossplane-system -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null | grep -q "True"; then
        check_pass "Test bucket provisioned successfully"

        # Cleanup
        kubectl delete bucket "${TEST_BUCKET}" -n crossplane-system --wait=false
        check_info "Test bucket deleted (async)"
    else
        check_fail "Test bucket failed to provision"
        kubectl describe bucket "${TEST_BUCKET}" -n crossplane-system || true
        kubectl get bucket "${TEST_BUCKET}" -n crossplane-system -o yaml || true
    fi
else
    check_info "Skipped test managed resource creation"
fi

# 9. Multi-Cloud Orchestrator Check
echo ""
echo "## 10. Multi-Cloud Orchestrator"
echo "-------------------------------"

ORCHESTRATOR_SCRIPTS=(
    "core/ai/skills/provision-infrastructure/scripts/multi_cloud_orchestrator.py"
    "overlay/ai/skills/complete-hub-spoke-temporal/workflows/multi-cloud-scatter-gather.go"
    "core/multi-cloud-abstraction.js"
)

for script in "${ORCHESTRATOR_SCRIPTS[@]}"; do
    if [[ -f "${PROJECT_ROOT}/${script}" ]]; then
        check_pass "Orchestrator script exists: $(basename ${script})"
    else
        check_warn "Orchestrator script missing: $(basename ${script})"
    fi
done

# Check if orchestrator needs Crossplane integration
check_info "Multi-cloud orchestrators need to be updated to support Crossplane as an alternative to direct cloud SDKs"

# 10. Terraform State Backup Check
echo ""
echo "## 11. Terraform State Backup"
echo "-----------------------------"

TFSTATE_FILES=$(find "${PROJECT_ROOT}/core/infrastructure/terraform" -name "*.tfstate" 2>/dev/null || true)
if [[ -n "${TFSTATE_FILES}" ]]; then
    TFSTATE_COUNT=$(echo "${TFSTATE_FILES}" | wc -l | tr -d ' ')
    check_info "Found ${TFSTATE_COUNT} Terraform state file(s)"
    # Could check for backups, but that's manual
    check_warn "Ensure Terraform state is backed up before migration"
else
    check_warn "No Terraform state files found (unexpected?)"
fi

# Summary
echo ""
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"
echo -e "Warnings: ${YELLOW}${WARNINGS}${NC}"
echo ""

if [[ ${FAILED} -gt 0 ]]; then
    echo -e "${RED}❌ Validation failed. Address failures before proceeding.${NC}"
    exit 1
elif [[ ${WARNINGS} -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  Validation passed with warnings. Review warnings before proceeding.${NC}"
    exit 0
else
    echo -e "${GREEN}✅ All checks passed! Ready for Phase 1: Foundation & Provider Validation${NC}"
    exit 0
fi

#!/usr/bin/env bash
# =============================================================================
# Cloud AI Agent — Bootstrap Script
# Validates prerequisites, checks env config, and verifies the skill suite
# =============================================================================
set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

pass() { echo -e "  ${GREEN}✓${RESET} $*"; }
fail() { echo -e "  ${RED}✗${RESET} $*"; ERRORS=$((ERRORS + 1)); }
warn() { echo -e "  ${YELLOW}!${RESET} $*"; WARNINGS=$((WARNINGS + 1)); }
info() { echo -e "  ${CYAN}→${RESET} $*"; }

ERRORS=0
WARNINGS=0
SKILL_DIR="${SKILL_DIR:-./.agents/skills}"
REQUIRED_SKILLS=(
  terraform-provisioning       cicd-pipeline-monitor
  incident-triage-runbook      tenant-lifecycle-manager
  compliance-security-scanner  sla-monitoring-alerting
  deployment-validation        kpi-report-generator
  runbook-documentation-gen    stakeholder-comms-drafter
  kubernetes-cluster-manager   cost-optimisation
  secrets-certificate-manager  workload-migration
  policy-as-code               capacity-planning
  observability-stack          orchestrator
  multi-cloud-networking       database-operations
  disaster-recovery            gitops-workflow
  service-mesh                 container-registry
  developer-self-service       audit-siem
  change-management            chaos-load-testing
)

# ── Header ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║   Cloud AI Agent — Bootstrap & Validation     ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${RESET}"
echo ""

# ── 1. Skill Suite Integrity ──────────────────────────────────────────────────
echo -e "${BOLD}[1/6] Validating skill suite (${#REQUIRED_SKILLS[@]} skills expected)${RESET}"

FOUND=0; MISSING=0
for skill in "${REQUIRED_SKILLS[@]}"; do
  if [[ -f "${SKILL_DIR}/${skill}/SKILL.md" ]]; then
    FOUND=$((FOUND + 1))
  else
    fail "Missing skill: ${skill}"
    MISSING=$((MISSING + 1))
  fi
done

if [[ $MISSING -eq 0 ]]; then
  pass "All ${FOUND} skills present"
else
  fail "${MISSING} skills missing — run from the .agents/skills parent directory"
fi

# Verify CLAUDE.md exists
[[ -f "CLAUDE.md" ]] && pass "CLAUDE.md found" || warn "CLAUDE.md not found — agent context will be limited"

echo ""

# ── 2. CLI Tools ──────────────────────────────────────────────────────────────
echo -e "${BOLD}[2/6] Checking required CLI tools${RESET}"

check_tool() {
  local tool=$1 min_version=$2 version_flag="${3:---version}"
  if command -v "$tool" &>/dev/null; then
    local ver
    ver=$("$tool" $version_flag 2>&1 | head -1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1)
    pass "${tool} ${ver}"
  else
    fail "${tool} not found (required)"
  fi
}

check_tool_optional() {
  local tool=$1
  if command -v "$tool" &>/dev/null; then
    pass "${tool} available"
  else
    warn "${tool} not found (optional — some skills will have limited functionality)"
  fi
}

# Required
check_tool "az"         "2.50"
check_tool "kubectl"    "1.28"
check_tool "helm"       "3.12"
check_tool "terraform"  "1.6"
check_tool "jq"         "1.6"
check_tool "yq"         "4.0"

# Optional but recommended
check_tool_optional "argocd"
check_tool_optional "flux"
check_tool_optional "istioctl"
check_tool_optional "notation"
check_tool_optional "trivy"
check_tool_optional "k6"
check_tool_optional "linkerd"
check_tool_optional "checkov"

echo ""

# ── 3. Azure Authentication ───────────────────────────────────────────────────
echo -e "${BOLD}[3/6] Checking Azure authentication & subscription${RESET}"

if az account show &>/dev/null; then
  SUB_NAME=$(az account show --query name -o tsv 2>/dev/null)
  SUB_ID=$(az account show --query id -o tsv 2>/dev/null)
  TENANT=$(az account show --query tenantId -o tsv 2>/dev/null)
  pass "Logged in — Subscription: ${SUB_NAME} (${SUB_ID})"
  info "Azure AD Tenant: ${TENANT}"
else
  fail "Not logged in to Azure — run: az login"
fi

echo ""

# ── 4. Environment Variables ──────────────────────────────────────────────────
echo -e "${BOLD}[4/6] Checking required environment variables${RESET}"

check_env() {
  local var=$1 required=${2:-true}
  if [[ -n "${!var:-}" ]]; then
    # Mask secrets — show only first 6 chars
    local val="${!var}"
    if [[ "$var" =~ (SECRET|PASSWORD|KEY|TOKEN|PSK) ]]; then
      val="${val:0:6}***"
    fi
    pass "${var}=${val}"
  elif [[ "$required" == "true" ]]; then
    fail "${var} not set (required)"
  else
    warn "${var} not set (optional)"
  fi
}

# Azure
check_env "AZURE_SUBSCRIPTION_ID"
check_env "AZURE_TENANT_ID"

# Kubernetes
check_env "KUBECONFIG" "false"

# Observability
check_env "PROMETHEUS_URL" "false"
check_env "GRAFANA_URL"    "false"
check_env "GRAFANA_TOKEN"  "false"

# GitOps
check_env "ARGOCD_URL"     "false"
check_env "ARGOCD_TOKEN"   "false"
check_env "GITHUB_ORG"     "false"
check_env "GITHUB_TOKEN"   "false"

# Notifications
check_env "SLACK_WEBHOOK"  "false"
check_env "PD_API_KEY"     "false"

# Platform resources
check_env "ACR_NAME"       "false"
check_env "KEY_VAULT_NAME" "false"
check_env "LAW_ID"         "false"
check_env "HUB_RG"         "false"
check_env "REGION"         "false"

echo ""

# ── 5. Kubernetes Context ─────────────────────────────────────────────────────
echo -e "${BOLD}[5/6] Checking Kubernetes access${RESET}"

if command -v kubectl &>/dev/null; then
  CONTEXT=$(kubectl config current-context 2>/dev/null || echo "none")
  if [[ "$CONTEXT" != "none" ]]; then
    pass "Current context: ${CONTEXT}"
    if kubectl auth can-i get pods -n kube-system &>/dev/null; then
      pass "Cluster API reachable"
      NODE_COUNT=$(kubectl get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')
      info "Nodes in current cluster: ${NODE_COUNT}"
    else
      warn "Cannot reach cluster API (offline or no auth?)"
    fi
  else
    warn "No kubectl context set"
  fi
else
  warn "kubectl not found — K8s skills will not function"
fi

echo ""

# ── 6. Quick Smoke Test ───────────────────────────────────────────────────────
echo -e "${BOLD}[6/6] Running skill smoke tests${RESET}"

# Test terraform-provisioning skill is parseable
if command -v terraform &>/dev/null; then
  if terraform version &>/dev/null; then
    pass "terraform-provisioning: CLI functional"
  fi
fi

# Test argocd connectivity if configured
if [[ -n "${ARGOCD_URL:-}" ]] && command -v argocd &>/dev/null; then
  if argocd app list &>/dev/null 2>&1; then
    APP_COUNT=$(argocd app list -o json 2>/dev/null | jq length)
    pass "gitops-workflow: ArgoCD reachable (${APP_COUNT} apps)"
  else
    warn "gitops-workflow: ArgoCD URL set but not reachable"
  fi
fi

# Test prometheus if configured
if [[ -n "${PROMETHEUS_URL:-}" ]]; then
  HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" \
    "${PROMETHEUS_URL}/api/v1/query?query=up" 2>/dev/null || echo "000")
  if [[ "$HTTP_CODE" == "200" ]]; then
    pass "observability-stack: Prometheus reachable"
  else
    warn "observability-stack: Prometheus at ${PROMETHEUS_URL} returned HTTP ${HTTP_CODE}"
  fi
fi

# Test Azure CLI skills
if az account show &>/dev/null; then
  RESOURCE_GROUPS=$(az group list --query "length(@)" -o tsv 2>/dev/null || echo "?")
  pass "terraform-provisioning/kubernetes-cluster-manager: Azure CLI functional (${RESOURCE_GROUPS} RGs visible)"
fi

echo ""

# ── Summary ───────────────────────────────────────────────────────────────────
echo -e "${BOLD}══════════════════════════════════════════════════════════${RESET}"
if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
  echo -e "${GREEN}${BOLD}  ✓ Bootstrap PASSED — all checks clean${RESET}"
  echo -e "${GREEN}  Agent is ready to operate.${RESET}"
elif [[ $ERRORS -eq 0 ]]; then
  echo -e "${YELLOW}${BOLD}  ⚠ Bootstrap PASSED with ${WARNINGS} warning(s)${RESET}"
  echo -e "${YELLOW}  Agent will operate in degraded mode for optional components.${RESET}"
else
  echo -e "${RED}${BOLD}  ✗ Bootstrap FAILED — ${ERRORS} error(s), ${WARNINGS} warning(s)${RESET}"
  echo -e "${RED}  Fix the errors above before operating the agent.${RESET}"
  echo ""
  echo -e "  ${CYAN}Quick fixes:${RESET}"
  echo -e "    az login                             # Fix Azure auth"
  echo -e "    brew install kubectl helm terraform  # macOS CLI tools"
  echo -e "    export AZURE_SUBSCRIPTION_ID=\$(az account show --query id -o tsv)"
fi
echo -e "${BOLD}══════════════════════════════════════════════════════════${RESET}"
echo ""

exit $ERRORS

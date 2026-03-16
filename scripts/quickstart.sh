#!/usr/bin/env bash
# =============================================================================
# Quickstart - MVP GitOps Infrastructure (One-Command Setup)
# =============================================================================
set -euo pipefail

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

pass() { echo -e "  ${GREEN}✓${RESET} $*"; }
fail() { echo -e "  ${RED}✗${RESET} $*"; exit 1; }
warn() { echo -e "  ${YELLOW}!${RESET} $*"; }
info() { echo -e "  ${CYAN}→${RESET} $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${SCRIPT_DIR}/helpers/wsl-detect.sh"
ensure_wsl_sanity "quickstart.sh" warn info

LOG_DIR="${SCRIPT_DIR}/../logs/quickstart"
START_TIME="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

mkdir -p "$LOG_DIR"
SUMMARY_FILE="$LOG_DIR/summary-$(date -u +"%Y%m%dT%H%M%SZ").json"

timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --help)
      cat <<EOF
Usage: $0

One-command MVP GitOps infrastructure setup with AI agents.

Deploys complete GitOps infrastructure and AI agents ecosystem with dashboard.
EOF
      exit 0
      ;;
    *)
      fail "Unknown option: $1. Use --help for usage."
      ;;
  esac
done

# MVP Setup Steps
run_step() {
  local step_name="$1"
  local step_command="$2"
  local log_file="$LOG_DIR/${step_name}.log"
  
  echo
  echo -e "${BOLD}Step: $step_name${RESET}"
  echo "Command: $step_command"
  echo "Log: $log_file"
  echo
  
  if eval "$step_command" 2>&1 | tee "$log_file"; then
    pass "$step_name completed successfully"
    return 0
  else
    fail "$step_name failed. Check $log_file for details"
  fi
}

# Main execution
main() {
  echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${RESET}"
  echo -e "${BOLD}║   GitOps Infra Control Plane — Quickstart (One Command)  ║${RESET}"
  echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${RESET}"
  echo
  echo "Start Time: $START_TIME"
  echo "Log Directory: $LOG_DIR"
  echo
  
  # Step 1: Prerequisites
  run_step "prerequisites" "${SCRIPT_DIR}/prerequisites.sh"
  
  # Step 2: GitOps Configuration
  run_step "gitops-config" "${SCRIPT_DIR}/setup-gitops-config.sh"
  
  # Step 3: Bootstrap Cluster (recovery anchor)
  run_step "bootstrap-cluster" "${SCRIPT_DIR}/create-bootstrap-cluster.sh"
  
  # Step 4: Hub Cluster (GitOps control plane)
  run_step "hub-cluster" "${SCRIPT_DIR}/create-hub-cluster.sh --provider kind --bootstrap-kubeconfig ${ROOT_DIR}/bootstrap-kubeconfig"
  
  # Step 5: Install Crossplane on hub
  run_step "install-crossplane" "${SCRIPT_DIR}/install-crossplane.sh --providers local"
  
  # Step 6: Create Spoke Clusters
  run_step "spoke-cluster" "${SCRIPT_DIR}/create-spoke-clusters.sh"
  
  # Step 7: Deploy AI Agents Ecosystem
  run_step "ai-agents-ecosystem" "${SCRIPT_DIR}/deploy-ai-agents-ecosystem.sh"
  
  # Summary
  echo
  echo -e "${BOLD}Quickstart Complete!${RESET}"
  echo "=================="
  
  if [[ true ]]; then
    echo "Your GitOps infrastructure is ready:"
    echo
    echo "Next steps:"
    echo "  1. Check cluster status:"
    echo "     export KUBECONFIG=\${SCRIPT_DIR}/../hub-kubeconfig"
    echo "     kubectl get clusters -n gitops-system"
    echo
    echo "  2. Check Flux:"
    echo "     kubectl get pods -n flux-system"
    echo
    echo "  3. Check Crossplane:"
    echo "     kubectl get providers -n crossplane-system"
    echo
    echo "  4. Access your spoke cluster:"
    echo "     export KUBECONFIG=\${SCRIPT_DIR}/../gitops-spoke-local-kubeconfig"
    echo "     kubectl get nodes"
    echo
    echo "  5. Access AI Agents Dashboard:"
    echo "     kubectl port-forward -n ai-infrastructure svc/agent-dashboard-service 8080:80"
    echo "     open http://localhost:8080"
    echo
    echo "  6. Access Temporal Workflow UI:"
    echo "     kubectl port-forward -n ai-infrastructure svc/temporal-frontend 7233:7233"
    echo "     open http://localhost:7233"
    echo
    echo "Logs available in: $LOG_DIR"
    echo "Summary saved to: $SUMMARY_FILE"
  fi
  
  # Create summary JSON
  cat > "$SUMMARY_FILE" <<EOF
{
  "start_time": "$START_TIME",
  "end_time": "$(timestamp)",
  "status": "success",
  "log_directory": "$LOG_DIR",
  "steps": [
    "prerequisites",
    "gitops-config",
    "bootstrap-cluster",
    "hub-cluster",
    "install-crossplane",
    "spoke-cluster",
    "ai-agents-ecosystem"
  ]
}
EOF
  
  echo -e "${GREEN}${BOLD}Quickstart GitOps infrastructure with AI agents deployed successfully!${RESET}"
}

# Run main function
main "$@"

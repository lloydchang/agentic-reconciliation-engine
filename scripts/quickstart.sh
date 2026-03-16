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
source "${SCRIPT_DIR}/helpers/wsl-detect.sh"
ensure_wsl_sanity "quickstart.sh" warn info

LOG_DIR="${SCRIPT_DIR}/../logs/quickstart"
START_TIME="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

mkdir -p "$LOG_DIR"
SUMMARY_FILE="$LOG_DIR/summary-$(date -u +"%Y%m%dT%H%M%SZ").json"

timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

# Parse arguments
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --help)
      cat <<EOF
Usage: $0 [options]

One-command MVP GitOps infrastructure setup.

Options:
  --dry-run           Show commands without executing
  --help              Show this help

Examples:
  $0                  # Full MVP setup
  $0 --dry-run        # Preview commands
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
  
  if [[ "$DRY_RUN" == "true" ]]; then
    info "[DRY RUN] Would run: $step_command"
    return 0
  fi
  
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
  echo -e "${BOLD}║   GitOps Infra Control Plane — Quickstart (One Command)     ║${RESET}"
  echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${RESET}"
  echo
  echo "Start Time: $START_TIME"
  echo "Log Directory: $LOG_DIR"
  echo
  
  # Step 1: Prerequisites
  run_step "prerequisites" "./scripts/prerequisites.sh"
  
  # Step 2: GitOps Configuration
  run_step "gitops-config" "./scripts/setup-gitops-config.sh"
  
  # Step 3: Bootstrap Cluster (required for recovery)
  run_step "bootstrap-cluster" "./scripts/create-bootstrap-cluster.sh"
  
  # Step 4: Hub Cluster (required for spokes)
  run_step "hub-cluster" "./scripts/create-hub-cluster.sh --provider local"
  
  # Step 5: Spoke Cluster
  if [[ "$SKIP_SPOKE" != "true" ]]; then
    run_step "spoke-cluster" "./scripts/create-spoke-clusters.sh"
  else
    warn "Skipping spoke cluster creation"
  fi
  
  # Summary
  echo
  echo -e "${BOLD}Quickstart Complete!${RESET}"
  echo "=================="
  
  if [[ "$DRY_RUN" != "true" ]]; then
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
    echo "Logs available in: $LOG_DIR"
    echo "Summary saved to: $SUMMARY_FILE"
  fi
  
  # Create summary JSON
  cat > "$SUMMARY_FILE" <<EOF
{
  "start_time": "$START_TIME",
  "end_time": "$(timestamp)",
  "status": "success",
  "skip_bootstrap": $SKIP_BOOTSTRAP,
  "skip_hub": $SKIP_HUB,
  "skip_spoke": $SKIP_SPOKE,
  "dry_run": $DRY_RUN,
  "log_directory": "$LOG_DIR",
  "steps": [
    "prerequisites",
    "gitops-config",
    "bootstrap-cluster",
    "hub-cluster",
    "spoke-cluster"
  ]
}
EOF
  
  echo -e "${GREEN}${BOLD}Quickstart GitOps infrastructure deployed successfully!${RESET}"
}

# Run main function
main "$@"

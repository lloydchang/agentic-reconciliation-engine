#!/usr/bin/env bash
# Helper to drive a fully automated local configuration setup using the migration wizard.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
source "${SCRIPT_DIR}/helpers/wsl-detect.sh"
ensure_wsl_sanity "$SCRIPT_NAME"

ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs/local-automation"
START_TIME="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

CONNECTOR_DEFAULT="local"
OVERLAY_DEFAULT=("./bootstrap" "./hub" "./emulator-azure" "./spoke-local")
EMULATOR_ACTION_DEFAULT="enable"
HELPERS_DEFAULT=("core/automation/scripts/enable-cloud.sh" "core/automation/scripts/export-argocd-state.sh")
CI_GATE_COMMAND=""
# Add required repo URL - for local development, use current directory
REPO_URL_DEFAULT="file://$(pwd)"

CONNECTOR="$CONNECTOR_DEFAULT"
EMULATOR_ACTION="$EMULATOR_ACTION_DEFAULT"
OVERLAY_ORDER=("${OVERLAY_DEFAULT[@]}")
HELPERS=("${HELPERS_DEFAULT[@]}")
REPO_URL="$REPO_URL_DEFAULT"

mkdir -p "$LOG_DIR"
SUMMARY_FILE="$LOG_DIR/summary-$(date -u +"%Y%m%dT%H%M%SZ").json"

timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
usage() {
  cat <<USAGE
Usage: setup-gitops-config.sh [options]

A local configuration setup script that:
1. Runs prerequisites.sh to validate prerequisites
2. Invokes the migration wizard to configure GitOps overlays
3. Generates configuration files and summary logs

The cloud provider is automatically determined from:
- The connector (azure-devops→azure, github→aws, gitlab→gcp)
- Or the overlay order if no connector match
- Defaults to 'azure' for backward compatibility

Required Environment Variables (depend on connector):
  - GitHub: GITHUB_ENTERPRISE_TOKEN, GITHUB_ENTERPRISE_HOST (for enterprise)
  - Azure DevOps: AZURE_DEVOPS_TOKEN, AZURE_DEVOPS_ORG, AZURE_DEVOPS_PROJECT
  - GitLab: GITLAB_TOKEN, GITLAB_HOST
  - Bitbucket: BITBUCKET_USER, BITBUCKET_TOKEN (cloud) or BITBUCKET_DC_* (data center)

Options:
  --connector <name>             Git host connector (default: $CONNECTOR_DEFAULT)
                                Supported: github, azure-devops, gitlab, bitbucket-dc, bitbucket-cloud, codecommit, gcp-ssm, local
  --repo-url <url>              Git repository URL (default: $REPO_URL_DEFAULT)
  --emulator-action <action>     Toggle action for the Azure emulator (enable|disable, default: $EMULATOR_ACTION_DEFAULT)
  --overlay-order <comma-list>   Comma-separated overlay order (default: ${OVERLAY_DEFAULT[*]})
  --help                         Show this message

Example:
  # For Azure DevOps
  export AZURE_DEVOPS_TOKEN="your-token"
  export AZURE_DEVOPS_ORG="your-org" 
  export AZURE_DEVOPS_PROJECT="your-project"
  setup-gitops-config.sh --connector azure-devops --repo-url https://dev.azure.com/your-org/your-project/_git/your-repo

  # For GitHub with AWS
  export GITHUB_ENTERPRISE_TOKEN="your-token"
  setup-gitops-config.sh --connector github-enterprise-cloud --repo-url https://github.com/your-org/your-repo

  # For local development
  setup-gitops-config.sh --connector local --emulator-action enable
USAGE
}

parse_overlay_order() {
  local raw="$1"
  IFS=',' read -ra entries <<< "$raw"
  OVERLAY_ORDER=()
  for entry in "${entries[@]}"; do
    entry="${entry#"${entry%%[![:space:]]*}"}"
    entry="${entry%"${entry##*[![:space:]]}"}"
    [[ -n "$entry" ]] && OVERLAY_ORDER+=("$entry")
  done
  if [[ ${#OVERLAY_ORDER[@]} -eq 0 ]]; then
    OVERLAY_ORDER=("${OVERLAY_DEFAULT[@]}")
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --connector)
      CONNECTOR="$2"
      shift 2
      ;;
    --repo-url)
      REPO_URL="$2"
      shift 2
      ;;
    --emulator-action)
      EMULATOR_ACTION="$2"
      shift 2
      ;;
    --overlay-order)
      parse_overlay_order "$2"
      shift 2
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

run_bootstrap() {
  echo "$(timestamp) - Running prerequisites.sh" | tee "$LOG_DIR/prerequisites.sh.log"
  "${SCRIPT_DIR}/prerequisites.sh" 2>&1 | tee -a "$LOG_DIR/prerequisites.sh.log"
}

# Determine the provider from connector or overlay order
get_provider() {
  local provider="azure"  # default for backward compatibility
  
  # Try to derive from connector
  case "$CONNECTOR" in
    "azure-devops") provider="azure" ;;
    "github"|"github-enterprise-server"|"github-enterprise-cloud") provider="aws" ;;
    "gitlab") provider="gcp" ;;
    *) 
      # Try to derive from overlay order
      for overlay in "${OVERLAY_ORDER[@]}"; do
        case "$overlay" in
          *"azure"*) provider="azure"; break ;;
          *"aws"*) provider="aws"; break ;;
          *"gcp"*) provider="gcp"; break ;;
        esac
      done
      ;;
  esac
  echo "$provider"
}

run_wizard() {
  local provider=$(get_provider)
  local command=("python" "${SCRIPT_DIR}/migration_wizard.py" "--repo-url" "$REPO_URL")
  command+=("--connector" "$CONNECTOR")
  command+=("--provider" "$provider")
  command+=("--overlay-order" "${OVERLAY_ORDER[@]}")
  command+=("--helper-script" "${HELPERS[@]}")
  command+=("--emulator" "$EMULATOR_ACTION")
  command+=("--ci-gate" "$CI_GATE_COMMAND")

  echo "$(timestamp) - Invoking migration wizard with repo URL: $REPO_URL (provider: $provider)" | tee "$LOG_DIR/migration-wizard.log"
  "${command[@]}" 2>&1 | tee -a "$LOG_DIR/migration-wizard.log"
}

generate_summary() {
  local exit_code="$1"
  python - "$SUMMARY_FILE" <<PY
import json, os, pathlib, sys
summary_path = pathlib.Path(sys.argv[1])
data = {
    "start_time": os.environ["START_TIME"],
    "end_time": os.environ["END_TIME"],
    "status": os.environ["STATUS"],
    "exit_code": int(os.environ["EXIT_CODE"]),
    "connector": os.environ["CONNECTOR"],
    "repo_url": os.environ["REPO_URL"],
    "provider": os.environ["PROVIDER"],
    "emulator_action": os.environ["EMULATOR_ACTION"],
    "overlay_order": os.environ["SUMMARY_OVERLAYS"].splitlines(),
    "helpers": os.environ["SUMMARY_HELPERS"].splitlines(),
    "ci_gate": os.environ["CI_GATE_COMMAND"],
    "logs": {
        "bootstrap": os.environ["LOG_DIR"] + "/prerequisites.sh.log",
        "wizard": os.environ["LOG_DIR"] + "/migration-wizard.log"
    }
}
summary_path.write_text(json.dumps(data, indent=2))
print(f"[automation] Summary saved to {summary_path}")
PY
}

trap_handler() {
  local exit_code="$1"
  local status_text="success"
  [[ "$exit_code" -ne 0 ]] && status_text="failure"
  export START_TIME
  export END_TIME="$(timestamp)"
  export STATUS="$status_text"
  export EXIT_CODE="$exit_code"
  export CONNECTOR
  export REPO_URL
  export PROVIDER="$(get_provider)"
  export EMULATOR_ACTION
  export LOG_DIR
  export SUMMARY_OVERLAYS="$(printf '%s\n' "${OVERLAY_ORDER[@]}")"
  export SUMMARY_HELPERS="$(printf '%s\n' "${HELPERS[@]}")"
  export CI_GATE_COMMAND
  generate_summary "$exit_code"
  ln -sf "$SUMMARY_FILE" "$LOG_DIR/latest-summary.json"
}

trap 'trap_handler $?' EXIT

main() {
  echo "$(timestamp) - Starting zero-touch local automation" > "$LOG_DIR/run-local-automation.log"
  run_bootstrap
  run_wizard
  echo "$(timestamp) - Run complete" >> "$LOG_DIR/run-local-automation.log"
  echo "Logs stored under $LOG_DIR"
}

main

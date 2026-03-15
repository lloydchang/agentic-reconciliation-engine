#!/usr/bin/env bash
# Helper to drive a fully automated, zero-touch local run using the migration wizard.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs/local-automation"
SCRIPT_NAME="$(basename "$0")"
START_TIME="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

CONNECTOR_DEFAULT="github"
OVERLAY_DEFAULT=("./bootstrap" "./hub" "./emulator-azure" "./spoke-local")
EMULATOR_ACTION_DEFAULT="enable"
HELPERS_DEFAULT=("scripts/enable-cloud.sh" "scripts/export-argocd-state.sh")
CI_GATE_COMMAND="./scripts/local-ci-gate.sh"

CONNECTOR="$CONNECTOR_DEFAULT"
EMULATOR_ACTION="$EMULATOR_ACTION_DEFAULT"
OVERLAY_ORDER=("${OVERLAY_DEFAULT[@]}")
HELPERS=("${HELPERS_DEFAULT[@]}")

mkdir -p "$LOG_DIR"
SUMMARY_FILE="$LOG_DIR/summary-$(date -u +"%Y%m%dT%H%M%SZ").json"

timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
usage() {
  cat <<USAGE
Usage: $SCRIPT_NAME [options]

Options:
  --connector <name>             Git host connector (default: $CONNECTOR_DEFAULT)
  --emulator-action <action>     Toggle action for the Azure emulator (enable|disable, default: $EMULATOR_ACTION_DEFAULT)
  --overlay-order <comma-list>   Comma-separated overlay order (default: ${OVERLAY_DEFAULT[*]})
  --help                         Show this message
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
  echo "$(timestamp) - Running scripts/bootstrap.sh" | tee "$LOG_DIR/bootstrap.log"
  scripts/bootstrap.sh 2>&1 | tee -a "$LOG_DIR/bootstrap.log"
}

run_wizard() {
  local command=("python" "scripts/migration_wizard.py" "--connector" "$CONNECTOR")
  command+=("--overlay-order" "${OVERLAY_ORDER[@]}")
  command+=("--helper-script" "${HELPERS[@]}")
  command+=("--emulator" "$EMULATOR_ACTION")
  command+=("--ci-gate" "$CI_GATE_COMMAND")

  echo "$(timestamp) - Invoking migration wizard" | tee "$LOG_DIR/migration-wizard.log"
  "${command[@]}" 2>&1 | tee -a "$LOG_DIR/migration-wizard.log"
}

generate_summary() {
  local exit_code="$1"
  python - "$SUMMARY_FILE" <<PY
import json, os, pathlib
summary_path = pathlib.Path(sys.argv[1])
data = {
    "start_time": os.environ["START_TIME"],
    "end_time": os.environ["END_TIME"],
    "status": os.environ["STATUS"],
    "exit_code": int(os.environ["EXIT_CODE"]),
    "connector": os.environ["CONNECTOR"],
    "emulator_action": os.environ["EMULATOR_ACTION"],
    "overlay_order": os.environ["SUMMARY_OVERLAYS"].splitlines(),
    "helpers": os.environ["SUMMARY_HELPERS"].splitlines(),
    "ci_gate": os.environ["CI_GATE_COMMAND"],
    "logs": {
        "bootstrap": os.environ["LOG_DIR"] + "/bootstrap.log",
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

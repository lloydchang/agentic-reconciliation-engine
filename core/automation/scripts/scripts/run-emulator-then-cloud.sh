#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
source "${SCRIPT_DIR}/helpers/wsl-detect.sh"
ensure_wsl_sanity "$SCRIPT_NAME"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <wizard-args...>"
  echo "Pass the arguments you would normally send to core/core/automation/ci-cd/scripts/migration_wizard.py."
  exit 1
fi

ARGS=("$@")

echo "Phase 1: run with local emulator enabled."
./core/core/automation/ci-cd/scripts/migration_wizard.py "${ARGS[@]}" --emulator=enable

echo "Phase 2: run with emulator disabled (real cloud takes over)."
./core/core/automation/ci-cd/scripts/migration_wizard.py "${ARGS[@]}" --emulator=disable

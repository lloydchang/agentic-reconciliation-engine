#!/bin/bash
# run-local-automation.sh - Wrapper script for local automation execution
#
# This script executes bootstrap checks, migration wizard, and CI gate
# without interactive steps. It wraps the quickstart.sh script with
# additional logging and summary generation.
#
# Usage:
#   ./run-local-automation.sh [--connector CONNECTOR] [--overlay-order ORDER] [--emulator-action ACTION]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/../../logs/local-core/automation/ci-cd"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Default values
CONNECTOR="${CONNECTOR:-github}"
OVERLAY_ORDER="${OVERLAY_ORDER:-./bootstrap,./hub,./emulator-azure,./spoke-local}"
EMULATOR_ACTION="${EMULATOR_ACTION:-enable}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --connector)
            CONNECTOR="$2"
            shift 2
            ;;
        --overlay-order)
            OVERLAY_ORDER="$2"
            shift 2
            ;;
        --emulator-action)
            EMULATOR_ACTION="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --connector CONNECTOR       Git connector (github, azure-devops, gitlab, bitbucket)"
            echo "  --overlay-order ORDER       Comma-separated overlay order"
            echo "  --emulator-action ACTION    Emulator action (enable, disable)"
            echo "  --help, -h                  Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Log file paths
LOG_FILE="${LOG_DIR}/run-local-automation-${TIMESTAMP}.log"
SUMMARY_FILE="${LOG_DIR}/summary-${TIMESTAMP}.json"

echo "=== Local Automation Runner ===" | tee -a "${LOG_FILE}"
echo "Timestamp: ${TIMESTAMP}" | tee -a "${LOG_FILE}"
echo "Connector: ${CONNECTOR}" | tee -a "${LOG_FILE}"
echo "Overlay Order: ${OVERLAY_ORDER}" | tee -a "${LOG_FILE}"
echo "Emulator Action: ${EMULATOR_ACTION}" | tee -a "${LOG_FILE}"
echo "" | tee -a "${LOG_FILE}"

# Record start time
START_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Run prerequisites
echo "Running prerequisites check..." | tee -a "${LOG_FILE}"
if "${SCRIPT_DIR}/prerequisites.sh" >> "${LOG_FILE}" 2>&1; then
    echo "✓ Prerequisites passed" | tee -a "${LOG_FILE}"
else
    echo "✗ Prerequisites failed" | tee -a "${LOG_FILE}"
    EXIT_CODE=1
fi

# Run quickstart with specified parameters
echo "" | tee -a "${LOG_FILE}"
echo "Running quickstart automation..." | tee -a "${LOG_FILE}"
if "${SCRIPT_DIR}/quickstart.sh" \
    --connector "${CONNECTOR}" \
    --overlay-order "${OVERLAY_ORDER}" \
    --emulator-action "${EMULATOR_ACTION}" >> "${LOG_FILE}" 2>&1; then
    echo "✓ Quickstart completed successfully" | tee -a "${LOG_FILE}"
    CI_STATUS="success"
    EXIT_CODE=${EXIT_CODE:-0}
else
    echo "✗ Quickstart failed" | tee -a "${LOG_FILE}"
    CI_STATUS="failure"
    EXIT_CODE=${EXIT_CODE:-1}
fi

# Record end time
END_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Generate summary JSON
cat > "${SUMMARY_FILE}" << EOF
{
  "timestamp": "${TIMESTAMP}",
  "start_time": "${START_TIME}",
  "end_time": "${END_TIME}",
  "connector": "${CONNECTOR}",
  "overlay_order": "${OVERLAY_ORDER}",
  "emulator_action": "${EMULATOR_ACTION}",
  "ci_status": "${CI_STATUS}",
  "log_file": "$(basename "${LOG_FILE}")",
  "scripts": {
    "prerequisites": "core/scripts/automation/prerequisites.sh",
    "quickstart": "core/scripts/automation/quickstart.sh"
  }
}
EOF

# Create latest summary symlink/copy
cp "${SUMMARY_FILE}" "${LOG_DIR}/latest-summary.json"

# Generate markdown summary
"${SCRIPT_DIR}/publish-summary.sh" "${SUMMARY_FILE}" 2>/dev/null || true

echo "" | tee -a "${LOG_FILE}"
echo "=== Summary ===" | tee -a "${LOG_FILE}"
echo "Status: ${CI_STATUS}" | tee -a "${LOG_FILE}"
echo "Log: ${LOG_FILE}" | tee -a "${LOG_FILE}"
echo "Summary: ${SUMMARY_FILE}" | tee -a "${LOG_FILE}"

exit ${EXIT_CODE:-0}

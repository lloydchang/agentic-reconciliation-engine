#!/usr/bin/env bash
# Publish the zero-touch summary to an external endpoint and optionally notify on failure.
set -euo pipefail
cd $(dirname $0)

SUMMARY_PATH="${1:-logs/local-automation/latest-summary.json}"

if [[ ! -f "$SUMMARY_PATH" ]]; then
  echo "[publish-summary] Summary file not found at $SUMMARY_PATH"
  exit 1
fi

SUMMARY_ENDPOINT="${SUMMARY_ENDPOINT:-}"
SUMMARY_TOKEN="${SUMMARY_TOKEN:-}"
NOTIFY_WEBHOOK="${NOTIFY_WEBHOOK:-}"

pprint() {
  local key="$1"
  local value="$2"
  echo "[publish-summary] $key: $value"
}

if [[ -n "$SUMMARY_ENDPOINT" ]]; then
  pprint "Publishing summary" "$SUMMARY_PATH → $SUMMARY_ENDPOINT"
  if [[ -n "$SUMMARY_TOKEN" ]]; then
    curl -sSf -H "Content-Type: application/json" -H "Authorization: Bearer $SUMMARY_TOKEN" -X POST --data-binary @"$SUMMARY_PATH" "$SUMMARY_ENDPOINT"
  else
    curl -sSf -H "Content-Type: application/json" -X POST --data-binary @"$SUMMARY_PATH" "$SUMMARY_ENDPOINT"
  fi
else
  pprint "Publishing summary" "skipped (SUMMARY_ENDPOINT not set)"
fi

if [[ -n "$NOTIFY_WEBHOOK" ]]; then
  STATUS=$(python - "$SUMMARY_PATH" <<PY
import json, sys
data = json.load(open(sys.argv[1]))
print(data.get("status", "unknown"))
PY
)
  if [[ "$STATUS" == "failure" ]]; then
    pprint "Notifying webhook" "$NOTIFY_WEBHOOK"
    curl -sSf -H "Content-Type: application/json" -X POST --data-binary "{\"text\":\"Zero-touch automation run failed (${SUMMARY_PATH}).\"}" "$NOTIFY_WEBHOOK"
  else
    pprint "Notifying webhook" "skipped (status=$STATUS)"
  fi
  else
    pprint "Notifying webhook" "skipped (NOTIFY_WEBHOOK not set)"
fi

REPORT_FILE="${SUMMARY_PATH%.json}.md"
python - "$SUMMARY_PATH" "$REPORT_FILE" <<'PY'
import json, pathlib, sys

summary_path = pathlib.Path(sys.argv[1])
report_path = pathlib.Path(sys.argv[2])
data = json.load(open(summary_path))
lines = [
    f"# Zero-Touch Automation Report",
    "",
    f"**Status:** {data.get('status', 'unknown').upper()}",
    f"**Connector:** {data.get('connector')}",
    f"**Overlay order:** {', '.join(data.get('overlay_order', []))}",
    f"**Emulator action:** {data.get('emulator_action')}",
    f"**CI gate command:** {data.get('ci_gate')}",
    "",
    "## Helpers",
]
helpers = data.get("helpers", [])
if helpers:
    lines += [f"- {helper}" for helper in helpers]
else:
    lines.append("- (none)")
lines += [
    "",
    "## Logs",
    f"- Bootstrap: {data['logs']['bootstrap']}",
    f"- Wizard: {data['logs']['wizard']}",
    "",
    "## Summary JSON",
    f"- {summary_path}",
]
report_path.write_text("\n".join(lines) + "\n")
print(f"[publish-summary] Human-readable report written to {report_path}")
PY

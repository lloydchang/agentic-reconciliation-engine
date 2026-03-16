#!/usr/bin/env bash
# =============================================================================
# Cloud AI Agent — enable a cloud overlay in the Flux control-plane kustomization
# =============================================================================
set -euo pipefail

usage() {
  cat <<-USAGE
Usage: $0 <provider> [--emulator=enable|disable] [--toggle=FILE|ENTRY|ACTION]

Enable the Flux overlay for <provider> (aws, azure, gcp) by adding the
subdirectory `control-plane/flux/cloud-<provider>` to the kustomization
resource list. The script is idempotent and will print the current
status if the overlay is already enabled.

Optional flags allow toggling overlay entries without manual edits:
  --emulator=enable|disable
      Enable/disable the Azure emulator (`local-emulator` entry).
  --toggle=FILE|ENTRY|ACTION
      Turn on/off any line (`ENTRY`) inside `FILE` (relative to repo root)
      by specifying ACTION=`enable` or `disable`.
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

PROVIDER=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
shift

EMULATOR_ACTION=""
declare -a TOGGLE_COMMANDS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --emulator=enable)  EMULATOR_ACTION="enable" ;;
    --emulator=disable) EMULATOR_ACTION="disable" ;;
    --toggle=*)
      VAL=${1#--toggle=}
      IFS='|' read -r FILE ENTRY ACTION <<< "$VAL"
      if [[ -z "$FILE" || -z "$ENTRY" || -z "$ACTION" ]]; then
        echo "Invalid toggle specification: $VAL" >&2
        usage
        exit 1
      fi
      TOGGLE_COMMANDS+=("$FILE|$ENTRY|$ACTION|")
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done
case "$PROVIDER" in
  aws|azure|gcp) ;;
  *)
    echo "Unknown provider: $PROVIDER" >&2
    usage
    exit 1
    ;;
esac

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
KUSTOMIZATION_FILE="$REPO_ROOT/control-plane/flux/kustomization.yaml"
OVERLAY_DIR="$REPO_ROOT/control-plane/flux/cloud-$PROVIDER"
OVERLAY_ENTRY="  - ./cloud-$PROVIDER"

if [[ ! -d "$OVERLAY_DIR" ]]; then
  echo "Overlay directory not found: $OVERLAY_DIR" >&2
  echo "Create it first (e.g., adapt control-plane/flux/cloud-aws)" >&2
  exit 1
fi

overlay_exists=false
if grep -qF "$OVERLAY_ENTRY" "$KUSTOMIZATION_FILE"; then
  overlay_exists=true
  echo "Overlay './cloud-$PROVIDER' already enabled in $KUSTOMIZATION_FILE"
else
  python <<PYTHON
from pathlib import Path
path = Path("$KUSTOMIZATION_FILE")
lines = path.read_text().splitlines()
entry = "$OVERLAY_ENTRY"
insert_idx = len(lines)
for idx, line in enumerate(lines):
    if line.startswith("# SOPS configuration"):
        insert_idx = idx
        break
lines.insert(insert_idx, entry)
path.write_text("\n".join(lines) + "\n")
print(f"Inserted overlay entry '{entry}' into {path}")
PYTHON
fi

toggle_entry() {
  local file="$1" line="$2" action="$3" before="$4"
  python - "$REPO_ROOT/$file" "$line" "$action" "$before" <<PYTHON
from pathlib import Path
import sys

path = Path(sys.argv[1])
entry = sys.argv[2]
action = sys.argv[3]
before = sys.argv[4]
lines = path.read_text().splitlines()

if action == "enable":
    if entry in lines:
        print(f"Entry already present in {path}: {entry}")
    else:
        insert_idx = len(lines)
        if before:
            for idx, line in enumerate(lines):
                if before in line:
                    insert_idx = idx
                    break
        lines.insert(insert_idx, entry)
        path.write_text("\n".join(lines) + "\n")
        print(f"Enabled entry '{entry}' in {path}")
elif action == "disable":
    new_lines = [line for line in lines if line.strip() != entry.strip()]
    if len(new_lines) != len(lines):
        path.write_text("\n".join(new_lines) + "\n")
        print(f"Disabled entry '{entry}' in {path}")
    else:
        print(f"No entry '{entry}' found in {path}")
else:
    raise SystemExit(f"Unknown toggle action: {action}")
PYTHON
}

if [[ "$PROVIDER" == "azure" && -n "$EMULATOR_ACTION" ]]; then
  TOGGLE_COMMANDS+=("control-plane/flux/cloud-azure/kustomization.yaml|  - local-emulator|$EMULATOR_ACTION|patchesStrategicMerge")
fi

for toggle in "${TOGGLE_COMMANDS[@]}"; do
  IFS='|' read -r toggle_file toggle_entry toggle_action toggle_before <<< "$toggle"
  toggle_entry "$toggle_file" "$toggle_entry" "$toggle_action" "$toggle_before"
done

echo "Run 'flux reconcile kustomization control-plane --with-source' to apply the overlay."

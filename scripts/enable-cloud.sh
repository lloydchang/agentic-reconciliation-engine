#!/usr/bin/env bash
# =============================================================================
# Cloud AI Agent — enable a cloud overlay in the Flux control-plane kustomization
# =============================================================================
set -euo pipefail

usage() {
  cat <<-USAGE
Usage: $0 <provider>

Enable the Flux overlay for <provider> (aws, azure, gcp) by adding the
subdirectory `control-plane/flux/cloud-<provider>` to the kustomization
resource list. The script is idempotent and will print the current
status if the overlay is already enabled.
USAGE
}

if [[ $# -ne 1 ]]; then
  usage
  exit 1
fi

PROVIDER=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
case "$PROVIDER" in
  aws|azure|gcp) ;;
  *)
    echo "Unknown provider: $1" >&2
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

if grep -qF "$OVERLAY_ENTRY" "$KUSTOMIZATION_FILE"; then
  echo "Overlay './cloud-$PROVIDER' already enabled in $KUSTOMIZATION_FILE"
  exit 0
fi

python <<PYTHON
from pathlib import Path
path = Path("$KUSTOMIZATION_FILE")
lines = path.read_text().splitlines()
entry = "$OVERLAY_ENTRY"
if entry in lines:
    print(f"Overlay already present: {entry}")
    raise SystemExit(0)
insert_idx = len(lines)
for idx, line in enumerate(lines):
    if line.startswith("# SOPS configuration"):
        insert_idx = idx
        break
lines.insert(insert_idx, entry)
path.write_text("\n".join(lines) + "\n")
print(f"Inserted overlay entry '{entry}' into {path}")
PYTHON

echo "Run 'flux reconcile kustomization control-plane --with-source' to apply the overlay."

#!/usr/bin/env bash
set -euo pipefail

ORDER_FILE=${1:-control-plane/flux/overlay-order.txt}
KUSTOMIZATION=control-plane/flux/kustomization.yaml

if [[ ! -f "$ORDER_FILE" ]]; then
  echo "Order file not found: $ORDER_FILE" >&2
  exit 1
fi

python - "$ORDER_FILE" "$KUSTOMIZATION" <<'PY'
import pathlib, sys

order_file = pathlib.Path(sys.argv[1])
kustomization = pathlib.Path(sys.argv[2])

desired = [line.strip() for line in order_file.read_text().splitlines() if line.strip()]
text = kustomization.read_text().splitlines()
start = next((i for i, line in enumerate(text) if line.strip().startswith("resources:")), None)
if start is None:
    raise SystemExit("resources block missing")
tail = next((i for i, line in enumerate(text[start+1:], start+1) if line.startswith("# SOPS configuration")), len(text))
segment = [line for line in text[start+1:tail] if line.strip()]
fixed = [line for line in segment if not line.strip().startswith("./cloud-") and "local-emulator" not in line]
rest = [f"  - {entry}" for entry in desired]
result = text[:start+1] + fixed + rest + text[tail:]
kustomization.write_text("\n".join(result) + "\n")
print("[apply-overlay-order] Applied overlay order:", desired)
PY

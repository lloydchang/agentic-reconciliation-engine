#!/usr/bin/env python3
"""Validate overlay order vs existing kustomization resources for sanity."""
from pathlib import Path
import sys

order_path = Path("core/operators/flux/overlay-order.txt")
kustomization_path = Path("core/operators/flux/kustomization.yaml")

if not order_path.exists() or not kustomization_path.exists():
    sys.exit(0)

desired = [line.strip() for line in order_path.read_text().splitlines() if line.strip()]
kustomization = kustomization_path.read_text().splitlines()
resources = [line.strip() for line in kustomization if line.strip().startswith("- ./")]
missing = [entry for entry in desired if entry not in [r.strip() for r in resources]]

if missing:
    print("[overlay-logician] Warning: ordered overlays missing from kustomization:", missing)
else:
    print("[overlay-logician] All ordered overlays present.")

#!/usr/bin/env bash
# CI gate helper invoked by the migration wizard.
set -uo pipefail

echo "[ci-gate] Running CI policy validation..."

# Run schema + policy validation in repo root if tools are available.
if command -v conftest >/dev/null 2>&1; then
    echo "[ci-gate] Running conftest policy validation..."
    if ! conftest test ./control-plane; then
        echo "[ci-gate] conftest validation failed"
        exit 1
    fi
else
    echo "[ci-gate] conftest not found, skipping policy validation"
fi

if command -v kubeconform >/dev/null 2>&1; then
    echo "[ci-gate] Running kubeconform schema validation..."
    if ! kubeconform ./control-plane; then
        echo "[ci-gate] kubeconform validation failed"
        exit 1
    fi
else
    echo "[ci-gate] kubeconform not found, skipping schema validation"
fi

echo "[ci-gate] CI gate completed"

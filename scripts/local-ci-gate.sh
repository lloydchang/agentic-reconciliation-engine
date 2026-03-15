#!/usr/bin/env bash
# CI gate helper invoked by the migration wizard.
set -euo pipefail

# Run schema + policy validation in repo root.
conftest test ./control-plane
kubeconform ./control-plane

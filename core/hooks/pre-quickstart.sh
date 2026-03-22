#!/bin/bash
# Overlay pre-quickstart hook
# This runs before the base quickstart.sh

echo "🔧 Overlay pre-quickstart hook executing..."

# Set overlay-specific defaults
export OVERLAY_DIR="overlay"
export OVERLAY_REGISTRY_ENABLED="true"
export OVERLAY_TEMPLATES_ENABLED="true"

# Override some quickstart defaults for overlay workflow
export QUICKSTART_MODE="overlay"
export QUICKSTART_FEATURES="overlay-creation,overlay-deployment,overlay-management"

echo "✅ Overlay environment prepared"

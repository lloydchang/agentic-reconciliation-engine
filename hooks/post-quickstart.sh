#!/bin/bash
# Overlay post-quickstart hook
# This runs after the base quickstart.sh

echo "🚀 Overlay post-quickstart hook executing..."

# Create overlay-specific directories
mkdir -p overlay/examples
mkdir -p overlay/templates
mkdir -p overlay/registry

# Initialize overlay registry if it doesn't exist
if [[ ! -f overlay/registry/catalog.yaml ]]; then
    cat > overlay/registry/catalog.yaml << 'REGISTRY_EOF'
apiVersion: v1
kind: OverlayRegistry
metadata:
  name: overlay-registry
  namespace: flux-system
spec:
  overlays: []
REGISTRY_EOF
fi

# Create overlay templates if they don't exist
if [[ ! -d overlay/templates ]]; then
    mkdir -p overlay/templates/{skill-overlay,dashboard-overlay,infra-overlay}
fi

echo "✅ Overlay structure initialized"

#!/bin/bash
# Overlay post-quickstart hook
# This runs after the base quickstart.sh

echo "🚀 Overlay post-quickstart hook executing..."

# Deploy Langfuse + Temporal Integration for Overlay
echo "🔍 Deploying Langfuse + Temporal Integration for Overlay..."

# Check if kubectl is available
if command -v kubectl &> /dev/null; then
    # Deploy Langfuse observability integration
    echo "🔍 Deploying Langfuse observability integration..."

    # Check if cluster is accessible
    if kubectl cluster-info &> /dev/null; then
        # Deploy Langfuse secrets
        echo "📋 Deploying Langfuse secrets..."
        
        if [[ -f "core/config/langfuse-secret.yaml" ]]; then
            if kubectl apply -f core/config/langfuse-secret.yaml; then
                echo "✅ Langfuse secrets deployed to control-plane namespace"
            else
                echo "⚠️  Failed to deploy Langfuse secrets to control-plane namespace"
            fi
        fi
        
        if [[ -f "core/config/langfuse-secret-gitops-infra.yaml" ]]; then
            if kubectl apply -f core/config/langfuse-secret-gitops-infra.yaml; then
                echo "✅ Langfuse secrets deployed to ai-infrastructure namespace"
            else
                echo "⚠️  Failed to deploy Langfuse secrets to ai-infrastructure namespace"
            fi
        fi
        
        # Deploy monitoring with Langfuse dashboard
        echo "📊 Deploying monitoring stack with Langfuse dashboard..."
        
        if [[ -d "core/resources/infrastructure/monitoring" ]]; then
            if kubectl apply -k core/resources/infrastructure/monitoring; then
                echo "✅ Monitoring stack with Langfuse dashboard deployed"
            else
                echo "⚠️  Failed to deploy monitoring stack"
            fi
        fi
        
        # Deploy self-hosted Langfuse with full automation
        if [[ -f "core/automation/scripts/auto-configure-langfuse.sh" ]]; then
            echo "🚀 Running fully automated Langfuse setup..."
            if bash "core/automation/scripts/auto-configure-langfuse.sh"; then
                echo "✅ Fully automated Langfuse setup completed"
            else
                echo "⚠️  Automated setup failed, but secrets deployed"
                echo "   You can run manually: ./core/automation/scripts/auto-configure-langfuse.sh"
            fi
        else
            echo "⚠️  Automated setup script not found"
        fi
    else
        echo "⚠️  Kubernetes cluster not accessible - skipping Langfuse deployment"
    fi

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
else
    echo "⚠️  kubectl not available - skipping overlay deployment"
fi

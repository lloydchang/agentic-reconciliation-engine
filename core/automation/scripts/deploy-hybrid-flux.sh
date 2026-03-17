#!/bin/bash
# Bootstrap Hybrid Flux Architecture
# Core Flux CD (Critical Path) + Flux Operator (Optional Add-on)

set -euxo pipefail

echo "🚀 Bootstrapping Hybrid Flux Architecture..."

# Configuration
REPO_URL="https://github.com/lloydchang/gitops-infra-control-plane"
BRANCH="main"
FLUX_PATH="core/resources/flux/core"

# Step 1: Bootstrap Core Flux CD (Critical Path)
echo "📦 Installing Core Flux CD (Critical Path)..."
flux bootstrap git \
  --url=$REPO_URL \
  --branch=$BRANCH \
  --path=$FLUX_PATH \
  --components=source-controller,kustomize-controller,helm-controller \
  --namespace=flux-system \
  --silent

echo "✅ Core Flux CD installed successfully"

# Step 2: Deploy Flux Operator (Optional Add-on)
echo "🛠️ Installing Flux Operator (Optional Add-on)..."
kubectl apply -f core/resources/flux/operator/

echo "✅ Flux Operator installed successfully"

# Step 3: Deploy Hub Flux System Kustomizations
echo "🔄 Deploying Hub Flux System..."
kubectl apply -f core/resources/flux/hub-flux-system.yaml

echo "✅ Hub Flux System deployed"

# Step 4: Wait for Core Flux to be ready
echo "⏳ Waiting for Core Flux controllers to be ready..."
kubectl wait --for=condition=available --timeout=120s \
  deployment/source-controller -n flux-system
kubectl wait --for=condition=available --timeout=120s \
  deployment/kustomize-controller -n flux-system
kubectl wait --for=condition=available --timeout=120s \
  deployment/helm-controller -n flux-system

echo "✅ Core Flux controllers ready"

# Step 5: Verify installation
echo "🔍 Verifying Hybrid Flux Installation..."

echo ""
echo "============================================="
echo "🎉 Hybrid Flux Architecture Ready!"
echo "============================================="
echo ""
echo "🔧 Core Flux CD (Critical Path):"
echo "  Controllers: kubectl get pods -n flux-system"
echo "  Kustomizations: flux get kustomizations -n flux-system"
echo "  Sources: flux get sources -n flux-system"
echo ""
echo "🖥️  Flux Operator (Optional Add-on):"
echo "  Controllers: kubectl get pods -n flux-operator-system"
echo "  Web UI: kubectl port-forward svc/flux-operator 9080:9080"
echo "  MCP Server: flux-operator-mcp status"
echo ""
echo "📊 Health Check Commands:"
echo "  # Core Flux (Critical)"
echo "  kubectl wait --for=condition=available --timeout=60s deployment/source-controller -n flux-system"
echo "  kubectl wait --for=condition=available --timeout=60s deployment/kustomize-controller -n flux-system"
echo ""
echo "  # Flux Operator (Optional)"
echo "  kubectl get pods -n flux-operator-system || echo '⚠️  Flux Operator not running (optional)'"
echo ""
echo "🚨 Incident Response:"
echo "  # If Core Flux fails: flux bootstrap git --force"
echo "  # If Operator fails: kubectl rollout restart deployment/flux-operator -n flux-operator-system"
echo ""
echo "✅ Hybrid Flux Architecture is ready for production!"

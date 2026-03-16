#!/bin/bash

# Recreate Kind clusters with network fixes
set -e

echo "🔧 Recreating Kind clusters with network configuration fixes..."

# Delete existing clusters
echo "🗑️  Deleting existing clusters..."
kind delete cluster --name gitops-bootstrap 2>/dev/null || true
kind delete cluster --name gitops-hub 2>/dev/null || true

# Wait for clusters to be fully deleted
sleep 5

# Create bootstrap cluster with custom config
echo "🚀 Creating bootstrap cluster with custom network config..."
kind create cluster --name gitops-bootstrap --config kind-config.yaml

# Create hub cluster with custom config  
echo "🚀 Creating hub cluster with custom network config..."
kind create cluster --name gitops-hub --config kind-config.yaml

# Set up contexts
echo "🔧 Setting up kubectl contexts..."
kubectl config rename-context kind-gitops-bootstrap bootstrap
kubectl config rename-context kind-gitops-hub hub

# Test connectivity
echo "🧪 Testing cluster connectivity..."
kubectl cluster-info --context=bootstrap
kubectl cluster-info --context=hub

echo "✅ Clusters recreated successfully!"
echo ""
echo "Next steps:"
echo "1. Test kubectl connectivity: kubectl get pods --context=hub"
echo "2. Run quickstart: bash ./scripts/overlay-quickstart-current.sh"

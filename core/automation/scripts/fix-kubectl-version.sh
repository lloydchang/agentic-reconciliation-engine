#!/bin/bash

# Fix kubectl version skew issues
set -e

echo "🔧 Checking and fixing kubectl version issues..."

# Check current versions
echo "📋 Current kubectl version:"
kubectl version --client --output=yaml 2>/dev/null || echo "kubectl version check failed"

echo ""
echo "📋 Cluster server version:"
kubectl version --server --output=yaml 2>/dev/null || echo "Server version check failed"

# Check for version skew
echo ""
echo "🔍 Checking for version skew..."
if command -v brew >/dev/null 2>&1; then
    echo "📦 Updating kubectl via brew..."
    brew install kubernetes-cli
    brew link --overwrite kubernetes-cli
    
    echo "✅ kubectl updated to latest version"
    kubectl version --client
else
    echo "⚠️  Homebrew not found, please update kubectl manually"
fi

# Test connectivity after update
echo ""
echo "🧪 Testing kubectl connectivity..."
kubectl cluster-info --context=hub 2>/dev/null || echo "Hub cluster not reachable"
kubectl cluster-info --context=bootstrap 2>/dev/null || echo "Bootstrap cluster not reachable"

echo "✅ kubectl version check completed"

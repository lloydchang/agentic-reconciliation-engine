#!/bin/bash

# Fix Helm timeout issues
set -e

echo "🔧 Fixing Helm timeout issues..."

# Update Helm repositories with extended timeout
echo "📦 Updating Helm repositories with extended timeout..."
helm repo update --timeout 10m

# Clear any problematic cached repositories
echo "🗑️  Clearing problematic Helm cache..."
helm repo rm crossplane 2>/dev/null || true
helm repo rm temporal 2>/dev/null || true

# Re-add repositories with connection testing
echo "➕ Re-adding Helm repositories..."
helm repo add crossplane https://charts.crossplane.io/stable
helm repo add temporal https://charts.temporal.io
helm repo add bitnami https://charts.bitnami.com/bitnami

# Test repository connectivity
echo "🧪 Testing repository connectivity..."
helm search repo crossplane/crossplane --max-col-width 120
helm search repo temporal/temporal --max-col-width 120

echo "✅ Helm repositories fixed and ready!"
echo ""
echo "Installation commands with extended timeouts:"
echo "helm install crossplane crossplane/crossplane --namespace crossplane-system --create-namespace --timeout 15m --wait"
echo "helm install temporal temporal/temporal --namespace ai-infrastructure --create-namespace --timeout 15m --wait"

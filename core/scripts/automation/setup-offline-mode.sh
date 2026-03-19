#!/bin/bash

# Offline Mode Setup Script
# Configures the Hub Cluster to operate from cached Git repository

set -euo pipefail

echo "🔧 Setting up Offline Mode for GitOps Infra Control Plane"

# Create namespace if it doesn't exist
kubectl create namespace flux-system --dry-run=client -o yaml | kubectl apply -f -

# Apply local Git cache
echo "📦 Deploying local Git cache..."
kubectl apply -f core/operators/flux/local-git-cache.yaml

# Wait for cache to be ready
echo "⏳ Waiting for Git cache to be ready..."
kubectl wait --for=condition=ready pod -l app=git-cache-manager -n flux-system --timeout=300s

# Test cache connectivity
echo "🔍 Testing cache connectivity..."
CACHE_POD=$(kubectl get pod -l app=git-cache-manager -n flux-system -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$CACHE_POD" -n flux-system -- curl -s http://localhost:8080/ | head -5

# Create offline mode ConfigMap
echo "📝 Creating offline mode configuration..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: offline-mode-config
  namespace: flux-system
data:
  offline-mode.yaml: |
    # Offline Mode Configuration
    # Enables operation from cached Git repository when remote repositories are unavailable
    
    offline:
      enabled: true
      cache_url: "http://git-cache-service.flux-system.svc.cluster.local:8080/agentic-reconciliation-engine"
      fallback_urls:
        - "http://git-cache-service.flux-system.svc.cluster.local:8080/agentic-reconciliation-engine"
      
    synchronization:
      queue_changes: true
      sync_on_recovery: true
      max_queue_size: 1000
      
    monitoring:
      health_check_interval: "30s"
      failover_threshold: 3
      
  recovery-procedures.yaml: |
    # Recovery Procedures for Git Outages
    
    procedures:
      - name: "Git Repository Outage"
        description: "Actions to take when Git repositories become unavailable"
        steps:
          1: "Verify all Git repository health"
          2: "Enable offline mode automatically"
          3: "Continue operations from cached state"
          4: "Queue changes for later synchronization"
          5: "Monitor repository recovery"
          6: "Synchronize queued changes on recovery"
          
      - name: "Manual Recovery"
        description: "Manual steps for recovery if automatic failover fails"
        steps:
          1: "Verify cache health: kubectl get service git-cache-service"
          2: "Check offline mode: kubectl get kustomizations -l fluxcd.io/offline-mode=true"
          3: "Force offline mode: kubectl annotate kustomization --all fluxcd.io/offline-mode=true"
          4: "Verify operations: kubectl get kustomizations -A"
EOF

echo "✅ Offline mode setup completed!"
echo ""
echo "📍 Cache service: git-cache-service.flux-system.svc.cluster.local:8080"
echo "🔧 Offline mode controller: offline-mode-controller"
echo "📊 Monitor with: kubectl get cronjobs -n flux-system"
echo ""
echo "📖 For manual failover:"
echo "  kubectl patch gitrepository $TOPDIR-primary -n flux-system -p '{\"spec\":{\"url\":\"http://git-cache-service.flux-system.svc.cluster.local:8080/agentic-reconciliation-engine\"}}' --type=merge"

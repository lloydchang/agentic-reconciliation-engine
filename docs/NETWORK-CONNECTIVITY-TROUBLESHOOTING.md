# Network Connectivity Troubleshooting Guide

## Overview

This guide addresses network connectivity issues that prevent Helm chart installations, kubectl operations, and Kind cluster communication in local development environments on macOS.

## Problem Statement

### Current Issues
- ❌ Crossplane installation timing out (Helm connectivity issues)
- ❌ Temporal installation timing out (Helm connectivity issues)  
- ❌ kubectl commands timing out (network connectivity)
- ❌ Dashboard service not fully deployed

### Root Cause Analysis
1. **Docker Desktop macOS Network Issues**: Docker containers run in a Linux VM, causing network isolation
2. **Kind Cluster Network Configuration**: Default Docker network conflicts with VPNs/local networks
3. **Helm Repository Timeouts**: Network connectivity issues preventing chart downloads
4. **kubectl Version Skew**: Client/server version mismatch causing connection issues

## Solution Options

### Option A: Docker Desktop Restart (First Priority)

**Manual Steps Required:**

1. **Quit Docker Desktop completely:**
   - Click Docker Desktop icon in menu bar
   - Select "Quit Docker Desktop"
   - Wait for all Docker processes to stop

2. **Restart Docker Desktop:**
   - Open Applications folder
   - Launch Docker Desktop
   - Wait for full startup (green status in menu bar)

3. **Test Docker connectivity:**
   ```bash
   docker --version
   docker ps
   ```

4. **Test Kind cluster connectivity:**
   ```bash
   kind get clusters
   kubectl cluster-info --context=kind-gitops-hub
   ```

### Option B: Kind Cluster Recreation with Custom Network

**Configuration File:** `kind-config.yaml`
```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  # Use custom subnet to avoid conflicts with VPNs/local networks
  podSubnet: "10.254.0.0/16"
  serviceSubnet: "10.255.0.0/16"
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 8080
    hostPort: 8080
    protocol: TCP
  - containerPort: 7233
    hostPort: 7233
    protocol: TCP
  - containerPort: 3000
    hostPort: 3000
    protocol: TCP
```

**Execution Script:** `scripts/recreate-clusters-with-fix.sh`
```bash
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
```

### Option C: Helm Timeout Fixes

**Execution Script:** `scripts/fix-helm-timeouts.sh`
```bash
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
```

**Installation Commands with Extended Timeouts:**
```bash
helm install crossplane crossplane/crossplane --namespace crossplane-system --create-namespace --timeout 15m --wait
helm install temporal temporal/temporal --namespace ai-infrastructure --create-namespace --timeout 15m --wait
```

### Option D: kubectl Version Check and Fix

**Execution Script:** `scripts/fix-kubectl-version.sh`
```bash
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
```

## Enhanced Error Handling and Diagnostics

### Crossplane Installation Diagnostics

The `scripts/install-crossplane.sh` has been enhanced with comprehensive error handling:

**Diagnostic Function:** `diagnose_installation_failure()`
- Analyzes exit codes and provides specific guidance
- Runs network connectivity diagnostics
- Provides operation-specific troubleshooting steps
- Suggests common solutions based on failure patterns

**Error Handling Setup:**
```bash
# Set error handling to use diagnostic function
set -Eeo pipefail
trap 'diagnose_installation_failure "unknown operation" $?' ERR
```

**Exit Code Analysis:**
- **Exit Code 1**: Command execution failure, permission issues, resource not found
- **Exit Code 2**: Invalid arguments, misconfiguration
- **Exit Code 125**: Command timeout, resource exhaustion, network latency
- **Exit Code 130**: Script interrupted (Ctrl+C), process termination
- **Exit Code 255**: Exit status out of range, signal termination

### Operation-Specific Diagnostics

**Helm Repository Issues:**
- Check internet connectivity
- Verify proxy settings: HTTP_PROXY, HTTPS_PROXY
- Test DNS resolution: `nslookup charts.crossplane.io`
- Check firewall rules for HTTPS (port 443)

**Helm Installation Issues:**
- Cluster connectivity problems
- Insufficient cluster resources
- Namespace creation issues
- Image pull failures
- Check: `kubectl get nodes`, `kubectl top nodes`

**Pod Verification Issues:**
- Pod startup failures
- Resource constraints (CPU/memory)
- Image pull issues
- Configuration errors
- Check: `kubectl get pods -n $NAMESPACE`, `kubectl describe pods -n $NAMESPACE`

### Debugging Commands

**Cluster Connectivity:**
```bash
kubectl cluster-info
kubectl get nodes
```

**Namespace and Events:**
```bash
kubectl get namespace $NAMESPACE -o yaml
kubectl get events -n $NAMESPACE --sort-by=.metadata.creationTimestamp
```

**Helm Status:**
```bash
helm list -n $NAMESPACE
helm history crossplane -n $NAMESPACE
```

**System Resources:**
```bash
kubectl top nodes
kubectl top pods --all-namespaces
```

**Network Connectivity:**
```bash
curl -I https://charts.crossplane.io/stable
ping -c 3 charts.crossplane.io
```

### Common Solutions

**1. Network Issues:**
```bash
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

**2. Resource Issues:**
```bash
kubectl describe nodes
```

**3. DNS Issues:**
```bash
kubectl rollout restart deployment/coredns -n kube-system
```

**4. Helm Issues:**
```bash
helm repo rm crossplane
helm repo add crossplane https://charts.crossplane.io/stable
```

**5. Permission Issues:**
```bash
kubectl auth can-i create namespace
kubectl auth can-i create deployment --namespace=$NAMESPACE
```

## Execution Sequence

### Step-by-Step Fix Process

1. **Option A: Docker Desktop Restart**
   - Quit and restart Docker Desktop
   - Verify Docker responsiveness
   - Test basic connectivity

2. **Option B: Recreate Clusters**
   ```bash
   chmod +x scripts/recreate-clusters-with-fix.sh
   ./scripts/recreate-clusters-with-fix.sh
   ```

3. **Option C: Fix Helm Timeouts**
   ```bash
   chmod +x scripts/fix-helm-timeouts.sh
   ./scripts/fix-helm-timeouts.sh
   ```

4. **Option D: Fix kubectl Version**
   ```bash
   chmod +x scripts/fix-kubectl-version.sh
   ./scripts/fix-kubectl-version.sh
   ```

5. **Option E: Final Test**
   ```bash
   # Test connectivity
   kubectl cluster-info --context=hub
   kubectl get pods -A --context=hub

   # Run quickstart
   bash ./scripts/overlay-quickstart-current.sh
   ```

## Alternative Solutions

### Option A: Use Minikube Instead
```bash
brew install minikube
minikube start --driver=docker
```

### Option B: Docker Network Reset
```bash
docker network prune
docker system prune -f
```

### Option C: Use Pre-built Images
```bash
kubectl apply -f infrastructure/ai-inference/shared/
```

## Success Criteria

**After applying fixes, the following should work:**
- ✅ Docker commands respond immediately
- ✅ kubectl commands complete without timeout
- ✅ Helm repository updates succeed
- ✅ Crossplane installation completes
- ✅ Temporal installation completes
- ✅ AI agents dashboard is accessible
- ✅ Quickstart script runs to completion

## Files Created/Modified

1. **`kind-config.yaml`** - Custom Kind cluster network configuration
2. **`scripts/recreate-clusters-with-fix.sh`** - Cluster recreation script
3. **`scripts/fix-helm-timeouts.sh`** - Helm timeout fixes
4. **`scripts/fix-kubectl-version.sh`** - kubectl version fixes
5. **`scripts/install-crossplane.sh`** - Enhanced with diagnostic functions

## References

- [Kind Known Issues](https://kind.sigs.k8s.io/docs/user/known-issues/)
- [Docker Desktop macOS Issues](https://github.com/docker/for-mac/issues)
- [Kubernetes Troubleshooting](https://kubernetes.io/docs/tasks/debug/debug-cluster/troubleshoot-kubectl/)
- [Helm Timeout Issues](https://github.com/helm/helm/issues/11306)

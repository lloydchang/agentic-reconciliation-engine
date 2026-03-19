#!/bin/bash

# Flux Operator Installation Script
# This script installs the Flux Operator and sets up the GitOps Infra Control Plane

set -euxo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FLUX_OPERATOR_VERSION="latest"
FLUX_INSTANCE_NAMESPACE="flux-system"
KUBECONFIG_PATH="${KUBECONFIG:-$HOME/.kube/config}"

echo -e "${BLUE}🚀 Flux Operator Installation Script${NC}"
echo "=================================="

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check kubectl connection
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

# Check flux-operator CLI
if ! command -v flux-operator &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Flux Operator CLI...${NC}"
    
    # Install via Homebrew (macOS)
    if command -v brew &> /dev/null; then
        brew install controlplaneio-fluxcd/tap/flux-operator
    else
        echo -e "${RED}❌ Homebrew not found. Please install flux-operator manually:${NC}"
        echo "Visit: https://fluxoperator.dev/get-started/"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Flux Operator CLI is already installed${NC}"
fi

# Verify flux-operator CLI
if command -v flux-operator &> /dev/null; then
    FLUX_OP_VERSION=$(flux-operator version --short 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✅ Flux Operator CLI version: $FLUX_OP_VERSION${NC}"
fi

# Create namespace
echo -e "${YELLOW}🏗️  Creating flux-system namespace...${NC}"
kubectl create namespace $FLUX_INSTANCE_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Create basic FluxInstance configuration
echo -e "${YELLOW}📝 Creating FluxInstance configuration...${NC}"

cat > flux-instance.yaml << EOF
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: $FLUX_INSTANCE_NAMESPACE
  labels:
    app.kubernetes.io/name: flux
    app.kubernetes.io/component: gitops
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  distribution:
    version: "2.x"
    registry: "ghcr.io/fluxcd"
    artifact: "oci://ghcr.io/controlplaneio-fluxcd/flux-operator-manifests"
  components:
    - source-controller
    - source-watcher
    - kustomize-controller
    - helm-controller
    - notification-controller
    - image-reflector-controller
    - image-automation-controller
  cluster:
    type: kubernetes
    size: medium
    multitenant: false
    networkPolicy: true
    domain: "cluster.local"
  kustomize:
    patch: |
      - patch: |
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: source-controller
            namespace: flux-system
          spec:
            template:
              spec:
                containers:
                - name: manager
                  resources:
                    requests:
                      cpu: 100m
                      memory: 256Mi
                    limits:
                      cpu: 500m
                      memory: 512Mi
        target:
          kind: Kustomization
          name: flux-components
          namespace: flux-system
EOF

# Install Flux Operator
echo -e "${YELLOW}🚀 Installing Flux Operator...${NC}"
flux-operator install -f flux-instance.yaml

# Wait for Flux components to be ready
echo -e "${YELLOW}⏳ Waiting for Flux components to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=flux -n $FLUX_INSTANCE_NAMESPACE --timeout=300s

# Verify installation
echo -e "${YELLOW}🔍 Verifying Flux Operator installation...${NC}"

# Check FluxInstance status
kubectl get fluxinstance flux -n $FLUX_INSTANCE_NAMESPACE -o wide

# Check pods
kubectl get pods -n $FLUX_INSTANCE_NAMESPACE -l app.kubernetes.io/name=flux

# Check CRDs
kubectl get crds | grep fluxcd || echo "Flux CRDs not yet available"

# Create sync configuration for GitOps Infra Control Plane
echo -e "${YELLOW}🔄 Creating sync configuration...${NC}"

cat > flux-sync.yaml << EOF
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: $FLUX_INSTANCE_NAMESPACE
spec:
  sync:
    kind: GitRepository
    url: "https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:\/]\(.*\)\.git/\1/' | cut -d'/' -f1)/$(basename $(git rev-parse --show-toplevel))"
    ref: "refs/heads/$(git branch --show-current)"
    path: "core/resources/tenants"
    pullSecret: "flux-system"
  distribution:
    version: "2.x"
    registry: "ghcr.io/fluxcd"
    artifact: "oci://ghcr.io/controlplaneio-fluxcd/flux-operator-manifests"
  components:
    - source-controller
    - source-watcher
    - kustomize-controller
    - helm-controller
    - notification-controller
    - image-reflector-controller
    - image-automation-controller
  cluster:
    type: kubernetes
    size: medium
    multitenant: false
    networkPolicy: true
    domain: "cluster.local"
EOF

# Create basic auth secret if needed (for private repos)
if git config --get remote.origin.url | grep -q "github.com"; then
    echo -e "${YELLOW}🔐 Checking if repository is private...${NC}"
    
    # Try to access the repository without authentication
    if ! git ls-remote --exit-code origin &> /dev/null; then
        echo -e "${YELLOW}🔐 Creating basic auth secret for private repository...${NC}"
        echo "Please provide your GitHub token:"
        read -s -p "GitHub Token: " GITHUB_TOKEN
        
        flux-operator create secret basic-auth flux-system \
            --namespace=$FLUX_INSTANCE_NAMESPACE \
            --username=git \
            --password=$GITHUB_TOKEN
        
        echo -e "${GREEN}✅ Basic auth secret created${NC}"
    else
        echo -e "${GREEN}✅ Repository is public, no auth needed${NC}"
    fi
fi

# Apply sync configuration
echo -e "${YELLOW}🔄 Applying sync configuration...${NC}"
kubectl apply -f flux-sync.yaml

# Wait for sync to complete
echo -e "${YELLOW}⏳ Waiting for initial sync to complete...${NC}"
sleep 30

# Check sync status
kubectl get fluxinstance flux -n $FLUX_INSTANCE_NAMESPACE -o yaml | grep -A 10 "sync:" || echo "Sync not yet configured"

# Create monitoring configuration
echo -e "${YELLOW}📊 Setting up monitoring...${NC}"

cat > flux-monitoring.yaml << EOF
apiVersion: v1
kind: Service
metadata:
  name: flux-operator
  namespace: $FLUX_INSTANCE_NAMESPACE
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: monitoring
spec:
  selector:
    app.kubernetes.io/name: flux
  ports:
  - name: http
    port: 9080
    targetPort: 9080
    protocol: TCP
  type: ClusterIP
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: flux-operator
  namespace: $FLUX_INSTANCE_NAMESPACE
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: flux
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
EOF

kubectl apply -f flux-monitoring.yaml

# Create ResourceSet for infrastructure components
echo -e "${YELLOW}🏗️  Creating ResourceSet for infrastructure...${NC}"

cat > infrastructure-resourceset.yaml << EOF
apiVersion: fluxcd.controlplane.io/v1
kind: ResourceSet
metadata:
  name: infrastructure
  namespace: $FLUX_INSTANCE_NAMESPACE
  labels:
    app.kubernetes.io/name: infrastructure
    app.kubernetes.io/component: gitops
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  resources:
  - name: network-infrastructure
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: agentic-reconciliation-engine
    path: core/resources/tenants/1-network
    prune: true
    wait: true
    timeout: 10m
  - name: cluster-infrastructure
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: agentic-reconciliation-engine
    path: core/resources/tenants/2-clusters
    prune: true
    wait: true
    timeout: 15m
    dependsOn:
    - network-infrastructure
  - name: workload-infrastructure
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: agentic-reconciliation-engine
    path: core/resources/tenants/3-workloads
    prune: true
    wait: true
    timeout: 20m
    dependsOn:
    - cluster-infrastructure
EOF

kubectl apply -f infrastructure-resourceset.yaml

echo -e "${GREEN}✅ Flux Operator installation completed!${NC}"
echo ""
echo -e "${BLUE}🎯 Next Steps:${NC}"
echo "1. Check Flux Operator status:"
echo "   kubectl get fluxinstance flux -n $FLUX_INSTANCE_NAMESPACE"
echo ""
echo "2. Access the Flux Operator UI:"
echo "   kubectl -n $FLUX_INSTANCE_NAMESPACE port-forward svc/flux-operator 9080:9080"
echo "   Then open http://localhost:9080"
echo ""
echo "3. Check synchronized resources:"
echo "   kubectl get resourceset -n $FLUX_INSTANCE_NAMESPACE"
echo ""
echo "4. Monitor Flux operations:"
echo "   kubectl logs -n $FLUX_INSTANCE_NAMESPACE deployment/flux-operator"
echo ""
echo -e "${YELLOW}📚 For more information, see:${NC}"
echo "- Flux Operator Documentation: https://fluxoperator.dev/"
echo "- MCP Server Setup: docs/FLUX-MCP-SERVER.md"
echo "- Advanced Configuration: docs/FLUX-OPERATOR-ADVANCED.md"

# Cleanup temporary files
rm -f flux-instance.yaml flux-sync.yaml flux-monitoring.yaml infrastructure-resourceset.yaml

echo -e "${GREEN}🎉 Installation script completed successfully!${NC}"

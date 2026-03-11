#!/bin/bash

# Karmada + Flux Multi-Cluster GitOps Setup
# This script sets up Karmada with Flux for multi-cluster management

set -e

echo "🚀 Setting up Karmada + Flux Multi-Cluster GitOps"
echo "=================================================="

# Configuration
KARMADA_VERSION="1.6.0"
MEMBER_CLUSTERS=3

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if kind is installed
    if ! command -v kind &> /dev/null; then
        print_error "kind is not installed. Please install kind first."
        exit 1
    fi
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check if flux is installed
    if ! command -v flux &> /dev/null; then
        print_error "flux is not installed. Please install flux first."
        exit 1
    fi
    
    print_status "Prerequisites check passed"
}

# Clone Karmada repository
setup_karmada() {
    print_status "Setting up Karmada..."
    
    if [ ! -d "karmada" ]; then
        print_status "Cloning Karmada repository..."
        git clone https://github.com/karmada-io/karmada.git
    fi
    
    cd karmada
    
    # Checkout specific version
    git checkout v$KARMADA_VERSION
    
    print_status "Starting Karmada development environment..."
    ./hack/local-up-karmada.sh
    
    cd ..
    
    print_status "Karmada setup completed"
}

# Verify Karmada clusters
verify_clusters() {
    print_status "Verifying Karmada clusters..."
    
    # Get Karmada config
    export KUBECONFIG=$HOME/.kube/karmada.config
    
    # List member clusters
    kubectl get clusters
    
    print_status "Karmada clusters verified"
}

# Install Flux CRDs in Karmada control plane
install_flux_crds() {
    print_status "Installing Flux CRDs in Karmada control plane..."
    
    export KUBECONFIG=$HOME/.kube/karmada.config
    
    # Install Flux CRDs only (no controllers in control plane)
    kubectl apply -k github.com/fluxcd/flux2/manifests/crds?ref=main
    
    print_status "Flux CRDs installed in Karmada control plane"
}

# Install Flux controllers in member clusters
install_flux_controllers() {
    print_status "Installing Flux controllers in member clusters..."
    
    # Install Flux in each member cluster
    for i in 1 2 3; do
        print_status "Installing Flux in member$i cluster..."
        
        export KUBECONFIG=$HOME/.kube/members.config
        kubectl config use-context member$i
        
        flux install
        
        print_status "Flux installed in member$i cluster"
    done
    
    print_status "Flux controllers installed in all member clusters"
}

# Create multi-cluster GitOps example
create_multi_cluster_example() {
    print_status "Creating multi-cluster GitOps example..."
    
    export KUBECONFIG=$HOME/.kube/karmada.config
    
    # Create namespace for multi-cluster resources
    cat > karmada-multi-cluster.yaml << 'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: gitops-multi-cluster
---
# Helm Repository for podinfo
apiVersion: source.toolkit.fluxcd.io/v1
kind: HelmRepository
metadata:
  name: podinfo
  namespace: gitops-multi-cluster
spec:
  interval: 1m
  url: https://stefanprodan.github.io/podinfo
---
# Helm Release for podinfo
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: podinfo
  namespace: gitops-multi-cluster
spec:
  interval: 5m
  chart:
    spec:
      chart: podinfo
      version: 6.5.0
      sourceRef:
        kind: HelmRepository
        name: podinfo
  values:
    replicaCount: 3
    ui:
      enabled: true
    ingress:
      enabled: true
      className: nginx
      hosts:
        - host: podinfo.local
          paths:
            - path: /
              pathType: Prefix
---
# Propagation Policy for HelmRepository
apiVersion: policy.karmada.io/v1alpha1
kind: PropagationPolicy
metadata:
  name: helm-repo-policy
  namespace: gitops-multi-cluster
spec:
  resourceSelectors:
    - apiVersion: source.toolkit.fluxcd.io/v1
      kind: HelmRepository
      name: podinfo
  placement:
    clusterAffinity:
      clusterNames:
        - member1
        - member2
        - member3
---
# Propagation Policy for HelmRelease
apiVersion: policy.karmada.io/v1alpha1
kind: PropagationPolicy
metadata:
  name: helm-release-policy
  namespace: gitops-multi-cluster
spec:
  resourceSelectors:
    - apiVersion: helm.toolkit.fluxcd.io/v2
      kind: HelmRelease
      name: podinfo
  placement:
    clusterAffinity:
      clusterNames:
        - member1
        - member2
        - member3
---
# Override Policy for cluster-specific customization
apiVersion: policy.karmada.io/v1alpha1
kind: OverridePolicy
metadata:
  name: podinfo-override
  namespace: gitops-multi-cluster
spec:
  resourceSelectors:
    - apiVersion: helm.toolkit.fluxcd.io/v2
      kind: HelmRelease
      name: podinfo
  overrideRules:
    - targetCluster:
        clusterNames:
          - member1
      overriders:
        plaintext:
          - path: "/spec/values"
            operator: add
            value:
              replicaCount: 2
              resources:
                limits:
                  cpu: 500m
                  memory: 512Mi
                requests:
                  cpu: 250m
                  memory: 256Mi
    - targetCluster:
        clusterNames:
          - member2
      overriders:
        plaintext:
          - path: "/spec/values"
            operator: add
            value:
              replicaCount: 4
              resources:
                limits:
                  cpu: 1000m
                  memory: 1Gi
                requests:
                  cpu: 500m
                  memory: 512Mi
EOF
    
    # Apply the multi-cluster configuration
    kubectl apply -f karmada-multi-cluster.yaml
    
    print_status "Multi-cluster GitOps example created"
}

# Verify multi-cluster deployment
verify_deployment() {
    print_status "Verifying multi-cluster deployment..."
    
    # Check deployment in each member cluster
    for i in 1 2 3; do
        print_status "Checking deployment in member$i cluster..."
        
        export KUBECONFIG=$HOME/.kube/members.config
        kubectl config use-context member$i
        
        # Wait for deployment
        kubectl wait --for=condition=available deployment/podinfo -n gitops-multi-cluster --timeout=300s
        
        # Check pods
        kubectl get pods -n gitops-multi-cluster
        
        # Check helm release
        helm list -n gitops-multi-cluster
    done
    
    print_status "Multi-cluster deployment verified"
}

# Create monitoring setup
create_monitoring() {
    print_status "Creating multi-cluster monitoring..."
    
    export KUBECONFIG=$HOME/.kube/karmada.config
    
    # Create monitoring resources
    cat > karmada-monitoring.yaml << 'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
---
# Prometheus Helm Repository
apiVersion: source.toolkit.fluxcd.io/v1
kind: HelmRepository
metadata:
  name: prometheus-community
  namespace: monitoring
spec:
  interval: 1h
  url: https://prometheus-community.github.io/helm-charts
---
# Grafana Helm Repository
apiVersion: source.toolkit.fluxcd.io/v1
kind: HelmRepository
metadata:
  name: grafana
  namespace: monitoring
spec:
  interval: 1h
  url: https://grafana.github.io/helm-charts
---
# Prometheus HelmRelease
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: prometheus
  namespace: monitoring
spec:
  interval: 5m
  chart:
    spec:
      chart: kube-prometheus-stack
      version: 45.28.0
      sourceRef:
        kind: HelmRepository
        name: prometheus-community
  values:
    prometheus:
      prometheusSpec:
        retention: 7d
        storageSpec:
          volumeClaimTemplate:
            spec:
              storageClassName: standard
              accessModes: ["ReadWriteOnce"]
              resources:
                requests:
                  storage: 20Gi
    grafana:
      enabled: true
      persistence:
        enabled: true
        size: 10Gi
---
# Grafana HelmRelease
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: grafana
  namespace: monitoring
spec:
  interval: 5m
  chart:
    spec:
      chart: grafana
      version: 6.58.9
      sourceRef:
        kind: HelmRepository
        name: grafana
  values:
    persistence:
      enabled: true
      size: 5Gi
    service:
      type: LoadBalancer
---
# Monitoring Propagation Policy
apiVersion: policy.karmada.io/v1alpha1
kind: PropagationPolicy
metadata:
  name: monitoring-policy
  namespace: monitoring
spec:
  resourceSelectors:
    - apiVersion: source.toolkit.fluxcd.io/v1
      kind: HelmRepository
      name: prometheus-community
    - apiVersion: source.toolkit.fluxcd.io/v1
      kind: HelmRepository
      name: grafana
    - apiVersion: helm.toolkit.fluxcd.io/v2
      kind: HelmRelease
      name: prometheus
    - apiVersion: helm.toolkit.fluxcd.io/v2
      kind: HelmRelease
      name: grafana
  placement:
    clusterAffinity:
      clusterNames:
        - member1
        - member2
        - member3
EOF
    
    # Apply monitoring configuration
    kubectl apply -f karmada-monitoring.yaml
    
    print_status "Multi-cluster monitoring created"
}

# Main execution
main() {
    print_status "Starting Karmada + Flux multi-cluster setup..."
    
    check_prerequisites
    setup_karmada
    verify_clusters
    install_flux_crds
    install_flux_controllers
    create_multi_cluster_example
    verify_deployment
    create_monitoring
    
    print_status "🎉 Karmada + Flux multi-cluster setup completed!"
    print_status "📊 Multi-cluster GitOps is now operational"
    print_status "🔍 Check deployments across all member clusters"
    
    # Show final status
    echo ""
    echo "============================================="
    echo "🎯 MULTI-CLUSTER STATUS"
    echo "============================================="
    
    export KUBECONFIG=$HOME/.kube/karmada.config
    kubectl get clusters
    kubectl get propagationpolicies -A
    kubectl get overridepolicies -A
}

# Run main function
main "$@"

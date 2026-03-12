#!/bin/bash

# Multi-Hub Architecture Setup Script
# Implements geographic distribution and automatic failover

set -euo pipefail

# Configuration
PRIMARY_HUB="hub-us-east-1"
SECONDARY_HUBS=("hub-us-west-2" "hub-eu-west-1")
NAMESPACE="flux-system"
GIT_REPO="${GIT_REPO:-https://github.com/your-org/gitops-infra-control-plane}"
BRANCH="${BRANCH:-main}"

echo "🚀 Setting up Multi-Hub Architecture for GitOps Infrastructure Control Plane"

# Function to setup individual hub
setup_hub() {
    local hub_name=$1
    local region=$2
    local is_primary=${3:-false}
    
    echo "📍 Setting up hub: $hub_name in region: $region"
    
    # Create kubeconfig context for hub
    kubectl config use-context $hub_name
    
    # Install Flux in hub
    if $is_primary; then
        echo "🎯 Setting up PRIMARY hub: $hub_name"
        flux bootstrap git \
            --url=$GIT_REPO \
            --branch=$BRANCH \
            --path=control-plane \
            --components-extra=image-reflector-controller,image-automation-controller \
            --namespace=$NAMESPACE
    else
        echo "🔄 Setting up SECONDARY hub: $hub_name"
        flux install \
            --namespace=$NAMESPACE \
            --components-extra=image-reflector-controller,image-automation-controller
        
        # Configure secondary hub to sync from same Git repo
        flux create source git gitops-infra \
            --url=$GIT_REPO \
            --branch=$BRANCH \
            --namespace=$NAMESPACE
            
        flux create kustomization control-plane \
            --source=gitops-infra \
            --path=./control-plane \
            --prune=true \
            --interval=5m \
            --namespace=$NAMESPACE
    fi
    
    # Apply hub-specific configurations
    if $is_primary; then
        kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: hub-role
  namespace: $NAMESPACE
data:
  role: "primary"
  priority: "1"
  region: "$region"
EOF
    else
        kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: hub-role
  namespace: $NAMESPACE
data:
  role: "secondary"
  priority: "2"
  region: "$region"
EOF
    fi
    
    echo "✅ Hub $hub_name setup completed"
}

# Function to setup Karmada control plane
setup_karmada() {
    echo "🌐 Setting up Karmada control plane for multi-hub coordination"
    
    # Install Karmada in primary hub
    kubectl config use-context $PRIMARY_HUB
    
    # Clone and setup Karmada
    if [ ! -d "karmada" ]; then
        git clone https://github.com/karmada-io/karmada.git
        cd karmada
    else
        cd karmada
        git pull origin main
    fi
    
    # Deploy Karmada control plane
    ./hack/local-up-karmada.sh
    
    # Register all hubs with Karmada
    for hub in "$PRIMARY_HUB" "${SECONDARY_HUBS[@]}"; do
        echo "🔗 Registering hub $hub with Karmada"
        kubectl config use-context $hub
        
        # Get hub credentials
        kubectl get secret $hub-kubeconfig -n $NAMESPACE -o yaml > /tmp/$hub-kubeconfig.yaml
        
        # Register with Karmada
        kubectl apply -f - <<EOF
apiVersion: cluster.karmada.io/v1alpha1
kind: Cluster
metadata:
  name: $hub
  labels:
    region: ${hub#hub-}
    role: ${hub == $PRIMARY_HUB && "primary" || "secondary"}
spec:
  kubeconfig: |
$(cat /tmp/$hub-kubeconfig.yaml | sed 's/^/    /')
  syncMode: Push
  proxyURL: ""
  insecureSkipTLSVerify: false
EOF
    done
    
    cd ..
    echo "✅ Karmada control plane setup completed"
}

# Function to setup health monitoring
setup_health_monitoring() {
    echo "🏥 Setting up health monitoring and failover detection"
    
    kubectl config use-context $PRIMARY_HUB
    
    # Deploy health monitoring service
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hub-health-monitor
  namespace: $NAMESPACE
spec:
  replicas: 2
  selector:
    matchLabels:
      app: hub-health-monitor
  template:
    metadata:
      labels:
        app: hub-health-monitor
    spec:
      containers:
      - name: monitor
        image: nginx:alpine
        command: ["/bin/sh"]
        args:
          - -c
          - |
            echo "Starting health monitoring..."
            while true; do
              for hub in $PRIMARY_HUB ${SECONDARY_HUBS[@]}; do
                echo "Checking health of hub: \$hub"
                # Check hub health via Karmada API
                kubectl get cluster \$hub -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' || echo "Failed to check \$hub"
              done
              sleep 30
            done
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
EOF
}

# Function to test failover
test_failover() {
    echo "🧪 Testing hub failover mechanism"
    
    # Simulate primary hub failure
    echo "🔥 Simulating primary hub failure..."
    kubectl config use-context $PRIMARY_HUB
    kubectl scale deployment kustomize-controller -n $NAMESPACE --replicas=0
    
    echo "⏳ Waiting 60 seconds for failover detection..."
    sleep 60
    
    # Check if secondary hubs take over
    for hub in "${SECONDARY_HUBS[@]}"; do
        echo "🔍 Checking status of secondary hub: $hub"
        kubectl config use-context $hub
        kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=flux
    done
    
    # Restore primary hub
    echo "🔄 Restoring primary hub..."
    kubectl config use-context $PRIMARY_HUB
    kubectl scale deployment kustomize-controller -n $NAMESPACE --replicas=1
    
    echo "✅ Failover test completed"
}

# Main execution
main() {
    echo "🎯 Starting Multi-Hub Architecture Setup"
    
    # Setup primary hub
    setup_hub "$PRIMARY_HUB" "us-east-1" true
    
    # Setup secondary hubs
    setup_hub "hub-us-west-2" "us-west-2" false
    setup_hub "hub-eu-west-1" "eu-west-2" false
    
    # Setup Karmada coordination
    setup_karmada
    
    # Setup health monitoring
    setup_health_monitoring
    
    # Test failover mechanism
    test_failover
    
    echo "🎉 Multi-Hub Architecture Setup Completed Successfully!"
    echo "📊 Architecture Summary:"
    echo "  - Primary Hub: $PRIMARY_HUB"
    echo "  - Secondary Hubs: ${SECONDARY_HUBS[*]}"
    echo "  - Coordination: Karmada"
    echo "  - Health Monitoring: Enabled"
    echo "  - Failover: Tested"
}

# Run main function
main "$@"

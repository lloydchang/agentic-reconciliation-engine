#!/bin/bash
# Local Management Cluster Setup Script
# Sets up a local Kubernetes cluster to emulate cloud management clusters

set -e

echo "🚀 Setting up Local Management Cluster"
echo "======================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
CLUSTER_TYPE=${CLUSTER_TYPE:-kind}  # kind or minikube
CLUSTER_NAME="gitops-management-local"
FLUX_VERSION="v2.1.0"

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 1. Create local Kubernetes cluster
create_cluster() {
    print_status "Creating local $CLUSTER_TYPE cluster..."

    case $CLUSTER_TYPE in
        kind)
            if ! command -v kind &> /dev/null; then
                print_warning "Kind not found. Installing..."
                curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
                chmod +x ./kind && sudo mv ./kind /usr/local/bin/
            fi

            cat <<EOF | kind create cluster --name $CLUSTER_NAME --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
  - containerPort: 30000
    hostPort: 30000
    protocol: TCP
EOF
            ;;

        minikube)
            if ! command -v minikube &> /dev/null; then
                print_warning "Minikube not found. Installing..."
                curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
                sudo install minikube-linux-amd64 /usr/local/bin/minikube
            fi

            minikube start --profile=$CLUSTER_NAME \
                --addons=ingress,metrics-server \
                --ports=30000:30000
            ;;
    esac

    print_status "✅ Local cluster created"
}

# 2. Install ingress controller
install_ingress() {
    print_status "Installing ingress-nginx..."

    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/kind/deploy.yaml

    # Wait for ingress to be ready
    kubectl wait --namespace ingress-nginx \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/component=controller \
        --timeout=300s

    print_status "✅ Ingress controller installed"
}

# 3. Bootstrap Flux
bootstrap_flux() {
    print_status "Bootstrapping Flux..."

    if ! command -v flux &> /dev/null; then
        print_warning "Flux CLI not found. Installing..."
        curl -s https://fluxcd.io/install.sh | sudo bash
    fi

    # Bootstrap Flux locally (no Git repo needed for local testing)
    flux install --components=source-controller,kustomize-controller,helm-controller

    # Wait for Flux to be ready
    kubectl wait --for=condition=available --timeout=300s deployment/flux-controller-manager -n flux-system

    print_status "✅ Flux bootstrapped"
}

# 4. Deploy cloud emulators
deploy_emulators() {
    print_status "Deploying cloud service emulators..."

    # AWS LocalStack (extended)
    kubectl apply -f infrastructure/tenants/aws/localstack/extended-services.yaml

    # LocalStack Azure (multi-cloud)
    kubectl apply -f infrastructure/tenants/azure/localstack/localstack-azure.yaml

    # GCP Emulators
    kubectl apply -f infrastructure/tenants/gcp/localstack/gcs-emulator.yaml
    kubectl apply -f infrastructure/tenants/gcp/localstack/pubsub-emulator.yaml
    kubectl apply -f infrastructure/tenants/gcp/localstack/firestore-emulator.yaml

    # Additional Azure Emulators
    kubectl apply -f infrastructure/tenants/azure/localstack/azurite.yaml
    kubectl apply -f infrastructure/tenants/azure/localstack/cosmos-emulator.yaml

    print_status "✅ Cloud emulators deployed"
}

# 5. Deploy local workload cluster simulation
deploy_workload_simulation() {
    print_status "Deploying workload cluster simulation..."

    # Create a simulated workload cluster using Kind
    cat <<EOF | kind create cluster --name gitops-workload-local --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "workload-cluster=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 8080
    protocol: TCP
  - containerPort: 443
    hostPort: 8443
    protocol: TCP
EOF

    print_status "✅ Workload cluster simulation created"
}

# 6. Deploy sample workloads
deploy_workloads() {
    print_status "Deploying sample workloads to simulated workload cluster..."

    # Switch to workload cluster context
    kubectl config use-context kind-gitops-workload-local

    # Deploy workloads
    kubectl apply -k infrastructure/tenants/local-testing/workloads-local/

    print_status "✅ Sample workloads deployed"
}

# 7. Setup port forwarding for access
setup_access() {
    print_status "Setting up access to services..."

    # Port forward emulators (in background)
    kubectl port-forward -n localstack svc/localstack 4566:4566 &  # AWS
    kubectl port-forward -n localstack svc/localstack-azure 4567:4567 &  # Azure
    kubectl port-forward -n default svc/gcs-emulator 9023:9023 &
    kubectl port-forward -n default svc/pubsub-emulator 8085:8085 &

    print_status "✅ Port forwarding established"
    print_status "🌐 LocalStack AWS: http://localhost:4566"
    print_status "🌐 LocalStack Azure: http://localhost:4567"
    print_status "🌐 GCS Emulator: http://localhost:9023"
    print_status "🌐 PubSub Emulator: http://localhost:8085"
}

# Main execution
main() {
    create_cluster
    install_ingress
    bootstrap_flux
    deploy_emulators
    deploy_workload_simulation
    deploy_workloads
    setup_access

    echo ""
    echo "============================================="
    echo "🎉 Local Management Cluster Setup Complete!"
    echo "============================================="
    echo ""
    echo "Management Cluster (Control Plane):"
    echo "  Context: kind-$CLUSTER_NAME"
    echo "  Flux: kubectl get pods -n flux-system"
    echo ""
    echo "Workload Cluster (Applications):"
    echo "  Context: kind-gitops-workload-local"
    echo "  Apps: kubectl get pods -A"
    echo ""
    echo "Emulator Endpoints:"
    echo "  AWS LocalStack: http://localhost:4566"
    echo "  Azure LocalStack: http://localhost:4567"
    echo "  GCP Storage: http://localhost:9023"
    echo "  GCP PubSub: http://localhost:8085"
    echo ""
    echo "Test commands:"
    echo "  kubectl config use-context kind-$CLUSTER_NAME  # Switch to management"
    echo "  kubectl config use-context kind-gitops-workload-local  # Switch to workload"
    echo "  ./tests/drift-test.sh  # Run tests"
}

# Run main function
main "$@"

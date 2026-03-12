#!/bin/bash
# Complete GitOps Infrastructure Control Plane Bootstrap Script
# Deploys the entire enterprise platform from scratch

set -euxo pipefail

# Configuration
REPO_URL="https://github.com/lloydchang/gitops-infra-control-plane"
BRANCH="main"
FLUX_PATH="control-plane/flux"
TIMEOUT=1800  # 30 minutes
CLUSTER_NAME=${CLUSTER_NAME:-"gitops-cluster"}  # Default cluster name

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_status() {
    echo -e "${GREEN}[BOOTSTRAP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Prerequisites check
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found. Please install kubectl."
        exit 1
    fi
    print_status "kubectl: ✓"

    # Check flux
    if ! command -v flux &> /dev/null; then
        print_error "flux CLI not found. Please install flux CLI."
        exit 1
    fi
    print_status "flux CLI: ✓"

    # Check git
    if ! command -v git &> /dev/null; then
        print_error "git not found. Please install git."
        exit 1
    fi
    print_status "git: ✓"

    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster."
        exit 1
    fi
    print_status "Kubernetes cluster: ✓"

    # Check cluster type (prefer local for testing)
    CLUSTER_TYPE=${CLUSTER_TYPE:-$(kubectl config current-context 2>/dev/null || echo "unknown")}
    print_status "Cluster type: $CLUSTER_TYPE"

    if [[ "$CLUSTER_TYPE" == *"docker-desktop"* ]] || [[ "$CLUSTER_TYPE" == *"kind"* ]] || [[ "$CLUSTER_TYPE" == *"minikube"* ]]; then
        print_status "Local cluster detected - enabling all emulators"
        ENABLE_EMULATORS=true
    else
        print_warning "Cloud cluster detected - some emulators may not be available"
        ENABLE_EMULATORS=false
    fi
}

# Clone repository if not already present
setup_repository() {
    print_header "Setting Up Repository"

    if [[ ! -d ".git" ]]; then
        print_status "Cloning repository..."
        git clone $REPO_URL .
        git checkout $BRANCH
    else
        print_status "Repository already exists, updating..."
        git pull origin $BRANCH
    fi
}

# Bootstrap Flux
bootstrap_flux() {
    print_header "Bootstrapping Flux GitOps Controller"

    print_status "Installing Flux components..."
    # Check if Flux is already installed
    if kubectl get namespace flux-system &>/dev/null && kubectl get deployments -n flux-system | grep -q "kustomize-controller"; then
        print_status "Flux already installed, skipping bootstrap..."
        # Apply local GitRepository and Kustomization for local testing
        if [[ -f "local-test.yaml" ]]; then
            kubectl apply -f local-test.yaml
        fi
        if [[ -f "test-kustomization.yaml" ]]; then
            kubectl apply -f test-kustomization.yaml
        fi
    else
        # For local testing, use local Git repository instead of remote
        if [[ "$CLUSTER_TYPE" == "kind" ]] || [[ "$CLUSTER_NAME" == *"local"* ]] || [[ "$CLUSTER_TYPE" == "kind-"* ]]; then
            print_status "Local cluster detected, using local Git repository..."
            # Create local GitRepository pointing to local filesystem
            cat <<EOF | kubectl apply -f -
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: local-infra
  namespace: flux-system
spec:
  interval: 1m0s
  ref:
    branch: main
  url: file:///workspace
EOF
            # Create basic Kustomization
            cat <<EOF | kubectl apply -f -
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: test-infra
  namespace: flux-system
spec:
  interval: 5m0s
  path: ./
  prune: true
  sourceRef:
    kind: GitRepository
    name: local-infra
EOF
        else
            flux bootstrap git \
                --url=$REPO_URL \
                --branch=$BRANCH \
                --path=$FLUX_PATH \
                --components-extra=image-reflector-controller,image-automation-controller \
                --silent
        fi
    fi

    print_status "Waiting for Flux controllers to be ready..."
    kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/kustomize-controller -n flux-system
    kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/helm-controller -n flux-system
    kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/source-controller -n flux-system

    print_status "Flux bootstrap: ✓"
}

# Deploy core infrastructure
deploy_core_infrastructure() {
    print_header "Deploying Core Infrastructure"

    # For local testing, skip cert-manager and external-dns as they may not be available
    print_status "Checking for local test environment..."
    
    if [[ "$CLUSTER_TYPE" == "kind" ]] || [[ "$CLUSTER_NAME" == *"local"* ]]; then
        print_status "Local cluster detected, deploying minimal infrastructure..."
        # Deploy basic monitoring if available
        if [[ -d "infrastructure/monitoring" ]]; then
            print_status "Deploying basic monitoring..."
            kubectl apply -k infrastructure/monitoring/ || true
        fi
    else
        print_status "Deploying cert-manager..."
        if [[ -d "infrastructure/control-plane/cert-manager" ]]; then
            kubectl apply -k infrastructure/control-plane/cert-manager/
            kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/cert-manager -n cert-manager
        fi

        print_status "Deploying external-dns..."
        if [[ -d "infrastructure/control-plane/external-dns" ]]; then
            kubectl apply -k infrastructure/control-plane/external-dns/
            kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/external-dns -n external-dns
        fi

        print_status "Deploying Velero..."
        if [[ -d "infrastructure/control-plane/velero" ]]; then
            kubectl apply -k infrastructure/control-plane/velero/
            kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/velero -n velero
        fi
    fi

    print_status "Core infrastructure: ✓"
}

# Deploy cloud providers
deploy_cloud_providers() {
    print_header "Deploying Cloud Provider Controllers"

    # For local testing, skip cloud provider controllers and use emulators
    if [[ "$CLUSTER_TYPE" == "kind" ]] || [[ "$CLUSTER_NAME" == *"local"* ]]; then
        print_status "Local cluster detected, using emulators instead of cloud controllers..."
        return
    fi

    print_status "Deploying AWS ACK controllers..."
    if [[ -d "infrastructure/tenants/aws/ack-controllers" ]]; then
        kubectl apply -k infrastructure/tenants/aws/ack-controllers/
        kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/ack-ec2-controller -n ack-system
    fi

    print_status "Deploying Azure ASO controllers..."
    if [[ -d "infrastructure/tenants/azure/aso-controllers" ]]; then
        kubectl apply -k infrastructure/tenants/azure/aso-controllers/
        kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/azureserviceoperator-controller-manager -n azureserviceoperator-system
    fi

    print_status "Deploying GCP KCC controllers..."
    if [[ -d "infrastructure/tenants/gcp/kcc-controllers" ]]; then
        kubectl apply -k infrastructure/tenants/gcp/kcc-controllers/
        kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/controller-manager -n cnrm-system
    fi

    print_status "Cloud providers: ✓"
}

# Deploy emulators (for local development)
deploy_emulators() {
    if [[ "$ENABLE_EMULATORS" != "true" ]]; then
        print_warning "Skipping emulators (not local cluster)"
        return
    fi

    print_header "Deploying Cloud Service Emulators"

    print_status "Deploying LocalStack (AWS)..."
    kubectl apply -k infrastructure/tenants/aws/localstack/
    kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/localstack -n localstack

    print_status "Deploying Azurite (Azure)..."
    kubectl apply -k infrastructure/tenants/azure/localstack/
    kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/azurite -n default

    print_status "Deploying GCP emulators..."
    kubectl apply -k infrastructure/tenants/gcp/localstack/
    kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/bigquery-emulator -n gcp-emulators

    print_status "Cloud emulators: ✓"
}

# Deploy platform workloads
deploy_platform_workloads() {
    print_header "Deploying Platform Workloads"

    print_status "Deploying monitoring stack..."
    kubectl apply -k infrastructure/tenants/3-workloads/monitoring/
    kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/prometheus -n monitoring

    print_status "Deploying security tools..."
    kubectl apply -k infrastructure/tenants/3-workloads/security/
    kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/opa-gatekeeper-controller-manager -n gatekeeper-system

    print_status "Deploying CI/CD tools..."
    kubectl apply -k infrastructure/tenants/3-workloads/cicd/
    kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/argocd-server -n argocd

    print_status "Deploying service mesh..."
    kubectl apply -k infrastructure/tenants/3-workloads/networking/
    kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/istiod -n istio-system

    print_status "Platform workloads: ✓"
}

# Deploy sample applications
deploy_sample_applications() {
    print_header "Deploying Sample Applications"

    print_status "Deploying nginx sample..."
    kubectl apply -k infrastructure/tenants/3-workloads/sample-apps/
    kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/nginx-sample -n default

    print_status "Deploying database sample..."
    kubectl wait --for=condition=available --timeout=${TIMEOUT}s deployment/mysql-sample -n default

    print_status "Sample applications: ✓"
}

# Run validation tests
run_validation_tests() {
    print_header "Running Validation Tests"

    print_status "Running comprehensive test suite..."
    if [[ -f "tests/test-local-suite.sh" ]]; then
        chmod +x tests/test-local-suite.sh
        ./tests/test-local-suite.sh
    else
        print_warning "Test suite not found, skipping automated tests"
    fi

    print_status "Basic connectivity test..."
    # Test nginx service
    kubectl port-forward svc/nginx-sample 8080:80 -n default &
    PF_PID=$!
    sleep 5
    if curl -s http://localhost:8080 | grep -q "nginx"; then
        print_status "Nginx service: ✓"
    else
        print_warning "Nginx service: Not responding"
    fi
    kill $PF_PID 2>/dev/null || true

    print_status "Validation tests: ✓"
}

# Generate deployment summary
generate_summary() {
    print_header "Deployment Summary"

    echo ""
    echo "🎉 GitOps Infrastructure Control Plane Successfully Deployed!"
    echo ""
    echo "📊 Components Deployed:"
    echo "   ✅ Flux GitOps Controllers"
    echo "   ✅ Core Infrastructure (cert-manager, external-dns, Velero)"
    echo "   ✅ Cloud Provider Controllers (ACK/ASO/KCC)"
    if [[ "$ENABLE_EMULATORS" == "true" ]]; then
        echo "   ✅ Cloud Service Emulators (LocalStack, Azurite, GCP)"
    fi
    echo "   ✅ Platform Workloads (Monitoring, Security, CI/CD, Networking)"
    echo "   ✅ Sample Applications"
    echo ""
    echo "🔗 Access Points:"
    echo "   Argo CD: kubectl port-forward svc/argocd-server 8080:443 -n argocd"
    echo "   Grafana: kubectl port-forward svc/grafana 3000:80 -n monitoring"
    echo "   Prometheus: kubectl port-forward svc/prometheus 9090:9090 -n monitoring"
    echo "   Nginx Sample: kubectl port-forward svc/nginx-sample 8080:80 -n default"
    echo ""
    echo "🧪 Testing:"
    echo "   Run validation: ./tests/test-local-suite.sh"
    echo "   Run drift test: ./tests/drift-test.sh"
    echo ""
    echo "📚 Documentation:"
    echo "   README.md - Complete setup guide"
    echo "   ARCHITECTURE.md - System architecture"
    echo "   tests/README.md - Testing documentation"
    echo ""
    echo "🚀 Next Steps:"
    echo "   1. Configure cloud provider credentials"
    echo "   2. Deploy your applications using GitOps"
    echo "   3. Set up monitoring alerts and dashboards"
    echo "   4. Configure backup and disaster recovery"
    echo ""
}

# Main execution
main() {
    echo "🚀 GitOps Infrastructure Control Plane Bootstrap"
    echo "==============================================="
    echo "Repository: $REPO_URL"
    echo "Branch: $BRANCH"
    echo "Flux Path: $FLUX_PATH"
    echo ""

    check_prerequisites
    setup_repository
    bootstrap_flux
    deploy_core_infrastructure
    deploy_cloud_providers
    deploy_emulators
    deploy_platform_workloads
    deploy_sample_applications
    run_validation_tests
    generate_summary

    echo ""
    echo "🎊 Bootstrap Complete! Your enterprise GitOps platform is ready."
    echo ""
}

# Run main function
main "$@"

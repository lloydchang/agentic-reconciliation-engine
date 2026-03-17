# Argo Workflows CI/CD Automation Scripts
# Helper scripts for CI/CD pipeline automation

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD_NUMBER="${BUILD_NUMBER:-$(date +%s)}"
REGISTRY="${REGISTRY:-ghcr.io}"
IMAGE_NAME="${IMAGE_NAME:-argo-workflows-qwen}"
NAMESPACE="${NAMESPACE:-argo-workflows-ci}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Install required tools
install_tools() {
    log_info "Installing required tools..."
    
    # Install kubectl
    if ! command -v kubectl &> /dev/null; then
        log_info "Installing kubectl..."
        curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
        chmod +x kubectl
        sudo mv kubectl /usr/local/bin/
    fi
    
    # Install kustomize
    if ! command -v kustomize &> /dev/null; then
        log_info "Installing kustomize..."
        curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
        sudo mv kustomize /usr/local/bin/
    fi
    
    # Install kind (if needed)
    if ! command -v kind &> /dev/null; then
        log_info "Installing kind..."
        curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
        chmod +x ./kind
        sudo mv ./kind /usr/local/bin/
    fi
    
    # Install helm (if needed)
    if ! command -v helm &> /dev/null; then
        log_info "Installing helm..."
        curl https://get.helm.sh/helm-v3.12.0-linux-amd64.tar.gz | tar xz
        sudo mv linux-amd64/helm /usr/local/bin/
    fi
    
    # Install shellcheck (if needed)
    if ! command -v shellcheck &> /dev/null; then
        log_info "Installing shellcheck..."
        sudo apt-get update && sudo apt-get install -y shellcheck
    fi
    
    # Install yq (if needed)
    if ! command -v yq &> /dev/null; then
        log_info "Installing yq..."
        sudo wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/download/v4.30.8/yq_linux_amd64
        sudo chmod +x /usr/local/bin/yq
    fi
    
    log_success "Tools installation completed"
}

# Validate YAML files
validate_yaml() {
    log_info "Validating YAML files..."
    
    local yaml_files
    yaml_files=$(find "${REPO_ROOT}/overlay/argo-workflows" -name '*.yaml' -o -name '*.yml')
    
    for file in $yaml_files; do
        if ! yq eval . "$file" > /dev/null 2>&1; then
            log_error "YAML validation failed for $file"
            return 1
        fi
    done
    
    log_success "YAML validation completed"
}

# Validate Kustomize overlays
validate_kustomize() {
    log_info "Validating Kustomize overlays..."
    
    cd "${REPO_ROOT}"
    
    # Validate main overlay
    if ! kustomize build overlay/argo-workflows | kubectl apply --dry-run=client -f - > /dev/null 2>&1; then
        log_error "Kustomize validation failed for main overlay"
        return 1
    fi
    
    # Validate examples
    if ! kustomize build overlay/argo-workflows/examples | kubectl apply --dry-run=client -f - > /dev/null 2>&1; then
        log_error "Kustomize validation failed for examples"
        return 1
    fi
    
    log_success "Kustomize validation completed"
}

# Validate shell scripts
validate_scripts() {
    log_info "Validating shell scripts..."
    
    local scripts=(
        "${REPO_ROOT}/scripts/quickstart-argo-workflows.sh"
        "${REPO_ROOT}/tests/argo-workflows/test-suite.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [[ -f "$script" ]]; then
            if ! shellcheck "$script"; then
                log_error "Shell script validation failed for $script"
                return 1
            fi
        else
            log_warning "Script not found: $script"
        fi
    done
    
    log_success "Shell script validation completed"
}

# Security scanning
security_scan() {
    log_info "Running security scans..."
    
    # Trivy scan
    log_info "Running Trivy vulnerability scan..."
    docker run --rm -v "${REPO_ROOT}:/workdir" aquasec/trivy:latest \
        fs --format json --exit-code 0 /workdir > "${REPO_ROOT}/trivy-results.json" || true
    
    # Parse results
    local high_vulns
    high_vulns=$(python3 -c "
import json
with open('${REPO_ROOT}/trivy-results.json') as f:
    results = json.load(f)

high_vulns = [r for r in results.get('Results', []) 
            if any(v['Severity'] in ['HIGH', 'CRITICAL'] for v in r.get('Vulnerabilities', []))]

if high_vulns:
    print('High or critical vulnerabilities found:')
    for vuln in high_vulns:
        print(f'  {vuln.get(\"Target\", \"Unknown\")}')
    exit(1)
else:
    print('No high or critical vulnerabilities found')
" || true)
    
    if [[ $? -ne 0 ]]; then
        log_error "High or critical vulnerabilities found"
        return 1
    fi
    
    # Kube-score scan
    log_info "Running kube-score scan..."
    docker run --rm -v "${REPO_ROOT}:/workdir" zegl/kube-score:latest \
        score --output-format ci /workdir/overlay/argo-workflows/base/*.yaml \
        /workdir/overlay/argo-workflows/qwen/*.yaml || return 1
    
    log_success "Security scanning completed"
}

# Setup test cluster
setup_cluster() {
    local cluster_type="${1:-kind}"
    
    log_info "Setting up ${cluster_type} cluster..."
    
    case "$cluster_type" in
        "kind")
            kind create cluster --name argo-workflows-ci --wait 30s
            ;;
        "k3s")
            curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
            sudo chmod 644 /etc/rancher/k3s/k3s.yaml
            mkdir -p "$HOME/.kube"
            cp /etc/rancher/k3s/k3s.yaml "$HOME/.kube/config"
            ;;
        *)
            log_error "Unsupported cluster type: $cluster_type"
            return 1
            ;;
    esac
    
    # Verify cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cluster setup failed"
        return 1
    fi
    
    log_success "Cluster setup completed"
}

# Deploy Argo Workflows
deploy_argo_workflows() {
    log_info "Deploying Argo Workflows..."
    
    cd "${REPO_ROOT}"
    
    # Run quickstart script
    if ! ./scripts/quickstart-argo-workflows.sh \
        --namespace "$NAMESPACE" \
        --cluster "auto" \
        --auto-approve; then
        log_error "Argo Workflows deployment failed"
        return 1
    fi
    
    log_success "Argo Workflows deployment completed"
}

# Wait for deployment
wait_for_deployment() {
    log_info "Waiting for deployment to be ready..."
    
    local components=(
        "argo-workflows-controller"
        "argo-workflows-server"
        "qwen-k8sgpt"
    )
    
    for component in "${components[@]}"; do
        log_info "Waiting for $component..."
        if ! kubectl wait --for=condition=available --timeout=600s \
            deployment/"$component" -n "$NAMESPACE"; then
            log_error "Deployment of $component failed"
            return 1
        fi
    done
    
    log_success "All components are ready"
}

# Run tests
run_tests() {
    local test_suite="${1:-all}"
    
    log_info "Running test suite: $test_suite"
    
    cd "${REPO_ROOT}"
    
    if ! ./tests/argo-workflows/test-suite.sh \
        --namespace "$NAMESPACE" \
        --test-suite "$test_suite" \
        --verbose; then
        log_error "Test suite $test_suite failed"
        return 1
    fi
    
    log_success "Test suite $test_suite completed"
}

# Collect artifacts
collect_artifacts() {
    local artifact_dir="${1:-${REPO_ROOT}/artifacts}"
    
    log_info "Collecting artifacts..."
    
    mkdir -p "$artifact_dir"
    
    # Collect logs
    mkdir -p "$artifact_dir/logs"
    kubectl logs -n "$NAMESPACE" deployment/argo-workflows-controller > "$artifact_dir/logs/controller.log"
    kubectl logs -n "$NAMESPACE" deployment/argo-workflows-server > "$artifact_dir/logs/server.log"
    kubectl logs -n "$NAMESPACE" deployment/qwen-k8sgpt > "$artifact_dir/logs/qwen.log"
    
    # Collect workflow information
    kubectl get workflows -n "$NAMESPACE" -o yaml > "$artifact_dir/workflows.yaml"
    kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' > "$artifact_dir/events.log"
    
    # Collect resource information
    kubectl get all -n "$NAMESPACE" -o wide > "$artifact_dir/resources.txt"
    kubectl top pods -n "$NAMESPACE" > "$artifact_dir/metrics.txt"
    
    # Collect test results
    if [[ -f "${REPO_ROOT}/test-results.json" ]]; then
        cp "${REPO_ROOT}/test-results.json" "$artifact_dir/"
    fi
    
    log_success "Artifacts collected to $artifact_dir"
}

# Cleanup cluster
cleanup_cluster() {
    local cluster_type="${1:-kind}"
    
    log_info "Cleaning up cluster..."
    
    # Delete namespace
    kubectl delete namespace "$NAMESPACE" --ignore-not-found=true
    
    # Delete cluster
    case "$cluster_type" in
        "kind")
            kind delete cluster --name argo-workflows-ci
            ;;
        "k3s")
            sudo k3s-uninstall.sh || true
            ;;
    esac
    
    log_success "Cluster cleanup completed"
}

# Build Docker image
build_image() {
    local tag="${1:-${BUILD_NUMBER}}"
    
    log_info "Building Docker image..."
    
    cd "${REPO_ROOT}"
    
    # Build image
    if ! docker build -t "${REGISTRY}/${IMAGE_NAME}:${tag}" .; then
        log_error "Docker build failed"
        return 1
    fi
    
    # Also build latest tag
    if ! docker tag "${REGISTRY}/${IMAGE_NAME}:${tag}" "${REGISTRY}/${IMAGE_NAME}:latest"; then
        log_error "Docker tag failed"
        return 1
    fi
    
    log_success "Docker image built: ${REGISTRY}/${IMAGE_NAME}:${tag}"
}

# Push Docker image
push_image() {
    local tag="${1:-${BUILD_NUMBER}"
    
    log_info "Pushing Docker image..."
    
    # Login to registry
    if [[ -n "${DOCKER_USER:-}" && -n "${DOCKER_PASSWORD:-}" ]]; then
        echo "$DOCKER_PASSWORD" | docker login "$REGISTRY" -u "$DOCKER_USER" --password-stdin
    fi
    
    # Push images
    if ! docker push "${REGISTRY}/${IMAGE_NAME}:${tag}"; then
        log_error "Docker push failed for tag $tag"
        return 1
    fi
    
    if ! docker push "${REGISTRY}/${IMAGE_NAME}:latest"; then
        log_error "Docker push failed for latest tag"
        return 1
    fi
    
    log_success "Docker image pushed: ${REGISTRY}/${IMAGE_NAME}:${tag}"
}

# Deploy to environment
deploy_to_env() {
    local env="${1:-staging}"
    local tag="${2:-${BUILD_NUMBER}}"
    
    log_info "Deploying to $env environment..."
    
    cd "${REPO_ROOT}"
    
    # Update image tag in kustomization
    kustomize edit set image "${REGISTRY}/${IMAGE_NAME}=${REGISTRY}/${IMAGE_NAME}:${tag}"
    
    # Deploy
    if ! kustomize build "overlay/argo-workflows/overlays/$env" | kubectl apply -f -; then
        log_error "Deployment to $env failed"
        return 1
    fi
    
    # Wait for deployment
    if ! kubectl wait --for=condition=available --timeout=600s \
        deployment/argo-workflows-controller -n "argo-workflows-$env"; then
        log_error "Deployment readiness check failed for $env"
        return 1
    fi
    
    log_success "Deployment to $env completed"
}

# Run smoke tests
run_smoke_tests() {
    local env="${1:-staging}"
    
    log_info "Running smoke tests against $env..."
    
    # Switch context if needed
    if [[ -n "${KUBECONFIG_STAGING:-}" && "$env" == "staging" ]]; then
        export KUBECONFIG="$KUBECONFIG_STAGING"
    elif [[ -n "${KUBECONFIG_PRODUCTION:-}" && "$env" == "production" ]]; then
        export KUBECONFIG="$KUBECONFIG_PRODUCTION"
    fi
    
    # Run basic tests
    if ! ./tests/argo-workflows/test-suite.sh \
        --namespace "argo-workflows-$env" \
        --test-suite basic \
        --verbose; then
        log_error "Smoke tests failed for $env"
        return 1
    fi
    
    log_success "Smoke tests passed for $env"
}

# Build documentation
build_docs() {
    log_info "Building documentation..."
    
    cd "${REPO_ROOT}/docs/argo-workflows"
    
    # Install mkdocs if needed
    if ! command -v mkdocs &> /dev/null; then
        pip3 install mkdocs mkdocs-material
    fi
    
    # Build documentation
    if ! mkdocs build --strict; then
        log_error "Documentation build failed"
        return 1
    fi
    
    log_success "Documentation built successfully"
}

# Upload documentation
upload_docs() {
    local docs_server="${1:-docs@docs-server}"
    
    log_info "Uploading documentation..."
    
    cd "${REPO_ROOT}/docs/argo-workflows"
    
    # Upload to documentation server
    if ! rsync -av site/ "${docs_server}:/var/www/argo-workflows/"; then
        log_error "Documentation upload failed"
        return 1
    fi
    
    log_success "Documentation uploaded successfully"
}

# Main execution
main() {
    local command="${1:-help}"
    
    case "$command" in
        "install-tools")
            install_tools
            ;;
        "validate")
            install_tools
            validate_yaml
            validate_kustomize
            validate_scripts
            ;;
        "security-scan")
            security_scan
            ;;
        "setup-cluster")
            setup_cluster "${2:-kind}"
            ;;
        "deploy")
            setup_cluster "${2:-kind}"
            deploy_argo_workflows
            wait_for_deployment
            ;;
        "test")
            run_tests "${2:-all}"
            ;;
        "collect-artifacts")
            collect_artifacts "${2:-}"
            ;;
        "cleanup")
            cleanup_cluster "${2:-kind}"
            ;;
        "build-image")
            build_image "${2:-}"
            ;;
        "push-image")
            push_image "${2:-}"
            ;;
        "deploy-env")
            deploy_to_env "${2:-staging}" "${3:-}"
            ;;
        "smoke-tests")
            run_smoke_tests "${2:-staging}"
            ;;
        "build-docs")
            build_docs
            ;;
        "upload-docs")
            upload_docs "${2:-}"
            ;;
        "full-ci")
            # Full CI pipeline
            install_tools
            validate_yaml
            validate_kustomize
            validate_scripts
            security_scan
            setup_cluster "${2:-kind}"
            deploy_argo_workflows
            wait_for_deployment
            run_tests all
            collect_artifacts
            cleanup_cluster "${2:-kind}"
            ;;
        "help"|*)
            cat << EOF
Argo Workflows CI/CD Automation Scripts

Usage: $0 <command> [options]

Commands:
  install-tools              Install required tools
  validate                   Validate YAML, Kustomize, and scripts
  security-scan             Run security scans
  setup-cluster <type>      Setup test cluster (kind, k3s)
  deploy                    Deploy Argo Workflows to test cluster
  test <suite>             Run test suite (all, basic, qwen, integration, performance, security)
  collect-artifacts <dir>   Collect test artifacts
  cleanup <type>           Cleanup test cluster
  build-image <tag>        Build Docker image
  push-image <tag>         Push Docker image to registry
  deploy-env <env> <tag>   Deploy to environment (staging, production)
  smoke-tests <env>        Run smoke tests against environment
  build-docs               Build documentation
  upload-docs <server>     Upload documentation to server
  full-ci <type>           Run full CI pipeline
  help                      Show this help message

Examples:
  $0 full-ci kind
  $0 setup-cluster kind
  $0 deploy
  $0 test all
  $0 build-image v1.0.0
  $0 deploy-env staging v1.0.0
  $0 smoke-tests staging

Environment Variables:
  BUILD_NUMBER             Build number (default: timestamp)
  REGISTRY                 Docker registry (default: ghcr.io)
  IMAGE_NAME               Image name (default: argo-workflows-qwen)
  NAMESPACE                Kubernetes namespace (default: argo-workflows-ci)
  DOCKER_USER              Docker registry username
  DOCKER_PASSWORD          Docker registry password
  KUBECONFIG_STAGING       Kubeconfig for staging cluster
  KUBECONFIG_PRODUCTION    Kubeconfig for production cluster

EOF
            ;;
    esac
}

# Run main function
main "$@"

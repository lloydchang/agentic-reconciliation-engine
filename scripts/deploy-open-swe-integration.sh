#!/bin/bash

# Open SWE Integration Deployment Script
# Complete deployment of Open SWE integration into GitOps control plane

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OPEN_SWE_DIR="${PROJECT_ROOT}/core/ai/runtime/open-swe-gateway"

NAMESPACE="ai-infrastructure"
GATEWAY_NAME="open-swe-gateway"
BACKUP_DIR="/tmp/open-swe-deploy-backup-$(date +%Y%m%d-%H%M%S)"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."

    # Check required tools
    local tools=("kubectl" "docker" "git")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is not installed or not in PATH"
            exit 1
        fi
    done

    # Check kubectl context
    if ! kubectl cluster-info &> /dev/null; then
        log_error "kubectl is not configured or cluster is not accessible"
        exit 1
    fi

    # Check namespace exists or create it
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_info "Creating namespace $NAMESPACE..."
        kubectl create namespace "$NAMESPACE"
    fi

    # Check if Temporal is available
    if ! kubectl get svc temporal-frontend -n temporal &> /dev/null; then
        log_warning "Temporal service not found in 'temporal' namespace"
        log_warning "Make sure Temporal is deployed before proceeding"
        read -p "Continue anyway? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    log_success "Prerequisites check passed"
}

# Function to build and push Docker image
build_and_push_image() {
    log_step "Building and pushing Docker image..."

    local image_name="gitops-infra-control-plane/open-swe-gateway"
    local image_tag="latest"

    # Build the image
    log_info "Building Docker image..."
    cd "$OPEN_SWE_DIR"
    docker build -t "${image_name}:${image_tag}" .

    # Push to registry (assuming local registry for now)
    log_info "Pushing image to registry..."
    docker tag "${image_name}:${image_tag}" "localhost:5000/${image_name}:${image_tag}"
    docker push "localhost:5000/${image_name}:${image_tag}"

    # Update deployment to use the image
    sed -i.bak "s|image: .*|image: localhost:5000/${image_name}:${image_tag}|g" "${OPEN_SWE_DIR}/k8s/deployment.yaml"

    log_success "Docker image built and pushed"
}

# Function to validate manifests
validate_manifests() {
    log_step "Validating Kubernetes manifests..."

    local manifests=(
        "${OPEN_SWE_DIR}/k8s/deployment.yaml"
        "${OPEN_SWE_DIR}/k8s/service.yaml"
        "${OPEN_SWE_DIR}/k8s/config.yaml"
        "${OPEN_SWE_DIR}/k8s/rbac.yaml"
        "${OPEN_SWE_DIR}/k8s/security.yaml"
    )

    for manifest in "${manifests[@]}"; do
        if [[ ! -f "$manifest" ]]; then
            log_error "Manifest not found: $manifest"
            exit 1
        fi

        # Validate YAML syntax
        if ! kubectl apply --dry-run=client -f "$manifest" &> /dev/null; then
            log_error "Invalid manifest: $manifest"
            kubectl apply --dry-run=client -f "$manifest"
            exit 1
        fi

        log_success "Validated: $(basename "$manifest")"
    done

    log_success "All manifests validated"
}

# Function to create backup
create_backup() {
    log_step "Creating backup of existing resources..."

    mkdir -p "$BACKUP_DIR"

    # Backup existing Open SWE resources if any
    kubectl get all -n "$NAMESPACE" -l component=open-swe-integration -o yaml > "${BACKUP_DIR}/existing-resources.yaml" 2>/dev/null || true
    kubectl get secrets -n "$NAMESPACE" -l component=open-swe-integration -o yaml > "${BACKUP_DIR}/existing-secrets.yaml" 2>/dev/null || true

    log_success "Backup created at: $BACKUP_DIR"
}

# Function to deploy components in order
deploy_components() {
    log_step "Deploying Open SWE integration components..."

    # 1. Deploy RBAC first
    log_info "Deploying RBAC..."
    kubectl apply -f "${OPEN_SWE_DIR}/k8s/rbac.yaml" -n "$NAMESPACE"

    # 2. Deploy security policies
    log_info "Deploying security policies..."
    kubectl apply -f "${OPEN_SWE_DIR}/k8s/security.yaml" -n "$NAMESPACE"

    # 3. Deploy configuration
    log_info "Deploying configuration..."
    kubectl apply -f "${OPEN_SWE_DIR}/k8s/config.yaml" -n "$NAMESPACE"

    # 4. Deploy services
    log_info "Deploying services..."
    kubectl apply -f "${OPEN_SWE_DIR}/k8s/service.yaml" -n "$NAMESPACE"

    # 5. Deploy the application
    log_info "Deploying application..."
    kubectl apply -f "${OPEN_SWE_DIR}/k8s/deployment.yaml" -n "$NAMESPACE"

    log_success "All components deployed"
}

# Function to wait for rollout
wait_for_rollout() {
    log_step "Waiting for deployment rollout..."

    # Wait for deployment to be ready
    log_info "Waiting for deployment to be available..."
    kubectl rollout status deployment/"$GATEWAY_NAME" -n "$NAMESPACE" --timeout=600s

    # Wait for pods to be ready
    log_info "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod -l app="$GATEWAY_NAME" -n "$NAMESPACE" --timeout=300s

    log_success "Deployment rollout completed"
}

# Function to verify deployment
verify_deployment() {
    log_step "Verifying deployment..."

    # Check pod status
    local ready_pods
    ready_pods=$(kubectl get pods -n "$NAMESPACE" -l app="$GATEWAY_NAME" -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' | grep -o "True" | wc -l)

    if [[ "$ready_pods" -lt 3 ]]; then
        log_error "Only $ready_pods pods are ready (expected: 3)"
        kubectl get pods -n "$NAMESPACE" -l app="$GATEWAY_NAME"
        exit 1
    fi

    # Check service endpoints
    local service_ip
    service_ip=$(kubectl get svc "$GATEWAY_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
    if [[ -z "$service_ip" ]]; then
        log_error "Service cluster IP not assigned"
        exit 1
    fi

    # Test health endpoint
    log_info "Testing health endpoint..."
    if ! kubectl run health-test --image=curlimages/curl --rm -i --restart=Never -- \
        curl -f --max-time 30 "http://$GATEWAY_NAME.$NAMESPACE.svc.cluster.local:8080/health" &> /dev/null; then
        log_error "Health check failed"
        kubectl logs -n "$NAMESPACE" -l app="$GATEWAY_NAME" --tail=50
        exit 1
    fi

    log_success "Deployment verification passed"
}

# Function to configure webhooks (optional)
configure_webhooks() {
    log_step "Configuring webhook endpoints..."

    local gateway_url="http://$GATEWAY_NAME.$NAMESPACE.svc.cluster.local:8080"

    log_info "Webhook endpoints configured:"
    echo "  Slack:  POST $gateway_url/webhooks/slack"
    echo "  Linear: POST $gateway_url/webhooks/linear"
    echo "  GitHub: POST $gateway_url/webhooks/github"
    echo "  Health: GET  $gateway_url/health"
    echo "  Metrics: GET $gateway_url/metrics"
    echo ""

    log_warning "⚠️  IMPORTANT: Configure these webhook URLs in your external services:"
    echo "   - Slack App settings"
    echo "   - Linear webhook settings"
    echo "   - GitHub repository webhook settings"
    echo ""

    read -p "Have you configured the webhook URLs? (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_success "Webhook configuration acknowledged"
    else
        log_info "Remember to configure webhook URLs when ready"
    fi
}

# Function to run post-deployment tests
run_post_deployment_tests() {
    log_step "Running post-deployment tests..."

    local test_script="${SCRIPT_DIR}/test-open-swe-integration.sh"

    if [[ -f "$test_script" ]]; then
        log_info "Running integration tests..."
        bash "$test_script" basic
        log_success "Post-deployment tests completed"
    else
        log_warning "Test script not found, skipping tests"
    fi
}

# Function to display deployment summary
display_deployment_summary() {
    log_step "Deployment Summary"

    echo ""
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}              Open SWE Integration Deployed!                  ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    echo -e "${CYAN}🚀 Service URLs:${NC}"
    echo "  Gateway:     http://$GATEWAY_NAME.$NAMESPACE.svc.cluster.local:8080"
    echo "  Load Balancer: $(kubectl get svc ${GATEWAY_NAME}-lb -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo 'Pending')"
    echo "  Metrics:     http://$GATEWAY_NAME.$NAMESPACE.svc.cluster.local:9090/metrics"
    echo ""

    echo -e "${CYAN}📊 Monitoring Commands:${NC}"
    echo "  Status:      ./scripts/monitor-open-swe-integration.sh status"
    echo "  Dashboard:   ./scripts/monitor-open-swe-integration.sh dashboard"
    echo "  Logs:        ./scripts/monitor-open-swe-integration.sh logs"
    echo "  Continuous:  ./scripts/monitor-open-swe-integration.sh continuous"
    echo ""

    echo -e "${CYAN}🧪 Testing Commands:${NC}"
    echo "  Basic:       ./scripts/test-open-swe-integration.sh basic"
    echo "  Webhooks:    ./scripts/test-open-swe-integration.sh webhooks"
    echo "  Full:        ./scripts/test-open-swe-integration.sh all"
    echo ""

    echo -e "${CYAN}🔧 Management Commands:${NC}"
    echo "  Rollback:    ./scripts/rollback-open-swe-integration.sh"
    echo "  Health:      ./scripts/monitor-open-swe-integration.sh report"
    echo ""

    echo -e "${YELLOW}⚠️  Next Steps:${NC}"
    echo "  1. Configure webhook URLs in external services"
    echo "  2. Test webhook integration"
    echo "  3. Monitor system health"
    echo "  4. Set up alerts and monitoring"
    echo ""

    echo -e "${GREEN}✅ Deployment successful!${NC}"
}

# Function to handle deployment failure
handle_deployment_failure() {
    log_error "Deployment failed!"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check pod status: kubectl get pods -n $NAMESPACE -l app=$GATEWAY_NAME"
    echo "2. Check pod logs: kubectl logs -n $NAMESPACE -l app=$GATEWAY_NAME --tail=100"
    echo "3. Check events: kubectl get events -n $NAMESPACE --sort-by=.metadata.creationTimestamp"
    echo "4. Rollback if needed: ./scripts/rollback-open-swe-integration.sh"
    echo ""
    echo "Backup available at: $BACKUP_DIR"
    exit 1
}

# Main deployment function
main() {
    local skip_build="${SKIP_BUILD:-false}"
    local skip_tests="${SKIP_TESTS:-false}"

    log_info "Starting Open SWE Integration Deployment..."
    log_info "Namespace: $NAMESPACE"
    log_info "Gateway: $GATEWAY_NAME"

    # Set up error handling
    trap handle_deployment_failure ERR

    # Execute deployment steps
    check_prerequisites

    if [[ "$skip_build" != "true" ]]; then
        build_and_push_image
    else
        log_info "Skipping Docker build (SKIP_BUILD=true)"
    fi

    validate_manifests
    create_backup
    deploy_components
    wait_for_rollout
    verify_deployment

    if [[ "$skip_tests" != "true" ]]; then
        run_post_deployment_tests
    else
        log_info "Skipping post-deployment tests (SKIP_TESTS=true)"
    fi

    configure_webhooks
    display_deployment_summary

    log_success "🎉 Open SWE Integration deployment completed successfully!"
}

# Run main function
main "$@"

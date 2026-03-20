#!/bin/bash
# Multi-Architecture Container Build Pipeline

set -e

# Configuration
REGISTRY="${REGISTRY:-agentic-reconciliation-engine}"
PLATFORMS="linux/amd64,linux/arm64"
BUILDX_BUILDER="${BUILDX_BUILDER:-multi-arch-builder}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Ensure buildx is available
check_buildx() {
    if ! docker buildx version >/dev/null 2>&1; then
        log_error "Docker Buildx is not available. Please install it first."
        exit 1
    fi
}

# Setup multi-arch builder
setup_builder() {
    if ! docker buildx ls | grep -q "$BUILDX_BUILDER"; then
        log_info "Creating buildx builder: $BUILDX_BUILDER"
        docker buildx create --name "$BUILDX_BUILDER" --use
    else
        log_info "Using existing buildx builder: $BUILDX_BUILDER"
        docker buildx use "$BUILDX_BUILDER"
    fi

    # Bootstrap the builder
    docker buildx inspect --bootstrap
}

# Build and push multi-arch image
build_multi_arch() {
    local dockerfile="$1"
    local context="$2"
    local image_name="$3"
    local tag="${4:-latest}"

    log_info "Building multi-arch image: $REGISTRY/$image_name:$tag"
    log_info "Dockerfile: $dockerfile"
    log_info "Context: $context"
    log_info "Platforms: $PLATFORMS"

    docker buildx build \
        --platform "$PLATFORMS" \
        --file "$dockerfile" \
        --context "$context" \
        --tag "$REGISTRY/$image_name:$tag" \
        --push \
        --progress plain

    if [ $? -eq 0 ]; then
        log_info "Successfully built and pushed: $REGISTRY/$image_name:$tag"
    else
        log_error "Failed to build: $REGISTRY/$image_name:$tag"
        return 1
    fi
}

# Build core services
build_core_services() {
    log_info "Building core services..."

    # API Service
    build_multi_arch \
        "core/docker/Dockerfile.api" \
        "." \
        "api"

    # Dashboard Service
    build_multi_arch \
        "core/dashboard/docker/Dockerfile.dashboard" \
        "." \
        "dashboard"

    # Pi-Mono Agent
    build_multi_arch \
        "core/ai/runtime/pi-mono-agent/Dockerfile" \
        "." \
        "pi-mono-agent"
}

# Build agent services
build_agent_services() {
    log_info "Building agent services..."

    # Cost Optimizer (Rust)
    if [ -f "core/ai/agents/cost-optimizer/Dockerfile" ]; then
        build_multi_arch \
            "core/ai/agents/cost-optimizer/Dockerfile" \
            "core/ai/agents/cost-optimizer" \
            "cost-optimizer-agent"
    fi

    # Security Scanner (Go)
    if [ -f "core/ai/agents/security-scanner/Dockerfile" ]; then
        build_multi_arch \
            "core/ai/agents/security-scanner/Dockerfile" \
            "core/ai/agents/security-scanner" \
            "security-scanner-agent"
    fi

    # Autonomous Decision Engine
    if [ -f "core/ai/agents/autonomous-decision-engine/Dockerfile" ]; then
        build_multi_arch \
            "core/ai/agents/autonomous-decision-engine/Dockerfile" \
            "core/ai/agents/autonomous-decision-engine" \
            "autonomous-decision-engine"
    fi

    # Swarm Coordinator
    if [ -f "core/ai/agents/swarm-coordinator/Dockerfile" ]; then
        build_multi_arch \
            "core/ai/agents/swarm-coordinator/Dockerfile" \
            "core/ai/agents/swarm-coordinator" \
            "swarm-coordinator"
    fi
}

# Build runtime services
build_runtime_services() {
    log_info "Building runtime services..."

    # Temporal Worker
    if [ -f "core/ai/workers/temporal/Dockerfile" ]; then
        build_multi_arch \
            "core/ai/workers/temporal/Dockerfile" \
            "core/ai/workers/temporal" \
            "temporal-worker"
    fi

    # OpenSWE Gateway
    if [ -f "core/ai/runtime/open-swe-gateway/Dockerfile" ]; then
        build_multi_arch \
            "core/ai/runtime/open-swe-gateway/Dockerfile" \
            "core/ai/runtime/open-swe-gateway" \
            "open-swe-gateway"
    fi

    # OpenSWE Integration
    if [ -f "core/ai/runtime/open-swe-integration/Dockerfile" ]; then
        build_multi_arch \
            "core/ai/runtime/open-swe-integration/Dockerfile" \
            "core/ai/runtime/open-swe-integration" \
            "open-swe-integration"
    fi

    # Dashboard Backend
    if [ -f "core/ai/runtime/dashboard/Dockerfile" ]; then
        build_multi_arch \
            "core/ai/runtime/dashboard/Dockerfile" \
            "." \
            "dashboard-backend"
    fi
}

# Main build function
main() {
    log_info "Starting multi-architecture container build pipeline"

    check_buildx
    setup_builder

    # Build all service categories
    build_core_services
    build_agent_services
    build_runtime_services

    log_info "Multi-architecture build pipeline completed successfully"
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

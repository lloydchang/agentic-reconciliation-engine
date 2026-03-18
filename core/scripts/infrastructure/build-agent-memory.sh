#!/bin/bash

# Build script for agent-memory-rust with Qwen LLM integration

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
AGENT_MEMORY_DIR="${REPO_ROOT}/core/ai/runtime/backend/agent-memory-rust"
IMAGE_NAME="agent-memory-rust"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-localhost:5000}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Rust
    if ! command -v cargo &> /dev/null; then
        log_error "cargo is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check if agent-memory-rust directory exists
    if [[ ! -d "${AGENT_MEMORY_DIR}" ]]; then
        log_error "agent-memory-rust directory not found at ${AGENT_MEMORY_DIR}"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Build Rust binary
build_rust_binary() {
    log_info "Building Rust binary..."
    
    cd "${AGENT_MEMORY_DIR}"
    
    # Create config directory if it doesn't exist
    mkdir -p config
    
    # Build in release mode
    cargo build --release
    
    if [[ $? -eq 0 ]]; then
        log_success "Rust binary built successfully"
    else
        log_error "Failed to build Rust binary"
        exit 1
    fi
}

# Run tests
run_tests() {
    log_info "Running tests..."
    
    cd "${AGENT_MEMORY_DIR}"
    
    cargo test
    
    if [[ $? -eq 0 ]]; then
        log_success "All tests passed"
    else
        log_warning "Some tests failed"
    fi
}

# Build Docker image
build_docker_image() {
    log_info "Building Docker image..."
    
    cd "${AGENT_MEMORY_DIR}"
    
    docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
    
    if [[ $? -eq 0 ]]; then
        log_success "Docker image built successfully: ${IMAGE_NAME}:${IMAGE_TAG}"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

# Tag and push to registry
push_to_registry() {
    if [[ "${PUSH_TO_REGISTRY:-false}" == "true" ]]; then
        log_info "Pushing image to registry..."
        
        # Tag for registry
        docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
        
        # Push to registry
        docker push "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
        
        if [[ $? -eq 0 ]]; then
            log_success "Image pushed to registry: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
        else
            log_error "Failed to push image to registry"
            exit 1
        fi
    fi
}

# Run integration tests
run_integration_tests() {
    if [[ "${RUN_INTEGRATION_TESTS:-false}" == "true" ]]; then
        log_info "Running integration tests..."
        
        # Start the service
        cd "${AGENT_MEMORY_DIR}"
        docker run -d --name agent-memory-test \
            -p 8080:8080 \
            -p 9090:9090 \
            -v "$(pwd)/test-data:/data" \
            "${IMAGE_NAME}:${IMAGE_TAG}"
        
        # Wait for service to start
        sleep 10
        
        # Run health check
        if curl -f http://localhost:8080/api/health; then
            log_success "Health check passed"
        else
            log_error "Health check failed"
            docker logs agent-memory-test
            docker stop agent-memory-test
            docker rm agent-memory-test
            exit 1
        fi
        
        # Cleanup
        docker stop agent-memory-test
        docker rm agent-memory-test
        
        log_success "Integration tests passed"
    fi
}

# Generate documentation
generate_docs() {
    if [[ "${GENERATE_DOCS:-false}" == "true" ]]; then
        log_info "Generating documentation..."
        
        cd "${AGENT_MEMORY_DIR}"
        cargo doc --no-deps --open
        
        log_success "Documentation generated"
    fi
}

# Clean build artifacts
clean_artifacts() {
    if [[ "${CLEAN:-false}" == "true" ]]; then
        log_info "Cleaning build artifacts..."
        
        cd "${AGENT_MEMORY_DIR}"
        cargo clean
        
        # Remove Docker images
        docker rmi "${IMAGE_NAME}:${IMAGE_TAG}" 2>/dev/null || true
        docker rmi "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}" 2>/dev/null || true
        
        log_success "Build artifacts cleaned"
    fi
}

# Show build information
show_build_info() {
    log_info "Build Information:"
    echo "  Image: ${IMAGE_NAME}:${IMAGE_TAG}"
    echo "  Registry: ${REGISTRY}"
    echo "  Source: ${AGENT_MEMORY_DIR}"
    echo "  Binary: ${AGENT_MEMORY_DIR}/target/release/agent-memory"
    echo
}

# Main function
main() {
    local action="${1:-build}"
    
    case "${action}" in
        "build")
            show_build_info
            check_prerequisites
            build_rust_binary
            run_tests
            build_docker_image
            push_to_registry
            run_integration_tests
            log_success "Build completed successfully!"
            ;;
        "test")
            check_prerequisites
            run_tests
            run_integration_tests
            ;;
        "docker")
            build_docker_image
            push_to_registry
            ;;
        "clean")
            clean_artifacts
            ;;
        "docs")
            generate_docs
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [build|test|docker|clean|docs|help]"
            echo
            echo "Actions:"
            echo "  build   - Build Rust binary, run tests, and build Docker image (default)"
            echo "  test    - Run unit and integration tests"
            echo "  docker  - Build and push Docker image only"
            echo "  clean   - Clean build artifacts"
            echo "  docs    - Generate documentation"
            echo "  help    - Show this help message"
            echo
            echo "Environment Variables:"
            echo "  IMAGE_TAG                    - Docker image tag (default: latest)"
            echo "  REGISTRY                     - Container registry (default: localhost:5000)"
            echo "  PUSH_TO_REGISTRY              - Push to registry (default: false)"
            echo "  RUN_INTEGRATION_TESTS        - Run integration tests (default: false)"
            echo "  GENERATE_DOCS                - Generate documentation (default: false)"
            echo "  CLEAN                        - Clean artifacts (default: false)"
            echo
            echo "Examples:"
            echo "  $0                           # Full build"
            echo "  $0 test                      # Run tests only"
            echo "  IMAGE_TAG=v1.0.0 $0         # Build with specific tag"
            echo "  PUSH_TO_REGISTRY=true $0     # Build and push to registry"
            ;;
        *)
            echo "Unknown action: ${action}"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"

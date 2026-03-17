#!/bin/bash

# Flagger Quickstart Script
# Quick setup for Flagger progressive delivery with AI integration

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROVIDER="${PROVIDER:-istio}"
NAMESPACE="${NAMESPACE:-flagger-system}"
EXAMPLE_APP="${EXAMPLE_APP:-frontend}"

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

# Quick installation
quick_install() {
    log_info "Starting Flagger quickstart with ${PROVIDER} provider..."
    
    # Run main setup script
    "${SCRIPT_DIR}/setup-flagger.sh" install "${PROVIDER}"
    
    log_success "Flagger quickstart completed!"
    show_quickstart_info
}

# Show quickstart information
show_quickstart_info() {
    echo
    echo "🚀 Flagger Quickstart Complete!"
    echo
    echo "📊 Monitoring:"
    echo "  - Flagger metrics: http://localhost:8080/metrics"
    echo "  - Prometheus: kubectl port-forward -n monitoring svc/prometheus-service 9090:9090"
    echo
    echo "🎯 Example Application:"
    echo "  - Namespace: examples"
    echo "  - Application: ${EXAMPLE_APP}"
    echo "  - Canary: kubectl get canary ${EXAMPLE_APP} -n examples"
    echo
    echo "🔧 Next Commands:"
    echo "  # Trigger canary deployment"
    echo "  kubectl set image deployment/${EXAMPLE_APP} ${EXAMPLE_APP}=nginx:1.21 -n examples"
    echo
    echo "  # Monitor canary progress"
    echo "  kubectl get canary ${EXAMPLE_APP} -n examples -w"
    echo
    echo "  # View Flagger logs"
    echo "  kubectl logs -n ${NAMESPACE} deployment/flagger -f"
    echo
    echo "📚 Documentation:"
    echo "  - Quickstart Guide: ${REPO_ROOT}/docs/flagger-quickstart.md"
    echo "  - Automation Guide: ${REPO_ROOT}/docs/flagger-automation-guide.md"
    echo "  - AI Skill: ${REPO_ROOT}/core/ai/skills/flagger-automation/SKILL.md"
    echo
}

# Test canary deployment
test_canary() {
    log_info "Testing canary deployment..."
    
    # Update image to trigger canary
    kubectl set image deployment/${EXAMPLE_APP} ${EXAMPLE_APP}=nginx:1.21 -n examples
    
    # Wait for canary to start
    log_info "Waiting for canary to start..."
    sleep 10
    
    # Show canary status
    log_info "Canary status:"
    kubectl get canary ${EXAMPLE_APP} -n examples
    
    log_success "Canary deployment test initiated!"
}

# Show AI integration info
show_ai_info() {
    log_info "AI Integration Information:"
    echo
    echo "🤖 K8sGPT with Qwen LLM:"
    echo "  - Model: qwen2.5-7b-instruct"
    echo "  - Backend: LocalAI"
    echo "  - Integration: Automated analysis and recommendations"
    echo
    echo "🧠 AI Skill Usage:"
    echo "  curl -X POST 'http://ai-agent:8080/api/skills/flagger-automation/execute' \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{"
    echo "      \"operation\": \"analyze_flagger_deployment\","
    echo "      \"deployment_name\": \"${EXAMPLE_APP}\","
    echo "      \"namespace\": \"examples\""
    echo "    }'"
    echo
    echo "📊 Automated Analysis:"
    echo "  python3 ${REPO_ROOT}/core/ai/skills/flagger-automation/scripts/qwen_k8sgpt_integration.py"
    echo
}

# Main function
main() {
    local action="${1:-quickstart}"
    
    case "${action}" in
        "quickstart"|"install")
            quick_install
            ;;
        "test")
            test_canary
            ;;
        "ai-info")
            show_ai_info
            ;;
        "help"|"-h"|"--help")
            echo "Flagger Quickstart Script"
            echo
            echo "Usage: $0 [quickstart|test|ai-info|help]"
            echo
            echo "Actions:"
            echo "  quickstart  - Quick installation and setup (default)"
            echo "  test        - Test canary deployment"
            echo "  ai-info     - Show AI integration information"
            echo "  help        - Show this help message"
            echo
            echo "Environment Variables:"
            echo "  PROVIDER        - Traffic provider (istio, nginx, linkerd) [default: istio]"
            echo "  NAMESPACE       - Flagger namespace [default: flagger-system]"
            echo "  EXAMPLE_APP     - Example application name [default: frontend]"
            echo
            echo "Examples:"
            echo "  $0                    # Quickstart with Istio"
            echo "  PROVIDER=nginx $0     # Quickstart with NGINX"
            echo "  $0 test               # Test canary deployment"
            echo "  $0 ai-info            # Show AI integration info"
            ;;
        *)
            echo "Unknown action: ${action}"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

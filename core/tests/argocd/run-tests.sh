#!/bin/bash

# Argo CD Integration Test Runner
# This script runs the comprehensive test suite for Argo CD + K8sGPT + Qwen integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_SCRIPT="$SCRIPT_DIR/test_argocd_integration.py"
REPORT_DIR="$PROJECT_ROOT/test-reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$REPORT_DIR/argocd-test-report-$TIMESTAMP.md"

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

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check test script
    if [ ! -f "$TEST_SCRIPT" ]; then
        log_error "Test script not found: $TEST_SCRIPT"
        exit 1
    fi
    
    # Create report directory
    mkdir -p "$REPORT_DIR"
    
    log_success "Prerequisites check passed"
}

setup_port_forwarding() {
    log_info "Setting up port forwarding..."
    
    # Function to start port forwarding
    start_port_forward() {
        local service=$1
        local namespace=$2
        local local_port=$3
        local remote_port=$4
        local pid_file="/tmp/${service}-test-pf.pid"
        
        # Kill existing port forwarding if running
        if [ -f "$pid_file" ]; then
            kill $(cat "$pid_file") 2>/dev/null || true
            rm -f "$pid_file"
        fi
        
        # Start new port forwarding
        kubectl port-forward svc/$service -n $namespace $local_port:$remote_port &
        echo $! > "$pid_file"
        sleep 2
        
        # Check if port forwarding is working
        if ! nc -z localhost $local_port 2>/dev/null; then
            log_warning "Port forwarding for $service may not be working"
        fi
    }
    
    # Start port forwarding for Argo CD and K8sGPT
    start_port_forward argocd-server argocd 8080 443
    start_port_forward k8sgpt k8sgpt-system 8081 8080
    
    log_success "Port forwarding started"
}

cleanup_port_forwarding() {
    log_info "Cleaning up port forwarding..."
    
    # Kill port forwarding processes
    for service in argocd-server k8sgpt; do
        pid_file="/tmp/${service}-test-pf.pid"
        if [ -f "$pid_file" ]; then
            kill $(cat "$pid_file") 2>/dev/null || true
            rm -f "$pid_file"
        fi
    done
    
    log_success "Port forwarding cleaned up"
}

run_unit_tests() {
    log_info "Running unit tests..."
    
    # Test Python syntax
    python3 -m py_compile "$TEST_SCRIPT"
    if [ $? -eq 0 ]; then
        log_success "Python syntax check passed"
    else
        log_error "Python syntax check failed"
        return 1
    fi
    
    # Test imports
    python3 -c "import requests, yaml, subprocess; print('All imports successful')"
    if [ $? -eq 0 ]; then
        log_success "Import tests passed"
    else
        log_error "Import tests failed"
        return 1
    fi
}

run_integration_tests() {
    log_info "Running integration tests..."
    
    # Set up port forwarding
    setup_port_forwarding
    
    # Run the test suite
    cd "$PROJECT_ROOT"
    
    local test_args=("$TEST_SCRIPT" "--output" "$REPORT_FILE")
    
    if [ "$VERBOSE" = "true" ]; then
        test_args+=("--verbose")
    fi
    
    if [ -n "$SPECIFIC_TEST" ]; then
        test_args+=("--test" "$SPECIFIC_TEST")
    fi
    
    # Run tests
    if python3 "${test_args[@]}"; then
        log_success "Integration tests completed"
        return 0
    else
        log_error "Integration tests failed"
        return 1
    fi
}

run_performance_tests() {
    log_info "Running performance tests..."
    
    # Test API response times
    local endpoints=(
        "http://localhost:8080/healthz"
        "http://localhost:8081/healthz"
    )
    
    for endpoint in "${endpoints[@]}"; do
        log_info "Testing endpoint: $endpoint"
        
        # Measure response time
        local start_time=$(date +%s%N)
        if curl -s "$endpoint" > /dev/null; then
            local end_time=$(date +%s%N)
            local response_time=$((($end_time - $start_time) / 1000000)) # Convert to milliseconds
            
            if [ $response_time -lt 1000 ]; then
                log_success "Endpoint $endpoint: ${response_time}ms (good)"
            elif [ $response_time -lt 5000 ]; then
                log_warning "Endpoint $endpoint: ${response_time}ms (acceptable)"
            else
                log_warning "Endpoint $endpoint: ${response_time}ms (slow)"
            fi
        else
            log_error "Endpoint $endpoint: not accessible"
        fi
    done
}

run_security_tests() {
    log_info "Running security tests..."
    
    # Check for exposed credentials
    log_info "Checking for exposed credentials..."
    
    # Check Argo CD default password
    local argocd_password=$(kubectl -n argocd get secret argocd-secret -o jsonpath="{.data.admin.password}" 2>/dev/null | base64 -d)
    if [ "$argocd_password" = "argocd123" ]; then
        log_warning "Argo CD is using default password - should be changed in production"
    fi
    
    # Check for insecure configurations
    log_info "Checking for insecure configurations..."
    
    # Check if Argo CD is running in insecure mode
    if kubectl -n argocd get deployment argocd-server -o yaml | grep -q "ARGOCD_SERVER_INSECURE.*true"; then
        log_warning "Argo CD is running in insecure mode - should be disabled in production"
    fi
    
    # Check network policies
    local network_policies=$(kubectl get networkpolicies --all-namespaces --no-headers | wc -l)
    if [ "$network_policies" -eq 0 ]; then
        log_warning "No network policies found - consider implementing network segmentation"
    fi
    
    log_success "Security tests completed"
}

generate_summary_report() {
    log_info "Generating summary report..."
    
    if [ ! -f "$REPORT_FILE" ]; then
        log_error "Test report not found: $REPORT_FILE"
        return 1
    fi
    
    # Add additional metadata to report
    local temp_file=$(mktemp)
    cat > "$temp_file" << EOF

# Additional Test Information

## Test Environment
- Timestamp: $(date)
- Kubernetes Cluster: $(kubectl config current-context)
- Python Version: $(python3 --version)
- Test Script: $TEST_SCRIPT

## Performance Summary
$(run_performance_tests 2>&1 | sed 's/^/    /')

## Security Summary
$(run_security_tests 2>&1 | sed 's/^/    /')

## Recommendations
1. Review any failed tests and fix underlying issues
2. Consider implementing automated testing in CI/CD pipeline
3. Monitor performance metrics in production
4. Implement security best practices
5. Regular backup of Argo CD configurations

EOF
    
    # Append to existing report
    cat "$REPORT_FILE" "$temp_file" > "${REPORT_FILE}.tmp"
    mv "${REPORT_FILE}.tmp" "$REPORT_FILE"
    rm "$temp_file"
    
    log_success "Summary report generated: $REPORT_FILE"
}

show_help() {
    cat << EOF
Argo CD Integration Test Runner

Usage: $0 [OPTIONS]

Options:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -t, --test TEST         Run specific test
    -u, --unit-only         Run only unit tests
    -i, --integration-only  Run only integration tests
    -p, --performance-only  Run only performance tests
    -s, --security-only     Run only security tests
    -o, --output FILE       Custom output file for report

Available Tests:
    argo_cd_installation
    k8sgpt_installation
    qwen_model_availability
    k8sgpt_analysis
    argocd_applications
    gitops_workflow
    monitoring_integration

Examples:
    $0                                    # Run all tests
    $0 -v                                # Run all tests with verbose output
    $0 -t k8sgpt_analysis               # Run specific test
    $0 -u                               # Run only unit tests
    $0 -o /tmp/custom-report.md        # Custom report location

EOF
}

# Main execution
main() {
    # Parse command line arguments
    VERBOSE="false"
    SPECIFIC_TEST=""
    UNIT_ONLY="false"
    INTEGRATION_ONLY="false"
    PERFORMANCE_ONLY="false"
    SECURITY_ONLY="false"
    CUSTOM_OUTPUT=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--verbose)
                VERBOSE="true"
                shift
                ;;
            -t|--test)
                SPECIFIC_TEST="$2"
                shift 2
                ;;
            -u|--unit-only)
                UNIT_ONLY="true"
                shift
                ;;
            -i|--integration-only)
                INTEGRATION_ONLY="true"
                shift
                ;;
            -p|--performance-only)
                PERFORMANCE_ONLY="true"
                shift
                ;;
            -s|--security-only)
                SECURITY_ONLY="true"
                shift
                ;;
            -o|--output)
                CUSTOM_OUTPUT="$2"
                REPORT_FILE="$2"
                shift 2
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Set up cleanup trap
    trap cleanup_port_forwarding EXIT
    
    log_info "Starting Argo CD integration test runner..."
    
    # Check prerequisites
    check_prerequisites
    
    # Run tests based on options
    local exit_code=0
    
    if [ "$UNIT_ONLY" = "true" ]; then
        run_unit_tests || exit_code=1
    elif [ "$INTEGRATION_ONLY" = "true" ]; then
        run_integration_tests || exit_code=1
    elif [ "$PERFORMANCE_ONLY" = "true" ]; then
        run_performance_tests
    elif [ "$SECURITY_ONLY" = "true" ]; then
        run_security_tests
    else
        # Run all tests
        run_unit_tests || exit_code=1
        run_integration_tests || exit_code=1
        run_performance_tests
        run_security_tests
        generate_summary_report
    fi
    
    # Show results
    if [ $exit_code -eq 0 ]; then
        log_success "All tests completed successfully!"
        if [ -f "$REPORT_FILE" ]; then
            log_info "Test report available at: $REPORT_FILE"
        fi
    else
        log_error "Some tests failed. Check the report for details."
        if [ -f "$REPORT_FILE" ]; then
            log_info "Test report available at: $REPORT_FILE"
        fi
    fi
    
    exit $exit_code
}

# Run main function
main "$@"

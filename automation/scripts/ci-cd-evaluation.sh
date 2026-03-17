#!/bin/bash
# AI Agent Evaluation CI/CD Integration Script
# Integrates evaluation framework into CI/CD pipelines

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EVALUATION_DIR="$PROJECT_ROOT/agent-tracing-evaluation"

# Default values
EVALUATORS="${EVALUATORS:-skill_invocation,performance,cost,monitoring,health_check}"
TRACE_COUNT="${TRACE_COUNT:-100}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-json}"
REPORTS_DIR="${REPORTS_DIR:-evaluation-reports}"
QUALITY_GATE_SCORE="${QUALITY_GATE_SCORE:-0.8}"
QUALITY_GATE_PASS_RATE="${QUALITY_GATE_PASS_RATE:-0.85}"

# Logging functions
print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is required but not installed"
        exit 1
    fi
    
    # Check evaluation directory
    if [[ ! -d "$EVALUATION_DIR" ]]; then
        print_error "Evaluation directory not found: $EVALUATION_DIR"
        exit 1
    fi
    
    print_success "Prerequisites satisfied"
}

# Install dependencies
install_dependencies() {
    print_header "Installing Dependencies"
    
    cd "$EVALUATION_DIR"
    
    # Install requirements
    if pip3 install -r requirements.txt; then
        print_success "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
}

# Run tests
run_tests() {
    print_header "Running Tests"
    
    cd "$EVALUATION_DIR"
    
    # Run test suite
    if python3 tests/test_evaluators.py; then
        print_success "All tests passed"
    else
        print_error "Tests failed"
        exit 1
    fi
}

# Generate sample traces
generate_traces() {
    print_header "Generating Sample Traces"
    
    cd "$EVALUATION_DIR"
    
    # Generate sample data
    if python3 cli.py --generate-sample "$TRACE_COUNT" --file evaluation_traces.json; then
        print_success "Generated $TRACE_COUNT sample traces"
    else
        print_error "Failed to generate sample traces"
        exit 1
    fi
}

# Run evaluation
run_evaluation() {
    print_header "Running Evaluation"
    
    cd "$EVALUATION_DIR"
    
    # Run evaluation with specified evaluators
    if python3 cli.py --file evaluation_traces.json --evaluators "$EVALUATORS" --format "$OUTPUT_FORMAT" --output evaluation_results.json; then
        print_success "Evaluation completed successfully"
    else
        print_error "Evaluation failed"
        exit 1
    fi
}

# Generate visualizations
generate_visualizations() {
    print_header "Generating Visualizations"
    
    cd "$EVALUATION_DIR"
    
    # Create reports directory
    mkdir -p "$REPORTS_DIR"
    
    # Generate visualizations
    if python3 cli.py --file evaluation_traces.json --visualize --report-dir "$REPORTS_DIR"; then
        print_success "Visualizations generated in $REPORTS_DIR"
    else
        print_warning "Visualization generation failed (non-critical)"
    fi
}

# Check quality gates
check_quality_gates() {
    print_header "Checking Quality Gates"
    
    cd "$EVALUATION_DIR"
    
    # Parse evaluation results
    if [[ ! -f "evaluation_results.json" ]]; then
        print_error "Evaluation results file not found"
        exit 1
    fi
    
    # Extract metrics using Python
    python3 -c "
import json
import sys

with open('evaluation_results.json', 'r') as f:
    results = json.load(f)

summary = results.get('summary', {})
overall_score = summary.get('overall_score', 0)
pass_rate = summary.get('overall_pass_rate', 0)
total_evaluations = summary.get('total_evaluations', 0)

print(f'OVERALL_SCORE={overall_score}')
print(f'PASS_RATE={pass_rate}')
print(f'TOTAL_EVALUATIONS={total_evaluations}')

# Write to environment file
with open('evaluation_metrics.env', 'w') as f:
    f.write(f'OVERALL_SCORE={overall_score}\n')
    f.write(f'PASS_RATE={pass_rate}\n')
    f.write(f'TOTAL_EVALUATIONS={total_evaluations}\n')
" > /dev/null
    
    # Load metrics
    source evaluation_metrics.env
    
    print_info "Evaluation Results:"
    print_info "  Overall Score: $OVERALL_SCORE"
    print_info "  Pass Rate: $PASS_RATE"
    print_info "  Total Evaluations: $TOTAL_EVALUATIONS"
    
    # Check quality gates
    local failed=false
    
    # Score gate
    if (( $(echo "$OVERALL_SCORE < $QUALITY_GATE_SCORE" | bc -l) )); then
        print_error "FAIL: Overall score below threshold ($OVERALL_SCORE < $QUALITY_GATE_SCORE)"
        failed=true
    fi
    
    # Pass rate gate
    if (( $(echo "$PASS_RATE < $QUALITY_GATE_PASS_RATE" | bc -l) )); then
        print_error "FAIL: Pass rate below threshold ($PASS_RATE < $QUALITY_GATE_PASS_RATE)"
        failed=true
    fi
    
    if [[ "$failed" == "true" ]]; then
        print_error "Quality gates failed"
        exit 1
    else
        print_success "All quality gates passed"
    fi
}

# Generate reports
generate_reports() {
    print_header "Generating Reports"
    
    cd "$EVALUATION_DIR"
    
    # Load metrics
    source evaluation_metrics.env
    
    # Create summary report
    cat > evaluation_summary.md << EOF
# AI Agent Evaluation Summary

## 📊 Results
- **Overall Score**: $OVERALL_SCORE
- **Pass Rate**: $PASS_RATE
- **Total Evaluations**: $TOTAL_EVALUATIONS

## 🎯 Quality Gates
- ✅ Overall Score ≥ $QUALITY_GATE_SCORE
- ✅ Pass Rate ≥ $QUALITY_GATE_PASS_RATE

## 📈 Performance
This evaluation was run on $(date) with $TRACE_COUNT sample traces.

## 🔧 Evaluators
The following evaluators were run: $EVALUATORS

## 📋 Details
See the generated visualizations and detailed results for more information.

## 🚀 Next Steps
1. Review the evaluation results
2. Check any failed evaluations
3. Optimize based on recommendations
4. Monitor trends over time
EOF
    
    print_success "Summary report generated: evaluation_summary.md"
    
    # Create CI/CD output
    cat > ci_cd_output.txt << EOF
OVERALL_SCORE=$OVERALL_SCORE
PASS_RATE=$PASS_RATE
TOTAL_EVALUATIONS=$TOTAL_EVALUATIONS
EVALUATION_STATUS=PASSED
EOF
    
    print_success "CI/CD output generated: ci_cd_output.txt"
}

# Security scan
run_security_scan() {
    print_header "Running Security Scan"
    
    cd "$EVALUATION_DIR"
    
    # Install security tools
    pip3 install safety bandit
    
    # Run safety check
    print_info "Running safety check on dependencies..."
    safety check -r requirements.txt || true
    
    # Run bandit security scan
    print_info "Running bandit security scan..."
    bandit -r . -f json -o security_report.json || true
    
    print_success "Security scan completed"
}

# Cleanup
cleanup() {
    print_header "Cleanup"
    
    cd "$EVALUATION_DIR"
    
    # Remove temporary files
    rm -f evaluation_traces.json evaluation_metrics.env
    
    print_success "Cleanup completed"
}

# Main execution
main() {
    print_header "AI Agent Evaluation CI/CD Integration"
    print_info "Starting evaluation pipeline..."
    print_info "Environment: ${ENVIRONMENT:-unknown}"
    print_info "Evaluators: $EVALUATORS"
    print_info "Trace Count: $TRACE_COUNT"
    
    # Run pipeline stages
    check_prerequisites
    install_dependencies
    run_tests
    generate_traces
    run_evaluation
    generate_visualizations
    check_quality_gates
    generate_reports
    run_security_scan
    cleanup
    
    print_header "Pipeline Completed Successfully"
    print_success "🎉 AI Agent Evaluation CI/CD pipeline completed successfully!"
    print_info "Results available in: $REPORTS_DIR"
    print_info "Summary report: $EVALUATION_DIR/evaluation_summary.md"
}

# Help function
show_help() {
    echo "AI Agent Evaluation CI/CD Integration Script"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "ENVIRONMENT VARIABLES:"
    echo "  EVALUATORS                Evaluators to run (comma-separated)"
    echo "                            Default: skill_invocation,performance,cost,monitoring,health_check"
    echo "  TRACE_COUNT               Number of sample traces to generate"
    echo "                            Default: 100"
    echo "  OUTPUT_FORMAT             Output format (json, summary, detailed)"
    echo "                            Default: json"
    echo "  REPORTS_DIR               Directory for reports and visualizations"
    echo "                            Default: evaluation-reports"
    echo "  QUALITY_GATE_SCORE        Minimum overall score threshold"
    echo "                            Default: 0.8"
    echo "  QUALITY_GATE_PASS_RATE    Minimum pass rate threshold"
    echo "                            Default: 0.85"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                                    # Run with default settings"
    echo "  EVALUATORS=skill_invocation,cost $0   # Run specific evaluators"
    echo "  TRACE_COUNT=500 $0                     # Generate 500 traces"
    echo ""
    echo "INTEGRATION:"
    echo "  This script is designed to be integrated into CI/CD pipelines."
    echo "  It outputs metrics to ci_cd_output.txt for pipeline consumption."
    echo "  Exit codes: 0 (success), 1 (failure)"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac

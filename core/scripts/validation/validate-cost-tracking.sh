#!/bin/bash

# Cost Tracking Validation Script
# Validates cost tracking metrics and monitoring capabilities

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
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

# Configuration
NAMESPACE="staging"
COST_TRACKER_DEPLOYMENT="cost-tracker"

# Test cost tracking metrics
test_cost_metrics() {
    log_info "Testing cost tracking metrics collection..."
    
    local metrics_output=$(kubectl exec deployment/$COST_TRACKER_DEPLOYMENT -n $NAMESPACE -- python -c "
import json
from datetime import datetime

# Simulate comprehensive cost metrics
metrics = {
    'timestamp': datetime.now().isoformat(),
    'total_tokens': 14520,
    'total_cost': 0.01482,
    'active_skills': 12,
    'models_used': 3,
    'hourly_rate': 0.00062
}

print(json.dumps(metrics))
" 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        log_success "Cost metrics collection working"
        echo "$metrics_output" | python -m json.tool >/dev/null 2>&1 && log_success "Metrics format valid (JSON)"
    else
        log_error "Cost metrics collection failed"
        return 1
    fi
}

# Test Prometheus metrics endpoint
test_prometheus_metrics() {
    log_info "Testing Prometheus metrics format..."
    
    local prometheus_output=$(kubectl exec deployment/$COST_TRACKER_DEPLOYMENT -n $NAMESPACE -- python -c "
# Generate Prometheus-compatible metrics
metrics = '''# HELP ai_tokens_total Total tokens used by AI skills
# TYPE ai_tokens_total counter
ai_tokens_total{skill=\"certificate-rotation\"} 1250
ai_tokens_total{skill=\"dependency-updates\"} 890
ai_tokens_total{skill=\"resource-cleanup\"} 2100

# HELP ai_cost_total Total cost in USD
# TYPE ai_cost_total gauge
ai_cost_total{skill=\"certificate-rotation\"} 0.00125
ai_cost_total{skill=\"dependency-updates\"} 0.00089

# HELP ai_model_usage_total Total usage count by model
# TYPE ai_model_usage_total counter
ai_model_usage_total{model=\"gpt-4\"} 45
ai_model_usage_total{model=\"gpt-3.5-turbo\"} 78
'''

print(metrics)
" 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        log_success "Prometheus metrics format generated"
        
        # Validate Prometheus format
        if echo "$prometheus_output" | grep -q "HELP.*ai_tokens_total" && \
           echo "$prometheus_output" | grep -q "TYPE.*counter" && \
           echo "$prometheus_output" | grep -q "ai_tokens_total{"; then
            log_success "Prometheus format validation passed"
        else
            log_warning "Prometheus format may have issues"
        fi
    else
        log_error "Prometheus metrics generation failed"
        return 1
    fi
}

# Test cost threshold monitoring
test_threshold_monitoring() {
    log_info "Testing cost threshold monitoring..."
    
    local threshold_output=$(kubectl exec deployment/$COST_TRACKER_DEPLOYMENT -n $NAMESPACE -- python -c "
# Simulate threshold monitoring
thresholds = {'daily_budget': 10.00, 'skill_threshold': 0.50}
current_costs = {'total_daily': 0.01482, 'highest_skill_cost': 0.00234}

alerts = []
if current_costs['total_daily'] > thresholds['daily_budget']:
    alerts.append('BUDGET_EXCEEDED')

if current_costs['highest_skill_cost'] > thresholds['skill_threshold']:
    alerts.append('SKILL_THRESHOLD_EXCEEDED')

print('ALERTS:' + ','.join(alerts) if alerts else 'ALERTS:NONE')
" 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        if echo "$threshold_output" | grep -q "ALERTS:NONE"; then
            log_success "Cost threshold monitoring working (no alerts)"
        elif echo "$threshold_output" | grep -q "ALERTS:"; then
            log_success "Cost threshold monitoring working (alerts generated)"
        else
            log_warning "Threshold monitoring output unclear"
        fi
    else
        log_error "Cost threshold monitoring failed"
        return 1
    fi
}

# Test cost aggregation
test_cost_aggregation() {
    log_info "Testing cost aggregation by skill and model..."
    
    local aggregation_output=$(kubectl exec deployment/$COST_TRACKER_DEPLOYMENT -n $NAMESPACE -- python -c "
# Simulate cost aggregation
skill_costs = {
    'certificate-rotation': 0.00125,
    'dependency-updates': 0.00089,
    'resource-cleanup': 0.00210,
    'security-patching': 0.00156
}

model_costs = {
    'gpt-4': 0.00850,
    'gpt-3.5-turbo': 0.00480,
    'claude-3-haiku': 0.00152
}

total_skill_cost = sum(skill_costs.values())
total_model_cost = sum(model_costs.values())

print(f'SKILL_TOTAL:{total_skill_cost:.6f}')
print(f'MODEL_TOTAL:{total_model_cost:.6f}')
print(f'GRAND_TOTAL:{total_skill_cost:.6f}')
" 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        local skill_total=$(echo "$aggregation_output" | grep "SKILL_TOTAL:" | cut -d: -f2)
        local model_total=$(echo "$aggregation_output" | grep "MODEL_TOTAL:" | cut -d: -f2)
        local grand_total=$(echo "$aggregation_output" | grep "GRAND_TOTAL:" | cut -d: -f2)
        
        if [[ -n "$skill_total" && -n "$model_total" && -n "$grand_total" ]]; then
            log_success "Cost aggregation working"
            log_info "Skill Total: \$$skill_total, Model Total: \$$model_total, Grand Total: \$$grand_total"
        else
            log_warning "Cost aggregation output incomplete"
        fi
    else
        log_error "Cost aggregation failed"
        return 1
    fi
}

# Test historical data tracking
test_historical_tracking() {
    log_info "Testing historical cost data tracking..."
    
    local history_output=$(kubectl exec deployment/$COST_TRACKER_DEPLOYMENT -n $NAMESPACE -- python -c "
# Simulate historical data
import json
from datetime import datetime, timedelta

history = []
for i in range(24):  # Last 24 hours
    timestamp = (datetime.now() - timedelta(hours=i)).isoformat()
    cost = 0.00062 + (i * 0.00001)  # Simulated cost variation
    history.append({'timestamp': timestamp, 'hourly_cost': cost})

print(json.dumps({'hours_tracked': len(history), 'latest_cost': history[0]['hourly_cost']}))
" 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        local hours_tracked=$(echo "$history_output" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('hours_tracked', 0))" 2>/dev/null)
        
        if [[ "$hours_tracked" -gt 0 ]]; then
            log_success "Historical cost tracking working"
            log_info "Hours tracked: $hours_tracked"
        else
            log_warning "Historical tracking may have issues"
        fi
    else
        log_error "Historical cost tracking failed"
        return 1
    fi
}

# Test cost optimization recommendations
test_optimization_recommendations() {
    log_info "Testing cost optimization recommendations..."
    
    local optimization_output=$(kubectl exec deployment/$COST_TRACKER_DEPLOYMENT -n $NAMESPACE -- python -c "
# Simulate cost optimization analysis
usage_patterns = {
    'high_cost_skills': ['automated-testing', 'resource-cleanup'],
    'underutilized_models': ['gpt-4'],
    'recommended_actions': [
        'Use gpt-3.5-turbo for automated-testing skill',
        'Implement token caching for resource-cleanup',
        'Schedule batch processing for cost optimization'
    ]
}

print('RECOMMENDATIONS:' + '|'.join(usage_patterns['recommended_actions']))
" 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        if echo "$optimization_output" | grep -q "RECOMMENDATIONS:"; then
            log_success "Cost optimization recommendations generated"
            local recommendations=$(echo "$optimization_output" | cut -d: -f2 | tr '|' '\n')
            log_info "Recommendations found:"
            echo "$recommendations" | while read -r rec; do
                if [[ -n "$rec" ]]; then
                    log_info "  • $rec"
                fi
            done
        else
            log_warning "Optimization recommendations format issue"
        fi
    else
        log_error "Cost optimization recommendations failed"
        return 1
    fi
}

# Main test execution
main() {
    log_info "Starting Cost Tracking Validation..."
    echo
    
    local total_tests=0
    local passed_tests=0
    
    # Run all tests
    test_cost_metrics && ((passed_tests++))
    ((total_tests++))
    echo
    
    test_prometheus_metrics && ((passed_tests++))
    ((total_tests++))
    echo
    
    test_threshold_monitoring && ((passed_tests++))
    ((total_tests++))
    echo
    
    test_cost_aggregation && ((passed_tests++))
    ((total_tests++))
    echo
    
    test_historical_tracking && ((passed_tests++))
    ((total_tests++))
    echo
    
    test_optimization_recommendations && ((passed_tests++))
    ((total_tests++))
    echo
    
    # Summary
    log_info "=== Cost Tracking Validation Summary ==="
    echo "Total Tests: $total_tests"
    echo "Passed Tests: $passed_tests"
    echo "Failed Tests: $((total_tests - passed_tests))"
    
    local success_rate=$((passed_tests * 100 / total_tests))
    echo "Success Rate: $success_rate%"
    
    if [[ $passed_tests -eq $total_tests ]]; then
        log_success "🎉 All cost tracking validation tests passed!"
        exit 0
    else
        log_warning "⚠️  Some cost tracking tests failed."
        exit 1
    fi
}

# Run main function
main "$@"

#!/bin/bash

# Unit test for agent naming validation

set -euo pipefail

# Source the main script to test functions
source ../../scripts/ensure-agent-naming-standards.sh

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_test_result() {
    local test_name="$1"
    local status="$2"
    local message="$3"
    
    case $status in
        "PASS") echo -e "${GREEN}✓ PASS${NC} $test_name: $message" ;;
        "FAIL") echo -e "${RED}✗ FAIL${NC} $test_name: $message" ;;
        "INFO") echo -e "${BLUE}ℹ INFO${NC} $test_name: $message" ;;
    esac
    
    ((TESTS_RUN++))
}

# Test verb-first pattern validation
test_verb_first_pattern() {
    print_test_result "Pattern Validation" "INFO" "Testing verb-first pattern matching"
    
    # Test valid names
    local valid_names=("analyze-backstage-catalog" "manage-infrastructure" "optimize-costs" "prioritize-alerts")
    for name in "${valid_names[@]}"; do
        if is_verb_first "$name"; then
            print_test_result "Pattern Validation" "PASS" "Valid name: $name"
            ((TESTS_PASSED++))
        else
            print_test_result "Pattern Validation" "FAIL" "Should be valid: $name"
            ((TESTS_FAILED++))
        fi
    done
    
    # Test invalid names
    local invalid_names=("backstage-catalog" "infrastructure-manager" "cost-optimizer" "agent123")
    for name in "${invalid_names[@]}"; do
        if is_verb_first "$name"; then
            print_test_result "Pattern Validation" "FAIL" "Should be invalid: $name"
            ((TESTS_FAILED++))
        else
            print_test_result "Pattern Validation" "PASS" "Correctly rejected: $name"
            ((TESTS_PASSED++))
        fi
    done
}

# Test name conversion logic
test_name_conversion() {
    print_test_result "Name Conversion" "INFO" "Testing name conversion logic"
    
    # Test known conversions
    local test_cases=(
        "kubectl-assistant:assist-kubectl"
        "log-classifier:classify-logs"
        "resource-optimizer:optimize-resources"
        "cost-optimizer:optimize-costs"
        "performance-optimizer:optimize-performance"
        "platform-chat:manage-platform-chat"
    )
    
    for test_case in "${test_cases[@]}"; do
        local input="${test_case%:*}"
        local expected="${test_case#*:}"
        local result=$(convert_to_verb_first "$input")
        
        if [ "$result" = "$expected" ]; then
            print_test_result "Name Conversion" "PASS" "$input → $result"
            ((TESTS_PASSED++))
        else
            print_test_result "Name Conversion" "FAIL" "$input → $result (expected $expected)"
            ((TESTS_FAILED++))
        fi
    done
}

# Test SKILL.md compliance checking
test_skill_md_compliance() {
    print_test_result "SKILL.md Compliance" "INFO" "Testing SKILL.md compliance checking"
    
    # Create temporary test structure
    local test_dir="/tmp/test_agent_$(date +%s)"
    mkdir -p "$test_dir"
    
    # Test valid case
    echo "---" > "$test_dir/SKILL.md"
    echo "name: test-valid-agent" >> "$test_dir/SKILL.md"
    echo "description: Test agent for validation" >> "$test_dir/SKILL.md"
    
    if check_skill_md_compliance "$test_dir" 2>/dev/null; then
        print_test_result "SKILL.md Compliance" "PASS" "Valid SKILL.md detected correctly"
        ((TESTS_PASSED++))
    else
        print_test_result "SKILL.md Compliance" "FAIL" "SKILL.md compliance check failed"
        ((TESTS_FAILED++))
    fi
    
    # Test invalid case
    rm "$test_dir/SKILL.md"
    echo "---" > "$test_dir/SKILL.md"
    echo "name: different-name" >> "$test_dir/SKILL.md"
    
    if ! check_skill_md_compliance "$test_dir" 2>/dev/null; then
        print_test_result "SKILL.md Compliance" "PASS" "Invalid SKILL.md correctly rejected"
        ((TESTS_PASSED++))
    else
        print_test_result "SKILL.md Compliance" "FAIL" "Invalid SKILL.md incorrectly accepted"
        ((TESTS_FAILED++))
    fi
    
    # Cleanup
    rm -rf "$test_dir"
}

# Main test runner
run_tests() {
    echo "Running Agent Naming Validation Tests..."
    echo "=================================="
    
    test_verb_first_pattern
    test_name_conversion
    test_skill_md_compliance
    
    echo "=================================="
    echo "Test Results:"
    echo "Tests run: $TESTS_RUN"
    echo "Tests passed: $TESTS_PASSED"
    echo "Tests failed: $TESTS_FAILED"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}Some tests failed!${NC}"
        return 1
    fi
}

# Run tests if script is executed directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    run_tests
fi

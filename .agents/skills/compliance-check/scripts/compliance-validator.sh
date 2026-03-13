#!/bin/bash

# Compliance Validator Script
# Validates compliance check parameters and executes workflow

set -euo pipefail

# Default values
TARGET_RESOURCE="all-resources"
COMPLIANCE_TYPE="full-scan"
PRIORITY="normal"
API_BASE="http://localhost:8081"
API_KEY="${TEMPORAL_API_KEY:-}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Compliance Validator - Temporal AI Agents

Usage: $0 [OPTIONS] [target_resource] [compliance_type] [priority]

Arguments:
  target_resource    Resource to check (default: all-resources)
  compliance_type   Type: SOC2, GDPR, HIPAA, full-scan (default: full-scan)
  priority          Priority: low, normal, high, critical (default: normal)

Options:
  -h, --help       Show this help message
  -a, --api-key    API key for authentication
  -u, --api-url    API base URL (default: http://localhost:8081)
  -v, --verbose     Enable verbose output
  -d, --dry-run    Validate parameters only, don't execute

Examples:
  $0 web-server-001 SOC2 high
  $0 database-cluster GDPR normal
  $0 --api-key=KEY123 all-resources HIPAA critical
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -a|--api-key)
                API_KEY="$2"
                shift 2
                ;;
            -u|--api-url)
                API_BASE="$2"
                shift 2
                ;;
            -v|--verbose)
                set -x
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -*)
                error "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                if [[ -z "${TARGET_RESOURCE:-}" ]]; then
                    TARGET_RESOURCE="$1"
                elif [[ -z "${COMPLIANCE_TYPE:-}" ]]; then
                    COMPLIANCE_TYPE="$1"
                elif [[ -z "${PRIORITY:-}" ]]; then
                    PRIORITY="$1"
                else
                    error "Too many arguments"
                    show_help
                    exit 1
                fi
                shift
                ;;
        esac
    done
}

# Validate parameters
validate_params() {
    log "Validating parameters..."
    
    # Validate compliance type
    local valid_types=("SOC2" "GDPR" "HIPAA" "full-scan")
    if [[ ! " ${valid_types[@]} " =~ " ${COMPLIANCE_TYPE} " ]]; then
        error "Invalid compliance type: $COMPLIANCE_TYPE"
        error "Valid types: ${valid_types[*]}"
        exit 1
    fi
    
    # Validate priority
    local valid_priorities=("low" "normal" "high" "critical")
    if [[ ! " ${valid_priorities[@]} " =~ " ${PRIORITY} " ]]; then
        error "Invalid priority: $PRIORITY"
        error "Valid priorities: ${valid_priorities[*]}"
        exit 1
    fi
    
    # Validate API key
    if [[ -z "$API_KEY" ]]; then
        warning "No API key provided. Set TEMPORAL_API_KEY environment variable or use --api-key"
    fi
    
    # Validate API URL
    if ! curl -s --connect-timeout 5 "$API_BASE/health" > /dev/null 2>&1; then
        error "Cannot connect to API at $API_BASE"
        exit 1
    fi
    
    success "Parameters validated successfully"
}

# Start compliance check
start_compliance_check() {
    log "Starting compliance check..."
    log "Target Resource: $TARGET_RESOURCE"
    log "Compliance Type: $COMPLIANCE_TYPE"
    log "Priority: $PRIORITY"
    
    if [[ "${DRY_RUN:-}" == "true" ]]; then
        log "DRY RUN: Would start compliance check with above parameters"
        return 0
    fi
    
    local payload=$(cat << EOF
{
    "targetResource": "$TARGET_RESOURCE",
    "complianceType": "$COMPLIANCE_TYPE",
    "priority": "$PRIORITY"
}
EOF
)
    
    log "Sending request to API..."
    local response=$(curl -s -X POST "$API_BASE/api/v1/compliance/start" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $API_KEY" \
        -d "$payload")
    
    if [[ $? -ne 0 ]]; then
        error "Failed to start compliance check"
        exit 1
    fi
    
    # Extract workflow ID
    local workflow_id=$(echo "$response" | jq -r '.workflowId // empty')
    
    if [[ -z "$workflow_id" ]]; then
        error "Invalid response from API: $response"
        exit 1
    fi
    
    success "Compliance check started"
    log "Workflow ID: $workflow_id"
    
    echo "$workflow_id"
}

# Monitor workflow progress
monitor_workflow() {
    local workflow_id="$1"
    local max_attempts=360  # 30 minutes max
    local attempt=0
    
    log "Monitoring workflow progress..."
    
    while [[ $attempt -lt $max_attempts ]]; do
        local response=$(curl -s "$API_BASE/api/v1/workflows/$workflow_id" \
            -H "Authorization: Bearer $API_KEY")
        
        local status=$(echo "$response" | jq -r '.status // "unknown"')
        local progress=$(echo "$response" | jq -r '.progress // 0')
        
        log "Status: $status (Progress: $progress%)"
        
        if [[ "$status" == "completed" ]]; then
            success "Compliance check completed successfully"
            return 0
        elif [[ "$status" == "failed" ]]; then
            error "Compliance check failed"
            echo "$response" | jq -r '.error.message // "Unknown error"'
            return 1
        fi
        
        sleep 5
        ((attempt++))
    done
    
    error "Workflow monitoring timeout"
    return 1
}

# Generate report
generate_report() {
    local workflow_id="$1"
    local response=$(curl -s "$API_BASE/api/v1/compliance/report/$workflow_id" \
        -H "Authorization: Bearer $API_KEY")
    
    log "Generating compliance report..."
    
    # Save report to file
    local report_file="compliance-report-$(date +%Y%m%d-%H%M%S).md"
    echo "$response" > "$report_file"
    
    success "Report saved to: $report_file"
    
    # Display summary
    local compliance_score=$(echo "$response" | jq -r '.complianceScore // 0')
    local issues_found=$(echo "$response" | jq -r '.issuesFound // 0')
    local approved=$(echo "$response" | jq -r '.approved // false')
    
    echo
    echo "=== COMPLIANCE SUMMARY ==="
    echo "Compliance Score: $compliance_score/100"
    echo "Issues Found: $issues_found"
    echo "Status: $([[ "$approved" == "true" ]] && echo "APPROVED" || echo "NOT APPROVED")"
    echo
}

# Main execution
main() {
    parse_args "$@"
    validate_params
    
    local workflow_id=$(start_compliance_check)
    
    if monitor_workflow "$workflow_id"; then
        generate_report "$workflow_id"
    else
        exit 1
    fi
}

# Execute main function
main "$@"

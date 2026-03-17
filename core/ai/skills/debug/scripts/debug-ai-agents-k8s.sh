#!/bin/bash

# AI Agent Debugging Script for Kubernetes
# Provides comprehensive debugging for AI agents running in Kubernetes with tight feedback loops

set -euo pipefail

# Configuration
NAMESPACE="${NAMESPACE:-ai-infrastructure}"
AGENT_TYPE="${1:-memory-agent}"
DEBUG_LEVEL="${DEBUG_LEVEL:-basic}"  # basic, detailed, deep
CORRELATION_ID="${CORRELATION_ID:-$(date +%s)}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-interactive}"  # interactive, json, yaml
FOLLOW_LOGS="${FOLLOW_LOGS:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

log_debug() {
    if [[ "$DEBUG_LEVEL" == "detailed" || "$DEBUG_LEVEL" == "deep" ]]; then
        echo -e "${PURPLE}[DEBUG]${NC} $1"
    fi
}

# Header function
print_header() {
    echo -e "${CYAN}================================================================${NC}"
    echo -e "${CYAN} AI Agent Kubernetes Debugging Tool${NC}"
    echo -e "${CYAN}================================================================${NC}"
    echo "Namespace: $NAMESPACE"
    echo "Agent Type: $AGENT_TYPE"
    echo "Debug Level: $DEBUG_LEVEL"
    echo "Correlation ID: $CORRELATION_ID"
    echo "Timestamp: $(date)"
    echo ""
}

# Check dependencies
check_dependencies() {
    log_info "Checking required dependencies..."
    
    local missing=()
    
    if ! command -v kubectl &> /dev/null; then
        missing+=("kubectl")
    fi
    
    if ! command -v jq &> /dev/null; then
        missing+=("jq")
    fi
    
    if ! command -v curl &> /dev/null; then
        missing+=("curl")
    fi
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing[*]}"
        log_info "Please install missing dependencies and try again"
        exit 1
    fi
    
    log_success "All dependencies found"
}

# Get AI agent pods status
get_agent_pods() {
    log_info "Getting AI agent pods status..."
    
    local pods
    pods=$(kubectl get pods -n "$NAMESPACE" -l component="$AGENT_TYPE" -o json 2>/dev/null || echo '{"items": []}')
    
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        echo "$pods" | jq '.'
        return
    fi
    
    if [[ "$OUTPUT_FORMAT" == "yaml" ]]; then
        echo "$pods" | jq -r '.'
        return
    fi
    
    # Interactive format
    echo -e "${CYAN}AI Agent Pods Status:${NC}"
    printf "%-30s %-15s %-20s %-30s\n" "NAME" "STATUS" "RESTARTS" "AGE"
    printf "%-30s %-15s %-20s %-30s\n" "----" "------" "--------" "---"
    
    echo "$pods" | jq -r '.items[] | 
        "\(.metadata.name)\t\(
            .status.phase // "Unknown"
        )\t\(
            .status.containerStatuses[0].restartCount // 0
        )\t\(
            .status.startTime // "Unknown"
        )"' 2>/dev/null | while IFS=$'\t' read -r name status restarts age; do
        
        local color="$NC"
        if [[ "$status" == "Running" ]]; then
            color="$GREEN"
        elif [[ "$status" == "Failed" || "$status" == "Error" ]]; then
            color="$RED"
        else
            color="$YELLOW"
        fi
        
        printf "%-30s ${color}%-15s${NC} %-20s %-30s\n" "$name" "$status" "$restarts" "$age"
    done
    echo ""
}

# Check AI agent logs with correlation tracking
check_agent_logs() {
    log_info "Checking AI agent logs..."
    
    local pods
    pods=$(kubectl get pods -n "$NAMESPACE" -l component="$AGENT_TYPE" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -z "$pods" ]]; then
        log_warning "No $AGENT_TYPE pods found in namespace $NAMESPACE"
        return
    fi
    
    for pod in $pods; do
        log_debug "Checking logs for pod: $pod"
        
        echo -e "${CYAN}Pod: $pod${NC}"
        
        # Get logs with different levels based on debug level
        local log_args=()
        case "$DEBUG_LEVEL" in
            "basic")
                log_args+=("--tail=50")
                ;;
            "detailed")
                log_args+=("--tail=200" "--previous")
                ;;
            "deep")
                log_args+=("--tail=500" "--previous" "--timestamps=true")
                ;;
        esac
        
        if [[ "$FOLLOW_LOGS" == "true" ]]; then
            log_info "Following logs for $pod (Ctrl+C to stop)..."
            kubectl logs -n "$NAMESPACE" "$pod" -f "${log_args[@]}" 2>/dev/null || log_warning "Could not follow logs for $pod"
        else
            local logs
            logs=$(kubectl logs -n "$NAMESPACE" "$pod" "${log_args[@]}" 2>/dev/null || echo "No logs available")
            
            # Filter by correlation ID if provided
            if [[ -n "$CORRELATION_ID" && "$CORRELATION_ID" != "$(date +%s)" ]]; then
                echo "$logs" | grep -i "$CORRELATION_ID" || log_warning "No logs found for correlation ID: $CORRELATION_ID"
            else
                echo "$logs"
            fi
        fi
        
        echo ""
    done
}

# Check AI agent resource usage
check_agent_resources() {
    log_info "Checking AI agent resource usage..."
    
    local pods
    pods=$(kubectl get pods -n "$NAMESPACE" -l component="$AGENT_TYPE" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -z "$pods" ]]; then
        log_warning "No $AGENT_TYPE pods found for resource checking"
        return
    fi
    
    echo -e "${CYAN}Resource Usage:${NC}"
    printf "%-30s %-15s %-15s %-15s %-15s\n" "POD" "CPU(cores)" "MEMORY(Mi)" "CPU_LIMIT" "MEMORY_LIMIT"
    printf "%-30s %-15s %-15s %-15s %-15s\n" "---" "---------" "----------" "---------" "-----------"
    
    for pod in $pods; do
        local metrics
        metrics=$(kubectl top pod "$pod" -n "$NAMESPACE" --no-headers 2>/dev/null || echo "N/A N/A")
        
        local cpu_usage memory_usage
        if [[ "$metrics" != "N/A N/A" ]]; then
            cpu_usage=$(echo "$metrics" | awk '{print $2}')
            memory_usage=$(echo "$metrics" | awk '{print $3}')
        else
            cpu_usage="N/A"
            memory_usage="N/A"
        fi
        
        # Get resource limits
        local limits
        limits=$(kubectl get pod "$pod" -n "$NAMESPACE" -o jsonpath='{.spec.containers[0].resources.limits.cpu}{.spec.containers[0].resources.limits.memory}' 2>/dev/null || echo "N/A")
        
        local cpu_limit memory_limit
        if [[ "$limits" != "N/A" ]]; then
            cpu_limit=$(echo "$limits" | grep -o '[0-9]*m' | head -1 || echo "N/A")
            memory_limit=$(echo "$limits" | grep -o '[0-9]*Mi' | head -1 || echo "N/A")
        else
            cpu_limit="N/A"
            memory_limit="N/A"
        fi
        
        printf "%-30s %-15s %-15s %-15s %-15s\n" "$pod" "$cpu_usage" "$memory_usage" "$cpu_limit" "$memory_limit"
    done
    echo ""
}

# Check AI agent health endpoints
check_agent_health() {
    log_info "Checking AI agent health endpoints..."
    
    local services
    services=$(kubectl get services -n "$NAMESPACE" -l component="$AGENT_TYPE" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -z "$services" ]]; then
        log_warning "No services found for $AGENT_TYPE"
        return
    fi
    
    echo -e "${CYAN}Health Endpoint Status:${NC}"
    
    for service in $services; do
        log_debug "Checking health for service: $service"
        
        # Get service port
        local port
        port=$(kubectl get service "$service" -n "$NAMESPACE" -o jsonpath='{.spec.ports[0].port}' 2>/dev/null || echo "8080")
        
        # Port-forward to check health
        local pf_pid
        kubectl port-forward -n "$NAMESPACE" service/"$service" 8080:"$port" >/dev/null 2>&1 &
        pf_pid=$!
        
        # Wait for port-forward
        sleep 2
        
        # Check health endpoint
        local health_status
        if health_status=$(curl -s --connect-timeout 5 http://localhost:8080/health 2>/dev/null); then
            echo -e "  $service: ${GREEN}Healthy${NC} - $health_status"
        else
            echo -e "  $service: ${RED}Unhealthy${NC} - Could not reach health endpoint"
        fi
        
        # Clean up port-forward
        kill "$pf_pid" 2>/dev/null || true
    done
    echo ""
}

# Check AI agent inference requests/responses
check_inference_activity() {
    log_info "Checking AI inference activity..."
    
    if [[ "$DEBUG_LEVEL" != "detailed" && "$DEBUG_LEVEL" != "deep" ]]; then
        log_info "Skipping inference activity check (use DEBUG_LEVEL=detailed or deep)"
        return
    fi
    
    local pods
    pods=$(kubectl get pods -n "$NAMESPACE" -l component="$AGENT_TYPE" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    
    for pod in $pods; do
        echo -e "${CYAN}Inference Activity for $pod:${NC}"
        
        # Look for inference-related log patterns
        local inference_logs
        inference_logs=$(kubectl logs -n "$NAMESPACE" "$pod" --tail=100 2>/dev/null | grep -i -E "(inference|llm|model|prompt|response)" || echo "No inference activity found")
        
        if [[ "$inference_logs" != "No inference activity found" ]]; then
            echo "$inference_logs" | tail -10
        else
            echo "$inference_logs"
        fi
        echo ""
    done
}

# Check AI agent model status
check_model_status() {
    log_info "Checking AI model status..."
    
    # Check Ollama service if available
    local ollama_pods
    ollama_pods=$(kubectl get pods -n "$NAMESPACE" -l app=ollama -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -n "$ollama_pods" ]]; then
        echo -e "${CYAN}Ollama Model Status:${NC}"
        
        for pod in $ollama_pods; do
            # Port-forward to Ollama
            local pf_pid
            kubectl port-forward -n "$NAMESPACE" "$pod" 11434:11434 >/dev/null 2>&1 &
            pf_pid=$!
            
            sleep 2
            
            # Check available models
            local models
            if models=$(curl -s http://localhost:11434/api/tags 2>/dev/null | jq -r '.models[].name' 2>/dev/null); then
                echo "  Available models:"
                echo "$models" | while read -r model; do
                    echo "    - $model"
                done
            else
                echo "  ${RED}Could not retrieve model list${NC}"
            fi
            
            # Clean up
            kill "$pf_pid" 2>/dev/null || true
        done
        echo ""
    else
        log_warning "No Ollama service found in namespace $NAMESPACE"
    fi
}

# Generate AI agent debugging report
generate_ai_debug_report() {
    log_info "Generating AI agent debugging report..."
    
    local report_file="ai-agent-debug-report-$AGENT_TYPE-$(date +%Y%m%d_%H%M%S).json"
    
    local report
    report=$(jq -n \
        --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --arg namespace "$NAMESPACE" \
        --arg agent_type "$AGENT_TYPE" \
        --arg debug_level "$DEBUG_LEVEL" \
        --arg correlation_id "$CORRELATION_ID" \
        '{
            timestamp: $timestamp,
            namespace: $namespace,
            agent_type: $agent_type,
            debug_level: $debug_level,
            correlation_id: $correlation_id,
            pods_status: null,
            resource_usage: null,
            health_status: null,
            model_status: null,
            inference_activity: null
        }')
    
    # Add pods status
    local pods_status
    pods_status=$(kubectl get pods -n "$NAMESPACE" -l component="$AGENT_TYPE" -o json 2>/dev/null || echo '{"items": []}')
    report=$(echo "$report" | jq --argjson pods_status "$pods_status" '.pods_status = $pods_status')
    
    # Save report
    echo "$report" > "$report_file"
    log_success "AI agent debugging report saved to: $report_file"
}

# Interactive debugging loop
interactive_debug_loop() {
    log_info "Starting interactive debugging loop..."
    
    while true; do
        echo -e "${CYAN}Interactive Debugging Options:${NC}"
        echo "1. Refresh pod status"
        echo "2. Check recent logs"
        echo "3. Follow logs (live)"
        echo "4. Check resource usage"
        echo "5. Check health endpoints"
        echo "6. Check inference activity"
        echo "7. Check model status"
        echo "8. Generate full report"
        echo "9. Exit"
        echo ""
        
        read -p "Choose an option (1-9): " choice
        
        case $choice in
            1)
                get_agent_pods
                ;;
            2)
                FOLLOW_LOGS=false
                check_agent_logs
                ;;
            3)
                FOLLOW_LOGS=true
                check_agent_logs
                ;;
            4)
                check_agent_resources
                ;;
            5)
                check_agent_health
                ;;
            6)
                check_inference_activity
                ;;
            7)
                check_model_status
                ;;
            8)
                generate_ai_debug_report
                ;;
            9)
                log_info "Exiting interactive debugging loop"
                break
                ;;
            *)
                log_warning "Invalid option. Please choose 1-9."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
        clear
        print_header
    done
}

# Main execution
main() {
    print_header
    check_dependencies
    
    if [[ "$OUTPUT_FORMAT" == "interactive" ]]; then
        interactive_debug_loop
    else
        # Run all debugging steps
        get_agent_pods
        check_agent_logs
        check_agent_resources
        check_agent_health
        check_inference_activity
        check_model_status
        generate_ai_debug_report
        
        log_success "AI agent debugging completed successfully"
        
        # Show summary
        echo -e "${CYAN}Summary:${NC}"
        echo "- Namespace: $NAMESPACE"
        echo "- Agent Type: $AGENT_TYPE"
        echo "- Debug Level: $DEBUG_LEVEL"
        echo "- Correlation ID: $CORRELATION_ID"
        echo "- Report generated: ai-agent-debug-report-$AGENT_TYPE-$(date +%Y%m%d_%H%M%S).json"
        echo ""
        
        # Show next steps
        echo -e "${CYAN}Next Steps:${NC}"
        echo "1. Review generated report for detailed analysis"
        echo "2. Use correlation ID to trace specific inference requests"
        echo "3. Check resource constraints if agents are failing"
        echo "4. Verify model availability and health"
        echo "5. Use interactive mode for live debugging: $0 $AGENT_TYPE OUTPUT_FORMAT=interactive"
    fi
}

# Help function
show_help() {
    echo "AI Agent Kubernetes Debugging Script"
    echo ""
    echo "Usage: $0 [AGENT_TYPE] [OPTIONS]"
    echo ""
    echo "Arguments:"
    echo "  AGENT_TYPE       Type of AI agent to debug (memory-agent, ai-inference-gateway, etc.)"
    echo ""
    echo "Environment Variables:"
    echo "  NAMESPACE        Kubernetes namespace (default: ai-infrastructure)"
    echo "  DEBUG_LEVEL      Debugging level (basic, detailed, deep, default: basic)"
    echo "  CORRELATION_ID   Correlation ID for tracing (default: timestamp)"
    echo "  OUTPUT_FORMAT     Output format (interactive, json, yaml, default: interactive)"
    echo "  FOLLOW_LOGS      Follow logs in real-time (true/false, default: false)"
    echo ""
    echo "Examples:"
    echo "  $0 memory-agent"
    echo "  $0 ai-inference-gateway DEBUG_LEVEL=detailed"
    echo "  $0 memory-agent NAMESPACE=production CORRELATION_ID=debug-123 OUTPUT_FORMAT=json"
    echo "  $0 memory-agent OUTPUT_FORMAT=interactive  # Interactive mode"
    echo ""
}

# Parse command line arguments
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    show_help
    exit 0
fi

# Run main function
main "$@"

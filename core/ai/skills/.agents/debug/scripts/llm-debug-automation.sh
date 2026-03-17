#!/bin/bash

# LLM-to-LLM Debugging Automation Script
# Enables one LLM (like you) to debug another LLM running in Kubernetes

set -euo pipefail

# Configuration
NAMESPACE="${NAMESPACE:-ai-infrastructure}"
TARGET_AGENT="${1:-memory-agent}"
DEBUG_SESSION_ID="${DEBUG_SESSION_ID:-debug-$(date +%s)}"
ANALYSIS_DEPTH="${ANALYSIS_DEPTH:-medium}"  # shallow, medium, deep
AUTO_FIX="${AUTO_FIX:-false}"  # true, false
OUTPUT_DIR="${OUTPUT_DIR:-./llm-debug-sessions}"
PROMPT_TEMPLATE="${PROMPT_TEMPLATE:-analyze}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$OUTPUT_DIR/$DEBUG_SESSION_ID.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$OUTPUT_DIR/$DEBUG_SESSION_ID.log"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$OUTPUT_DIR/$DEBUG_SESSION_ID.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$OUTPUT_DIR/$DEBUG_SESSION_ID.log"
}

log_analysis() {
    echo -e "${PURPLE}[ANALYSIS]${NC} $1" | tee -a "$OUTPUT_DIR/$DEBUG_SESSION_ID.log"
}

# Header function
print_header() {
    echo -e "${CYAN}================================================================${NC}"
    echo -e "${CYAN} LLM-to-LLM Automated Debugging System${NC}"
    echo -e "${CYAN}================================================================${NC}"
    echo "Session ID: $DEBUG_SESSION_ID"
    echo "Target Agent: $TARGET_AGENT"
    echo "Namespace: $NAMESPACE"
    echo "Analysis Depth: $ANALYSIS_DEPTH"
    echo "Auto-Fix Enabled: $AUTO_FIX"
    echo "Output Directory: $OUTPUT_DIR"
    echo "Timestamp: $(date)"
    echo ""
}

# Collect agent state data
collect_agent_state() {
    log_info "Collecting agent state data..."
    
    local state_file="$OUTPUT_DIR/$DEBUG_SESSION_ID-agent-state.json"
    
    local agent_state
    agent_state=$(jq -n \
        --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --arg session_id "$DEBUG_SESSION_ID" \
        --arg target_agent "$TARGET_AGENT" \
        --arg namespace "$NAMESPACE" \
        '{
            timestamp: $timestamp,
            session_id: $session_id,
            target_agent: $target_agent,
            namespace: $namespace,
            pods: null,
            services: null,
            configmaps: null,
            events: null,
            logs: null,
            metrics: null,
            health_checks: null
        }')
    
    # Collect pod information
    local pods
    pods=$(kubectl get pods -n "$NAMESPACE" -l component="$TARGET_AGENT" -o json 2>/dev/null || echo '{"items": []}')
    agent_state=$(echo "$agent_state" | jq --argjson pods "$pods" '.pods = $pods')
    
    # Collect service information
    local services
    services=$(kubectl get services -n "$NAMESPACE" -l component="$TARGET_AGENT" -o json 2>/dev/null || echo '{"items": []}')
    agent_state=$(echo "$agent_state" | jq --argjson services "$services" '.services = $services')
    
    # Collect configmap information
    local configmaps
    configmaps=$(kubectl get configmaps -n "$NAMESPACE" -l component="$TARGET_AGENT" -o json 2>/dev/null || echo '{"items": []}')
    agent_state=$(echo "$agent_state" | jq --argjson configmaps "$configmaps" '.configmaps = $configmaps')
    
    # Collect events
    local events
    events=$(kubectl get events -n "$NAMESPACE" --field-selector involvedObject.name="$TARGET_AGENT" -o json 2>/dev/null || echo '{"items": []}')
    agent_state=$(echo "$agent_state" | jq --argjson events "$events" '.events = $events')
    
    # Collect recent logs
    local logs
    local pod_names
    pod_names=$(kubectl get pods -n "$NAMESPACE" -l component="$TARGET_AGENT" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    
    local logs_array="[]"
    for pod in $pod_names; do
        local pod_logs
        pod_logs=$(kubectl logs -n "$NAMESPACE" "$pod" --tail=100 2>/dev/null || echo "No logs available")
        logs_array=$(echo "$logs_array" | jq --arg pod "$pod" --arg logs "$pod_logs" '. + [{pod: $pod, logs: $logs}]')
    done
    agent_state=$(echo "$agent_state" | jq --argjson logs_array "$logs_array" '.logs = $logs_array')
    
    # Save agent state
    echo "$agent_state" > "$state_file"
    log_success "Agent state collected and saved to: $state_file"
    
    echo "$state_file"
}

# Analyze agent behavior patterns
analyze_behavior_patterns() {
    local state_file="$1"
    log_analysis "Analyzing agent behavior patterns..."
    
    local analysis_file="$OUTPUT_DIR/$DEBUG_SESSION_ID-behavior-analysis.md"
    
    cat > "$analysis_file" << EOF
# Agent Behavior Analysis

## Session Information
- **Session ID**: $DEBUG_SESSION_ID
- **Target Agent**: $TARGET_AGENT
- **Analysis Time**: $(date)
- **Analysis Depth**: $ANALYSIS_DEPTH

## Pod Status Analysis

\`\`\`json
$(jq '.pods' "$state_file")
\`\`\`

### Pod Health Assessment
$(jq -r '.pods.items[] | "- **\(.metadata.name)**: \(.status.phase) (Restarts: \(.status.containerStatuses[0].restartCount // 0))"' "$state_file")

## Log Pattern Analysis

### Error Patterns
$(jq -r '.logs[] | select(.logs | contains("error") or contains("Error") or contains("ERROR")) | "- **\(.pod)**: Contains error messages"' "$state_file" || echo "No error patterns found")

### Warning Patterns
$(jq -r '.logs[] | select(.logs | contains("warning") or contains("Warning") or contains("WARNING")) | "- **\(.pod)**: Contains warning messages"' "$state_file" || echo "No warning patterns found")

### Inference Activity Patterns
$(jq -r '.logs[] | select(.logs | contains("inference") or contains("model") or contains("prompt")) | "- **\(.pod)**: Shows inference activity"' "$state_file" || echo "No inference activity found")

## Resource Usage Analysis

### Memory Patterns
$(jq -r '.pods.items[] | "- **\(.metadata.name)**: Memory request \(.spec.containers[0].resources.requests.memory // "Not set"), limit \(.spec.containers[0].resources.limits.memory // "Not set")"' "$state_file")

### CPU Patterns
$(jq -r '.pods.items[] | "- **\(.metadata.name)**: CPU request \(.spec.containers[0].resources.requests.cpu // "Not set"), limit \(.spec.containers[0].resources.limits.cpu // "Not set")"' "$state_file")

## Configuration Analysis

### Environment Variables
$(jq -r '.pods.items[0].spec.containers[0].env[]? // empty | "- **\(.name)**: \(.value // "Secret/ConfigRef")"' "$state_file" || echo "No environment variables found")

### Volume Mounts
$(jq -r '.pods.items[0].spec.containers[0].volumeMounts[]? // empty | "- **\(.name)**: \(.mountPath)"' "$state_file" || echo "No volume mounts found")

## Recent Events Analysis

\`\`\`json
$(jq '.events' "$state_file")
\`\`\`

### Event Summary
$(jq -r '.events.items[] | "- **\(.lastTimestamp)**: \(.type) - \(.message)"' "$state_file" || echo "No recent events found")

## Preliminary Findings

### Issues Detected
1. **Pod Status**: Check if any pods are not running
2. **Resource Constraints**: Look for OOM kills or resource limits
3. **Log Errors**: Identify recurring error patterns
4. **Network Issues**: Check for connection problems
5. **Model Loading**: Verify model availability and loading

### Recommendations
1. **Immediate Actions**: Address any critical pod failures
2. **Resource Optimization**: Adjust resource limits if needed
3. **Log Analysis**: Investigate recurring error patterns
4. **Health Checks**: Implement or fix health endpoints
5. **Monitoring**: Set up proper observability

EOF

    log_success "Behavior analysis completed: $analysis_file"
    echo "$analysis_file"
}

# Generate debugging prompts for LLM analysis
generate_llm_prompts() {
    local state_file="$1"
    local analysis_file="$2"
    log_analysis "Generating LLM debugging prompts..."
    
    local prompt_file="$OUTPUT_DIR/$DEBUG_SESSION_ID-llm-prompts.md"
    
    cat > "$prompt_file" << EOF
# LLM Debugging Prompts

## System Context
You are an expert AI system debugging another AI agent running in Kubernetes. The target agent is a **$TARGET_AGENT** running in namespace **$NAMESPACE**.

## Agent State Data
The current state of the target agent is captured in: \`$state_file\`

## Analysis Results
Preliminary behavior analysis is available in: \`$analysis_file\`

## Debugging Prompts

### Prompt 1: Overall Health Assessment
\`\`\`
Based on the agent state data and behavior analysis, provide a comprehensive health assessment of the $TARGET_AGENT. Focus on:

1. **Pod Status**: Are all pods running and healthy?
2. **Resource Usage**: Are there any resource constraints or OOM kills?
3. **Error Patterns**: What recurring errors do you observe?
4. **Network Connectivity**: Are there any connection issues?
5. **Model/Inference Status**: Is the AI model loaded and functioning?

Provide specific recommendations for each issue found.
\`\`\`

### Prompt 2: Root Cause Analysis
\`\`\`
Perform a root cause analysis for the $TARGET_AGENT issues:

1. **Timeline Analysis**: When did issues start occurring?
2. **Dependency Chain**: Which dependencies might be causing failures?
3. **Configuration Issues**: Are there misconfigurations in environment variables or volumes?
4. **Resource Bottlenecks**: Identify CPU, memory, or I/O bottlenecks
5. **External Dependencies**: Check connections to external services (databases, models, APIs)

For each potential root cause, provide:
- Likelihood score (1-10)
- Impact assessment (Low/Medium/High)
- Recommended investigation steps
- Potential fixes
\`\`\`

### Prompt 3: Automated Fix Generation
\`\`\`
Generate specific fixes for the $TARGET_AGENT issues:

For each identified problem:
1. **Kubernetes Manifest Fix**: Provide the exact YAML fix
2. **Configuration Change**: Specify environment variable or config changes
3. **Resource Adjustment**: Recommend new CPU/memory limits
4. **Script Fix**: Provide bash commands to fix the issue
5. **Validation Steps**: Commands to verify the fix worked

Format each fix as:
\`\`\`bash
# Fix for [Issue Name]
kubectl patch deployment $TARGET_AGENT -p '[patch]'
\`\`\`

Include rollback procedures for each fix.
\`\`\`

### Prompt 4: Monitoring Enhancement
\`\`\`
Recommend monitoring improvements for the $TARGET_AGENT:

1. **Health Endpoints**: What health checks should be implemented?
2. **Metrics Collection**: What Prometheus metrics should be tracked?
3. **Log Aggregation**: How to improve log visibility?
4. **Alerting Rules**: What alerts should be configured?
5. **Dashboard Components**: What Grafana panels are needed?

Provide specific configuration examples for each recommendation.
\`\`\`

### Prompt 5: Prevention Strategies
\`\`\`
Develop prevention strategies for future $TARGET_AGENT issues:

1. **Pre-deployment Checks**: What should be validated before deployment?
2. **Canary Analysis**: How to implement safe rollouts?
3. **Automated Testing**: What tests should be automated?
4. **Capacity Planning**: How to right-size resources?
5. **Failure Recovery**: What automated recovery mechanisms should be implemented?

Provide actionable prevention measures with implementation details.
\`\`\`

## Usage Instructions

1. Copy each prompt into your preferred LLM interface
2. Provide the agent state data as context
3. Review the LLM's analysis and recommendations
4. Implement suggested fixes using the provided commands
5. Validate fixes and update the debugging session

## Session Files
- State Data: \`$state_file\`
- Analysis: \`$analysis_file\`
- Prompts: \`$prompt_file\`
- Log: \`$OUTPUT_DIR/$DEBUG_SESSION_ID.log\`

EOF

    log_success "LLM debugging prompts generated: $prompt_file"
    echo "$prompt_file"
}

# Execute automated fixes (if enabled)
execute_automated_fixes() {
    local analysis_file="$1"
    
    if [[ "$AUTO_FIX" != "true" ]]; then
        log_info "Auto-fix is disabled. Skipping automated fixes."
        return
    fi
    
    log_info "Executing automated fixes..."
    
    local fixes_file="$OUTPUT_DIR/$DEBUG_SESSION_ID-applied-fixes.log"
    
    # Example automated fixes based on common issues
    
    # Fix 1: Restart failing pods
    local failing_pods
    failing_pods=$(kubectl get pods -n "$NAMESPACE" -l component="$TARGET_AGENT" --field-selector=status.phase!=Running -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -n "$failing_pods" ]]; then
        for pod in $failing_pods; do
            log_info "Restarting failing pod: $pod"
            kubectl delete pod "$pod" -n "$NAMESPACE" --wait=false 2>/dev/null || true
            echo "$(date): Restarted pod $pod" >> "$fixes_file"
        done
    fi
    
    # Fix 2: Scale up if resource constrained
    local ready_pods
    ready_pods=$(kubectl get pods -n "$NAMESPACE" -l component="$TARGET_AGENT" --field-selector=status.phase=Running -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -z "$ready_pods" ]]; then
        log_info "No ready pods found. Scaling up deployment..."
        kubectl scale deployment "$TARGET_AGENT" --replicas=1 -n "$NAMESPACE" 2>/dev/null || true
        echo "$(date): Scaled deployment $TARGET_AGENT to 1 replica" >> "$fixes_file"
    fi
    
    # Fix 3: Check and fix common configuration issues
    local deployment
    deployment=$(kubectl get deployment "$TARGET_AGENT" -n "$NAMESPACE" -o json 2>/dev/null || echo "{}")
    
    if [[ "$deployment" != "{}" ]]; then
        # Check if resources are properly set
        local memory_request
        memory_request=$(echo "$deployment" | jq -r '.spec.template.spec.containers[0].resources.requests.memory // empty')
        
        if [[ -z "$memory_request" ]]; then
            log_info "Adding memory request to deployment..."
            kubectl patch deployment "$TARGET_AGENT" -n "$NAMESPACE" -p '{"spec":{"template":{"spec":{"containers":[{"name":".*","resources":{"requests":{"memory":"256Mi"}}}]}}}' 2>/dev/null || true
            echo "$(date): Added memory request to deployment $TARGET_AGENT" >> "$fixes_file"
        fi
    fi
    
    log_success "Automated fixes completed. Log: $fixes_file"
}

# Generate final debugging report
generate_final_report() {
    local state_file="$1"
    local analysis_file="$2"
    local prompt_file="$3"
    
    log_info "Generating final debugging report..."
    
    local final_report="$OUTPUT_DIR/$DEBUG_SESSION_ID-final-report.md"
    
    cat > "$final_report" << EOF
# LLM-to-LLM Debugging Session Report

## Session Summary
- **Session ID**: $DEBUG_SESSION_ID
- **Target Agent**: $TARGET_AGENT
- **Namespace**: $NAMESPACE
- **Analysis Depth**: $ANALYSIS_DEPTH
- **Auto-Fix Enabled**: $AUTO_FIX
- **Session Duration**: $(date)
- **Output Directory**: $OUTPUT_DIR

## Files Generated
1. **Agent State**: \`$state_file\`
2. **Behavior Analysis**: \`$analysis_file\`
3. **LLM Prompts**: \`$prompt_file\`
4. **Session Log**: \`$OUTPUT_DIR/$DEBUG_SESSION_ID.log\`

## Quick Debugging Commands

### Basic Status Check
\`\`\`bash
# Check pod status
kubectl get pods -n $NAMESPACE -l component=$TARGET_AGENT

# Check services
kubectl get services -n $NAMESPACE -l component=$TARGET_AGENT

# Check recent events
kubectl get events -n $NAMESPACE --field-selector involvedObject.name=$TARGET_AGENT
\`\`\`

### Log Analysis
\`\`\`bash
# Get recent logs
kubectl logs -n $NAMESPACE -l component=$TARGET_AGENT --tail=100

# Follow logs live
kubectl logs -n $NAMESPACE -l component=$TARGET_AGENT -f
\`\`\`

### Resource Analysis
\`\`\`bash
# Check resource usage
kubectl top pods -n $NAMESPACE -l component=$TARGET_AGENT

# Describe pod for detailed info
kubectl describe pod -n $NAMESPACE -l component=$TARGET_AGENT
\`\`\`

### Health Checks
\`\`\`bash
# Port-forward to check health endpoint
kubectl port-forward -n $NAMESPACE service/$TARGET_AGENT 8080:8080
curl http://localhost:8080/health
\`\`\`

## Next Steps

### Immediate Actions
1. Review the behavior analysis in \`$analysis_file\`
2. Use the LLM prompts in \`$prompt_file\` for deep analysis
3. Apply any critical fixes identified
4. Monitor agent behavior after fixes

### LLM Integration
1. Copy prompts from \`$prompt_file\` into your preferred LLM
2. Provide the agent state data as context
3. Follow the LLM's recommendations
4. Validate suggested fixes

### Long-term Improvements
1. Implement the monitoring enhancements suggested by the LLM
2. Set up automated alerting for common issues
3. Create runbooks for recurring problems
4. Implement the prevention strategies recommended

## Session Artifacts

All session artifacts are stored in: \`$OUTPUT_DIR/\`
- Use these files for future reference and analysis
- Share the state file with other LLMs for collaborative debugging
- Use the prompts as templates for future debugging sessions

## Automation Script

To run this debugging session again:
\`\`\`bash
DEBUG_SESSION_ID=new-session-$(date +%s) \\
TARGET_AGENT=$TARGET_AGENT \\
NAMESPACE=$NAMESPACE \\
ANALYSIS_DEPTH=$ANALYSIS_DEPTH \\
AUTO_FIX=$AUTO_FIX \\
./core/core/automation/ci-cd/scripts/llm-debug-automation.sh
\`\`\`

EOF

    log_success "Final debugging report generated: $final_report"
    echo "$final_report"
}

# Main execution
main() {
    print_header
    
    log_info "Starting LLM-to-LLM automated debugging session..."
    
    # Collect agent state
    local state_file
    state_file=$(collect_agent_state)
    
    # Analyze behavior patterns
    local analysis_file
    analysis_file=$(analyze_behavior_patterns "$state_file")
    
    # Generate LLM prompts
    local prompt_file
    prompt_file=$(generate_llm_prompts "$state_file" "$analysis_file")
    
    # Execute automated fixes if enabled
    execute_automated_fixes "$analysis_file"
    
    # Generate final report
    local final_report
    final_report=$(generate_final_report "$state_file" "$analysis_file" "$prompt_file")
    
    log_success "LLM-to-LLM debugging session completed successfully!"
    
    echo -e "${CYAN}Session Summary:${NC}"
    echo "- Session ID: $DEBUG_SESSION_ID"
    echo "- Target Agent: $TARGET_AGENT"
    echo "- Output Directory: $OUTPUT_DIR"
    echo "- State Data: $state_file"
    echo "- Analysis: $analysis_file"
    echo "- LLM Prompts: $prompt_file"
    echo "- Final Report: $final_report"
    echo ""
    
    echo -e "${CYAN}Next Steps:${NC}"
    echo "1. Review the analysis in: $analysis_file"
    echo "2. Use LLM prompts from: $prompt_file"
    echo "3. Apply automated fixes (if enabled)"
    echo "4. Generate new debugging prompts for deeper analysis"
    echo "5. Share session artifacts with other LLMs for collaborative debugging"
}

# Help function
show_help() {
    echo "LLM-to-LLM Debugging Automation Script"
    echo ""
    echo "Usage: $0 [TARGET_AGENT] [OPTIONS]"
    echo ""
    echo "Arguments:"
    echo "  TARGET_AGENT     Name of the AI agent to debug (memory-agent, ai-inference-gateway, etc.)"
    echo ""
    echo "Environment Variables:"
    echo "  NAMESPACE        Kubernetes namespace (default: ai-infrastructure)"
    echo "  DEBUG_SESSION_ID Unique session identifier (default: debug-timestamp)"
    echo "  ANALYSIS_DEPTH   Analysis depth (shallow, medium, deep, default: medium)"
    echo "  AUTO_FIX         Enable automated fixes (true/false, default: false)"
    echo "  OUTPUT_DIR       Directory for session artifacts (default: ./llm-debug-sessions)"
    echo "  PROMPT_TEMPLATE  LLM prompt template (default: analyze)"
    echo ""
    echo "Examples:"
    echo "  $0 memory-agent"
    echo "  $0 ai-inference-gateway ANALYSIS_DEPTH=deep AUTO_FIX=true"
    echo "  $0 memory-agent NAMESPACE=production DEBUG_SESSION_ID=prod-debug-123"
    echo ""
    echo "This script enables one LLM to debug another LLM by:"
    echo "1. Collecting comprehensive agent state data"
    echo "2. Analyzing behavior patterns and identifying issues"
    echo "3. Generating specific debugging prompts for LLM analysis"
    echo "4. Providing automated fix capabilities"
    echo "5. Creating session artifacts for collaborative debugging"
    echo ""
}

# Parse command line arguments
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    show_help
    exit 0
fi

# Run main function
main "$@"

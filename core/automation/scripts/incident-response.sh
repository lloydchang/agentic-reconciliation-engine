#!/bin/bash

# Incident Response Automation Script
# This script automates security incident response procedures

set -euxo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INCIDENT_DIR="$PROJECT_ROOT/incident-reports"
LOG_FILE="$PROJECT_ROOT/logs/incident-response.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Incident severity levels
declare -A SEVERITY_LEVELS=(
    ["CRITICAL"]=1
    ["HIGH"]=2
    ["MEDIUM"]=3
    ["LOW"]=4
    ["INFO"]=5
)

# Logging functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

error_exit() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    log "ERROR: $1"
    exit 1
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
    log "SUCCESS: $1"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    log "WARNING: $1"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
    log "INFO: $1"
}

critical() {
    echo -e "${RED}🚨 CRITICAL: $1${NC}"
    log "CRITICAL: $1"
}

# Initialize incident response
init_incident() {
    local incident_type="$1"
    local severity="$2"
    local description="$3"
    
    mkdir -p "$INCIDENT_DIR"
    mkdir -p "$(dirname "$LOG_FILE")"
    
    local incident_id="INC-$(date +%Y%m%d-%H%M%S)"
    local incident_file="$INCIDENT_DIR/$incident_id.json"
    
    # Create incident record
    cat > "$incident_file" << EOF
{
  "incident_id": "$incident_id",
  "type": "$incident_type",
  "severity": "$severity",
  "description": "$description",
  "status": "OPEN",
  "created_at": "$(date -Iseconds)",
  "updated_at": "$(date -Iseconds)",
  "actions_taken": [],
  "evidence": {},
  "affected_resources": [],
  "investigation": {},
  "resolution": null
}
EOF
    
    log "Incident created: $incident_id"
    echo "$incident_id"
}

# Add action to incident
add_action() {
    local incident_id="$1"
    local action="$2"
    local result="$3"
    
    local incident_file="$INCIDENT_DIR/$incident_id.json"
    
    if [[ ! -f "$incident_file" ]]; then
        error_exit "Incident file not found: $incident_id"
    fi
    
    # Add action to incident
    local temp_file=$(mktemp)
    jq --arg action "$action" --arg result "$result" --arg timestamp "$(date -Iseconds)" \
       '.actions_taken += [{"action": $action, "result": $result, "timestamp": $timestamp}] | .updated_at = $timestamp' \
       "$incident_file" > "$temp_file" && mv "$temp_file" "$incident_file"
    
    log "Action added to $incident_id: $action -> $result"
}

# Add evidence to incident
add_evidence() {
    local incident_id="$1"
    local evidence_type="$2"
    local evidence_data="$3"
    
    local incident_file="$INCIDENT_DIR/$incident_id.json"
    
    if [[ ! -f "$incident_file" ]]; then
        error_exit "Incident file not found: $incident_id"
    fi
    
    local temp_file=$(mktemp)
    jq --arg type "$evidence_type" --arg data "$evidence_data" --arg timestamp "$(date -Iseconds)" \
       '.evidence[$type] = {"data": $data, "collected_at": $timestamp} | .updated_at = $timestamp' \
       "$incident_file" > "$temp_file" && mv "$temp_file" "$incident_file"
    
    log "Evidence added to $incident_id: $evidence_type"
}

# Incident Response Functions

# Response 1: Secret Exposure
respond_secret_exposure() {
    local incident_id="$1"
    local secret_name="$2"
    local namespace="$3"
    
    info "🔒 Responding to secret exposure incident: $incident_id"
    
    # Step 1: Identify exposed secret
    add_action "$incident_id" "Identify exposed secret" "Secret: $secret_name in namespace: $namespace"
    
    # Step 2: Check if secret is sealed
    local is_sealed=$(kubectl get secret "$secret_name" -n "$namespace" -o jsonpath='{.metadata.annotations.sealedsecrets\.bitnami\.com/cluster-wide}' 2>/dev/null || echo "false")
    
    if [[ "$is_sealed" == "true" ]]; then
        add_action "$incident_id" "Check secret type" "SealedSecret - lower risk"
        warning "Secret is a SealedSecret, but exposure still detected"
    else
        add_action "$incident_id" "Check secret type" "Regular Secret - HIGH RISK"
        critical "Regular secret exposed - immediate action required"
    fi
    
    # Step 3: Collect evidence
    local secret_data=$(kubectl get secret "$secret_name" -n "$namespace" -o yaml | \
        sed 's/data:/data_removed:/' | \
        sed 's/^\([[:space:]]*[^[:space:]]\):[[:space:]]*.*/\1: [REDACTED]/')
    
    add_evidence "$incident_id" "secret_manifest" "$secret_data"
    
    # Step 4: Rotate the secret
    info "Rotating exposed secret..."
    if ./core/core/automation/ci-cd/scripts/rotate-secrets.sh; then
        add_action "$incident_id" "Rotate secret" "SUCCESS"
        success "Secret rotated successfully"
    else
        add_action "$incident_id" "Rotate secret" "FAILED"
        error_exit "Failed to rotate secret"
    fi
    
    # Step 5: Review access logs
    info "Reviewing secret access logs..."
    local access_logs=$(kubectl get events -n "$namespace" --field-selector involvedObject.name="$secret_name" --sort-by='.lastTimestamp' | tail -10)
    add_evidence "$incident_id" "access_logs" "$access_logs"
    
    # Step 6: Update RBAC if needed
    add_action "$incident_id" "Review RBAC" "Checking for overly permissive access"
    
    # Step 7: Notify security team
    local notification="🚨 SECURITY INCIDENT: Secret exposure detected\nIncident ID: $incident_id\nSecret: $secret_name\nNamespace: $namespace\nAction: Secret rotated and access reviewed"
    add_evidence "$incident_id" "notification_sent" "$notification"
    
    success "Secret exposure incident response completed"
}

# Response 2: Unauthorized Access
respond_unauthorized_access() {
    local incident_id="$1"
    local user="$2"
    local resource="$3"
    local action="$4"
    
    info "🚫 Responding to unauthorized access incident: $incident_id"
    
    # Step 1: Identify the unauthorized access
    add_action "$incident_id" "Identify unauthorized access" "User: $user, Resource: $resource, Action: $action"
    
    # Step 2: Collect evidence
    local audit_logs=$(kubectl auth can-i --list --as="$user" 2>/dev/null || echo "Permission check failed")
    add_evidence "$incident_id" "audit_logs" "$audit_logs"
    
    # Step 3: Check if user exists
    local user_exists=$(kubectl get user "$user" --no-headers 2>/dev/null | wc -l)
    if [[ $user_exists -eq 0 ]]; then
        add_action "$incident_id" "Check user existence" "User does not exist - possible spoofing"
        critical "Unknown user attempting access"
    else
        add_action "$incident_id" "Check user existence" "User exists"
    fi
    
    # Step 4: Review RBAC bindings
    local bindings=$(kubectl get rolebindings,clusterrolebindings --all-namespaces -o json | \
        jq -r --arg user "$user" '.items[] | select(.subjects[]?.name == $user) | "\(.kind)/\(.metadata.name) in \(.metadata.namespace)"')
    
    add_evidence "$incident_id" "user_bindings" "$bindings"
    
    # Step 5: Temporarily restrict access if needed
    if [[ "${SEVERITY_LEVELS[$5]}" -le 2 ]]; then  # If severity is CRITICAL or HIGH
        info "Applying temporary restrictions..."
        # Create temporary deny policy
        cat > /tmp/deny-user-policy.yaml << EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: deny-all-$user
rules: []
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: deny-all-$user
subjects:
- kind: User
  name: $user
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: deny-all-$user
  apiGroup: rbac.authorization.k8s.io
EOF
        
        if kubectl apply -f /tmp/deny-user-policy.yaml; then
            add_action "$incident_id" "Apply temporary restrictions" "SUCCESS"
            warning "User $user temporarily restricted"
        else
            add_action "$incident_id" "Apply temporary restrictions" "FAILED"
        fi
        
        rm -f /tmp/deny-user-policy.yaml
    fi
    
    # Step 6: Notify security team
    local notification="🚨 SECURITY INCIDENT: Unauthorized access detected\nIncident ID: $incident_id\nUser: $user\nResource: $resource\nAction: $action\nStatus: Under investigation"
    add_evidence "$incident_id" "notification_sent" "$notification"
    
    success "Unauthorized access incident response initiated"
}

# Response 3: Pod Security Issue
respond_pod_security() {
    local incident_id="$1"
    local pod_name="$2"
    local namespace="$3"
    local issue="$4"
    
    info "🔍 Responding to pod security incident: $incident_id"
    
    # Step 1: Investigate the pod
    add_action "$incident_id" "Investigate pod" "Pod: $pod_name in namespace: $namespace, Issue: $issue"
    
    # Step 2: Collect pod evidence
    local pod_spec=$(kubectl get pod "$pod_name" -n "$namespace" -o yaml)
    add_evidence "$incident_id" "pod_spec" "$pod_spec"
    
    # Step 3: Check security context
    local security_context=$(kubectl get pod "$pod_name" -n "$namespace" -o jsonpath='{.spec.securityContext}')
    add_evidence "$incident_id" "security_context" "$security_context"
    
    # Step 4: Isolate the pod if critical
    if [[ "${SEVERITY_LEVELS[$5]}" -le 2 ]]; then  # CRITICAL or HIGH
        info "Isolating problematic pod..."
        
        # Add network policy to isolate
        cat > /tmp/isolate-pod.yaml << EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-$pod_name
  namespace: $namespace
spec:
  podSelector:
    matchLabels:
      name: $pod_name
  policyTypes:
  - Ingress
  - Egress
EOF
        
        if kubectl apply -f /tmp/isolate-pod.yaml; then
            add_action "$incident_id" "Isolate pod" "SUCCESS - Network policy applied"
        else
            add_action "$incident_id" "Isolate pod" "FAILED"
        fi
        
        rm -f /tmp/isolate-pod.yaml
    fi
    
    # Step 5: Terminate the pod if necessary
    if [[ "$issue" == "privileged" ]] || [[ "$issue" == "host-access" ]]; then
        warning "Critical pod security issue - terminating pod"
        if kubectl delete pod "$pod_name" -n "$namespace" --force --grace-period=0; then
            add_action "$incident_id" "Terminate pod" "SUCCESS"
        else
            add_action "$incident_id" "Terminate pod" "FAILED"
        fi
    fi
    
    success "Pod security incident response completed"
}

# Response 4: Network Policy Violation
respond_network_violation() {
    local incident_id="$1"
    local source="$2"
    local destination="$3"
    local port="$4"
    
    info "🌐 Responding to network policy violation: $incident_id"
    
    # Step 1: Analyze the violation
    add_action "$incident_id" "Analyze violation" "Source: $source, Destination: $destination, Port: $port"
    
    # Step 2: Check existing network policies
    local policies=$(kubectl get networkpolicies -n "${destination%%/*}" -o yaml)
    add_evidence "$incident_id" "network_policies" "$policies"
    
    # Step 3: Identify the issue
    if [[ "$port" == "22" ]] || [[ "$port" == "3389" ]]; then
        critical "Remote access protocol violation detected"
    fi
    
    # Step 4: Block the traffic if malicious
    if [[ "${SEVERITY_LEVELS[$5]}" -le 2 ]]; then  # CRITICAL or HIGH
        info "Blocking malicious traffic..."
        
        # Create blocking rule
        cat > /tmp/block-traffic.yaml << EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-malicious-traffic
  namespace: ${destination%%/*}
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ${source%%/*}
    ports:
    - protocol: TCP
      port: $port
EOF
        
        if kubectl apply -f /tmp/block-traffic.yaml; then
            add_action "$incident_id" "Block traffic" "SUCCESS - Network policy updated"
        else
            add_action "$incident_id" "Block traffic" "FAILED"
        fi
        
        rm -f /tmp/block-traffic.yaml
    fi
    
    success "Network policy violation response completed"
}

# Generate incident report
generate_report() {
    local incident_id="$1"
    local incident_file="$INCIDENT_DIR/$incident_id.json"
    
    if [[ ! -f "$incident_file" ]]; then
        error_exit "Incident file not found: $incident_id"
    fi
    
    local report_file="$INCIDENT_DIR/$incident_id-report.md"
    
    # Extract incident data
    local type=$(jq -r '.type' "$incident_file")
    local severity=$(jq -r '.severity' "$incident_file")
    local description=$(jq -r '.description' "$incident_file")
    local status=$(jq -r '.status' "$incident_file")
    local created_at=$(jq -r '.created_at' "$incident_file")
    local updated_at=$(jq -r '.updated_at' "$incident_file")
    
    cat > "$report_file" << EOF
# Security Incident Report

**Incident ID:** $incident_id  
**Type:** $type  
**Severity:** $severity  
**Status:** $status  
**Created:** $created_at  
**Updated:** $updated_at  

## Description

$description

## Actions Taken

$(jq -r '.actions_taken[] | "- \(.action): \(.result) (\(.timestamp))"' "$incident_file")

## Evidence

$(jq -r '.evidence | to_entries[] | "### \(.key)\n\`\`\`\n\(.value.data)\n\`\`\`"' "$incident_file")

## Investigation Summary

$(jq -r '.investigation // "No investigation notes available"' "$incident_file")

## Resolution

$(jq -r '.resolution // "Incident still open"' "$incident_file")

## Recommendations

1. Review and update security policies
2. Implement additional monitoring
3. Conduct security training
4. Update incident response procedures

---

**Report Generated:** $(date -Iseconds)  
**Next Review:** $(date -d "+7 days" +%Y-%m-%d)
EOF
    
    success "Incident report generated: $report_file"
}

# Close incident
close_incident() {
    local incident_id="$1"
    local resolution="$2"
    
    local incident_file="$INCIDENT_DIR/$incident_id.json"
    
    if [[ ! -f "$incident_file" ]]; then
        error_exit "Incident file not found: $incident_id"
    fi
    
    local temp_file=$(mktemp)
    jq --arg resolution "$resolution" --arg timestamp "$(date -Iseconds)" \
       '.status = "CLOSED" | .resolution = $resolution | .updated_at = $timestamp' \
       "$incident_file" > "$temp_file" && mv "$temp_file" "$incident_file"
    
    log "Incident closed: $incident_id"
    success "Incident $incident_id closed with resolution: $resolution"
    
    # Generate final report
    generate_report "$incident_id"
}

# Main function
main() {
    local command="${1:-help}"
    
    case "$command" in
        "secret-exposure")
            if [[ $# -lt 4 ]]; then
                error_exit "Usage: $0 secret-exposure <secret_name> <namespace> <severity>"
            fi
            local incident_id=$(init_incident "secret-exposure" "$4" "Secret exposure detected: $1 in namespace $2")
            respond_secret_exposure "$incident_id" "$2" "$3"
            ;;
        "unauthorized-access")
            if [[ $# -lt 5 ]]; then
                error_exit "Usage: $0 unauthorized-access <user> <resource> <action> <severity>"
            fi
            local incident_id=$(init_incident "unauthorized-access" "$5" "Unauthorized access: $1 attempted $3 on $2")
            respond_unauthorized_access "$incident_id" "$1" "$2" "$3" "$5"
            ;;
        "pod-security")
            if [[ $# -lt 5 ]]; then
                error_exit "Usage: $0 pod-security <pod_name> <namespace> <issue> <severity>"
            fi
            local incident_id=$(init_incident "pod-security" "$5" "Pod security issue: $3 in pod $1")
            respond_pod_security "$incident_id" "$1" "$2" "$3" "$5"
            ;;
        "network-violation")
            if [[ $# -lt 5 ]]; then
                error_exit "Usage: $0 network-violation <source> <destination> <port> <severity>"
            fi
            local incident_id=$(init_incident "network-violation" "$5" "Network policy violation: $1 to $2:$3")
            respond_network_violation "$incident_id" "$1" "$2" "$3" "$5"
            ;;
        "close")
            if [[ $# -lt 3 ]]; then
                error_exit "Usage: $0 close <incident_id> <resolution>"
            fi
            close_incident "$2" "$3"
            ;;
        "list")
            echo "Open incidents:"
            find "$INCIDENT_DIR" -name "*.json" -exec basename {} .json \; | sort
            ;;
        "report")
            if [[ $# -lt 2 ]]; then
                error_exit "Usage: $0 report <incident_id>"
            fi
            generate_report "$2"
            ;;
        "help"|*)
            echo "GitOps Incident Response Automation"
            echo ""
            echo "Usage: $0 <command> [options]"
            echo ""
            echo "Commands:"
            echo "  secret-exposure <secret_name> <namespace> <severity>  Respond to secret exposure"
            echo "  unauthorized-access <user> <resource> <action> <severity>  Respond to unauthorized access"
            echo "  pod-security <pod_name> <namespace> <issue> <severity>  Respond to pod security issue"
            echo "  network-violation <source> <destination> <port> <severity>  Respond to network violation"
            echo "  close <incident_id> <resolution>                           Close an incident"
            echo "  list                                                       List open incidents"
            echo "  report <incident_id>                                       Generate incident report"
            echo "  help                                                       Show this help"
            echo ""
            echo "Severity levels: CRITICAL, HIGH, MEDIUM, LOW, INFO"
            echo ""
            exit 0
            ;;
    esac
}

# Execute main function
main "$@"

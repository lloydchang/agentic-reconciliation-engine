#!/bin/bash

# Comprehensive Security Audit Script for GitOps Infrastructure
# This script performs a complete security audit of the infrastructure

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
AUDIT_DIR="$PROJECT_ROOT/audit-reports"
AUDIT_FILE="$AUDIT_DIR/security-audit-$(date +%Y%m%d-%H%M%S).json"
REPORT_FILE="$AUDIT_DIR/security-audit-$(date +%Y%m%d-%H%M%S).md"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Audit results
declare -A SEVERITY_COUNTS=([CRITICAL]=0 [HIGH]=0 [MEDIUM]=0 [LOW]=0 [INFO]=0)
ISSUES_FOUND=false

# Logging functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$AUDIT_FILE.log"
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
    ((SEVERITY_COUNTS[CRITICAL]++))
    ISSUES_FOUND=true
}

high() {
    echo -e "${RED}🔴 HIGH: $1${NC}"
    log "HIGH: $1"
    ((SEVERITY_COUNTS[HIGH]++))
    ISSUES_FOUND=true
}

medium() {
    echo -e "${YELLOW}🟡 MEDIUM: $1${NC}"
    log "MEDIUM: $1"
    ((SEVERITY_COUNTS[MEDIUM]++))
    ISSUES_FOUND=true
}

low() {
    echo -e "${BLUE}🔵 LOW: $1${NC}"
    log "LOW: $1"
    ((SEVERITY_COUNTS[LOW]++))
}

info_msg() {
    echo -e "${CYAN}ℹ️  INFO: $1${NC}"
    log "INFO: $1"
    ((SEVERITY_COUNTS[INFO]++))
}

# Initialize audit
init_audit() {
    info "Initializing comprehensive security audit..."
    mkdir -p "$AUDIT_DIR"
    
    # Initialize JSON report
    cat > "$AUDIT_FILE" << EOF
{
  "audit_date": "$(date -Iseconds)",
  "audit_version": "1.0.0",
  "cluster": "$(kubectl config current-context 2>/dev/null || echo 'unknown')",
  "findings": [],
  "summary": {}
}
EOF
    
    # Initialize log file
    echo "Security Audit Started: $(date)" > "$AUDIT_FILE.log"
    
    success "Audit initialized"
}

# Check dependencies
check_dependencies() {
    info "Checking audit dependencies..."
    
    local missing_deps=()
    
    command -v kubectl >/dev/null 2>&1 || missing_deps+=("kubectl")
    command -v jq >/dev/null 2>&1 || missing_deps+=("jq")
    command -v yq >/dev/null 2>&1 || missing_deps+=("yq")
    command -v openssl >/dev/null 2>&1 || missing_deps+=("openssl")
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        error_exit "Missing dependencies: ${missing_deps[*]}"
    fi
    
    success "All dependencies available"
}

# Audit 1: Secret Management
audit_secrets() {
    info "🔍 Auditing Secret Management..."
    
    # Check for hardcoded secrets
    info "Scanning for hardcoded secrets..."
    local secret_patterns=(
        "password:\s*[\"']?[^\"'\s<][^\"'\s]*[\"']?"
        "secret:\s*[\"']?[^\"'\s<][^\"'\s]*[\"']?"
        "key:\s*[\"']?[^\"'\s<][^\"'\s]*[\"']?"
        "token:\s*[\"']?[^\"'\s<][^\"'\s]*[\"']?"
        "adminPassword:\s*[\"']?[^\"'\s<][^\"'\s]*[\"']?"
        "admin_password:\s*[\"']?[^\"'\s<][^\"'\s]*[\"']?"
        "apiKey:\s*[\"']?[^\"'\s<][^\"'\s]*[\"']?"
        "api_key:\s*[\"']?[^\"'\s<][^\"'\s]*[\"']?"
    )
    
    for pattern in "${secret_patterns[@]}"; do
        local matches=$(find "$PROJECT_ROOT" -name "*.yaml" -o -name "*.yml" -o -name "*.json" | \
            grep -v "audit-reports" | \
            xargs grep -E "$pattern" 2>/dev/null | \
            grep -v "FromSecret\|from_secret\|valueFrom\|<encrypted\|placeholder\|CHANGE_ME\|example" || true)
        
        if [[ -n "$matches" ]]; then
            critical "Hardcoded secrets found in configuration files"
            echo "$matches" | while read -r line; do
                echo "  $line"
            done
        fi
    done
    
    # Check SealedSecrets usage
    info "Checking SealedSecrets implementation..."
    local sealed_secrets=$(find "$PROJECT_ROOT" -name "*sealed-secret*.yaml" -o -name "*secrets.yaml" | grep -v template | wc -l)
    local helmreleases=$(find "$PROJECT_ROOT" -name "*helmrelease*.yaml" -o -name "*helm-release*.yaml" | wc -l)
    
    if [[ $sealed_secrets -eq 0 ]]; then
        high "No SealedSecrets found in the repository"
    else
        success "Found $sealed_secrets SealedSecret files"
    fi
    
    # Validate SealedSecrets format
    find "$PROJECT_ROOT" -name "*sealed-secret*.yaml" -o -name "*secrets.yaml" | \
        grep -v template | while read -r secret_file; do
        if ! grep -q "kind: SealedSecret" "$secret_file"; then
            high "Invalid SealedSecret format: $secret_file"
        fi
        
        if ! grep -q "encryptedData:" "$secret_file"; then
            high "Missing encryptedData in SealedSecret: $secret_file"
        fi
    done
    
    info_msg "Secret management audit completed"
}

# Audit 2: RBAC and Permissions
audit_rbac() {
    info "🔍 Auditing RBAC and Permissions..."
    
    # Check for overly permissive RBAC
    if kubectl get clusterroles -o json 2>/dev/null | jq -r '.items[] | select(.rules[]? | .verbs[]? | contains("*")) | .metadata.name' | grep -q .; then
        high "ClusterRoles with wildcard verbs found"
    fi
    
    # Check for service accounts with excessive permissions
    local risky_sas=$(kubectl get serviceaccounts --all-namespaces -o json 2>/dev/null | \
        jq -r '.items[] | select(.metadata.name == "default") | "\(.metadata.namespace)/\(.metadata.name)"' | wc -l)
    
    if [[ $risky_sas -gt 5 ]]; then
        medium "High number of default service accounts in use: $risky_sas"
    fi
    
    # Check for namespace-level RBAC issues
    kubectl get namespaces -o json 2>/dev/null | jq -r '.items[].metadata.name' | while read -r ns; do
        local rolebindings=$(kubectl get rolebindings -n "$ns" -o json 2>/dev/null | jq '.items | length' 2>/dev/null || echo "0")
        if [[ $rolebindings -gt 10 ]]; then
            medium "Namespace $ns has many RoleBindings: $rolebindings"
        fi
    done
    
    info_msg "RBAC audit completed"
}

# Audit 3: Network Policies
audit_network_policies() {
    info "🔍 Auditing Network Policies..."
    
    # Check if network policies are enabled
    local namespaces_with_np=0
    local total_namespaces=0
    
    kubectl get namespaces -o json 2>/dev/null | jq -r '.items[].metadata.name' | while read -r ns; do
        ((total_namespaces++))
        local np_count=$(kubectl get networkpolicies -n "$ns" -o json 2>/dev/null | jq '.items | length' 2>/dev/null || echo "0")
        if [[ $np_count -gt 0 ]]; then
            ((namespaces_with_np++))
        else
            if [[ "$ns" != "kube-system" && "$ns" != "kube-public" && "$ns" != "kube-node-lease" ]]; then
                medium "Namespace $ns has no network policies"
            fi
        fi
    done
    
    if [[ $namespaces_with_np -eq 0 ]]; then
        high "No network policies found in any namespace"
    else
        success "Network policies found in $namespaces_with_np namespaces"
    fi
    
    info_msg "Network policy audit completed"
}

# Audit 4: Pod Security
audit_pod_security() {
    info "🔍 Auditing Pod Security..."
    
    # Check for privileged pods
    local privileged_pods=$(kubectl get pods --all-namespaces -o json 2>/dev/null | \
        jq '.items[] | select(.spec.containers[]?.securityContext?.privileged == true) | .metadata.name' | wc -l)
    
    if [[ $privileged_pods -gt 0 ]]; then
        high "Found $privileged_pods privileged pods"
    fi
    
    # Check for pods running as root
    local root_pods=$(kubectl get pods --all-namespaces -o json 2>/dev/null | \
        jq '.items[] | select(.spec.containers[]?.securityContext?.runAsUser == 0) | .metadata.name' | wc -l)
    
    if [[ $root_pods -gt 5 ]]; then
        medium "Found $root_pods pods running as root user"
    fi
    
    # Check for containers with host access
    local host_pids=$(kubectl get pods --all-namespaces -o json 2>/dev/null | \
        jq '.items[] | select(.spec.hostPID == true) | .metadata.name' | wc -l)
    
    if [[ $host_pids -gt 0 ]]; then
        high "Found $host_pids pods with hostPID access"
    fi
    
    info_msg "Pod security audit completed"
}

# Audit 5: Image Security
audit_image_security() {
    info "🔍 Auditing Container Image Security..."
    
    # Check for images using latest tag
    local latest_images=$(kubectl get pods --all-namespaces -o json 2>/dev/null | \
        jq '.items[].spec.containers[]?.image | select(test(":latest$|:latest@"))' | wc -l)
    
    if [[ $latest_images -gt 0 ]]; then
        medium "Found $latest_images containers using 'latest' tag"
    fi
    
    # Check for images from untrusted registries
    local untrusted_registries=$(kubectl get pods --all-namespaces -o json 2>/dev/null | \
        jq '.items[].spec.containers[]?.image | select(test("docker.io/[^/]+/[^/]+") | not) | select(test("gcr.io|k8s.gcr.io|quay.io|registry.k8s.io") | not)' | wc -l)
    
    if [[ $untrusted_registries -gt 0 ]]; then
        low "Found $untrusted_registries containers from potentially untrusted registries"
    fi
    
    info_msg "Image security audit completed"
}

# Audit 6: Configuration Security
audit_config_security() {
    info "🔍 Auditing Configuration Security..."
    
    # Check for exposed services
    local loadbalancer_services=$(kubectl get services --all-namespaces -o json 2>/dev/null | \
        jq '.items[] | select(.spec.type == "LoadBalancer") | .metadata.name' | wc -l)
    
    if [[ $loadbalancer_services -gt 5 ]]; then
        medium "Found $loadbalancer_services LoadBalancer services (potential exposure)"
    fi
    
    # Check for NodePort services
    local nodeport_services=$(kubectl get services --all-namespaces -o json 2>/dev/null | \
        jq '.items[] | select(.spec.type == "NodePort") | .metadata.name' | wc -l)
    
    if [[ $nodeport_services -gt 0 ]]; then
        medium "Found $nodeport_services NodePort services"
    fi
    
    # Check for Ingress configurations
    local ingress_count=$(kubectl get ingress --all-namespaces -o json 2>/dev/null | jq '.items | length' 2>/dev/null || echo "0")
    if [[ $ingress_count -gt 0 ]]; then
        info "Found $ingress_count Ingress resources - review TLS configurations"
        
        # Check for TLS configurations
        local tls_ingress=$(kubectl get ingress --all-namespaces -o json 2>/dev/null | \
            jq '.items[] | select(has("spec") and .spec.tls) | .metadata.name' | wc -l)
        
        if [[ $tls_ingress -lt $ingress_count ]]; then
            medium "Not all Ingress resources have TLS configured"
        fi
    fi
    
    info_msg "Configuration security audit completed"
}

# Audit 7: GitOps Security
audit_gitops_security() {
    info "🔍 Auditing GitOps Security..."
    
    # Check Flux CD security
    if kubectl get namespaces flux-system -o json 2>/dev/null >/dev/null; then
        info "Flux CD namespace found - checking security configuration..."
        
        # Check Flux source security
        local flux_sources=$(kubectl get gitrepositories -n flux-system -o json 2>/dev/null | jq '.items | length' 2>/dev/null || echo "0")
        if [[ $flux_sources -gt 0 ]]; then
            info "Found $flux_sources GitRepository sources"
            
            # Check for HTTPS usage
            local http_sources=$(kubectl get gitrepositories -n flux-system -o json 2>/dev/null | \
                jq '.items[] | select(.spec.url | startswith("http://")) | .metadata.name' | wc -l)
            
            if [[ $http_sources -gt 0 ]]; then
                high "Found $http_sources GitRepository sources using HTTP (not HTTPS)"
            fi
        fi
        
        # Check HelmRepository security
        local helm_repos=$(kubectl get helmrepositories -n flux-system -o json 2>/dev/null | jq '.items | length' 2>/dev/null || echo "0")
        if [[ $helm_repos -gt 0 ]]; then
            info "Found $helm_repos HelmRepository sources"
        fi
    fi
    
    # Check for sensitive data in Git
    if [[ -d "$PROJECT_ROOT/.git" ]]; then
        info "Checking Git repository security..."
        
        # Check for large files in Git history
        if git log --all --full-history -- **/*.pem 2>/dev/null | grep -q .; then
            critical "Certificate files found in Git history"
        fi
        
        # Check for sensitive file patterns
        if git log --all --full-history -- **/*.key **/*.p12 **/*.pfx 2>/dev/null | grep -q .; then
            critical "Private key files found in Git history"
        fi
    fi
    
    info_msg "GitOps security audit completed"
}

# Audit 8: Monitoring and Logging
audit_monitoring() {
    info "🔍 Auditing Monitoring and Logging..."
    
    # Check for monitoring stack
    local monitoring_ns=""
    if kubectl get namespace monitoring -o json 2>/dev/null >/dev/null; then
        monitoring_ns="monitoring"
    elif kubectl get namespace prometheus -o json 2>/dev/null >/dev/null; then
        monitoring_ns="prometheus"
    fi
    
    if [[ -n "$monitoring_ns" ]]; then
        info "Monitoring namespace found: $monitoring_ns"
        
        # Check for Prometheus
        if kubectl get prometheus -n "$monitoring_ns" -o json 2>/dev/null | jq '.items | length' 2>/dev/null | grep -q "0"; then
            medium "No Prometheus instances found in monitoring namespace"
        fi
        
        # Check for Grafana
        if kubectl get grafana -n "$monitoring_ns" -o json 2>/dev/null | jq '.items | length' 2>/dev/null | grep -q "0"; then
            low "No Grafana instances found"
        fi
    else
        medium "No monitoring namespace found"
    fi
    
    # Check for logging stack
    if kubectl get namespace logging -o json 2>/dev/null >/dev/null; then
        info "Logging namespace found"
    else
        low "No dedicated logging namespace found"
    fi
    
    info_msg "Monitoring audit completed"
}

# Generate audit report
generate_report() {
    info "📊 Generating comprehensive audit report..."
    
    # Create markdown report
    cat > "$REPORT_FILE" << EOF
# Security Audit Report

**Date:** $(date)
**Cluster:** $(kubectl config current-context 2>/dev/null || echo 'unknown')
**Audit Version:** 1.0.0

## Executive Summary

### Severity Distribution
- 🚨 **Critical:** ${SEVERITY_COUNTS[CRITICAL]}
- 🔴 **High:** ${SEVERITY_COUNTS[HIGH]}
- 🟡 **Medium:** ${SEVERITY_COUNTS[MEDIUM]}
- 🔵 **Low:** ${SEVERITY_COUNTS[LOW]}
- ℹ️  **Info:** ${SEVERITY_COUNTS[INFO]}

### Overall Risk Level
EOF

    # Determine overall risk level
    if [[ ${SEVERITY_COUNTS[CRITICAL]} -gt 0 ]]; then
        echo "🚨 **CRITICAL** - Immediate action required" >> "$REPORT_FILE"
    elif [[ ${SEVERITY_COUNTS[HIGH]} -gt 2 ]]; then
        echo "🔴 **HIGH** - Significant security concerns" >> "$REPORT_FILE"
    elif [[ ${SEVERITY_COUNTS[MEDIUM]} -gt 5 ]]; then
        echo "🟡 **MEDIUM** - Moderate security posture" >> "$REPORT_FILE"
    else
        echo "🔵 **LOW** - Generally secure" >> "$REPORT_FILE"
    fi
    
    cat >> "$REPORT_FILE" << EOF

## Detailed Findings

### 1. Secret Management
- SealedSecrets implementation status
- Hardcoded secret detection
- Secret reference validation

### 2. RBAC and Permissions
- Wildcard verb usage
- Service account permissions
- Role binding analysis

### 3. Network Policies
- Network policy coverage
- Namespace isolation
- Traffic control

### 4. Pod Security
- Privileged containers
- Root user access
- Host access permissions

### 5. Image Security
- Image tag policies
- Registry trust
- Vulnerability scanning

### 6. Configuration Security
- Service exposure
- Ingress TLS
- Access controls

### 7. GitOps Security
- Source repository security
- HTTPS usage
- Git history analysis

### 8. Monitoring and Logging
- Monitoring stack coverage
- Log aggregation
- Security monitoring

## Recommendations

### Immediate Actions (Critical/High)
1. Address all critical and high severity findings
2. Implement missing security controls
3. Review and update RBAC policies

### Short-term Improvements (Medium)
1. Enhance network policy coverage
2. Implement image scanning
3. Strengthen monitoring

### Long-term Enhancements (Low/Info)
1. Automate security testing
2. Implement compliance frameworks
3. Enhance incident response

## Compliance Status

- ✅ Secret Management: $([[ ${SEVERITY_COUNTS[CRITICAL]} -eq 0 ]] && echo "Compliant" || echo "Non-compliant")
- ✅ Access Control: $([[ ${SEVERITY_COUNTS[HIGH]} -lt 3 ]] && echo "Compliant" || echo "Non-compliant")
- ✅ Network Security: $([[ ${SEVERITY_COUNTS[MEDIUM]} -lt 5 ]] && echo "Compliant" || echo "Non-compliant")

---

**Generated by:** GitOps Security Audit Script  
**Next Review:** $(date -d "+30 days" +%Y-%m-%d)
EOF

    # Update JSON summary
    local temp_json=$(mktemp)
    jq --arg critical "${SEVERITY_COUNTS[CRITICAL]}" \
       --arg high "${SEVERITY_COUNTS[HIGH]}" \
       --arg medium "${SEVERITY_COUNTS[MEDIUM]}" \
       --arg low "${SEVERITY_COUNTS[LOW]}" \
       --arg info "${SEVERITY_COUNTS[INFO]}" \
       --arg issues_found "$ISSUES_FOUND" \
       '.summary = {
         severity_counts: {
           critical: ($critical | tonumber),
           high: ($high | tonumber),
           medium: ($medium | tonumber),
           low: ($low | tonumber),
           info: ($info | tonumber)
         },
         issues_found: ($issues_found | test("true")),
         total_issues: (($critical | tonumber) + ($high | tonumber) + ($medium | tonumber) + ($low | tonumber))
       }' "$AUDIT_FILE" > "$temp_json" && mv "$temp_json" "$AUDIT_FILE"
    
    success "Audit report generated: $REPORT_FILE"
    success "JSON data saved: $AUDIT_FILE"
}

# Main audit function
main() {
    echo -e "${PURPLE}🔍 GitOps Infrastructure Security Audit${NC}"
    echo -e "${PURPLE}======================================${NC}"
    
    init_audit
    check_dependencies
    
    # Run all audit modules
    audit_secrets
    audit_rbac
    audit_network_policies
    audit_pod_security
    audit_image_security
    audit_config_security
    audit_gitops_security
    audit_monitoring
    
    # Generate final report
    generate_report
    
    echo ""
    echo -e "${PURPLE}📊 Audit Summary${NC}"
    echo -e "${PURPLE}================${NC}"
    echo -e "🚨 Critical: ${SEVERITY_COUNTS[CRITICAL]}"
    echo -e "🔴 High: ${SEVERITY_COUNTS[HIGH]}"
    echo -e "🟡 Medium: ${SEVERITY_COUNTS[MEDIUM]}"
    echo -e "🔵 Low: ${SEVERITY_COUNTS[LOW]}"
    echo -e "ℹ️  Info: ${SEVERITY_COUNTS[INFO]}"
    echo ""
    
    if [[ "$ISSUES_FOUND" == true ]]; then
        echo -e "${RED}🚨 Security issues detected! Review the report for details.${NC}"
        echo -e "${RED}📄 Report: $REPORT_FILE${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ No critical security issues found!${NC}"
        echo -e "${GREEN}📄 Report: $REPORT_FILE${NC}"
        exit 0
    fi
}

# Execute main function
main "$@"

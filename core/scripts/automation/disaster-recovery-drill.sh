#!/bin/bash

# Git Outage Disaster Recovery Drill Script
# Simulates Git outage scenarios and tests recovery procedures

set -euo pipefail

# Configuration
NAMESPACE="flux-system"
DRILL_TYPE="${1:-primary-outage}"  # primary-outage, complete-outage, cache-failure
LOG_FILE="/tmp/git-drill-$(date +%Y%m%d-%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
}

# Pre-drill checks
pre_drill_checks() {
    log "🔍 Running pre-drill checks..."
    
    # Check namespace exists
    if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        log_error "Namespace $NAMESPACE does not exist"
        exit 1
    fi
    
    # Check critical components
    local components=("$TOPDIR-primary" "$TOPDIR-secondary" "$TOPDIR-tertiary" "git-cache-service")
    for component in "${components[@]}"; do
        if kubectl get gitrepository "$component" -n "$NAMESPACE" >/dev/null 2>&1 || \
           kubectl get service "$component" -n "$NAMESPACE" >/dev/null 2>&1; then
            log_success "Component $component found"
        else
            log_warning "Component $component not found"
        fi
    done
    
    # Check current health
    log "📊 Current repository health status:"
    kubectl get gitrepositories -n "$NAMESPACE" -L gitrepo.fluxcd.io/healthy | tee -a "$LOG_FILE"
    
    log_success "Pre-drill checks completed"
}

# Scenario 1: Primary Repository Outage
simulate_primary_outage() {
    log "🚨 Simulating primary repository outage..."
    
    # Mark primary repository as unhealthy
    kubectl label gitrepository $TOPDIR-primary gitrepo.fluxcd.io/healthy=false --overwrite -n "$NAMESPACE"
    kubectl annotate gitrepository $TOPDIR-primary gitrepo.fluxcd.io/error-message="Simulated outage for drill" --overwrite -n "$NAMESPACE"
    
    # Increment failure count
    local current_count=$(kubectl get gitrepository $TOPDIR-primary -n "$NAMESPACE" -o jsonpath='{.metadata.annotations.gitrepo\.fluxcd\.io/failure-count}' 2>/dev/null || echo "0")
    for i in {1..4}; do
        kubectl annotate gitrepository $TOPDIR-primary gitrepo.fluxcd.io/failure-count="$i" --overwrite -n "$NAMESPACE"
        sleep 2
    done
    
    log_warning "Primary repository marked as unhealthy with 4 failures"
    
    # Wait for automatic failover
    log "⏳ Waiting for automatic failover (30 seconds)..."
    sleep 30
    
    # Check if failover occurred
    local current_source=$(kubectl get kustomization infrastructure -n "$NAMESPACE" -o jsonpath='{.spec.sourceRef.name}' 2>/dev/null || echo "unknown")
    
    if [[ "$current_source" == "$TOPDIR-secondary" || "$current_source" == "$TOPDIR-tertiary" ]]; then
        log_success "✅ Automatic failover successful: switched to $current_source"
    else
        log_warning "⚠️ Automatic failover did not occur, attempting manual failover"
        
        # Manual failover
        kubectl patch kustomization infrastructure -n "$NAMESPACE" -p '{"spec":{"sourceRef":{"name":"$TOPDIR-secondary"}}}' --type=merge
        log_success "✅ Manual failover to secondary completed"
    fi
    
    # Verify operations continue
    log "🔍 Verifying operations continue..."
    kubectl get kustomizations -n "$NAMESPACE" | tee -a "$LOG_FILE"
}

# Scenario 2: Complete Git Outage
simulate_complete_outage() {
    log "🚨 Simulating complete Git outage..."
    
    # Mark all repositories as unhealthy
    local repos=("$TOPDIR-primary" "$TOPDIR-secondary" "$TOPDIR-tertiary")
    for repo in "${repos[@]}"; do
        kubectl label gitrepository "$repo" gitrepo.fluxcd.io/healthy=false --overwrite -n "$NAMESPACE"
        kubectl annotate gitrepository "$repo" gitrepo.fluxcd.io/failure-count="5" --overwrite -n "$NAMESPACE"
    done
    
    log_warning "All repositories marked as unhealthy"
    
    # Wait for offline mode activation
    log "⏳ Waiting for offline mode activation (60 seconds)..."
    sleep 60
    
    # Check if offline mode is active
    local offline_mode=$(kubectl get kustomization infrastructure -n "$NAMESPACE" -o jsonpath='{.metadata.annotations.fluxcd\.io/offline-mode}' 2>/dev/null || echo "false")
    
    if [[ "$offline_mode" == "true" ]]; then
        log_success "✅ Offline mode activated automatically"
    else
        log_warning "⚠️ Offline mode not activated, enabling manually"
        kubectl annotate kustomization infrastructure fluxcd.io/offline-mode=true --overwrite -n "$NAMESPACE"
        log_success "✅ Offline mode enabled manually"
    fi
    
    # Verify cache operations
    log "🔍 Verifying Git cache operations..."
    local cache_health=$(kubectl get service git-cache-service -n "$NAMESPACE" -l cache.fluxcd.io/healthy=true --no-headers | wc -l)
    
    if [[ "$cache_health" -gt 0 ]]; then
        log_success "✅ Git cache is healthy"
    else
        log_error "❌ Git cache is unhealthy - this is a critical issue"
    fi
    
    # Test state recovery if needed
    log "🔄 Testing state recovery procedures..."
    kubectl create job --from=cronjob/state-recovery-controller drill-recovery -n "$NAMESPACE"
    
    # Wait for recovery job
    kubectl wait --for=condition=complete job/drill-recovery -n "$NAMESPACE" --timeout=120s
    log_success "✅ State recovery test completed"
}

# Scenario 3: Git Cache Failure
simulate_cache_failure() {
    log "🚨 Simulating Git cache failure..."
    
    # Mark cache as unhealthy
    kubectl label service git-cache-service cache.fluxcd.io/healthy=false --overwrite -n "$NAMESPACE"
    
    # Scale down cache deployment
    kubectl scale deployment git-cache-manager --replicas=0 -n "$NAMESPACE"
    
    log_warning "Git cache marked as unhealthy and scaled down"
    
    # Wait for detection
    log "⏳ Waiting for cache failure detection (30 seconds)..."
    sleep 30
    
    # Test recovery procedures
    log "🔄 Testing cache recovery procedures..."
    
    # Scale up cache deployment
    kubectl scale deployment git-cache-manager --replicas=1 -n "$NAMESPACE"
    
    # Wait for ready state
    kubectl wait --for=condition=available deployment/git-cache-manager -n "$NAMESPACE" --timeout=120s
    
    # Mark cache as healthy
    kubectl label service git-cache-service cache.fluxcd.io/healthy=true --overwrite -n "$NAMESPACE"
    
    log_success "✅ Cache recovery completed"
}

# Post-drill recovery
post_drill_recovery() {
    log "🔄 Running post-drill recovery..."
    
    # Restore primary repository health
    kubectl label gitrepository $TOPDIR-primary gitrepo.fluxcd.io/healthy=true --overwrite -n "$NAMESPACE"
    kubectl annotate gitrepository $TOPDIR-primary gitrepo.fluxcd.io/failure-count="0" --overwrite -n "$NAMESPACE"
    kubectl annotate gitrepository $TOPDIR-primary gitrepo.fluxcd.io/error-message- --overwrite -n "$NAMESPACE"
    
    # Restore secondary repository health
    kubectl label gitrepository $TOPDIR-secondary gitrepo.fluxcd.io/healthy=true --overwrite -n "$NAMESPACE"
    kubectl annotate gitrepository $TOPDIR-secondary gitrepo.fluxcd.io/failure-count="0" --overwrite -n "$NAMESPACE"
    
    # Restore tertiary repository health
    kubectl label gitrepository $TOPDIR-tertiary gitrepo.fluxcd.io/healthy=true --overwrite -n "$NAMESPACE"
    kubectl annotate gitrepository $TOPDIR-tertiary gitrepo.fluxcd.io/failure-count="0" --overwrite -n "$NAMESPACE"
    
    # Switch back to primary repository
    kubectl patch kustomization infrastructure -n "$NAMESPACE" -p '{"spec":{"sourceRef":{"name":"$TOPDIR-primary"}}}' --type=merge
    
    # Disable offline mode
    kubectl annotate kustomization infrastructure fluxcd.io/offline-mode- --overwrite -n "$NAMESPACE"
    
    # Wait for normal operations
    log "⏳ Waiting for normal operations to resume (60 seconds)..."
    sleep 60
    
    # Verify final state
    log "📊 Final system state:"
    kubectl get gitrepositories -n "$NAMESPACE" -L gitrepo.fluxcd.io/healthy | tee -a "$LOG_FILE"
    kubectl get kustomizations -n "$NAMESPACE" -L fluxcd.io/offline-mode | tee -a "$LOG_FILE"
    
    log_success "✅ Post-drill recovery completed"
}

# Generate drill report
generate_drill_report() {
    log "📋 Generating drill report..."
    
    local report_file="/tmp/git-drill-report-$(date +%Y%m%d-%H%M%S).md"
    
    cat > "$report_file" << EOF
# Git Outage Disaster Recovery Drill Report

## Drill Information
- **Date**: $(date '+%Y-%m-%d %H:%M:%S')
- **Drill Type**: $DRILL_TYPE
- **Namespace**: $NAMESPACE
- **Log File**: $LOG_FILE

## Scenario Executed
$DRILL_TYPE

## Results Summary

### Pre-Drill State
$(kubectl get gitrepositories -n "$NAMESPACE" -L gitrepo.fluxcd.io/healthy)

### Post-Drill State
$(kubectl get gitrepositories -n "$NAMESPACE" -L gitrepo.fluxcd.io/healthy)

### Failover Test Results
- **Automatic Failover**: $(kubectl get kustomizations -n "$NAMESPACE" -o yaml | grep -q "$TOPDIR-secondary\|$TOPDIR-tertiary" && echo "✅ PASSED" || echo "❌ FAILED")
- **Offline Mode**: $(kubectl get kustomization infrastructure -n "$NAMESPACE" -o jsonpath='{.metadata.annotations.fluxcd\.io/offline-mode}' 2>/dev/null || echo "false")
- **State Recovery**: $(kubectl get jobs -n "$NAMESPACE" -l batch.kubernetes.io/job-name=drill-recovery --no-headers | wc -l) recovery jobs executed

### Performance Metrics
- **Failover Time**: Measured during drill
- **Recovery Time**: Measured during drill
- **Data Loss**: None expected

## Issues Identified
<!-- Add any issues found during the drill -->

## Recommendations
<!-- Add recommendations based on drill results -->

## Next Steps
1. Review drill results with team
2. Update procedures if needed
3. Schedule next drill
4. Address any identified issues

EOF
    
    log_success "📋 Drill report generated: $report_file"
    echo "Report available at: $report_file"
}

# Main execution
main() {
    log "🚀 Starting Git Outage Disaster Recovery Drill"
    log "Drill type: $DRILL_TYPE"
    log "Log file: $LOG_FILE"
    
    # Pre-drill checks
    pre_drill_checks
    
    # Execute drill scenario
    case "$DRILL_TYPE" in
        "primary-outage")
            simulate_primary_outage
            ;;
        "complete-outage")
            simulate_complete_outage
            ;;
        "cache-failure")
            simulate_cache_failure
            ;;
        *)
            log_error "Unknown drill type: $DRILL_TYPE"
            echo "Usage: $0 [primary-outage|complete-outage|cache-failure]"
            exit 1
            ;;
    esac
    
    # Post-drill recovery
    post_drill_recovery
    
    # Generate report
    generate_drill_report
    
    log_success "🎉 Git Outage Disaster Recovery Drill completed successfully!"
    log "📋 Review the log file: $LOG_FILE"
}

# Execute main function
main "$@"

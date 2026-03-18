#!/bin/bash

# Agent Naming Standardization Automation Script
# This script ensures all agents follow the [verb]-[qualifier] pattern
# and comply with agentskills.io specification

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AGENTS_DIR=".agents"
WORKSPACE_DIR="core/workspace/repo/.agents"

# Function to print colored output
print_status() {
    local status="$1"
    local message="$2"
    case $status in
        "INFO") echo -e "${BLUE}[INFO]${NC} $message" ;;
        "SUCCESS") echo -e "${GREEN}[SUCCESS]${NC} $message" ;;
        "WARNING") echo -e "${YELLOW}[WARNING]${NC} $message" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $message" ;;
        *) echo -e "[INFO] $message" ;;
    esac
}

# Function to check if a name follows verb-first pattern
is_verb_first() {
    local name="$1"
    [[ "$name" =~ ^[a-z]+-[a-z-]+$ ]]
}

# Function to convert noun-first to verb-first naming
convert_to_verb_first() {
    local old_name="$1"
    
    # Common conversions
    case "$old_name" in
        "kubectl-assistant") echo "assist-kubectl" ;;
        "log-classifier") echo "classify-logs" ;;
        "log-analyzer") echo "analyze-logs" ;;
        "feature-flag-manager") echo "manage-feature-flags" ;;
        "resource-optimizer") echo "optimize-resources" ;;
        "cost-optimizer") echo "optimize-costs" ;;
        "performance-optimizer") echo "optimize-performance" ;;
        "platform-chat") echo "manage-platform-chat" ;;
        "release-manager") echo "manage-releases" ;;
        "remediation-bot") echo "remediate-issues" ;;
        "resource-balancer") echo "balance-resources" ;;
        "alert-prioritizer") echo "prioritize-alerts" ;;
        "alert-router") echo "route-alerts" ;;
        "cicd-pipeline-monitor") echo "monitor-ci-cd-pipelines" ;;
        "sla-monitoring-alerting") echo "monitor-sla-alerting" ;;
        "slo-monitor") echo "monitor-slo" ;;
        "stakeholder-comms-drafter") echo "draft-stakeholder-comms" ;;
        "troubleshooting-playbook") echo "execute-troubleshooting-playbook" ;;
        "workflow-management") echo "manage-workflows" ;;
        "workload-migration") echo "migrate-workload" ;;
        "ci-cd-integrator") echo "integrate-ci-cd" ;;
        "capacity-planning") echo "plan-capacity" ;;
        "chaos-load-testing") echo "test-load-chaos" ;;
        "deployment-strategy") echo "deploy-strategy" ;;
        "deployment-validation") echo "validate-deployment" ;;
        "disaster-recovery") echo "recover-from-disaster" ;;
        "distributed-debug") echo "debug-distributed-systems" ;;
        "doc-generator") echo "generate-docs" ;;
        "gitops-pr") echo "manage-gitops-prs" ;;
        "gitops-workflow") echo "manage-gitops-workflows" ;;
        "incident-history") echo "track-incidents" ;;
        "incident-predictor") echo "predict-incidents" ;;
        "incident-summary") echo "summarize-incidents" ;;
        "infrastructure-discovery") echo "discover-infrastructure" ;;
        "infrastructure-manager") echo "manage-infrastructure" ;;
        "infrastructure-provisioning") echo "provision-infrastructure" ;;
        "kpi-report-generator") echo "generate-kpi-reports" ;;
        "load-balancer-tuner") echo "tune-load-balancer" ;;
        "manifest-generator") echo "generate-manifests" ;;
        "multi-cloud-networking") echo "network-multi-cloud" ;;
        "node-maintenance") echo "maintain-nodes" ;;
        "node-scale-assistant") echo "scale-nodes" ;;
        "observability-aggregator") echo "aggregate-observability" ;;
        "observability-stack") echo "deploy-observability-stack" ;;
        "onboarding-assistant") echo "assist-onboarding" ;;
        "orchestrator") echo "orchestrate-workflows" ;;
        "policy-as-code") echo "implement-policy-as-code" ;;
        "policy-explainer") echo "explain-policies" ;;
        "database-maintenance") echo "maintain-databases" ;;
        "database-operations") echo "operate-databases" ;;
        "backup-orchestrator") echo "orchestrate-backups" ;;
        "autoscaler-advisor") echo "scale-resources" ;;
        "cluster-health-check") echo "check-cluster-health" ;;
        "container-registry") echo "manage-container-registry" ;;
        "kubernetes-cluster-manager") echo "manage-kubernetes-cluster" ;;
        "secrets-certificate-manager") echo "manage-certificates" ;;
        "secret-rotation") echo "rotate-secrets" ;;
        "runbook-documentation-gen") echo "generate-runbook-docs" ;;
        "runbook-planner") echo "plan-runbooks" ;;
        "tenant-lifecycle-manager") echo "manage-tenant-lifecycle" ;;
        "change-management") echo "manage-changes" ;;
        "audit-siem") echo "audit-security-events" ;;
        "rollback-assistant") echo "assist-rollback" ;;
        "incident-triage-runbook") echo "incident-triage-runbook" ;;
        "diagnose-network") echo "diagnose-network" ;;
        "manage-service-mesh") echo "manage-service-mesh" ;;
        "resource-optimizer") echo "optimize-resources" ;;
        "audit-trail") echo "track-audit-events" ;;
        "generate-compliance-report") echo "generate-compliance-report" ;;
        "generate-security-report") echo "generate-security-report" ;;
        *) echo "$old_name" ;; # Return as-is if no conversion needed
    esac
}

# Function to update SKILL.md name field
update_skill_md_name() {
    local skill_dir="$1"
    local old_name="$2"
    local new_name="$3"
    local skill_file="$skill_dir/SKILL.md"
    
    if [ -f "$skill_file" ]; then
        print_status "INFO" "Updating name in $skill_file: $old_name → $new_name"
        sed -i '' "s/^name: $old_name$/name: $new_name/" "$skill_file"
        
        # Also update the title if it exists (line 15 typically)
        sed -i '' "15s/# $old_name/# $new_name/" "$skill_file" 2>/dev/null || true
    else
        print_status "WARNING" "SKILL.md not found: $skill_file"
    fi
}

# Function to validate a single agent directory
validate_agent() {
    local agent_dir="$1"
    local agent_name=$(basename "$agent_dir")
    
    print_status "INFO" "Validating agent: $agent_name"
    
    # Check if it follows verb-first pattern
    if is_verb_first "$agent_name"; then
        print_status "SUCCESS" "✓ $agent_name follows verb-first pattern"
        return 0
    else
        local new_name=$(convert_to_verb_first "$agent_name")
        if [ "$new_name" != "$agent_name" ]; then
            print_status "WARNING" "✗ $agent_name needs renaming → $new_name"
            return 1
        else
            print_status "INFO" "? $agent_name - unknown pattern"
            return 2
        fi
    fi
}

# Function to validate all agents in a directory
validate_all_agents() {
    local base_dir="$1"
    local issues=0
    local total=0
    
    print_status "INFO" "Validating agents in: $base_dir"
    
    for agent_dir in "$base_dir"/*; do
        if [ -d "$agent_dir" ] && [ "$(basename "$agent_dir")" != "SKILL.md" ] && [ "$(basename "$agent_dir")" != "scripts" ]; then
            ((total++))
            if ! validate_agent "$agent_dir"; then
                ((issues++))
            fi
        fi
    done
    
    print_status "INFO" "Validation complete: $total agents checked, $issues issues found"
    return $issues
}

# Function to fix all naming issues
fix_all_naming_issues() {
    local base_dir="$1"
    local fixes=0
    
    print_status "INFO" "Fixing naming issues in: $base_dir"
    
    for agent_dir in "$base_dir"/*; do
        if [ -d "$agent_dir" ] && [ "$(basename "$agent_dir")" != "SKILL.md" ] && [ "$(basename "$agent_dir")" != "scripts" ]; then
            local agent_name=$(basename "$agent_dir")
            
            if ! is_verb_first "$agent_name"; then
                local new_name=$(convert_to_verb_first "$agent_name")
                if [ "$new_name" != "$agent_name" ]; then
                    # Rename directory
                    mv "$agent_dir" "$(dirname "$agent_dir")/$new_name"
                    print_status "SUCCESS" "Renamed: $agent_name → $new_name"
                    
                    # Update SKILL.md
                    update_skill_md_name "$(dirname "$agent_dir")/$new_name" "$agent_name" "$new_name"
                    ((fixes++))
                fi
            fi
        fi
    done
    
    print_status "INFO" "Fixed $fixes naming issues"
    return $fixes
}

# Function to check SKILL.md compliance
check_skill_md_compliance() {
    local base_dir="$1"
    local compliance_issues=0
    
    print_status "INFO" "Checking SKILL.md compliance in: $base_dir"
    
    for skill_file in "$base_dir"/*/SKILL.md; do
        if [ -f "$skill_file" ]; then
            local dir_name=$(basename "$(dirname "$skill_file")")
            local name_in_file=$(grep "^name:" "$skill_file" | sed 's/name: //' | sed 's/^ *//')
            
            if [ "$name_in_file" != "$dir_name" ]; then
                print_status "WARNING" "Name mismatch in $skill_file: file says '$name_in_file', directory is '$dir_name'"
                update_skill_md_name "$(dirname "$skill_file")" "$name_in_file" "$dir_name"
                ((compliance_issues++))
            fi
        fi
    done
    
    print_status "INFO" "Fixed $compliance_issues SKILL.md compliance issues"
    return $compliance_issues
}

# Main execution logic
case "${1:-validate}" in
    "validate")
        shift
        if [ $# -eq 0 ]; then
            validate_all_agents "$AGENTS_DIR"
            validate_all_agents "$WORKSPACE_DIR"
        else
            for dir in "$@"; do
                validate_all_agents "$dir"
            done
        ;;
    "fix")
        shift
        if [ $# -eq 0 ]; then
            fix_all_naming_issues "$AGENTS_DIR"
            fix_all_naming_issues "$WORKSPACE_DIR"
        else
            for dir in "$@"; do
                fix_all_naming_issues "$dir"
            done
        ;;
    "compliance")
        shift
        if [ $# -eq 0 ]; then
            check_skill_md_compliance "$AGENTS_DIR"
            check_skill_md_compliance "$WORKSPACE_DIR"
        else
            for dir in "$@"; do
                check_skill_md_compliance "$dir"
            done
        ;;
    "help"|"-h"|"--help")
        echo "Agent Naming Standardization Tool"
        echo ""
        echo "Usage: $0 [COMMAND] [OPTIONS]"
        echo ""
        echo "Commands:"
        echo "  validate [dirs...]    Validate agent naming in specified directories"
        echo "  fix [dirs...]         Fix naming issues in specified directories"
        echo "  compliance [dirs...]   Check SKILL.md compliance in specified directories"
        echo ""
        echo "Defaults:"
        echo "  If no directories specified, validates both .agents and core/workspace/repo/.agents"
        echo ""
        echo "Examples:"
        echo "  $0 validate                    # Validate all directories"
        echo "  $0 fix .agents                 # Fix naming in main .agents directory"
        echo "  $0 compliance core/workspace/repo/.agents  # Check compliance in workspace"
        ;;
    *)
        print_status "ERROR" "Unknown command: $1"
        echo "Use '$0 --help' for usage information"
        exit 1
        ;;
esac

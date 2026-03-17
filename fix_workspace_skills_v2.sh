#!/bin/bash

# Script to fix SKILL.md files to match directory names
cd /Users/lloyd/github/antigravity/gitops-infra-control-plane/workspace/repo/.agents

# Function to update SKILL.md files
update_skill_md() {
    local old_name="$1"
    local new_name="$2"
    
    if [ -f "$new_name/SKILL.md" ]; then
        echo "Updating SKILL.md in $new_name"
        sed -i '' "s/^name: $old_name$/name: $new_name/" "$new_name/SKILL.md"
    fi
}

# Update specific SKILL.md files that need fixing
update_skill_md "database-maintenance" "maintain-databases"
update_skill_md "feature-flag-manager" "manage-feature-flags"
update_skill_md "resource-optimizer" "optimize-resources"
update_skill_md "onboarding-assistant" "assist-onboarding"
update_skill_md "multi-cloud-networking" "network-multi-cloud"
update_skill_md "policy-as-code" "implement-policy-as-code"
update_skill_md "observability-stack" "deploy-observability-stack"
update_skill_md "database-operations" "operate-databases"
update_skill_md "cost-optimizer" "optimize-costs"
update_skill_md "performance-optimizer" "optimize-performance"
update_skill_md "platform-chat" "manage-platform-chat"
update_skill_md "release-manager" "manage-releases"
update_skill_md "remediation-bot" "remediate-issues"
update_skill_md "resource-balancer" "balance-resources"
update_skill_md "sla-monitoring-alerting" "monitor-sla-alerting"
update_skill_md "slo-monitor" "monitor-slo"
update_skill_md "stakeholder-comms-drafter" "draft-stakeholder-comms"
update_skill_md "troubleshooting-playbook" "execute-troubleshooting-playbook"
update_skill_md "workflow-management" "manage-workflows"
update_skill_md "workload-migration" "migrate-workload"
update_skill_md "ci-cd-integrator" "integrate-ci-cd"
update_skill_md "capacity-planning" "plan-capacity"
update_skill_md "chaos-load-testing" "test-load-chaos"
update_skill_md "deployment-strategy" "deploy-strategy"
update_skill_md "deployment-validation" "validate-deployment"
update_skill_md "disaster-recovery" "recover-from-disaster"
update_skill_md "distributed-debug" "debug-distributed-systems"
update_skill_md "doc-generator" "generate-docs"
update_skill_md "gitops-pr" "manage-gitops-prs"
update_skill_md "gitops-workflow" "manage-gitops-workflows"
update_skill_md "incident-history" "track-incidents"
update_skill_md "incident-predictor" "predict-incidents"
update_skill_md "incident-summary" "summarize-incidents"
update_skill_md "infrastructure-discovery" "discover-infrastructure"
update_skill_md "infrastructure-manager" "manage-infrastructure"
update_skill_md "infrastructure-provisioning" "provision-infrastructure"
update_skill_md "kpi-report-generator" "generate-kpi-reports"
update_skill_md "load-balancer-tuner" "tune-load-balancer"
update_skill_md "log-analyzer" "analyze-logs"
update_skill_md "manifest-generator" "generate-manifests"
update_skill_md "node-maintenance" "maintain-nodes"
update_skill_md "node-scale-assistant" "scale-nodes"
update_skill_md "observability-aggregator" "aggregate-observability"
update_skill_md "runbook-documentation-gen" "generate-runbook-docs"
update_skill_md "runbook-planner" "plan-runbooks"
update_skill_md "backup-orchestrator" "orchestrate-backups"
update_skill_md "autoscaler-advisor" "scale-resources"
update_skill_md "cluster-health-check" "check-cluster-health"
update_skill_md "container-registry" "manage-container-registry"
update_skill_md "kubernetes-cluster-manager" "manage-kubernetes-cluster"
update_skill_md "policy-explainer" "explain-policies"
update_skill_md "secrets-certificate-manager" "manage-certificates"

echo "SKILL.md fixing complete!"

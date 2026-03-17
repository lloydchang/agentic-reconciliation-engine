#!/bin/bash

# Script to fix SKILL.md files to match directory names
cd /Users/lloyd/github/antigravity/gitops-infra-core/operators/core/workspace/repo/.agents

# Mapping of old names to new names
declare -A name_mapping=(
    ["kubectl-assistant"]="assist-kubectl"
    ["log-classifier"]="classify-logs" 
    ["rotate-secrets"]="rotate-secrets"
    ["tenant-lifecycle-manager"]="manage-tenant-lifecycle"
    ["generate-security-report"]="generate-security-report"
    ["change-management"]="manage-changes"
    ["audit-siem"]="audit-security-events"
    ["rollback-assistant"]="assist-rollback"
    ["incident-triage-runbook"]="incident-triage-runbook"
    ["diagnose-network"]="diagnose-network"
    ["manage-service-mesh"]="manage-service-mesh"
    ["resource-optimizer"]="optimize-resources"
    ["onboarding-assistant"]="assist-onboarding"
    ["multi-cloud-networking"]="network-multi-cloud"
    ["policy-as-code"]="implement-policy-as-code"
    ["observability-stack"]="deploy-observability-stack"
    ["database-operations"]="operate-databases"
    ["cost-optimizer"]="optimize-costs"
    ["performance-optimizer"]="optimize-performance"
    ["platform-chat"]="manage-platform-chat"
    ["release-manager"]="manage-releases"
    ["remediation-bot"]="remediate-issues"
    ["resource-balancer"]="balance-resources"
    ["sla-monitoring-alerting"]="monitor-sla-alerting"
    ["slo-monitor"]="monitor-slo"
    ["stakeholder-comms-drafter"]="draft-stakeholder-comms"
    ["troubleshooting-playbook"]="execute-troubleshooting-playbook"
    ["workflow-management"]="manage-workflows"
    ["workload-migration"]="migrate-workload"
    ["ci-cd-integrator"]="integrate-ci-cd"
    ["capacity-planning"]="plan-capacity"
    ["chaos-load-testing"]="test-load-chaos"
    ["deployment-strategy"]="deploy-strategy"
    ["deployment-validation"]="validate-deployment"
    ["disaster-recovery"]="recover-from-disaster"
    ["distributed-debug"]="debug-distributed-systems"
    ["doc-generator"]="generate-docs"
    ["gitops-pr"]="manage-gitops-prs"
    ["gitops-workflow"]="manage-gitops-workflows"
    ["incident-history"]="track-incidents"
    ["incident-predictor"]="predict-incidents"
    ["incident-summary"]="summarize-incidents"
    ["infrastructure-discovery"]="discover-infrastructure"
    ["infrastructure-manager"]="manage-infrastructure"
    ["infrastructure-provisioning"]="provision-infrastructure"
    ["kpi-report-generator"]="generate-kpi-reports"
    ["load-balancer-tuner"]="tune-load-balancer"
    ["log-analyzer"]="analyze-logs"
    ["manifest-generator"]="generate-manifests"
    ["node-maintenance"]="maintain-nodes"
    ["node-scale-assistant"]="scale-nodes"
    ["observability-aggregator"]="aggregate-observability"
    ["runbook-documentation-gen"]="generate-runbook-docs"
    ["runbook-planner"]="plan-runbooks"
    ["backup-orchestrator"]="orchestrate-backups"
    ["autoscaler-advisor"]="scale-resources"
    ["cluster-health-check"]="check-cluster-health"
    ["container-registry"]="manage-container-registry"
    ["kubernetes-cluster-manager"]="manage-kubernetes-cluster"
    ["policy-explainer"]="explain-policies"
    ["secrets-certificate-manager"]="manage-certificates"
    ["secret-rotation"]="rotate-secrets"
    ["alert-router"]="route-alerts"
    ["alert-prioritizer"]="prioritize-alerts"
    ["cicd-pipeline-monitor"]="monitor-ci-cd-pipelines"
)

# Process each directory
for old_name in "${!name_mapping[@]}"; do
    new_name="${name_mapping[$old_name]}"
    
    if [ -d "$old_name" ] && [ -d "$new_name" ]; then
        echo "Renaming directory: $old_name -> $new_name"
        mv "$old_name" "$new_name" 2>/dev/null
        
        # Update SKILL.md if it exists
        if [ -f "$new_name/SKILL.md" ]; then
            echo "Updating SKILL.md in $new_name"
            sed -i '' "s/^name: $old_name$/name: $new_name/" "$new_name/SKILL.md"
        fi
    fi
done

echo "SKILL.md fixing complete!"

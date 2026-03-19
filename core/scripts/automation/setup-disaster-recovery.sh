#!/bin/bash

source ../../../../scripts/set-topdir.sh

# Disaster Recovery Setup Script
# Configures and validates disaster recovery procedures for Git outages

set -euo pipefail

echo "🚨 Setting up Git Outage Disaster Recovery Procedures"

# Create namespace if it doesn't exist
kubectl create namespace flux-system --dry-run=client -o yaml | kubectl apply -f -

# Create disaster recovery ConfigMap with procedures
echo "📋 Installing disaster recovery procedures..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: disaster-recovery-procedures
  namespace: flux-system
  labels:
    app.kubernetes.io/name: "gitops-disaster-recovery"
    app.kubernetes.io/component: "procedures"
data:
  emergency-contacts.yaml: |
    # Emergency Contacts for Git Outage Incidents
    
    contacts:
      primary:
        - name: "DevOps Lead"
          role: "Incident Commander"
          phone: "+1-555-DEVOPS1"
          email: "devops-lead@company.com"
          slack: "@devops-lead"
          
        - name: "Engineering Manager"
          role: "Management Liaison"
          phone: "+1-555-ENG-MGR"
          email: "eng-mgr@company.com"
          slack: "@eng-mgr"
          
      secondary:
        - name: "Senior DevOps Engineer"
          role: "Technical Lead"
          phone: "+1-555-SENIOR-DEV"
          email: "senior-devops@company.com"
          slack: "@senior-devops"
          
      external:
        - name: "GitHub Support"
          service: "GitHub Enterprise Support"
          contact: "support@github.com"
          priority: "P1 - Critical Infrastructure"
          
        - name: "GitLab Support"
          service: "GitLab Premium Support"
          contact: "support@gitlab.com"
          priority: "P1 - Critical Infrastructure"
          
        - name: "Cloud Provider"
          service: "Cloud Infrastructure Support"
          contact: "cloud-support@company.com"
          priority: "P1 - Infrastructure"
          
    escalation:
      level_1:
        trigger: "Git repository unavailable > 5 minutes"
        notify: ["primary"]
        response_time: "15 minutes"
        
      level_2:
        trigger: "Git repository unavailable > 30 minutes"
        notify: ["primary", "secondary"]
        response_time: "5 minutes"
        
      level_3:
        trigger: "All Git repositories unavailable > 15 minutes"
        notify: ["primary", "secondary", "external"]
        response_time: "Immediate"
        
  communication-templates.yaml: |
    # Communication Templates for Git Outage Incidents
    
    templates:
      initial_alert:
        title: "🚨 Git Repository Outage Detected"
        severity: "critical"
        channels: ["slack", "email", "pagerduty"]
        message: |
          Git repository outage detected in GitOps Infra Control Plane.
          
          Status: {{.Status}}
          Affected Repositories: {{.AffectedRepos}}
          Time Detected: {{.Timestamp}}
          Impact: Infrastructure reconciliation may be delayed
          
          Actions in progress:
          - Verifying repository connectivity
          - Checking failover options
          - Preparing offline mode if needed
          
          Next update in 15 minutes or when status changes.
          
      failover_notification:
        title: "🔄 Git Repository Failover Activated"
        severity: "warning"
        channels: ["slack", "email"]
        message: |
          Git repository failover has been activated.
          
          From: {{.FromRepository}}
          To: {{.ToRepository}}
          Reason: {{.Reason}}
          Time: {{.Timestamp}}
          
          Impact: Normal operations continue with backup repository
          Performance: Slightly increased reconciliation times expected
          
      recovery_notification:
        title: "✅ Git Repository Recovery Completed"
        severity: "info"
        channels: ["slack", "email"]
        message: |
          Git repository outage has been resolved.
          
          Affected Period: {{.OutageStart}} to {{.OutageEnd}}
          Duration: {{.Duration}}
          Root Cause: {{.RootCause}}
          
          Actions Taken:
          {{range .ActionsTaken}}
          - {{.}}
          {{end}}
          
          All systems have returned to normal operation.
          
      offline_mode_notification:
        title: "📱 GitOps Offline Mode Activated"
        severity: "warning"
        channels: ["slack", "email", "pagerduty"]
        message: |
          GitOps Infra Control Plane has entered offline mode.
          
          Reason: All Git repositories unavailable
          Time: {{.Timestamp}}
          Expected Duration: Unknown
          
          Current Status:
          - Infrastructure continues operating from cached state
          - New changes will be queued
          - Monitoring and alerting remain active
          
          Impact: No immediate impact on running infrastructure
          Limitation: No new infrastructure changes until repositories recover
          
  runbook-commands.yaml: |
    # Emergency Runbook Commands for Git Outages
    
    commands:
      assessment:
        - name: "Check repository health"
          command: "kubectl get gitrepositories -n flux-system -L gitrepo.fluxcd.io/healthy"
          description: "Check health status of all Git repositories"
          
        - name: "Check current failover status"
          command: "kubectl get kustomizations -n flux-system -L fluxcd.io/offline-mode"
          description: "Check if offline mode or failover is active"
          
        - name: "Check Git cache health"
          command: "kubectl get service git-cache-service -n flux-system -L cache.fluxcd.io/healthy"
          description: "Check if local Git cache is healthy"
          
        - name: "View recent events"
          command: "kubectl get events -n flux-system --field-selector type=Warning --sort-by=.lastTimestamp"
          description: "Check for recent warning events"
          
      immediate_actions:
        - name: "Enable offline mode"
          command: "kubectl annotate kustomization infrastructure fluxcd.io/offline-mode=true --overwrite -n flux-system"
          description: "Force enable offline mode for all repositories"
          
        - name: "Switch to secondary repository"
          command: "kubectl patch kustomization infrastructure -n flux-system -p '{\"spec\":{\"sourceRef\":{\"name\":\"$TOPDIR-secondary\"}}}' --type=merge"
          description: "Manually failover to secondary Git repository"
          
        - name: "Switch to tertiary repository"
          command: "kubectl patch kustomization infrastructure -n flux-system -p '{\"spec\":{\"sourceRef\":{\"name\":\"$TOPDIR-tertiary\"}}}' --type=merge"
          description: "Manually failover to tertiary Git repository"
          
        - name: "Use cached repository"
          command: "kubectl patch gitrepository $TOPDIR-primary -n flux-system -p '{\"spec\":{\"url\":\"http://git-cache-service.flux-system.svc.cluster.local:8080/agentic-reconciliation-engine\"}}' --type=merge"
          description: "Switch to locally cached Git repository"
          
      recovery_actions:
        - name: "Restore primary repository"
          command: "kubectl patch gitrepository $TOPDIR-primary -n flux-system -p '{\"spec\":{\"url\":\"https://github.com/lloydchang/agentic-reconciliation-engine.git\"}}' --type=merge"
          description: "Restore primary Git repository URL"
          
        - name: "Disable offline mode"
          command: "kubectl annotate kustomization infrastructure fluxcd.io/offline-mode- --overwrite -n flux-system"
          description: "Disable offline mode and return to normal operations"
          
        - name: "Switch back to primary"
          command: "kubectl patch kustomization infrastructure -n flux-system -p '{\"spec\":{\"sourceRef\":{\"name\":\"$TOPDIR-primary\"}}}' --type=merge"
          description: "Switch back to primary Git repository"
          
        - name: "Restore from backup"
          command: "kubectl create job --from=cronjob/state-recovery-controller manual-recovery -n flux-system"
          description: "Trigger manual state recovery from latest backup"
          
      validation:
        - name: "Check Flux reconciliation"
          command: "kubectl get kustomizations -n flux-system"
          description: "Verify Flux is reconciling properly"
          
        - name: "Check resource status"
          command: "kubectl get all --all-namespaces"
          description: "Verify all resources are running properly"
          
        - name: "Test repository connectivity"
          command: "git ls-remote https://github.com/lloydchang/agentic-reconciliation-engine.git"
          description: "Test connectivity to primary repository"
          
        - name: "View health dashboard"
          command: "kubectl port-forward -n flux-system service/git-health-dashboard 8080:8080"
          description: "Access health dashboard for detailed status"
          
  testing-procedures.yaml: |
    # Testing Procedures for Disaster Recovery
    
    test_scenarios:
      monthly_drills:
        - name: "Primary Repository Outage"
          frequency: "Monthly"
          duration: "30 minutes"
          scenario: "Simulate primary repository failure"
          success_criteria:
            - "Automatic failover to secondary repository"
            - "No interruption to infrastructure operations"
            - "Recovery time < 5 minutes"
            
        - name: "Git Cache Failure"
          frequency: "Monthly"
          duration: "15 minutes"
          scenario: "Simulate Git cache service failure"
          success_criteria:
            - "Cache service restarts successfully"
            - "No impact on Git operations"
            - "Recovery time < 3 minutes"
            
      quarterly_tests:
        - name: "Complete Git Outage"
          frequency: "Quarterly"
          duration: "2 hours"
          scenario: "Simulate all Git repositories unavailable"
          success_criteria:
            - "Offline mode activates automatically"
            - "Infrastructure continues operating"
            - "State recovery works correctly"
            - "Recovery time < 30 minutes"
            
        - name: "Extended Outage"
          frequency: "Quarterly"
          duration: "4 hours"
          scenario: "Simulate extended Git provider outage"
          success_criteria:
            - "System operates in offline mode for extended period"
            - "Change queuing works properly"
            - "Recovery synchronization successful"
            
      annual_exercises:
        - name: "Full Disaster Recovery"
          frequency: "Annually"
          duration: "8 hours"
          scenario: "Complete system failure and recovery"
          success_criteria:
            - "All recovery procedures tested"
            - "Team coordination effective"
            - "Communication procedures work"
            - "Documentation up to date"
            
    test_execution:
      preparation:
        - "Schedule test window"
        - "Notify stakeholders"
        - "Prepare test data"
        - "Backup current state"
        
      execution:
        - "Execute test scenario"
        - "Monitor system response"
        - "Document observations"
        - "Record timing metrics"
        
      post_test:
        - "Restore normal operations"
        - "Analyze test results"
        - "Update procedures"
        - "Schedule improvements"
EOF

# Create emergency response ServiceAccount and permissions
echo "🔐 Setting up emergency response permissions..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: emergency-responder
  namespace: flux-system
  labels:
    app.kubernetes.io/name: "gitops-emergency-response"
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: emergency-responder-role
  labels:
    app.kubernetes.io/name: "gitops-emergency-response"
rules:
- apiGroups: ["source.toolkit.fluxcd.io"]
  resources: ["gitrepositories"]
  verbs: ["get", "list", "watch", "patch", "update"]
- apiGroups: ["kustomize.toolkit.fluxcd.io"]
  resources: ["kustomizations"]
  verbs: ["get", "list", "watch", "patch", "update", "annotate"]
- apiGroups: [""]
  resources: ["configmaps", "secrets", "services", "events"]
  verbs: ["get", "list", "watch", "create", "patch", "update"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["get", "list", "watch", "create", "patch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch", "patch", "scale"]
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: emergency-responder-binding
  labels:
    app.kubernetes.io/name: "gitops-emergency-response"
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: emergency-responder-role
subjects:
- kind: ServiceAccount
  name: emergency-responder
  namespace: flux-system
EOF

# Make disaster recovery drill script executable
echo "🔧 Setting up disaster recovery drill script..."
chmod +x core/automation/scripts/disaster-recovery-drill.sh

# Create initial drill schedule
echo "📅 Creating drill schedule..."
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: monthly-drill-primary-outage
  namespace: flux-system
  labels:
    app.kubernetes.io/name: "gitops-drill"
    app.kubernetes.io/component: "monthly-drill"
spec:
  schedule: "0 2 1 * *"  # First day of month at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: emergency-responder
          containers:
          - name: drill-runner
            image: bitnami/kubectl:latest
            command:
            - /bin/bash
            - -c
            - |
              /core/automation/scripts/disaster-recovery-drill.sh primary-outage
            volumeMounts:
            - name: drill-scripts
              mountPath: /scripts
              readOnly: true
          volumes:
          - name: drill-scripts
            configMap:
              name: disaster-recovery-procedures
              defaultMode: 0755
          restartPolicy: OnFailure
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: quarterly-drill-complete-outage
  namespace: flux-system
  labels:
    app.kubernetes.io/name: "gitops-drill"
    app.kubernetes.io/component: "quarterly-drill"
spec:
  schedule: "0 3 1 1,4,7,10 *"  # First day of quarter at 3 AM
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: emergency-responder
          containers:
          - name: drill-runner
            image: bitnami/kubectl:latest
            command:
            - /bin/bash
            - -c
            - |
              /core/automation/scripts/disaster-recovery-drill.sh complete-outage
            volumeMounts:
            - name: drill-scripts
              mountPath: /scripts
              readOnly: true
          volumes:
          - name: drill-scripts
              configMap:
                name: disaster-recovery-procedures
                defaultMode: 0755
          restartPolicy: OnFailure
EOF

# Validate setup
echo "🔍 Validating disaster recovery setup..."
kubectl get serviceaccount emergency-responder -n flux-system
kubectl get clusterrole emergency-responder-role
kubectl get configmap disaster-recovery-procedures -n flux-system
kubectl get cronjobs -n flux-system -l app.kubernetes.io/name=gitops-drill

echo "✅ Disaster recovery setup completed!"
echo ""
echo "📋 Emergency procedures: kubectl get configmap disaster-recovery-procedures -n flux-system -o yaml"
echo "🔧 Emergency responder: emergency-responder service account"
echo "📅 Drill schedules:"
echo "  - Monthly primary outage: kubectl get cronjob monthly-drill-primary-outage -n flux-system"
echo "  - Quarterly complete outage: kubectl get cronjob quarterly-drill-complete-outage -n flux-system"
echo ""
echo "🧪 Run manual drill:"
echo "  ./core/automation/scripts/disaster-recovery-drill.sh primary-outage"
echo "  ./core/automation/scripts/disaster-recovery-drill.sh complete-outage"
echo "  ./core/automation/scripts/disaster-recovery-drill.sh cache-failure"
echo ""
echo "📖 Full documentation: docs/GIT-OUTAGE-DISASTER-RECOVERY.md"

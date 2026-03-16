#!/bin/bash

# State Persistence Setup Script
# Configures infrastructure state persistence in Kubernetes etcd

set -euo pipefail
cd $(dirname $0)

echo "🗄️ Setting up Infrastructure State Persistence"

# Create namespace if it doesn't exist
kubectl create namespace flux-system --dry-run=client -o yaml | kubectl apply -f -

# Apply state persistence configuration
echo "📦 Deploying state persistence configuration..."
kubectl apply -f control-plane/flux/state-persistence.yaml

# Apply backup controller
echo "🔄 Deploying state backup controller..."
kubectl apply -f control-plane/flux/state-backup-controller

# Wait for backup controller to be ready
echo "⏳ Waiting for backup controller to be ready..."
kubectl wait --for=condition=ready job -l batch.kubernetes.io/job-name=state-backup-controller -n flux-system --timeout=300s || true

# Create initial backup
echo "📦 Creating initial infrastructure state backup..."
kubectl create job --from=cronjob/state-backup-controller initial-backup -n flux-system

# Wait for initial backup to complete
echo "⏳ Waiting for initial backup to complete..."
kubectl wait --for=condition=complete job/initial-backup -n flux-system --timeout=300s

# Verify backup was created
echo "🔍 Verifying backup was created..."
BACKUP_COUNT=$(kubectl get configmaps -n flux-system -l backup.fluxcd.io/type=infrastructure-state --no-headers | wc -l)
echo "✅ Found $BACKUP_COUNT backup ConfigMaps"

# Create recovery procedures documentation
echo "📝 Creating recovery procedures..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: recovery-procedures
  namespace: flux-system
data:
  manual-recovery.md: |
    # Manual Infrastructure State Recovery Procedures
    
    ## When to Use Manual Recovery
    
    - Automatic recovery fails during Git outages
    - Critical infrastructure resources are missing
    - Need to restore to a known good state
    
    ## Recovery Steps
    
    ### 1. List Available Backups
    
    \`\`\`bash
    kubectl get configmaps -n flux-system -l backup.fluxcd.io/type=infrastructure-state \
      -o custom-columns=TIMESTAMP:.metadata.labels.backup\.fluxcd\.io/timestamp,NAME:.metadata.name
    \`\`\`
    
    ### 2. Verify Current State
    
    \`\`\`bash
    # Check critical resources
    kubectl get vpcs.ec2.aws.crossplane.io --all-namespaces
    kubectl get eksclusters.eks.aws.crossplane.io --all-namespaces
    kubectl get virtualnetworks.network.azure.com --all-namespaces
    \`\`\`
    
    ### 3. Perform Recovery
    
    \`\`\`bash
    # Recovery from specific backup
    TIMESTAMP="20240312-143000"  # Replace with desired timestamp
    kubectl exec -n flux-system deployment/state-recovery-controller -- /scripts/recovery-script.sh "$TIMESTAMP"
    \`\`\`
    
    ### 4. Verify Recovery
    
    \`\`\`bash
    # Check that resources are restored
    kubectl get vpcs.ec2.aws.crossplane.io --all-namespaces
    kubectl get eksclusters.eks.aws.crossplane.io --all-namespaces
    \`\`\`
    
    ### 5. Monitor Flux Reconciliation
    
    \`\`\`bash
    # Check Flux status
    kubectl get kustomizations -n flux-system
    kubectl get gitrepositories -n flux-system
    \`\`\`
    
    ## Emergency Procedures
    
    ### Complete Git Outage Recovery
    
    1. Enable offline mode:
       \`\`\`bash
       kubectl annotate kustomization infrastructure fluxcd.io/offline-mode=true --overwrite -n flux-system
       \`\`\`
    
    2. Restore from latest backup:
       \`\`\`bash
       LATEST_BACKUP=$(kubectl get configmaps -n flux-system -l backup.fluxcd.io/type=infrastructure-state \
         --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.labels.backup\.fluxcd\.io/timestamp}')
       kubectl exec -n flux-system deployment/state-recovery-controller -- /scripts/recovery-script.sh "$LATEST_BACKUP"
       \`\`\`
    
    3. Verify operations:
       \`\`\`bash
       kubectl get all --all-namespaces
       kubectl get infrastructure-resources --all-namespaces
       \`\`\`
    
    ## Troubleshooting
    
    ### Backup Not Found
    - Check backup controller logs: \`kubectl logs -n flux-system -l app=state-backup\`
    - Verify permissions: \`kubectl auth can-i create configmaps -n flux-system\`
    
    ### Recovery Fails
    - Check for resource conflicts: \`kubectl get all --all-namespaces\`
    - Verify backup integrity: \`kubectl get configmap backup-manifest-<timestamp> -n flux-system -o yaml\`
    
    ### Resources Not Restoring
    - Check cloud provider credentials
    - Verify controller status: \`kubectl get pods -n ack-system\`
    - Check controller logs for errors
EOF

echo "✅ State persistence setup completed!"
echo ""
echo "📊 Backup controller: state-backup-controller (runs every 5 minutes)"
echo "🔄 Recovery controller: state-recovery-controller"
echo "📝 Recovery procedures: kubectl get configmap recovery-procedures -n flux-system -o yaml"
echo ""
echo "🔍 Monitor backups:"
echo "  kubectl get configmaps -n flux-system -l backup.fluxcd.io/type=infrastructure-state"
echo ""
echo "📖 Manual recovery:"
echo "  kubectl exec -n flux-system deployment/state-recovery-controller -- /scripts/recovery-script.sh <timestamp>"

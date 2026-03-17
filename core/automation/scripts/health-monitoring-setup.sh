#!/bin/bash

# Git Repository Health Monitoring Setup Script
# Configures comprehensive health monitoring and alerting

set -euo pipefail

echo "🔍 Setting up Git Repository Health Monitoring"

# Create namespace if it doesn't exist
kubectl create namespace flux-system --dry-run=client -o yaml | kubectl apply -f -

# Apply health monitoring configuration
echo "📦 Deploying health monitoring configuration..."
kubectl apply -f core/operators/flux/git-health-monitoring.yaml

# Apply health monitoring controller
echo "🔄 Deploying health monitoring controller..."
kubectl apply -f core/operators/flux/health-monitoring-controller.yaml

# Wait for dashboard to be ready
echo "⏳ Waiting for health dashboard to be ready..."
kubectl wait --for=condition=available deployment/git-health-dashboard -n flux-system --timeout=300s

# Test health monitoring
echo "🧪 Testing health monitoring..."
kubectl create job --from=cronjob/git-health-monitor test-health-monitor -n flux-system

# Wait for test to complete
echo "⏳ Waiting for health monitoring test to complete..."
kubectl wait --for=condition=complete job/test-health-monitor -n flux-system --timeout=120s

# Verify monitoring is working
echo "🔍 Verifying health monitoring is working..."
HEALTHY_REPOS=$(kubectl get gitrepositories -n flux-system -l gitrepo.fluxcd.io/healthy=true --no-headers | wc -l)
UNHEALTHY_REPOS=$(kubectl get gitrepositories -n flux-system -l gitrepo.fluxcd.io/healthy=false --no-headers | wc -l)

echo "✅ Healthy repositories: $HEALTHY_REPOS"
echo "⚠️ Unhealthy repositories: $UNHEALTHY_REPOS"

# Check health reports
echo "📊 Checking health reports..."
HEALTH_REPORTS=$(kubectl get configmaps -n flux-system -l health_percentage --no-headers | wc -l)
echo "📈 Health reports generated: $HEALTH_REPORTS"

# Create monitoring documentation
echo "📝 Creating monitoring documentation..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: monitoring-documentation
  namespace: flux-system
data:
  health-monitoring-guide.md: |
    # Git Repository Health Monitoring Guide
    
    ## Overview
    
    The GitOps Infra Control Plane includes comprehensive health monitoring for all Git repositories to ensure high availability and early detection of issues.
    
    ## Components
    
    ### 1. Health Monitor Controller
    - **Name**: \`git-health-monitor\`
    - **Schedule**: Every minute
    - **Function**: Performs health checks on all configured Git repositories
    
    ### 2. Health Dashboard
    - **Name**: \`git-health-dashboard\`
    - **Access**: \`http://git-health-dashboard.flux-system.svc.cluster.local:8080\`
    - **Function**: Web interface for monitoring repository health
    
    ### 3. Alert System
    - **Trigger**: After 3 consecutive health check failures
    - **Channels**: Kubernetes Events, Email, Slack (configurable)
    
    ## Health Check Metrics
    
    ### Repository Health
    - **Connectivity**: Can we reach the repository?
    - **Response Time**: How long does it take to respond?
    - **Availability**: Is the repository accessible?
    
    ### Git Cache Health
    - **Service Status**: Is the cache service running?
    - **Content Availability**: Can we access cached content?
    
    ### Flux Controller Health
    - **Pod Status**: Are all Flux controllers running?
    - **Reconciliation Status**: Are resources being reconciled?
    
    ## Alerting
    
    ### Alert Triggers
    - Repository failure count >= 3
    - Git cache unavailable
    - Flux controller not running
    
    ### Alert Severity Levels
    - **Critical**: All repositories failed
    - **Warning**: Some repositories failed
    - **Info**: Performance degradation
    
    ## Monitoring Commands
    
    ### Check Repository Health
    \`\`\`bash
    # List all repositories with health status
    kubectl get gitrepositories -n flux-system -L gitrepo.fluxcd.io/healthy
    
    # Get detailed health information
    kubectl get gitrepository gitops-infra-primary -n flux-system -o yaml
    
    # Check failure counts
    kubectl get gitrepositories -n flux-system -l gitrepo.fluxcd.io/failure-count
    \`\`\`
    
    ### View Health Reports
    \`\`\`bash
    # List health reports
    kubectl get configmaps -n flux-system -l health_percentage
    
    # View latest health report
    kubectl get configmap -n flux-system -l health_percentage --sort-by=.metadata.creationTimestamp -o yaml | tail -20
    \`\`\`
    
    ### Monitor Logs
    \`\`\`bash
    # Health monitor logs
    kubectl logs -n flux-system -l batch.kubernetes.io/job-name=git-health-monitor
    
    # Dashboard logs
    kubectl logs -n flux-system deployment/git-health-dashboard
    \`\`\`
    
    ### Manual Health Check
    \`\`\`bash
    # Run manual health check
    kubectl create job --from=cronjob/git-health-monitor manual-health-check -n flux-system
    
    # Check repository connectivity manually
    git ls-remote https://github.com/antigravity/gitops-infra-control-plane.git
    \`\`\`
    
    ## Dashboard Access
    
    ### Port Forward (for local access)
    \`\`\`bash
    kubectl port-forward -n flux-system service/git-health-dashboard 8080:8080
    # Then visit http://localhost:8080
    \`\`\`
    
    ### Ingress (for production)
    Configure ingress to expose the dashboard externally:
    \`\`\`yaml
    apiVersion: networking.k8s.io/v1
    kind: Ingress
    metadata:
      name: git-health-dashboard
      namespace: flux-system
    spec:
      rules:
      - host: git-health.company.com
        http:
          paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: git-health-dashboard
                port:
                  number: 8080
    \`\`\`
    
    ## Troubleshooting
    
    ### Repository Shows as Unhealthy
    1. Check network connectivity to repository
    2. Verify credentials are correct
    3. Check if repository actually exists
    4. Look at health monitor logs for specific errors
    
    ### Alerts Not Triggering
    1. Verify alert threshold configuration
    2. Check RBAC permissions for event creation
    3. Verify notification channel configuration
    
    ### Dashboard Not Loading
    1. Check dashboard pod status
    2. Verify service configuration
    3. Check network policies
    4. Review nginx configuration
    
    ## Performance Tuning
    
    ### Health Check Frequency
    - Default: Every minute
    - High-frequency: Every 30 seconds (for critical systems)
    - Low-frequency: Every 5 minutes (for resource-constrained environments)
    
    ### Alert Thresholds
    - Default: 3 consecutive failures
    - Sensitive: 2 consecutive failures
    - Lenient: 5 consecutive failures
    
    ### Resource Limits
    - Monitor CPU/memory usage of health monitoring components
    - Adjust limits based on repository count and check frequency
EOF

echo "✅ Health monitoring setup completed!"
echo ""
echo "📊 Health dashboard: http://git-health-dashboard.flux-system.svc.cluster.local:8080"
echo "🔄 Health monitor: git-health-monitor (runs every minute)"
echo "📚 Documentation: kubectl get configmap monitoring-documentation -n flux-system -o yaml"
echo ""
echo "🔍 Monitor repository health:"
echo "  kubectl get gitrepositories -n flux-system -L gitrepo.fluxcd.io/healthy"
echo ""
echo "📈 View health reports:"
echo "  kubectl get configmaps -n flux-system -l health_percentage"
echo ""
echo "🧪 Run manual health check:"
echo "  kubectl create job --from=cronjob/git-health-monitor manual-health-check -n flux-system"

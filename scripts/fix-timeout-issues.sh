#!/bin/bash

echo "🔧 Fixing agent deployment timeouts and ImagePullBackOff issues..."

# Function to execute commands with timeout and retry
execute_with_timeout() {
    local cmd="$1"
    local timeout_duration="${2:-30}"
    local description="${3:-command}"
    
    echo "⏱️ Executing: $description"
    timeout "$timeout_duration" bash -c "$cmd" 2>/dev/null
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "✅ Success: $description"
        return 0
    elif [ $exit_code -eq 124 ]; then
        echo "⏰ Timeout: $description after ${timeout_duration}s"
        return 1
    else
        echo "❌ Failed: $description (exit code: $exit_code)"
        return 1
    fi
}

# Optimize Docker resources to prevent timeouts
echo "🧹 Optimizing Docker resources..."
execute_with_timeout "docker system prune -f" 60 "docker system prune"

# Verify images are available in cluster
echo "🔍 Verifying images in Kind cluster..."
execute_with_timeout "docker exec gitops-hub-control-plane crictl images | grep -E '(cost-optimizer|security-scanner|swarm-coordinator)'" 30 "check cluster images"

# Clean up existing problematic resources
echo "🧹 Cleaning up existing resources..."
execute_with_timeout "kubectl delete pods -l agent-type=cost-optimizer -n ai-infrastructure --force --grace-period=0" 15 "delete cost-optimizer pods"
execute_with_timeout "kubectl delete pods -l agent-type=security-scanner -n ai-infrastructure --force --grace-period=0" 15 "delete security-scanner pods"
execute_with_timeout "kubectl delete pods -l component=agent-swarm-coordinator -n ai-infrastructure --force --grace-period=0" 15 "delete swarm-coordinator pods"

# Wait for cleanup
echo "⏳ Waiting for pod cleanup..."
sleep 10

# Apply corrected deployments
echo " Applying corrected deployments..."
execute_with_timeout "kubectl apply -f core/resources/infrastructure/agents/cost-optimizer-deployment.yaml" 30 "apply cost-optimizer deployment"
execute_with_timeout "kubectl apply -f core/resources/infrastructure/agents/security-scanner-deployment.yaml" 30 "apply security-scanner deployment"
execute_with_timeout "kubectl apply -f core/resources/infrastructure/agents/agent-swarm-coordinator-deployment.yaml" 30 "apply swarm-coordinator deployment"

# Monitor rollout status
echo " Monitoring deployment rollout..."
execute_with_timeout "kubectl rollout status deployment/cost-optimizer-agent -n ai-infrastructure --timeout=60s" 70 "cost-optimizer rollout"
execute_with_timeout "kubectl rollout status deployment/security-scanner-agent -n ai-infrastructure --timeout=60s" 70 "security-scanner rollout"
execute_with_timeout "kubectl rollout status deployment/agent-swarm-coordinator -n ai-infrastructure --timeout=60s" 70 "swarm-coordinator rollout"

# Wait for pods to become ready
echo " Waiting for pods to become ready..."
sleep 30

# Final status check
echo " Final pod status:"
execute_with_timeout "kubectl get pods -n ai-infrastructure | grep -E '(cost-optimizer|security-scanner|swarm-coordinator)'" 10 "final pod status"

# System health verification
echo " Verifying system health..."
execute_with_timeout "kubectl cluster-info" 20 "cluster connectivity check"
execute_with_timeout "docker system df" 15 "docker resource usage"

echo " Agent deployment fix completed!"

# Alternative manual commands (uncomment if needed)
: '
# Manual cleanup commands (if script fails):
kubectl delete pods -l agent-type=cost-optimizer -n ai-infrastructure --force --grace-period=0
kubectl delete pods -l agent-type=security-scanner -n ai-infrastructure --force --grace-period=0
kubectl delete pods -l component=agent-swarm-coordinator -n ai-infrastructure --force --grace-period=0

# Manual deployment commands:
kubectl apply -f core/resources/infrastructure/agents/cost-optimizer-deployment.yaml
kubectl apply -f core/resources/infrastructure/agents/security-scanner-deployment.yaml
kubectl apply -f core/resources/infrastructure/agents/agent-swarm-coordinator-deployment.yaml

# Manual rollout monitoring:
kubectl rollout status deployment/cost-optimizer-agent -n ai-infrastructure
kubectl rollout status deployment/security-scanner-agent -n ai-infrastructure
kubectl rollout status deployment/agent-swarm-coordinator -n ai-infrastructure
'

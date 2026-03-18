#!/bin/bash

echo "🔧 Fixing agent deployment connectivity issues..."

# Function to retry commands with timeout
retry_command() {
    local cmd="$1"
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "📝 Attempt $attempt: $cmd"
        if timeout 30 bash -c "$cmd"; then
            echo "✅ Success on attempt $attempt"
            return 0
        else
            echo "❌ Failed attempt $attempt"
            if [ $attempt -eq $max_attempts ]; then
                echo "🚨 All attempts failed for: $cmd"
                return 1
            fi
            sleep 5
        fi
        attempt=$((attempt + 1))
    done
}

# Build remaining images
echo "🏗️ Building swarm-coordinator image..."
retry_command "cd core/ai/agents/swarm-coordinator && docker build -t localhost:5000/agent-swarm-coordinator:latest ."

# Load images into Kind cluster
echo "📦 Loading images into Kind cluster..."
retry_command "kind load docker-image localhost:5000/cost-optimizer-agent:latest --name gitops-hub"
retry_command "kind load docker-image localhost:5000/agent-swarm-coordinator:latest --name gitops-hub"

# Apply updated deployments
echo "🚀 Applying updated deployments..."
retry_command "kubectl apply -f core/resources/infrastructure/agents/cost-optimizer-deployment.yaml"
retry_command "kubectl apply -f core/resources/infrastructure/agents/security-scanner-deployment.yaml"
retry_command "kubectl apply -f core/resources/infrastructure/agents/agent-swarm-coordinator-deployment.yaml"

# Check pod status
echo "🔍 Checking pod status..."
retry_command "kubectl get pods -n ai-infrastructure | grep -E '(cost-optimizer|security-scanner|swarm-coordinator)'"

echo "✅ Agent deployment fix completed!"

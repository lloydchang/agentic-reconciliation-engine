#!/bin/bash

echo "🚀 Deploying Comprehensive AI Agents Analytics Dashboard..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kubernetes cluster not accessible. Please check your kubeconfig."
    exit 1
fi

# Create namespace if it doesn't exist
echo "📦 Creating ai-infrastructure namespace..."
kubectl create namespace ai-infrastructure --dry-run=client -o yaml | kubectl apply -f -

# Deploy the comprehensive dashboard components
echo "🔧 Deploying comprehensive dashboard API..."
kubectl apply -f core/ai/runtime/dashboard/deployment/kubernetes/comprehensive-dashboard-api-configmap.yaml

echo "🔧 Deploying comprehensive dashboard frontend..."
kubectl apply -f core/ai/runtime/dashboard/deployment/kubernetes/comprehensive-dashboard-configmap.yaml

echo "🚀 Deploying comprehensive dashboard services..."
kubectl apply -f core/ai/runtime/dashboard/deployment/kubernetes/comprehensive-dashboard-deployment.yaml

# Wait for deployments to be ready
echo "⏳ Waiting for deployments to be ready..."
kubectl rollout status deployment/comprehensive-dashboard-api -n ai-infrastructure --timeout=120s
kubectl rollout status deployment/comprehensive-dashboard-frontend -n ai-infrastructure --timeout=120s

# Get service URLs
echo "📊 Getting service information..."
API_SERVICE=$(kubectl get svc comprehensive-dashboard-api -n ai-infrastructure -o jsonpath='{.spec.clusterIP}')
FRONTEND_SERVICE=$(kubectl get svc comprehensive-dashboard-frontend -n ai-infrastructure -o jsonpath='{.spec.clusterIP}')

echo ""
echo "✅ Comprehensive Dashboard Deployment Complete!"
echo ""
echo "🎯 Access Information:"
echo "  Frontend: http://localhost:8083 (auto-started)"
echo "  API: http://localhost:5001 (auto-started)"
echo ""
echo "🔧 Port Forward Commands (if needed manually):"
echo "  kubectl port-forward svc/comprehensive-dashboard-frontend 8083:80 -n ai-infrastructure &"
echo "  kubectl port-forward svc/comprehensive-dashboard-api 5001:5000 -n ai-infrastructure &"
echo ""
echo "📊 Dashboard Features:"
echo "  ✅ Real-time agent counting (pods + workflows + memory agents)"
echo "  ✅ Detailed skill descriptions from SKILL.md files"
echo "  ✅ Time-series metrics visualization"
echo "  ✅ Failure analysis with root cause and post-mortem"
echo "  ✅ Dynamic success rate calculation"
echo "  ✅ Comprehensive agent discovery across all execution methods"
echo ""
echo "🚀 Starting port-forwards for immediate access..."

# Start port-forwards in background
PORT_FORWARDS=(
    "svc/comprehensive-dashboard-frontend 8083:80"
    "svc/comprehensive-dashboard-api 5001:5000"
)

for port_config in "${PORT_FORWARDS[@]}"; do
    service_name=$(echo "$port_config" | cut -d' ' -f1)
    local_port=$(echo "$port_config" | cut -d' ' -f2 | cut -d':' -f1)
    log_file="/tmp/${service_name##*/}-port-forward.log"
    
    # Check if already running
    if pgrep -f "port-forward.*$service_name.*$local_port" > /dev/null; then
        echo "  ✅ Port-forward for $service_name (port $local_port) already running"
    else
        # Start port-forward
        nohup kubectl port-forward -n ai-infrastructure $port_config > "$log_file" 2>&1 &
        sleep 2
        
        # Verify it started
        if pgrep -f "port-forward.*$service_name.*$local_port" > /dev/null; then
            echo "  ✅ Started port-forward for $service_name: http://localhost:$local_port"
            echo "     Logs: tail -f $log_file"
        else
            echo "  ❌ Failed to start port-forward for $service_name"
        fi
    fi
done

echo ""
echo "🌐 Dashboard Access:"
echo "   Frontend: http://localhost:8083"
echo "   API: http://localhost:5001"

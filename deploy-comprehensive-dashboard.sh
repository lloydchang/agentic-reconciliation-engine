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
echo "  Frontend: http://localhost:8083 (after port-forward)"
echo "  API: http://localhost:5001 (after port-forward)"
echo ""
echo "🔧 Port Forward Commands:"
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
echo "🚀 Start the port forwards and access your new dashboard!"
echo "   Frontend: http://localhost:8083"
echo "   API: http://localhost:5001"

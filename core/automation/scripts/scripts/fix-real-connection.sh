#!/bin/bash

echo "🔧 FIXING REAL DATA CONNECTION"
echo "============================"

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "port-forward.*ai-metrics" 2>/dev/null || true
pkill -f "real-data-api" 2>/dev/null || true

sleep 2

# Set up kubeconfig
export KUBECONFIG=/Users/lloyd/github/antigravity/gitops-infra-core/operators/hub-kubeconfig
kubectl config use-context hub

echo "📡 Establishing port-forward to ai-metrics-service..."
kubectl port-forward svc/ai-metrics-service 8080:8080 -n ai-infrastructure &
PF_PID=$!

echo "   Port-forward PID: $PF_PID"
sleep 3

# Test connection
echo "🧪 Testing Go metrics server connection..."
if curl -s --connect-timeout 2 http://localhost:8080/health >/dev/null 2>&1; then
    echo "✅ Go metrics server accessible!"
    
    echo "🔄 Restarting real data API..."
    python3 real-data-api.py &
    API_PID=$!
    
    sleep 3
    
    # Test full data flow
    echo "🔗 Testing complete data flow..."
    if curl -s --connect-timeout 2 http://localhost:5002/api/core/ai/runtime/detailed >/dev/null 2>&1; then
        echo "✅ Real data flowing successfully!"
        echo ""
        echo "🎉 REAL DATA CONNECTION ESTABLISHED!"
        echo "   Port-forward PID: $PF_PID"
        echo "   API PID: $API_PID"
        echo "   Dashboard: http://localhost:3001/"
        echo "   Go Server: http://localhost:8080/health"
        echo ""
        echo "🚀 Your dashboard now shows REAL AI agents metrics!"
    else
        echo "❌ API connection issue"
    fi
else
    echo "❌ Failed to connect to Go metrics server"
    echo "   Checking service status..."
    
    # Check service details
    kubectl get svc ai-metrics-service -n ai-infrastructure -o yaml
    echo ""
    echo "Checking pod logs..."
    kubectl logs -n ai-infrastructure -l app=ai-metrics-server --tail=10
fi

#!/bin/bash

echo "🔗 Setting up real connection to Go metrics server..."

# Kill any existing port-forwards
pkill -f "kubectl port-forward.*ai-metrics" 2>/dev/null || true

# Set up port-forward
export KUBECONFIG=agentic-reconciliation-engine/core/operators/hub-kubeconfig
kubectl config use-context hub

echo "📡 Establishing port-forward to ai-metrics-service..."
kubectl port-forward svc/ai-metrics-service 8080:8080 -n ai-infrastructure &

# Wait for connection
sleep 3

# Test connection
if curl -s http://localhost:8080/health >/dev/null 2>&1; then
    echo "✅ Real connection established!"
    echo "   Go Metrics Server: http://localhost:8080"
    echo "   Available endpoints:"
    echo "     - /api/core/ai/runtime/detailed"
    echo "     - /api/workflows/status" 
    echo "     - /api/metrics/real-time"
    echo "     - /api/system/health"
    echo ""
    echo "🚀 Enhanced API will now use REAL DATA only!"
    echo "   Restart enhanced API: pkill -f enhanced-api && ./start-api.sh"
else
    echo "❌ Failed to connect to Go metrics server"
    echo "   Check if ai-metrics-server pod is running"
fi

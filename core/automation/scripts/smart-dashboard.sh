#!/bin/bash

# Smart Dashboard Launcher
# Tries NodePort first, falls back to port-forward if needed

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Smart Dashboard Launcher..."
echo ""

# Set KUBECONFIG to hub cluster
export KUBECONFIG="${SCRIPT_DIR}/../core/config/kubeconfigs/hub-kubeconfig"

# Switch to hub context
kubectl config use-context hub &> /dev/null || echo "Could not switch to hub context"

# Kill any existing port-forwards
pkill -f "kubectl port-forward.*agent-dashboard" 2>/dev/null || true
pkill -f "kubectl port-forward.*dashboard-api" 2>/dev/null || true

# Try NodePort approach first
echo "📡 Setting up NodePort services for automatic access..."

# Create NodePort service for dashboard
kubectl apply -f - <<EOF >/dev/null 2>&1
apiVersion: v1
kind: Service
metadata:
  name: dashboard-api-enhanced-service-nodeport
  namespace: ai-infrastructure
  labels:
    component: dashboard-api-enhanced
spec:
  type: NodePort
  ports:
  - port: 5000
    targetPort: 5000
    nodePort: 30001
  selector:
    component: dashboard-api-enhanced
EOF

# Wait a moment for services to be ready
sleep 3

# Test NodePort access
echo "🔍 Testing NodePort access..."
if curl -s --connect-timeout 2 http://localhost:30001/health >/dev/null 2>&1; then
    echo ""
    echo "✅ NodePort access working!"
    echo ""
    echo "🌐 Access URLs:"
    echo "   Dashboard: http://localhost:30001/"
    echo "   API: http://localhost:30001/api/config"
    echo ""
    echo "💡 No port-forwarding needed!"
else
    echo "⚠️  NodePort not accessible, falling back to port-forward..."
    
    # Clean up NodePort services
    kubectl delete svc dashboard-api-enhanced-service-nodeport -n ai-infrastructure >/dev/null 2>&1 || true
    
    echo "🔄 Starting port-forward in background..."
    
    # Start port-forward in background
    kubectl port-forward svc/dashboard-api-enhanced-service 3001:5000 -n ai-infrastructure &
    DASHBOARD_PID=$!
    
    echo ""
    echo "✅ Port-forward started!"
    echo ""
    echo "🌐 Access URLs:"
    echo "   Dashboard: http://localhost:3001/"
    echo "   API: http://localhost:3001/api/config"
    echo ""
    echo "🔧 Port-forward running (PID: $DASHBOARD_PID)"
    echo "   To stop: kill $DASHBOARD_PID"
    echo "   Or run: pkill -f 'kubectl port-forward.*dashboard-api-enhanced'"
fi

echo ""
echo "🎯 Dashboard should now be accessible!"

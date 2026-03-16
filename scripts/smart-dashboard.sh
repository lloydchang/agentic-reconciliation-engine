#!/bin/bash

# Smart Dashboard Launcher
# Tries NodePort first, falls back to port-forward if needed

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Smart Dashboard Launcher..."
echo ""

# Set KUBECONFIG to hub cluster
export KUBECONFIG="${SCRIPT_DIR}/../hub-kubeconfig"

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
  name: agent-dashboard-service-nodeport
  namespace: ai-infrastructure
  labels:
    component: agent-dashboard
spec:
  type: NodePort
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30888
  selector:
    component: agent-dashboard
EOF

# Create NodePort service for API
kubectl apply -f - <<EOF >/dev/null 2>&1
apiVersion: v1
kind: Service
metadata:
  name: dashboard-api-service-nodeport
  namespace: ai-infrastructure
  labels:
    component: dashboard-api
spec:
  type: NodePort
  ports:
  - port: 5000
    targetPort: 5000
    nodePort: 30500
  selector:
    component: dashboard-api
EOF

# Wait a moment for services to be ready
sleep 3

# Test NodePort access
echo "🔍 Testing NodePort access..."
if curl -s --connect-timeout 2 http://localhost:30888/ >/dev/null 2>&1; then
    echo ""
    echo "✅ NodePort access working!"
    echo ""
    echo "🌐 Access URLs:"
    echo "   Dashboard: http://localhost:30888/"
    echo "   API: http://localhost:30500/api/cluster-status"
    echo ""
    echo "💡 No port-forwarding needed!"
else
    echo "⚠️  NodePort not accessible, falling back to port-forward..."
    
    # Clean up NodePort services
    kubectl delete svc agent-dashboard-service-nodeport dashboard-api-service-nodeport -n ai-infrastructure >/dev/null 2>&1 || true
    
    echo "🔄 Starting port-forward in background..."
    
    # Start port-forwards in background
    kubectl port-forward svc/agent-dashboard-service 8888:80 -n ai-infrastructure &
    DASHBOARD_PID=$!
    
    kubectl port-forward svc/dashboard-api-service 5000:5000 -n ai-infrastructure &
    API_PID=$!
    
    echo ""
    echo "✅ Port-forward started!"
    echo ""
    echo "🌐 Access URLs:"
    echo "   Dashboard: http://localhost:8888/"
    echo "   API: http://localhost:5000/api/cluster-status"
    echo ""
    echo "🔧 Port-forwards running (PIDs: $DASHBOARD_PID, $API_PID)"
    echo "   To stop: kill $DASHBOARD_PID $API_PID"
    echo "   Or run: pkill -f 'kubectl port-forward.*agent-dashboard'"
fi

echo ""
echo "🎯 Dashboard should now be accessible!"

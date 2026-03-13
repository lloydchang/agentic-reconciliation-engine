#!/bin/bash

echo "Starting Agent Orchestration Dashboard..."
echo "This will start two port-forwards in the background."
echo ""

# Kill any existing port-forwards
pkill -f "kubectl port-forward.*agent-dashboard" 2>/dev/null || true
pkill -f "kubectl port-forward.*dashboard-api" 2>/dev/null || true

# Start port-forwards in background
kubectl port-forward svc/agent-dashboard 8888:8080 -n monitoring &
DASHBOARD_PID=$!

kubectl port-forward svc/dashboard-api 5000:5000 -n monitoring &
API_PID=$!

echo "✅ Dashboard: http://localhost:8888/"
echo "✅ API: http://localhost:5000/api/cluster-status"
echo ""
echo "Port-forwards are running in background (PIDs: $DASHBOARD_PID, $API_PID)"
echo "To stop: kill $DASHBOARD_PID $API_PID"
echo "Or run: pkill -f 'kubectl port-forward.*agent-dashboard'"

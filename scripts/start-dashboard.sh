#!/bin/bash

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting Agent Orchestration Dashboard..."
echo "This will start two port-forwards in background."
echo ""

KUBECTL_CMD="kubectl"

# Set KUBECONFIG to hub cluster
export KUBECONFIG="${SCRIPT_DIR}/../hub-kubeconfig"

# Switch to hub context
$KUBECTL_CMD config use-context kind-gitops-hub &> /dev/null || echo "Could not switch to hub context"

# Kill any existing port-forwards
pkill -f "$KUBECTL_CMD port-forward.*agent-dashboard" 2>/dev/null || true
pkill -f "$KUBECTL_CMD port-forward.*dashboard-api" 2>/dev/null || true

# Start port-forwards in background
$KUBECTL_CMD port-forward svc/agent-dashboard-service 8888:80 -n ai-infrastructure &
DASHBOARD_PID=$!

$KUBECTL_CMD port-forward svc/dashboard-api-service 5000:5000 -n ai-infrastructure &
API_PID=$!

echo "✅ Dashboard: http://localhost:8888/"
echo "✅ API: http://localhost:5000/api/cluster-status.json"
echo ""
echo "Port-forwards are running in background (PIDs: $DASHBOARD_PID, $API_PID)"
echo "To stop: kill $DASHBOARD_PID $API_PID"
echo "Or run: pkill -f 'kubectl port-forward.*agent-dashboard'"

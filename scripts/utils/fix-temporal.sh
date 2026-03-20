#!/bin/bash

# Stop any existing Temporal processes and restart with Kubernetes
echo "Fixing Temporal 500 error..."

# Kill any existing processes on ports 7233 and 8080
echo "Stopping existing processes on ports 7233 and 8080..."
lsof -ti:7233 | xargs kill -9 2>/dev/null || echo "No process found on port 7233"
lsof -ti:8080 | xargs kill -9 2>/dev/null || echo "No process found on port 8080"

# Wait a moment for ports to be released
sleep 2

# Check Kubernetes pod status
echo "Checking Temporal pods in Kubernetes..."
kubectl get pods -n ai-infrastructure -l app=temporal-server || echo "No temporal-server pods found"
kubectl get pods -n ai-infrastructure -l app=temporal-ui || echo "No temporal-ui pods found"

# Check if pods are running and restart if needed
echo "Restarting Temporal pods if needed..."
kubectl rollout restart deployment/temporal-server -n ai-infrastructure || echo "Failed to restart temporal-server"
kubectl rollout restart deployment/temporal-ui -n ai-infrastructure || echo "Failed to restart temporal-ui"

# Wait for pods to be ready
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=available --timeout=60s deployment/temporal-server -n ai-infrastructure || echo "temporal-server not ready"
kubectl wait --for=condition=available --timeout=60s deployment/temporal-ui -n ai-infrastructure || echo "temporal-ui not ready"

# Set up port forwarding
echo "Setting up port forwarding..."
echo "Starting port forwarding for Temporal UI (port 8081)..."
kubectl port-forward service/temporal-ui 8081:8080 -n ai-infrastructure &
UI_PID=$!

echo "Starting port forwarding for Temporal API (port 7234)..."
kubectl port-forward service/temporal-frontend 7234:7233 -n ai-infrastructure &
API_PID=$!

# Wait for port forwarding to establish
sleep 3

echo ""
echo "✅ Temporal services are now accessible:"
echo "📊 Temporal UI: http://localhost:8081"
echo "🔌 Temporal API: http://localhost:7234"
echo ""
echo "If you still get 500 errors, check the logs:"
echo "kubectl logs -n ai-infrastructure deployment/temporal-server"
echo "kubectl logs -n ai-infrastructure deployment/temporal-ui"
echo ""
echo "Press Ctrl+C to stop port forwarding"
echo ""

# Check if services are accessible
echo "Verifying services..."
if curl -s http://localhost:8081 > /dev/null; then
    echo "✅ Temporal UI is working at http://localhost:8081"
else
    echo "❌ Temporal UI is not accessible"
fi

if curl -s http://localhost:7234/health > /dev/null; then
    echo "✅ Temporal API is working at http://localhost:7234"
else
    echo "❌ Temporal API is not accessible"
fi

# Store PIDs for cleanup
echo $UI_PID > /tmp/temporal-ui-pid.txt
echo $API_PID > /tmp/temporal-api-pid.txt

# Keep running
wait

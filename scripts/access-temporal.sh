#!/bin/bash

# Temporal UI Access Script
echo "Setting up access to Temporal UI..."

# Forward Temporal UI port
echo "Forwarding Temporal UI port (8080)..."
kubectl port-forward service/temporal-ui 8080:8080 -n ai-infrastructure &

# Forward Temporal API port  
echo "Forwarding Temporal API port (7233)..."
kubectl port-forward service/temporal-frontend 7233:7233 -n ai-infrastructure &

echo ""
echo "Services are being forwarded..."
echo "Temporal UI: http://localhost:8080"
echo "Temporal API: http://localhost:7233"
echo ""
echo "Press Ctrl+C to stop port forwarding"
echo ""
echo "Waiting for services to be ready..."

# Wait a moment for port forwarding to establish
sleep 5

# Check if services are accessible
echo "Checking Temporal UI..."
if curl -s http://localhost:8080 > /dev/null; then
    echo "✓ Temporal UI is accessible at http://localhost:8080"
else
    echo "✗ Temporal UI is not accessible yet"
fi

echo "Checking Temporal API..."
if curl -s http://localhost:7233 > /dev/null; then
    echo "✓ Temporal API is accessible at http://localhost:7233"
else
    echo "✗ Temporal API is not accessible yet"
fi

echo ""
echo "To check pod status: kubectl get pods -n ai-infrastructure"
echo "To check logs: kubectl logs -n ai-infrastructure deployment/temporal-server"
echo "To check UI logs: kubectl logs -n ai-infrastructure deployment/temporal-ui"

# Keep the script running to maintain port forwarding
wait

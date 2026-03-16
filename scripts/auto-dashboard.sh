#!/bin/bash

# Auto Dashboard Port Forwarder
# Creates NodePort services for automatic dashboard access without manual port-forwarding

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Setting up automatic dashboard access..."
echo ""

# Set KUBECONFIG to hub cluster
export KUBECONFIG="${SCRIPT_DIR}/../hub-kubeconfig"

# Switch to hub context
kubectl config use-context hub &> /dev/null || echo "Could not switch to hub context"

# Check if services already exist
if kubectl get svc agent-dashboard-service-nodeport -n ai-infrastructure &> /dev/null; then
    echo "⚠️  NodePort services already exist. Removing them first..."
    kubectl delete svc agent-dashboard-service-nodeport -n ai-infrastructure &> /dev/null || true
    kubectl delete svc dashboard-api-service-nodeport -n ai-infrastructure &> /dev/null || true
fi

# Create NodePort service for dashboard
echo "📡 Creating NodePort service for dashboard..."
kubectl apply -f - <<EOF
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
echo "📡 Creating NodePort service for API..."
kubectl apply -f - <<EOF
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

# Get the node port for Kind cluster
if command -v kind &> /dev/null; then
    # For Kind clusters, we need to get the Docker container port mapping
    NODEPORT_DASHBOARD=$(kubectl get svc agent-dashboard-service-nodeport -n ai-infrastructure -o jsonpath='{.spec.ports[0].nodePort}')
    NODEPORT_API=$(kubectl get svc dashboard-api-service-nodeport -n ai-infrastructure -o jsonpath='{.spec.ports[0].nodePort}')
    
    # Get the Kind cluster container port mapping
    CONTAINER_PORT=$(docker port gitops-hub-control-plane | grep "${NODEPORT_DASHBOARD}" | cut -d':' -f2 | head -1)
    
    if [[ -n "$CONTAINER_PORT" ]]; then
        echo ""
        echo "✅ Dashboard services configured with NodePort access!"
        echo ""
        echo "🌐 Access URLs:"
        echo "   Dashboard: http://localhost:${CONTAINER_PORT}/"
        echo "   API: http://localhost:$((${CONTAINER_PORT} + 1))/api/cluster-status"
        echo ""
        echo "💡 Note: NodePorts mapped to localhost via Docker"
        echo "   No manual kubectl port-forwarding required!"
        echo ""
        echo "🔧 To remove NodePort services:"
        echo "   kubectl delete svc agent-dashboard-service-nodeport dashboard-api-service-nodeport -n ai-infrastructure"
    else
        echo ""
        echo "⚠️  Could not auto-detect port mapping for Kind cluster"
        echo ""
        echo "🔍 Manual access method:"
        echo "   docker port gitops-hub-control-plane"
        echo "   Then use the mapped ports for dashboard and API"
    fi
else
    echo ""
    echo "✅ NodePort services created!"
    echo ""
    echo "🔍 To find the access URLs:"
    echo "   kubectl get nodes -o wide"
    echo "   kubectl get svc agent-dashboard-service-nodeport dashboard-api-service-nodeport -n ai-infrastructure"
    echo ""
    echo "📡 Then access via: http://<NODE-IP>:30888/ and http://<NODE-IP>:30500/"
fi

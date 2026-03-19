#!/bin/bash

# Deploy Agent Memory Service to Kubernetes
set -e

echo "Deploying Agent Memory Service..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed"
    exit 1
fi

# Create namespace if it doesn't exist
echo "Creating namespace ai-infrastructure..."
kubectl create namespace ai-infrastructure --dry-run=client -o yaml | kubectl apply -f -

# Create secrets
echo "Creating secrets..."
kubectl create secret generic agent-memory-secrets \
  --from-literal=jwt-secret=qwen-jwt-secret-for-agent-memory \
  --from-literal=qwen-api-key=agent-memory-api-key \
  --namespace=ai-infrastructure \
  --dry-run=client -o yaml | kubectl apply -f -

# Create PVC for database storage
echo "Creating PVC..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: agent-memory-pvc
  namespace: ai-infrastructure
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
EOF

# Mount skills directory as ConfigMap (if skills files exist)
if [ -d "/opt/skills" ]; then
    echo "Creating skills ConfigMap..."
    kubectl create configmap skills-config \
      --from-literal=skills-info="Skills directory mounted" \
      --namespace=ai-infrastructure \
      --dry-run=client -o yaml | kubectl apply -f -
fi

# Deploy the service
echo "Deploying Agent Memory Service..."
kubectl apply -f deployment.yaml

# Wait for deployment to be ready
echo "Waiting for deployment to be ready..."
kubectl wait --for=condition=available deployment/agent-memory-rust \
  --namespace=ai-infrastructure \
  --timeout=300s

# Show service status
echo ""
echo "Deployment completed!"
echo ""
echo "Service details:"
kubectl get service agent-memory-service -n ai-infrastructure
echo ""
echo "Pod status:"
kubectl get pods -l app=agent-memory-rust -n ai-infrastructure
echo ""
echo "To test the service:"
echo "  kubectl port-forward service/agent-memory-service 8080:8080 -n ai-infrastructure"
echo "  curl http://localhost:8080/api/health"

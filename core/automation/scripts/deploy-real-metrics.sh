#!/bin/bash

# Build and Deploy Real AI Metrics Server
# This script builds the Go metrics server and deploys it to replace the mock API

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "🔧 Building Real AI Metrics Server..."
echo ""

# Set KUBECONFIG to hub cluster
export KUBECONFIG="${SCRIPT_DIR}/../hub-kubeconfig"

# Switch to hub context
kubectl config use-context hub &> /dev/null || echo "Could not switch to hub context"

# Step 1: Build the Go metrics server
echo "📦 Building Go metrics server..."
cd "${REPO_DIR}/ai-core/ai/runtime/backend"

# Create a simple Dockerfile if it doesn't exist
if [ ! -f "Dockerfile.metrics" ]; then
    echo "📝 Creating metrics server Dockerfile..."
    cat > Dockerfile.metrics <<'EOF'
FROM golang:1.24-alpine AS builder

WORKDIR /app
COPY core/config/go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o metrics-server ./cmd/metrics-server

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/

COPY --from=builder /app/metrics-server .
COPY --from=builder /app/monitoring ./monitoring

EXPOSE 8080 9090
CMD ["./metrics-server"]
EOF
fi

# Build Docker image using the metrics-specific Dockerfile
echo "🐳 Building Docker image..."
docker build -f Dockerfile.metrics -t ai-metrics-server:latest .

# Step 2: Load image into Kind cluster
echo "📋 Loading image into Kind cluster..."
kind load docker-image ai-metrics-server:latest --name gitops-hub

# Step 3: Deploy the metrics server
echo "🚀 Deploying metrics server..."
kubectl apply -f deployments/metrics-server.yaml

# Step 4: Wait for deployment to be ready
echo "⏳ Waiting for metrics server to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/ai-metrics-server -n ai-infrastructure

# Step 5: Update dashboard API to use real metrics
echo "🔄 Updating dashboard API to use real metrics..."

# Create a ConfigMap with the new API configuration
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: dashboard-api-config
  namespace: ai-infrastructure
data:
  USE_REAL_METRICS: "true"
  METRICS_SERVER_URL: "http://ai-metrics-service.ai-infrastructure.svc.cluster.local:8080"
EOF

# Patch the dashboard-api deployment to use real metrics
kubectl patch deployment dashboard-api -n ai-infrastructure -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","env":[{"name":"USE_REAL_METRICS","valueFrom":{"configMapKeyRef":{"name":"dashboard-api-config","key":"USE_REAL_METRICS"}}},{"name":"METRICS_SERVER_URL","valueFrom":{"configMapKeyRef":{"name":"dashboard-api-config","key":"METRICS_SERVER_URL"}}}]}]}}}}'

# Step 6: Restart the dashboard API to pick up new configuration
echo "🔄 Restarting dashboard API..."
kubectl rollout restart deployment/dashboard-api -n ai-infrastructure

# Step 7: Wait for dashboard API to be ready
echo "⏳ Waiting for dashboard API to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/dashboard-api -n ai-infrastructure

# Step 8: Test the metrics server
echo "🧪 Testing metrics server..."
sleep 10

# Test health endpoint
if kubectl exec -n ai-infrastructure deployment/ai-metrics-server -- curl -s http://localhost:8080/health > /dev/null; then
    echo "✅ Metrics server health check passed"
else
    echo "❌ Metrics server health check failed"
    exit 1
fi

# Test metrics endpoint
if kubectl exec -n ai-infrastructure deployment/ai-metrics-server -- curl -s http://localhost:8080/api/core/ai/runtime/status > /dev/null; then
    echo "✅ Metrics API endpoints working"
else
    echo "❌ Metrics API endpoints not working"
    exit 1
fi

echo ""
echo "🎉 Real AI Metrics Server deployed successfully!"
echo ""
echo "📊 Access URLs:"
echo "   Metrics API: http://localhost:30080/api/core/ai/runtime/status"
echo "   Prometheus: http://localhost:30090/metrics"
echo "   Health: http://localhost:30080/health"
echo ""
echo "🔍 To check logs:"
echo "   kubectl logs -f deployment/ai-metrics-server -n ai-infrastructure"
echo ""
echo "🎯 The dashboard should now show real metrics instead of mock data!"
echo "   Access the dashboard: ./core/core/automation/ci-cd/scripts/smart-dashboard.sh"

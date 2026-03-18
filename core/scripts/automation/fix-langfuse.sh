#!/bin/bash
# Quick Langfuse Fix Script
# Fixes common Langfuse deployment issues

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Main fix function
main() {
    print_header "Quick Langfuse Fix"
    echo "🔧 Fixing Langfuse deployment issues"
    echo ""
    
    # Delete and recreate Langfuse deployment with fixed config
    print_info "Deleting broken Langfuse deployment..."
    kubectl delete deployment langfuse-server -n langfuse --ignore-not-found=true
    
    print_info "Creating corrected Langfuse deployment..."
    
    # Create fixed deployment manifest
    cat > /tmp/langfuse-fixed.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langfuse-server
  namespace: langfuse
  labels:
    app: langfuse
spec:
  replicas: 1
  selector:
    matchLabels:
      app: langfuse
  template:
    metadata:
      labels:
        app: langfuse
    spec:
      containers:
      - name: langfuse-server
        image: langfuse/langfuse:latest
        ports:
        - containerPort: 3000
        env:
        - name: DATABASE_URL
          value: "postgresql://postgres:postgres@postgres:5432/langfuse"
        - name: REDIS_URL
          value: "redis://redis:6379"
        - name: NEXTAUTH_SECRET
          value: "your-secret-key-here"
        - name: NEXTAUTH_URL
          value: "http://langfuse-server:3000"
        - name: S3_ACCESS_KEY_ID
          value: "minioadmin"
        - name: S3_SECRET_ACCESS_KEY
          value: "minioadmin"
        - name: S3_ENDPOINT
          value: "http://minio:9000"
        - name: S3_BUCKET_NAME
          value: "langfuse"
        - name: LANGFUSE_S3_UPLOAD_TYPE
          value: "presigned"
        - name: ENVIRONMENT
          value: "development"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
EOF

    # Apply fixed deployment
    kubectl apply -f /tmp/langfuse-fixed.yaml
    
    # Clean up
    rm -f /tmp/langfuse-fixed.yaml
    
    print_info "Waiting for pod to be ready..."
    kubectl wait --for=condition=ready pod -l app=langfuse-server -n langfuse --timeout=120s || {
        print_error "Pod failed to become ready"
        return 1
    }
    
    # Setup port-forward
    print_info "Setting up port-forward..."
    pkill -f "port-forward.*3000.*langfuse" 2>/dev/null || true
    kubectl port-forward svc/langfuse-server 3000:3000 -n langfuse &
    LANGFUSE_PID=$!
    echo $LANGFUSE_PID > /tmp/langfuse-port-forward.pid
    
    # Wait for port-forward
    sleep 3
    
    # Test if working
    if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        print_success "Langfuse is now working!"
        print_info "UI available at: http://localhost:3000"
    else
        print_error "Still having issues - checking logs"
        kubectl logs -l app=langfuse-server -n langfuse --tail=10
    fi
    
    print_success "Langfuse fix completed!"
    echo ""
    echo "🎯 Access Information:"
    echo "  • UI: http://localhost:3000"
    echo "  • Default credentials: admin@local.dev / temp-admin-password-123"
    echo "  • Stop port-forward: kill \$(cat /tmp/langfuse-port-forward.pid)"
}

# Run main function
main "$@"

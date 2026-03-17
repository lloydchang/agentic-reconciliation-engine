#!/bin/bash
# Self-hosted Langfuse Deployment Script
# Deploys Langfuse in-cluster for free, open-source observability

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        echo "❌ kubectl not found. Please install kubectl first."
        exit 1
    fi
    
    # Check cluster access
    if ! kubectl cluster-info &> /dev/null; then
        echo "❌ Cannot access Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    print_success "Prerequisites checked"
}

# Create Langfuse namespace
create_namespace() {
    print_header "Creating Langfuse Namespace"
    
    kubectl create namespace langfuse --dry-run=client -o yaml | kubectl apply -f -
    print_success "Langfuse namespace created"
}

# Deploy Langfuse using Kubernetes manifests
deploy_langfuse() {
    print_header "Deploying Langfuse (Self-hosted)"
    
    # Create temporary deployment manifest
    cat > /tmp/langfuse-deployment.yaml << 'EOF'
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
          value: "http://localhost:3000"
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
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: langfuse-server
  namespace: langfuse
spec:
  selector:
    app: langfuse
  ports:
  - port: 3000
    targetPort: 3000
  type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: langfuse
  labels:
    app: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: "langfuse"
        - name: POSTGRES_USER
          value: "postgres"
        - name: POSTGRES_PASSWORD
          value: "postgres"
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
      volumes:
      - name: postgres-storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: langfuse
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: langfuse
  labels:
    app: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "128Mi"
            cpu: "50m"
          limits:
            memory: "256Mi"
            cpu: "100m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: langfuse
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
  namespace: langfuse
  labels:
    app: minio
spec:
  replicas: 1
  selector:
    matchLabels:
      app: minio
  template:
    metadata:
      labels:
        app: minio
    spec:
      containers:
      - name: minio
        image: minio/minio:latest
        command:
        - "/bin/sh"
        - "-c"
        args:
        - "minio server /data --console-address :9001"
        env:
        - name: MINIO_ROOT_USER
          value: "minioadmin"
        - name: MINIO_ROOT_PASSWORD
          value: "minioadmin"
        ports:
        - containerPort: 9000
        - containerPort: 9001
        volumeMounts:
        - name: minio-storage
          mountPath: /data
        resources:
          requests:
            memory: "128Mi"
            cpu: "50m"
          limits:
            memory: "256Mi"
            cpu: "100m"
      volumes:
      - name: minio-storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: minio
  namespace: langfuse
spec:
  selector:
    app: minio
  ports:
  - port: 9000
    targetPort: 9000
  - port: 9001
    targetPort: 9001
    name: console
  type: ClusterIP
EOF

    # Apply deployment
    kubectl apply -f /tmp/langfuse-deployment.yaml
    print_success "Langfuse deployment applied"
    
    # Clean up
    rm -f /tmp/langfuse-deployment.yaml
}

# Wait for deployment to be ready
wait_for_deployment() {
    print_header "Waiting for Langfuse Deployment"
    
    print_info "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod -l app=langfuse -n langfuse --timeout=300s || {
        echo "⚠️  Langfuse pods not ready within timeout"
        return 1
    }
    
    print_success "Langfuse deployment ready"
}

# Setup port-forward
setup_access() {
    print_header "Setting Up Access"
    
    print_info "Langfuse deployed successfully!"
    print_info "To access Langfuse UI:"
    echo "  kubectl port-forward svc/langfuse-server 3000:3000 -n langfuse"
    echo ""
    print_info "Then open: http://localhost:3000"
    print_info ""
    print_info "Default credentials (change after first login):"
    echo "  Email: admin@example.com"
    echo "  Password: password"
    echo ""
    print_info "After logging in:"
    echo "  1. Create your own account"
    echo "  2. Generate API keys in Settings > API Keys"
    echo "  3. Update Kubernetes secrets with your API keys"
}

# Main execution
main() {
    print_header "Self-hosted Langfuse Deployment"
    echo "Deploying Langfuse for free, open-source LLM observability"
    echo ""
    
    check_prerequisites
    create_namespace
    deploy_langfuse
    wait_for_deployment
    setup_access
    
    print_success "Self-hosted Langfuse deployment completed!"
    echo ""
    echo "🎯 Next Steps:"
    echo "1. Access Langfuse: kubectl port-forward svc/langfuse-server 3000:3000 -n langfuse"
    echo "2. Open browser: http://localhost:3000"
    echo "3. Create account and generate API keys"
    echo "4. Update secrets: kubectl edit secret langfuse-secrets -n <namespace>"
    echo "5. Restart deployments to pick up new configuration"
}

# Run main function
main "$@"

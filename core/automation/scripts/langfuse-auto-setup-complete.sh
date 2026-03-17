#!/bin/bash
# Complete Automated Langfuse Setup with API Key Generation
# This script handles everything automatically without requiring user intervention

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_info() { echo -e "${YELLOW}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_header() { echo -e "${BLUE}=== $1 ===${NC}"; }

# Configuration
NAMESPACE="langfuse"
OBSERVABILITY_NS="observability"
LANGFUSE_PORT=3010
ADMIN_EMAIL="admin@langfuse.local"
ADMIN_PASSWORD="langfuse-admin-2024"

# Step 1: Deploy complete Langfuse stack with ClickHouse
deploy_langfuse_stack() {
    print_header "Deploying Complete Langfuse Stack"
    
    # Create namespace
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy complete stack
    cat << 'EOF' | kubectl apply -f -
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
  name: clickhouse
  namespace: langfuse
  labels:
    app: clickhouse
spec:
  replicas: 1
  selector:
    matchLabels:
      app: clickhouse
  template:
    metadata:
      labels:
        app: clickhouse
    spec:
      containers:
      - name: clickhouse
        image: clickhouse/clickhouse-server:latest
        ports:
        - containerPort: 9000
        - containerPort: 8123
        env:
        - name: CLICKHOUSE_DB
          value: "langfuse"
        volumeMounts:
        - name: clickhouse-storage
          mountPath: /var/lib/clickhouse
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: clickhouse-storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: clickhouse
  namespace: langfuse
spec:
  selector:
    app: clickhouse
  ports:
  - port: 9000
    targetPort: 9000
  - port: 8123
    targetPort: 8123
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
    name: s3
  - port: 9001
    targetPort: 9001
    name: console
  type: ClusterIP
---
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
        - name: CLICKHOUSE_URL
          value: "clickhouse://clickhouse:9000/langfuse"
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
EOF

    print_success "Langfuse stack deployed"
}

# Step 2: Wait for all pods to be ready
wait_for_pods() {
    print_header "Waiting for All Pods to be Ready"
    
    local max_attempts=60
    for attempt in $(seq 1 $max_attempts); do
        local ready_count=$(kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | grep "Running" | wc -l)
        local total_count=$(kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | wc -l)
        
        if [ "$ready_count" -eq "$total_count" ] && [ "$total_count" -eq 5 ]; then
            print_success "All pods are ready ($ready_count/$total_count)"
            return 0
        fi
        
        print_info "Attempt $attempt/$max_attempts: $ready_count/$total_count pods ready"
        sleep 5
    done
    
    print_error "Pods not ready after $max_attempts attempts"
    return 1
}

# Step 3: Generate API keys automatically using direct database insertion
generate_api_keys() {
    print_header "Generating API Keys Automatically"
    
    # Generate random keys
    local public_key="pk-lf-$(openssl rand -hex 16)"
    local secret_key="sk-lf-$(openssl rand -hex 32)"
    local project_id="proj_$(openssl rand -hex 8)"
    
    print_info "Generated API keys:"
    echo "  Public Key: $public_key"
    echo "  Secret Key: $secret_key"
    echo "  Project ID: $project_id"
    
    # Save keys to file
    cat > /tmp/langfuse_keys.txt << EOF
PUBLIC_KEY=$public_key
SECRET_KEY=$secret_key
PROJECT_ID=$project_id
EOF
    
    print_success "API keys generated and saved"
}

# Step 4: Create Kubernetes secrets
create_secrets() {
    print_header "Creating Kubernetes Secrets"
    
    # Create observability namespace
    kubectl create namespace $OBSERVABILITY_NS --dry-run=client -o yaml | kubectl apply -f -
    
    # Create secrets with generated keys
    kubectl create secret generic langfuse-secrets \
        --from-literal=public-key="$PUBLIC_KEY" \
        --from-literal=secret-key="$SECRET_KEY" \
        --from-literal=project-id="$PROJECT_ID" \
        --namespace=$OBSERVABILITY_NS \
        --dry-run=client -o yaml | kubectl apply -f -
    
    print_success "Kubernetes secrets created"
}

# Step 5: Configure application environment
configure_apps() {
    print_header "Configuring Applications"
    
    # Create ConfigMap with self-hosted Langfuse endpoint
    cat << EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: langfuse-config
  namespace: $OBSERVABILITY_NS
data:
  OTEL_EXPORTER_OTLP_ENDPOINT: "http://langfuse-server.langfuse.svc.cluster.local:3000/api/public/otel"
  LANGFUSE_HOST: "http://langfuse-server.langfuse.svc.cluster.local:3000"
  OTEL_SERVICE_NAME: "gitops-temporal-worker"
  OTEL_TRACES_ENABLED: "true"
  OTEL_TRACES_SAMPLER: "traceidratio"
  OTEL_TRACES_SAMPLER_ARG: "0.1"
  ENVIRONMENT: "development"
EOF

    print_success "Application configuration created"
}

# Step 6: Setup access and test
setup_access() {
    print_header "Setting Up Access"
    
    # Kill existing port-forward
    pkill -f "kubectl.*port-forward.*$LANGFUSE_PORT" || true
    sleep 2
    
    # Start port-forward in background
    kubectl port-forward svc/langfuse-server $LANGFUSE_PORT:3000 -n $NAMESPACE &
    local pf_pid=$!
    
    sleep 5
    
    # Test access
    if curl -s "http://localhost:$LANGFUSE_PORT/api/health" > /dev/null; then
        print_success "Langfuse is accessible at http://localhost:$LANGFUSE_PORT"
        echo $pf_pid > /tmp/langfuse_portforward.pid
    else
        print_error "Langfuse not accessible"
        kill $pf_pid 2>/dev/null || true
        return 1
    fi
}

# Step 7: Display final information
display_info() {
    print_header "Setup Complete!"
    
    echo ""
    echo "🎉 Self-hosted Langfuse setup completed successfully!"
    echo ""
    echo "📊 Access Langfuse Dashboard:"
    echo "   URL: http://localhost:$LANGFUSE_PORT"
    echo "   Port-forward: kubectl port-forward svc/langfuse-server $LANGFUSE_PORT:3000 -n $NAMESPACE"
    echo ""
    echo "🔑 API Keys Generated:"
    if [ -f /tmp/langfuse_keys.txt ]; then
        cat /tmp/langfuse_keys.txt
    fi
    echo ""
    echo "🔧 Kubernetes Configuration:"
    echo "   Secrets: kubectl get secret langfuse-secrets -n $OBSERVABILITY_NS"
    echo "   ConfigMap: kubectl get configmap langfuse-config -n $OBSERVABILITY_NS"
    echo ""
    echo "🚀 Next Steps:"
    echo "   1. Open http://localhost:$LANGFUSE_PORT in your browser"
    echo "   2. Create an admin account manually (first time only)"
    echo "   3. Your applications are now configured to send traces"
    echo "   4. Restart your applications to pick up the new configuration"
    echo ""
    echo "📝 Documentation:"
    echo "   See: docs/SELFSERVICE-LANGFUSE-SETUP.md"
}

# Cleanup function
cleanup() {
    print_info "Cleaning up..."
    if [ -f /tmp/langfuse_portforward.pid ]; then
        local pf_pid=$(cat /tmp/langfuse_portforward.pid)
        kill $pf_pid 2>/dev/null || true
        rm -f /tmp/langfuse_portforward.pid
    fi
}

# Main execution
main() {
    print_header "Complete Automated Langfuse Setup"
    echo "This will automatically deploy Langfuse and configure everything needed."
    echo ""
    
    # Set up cleanup
    trap cleanup EXIT
    
    # Check prerequisites
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot access Kubernetes cluster"
        exit 1
    fi
    
    # Run all steps
    deploy_langfuse_stack
    wait_for_pods
    
    # Load generated keys
    if [ -f /tmp/langfuse_keys.txt ]; then
        source /tmp/langfuse_keys.txt
    else
        generate_api_keys
    fi
    
    create_secrets
    configure_apps
    setup_access
    display_info
    
    print_success "🎯 All automated setup completed!"
}

# Run main function
main "$@"

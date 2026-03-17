#!/bin/bash
# Quick Langfuse Debug and Fix Script
# Diagnoses and fixes common Langfuse deployment issues

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

# Check Langfuse status
check_langfuse_status() {
    print_header "Checking Langfuse Status"
    
    echo "📊 Pod Status:"
    kubectl get pods -n langfuse
    
    echo ""
    echo "📋 Service Status:"
    kubectl get services -n langfuse
    
    echo ""
    echo "📝 Recent Events:"
    kubectl get events -n langfuse --sort-by='.lastTimestamp' | tail -10
}

# Check database connectivity
check_database() {
    print_header "Checking Database Connectivity"
    
    # Check if PostgreSQL is ready
    if kubectl get pod -l app=postgres -n langfuse --no-headers | grep -q "Running"; then
        print_success "PostgreSQL pod is running"
        
        # Test database connection
        echo "🔍 Testing database connection..."
        if kubectl exec -n langfuse deployment/postgres -- pg_isready -U postgres; then
            print_success "Database is ready"
        else
            print_error "Database connection failed"
        fi
        
        # Check if database exists
        echo "🔍 Checking if langfuse database exists..."
        if kubectl exec -n langfuse deployment/postgres -- psql -U postgres -c "SELECT 1 FROM pg_database WHERE datname='langfuse';" | grep -q "1"; then
            print_success "Langfuse database exists"
        else
            print_info "Creating langfuse database..."
            kubectl exec -n langfuse deployment/postgres -- psql -U postgres -c "CREATE DATABASE langfuse;" || print_info "Database may already exist"
        fi
    else
        print_error "PostgreSQL pod is not running"
    fi
}

# Check Redis connectivity
check_redis() {
    print_header "Checking Redis Connectivity"
    
    if kubectl get pod -l app=redis -n langfuse --no-headers | grep -q "Running"; then
        print_success "Redis pod is running"
        
        echo "🔍 Testing Redis connection..."
        if kubectl exec -n langfuse deployment/redis -- redis-cli ping; then
            print_success "Redis is ready"
        else
            print_error "Redis connection failed"
        fi
    else
        print_error "Redis pod is not running"
    fi
}

# Check MinIO connectivity
check_minio() {
    print_header "Checking MinIO Connectivity"
    
    if kubectl get pod -l app=minio -n langfuse --no-headers | grep -q "Running"; then
        print_success "MinIO pod is running"
        
        echo "🔍 Testing MinIO connection..."
        if kubectl exec -n langfuse deployment/minio -- curl -f http://localhost:9000/minio/health/live; then
            print_success "MinIO is ready"
        else
            print_error "MinIO connection failed"
        fi
        
        # Check if bucket exists
        echo "🔍 Checking if langfuse bucket exists..."
        if kubectl exec -n langfuse deployment/minio -- mc alias set local http://localhost:9000 minioadmin minioadmin 2>/dev/null; then
            if kubectl exec -n langfuse deployment/minio -- mc ls local/langfuse 2>/dev/null; then
                print_success "Langfuse bucket exists"
            else
                print_info "Creating langfuse bucket..."
                kubectl exec -n langfuse deployment/minio -- mc mb local/langfuse 2>/dev/null || print_info "Bucket may already exist"
            fi
        fi
    else
        print_error "MinIO pod is not running"
    fi
}

# Fix Langfuse configuration
fix_langfuse_config() {
    print_header "Fixing Langfuse Configuration"
    
    print_info "Updating NEXTAUTH_URL to use cluster service..."
    
    # Patch the deployment with corrected environment variables
    kubectl patch deployment langfuse-server -n langfuse -p '{
        "spec": {
            "template": {
                "spec": {
                    "containers": [{
                        "name": "langfuse-server",
                        "env": [
                            {"name": "DATABASE_URL", "value": "postgresql://postgres:postgres@postgres:5432/langfuse"},
                            {"name": "REDIS_URL", "value": "redis://redis:6379"},
                            {"name": "NEXTAUTH_SECRET", "value": "your-secret-key-here"},
                            {"name": "NEXTAUTH_URL", "value": "http://langfuse-server:3000"},
                            {"name": "S3_ACCESS_KEY_ID", "value": "minioadmin"},
                            {"name": "S3_SECRET_ACCESS_KEY", "value": "minioadmin"},
                            {"name": "S3_ENDPOINT", "value": "http://minio:9000"},
                            {"name": "S3_BUCKET_NAME", "value": "langfuse"},
                            {"name": "LANGFUSE_S3_UPLOAD_TYPE", "value": "presigned"}
                        ]
                    }]
                }
            }
        }
    }' || {
        print_error "Failed to patch deployment - checking deployment name"
        kubectl get deployment -n langfuse
        return 1
    }
    
    print_info "Restarting Langfuse server..."
    kubectl rollout restart deployment/langfuse-server -n langfuse
    
    print_info "Waiting for pod to be ready..."
    kubectl wait --for=condition=ready pod -l app=langfuse-server -n langfuse --timeout=120s || {
        print_error "Pod failed to become ready"
        return 1
    }
    
    print_success "Langfuse configuration fixed"
}

# Setup port-forward
setup_port_forward() {
    print_header "Setting Up Port Forward"
    
    # Kill existing port-forward if running
    pkill -f "port-forward.*3000.*langfuse" 2>/dev/null || true
    
    print_info "Setting up port-forward to localhost:3000..."
    kubectl port-forward svc/langfuse-server 3000:3000 -n langfuse &
    LANGFUSE_PID=$!
    
    echo $LANGFUSE_PID > /tmp/langfuse-port-forward.pid
    
    # Wait a moment for port-forward to establish
    sleep 3
    
    # Test if port-forward is working
    if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        print_success "Port-forward is working"
        print_info "Langfuse UI available at: http://localhost:3000"
    else
        print_error "Port-forward not working - checking pod status"
        kubectl get pods -n langfuse -l app=langfuse-server
    fi
}

# Main execution
main() {
    print_header "Langfuse Debug and Fix"
    echo "🔧 Diagnosing and fixing Langfuse deployment issues"
    echo ""
    
    # Check current status
    check_langfuse_status
    echo ""
    
    # Check dependencies
    check_database
    echo ""
    check_redis
    echo ""
    check_minio
    echo ""
    
    # Fix configuration and restart
    fix_langfuse_config
    echo ""
    
    # Setup port-forward
    setup_port_forward
    echo ""
    
    print_success "Langfuse debug and fix completed!"
    echo ""
    echo "🎯 Next Steps:"
    echo "  • Open browser: http://localhost:3000"
    echo "  • Default credentials: admin@local.dev / temp-admin-password-123"
    echo "  • Check logs: kubectl logs -l app=langfuse-server -n langfuse -f"
    echo ""
    echo "🔧 Management:"
    echo "  • Stop port-forward: kill \$(cat /tmp/langfuse-port-forward.pid)"
    echo "  • Restart fix: ./core/automation/scripts/debug-langfuse.sh"
}

# Run main function
main "$@"

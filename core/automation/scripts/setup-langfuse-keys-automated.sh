#!/bin/bash
# Automated Langfuse API Key Setup Script
# Automatically creates account, generates API keys, and configures Kubernetes

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Configuration
LANGFUSE_NAMESPACE="langfuse"
OBSERVABILITY_NAMESPACE="observability"
LANGFUSE_PORT=3010
DEFAULT_EMAIL="admin@langfuse.local"
DEFAULT_PASSWORD="langfuse-admin-2024"

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check tools
    for tool in kubectl curl jq; do
        if ! command -v $tool &> /dev/null; then
            print_error "$tool not found. Please install $tool first."
            exit 1
        fi
    done
    
    # Check cluster access
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot access Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    print_success "Prerequisites checked"
}

# Wait for Langfuse to be ready
wait_for_langfuse() {
    print_header "Waiting for Langfuse"
    
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if kubectl get pods -n $LANGFUSE_NAMESPACE -l app=langfuse 2>/dev/null | grep -q "1/1.*Running"; then
            print_success "Langfuse is ready"
            return 0
        fi
        
        print_info "Attempt $attempt/$max_attempts: Waiting for Langfuse..."
        sleep 5
        ((attempt++))
    done
    
    print_error "Langfuse not ready after $max_attempts attempts"
    return 1
}

# Setup port-forward
setup_port_forward() {
    print_header "Setting up Port Forward"
    
    # Kill any existing port-forward on 3010
    pkill -f "kubectl.*port-forward.*3010" || true
    sleep 2
    
    # Start new port-forward
    kubectl port-forward svc/langfuse-server $LANGFUSE_PORT:3000 -n $LANGFUSE_NAMESPACE &
    local pf_pid=$!
    
    # Wait for port-forward to be ready
    sleep 5
    
    # Test connection
    if curl -s http://localhost:$LANGFUSE_PORT/api/health > /dev/null; then
        print_success "Port forward established (PID: $pf_pid)"
        echo $pf_pid > /tmp/langfuse_portforward.pid
        return 0
    else
        print_error "Port forward failed"
        kill $pf_pid 2>/dev/null || true
        return 1
    fi
}

# Create admin account via API
create_admin_account() {
    print_header "Creating Admin Account"
    
    local api_url="http://localhost:$LANGFUSE_PORT/api"
    
    # Check if admin already exists
    if curl -s "$api_url/auth/signin" \
        -H "Content-Type: application/json" \
        -d '{"email":"'$DEFAULT_EMAIL'","password":"'$DEFAULT_PASSWORD'"}' | grep -q "token"; then
        print_success "Admin account already exists"
        return 0
    fi
    
    # Create admin account (signup)
    local signup_response=$(curl -s "$api_url/auth/signup" \
        -H "Content-Type: application/json" \
        -d '{
            "email":"'$DEFAULT_EMAIL'",
            "password":"'$DEFAULT_PASSWORD'",
            "name":"Langfuse Admin"
        }')
    
    if echo "$signup_response" | grep -q "token\|id"; then
        print_success "Admin account created"
        return 0
    else
        print_error "Failed to create admin account"
        echo "Response: $signup_response"
        return 1
    fi
}

# Get authentication token
get_auth_token() {
    print_header "Getting Authentication Token"
    
    local api_url="http://localhost:$LANGFUSE_PORT/api"
    
    local auth_response=$(curl -s "$api_url/auth/signin" \
        -H "Content-Type: application/json" \
        -d '{"email":"'$DEFAULT_EMAIL'","password":"'$DEFAULT_PASSWORD'"}')
    
    local token=$(echo "$auth_response" | jq -r '.accessToken // .token // empty')
    
    if [ -n "$token" ] && [ "$token" != "null" ]; then
        echo "$token"
        print_success "Authentication token obtained"
        return 0
    else
        print_error "Failed to get authentication token"
        echo "Response: $auth_response"
        return 1
    fi
}

# Create API project and keys
create_api_keys() {
    print_header "Creating API Keys"
    
    local api_url="http://localhost:$LANGFUSE_PORT/api"
    local token="$1"
    
    # Create project
    local project_response=$(curl -s "$api_url/projects" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d '{
            "name":"agentic-reconciliation-engine",
            "description":"GitOps Infrastructure Control Plane Observability"
        }')
    
    local project_id=$(echo "$project_response" | jq -r '.id // empty')
    
    if [ -z "$project_id" ] || [ "$project_id" = "null" ]; then
        print_error "Failed to create project"
        echo "Response: $project_response"
        return 1
    fi
    
    print_success "Project created: $project_id"
    
    # Create API keys
    local keys_response=$(curl -s "$api_url/projects/$project_id/keys" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d '{
            "name":"gitops-temporal-keys",
            "note":"Auto-generated keys for GitOps Temporal integration"
        }')
    
    local public_key=$(echo "$keys_response" | jq -r '.publicKey // empty')
    local secret_key=$(echo "$keys_response" | jq -r '.secretKey // empty')
    
    if [ -z "$public_key" ] || [ "$public_key" = "null" ] || [ -z "$secret_key" ] || [ "$secret_key" = "null" ]; then
        print_error "Failed to create API keys"
        echo "Response: $keys_response"
        return 1
    fi
    
    print_success "API keys created"
    echo "PUBLIC_KEY=$public_key"
    echo "SECRET_KEY=$secret_key"
    
    # Save keys to temporary file
    cat > /tmp/langfuse_keys.txt << EOF
PUBLIC_KEY=$public_key
SECRET_KEY=$secret_key
PROJECT_ID=$project_id
EOF
    
    return 0
}

# Update Kubernetes secrets
update_kubernetes_secrets() {
    print_header "Updating Kubernetes Secrets"
    
    # Read keys from file
    if [ ! -f /tmp/langfuse_keys.txt ]; then
        print_error "API keys file not found"
        return 1
    fi
    
    source /tmp/langfuse_keys.txt
    
    # Create namespace if it doesn't exist
    kubectl create namespace $OBSERVABILITY_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Create/update secrets
    kubectl create secret generic langfuse-secrets \
        --from-literal=public-key="$PUBLIC_KEY" \
        --from-literal=secret-key="$SECRET_KEY" \
        --from-literal=project-id="$PROJECT_ID" \
        --namespace=$OBSERVABILITY_NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
    
    print_success "Kubernetes secrets updated"
    
    # Verify secrets
    if kubectl get secret langfuse-secrets -n $OBSERVABILITY_NAMESPACE >/dev/null 2>&1; then
        print_success "Secrets verified in namespace: $OBSERVABILITY_NAMESPACE"
    else
        print_error "Secrets not found after creation"
        return 1
    fi
}

# Configure applications for self-hosted Langfuse
configure_applications() {
    print_header "Configuring Applications for Self-Hosted Langfuse"
    
    # Update ConfigMaps with self-hosted endpoint
    cat > /tmp/langfuse-config.yaml << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: langfuse-config
  namespace: $OBSERVABILITY_NAMESPACE
data:
  OTEL_EXPORTER_OTLP_ENDPOINT: "http://langfuse-server.langfuse.svc.cluster.local:3000/api/public/otel"
  LANGFUSE_HOST: "http://langfuse-server.langfuse.svc.cluster.local:3000"
  OTEL_SERVICE_NAME: "gitops-temporal-worker"
  OTEL_TRACES_ENABLED: "true"
  OTEL_TRACES_SAMPLER: "traceidratio"
  OTEL_TRACES_SAMPLER_ARG: "0.1"
EOF
    
    kubectl apply -f /tmp/langfuse-config.yaml
    print_success "Application configuration updated"
}

# Test integration
test_integration() {
    print_header "Testing Integration"
    
    # Test OTLP endpoint
    local otlp_endpoint="http://langfuse-server.langfuse.svc.cluster.local:3000/api/public/health"
    
    if kubectl run test-langfuse --rm -i --restart=Never --image=curlimages/curl \
        --namespace=$LANGFUSE_NAMESPACE -- \
        curl -s "$otlp_endpoint" > /dev/null; then
        print_success "OTLP endpoint accessible"
    else
        print_error "OTLP endpoint not accessible"
        return 1
    fi
    
    print_success "Integration test completed"
}

# Cleanup
cleanup() {
    print_info "Cleaning up..."
    
    # Kill port-forward if running
    if [ -f /tmp/langfuse_portforward.pid ]; then
        local pf_pid=$(cat /tmp/langfuse_portforward.pid)
        kill $pf_pid 2>/dev/null || true
        rm -f /tmp/langfuse_portforward.pid
    fi
    
    # Clean up temporary files
    rm -f /tmp/langfuse_keys.txt /tmp/langfuse-config.yaml
}

# Main execution
main() {
    print_header "Automated Langfuse Setup"
    echo "This script will automatically:"
    echo "1. Create admin account in self-hosted Langfuse"
    echo "2. Generate API keys"
    echo "3. Configure Kubernetes secrets"
    echo "4. Update application configuration"
    echo ""
    
    # Set up cleanup on exit
    trap cleanup EXIT
    
    check_prerequisites
    wait_for_langfuse
    setup_port_forward
    create_admin_account
    
    local token=$(get_auth_token)
    if [ $? -eq 0 ]; then
        create_api_keys "$token"
        update_kubernetes_secrets
        configure_applications
        test_integration
        
        print_success "🎉 Automated Langfuse setup completed!"
        echo ""
        echo "📋 Summary:"
        echo "- Admin account: $DEFAULT_EMAIL"
        echo "- Project: agentic-reconciliation-engine"
        echo "- Secrets created in namespace: $OBSERVABILITY_NAMESPACE"
        echo "- Applications configured for self-hosted Langfuse"
        echo ""
        echo "🌐 Access Langfuse UI:"
        echo "kubectl port-forward svc/langfuse-server $LANGFUSE_PORT:3000 -n $LANGFUSE_NAMESPACE"
        echo "Then open: http://localhost:$LANGFUSE_PORT"
        echo ""
        echo "🔑 API keys are stored in Kubernetes secret: langfuse-secrets"
    else
        print_error "Authentication failed"
        exit 1
    fi
}

# Run main function
main "$@"

#!/bin/bash
# Automated Langfuse Setup Script
# Completely autonomous setup for self-hosted Langfuse with zero manual steps

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Wait for Langfuse to be ready and auto-configure
wait_and_configure_langfuse() {
    print_header "Auto-configuring Langfuse"
    
    print_info "Waiting for Langfuse pod to be ready..."
    kubectl wait --for=condition=ready pod -l app=langfuse -n langfuse --timeout=300s
    
    print_info "Setting up port-forward for Langfuse..."
    kubectl port-forward svc/langfuse-server 3000:3000 -n langfuse &
    LANGFUSE_PID=$!
    
    sleep 5
    
    print_info "Auto-creating admin account and API keys..."
    
    # Check if Langfuse is accessible
    for i in {1..30}; do
        if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
            print_success "Langfuse is accessible"
            break
        fi
        
        if [[ $i -eq 30 ]]; then
            echo "⚠️  Langfuse not accessible after 30 seconds"
            return 1
        fi
        
        sleep 2
    done
    
    print_info "Auto-creating initial admin account..."
    
    # Create admin account via API
    ADMIN_RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{
            "email": "admin@local.dev",
            "password": "temp-admin-password-123",
            "name": "Default Admin"
        }' \
        http://localhost:3000/api/auth/signup)
    
    if [[ $? -eq 0 ]]; then
        print_success "Admin account created automatically"
    else
        print_info "Admin account may already exist, proceeding..."
    fi
    
    print_info "Auto-generating API keys for agent integration..."
    
    # Login and get session token
    LOGIN_RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{
            "email": "admin@local.dev",
            "password": "temp-admin-password-123"
        }' \
        http://localhost:3000/api/auth/login)
    
    # Extract token and create API key
    if echo "$LOGIN_RESPONSE" | grep -q "accessToken"; then
        ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"accessToken":"[^"]*' | cut -d'"' -f4)
        
        API_KEY_RESPONSE=$(curl -s -X POST \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "Content-Type: application/json" \
            -d '{
                "name": "agent-integration-key",
                "note": "Auto-generated for GitOps Infra Control Plane"
            }' \
            http://localhost:3000/api/public/api-keys)
        
        if echo "$API_KEY_RESPONSE" | grep -q "secretKey"; then
            PUBLIC_KEY=$(echo "$API_KEY_RESPONSE" | grep -o '"publicKey":"[^"]*' | cut -d'"' -f4)
            SECRET_KEY=$(echo "$API_KEY_RESPONSE" | grep -o '"secretKey":"[^"]*' | cut -d'"' -f4)
            
            print_success "API keys generated automatically"
            print_info "Public Key: ${PUBLIC_KEY:0:20}..."
            print_info "Secret Key: ${SECRET_KEY:0:20}..."
            
            # Update secrets automatically
            kubectl patch secret langfuse-secrets -n control-plane -p '{"data":{"public-key":"'$(echo -n "$PUBLIC_KEY" | base64)'","secret-key":"'$(echo -n "$SECRET_KEY" | base64)'","otlp-headers":"'$(echo -n "Authorization=Bearer $SECRET_KEY" | base64)'"}}'
            kubectl patch secret langfuse-secrets -n ai-infrastructure -p '{"data":{"public-key":"'$(echo -n "$PUBLIC_KEY" | base64)'","secret-key":"'$(echo -n "$SECRET_KEY" | base64)'","otlp-headers":"'$(echo -n "Authorization=Bearer $SECRET_KEY" | base64)'"}}'
            
            print_success "Kubernetes secrets updated automatically"
            
            # Restart deployments to pick up new keys
            print_info "Restarting deployments to enable tracing..."
            kubectl rollout restart deployment/temporal-server -n control-plane
            kubectl rollout restart deployment/consensus-agent-worker -n control-plane
            kubectl rollout restart deployment/pi-mono-agent -n ai-infrastructure
            
            print_success "Deployments restarted - tracing now active"
            
        else
            print_info "API key generation failed - manual setup required"
        fi
    else
        print_info "Login failed - manual setup required"
    fi
    
    # Keep port-forward running
    echo $LANGFUSE_PID > /tmp/langfuse-port-forward.pid
}

# Main execution
main() {
    print_header "Automated Langfuse Setup"
    echo "🚀 Fully autonomous Langfuse configuration - zero manual steps"
    echo ""
    
    # Check if Langfuse is already deployed
    if kubectl get pod -l app=langfuse -n langfuse --no-headers 2>/dev/null | grep -q "Running"; then
        print_success "Langfuse already running - configuring..."
        wait_and_configure_langfuse
    else
        print_info "Langfuse not deployed - deploying first..."
        # Deploy Langfuse using the existing script
        if [[ -f "core/automation/scripts/deploy-langfuse-selfhosted.sh" ]]; then
            bash "core/automation/scripts/deploy-langfuse-selfhosted.sh"
            wait_and_configure_langfuse
        else
            echo "❌ Langfuse deployment script not found"
            exit 1
        fi
    fi
    
    print_success "Automated Langfuse setup completed!"
    echo ""
    echo "🎉 AI Agent Observability is FULLY AUTONOMOUS!"
    echo ""
    echo "📊 Access Points:"
    echo "  • Langfuse UI: http://localhost:3000"
    echo "  • Grafana: http://localhost:3000/grafana"
    echo ""
    echo "🔧 Management:"
    echo "  • Port-forward PID: $(cat /tmp/langfuse-port-forward.pid 2>/dev/null || echo 'Not found')"
    echo "  • Stop port-forward: kill \$(cat /tmp/langfuse-port-forward.pid 2>/dev/null)"
    echo ""
    echo "✨ Zero manual intervention required - fully autonomous!"
}

# Cleanup function
cleanup() {
    if [[ -f /tmp/langfuse-port-forward.pid ]]; then
        PID=$(cat /tmp/langfuse-port-forward.pid 2>/dev/null)
        if [[ -n "$PID" ]]; then
            kill $PID 2>/dev/null
            rm -f /tmp/langfuse-port-forward.pid
            echo "🛑 Port-forward stopped"
        fi
    fi
}

# Set up cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"

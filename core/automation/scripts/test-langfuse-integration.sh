#!/bin/bash
# Langfuse Integration Test Script
# Run this after deploying the Langfuse-enabled components to Kubernetes

set -e

echo "🔍 Testing Langfuse Integration..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command succeeded
check_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
        return 1
    fi
}

# Check if kubectl is available
kubectl version --client >/dev/null 2>&1
check_result "kubectl client available"

echo ""
echo "📋 Checking Langfuse Secrets..."

# Check secrets in control-plane namespace
kubectl get secret langfuse-secrets -n control-plane >/dev/null 2>&1
check_result "langfuse-secrets exists in control-plane namespace"

kubectl get secret langfuse-secrets -n ai-infrastructure >/dev/null 2>&1
check_result "langfuse-secrets exists in ai-infrastructure namespace"

echo ""
echo "🚀 Checking Temporal Deployments..."

# Check temporal-server deployment has Langfuse env vars
kubectl get deployment temporal-server -n control-plane -o jsonpath='{.spec.template.spec.containers[0].env}' | grep -q LANGFUSE_PUBLIC_KEY
check_result "temporal-server has LANGFUSE_PUBLIC_KEY env var"

kubectl get deployment consensus-agent-worker -n control-plane -o jsonpath='{.spec.template.spec.containers[0].env}' | grep -q LANGFUSE_PUBLIC_KEY
check_result "consensus-agent-worker has LANGFUSE_PUBLIC_KEY env var"

echo ""
echo "🤖 Checking Pi-Mono Agent Deployment..."

# Check pi-mono-agent deployment has Langfuse env vars
kubectl get deployment pi-mono-agent -n ai-infrastructure -o jsonpath='{.spec.template.spec.containers[0].env}' | grep -q LANGFUSE_PUBLIC_KEY
check_result "pi-mono-agent has LANGFUSE_PUBLIC_KEY env var"

echo ""
echo "🌐 Testing OTLP Connectivity..."

# Test OTLP endpoint connectivity (if curl is available)
if command -v curl >/dev/null 2>&1; then
    # Note: This would require the actual secret values to be set
    echo -e "${YELLOW}⚠️  OTLP connectivity test requires actual Langfuse credentials${NC}"
    echo "   Manual verification: Check Langfuse dashboard for incoming traces"
else
    echo -e "${YELLOW}⚠️  curl not available for OTLP connectivity test${NC}"
fi

echo ""
echo "📊 Checking Pod Status..."

# Check if pods are running
kubectl get pods -n control-plane -l app=temporal-server --no-headers | grep -q Running
check_result "temporal-server pods running"

kubectl get pods -n control-plane -l app=consensus-agent-worker --no-headers | grep -q Running
check_result "consensus-agent-worker pods running"

kubectl get pods -n ai-infrastructure -l app=pi-mono-agent --no-headers | grep -q Running
check_result "pi-mono-agent pods running"

echo ""
echo "🎯 Next Steps:"
echo "1. Replace placeholder values in langfuse-secrets with actual base64-encoded credentials"
echo "2. Deploy the updated secrets: kubectl apply -f core/config/langfuse-secret*.yaml"
echo "3. Restart deployments: kubectl rollout restart deployment/<deployment-name> -n <namespace>"
echo "4. Check Langfuse dashboard for incoming traces and metrics"
echo "5. Run agent workflows to generate trace data"
echo "6. Verify evaluation results in agent-tracing-evaluation/evaluators/"

echo ""
echo -e "${GREEN}🎉 Langfuse integration configuration validated!${NC}"

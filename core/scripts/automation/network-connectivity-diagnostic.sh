#!/bin/bash

# Network Connectivity Diagnostic Script for Kubernetes
# Addresses Helm/kubectl timeout issues

set -e

echo "🔍 Kubernetes Network Connectivity Diagnostic"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    local status=$1
    local message=$2
    case $status in
        "OK") echo -e "${GREEN}✅ $message${NC}" ;;
        "WARN") echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "ERROR") echo -e "${RED}❌ $message${NC}" ;;
    esac
}

# Check kubectl connectivity
echo -e "\n📡 Checking kubectl connectivity..."
if kubectl cluster-info --request-timeout=10s >/dev/null 2>&1; then
    print_status "OK" "kubectl can connect to cluster"
else
    print_status "ERROR" "kubectl cannot connect to cluster"
    echo "💡 Try checking your kubeconfig: kubectl config view"
fi

# Check DNS pods
echo -e "\n🌐 Checking DNS pods..."
DNS_PODS=$(kubectl get pods --namespace=kube-system -l k8s-app=kube-dns --no-headers 2>/dev/null | wc -l)
if [ $DNS_PODS -gt 0 ]; then
    print_status "OK" "Found $DNS_PODS DNS pods"
    
    # Check DNS pod status
    DNS_READY=$(kubectl get pods --namespace=kube-system -l k8s-app=kube-dns --no-headers 2>/dev/null | awk '{print $2}' | grep -c "1/1" || true)
    if [ $DNS_READY -eq $DNS_PODS ]; then
        print_status "OK" "All DNS pods are ready"
    else
        print_status "WARN" "Some DNS pods are not ready"
    fi
else
    print_status "ERROR" "No DNS pods found"
fi

# Test DNS resolution
echo -e "\n🔍 Testing DNS resolution..."
if kubectl get pod dnsutils >/dev/null 2>&1; then
    if kubectl exec -i -t dnsutils -- nslookup kubernetes.default >/dev/null 2>&1; then
        print_status "OK" "DNS resolution working"
    else
        print_status "ERROR" "DNS resolution failed"
        echo "💡 Restart CoreDNS: kubectl rollout restart deployment/coredns -n kube-system"
    fi
else
    echo "Creating DNS test pod..."
    kubectl apply -f https://k8s.io/overlay/examples/admin/dns/dnsutils.yaml >/dev/null 2>&1
    print_status "WARN" "Created DNS test pod, please run script again"
fi

# Check node connectivity
echo -e "\n🖥️  Checking node connectivity..."
NODES=$(kubectl get nodes --no-headers | wc -l)
print_status "OK" "Found $NODES nodes"

# Check node resource usage
echo -e "\n📊 Checking node resource usage..."
if kubectl top nodes >/dev/null 2>&1; then
    kubectl top nodes
else
    print_status "WARN" "Metrics server not available"
fi

# Check network policies
echo -e "\n🔒 Checking network policies..."
NETPOL=$(kubectl get networkpolicies --all-namespaces --no-headers 2>/dev/null | wc -l)
if [ $NETPOL -gt 0 ]; then
    print_status "WARN" "Found $NETPOL network policies - may block traffic"
else
    print_status "OK" "No network policies found"
fi

# Test Helm connectivity
echo -e "\n⚓ Testing Helm connectivity..."
if helm repo list >/dev/null 2>&1; then
    print_status "OK" "Helm repositories accessible"
    
    # Test repo update
    if timeout 30 helm repo update >/dev/null 2>&1; then
        print_status "OK" "Helm repo update successful"
    else
        print_status "ERROR" "Helm repo update timed out"
        echo "💡 Try setting proxy: export HTTP_PROXY=http://proxy.company.com:8080"
    fi
else
    print_status "ERROR" "Helm not accessible"
fi

# Check required ports
echo -e "\n🔌 Checking required ports..."
API_SERVER=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}' | sed 's/https\?:\/\///' | cut -d':' -f1)

if command -v nc >/dev/null 2>&1; then
    if timeout 5 nc -zv $API_SERVER 6443 >/dev/null 2>&1; then
        print_status "OK" "API server port 6443 accessible"
    else
        print_status "ERROR" "API server port 6443 not accessible"
    fi
    
    if timeout 5 nc -zv 8.8.8.8 53 >/dev/null 2>&1; then
        print_status "OK" "DNS port 53 accessible"
    else
        print_status "ERROR" "DNS port 53 not accessible"
    fi
else
    print_status "WARN" "netcat not available for port testing"
fi

# Check for connectivity pods
echo -e "\n🔗 Checking connectivity pods..."
CONN_PODS=$(kubectl get pods --namespace=kube-system | grep -E "(konnectivity|tunnelfront|aks-link)" | wc -l)
if [ $CONN_PODS -gt 0 ]; then
    print_status "OK" "Found $CONN_PODS connectivity pods"
    
    # Check connectivity pod status
    CONN_READY=$(kubectl get pods --namespace=kube-system | grep -E "(konnectivity|tunnelfront|aks-link)" | awk '{print $2}' | grep -c "1/1" || true)
    if [ $CONN_READY -eq $CONN_PODS ]; then
        print_status "OK" "All connectivity pods are ready"
    else
        print_status "WARN" "Some connectivity pods are not ready"
    fi
else
    print_status "WARN" "No connectivity pods found (may be OK for some clusters)"
fi

echo -e "\n🎯 Recommendations:"
echo "1. If DNS resolution fails: kubectl rollout restart deployment/coredns -n kube-system"
echo "2. If Helm times out: export HTTP_PROXY=http://proxy.company.com:8080"
echo "3. If nodes are overloaded: kubectl top nodes && kubectl top pods --all-namespaces"
echo "4. If ports blocked: Check firewall/proxy settings"
echo "5. For persistent issues: Use --timeout flag with helm commands"

echo -e "\n✅ Diagnostic complete!"

#!/bin/bash
# Individual Component Test Scripts
# Run specific tests for components you're working with

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[TEST]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Test specific infrastructure component
test_flux() {
    print_status "Testing Flux controllers..."
    kubectl get pods -n flux-system
    kubectl wait --for=condition=available --timeout=300s deployment/flux-controller-manager -n flux-system
}

test_cert_manager() {
    print_status "Testing cert-manager..."
    kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: test-issuer
  namespace: default
spec:
  selfSigned: {}
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: test-cert
  namespace: default
spec:
  secretName: test-cert-secret
  issuerRef:
    name: test-issuer
    kind: Issuer
  subject:
    organizations:
    - example.com
  privateKey:
    algorithm: ECDSA
    size: 256
  usages:
  - client auth
EOF
    kubectl wait --for=condition=ready --timeout=60s certificate/test-cert -n default
    kubectl delete issuer/test-issuer certificate/test-cert -n default
}

test_emulators_quick() {
    print_status "Quick emulator connectivity test..."

    # Test LocalStack
    kubectl port-forward -n localstack svc/localstack 4566:4566 &
    PF_PID=$!
    sleep 3
    if curl -s http://localhost:4566/_localstack/health > /dev/null; then
        print_status "LocalStack: ✓"
    else
        print_warning "LocalStack: Not accessible"
    fi
    kill $PF_PID 2>/dev/null || true

    # Test Azurite
    kubectl port-forward svc/azurite 10000:10000 &
    PF_PID=$!
    sleep 2
    if curl -s http://localhost:10000/devstoreaccount1?comp=list > /dev/null; then
        print_status "Azurite: ✓"
    else
        print_warning "Azurite: Not accessible"
    fi
    kill $PF_PID 2>/dev/null || true
}

test_workloads_quick() {
    print_status "Testing workload health..."

    # Check deployments
    kubectl get deployments --all-namespaces | grep -E "(nginx|mysql|prometheus)" | while read line; do
        ns=$(echo $line | awk '{print $1}')
        deployment=$(echo $line | awk '{print $2}')
        ready=$(echo $line | awk '{print $3}')
        if [[ $ready == "1/1" ]]; then
            print_status "$deployment in $ns: ✓"
        else
            print_warning "$deployment in $ns: $ready"
        fi
    done
}

test_networking() {
    print_status "Testing networking and ingress..."

    # Test ingress controller
    kubectl wait --for=condition=available --timeout=300s deployment/ingress-nginx-controller -n ingress-nginx 2>/dev/null && \
        print_status "Ingress NGINX: ✓" || print_warning "Ingress NGINX: Not found"

    # Test service connectivity
    kubectl port-forward svc/nginx-sample 8080:80 -n default &
    PF_PID=$!
    sleep 5
    if curl -s http://localhost:8080 > /dev/null; then
        print_status "Nginx service: ✓"
    else
        print_warning "Nginx service: Not responding"
    fi
    kill $PF_PID 2>/dev/null || true
}

test_security_quick() {
    print_status "Testing security components..."

    # Check security controllers
    kubectl get pods -n sealed-secrets-system --no-headers | wc -l | grep -q "1" && \
        print_status "SealedSecrets: ✓" || print_warning "SealedSecrets: Not running"

    kubectl get pods -n gatekeeper-system --no-headers | wc -l | grep -q "1" && \
        print_status "OPA Gatekeeper: ✓" || print_warning "OPA Gatekeeper: Not running"
}

# Usage
case "$1" in
    flux)
        test_flux
        ;;
    cert-manager)
        test_cert_manager
        ;;
    emulators)
        test_emulators_quick
        ;;
    workloads)
        test_workloads_quick
        ;;
    networking)
        test_networking
        ;;
    security)
        test_security_quick
        ;;
    all)
        test_flux
        test_emulators_quick
        test_workloads_quick
        test_networking
        test_security_quick
        ;;
    *)
        echo "Usage: $0 {flux|cert-manager|emulators|workloads|networking|security|all}"
        exit 1
        ;;
esac

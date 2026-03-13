---
name: service-mesh
description: >
  Use this skill to install, configure, and operate a service mesh (Istio or
  Linkerd) across Kubernetes clusters. Triggers: any request to enable mTLS
  between services, configure traffic management (canary, circuit breaker,
  retries, timeouts), set up mutual TLS enforcement, generate a service
  dependency map, debug inter-service connectivity, configure observability
  through the mesh, or enforce zero-trust service-to-service communication.
tools:
  - bash
  - computer
---

# Service Mesh Skill

Deploy and operate a production service mesh with mTLS, traffic policies,
observability, and zero-trust service identity — using Istio (default) or
Linkerd.

---

## Installation

### Istio (Production Profile)
```bash
# Install Istio with production profile
istioctl install --set profile=production \
  --set values.global.proxy.resources.requests.cpu=100m \
  --set values.global.proxy.resources.requests.memory=128Mi \
  --set values.global.proxy.resources.limits.cpu=500m \
  --set values.global.proxy.resources.limits.memory=256Mi \
  -y

# Verify installation
istioctl verify-install

# Label namespace for sidecar injection
kubectl label namespace "${TENANT_NAMESPACE}" istio-injection=enabled
```

### Linkerd (lightweight alternative)
```bash
linkerd install --crds | kubectl apply -f -
linkerd install | kubectl apply -f -
linkerd viz install | kubectl apply -f -
linkerd check

# Annotate namespace for injection
kubectl annotate namespace "${TENANT_NAMESPACE}" \
  linkerd.io/inject=enabled
```

---

## mTLS Enforcement (Zero-Trust)

```yaml
# Enforce STRICT mTLS in a namespace — all traffic must be encrypted + authenticated
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: ${TENANT_NAMESPACE}
spec:
  mtls:
    mode: STRICT
---
# Deny all traffic not using mTLS
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: deny-all
  namespace: ${TENANT_NAMESPACE}
spec:
  {} # empty spec = deny all
---
# Allow specific service-to-service communication
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-api-to-db
  namespace: ${TENANT_NAMESPACE}
spec:
  selector:
    matchLabels:
      app: database-proxy
  rules:
    - from:
        - source:
            principals:
              - cluster.local/ns/${TENANT_NAMESPACE}/sa/api-service
      to:
        - operation:
            ports: ["5432"]
```

---

## Traffic Management

### Canary Deployment via VirtualService
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: ${APP_NAME}
  namespace: ${TENANT_NAMESPACE}
spec:
  hosts:
    - ${APP_NAME}
  http:
    - route:
        - destination:
            host: ${APP_NAME}
            subset: stable
          weight: 90
        - destination:
            host: ${APP_NAME}
            subset: canary
          weight: 10
---
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: ${APP_NAME}
  namespace: ${TENANT_NAMESPACE}
spec:
  host: ${APP_NAME}
  subsets:
    - name: stable
      labels:
        version: stable
    - name: canary
      labels:
        version: canary
```

### Circuit Breaker
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: ${APP_NAME}-circuit-breaker
  namespace: ${TENANT_NAMESPACE}
spec:
  host: ${APP_NAME}
  trafficPolicy:
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 100
        http2MaxRequests: 1000
```

### Retry & Timeout Policy
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: ${APP_NAME}-resilience
spec:
  hosts:
    - ${APP_NAME}
  http:
    - timeout: 5s
      retries:
        attempts: 3
        perTryTimeout: 2s
        retryOn: gateway-error,connect-failure,retriable-4xx
      route:
        - destination:
            host: ${APP_NAME}
```

---

## Observability via Mesh

```bash
# Install Kiali (service topology dashboard)
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/kiali.yaml

# View service graph
istioctl dashboard kiali &

# Envoy proxy stats for a pod
istioctl proxy-status
istioctl proxy-config cluster "${POD_NAME}.${NAMESPACE}"

# Per-service traffic metrics via Prometheus
# Request rate
sum(rate(istio_requests_total{destination_service="${APP_NAME}.${NAMESPACE}.svc.cluster.local"}[5m]))

# Error rate
sum(rate(istio_requests_total{
  destination_service="${APP_NAME}.${NAMESPACE}.svc.cluster.local",
  response_code=~"5.."
}[5m])) /
sum(rate(istio_requests_total{
  destination_service="${APP_NAME}.${NAMESPACE}.svc.cluster.local"
}[5m]))

# P99 latency
histogram_quantile(0.99,
  sum(rate(istio_request_duration_milliseconds_bucket{
    destination_service="${APP_NAME}.${NAMESPACE}.svc.cluster.local"
  }[5m])) by (le)
)
```

---

## Service Dependency Map

```bash
# Generate service dependency graph
kubectl get serviceentries,virtualservices,destinationrules -A -o json | \
  jq -r '.items[] | "\(.metadata.namespace)/\(.metadata.name): \(.spec.hosts[]?)"'

# Kiali API — get service graph as JSON
curl -s "http://kiali:20001/kiali/api/namespaces/${NAMESPACE}/graph?duration=5m" | \
  jq '.elements.nodes[] | {id: .data.id, service: .data.service, workload: .data.workload}'
```

---

## Debugging Inter-Service Connectivity

```bash
# Check if sidecar is injected
kubectl get pod "${POD_NAME}" -n "${NAMESPACE}" \
  -o jsonpath='{.spec.containers[*].name}'

# Proxy configuration analysis
istioctl analyze -n "${NAMESPACE}"

# Test connectivity through mesh
kubectl exec "${SOURCE_POD}" -n "${SOURCE_NS}" \
  -c istio-proxy -- curl -sv \
  "http://${DEST_SERVICE}.${DEST_NS}.svc.cluster.local/health" 2>&1

# Envoy access logs for debugging
kubectl logs "${POD_NAME}" -n "${NAMESPACE}" -c istio-proxy | \
  grep -E "\"[0-9]{3}\"" | tail -20

# Check mTLS is active between two services
istioctl authn tls-check "${SOURCE_POD}.${SOURCE_NS}" \
  "${DEST_SERVICE}.${DEST_NS}.svc.cluster.local"
```

---

## Examples

- "Enable mTLS and strict PeerAuthentication for the tenant-42 namespace"
- "Set up a canary split: 10% traffic to payments-api v2.3.1"
- "Configure circuit breaker for the inventory service — it keeps cascading"
- "Show me the service dependency map for the order processing namespace"
- "Why is the cart service returning 503s when calling the pricing service?"
- "Install Istio on the new production cluster with production profile"

---

## Output Format

```json
{
  "operation": "install|mtls|traffic|circuit-breaker|debug|map",
  "namespace": "string",
  "app": "string",
  "mtls_mode": "STRICT|PERMISSIVE|DISABLED",
  "canary_weight": 0,
  "status": "success|failure",
  "connectivity": "OK|BLOCKED|DEGRADED",
  "issues": []
}
```

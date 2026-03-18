# Component Configuration Guide for Centralized K8sGPT
# This document shows how different components should integrate with the unified K8sGPT service

## Service Discovery

All components should use the centralized K8sGPT service at:
```
http://k8sgpt.k8sgpt-system.svc.cluster.local:8080
```

Metrics endpoint:
```
http://k8sgpt.k8sgpt-system.svc.cluster.local:9090/metrics
```

## Component Integration Patterns

### 1. Argo Workflows Integration

Update Argo Workflows to use centralized K8sGPT:

```yaml
# argo-workflows-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argo-workflows-config
  namespace: argo-workflows
data:
  config: |
    containerRuntimeExecutor: pns
    k8sGPT:
      enabled: true
      serverURL: "http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
      apiKey: ""
      model: "qwen2.5-7b-instruct"
      backend: "agent-memory"
      analysisInterval: "5m"
      namespaces: ["argo-workflows", "default", "production"]
```

### 2. Argo Rollouts Integration

Update Argo Rollouts analysis templates:

```yaml
# rollouts-analysis-template.yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: k8sgpt-analysis
  namespace: argo-rollouts
spec:
  args:
  - name: service-name
  - name: namespace
  metrics:
  - name: k8sgpt-health-analysis
    interval: 5m
    count: 3
    provider:
      k8sGPT:
        address: "http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
        resources:
          - name: "{{args.service-name}}"
            namespace: "{{args.namespace}}"
        analysisType: "health"
        severity: "medium"
```

### 3. Flux CD Integration

Update Flux Kustomizations to use centralized K8sGPT:

```yaml
# flux-kustomization-patch.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: apps
  namespace: flux-system
spec:
  healthChecks:
  - apiVersion: apps/v1
    kind: Deployment
    name: k8sgpt
    namespace: k8sgpt-system
  postBuild:
    substitute:
      K8SGPT_ENDPOINT: "http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
    substituteFrom:
    - kind: ConfigMap
      name: k8sgpt-config
      namespace: k8sgpt-system
```

### 4. Argo Events Integration

Update Argo Events sensors to use centralized K8sGPT:

```yaml
# argo-events-sensor.yaml
apiVersion: argoproj.io/v1alpha1
kind: Sensor
metadata:
  name: k8sgpt-analysis-sensor
  namespace: argo-events
spec:
  dependencies:
  - name: k8sgpt-trigger
    eventSourceName: webhook
    eventName: analyze
  triggers:
  - template:
      name: k8sgpt-analysis-workflow
      k8s:
        operation: create
        source:
          resource:
            apiVersion: argoproj.io/v1alpha1
            kind: Workflow
            metadata:
              generateName: k8sgpt-analysis-
            spec:
              entrypoint: analyze-with-k8sgpt
              arguments:
                parameters:
                - name: k8sgpt-endpoint
                  value: "http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
```

### 5. PipeCD Integration

Update PipeCD configuration to use centralized K8sGPT:

```yaml
# pipecd-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: pipecd-config
  namespace: pipecd
data:
  pipecd.yaml: |
    analysis:
      k8sgpt:
        enabled: true
        endpoint: "http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
        timeout: "30s"
        retry: 3
        metrics:
          - name: deployment-health
            interval: "5m"
            query: "deployment health issues"
```

## Environment Variables for Components

All components should use these standard environment variables:

```bash
# K8sGPT Service Configuration
K8SGPT_ENDPOINT="http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
K8SGPT_METRICS_ENDPOINT="http://k8sgpt.k8sgpt-system.svc.cluster.local:9090/metrics"
K8SGPT_TIMEOUT="30s"
K8SGPT_RETRY="3"

# Analysis Configuration
K8SGPT_MODEL="qwen2.5-7b-instruct"
K8SGPT_BACKEND="agent-memory"
K8SGPT_TEMPERATURE="0.7"
K8SGPT_MAX_TOKENS="2048"

# Authentication (if needed)
K8SGPT_API_KEY=""
K8SGPT_AUTH_TYPE="none"  # none, jwt, token
```

## Service Account and RBAC

Components that need to interact with K8sGPT should have appropriate permissions:

```yaml
# component-service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{component-name}}-sa
  namespace: {{component-namespace}}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {{component-name}}-k8sgpt-role
  namespace: {{component-namespace}}
rules:
- apiGroups: [""]
  resources: ["services", "endpoints"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
  resourceNames: ["k8sgpt-config", "k8sgpt-secrets"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: {{component-name}}-k8sgpt-binding
  namespace: {{component-namespace}}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: {{component-name}}-k8sgpt-role
subjects:
- kind: ServiceAccount
  name: {{component-name}}-sa
  namespace: {{component-namespace}}
```

## Network Policies

Ensure network policies allow access to K8sGPT:

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-k8sgpt-access
  namespace: k8sgpt-system
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: k8sgpt
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: argo-workflows
    - namespaceSelector:
        matchLabels:
          name: argo-rollouts
    - namespaceSelector:
        matchLabels:
          name: flux-system
    - namespaceSelector:
        matchLabels:
          name: argo-events
    - namespaceSelector:
        matchLabels:
          name: pipecd
    ports:
    - protocol: TCP
      port: 8080
    - protocol: TCP
      port: 9090
```

## Migration Steps

For each component:

1. **Update Configuration**: Change K8sGPT endpoint to centralized service
2. **Remove Local Deployment**: Delete component-specific K8sGPT deployments
3. **Update RBAC**: Ensure proper permissions to access centralized service
4. **Update Network Policies**: Allow traffic to k8sgpt-system namespace
5. **Test Integration**: Verify component can communicate with centralized K8sGPT
6. **Monitor**: Check logs and metrics to ensure proper operation

## Monitoring Integration

Components should monitor K8sGPT health and performance:

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: k8sgpt-metrics
  namespace: k8sgpt-system
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: k8sgpt
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

## Troubleshooting

Common issues and solutions:

1. **Connection Refused**: Check network policies and service endpoints
2. **Authentication Errors**: Verify API keys and service account permissions
3. **Timeout Issues**: Increase timeout values or check K8sGPT health
4. **Missing Analysis Results**: Verify backend configuration and model availability

## Testing Integration

Test script to verify component integration:

```bash
#!/bin/bash
# test-k8sgpt-integration.sh

K8SGPT_ENDPOINT="http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"

echo "Testing K8sGPT integration..."

# Test health endpoint
echo "Testing health endpoint..."
curl -f "$K8SGPT_ENDPOINT/healthz" || exit 1

# Test metrics endpoint
echo "Testing metrics endpoint..."
curl -f "$K8SGPT_ENDPOINT:9090/metrics" || exit 1

# Test analysis endpoint
echo "Testing analysis endpoint..."
curl -X POST "$K8SGPT_ENDPOINT/analyze" \
  -H "Content-Type: application/json" \
  -d '{"namespace":"default","resources":["deployments"]}' || exit 1

echo "All tests passed!"
```

This guide ensures all components properly integrate with the centralized K8sGPT service while maintaining the single-instance-per-cluster principle.

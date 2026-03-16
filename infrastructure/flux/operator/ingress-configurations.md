# Flux Status Page Ingress Configuration

This directory contains Ingress configurations for external access to the Flux Status Page.

## Basic Ingress Configuration

### Basic HTTP Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flux-ui-ingress
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
spec:
  ingressClassName: nginx
  rules:
  - host: flux-ui.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: flux-operator
            port:
              number: 9080
```

### TLS Ingress with Cert-Manager

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flux-ui-ingress
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - flux-ui.example.com
    secretName: flux-ui-tls
  rules:
  - host: flux-ui.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: flux-operator
            port:
              number: 9080
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: flux-ui-tls
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  secretName: flux-ui-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - flux-ui.example.com
```

### Ingress with Authentication

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flux-ui-ingress
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/auth-type: basic
    nginx.ingress.kubernetes.io/auth-secret: flux-ui-auth
    nginx.ingress.kubernetes.io/auth-realm: "Flux Status Page Authentication"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - flux-ui.example.com
    secretName: flux-ui-tls
  rules:
  - host: flux-ui.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: flux-operator
            port:
              number: 9080
---
apiVersion: v1
kind: Secret
metadata:
  name: flux-ui-auth
  namespace: flux-system
  type: Opaque
data:
  # username: admin, password: [REPLACE_WITH_SECURE_PASSWORD] (base64 encoded)
  auth: [REPLACE_WITH_BASE64_ENCODED_CREDENTIALS]
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: flux-ui-tls
  namespace: flux-system
spec:
  secretName: flux-ui-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - flux-ui.example.com
```

### Ingress with OIDC Authentication

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flux-ui-ingress
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/auth-url: "https://oauth.example.com/oauth2/auth"
    nginx.ingress.kubernetes.io/auth-signin: "https://oauth.example.com/oauth2/start?rd=https://$host$request_uri"
    nginx.ingress.kubernetes.io/auth-response-headers: "Authorization"
    nginx.ingress.kubernetes.io/proxy-buffering: "on"
    nginx.ingress.kubernetes.io/proxy-buffer-size: "8k"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - flux-ui.example.com
    secretName: flux-ui-tls
  rules:
  - host: flux-ui.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: flux-operator
            port:
              number: 9080
```

## Advanced Ingress Configurations

### Multi-Path Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flux-ui-ingress
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - gitops.example.com
    secretName: flux-ui-tls
  rules:
  - host: gitops.example.com
    http:
      paths:
      - path: /flux(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: flux-operator
            port:
              number: 9080
```

### Load Balancer Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: flux-ui-lb
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
spec:
  type: LoadBalancer
  selector:
    app.kubernetes.io/name: flux
  ports:
  - name: http
    port: 80
    targetPort: 9080
    protocol: TCP
  - name: https
    port: 443
    targetPort: 9080
    protocol: TCP
```

### Istio Gateway

```yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: flux-ui-gateway
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - flux-ui.example.com
  - port:
      number: 443
      name: https
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: flux-ui-tls
    hosts:
    - flux-ui.example.com
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: flux-ui-vs
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  hosts:
  - flux-ui.example.com
  gateways:
  - flux-ui-gateway
  http:
  - match:
    - uri:
        prefix: /
    route:
    - destination:
        host: flux-operator
        port:
          number: 9080
```

## Ingress Controller Setup

### NGINX Ingress Controller

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: gitops-infra-control-plane
---
apiVersion: helm.cattle.io/v1
kind: HelmChart
metadata:
  name: ingress-nginx
  namespace: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  repo: https://kubernetes.github.io/ingress-nginx
  chart: ingress-nginx
  version: "4.7.0"
  bootstrap: true
  values:
    controller:
      replicaCount: 2
      service:
        type: LoadBalancer
        externalTrafficPolicy: Local
        annotations:
          service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
      config:
        use-forwarded-headers: "true"
        compute-full-forwarded-for: "true"
        proxy-buffer-size: "16k"
        client-max-body-size: "10m"
        proxy-read-timeout: "300"
        proxy-send-timeout: "300"
        ssl-protocols: "TLSv1.2 TLSv1.3"
      resources:
        requests:
          cpu: 100m
          memory: 128Mi
        limits:
          cpu: 500m
          memory: 512Mi
      metrics:
        enabled: true
        serviceMonitor:
          enabled: true
          namespace: ingress-nginx
      admissionWebhooks:
        enabled: true
        patch:
          enabled: true
```

### Cert-Manager Setup

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cert-manager
  labels:
    app.kubernetes.io/name: cert-manager
    app.kubernetes.io/part-of: gitops-infra-control-plane
---
apiVersion: helm.cattle.io/v1
kind: HelmChart
metadata:
  name: cert-manager
  namespace: cert-manager
  labels:
    app.kubernetes.io/name: cert-manager
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  repo: https://charts.jetstack.io
  chart: cert-manager
  version: "v1.12.0"
  bootstrap: true
  values:
    installCRDs: true
    replicaCount: 2
    resources:
      requests:
        cpu: 10m
        memory: 32Mi
      limits:
        cpu: 100m
        memory: 128Mi
    prometheus:
      enabled: true
      serviceMonitor:
        enabled: true
        namespace: cert-manager
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
  labels:
    app.kubernetes.io/name: cert-manager
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
  labels:
    app.kubernetes.io/name: cert-manager
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-staging
    solvers:
    - http01:
        ingress:
          class: nginx
```

## Security Configuration

### Security Headers

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flux-ui-ingress
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    # Security headers
    nginx.ingress.kubernetes.io/configuration-snippet: |
      more_set_headers "X-Content-Type-Options: nosniff";
      more_set_headers "X-Frame-Options: DENY";
      more_set_headers "X-XSS-Protection: 1; mode=block";
      more_set_headers "Strict-Transport-Security: max-age=31536000; includeSubDomains";
      more_set_headers "Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:;";
    # Rate limiting
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    # CORS
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-origin: "https://gitops.example.com"
    nginx.ingress.kubernetes.io/cors-allow-methods: "GET, POST, PUT, DELETE, OPTIONS"
    nginx.ingress.kubernetes.io/cors-allow-headers: "Authorization, Content-Type"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - flux-ui.example.com
    secretName: flux-ui-tls
  rules:
  - host: flux-ui.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: flux-operator
            port:
              number: 9080
```

### IP Whitelist

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flux-ui-ingress
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/whitelist-source-range: "10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
    nginx.ingress.kubernetes.io/denylist-source-range: "0.0.0.0/8"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - flux-ui.example.com
    secretName: flux-ui-tls
  rules:
  - host: flux-ui.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: flux-operator
            port:
              number: 9080
```

## Monitoring and Observability

### Ingress Monitoring

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: nginx-ingress-controller
  namespace: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: ingress-nginx
      app.kubernetes.io/component: controller
  endpoints:
  - port: prometheus
    interval: 30s
    path: /metrics
---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: nginx-ingress-alerts
  namespace: ingress-nginx
  labels:
    app.kubernetes.io/name: ingress-nginx
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  groups:
  - name: nginx-ingress
    rules:
    - alert: NginxIngressControllerDown
      expr: up{job="nginx-ingress-controller"} == 0
      for: 5m
      labels:
        severity: critical
        app: nginx-ingress
      annotations:
        summary: "NGINX Ingress Controller is down"
        description: "NGINX Ingress Controller has been down for more than 5 minutes"
    - alert: NginxIngressHighErrorRate
      expr: rate(nginx_ingress_controller_requests{status=~"5.."}[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
        app: nginx-ingress
      annotations:
        summary: "NGINX Ingress Controller high error rate"
        description: "NGINX Ingress Controller error rate is {{ $value }} errors per second"
```

### Ingress Dashboard

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-ingress-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  nginx-ingress.json: |
    {
      "dashboard": {
        "title": "NGINX Ingress Controller",
        "panels": [
          {
            "title": "Request Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(nginx_ingress_controller_requests[5m])",
                "legendFormat": "{{host}}"
              }
            ]
          },
          {
            "title": "Response Time",
            "type": "graph",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, rate(nginx_ingress_controller_request_duration_seconds_bucket[5m]))",
                "legendFormat": "95th percentile"
              }
            ]
          },
          {
            "title": "Error Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(nginx_ingress_controller_requests{status=~\"5..\"}[5m])",
                "legendFormat": "5xx errors"
              }
            ]
          }
        ]
      }
    }
```

## Troubleshooting

### Common Issues

#### 1. Ingress Not Working

```bash
# Check Ingress status
kubectl get ingress -n flux-system

# Check Ingress controller
kubectl get pods -n ingress-nginx

# Check Ingress logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Test connectivity
curl -v -u [USERNAME]:[PASSWORD] http://flux-ui.local
```

#### 2. TLS Certificate Issues

```bash
# Check certificate status
kubectl get certificate -n flux-system

# Check certificate details
kubectl describe certificate flux-ui-tls -n flux-system

# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager
```

#### 3. Authentication Issues

```bash
# Check auth secret
kubectl get secret flux-ui-auth -n flux-system -o yaml

# Test basic auth
curl -v -u {{USERNAME}}:{{PASSWORD}} http://flux-ui.local

# Check Ingress annotations
kubectl get ingress flux-ui-ingress -n flux-system -o yaml
```

### Debug Commands

```bash
# Get Ingress details
kubectl describe ingress flux-ui-ingress -n flux-system

# Check service endpoints
kubectl get endpoints flux-operator -n flux-system

# Check DNS resolution
nslookup flux-ui.local

# Test with curl
curl -v -H "Host: flux-ui.local" http://<ingress-ip>

# Check NGINX configuration
kubectl exec -n ingress-nginx deployment/ingress-nginx-controller -- nginx -T
```

## Best Practices

1. **Use TLS**: Always enable HTTPS with valid certificates
2. **Implement Authentication**: Use SSO or basic auth for security
3. **Monitor Ingress**: Set up monitoring and alerting
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Security Headers**: Add security headers for protection
6. **Backup Configuration**: Version control all Ingress configurations
7. **Test Failover**: Test Ingress controller failover scenarios
8. **Document Access**: Maintain documentation for access procedures

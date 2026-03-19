# Flux Status Page Complete Implementation Guide

This comprehensive guide covers the complete implementation of the Flux Status Page for the GitOps Infra Control Plane, including setup, configuration, authentication, user management, and best practices.

## Overview

The Flux Status Page is a lightweight, mobile-friendly web interface that provides real-time visibility into your GitOps pipelines. It's embedded directly within the Flux Operator and requires no additional installation beyond the base setup.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Authentication and SSO](#authentication-and-sso)
5. [User Management](#user-management)
6. [Ingress and External Access](#ingress-and-external-access)
7. [Monitoring and Observability](#monitoring-and-observability)
8. [Security Best Practices](#security-best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Features](#advanced-features)

## Quick Start

### Prerequisites

- Kubernetes cluster v1.24 or later
- Flux Operator installed
- kubectl configured to access the cluster
- Administrative privileges on the cluster

### One-Command Setup

```bash
# Install Flux Status Page with all features
./core/core/automation/ci-cd/scripts/setup-flux-status-page.sh

# Set up SSO and authentication
./core/core/automation/ci-cd/scripts/setup-flux-sso.sh

# Access the UI locally
kubectl -n flux-system port-forward svc/flux-operator 9080:9080
# Then open http://localhost:9080
```

## Installation

### Basic Installation

```bash
# Run the setup script
./core/core/automation/ci-cd/scripts/setup-flux-status-page.sh
```

This script will:

- Create the Flux Status Page service
- Configure monitoring and alerting
- Set up RBAC permissions
- Create network policies
- Test local access

### Manual Installation

```bash
# Create the service
kubectl apply -f flux-operator/flux-ui-service.yaml

# Create configuration
kubectl apply -f flux-operator/flux-ui-config.yaml

# Create monitoring
kubectl apply -f flux-operator/flux-ui-monitoring.yaml

# Create RBAC
kubectl apply -f flux-operator/flux-ui-rbac.yaml

# Create network policies
kubectl apply -f flux-operator/flux-ui-networkpolicy.yaml
```

### Verification

```bash
# Check service status
kubectl get svc flux-operator -n flux-system

# Check pods
kubectl get pods -n flux-system -l app.kubernetes.io/name=flux

# Test local access
kubectl -n flux-system port-forward svc/flux-operator 9080:9080 &
curl -s http://localhost:9080/health
```

## Configuration

### Basic Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-config
  namespace: flux-system
data:
  config.yaml: |
    ui:
      title: "GitOps Infra Control Plane"
      logo: "/static/logo.png"
      theme: "light"
      refreshInterval: "30s"
      
    cluster:
      name: "production"
      description: "Production GitOps Infrastructure"
      
    features:
      favorites: true
      search: true
      graphs: true
      history: true
      sso: true
      
    filters:
      namespaces:
        include: ["flux-system", "production", "staging"]
        exclude: ["kube-system", "kube-public"]
      labels:
        include: ["app.kubernetes.io/part-of=agentic-reconciliation-engine"]
        
    dashboards:
      cluster:
        enabled: true
        refreshInterval: "30s"
        showControllers: true
        showStats: true
        showActivity: true
        
      workloads:
        enabled: true
        groupBy: "namespace"
        showHealth: true
        showReplicas: true
        
      helm:
        enabled: true
        showHistory: true
        showValues: true
        showConditions: true
        
      sources:
        enabled: true
        showArtifacts: true
        showRevisions: true
```

### Advanced Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-advanced-config
  namespace: flux-system
data:
  advanced-config.yaml: |
    # Performance tuning
    performance:
      cacheSize: 1000
      cacheTTL: "5m"
      maxConcurrentRequests: 10
      requestTimeout: "30s"
      
    # Search configuration
    search:
      enabled: true
      maxResults: 50
      indexFields: ["name", "namespace", "kind", "labels"]
      fuzzySearch: true
      
    # Favorites configuration
    favorites:
      enabled: true
      maxFavorites: 20
      autoCleanup: true
      syncAcrossSessions: true
      
    # Graph configuration
    graph:
      enabled: true
      layout: "hierarchical"
      showConditions: true
      showDependencies: true
      maxDepth: 5
      autoRefresh: true
      
    # History configuration
    history:
      enabled: true
      maxEntries: 100
      retention: "7d"
      compression: true
      
    # Export configuration
    export:
      enabled: true
      formats: ["json", "yaml", "csv"]
      maxExportSize: "10MB"
      
    # Notifications
    notifications:
      enabled: true
      webhook: "${WEBHOOK_URL}"
      email:
        enabled: false
        smtp: "${SMTP_SERVER}"
        from: "${FROM_EMAIL}"
      
    # API configuration
    api:
      enabled: true
      rateLimit: 100
      cors:
        enabled: true
        origins: ["https://gitops.example.com"]
      versioning: true
```

## Authentication and SSO

### Basic Authentication

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flux-ui-ingress
  namespace: flux-system
  annotations:
    nginx.ingress.kubernetes.io/auth-type: basic
    nginx.ingress.kubernetes.io/auth-secret: flux-ui-auth
    nginx.ingress.kubernetes.io/auth-realm: "Flux Status Page Authentication"
spec:
  ingressClassName: nginx
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
  # username: admin, password: admin123 (base64 encoded)
  auth: YWRtaW46JGFwcjEkZlZkR2hJYkEka1p2L1FvV3JFZ2NkTjNOLgo=
```

### OIDC Authentication

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: flux-ui-oidc
  namespace: flux-system
type: Opaque
stringData:
  OIDC_ISSUER_URL: "https://dex.dex.svc.cluster.local:5556/dex"
  OIDC_CLIENT_ID: "flux-ui"
  OIDC_CLIENT_SECRET: "flux-ui-secret"
  OIDC_REDIRECT_URI: "https://flux-ui.example.com/oauth2/callback"
  OIDC_SCOPES: "openid,profile,email,groups"
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flux-ui-ingress
  namespace: flux-system
  annotations:
    nginx.ingress.kubernetes.io/auth-url: "https://oauth2-proxy.oauth2-proxy.svc.cluster.local:4180/oauth2/auth"
    nginx.ingress.kubernetes.io/auth-signin: "https://dex.example.com/auth?rd=https://$host$request_uri"
    nginx.ingress.kubernetes.io/auth-response-headers: "Authorization,X-Auth-Request-Email,X-Auth-Request-User,X-Auth-Request-Groups"
spec:
  ingressClassName: nginx
  rules:
  - host: flux-ui.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: oauth2-proxy
            port:
              number: 4180
```

### SSO Setup

```bash
# Set up complete SSO with Dex and OAuth2 Proxy
./core/core/automation/ci-cd/scripts/setup-flux-sso.sh
```

This script will:

- Install Dex OIDC Provider
- Configure OAuth2 Proxy
- Set up user management
- Create SSO monitoring
- Test authentication flow

## User Management

### Role-Based Access Control

#### Admin Role

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: flux-ui-admin
rules:
- apiGroups: ["fluxcd.controlplane.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["source.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["kustomize.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["helm.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["image.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

#### Operator Role

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: flux-ui-operator
rules:
- apiGroups: ["fluxcd.controlplane.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: ["source.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: ["kustomize.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: ["helm.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: ["image.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "update", "patch"]
```

#### Viewer Role

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: flux-ui-viewer
rules:
- apiGroups: ["fluxcd.controlplane.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["source.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["kustomize.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["helm.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["image.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
```

### User Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-users
  namespace: flux-system
data:
  users.yaml: |
    users:
      - email: "admin@example.com"
        username: "admin"
        displayName: "Administrator"
        roles: ["admin"]
        groups: ["flux-admins"]
        enabled: true
      - email: "operator@example.com"
        username: "operator"
        displayName: "Operator"
        roles: ["operator"]
        groups: ["flux-operators"]
        enabled: true
      - email: "viewer@example.com"
        username: "viewer"
        displayName: "Viewer"
        roles: ["viewer"]
        groups: ["flux-viewers"]
        enabled: true
    
    groups:
      flux-admins:
        description: "Flux administrators"
        members:
          - "admin@example.com"
        roles: ["admin"]
      
      flux-operators:
        description: "Flux operators"
        members:
          - "operator@example.com"
        roles: ["operator"]
      
      flux-viewers:
        description: "Flux viewers"
        members:
          - "viewer@example.com"
        roles: ["viewer"]
```

### Group-Based Access Control

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-group-mapping
  namespace: flux-system
data:
  group-mapping.yaml: |
    groupMapping:
      "flux-admins":
        roles: ["admin"]
        permissions: ["full_access"]
      
      "platform-admins":
        roles: ["admin"]
        permissions: ["full_access"]
      
      "devops-team":
        roles: ["operator"]
        permissions: ["operational_access"]
      
      "developers":
        roles: ["viewer"]
        permissions: ["read_only"]
      
      "qa-team":
        roles: ["viewer"]
        permissions: ["read_only"]
```

## Ingress and External Access

### Basic Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flux-ui-ingress
  namespace: flux-system
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
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

### Advanced Ingress with Security

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flux-ui-ingress
  namespace: flux-system
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
    # Performance
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
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

### Load Balancer Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: flux-ui-lb
  namespace: flux-system
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

## Monitoring and Observability

### Prometheus Monitoring

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: flux-ui
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: flux-operator
      app.kubernetes.io/component: ui
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: flux-ui-alerts
  namespace: flux-system
spec:
  groups:
  - name: flux-ui
    rules:
    - alert: FluxUIDown
      expr: up{job="flux-ui"} == 0
      for: 5m
      labels:
        severity: critical
        app: flux-ui
      annotations:
        summary: "Flux Status Page is down"
        description: "Flux Status Page has been down for more than 5 minutes"
    - alert: FluxUIHighErrorRate
      expr: rate(http_requests_total{job="flux-ui",status=~"5.."}[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
        app: flux-ui
      annotations:
        summary: "Flux Status Page high error rate"
        description: "Flux Status Page error rate is {{ $value }} errors per second"
    - alert: FluxUIHighLatency
      expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="flux-ui"}[5m])) > 1
      for: 5m
      labels:
        severity: warning
        app: flux-ui
      annotations:
        summary: "Flux Status Page high latency"
        description: "Flux Status Page 95th percentile latency is {{ $value }}s"
```

### Grafana Dashboard

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  flux-ui.json: |
    {
      "dashboard": {
        "title": "Flux Status Page Overview",
        "panels": [
          {
            "title": "Flux Status Page Uptime",
            "type": "stat",
            "targets": [
              {
                "expr": "up{job=\"flux-ui\"}",
                "legendFormat": "Uptime"
              }
            ]
          },
          {
            "title": "Request Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(http_requests_total{job=\"flux-ui\"}[5m])",
                "legendFormat": "{{method}} {{status}}"
              }
            ]
          },
          {
            "title": "Response Time",
            "type": "graph",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job=\"flux-ui\"}[5m]))",
                "legendFormat": "95th percentile"
              }
            ]
          },
          {
            "title": "Error Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(http_requests_total{job=\"flux-ui\",status=~\"5..\"}[5m])",
                "legendFormat": "5xx errors"
              }
            ]
          },
          {
            "title": "Active Users",
            "type": "stat",
            "targets": [
              {
                "expr": "flux_ui_active_users_total",
                "legendFormat": "Active Users"
              }
            ]
          },
          {
            "title": "Resource Views",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(flux_ui_resource_views_total[5m])",
                "legendFormat": "{{resource_type}}"
              }
            ]
          }
        ]
      }
    }
```

### Logging

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-logging
  namespace: flux-system
data:
  logging.yaml: |
    # Logging configuration
    logging:
      level: "info"
      format: "json"
      
      # Log outputs
      outputs:
        - type: "console"
          level: "info"
        - type: "file"
          path: "/var/log/flux-ui/app.log"
          level: "debug"
          maxsize: "100MB"
          maxfiles: 10
        - type: "syslog"
          facility: "local0"
          level: "info"
      
      # Log categories
      categories:
        "http":
          level: "info"
        "auth":
          level: "warn"
        "api":
          level: "info"
        "cache":
          level: "debug"
        "metrics":
          level: "info"
      
      # Structured logging
      structured:
        enabled: true
        fields:
          - "timestamp"
          - "level"
          - "component"
          - "request_id"
          - "user_id"
          - "duration"
          - "status"
      
      # Audit logging
      audit:
        enabled: true
        events:
          - "user_login"
          - "user_logout"
          - "resource_access"
          - "permission_denied"
          - "suspicious_activity"
        output: "/var/log/flux-ui/audit.log"
```

## Security Best Practices

### 1. Network Security

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: flux-ui-netpol
  namespace: flux-system
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: flux-operator
      app.kubernetes.io/component: ui
  policyTypes:
  - Ingress
  - Egress
  ingress:
  # Allow traffic from ingress controller
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 9080
  # Allow traffic from monitoring
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 9080
  # Allow intra-namespace traffic
  - from:
    - podSelector: {}
  egress:
  # Allow DNS
  - to: []
    ports:
    - protocol: UDP
      port: 53
  # Allow HTTPS to external services
  - to: []
    ports:
    - protocol: TCP
      port: 443
  # Allow Kubernetes API
  - to: []
    ports:
    - protocol: TCP
      port: 443
```

### 2. Pod Security

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: flux-ui-security
  namespace: flux-system
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: flux-ui
    image: ghcr.io/controlplaneio-fluxcd/flux-operator:latest
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
      volumeMounts:
      - name: tmp
        mountPath: /tmp
      - name: var-run
        mountPath: /var/run
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi
  volumes:
  - name: tmp
    emptyDir: {}
  - name: var-run
    emptyDir: {}
```

### 3. Secret Management

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: flux-ui-secrets
  namespace: flux-system
type: Opaque
stringData:
  # Use external secret management
  OIDC_CLIENT_SECRET: "your-oidc-client-secret"
  WEBHOOK_SECRET: "your-webhook-secret"
  ENCRYPTION_KEY: "your-encryption-key"
---
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: flux-system
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "flux-ui"
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: flux-ui-vault-secrets
  namespace: flux-system
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: flux-ui-secrets
    creationPolicy: Owner
  data:
  - secretKey: OIDC_CLIENT_SECRET
    remoteRef:
      key: flux-ui/oidc-client-secret
  - secretKey: WEBHOOK_SECRET
    remoteRef:
      key: flux-ui/webhook-secret
```

### 4. Compliance and Auditing

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-compliance
  namespace: flux-system
data:
  compliance.yaml: |
    # Compliance configuration
    compliance:
      # GDPR compliance
      gdpr:
        enabled: true
        dataRetention: "365d"
        rightToErasure: true
        consentManagement: true
      
      # SOX compliance
      sox:
        enabled: true
        auditLogging: true
        accessControl: true
        dataIntegrity: true
      
      # HIPAA compliance
      hipaa:
        enabled: false
        phiProtection: false
        auditLogging: true
      
      # PCI DSS compliance
      pci:
        enabled: false
        cardDataProtection: false
        networkSecurity: true
        accessControl: true
      
      # Audit configuration
      audit:
        enabled: true
        level: "detailed"
        retention: "7y"
        encryption: true
        integrity: true
        
      # Data protection
      dataProtection:
        encryptionAtRest: true
        encryptionInTransit: true
        keyRotation: "90d"
        backupEncryption: true
        
      # Access control
      accessControl:
        mfaRequired: true
        sessionTimeout: "8h"
        passwordPolicy:
          minLength: 12
          requireUppercase: true
          requireLowercase: true
          requireNumbers: true
          requireSymbols: true
          maxAge: "90d"
```

## Troubleshooting

### Common Issues

#### 1. UI Not Loading

```bash
# Check service status
kubectl get svc flux-operator -n flux-system

# Check pod logs
kubectl logs -n flux-system deployment/flux-operator

# Check port-forward
kubectl -n flux-system port-forward svc/flux-operator 9080:9080
curl -v http://localhost:9080/health
```

#### 2. Authentication Issues

```bash
# Check SSO configuration
kubectl get secret flux-ui-oidc -n flux-system -o yaml

# Check OAuth2 Proxy logs
kubectl logs -n oauth2-proxy deployment/oauth2-proxy

# Test OIDC flow
curl -v https://dex.example.com/.well-known/openid-configuration
```

#### 3. Permission Issues

```bash
# Check user permissions
kubectl auth can-i get fluxinstances --as=user@example.com

# Check role bindings
kubectl get clusterrolebinding | grep user@example.com

# Verify role definitions
kubectl describe clusterrole flux-ui-admin
```

#### 4. Performance Issues

```bash
# Check resource usage
kubectl top pods -n flux-system

# Check metrics
curl -s http://localhost:9080/metrics | grep http_requests

# Check logs for errors
kubectl logs -n flux-system deployment/flux-operator | grep -i error
```

### Debug Commands

```bash
# Comprehensive health check
kubectl get pods -n flux-system -o wide
kubectl get svc -n flux-system -o wide
kubectl get ingress -n flux-system -o wide

# Check Flux Operator status
kubectl get fluxinstance flux -n flux-system -o yaml

# Check authentication status
kubectl auth can-i --list --as=user@example.com

# Test connectivity
kubectl port-forward -n flux-system svc/flux-operator 9080:9080 &
PF_PID=$!
sleep 5
curl -v http://localhost:9080/health
curl -v http://localhost:9080/api/status
kill $PF_PID 2>/dev/null || true

# Check logs
kubectl logs -n flux-system deployment/flux-operator --tail=100
kubectl logs -n oauth2-proxy deployment/oauth2-proxy --tail=100
kubectl logs -n dex deployment/dex --tail=100
```

## Advanced Features

### 1. Multi-Cluster Support

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-multi-cluster
  namespace: flux-system
data:
  multi-cluster.yaml: |
    # Multi-cluster configuration
    clusters:
      - name: "production"
        endpoint: "https://prod-k8s.example.com"
        kubeconfig: "/etc/kubeconfig/prod"
        description: "Production cluster"
        region: "us-west-2"
        environment: "production"
      - name: "staging"
        endpoint: "https://staging-k8s.example.com"
        kubeconfig: "/etc/kubeconfig/staging"
        description: "Staging cluster"
        region: "us-west-2"
        environment: "staging"
      - name: "development"
        endpoint: "https://dev-k8s.example.com"
        kubeconfig: "/etc/kubeconfig/dev"
        description: "Development cluster"
        region: "us-west-2"
        environment: "development"
    
    # Cluster switching
    clusterSwitching:
      enabled: true
      defaultCluster: "production"
      autoSwitch: false
      sessionPersistence: true
    
    # Cross-cluster visibility
    crossCluster:
      enabled: true
      aggregation: true
      comparison: true
      resourceSync: true
```

### 2. Custom Dashboards

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-custom-dashboards
  namespace: flux-system
data:
  custom-dashboards.yaml: |
    # Custom dashboard definitions
    dashboards:
      - name: "infrastructure-overview"
        title: "Infrastructure Overview"
        description: "Overview of all infrastructure resources"
        layout: "grid"
        widgets:
          - type: "metric"
            title: "Total Resources"
            query: "count(resources)"
            format: "number"
          - type: "chart"
            title: "Resource Distribution"
            query: "group_by_type(resources)"
            chartType: "pie"
          - type: "table"
            title: "Resource Status"
            query: "resource_status_summary"
            columns: ["name", "type", "status", "last_updated"]
      
      - name: "deployment-health"
        title: "Deployment Health"
        description: "Health status of all deployments"
        layout: "cards"
        widgets:
          - type: "health"
            title: "Overall Health"
            query: "deployment_health_summary"
          - type: "timeline"
            title: "Deployment History"
            query: "deployment_timeline"
          - type: "alerts"
            title: "Active Alerts"
            query: "active_alerts"
```

### 3. Plugin System

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-plugins
  namespace: flux-system
data:
  plugins.yaml: |
    # Plugin configuration
    plugins:
      - name: "slack-notifications"
        enabled: true
        config:
          webhook: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
          channel: "#gitops-alerts"
          username: "Flux UI"
          icon_emoji: ":flux:"
      
      - name: "github-integration"
        enabled: true
        config:
          token: "${GITHUB_TOKEN}"
          owner: "your-org"
          repo: "agentic-reconciliation-engine"
          autoCreateIssues: true
          autoCreatePRs: false
      
      - name: "jira-integration"
        enabled: false
        config:
          url: "https://your-domain.atlassian.net"
          username: "flux-bot@your-domain.com"
          token: "${JIRA_TOKEN}"
          project: "GITOPS"
      
      - name: "cost-analysis"
        enabled: true
        config:
          provider: "aws"
          region: "us-west-2"
          billingAccount: "123456789012"
          costCenter: "gitops"
      
      - name: "security-scanning"
        enabled: true
        config:
          trivy:
            enabled: true
            severity: "HIGH,CRITICAL"
            ignoreUnfixed: false
          falco:
            enabled: true
            rules: ["suspicious_activity"]
```

### 4. API Extensions

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-api-extensions
  namespace: flux-system
data:
  api-extensions.yaml: |
    # API extension configuration
    extensions:
      - name: "custom-endpoints"
        enabled: true
        endpoints:
          - path: "/api/v1/custom/metrics"
            method: "GET"
            handler: "customMetricsHandler"
            permissions: ["read"]
          - path: "/api/v1/custom/export"
            method: "POST"
            handler: "customExportHandler"
            permissions: ["read"]
          - path: "/api/v1/custom/import"
            method: "POST"
            handler: "customImportHandler"
            permissions: ["write"]
      
      - name: "webhooks"
        enabled: true
        webhooks:
          - name: "deployment-complete"
            url: "https://your-webhook.example.com/deployment-complete"
            events: ["deployment.completed"]
            secret: "webhook-secret"
          - name: "resource-failed"
            url: "https://your-webhook.example.com/resource-failed"
            events: ["resource.failed"]
            secret: "webhook-secret"
      
      - name: "middleware"
        enabled: true
        middleware:
          - name: "rate-limiting"
            config:
              requests: 100
              window: "1m"
              burst: 20
          - name: "caching"
            config:
              ttl: "5m"
              maxSize: 1000
          - name: "compression"
            config:
              enabled: true
              level: 6
```

## Migration and Upgrade

### From Basic UI to Full SSO

```bash
# Step 1: Backup current configuration
kubectl get configmap flux-ui-config -n flux-system -o yaml > flux-ui-config-backup.yaml
kubectl get secret flux-ui-secrets -n flux-system -o yaml > flux-ui-secrets-backup.yaml

# Step 2: Install SSO components
./core/core/automation/ci-cd/scripts/setup-flux-sso.sh

# Step 3: Update configuration
kubectl apply -f flux-operator/flux-ui-sso-config.yaml

# Step 4: Update Ingress for SSO
kubectl apply -f flux-operator/flux-ui-sso-ingress.yaml

# Step 5: Verify migration
kubectl -n oauth2-proxy port-forward svc/oauth2-proxy 4180:4180 &
curl -v http://localhost:4180/oauth2/auth
```

### Upgrade Flux Operator

```bash
# Step 1: Backup current state
kubectl get fluxinstance flux -n flux-system -o yaml > flux-instance-backup.yaml

# Step 2: Upgrade Flux Operator
flux-operator upgrade --version=latest

# Step 3: Update UI configuration
kubectl apply -f flux-operator/flux-ui-config.yaml

# Step 4: Verify upgrade
kubectl get fluxinstance flux -n flux-system -o yaml
kubectl get pods -n flux-system -l app.kubernetes.io/name=flux
```

## Conclusion

The Flux Status Page provides a comprehensive, secure, and user-friendly interface for monitoring and managing your GitOps infrastructure. With features like real-time visibility, advanced search, SSO integration, and comprehensive RBAC, it offers everything needed for effective GitOps operations.

### Key Benefits

1. **Real-Time Visibility**: Monitor all Flux resources in real-time
2. **User-Friendly Interface**: Mobile-friendly, responsive design
3. **Secure Access**: SSO integration and granular RBAC
4. **Advanced Features**: Search, favorites, graphs, and history
5. **Monitoring Integration**: Built-in Prometheus metrics and alerting
6. **Multi-Cluster Support**: Manage multiple clusters from one interface
7. **Extensible**: Plugin system and API extensions

### Next Steps

1. Deploy the Flux Status Page using the setup scripts
2. Configure authentication and user management
3. Set up monitoring and alerting
4. Customize dashboards and features
5. Integrate with existing tools and workflows

For more information and support, refer to the detailed documentation and community resources.

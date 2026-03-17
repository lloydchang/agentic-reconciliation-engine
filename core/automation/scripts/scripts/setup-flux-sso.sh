#!/bin/bash

# Flux Status Page SSO Setup Script
# This script configures SSO and authentication for the Flux Status Page

set -euxo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FLUX_NAMESPACE="flux-system"
OIDC_ISSUER_URL="https://your-oidc-provider.com"
OIDC_CLIENT_ID="flux-ui-client"
OIDC_CLIENT_SECRET="your-client-secret"
DEX_NAMESPACE="dex"
DEX_VERSION="v2.35.3"

echo -e "${BLUE}🔐 Flux Status Page SSO Setup Script${NC}"
echo "===================================="

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check kubectl connection
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

# Check Flux Status Page is installed
if ! kubectl get svc flux-operator -n $FLUX_NAMESPACE &> /dev/null; then
    echo -e "${RED}❌ Flux Status Page is not installed. Please run setup script first.${NC}"
    echo "Run: ./core/core/automation/ci-cd/scripts/setup-flux-status-page.sh"
    exit 1
fi

# Install Dex OIDC Provider
echo -e "${YELLOW}🚀 Installing Dex OIDC Provider...${NC}"

cat > dex-install.yaml << EOF
apiVersion: v1
kind: Namespace
metadata:
  name: $DEX_NAMESPACE
  labels:
    app.kubernetes.io/name: dex
    app.kubernetes.io/part-of: gitops-infra-control-plane
---
apiVersion: helm.cattle.io/v1
kind: HelmChart
metadata:
  name: dex
  namespace: $DEX_NAMESPACE
  labels:
    app.kubernetes.io/name: dex
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  repo: https://charts.dexidp.io
  chart: dex
  version: "$DEX_VERSION"
  bootstrap: true
  values:
    image:
      tag: "$DEX_VERSION"
    replicas: 2
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi
    config:
      issuer: https://dex.$DEX_NAMESPACE.svc.cluster.local:5556/dex
      storage:
        type: kubernetes
        config:
          inCluster: true
      web:
        http: 0.0.0.0:5556
      telemetry:
        http: 0.0.0.0:5558
      connectors:
      - type: oidc
        id: oidc
        name: OpenID Connect
        config:
          issuer: $OIDC_ISSUER_URL
          clientID: $OIDC_CLIENT_ID
          clientSecret: $OIDC_CLIENT_SECRET
          requestedScopes: ["openid", "profile", "email", "groups"]
      - type: github
        id: github
        name: GitHub
        config:
          clientID: \$GITHUB_CLIENT_ID
          clientSecret: \$GITHUB_CLIENT_SECRET
          orgs:
          - name: your-org
            teams:
              flux-admins:
              - flux-viewers
      staticClients:
      - id: flux-ui
        redirectURIs:
        - https://flux-ui.example.com/oauth2/callback
        name: 'Flux Status Page'
        secret: flux-ui-secret
      enablePasswordDB: true
      staticPasswords:
      - email: "admin@example.com"
        hash: "\$2a\$10\$2d2d2d2d2d2d2d2d2d2d2OZ1d7b4d8d8d8d8d8d8d8d8d8d8d8d8d8d8d8d8"
        username: admin
        userID: "08a8684b-87e1-409b-901e-6705df074c7a"
    ingress:
      enabled: true
      className: nginx
      hosts:
      - host: dex.$DEX_NAMESPACE.svc.cluster.local
        paths:
        - path: /
          pathType: Prefix
      tls:
      - hosts:
        - dex.$DEX_NAMESPACE.svc.cluster.local
        secretName: dex-tls
    service:
      type: ClusterIP
      ports:
      - name: http
        port: 5556
        protocol: TCP
      - name: telemetry
        port: 5558
        protocol: TCP
EOF

kubectl apply -f dex-install.yaml
echo -e "${GREEN}✅ Dex OIDC Provider installation started${NC}"

# Wait for Dex to be ready
echo -e "${YELLOW}⏳ Waiting for Dex to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=dex -n $DEX_NAMESPACE --timeout=300s

# Create OIDC configuration for Flux UI
echo -e "${YELLOW}⚙️  Creating OIDC configuration for Flux UI...${NC}"

cat > flux-ui-oidc.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: flux-ui-oidc
  namespace: $FLUX_NAMESPACE
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
type: Opaque
stringData:
  OIDC_ISSUER_URL: "https://dex.$DEX_NAMESPACE.svc.cluster.local:5556/dex"
  OIDC_CLIENT_ID: "flux-ui"
  OIDC_CLIENT_SECRET: "flux-ui-secret"
  OIDC_REDIRECT_URI: "https://flux-ui.example.com/oauth2/callback"
  OIDC_SCOPES: "openid,profile,email,groups"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-oidc-config
  namespace: $FLUX_NAMESPACE
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
data:
  oidc-config.yaml: |
    # OIDC Configuration for Flux Status Page
    oidc:
      enabled: true
      issuer: "https://dex.$DEX_NAMESPACE.svc.cluster.local:5556/dex"
      clientId: "flux-ui"
      clientSecret: "flux-ui-secret"
      redirectUri: "https://flux-ui.example.com/oauth2/callback"
      scopes:
        - "openid"
        - "profile"
        - "email"
        - "groups"
      # Token configuration
      token:
        expiresIn: "1h"
        refreshEnabled: true
        refreshExpiresIn: "24h"
      # User mapping
      userMapping:
        usernameField: "email"
        displayNameField: "name"
        groupsField: "groups"
        emailField: "email"
      # Role mapping
      roleMapping:
        admin:
          groups: ["flux-admins", "admin"]
          users: ["admin@example.com"]
        operator:
          groups: ["flux-operators"]
          users: []
        viewer:
          groups: ["flux-viewers"]
          users: []
      # Session configuration
      session:
        store: "cookie"
        cookie:
          name: "flux-ui-session"
          secure: true
          httpOnly: true
          sameSite: "strict"
          maxAge: "24h"
      # Security
      security:
        nonce: true
        state: true
        pkce: true
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dex-ingress
  namespace: $DEX_NAMESPACE
  labels:
    app.kubernetes.io/name: dex
    app.kubernetes.io/part-of: gitops-infra-control-plane
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - dex.example.com
    secretName: dex-tls
  rules:
  - host: dex.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: dex
            port:
              number: 5556
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: dex-tls
  namespace: $DEX_NAMESPACE
  labels:
    app.kubernetes.io/name: dex
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  secretName: dex-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - dex.example.com
EOF

kubectl apply -f flux-ui-oidc.yaml
echo -e "${GREEN}✅ OIDC configuration created${NC}"

# Create OAuth2 Proxy for authentication
echo -e "${YELLOW}🛡️  Creating OAuth2 Proxy...${NC}"

cat > oauth2-proxy.yaml << EOF
apiVersion: v1
kind: Namespace
metadata:
  name: oauth2-proxy
  labels:
    app.kubernetes.io/name: oauth2-proxy
    app.kubernetes.io/part-of: gitops-infra-control-plane
---
apiVersion: v1
kind: Secret
metadata:
  name: oauth2-proxy-secret
  namespace: oauth2-proxy
  labels:
    app.kubernetes.io/name: oauth2-proxy
    app.kubernetes.io/part-of: gitops-infra-control-plane
type: Opaque
stringData:
  cookie-secret: "OQnA5jJbR9l3wG2X8pZ4qV7sY1cT6nU0iK3mF8hE2dW5rY7zA1bC4vN6xQ9sP2t"
  client-id: "flux-ui"
  client-secret: "flux-ui-secret"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oauth2-proxy
  namespace: oauth2-proxy
  labels:
    app.kubernetes.io/name: oauth2-proxy
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  replicas: 2
  selector:
    matchLabels:
      app.kubernetes.io/name: oauth2-proxy
  template:
    metadata:
      labels:
        app.kubernetes.io/name: oauth2-proxy
        app.kubernetes.io/part-of: gitops-infra-control-plane
    spec:
      containers:
      - name: oauth2-proxy
        image: quay.io/oauth2-proxy/oauth2-proxy:v7.5.1
        args:
        - --provider=oidc
        - --provider-display-name="Dex OIDC"
        - --client-id=\$(CLIENT_ID)
        - --client-secret=\$(CLIENT_SECRET)
        - --oidc-issuer-url=https://dex.$DEX_NAMESPACE.svc.cluster.local:5556/dex
        - --redirect-url=https://flux-ui.example.com/oauth2/callback
        - --upstream=http://flux-operator.$FLUX_NAMESPACE.svc.cluster.local:9080
        - --http-address=0.0.0.0:4180
        - --email-domain=*
        - --cookie-secret=\$(COOKIE_SECRET)
        - --cookie-secure=true
        - --cookie-http-only=true
        - --cookie-samesite=strict
        - --cookie-expire=24h
        - --session-cookie-minimal=true
        - --pass-authorization-header=true
        - --pass-access-token=true
        - --pass-user-headers=true
        - --prefer-email-to-user=true
        - --oidc-groups-claim=groups
        - --skip-auth-regex=^/health|^/metrics|^/static
        - --silence-ping-logging=true
        env:
        - name: CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: oauth2-proxy-secret
              key: client-id
        - name: CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: oauth2-proxy-secret
              key: client-secret
        - name: COOKIE_SECRET
          valueFrom:
            secretKeyRef:
              name: oauth2-proxy-secret
              key: cookie-secret
        ports:
        - containerPort: 4180
          name: http
          protocol: TCP
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 256Mi
        livenessProbe:
          httpGet:
            path: /ping
            port: 4180
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ping
            port: 4180
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: oauth2-proxy
  namespace: oauth2-proxy
  labels:
    app.kubernetes.io/name: oauth2-proxy
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  selector:
    app.kubernetes.io/name: oauth2-proxy
  ports:
  - name: http
    port: 4180
    targetPort: 4180
    protocol: TCP
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flux-ui-oauth2-proxy
  namespace: oauth2-proxy
  labels:
    app.kubernetes.io/name: oauth2-proxy
    app.kubernetes.io/part-of: gitops-infra-control-plane
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/auth-signin: "https://dex.example.com/auth?rd=https://\$host\$request_uri"
    nginx.ingress.kubernetes.io/auth-url: "https://oauth2-proxy.oauth2-proxy.svc.cluster.local:4180/oauth2/auth"
    nginx.ingress.kubernetes.io/auth-response-headers: "Authorization,X-Auth-Request-Email,X-Auth-Request-User,X-Auth-Request-Groups"
    nginx.ingress.kubernetes.io/auth-snippet: |
      proxy_set_header X-Auth-Request-Redirect \$scheme://\$http_host\$request_uri;
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
      - path: /oauth2
        pathType: Prefix
        backend:
          service:
            name: oauth2-proxy
            port:
              number: 4180
      - path: /
        pathType: Prefix
        backend:
          service:
            name: oauth2-proxy
            port:
              number: 4180
EOF

kubectl apply -f oauth2-proxy.yaml
echo -e "${GREEN}✅ OAuth2 Proxy created${NC}"

# Wait for OAuth2 Proxy to be ready
echo -e "${YELLOW}⏳ Waiting for OAuth2 Proxy to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=oauth2-proxy -n oauth2-proxy --timeout=300s

# Create user management configuration
echo -e "${YELLOW}👥 Creating user management configuration...${CN}"

cat > user-management.yaml << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-users
  namespace: $FLUX_NAMESPACE
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
data:
  users.yaml: |
    # User management configuration for Flux Status Page
    
    # Default users
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
    
    # Role definitions
    roles:
      admin:
        description: "Full administrative access"
        permissions:
          - "read"
          - "write"
          - "delete"
          - "reconcile"
        resources:
          - "fluxinstances"
          - "resourcesets"
          - "kustomizations"
          - "helmreleases"
          - "gitrepositories"
          - "ocirepositories"
          - "buckets"
          - "imagerepositories"
          - "imagepolicies"
          - "imageupdateautomations"
      
      operator:
        description: "Operator access with reconciliation capabilities"
        permissions:
          - "read"
          - "reconcile"
        resources:
          - "fluxinstances"
          - "resourcesets"
          - "kustomizations"
          - "helmreleases"
          - "gitrepositories"
          - "ocirepositories"
          - "buckets"
      
      viewer:
        description: "Read-only access"
        permissions:
          - "read"
        resources:
          - "*"
    
    # Group definitions
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
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: flux-ui-admin
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
rules:
# Flux resources
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
# Kubernetes resources
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets", "events"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "daemonsets", "statefulsets"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
# RBAC
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["roles", "rolebindings", "clusterroles", "clusterrolebindings"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: flux-ui-operator
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
rules:
# Flux resources
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
# Kubernetes resources
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets", "events"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "daemonsets", "statefulsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: flux-ui-viewer
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
rules:
# Flux resources
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
# Kubernetes resources
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets", "events"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "daemonsets", "statefulsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: flux-ui-admin-binding
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: flux-ui-admin
subjects:
- kind: ServiceAccount
  name: flux-ui
  namespace: $FLUX_NAMESPACE
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: flux-ui-operator-binding
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: flux-ui-operator
subjects:
- kind: ServiceAccount
  name: flux-ui
  namespace: $FLUX_NAMESPACE
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: flux-ui-viewer-binding
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: flux-ui-viewer
subjects:
- kind: ServiceAccount
  name: flux-ui
  namespace: $FLUX_NAMESPACE
EOF

kubectl apply -f user-management.yaml
echo -e "${GREEN}✅ User management configuration created${NC}"

# Create monitoring for SSO components
echo -e "${YELLOW}📊 Creating SSO monitoring configuration...${CN}"

cat > sso-monitoring.yaml << EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: dex
  namespace: $DEX_NAMESPACE
  labels:
    app.kubernetes.io/name: dex
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: dex
  endpoints:
  - port: telemetry
    path: /metrics
    interval: 30s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: oauth2-proxy
  namespace: oauth2-proxy
  labels:
    app.kubernetes.io/name: oauth2-proxy
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: oauth2-proxy
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: sso-alerts
  namespace: $FLUX_NAMESPACE
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  groups:
  - name: sso
    rules:
    - alert: DexDown
      expr: up{job="dex"} == 0
      for: 5m
      labels:
        severity: critical
        app: dex
      annotations:
        summary: "Dex OIDC Provider is down"
        description: "Dex OIDC Provider has been down for more than 5 minutes"
    - alert: OAuth2ProxyDown
      expr: up{job="oauth2-proxy"} == 0
      for: 5m
      labels:
        severity: critical
        app: oauth2-proxy
      annotations:
        summary: "OAuth2 Proxy is down"
        description: "OAuth2 Proxy has been down for more than 5 minutes"
    - alert: SSOHighErrorRate
      expr: rate(http_requests_total{job=~"dex|oauth2-proxy",status=~"5.."}[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
        app: sso
      annotations:
        summary: "SSO component high error rate"
        description: "SSO component error rate is {{ $value }} errors per second"
EOF

kubectl apply -f sso-monitoring.yaml
echo -e "${GREEN}✅ SSO monitoring configuration created${NC}"

# Test SSO setup
echo -e "${YELLOW}🧪 Testing SSO setup...${CN}"

# Wait for all components to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=dex -n $DEX_NAMESPACE --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=oauth2-proxy -n oauth2-proxy --timeout=300s

# Test Dex connectivity
echo -e "${YELLOW}🔍 Testing Dex connectivity...${CN}"
kubectl port-forward -n $DEX_NAMESPACE svc/dex 5556:5556 &
DEX_PF_PID=$!

sleep 5

if curl -s http://localhost:5556/dex/.well-known/openid-configuration > /dev/null; then
    echo -e "${GREEN}✅ Dex OIDC Provider is accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Dex OIDC Provider not yet ready${NC}"
fi

kill $DEX_PF_PID 2>/dev/null || true

# Test OAuth2 Proxy
echo -e "${YELLOW}🔍 Testing OAuth2 Proxy...${CN}"
kubectl port-forward -n oauth2-proxy svc/oauth2-proxy 4180:4180 &
OAUTH_PF_PID=$!

sleep 5

if curl -s http://localhost:4180/ping > /dev/null; then
    echo -e "${GREEN}✅ OAuth2 Proxy is accessible${NC}"
else
    echo -e "${YELLOW}⚠️  OAuth2 Proxy not yet ready${NC}"
fi

kill $OAUTH_PF_PID 2>/dev/null || true

echo -e "${GREEN}✅ Flux Status Page SSO setup completed!${NC}"
echo ""
echo -e "${BLUE}🎯 Next Steps:${NC}"
echo "1. Configure your OIDC provider:"
echo "   - Update OIDC_ISSUER_URL, OIDC_CLIENT_ID, and OIDC_CLIENT_SECRET"
echo "   - Add your organization's OIDC configuration"
echo ""
echo "2. Update Ingress configuration:"
echo "   - Replace flux-ui.example.com with your actual domain"
echo "   - Configure DNS records"
echo ""
echo "3. Test SSO authentication:"
echo "   kubectl port-forward -n oauth2-proxy svc/oauth2-proxy 4180:4180"
echo "   Then open http://localhost:4180"
echo ""
echo "4. Configure user permissions:"
echo "   kubectl create clusterrolebinding flux-ui-user-admin \\"
echo "     --clusterrole=flux-ui-admin \\"
echo "     --user=<your-username>"
echo ""
echo "5. Access the Flux Status Page:"
echo "   https://flux-ui.example.com"
echo ""
echo -e "${YELLOW}📚 For more information, see:${NC}"
echo "- SSO Configuration: docs/FLUX-UI-SSO.md"
echo "- User Management: docs/FLUX-UI-USERS.md"
echo "- Troubleshooting: docs/FLUX-UI-TROUBLESHOOTING.md"

# Cleanup temporary files
rm -f dex-install.yaml flux-ui-oidc.yaml oauth2-proxy.yaml user-management.yaml sso-monitoring.yaml

echo -e "${GREEN}🎉 SSO setup completed successfully!${NC}"

#!/bin/bash

# Flux Status Page Setup Script
# This script configures the Flux Status Page for the GitOps Infra Control Plane

set -euxo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FLUX_NAMESPACE="flux-system"
UI_SERVICE_NAME="flux-operator"
UI_PORT="9080"
INGRESS_HOST="flux-ui.local"
TLS_SECRET_NAME="flux-ui-tls"
OIDC_SECRET_NAME="flux-ui-oidc"

echo -e "${BLUE}🚀 Flux Status Page Setup Script${NC}"
echo "=================================="

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

# Check Flux Operator is installed
if ! kubectl get fluxinstance -n $FLUX_NAMESPACE &> /dev/null; then
    echo -e "${RED}❌ Flux Operator is not installed. Please install Flux Operator first.${NC}"
    echo "Run: ./core/automation/scripts/install-flux-operator.sh"
    exit 1
fi

# Check if Flux Operator UI service exists
if ! kubectl get svc $UI_SERVICE_NAME -n $FLUX_NAMESPACE &> /dev/null; then
    echo -e "${YELLOW}📦 Creating Flux Status Page service...${NC}"
    
    cat > flux-ui-service.yaml << EOF
apiVersion: v1
kind: Service
metadata:
  name: $UI_SERVICE_NAME
  namespace: $FLUX_NAMESPACE
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: agentic-reconciliation-engine
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "9080"
    prometheus.io/path: "/metrics"
spec:
  selector:
    app.kubernetes.io/name: flux
  ports:
  - name: http
    port: $UI_PORT
    targetPort: $UI_PORT
    protocol: TCP
  type: ClusterIP
EOF

    kubectl apply -f flux-ui-service.yaml
    echo -e "${GREEN}✅ Flux Status Page service created${NC}"
else
    echo -e "${GREEN}✅ Flux Status Page service already exists${NC}"
fi

# Create UI configuration
echo -e "${YELLOW}⚙️  Creating Flux Status Page configuration...${NC}"

cat > flux-ui-config.yaml << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-ui-config
  namespace: $FLUX_NAMESPACE
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: agentic-reconciliation-engine
data:
  config.yaml: |
    # Flux Status Page Configuration
    ui:
      title: "GitOps Infra Control Plane"
      logo: "/static/logo.png"
      theme: "light"
      refreshInterval: "30s"
      
    # Cluster configuration
    cluster:
      name: "production"
      description: "Production Agentic Reconciliation Engine"
      
    # Feature flags
    features:
      favorites: true
      search: true
      graphs: true
      history: true
      sso: true
      
    # Resource filtering
    filters:
      namespaces:
        include: ["flux-system", "production", "staging", "network-system", "cluster-system"]
        exclude: ["kube-system", "kube-public"]
      labels:
        include: ["app.kubernetes.io/part-of=agentic-reconciliation-engine"]
        
    # Dashboard configuration
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
        
    # Search configuration
    search:
      enabled: true
      maxResults: 50
      indexFields: ["name", "namespace", "kind", "labels"]
      
    # Favorites configuration
    favorites:
      enabled: true
      maxFavorites: 20
      autoCleanup: true
      
    # Graph configuration
    graph:
      enabled: true
      layout: "hierarchical"
      showConditions: true
      showDependencies: true
      maxDepth: 5
      
    # History configuration
    history:
      enabled: true
      maxEntries: 100
      retention: "7d"
      
    # SSO configuration
    sso:
      enabled: true
      provider: "oidc"
      clientId: "\${OIDC_CLIENT_ID}"
      issuerUrl: "\${OIDC_ISSUER_URL}"
      scopes: ["openid", "profile", "email"]
      
    # RBAC configuration
    rbac:
      enabled: true
      defaultRole: "viewer"
      roles:
        viewer:
          permissions: ["read"]
          resources: ["*"]
        admin:
          permissions: ["read", "write"]
          resources: ["*"]
        operator:
          permissions: ["read", "write", "reconcile"]
          resources: ["*"]
          
    # Notifications
    notifications:
      enabled: true
      webhook: "\${WEBHOOK_URL}"
      
    # Performance tuning
    performance:
      cacheSize: 1000
      cacheTTL: "5m"
      maxConcurrentRequests: 10
EOF

kubectl apply -f flux-ui-config.yaml
echo -e "${GREEN}✅ Flux Status Page configuration created${NC}"

# Create monitoring configuration
echo -e "${YELLOW}📊 Creating monitoring configuration...${NC}"

cat > flux-ui-monitoring.yaml << EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: flux-ui
  namespace: $FLUX_NAMESPACE
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: agentic-reconciliation-engine
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
  namespace: $FLUX_NAMESPACE
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: agentic-reconciliation-engine
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
EOF

kubectl apply -f flux-ui-monitoring.yaml
echo -e "${GREEN}✅ Monitoring configuration created${NC}"

# Create RBAC configuration
echo -e "${YELLOW}🔐 Creating RBAC configuration...${NC}"

cat > flux-ui-rbac.yaml << EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: flux-ui
  namespace: $FLUX_NAMESPACE
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: agentic-reconciliation-engine
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: flux-ui-viewer
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: agentic-reconciliation-engine
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
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "daemonsets", "statefulsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["get", "list", "watch"]
# RBAC
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["roles", "rolebindings", "clusterroles", "clusterrolebindings"]
  verbs: ["get", "list", "watch"]
# Events
- apiGroups: [""]
  resources: ["events"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: flux-ui-admin
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: agentic-reconciliation-engine
rules:
# Include viewer permissions
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
  resources: ["pods", "services", "configmaps", "secrets"]
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
# Events
- apiGroups: [""]
  resources: ["events"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: flux-ui-viewer
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: agentic-reconciliation-engine
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: flux-ui-viewer
subjects:
- kind: ServiceAccount
  name: flux-ui
  namespace: $FLUX_NAMESPACE
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: flux-ui-admin
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: agentic-reconciliation-engine
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: flux-ui-admin
subjects:
- kind: ServiceAccount
  name: flux-ui
  namespace: $FLUX_NAMESPACE
EOF

kubectl apply -f flux-ui-rbac.yaml
echo -e "${GREEN}✅ RBAC configuration created${NC}"

# Create network policies
echo -e "${YELLOW}🛡️  Creating network policies...${NC}"

cat > flux-ui-networkpolicy.yaml << EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: flux-ui-netpol
  namespace: $FLUX_NAMESPACE
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: agentic-reconciliation-engine
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
  # Allow HTTP to external services
  - to: []
    ports:
    - protocol: TCP
      port: 80
  # Allow Kubernetes API
  - to: []
    ports:
    - protocol: TCP
      port: 443
EOF

kubectl apply -f flux-ui-networkpolicy.yaml
echo -e "${GREEN}✅ Network policies created${NC}"

# Test local access
echo -e "${YELLOW}🧪 Testing local access...${NC}"

# Start port-forward in background
kubectl port-forward -n $FLUX_NAMESPACE svc/$UI_SERVICE_NAME $UI_PORT:$UI_PORT &
PF_PID=$!

# Wait for port-forward to start
sleep 5

# Test connectivity
if curl -s http://localhost:$UI_PORT/health > /dev/null; then
    echo -e "${GREEN}✅ Flux Status Page is accessible locally${NC}"
    echo -e "${BLUE}🌐 Local URL: http://localhost:$UI_PORT${NC}"
else
    echo -e "${YELLOW}⚠️  Flux Status Page not yet ready, this is normal during initial setup${NC}"
fi

# Stop port-forward
kill $PF_PID 2>/dev/null || true

echo -e "${GREEN}✅ Flux Status Page setup completed!${NC}"
echo ""
echo -e "${BLUE}🎯 Next Steps:${NC}"
echo "1. Configure Ingress for external access:"
echo "   kubectl apply -f flux-ui-ingress.yaml"
echo ""
echo "2. Set up SSO authentication:"
echo "   kubectl apply -f flux-ui-sso.yaml"
echo ""
echo "3. Access the UI locally:"
echo "   kubectl -n $FLUX_NAMESPACE port-forward svc/$UI_SERVICE_NAME $UI_PORT:$UI_PORT"
echo "   Then open http://localhost:$UI_PORT"
echo ""
echo "4. Configure user permissions:"
echo "   kubectl create clusterrolebinding flux-ui-user-viewer \\"
echo "     --clusterrole=flux-ui-viewer \\"
echo "     --user=<your-username>"
echo ""
echo -e "${YELLOW}📚 For more information, see:${NC}"
echo "- Flux Status Page Documentation: docs/FLUX-STATUS-PAGE.md"
echo "- Ingress Configuration: docs/FLUX-UI-INGRESS.md"
echo "- SSO Configuration: docs/FLUX-UI-SSO.md"

# Cleanup temporary files
rm -f flux-ui-service.yaml flux-ui-config.yaml flux-ui-monitoring.yaml flux-ui-rbac.yaml flux-ui-networkpolicy.yaml

echo -e "${GREEN}🎉 Flux Status Page setup completed successfully!${NC}"

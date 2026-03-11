#!/bin/bash

# Multi-Cluster GitOps Workflows Setup Script
# This script implements comprehensive multi-cluster GitOps workflows

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HUB_NAMESPACE="flux-system"
SPOKE_NAMESPACE="default"
WORKFLOW_DIR="control-plane/multi-cluster"
GIT_REPO="https://github.com/your-org/gitops-infra-control-plane.git"

echo -e "${BLUE}🔄 Multi-Cluster GitOps Workflows Setup${NC}"
echo "========================================="

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

# Check Flux is installed
if ! kubectl get fluxinstance -n $HUB_NAMESPACE &> /dev/null; then
    echo -e "${RED}❌ Flux is not installed. Please install Flux first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites validated${NC}"

# Create multi-cluster workflow directory
echo -e "${YELLOW}📁 Creating multi-cluster workflow directory...${NC}"

mkdir -p $WORKFLOW_DIR/{clusters,workflows,policies,templates}

# Create cluster management workflows
echo -e "${YELLOW}🏗️  Creating cluster management workflows...${NC}"

cat > $WORKFLOW_DIR/clusters/spoke-cluster-template.yaml << EOF
# Spoke Cluster Template
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: spoke-cluster
  namespace: $HUB_NAMESPACE
  labels:
    app.kubernetes.io/name: spoke-cluster
    app.kubernetes.io/component: gitops
    app.kubernetes.io/part-of: gitops-infra-control-plane
    cluster.example.com/name: "spoke-cluster"
    cluster.example.com/environment: "production"
    cluster.example.com/region: "us-west-2"
spec:
  distribution:
    version: "2.x"
    registry: "ghcr.io/fluxcd"
    artifact: "oci://ghcr.io/controlplaneio-fluxcd/flux-operator-manifests"
  components:
    - source-controller
    - kustomize-controller
    - helm-controller
    - notification-controller
  cluster:
    type: kubernetes
    size: medium
    multitenant: false
    networkPolicy: true
    domain: "cluster.local"
  sync:
    kind: GitRepository
    url: "$GIT_REPO"
    ref: "refs/heads/main"
    path: "clusters/spoke-cluster"
    interval: "5m"
    timeout: "3m"
  security:
    rbac:
      enabled: true
      crossNamespace: false
  monitoring:
    enabled: true
    prometheus:
      enabled: true
      serviceMonitor: true
---
# Spoke Cluster ResourceSet
apiVersion: fluxcd.controlplane.io/v1
kind: ResourceSet
metadata:
  name: spoke-cluster-resources
  namespace: $HUB_NAMESPACE
  labels:
    app.kubernetes.io/name: spoke-cluster
    app.kubernetes.io/component: gitops
    app.kubernetes.io/part-of: gitops-infra-control-plane
    cluster.example.com/name: "spoke-cluster"
spec:
  resources:
  - name: monitoring-stack
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "infrastructure/tenants/3-workloads/monitoring"
    prune: true
    wait: true
    timeout: 10m
    dependsOn: []
  - name: logging-stack
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "infrastructure/tenants/3-workloads/logging"
    prune: true
    wait: true
    timeout: 10m
    dependsOn: []
  - name: security-stack
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "infrastructure/tenants/3-workloads/security"
    prune: true
    wait: true
    timeout: 10m
    dependsOn: []
EOF

# Create application deployment workflows
cat > $WORKFLOW_DIR/workflows/application-deployment.yaml << EOF
# Application Deployment Workflow
apiVersion: fluxcd.controlplane.io/v1
kind: ResourceSet
metadata:
  name: application-deployment-workflow
  namespace: $HUB_NAMESPACE
  labels:
    app.kubernetes.io/name: application-workflow
    app.kubernetes.io/component: gitops
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  resources:
  - name: namespace-setup
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "applications/namespaces"
    prune: true
    wait: true
    timeout: 5m
    dependsOn: []
  - name: rbac-setup
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "applications/rbac"
    prune: true
    wait: true
    timeout: 5m
    dependsOn:
    - namespace-setup
  - name: config-maps
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "applications/configmaps"
    prune: true
    wait: true
    timeout: 5m
    dependsOn:
    - rbac-setup
  - name: secrets
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "applications/secrets"
    prune: true
    wait: true
    timeout: 5m
    dependsOn:
    - rbac-setup
  - name: frontend-app
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "applications/frontend"
    prune: true
    wait: true
    timeout: 10m
    dependsOn:
    - config-maps
    - secrets
  - name: backend-app
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "applications/backend"
    prune: true
    wait: true
    timeout: 10m
    dependsOn:
    - config-maps
    - secrets
  - name: database
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "applications/database"
    prune: true
    wait: true
    timeout: 15m
    dependsOn:
    - rbac-setup
  - name: ingress
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "applications/ingress"
    prune: true
    wait: true
    timeout: 5m
    dependsOn:
    - frontend-app
    - backend-app
EOF

# Create progressive deployment workflows
cat > $WORKFLOW_DIR/workflows/progressive-deployment.yaml << EOF
# Progressive Deployment Workflow (Canary + Blue-Green)
apiVersion: fluxcd.controlplane.io/v1
kind: ResourceSet
metadata:
  name: progressive-deployment-workflow
  namespace: $HUB_NAMESPACE
  labels:
    app.kubernetes.io/name: progressive-deployment
    app.kubernetes.io/component: gitops
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  resources:
  - name: canary-preparation
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "applications/canary/preparation"
    prune: false
    wait: true
    timeout: 5m
    dependsOn: []
  - name: canary-deployment
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "applications/canary/deployment"
    prune: false
    wait: true
    timeout: 10m
    dependsOn:
    - canary-preparation
  - name: canary-analysis
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "applications/canary/analysis"
    prune: false
    wait: true
    timeout: 15m
    dependsOn:
    - canary-deployment
  - name: blue-green-preparation
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "applications/blue-green/preparation"
    prune: false
    wait: true
    timeout: 5m
    dependsOn: []
  - name: blue-green-deployment
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "applications/blue-green/deployment"
    prune: false
    wait: true
    timeout: 10m
    dependsOn:
    - blue-green-preparation
  - name: blue-green-cutover
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "applications/blue-green/cutover"
    prune: false
    wait: true
    timeout: 5m
    dependsOn:
    - blue-green-deployment
EOF

# Create disaster recovery workflows
cat > $WORKFLOW_DIR/workflows/disaster-recovery.yaml << EOF
# Disaster Recovery Workflow
apiVersion: fluxcd.controlplane.io/v1
kind: ResourceSet
metadata:
  name: disaster-recovery-workflow
  namespace: $HUB_NAMESPACE
  labels:
    app.kubernetes.io/name: disaster-recovery
    app.kubernetes.io/component: gitops
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  resources:
  - name: backup-configuration
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "disaster-recovery/backup-config"
    prune: true
    wait: true
    timeout: 5m
    dependsOn: []
  - name: etcd-backup
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "disaster-recovery/etcd-backup"
    prune: true
    wait: true
    timeout: 10m
    dependsOn:
    - backup-configuration
  - name: pv-backup
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "disaster-recovery/pv-backup"
    prune: true
    wait: true
    timeout: 15m
    dependsOn:
    - backup-configuration
  - name: state-backup
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "disaster-recovery/state-backup"
    prune: true
    wait: true
    timeout: 10m
    dependsOn:
    - etcd-backup
    - pv-backup
  - name: restore-procedure
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "disaster-recovery/restore"
    prune: false
    wait: true
    timeout: 20m
    dependsOn: []
EOF

# Create multi-environment workflows
cat > $WORKFLOW_DIR/workflows/multi-environment.yaml << EOF
# Multi-Environment Workflow
apiVersion: fluxcd.controlplane.io/v1
kind: ResourceSet
metadata:
  name: multi-environment-workflow
  namespace: $HUB_NAMESPACE
  labels:
    app.kubernetes.io/name: multi-environment
    app.kubernetes.io/component: gitops
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  resources:
  - name: development-env
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "environments/development"
    prune: true
    wait: true
    timeout: 10m
    dependsOn: []
  - name: staging-env
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "environments/staging"
    prune: true
    wait: true
    timeout: 10m
    dependsOn:
    - development-env
  - name: production-env
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "environments/production"
    prune: true
    wait: true
    timeout: 15m
    dependsOn:
    - staging-env
  - name: dr-env
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "environments/disaster-recovery"
    prune: true
    wait: true
    timeout: 15m
    dependsOn:
    - production-env
EOF

# Create policy enforcement workflows
cat > $WORKFLOW_DIR/policies/policy-enforcement.yaml << EOF
# Policy Enforcement Workflow
apiVersion: fluxcd.controlplane.io/v1
kind: ResourceSet
metadata:
  name: policy-enforcement-workflow
  namespace: $HUB_NAMESPACE
  labels:
    app.kubernetes.io/name: policy-enforcement
    app.kubernetes.io/component: gitops
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  resources:
  - name: security-policies
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "policies/security"
    prune: true
    wait: true
    timeout: 5m
    dependsOn: []
  - name: compliance-policies
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "policies/compliance"
    prune: true
    wait: true
    timeout: 5m
    dependsOn:
    - security-policies
  - name: cost-policies
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "policies/cost"
    prune: true
    wait: true
    timeout: 5m
    dependsOn:
    - security-policies
  - name: governance-policies
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: "policies/governance"
    prune: true
    wait: true
    timeout: 5m
    dependsOn:
    - compliance-policies
    - cost-policies
EOF

# Create GitOps automation templates
echo -e "${YELLOW}📋 Creating GitOps automation templates...${NC}"

cat > $WORKFLOW_DIR/templates/cluster-bootstrap.yaml << EOF
# Cluster Bootstrap Template
apiVersion: v1
kind: Namespace
metadata:
  name: flux-system
  labels:
    app.kubernetes.io/name: flux-system
    app.kubernetes.io/component: gitops
    app.kubernetes.io/part-of: gitops-infra-control-plane
---
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: flux-system
  namespace: flux-system
spec:
  interval: 5m
  url: $GIT_REPO
  ref:
    branch: main
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: flux-system
  namespace: flux-system
spec:
  interval: 5m
  path: ./clusters/spoke-cluster
  prune: true
  sourceRef:
    kind: GitRepository
    name: flux-system
  dependsOn: []
EOF

cat > $WORKFLOW_DIR/templates/application-template.yaml << EOF
# Application Template
apiVersion: v1
kind: Namespace
metadata:
  name: {{ .Values.namespace }}
  labels:
    app.kubernetes.io/name: {{ .Values.name }}
    app.kubernetes.io/component: application
    app.kubernetes.io/part-of: gitops-infra-control-plane
    environment: {{ .Values.environment }}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Values.name }}
  namespace: {{ .Values.namespace }}
  labels:
    app.kubernetes.io/name: {{ .Values.name }}
    app.kubernetes.io/component: application
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  replicas: {{ .Values.replicas }}
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ .Values.name }}
      app.kubernetes.io/component: application
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ .Values.name }}
        app.kubernetes.io/component: application
    spec:
      containers:
      - name: {{ .Values.name }}
        image: {{ .Values.image }}
        ports:
        - containerPort: {{ .Values.port }}
        resources:
          requests:
            cpu: {{ .Values.resources.requests.cpu }}
            memory: {{ .Values.resources.requests.memory }}
          limits:
            cpu: {{ .Values.resources.limits.cpu }}
            memory: {{ .Values.resources.limits.memory }}
---
apiVersion: v1
kind: Service
metadata:
  name: {{ .Values.name }}
  namespace: {{ .Values.namespace }}
  labels:
    app.kubernetes.io/name: {{ .Values.name }}
    app.kubernetes.io/component: application
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  selector:
    app.kubernetes.io/name: {{ .Values.name }}
    app.kubernetes.io/component: application
  ports:
  - port: {{ .Values.service.port }}
    targetPort: {{ .Values.port }}
    protocol: TCP
  type: {{ .Values.service.type }}
EOF

# Create workflow automation scripts
echo -e "${YELLOW}🔧 Creating workflow automation scripts...${NC}"

cat > $WORKFLOW_DIR/scripts/deploy-spoke-cluster.sh << EOF
#!/bin/bash

# Deploy Spoke Cluster Script
set -e

CLUSTER_NAME=\$1
CLUSTER_TYPE=\${2:-"eks"}
REGION=\${3:-"us-west-2"}
ENVIRONMENT=\${4:-"production"}

if [[ -z "\$CLUSTER_NAME" ]]; then
    echo "Usage: \$0 <cluster-name> [cluster-type] [region] [environment]"
    exit 1
fi

echo "🚀 Deploying spoke cluster: \$CLUSTER_NAME"
echo "Type: \$CLUSTER_TYPE"
echo "Region: \$REGION"
echo "Environment: \$ENVIRONMENT"

# Create cluster-specific directory
mkdir -p clusters/\$CLUSTER_NAME

# Copy template and customize
sed "s/spoke-cluster/\$CLUSTER_NAME/g" $WORKFLOW_DIR/clusters/spoke-cluster-template.yaml > clusters/\$CLUSTER_NAME/flux-instance.yaml

# Add cluster-specific labels
kubectl label -f clusters/\$CLUSTER_NAME/flux-instance.yaml \\
    cluster.example.com/name=\$CLUSTER_NAME \\
    cluster.example.com/environment=\$ENVIRONMENT \\
    cluster.example.com/region=\$REGION

# Apply to hub cluster
kubectl apply -f clusters/\$CLUSTER_NAME/flux-instance.yaml

echo "✅ Spoke cluster \$CLUSTER_NAME deployment initiated"
echo "📊 Monitor status with: kubectl get fluxinstance \$CLUSTER_NAME -n flux-system"
EOF

cat > $WORKFLOW_DIR/scripts/promote-environment.sh << EOF
#!/bin/bash

# Environment Promotion Script
set -e

FROM_ENV=\$1
TO_ENV=\$2
APPLICATION=\$3

if [[ -z "\$FROM_ENV" || -z "\$TO_ENV" || -z "\$APPLICATION" ]]; then
    echo "Usage: \$0 <from-env> <to-env> <application>"
    exit 1
fi

echo "🔄 Promoting \$APPLICATION from \$FROM_ENV to \$TO_ENV"

# Create promotion branch
git checkout -b "promote-\$APPLICATION-\$FROM_ENV-to-\$TO_ENV"

# Copy manifests
cp -r environments/\$FROM_ENV/\$APPLICATION environments/\$TO_ENV/

# Update environment-specific values
sed -i "s/environment: \$FROM_ENV/environment: \$TO_ENV/g" environments/\$TO_ENV/\$APPLICATION/*.yaml

# Update replicas for production
if [[ "\$TO_ENV" == "production" ]]; then
    sed -i 's/replicas: [0-9]*/replicas: 3/g' environments/\$TO_ENV/\$APPLICATION/*.yaml
fi

# Commit and push
git add environments/\$TO_ENV/\$APPLICATION/
git commit -m "Promote \$APPLICATION from \$FROM_ENV to \$TO_ENV"
git push origin "promote-\$APPLICATION-\$FROM_ENV-to-\$TO_ENV"

echo "✅ Promotion branch created: promote-\$APPLICATION-\$FROM_ENV-to-\$TO_ENV"
echo "🔄 Create pull request to continue promotion"
EOF

cat > $WORKFLOW_DIR/scripts/rollback-application.sh << EOF
#!/bin/bash

# Application Rollback Script
set -e

APPLICATION=\$1
ENVIRONMENT=\$2
PREVIOUS_COMMIT=\$3

if [[ -z "\$APPLICATION" || -z "\$ENVIRONMENT" || -z "\$PREVIOUS_COMMIT" ]]; then
    echo "Usage: \$0 <application> <environment> <previous-commit>"
    exit 1
fi

echo "🔄 Rolling back \$APPLICATION in \$ENVIRONMENT to commit \$PREVIOUS_COMMIT"

# Create rollback branch
git checkout -b "rollback-\$APPLICATION-\$ENVIRONMENT"

# Reset to previous commit
git checkout \$PREVIOUS_COMMIT -- environments/\$ENVIRONMENT/\$APPLICATION/

# Commit rollback
git add environments/\$ENVIRONMENT/\$APPLICATION/
git commit -m "Rollback \$APPLICATION in \$ENVIRONMENT to commit \$PREVIOUS_COMMIT"

# Push rollback branch
git push origin "rollback-\$APPLICATION-\$ENVIRONMENT"

echo "✅ Rollback branch created: rollback-\$APPLICATION-\$ENVIRONMENT"
echo "🔄 Merge rollback branch to complete rollback"
EOF

# Create monitoring and observability for workflows
echo -e "${YELLOW}📊 Creating workflow monitoring...${NC}"

cat > $WORKFLOW_DIR/monitoring/workflow-metrics.yaml << EOF
# Workflow Monitoring Configuration
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: flux-workflow-metrics
  namespace: $HUB_NAMESPACE
  labels:
    app.kubernetes.io/name: flux-workflow
    app.kubernetes.io/component: monitoring
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: flux
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: flux-workflow-alerts
  namespace: $HUB_NAMESPACE
  labels:
    app.kubernetes.io/name: flux-workflow
    app.kubernetes.io/component: monitoring
    app.kubernetes.io/part-of: gitops-infra-control-plane
spec:
  groups:
  - name: workflow
    rules:
    - alert: WorkflowReconciliationFailure
      expr: flux_kustomization_status_condition{status="False",type="Ready"} == 1
      for: 5m
      labels:
        severity: warning
        workflow: "reconciliation"
      annotations:
        summary: "Workflow reconciliation failure"
        description: "Kustomization {{ \$labels.name }} has failed to reconcile"
    - alert: WorkflowStalled
      expr: time() - flux_kustomization_last_handled_reconcile_at_timestamp > 3600
      for: 10m
      labels:
        severity: warning
        workflow: "stalled"
      annotations:
        summary: "Workflow stalled"
        description: "Kustomization {{ \$labels.name }} has not reconciled in over 1 hour"
    - alert: DependencyChainFailure
      expr: |
        (
          flux_kustomization_status_condition{status="False",type="Ready"} == 1
        ) and on (depends_on) (
          flux_kustomization_spec_depends_on{depends_on!=""}
        )
      for: 5m
      labels:
        severity: critical
        workflow: "dependency"
      annotations:
        summary: "Dependency chain failure"
        description: "Kustomization {{ \$labels.name }} depends on failed resource {{ \$labels.depends_on }}"
EOF

# Apply multi-cluster workflows
echo -e "${YELLOW}🚀 Applying multi-cluster workflows...${NC}"

# Create namespace for workflows if it doesn't exist
kubectl create namespace $HUB_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Apply workflow configurations
kubectl apply -f $WORKFLOW_DIR/clusters/spoke-cluster-template.yaml
kubectl apply -f $WORKFLOW_DIR/workflows/application-deployment.yaml
kubectl apply -f $WORKFLOW_DIR/workflows/progressive-deployment.yaml
kubectl apply -f $WORKFLOW_DIR/workflows/disaster-recovery.yaml
kubectl apply -f $WORKFLOW_DIR/workflows/multi-environment.yaml
kubectl apply -f $WORKFLOW_DIR/policies/policy-enforcement.yaml
kubectl apply -f $WORKFLOW_DIR/monitoring/workflow-metrics.yaml

# Make scripts executable
chmod +x $WORKFLOW_DIR/scripts/*.sh

echo -e "${GREEN}✅ Multi-cluster GitOps workflows created!${NC}"
echo ""
echo -e "${BLUE}🎯 Available Workflows:${NC}"
echo "  🏗️  Cluster Management: Deploy and manage spoke clusters"
echo "  🚀 Application Deployment: Deploy applications with dependencies"
echo "  🔄 Progressive Deployment: Canary and blue-green deployments"
echo "  🛡️  Disaster Recovery: Backup and restore procedures"
echo "  🌍 Multi-Environment: Dev, staging, production environments"
echo "  📋 Policy Enforcement: Security, compliance, and governance"
echo ""
echo -e "${BLUE}🔧 Available Scripts:${NC}"
echo "  ./control-plane/multi-cluster/scripts/deploy-spoke-cluster.sh <name>"
echo "  ./control-plane/multi-cluster/scripts/promote-environment.sh <from> <to> <app>"
echo "  ./control-plane/multi-cluster/scripts/rollback-application.sh <app> <env> <commit>"
echo ""
echo -e "${BLUE}📊 Monitoring:${NC}"
echo "  Workflow metrics and alerts configured"
echo "  Dependency chain failure detection"
echo "  Reconciliation status monitoring"
echo ""
echo -e "${YELLOW}📚 Next Steps:${NC}"
echo "  1. Configure cloud provider credentials"
echo "  2. Deploy first spoke cluster"
echo "  3. Set up application workloads"
echo "  4. Configure promotion workflows"
echo "  5. Test disaster recovery procedures"

echo -e "${GREEN}🎉 Multi-cluster GitOps workflows setup complete!${NC}"

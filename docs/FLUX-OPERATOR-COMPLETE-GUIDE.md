# Flux Operator Complete Implementation Guide

This comprehensive guide covers the complete implementation of Flux Operator for the GitOps Infrastructure Control Plane, including installation, configuration, advanced features, and best practices.

## Overview

Flux Operator is a Kubernetes operator that simplifies the installation and management of Flux CD. It provides a declarative API for Flux components and enables GitOps operations through a simplified interface.

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [FluxInstance CRD](#fluxinstance-crd)
4. [Sync Configurations](#sync-configurations)
5. [MCP Server Integration](#mcp-server-integration)
6. [Advanced Features](#advanced-features)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Migration Guide](#migration-guide)

## Installation

### Prerequisites

- Kubernetes cluster v1.24 or later
- kubectl configured to access the cluster
- Administrative privileges on the cluster

### Quick Install

```bash
# Install Flux Operator CLI
brew install controlplaneio-fluxcd/tap/flux-operator

# Install Flux Operator with basic configuration
./scripts/install-flux-operator.sh
```

### Manual Installation

```bash
# Install CLI
curl -L "https://github.com/controlplaneio-fluxcd/flux-operator/releases/latest/download/flux-operator-darwin-amd64" \
    -o /usr/local/bin/flux-operator
chmod +x /usr/local/bin/flux-operator

# Install Flux Operator
flux-operator install --version=2.x --components=source-controller,kustomize-controller,helm-controller
```

### Verification

```bash
# Check Flux Operator status
kubectl get fluxinstance flux -n flux-system

# Check Flux components
kubectl get pods -n flux-system -l app.kubernetes.io/name=flux

# Check CRDs
kubectl get crds | grep fluxcd
```

## Configuration

### Basic FluxInstance

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
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
```

### Production Configuration

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
spec:
  distribution:
    version: "2.2.x"
    registry: "ghcr.io/fluxcd"
    artifact: "oci://ghcr.io/controlplaneio-fluxcd/flux-operator-manifests"
  components:
    - source-controller
    - source-watcher
    - kustomize-controller
    - helm-controller
    - notification-controller
    - image-reflector-controller
    - image-automation-controller
  cluster:
    type: kubernetes
    size: large
    multitenant: true
    networkPolicy: true
    domain: "cluster.local"
    sharding:
      enabled: true
      shards: 3
  security:
    rbac:
      enabled: true
      crossNamespace: true
    encryption:
      enabled: true
      provider: sops
  monitoring:
    enabled: true
    prometheus:
      enabled: true
      serviceMonitor: true
    alerts:
      enabled: true
```

## FluxInstance CRD

### Core Fields

#### Distribution

```yaml
spec:
  distribution:
    version: "2.x"                    # Flux version
    registry: "ghcr.io/fluxcd"        # Container registry
    artifact: "oci://..."              # OCI artifact URL
```

#### Components

```yaml
spec:
  components:
    - source-controller               # Git and OCI sources
    - source-watcher                   # Webhook handling
    - kustomize-controller             # Kustomize deployments
    - helm-controller                  # Helm releases
    - notification-controller          # Notifications
    - image-reflector-controller       # Image scanning
    - image-automation-controller      # Image updates
```

#### Cluster Configuration

```yaml
spec:
  cluster:
    type: kubernetes                   # Cluster type
    size: medium                        # small, medium, large
    multitenant: false                  # Multi-tenant mode
    networkPolicy: true                 # Network policies
    domain: "cluster.local"            # Cluster domain
    sharding:                           # Controller sharding
      enabled: true
      shards: 3
    highAvailability:                   # HA configuration
      enabled: true
      replicas: 3
```

#### Security Configuration

```yaml
spec:
  security:
    rbac:                              # RBAC settings
      enabled: true
      crossNamespace: true
    encryption:                         # Encryption settings
      enabled: true
      provider: sops
      secretRef:
        name: sops-keys
```

#### Monitoring Configuration

```yaml
spec:
  monitoring:
    enabled: true
    prometheus:
      enabled: true
      serviceMonitor: true
      port: 8080
    alerts:
      enabled: true
      rules:
        - name: FluxReconciliationFailure
          condition: "flux_reconciliation_failed_total > 0"
          message: "Flux reconciliation has failed"
          severity: warning
```

#### Sync Configuration

```yaml
spec:
  sync:
    kind: GitRepository                 # Source type
    url: "https://github.com/user/repo"  # Repository URL
    ref: "refs/heads/main"              # Git reference
    path: "clusters/production"         # Path within repo
    interval: "5m"                      # Sync interval
    timeout: "3m"                       # Sync timeout
    pullSecret: "flux-system"           # Authentication secret
```

#### Kustomize Patches

```yaml
spec:
  kustomize:
    patch: |
      # Resource limits
      - patch: |
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: source-controller
            namespace: flux-system
          spec:
            template:
              spec:
                containers:
                - name: manager
                  resources:
                    requests:
                      cpu: 100m
                      memory: 256Mi
                    limits:
                      cpu: 500m
                      memory: 512Mi
        target:
          kind: Kustomization
          name: flux-components
          namespace: flux-system
```

## Sync Configurations

### Git Repository Sync

#### Public Repository

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
spec:
  sync:
    kind: GitRepository
    url: "https://github.com/fluxcd/flux2-kustomize-helm-example"
    ref: "refs/heads/main"
    path: "clusters/staging"
    interval: "5m"
    timeout: "3m"
```

#### Private Repository

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
spec:
  sync:
    kind: GitRepository
    url: "https://github.com/your-org/gitops-infra-control-plane"
    ref: "refs/heads/main"
    path: "infrastructure/tenants"
    interval: "5m"
    timeout: "3m"
    pullSecret: "flux-system"
---
apiVersion: v1
kind: Secret
metadata:
  name: flux-system
  namespace: flux-system
type: Opaque
stringData:
  username: "git"
  password: "your-github-token"
```

#### SSH Authentication

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
spec:
  sync:
    kind: GitRepository
    url: "ssh://git@github.com/your-org/gitops-infra-control-plane.git"
    ref: "refs/heads/main"
    path: "infrastructure/tenants"
    interval: "5m"
    timeout: "3m"
    pullSecret: "flux-ssh-credentials"
---
apiVersion: v1
kind: Secret
metadata:
  name: flux-ssh-credentials
  namespace: flux-system
type: Opaque
stringData:
  identity: |
    -----BEGIN OPENSSH PRIVATE KEY-----
    your-ssh-private-key-content
    -----END OPENSSH PRIVATE KEY-----
  known_hosts: |
    github.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC...
```

### OCI Repository Sync

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
spec:
  sync:
    kind: OCIRepository
    url: "oci://ghcr.io/your-org/helm-charts"
    ref: "latest"
    interval: "10m"
    timeout: "5m"
    pullSecret: "ghcr-credentials"
---
apiVersion: v1
kind: Secret
metadata:
  name: ghcr-credentials
  namespace: flux-system
type: kubernetes.io/dockerconfigjson
stringData:
  .dockerconfigjson: |
    {
      "auths": {
        "ghcr.io": {
          "username": "your-username",
          "password": "your-ghcr-token",
          "auth": "base64-encoded-auth-string"
        }
      }
    }
```

### Bucket Sync

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
spec:
  sync:
    kind: Bucket
    bucketName: "gitops-manifests"
    endpoint: "s3.amazonaws.com"
    region: "us-west-2"
    provider: "aws"
    interval: "5m"
    timeout: "3m"
    pullSecret: "s3-credentials"
---
apiVersion: v1
kind: Secret
metadata:
  name: s3-credentials
  namespace: flux-system
type: Opaque
stringData:
  accesskey: "your-access-key-id"
  secretkey: "your-secret-access-key"
```

## MCP Server Integration

### Installation

```bash
# Install MCP server CLI
brew install controlplaneio-fluxcd/tap/flux-operator-mcp

# Install MCP server
./scripts/install-flux-mcp-server.sh
```

### Configuration

#### Claude Desktop

```json
{
  "mcpServers": {
    "flux-operator-mcp": {
      "command": "flux-operator-mcp",
      "args": [
        "serve",
        "--read-only=false",
        "--kubeconfig=/Users/username/.kube/config",
        "--namespace=flux-system",
        "--log-level=info"
      ],
      "env": {
        "KUBECONFIG": "/Users/username/.kube/config",
        "FLUX_NAMESPACE": "flux-system"
      }
    }
  }
}
```

#### Cursor

```json
{
  "mcpServers": {
    "flux-operator-mcp": {
      "command": "flux-operator-mcp",
      "args": [
        "serve",
        "--read-only=false",
        "--kubeconfig=/Users/username/.kube/config",
        "--namespace=flux-system",
        "--log-level=info"
      ],
      "env": {
        "KUBECONFIG": "/Users/username/.kube/config",
        "FLUX_NAMESPACE": "flux-system"
      }
    }
  }
}
```

### Available Commands

#### Flux Instance Management

- `list_flux_instances` - List all Flux instances
- `get_flux_instance` - Get a specific Flux instance
- `create_flux_instance` - Create a new Flux instance
- `update_flux_instance` - Update a Flux instance
- `delete_flux_instance` - Delete a Flux instance

#### ResourceSet Management

- `list_resourcesets` - List all ResourceSets
- `get_resourceset` - Get a specific ResourceSet
- `create_resourceset` - Create a new ResourceSet

#### Sync and Reconciliation

- `sync_status` - Get sync status
- `reconcile_flux_instance` - Trigger reconciliation

#### Health and Monitoring

- `health_check` - Check health status
- `get_events` - Get recent events
- `component_status` - Check component status

### Example Prompts

```bash
# Deploy new application
"Create a new FluxInstance named 'app-flux' that:
- Syncs from https://github.com/user/app-manifests
- Uses the main branch
- Deploys to the my-app namespace
- Includes source-controller, kustomize-controller, and helm-controller
- Enables health checks"

# Troubleshoot issues
"My FluxInstance is not syncing properly. Can you:
1. Check the sync status
2. Show recent events
3. Verify all components are healthy
4. Trigger a manual reconciliation"

# Multi-environment management
"Create a staging FluxInstance that:
- Syncs from https://github.com/user/infrastructure-manifests
- Uses the staging branch
- Deploys to staging namespaces
- Has smaller resource limits than production"
```

## Advanced Features

### Multi-Tenant Configuration

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
spec:
  cluster:
    multitenant: true
    sharding:
      enabled: true
      shards: 3
  security:
    rbac:
      enabled: true
      crossNamespace: false
    encryption:
      enabled: true
      provider: sops
  kustomize:
    patch: |
      # Multi-tenant service accounts
      - patch: |
          apiVersion: v1
          kind: ServiceAccount
          metadata:
            name: kustomize-controller
            namespace: flux-system
            annotations:
              iam.amazonaws.com/role: flux-kustomize-controller
        target:
          kind: Kustomization
          name: flux-components
          namespace: flux-system
```

### High Availability

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
spec:
  cluster:
    size: large
    sharding:
      enabled: true
      shards: 3
    highAvailability:
      enabled: true
      replicas: 3
  kustomize:
    patch: |
      # High availability deployments
      - patch: |
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: source-controller
            namespace: flux-system
          spec:
            replicas: 3
            template:
              spec:
                containers:
                - name: manager
                  resources:
                    requests:
                      cpu: 100m
                      memory: 256Mi
                    limits:
                      cpu: 500m
                      memory: 512Mi
                  affinity:
                    podAntiAffinity:
                      preferredDuringSchedulingIgnoredDuringExecution:
                      - weight: 100
                        podAffinityTerm:
                          labelSelector:
                            matchLabels:
                              app.kubernetes.io/name: source-controller
                          topologyKey: kubernetes.io/hostname
        target:
          kind: Kustomization
          name: flux-components
          namespace: flux-system
```

### Custom Registry

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
spec:
  distribution:
    version: "2.x"
    registry: "your-registry.example.com/fluxcd"
    artifact: "oci://your-registry.example.com/fluxcd/flux-operator-manifests"
  kustomize:
    patch: |
      # Custom registry authentication
      - patch: |
          apiVersion: v1
          kind: Secret
          metadata:
            name: registry-credentials
            namespace: flux-system
          type: kubernetes.io/dockerconfigjson
          stringData:
            .dockerconfigjson: |
              {
                "auths": {
                  "your-registry.example.com": {
                    "username": "your-username",
                    "password": "your-password",
                    "auth": "base64-encoded-auth-string"
                  }
                }
              }
        target:
          kind: Kustomization
          name: flux-components
          namespace: flux-system
```

### ResourceSet API

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: ResourceSet
metadata:
  name: infrastructure
  namespace: flux-system
  labels:
    app.kubernetes.io/name: infrastructure
    app.kubernetes.io/component: gitops
spec:
  resources:
  - name: network-infrastructure
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: infrastructure/tenants/1-network
    prune: true
    wait: true
    timeout: 10m
    dependsOn: []
  - name: cluster-infrastructure
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: infrastructure/tenants/2-clusters
    prune: true
    wait: true
    timeout: 15m
    dependsOn:
    - network-infrastructure
  - name: workload-infrastructure
    kind: Kustomization
    sourceRef:
      kind: GitRepository
      name: gitops-infra-control-plane
    path: infrastructure/tenants/3-workloads
    prune: true
    wait: true
    timeout: 20m
    dependsOn:
    - cluster-infrastructure
```

## Best Practices

### 1. Use dependsOn for Dependencies

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: ResourceSet
metadata:
  name: infrastructure
  namespace: flux-system
spec:
  resources:
  - name: network-infrastructure
    kind: Kustomization
    path: infrastructure/tenants/1-network
    dependsOn: []
  - name: cluster-infrastructure
    kind: Kustomization
    path: infrastructure/tenants/2-clusters
    dependsOn:
    - network-infrastructure
  - name: workload-infrastructure
    kind: Kustomization
    path: infrastructure/tenants/3-workloads
    dependsOn:
    - cluster-infrastructure
```

### 2. Implement Security Best Practices

```yaml
spec:
  security:
    rbac:
      enabled: true
      crossNamespace: false
    encryption:
      enabled: true
      provider: sops
      secretRef:
        name: sops-keys
  cluster:
    networkPolicy: true
    multitenant: true
```

### 3. Configure Monitoring and Alerting

```yaml
spec:
  monitoring:
    enabled: true
    prometheus:
      enabled: true
      serviceMonitor: true
    alerts:
      enabled: true
      rules:
        - name: FluxReconciliationFailure
          condition: "flux_reconciliation_failed_total > 0"
          message: "Flux reconciliation has failed"
          severity: warning
```

### 4. Use Appropriate Resource Limits

```yaml
spec:
  kustomize:
    patch: |
      - patch: |
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: source-controller
            namespace: flux-system
          spec:
            template:
              spec:
                containers:
                - name: manager
                  resources:
                    requests:
                      cpu: 100m
                      memory: 256Mi
                    limits:
                      cpu: 500m
                      memory: 512Mi
        target:
          kind: Kustomization
          name: flux-components
          namespace: flux-system
```

### 5. Enable Health Checks

```yaml
spec:
  sync:
    healthChecks:
      enabled: true
      timeout: "10m"
      resources:
        - kind: Deployment
          name: network-controller
          namespace: network-system
        - kind: Service
          name: api-service
          namespace: production
```

## Troubleshooting

### Common Issues

#### 1. Installation Failures

```bash
# Check prerequisites
kubectl cluster-info
kubectl get crd fluxinstances.fluxcd.controlplane.io

# Check operator logs
kubectl logs -n flux-system deployment/flux-operator

# Verify installation
kubectl get fluxinstance flux -n flux-system -o yaml
```

#### 2. Sync Failures

```bash
# Check sync status
kubectl get fluxinstance flux -n flux-system -o yaml | grep -A 10 "sync:"

# Check source status
kubectl get gitrepository -n flux-system
kubectl get ocirepository -n flux-system

# Check events
kubectl get events -n flux-system --sort-by='.lastTimestamp'
```

#### 3. Permission Issues

```bash
# Check RBAC permissions
kubectl auth can-i create fluxinstances --as=system:serviceaccount:flux-system:default

# Check service account
kubectl get serviceaccount -n flux-system

# Check cluster roles
kubectl get clusterrole | grep flux
```

#### 4. MCP Server Issues

```bash
# Check MCP server status
ps aux | grep flux-operator-mcp

# Check configuration
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | jq .

# Test MCP server manually
flux-operator-mcp serve --log-level=debug
```

### Debug Commands

```bash
# Enable debug logging
flux-operator-mcp serve --log-level=debug

# Force reconciliation
kubectl patch fluxinstance flux -n flux-system --type=merge -p '{"spec":{"reconcileAt":"'$(date -u +'%Y-%m-%dT%H:%M:%SZ')'"}}'

# Check component logs
kubectl logs -n flux-system deployment/source-controller
kubectl logs -n flux-system deployment/kustomize-controller
kubectl logs -n flux-system deployment/helm-controller
```

## Migration Guide

### From Traditional Flux

1. **Backup Current Configuration**
   ```bash
   flux get sources all -o yaml > current-sources.yaml
   flux get kustomizations all -o yaml > current-kustomizations.yaml
   ```

2. **Install Flux Operator**
   ```bash
   ./scripts/install-flux-operator.sh
   ```

3. **Create FluxInstance**
   ```yaml
   apiVersion: fluxcd.controlplane.io/v1
   kind: FluxInstance
   metadata:
     name: flux
     namespace: flux-system
   spec:
     sync:
       kind: GitRepository
       url: "https://github.com/your-org/gitops-infra-control-plane"
       ref: "refs/heads/main"
       path: "infrastructure/tenants"
     distribution:
       version: "2.x"
       registry: "ghcr.io/fluxcd"
     components:
       - source-controller
       - kustomize-controller
       - helm-controller
     cluster:
       type: kubernetes
       size: medium
   ```

4. **Migrate to ResourceSet**
   ```yaml
   apiVersion: fluxcd.controlplane.io/v1
   kind: ResourceSet
   metadata:
     name: infrastructure
     namespace: flux-system
   spec:
     resources:
     - name: network-infrastructure
       kind: Kustomization
       path: infrastructure/tenants/1-network
     - name: cluster-infrastructure
       kind: Kustomization
       path: infrastructure/tenants/2-clusters
       dependsOn:
       - network-infrastructure
     - name: workload-infrastructure
       kind: Kustomization
       path: infrastructure/tenants/3-workloads
       dependsOn:
       - cluster-infrastructure
   ```

5. **Verify Migration**
   ```bash
   kubectl get fluxinstance -n flux-system
   kubectl get resourceset -n flux-system
   kubectl get kustomizations -n flux-system
   ```

### From Other GitOps Tools

1. **Export Current Configuration**
   ```bash
   # Export from ArgoCD
   argocd app list -o yaml > argocd-apps.yaml
   
   # Export from Jenkins X
   # Custom export process
   ```

2. **Install Flux Operator**
   ```bash
   ./scripts/install-flux-operator.sh
   ```

3. **Create FluxInstance**
   ```yaml
   apiVersion: fluxcd.controlplane.io/v1
   kind: FluxInstance
   metadata:
     name: flux
     namespace: flux-system
   spec:
     sync:
       kind: GitRepository
       url: "https://github.com/your-org/gitops-infra-control-plane"
       ref: "refs/heads/main"
       path: "infrastructure/tenants"
     distribution:
       version: "2.x"
       registry: "ghcr.io/fluxcd"
     components:
       - source-controller
       - kustomize-controller
       - helm-controller
     cluster:
       type: kubernetes
       size: medium
   ```

4. **Migrate Applications**
   ```yaml
   apiVersion: fluxcd.controlplane.io/v1
   kind: ResourceSet
   metadata:
     name: applications
     namespace: flux-system
   spec:
     resources:
     - name: app1
       kind: Kustomization
       path: applications/app1
     - name: app2
       kind: HelmRelease
       path: applications/app2
   ```

## Performance Optimization

### 1. Controller Sizing

```yaml
spec:
  cluster:
    size: large
    sharding:
      enabled: true
      shards: 3
  kustomize:
    patch: |
      - patch: |
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: source-controller
            namespace: flux-system
          spec:
            template:
              spec:
                containers:
                - name: manager
                  resources:
                    requests:
                      cpu: 200m
                      memory: 512Mi
                    limits:
                      cpu: 1000m
                      memory: 1Gi
        target:
          kind: Kustomization
          name: flux-components
          namespace: flux-system
```

### 2. Sync Optimization

```yaml
spec:
  sync:
    interval: "10m"
    timeout: "5m"
    healthChecks:
      enabled: false  # Disable for better performance
  kustomize:
    patch: |
      - patch: |
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: kustomize-controller
            namespace: flux-system
          spec:
            template:
              spec:
                containers:
                - name: manager
                  env:
                  - name: KUSTOMIZE_CONTROLLER_NO_HEALTH_CHECK
                    value: "true"
        target:
          kind: Kustomization
          name: flux-components
          namespace: flux-system
```

### 3. Resource Limits

```yaml
spec:
  kustomize:
    patch: |
      - patch: |
          apiVersion: v1
          kind: LimitRange
          metadata:
            name: flux-controller-limits
            namespace: flux-system
          spec:
            limits:
            - default:
                cpu: 500m
                memory: 512Mi
              defaultRequest:
                cpu: 100m
                memory: 128Mi
              type: Container
        target:
          kind: Kustomization
          name: flux-components
          namespace: flux-system
```

## Security Hardening

### 1. Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: flux-system-netpol
  namespace: flux-system
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  # Allow metrics
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 8080
  # Allow webhooks
  - from: []
    ports:
    - protocol: TCP
      port: 9292
  egress:
  # Allow DNS
  - to: []
    ports:
    - protocol: UDP
      port: 53
  # Allow HTTPS
  - to: []
    ports:
    - protocol: TCP
      port: 443
```

### 2. RBAC Configuration

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: flux-operator-controller
rules:
- apiGroups: ["fluxcd.controlplane.io"]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["source.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["kustomize.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["helm.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: flux-operator-controller
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: flux-operator-controller
subjects:
- kind: ServiceAccount
  name: flux-operator
  namespace: flux-system
```

### 3. Secret Management

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: sops-keys
  namespace: flux-system
stringData:
  age.agekey: |
    # created: 2023-01-01T00:00:00Z
    # public key: age1ql3z7hjy64pw3dw93p4j8k2tq6s8r9x0y2z1w2v3u4x5y6z7a8b9c0d1e2f3
    AGE-SECRET-KEY-1abc2def3ghi4jkl5mno6pqr7stu8vwx9yz0abc1def2ghi3jkl4mno5pqr6stu7vwx8yz9abc2def3ghi4jkl5mno6pqr7stu8vwx9yz0abc
---
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
spec:
  security:
    encryption:
      enabled: true
      provider: sops
      secretRef:
        name: sops-keys
```

## Monitoring and Observability

### 1. Prometheus Metrics

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: flux-operator
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: flux
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
```

### 2. Alerting Rules

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: flux-operator-alerts
  namespace: flux-system
spec:
  groups:
  - name: flux-operator
    rules:
    - alert: FluxOperatorDown
      expr: up{job="flux-operator"} == 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Flux Operator is down"
        description: "Flux Operator has been down for more than 5 minutes"
    - alert: FluxInstanceReconciliationFailure
      expr: flux_instance_reconcile_failed_total > 0
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "FluxInstance reconciliation failure"
        description: "FluxInstance {{ $labels.name }} has failed {{ $value }} times"
```

### 3. Dashboard Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-operator-dashboard
  namespace: flux-system
  labels:
    grafana_dashboard: "1"
data:
  flux-operator.json: |
    {
      "dashboard": {
        "title": "Flux Operator Overview",
        "panels": [
          {
            "title": "Flux Instances",
            "type": "stat",
            "targets": [
              {
                "expr": "count(flux_instance_status_condition{condition=\"Ready\"})",
                "legendFormat": "Ready Instances"
              }
            ]
          },
          {
            "title": "Reconciliation Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(flux_instance_reconcile_total[5m])",
                "legendFormat": "{{instance}}"
              }
            ]
          }
        ]
      }
    }
```

## Conclusion

This comprehensive guide provides everything needed to successfully implement and operate Flux Operator for the GitOps Infrastructure Control Plane. The Flux Operator simplifies Flux CD management while providing powerful features for advanced GitOps operations.

Key benefits of using Flux Operator:

1. **Simplified Installation**: Single command installation with sensible defaults
2. **Declarative Configuration**: YAML-based configuration for all Flux components
3. **Built-in Monitoring**: Integrated Prometheus metrics and alerting
4. **Multi-Tenant Support**: Native support for multi-tenant environments
5. **MCP Integration**: Agentic GitOps capabilities with AI assistants
6. **High Availability**: Built-in support for controller sharding and HA
7. **Security Features**: RBAC, encryption, and network policies

For more information and support, refer to the official Flux Operator documentation and community resources.

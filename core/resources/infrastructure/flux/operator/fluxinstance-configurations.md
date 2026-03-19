# FluxInstance Configurations

This directory contains FluxInstance CRD configurations for different deployment scenarios of the GitOps Infra Control Plane.

## Basic FluxInstance

### flux-instance-basic.yaml

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux
    app.kubernetes.io/component: gitops
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  distribution:
    version: "2.x"
    registry: "ghcr.io/fluxcd"
    artifact: "oci://ghcr.io/controlplaneio-fluxcd/flux-operator-manifests"
  components:
    - source-controller
    - source-watcher
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

## Production FluxInstance

### flux-instance-production.yaml

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux
    app.kubernetes.io/component: gitops
    app.kubernetes.io/part-of: agentic-reconciliation-engine
    environment: production
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
  kustomize:
    patch: |
      # Resource limits for production
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
      # Add custom annotations
      - patch: |
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: kustomize-controller
            namespace: flux-system
            annotations:
              prometheus.io/scrape: "true"
              prometheus.io/port: "8080"
              prometheus.io/path: "/metrics"
        target:
          kind: Kustomization
          name: flux-components
          namespace: flux-system
```

## Development FluxInstance

### flux-instance-development.yaml

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux
    app.kubernetes.io/component: gitops
    app.kubernetes.io/part-of: agentic-reconciliation-engine
    environment: development
spec:
  distribution:
    version: "2.x"
    registry: "ghcr.io/fluxcd"
    artifact: "oci://ghcr.io/controlplaneio-fluxcd/flux-operator-manifests"
  components:
    - source-controller
    - kustomize-controller
    - helm-controller
  cluster:
    type: kubernetes
    size: small
    multitenant: false
    networkPolicy: false
    domain: "cluster.local"
  kustomize:
    patch: |
      # Development overrides
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
                  env:
                  - name: LOG_LEVEL
                    value: debug
                  - name: LEADER_ELECTION_LEASE_DURATION
                    value: 15s
        target:
          kind: Kustomization
          name: flux-components
          namespace: flux-system
```

## Multi-Tenant FluxInstance

### flux-instance-multitenant.yaml

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux
    app.kubernetes.io/component: gitops
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  distribution:
    version: "2.x"
    registry: "ghcr.io/fluxcd"
    artifact: "oci://ghcr.io/controlplaneio-fluxcd/flux-operator-manifests"
  components:
    - source-controller
    - source-watcher
    - kustomize-controller
    - helm-controller
    - notification-controller
  cluster:
    type: kubernetes
    size: medium
    multitenant: true
    networkPolicy: true
    domain: "cluster.local"
    sharding:
      enabled: true
      shards: 2
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
      # Network policies for multi-tenant
      - patch: |
          apiVersion: networking.k8s.io/v1
          kind: NetworkPolicy
          metadata:
            name: allow-tenant-isolation
            namespace: flux-system
          spec:
            podSelector: {}
            policyTypes:
            - Egress
            egress:
            - to:
              - namespaceSelector:
                  matchLabels:
                    name: flux-system
              - namespaceSelector:
                  matchLabels:
                    name: kube-system
        target:
          kind: Kustomization
          name: flux-components
          namespace: flux-system
```

## High-Availability FluxInstance

### flux-instance-ha.yaml

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux
    app.kubernetes.io/component: gitops
    app.kubernetes.io/part-of: agentic-reconciliation-engine
    availability: high
spec:
  distribution:
    version: "2.x"
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
    multitenant: false
    networkPolicy: true
    domain: "cluster.local"
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
      # Pod disruption budgets
      - patch: |
          apiVersion: policy/v1
          kind: PodDisruptionBudget
          metadata:
            name: source-controller-pdb
            namespace: flux-system
          spec:
            minAvailable: 2
            selector:
              matchLabels:
                app.kubernetes.io/name: source-controller
        target:
          kind: Kustomization
          name: flux-components
          namespace: flux-system
```

## Edge Computing FluxInstance

### flux-instance-edge.yaml

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux
    app.kubernetes.io/component: gitops
    app.kubernetes.io/part-of: agentic-reconciliation-engine
    deployment: edge
spec:
  distribution:
    version: "2.x"
    registry: "ghcr.io/fluxcd"
    artifact: "oci://ghcr.io/controlplaneio-fluxcd/flux-operator-manifests"
  components:
    - source-controller
    - kustomize-controller
  cluster:
    type: kubernetes
    size: small
    multitenant: false
    networkPolicy: false
    domain: "cluster.local"
  kustomize:
    patch: |
      # Edge computing optimizations
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
                      cpu: 50m
                      memory: 128Mi
                    limits:
                      cpu: 200m
                      memory: 256Mi
                  env:
                  - name: SOURCE_CONTROLLER_INTERVAL
                    value: "10m"
                  - name: SOURCE_CONTROLLER_TIMEOUT
                    value: "30s"
        target:
          kind: Kustomization
          name: flux-components
          namespace: flux-system
      # Disable expensive features for edge
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
                  - name: KUSTOMIZE_CONTROLLER_NO_PRUNE
                    value: "true"
        target:
          kind: Kustomization
          name: flux-components
          namespace: flux-system
```

## Custom Registry FluxInstance

### flux-instance-custom-registry.yaml

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux
    app.kubernetes.io/component: gitops
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  distribution:
    version: "2.x"
    registry: "your-registry.example.com/fluxcd"
    artifact: "oci://your-registry.example.com/fluxcd/flux-operator-manifests"
  components:
    - source-controller
    - kustomize-controller
    - helm-controller
  cluster:
    type: kubernetes
    size: medium
    multitenant: false
    networkPolicy: true
    domain: "cluster.local"
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
      # Image pull secrets
      - patch: |
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: source-controller
            namespace: flux-system
          spec:
            template:
              spec:
                imagePullSecrets:
                - name: registry-credentials
        target:
          kind: Kustomization
          name: flux-components
          namespace: flux-system
```

## Usage Instructions

### Apply a FluxInstance

```bash
# Apply basic configuration
kubectl apply -f flux-instance-basic.yaml

# Apply production configuration
kubectl apply -f flux-instance-production.yaml

# Check status
kubectl get fluxinstance flux -n flux-system -o yaml
```

### Monitor FluxInstance

```bash
# Watch FluxInstance status
kubectl get fluxinstance flux -n flux-system -w

# Check component status
kubectl get pods -n flux-system -l app.kubernetes.io/name=flux

# View logs
kubectl logs -n flux-system deployment/flux-operator
```

### Update FluxInstance

```bash
# Update configuration
kubectl apply -f flux-instance-production.yaml

# Force reconciliation
kubectl patch fluxinstance flux -n flux-system --type=merge -p '{"spec":{"reconcileAt":"'$(date -u +'%Y-%m-%dT%H:%M:%SZ')'"}}'
```

### Delete FluxInstance

```bash
# Delete FluxInstance
kubectl delete fluxinstance flux -n flux-system

# This will also remove all Flux components
```

## Configuration Options

### Distribution

- **version**: Flux version to install (e.g., "2.x", "2.2.x")
- **registry**: Container registry for Flux images
- **artifact**: OCI artifact URL for Flux manifests

### Components

Available components:
- source-controller
- source-watcher
- kustomize-controller
- helm-controller
- notification-controller
- image-reflector-controller
- image-automation-controller

### Cluster Configuration

- **type**: Kubernetes cluster type
- **size**: small, medium, large
- **multitenant**: Enable multi-tenant mode
- **networkPolicy**: Enable network policies
- **domain**: Cluster domain

### Advanced Features

- **sharding**: Enable controller sharding
- **highAvailability**: Configure HA settings
- **security**: RBAC and encryption settings
- **monitoring**: Prometheus and alerting configuration
- **kustomize**: Custom patches and overrides

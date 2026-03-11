# Flux Source and Reconciliation Workflows

This guide covers Flux CD source management and reconciliation workflows, including detailed explanations of how sources work, reconciliation patterns, and best practices for the GitOps Infrastructure Control Plane.

## Source Types Overview

Flux supports multiple source types for acquiring configuration data:

### 1. GitRepository

The most common source type for Git-based configuration.

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: gitops-infra-control-plane
  namespace: flux-system
spec:
  interval: 5m
  url: https://github.com/your-org/gitops-infra-control-plane
  ref:
    branch: main
  ignore: |
    # Exclude build artifacts and temporary files
    *.tar.gz
    *.tmp
    build/
    dist/
    .git/
    # Include only relevant directories
    !infrastructure/
    !control-plane/
    !apps/
  gitImplementation: go-git
  timeout: 60s
  recurseSubmodules: false
```

### 2. OCIRepository

Modern OCI-compliant source for container registries.

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: OCIRepository
metadata:
  name: helm-charts
  namespace: flux-system
spec:
  interval: 10m
  url: oci://ghcr.io/your-org/helm-charts
  ref:
    tag: latest
    semver: ">=1.0.0"
  verify:
    provider: cosign
    secretRef:
      name: cosign-pub
  timeout: 60s
  ignore: |
    # Exclude test artifacts
    test/
    *.test.*
```

### 3. HelmRepository

For Helm chart repositories.

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: HelmRepository
metadata:
  name: bitnami
  namespace: flux-system
spec:
  interval: 10m
  url: https://charts.bitnami.com/bitnami
  timeout: 60s
  passCredentials: false
  secretRef:
    name: helm-registry-credentials
```

### 4. Bucket

For object storage sources (S3, GCS, Azure Blob).

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: Bucket
metadata:
  name: s3-configs
  namespace: flux-system
spec:
  interval: 5m
  provider: aws
  bucketName: gitops-configs
  region: us-west-2
  endpoint: s3.amazonaws.com
  timeout: 60s
  secretRef:
    name: s3-credentials
  ignore: |
    # Exclude temporary files
    tmp/
    *.tmp
```

## Source Authentication

### SSH Authentication for GitRepository

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: gitops-infra-control-plane
  namespace: flux-system
spec:
  interval: 5m
  url: ssh://git@github.com/your-org/gitops-infra-control-plane.git
  ref:
    branch: main
  secretRef:
    name: git-ssh-credentials
---
apiVersion: v1
kind: Secret
metadata:
  name: git-ssh-credentials
  namespace: flux-system
stringData:
  identity: |
    -----BEGIN OPENSSH PRIVATE KEY-----
    ...
    -----END OPENSSH PRIVATE KEY-----
  known_hosts: |
    github.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC...
```

### HTTPS Authentication for GitRepository

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: gitops-infra-control-plane
  namespace: flux-system
spec:
  interval: 5m
  url: https://github.com/your-org/gitops-infra-control-plane.git
  ref:
    branch: main
  secretRef:
    name: git-https-credentials
---
apiVersion: v1
kind: Secret
metadata:
  name: git-https-credentials
  namespace: flux-system
stringData:
  username: your-username
  password: your-personal-access-token
```

### TLS Certificate Verification

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: gitops-infra-control-plane
  namespace: flux-system
spec:
  interval: 5m
  url: https://git.internal.com/infra/control-plane.git
  ref:
    branch: main
  certSecretRef:
    name: git-ca-certificates
  secretRef:
    name: git-credentials
---
apiVersion: v1
kind: Secret
metadata:
  name: git-ca-certificates
  namespace: flux-system
stringData:
  caFile: |
    -----BEGIN CERTIFICATE-----
    ...
    -----END CERTIFICATE-----
```

## Reconciliation Workflows

### Reconciliation Triggers

Flux sources can be reconciled through multiple triggers:

#### 1. Interval-Based Reconciliation

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: gitops-infra-control-plane
  namespace: flux-system
spec:
  interval: 5m  # Reconcile every 5 minutes
  url: https://github.com/your-org/gitops-infra-control-plane.git
  ref:
    branch: main
```

#### 2. Webhook-Based Reconciliation

```yaml
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Receiver
metadata:
  name: github-receiver
  namespace: flux-system
spec:
  type: github
  events:
    - "push"
    - "pull_request"
  resources:
    - kind: GitRepository
      name: gitops-infra-control-plane
      namespace: flux-system
  secretRef:
    name: github-webhook-token
---
apiVersion: v1
kind: Secret
metadata:
  name: github-webhook-token
  namespace: flux-system
stringData:
  token: "your-github-webhook-secret"
  address: "https://your-flux-webhook-url"
```

#### 3. Manual Reconciliation

```bash
# Reconcile a specific GitRepository
flux reconcile source git gitops-infra-control-plane

# Reconcile all sources
flux reconcile source all

# Reconcile with force flag
flux reconcile source git gitops-infra-control-plane --with-source
```

### Reconciliation Status and Conditions

```yaml
# Example GitRepository status
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: gitops-infra-control-plane
  namespace: flux-system
status:
  conditions:
  - lastTransitionTime: "2023-01-01T00:00:00Z"
    message: 'Fetched revision: main/sha256:abc123'
    observedGeneration: 1
    reason: GitOperationSucceed
    status: "True"
    type: Ready
  - lastTransitionTime: "2023-01-01T00:00:00Z"
    message: 'no conflict with artifact'
    observedGeneration: 1
    reason: Succeed
    status: "True"
    type: ArtifactOutdated
  artifact:
    checksum: sha256:abc123...
    lastUpdateTime: "2023-01-01T00:00:00Z"
    path: gitops-infra-control-plane/sha256:abc123.tar.gz
    revision: main/sha256:abc123
    size: 1234567
  observedGeneration: 1
```

## Kustomization Reconciliation

### Basic Kustomization

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: infrastructure-networks
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: gitops-infra-control-plane
  path: ./infrastructure/tenants/1-network
  prune: true
  wait: true
  timeout: 5m
  retryInterval: 2m
```

### Advanced Kustomization Features

#### Dependency Management

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: infrastructure-workloads
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: gitops-infra-control-plane
  path: ./infrastructure/tenants/3-workloads
  prune: true
  wait: true
  timeout: 15m
  dependsOn:
    - name: infrastructure-networks
    - name: infrastructure-clusters
  healthChecks:
    - kind: Deployment
      name: network-controller
      namespace: network-system
    - kind: Service
      name: cluster-api
      namespace: cluster-system
```

#### Secret Decryption

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: infrastructure-workloads
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: gitops-infra-control-plane
  path: ./infrastructure/tenants/3-workloads
  prune: true
  wait: true
  timeout: 15m
  decryption:
    provider: sops
    secretRef:
      name: sops-keys
---
apiVersion: v1
kind: Secret
metadata:
  name: sops-keys
  namespace: flux-system
stringData:
  age.agekey: |
    # created: 2023-01-01T00:00:00Z
    # public key: age1...
    AGE-SECRET-KEY-1...
```

#### Post-Build Substitution

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: infrastructure-workloads
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: gitops-infra-control-plane
  path: ./infrastructure/tenants/3-workloads
  prune: true
  wait: true
  timeout: 15m
  postBuild:
    substitute:
      CLUSTER_NAME: "production"
      ENVIRONMENT: "prod"
      REGION: "us-west-2"
    substituteFrom:
    - kind: ConfigMap
      name: cluster-config
    - kind: Secret
      name: cluster-secrets
      optional: true
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-config
  namespace: flux-system
data:
  DOMAIN: "example.com"
  TLS_VERSION: "1.3"
```

## Helm Reconciliation

### Basic HelmRelease

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: cert-manager
  namespace: flux-system
spec:
  interval: 10m
  chartRef:
    kind: HelmChart
    name: cert-manager-chart
  targetNamespace: cert-manager
  install:
    remediation:
      retries: 3
  upgrade:
    remediation:
      retries: 3
    cleanupOnFail: true
  values:
    installCRDs: true
    prometheus:
      enabled: true
```

### Advanced Helm Features

#### Custom Chart Sources

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: HelmChart
metadata:
  name: custom-app-chart
  namespace: flux-system
spec:
  interval: 10m
  chart: ./chart
  version: ">=1.0.0"
  sourceRef:
    kind: GitRepository
    name: app-source
  reconcileStrategy: ChartVersion
  valuesFiles:
  - values-prod.yaml
  - values-secrets.yaml
---
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: custom-app
  namespace: flux-system
spec:
  interval: 10m
  chartRef:
    kind: HelmChart
    name: custom-app-chart
  targetNamespace: production
  valuesFrom:
  - kind: ConfigMap
    name: app-values
    valuesKey: values.yaml
  - kind: Secret
    name: app-secrets
    valuesKey: secrets.yaml
    optional: true
```

#### Post-Rendering with Kustomize

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: app-with-post-render
  namespace: flux-system
spec:
  interval: 10m
  chartRef:
    kind: HelmChart
    name: app-chart
  targetNamespace: production
  postRenderers:
  - kustomize:
      patchesStrategicMerge:
      - |-
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: app
          annotations:
            prometheus.io/scrape: "true"
            prometheus.io/port: "8080"
        spec:
          template:
            spec:
              containers:
              - name: app
                env:
                - name: LOG_LEVEL
                  value: "info"
```

## Multi-Source Workflows

### Composite Source Pattern

```yaml
# Infrastructure source
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: infrastructure-source
  namespace: flux-system
spec:
  interval: 5m
  url: https://github.com/your-org/infrastructure-manifests
  ref:
    branch: main
---
# Application source
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: application-source
  namespace: flux-system
spec:
  interval: 5m
  url: https://github.com/your-org/application-manifests
  ref:
    branch: main
---
# Infrastructure kustomization
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: infrastructure
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: infrastructure-source
  path: ./infrastructure
  prune: true
  wait: true
  timeout: 10m
---
# Application kustomization
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: applications
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: application-source
  path: ./applications
  prune: true
  wait: true
  timeout: 15m
  dependsOn:
    - name: infrastructure
```

### Source Hierarchy

```yaml
# Base configuration source
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: base-config
  namespace: flux-system
spec:
  interval: 10m
  url: https://github.com/your-org/base-config
  ref:
    branch: main
---
# Environment-specific source
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: production-config
  namespace: flux-system
spec:
  interval: 5m
  url: https://github.com/your-org/production-config
  ref:
    branch: main
---
# Base kustomization
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: base-infrastructure
  namespace: flux-system
spec:
  interval: 15m
  sourceRef:
    kind: GitRepository
    name: base-config
  path: ./base/infrastructure
  prune: false
  wait: true
---
# Production overlay
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: production-infrastructure
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: production-config
  path: ./overlays/production/infrastructure
  prune: true
  wait: true
  dependsOn:
    - name: base-infrastructure
```

## Reconciliation Patterns

### 1. Sequential Reconciliation

```yaml
# Network infrastructure
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: network-infrastructure
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: gitops-infra-control-plane
  path: ./infrastructure/tenants/1-network
  prune: true
  wait: true
  timeout: 5m
---
# Cluster infrastructure (depends on network)
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: cluster-infrastructure
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: gitops-infra-control-plane
  path: ./infrastructure/tenants/2-clusters
  prune: true
  wait: true
  timeout: 10m
  dependsOn:
    - name: network-infrastructure
---
# Workloads (depends on clusters)
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: workloads
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: gitops-infra-control-plane
  path: ./infrastructure/tenants/3-workloads
  prune: true
  wait: true
  timeout: 15m
  dependsOn:
    - name: cluster-infrastructure
```

### 2. Parallel Reconciliation

```yaml
# Independent workloads can reconcile in parallel
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: frontend-apps
  namespace: flux-system
spec:
  interval: 5m
  sourceRef:
    kind: GitRepository
    name: gitops-infra-control-plane
  path: ./apps/frontend
  prune: true
  wait: true
  timeout: 10m
---
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: backend-apps
  namespace: flux-system
spec:
  interval: 5m
  sourceRef:
    kind: GitRepository
    name: gitops-infra-control-plane
  path: ./apps/backend
  prune: true
  wait: true
  timeout: 10m
---
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: monitoring-stack
  namespace: flux-system
spec:
  interval: 5m
  sourceRef:
    kind: GitRepository
    name: gitops-infra-control-plane
  path: ./monitoring
  prune: true
  wait: true
  timeout: 10m
```

### 3. Conditional Reconciliation

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: production-workloads
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: gitops-infra-control-plane
  path: ./workloads/production
  prune: true
  wait: true
  timeout: 15m
  # Only reconcile if production flag is set
  suspend: false
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: deployment-flags
  namespace: flux-system
data:
  production_enabled: "true"
  staging_enabled: "true"
  development_enabled: "false"
```

## Health Checking and Validation

### Health Check Configuration

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: critical-apps
  namespace: flux-system
spec:
  interval: 5m
  sourceRef:
    kind: GitRepository
    name: gitops-infra-control-plane
  path: ./apps/critical
  prune: true
  wait: true
  timeout: 20m
  healthChecks:
  # Deployment health checks
  - kind: Deployment
    name: api-server
    namespace: production
    fieldPath: .status.readyReplicas
    value: "3"
  - kind: Deployment
    name: web-server
    namespace: production
    fieldPath: .status.readyReplicas
    value: "2"
  # Service health checks
  - kind: Service
    name: api-service
    namespace: production
  # Ingress health checks
  - kind: Ingress
    name: api-ingress
    namespace: production
  # Custom resource health checks
  - kind: Certificate
    name: api-tls
    namespace: production
```

### Validation Strategies

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: validated-workloads
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: gitops-infra-control-plane
  path: ./workloads/validated
  prune: true
  wait: true
  timeout: 15m
  # Validation before apply
  validation:
    client: true
    # Use dry-run to validate
  # Post-build validation
  postBuild:
    substitute:
      ENVIRONMENT: "production"
      CLUSTER_NAME: "prod-cluster"
```

## Troubleshooting Reconciliation Issues

### Common Source Issues

#### 1. Authentication Failures

```bash
# Check GitRepository status
kubectl get gitrepository gitops-infra-control-plane -n flux-system -o yaml

# Check secret references
kubectl get secret git-credentials -n flux-system -o yaml

# Test connectivity
flux reconcile source git gitops-infra-control-plane --with-source
```

#### 2. Network Connectivity

```bash
# Check source controller logs
kubectl logs -n flux-system deployment/source-controller

# Test repository access
curl -I https://github.com/your-org/gitops-infra-control-plane

# Check webhook configuration
kubectl get receiver github-receiver -n flux-system -o yaml
```

#### 3. Artifact Issues

```bash
# Check artifact status
flux get artifacts

# Force artifact recreation
flux reconcile source git gitops-infra-control-plane

# Check artifact storage
kubectl get artifacts.source.toolkit.fluxcd.io -n flux-system
```

### Common Kustomization Issues

#### 1. Build Failures

```bash
# Build kustomization locally
flux build kustomization infrastructure-networks --path=./infrastructure/tenants/1-network

# Check kustomization status
kubectl get kustomization infrastructure-networks -n flux-system -o yaml

# Validate manifests
kubectl apply --dry-run=client -k ./infrastructure/tenants/1-network
```

#### 2. Dependency Issues

```bash
# Check dependency status
flux get kustomizations -n flux-system

# Force dependency reconciliation
flux reconcile kustomization infrastructure-workloads --with-source

# Check dependency graph
kubectl get kustomization -n flux-system -o custom-columns=NAME:.metadata.name,DEPS:.spec.dependsOn[*].name
```

#### 3. Health Check Failures

```bash
# Check health check status
kubectl get kustomization critical-apps -n flux-system -o yaml

# Manually check resource health
kubectl get deployments -n production
kubectl get services -n production
kubectl get ingress -n production
```

## Performance Optimization

### Source Optimization

```yaml
# Optimized GitRepository
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: gitops-infra-control-plane
  namespace: flux-system
spec:
  interval: 10m  # Longer interval for stability
  url: https://github.com/your-org/gitops-infra-control-plane
  ref:
    branch: main
  ignore: |
    # Exclude unnecessary files
    *.log
    *.tmp
    docs/
    test/
    .github/
    # Optimize for specific paths
    !infrastructure/
    !control-plane/
  gitImplementation: go-git  # More efficient than libgit2
  timeout: 30s
```

### Kustomization Optimization

```yaml
# Optimized Kustomization
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: infrastructure-workloads
  namespace: flux-system
spec:
  interval: 15m  # Longer interval for complex workloads
  sourceRef:
    kind: GitRepository
    name: gitops-infra-control-plane
  path: ./infrastructure/tenants/3-workloads
  prune: true
  wait: false  # Disable waiting for faster reconciliation
  timeout: 10m
  retryInterval: 3m  # Retry interval for failed reconciliations
  # Parallel processing
  patchesStrategicMerge: []
  # Optimized health checks
  healthChecks:
  - kind: Deployment
    name: critical-app
    namespace: production
```

### Resource Optimization

```yaml
# Controller resource optimization
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
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        env:
        - name: KUSTOMIZE_CONTROLLER_CONCURRENCY
          value: "4"  # Increase concurrency
```

## Best Practices

### Source Management

1. **Use Specific Paths**: Configure specific paths to reduce artifact size
2. **Implement .sourceignore**: Exclude unnecessary files
3. **Optimize Intervals**: Balance responsiveness with resource usage
4. **Use Webhooks**: Enable instant reconciliation for critical sources

### Reconciliation Patterns

1. **Explicit Dependencies**: Use `dependsOn` for clear dependency chains
2. **Health Checks**: Configure comprehensive health checks
3. **Timeout Configuration**: Set appropriate timeouts for complex workloads
4. **Retry Logic**: Configure retry intervals for resilience

### Performance Optimization

1. **Artifact Size**: Minimize artifact size through proper filtering
2. **Parallel Processing**: Enable parallel reconciliation where possible
3. **Resource Limits**: Configure appropriate resource limits
4. **Monitoring**: Monitor reconciliation performance and metrics

### Security Practices

1. **Authentication**: Use secure authentication methods
2. **TLS Verification**: Enable certificate verification
3. **Secret Management**: Encrypt secrets with SOPS
4. **Network Policies**: Implement strict network isolation

---

This comprehensive guide covers all aspects of Flux source management and reconciliation workflows, providing the foundation for robust and efficient GitOps operations in the GitOps Infrastructure Control Plane.

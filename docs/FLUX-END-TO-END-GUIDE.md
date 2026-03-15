# Strategic Architecture Context

**Strategic Architecture: Flux + Temporal + Consensus Hybrid Approach**

This file provides end-to-end guidance for Flux implementation within the hybrid architecture.

**North Star Vision**: Establish a reference implementation for autonomous, self-organizing infrastructure management.

**Current Status**: Documenting complete Flux integration and deployment patterns.

**Strategic Plan**: See [docs/STRATEGIC-ARCHITECTURE.md](docs/STRATEGIC-ARCHITECTURE.md) for comprehensive roadmap.

---

# Flux End-to-End Implementation Guide

This guide provides a comprehensive overview of Flux CD's end-to-end architecture and implementation for the GitOps Infra Control Plane, updated for Flux v2.0+ with modern practices and OCIRepository support.

## Overview

Flux CD is a declarative, GitOps continuous delivery tool for Kubernetes that automates the deployment lifecycle. This guide covers the complete flow of data through Flux, from Git commits to cluster deployments, including all controller interactions and security considerations.

## Architecture Overview

### Core Components

Flux consists of six main controllers that work together to provide a complete GitOps solution:

1. **Source Controller**: Acquires and stores artifacts from external sources
2. **Kustomize Controller**: Reconciles Kustomize-based deployments
3. **Helm Controller**: Manages Helm releases with full compatibility
4. **Notification Controller**: Handles inbound/outbound events and notifications
5. **Image Reflector Controller**: Scans image repositories and reflects metadata
6. **Image Automation Controller**: Automates Git commits for image updates

### Microservice Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  flux-system Namespace                  │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐  │   │
│  │  │ Source      │ │ Kustomize   │ │ Helm            │  │   │
│  │  │ Controller  │ │ Controller  │ │ Controller      │  │   │
│  │  └─────────────┘ └─────────────┘ └─────────────────┘  │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐  │   │
│  │  │ Notification│ │ Image       │ │ Image           │  │   │
│  │  │ Controller  │ │ Reflector   │ │ Automation      │  │   │
│  │  └─────────────┘ └─────────────┘ └─────────────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Overview

### Git Commit Lifecycle

The complete lifecycle of a change from Git commit to cluster deployment:

1. **Developer Commit**: Changes are pushed to Git repository
2. **Webhook Trigger**: Git provider sends webhook to Flux Receiver
3. **Source Acquisition**: Source Controller fetches the latest commit
4. **Artifact Creation**: Source creates compressed artifact (.tar.gz)
5. **Manifest Building**: Kustomize/Helm controllers build manifests
6. **Validation**: Resources are validated against Kubernetes API
7. **Application**: Changes are applied using Server-Side Apply
8. **Health Checking**: Controllers wait for resources to become ready
9. **Status Updates**: Status is updated and events are emitted
10. **Notifications**: External systems are notified of changes

### Detailed Flow Diagram

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Git      │───▶│   Flux      │───▶   Source    │───▶   Artifact   │
│ Repository  │    │   Receiver  │    │ Controller  │    │   Storage    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Notification │    │ Kustomize   │    │   Helm      │    │ Kubernetes  │
│ Controller  │◀───│ Controller  │◀───│ Controller  │◀───│   API       │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## Component Deep Dive

### 1. Source Controller

**Purpose**: Acquires and stores artifacts from external sources in a read-only format.

**Supported Sources**:

- **GitRepository**: Git repositories (GitHub, GitLab, Bitbucket, etc.)
- **Bucket**: S3, GCS, and other object storage services
- **HelmRepository**: Helm chart repositories
- **OCIRepository**: OCI-compliant registries (new in v2.0+)

**Key Features**:

- Cryptographic signature verification (PGP, Cosign)
- Semantic version filtering
- Webhook-based instant reconciliation
- Artifact compression and caching
- Multi-tenant support with namespace isolation

**Configuration Example**:

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
    # Exclude build artifacts
    *.tar.gz
    build/
    # Include only infrastructure manifests
    !infrastructure/
    !control-plane/
  gitImplementation: go-git
  timeout: 60s
```

**OCIRepository Example (v2.0+)**:

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
  verify:
    provider: cosign
    secretRef:
      name: cosign-pub
```

### 2. Kustomize Controller

**Purpose**: Reconciles cluster state with Kustomize-based manifests from sources.

**Key Features**:

- Server-Side Apply for efficient updates
- Dependency ordering with `dependsOn`
- Health checking and readiness validation
- Secret decryption with SOPS
- Multi-cluster deployment support
- Prune/garbage collection

**Configuration Example**:

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
  dependsOn:
    - name: flux-system
  decryption:
    provider: sops
    secretRef:
      name: sops-keys
  postBuild:
    substitute:
      CLUSTER_NAME: "production"
      ENVIRONMENT: "prod"
    substituteFrom:
      - kind: ConfigMap
        name: cluster-config
```

### 3. Helm Controller

**Purpose**: Manages Helm releases with full upstream compatibility.

**Key Features**:

- Complete Helm client library compatibility
- Chart hooks and lifecycle events
- Post-rendering with Kustomize
- Rollback and uninstall capabilities
- Helm test execution
- Multi-source chart acquisition

**Configuration Example**:

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
  postRenderers:
    - kustomize:
        patchesStrategicMerge:
          - |-
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: cert-manager
              annotations:
                prometheus.io/scrape: "true"
```

### 4. Notification Controller

**Purpose**: Handles inbound events and outbound notifications.

**Capabilities**:

- Webhook receivers for instant reconciliation
- Multi-platform notifications (Slack, Teams, Discord)
- Git commit status updates
- Event filtering and routing
- Rate limiting and deduplication

**Receiver Configuration**:

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
```

**Provider Configuration**:

```yaml
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Provider
metadata:
  name: slack-provider
  namespace: flux-system
spec:
  type: slack
  channel: "#gitops-alerts"
  address: https://hooks.slack.com/services/...
  secretRef:
    name: slack-webhook-url
```

### 5. Image Reflector Controller

**Purpose**: Scans image repositories and reflects metadata in Kubernetes.

**Features**:

- Multi-registry support (Docker Hub, GHCR, ECR, GCR, etc.)
- Authentication and TLS configuration
- Tag filtering and sorting
- Policy-based image selection

**Configuration Example**:

```yaml
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageRepository
metadata:
  name: app-images
  namespace: flux-system
spec:
  interval: 5m
  image: ghcr.io/your-org/my-app
  secretRef:
    name: ghcr-credentials
  certSecretRef:
    name: registry-ca
  timeout: 1m
---
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImagePolicy
metadata:
  name: app-latest
  namespace: flux-system
spec:
  imageRepositoryRef:
    name: app-images
  policy:
    semver:
      range: ">=1.0.0"
  filterTags:
    pattern: '^v?[0-9]+\.[0-9]+\.[0-9]+$'
    extract: '$ts'
```

### 6. Image Automation Controller

**Purpose**: Automates Git commits for image updates.

**Features**:

- Automated manifest updates
- Commit message customization
- Branch management
- Multi-policy support

**Configuration Example**:

```yaml
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageUpdateAutomation
metadata:
  name: app-updates
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: gitops-infra-control-plane
  git:
    checkout:
      ref:
        branch: main
    commit:
      author:
        email: flux-bot@users.noreply.github.com
        name: fluxcd-bot
      messageTemplate: |
        🚀 Automated image update
        
        {{range .Updated.Images}}
        - Image: {{.Repository}}:{{.Tag}}
        - Digest: {{.Digest}}
        {{end}}
        
        This commit was automatically generated by Flux.
    push:
      branch: staging
  update:
    path: ./infrastructure/tenants/3-workloads
    strategy: Setters
```

## Bootstrap Process

### Overview

Bootstrapping is the process of installing Flux so that Flux manages itself. This is the recommended approach for new installations.

### Bootstrap Steps

1. **Prerequisites**: Kubernetes cluster and kubectl configured
2. **Repository Setup**: Create or use existing Git repository
3. **Authentication**: Configure Git credentials (SSH/HTTPS)
4. **Bootstrap Execution**: Run `flux bootstrap` command
5. **Validation**: Verify Flux installation and reconciliation

### Bootstrap Commands

```bash
# Bootstrap with GitHub (SSH)
flux bootstrap github \
  --owner=your-org \
  --repository=gitops-infra-control-plane \
  --branch=main \
  --path=./clusters/production \
  --personal

# Bootstrap with Git (generic)
flux bootstrap git \
  --url=ssh://git@github.com/your-org/gitops-infra-control-plane.git \
  --branch=main \
  --path=./clusters/production \
  --private-key-file=~/.ssh/id_rsa

# Bootstrap with existing repository
flux bootstrap git \
  --url=https://github.com/your-org/gitops-infra-control-plane.git \
  --branch=main \
  --path=./clusters/production \
  --token-auth
```

### Bootstrap Artifacts

The bootstrap process creates:

1. **Custom Resource Definitions**: All Flux CRDs
2. **Namespace**: `flux-system` namespace with proper labels
3. **Controllers**: All six Flux controllers deployed
4. **GitRepository**: Source for Flux manifests
5. **Kustomization**: Flux self-management configuration
6. **Network Policies**: Default security policies
7. **Service Accounts**: Proper RBAC configuration

## Security and Network Policies

### Default Network Policies

Flux includes default NetworkPolicies that restrict communication:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-scraping
  namespace: flux-system
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from: []
    ports:
    - protocol: TCP
      port: 8080  # Metrics port
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-webhooks
  namespace: flux-system
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from: []
    ports:
    - protocol: TCP
      port: 9292  # Notification controller webhook port
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-egress
  namespace: flux-system
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - {}
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: flux-system
```

### Security Best Practices

1. **Least Privilege**: Use minimal RBAC permissions
2. **Secret Management**: Encrypt secrets with SOPS
3. **Image Verification**: Use Cosign for image signing
4. **Network Isolation**: Implement strict NetworkPolicies
5. **Audit Logging**: Enable audit logging for all operations

### Secret Encryption with SOPS

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: database-credentials
  namespace: production
stringData:
  username: ENC[AES256_GCM,data:...,iv:...,tag:...]
  password: ENC[AES256_GCM,data:...,iv:...,tag:...]
sops:
  kms:
  - arn: arn:aws:kms:us-west-2:123456789012:key/...
    created_at: "2023-01-01T00:00:00Z"
  encryptions:
  - kms: []
    aes_gcm: []
  version: 3.7.3
```

## Advanced Features

### Multi-Cluster GitOps

Flux can manage multiple clusters from a single repository:

```yaml
# clusters/production/kustomization.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: production-cluster
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: gitops-infra-control-plane
  path: ./infrastructure/tenants/3-workloads/production
  kubeConfig:
    secretRef:
      name: production-cluster-kubeconfig
---
# clusters/staging/kustomization.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: staging-cluster
  namespace: flux-system
spec:
  interval: 5m
  sourceRef:
    kind: GitRepository
    name: gitops-infra-control-plane
  path: ./infrastructure/tenants/3-workloads/staging
  kubeConfig:
    secretRef:
      name: staging-cluster-kubeconfig
```

### Dependency Management

Use `dependsOn` for explicit dependency ordering:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: workloads
  namespace: flux-system
spec:
  dependsOn:
    - name: infrastructure-networks
    - name: infrastructure-clusters
  # ... rest of configuration
```

### Progressive Delivery

Implement progressive delivery strategies:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: app-canary
  namespace: flux-system
spec:
  interval: 5m
  path: ./apps/canary
  healthChecks:
    - kind: Deployment
      name: app
      namespace: canary
  postBuild:
    substitute:
      ROLLOUT_STRATEGY: "canary"
      CANARY_WEIGHT: "10"
```

## Monitoring and Observability

### Metrics

All Flux controllers expose Prometheus metrics:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: source-controller
  namespace: flux-system
  labels:
    app.kubernetes.io/name: source-controller
spec:
  ports:
  - name: http
    port: 8080
    protocol: TCP
  selector:
    app.kubernetes.io/name: source-controller
```

### Health Checks

Monitor Flux health with custom resources:

```bash
# Check overall Flux health
flux check

# Check specific components
flux get sources all
flux get kustomizations all
flux get helmreleases all

# Check reconciliation status
kubectl get kustomizations -n flux-system -o wide
```

### Alerts and Notifications

Configure alerts for critical events:

```yaml
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: flux-alerts
  namespace: flux-system
spec:
  eventSeverity: info
  eventSources:
    - kind: Kustomization
      name: "*"
  providerRef:
    name: slack-provider
  exclusionList:
    - ".*no changes.*"
    - ".*dry run.*"
```

## Troubleshooting

### Common Issues

1. **Source Reconciliation Failures**

   ```bash
   kubectl get gitrepositories -A
   kubectl describe gitrepository gitops-infra-control-plane -n flux-system
   ```

2. **Kustomization Build Errors**

   ```bash
   flux build kustomization infrastructure-networks --path=./infrastructure/tenants/1-network
   ```

3. **Helm Release Failures**

   ```bash
   kubectl get helmreleases -A
   kubectl describe helmrelease cert-manager -n flux-system
   ```

4. **Permission Issues**

   ```bash
   kubectl auth can-i create kustomizations --as=system:serviceaccount:flux-system:kustomize-controller
   ```

### Debug Commands

```bash
# Check controller logs
kubectl logs -n flux-system deployment/source-controller
kubectl logs -n flux-system deployment/kustomize-controller

# Force reconciliation
flux reconcile source git gitops-infra-control-plane
flux reconcile kustomization infrastructure-networks

# Export resources for debugging
flux get kustomizations -A -o yaml
flux get sources all -A -o yaml
```

## Performance Optimization

### Source Optimization

1. **Artifact Size**: Use `.sourceignore` to exclude unnecessary files
2. **Polling Intervals**: Balance between responsiveness and resource usage
3. **Webhook Triggers**: Use webhooks for instant reconciliation
4. **Caching**: Leverage controller caching mechanisms

### Manifest Optimization

1. **Kustomize Overlays**: Use efficient overlay structures
2. **Resource Ordering**: Use `dependsOn` for explicit dependencies
3. **Parallel Reconciliation**: Configure independent kustomizations
4. **Health Checks**: Optimize health check intervals

### Controller Scaling

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kustomize-controller
  namespace: flux-system
spec:
  replicas: 2  # Scale for high availability
  template:
    spec:
      containers:
      - name: manager
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
```

## Migration Guide

### From v1 to v2

1. **OCIRepository**: Replace HelmRepository with OCIRepository for OCI registries
2. **API Versions**: Update to latest API versions
3. **Controller Images**: Use latest controller images
4. **Configuration**: Review and update deprecated fields

### From Other GitOps Tools

1. **Export Existing Configuration**: Export current deployments
2. **Create Flux Resources**: Convert to Flux custom resources
3. **Validate**: Test in non-production environment
4. **Migrate**: Cut over to Flux gradually

## Best Practices

### Repository Structure

```
gitops-infra-control-plane/
├── clusters/
│   ├── production/
│   │   ├── kustomization.yaml
│   │   └── flux-system/
│   │       └── gotk-sync.yaml
│   └── staging/
│       ├── kustomization.yaml
│       └── flux-system/
│           └── gotk-sync.yaml
├── infrastructure/
│   ├── tenants/
│   │   ├── 1-network/
│   │   ├── 2-clusters/
│   │   └── 3-workloads/
│   └── control-plane/
│       ├── flux/
│       └── karmada/
└── apps/
    ├── base/
    └── overlays/
        ├── production/
        └── staging/
```

### Resource Naming

- Use descriptive, consistent naming
- Include environment and purpose in names
- Follow Kubernetes naming conventions

### Change Management

1. **Preview Changes**: Use `flux diff kustomization` before applying
2. **Progressive Rollout**: Use canary deployments for critical changes
3. **Rollback Planning**: Always have rollback strategy
4. **Testing**: Validate in staging before production

### Security Practices

1. **Secret Management**: Always encrypt secrets with SOPS
2. **Image Verification**: Use Cosign for production images
3. **Network Policies**: Implement strict network isolation
4. **RBAC**: Use principle of least privilege

---

This comprehensive guide provides the foundation for implementing Flux CD end-to-end in your GitOps Infra Control Plane, covering all aspects from bootstrap to production operations with modern Flux v2.0+ features and best practices.

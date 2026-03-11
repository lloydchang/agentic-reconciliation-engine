# Flux Bootstrap and Setup Guide

This comprehensive guide covers the complete process of bootstrapping and setting up Flux CD for the GitOps Infrastructure Control Plane, including various installation methods, configuration options, and best practices.

## Prerequisites

### System Requirements

- **Kubernetes Cluster**: v1.24 or later
- **kubectl**: Configured to access the target cluster
- **Git Repository**: For storing Flux manifests and infrastructure code
- **Permissions**: Cluster admin rights for bootstrap process

### Required Tools

```bash
# Install Flux CLI
curl -sSL https://fluxcd.io/install.sh | sudo bash

# Verify installation
flux --version

# Install kubectl (if not already installed)
# macOS
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

### Git Repository Preparation

Create a repository structure:

```bash
# Clone or create repository
git clone https://github.com/your-org/gitops-infra-control-plane.git
cd gitops-infra-control-plane

# Create initial structure
mkdir -p clusters/production/flux-system
mkdir -p infrastructure/tenants/{1-network,2-clusters,3-workloads}
mkdir -p control-plane/{flux,karmada,controllers}
```

## Bootstrap Methods

### 1. GitHub Bootstrap (Recommended)

#### SSH Key Authentication

```bash
flux bootstrap github \
  --owner=your-org \
  --repository=gitops-infra-control-plane \
  --branch=main \
  --path=./clusters/production \
  --personal \
  --ssh-key-algorithm=ed25519 \
  --ssh-key-bits=4096
```

#### HTTPS Token Authentication

```bash
# Create GitHub token with repo permissions
export GITHUB_TOKEN=your-github-token

flux bootstrap github \
  --owner=your-org \
  --repository=gitops-infra-control-plane \
  --branch=main \
  --path=./clusters/production \
  --token-auth \
  --personal
```

#### Organization Repository

```bash
flux bootstrap github \
  --owner=your-org \
  --repository=gitops-infra-control-plane \
  --branch=main \
  --path=./clusters/production \
  --team=team-name \
  --ssh-key-algorithm=ed25519
```

### 2. Generic Git Bootstrap

#### SSH Authentication

```bash
flux bootstrap git \
  --url=ssh://git@github.com/your-org/gitops-infra-control-plane.git \
  --branch=main \
  --path=./clusters/production \
  --private-key-file=~/.ssh/id_rsa \
  --author-name=flux-cd \
  --author-email=flux-cd@users.noreply.github.com
```

#### HTTPS Authentication

```bash
flux bootstrap git \
  --url=https://github.com/your-org/gitops-infra-control-plane.git \
  --branch=main \
  --path=./clusters/production \
  --token-auth \
  --username=your-username \
  --password=your-token
```

### 3. GitLab Bootstrap

```bash
flux bootstrap gitlab \
  --owner=your-group \
  --repository=gitops-infra-control-plane \
  --branch=main \
  --path=./clusters/production \
  --token-auth \
  --hostname=gitlab.example.com
```

### 4. Bitbucket Bootstrap

```bash
flux bootstrap bitbucket \
  --owner=your-workspace \
  --repository=gitops-infra-control-plane \
  --branch=main \
  --path=./clusters/production \
  --ssh-key-algorithm=ed25519
```

## Bootstrap Configuration Options

### Custom Namespace

```bash
flux bootstrap github \
  --owner=your-org \
  --repository=gitops-infra-control-plane \
  --branch=main \
  --path=./clusters/production \
  --namespace=gitops-system
```

### Custom Components

```bash
flux bootstrap github \
  --owner=your-org \
  --repository=gitops-infra-control-plane \
  --branch=main \
  --path=./clusters/production \
  --components=source-controller,kustomize-controller,helm-controller,notification-controller
```

### Version Pinning

```bash
flux bootstrap github \
  --owner=your-org \
  --repository=gitops-infra-control-plane \
  --branch=main \
  --path=./clusters/production \
  --version=v2.2.0 \
  --arch=amd64
```

### Registry Configuration

```bash
flux bootstrap github \
  --owner=your-org \
  --repository=gitops-infra-control-plane \
  --branch=main \
  --path=./clusters/production \
  --registry=ghcr.io/fluxcd \
  --registry-credentials=docker-registry-secret
```

## Post-Bootstrap Configuration

### Verify Installation

```bash
# Check Flux health
flux check

# Verify all components
kubectl get pods -n flux-system

# Check custom resources
kubectl get crds | grep flux

# Verify GitRepository
flux get source git
```

### Configure Additional Sources

#### Add GitRepository

```yaml
# clusters/production/git-repositories.yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: infrastructure-repo
  namespace: flux-system
spec:
  interval: 5m
  url: https://github.com/your-org/infrastructure-manifests
  ref:
    branch: main
  ignore: |
    # Exclude test files
    test/
    *.test.yaml
    # Include only production manifests
    !production/
```

#### Add OCIRepository

```yaml
# clusters/production/oci-repositories.yaml
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

#### Add HelmRepository

```yaml
# clusters/production/helm-repositories.yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: HelmRepository
metadata:
  name: bitnami
  namespace: flux-system
spec:
  interval: 10m
  url: https://charts.bitnami.com/bitnami
```

### Configure Kustomizations

#### Infrastructure Kustomizations

```yaml
# clusters/production/infrastructure-networks.yaml
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
  healthChecks:
    - kind: Deployment
      name: network-controller
      namespace: network-system
---
# clusters/production/infrastructure-clusters.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: infrastructure-clusters
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
    - name: infrastructure-networks
---
# clusters/production/infrastructure-workloads.yaml
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
    - name: infrastructure-clusters
```

### Configure Helm Releases

```yaml
# clusters/production/helm-releases.yaml
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
---
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: HelmChart
metadata:
  name: cert-manager-chart
  namespace: flux-system
spec:
  interval: 10m
  chart: cert-manager
  version: "v1.13.0"
  sourceRef:
    kind: HelmRepository
    name: jetstack
  reconcileStrategy: ChartVersion
```

## Advanced Configuration

### Multi-Cluster Setup

```yaml
# clusters/production/multi-cluster.yaml
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
apiVersion: v1
kind: Secret
metadata:
  name: production-cluster-kubeconfig
  namespace: flux-system
stringData:
  kubeconfig: |
    apiVersion: v1
    kind: Config
    clusters:
    - name: production
      cluster:
        server: https://production.example.com
        certificate-authority-data: <base64-ca>
    contexts:
    - name: production
      context:
        cluster: production
        user: admin
    current-context: production
```

### Secret Management with SOPS

```bash
# Install SOPS
brew install sops  # macOS
# or
go install github.com/getsops/sops/v3/cmd/sops@latest

# Create age key
age-keygen -o key.txt

# Encrypt secret
sops --age=$(cat key.txt | grep "public key:" | cut -d' ' -f4) --encrypt secret.yaml
```

```yaml
# clusters/production/sops-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: database-credentials
  namespace: production
stringData:
  username: ENC[AES256_GCM,data:...,iv:...,tag:...]
  password: ENC[AES256_GCM,data:...,iv:...,tag:...]
sops:
  age:
  - recipient: age1...
    enc: |
      -----BEGIN AGE ENCRYPTED FILE-----
      ...
      -----END AGE ENCRYPTED FILE-----
  lastmodified: "2023-01-01T00:00:00Z"
  mac: ENC[AES256_GCM,data:...,iv:...,tag:...]
  version: 3.7.3
```

### Notification Setup

```yaml
# clusters/production/notifications.yaml
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
---
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
    - kind: HelmRelease
      name: "*"
  providerRef:
    name: slack-provider
  exclusionList:
    - ".*no changes.*"
    - ".*dry run.*"
```

### Webhook Receivers

```yaml
# clusters/production/webhook-receivers.yaml
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

## Image Update Automation

### Configure Image Repository

```yaml
# clusters/production/image-repositories.yaml
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

### Configure Image Update Automation

```yaml
# clusters/production/image-update-automation.yaml
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

## Security Configuration

### Network Policies

```yaml
# clusters/production/network-policies.yaml
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
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 8080
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
      port: 9292
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

### RBAC Configuration

```yaml
# clusters/production/rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: flux-system-controller
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: flux-system-controller
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: flux-system-controller
subjects:
- kind: ServiceAccount
  name: kustomize-controller
  namespace: flux-system
- kind: ServiceAccount
  name: helm-controller
  namespace: flux-system
```

## Monitoring and Observability

### Prometheus Monitoring

```yaml
# clusters/production/monitoring.yaml
apiVersion: v1
kind: Service
metadata:
  name: source-controller
  namespace: flux-system
  labels:
    app.kubernetes.io/name: source-controller
    app.kubernetes.io/component: controller
spec:
  ports:
  - name: http
    port: 8080
    protocol: TCP
  selector:
    app.kubernetes.io/name: source-controller
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: flux-system
  namespace: flux-system
  labels:
    app.kubernetes.io/name: flux-system
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: flux-system
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
```

### Health Checks

```yaml
# clusters/production/health-checks.yaml
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
  healthChecks:
    - kind: Deployment
      name: app-deployment
      namespace: production
    - kind: Service
      name: app-service
      namespace: production
    - kind: Ingress
      name: app-ingress
      namespace: production
```

## Troubleshooting Bootstrap Issues

### Common Problems

#### 1. Authentication Failures

```bash
# Check Git credentials
flux check --namespace flux-system

# Verify SSH key
ssh -T git@github.com

# Test HTTPS access
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

#### 2. Permission Issues

```bash
# Check cluster permissions
kubectl auth can-i create namespaces
kubectl auth can-i create customresourcedefinitions

# Verify service account permissions
kubectl get clusterrole flux-system-controller -o yaml
```

#### 3. Network Issues

```bash
# Test connectivity to Git repository
curl -I https://github.com/your-org/gitops-infra-control-plane

# Check DNS resolution
nslookup github.com

# Verify webhook access
curl -X POST https://your-webhook-url/webhook
```

#### 4. Resource Limits

```bash
# Check node resources
kubectl top nodes
kubectl describe nodes

# Check controller resources
kubectl get pods -n flux-system -o wide
kubectl describe pod source-controller-xxxx -n flux-system
```

### Debug Commands

```bash
# Check Flux version and components
flux version
flux check

# Get detailed status
flux get sources all
flux get kustomizations all
flux get helmreleases all

# Check controller logs
kubectl logs -n flux-system deployment/source-controller
kubectl logs -n flux-system deployment/kustomize-controller

# Force reconciliation
flux reconcile source git gitops-infra-control-plane
flux reconcile kustomization infrastructure-networks

# Export manifests for debugging
flux export source git gitops-infra-control-plane
flux export kustomization infrastructure-networks
```

### Recovery Procedures

#### Restore from Backup

```bash
# Export current state
flux get sources all -o yaml > sources-backup.yaml
flux get kustomizations all -o yaml > kustomizations-backup.yaml

# Restore if needed
kubectl apply -f sources-backup.yaml
kubectl apply -f kustomizations-backup.yaml
```

#### Re-bootstrap

```bash
# Clean up existing installation
kubectl delete namespace flux-system --ignore-not-found=true

# Re-bootstrap
flux bootstrap github \
  --owner=your-org \
  --repository=gitops-infra-control-plane \
  --branch=main \
  --path=./clusters/production
```

## Best Practices

### Repository Organization

```
gitops-infra-control-plane/
├── clusters/
│   ├── production/
│   │   ├── flux-system/
│   │   │   ├── gotk-sync.yaml
│   │   │   ├── kustomization.yaml
│   │   │   └── webhooks.yaml
│   │   ├── infrastructure.yaml
│   │   ├── applications.yaml
│   │   └── monitoring.yaml
│   ├── staging/
│   └── development/
├── infrastructure/
│   ├── tenants/
│   │   ├── 1-network/
│   │   ├── 2-clusters/
│   │   └── 3-workloads/
│   └── control-plane/
├── apps/
│   ├── base/
│   └── overlays/
└── docs/
```

### Configuration Management

1. **Use Kustomize Overlays**: Separate base configurations from environment-specific changes
2. **Version Pinning**: Pin critical dependencies for stability
3. **Dependency Management**: Use `dependsOn` for explicit ordering
4. **Secret Management**: Encrypt all secrets with SOPS

### Security Practices

1. **Least Privilege**: Use minimal RBAC permissions
2. **Network Isolation**: Implement strict NetworkPolicies
3. **Image Verification**: Use Cosign for production images
4. **Audit Logging**: Enable comprehensive logging

### Operational Practices

1. **Health Checks**: Configure comprehensive health checks
2. **Monitoring**: Set up Prometheus monitoring and alerting
3. **Backup**: Regular backup of Git repository and critical configurations
4. **Testing**: Validate changes in staging before production

---

This comprehensive bootstrap and setup guide provides everything needed to successfully install, configure, and operate Flux CD for the GitOps Infrastructure Control Plane with modern best practices and security considerations.

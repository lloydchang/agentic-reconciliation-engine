# Git Repository Sync Configurations

This directory contains various sync configurations for Flux Operator to synchronize with Git repositories, container registries, and object storage.

## Git Repository Sync

### Git Repository Sync - Public Repository

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
    size: medium
    multitenant: false
    networkPolicy: true
```

### Git Repository Sync - Private Repository

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
    path: "core/resources/tenants"
    interval: "5m"
    timeout: "3m"
    pullSecret: "flux-system"
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
    size: medium
    multitenant: false
    networkPolicy: true
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

### Git Repository Sync - SSH Authentication

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
    path: "core/resources/tenants"
    interval: "5m"
    timeout: "3m"
    pullSecret: "flux-ssh-credentials"
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
    size: medium
    multitenant: false
    networkPolicy: true
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

### Git Repository Sync - Multiple Branches

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux-main
  namespace: flux-system
spec:
  sync:
    kind: GitRepository
    url: "https://github.com/your-org/gitops-infra-control-plane"
    ref: "refs/heads/main"
    path: "core/resources/tenants"
    interval: "5m"
    timeout: "3m"
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
    size: medium
    multitenant: false
    networkPolicy: true
---
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux-staging
  namespace: flux-system
spec:
  sync:
    kind: GitRepository
    url: "https://github.com/your-org/gitops-infra-control-plane"
    ref: "refs/heads/staging"
    path: "core/resources/tenants/staging"
    interval: "3m"
    timeout: "2m"
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
    networkPolicy: true
```

## Container Registry Sync

### Container Registry Sync - OCI Repository

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
  distribution:
    version: "2.x"
    registry: "ghcr.io/fluxcd"
    artifact: "oci://ghcr.io/controlplaneio-fluxcd/flux-operator-manifests"
  components:
    - source-controller
    - helm-controller
  cluster:
    type: kubernetes
    size: medium
    multitenant: false
    networkPolicy: true
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

### Container Registry Sync - Multiple OCI Repositories

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux-charts
  namespace: flux-system
spec:
  sync:
    kind: OCIRepository
    url: "oci://ghcr.io/your-org/helm-charts"
    ref: "latest"
    interval: "10m"
    timeout: "5m"
  distribution:
    version: "2.x"
    registry: "ghcr.io/fluxcd"
    artifact: "oci://ghcr.io/controlplaneio-fluxcd/flux-operator-manifests"
  components:
    - source-controller
    - helm-controller
  cluster:
    type: kubernetes
    size: medium
    multitenant: false
    networkPolicy: true
---
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux-manifests
  namespace: flux-system
spec:
  sync:
    kind: OCIRepository
    url: "oci://ghcr.io/your-org/manifests"
    ref: "main"
    interval: "5m"
    timeout: "3m"
  distribution:
    version: "2.x"
    registry: "ghcr.io/fluxcd"
    artifact: "oci://ghcr.io/controlplaneio-fluxcd/flux-operator-manifests"
  components:
    - source-controller
    - kustomize-controller
  cluster:
    type: kubernetes
    size: medium
    multitenant: false
    networkPolicy: true
```

## Object Storage Sync

### S3 Bucket Sync

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
  distribution:
    version: "2.x"
    registry: "ghcr.io/fluxcd"
    artifact: "oci://ghcr.io/controlplaneio-fluxcd/flux-operator-manifests"
  components:
    - source-controller
    - kustomize-controller
  cluster:
    type: kubernetes
    size: medium
    multitenant: false
    networkPolicy: true
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

### GCS Bucket Sync

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
    endpoint: "storage.googleapis.com"
    provider: "gcp"
    interval: "5m"
    timeout: "3m"
    pullSecret: "gcs-credentials"
  distribution:
    version: "2.x"
    registry: "ghcr.io/fluxcd"
    artifact: "oci://ghcr.io/controlplaneio-fluxcd/flux-operator-manifests"
  components:
    - source-controller
    - kustomize-controller
  cluster:
    type: kubernetes
    size: medium
    multitenant: false
    networkPolicy: true
---
apiVersion: v1
kind: Secret
metadata:
  name: gcs-credentials
  namespace: flux-system
type: Opaque
stringData:
  serviceaccount.json: |
    {
      "type": "service_account",
      "project_id": "your-project-id",
      "private_key_id": "your-key-id",
      "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
      "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
      "client_id": "your-client-id",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token"
    }
```

## Advanced Sync Configurations

### Multi-Source Sync

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux-infrastructure
  namespace: flux-system
spec:
  sync:
    kind: GitRepository
    url: "https://github.com/your-org/infrastructure-manifests"
    ref: "refs/heads/main"
    path: "infrastructure"
    interval: "5m"
    timeout: "3m"
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
    size: medium
    multitenant: false
    networkPolicy: true
---
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux-applications
  namespace: flux-system
spec:
  sync:
    kind: GitRepository
    url: "https://github.com/your-org/application-manifests"
    ref: "refs/heads/main"
    path: "applications"
    interval: "3m"
    timeout: "2m"
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
    size: medium
    multitenant: false
    networkPolicy: true
```

### Sync with Webhook Triggers

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
    path: "core/resources/tenants"
    interval: "5m"
    timeout: "3m"
    webhook:
      enabled: true
      secret: "webhook-secret"
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
---
apiVersion: v1
kind: Secret
metadata:
  name: webhook-secret
  namespace: flux-system
stringData:
  token: "your-webhook-secret-token"
```

### Sync with Health Checks

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
    path: "core/resources/tenants"
    interval: "5m"
    timeout: "3m"
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
    size: medium
    multitenant: false
    networkPolicy: true
```

## Sync Configuration Options

### Sync Parameters

- **kind**: Source type (GitRepository, OCIRepository, Bucket)
- **url**: Source URL
- **ref**: Reference (branch, tag, or digest)
- **path**: Path within the source
- **interval**: Sync interval
- **timeout**: Sync timeout
- **pullSecret**: Secret for authentication

### Advanced Sync Options

- **webhook**: Webhook configuration for instant sync
- **healthChecks**: Health check configuration
- **ignore**: Path ignore patterns
- **recurseSubmodules**: Git submodule recursion
- **gitImplementation**: Git implementation (go-git, libgit2)

### Authentication Options

- **pullSecret**: Secret containing authentication credentials
- **certSecretRef**: Secret containing TLS certificates
- **sshKeyRef**: Secret containing SSH keys

## Usage Examples

### Apply Sync Configuration

```bash
# Apply basic Git sync
kubectl apply -f git-sync-public.yaml

# Apply private repository sync
kubectl apply -f git-sync-private.yaml

# Apply OCI repository sync
kubectl apply -f oci-sync.yaml

# Apply S3 bucket sync
kubectl apply -f s3-sync.yaml
```

### Monitor Sync Status

```bash
# Check FluxInstance status
kubectl get fluxinstance -n flux-system

# Check sync status
kubectl get fluxinstance flux -n flux-system -o yaml | grep -A 10 "sync:"

# Check source status
kubectl get gitrepository -n flux-system
kubectl get ocirepository -n flux-system
kubectl get bucket -n flux-system
```

### Force Sync

```bash
# Force reconciliation
kubectl patch fluxinstance flux -n flux-system --type=merge -p '{"spec":{"reconcileAt":"'$(date -u +'%Y-%m-%dT%H:%M:%SZ')'"}}'

# Trigger webhook
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/your-org/repo", "ref": "refs/heads/main"}' \
  http://flux-operator.flux-system.svc.cluster.local/webhook
```

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   ```bash
   # Check secret
   kubectl get secret flux-system -n flux-system -o yaml
   
   # Test repository access
   flux-operator test sync --url=https://github.com/your-org/repo
   ```

2. **Sync Timeouts**
   ```bash
   # Increase timeout
   kubectl patch fluxinstance flux -n flux-system --type=merge -p '{"spec":{"sync":{"timeout":"10m"}}}'
   ```

3. **Path Issues**
   ```bash
   # Check source content
   kubectl get gitrepository flux -n flux-system -o yaml | grep -A 5 "artifact:"
   ```

### Debug Commands

```bash
# Check FluxInstance logs
kubectl logs -n flux-system deployment/flux-operator

# Check source controller logs
kubectl logs -n flux-system deployment/source-controller

# Describe FluxInstance
kubectl describe fluxinstance flux -n flux-system

# Check events
kubectl get events -n flux-system --sort-by='.lastTimestamp'
```

## Best Practices

1. **Use Specific Paths**: Configure specific paths to reduce sync time
2. **Set Appropriate Intervals**: Balance responsiveness with resource usage
3. **Enable Webhooks**: Use webhooks for instant sync on changes
4. **Monitor Health**: Configure health checks for critical resources
5. **Secure Authentication**: Use secrets for all authentication
6. **Network Policies**: Enable network policies for security
7. **Resource Limits**: Set appropriate resource limits for controllers

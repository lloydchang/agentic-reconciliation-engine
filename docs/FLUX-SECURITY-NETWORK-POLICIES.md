# Flux Security and Network Policies

This comprehensive guide covers security configurations, network policies, and best practices for securing Flux CD in the GitOps Infra Control Plane.

## Security Overview

Flux CD provides multiple layers of security to ensure safe GitOps operations:

1. **Network Security**: NetworkPolicies to control traffic flow
2. **Authentication**: Secure authentication to external sources
3. **Authorization**: RBAC for least privilege access
4. **Secret Management**: Encrypted secrets with SOPS
5. **Image Verification**: Cryptographic verification with Cosign
6. **Audit Logging**: Comprehensive audit trails

## Network Policies

### Default Flux Network Policies

Flux automatically creates default NetworkPolicies when installed:

```yaml
# Allow metrics scraping
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
      port: 8080  # Metrics port for all controllers
---
# Allow webhook notifications
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
# Allow egress to external sources
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
  - {}  # Allow all egress for Git, Helm, and image repositories
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: flux-system
```

### Enhanced Network Policies

#### Restrictive Ingress Policy

```yaml
# Restrictive ingress policy for production
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: restrictive-ingress
  namespace: flux-system
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  # Allow metrics only from monitoring namespace
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 8080
  # Allow webhooks only from specific sources
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 9292
  # Allow intra-namespace communication
  - from:
    - podSelector: {}
```

#### Egress Restrictions

```yaml
# Restricted egress policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: restricted-egress
  namespace: flux-system
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  # Allow DNS
  - to: []
    ports:
    - protocol: UDP
      port: 53
  # Allow HTTPS to specific domains
  - to: []
    ports:
    - protocol: TCP
      port: 443
  # Allow HTTP to specific domains
  - to: []
    ports:
    - protocol: TCP
      port: 80
  # Allow Git SSH
  - to: []
    ports:
    - protocol: TCP
      port: 22
```

#### Controller-Specific Policies

```yaml
# Source controller network policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: source-controller-netpol
  namespace: flux-system
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: source-controller
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
  # Allow webhook notifications
  - from:
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: notification-controller
    ports:
    - protocol: TCP
      port: 8080
  egress:
  # Allow Git repositories
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 22
  # Allow container registries
  - to: []
    ports:
    - protocol: TCP
      port: 443
---
# Kustomize controller network policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: kustomize-controller-netpol
  namespace: flux-system
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: kustomize-controller
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
  # Allow source controller communication
  - from:
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: source-controller
    ports:
    - protocol: TCP
      port: 8080
  egress:
  # Allow Kubernetes API
  - to: []
    ports:
    - protocol: TCP
      port: 443
  # Allow DNS
  - to: []
    ports:
    - protocol: UDP
      port: 53
```

## Authentication and Authorization

### RBAC Configuration

#### Service Account Configuration

```yaml
# Flux service accounts
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kustomize-controller
  namespace: flux-system
  annotations:
    iam.amazonaws.com/role: flux-system
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: helm-controller
  namespace: flux-system
  annotations:
    iam.amazonaws.com/role: flux-system
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: source-controller
  namespace: flux-system
  annotations:
    iam.amazonaws.com/role: flux-system
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: notification-controller
  namespace: flux-system
  annotations:
    iam.amazonaws.com/role: flux-system
```

#### ClusterRole and ClusterRoleBinding

```yaml
# Flux controller cluster role
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: flux-system-controller
rules:
# Source controller permissions
- apiGroups: ["source.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["*"]
# Kustomize controller permissions
- apiGroups: ["kustomize.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["*"]
# Helm controller permissions
- apiGroups: ["helm.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["*"]
# Notification controller permissions
- apiGroups: ["notification.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["*"]
# Image automation permissions
- apiGroups: ["image.toolkit.fluxcd.io"]
  resources: ["*"]
  verbs: ["*"]
# Core Kubernetes permissions
- apiGroups: [""]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["apps"]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["batch"]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["extensions"]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["networking.k8s.io"]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["policy"]
  resources: ["*"]
  verbs: ["*"]
- apiGroups: ["rbac.authorization.k8s.io"]
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
- kind: ServiceAccount
  name: source-controller
  namespace: flux-system
- kind: ServiceAccount
  name: notification-controller
  namespace: flux-system
```

#### Namespace-Specific Roles

```yaml
# Production namespace role
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: flux-system-manager
  namespace: production
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["create", "get", "list", "watch", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["events"]
  verbs: ["create", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: flux-system-manager
  namespace: production
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: flux-system-manager
subjects:
- kind: ServiceAccount
  name: kustomize-controller
  namespace: flux-system
- kind: ServiceAccount
  name: helm-controller
  namespace: flux-system
```

### Authentication Methods

#### SSH Key Authentication

```yaml
# SSH key secret for Git repositories
apiVersion: v1
kind: Secret
metadata:
  name: git-ssh-credentials
  namespace: flux-system
type: Opaque
stringData:
  identity: |
    -----BEGIN OPENSSH PRIVATE KEY-----
    your-ssh-private-key-content
    -----END OPENSSH PRIVATE KEY-----
  known_hosts: |
    github.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC...
    gitlab.com ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTY...
  identity.pub: |
    ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... user@hostname
---
# GitRepository with SSH authentication
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: agentic-reconciliation-engine
  namespace: flux-system
spec:
  interval: 5m
  url: ssh://git@github.com/your-org/agentic-reconciliation-engine.git
  ref:
    branch: main
  secretRef:
    name: git-ssh-credentials
```

#### HTTPS Token Authentication

```yaml
# HTTPS token secret
apiVersion: v1
kind: Secret
metadata:
  name: git-https-credentials
  namespace: flux-system
type: Opaque
stringData:
  username: your-username
  password: your-personal-access-token
  caFile: |
    -----BEGIN CERTIFICATE-----
    your-ca-certificate-content
    -----END CERTIFICATE-----
---
# GitRepository with HTTPS authentication
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: agentic-reconciliation-engine
  namespace: flux-system
spec:
  interval: 5m
  url: https://github.com/your-org/agentic-reconciliation-engine.git
  ref:
    branch: main
  secretRef:
    name: git-https-credentials
  certSecretRef:
    name: git-ca-certificates
```

#### Container Registry Authentication

```yaml
# Container registry credentials
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
---
# ImageRepository with authentication
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
```

## Secret Management

### SOPS Configuration

#### Age Encryption

```yaml
# SOPS encrypted secret
apiVersion: v1
kind: Secret
metadata:
  name: database-credentials
  namespace: production
stringData:
  username: ENC[AES256_GCM,data:VGVzdFVzZXI=,iv:abc123...,tag:def456...]
  password: ENC[AES256_GCM,data:VGVzdFBhc3N3b3Jk,iv:xyz789...,tag:ghi012...]
  connection-string: ENC[AES256_GCM,data:cG9zdGdyZXNxbDovL3Rlc3Q6dGVzdEBkYi50ZXN0,iv:jkl345...,tag:mno678...]
sops:
  age:
  - recipient: age1ql3z7hjy64pw3dw93p4j8k2tq6s8r9x0y2z1w2v3u4x5y6z7a8b9c0d1e2f3
    enc: |
      -----BEGIN AGE ENCRYPTED FILE-----
      ...
      -----END AGE ENCRYPTED FILE-----
  lastmodified: "2023-01-01T00:00:00Z"
  mac: ENC[AES256_GCM,data:abc123...,iv:def456...,tag:ghi789...]
  version: 3.7.3
```

#### SOPS Age Key Secret

```yaml
# Age key for decryption
apiVersion: v1
kind: Secret
metadata:
  name: sops-age-key
  namespace: flux-system
stringData:
  age.agekey: |
    # created: 2023-01-01T00:00:00Z
    # public key: age1ql3z7hjy64pw3dw93p4j8k2tq6s8r9x0y2z1w2v3u4x5y6z7a8b9c0d1e2f3
    AGE-SECRET-KEY-1abc2def3ghi4jkl5mno6pqr7stu8vwx9yz0abc1def2ghi3jkl4mno5pqr6stu7vwx8yz9abc2def3ghi4jkl5mno6pqr7stu8vwx9yz0abc
---
# Kustomization with SOPS decryption
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: production-workloads
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: agentic-reconciliation-engine
  path: ./core/resources/tenants/3-workloads/production
  prune: true
  wait: true
  timeout: 15m
  decryption:
    provider: sops
    secretRef:
      name: sops-age-key
```

#### KMS Encryption

```yaml
# SOPS with AWS KMS
apiVersion: v1
kind: Secret
metadata:
  name: aws-secrets
  namespace: production
stringData:
  access-key-id: ENC[AES256_GCM,data:ABC123...,iv:xyz789...,tag:def456...]
  secret-access-key: ENC[AES256_GCM,data:DEF456...,iv:abc123...,tag:ghi789...]
sops:
  kms:
  - arn: arn:aws:kms:us-west-2:123456789012:key/abcd1234-efgh-5678-ijkl-9012mnop3456
    role: arn:aws:iam::123456789012:role/flux-decrypt-role
    created_at: "2023-01-01T00:00:00Z"
    enc: |
      -----BEGIN AGE ENCRYPTED FILE-----
      ...
      -----END AGE ENCRYPTED FILE-----
  lastmodified: "2023-01-01T00:00:00Z"
  mac: ENC[AES256_GCM,data:ghi789...,iv:def456...,tag:abc123...]
  version: 3.7.3
---
# KMS decryption configuration
apiVersion: v1
kind: Secret
metadata:
  name: sops-kms-credentials
  namespace: flux-system
stringData:
  aws-access-key-id: your-aws-access-key-id
  aws-secret-access-key: your-aws-secret-access-key
  aws-default-region: us-west-2
```

## Image Verification

### Cosign Configuration

#### Cosign Public Key

```yaml
# Cosign public key secret
apiVersion: v1
kind: Secret
metadata:
  name: cosign-pub
  namespace: flux-system
stringData:
  cosign.pub: |
    -----BEGIN PUBLIC KEY-----
    MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
    -----END PUBLIC KEY-----
---
# OCIRepository with Cosign verification
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: OCIRepository
metadata:
  name: verified-charts
  namespace: flux-system
spec:
  interval: 10m
  url: oci://ghcr.io/your-org/verified-charts
  ref:
    tag: latest
  verify:
    provider: cosign
    secretRef:
      name: cosign-pub
```

#### Image Policy with Verification

```yaml
# ImageRepository for verified images
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageRepository
metadata:
  name: verified-app-images
  namespace: flux-system
spec:
  interval: 5m
  image: ghcr.io/your-org/verified-app
  secretRef:
    name: ghcr-credentials
---
# ImagePolicy with verification
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImagePolicy
metadata:
  name: verified-app-latest
  namespace: flux-system
spec:
  imageRepositoryRef:
    name: verified-app-images
  policy:
    semver:
      range: ">=1.0.0"
  filterTags:
    pattern: '^v?[0-9]+\.[0-9]+\.[0-9]+$'
    extract: '$ts'
  verify:
    provider: cosign
    secretRef:
      name: cosign-pub
```

### Notary V2 Integration

```yaml
# Notary V2 configuration
apiVersion: v1
kind: Secret
metadata:
  name: notary-credentials
  namespace: flux-system
stringData:
  auth: your-notary-auth-token
---
# OCIRepository with Notary verification
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: OCIRepository
metadata:
  name: notarized-charts
  namespace: flux-system
spec:
  interval: 10m
  url: oci://ghcr.io/your-org/notarized-charts
  ref:
    tag: latest
  verify:
    provider: notaryv2
    secretRef:
      name: notary-credentials
```

## Admission Control

### Validating Admission Policy

```yaml
# Validating admission policy for Flux resources
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: flux-resources-policy
spec:
  failurePolicy: Fail
  matchConstraints:
  - resourceRules:
    - apiGroups: ["source.toolkit.fluxcd.io"]
      resources: ["gitrepositories"]
    - apiGroups: ["kustomize.toolkit.fluxcd.io"]
      resources: ["kustomizations"]
    - apiGroups: ["helm.toolkit.fluxcd.io"]
      resources: ["helmreleases"]
  validations:
  - expression: "has(object.spec.interval) && object.spec.interval >= '1m'"
    message: "Interval must be at least 1 minute"
  - expression: "has(object.spec.sourceRef) || has(object.spec.url)"
    message: "Must specify source reference or URL"
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: flux-resources-binding
spec:
  policyName: flux-resources-policy
  validationActions: [Deny]
  matchResources:
    resourceRules:
    - apiGroups: ["source.toolkit.fluxcd.io"]
      resources: ["*"]
    - apiGroups: ["kustomize.toolkit.fluxcd.io"]
      resources: ["*"]
    - apiGroups: ["helm.toolkit.fluxcd.io"]
      resources: ["*"]
```

### Mutating Admission Webhook

```yaml
# Mutating webhook for Flux resources
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: flux-mutator
webhooks:
- name: flux-mutator.fluxcd.io
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: ["source.toolkit.fluxcd.io", "kustomize.toolkit.fluxcd.io", "helm.toolkit.fluxcd.io"]
    apiVersions: ["v1beta2", "v2beta1"]
    resources: ["*"]
  clientConfig:
    service:
      name: flux-mutator-service
      namespace: flux-system
      path: "/mutate"
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Fail
```

## Audit Logging

### Audit Policy Configuration

```yaml
# Audit policy for Flux operations
apiVersion: audit.k8s.io/v1
kind: Policy
metadata:
  name: flux-audit-policy
rules:
- level: Metadata
  namespaces: ["flux-system"]
  resources:
  - group: "source.toolkit.fluxcd.io"
    resources: ["*"]
  - group: "kustomize.toolkit.fluxcd.io"
    resources: ["*"]
  - group: "helm.toolkit.fluxcd.io"
    resources: ["*"]
- level: Request
  namespaces: ["flux-system"]
  resources:
  - group: ""
    resources: ["secrets"]
    verbs: ["create", "update", "patch"]
- level: RequestResponse
  namespaces: ["flux-system"]
  resources:
  - group: "rbac.authorization.k8s.io"
    resources: ["roles", "rolebindings"]
```

### Audit Log Collection

```yaml
# Fluent Bit configuration for audit logs
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-audit-config
  namespace: flux-system
data:
  fluent-bit.conf: |
    [INPUT]
        Name tail
        Path /var/log/audit/audit.log
        Parser kube-audit-parser
        Tag kube.audit.*
        Mem_Buf_Limit 50MB
        Skip_Long_Lines On

    [FILTER]
        Name grep
        Match kube.audit.*
        Regex objectRef.namespace flux-system

    [OUTPUT]
        Name forward
        Match kube.audit.*
        Host log-collector.monitoring.svc.cluster.local
        Port 24224
```

## Security Monitoring

### Prometheus Security Rules

```yaml
# Prometheus security rules
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: flux-security-rules
  namespace: flux-system
spec:
  groups:
  - name: flux.security
    rules:
    - alert: FluxSourceAuthenticationFailure
      expr: flux_source_reconcile_failed_total{reason="AuthenticationFailed"} > 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Flux source authentication failure"
        description: "Flux source {{ $labels.name }} is failing authentication for {{ $value }} times"
    - alert: FluxKustomizationReconciliationFailure
      expr: flux_kustomize_reconcile_failed_total > 0
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "Flux kustomization reconciliation failure"
        description: "Flux kustomization {{ $labels.name }} has failed {{ $value }} times"
    - alert: FluxHelmReleaseFailure
      expr: flux_helm_release_failed_total > 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Flux Helm release failure"
        description: "Flux Helm release {{ $labels.name }} has failed {{ $value }} times"
```

### Falco Security Rules

```yaml
# Falco rules for Flux security
apiVersion: v1
kind: ConfigMap
metadata:
  name: falco-flux-rules
  namespace: flux-system
data:
  flux_rules.yaml: |
    - rule: Unauthorized Flux Source Access
      desc: Detect unauthorized access to Flux sources
      condition: >
        ka.namespace.name = "flux-system" and
        ka.target.resource in ["gitrepositories", "helmrepositories", "ocirepositories"] and
        not ka.user.name in ["system:serviceaccount:flux-system:kustomize-controller",
                           "system:serviceaccount:flux-system:helm-controller",
                           "system:serviceaccount:flux-system:source-controller"]
      output: >
        Unauthorized access to Flux source (user=%ka.user.name resource=%ka.target.resource)
      priority: WARNING
      tags:
        - flux
        - security

    - rule: Flux Secret Access
      desc: Detect access to Flux secrets
      condition: >
        ka.namespace.name = "flux-system" and
        ka.target.resource = "secrets" and
        ka.verb in ["get", "list", "watch"] and
        not ka.user.name in ["system:serviceaccount:flux-system:*"]
      output: >
        Access to Flux secret (user=%ka.user.name secret=%ka.target.name)
      priority: WARNING
      tags:
        - flux
        - security
```

## Compliance and Governance

### Policy as Code

```yaml
# Open Policy Agent policy for Flux
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-opa-policy
  namespace: flux-system
data:
  policy.rego: |
    package flux.security
    
    deny[msg] {
        input.kind == "GitRepository"
        not input.spec.secretRef
        msg := "GitRepository must use secretRef for authentication"
    }
    
    deny[msg] {
        input.kind == "Kustomization"
        input.spec.prune == true
        not input.spec.wait
        msg := "Kustomization with prune=true must have wait=true"
    }
    
    deny[msg] {
        input.kind == "HelmRelease"
        not has(input.spec.chartRef)
        not has(input.spec.chart)
        msg := "HelmRelease must specify chartRef or chart"
    }
```

### Compliance Reporting

```yaml
# Compliance reporting job
apiVersion: batch/v1
kind: CronJob
metadata:
  name: flux-compliance-report
  namespace: flux-system
spec:
  schedule: "0 6 * * *"  # Daily at 6 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: compliance-scanner
            image: ghcr.io/your-org/flux-compliance-scanner:latest
            command:
            - /bin/sh
            - -c
            - |
              # Scan all Flux resources
              flux get sources all -o json > /tmp/sources.json
              flux get kustomizations all -o json > /tmp/kustomizations.json
              flux get helmreleases all -o json > /tmp/helmreleases.json
              
              # Generate compliance report
              /usr/local/bin/generate-report \
                --sources /tmp/sources.json \
                --kustomizations /tmp/kustomizations.json \
                --helmreleases /tmp/helmreleases.json \
                --output /tmp/compliance-report.json
              
              # Upload to compliance system
              curl -X POST \
                -H "Authorization: Bearer $COMPLIANCE_TOKEN" \
                -F "report=@/tmp/compliance-report.json" \
                https://compliance.example.com/api/reports
            env:
            - name: COMPLIANCE_TOKEN
              valueFrom:
                secretKeyRef:
                  name: compliance-credentials
                  key: token
          restartPolicy: OnFailure
```

## Security Best Practices

### 1. Network Security

- **Default Deny**: Implement default deny NetworkPolicies
- **Namespace Isolation**: Isolate flux-system namespace
- **Egress Filtering**: Restrict egress to required destinations only
- **Ingress Control**: Limit ingress to monitoring and webhook sources

### 2. Authentication

- **Secure Credentials**: Use secrets for all authentication
- **Rotate Regularly**: Rotate authentication credentials regularly
- **Multi-Factor**: Enable MFA for Git repository access
- **Service Accounts**: Use dedicated service accounts for each controller

### 3. Authorization

- **Least Privilege**: Grant minimal required permissions
- **Namespace Scoping**: Scope permissions to specific namespaces
- **Role Separation**: Separate roles for different functions
- **Audit Access**: Log all authorization decisions

### 4. Secret Management

- **Encrypt Secrets**: Always encrypt secrets with SOPS
- **Key Management**: Use secure key management practices
- **Access Control**: Limit access to decryption keys
- **Backup Keys**: Maintain secure backups of encryption keys

### 5. Image Security

- **Image Verification**: Verify all images with Cosign
- **Vulnerability Scanning**: Scan images for vulnerabilities
- **Signed Images**: Only deploy signed images in production
- **SBOM Generation**: Generate and maintain SBOMs

### 6. Monitoring and Auditing

- **Comprehensive Logging**: Log all Flux operations
- **Security Monitoring**: Monitor for security events
- **Compliance Reporting**: Generate regular compliance reports
- **Alerting**: Configure alerts for security events

## Troubleshooting Security Issues

### Common Security Problems

#### 1. Network Policy Issues

```bash
# Check network policies
kubectl get networkpolicies -n flux-system -o yaml

# Test connectivity
kubectl run test-pod --image=busybox --rm -it -- /bin/sh
# Inside pod:
# nslookup github.com
# wget -O- https://github.com

# Check pod connectivity
kubectl exec -n flux-system deployment/source-controller -- ping github.com
```

#### 2. Authentication Failures

```bash
# Check secret references
kubectl get secrets -n flux-system
kubectl describe secret git-credentials -n flux-system

# Test Git access
flux reconcile source git agentic-reconciliation-engine --with-source

# Check controller logs
kubectl logs -n flux-system deployment/source-controller | grep -i auth
```

#### 3. RBAC Issues

```bash
# Check permissions
kubectl auth can-i create gitrepositories --as=system:serviceaccount:flux-system:source-controller
kubectl auth can-i create kustomizations --as=system:serviceaccount:flux-system:kustomize-controller

# Check role bindings
kubectl get clusterroles,clusterrolebindings | grep flux-system
```

#### 4. Secret Decryption Issues

```bash
# Check SOPS keys
kubectl get secret sops-age-key -n flux-system -o yaml

# Test decryption
sops --decrypt secret.yaml

# Check controller logs for decryption errors
kubectl logs -n flux-system deployment/kustomize-controller | grep -i sops
```

### Security Incident Response

#### 1. Isolate Affected Systems

```bash
# Scale down controllers
kubectl scale deployment -n flux-system --replicas=0

# Isolate namespace
kubectl annotate namespace flux-system security.isolation=true
```

#### 2. Investigate the Incident

```bash
# Check audit logs
kubectl get events -n flux-system --sort-by='.lastTimestamp'

# Check controller logs
kubectl logs -n flux-system --all-containers=true --tail=1000

# Check for unauthorized access
kubectl auth can-i --list --as=system:anonymous
```

#### 3. Remediate and Recover

```bash
# Rotate all secrets
kubectl create secret generic new-credentials --from-literal=token=new-token

# Update resource references
kubectl patch gitrepository agentic-reconciliation-engine -p '{"spec":{"secretRef":{"name":"new-credentials"}}}'

# Restore operations
kubectl scale deployment -n flux-system --replicas=1
```

---

This comprehensive security guide provides the foundation for securing Flux CD operations in the GitOps Infra Control Plane, covering all aspects of network security, authentication, authorization, secret management, and compliance.

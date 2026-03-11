# Flux GitHub Action Implementation Guide

This guide explains the implementation of Flux GitHub Action workflows for the GitOps Infrastructure Control Plane, providing automated operations for Flux management, OCI artifact handling, and comprehensive testing.

## Overview

The Flux GitHub Action integration enables automated GitOps operations directly within GitHub Actions workflows, providing:

- **Automated Flux Updates**: Keep Flux components up-to-date automatically
- **OCI Artifact Management**: Push and sign Kubernetes manifests as OCI artifacts
- **End-to-End Testing**: Comprehensive testing with Kubernetes Kind
- **Security & Compliance**: Artifact signing and verification

## Workflows Implemented

### 1. Flux Components Update

**File**: `.github/workflows/flux-update.yml`

Automates Flux component updates through pull requests.

#### Features

- **Scheduled Updates**: Daily checks for new Flux versions
- **Manual Triggers**: On-demand Flux updates
- **PR Automation**: Automatic pull request creation
- **Validation**: Component validation before PR creation
- **Change Detection**: Only creates PRs when updates are available

#### Workflow Triggers

```yaml
on:
  workflow_dispatch:                    # Manual trigger
  schedule:                            # Daily at 00:00 UTC
    - cron: "0 0 * * *"
  push:                                # On workflow changes
    branches:
      - main
    paths:
      - '.github/workflows/flux-update.yml'
```

#### Key Steps

1. **Check Updates**: Compare current vs latest Flux version
2. **Generate Components**: Export latest Flux components
3. **Validate**: Test new components for compatibility
4. **Create PR**: Automated pull request with detailed description

#### Configuration

```yaml
env:
  FLUX_VERSION: latest                 # Flux CLI version
permissions:
  contents: write                      # PR creation
  pull-requests: write                 # PR management
  packages: write                      # Registry access
```

### 2. OCI Manifest Push

**File**: `.github/workflows/oci-manifests.yml`

Pushes Kubernetes manifests as OCI artifacts to container registries.

#### Features

- **Multi-Environment**: Support for staging and production
- **Component Separation**: Individual artifacts for each component
- **SBOM Generation**: Software Bill of Materials for each artifact
- **Security Scanning**: Trivy integration for vulnerability scanning
- **Artifact Tagging**: Environment-specific and latest tags

#### Workflow Triggers

```yaml
on:
  push:
    branches:
      - main
      - develop
  workflow_dispatch:                    # Manual trigger with inputs
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'staging'
        type: choice
        options:
        - staging
        - production
```

#### Key Steps

1. **Generate Manifests**: Build Kustomize manifests
2. **Push Artifacts**: Upload to GitHub Container Registry
3. **Tag Deployment**: Environment-specific tagging
4. **Generate SBOM**: Create software bill of materials
5. **Security Scan**: Vulnerability assessment

#### Artifact Structure

```
ghcr.io/owner/gitops-manifests:
  ├─ network:staging-abc123-20231201120000
  ├─ clusters:staging-abc123-20231201120000
  ├─ workloads:staging-abc123-20231201120000
  ├─ flux-system:staging-abc123-20231201120000
  └─ all:staging-abc123-20231201120000
```

### 3. Signed OCI Manifest Workflow

**File**: `.github/workflows/signed-oci-manifests.yml`

Enhanced OCI workflow with cryptographic signing using Cosign and GitHub OIDC.

#### Features

- **Cryptographic Signing**: Cosign integration with GitHub OIDC
- **Signature Verification**: Automated signature validation
- **SBOM Attestation**: Signed software bill of materials
- **Transparency Logging**: Complete audit trail
- **Release Integration**: Automatic signing on releases

#### Security Features

```yaml
permissions:
  contents: read
  packages: write
  id-token: write                       # Required for OIDC token
env:
  COSIGN_EXPERIMENTAL: "1"             # Enable experimental features
```

#### Signing Process

1. **Push Artifact**: Upload to container registry
2. **Generate Signature**: Sign with GitHub OIDC token
3. **Verify Signature**: Validate signature integrity
4. **Attach SBOM**: Add signed software bill of materials
5. **Transparency Log**: Create audit trail entry

#### Signature Verification

```bash
# Verify artifact signature
cosign verify ghcr.io/owner/gitops-manifests@sha256:...

# Verify SBOM attestation
cosign verify-attestation --type spdxjson ghcr.io/owner/...
```

### 4. End-to-End Testing

**File**: `.github/workflows/e2e-testing-new.yml`

Comprehensive testing using Kubernetes Kind clusters.

#### Features

- **Multi-Version Testing**: Test across Kubernetes versions
- **Flux Integration**: Real Flux deployment testing
- **Manifest Validation**: YAML syntax and application testing
- **Integration Tests**: GitRepository and Kustomization testing
- **Performance Benchmarks**: Resource usage and timing metrics

#### Test Suites

```yaml
inputs:
  test-suite:
    type: choice
    options:
    - all                              # Run all tests
    - flux                             # Flux-specific tests
    - manifests                        # Manifest validation
    - integration                      # Integration tests
  cluster-version:
    description: 'Kubernetes version'
    default: 'v1.28.0'
```

#### Test Categories

1. **Setup Tests**: Kind cluster creation and configuration
2. **Flux Tests**: Installation, health checks, and operations
3. **Manifest Tests**: YAML validation and deployment testing
4. **Integration Tests**: GitRepository and Kustomization workflows
5. **Performance Tests**: Resource usage and timing benchmarks

#### Kind Cluster Configuration

**File**: `.github/kind-cluster.yaml`

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: gitops-e2e
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
  - containerPort: 443
    hostPort: 443
- role: worker
- role: worker
```

## Setup Instructions

### Prerequisites

1. **GitHub Repository**: GitOps Infrastructure Control Plane
2. **Container Registry**: GitHub Container Registry enabled
3. **Permissions**: Required GitHub Actions permissions
4. **Flux CLI**: Available in workflows via action

### Repository Settings

#### Enable Actions Permissions

1. Go to repository **Settings → Actions**
2. Under **Workflow permissions**, select **Read and write permissions**
3. Enable **Allow GitHub Actions to create and approve pull requests**

#### Container Registry

1. GitHub Container Registry is automatically available
2. Ensure **Packages** permissions are enabled
3. Configure registry access if using external registries

### Workflow Configuration

#### 1. Flux Update Workflow

No additional configuration required. The workflow:

- Automatically detects Flux updates
- Creates pull requests with detailed descriptions
- Validates components before submission

#### 2. OCI Manifest Workflows

Configure environment variables as needed:

```yaml
env:
  OCI_REPO: "oci://ghcr.io/${{ github.repository_owner }}/gitops-manifests"
  REGISTRY: "ghcr.io"
```

#### 3. Signed Workflow

Requires OIDC configuration:

1. Ensure `id-token: write` permission
2. Configure Cosign signing policy
3. Set up signature verification in production

#### 4. E2E Testing

Configure test parameters:

```yaml
env:
  KIND_CLUSTER_NAME: "gitops-e2e"
  KUBECONFIG: "/tmp/kubeconfig"
```

## Usage Examples

### Manual Flux Update

```bash
# Trigger Flux update manually
gh workflow run flux-update.yml
```

### Manual OCI Manifest Push

```bash
# Push to staging
gh workflow run oci-manifests.yml \
  --field environment=staging

# Push to production with custom tag
gh workflow run oci-manifests.yml \
  --field environment=production \
  --field tag=v1.2.3
```

### Manual Signed Manifest

```bash
# Push and sign manifests
gh workflow run signed-oci-manifests.yml \
  --field environment=production \
  --field sign=true
```

### Run E2E Tests

```bash
# Run all tests
gh workflow run e2e-testing-new.yml

# Run specific test suite
gh workflow run e2e-testing-new.yml \
  --field test-suite=flux \
  --field cluster-version=v1.27.0
```

## Security Considerations

### Permission Management

#### Minimal Permissions

```yaml
permissions:
  contents: read                      # Repository access
  packages: write                     # Registry push
  pull-requests: write                 # PR creation
  id-token: write                     # OIDC tokens
```

#### Secret Management

- Use GitHub's built-in token (`GITHUB_TOKEN`) when possible
- Store external registry credentials in GitHub Secrets
- Rotate secrets regularly

### Artifact Security

#### Cryptographic Signing

```yaml
# Enable OIDC-based signing
permissions:
  id-token: write

# Sign artifacts with Cosign
cosign sign --yes ${{ steps.push.outputs.digest }}
```

#### Signature Verification

```bash
# Verify in production
cosign verify \
  --certificate-identity="https://github.com/${{ github.repository }}/.github/workflows/signed-oci-manifests.yml@refs/heads/main" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  ghcr.io/owner/gitops-manifests@sha256:...
```

### Supply Chain Security

#### SBOM Generation

- Automatic SBOM generation for all artifacts
- CycloneDX format for compatibility
- Inclusion of build metadata and dependencies

#### Vulnerability Scanning

- Trivy integration for security scanning
- SARIF output for GitHub Security tab integration
- Fail-fast on critical vulnerabilities

## Advanced Configuration

### Custom Registry Configuration

For external container registries:

```yaml
- name: Login to Registry
  uses: docker/login-action@v3
  with:
    registry: ${{ secrets.REGISTRY_URL }}
    username: ${{ secrets.REGISTRY_USERNAME }}
    password: ${{ secrets.REGISTRY_PASSWORD }}
```

### Multi-Environment Deployment

Configure environment-specific settings:

```yaml
env:
  STAGING_REGISTRY: "oci://ghcr.io/${{ github.repository_owner }}/staging-manifests"
  PROD_REGISTRY: "oci://ghcr.io/${{ github.repository_owner }}/prod-manifests"
```

### Custom Test Configuration

Extend E2E testing with custom scenarios:

```yaml
- name: Custom Integration Test
  run: |
    # Add custom test scenarios
    kubectl apply -f ./tests/custom-scenario.yaml
    kubectl wait --for=condition=complete job/custom-test --timeout=300s
```

## Monitoring and Observability

### Workflow Status

Monitor workflow execution:

```bash
# Check workflow status
gh run list --repo=owner/repo

# View specific run
gh run view <run-id> --repo=owner/repo
```

### Artifact Tracking

Track OCI artifacts:

```bash
# List artifacts
flux list artifacts ghcr.io/owner/gitops-manifests

# Get artifact details
flux get artifact ghcr.io/owner/gitops-manifests:tag
```

### Security Monitoring

Monitor signature verification:

```bash
# Verify artifact signatures
cosign verify ghcr.io/owner/gitops-manifests@sha256:...

# Check SBOM attestations
cosign verify-attestation ghcr.io/owner/gitops-manifests@sha256:...
```

## Troubleshooting

### Common Issues

#### Flux Update Failures

1. **Permission Issues**: Ensure `pull-requests: write` permission
2. **Git Conflicts**: Resolve conflicts in target branch
3. **API Limits**: Check GitHub API rate limits

#### OCI Push Failures

1. **Registry Access**: Verify registry credentials
2. **Size Limits**: Check artifact size limits
3. **Network Issues**: Verify network connectivity

#### Signing Failures

1. **OIDC Configuration**: Ensure `id-token: write` permission
2. **Cosign Version**: Use compatible Cosign version
3. **Trust Store**: Configure proper trust relationships

#### E2E Test Failures

1. **Kind Installation**: Verify Kind CLI availability
2. **Resource Limits**: Check available resources
3. **Network Policies**: Verify network configuration

### Debug Commands

```bash
# Debug Flux installation
flux check
kubectl get pods -n flux-system
kubectl logs -n flux-system deployment/source-controller

# Debug OCI artifacts
flux get artifacts
flux list artifacts ghcr.io/owner/gitops-manifests

# Debug signatures
cosign verify ghcr.io/owner/gitops-manifests@sha256:...
cosign triangulate ghcr.io/owner/gitops-manifests:tag

# Debug Kind cluster
kind get clusters
kubectl get nodes -o wide
kubectl get pods -A
```

## Best Practices

### Workflow Design

1. **Idempotent**: Workflows should be runnable multiple times
2. **Fail-Fast**: Exit early on critical failures
3. **Resource Cleanup**: Clean up temporary resources
4. **Logging**: Provide comprehensive logging for debugging

### Security Practices

1. **Least Privilege**: Use minimal required permissions
2. **Secret Rotation**: Rotate secrets regularly
3. **Artifact Signing**: Sign all production artifacts
4. **Vulnerability Scanning**: Scan all artifacts

### Testing Practices

1. **Comprehensive Coverage**: Test all critical paths
2. **Environment Parity**: Test in production-like environments
3. **Automated Validation**: Validate all generated artifacts
4. **Performance Monitoring**: Track test execution times

## Integration with Existing Workflows

### Jenkins Integration

Combine with Jenkins CI/CD:

```yaml
- name: Trigger Jenkins
  run: |
    curl -X POST \
      -H "Authorization: token ${{ secrets.JENKINS_TOKEN }}" \
      https://jenkins.example.com/job/build
```

### Monitoring Integration

Integrate with monitoring systems:

```yaml
- name: Notify Monitoring
  run: |
    curl -X POST \
      -H "Content-Type: application/json" \
      -d '{"status": "success", "artifact": "${{ steps.push.outputs.digest }}"}' \
      https://monitoring.example.com/webhook
```

### Slack Integration

Add Slack notifications:

```yaml
- name: Slack Notification
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: "Flux GitHub Action completed: ${{ job.status }}"
```

## Migration Guide

### From Manual Operations

1. **Identify Manual Tasks**: List current manual Flux operations
2. **Map to Workflows**: Create corresponding GitHub Actions
3. **Gradual Migration**: Migrate one workflow at a time
4. **Validation**: Validate automated operations match manual results

### From Other CI/CD Systems

1. **Export Configuration**: Export existing CI/CD configurations
2. **Convert to GitHub Actions**: Translate to GitHub Actions syntax
3. **Test Thoroughly**: Validate converted workflows
4. **Decommission Old System**: Remove old CI/CD system

## Performance Optimization

### Workflow Optimization

1. **Parallel Execution**: Use matrix strategies for parallel jobs
2. **Caching**: Cache dependencies and build artifacts
3. **Resource Limits**: Optimize resource allocation
4. **Early Termination**: Fail fast on non-critical jobs

### Artifact Optimization

1. **Layer Caching**: Use Docker layer caching
2. **Compression**: Compress artifacts before upload
3. **Deduplication**: Avoid duplicate artifact uploads
4. **Cleanup**: Regular cleanup of old artifacts

## Future Enhancements

### Planned Features

1. **Multi-Cluster Testing**: Test across multiple Kubernetes distributions
2. **Advanced Signing**: Support for multiple signing algorithms
3. **Policy Enforcement**: Integrated policy-as-code validation
4. **Performance Metrics**: Detailed performance analytics

### Integration Roadmap

1. **External Registries**: Support for additional container registries
2. **Cloud Integration**: Direct cloud provider integrations
3. **Advanced Testing**: Chaos engineering and load testing
4. **AI/ML Integration**: Intelligent anomaly detection

---

This Flux GitHub Action implementation provides a comprehensive, secure, and automated approach to GitOps operations, enabling reliable infrastructure management at scale while maintaining security and compliance requirements.

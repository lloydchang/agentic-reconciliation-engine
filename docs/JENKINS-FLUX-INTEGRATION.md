# Jenkins + Flux Integration Guide

This guide explains how to integrate Jenkins CI with Flux CD for a complete GitOps workflow in the GitOps Infra Control Plane.

## Overview

The integration follows GitOps principles by separating concerns:
- **Jenkins (CI)**: Builds, tests, and pushes container images
- **Flux (CD)**: Deploys applications based on image updates

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Jenkins   │───▶│ Container    │───▶│    Flux     │
│     CI      │    │   Registry   │    │     CD      │
└─────────────┘    └──────────────┘    └─────────────┘
       │                   │                   │
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Build     │    │   Image      │    │   Deploy    │
│   & Test    │    │   Tags       │    │   Updates   │
└─────────────┘    └──────────────┘    └─────────────┘
```

## Components

### 1. Jenkins Pipeline

**File**: `jenkins/Jenkinsfile`

A declarative pipeline that:
- Builds OCI images using Docker
- Runs tests in isolated containers
- Pushes development and release tags
- Integrates with Flux for automated deployments

#### Pipeline Stages

1. **Build**: Creates Docker image locally
2. **Development**: Pushes dev tags and runs tests in parallel
3. **Release**: Pushes SemVer tags for production
4. **Update GitOps**: Triggers Flux image update automation

#### Image Tagging Strategy

- **Development**: `{branch}-{sha}-{timestamp}` (e.g., `main-a1b2c3d4-1672531200`)
- **Release**: SemVer tags (e.g., `v1.2.3`)
- **Latest**: Always points to latest main branch build

### 2. Flux Image Automation

**File**: `control-plane/flux/jenkins-image-automation.yaml`

Flux resources that:
- Monitor container registry for new images
- Apply update policies for development and production
- Automatically update Git manifests with new image references

#### Image Policies

- **Production**: SemVer range `>=1.0.0` with pattern `^v?[0-9]+\.[0-9]+\.[0-9]+$`
- **Development**: Alphabetical ordering with pattern `^[a-zA-Z0-9_-]+-[a-fA-F0-9]{8}-[0-9]+$`

### 3. Jenkins Docker Configuration

**File**: `jenkins/docker-pod.yaml`

Kubernetes pod configuration for Jenkins agents that:
- Uses Docker-in-Docker (DinD) for container builds
- Provides privileged access for Docker daemon
- Includes Jenkins JNLP agent for communication

### 4. Test Scripts

**File**: `jenkins/run-tests.sh`

Comprehensive test suite that validates:
- Container environment and system commands
- Project file structure and YAML syntax
- Kubernetes manifests and Flux configuration
- Security and performance metrics

## Setup Instructions

### Prerequisites

1. **Kubernetes Cluster** with Jenkins installed
2. **Docker Registry** (GitHub Container Registry recommended)
3. **Flux CD** installed and configured
4. **Git Repository** with GitOps manifests

### 1. Configure Jenkins

#### Install Required Plugins

- Kubernetes Plugin
- Docker Plugin
- Credentials Binding Plugin

#### Configure Docker Registry Credentials

1. Go to Jenkins → Manage Jenkins → Manage Credentials
2. Add new Username/Password credentials
3. Set ID: `ghcr-registry-account`
4. Username: GitHub username or organization
5. Password: GitHub personal access token with `read:packages` scope

#### Configure Kubernetes Cloud

1. Go to Jenkins → Manage Jenkins → Manage Nodes and Clouds
2. Configure Kubernetes cloud settings
3. Set pod template to use `jenkins/docker-pod.yaml`

### 2. Create Multibranch Pipeline

1. Go to Jenkins → New Item → Multibranch Pipeline
2. Configure repository URL and credentials
3. Set branch sources to include:
   - All branches for development builds
   - Tags for release builds
4. Save and let Jenkins scan the repository

### 3. Configure Flux

#### Deploy Image Automation Resources

```bash
# Apply Flux image automation configuration
kubectl apply -f control-plane/flux/jenkins-image-automation.yaml

# Verify resources
kubectl get imagerepository -n flux-system
kubectl get imagepolicy -n flux-system
kubectl get imageupdateautomation -n flux-system
```

#### Configure Git Repository

Ensure your GitRepository resource points to the correct branch:

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: flux-system
  namespace: flux-system
spec:
  interval: 5m
  ref:
    branch: main
  url: https://github.com/your-org/gitops-infra-control-plane
```

### 4. Enable Auto PR (Optional)

For production deployments, enable the GitHub Actions Auto PR workflow:

1. Deploy `.github/workflows/staging-auto-pr.yml`
2. Configure ImageUpdateAutomation to push to `staging` branch
3. Enable branch protection rules on main branch

## Workflow Process

### Development Workflow

1. **Developer pushes code** to feature branch
2. **Jenkins triggers** build pipeline
3. **Build stage**: Creates Docker image locally
4. **Development stage**: 
   - Pushes dev tag to registry
   - Runs tests in parallel
5. **Flux detects** new development image
6. **Automatic deployment** to development environment

### Release Workflow

1. **Developer creates Git tag**: `git tag v1.2.3`
2. **Jenkins triggers** release pipeline
3. **Build stage**: Rebuilds image with cache
4. **Test stage**: Runs full test suite
5. **Release stage**: 
   - Pushes SemVer tag
   - Pushes latest tag (for main branch)
6. **Flux detects** new release image
7. **Auto PR created** (if enabled)
8. **Manual approval** and merge to main
9. **Production deployment** triggered

## Configuration Options

### Environment Variables

Customize the pipeline by modifying these variables in `Jenkinsfile`:

```groovy
dockerRepoHost = 'ghcr.io'                    // Container registry
dockerRepoUser = '${{ github.repository_owner }}'  // Registry username
dockerRepoProj = 'gitops-infra-control-plane' // Repository name
jenkinsDockerSecret = 'ghcr-registry-account' // Jenkins credential ID
```

### Image Update Policies

Adjust Flux image policies based on your needs:

#### Development Policy
```yaml
filterTags:
  pattern: '^[a-zA-Z0-9_-]+-[a-fA-F0-9]{8}-[0-9]+$'
policy:
  alphabetical:
    order: asc
```

#### Production Policy
```yaml
filterTags:
  pattern: '^v?[0-9]+\.[0-9]+\.[0-9]+$'
policy:
  semver:
    range: '>=1.0.0'
```

### Jenkins Agent Configuration

Modify `jenkins/docker-pod.yaml` for different build requirements:

- **Resource limits**: Adjust CPU/memory based on build needs
- **Security context**: Configure based on cluster policies
- **Storage**: Add persistent volumes for build caches

## Security Considerations

### Jenkins Security

1. **Pod Security**: Use privileged pods only for Docker builds
2. **Credentials**: Store registry tokens in Jenkins credentials store
3. **Network**: Limit network access for build containers
4. **Image Scanning**: Integrate security scanning in pipeline

### Flux Security

1. **Repository Access**: Use read-only tokens for Git operations
2. **Image Registry**: Use scoped tokens with minimal permissions
3. **Branch Protection**: Enforce PR reviews for production changes
4. **Audit Trail**: Maintain complete git history of changes

### Container Security

1. **Base Images**: Use minimal, secure base images
2. **Scanning**: Scan images for vulnerabilities
3. **Signing**: Sign images with cosign or similar tools
4. **Policies**: Implement image admission policies

## Troubleshooting

### Common Issues

#### Jenkins Build Failures

1. **Docker Socket Issues**
   ```bash
   # Check Docker socket permissions
   ls -la /var/run/docker.sock
   
   # Ensure Jenkins pod has access
   kubectl describe pod jenkins-agent-pod
   ```

2. **Registry Authentication**
   ```bash
   # Test registry access
   docker login ghcr.io -u username -p token
   
   # Check Jenkins credentials
   # Jenkins → Manage Credentials → Update ghcr-registry-account
   ```

3. **Resource Constraints**
   ```bash
   # Check pod resource usage
   kubectl top pods
   
   # Adjust resource limits in docker-pod.yaml
   ```

#### Flux Image Update Issues

1. **Image Repository Not Syncing**
   ```bash
   # Check image repository status
   kubectl get imagerepository gitops-infra-control-plane -n flux-system -o yaml
   
   # Check logs
   kubectl logs -n flux-system deployment/image-reflector-controller
   ```

2. **Policy Not Matching**
   ```bash
   # Check available tags
   kubectl get image gitops-infra-control-plane -n flux-system -o yaml
   
   # Verify tag patterns
   # Update filterTags in imagepolicy.yaml
   ```

3. **Git Push Failures**
   ```bash
   # Check git repository credentials
   kubectl get secret -n flux-system
   
   # Verify git access
   flux reconcile source git flux-system
   ```

### Debug Commands

```bash
# Jenkins
kubectl logs -n jenkins deployment/jenkins
kubectl get pods -n jenkins

# Flux
flux get kustomizations -A
flux get sources -A
flux reconcile all -A

# Image Updates
kubectl get images -A
kubectl get imagepolicies -A
kubectl get imageupdateautomations -A
```

## Best Practices

### Jenkins Pipeline

1. **Parallel Execution**: Run tests in parallel to reduce build time
2. **Caching**: Use Docker layer caching for faster builds
3. **Fail Fast**: Fail early in pipeline to save resources
4. **Cleanup**: Clean up Docker images and containers after builds

### Flux Configuration

1. **Incremental Updates**: Use small, frequent updates
2. **Version Pinning**: Pin to specific versions for stability
3. **Monitoring**: Monitor Flux reconciliation status
4. **Backup**: Backup Git repository regularly

### GitOps Workflow

1. **Branch Strategy**: Use clear branch naming conventions
2. **Tag Management**: Follow SemVer for release tags
3. **Documentation**: Document deployment procedures
4. **Testing**: Test in development before production

## Integration Examples

### Example 1: Development Deployment

```bash
# Push to feature branch
git push origin feature/new-component

# Jenkins builds and tests
# Image tagged: feature-new-component-a1b2c3d4-1672531200

# Flux detects and deploys to development
kubectl get deployments -n development
```

### Example 2: Production Release

```bash
# Create release tag
git tag v1.2.3
git push origin v1.2.3

# Jenkins builds, tests, and pushes release
# Image tagged: v1.2.3

# Flux creates PR for review
# PR reviewed and merged

# Production deployment
kubectl get deployments -n production
```

## Advanced Features

### Multi-Environment Deployments

Configure different Flux resources for each environment:

```yaml
# Development
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImagePolicy
metadata:
  name: app-development
spec:
  filterTags:
    pattern: '^[a-zA-Z0-9_-]+-[a-fA-F0-9]{8}-[0-9]+$'

# Production
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImagePolicy
metadata:
  name: app-production
spec:
  filterTags:
    pattern: '^v?[0-9]+\.[0-9]+\.[0-9]+$'
```

### Custom Build Strategies

Replace Docker with other build tools:

```groovy
// Using BuildKit
sh """
  docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --push \
    -t ${env.DEVELOPMENT_IMAGE} \
    ./
"""

// Using Kaniko
sh """
  /kaniko/executor \
    --dockerfile Dockerfile \
    --destination ${env.DEVELOPMENT_IMAGE} \
    --cache=true
"""
```

### Integration with External Systems

Connect with monitoring, security scanning, or notification systems:

```groovy
stage('Security Scan') {
    steps {
        sh 'trivy image ${env.DEVELOPMENT_IMAGE}'
    }
}

stage('Notify Team') {
    steps {
        slackSend(
            channel: '#deployments',
            color: 'good',
            message: "✅ New image deployed: ${env.DEVELOPMENT_IMAGE}"
        )
    }
}
```

## Migration Guide

### From Traditional CI/CD

1. **Remove kubectl apply** from Jenkins pipelines
2. **Add ImageUpdateAutomation** resources
3. **Configure image policies** for automatic updates
4. **Enable branch protection** for production
5. **Monitor Flux reconciliation** status

### From Other GitOps Tools

1. **Export existing manifests** to Git repository
2. **Configure Flux GitRepository** source
3. **Set up image automation** resources
4. **Migrate pipelines** to push images only
5. **Test deployment** in development first

## Support and Resources

### Documentation

- [Flux CD Documentation](https://fluxcd.io/docs/)
- [Jenkins Pipeline Syntax](https://jenkins.io/doc/book/pipeline/syntax/)
- [GitOps Principles](https://fluxcd.io/docs/gitops/)

### Community

- [Flux CD Slack](https://fluxcd.slack.com/)
- [Jenkins Community](https://community.jenkins.io/)
- [Kubernetes Community](https://kubernetes.slack.com/)

### Examples

- [Jenkins + Flux Examples](https://github.com/fluxcd/flux2-kustomize-helm-example)
- [Multi-Environment GitOps](https://github.com/fluxcd/flux2-multi-tenancy)
- [Image Update Automation](https://github.com/fluxcd/flux2-image-update)

---

This integration provides a robust, secure, and scalable CI/CD pipeline that follows GitOps best practices while maintaining the separation of concerns between Jenkins (CI) and Flux (CD).

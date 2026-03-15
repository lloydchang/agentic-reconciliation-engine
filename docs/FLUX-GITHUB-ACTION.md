# Flux GitHub Action

## Overview

The Flux GitHub Action can be used to automate various tasks in CI such as:

- Automate Flux upgrades on clusters via Pull Requests
- Push Kubernetes manifests to container registries
- Run end-to-end testing with Flux and Kubernetes Kind

## Usage

```yaml
- name: Setup Flux CLI
  uses: fluxcd/flux2/action@main
  with:
    # Flux CLI version e.g. 2.0.0.
    # Defaults to latest stable release.
    version: 'latest'

    # Alternative download location for the Flux CLI binary.
    # Defaults to path relative to $RUNNER_TOOL_CACHE.
    bindir: ''
```

## Compatibility

The Flux GitHub Action is compatible with the Linux, macOS and Windows GitHub-hosted Runners.

The Flux GitHub Action is compatible with self-hosted GitHub Runners for the following architectures:

- amd64 (Linux, macOS, Windows)
- arm64 (Linux, macOS)
- arm/v7 (Linux)

## Examples

### Automate Flux Updates

Example workflow for updating Flux's components generated with `flux bootstrap --path=clusters/production`:

```yaml
name: update-flux

on:
  workflow_dispatch:
  schedule:
    - cron: "0 * * * *"

permissions:
  contents: write
  pull-requests: write

jobs:
  components:
    runs-on: ubuntu-latest
    steps:
      - name: Check out code
        uses: actions/checkout@v4
      - name: Setup Flux CLI
        uses: fluxcd/flux2/action@main
      - name: Check for updates
        id: update
        run: |
          flux install \
            --export > ./clusters/production/flux-system/gotk-components.yaml

          VERSION="$(flux -v)"
          echo "flux_version=$VERSION" >> $GITHUB_OUTPUT
      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v7
        with:
            branch: update-flux
            commit-message: Update to ${{ steps.update.outputs.flux_version }}
            title: Update to ${{ steps.update.outputs.flux_version }}
            body: |
              ${{ steps.update.outputs.flux_version }}
```

#### Pull Request Permissions

For automated pull requests to work, you will need to enable **Allow GitHub Actions to create and approve pull requests**, for your repository, which can be found at `https://github.com/<ORG>/<REPO>/settings/actions`.

### Push Kubernetes Manifests to Container Registries

Example workflow for publishing Kubernetes manifests bundled as OCI artifacts to GitHub Container Registry:

```yaml
name: push-artifact-staging

on:
  push:
    branches:
      - 'main'

permissions:
  packages: write # needed for ghcr.io access

env:
  OCI_REPO: "oci://ghcr.io/my-org/manifests/${{ github.event.repository.name }}"

jobs:
  kubernetes:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Setup Flux CLI
        uses: fluxcd/flux2/action@main
      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Generate manifests
        run: |
          kustomize build ./manifests/staging > ./deploy/app.yaml
      - name: Push manifests
        run: |
          flux push artifact $OCI_REPO:$(git rev-parse --short HEAD) \
            --path="./deploy" \
            --source="$(git config --get remote.origin.url)" \
            --revision="$(git branch --show-current)@sha1:$(git rev-parse HEAD)"
      - name: Deploy manifests to staging
        run: |
          flux tag artifact $OCI_REPO:$(git rev-parse --short HEAD) --tag staging
```

### Push and Sign Kubernetes Manifests to Container Registries

Example workflow for publishing Kubernetes manifests bundled as OCI artifacts which are signed with Cosign and GitHub OIDC:

```yaml
name: push-sign-artifact

on:
  push:
    branches:
      - 'main'

permissions:
  packages: write # needed for ghcr.io access
  id-token: write # needed for keyless signing

env:
  OCI_REPO: "oci://ghcr.io/my-org/manifests/${{ github.event.repository.name }}"

jobs:
  kubernetes:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Setup Flux CLI
        uses: fluxcd/flux2/action@main
      - name: Setup Cosign
        uses: sigstore/cosign-installer@main
        with:
          cosign-release: v2.6.1 # cosign v3+ will be supported only in Flux v2.8+
      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Push and sign manifests
        run: |
          digest_url=$(flux push artifact \
          $OCI_REPO:$(git rev-parse --short HEAD) \
          --path="./manifests" \
          --source="$(git config --get remote.origin.url)" \
          --revision="$(git branch --show-current)@sha1:$(git rev-parse HEAD)" \
          --output=json | \
          jq -r '. | .repository + "@" + .digest')

          cosign sign --yes $digest_url
```

### End-to-End Testing

Example workflow for running Flux in Kubernetes Kind:

```yaml
name: e2e

on:
  push:
    branches:
      - '*'

jobs:
  kubernetes:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Setup Flux CLI
        uses: fluxcd/flux2/action@main
      - name: Setup Kubernetes Kind
        uses: helm/kind-action@main
      - name: Install Flux in Kubernetes Kind
        run: flux install
```

A complete e2e testing workflow is available here: [flux2-kustomize-helm-example](https://github.com/fluxcd/flux2-kustomize-helm-example)

## Repository Integration

The Flux GitHub Action integrates seamlessly with the GitOps Infra Control Plane for automated CI/CD workflows.

### Integration with Control Plane

```yaml
# Example: Automated Flux component updates
name: update-flux-components
on:
  schedule:
    - cron: "0 2 * * 1"  # Weekly on Monday
permissions:
  contents: write
  pull-requests: write
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: fluxcd/flux2/action@main
      - run: |
          flux install --export > infrastructure/bootstrap/flux-system/gotk-components.yaml
          flux create source git flux-system \
            --url=https://github.com/your-org/your-repo \
            --branch=main \
            --export > infrastructure/bootstrap/flux-system/gotk-sync.yaml
      - uses: peter-evans/create-pull-request@v7
        with:
          title: "🤖 Automated Flux Components Update"
          body: "Weekly update of Flux components for security and feature enhancements"
          branch: automated/flux-update
```

### Benefits

#### Automated Upgrades

- Keep Flux components up-to-date without manual intervention
- Schedule regular updates for security patches
- Automate pull request creation for review and approval

#### OCI Artifact Management

- Publish Kubernetes manifests as signed OCI artifacts
- Enable secure distribution of configuration
- Support for supply chain security with Cosign signing

#### Testing Integration

- Run Flux in isolated Kind clusters for CI testing
- Validate manifests before production deployment
- Integrate with existing CI pipelines

## Advanced Usage

### Multi-Environment Deployments

```yaml
# Push to multiple registries/environments
name: multi-env-deploy
jobs:
  build-and-push:
    steps:
      - name: Push to staging
        run: flux push artifact oci://ghcr.io/org/app:staging --path=./manifests/staging
      - name: Push to production
        run: flux push artifact oci://ghcr.io/org/app:v1.2.3 --path=./manifests/production
```

### Integration with Image Automation

Combine Flux GitHub Action with image update automation for complete CI/CD:

```yaml
# CI: Build and push images
- name: Build and push image
  run: docker build -t app:${{ github.sha }} . && docker push app:${{ github.sha }}

# CI: Push manifests with new image
- name: Push manifests
  run: flux push artifact oci://registry/manifests:${{ github.sha }} --path=./k8s

# CD: Flux deploys automatically via ImagePolicy
# (Configured in GitOps repository)
```

Last modified 2025-10-20: Add cosign v3 to 2.8 roadmap (5ba6446)

# GitHub Actions Manifest Generation

## Disclaimer

This document is under review and may be declared out of scope for Flux.

Note that this guide no longer describes the recommended way to handle manifest generation in Flux. It also predates the introduction of OCIRepository and needs updates in consideration of those advancements.

Expect this doc to either be archived soon, or to receive a major overhaul in support of the new preferred approach described below.

## Author's Note

If you want to use Flux with tooling-generated manifests today, you should capture the output and store it in an OCI Artifact with flux push artifact. The following doc uses an old method that has many disadvantages: it can't be provenance secured with Cosign. The artifacts can't be indexed as efficiently as an OCI registry's tag-based distribution. Nor can the delivery of a private Git repository be authenticated and authorized in a workload cluster, using any cloud-based IAM or ambient environmental credentials that are typically used to secure a private OCI registry.

These methods were developed to bridge the gap for Flux users transitioning from Flux v1. The introduction of the OCIRepository since then, has nigh obsoleted the approach shown here. Please follow the OCI Cheatsheet guide to understand what is possible, and migrate your workflows to use Flux OCI!

## Overview

This guide shows how to configure GitHub Actions to generate Kubernetes manifests using various tools and commit them back to Git, where Flux's kustomize-controller applies them. This covers the "build-time" manifest generation pattern.

## Primary Uses of Flux

Flux's primary use case for kustomize-controller is to apply YAML manifests from the latest Revision of an Artifact.

## Security Consideration

Flux v2 can not be configured to call out to arbitrary binaries that a user might supply with an InitContainer, as it was possible to do in Flux v1.

## Motivation for this Guide

In Flux v2 it is assumed if users want to run more than Kustomize with envsubst, that it will be done outside of Flux; the goal of this guide is to show several common use cases of this pattern in secure ways.

## Demonstrated Concepts

It is intended, finally, to show through this use case, three fundamental ideas for use in CI to accompany Flux automation:

- Writing workflow that can commit changes back to the same branch of a working repository.
- A workflow to commit generated content from one directory into a different branch in the repository.
- Workflow to commit from any source directory into a target branch on a different repository.

Readers can interpret this document with adaptations for use with other CI providers, or Git source hosts, or manifest generators.

Jsonnet is demonstrated with examples presented in sufficient depth that, hopefully, Flux users who are not already familiar with manifest generation or Jsonnet can pick up kubecfg and start using it to solve novel and interesting configuration problems.

## Manifest Generation Examples

There are several use cases presented.

### String Substitution with sed -i

GitRepository source only targets one branch. While this first example operates on any branch (branches: ['*']), each Kustomization in Flux only deploys manifests from one branch or tag at a time.

```yaml
# ./.github/workflows/01-manifest-generate.yaml
name: Manifest Generation
on:
  push:
    branches:
    - '*'

jobs:
  run:
    name: Push Git Update
    runs-on: ubuntu-latest
    steps:
      - name: Prepare
        id: prep
        run: |
          VERSION=${GITHUB_SHA::8}
          echo BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') >> $GITHUB_OUTPUT
          echo VERSION=${VERSION} >> $GITHUB_OUTPUT

      - name: Checkout repo
        uses: actions/checkout@v3

      - name: Update manifests
        run: ./update-k8s.sh $GITHUB_SHA

      - name: Commit changes
        uses: EndBug/add-and-commit@v7
        with:
          add: '.'
          message: "[ci skip] deploy from ${{ steps.prep.outputs.VERSION }}"
          signoff: true
```

The script `update-k8s.sh`:

```bash
#!/bin/bash

# update-k8s.sh
set -feu # Usage: $0 <GIT_SHA> # Fails when GIT_SHA is not provided

GIT_SHA=${1:0:8}
sed -i "s|image: kingdonb/any-old-app:.*|image: kingdonb/any-old-app:$GIT_SHA|" k8s.yml
sed -i "s|GIT_SHA: .*|GIT_SHA: $GIT_SHA|" flux-config/configmap.yaml
```

### Docker Build and Tag with Version

ImageRepository can reflect both branches and tags.

```yaml
# ./.github/workflows/02-docker-build.yaml
name: Docker Build, Push

on:
  push:
    branches:
      - '*'
    tags-ignore:
      - 'release/*'

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - name: Prepare
        id: prep
        run: |
          VERSION=${GITHUB_SHA::8}
          if [[ $GITHUB_REF == refs/tags/* ]]; then
            VERSION=${GITHUB_REF/refs\/tags\//}
          fi
          echo BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') >> $GITHUB_OUTPUT
          echo VERSION=${VERSION} >> $GITHUB_OUTPUT

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v2

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to DockerHub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        id: docker_build
        uses: docker/build-push-action@v4
        with:
          push: true
          tags: kingdonb/any-old-app:${{ steps.prep.outputs.VERSION }}

      - name: Image digest
        run: echo ${{ steps.docker_build.outputs.digest }}
```

### Jsonnet for YAML Document Rehydration

GitRepository source only targets one branch. Since Flux uses one branch per Kustomization, to trigger an update we must write to a deploy branch or tag.

```yaml
# ./.github/workflows/03-release-manifests.yaml
name: Build jsonnet
on:
  push:
    tags: ['release/*']
    branches: ['release']

jobs:
  run:
    name: jsonnet push
    runs-on: ubuntu-latest
    steps:
      - name: Prepare
        id: prep
        run: |
          VERSION=${GITHUB_SHA::8}
          if [[ $GITHUB_REF == refs/tags/release/* ]]; then
            VERSION=${GITHUB_REF/refs\/tags\/release\//}
          fi
          echo BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') >> $GITHUB_OUTPUT
          echo VERSION=${VERSION} >> $GITHUB_OUTPUT

      - name: Checkout repo
        uses: actions/checkout@v3

      - name: Setup kubecfg CLI
        uses: kingdonb/kubecfg/action@main

      - name: kubecfg show
        run: kubecfg show manifests/example.jsonnet > output/production.yaml

      - name: Prepare target branch
        run: ./ci/rake.sh deploy

      - name: Commit changes
        uses: EndBug/add-and-commit@v7
        with:
          add: 'production.yaml'
          branch: deploy
          message: "[ci skip] from ${{ steps.prep.outputs.VERSION }}"
          signoff: true
```

### Jsonnet Examples

#### External Variable Substitution

```jsonnet
// manifests/example.jsonnet
local kube = import 'https://github.com/bitnami-labs/kube-libsonnet/raw/73bf12745b86718083df402e89c6c6c903edd327d2/kube.libsonnet';
local example = import 'example.libsonnet';

{
  version_configmap: kube.ConfigMap('any-old-app-version') {
    metadata+: {
      namespace: 'prod',
    },
    data+: {
      VERSION: std.extVar('VERSION'),
    },
  },
  flux_kustomization: example.kustomization('any-old-app-prod') {
    metadata+: {
      namespace: 'flux-system',
    },
    spec+: {
      path: './flux-config/',
      postBuild+: {
        substituteFrom+: [
          {
            kind: 'ConfigMap',
            name: 'any-old-app-version',
          },
        ],
      },
    },
  },
  flux_gitrepository: example.gitrepository('any-old-app-prod') {
    metadata+: {
      namespace: 'flux-system',
    },
    spec+: {
      url: 'https://github.com/kingdonb/any_old_app',
    },
  },
}
```

#### Make Two Environments

```jsonnet
// manifests/example.jsonnet
{
  version_configmap: kube.ConfigMap('any-old-app-version') {
    metadata+: {
      namespace: 'flux-system',
    },
    data+: {
      VERSION: std.extVar('VERSION'),
    },
  },
  test_flux_kustomization: example.kustomization('any-old-app-test') {
    spec+: {
      path: './flux-config/',
      postBuild+: {
        substituteFrom+: [
          {
            kind: 'ConfigMap',
            name: 'any-old-app-version',
          },
        ],
      },
      targetNamespace: 'test-tenant',
    },
  },
  prod_flux_kustomization: example.kustomization('any-old-app-prod') {
    spec+: {
      path: './flux-config/',
      postBuild+: {
        substituteFrom+: [
          {
            kind: 'ConfigMap',
            name: 'any-old-app-version',
          },
        ],
      },
      targetNamespace: 'prod-tenant',
    },
  },
  flux_gitrepository: example.gitrepository('any-old-app-prod') {
    metadata+: {
      namespace: 'flux-system',
    },
    spec+: {
      url: 'https://github.com/kingdonb/any_old_app',
    },
  },
}
```

#### List Comprehension for Multiple Environments

```jsonnet
// manifests/example.jsonnet
local kube = import 'https://github.com/bitnami-labs/kube-libsonnet/raw/73bf12745b86718083df402e89c6c6c903edd327d2/kube.libsonnet';
local example = import 'example.libsonnet';
local kubecfg = import 'kubecfg.libsonnet';
local kustomize = import 'kustomize.libsonnet';

local config_ns = 'flux-system';

local flux_config = [
  kube.ConfigMap('any-old-app-version') {
    data+: {
      VERSION: std.extVar('VERSION'),
    },
  },
  example.gitrepository('any-old-app-prod') {
    spec+: {
      url: 'https://github.com/kingdonb/any_old_app',
    },
  },
] + kubecfg.parseYaml(importstr 'examples/configMap.yaml');

local kustomization = kustomize.applyList([
  kustomize.namespace(config_ns),
]);

local kustomization_output = std.map(kustomization, flux_config);

{ flux_config: kustomization_output } + {

  local items = ['test', 'prod'],

  joined: {
    [ns + '_flux_kustomization']: {
      data: example.any_old_app(ns) {
        spec+: {
          prune: if ns == 'prod' then false else true,
        },
      },
    }
    for ns in items
  },
}
```

### Commit Across Repositories Workflow

```yaml
# ./.github/workflows/04-update-fleet-infra.yaml
name: Update Fleet-Infra
on:
  push:
    branches:
    - 'main'

jobs:
  run:
    name: Push Update
    runs-on: ubuntu-latest
    steps:
      - name: Prepare
        id: prep
        run: |
          VERSION=${GITHUB_SHA::8}
          if [[ $GITHUB_REF == refs/tags/* ]]; then
            VERSION=${GITHUB_REF/refs\/tags\//}
          fi
          echo BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') >> $GITHUB_OUTPUT
          echo VERSION=${VERSION} >> $GITHUB_OUTPUT

      - name: Checkout repo
        uses: actions/checkout@v3

      - name: Update manifests
        run: ./update-k8s.sh $GITHUB_SHA

      - name: Push directory to another repository
        uses: cpina/github-action-push-to-another-repository@v1.2
        env:
          API_TOKEN_GITHUB: ${{ secrets.API_TOKEN_GITHUB }}
        with:
          source-directory: 'flux-config'
          destination-github-username: 'kingdonb'
          destination-repository-name: 'fleet-infra'
          target-branch: 'deploy'
          user-email: kingdon+bot@weave.works
          commit-message: "[ci skip] deploy from ${{ steps.prep.outputs.VERSION }}"
```

## Adapting for Flux v2

In Flux v2, with ImagePolicy, these examples may be adjusted to order tags by their BUILD_DATE, by adding more string information to the tags. Besides a build timestamp, we can also add branch name.

Why not have it all: `${branch}-${sha}-${ts}` – this is the suggestion given in the Sortable image tags guide.

## Repository Integration

This GitHub Actions workflow is designed to work seamlessly with the GitOps Infra Control Plane. The generated manifests can be applied directly by Flux's kustomize-controller from the target Git repository branch.

### Integration with Flux

1. **Branch Targeting**: Kustomizations can target specific branches for different environments
2. **Manifest Generation**: CI generates manifests that Flux reconciles
3. **Multi-Repository**: Support for pushing to separate fleet-infra repositories
4. **Environment Separation**: Different branches for different environments

### Example Flux Configuration

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: app-manifests
  namespace: flux-system
spec:
  interval: 5m
  ref:
    branch: deploy  # Target the generated manifests branch
  url: https://github.com/my-org/my-app

---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 5m
  path: ./
  prune: true
  sourceRef:
    kind: GitRepository
    name: app-manifests
```

## Further Reading

- [Flux Image Update Guide](https://fluxcd.io/flux/guides/image-update/)
- [Sortable Image Tags](https://fluxcd.io/flux/guides/sortable-image-tags/)
- [Jsonnet Documentation](https://jsonnet.org/)
- [Kubecfg Documentation](https://github.com/bitnami-labs/kubecfg)

Last modified 2023-08-17: Fix and normalise internal links (8ac5345)

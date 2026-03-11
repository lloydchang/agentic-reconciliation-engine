# Flux Monitoring & Alerts Guide

## Overview

Flux provides comprehensive monitoring and alerting capabilities for GitOps pipelines. Different teams can receive notifications about their GitOps pipeline status - on-call teams get alerts about reconciliation failures, while dev teams get notified about successful deployments.

## Prerequisites

- Kubernetes cluster bootstrapped with Flux
- Flux notification controller (included in default installation)

## Notification Providers

Flux supports various notification providers including Slack, Microsoft Teams, Discord, PagerDuty, Telegram, Sentry, and others.

### Slack Provider Setup

Create a secret with your Slack bot token:

```bash
kubectl -n flux-system create secret generic slack-bot-token \
--from-literal=token=xoxb-YOUR-TOKEN
```

Create a notification provider:

```yaml
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Provider
metadata:
  name: slack-bot
  namespace: flux-system
spec:
  type: slack
  channel: general
  address: https://slack.com/api/chat.postMessage
  secretRef:
    name: slack-bot-token
```

## Alert Configuration

Create alerts for repositories and kustomizations:

```yaml
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: on-call-webapp
  namespace: flux-system
spec:
  summary: "cluster addons"
  eventMetadata:
    env: "production"
    cluster: "my-cluster"
    region: "us-east-2"
  providerRef:
    name: slack-bot
  eventSeverity: info
  eventSources:
    - kind: GitRepository
      name: '*'
    - kind: Kustomization
      name: '*'
```

### Alert Severities

- **info**: Alerts on object creation/updates, health check passing, dependency delays, errors
- **error**: Alerts only on reconciliation errors (build failures, validation errors, health check failures)

## Git Commit Status Integration

Flux can update Git commit status for GitHub, GitLab, Gitea, Bitbucket, and Azure DevOps, providing visual feedback on deployments.

### GitHub Provider Setup

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: github-token
  namespace: flux-system
data:
  token: <base64-encoded-token>
---
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Provider
metadata:
  name: github-status
  namespace: flux-system
spec:
  type: github
  address: https://github.com/<username>/<repository>
  secretRef:
    name: github-token
---
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: commit-status
  namespace: flux-system
spec:
  providerRef:
    name: github-status
  eventSeverity: info
  eventSources:
    - kind: Kustomization
      name: podinfo
```

### Benefits

- **Visual Feedback**: Green checkmarks/red crosses next to commits
- **Deployment Loop Closure**: Immediate feedback on reconciliation success/failure
- **API Integration**: Commit status can be queried programmatically
- **Automation Ready**: Enables custom promotion workflows

## Grafana Integration

Display Flux events as annotations on Grafana dashboards:

```yaml
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: grafana-events
  namespace: monitoring
spec:
  providerRef:
    name: grafana
  eventSeverity: info
  eventSources:
    - kind: GitRepository
      name: '*'
---
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Provider
metadata:
  name: grafana
  namespace: monitoring
spec:
  type: grafana
  address: "http://grafana.monitoring/api/annotations"
  secretRef:
    name: grafana-auth
```

## Flux GitHub Actions

### Setup Action

```yaml
- name: Setup Flux CLI
  uses: fluxcd/flux2/action@main
  with:
    version: 'latest'
    bindir: ''
```

### Automated Flux Updates

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
      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v7
        with:
          branch: update-flux
          commit-message: Update to Flux ${{ steps.update.outputs.flux_version }}
          title: Update to Flux ${{ steps.update.outputs.flux_version }}
```

### Push Manifests to OCI Registry

```yaml
name: push-artifact-staging
on:
  push:
    branches: ['main']
permissions:
  packages: write
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
      - name: Push manifests
        run: |
          flux push artifact $OCI_REPO:$(git rev-parse --short HEAD) \
            --path="./deploy" \
            --source="$(git config --get remote.origin.url)" \
            --revision="$(git branch --show-current)@sha1:$(git rev-parse HEAD)"
```

### End-to-End Testing

```yaml
name: e2e
on:
  push:
    branches: ['*']
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

## Monitoring Best Practices

### Alert Categories

1. **Infrastructure Alerts**: Cluster health, controller status
2. **Application Alerts**: Deployment success/failure, health checks
3. **Security Alerts**: Policy violations, access issues
4. **Performance Alerts**: Resource usage, response times

### Provider Selection

- **Slack/Microsoft Teams**: Team communication, on-call alerts
- **PagerDuty/Opsgenie**: Critical incident response
- **Git Providers**: CI/CD feedback, deployment tracking
- **Grafana**: Dashboard annotations, historical tracking

### Alert Tuning

- Use **error** severity for critical issues only
- Use **info** severity for informational updates
- Set appropriate timeouts for health checks
- Configure meaningful event metadata for filtering

## Troubleshooting

### Common Issues

1. **Events not received**: Check provider secret and permissions
2. **Commit status not updating**: Verify token has write access to repository
3. **Health check timeouts**: Adjust Kustomization timeout values
4. **Provider connectivity**: Verify network policies and DNS resolution

### Verification Commands

```bash
# Check alert status
flux get alerts

# View provider configurations
kubectl get providers -A

# Check notification controller logs
kubectl logs -n flux-system deployment/notification-controller
```

# Flux Monitoring & Alerts Implementation

This directory contains Flux monitoring and alerting configurations for the Agentic Reconciliation Engine.

## Files

- `providers/`: Notification provider configurations (Slack, Teams, GitHub, etc.)
- `alerts/`: Alert definitions for different event sources
- `grafana/`: Grafana integration for dashboard annotations

## Quick Setup

### 1. Slack Notifications

```bash
# Create Slack bot token secret
kubectl -n flux-system create secret generic slack-bot-token \
--from-literal=token=xoxb-YOUR-TOKEN

# Apply provider and alert
kubectl apply -k providers/slack/
kubectl apply -k alerts/on-call/
```

### 2. GitHub Commit Status

```bash
# Create GitHub token secret
kubectl -n flux-system create secret generic github-token \
--from-literal=token=YOUR-GITHUB-TOKEN

# Apply GitHub provider
kubectl apply -k providers/github/
kubectl apply -k alerts/commit-status/
```

### 3. Grafana Annotations

```bash
# Apply Grafana provider
kubectl apply -k providers/grafana/
kubectl apply -k alerts/grafana-events/
```

## Provider Types

- **slack**: Team notifications and alerts
- **msteams**: Microsoft Teams integration
- **discord**: Discord channels
- **pagerduty**: Incident management
- **github**: Commit status updates
- **gitlab**: GitLab integration
- **grafana**: Dashboard annotations

## Alert Severities

- **info**: Informational updates (deployments, health checks)
- **error**: Critical failures (reconciliation errors, health check failures)

## Event Sources

- **GitRepository**: Source sync events
- **Kustomization**: Reconciliation events
- **HelmRelease**: Chart deployment events
- **ImagePolicy**: Image update events

## Testing

```bash
# Check alert status
flux get alerts

# View recent events
kubectl get events -n flux-system --sort-by='.lastTimestamp'

# Test provider connectivity
flux get providers
```

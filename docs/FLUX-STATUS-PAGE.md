# Flux Status Page

## Overview

The Flux Status Page provides a lightweight, mobile-friendly web interface for real-time visibility into GitOps pipelines. Embedded within the Flux Operator, it requires no additional installation and offers mission control capabilities for Flux-managed clusters.

## Features

### Real-time Visibility

View the real-time status and readiness of all workloads managed by Flux across your cluster.

### Pinpoint Issues

Quickly identify and troubleshoot failures within your app delivery pipelines with detailed error messages.

### Advanced Search

Use powerful search and filtering to find specific resources instantly across all namespaces.

### Deep Dive Dashboards

Access dedicated dashboards for ResourceSets, HelmReleases, Kustomizations and Flux sources.

### Favorites

Mark important resources as favorites for quick access and at-a-glance status monitoring.

### Single Sign-On

Securely access the UI using OpenID Connect and Kubernetes RBAC policies mapped to your identity provider.

## Dashboards

### Cluster Dashboard

Get a complete overview of your Flux installation at a glance. Displays the status of all Flux controllers, recent reconciliation activity, and quick stats about GitOps resources including Kustomizations, HelmReleases, and source repositories.

### Helm Release Dashboard

Dive deep into individual HelmRelease configurations. View current state, revision history, applied values, conditions, and errors. Trigger Flux actions like reconcile, suspend, and resume with RBAC guards.

### Workloads Overview

Monitor all workloads managed by Flux across your cluster. See deployment status, replica counts, and health indicators for every application.

### GitOps Graph

Visualize your app delivery pipeline in an interactive graph. See real-time status updates as resources reconcile, trace dependencies from sources to deployments, and spot issues instantly.

### Reconciliation History

Track changes over time with detailed reconciliation history. See when resources were updated, what changed, and identify deployment patterns.

## Getting Started

### Access the Status Page

After installing the Flux Operator, port-forward to access the built-in dashboard:

```bash
kubectl -n flux-system port-forward svc/flux-operator 9080:9080
```

Open <http://localhost:9080> in your browser to monitor your GitOps pipelines.

### Configuration

The Status Page is automatically configured with the Flux Operator installation. For advanced configuration options, see the [config reference](https://fluxoperator.dev/docs/web-ui/config/).

## Next Steps

### Ingress Configuration

Set up [Ingress with TLS for external access](https://fluxoperator.dev/docs/web-ui/ingress/).

### User Management

Configure [role-based access control and user permissions](https://fluxoperator.dev/docs/web-ui/rbac/).

### SSO with Dex

Configure [Single Sign-On using Dex and OIDC](https://fluxoperator.dev/docs/web-ui/sso/).

## Repository Integration

The Flux Status Page integrates seamlessly with the GitOps Infra Control Plane, providing comprehensive monitoring and management capabilities.

### Integration Benefits

- **Unified Dashboard**: Single pane of glass for all GitOps operations
- **Real-time Monitoring**: Live status updates and health indicators
- **Troubleshooting**: Detailed error messages and reconciliation history
- **Multi-tenant Support**: Namespace-scoped views with proper RBAC
- **Mobile Friendly**: Responsive design for monitoring on any device

### Enterprise Features

- **SSO Integration**: Secure access with corporate identity providers
- **Advanced Search**: Powerful filtering and resource discovery
- **Favorites**: Quick access to critical resources
- **Audit Trail**: Comprehensive reconciliation history
- **Graph Visualization**: Interactive dependency mapping

Built by CNCF Flux core maintainers at ControlPlane. Licensed under AGPL-3.0.

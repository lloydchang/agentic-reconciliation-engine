# Strategic Architecture Context

**Strategic Architecture: Flux + Temporal + Consensus Hybrid Approach**

This file documents Flux operator deployment for simplified management within the hybrid architecture.

**North Star Vision**: Establish a reference implementation for autonomous, self-organizing infrastructure management.

**Current Status**: Providing enterprise-grade Flux deployment and management capabilities.

**Strategic Plan**: See [docs/STRATEGIC-ARCHITECTURE.md](docs/STRATEGIC-ARCHITECTURE.md) for comprehensive roadmap.

---

# Flux Operator

## Overview

The Flux Operator simplifies the deployment and management of Flux CD by providing a declarative way to install and configure Flux instances. It offers enterprise-grade features including multi-tenancy, sharding, and comprehensive monitoring.

## Quick Start

### 1. Install the Flux Operator CLI

Install the Flux Operator CLI using Homebrew:

```bash
brew install controlplaneio-fluxcd/tap/flux-operator
```

For other install methods see the [CLI documentation](https://fluxoperator.dev/docs/cli/).

### 2. Create a Flux Instance

Define your Flux configuration with the FluxInstance CRD:

```yaml
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
spec:
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
    domain: "cluster.local"
```

Install the Flux Operator and apply your configuration on a cluster:

```bash
flux-operator install -f flux-instance.yaml
```

Other deployment methods: [Helm](https://fluxoperator.dev/docs/installation/helm/), [Terraform](https://fluxoperator.dev/docs/installation/terraform/), [OperatorHub](https://operatorhub.io/operator/flux-operator).

### 3. Sync from a Git Repository

Add a sync configuration to deploy resources from a Git repository:

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
    pullSecret: "flux-system"
```

For private repositories, create a secret with your credentials:

```bash
flux-operator create secret basic-auth flux-system \
  --namespace=flux-system \
  --username=git \
  --password=$GITHUB_TOKEN
```

For more information on how to configure syncing from Git repositories, container registries and S3-compatible storage, refer to the [cluster sync guide](https://fluxoperator.dev/docs/sync/).

### 4. Access the Status Page

Port-forward to access the built-in dashboards:

```bash
kubectl -n flux-system port-forward svc/flux-operator 9080:9080
```

Open http://localhost:9080 in your browser to monitor your GitOps pipelines.

Learn more about the [Flux Web UI](https://fluxoperator.dev/docs/web-ui/) →

### 5. Setup the MCP Server

Install the Flux MCP Server to enable Agentic GitOps within Claude, Cursor, or other MCP-compatible tools:

```bash
brew install controlplaneio-fluxcd/tap/flux-operator-mcp
```

Add the following configuration to your AI assistant's MCP server settings:

```json
{
  "flux-operator-mcp": {
    "command": "flux-operator-mcp",
    "args": [
      "serve",
      "--read-only=false"
    ],
    "env": {
      "KUBECONFIG": "/path/to/.kube/config"
    }
  }
}
```

Learn more about the [Flux MCP Server](https://fluxoperator.dev/docs/mcp/) →

## Next Steps

### Instance Configuration
Learn about [multi-tenancy, sharding, scaling, and customization](https://fluxoperator.dev/docs/configuration/).

### ResourceSet API
Discover [self-service environments and app definitions](https://fluxoperator.dev/docs/resourceset/).

### AI Prompting Guide
Explore [effective prompting strategies for Flux MCP Server](https://fluxoperator.dev/docs/mcp/prompting/).

### Monitoring
Set up [Prometheus metrics and alerting](https://fluxoperator.dev/docs/monitoring/).

## Features

### Enterprise Distribution
- **Multi-tenancy**: Isolated Flux instances per team/namespace
- **Sharding**: Scale Flux controllers across multiple replicas
- **Security**: Built-in network policies and RBAC
- **Monitoring**: Comprehensive metrics and alerting
- **Web UI**: Built-in dashboards for GitOps monitoring

### MCP Server Integration
- **Agentic GitOps**: AI-powered GitOps operations
- **Claude/Cursor Integration**: Seamless IDE integration
- **Read/Write Operations**: Full GitOps workflow automation
- **Context Awareness**: Intelligent Flux resource management

### Deployment Options
- **CLI Installation**: Simple command-line deployment
- **Helm Charts**: Kubernetes-native package management
- **Terraform Provider**: Infrastructure-as-Code integration
- **OperatorHub**: Enterprise catalog integration

## Repository Integration

The Flux Operator integrates seamlessly with the GitOps Infrastructure Control Plane, providing an enterprise-ready way to deploy and manage Flux instances.

### Integration with Control Plane

```yaml
# Example: Flux Operator deployment in control plane
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: gitops-control-plane
  namespace: flux-system
spec:
  distribution:
    version: "2.x"
    registry: "ghcr.io/fluxcd"
  components:
    - source-controller
    - kustomize-controller
    - helm-controller
    - notification-controller
    - image-reflector-controller
    - image-automation-controller
  cluster:
    type: kubernetes
    size: large
    multitenant: true
    networkPolicy: true
  sync:
    kind: GitRepository
    url: "https://github.com/your-org/infrastructure"
    ref: "refs/heads/main"
    path: "clusters/production"
---
# MCP Server for AI-assisted operations
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-operator-mcp-config
  namespace: flux-system
data:
  config.json: |
    {
      "flux-operator-mcp": {
        "command": "flux-operator-mcp",
        "args": ["serve", "--read-only=false"],
        "env": {
          "KUBECONFIG": "/etc/kubernetes/kubeconfig"
        }
      }
    }
```

### Benefits

#### Simplified Operations
- **Single CRD**: Deploy complete Flux instances with one resource
- **Auto-scaling**: Automatic controller scaling based on load
- **Self-healing**: Built-in health checks and recovery
- **Multi-tenant**: Safe isolation between teams and environments

#### Enterprise Features
- **Web Dashboard**: Built-in monitoring and management UI
- **MCP Integration**: AI-powered GitOps operations
- **Security Hardening**: Network policies, RBAC, and audit logging
- **Compliance**: Enterprise-grade security and governance

#### Developer Experience
- **Quick Start**: Get Flux running in minutes
- **Rich CLI**: Powerful command-line tooling
- **Multiple Deployment Options**: Choose your preferred installation method
- **Comprehensive Documentation**: Enterprise-ready guides and examples

## Architecture

The Flux Operator manages the complete Flux CD lifecycle:

1. **Installation**: Deploys Flux controllers and CRDs
2. **Configuration**: Applies custom configurations and policies
3. **Sync Setup**: Configures Git/OCI/S3 sources for synchronization
4. **Monitoring**: Provides dashboards and metrics endpoints
5. **MCP Server**: Enables AI-assisted GitOps operations

This operator approach simplifies complex Flux deployments while maintaining all the power and flexibility of the underlying Flux toolkit.

Built by CNCF Flux core maintainers at ControlPlane. Licensed under AGPL-3.0.

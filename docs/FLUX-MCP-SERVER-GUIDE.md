# Flux MCP Server Configuration and Usage

This guide covers the setup, configuration, and usage of the Flux MCP (Model Context Protocol) Server for enabling Agentic GitOps with AI assistants like Claude, Cursor, and VS Code.

## Overview

The Flux MCP Server provides a bridge between AI assistants and Flux CD, enabling conversational GitOps operations through natural language commands.

## Installation

### Prerequisites

- Kubernetes cluster with Flux Operator installed
- kubectl configured to access the cluster
- AI assistant (Claude Desktop, Cursor, VS Code)

### Quick Install

```bash
# Install Flux MCP Server CLI
brew install controlplaneio-fluxcd/tap/flux-operator-mcp

# Run installation script
./scripts/install-flux-mcp-server.sh
```

### Manual Installation

```bash
# Install CLI
curl -L "https://github.com/controlplaneio-fluxcd/flux-operator-mcp/releases/latest/download/flux-operator-mcp-darwin-amd64" \
    -o /usr/local/bin/flux-operator-mcp
chmod +x /usr/local/bin/flux-operator-mcp

# Start MCP server
flux-operator-mcp serve --read-only=false --kubeconfig=$HOME/.kube/config --namespace=flux-system
```

## Configuration

### Claude Desktop Configuration

Create or update `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "flux-operator-mcp": {
      "command": "flux-operator-mcp",
      "args": [
        "serve",
        "--read-only=false",
        "--kubeconfig=/Users/username/.kube/config",
        "--namespace=flux-system",
        "--log-level=info"
      ],
      "env": {
        "KUBECONFIG": "/Users/username/.kube/config",
        "FLUX_NAMESPACE": "flux-system"
      }
    }
  }
}
```

### Cursor Configuration

Create `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "flux-operator-mcp": {
      "command": "flux-operator-mcp",
      "args": [
        "serve",
        "--read-only=false",
        "--kubeconfig=/Users/username/.kube/config",
        "--namespace=flux-system",
        "--log-level=info"
      ],
      "env": {
        "KUBECONFIG": "/Users/username/.kube/config",
        "FLUX_NAMESPACE": "flux-system"
      }
    }
  }
}
```

### VS Code Configuration

Create `~/.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "flux-operator-mcp": {
      "command": "flux-operator-mcp",
      "args": [
        "serve",
        "--read-only=false",
        "--kubeconfig=/Users/username/.kube/config",
        "--namespace=flux-system",
        "--log-level=info"
      ],
      "env": {
        "KUBECONFIG": "/Users/username/.kube/config",
        "FLUX_NAMESPACE": "flux-system"
      }
    }
  }
}
```

## MCP Server Commands

### Flux Instance Management

#### List Flux Instances
```bash
# Available MCP command: list_flux_instances
"List all Flux instances in the flux-system namespace"
```

#### Get Flux Instance
```bash
# Available MCP command: get_flux_instance
"Get the details of the flux FluxInstance"
"Get the flux FluxInstance with full YAML output"
```

#### Create Flux Instance
```bash
# Available MCP command: create_flux_instance
"Create a new FluxInstance named 'app-flux' with the following configuration:
- Sync from https://github.com/user/app-manifests
- Use the main branch
- Path: clusters/production
- Include source-controller, kustomize-controller, and helm-controller"
```

#### Update Flux Instance
```bash
# Available MCP command: update_flux_instance
"Update the flux FluxInstance to use the staging branch instead of main"
"Add notification-controller to the flux FluxInstance components"
```

#### Delete Flux Instance
```bash
# Available MCP command: delete_flux_instance
"Delete the app-flux FluxInstance"
```

### ResourceSet Management

#### List ResourceSets
```bash
# Available MCP command: list_resourcesets
"List all ResourceSets in the flux-system namespace"
```

#### Get ResourceSet
```bash
# Available MCP command: get_resourceset
"Get the details of the infrastructure ResourceSet"
"Show the resources in the infrastructure ResourceSet"
```

#### Create ResourceSet
```bash
# Available MCP command: create_resourceset
"Create a ResourceSet named 'app-resources' with the following resources:
- Kustomization for app-deployment
- HelmRelease for app-helm
- GitRepository for app-source"
```

### Sync and Reconciliation

#### Sync Status
```bash
# Available MCP command: sync_status
"What is the current sync status of all Flux instances?"
"Show the sync status of the flux FluxInstance"
"Check if there are any sync failures"
```

#### Trigger Reconciliation
```bash
# Available MCP command: reconcile_flux_instance
"Trigger reconciliation for the flux FluxInstance"
"Force reconcile all Flux instances"
```

### Health and Monitoring

#### Health Check
```bash
# Available MCP command: health_check
"Check the health status of all Flux components"
"Show the health of the flux FluxInstance"
"Are there any unhealthy Flux resources?"
```

#### Get Events
```bash
# Available MCP command: get_events
"Get recent events for the flux FluxInstance"
"Show the last 10 events for all Flux instances"
"Are there any warning or error events?"
```

#### Component Status
```bash
# Available MCP command: component_status
"Check the status of all Flux components"
"Show the status of source-controller and kustomize-controller"
"Are all Flux controllers running properly?"
```

## Usage Examples

### Basic GitOps Operations

#### Deploy New Application
```bash
"Create a new FluxInstance for my-app that:
- Syncs from https://github.com/user/my-app-manifests
- Uses the main branch
- Deploys to the my-app namespace
- Includes source-controller, kustomize-controller, and helm-controller
- Enables health checks"
```

#### Update Deployment
```bash
"Update the my-app FluxInstance to:
- Use the develop branch
- Add notification-controller to components
- Increase sync interval to 2 minutes"
```

#### Troubleshooting
```bash
"My FluxInstance is not syncing properly. Can you:
1. Check the sync status
2. Show recent events
3. Verify all components are healthy
4. Trigger a manual reconciliation"
```

### Multi-Environment Management

#### Create Staging Environment
```bash
"Create a staging FluxInstance that:
- Syncs from https://github.com/user/infrastructure-manifests
- Uses the staging branch
- Deploys to staging namespaces
- Has smaller resource limits than production"
```

#### Promote to Production
```bash
"Update the production FluxInstance to:
- Use the latest commit from main branch
- Enable webhook triggers
- Add comprehensive health checks
- Set up notifications for failures"
```

### Advanced Operations

#### Multi-Source Sync
```bash
"Create a FluxInstance that syncs from multiple sources:
1. GitRepository for infrastructure manifests
2. OCIRepository for Helm charts
3. Bucket for configuration files
- Use proper dependency ordering
- Enable health checks for all components"
```

#### Enable Monitoring
```bash
"Update the flux FluxInstance to:
- Enable Prometheus monitoring
- Add service monitors
- Configure alerts for sync failures
- Set up dashboard configurations"
```

## Configuration Options

### Server Options

```bash
flux-operator-mcp serve \
  --read-only=false \
  --kubeconfig=$HOME/.kube/config \
  --namespace=flux-system \
  --log-level=info \
  --port=8080 \
  --host=localhost
```

#### Option Descriptions

- `--read-only`: Enable read-only mode (default: false)
- `--kubeconfig`: Path to kubeconfig file
- `--namespace`: Default namespace for Flux resources
- `--log-level`: Log level (debug, info, warning, error)
- `--port`: Server port (default: 8080)
- `--host`: Server host (default: localhost)

### Environment Variables

```bash
export KUBECONFIG=$HOME/.kube/config
export FLUX_NAMESPACE=flux-system
export FLUX_LOG_LEVEL=info
export FLUX_READ_ONLY=false
```

## Security Considerations

### Read-Only Mode

For production environments, consider enabling read-only mode:

```json
{
  "mcpServers": {
    "flux-operator-mcp": {
      "command": "flux-operator-mcp",
      "args": [
        "serve",
        "--read-only=true",
        "--kubeconfig=/Users/username/.kube/config",
        "--namespace=flux-system"
      ]
    }
  }
}
```

### RBAC Configuration

Create a service account with limited permissions:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: flux-mcp
  namespace: flux-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: flux-mcp-reader
rules:
- apiGroups: ["fluxcd.controlplane.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: flux-mcp-reader
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: flux-mcp-reader
subjects:
- kind: ServiceAccount
  name: flux-mcp
  namespace: flux-system
```

### Network Security

Configure network policies to restrict MCP server access:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: flux-mcp-netpol
  namespace: flux-system
spec:
  podSelector:
    matchLabels:
      app: flux-mcp
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: flux-system
  - to: []
    ports:
    - protocol: TCP
      port: 443  # Kubernetes API
```

## Troubleshooting

### Common Issues

#### MCP Server Not Starting

```bash
# Check kubeconfig
echo $KUBECONFIG
kubectl cluster-info

# Check Flux Operator
kubectl get crd fluxinstances.fluxcd.controlplane.io

# Check permissions
kubectl auth can-i get fluxinstances
```

#### AI Assistant Not Showing Tools

```bash
# Restart AI assistant
# Check configuration file syntax
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | jq .

# Check MCP server logs
flux-operator-mcp serve --log-level=debug
```

#### Permission Errors

```bash
# Check current user
kubectl whoami

# Check service account permissions
kubectl auth can-i create fluxinstances --as=system:serviceaccount:flux-system:default

# Test basic operations
kubectl get fluxinstances -n flux-system
```

### Debug Commands

```bash
# Enable debug logging
flux-operator-mcp serve --log-level=debug

# Test MCP server manually
curl -X POST http://localhost:8080/mcp/list_flux_instances

# Check system logs
# macOS
log show --predicate 'process == "flux-operator-mcp"' --last 1h

# Linux
journalctl --user -u flux-mcp --since "1 hour ago"
```

## Best Practices

### 1. Configuration Management

- Use environment-specific configurations
- Store sensitive data in secrets
- Version control configuration files
- Use read-only mode for production

### 2. Security

- Enable read-only mode when possible
- Use service accounts with minimal permissions
- Configure network policies
- Monitor MCP server access

### 3. Performance

- Optimize kubeconfig for large clusters
- Use appropriate log levels
- Limit concurrent requests
- Monitor resource usage

### 4. Reliability

- Set up health checks
- Configure automatic restarts
- Monitor MCP server logs
- Use systemd/launch agents for auto-start

## Advanced Features

### Custom Commands

Extend MCP server with custom commands:

```bash
# Create custom command file
cat > custom-commands.json << EOF
{
  "commands": {
    "deploy_app": {
      "description": "Deploy a new application",
      "parameters": {
        "name": "string",
        "repository": "string",
        "branch": "string",
        "namespace": "string"
      }
    }
  }
}
EOF

# Load custom commands
flux-operator-mcp serve --custom-commands=custom-commands.json
```

### Integration with Other Tools

Configure MCP server to work with other GitOps tools:

```bash
# Integrate with ArgoCD
flux-operator-mcp serve --argocd-enabled=true

# Integrate with Jenkins
flux-operator-mcp serve --jenkins-enabled=true

# Integrate with GitHub Actions
flux-operator-mcp serve --github-actions-enabled=true
```

### Multi-Cluster Support

Configure MCP server for multi-cluster environments:

```bash
# Multi-cluster configuration
flux-operator-mcp serve \
  --kubeconfig-dir=/path/to/kubeconfigs \
  --default-cluster=production \
  --cluster-discovery=true
```

## Examples and Templates

### Production Deployment Template

```bash
"Create a production-ready FluxInstance with:
- High availability configuration
- Comprehensive monitoring
- Security best practices
- Health checks and alerts
- Backup and recovery procedures"
```

### Development Template

```bash
"Create a development FluxInstance with:
- Fast sync intervals
- Debug logging enabled
- Test configurations
- Rollback capabilities
- Feature flag support"
```

### Multi-Tenant Template

```bash
"Create a multi-tenant FluxInstance with:
- Namespace isolation
- RBAC per tenant
- Resource quotas
- Network policies
- Audit logging"
```

## Community and Support

### Getting Help

- **Documentation**: https://fluxoperator.dev/mcp/
- **GitHub Issues**: https://github.com/controlplaneio-fluxcd/flux-operator-mcp/issues
- **Discord**: https://discord.gg/fluxcd
- **Discussions**: https://github.com/controlplaneio-fluxcd/flux-operator-mcp/discussions

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Release Notes

Check the [GitHub Releases](https://github.com/controlplaneio-fluxcd/flux-operator-mcp/releases) for the latest updates and features.

---

This comprehensive guide provides everything needed to set up and use the Flux MCP Server for Agentic GitOps operations with AI assistants.

# Flux MCP Server

## Overview

The Flux MCP Server connects AI assistants directly to your Kubernetes clusters, enabling seamless interaction through natural language for troubleshooting, analysis, and operations. It provides AI-powered GitOps capabilities through the Model Context Protocol (MCP).

## Capabilities

### Instant Understanding
Quickly understand your Flux installation status, resource configurations, and deployment histories across environments.

### Environment Comparison
Compare Flux configurations for applications and infrastructure between development, staging, and production.

### Faster Incident Response
Reduce mean time to resolution (MTTR) during incidents with contextual analysis and actionable remediation steps.

### Root Cause Analysis
Automatically correlate events, logs, and configuration changes to identify the source of failures in a GitOps pipeline.

### Pipeline Management
Trigger reconciliations, suspend/resume Flux resources, and manage your delivery pipelines with simple requests.

### Visualization
Generate diagrams that map out Flux dependencies, resource relationships, and delivery workflows across clusters.

## How It Works

The Flux MCP Server integrates with AI assistants through the Model Context Protocol:

```
AI Agent (Claude, Copilot, Gemini)
    ↓
MCP Client
    ↓
Flux MCP Server (Local or remote kubeconfig)
    ↓
Kubernetes Clusters
```

When you ask a question or make a request, the AI uses purpose-built tools to gather information, analyze configurations, and perform operations based on your instructions.

## Security Built-in

The Flux MCP Server is designed with security in mind:

- **Read-only Mode**: Provides observation capabilities without affecting cluster state
- **Secret Masking**: Automatically masks sensitive information in Kubernetes Secret values
- **RBAC Compliance**: Operates with your existing kubeconfig permissions
- **Impersonation Support**: Supports Kubernetes impersonation for limited access
- **File System Security**: Read-only access to local file system, restricted to kubeconfig

## Installation

### Prerequisites
- Flux Operator installed and running
- AI assistant that supports MCP (Claude, Cursor, etc.)
- Valid kubeconfig with appropriate cluster access

### Install Flux MCP Server

```bash
brew install controlplaneio-fluxcd/tap/flux-operator-mcp
```

### Configure AI Assistant

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

## Usage Examples

### Natural Language Commands

With the MCP server configured, you can interact with your Flux clusters using natural language:

- **"Show me the status of all Flux resources in the production namespace"**
- **"Why is the my-app deployment failing?"**
- **"Compare the Flux configuration between staging and production"**
- **"Trigger a reconciliation for the flux-system kustomization"**
- **"Generate a diagram of my GitOps pipeline dependencies"**

### Troubleshooting Support

The MCP server provides contextual analysis for common issues:

- **Incident Response**: "What's causing the deployment failure in the web app?"
- **Configuration Drift**: "Are there any differences between my Git manifests and cluster state?"
- **Performance Issues**: "Why is reconciliation taking so long?"

### Operational Tasks

- **Reconciliation**: "Reconcile the flux-system resources"
- **Suspension**: "Suspend the problematic helm release"
- **Status Checks**: "Give me a summary of all failing resources"

## Advanced Features

### Environment Comparison
Compare configurations across environments:

```
Compare the Flux resources between dev and prod environments
Show differences in HelmRelease configurations
Identify configuration drift between clusters
```

### Root Cause Analysis
Automated analysis of failures:

```
Analyze why the recent deployment failed
Correlate events leading to the outage
Identify configuration changes that caused issues
```

### Pipeline Visualization
Generate dependency diagrams:

```
Show the GitOps pipeline for my microservices
Map out Flux resource relationships
Visualize the deployment workflow
```

## Integration with Control Plane

The Flux MCP Server integrates seamlessly with the GitOps Infrastructure Control Plane, providing AI-powered operations for the complete enterprise platform.

### Enterprise Benefits
- **Accelerated Troubleshooting**: Reduce MTTR with AI-assisted analysis
- **Natural Interaction**: Use plain English to manage complex GitOps operations
- **Contextual Insights**: Get intelligent recommendations and explanations
- **Secure Automation**: Perform operations with full RBAC and audit trails
- **Multi-cluster Support**: Manage multiple clusters through unified AI interface

### Configuration Examples

```yaml
# Example: MCP Server configuration for enterprise deployment
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-mcp-config
  namespace: flux-system
data:
  mcp-config.json: |
    {
      "flux-operator-mcp": {
        "command": "flux-operator-mcp",
        "args": ["serve", "--read-only=false", "--multi-cluster=true"],
        "env": {
          "KUBECONFIG": "/etc/kubernetes/multi-cluster-config",
          "FLUX_MCP_LOG_LEVEL": "info"
        }
      }
    }
---
# RBAC for MCP operations
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: flux-mcp-operator
rules:
- apiGroups: ["fluxcd.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "patch", "update"]
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list"]
```

## Best Practices

### Security Considerations
- Use read-only mode for initial exploration
- Implement proper RBAC for AI-assisted operations
- Regularly audit MCP server access logs
- Keep kubeconfig files secure and rotated

### Performance Optimization
- Configure appropriate timeouts for large clusters
- Use filtering to limit result sets
- Cache frequently accessed information
- Monitor MCP server resource usage

### Operational Guidelines
- Start with simple queries to learn capabilities
- Use natural language descriptions for complex requests
- Validate AI suggestions before applying changes
- Combine MCP insights with traditional kubectl commands

## Prompting Guide

For effective interaction with the Flux MCP Server, refer to the [prompting guide](https://fluxoperator.dev/docs/mcp/prompting/) which provides detailed examples and best practices for various use cases.

Built by CNCF Flux core maintainers at ControlPlane. Licensed under AGPL-3.0.

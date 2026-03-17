# Pi-Mono Containerized Agent Documentation

## Overview

This document provides comprehensive documentation for the Pi-Mono containerized agent implementation as the third agent execution method in the GitOps Control Plane architecture.

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture](#architecture)
3. [Implementation Details](#implementation-details)
4. [Deployment Guide](#deployment-guide)
5. [Usage Examples](#usage-examples)
6. [Integration Points](#integration-points)
7. [Configuration](#configuration)
8. [Monitoring & Observability](#monitoring--observability)
9. [Security Considerations](#security-considerations)
10. [Troubleshooting](#troubleshooting)
11. [Comparison with Other Methods](#comparison-with-other-methods)
12. [Future Enhancements](#future-enhancements)

---

## Introduction

### What is Pi-Mono?

Pi-Mono is a comprehensive AI agent toolkit that provides:
- Interactive coding assistance
- Multi-provider LLM support (Anthropic, OpenAI, Google, etc.)
- Extensible skill system (agentskills.io compatible)
- Rich tool ecosystem with built-in tools
- RPC mode for container integration

### Why Containerized Pi-Mono?

The containerized pi-mono agent serves as a **third execution method** alongside:
1. **Temporal Workflows** - Complex orchestration
2. **Container Agents** - Custom implementations
3. **Pi-Mono RPC** - Interactive AI assistance

### Key Benefits

- **Interactive**: Rich TUI and web interfaces
- **Multi-Provider**: 15+ LLM providers supported
- **Skill Compatible**: Full agentskills.io compliance
- **GitOps Integrated**: All changes audited via PR workflow
- **Simple Setup**: Container-based deployment

---

## Architecture

### System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  User / Operator Request                     │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│              Agent Execution Methods                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   Temporal  │ │   Container │ │     Pi-Mono RPC         │ │
│  │   Workflows │ │   Agents    │ │     Container           │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└───────────┬───────────────────┬───────────────────────────────┘
            │                   │
            ▼                   ▼
┌───────────────────────┐  ┌───────────────────────────────────┐
│  Memory Agent Layer   │  │       GitOps Control Layer        │
│                       │  │                                   │
│  Rust / Go / Python   │  │  Executes structured JSON plans   │
│  Local inference      │  │  via Flux or ArgoCD. Never runs   │
│  (llama.cpp / Ollama) │  │  LLM output directly on cluster.  │
│  SQLite persistence   │  │                                   │
└───────────────────────┘  └───────────────────────────────────┘
            │                          │
            └──────────────┬───────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│           Monitoring & Observability Layer                   │
│     Prometheus · Grafana · ELK · Alertmanager · Dashboard    │
└──────────────────────────────────────────────────────────────┘
```

### Pi-Mono Container Architecture

```
┌─────────────────────────────────────────┐
│           Pi-Mono Container            │
├─────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────────────┐ │
│  │   RPC Mode  │ │   Skills System     │ │
│  │             │ │                     │ │
│  │ • stdin/stdout│ │ • agentskills.io    │ │
│  │ • JSON-RPC   │ │ • GitOps operations │ │
│  │ • Events     │ │ • Custom skills     │ │
│  └─────────────┘ └─────────────────────┘ │
├─────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────────────┐ │
│  │   LLM API   │ │   Extensions        │ │
│  │             │ │                     │ │
│  │ • 15+ providers│ │ • TypeScript       │ │
│  │ • Model mgmt │ │ • Custom tools      │ │
│  │ • Auth       │ │ • UI components     │ │
│  └─────────────┘ └─────────────────────┘ │
├─────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────────────┐ │
│  │   GitOps    │ │   Monitoring        │ │
│  │             │ │                     │ │
│  │ • PR workflow│ │ • Metrics           │ │
│  │ • K8s recon  │ │ • Health checks     │ │
│  │ • Safety     │ │ • Logging           │ │
│  └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## Implementation Details

### Repository Structure

```
core/ai/runtime/pi-mono-agent/
├── Dockerfile                 # Container definition
├── README.md                  # Implementation documentation
├── package.json               # Node.js dependencies
├── config/
│   └── settings.json          # Pi-mono configuration
├── k8s/
│   └── pi-mono-agent-deployment.yaml  # Kubernetes manifests
└── skills/
    └── gitops-operations/
        └── SKILL.md           # GitOps operations skill
```

### Key Components

#### 1. Dockerfile
- **Base Image**: `node:18-alpine`
- **Security**: Non-root user (uid/gid: 1001)
- **Installation**: Global pi-mono installation
- **Health Checks**: RPC endpoint monitoring
- **Ports**: 8080 for RPC communication

#### 2. Kubernetes Deployment
- **Replicas**: 3 (auto-scaling to 10)
- **Resources**: 500m CPU, 512Mi memory (limits: 2CPU, 2Gi)
- **Environment Variables**: API keys, service URLs
- **Probes**: Liveness and readiness checks
- **Security**: Non-root, read-only filesystem

#### 3. Configuration
- **Default Model**: Anthropic Claude 3.5 Sonnet
- **Skills**: Enabled with agentskills.io support
- **GitOps**: PR-based approval workflow
- **Monitoring**: Token usage and cost tracking

#### 4. Skills System
- **agentskills.io Compatible**: Full specification compliance
- **GitOps Operations**: Infrastructure deployment and management
- **Risk Assessment**: Medium risk, conditional autonomy
- **Human Gates**: PR approval for production changes

---

## Deployment Guide

### Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Container registry access
- LLM provider API keys

### Quick Start

#### 1. Build Container

```bash
cd core/ai/runtime/pi-mono-agent
docker build -t gitops-infra-control-plane/pi-mono-agent:latest .
```

#### 2. Create Secrets

```bash
kubectl create secret generic ai-api-keys \
  --from-literal=anthropic-api-key=sk-ant-... \
  --from-literal=openai-api-key=sk-... \
  --from-literal=google-ai-api-key=... \
  -n ai-infrastructure
```

#### 3. Deploy to Kubernetes

```bash
kubectl apply -f k8s/pi-mono-agent-deployment.yaml
```

#### 4. Verify Deployment

```bash
# Check pod status
kubectl get pods -n ai-infrastructure -l app=pi-mono-agent

# Check service
kubectl get svc -n ai-infrastructure pi-mono-agent-service

# View logs
kubectl logs -f deployment/pi-mono-agent -n ai-infrastructure
```

### Environment Variables

| Variable | Description | Required |
|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | No |
| `OPENAI_API_KEY` | OpenAI GPT API key | No |
| `GOOGLE_AI_API_KEY` | Google Gemini API key | No |
| `PI_WORKSPACE_DIR` | Working directory | No |
| `MEMORY_AGENT_URL` | Memory agent service URL | No |
| `TEMPORAL_ADDRESS` | Temporal service address | No |
| `PROMETHEUS_URL` | Prometheus service URL | No |

---

## Usage Examples

### RPC Communication

#### Basic Prompt

```bash
# Send JSON-RPC command
echo '{"type":"prompt","message":"Hello, how can you help with GitOps?"}' | \
  kubectl exec -i deployment/pi-mono-agent -n ai-infrastructure -- \
  pi --mode rpc --no-session
```

#### Skill Execution

```bash
# Execute GitOps skill
echo '{"type":"skill","skill":"gitops-operations","message":"Check deployment status"}' | \
  kubectl exec -i deployment/pi-mono-agent -n ai-infrastructure -- \
  pi --mode rpc --no-session
```

#### Health Check

```bash
# Ping the agent
echo '{"type":"ping"}' | \
  kubectl exec -i deployment/pi-mono-agent -n ai-infrastructure -- \
  pi --mode rpc --no-session
```

### Port Forwarding

```bash
# Forward port for local access
kubectl port-forward -n ai-infrastructure svc/pi-mono-agent-service 8080:8080

# Send request locally
curl -X POST http://localhost:8080 \
  -H 'Content-Type: application/json' \
  -d '{"type":"prompt","message":"Review this Kubernetes manifest"}'
```

### Interactive Session

```bash
# Connect to container for interactive mode
kubectl exec -it deployment/pi-mono-agent -n ai-infrastructure -- /bin/sh

# Start interactive pi-mono
pi --provider anthropic --model claude-3-5-sonnet-20241022
```

---

## Integration Points

### Memory Agent Integration

```typescript
// Query memory agent from pi-mono skill
const response = await fetch(`${MEMORY_AGENT_URL}/api/query`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: "previous deployment patterns",
    limit: 5
  })
});
```

### Temporal Workflow Integration

```bash
# Trigger Temporal workflow from pi-mono
curl -X POST "$TEMPORAL_ADDRESS/api/v1/workflows" \
  -H 'Content-Type: application/json' \
  -d '{
    "workflowType": "gitops-deployment",
    "input": {"manifests": ["k8s/deployment.yaml"]}
  }'
```

### GitOps Pipeline Integration

```bash
# Create PR for infrastructure changes
git add gitops/manifests/
git commit -m "Infrastructure update: add new service"
git push origin feature/infrastructure-update
gh pr create --title "Infrastructure Update" --body "Changes: Add new microservice"
```

### Monitoring Integration

```bash
# Metrics endpoint
curl http://pi-mono-agent-service.ai-infrastructure.svc.cluster.local:8080/metrics

# Health endpoint
curl http://pi-mono-agent-service.ai-infrastructure.svc.cluster.local:8080/health
```

---

## Configuration

### Settings File

Located at `/home/pi/.pi/agent/settings.json`:

```json
{
  "defaultModel": "anthropic:claude-3-5-sonnet-20241022",
  "enableSkills": true,
  "enableExtensions": true,
  "enablePrompts": true,
  "workingDirectory": "/workspace",
  "theme": "dark",
  "gitOps": {
    "enabled": true,
    "autoCommit": false,
    "prRequired": true,
    "reviewRequired": true
  },
  "monitoring": {
    "enabled": true,
    "tokenUsage": true,
    "costTracking": true,
    "performanceMetrics": true
  },
  "rpc": {
    "enabled": true,
    "timeout": 30000
  },
  "container": {
    "mode": "rpc",
    "noSession": true,
    "sessionDir": "/home/pi/.pi/agent/sessions"
  }
}
```

### Model Configuration

```json
{
  "providers": {
    "anthropic": {
      "type": "anthropic",
      "apiKey": "${ANTHROPIC_API_KEY}",
      "models": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
    },
    "openai": {
      "type": "openai",
      "apiKey": "${OPENAI_API_KEY}",
      "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
    }
  }
}
```

---

## Monitoring & Observability

### Built-in Metrics

Pi-mono provides comprehensive monitoring out of the box:

#### Token Usage
- Input/output tokens per request
- Cost tracking by provider
- Rate limiting monitoring

#### Performance Metrics
- Response times by model
- Request success rates
- Error categorization

#### Agent Metrics
- Skill execution counts
- Extension usage statistics
- Session management metrics

### Prometheus Integration

```yaml
# ServiceMonitor for Prometheus scraping
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: pi-mono-agent-monitor
  namespace: ai-infrastructure
spec:
  selector:
    matchLabels:
      app: pi-mono-agent
  endpoints:
  - port: rpc
    path: /metrics
    interval: 30s
```

### Logging

Structured JSON logging with correlation IDs:

```json
{
  "timestamp": "2026-03-17T00:00:00Z",
  "level": "info",
  "correlation_id": "req-123456",
  "event": "skill_execution",
  "skill": "gitops-operations",
  "duration_ms": 1500,
  "tokens_used": 1250,
  "cost_usd": 0.00625
}
```

### Health Checks

#### Liveness Probe
```bash
echo '{"type":"ping"}' | timeout 10 pi --mode rpc --no-session
```

#### Readiness Probe
```bash
echo '{"type":"ping"}' | timeout 5 pi --mode rpc --no-session
```

---

## Security Considerations

### Container Security

- **Non-root Execution**: Runs as user/group 1001
- **Minimal Base Image**: Alpine Linux with minimal packages
- **Resource Limits**: CPU/memory constraints
- **Read-only Filesystem**: Where possible

### API Key Management

- **Kubernetes Secrets**: Stored securely in cluster
- **Environment Variables**: Injected from secrets
- **No Hardcoded Keys**: Never committed to repository
- **Rotation Support**: Easy key rotation workflow

### Network Security

- **ClusterIP Service**: Internal cluster communication only
- **Network Policies**: Restricted inter-service access
- **TLS Encryption**: For external communication
- **VPC Isolation**: When running in cloud environments

### GitOps Safety

- **PR Workflow**: All changes require pull requests
- **Code Review**: Human approval required
- **Kubernetes Reconciliation**: Automatic rollback on invalid changes
- **Audit Trail**: Complete change history

### RBAC

```yaml
# Service account with minimal permissions
apiVersion: v1
kind: ServiceAccount
metadata:
  name: pi-mono-agent
  namespace: ai-infrastructure
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pi-mono-agent-role
  namespace: ai-infrastructure
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch"]
```

---

## Troubleshooting

### Common Issues

#### Container Not Starting

**Symptoms**: Pod in CrashLoopBackOff or Error state

**Diagnostics**:
```bash
# Check pod events
kubectl describe pod -l app=pi-mono-agent -n ai-infrastructure

# View logs
kubectl logs deployment/pi-mono-agent -n ai-infrastructure

# Check resource usage
kubectl top pods -n ai-infrastructure -l app=pi-mono-agent
```

**Solutions**:
- Verify API keys are correctly configured
- Check resource limits and requests
- Ensure container image is accessible
- Validate configuration syntax

#### RPC Communication Issues

**Symptoms**: Timeout errors, connection refused

**Diagnostics**:
```bash
# Test RPC endpoint
kubectl exec -n ai-infrastructure deployment/pi-mono-agent -- \
  echo '{"type":"ping"}' | timeout 5 pi --mode rpc --no-session

# Check service endpoints
kubectl get endpoints pi-mono-agent-service -n ai-infrastructure

# Port forward test
kubectl port-forward svc/pi-mono-agent-service 8080:8080
curl -X POST http://localhost:8080 -d '{"type":"ping"}'
```

**Solutions**:
- Verify service configuration
- Check network policies
- Ensure container is healthy
- Test with port forwarding

#### Skill Loading Issues

**Symptoms**: Skills not found, execution failures

**Diagnostics**:
```bash
# Check skill files
kubectl exec -n ai-infrastructure deployment/pi-mono-agent -- \
  ls -la /home/pi/.pi/agent/skills/

# Test skill loading
echo '{"type":"skill","skill":"gitops-operations"}' | \
  kubectl exec -i deployment/pi-mono-agent -n ai-infrastructure -- \
  pi --mode rpc --no-session
```

**Solutions**:
- Verify skill directory structure
- Check SKILL.md format
- Validate metadata fields
- Restart container if needed

### Performance Issues

#### High Latency

**Causes**:
- Model selection (larger models = slower)
- Network latency to LLM providers
- Resource constraints

**Solutions**:
- Use faster models for simple tasks
- Optimize prompts for conciseness
- Increase resource allocation
- Enable response streaming

#### High Costs

**Causes**:
- Expensive models (GPT-4, Claude 3 Opus)
- Long conversations
- Frequent tool usage

**Solutions**:
- Use cost-effective models when possible
- Implement session compaction
- Cache common responses
- Monitor and set cost alerts

### Debug Mode

Enable debug logging:

```bash
# Set debug environment variable
kubectl set env deployment/pi-mono-agent DEBUG=pi:* -n ai-infrastructure

# View debug logs
kubectl logs -f deployment/pi-mono-agent -n ai-infrastructure
```

---

## Comparison with Other Methods

| Feature | Temporal | Container Agents | Pi-Mono RPC |
|---|---|---|---|
| **Complexity** | High | Medium | Low |
| **Setup Time** | 2-4 hours | 1-2 hours | 15-30 minutes |
| **Interactivity** | Low | Medium | High |
| **Skill System** | Custom | Custom | agentskills.io |
| **LLM Support** | Custom | Custom | Built-in 15+ |
| **UI/UX** | None | Basic | Rich TUI/Web |
| **State Management** | Built-in | Custom | Sessions |
| **Monitoring** | Custom | Basic | Built-in |
| **GitOps Integration** | Manual | Manual | Built-in |
| **Multi-Provider** | Custom | Custom | Built-in |
| **Development Speed** | Slow | Medium | Fast |

### Use Case Recommendations

#### Use Temporal When:
- Complex multi-step workflows required
- Custom orchestration logic needed
- Advanced state management required
- Integration with existing Temporal workflows

#### Use Container Agents When:
- Simple custom logic needed
- Existing container-based architecture
- Minimal external dependencies required
- Full control over implementation

#### Use Pi-Mono RPC When:
- Interactive assistance needed
- Rapid development required
- Multi-provider LLM support needed
- agentskills.io compatibility required
- Rich UI/UX desired

---

## Future Enhancements

### Planned Features

#### 1. Web UI Integration
- React-based web interface
- Real-time collaboration
- Visual workflow designer
- Integrated monitoring dashboard

#### 2. Multi-Cluster Support
- Cross-cluster deployments
- Cluster federation
- Global resource management
- Disaster recovery capabilities

#### 3. Advanced Monitoring
- Custom metrics dashboards
- Alert management
- Performance analytics
- Cost optimization recommendations

#### 4. Enterprise Features
- SSO integration (SAML, OIDC)
- Role-based access control
- Audit logging
- Compliance reporting

#### 5. Model Fine-Tuning
- Custom model training
- Domain-specific optimization
- On-premise model hosting
- Private model management

### Community Contributions

We welcome contributions for:
- New skills and extensions
- Performance optimizations
- Security enhancements
- Documentation improvements
- Bug fixes and testing

### Development Roadmap

| Quarter | Features |
|---|---|
| Q2 2026 | Web UI, Multi-cluster support |
| Q3 2026 | Enterprise SSO, Advanced monitoring |
| Q4 2026 | Model fine-tuning, Performance analytics |
| Q1 2027 | Global federation, Compliance tools |

---

## References

### Documentation
- [Pi-Mono Repository](https://github.com/badlogic/pi-mono)
- [Agent Skills Specification](https://agentskills.io)
- [GitOps Control Plane Documentation](../README.md)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/)

### API References
- [Pi-Mono RPC Protocol](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/rpc.md)
- [Pi-Mono SDK](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/sdk.md)
- [Memory Agent API](../core/ai/runtime/agents/README.md)

### Community
- [Discord Server](https://discord.com/invite/3cU7Bz4UPx)
- [GitHub Discussions](https://github.com/lloydchang/gitops-infra-control-plane/discussions)
- [Issue Tracker](https://github.com/lloydchang/gitops-infra-control-plane/issues)

---

## Conclusion

The Pi-Mono containerized agent provides a powerful, interactive, and easy-to-use third execution method for the GitOps Control Plane. With its rich feature set, multi-provider support, and seamless integration, it enables rapid development and deployment of AI-powered infrastructure operations.

By following this documentation, teams can successfully implement, deploy, and operate Pi-Mono agents alongside existing Temporal workflows and containerized agents, creating a comprehensive and flexible AI agent ecosystem.

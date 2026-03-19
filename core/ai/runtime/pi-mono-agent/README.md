# Pi-Mono Containerized Agent

**Third Agent Execution Method for GitOps Control Plane**

This provides pi-mono as a containerized agent execution method alongside Temporal and other containerized agents.

## Overview

Pi-mono is an AI agent toolkit that provides:
- Interactive coding assistance
- Multi-provider LLM support (Anthropic, OpenAI, Google, etc.)
- Extensible skill system (agentskills.io compatible)
- RPC mode for container integration
- Rich tool ecosystem

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Execution Methods                  │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Temporal      │   Container    │      Pi-Mono RPC        │
│   Workflows     │   Agents        │      Container          │
└─────────────────┴─────────────────┴─────────────────────────┘
                           │
                    ┌───────▼───────┐
                    │   Pi-Mono     │
                    │   Container   │
                    │               │
                    │ • RPC Mode    │
                    │ • Skills      │
                    │ • Extensions  │
                    │ • GitOps      │
                    └───────────────┘
```

## Quick Start

### Build and Deploy

```bash
# Build container
cd core/ai/runtime/pi-mono-agent
npm run build

# Deploy to Kubernetes
npm run k8s:deploy

# Check status
kubectl get pods -n ai-infrastructure -l app=pi-mono-agent
```

### Use the Agent

```bash
# Test RPC communication
kubectl exec -n ai-infrastructure deployment/pi-mono-agent -- \
  echo '{"type":"prompt","message":"Hello"}' | pi --mode rpc --no-session

# Port forward for local testing
kubectl port-forward -n ai-infrastructure svc/pi-mono-agent-service 8080:8080

# Send RPC request
curl -X POST http://localhost:8080 \
  -H 'Content-Type: application/json' \
  -d '{"type":"prompt","message":"Review this Kubernetes manifest"}'
```

## Container Features

### RPC Mode
- JSON-RPC over stdin/stdout
- Event streaming for real-time responses
- Container-optimized configuration

### Skills Integration
- agentskills.io compatible
- GitOps operations skill included
- Custom skill support

### Security
- Non-root user execution
- Read-only filesystem where possible
- Health checks and readiness probes

### Scalability
- Horizontal Pod Autoscaler
- Load balancing via service
- Resource limits and requests

## Configuration

### Environment Variables

```bash
# LLM Provider Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_AI_API_KEY=...

# GitOps Integration
PI_WORKSPACE_DIR=/workspace
MEMORY_AGENT_URL=http://agent-memory-service.ai-infrastructure.svc.cluster.local:8080
TEMPORAL_ADDRESS=temporal-frontend.ai-infrastructure.svc.cluster.local:7233

# Monitoring
PROMETHEUS_URL=http://prometheus.monitoring.svc.cluster.local:9090
```

### Settings

Configuration in `config/settings.json`:
- Default model selection
- Skill/extension enablement
- GitOps integration settings
- Monitoring configuration

## Usage Examples

### Interactive Coding

```json
{
  "type": "prompt",
  "message": "Review the Kubernetes deployment in gitops/staging/"
}
```

### GitOps Operations

```json
{
  "type": "prompt", 
  "message": "Deploy the updated manifests to staging via GitOps"
}
```

### Skill Execution

```json
{
  "type": "skill",
  "skill": "gitops-operations",
  "message": "Check deployment status"
}
```

## Integration Points

### Memory Agent
```bash
# Query memory agent from pi-mono skill
curl -X POST "$MEMORY_AGENT_URL/api/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "previous deployment patterns"}'
```

### Temporal Workflows
```bash
# Trigger Temporal workflow from pi-mono
curl -X POST "$TEMPORAL_ADDRESS/api/v1/workflows" \
  -H "Content-Type: application/json" \
  -d '{"workflowType":"gitops-deployment"}'
```

### GitOps Pipeline
```bash
# Create PR for infrastructure changes
git add gitops/manifests/
git commit -m "Infrastructure update"
git push origin feature/update
gh pr create --title "Infrastructure Update"
```

## Monitoring

### Health Checks
- RPC endpoint responsiveness
- Resource usage monitoring
- Error rate tracking

### Metrics
- Token usage and cost
- Response times
- Skill execution success rates
- Integration health

### Logs
- Structured JSON logging
- Correlation IDs for request tracking
- Error details and stack traces

## Development

### Local Development

```bash
# Run locally
docker run -p 8080:8080 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v $(pwd)/skills:/home/pi/.pi/agent/skills \
  agentic-reconciliation-engine/pi-mono-agent:latest

# Test RPC
echo '{"type":"ping"}' | nc localhost 8080
```

### Custom Skills

Add skills to `skills/` directory following agentskills.io:

```markdown
---
name: my-custom-skill
description: Custom skill for specific operations
metadata:
  risk_level: low
  autonomy: fully_auto
---

# My Custom Skill
Use this for specific operations...

## Steps
1. Do this
2. Then that
```

### Custom Extensions

Create TypeScript extensions in `extensions/`:

```typescript
export default function (pi: ExtensionAPI) {
  pi.registerTool({
    name: "custom-tool",
    description: "Custom tool functionality",
    execute: async (params) => {
      // Implementation
    }
  });
}
```

## Comparison

| Feature | Temporal | Container Agents | Pi-Mono RPC |
|---|---|---|---|
| **Complexity** | High | Medium | Low |
| **Interactivity** | Low | Medium | High |
| **Skill System** | Custom | Custom | agentskills.io |
| **LLM Support** | Custom | Custom | Built-in 15+ |
| **UI/UX** | None | Basic | Rich TUI/Web |
| **State Management** | Built-in | Custom | Sessions |
| **Monitoring** | Custom | Basic | Built-in |

## Troubleshooting

### Common Issues

**Container Not Starting:**
```bash
kubectl logs deployment/pi-mono-agent -n ai-infrastructure
kubectl describe pod -l app=pi-mono-agent -n ai-infrastructure
```

**RPC Not Responding:**
```bash
# Test health endpoint
kubectl exec -n ai-infrastructure deployment/pi-mono-agent -- \
  echo '{"type":"ping"}' | pi --mode rpc --no-session

# Check port
kubectl port-forward svc/pi-mono-agent-service 8080:8080
```

**Skill Loading Issues:**
```bash
# Check skill files
kubectl exec -n ai-infrastructure deployment/pi-mono-agent -- \
  ls -la /home/pi/.pi/agent/skills/

# Test skill loading
echo '{"type":"skill","skill":"gitops-operations"}' | pi --mode rpc
```

## Security

- API keys stored in Kubernetes secrets
- Non-root container execution
- Network policies for inter-service communication
- RBAC for container permissions
- Resource limits for DoS protection

## Future Enhancements

- Web UI integration
- Multi-cluster support
- Advanced monitoring dashboards
- Custom model fine-tuning
- Enterprise SSO integration

## References

- [Pi-Mono Repository](https://github.com/badlogic/pi-mono)
- [Agent Skills Specification](https://agentskills.io)
- [GitOps Control Plane Documentation](../../../docs/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/)

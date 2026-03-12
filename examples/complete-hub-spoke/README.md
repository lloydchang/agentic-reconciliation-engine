# Complete Hub-Spoke AI Integration Example

This example demonstrates a comprehensive multi-agent AI system for GitOps infrastructure management, with flexible deployment options for different use cases.

## Architecture Overview

The example implements three deployment modes:

### 1. Enterprise Mode (Default)
- Uses AI Gateway for compliance and audit trails
- Multiple agents coordinate through the gateway
- Recommended for enterprise environments

```
[AI CronJobs] ◄────────────► [AI Gateway] ◄────────────► [Claude API]
       │                        │
       │                        ▼
       ▼                  [Audit Logs]
[Reports Storage]
```

### 2. Direct API Mode
- Direct Claude API access
- Faster performance, no gateway overhead
- Good for development/small teams

```
[AI CronJobs] ──► [Claude API] ──► [Reports Storage]
       ▲
       │
[Git Changes] ──► [Validation Jobs]
```

### 3. Local LLM Mode
- Uses local LLM service (Llama, etc.)
- No external API dependencies
- Maximum privacy and cost control

```
[AI CronJobs] ──► [Local LLM] ──► [Reports Storage]
       ▲                │
       │                ▼
[Git Changes] ──► [Validation Jobs] ──► [Local Storage]
```

## Components

### AI Gateway (`ai-gateway/`)
- **Purpose**: Traffic control and basic security filtering
- **Capabilities**: Regex-based filtering, rate limiting, audit logging
- **Limitations**: Cannot provide content-aware security (see architecture notes)
- **When to use**: Enterprise compliance requirements
- **When to skip**: Local LLM setups, development environments

### AI CronJobs (`ai-cronjobs/`)
- **Drift Analysis Agent**: Runs every 4 hours to monitor infrastructure changes
- **Validation Agent**: Daily manifest validation and security checks
- **Configuration**: Supports all three deployment modes via environment variables

### AI Validation Pipeline (`ai-validation/`)
- **GitOps Integration**: Triggered by Flux on repository changes
- **Real-time Validation**: Validates new manifests before deployment
- **Flexible Dependencies**: Can operate with or without AI Gateway

## Deployment Options

### Option 1: Enterprise Mode (Default)
```bash
kubectl apply -f examples/complete-hub-spoke/
```
- AI Gateway enabled
- All traffic routed through gateway
- Audit logging enabled

### Option 2: Direct API Mode
```bash
# Comment out ai-gateway in kustomization.yaml
# Set GATEWAY_MODE=direct in environment
kubectl apply -f examples/complete-hub-spoke/
```

### Option 3: Local LLM Mode
```bash
# Comment out ai-gateway in kustomization.yaml
# Set GATEWAY_MODE=local and CLAUDE_BASE_URL to local endpoint
kubectl apply -f examples/complete-hub-spoke/
```

## Configuration

### Environment Variables

| Variable | Default | Options | Description |
|----------|---------|---------|-------------|
| `GATEWAY_MODE` | `gateway` | `gateway`, `direct`, `local` | Deployment mode |
| `CLAUDE_BASE_URL` | Gateway URL | Any valid endpoint | LLM service URL |
| `CLAUDE_API_KEY` | From secret | - | API authentication |

### Kustomization Overrides

```yaml
# For local LLM setup
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../control-plane/
  # - ai-gateway/  # Disabled for local LLM
  - ai-cronjobs/
  - ai-validation/
configMapGenerator:
- name: ai-deployment-config
  literals:
  - GATEWAY_MODE=local
  - CLAUDE_BASE_URL=http://local-llm-service.default.svc.cluster.local:8080
```

## Architecture Limitations

### AI Gateway Catch-22
The AI Gateway cannot effectively filter LLM requests without already processing content through an LLM, creating a circular dependency. Current implementation only provides:
- Basic regex pattern matching
- Rate limiting and authentication
- Request metadata logging

**What it cannot do**:
- Content-aware security filtering
- Semantic analysis of prompts
- Sophisticated data exfiltration prevention

### Recommended Alternatives

**For Enterprise Compliance**:
- Use API Gateway with rate limiting and audit logging
- Implement client-side data sanitization
- Use network policies and RBAC

**For Local LLM Setups**:
- Bypass AI Gateway entirely
- Use local network policies for security
- Implement application-level filtering if needed

## Monitoring

### Agent Metrics
- **Gateway**: Request count, rate limit events, pattern matches
- **CronJobs**: Success/failure rates, execution times
- **Validation**: Validation coverage, error rates

### Logs Collection
All agents log to stdout/stderr for collection by cluster logging solution.

## Security Considerations

### Network Policies
- AI Gateway only accepts traffic from authorized agents
- CronJobs and Validation have egress restrictions
- Local LLM mode requires different network configuration

### RBAC
- Minimal permissions per component
- Service accounts with least privilege
- No cluster-admin access required

## Troubleshooting

### Common Issues

1. **Gateway Not Ready**
   ```bash
   kubectl get deployment claude-code-gateway
   kubectl logs deployment/claude-code-gateway
   ```

2. **CronJobs Failing**
   ```bash
   kubectl get cronjobs
   kubectl get jobs
   kubectl logs job/<job-name>
   ```

3. **Validation Pipeline Issues**
   ```bash
   kubectl get kustomization ai-validation-kustomization
   kubectl describe kustomization ai-validation-kustomization
   ```

### Mode Switching

To switch between deployment modes:
1. Update `kustomization.yaml` resources section
2. Modify `configMapGenerator` literals
3. Apply changes: `kubectl apply -k examples/complete-hub-spoke/`

## Example Workflows

### Scheduled Infrastructure Monitoring
1. CronJob triggers every 4 hours
2. Sends analysis request to configured LLM endpoint
3. LLM analyzes infrastructure state
4. Results stored in persistent volume
5. Alerts triggered on policy violations

### GitOps-Driven Validation
1. Developer commits changes to Git
2. Flux detects changes and triggers validation
3. Validation Job runs AI analysis
4. Results stored and potentially create PR comments
5. Changes only applied if validation passes

## Cost Considerations

### Enterprise Mode
- Gateway overhead: ~128Mi RAM, 100m CPU per replica
- Audit logging storage: ~1GB/month
- API costs through Claude

### Direct API Mode
- No gateway overhead
- Direct API costs
- Faster response times

### Local LLM Mode
- LLM service resource requirements
- No external API costs
- Maximum privacy

This example provides flexible deployment options while maintaining clear documentation of architectural trade-offs and limitations.

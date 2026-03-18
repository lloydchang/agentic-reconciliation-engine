# Slack Integration for Open SWE + GitOps Control Plane

## Overview

This directory contains the Slack integration for the Open SWE + GitOps Control Plane hybrid architecture. It allows users to trigger infrastructure operations through natural language commands in Slack.

## Files

- `main.go` - Main entry point and server setup
- `webhook_handler.go` - Slack webhook processing and event handling
- `command_router.go` - Command parsing, routing, and workflow execution

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SLACK_BOT_TOKEN` | Slack bot token for API access | Yes |
| `SLACK_SIGNING_SECRET` | Slack signing secret for webhook verification | Yes |
| `PORT` | Port to run the server on (default: 8080) | No |

## Supported Commands

| Command | GitOps Skill | Description |
|---------|--------------|-------------|
| `deploy` | deployment-strategy | Deploy applications |
| `optimize` | optimize-costs | Optimize cloud costs |
| `secure` | analyze-security | Run security analysis |
| `scale` | scale-resources | Scale resources |
| `backup` | orchestrate-backups | Create backups |
| `monitor` | check-cluster-health | Check cluster health |
| `troubleshoot` | diagnose-network | Network troubleshooting |
| `certificate` | manage-certificates | Certificate management |
| `database` | maintain-databases | Database maintenance |
| `cluster` | manage-kubernetes-cluster | Cluster management |

## Command Syntax

```
@GitOpsBot <command> [parameters]

Examples:
@GitOpsBot deploy environment:staging
@GitOpsBot optimize
@GitOpsBot scale target:web-app amount:50%
@GitOpsBot certificate service:my-service
```

## Parameters

- `environment`: Target environment (staging, production, etc.)
- `namespace`: Kubernetes namespace
- `service`: Service name
- `amount`: Scaling amount or percentage
- `target`: Target resource for scaling

## Architecture

```
Slack Message → Webhook Handler → Command Parser → Skill Router → Temporal Workflow → GitOps Execution
```

## Security

- **Request Verification**: All webhook requests are verified using Slack's signing secret
- **Replay Attack Protection**: Timestamp validation prevents replay attacks
- **Permission Checking**: Commands are validated against user permissions
- **Audit Logging**: All commands and executions are logged

## Deployment

### Docker Build
```bash
cd core/ai/runtime/open-swe-integration/slack
docker build -t gitops-slack-integration:latest .
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: slack-integration
  namespace: ai-infrastructure
spec:
  replicas: 1
  selector:
    matchLabels:
      app: slack-integration
  template:
    metadata:
      labels:
        app: slack-integration
    spec:
      containers:
      - name: slack-integration
        image: gitops-slack-integration:latest
        ports:
        - containerPort: 8080
        env:
        - name: SLACK_BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: slack-secrets
              key: bot-token
        - name: SLACK_SIGNING_SECRET
          valueFrom:
            secretKeyRef:
              name: slack-secrets
              key: signing-secret
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: slack-integration-service
  namespace: ai-infrastructure
spec:
  selector:
    app: slack-integration
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
  type: ClusterIP
```

### Ingress Configuration
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: slack-integration-ingress
  namespace: ai-infrastructure
spec:
  rules:
  - host: slack-integration.your-domain.com
    http:
      paths:
      - path: /webhooks/slack
        pathType: Prefix
        backend:
          service:
            name: slack-integration-service
            port:
              number: 80
```

## Monitoring

### Health Endpoints
- `GET /health` - Service health status
- `GET /metrics` - Prometheus metrics

### Metrics Collected
- Commands processed count
- Active conversation threads
- Error count
- Response latency
- Workflow execution status

## Error Handling

### Command Parsing Errors
- Invalid syntax → Ephemeral error message
- Unknown commands → List available commands
- Missing parameters → Parameter requirements

### Workflow Execution Errors
- Skill execution failures → Error notification in thread
- Timeout errors → Timeout notification with retry option
- Permission errors → Permission denied message

## Thread Management

### Thread Routing
- Each Slack thread maps to a unique conversation ID
- Context is maintained across messages in the same thread
- Memory agent stores conversation history

### Status Updates
- Initial acknowledgment when command received
- Progress updates during workflow execution
- Final results with links to PRs/deployments

## Integration with GitOps Control Plane

### Workflow Execution
1. Slack command parsed and validated
2. Memory context retrieved for conversation history
3. Temporal workflow started with skill name and parameters
4. GitOps skill executed through existing infrastructure
5. Results posted back to Slack thread

### Safety Integration
- All operations flow through GitOps validation
- Risk assessment and human gating maintained
- Audit trail includes Slack interaction details

## Development

### Local Testing
```bash
# Set environment variables
export SLACK_BOT_TOKEN="xoxb-your-bot-token"
export SLACK_SIGNING_SECRET="your-signing-secret"

# Run locally
go run main.go webhook_handler.go command_router.go
```

### Testing with ngrok
```bash
# Expose local server
ngrok http 8080

# Update Slack app webhook URL with ngrok URL
```

## Future Enhancements

- **NLP Integration**: Advanced natural language understanding
- **Interactive Elements**: Buttons for approval workflows
- **File Upload Support**: Upload manifests or configurations
- **Multi-channel Support**: Support for private messages and channels
- **Rich Formatting**: Enhanced message formatting with links and images

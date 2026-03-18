# Open SWE Integration Kubernetes Deployment

## Overview

This directory contains Kubernetes manifests for deploying the Open SWE + GitOps Control Plane integration to staging and production environments.

## Files

- `deployment.yaml` - Main deployment with security hardening and resource limits
- `service.yaml` - Service, ServiceAccount, and RBAC configuration
- `ingress.yaml` - HTTPS ingress with TLS and rate limiting
- `configmap.yaml` - Application configuration and feature flags
- `secrets.yaml` - Slack secrets and TLS certificates (managed by cert-manager)
- `monitoring.yaml` - Prometheus monitoring and alerting rules

## Prerequisites

### Required Infrastructure
- Kubernetes cluster (v1.24+)
- NGINX Ingress Controller
- cert-manager for TLS certificates
- Prometheus Operator for monitoring
- Temporal cluster running in `temporal` namespace
- Agent Memory Service running in `ai-infrastructure` namespace

### Required Namespaces
```bash
kubectl create namespace ai-infrastructure
kubectl create namespace temporal
```

## Configuration

### Slack Integration Setup

1. **Create Slack App**:
   - Go to https://api.slack.com/apps
   - Create new app with "Bots" permissions
   - Enable "Interactive Components" and "Slash Commands"
   - Add bot token scopes: `chat:write`, `chat:write.public`, `commands`, `app_mentions:read`

2. **Configure Webhooks**:
   - Set request URL: `https://slack-integration.gitops.example.com/webhooks/slack`
   - Enable "Always show a 200 OK response"

3. **Get Credentials**:
   - Bot Token: `xoxb-...`
   - Signing Secret: From app credentials page

### Update Secrets

Replace the placeholder values in `secrets.yaml`:

```bash
# Encode your Slack bot token
echo -n "xoxb-your-actual-bot-token" | base64

# Encode your Slack signing secret  
echo -n "your-actual-signing-secret" | base64

# Update secrets.yaml with the encoded values
```

### Update Ingress Host

Edit `ingress.yaml` to use your actual domain:

```yaml
spec:
  tls:
  - hosts:
    - slack-integration.your-actual-domain.com  # Update this
```

## Deployment

### 1. Apply Configuration

```bash
# Apply all manifests
kubectl apply -f kubernetes/

# Or apply individually
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/secrets.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/ingress.yaml
kubectl apply -f kubernetes/monitoring.yaml
```

### 2. Verify Deployment

```bash
# Check pod status
kubectl get pods -n ai-infrastructure -l app=slack-integration

# Check service status
kubectl get svc -n ai-infrastructure -l app=slack-integration

# Check ingress status
kubectl get ingress -n ai-infrastructure slack-integration-ingress

# View logs
kubectl logs -n ai-infrastructure -l app=slack-integration -f
```

### 3. Test Health Endpoints

```bash
# Test health endpoint
kubectl port-forward -n ai-infrastructure svc/slack-integration-service 8080:80 &
curl http://localhost:8080/health

# Test metrics endpoint
curl http://localhost:8080/metrics
```

## Configuration Options

### Feature Flags

Control integration features via `configmap.yaml`:

```yaml
feature_flags:
  enable_linear_integration: false      # Enable Linear webhook support
  enable_subagent_parallelism: true     # Enable parallel subagent execution
  enable_middleware_hooks: true         # Enable middleware system
  enable_context_enhancement: true      # Enable AGENTS.md context
  enable_advanced_nlp: false            # Enable advanced NLP processing
```

### Resource Limits

Adjust resource limits in `deployment.yaml`:

```yaml
resources:
  requests:
    cpu: 100m          # Minimum CPU
    memory: 128Mi       # Minimum memory
  limits:
    cpu: 500m          # Maximum CPU
    memory: 512Mi       # Maximum memory
```

### Scaling

For high availability, update replica count:

```yaml
spec:
  replicas: 2  # Increase for HA
```

## Monitoring

### Prometheus Metrics

Available at `/metrics` endpoint:

- `http_requests_total` - HTTP request count by status code
- `http_request_duration_seconds` - Request latency histogram
- `slack_commands_processed_total` - Commands processed count
- `temporal_workflows_started_total` - Temporal workflows started
- `memory_agent_requests_total` - Memory agent requests

### Alerting

Alerts configured in `monitoring.yaml`:

- **SlackIntegrationDown** - Service unavailable
- **SlackIntegrationHighErrorRate** - Error rate > 10%
- **SlackIntegrationHighLatency** - 95th percentile latency > 2s
- **SlackIntegrationMemoryUsageHigh** - Memory usage > 80%
- **SlackIntegrationCPUUsageHigh** - CPU usage > 80%
- **SlackIntegrationWorkflowFailures** - Workflow failure rate > 10%

### Grafana Dashboard

Import the provided Grafana dashboard for comprehensive monitoring:

```bash
# Import dashboard
kubectl apply -f monitoring/grafana-dashboard.yaml
```

## Security

### Network Policies

Apply network policies for additional security:

```bash
kubectl apply -f security/network-policy.yaml
```

### Pod Security

Deployment includes:
- Non-root user (UID 1000)
- Read-only filesystem
- All capabilities dropped
- Security context constraints

### RBAC

Service account has minimal required permissions:
- Read access to pods, services, configmaps, secrets
- Read access to deployments, replicasets
- Create access to jobs
- Full access to Temporal workflows

## Troubleshooting

### Common Issues

1. **Pod Not Starting**:
   ```bash
   kubectl describe pod -n ai-infrastructure -l app=slack-integration
   kubectl logs -n ai-infrastructure -l app=slack-integration
   ```

2. **Webhook Not Working**:
   - Check ingress configuration
   - Verify Slack webhook URL
   - Check TLS certificate status

3. **High Memory Usage**:
   - Check memory limits in deployment
   - Monitor memory usage trends
   - Consider increasing limits if needed

4. **Workflow Failures**:
   - Check Temporal cluster status
   - Verify Temporal connection
   - Review workflow logs

### Debug Commands

```bash
# Port-forward for local testing
kubectl port-forward -n ai-infrastructure svc/slack-integration-service 8080:80 &

# Test webhook endpoint
curl -X POST http://localhost:8080/webhooks/slack \
  -H "Content-Type: application/json" \
  -d '{"type":"url_verification","challenge":"test"}'

# Check Temporal connection
kubectl exec -n ai-infrastructure -l app=slack-integration -- \
  curl -s http://temporal-frontend.temporal.svc.cluster.local:7233/ping
```

## Maintenance

### Updates

To update the deployment:

```bash
# Build new image
docker build -t gitops-slack-integration:v1.1.0 .

# Update deployment image
kubectl set image deployment/slack-integration \
  slack-integration=gitops-slack-integration:v1.1.0 \
  -n ai-infrastructure

# Monitor rollout
kubectl rollout status deployment/slack-integration -n ai-infrastructure
```

### Backup

Backup configuration:

```bash
# Export current configuration
kubectl get all -n ai-infrastructure -l app=slack-integration -o yaml > backup.yaml

# Backup secrets
kubectl get secrets -n ai-infrastructure slack-secrets -o yaml > secrets-backup.yaml
```

## Production Considerations

### High Availability

- Deploy multiple replicas (2+)
- Use anti-affinity rules
- Configure proper resource limits
- Set up proper monitoring and alerting

### Performance

- Enable horizontal pod autoscaling
- Configure proper resource requests/limits
- Monitor key metrics
- Optimize Temporal workflow timeouts

### Disaster Recovery

- Backup configuration and secrets
- Document recovery procedures
- Test failover scenarios
- Maintain proper backup retention

# Fully Autonomous Langfuse Integration

## Overview

The GitOps Infra Control Plane now includes **completely autonomous Langfuse integration** that requires **zero manual steps**. When you run the quickstart scripts, Langfuse is automatically deployed, configured, and integrated with AI agent tracing.

## Key Features

- 🚀 **Zero Manual Intervention**: Fully automated setup
- 🆓 **Self-Hosted & Free**: No external dependencies or costs
- 🔒 **Data Privacy**: All traces stay in your infrastructure
- ⚡ **Immediate Access**: UI and dashboards ready after deployment
- 🔄 **Auto-Configuration**: API keys generated and secrets updated automatically

## Quick Start

### Option 1: Base Quickstart
```bash
./core/automation/scripts/quickstart.sh
```

### Option 2: Overlay Quickstart
```bash
./core/automation/scripts/overlay-quickstart.sh
```

### Option 3: Direct Setup
```bash
./core/automation/scripts/auto-configure-langfuse.sh
```

**All options provide the same result: Fully autonomous Langfuse integration**

## What Happens Automatically

### 1. Deployment Phase
- ✅ Deploys complete Langfuse stack (server, PostgreSQL, Redis, MinIO)
- ✅ Creates `langfuse` namespace
- ✅ Applies Kubernetes manifests
- ✅ Waits for pod readiness

### 2. Configuration Phase
- ✅ Sets up port-forward to localhost:3000
- ✅ Creates admin account automatically via API
- ✅ Generates API keys for agent integration
- ✅ Updates Kubernetes secrets with local keys

### 3. Integration Phase
- ✅ Restarts Temporal deployments to enable tracing
- ✅ Restarts pi-mono-agent deployment
- ✅ Deploys monitoring stack with Langfuse dashboard
- ✅ Maintains port-forward for continued access

## Access Points

After quickstart completion:

- **Langfuse UI**: http://localhost:3000
- **Grafana Dashboard**: http://localhost:3000/grafana
- **API Keys**: Automatically generated and configured
- **Tracing**: Active and collecting traces immediately

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Quickstart Scripts                        │
│  quickstart.sh / overlay-quickstart.sh                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              auto-configure-langfuse.sh                      │
│           Fully Autonomous Setup Script                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                Langfuse Stack (Self-Hosted)                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│  │   Server    │ │ PostgreSQL  │ │    Redis    │ │  MinIO  │ │
│  │   (UI)      │ │  (Database) │ │   (Cache)   │ │(Storage)│ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              AI Agent Integration                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Temporal  │ │ pi-mono     │ │   Grafana   │           │
│  │   Worker    │ │   Agent     │ │ Dashboard   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┐
```

## File Structure

```
core/automation/scripts/
├── auto-configure-langfuse.sh          # Fully autonomous setup
├── deploy-langfuse-selfhosted.sh        # Basic deployment script
├── quickstart.sh                         # Base quickstart
└── overlay-quickstart.sh                # Overlay quickstart

core/config/
├── langfuse-secret.yaml                  # Secrets for control-plane
└── langfuse-secret-$TOPDIR.yaml     # Secrets for ai-infrastructure

core/resources/infrastructure/monitoring/
├── kustomization.yaml                    # Updated with langfuse-dashboard.yaml
└── langfuse-dashboard.yaml               # Grafana dashboard

core/hooks/
└── post-quickstart.sh                    # Updated for autonomous setup
```

## Environment Variables

The setup automatically configures the following:

- `LANGFUSE_PUBLIC_KEY`: Auto-generated API public key
- `LANGFUSE_SECRET_KEY`: Auto-generated API secret key
- `LANGFUSE_HOST`: http://localhost:3000 (self-hosted)
- `OTEL_EXPORTER_OTLP_ENDPOINT`: http://localhost:3000/api/public/otel
- `OTEL_SERVICE_NAME`: Configured per deployment

## Monitoring and Observability

### Grafana Dashboard
- **Name**: Langfuse AI Agent Observability
- **Panels**: Agent performance, skill invocation success rates, cost analysis
- **Auto-deployed**: Integrated with monitoring stack

### Metrics Available
- Total traces and evaluations
- Skill invocation success rates
- Cost analysis and efficiency
- Response time distributions
- Error rates by operation type

## Troubleshooting

### Common Issues

1. **Port Forward Issues**
   ```bash
   # Check if port-forward is running
   ps aux | grep "port-forward"
   
   # Restart if needed
   ./core/automation/scripts/auto-configure-langfuse.sh
   ```

2. **Pod Not Ready**
   ```bash
   # Check pod status
   kubectl get pods -n langfuse
   
   # Check logs
   kubectl logs -l app=langfuse-server -n langfuse
   ```

3. **API Key Issues**
   ```bash
   # Check secrets
   kubectl get secret langfuse-secrets -n control-plane -o yaml
   kubectl get secret langfuse-secrets -n ai-infrastructure -o yaml
   ```

### Manual Recovery

If automated setup fails:
```bash
# Run manual setup
./core/automation/scripts/deploy-langfuse-selfhosted.sh

# Then run configuration
./core/automation/scripts/auto-configure-langfuse.sh
```

## Security Considerations

### Data Privacy
- All data stays within your Kubernetes cluster
- No external API calls to cloud services
- Full control over data retention and access

### Access Control
- Default admin account: admin@local.dev
- Temporary password: temp-admin-password-123
- **Important**: Change credentials after first login

### Network Security
- Port-forward provides secure local access
- No external exposure without explicit configuration
- Network policies can restrict inter-pod communication

## Performance Optimization

### Resource Allocation
- **Langfuse Server**: 512Mi memory, 250m CPU (requests)
- **PostgreSQL**: 256Mi memory, 100m CPU (requests)
- **Redis**: 128Mi memory, 50m CPU (requests)
- **MinIO**: 128Mi memory, 50m CPU (requests)

### Scaling Considerations
- Single-node deployment suitable for development/testing
- Production deployments may require resource scaling
- Persistent storage recommended for data durability

## Integration with AI Agents

### Temporal Workers
- Automatic tracing of workflow executions
- Activity-level observability
- Error tracking and performance metrics

### pi-mono Agent
- Skill invocation tracing
- Response time monitoring
- Resource usage tracking

### Custom Agents
- Follow OpenTelemetry standards
- Automatic integration with Langfuse
- Consistent tracing across all agents

## Future Enhancements

### Planned Features
- High-availability deployment options
- Automated backup and restore
- Advanced alerting and notifications
- Multi-cluster support

### Extensibility
- Custom dashboard configurations
- Additional monitoring integrations
- Plugin architecture for custom metrics

## Migration from Cloud

If migrating from Langfuse Cloud:

1. **Data Export**: Export existing data from cloud
2. **Local Setup**: Run autonomous setup
3. **Data Import**: Import data to local instance
4. **Configuration Update**: Update applications to use local endpoint
5. **Validation**: Verify tracing functionality

## Support and Maintenance

### Logs and Debugging
```bash
# Langfuse server logs
kubectl logs -l app=langfuse-server -n langfuse -f

# Database logs
kubectl logs -l app=postgres -n langfuse -f

# Setup script logs
./core/automation/scripts/auto-configure-langfuse.sh 2>&1 | tee setup.log
```

### Health Checks
```bash
# Check Langfuse health
curl http://localhost:3000/api/health

# Check Kubernetes resources
kubectl get all -n langfuse
```

### Updates and Maintenance
- Regular updates via container image tags
- Database migrations handled automatically
- Configuration updates via script re-execution

---

**Result**: Complete autonomous Langfuse integration with zero manual steps required. Run quickstart and you have full AI agent observability immediately.

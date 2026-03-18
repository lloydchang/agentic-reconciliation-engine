# Agentic AI Infrastructure User Guide

## Overview

The GitOps-infra-control-plane now includes comprehensive agentic AI capabilities that automate infrastructure operations, provide intelligent monitoring, and enable autonomous workflows. This guide covers deployment, configuration, and usage of the agentic AI infrastructure.

## Architecture Components

### 1. Memory Agent Layer
- **Rust Memory Agent**: Performance-critical inference with llama.cpp
- **Go Memory Agent**: Temporal workflow integration
- **Python Memory Agent**: ML/AI prototyping and experimentation

### 2. Temporal Orchestration Layer
- Multi-skill workflow coordination
- Durable execution with Cassandra persistence
- Risk assessment and human gate management

### 3. MCP Gateway
- Redis-backed server registry
- Authorization and authentication
- Tool and service discovery

### 4. Background Task Queue
- Asynchronous job processing
- Cost tracking and monitoring
- Performance optimization

## Deployment

### Prerequisites
- Kubernetes cluster (1.24+)
- Flux CD or ArgoCD for GitOps
- Redis for MCP registry
- Cassandra for Temporal persistence

### Quick Start

1. **Deploy Base Infrastructure**
   ```bash
   kubectl apply -f core/gitops/ai-infrastructure-base.yaml
   ```

2. **Deploy MCP Gateway**
   ```bash
   kubectl apply -f core/gitops/mcp-gateway-deployment.yaml
   ```

3. **Deploy Task Queue**
   ```bash
   kubectl apply -f core/gitops/task-queue-deployment.yaml
   ```

4. **Configure Environment**
   ```bash
   kubectl apply -f core/gitops/ai-agent-config.yaml
   ```

### Validation
Run the comprehensive test suite:
```bash
./test/run-tests.sh --all
```

## Available Skills

### Toil Automation Skills

#### Certificate Rotation (`certificate-rotation`)
**Purpose**: Automated SSL/TLS certificate management and rotation
**Triggers**: Certificate expiry within 30 days
**Actions**:
- Monitors certificate validity
- Generates renewal requests
- Updates Kubernetes secrets
- Validates certificate chains

#### Dependency Updates (`dependency-updates`)
**Purpose**: Automated dependency management and security updates
**Triggers**: New security advisories, outdated dependencies
**Actions**:
- Scans for vulnerable dependencies
- Creates update PRs with testing
- Validates compatibility
- Manages version constraints

#### Code Review Automation (`pr-analysis`)
**Purpose**: Automated code review and quality assurance
**Triggers**: Pull request creation/modification
**Actions**:
- Static code analysis
- Security vulnerability scanning
- Best practices validation
- Performance impact assessment

### Monitoring & Compliance Skills

#### Compliance Validation (`compliance-validation`)
**Purpose**: Automated compliance checking across frameworks
**Triggers**: Configuration changes, scheduled audits
**Actions**:
- CIS benchmark validation
- NIST framework compliance
- PCI-DSS requirement checking
- HIPAA security assessment

#### Risk Assessment (`risk-assessment`)
**Purpose**: Deployment risk evaluation and mitigation
**Triggers**: Pre-deployment validation
**Actions**:
- Change impact analysis
- Rollback plan generation
- Resource utilization forecasting
- Security threat modeling

#### Automated Testing (`automated-testing`)
**Purpose**: CI/CD pipeline validation and testing
**Triggers**: Code changes, deployment requests
**Actions**:
- Unit test execution
- Integration test validation
- Performance benchmarking
- Load testing automation

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_GATEWAY_URL` | MCP gateway endpoint | `http://mcp-gateway:8080` |
| `TEMPORAL_HOST` | Temporal server host | `temporal-frontend` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |
| `LANGUAGE_PRIORITY` | Memory agent priority | `rust,go,python` |
| `COST_TRACKING_ENABLED` | Enable cost monitoring | `true` |
| `SECURITY_LEVEL` | Security validation level | `medium` |

### Skill Configuration

Each skill can be configured via ConfigMap:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: skill-config
data:
  certificate-rotation: |
    expiry_threshold: 30
    auto_renewal: true
  dependency-updates: |
    security_only: false
    auto_merge: false
```

## Usage Examples

### Certificate Management
```bash
# Trigger certificate rotation
kubectl create job cert-rotation \
  --from=cronjob/certificate-rotation-cron \
  --image=agent-runner
```

### Dependency Updates
```bash
# Run dependency scan
kubectl exec -it dependency-scanner -- \
  python -m skills.dependency_updates scan --all
```

### Compliance Validation
```bash
# Execute compliance audit
kubectl run compliance-audit \
  --image=compliance-validator \
  --restart=Never \
  -- --framework=cis --scope=cluster
```

## Monitoring & Observability

### Metrics
- **Temporal Workflows**: Success rates, execution times
- **Skill Performance**: Response times, error rates
- **Cost Tracking**: Token usage, API costs
- **MCP Gateway**: Request rates, latency

### Dashboards
Access monitoring dashboards at:
- Prometheus: `http://prometheus:9090`
- Grafana: `http://grafana:3000`
- Temporal UI: `http://temporal-frontend:8080`

### Alerting
Configured alerts for:
- Skill execution failures
- High error rates
- Resource exhaustion
- Security violations

## Troubleshooting

### Common Issues

#### Memory Agent Unavailable
```bash
# Check agent health
kubectl get pods -l app=memory-agent

# View logs
kubectl logs -l app=memory-agent

# Restart agent
kubectl rollout restart deployment/memory-agent
```

#### MCP Gateway Connection Issues
```bash
# Verify gateway status
kubectl get pods -l app=mcp-gateway

# Check Redis connectivity
kubectl exec -it mcp-gateway -- redis-cli ping

# Validate configuration
kubectl describe configmap ai-agent-config
```

#### Skill Execution Failures
```bash
# Check Temporal workflows
kubectl get workflows.temporal.io

# View workflow logs
kubectl logs -l workflow=<workflow-name>

# Manual skill execution
kubectl run skill-test \
  --image=skill-runner \
  --restart=Never \
  -- --skill=<skill-name> --params=<params>
```

### Log Analysis
```bash
# View all agent logs
kubectl logs -l app.kubernetes.io/name=ai-agent --all-containers

# Filter by skill
kubectl logs -l skill=<skill-name>

# Search for errors
kubectl logs -l app=memory-agent | grep ERROR
```

## Security Considerations

### Authentication & Authorization
- MCP gateway requires API keys for external access
- Kubernetes RBAC controls internal access
- Skills validate permissions before execution

### Data Protection
- All data encrypted in transit and at rest
- Sensitive information stored in Kubernetes secrets
- Audit logging enabled for all operations

### Network Security
- Service mesh integration (Istio/Linkerd)
- Network policies restrict pod communication
- External access through ingress with TLS

## Performance Tuning

### Resource Allocation
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

### Scaling
- Horizontal Pod Autoscaling based on CPU/memory
- Temporal worker scaling for high load
- Redis cluster for MCP registry scaling

### Optimization
- Model quantization for memory agents
- Caching for frequently accessed data
- Async processing for non-critical tasks

## Support & Contributing

### Getting Help
1. Check this documentation
2. Review troubleshooting section
3. Check GitHub issues
4. Contact the infrastructure team

### Contributing
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

### Roadmap
- Enhanced ML model integration
- Multi-cloud support expansion
- Advanced cost optimization
- Real-time monitoring dashboards
